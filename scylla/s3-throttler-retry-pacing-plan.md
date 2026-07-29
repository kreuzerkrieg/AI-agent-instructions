# Improvement plan: pace S3 retries and stop throttles consuming the retry budget

**Load this together with `s3-throttler-work.md` when implementing the S3 throttler fix
(PR 30775 / SCYLLADB-3249 / SRE-1418).** That document is the measurement record; this one is the
implementation plan.

Written 2026-07-29 after run 10 measured the reworked controller (per-client limiters, seeded and
enabled from the first request). Everything with a file:line is verified against the tree at that
date — check a reference if you doubt it, don't re-derive the whole picture.

---

## 1. Goal and success criteria

**Goal:** a backup under S3 throttling **completes** rather than losing objects.

Success is measured on the upload phase of the perf harness, 16 x i4i.16xlarge, flat keys into the
warm `sstables_ewz` prefix (the shape of runs 7, 9 and 10):

| | PUT/s | slowdown | **files LOST** |
|---|---|---|---|
| run 7 · no controller | 2,346 | 24,867 | **116** |
| run 9 · per-shard controller | 2,242 | 24,220 | **236** |
| run 10 · per-client seeded controller, pass 1 | 2,153 | 25,957 | **260** |
| run 10 · pass 2 | 2,548 | 101,828 | **202** |
| **target** | *may drop* | *may stay high* | **0** |

**`slowdown` staying high is acceptable, even expected** — S3 pushing back is not the failure. A
lower PUT/s is an acceptable price. The only metric that must reach zero is **lost files**, because a
backup has no partial credit: an sstable missing `Data.db` or `TOC.txt` cannot be restored, and
production `backup_task` aborts on the first unrecoverable error.

## 2. Why admission-rate control alone cannot get there

Run 10, pass 1, per box — the table that motivates this plan:

```
box                elapsed  PUT/s  slowdown   LOST
98.81.206.207         971s     49     3,573     29     <- self-throttled 3.6x slower, still lost
3.94.52.203           427s    114     6,003     57
98.94.36.50           416s    117     4,854     52
...
3.94.10.250           276s    162        19      0     <- barely throttled by S3
3.95.134.216          250s    175         0      0
34.204.69.52          248s    178         0      0
44.203.203.232        244s    178         1      0
```

Loss tracks **slowdown**, not rate. The four clean boxes are the ones S3 happened not to throttle, and
they ran at the *highest* PUT/s. Every throttled box lost files, and backing off did not rescue any of
them — the worst box was cut from 178 to 49 PUT/s and still lost 29 objects after 971 s.

The reason is structural: **loss comes from the retry budget expiring, not from the admission rate.**
`acquire()` is called once on admission (`utils/s3/client.cc:620`), immediately *before*
`gc.http.make_request(request, handler, rs, ...)` — and the retry loop lives inside that seastar call.
A request already in the retry loop fires all 11 attempts unpaced within ~25.5 s
(`default_max_retries = 10`, backoff `(1 << attempt) * 25ms`) and then gives up. Slowing *new*
admissions does nothing for it.

## 3. Change 1 — pace retries at the converged rate

Put the limiter in the retry path, beside the backoff that already exists:

```cpp
// default_aws_retry_strategy::should_retry(), where sleep_before_retry() already awaits
if (should_retry) {
    co_await sleep_before_retry(attempted_retries);
    co_await limiter->acquire();          // <-- new: retry at the current fill rate
}
```

### Three constraints that shape the design — all verified

1. **`should_retry()` is `const`** (`seastar/include/seastar/http/retry_strategy.hh:19`). Pacing must
   not mutate the strategy. Calling `acquire()` through a `throttling_controller*` member is fine —
   the pointee is non-const.
2. **`should_retry()` does not know the request class.** It receives only `(exception_ptr, unsigned)`.
   The client picks read-vs-write limiter at the call site (`client.cc:620`) but the strategy is shared
   — `*_retry_strategy` is passed to every `make_request` (`client.cc:603, 642, 891`). **Recommendation:
   hold two strategy instances, one per class, each bound to its own limiter**, and select at the same
   place the limiter is selected. Threading a class parameter through the seastar interface is the
   alternative and is worse — it changes an upstream API for a Scylla-specific need.
3. **The strategy outlives/precedes the limiters in construction order.** Callers pass a strategy into
   `client::make()` (the perf harness passes its own `counting_retry_strategy`), while the limiters are
   created inside the client ctor (`client.cc:162-163`). So the wiring must be *injection after
   construction*, not a constructor argument. Since `seastar::http::retry_strategy` has only
   `should_retry()`, add a Scylla-side interface — e.g. `aws::rate_limited_retry_strategy` with
   `void set_limiter(throttling_controller*)` — and have the client call it in the ctor when the
   strategy implements it (`dynamic_cast` or a virtual no-op default). A caller-supplied strategy that
   does not implement it keeps today's behaviour.

## 4. Change 2 — stop throttles consuming the retry budget

The cap is currently tested **before** the error is even classified
(`utils/s3/default_aws_retry_strategy.cc`):

```cpp
if (attempted_retries >= _max_retries) {   // fires regardless of error kind
    rs_logger.warn("Retries exhausted. Retry# {}", attempted_retries);
    co_return false;
}
auto err = aws_error::from_exception_ptr(error);
```

