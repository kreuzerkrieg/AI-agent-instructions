# Working on the S3 throttling controller (PR 30775)

**Load this when the task involves the S3 send-rate throttler, PR 30775, SCYLLADB-3249, or
SRE-1418 upload failures.**

Written 2026-07-28 as a handoff. Everything below marked *measured* comes from three 16-instance
fleet runs; everything marked *code* has a file:line reference you can check in seconds. Do not
re-derive it — verify a reference if you doubt it, then move on.

---

## 1. The problem, in one paragraph

Native backup on a customer cluster (SRE-1418, 27 nodes / ~260 TiB, large ARM instances) fails
because S3 throttles PUTs. Reproduced 2026-07-28: **uploads throttle hard and lose objects
outright**, while downloads are untouched. The throttler in PR 30775 is intended to fix this and,
as measured, does not — it costs ~6% throughput and reduces neither throttling nor data loss. The
reasons are all in the wiring rather than the CUBIC algorithm, and all four are fixable.

## 2. What was measured

Three runs, 16 x i4i.16xlarge (64 shards each), same source dataset, corpus written to disk.

| | X1 baseline | X2 hashed prefix (PR 30846) | X3 throttler (PR 30775) |
|---|---|---|---|
| upload PUT/s aggregate | 2,346 | 2,231 | 2,242 |
| upload MB/s | 53.9 GB/s | 51.0 GB/s | 50.9 GB/s |
| slowdown (retry events) | 24,867 | 97,033 | 24,220 |
| **files LOST** | **116** | **1,082** | **236** |
| download GET/s aggregate | 6,695 | 6,124 | 5,777 |
| download slowdown / lost | 0 / 0 | 0 / 0 | 0 / 1 |

**The number that matters is files LOST.** A backup has no partial credit: an sstable missing
`Data.db` or `TOC.txt` cannot be restored, and production `backup_task` aborts on the first
unrecoverable error. So these are not tolerable loss rates — they are the frequency at which the
whole backup dies, matching the customer's "backup ERRORed at 64% after 2h29m".

**Downloads are not the problem.** 1 lost object in 1,235,405 across all three runs, zero
`slowdown`, zero `net_reset`. Scope all work to the write path.

Failure signature to grep for:

```
Code: 19. Reason: Please reduce your request rate.      (aws_error_type::SLOW_DOWN)
default_http_retry_strategy - Retries exhausted. Retry# 10
std::runtime_error (Failed to parse ETag list. Aborting multipart upload.)
```

The ETag message is a **masking artefact** — `upload_part` swallows the real error and leaves an
empty ETag, so ~2/3 of losses surface as a parse failure rather than as throttling. The rest surface
as `storage_io_error` directly. Fixing only the ETag path improves the message, not the outcome.

## 3. Why it does not work — four causes, all code

### 3.1 Retries bypass the limiter *(this is the one that costs data)*

`utils/s3/client.cc:596`:

```cpp
co_await (rc == read ? gc.read_limiter : gc.write_limiter)->acquire(as);   // once, on admission
co_await gc.http.make_request(request, handler, rs, std::nullopt, as)...   // retries happen inside
```

The retry loop lives inside seastar's `http::client::make_request(req, handler, rs, ...)`, below the
s3 layer. A request takes **one token on admission** and then all retry attempts fire without
touching the token bucket again. The limiter gates admission, not retries.

The throttler still *learns* from retries — `wrap_handler` calls `update_client_sending_rate(true)`
per throttled reply (`client.cc:530`) — but the reduced fill rate applies only to *new* requests.

Budget: `default_max_retries = 10` (`default_aws_retry_strategy.hh:21`), backoff
`(1 << attempt) * 25ms` (`default_aws_retry_strategy.cc`), so the whole retry window is
25 * (2^10 - 1) ~= **25.6 s**. Observed throttling lasted *minutes*. Requests therefore exhaust the
budget and the multipart upload aborts.

### 3.2 The cap is checked before anything else

`default_aws_retry_strategy::should_retry()`:

```cpp
if (attempted_retries >= _max_retries) {   // before any classification
    rs_logger.warn("Retries exhausted. Retry# {}", attempted_retries);
    co_return false;                        // request fails
}
...
if (should_retry) { co_await sleep_before_retry(attempted_retries); }
```

At attempt 10 the request fails regardless of whether the error was a throttle. **Pacing alone
cannot give zero failures** — it raises per-attempt success probability without removing the ceiling.

### 3.3 The controller is a no-op until it has already been throttled

`aws_throttling_controller::acquire()` returns immediately while `!_enabled`
(`aws_throttling_controller.cc:28`), and `_enabled = true` is set only in the throttling branch
(`:110`). The opening burst always throttles, by construction. On a 64-shard node, 63 shards each
wait to be throttled personally before doing anything.

### 3.4 There is one limiter per shard per scheduling group

`client.hh:147-150` — `group_client` owns `write_limiter` and `read_limiter`.
`client.hh:153` — `client::_https` is `unordered_map<scheduling_group, group_client>`, on a
per-shard client.

So limiters = shards x scheduling_groups x nodes. Run 9 had **1,024** (64 x 1 x 16; only `main` was
active). Each has its own `_enabled` flag and its own local view, while the S3 limit is
**per-partition and global**. A thousand controllers each reacting to ~1/1000th of the feedback
engage enough to cost throughput, then independently probe back up.

Also `min_fill_rate = 0.5` req/s is **per limiter**, so 64 x 16 cannot go below ~512 req/s aggregate
at maximum backoff. If a partition's real ceiling is under that, the fleet overshoots even fully
backed off.