So a throttled request dies at attempt 11 **while still flagged retryable** — which is the single most
common misreading of this code, because `client.cc` does mark it retryable
(`should_retry = possible_error->is_retryable() || utils::http::retryable(is_throttling)`).

Reorder so classification comes first, and give throttles a different bound.

### Prerequisite

`is_throttling_error()` is a **file-static in `client.cc:85`** and is not reachable from the retry
strategy. Move it to a shared header — `utils/s3/aws_error.hh` is the natural home — as a first,
mechanically-safe commit. Do not duplicate it; two copies of a retryability predicate will drift.

### Mandatory: replace the count bound with a *time* bound, do not simply remove it

`make_request` takes **no deadline** — only `abort_source*` (`client.hh:184-211`). If throttles stop
consuming `_max_retries` and nothing else bounds them, a permanently hot partition means an unbounded
retry loop: backup hangs instead of failing, holding a connection and an `_mpus_sem` slot
(`max_client_mpu_in_flight = 32`) for the duration. **That is a worse failure than losing a file.**

So: for throttling errors, bound by elapsed wall-clock (a generous deadline — minutes, since observed
throttling episodes lasted minutes) or by an explicit much larger attempt cap, and keep honouring the
`abort_source`. State the chosen bound in the commit message.

### Both halves are required

- pacing alone → the same 11 attempts stretched over a longer window; still hits the cliff
- exemption alone → reissues at full rate into a hot partition, adding load precisely when it hurts

## 5. Risks to think about before writing code

- **Blast radius beyond backup.** `_retry_strategy` is used by every S3 operation, not just uploads.
  Downloads currently never throttle (1 lost object in 1,235,405 across three runs), so the read path
  should be unaffected in practice — but the change is global, so say so explicitly.
- **The perf harness must keep reproducing SRE-1418.** Bounded retries were a deliberate early
  requirement: they are what makes the failure observable. If throttles stop consuming budget in the
  client, `perf_s3_downloader` needs its own bounded strategy (it already subclasses one —
  `counting_retry_strategy`) or it can no longer measure the threshold.
- **A separate hand-rolled retry loop exists** in `chunked_download_source` (`client.cc:1644` uses
  `default_aws_retry_strategy::default_max_retries` directly). It is on the read path so it is not
  urgent, but leaving it inconsistent is a trap for the next person.
- **`min_fill_rate = 0.5` req/s is per limiter.** With one limiter per client and a client per shard,
  64 shards x 16 nodes cannot go below ~512 req/s aggregate at maximum backoff. If a partition's real
  ceiling is under that, pacing cannot reach it no matter how well the retry path behaves — this is the
  remaining per-shard aggregation problem, tracked in `s3-throttler-work.md` section 4.

## 6. Verification, cheapest first

1. **Unit test, no AWS.** `test/boost/s3_test.cc` already gained controller tests in the PR's third
   commit. Add: under a strategy bound to a limiter with a tiny fill rate, N synthetic throttle
   responses produce N paced retries and **no** exhaustion inside the deadline; and a non-throttling
   error still exhausts at `_max_retries`.
2. **Local single-process run** against the real bucket with a small fallocated corpus — enough to
   confirm the retry path is exercised and nothing deadlocks. `fallocate` is legitimate for the upload
   path: unwritten extents read as zeros without device I/O, the path is NIC-bound, and S3 cannot
   distinguish zeros from data.
3. **One fleet run, only if 1 and 2 pass.** 16 x i4i.16xlarge, 20-minute download then two upload
   passes (`PHASES=both ROUND_MIN=20 UPLOAD_PASSES=2 UPLOAD_PREFIX=sstables_ewz`), which is run 10's
   exact shape so the numbers are directly comparable. ~35 min of instance time, ~$50.
   **There is no budget for casual fleet runs — cost it and ask first.**

Onset timing to size any run: throttling-induced failure appeared at **233–365 s** into the upload
across runs 7/8/9 (first 503 roughly 25 s earlier). A single upload pass off a 20-minute download only
lasts ~310 s, so it can end *before* onset and read as a false pass — hence two passes.

## 7. File map

| what | where |
|---|---|
| `acquire()` on admission, outside the retry loop | `utils/s3/client.cc:620` |
| retry strategy owned / passed | `utils/s3/client.hh:162`, `client.cc:140,148-149,603,642,891` |
| limiters (per client since run 10's version) | `utils/s3/client.hh:155-156`, created `client.cc:162-163` |
| seed rate | `client.cc:157` — `connections_per_shard / 2.0` |
| retryable flag set | `client.cc:551` and the `should_retry` assignment below it |
| cap checked before classification | `utils/s3/default_aws_retry_strategy.cc` |
| retry budget + backoff | `default_aws_retry_strategy.hh:21`, `.cc` `sleep_before_retry` |
| `is_throttling_error` (file-static, needs moving) | `utils/s3/client.cc:85` |
| controller: `_enabled`, `min_fill_rate`, ctor | `utils/s3/aws_throttling_controller.{hh,cc}` |
| separate hand-rolled retry loop | `utils/s3/client.cc:1644` |