## 4. What to do, in order of value

1. **Pace retries AND stop counting throttles against the budget.** `should_retry()` already awaits
   (`sleep_before_retry`), so `co_await limiter->acquire()` belongs beside it — the strategy needs a
   reference to the limiter. Pair it with exempting throttling responses from `_max_retries` (retry
   indefinitely, bounded by abort/wall-clock, or give throttles a much larger separate cap). **Either
   half alone leaves the failure mode intact:** pacing alone delays exhaustion, exemption alone
   reissues at full rate.
2. **Do not start disabled.** Begin from a conservative fill rate. If the goal is avoiding throttling
   rather than recovering from it, unlimited-until-first-throttle defeats it.
3. **Move the limiter to the `s3_client` level.** Agreed with Ernest 2026-07-28. All scheduling groups
   in one client share the endpoint and therefore the same partitions, so independent CUBIC probes per
   group compete over one resource. Worth 3-4x fewer controllers in production. *Be honest that this
   would not have changed run 9* — only `main` was active there, so the shard dimension is what
   produced 1,024.
4. **For the shard dimension, share the signal, not the bucket.** A cross-shard token bucket puts a
   core-to-core hop on every request's fast path. Instead: target `global_limit / smp::count` per
   shard, and broadcast `update_client_sending_rate(true)` on throttle so every shard backs off on
   first evidence — which also fixes 3.3 for 63 of 64 shards.

**Keep the read/write split.** `classify_request` (`client.cc:104`) separates them because S3's GET
and PUT ceilings genuinely differ (~5,500 vs ~3,500 per prefix). That division reflects reality; the
scheduling-group division does not.

## 5. Constraints — read before proposing anything

- **There is no budget for fleet runs.** Ernest, 2026-07-28: "these jerks don't have a couple of
  bucks". A 16 x i4i.16xlarge fleet is ~$88/hr. **Reason from code and S3 semantics.** If a run is
  genuinely required, cost it explicitly and ask first — never launch an instance without explicit
  per-run approval.
- **i4i/i7i spot capacity is effectively zero at every size** despite quoted prices. i7i.16xlarge had
  no capacity at all, spot or on-demand, across five AZs. Budget on-demand.
- **Do not blindly trust the AWS 3,500 PUT/s / 5,500 GET/s figures.** Measured: GET sustained 22%
  *above* its documented limit with zero pushback while PUT broke 33% *below* its own.
- **Bounded retries are deliberate in the test harness.** They are what makes SRE-1418 reproducible.
  If throttles stop consuming budget in the client, the perf test needs its own bounded strategy or
  it can no longer measure the threshold.

## 6. Tools you already have

Branch `perf-s3-downloader` in `~/Development/scylladb` (unpushed) carries the harness plus PR
30775's two functional commits cherry-picked (`35ea3bf` interface, `5e7661d` client wiring).

`test/perf/perf_s3_downloader.cc` flags that matter:

| flag | use |
|---|---|
| `--mode download\|upload` | phase |
| `--fleet_size N --fleet_index i` | partition the dataset by position in the ordered listing; balanced at any N, no coordinator |
| `--corpus_dir DIR` | **must** be set for a representative run — the disk write is what keeps `chunked_download_source` out of contiguous mode |
| `--upload_hash_prefix` | PR 30846's hashed key layout |
| `--sample_interval N` | per-shard samples now **flush as taken**, escalating to `warn` on any SlowDown, so a run can be aborted early |
| `--round_timeout M --max_rounds 1` | one fixed-length round |
| `--initial_connections N` | default 128 *per shard* |

Fleet driver: `~/.config/JetBrains/CLion2026.1/scratches/GitHubCopilot/_internal/s3-fleet.sh`
(`launch N` / `setup` / `run` / `collect` / `kill`; `PHASES`, `ROUND_MIN`, `HASH_PREFIX`,
`UPLOAD_PREFIX`, `SRC_BUCKET`, `SRC_PREFIX` are env-overridable). Operational traps are documented in
`scylla/spot-fleet-setup.md` — **read it before driving a fleet**, it is a list of things that have
each already cost a run.

Full chronology: `s3-throttling-experiment.md`; digest: `s3-throttling-SUMMARY.md`; both in the CLion
scratches `GitHubCopilot/` directory. Note that path is version-pinned and JetBrains *copies*
scratches on upgrade — resolve the newest with
`ls -d ~/.config/JetBrains/CLion*/scratches/GitHubCopilot | sort -V | tail -1`.

## 7. Two related findings you will otherwise rediscover

- **Request amplification is a function of node size.** `chunked_download_source` picks one ranged GET
  vs many 5 MiB GETs from `_buffers_size < _max_buffers_size * _buffers_high_watermark`. More shards
  means more concurrent streams sharing one RAID, buffers stay above the watermark, contiguous mode
  never engages: **1.27 requests/object at 32 shards vs 15.1 at 64 shards**, a ~12x swing driven
  purely by instance size. Neither PR addresses it, and cutting it is arithmetically equivalent to a
  12x larger request budget — the cheapest unexploited lever.
- **PR 30846's hash is in the wrong position.** It builds
  `{prefix}/{hash}/{sstable_id}/{component}`, so entropy sits *after* the static prefix and all keys
  still share leading bytes; S3 partitions by key range from the front. Ernest's experience: randomize
  at the **bucket root** (`{hash}/{prefix}/...`). Caveat if proposing it: a leading hash breaks
  prefix-scoped listing and lifecycle rules for a keyspace/table.
