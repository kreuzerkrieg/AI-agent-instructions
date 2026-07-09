# Production Cluster Investigation — Reference

**Load this file when:** investigating a customer/production ScyllaDB Cloud
(dbaas) cluster — perf issue, stall, disk-space concern, error spike,
incident triage, or a Zendesk/Jira ticket that references a cluster ID.

Companion sub-references:
- `scylla/disk-usage-accounting.md` — for `du` / `df` / metric reconciliation
- `scylla/scylladb_all_metrics_mapping.md` — full metric catalog
- `scylla/sct-instructions.md` — SCT test-run artifacts (different world;
  don't confuse with prod clusters)

---

## 0. Ground Rule — Data First, Narrative Last

**Never write a "situation report" until you've called at least one data
tool.** No timestamps, log lines, ticket numbers, DC names, error messages,
or root-cause claims may appear in a response unless they came from a real
tool call in **this** session. If you have not yet queried anything, the
correct opening is *"I have no data on this cluster yet — querying now"*
followed immediately by the tool calls.

Speculation is allowed but must be prefixed **"Speculation:"** or
**"Hypothesis:"** and kept visually separated from verified facts.

This is a rule with teeth — see the Lessons Learned entry in
`global-agents.instructions.md` (2026-07-08) for the specific failure that
motivated it.

---

## 1. Access Prerequisites

### 1.1 WARP + scylla-cloud-prod VNet (always required)

Every production data source below is behind Cloudflare Zero Trust and
requires **WARP connected with the `scylla-cloud-prod` VNet**:

```bash
warp-cli connect
warp-cli vnet 6666a685-9b3b-4f0c-bd18-36e0ae1c987d
```

For daily use: `warp-login` script (see `scylla/warp-setup.md`).
Symptom of missing VNet: MCP tool returns TLS/connection error or 403.

### 1.2 StrongDM (SSH to nodes)

**Direct SSH into customer/production Scylla nodes is possible via
StrongDM** (SDM). This is the *only* sanctioned path — there is no
public bastion IP, no ssh-key-in-authorized_keys mechanism.

Confluence reference:
<https://scylladb.atlassian.net/wiki/spaces/RND/pages/42238619>

Prerequisites (one-time):
- Email `it@scylladb.com` to be added to the correct Okta group:
  - `SDMSupport-Prod` — production
  - `SDMSupport-Sandbox` — lab / staging
- Install the StrongDM app + CLI. Follow the **EU** installation guide
  (not US). Download page: <https://app.eu.strongdm.com/app/downloads>
- Set `export SDM_DOMAIN=eu.strongdm.com` in your shell profile.
- WARP must be connected before any `sdm` command.

Daily flow (agent-runnable):

```bash
# 1. Log in (opens Okta in browser)
sdm login --email "$USER@scylladb.com"

# 2. List nodes for a specific cluster (cluster id 100 in this example)
sdm access catalog \
  --filter 'tag:Environment=prd' \
  --filter 'name:"/c:100/*"' \
  --timeout 120s

# 3. Request just-in-time access to a node — reason is mandatory
sdm access to "/c:100/r:scylla/<instance-id>/u:support" \
  --reason "investigating <ticket>" --duration 2h

# 4. SSH once approval arrives
sdm ssh "/c:100/r:scylla/<instance-id>/u:support"
```

Resource-name grammar `/c:<cluster>/r:<role>/<instance-id>/u:<user>`:
- `r:` is `scylla`, `manager`, or `monitor`
- `u:` is almost always `support`

Get CQL credentials for a cluster (helper host, not the cluster itself):

```bash
sdm access to /prd/devops/details/u:support --reason "cluster inventory" --duration 1h
sdm ssh /prd/devops/details/u:support -- "show --cluster-id $CLUSTER_ID"
```

Copy files:
- **Host → node:** `base64 -i <file> | sdm ssh ... "base64 -d > /home/support/<file>"`
- **Node → host:** use <https://upload.scylladb.com/> (see the "Handling
  customer files" runbook), not `scp`.

Common issues:
- `Bad server host key: Invalid key length` → add `RSAMinSize 1024` to
  `~/.ssh/config` or pass `-o RSAMinSize=1024`.
- `connection refused` → `sdm ready`; check `is_linked=true`; try
  `telnet strongdm-us-east-1.siren.scylla.cloud 5000`.
- Missing resource → wrong Okta group; email IT.

### 1.3 What we STILL do NOT have

Even with WARP + StrongDM:
- **Customer application-side logs** — the customer's own microservices
  that *drive* Scylla live in the customer's environment. VictoriaLogs
  only carries Scylla's *own* logs (see §2).
- **Zendesk tickets** — no MCP; the user must paste ticket content, or
  use the Zendesk URL in a browser.
- **Customer credentials** — CQL creds for support work come from the
  devops helper via SDM (above), not from the customer.
- **Anything on a non-cloud (self-hosted) cluster** — StrongDM only
  covers ScyllaDB Cloud / dbaas.

Anything requiring the above must be requested from the user; do not
fabricate it.

---

## 2. Available Data Sources

| Source | How to reach it | Good for | NOT for |
|---|---|---|---|
| **Prometheus / Thanos** | `prometheus-mcp` server (Thanos backend, multi-cluster). Scope with `{cluster="#NNNN"}` | Any metric — CPU, disk, memory, per-shard, per-keyspace, per-table, streaming, repair, compaction, cache, IO queue, CQL rates, errors | Log messages, config values, schema, per-request tracing |
| **VictoriaLogs** | `victorialogs` MCP server (LogsQL). Scope with `cluster:"#NNNN"` and time range | **Scylla-side** logs from cluster nodes — `system.log` / journal from `scylla-server`, `scylla-manager-agent`, `scylla-node-exporter`, `scylla-manager`. Error stacks, streaming/repair messages, config dumps at startup, DC/rack topology from log context. **Also holds** control-plane / cloud-orchestration logs. | The customer's own application-side logs (their microservices that query Scylla — those live in the customer's env, we never see them). Anything metric-shaped — use Prometheus. Broad `_time` queries with no filter are expensive |
| **Grafana dashboards** | Browser URL: `https://graphs.backoffice.prd.dbaas.scyop.net/cluster/<ID>/monitor/d/<dashboard>/...` | Visual confirmation, sharing a link with the user | Direct programmatic reads — we can't scrape panels. **Use the underlying PromQL via `prometheus-mcp` instead**, then optionally give the user the panel URL |
| **Backtrace symbolication** | `scylla-backtrace` MCP + `https://backtrace.scylladb.com/api/backtrace` | Turning raw addresses in crash logs into function names + source lines | Anything that isn't a backtrace |
| **ScyllaDB source** (OSS + enterprise) | `scylla-backtrace` MCP + `scylla_build_tools` (`lookup_build_id` / `search_builds`) to resolve build → commit; GitHub MCP `get_file_contents(ref=<tag>)` for `scylladb/scylladb` (OSS) or `scylladb/scylla-enterprise` (private); local clone + `clion-codenav` **only when its checked-out ref matches the customer's version** | Confirming what a metric name means, what an error string is thrown from, what a config flag actually gates — **at the specific version the cluster runs** (see §6 Step 6) | Runtime state of a live cluster. Also: default-branch/master source is misleading when the cluster runs an older enterprise release |
| **GitHub / Jira / Confluence** | GitHub MCP, Atlassian MCP | Linked issues, known-bug lookups, related PRs, past postmortems | Live cluster state |

**Rule of thumb:** if the question is *"what is happening right now / did
happen at time T"*, the answer lives in Prometheus and VictoriaLogs, and
nowhere else you can reach — **unless** you need on-node state (files on
disk, `nodetool` output, live core file, kernel dmesg), in which case
StrongDM SSH (§1.2) is the only path.

---

## 2b. What to Run Once You're SSH'd Into a Node

Everything below assumes `sdm ssh /c:<id>/r:scylla/<inst>/u:support`.
The `support` user has read access + can run `nodetool`; it is not root.

### Filesystem / disk (the class of questions VictoriaLogs+Prometheus can't answer)

```bash
# Root of the drift — what does df say vs Scylla metrics?
df -h /var/lib/scylla
du -xh --max-depth=1 /var/lib/scylla/ | sort -h

# Snapshots (biggest source of `du` vs Prometheus drift)
nodetool listsnapshots

# Coredumps — often bind-mounted on the same volume; a single one can be 10s of GiB
ls -lh /var/lib/systemd/coredump/ 2>/dev/null
coredumpctl list --no-pager 2>/dev/null | tail -20

# Hints on disk (the Scylla metric is in-memory only, not on-disk size)
du -sh /var/lib/scylla/hints /var/lib/scylla/view_hints 2>/dev/null

# Backup staging
du -sh /var/lib/scylla/data/*/*/upload /var/lib/scylla/data/*/*/staging 2>/dev/null

# Orphaned tmp sstables from crashed compactions
find /var/lib/scylla/data -maxdepth 4 \( -name '*-tmp-*' -o -name '*.tmp' \) | head
```

See `scylla/disk-usage-accounting.md` for full reconciliation.

### Scylla runtime state

```bash
nodetool status                   # DC / rack / up-down / ownership
nodetool statusgossip
nodetool describecluster
nodetool tablestats <ks>.<table>  # per-table live/total, tombstones, sstable count
nodetool tpstats                  # per-scheduling-group queues (older Scylla)
nodetool netstats                 # legacy streaming ONLY — RBNO does NOT appear here
nodetool compactionstats -H       # active compactions
nodetool cfhistograms <ks>.<table>
```

### Logs on the node

```bash
journalctl -u scylla-server -n 1000 --no-pager
journalctl -u scylla-server --since "1 hour ago" --no-pager
journalctl -u scylla-manager-agent -n 500 --no-pager

# Older archived logs
ls -la /var/log/scylla/
zcat /var/log/scylla/scylla.log-*.gz | grep -i "error\|backtrace"
```

Prefer VictoriaLogs for cross-node time-range queries; use `journalctl`
on-node only when VictoriaLogs is missing recent lines (rare) or when
correlating with `dmesg` / kernel-side events.

### Kernel / OS

```bash
dmesg -T | tail -100                # oomkills, XFS errors, disk timeouts
uname -a
cat /etc/os-release
top -bn1 -o %CPU | head -30
iostat -xm 2 3                      # if sysstat installed
```

### Config

```bash
sudo cat /etc/scylla/scylla.yaml
sudo cat /etc/scylla.d/*.conf 2>/dev/null    # perftune, io.conf, cpuset.conf
```

### Copying artifacts off the node

- Small text (yaml, log excerpt): `base64` roundtrip through `sdm ssh`.
- Anything binary or large (coredump, sstable): use
  <https://upload.scylladb.com/> per the "Handling customer files"
  runbook. Never `scp` directly.

---

## 4. On-Call Context

When the user is on-call, the origin of the request shapes the workflow.

### Two independent on-call rotations

| Rotation | Owner | Scope | Confluence |
|---|---|---|---|
| **Core Engineer On-Call** | R&D / kernel | Cluster is unresponsive / down, node crashes, correctness bugs, backtrace investigation, performance regressions in the DB itself | <https://scylladb.atlassian.net/wiki/spaces/RND/pages/20512806> |
| **Cloud On-Call** | Cloud R&D | Provisioning failures, scaling failures, VPC / PrivateLink / connectivity, backoffice, siren, control-plane | <https://scylladb.atlassian.net/wiki/spaces/RND/pages/359596587> |

Tier structure (both rotations):
- **Tier 1** — first responder (rotating).
- **Tier 2** — R&D directors (weekly rotation, Mon 09:00 Jerusalem for
  Core / 09:00 CET for Cloud).
- **Tier 3** — CTO (Core only; only if all else fails).

### Where pages come from

- **DataDog On-Call** manages shifts and paging (phone, SMS, mobile
  push, email). Log in via Okta.
- **Slack war rooms** — join the channel named in the page. General:
  **`#0_p1_war_room`** (Cloud) — every incident gets its own
  `#inc-zd<ticket>-<customer>-<summary>` channel.
- **Jira** — page title usually includes the ticket key
  (`CUSTOMER-NNN`, `SRE-NNN`).
- **Zendesk** — the customer-facing ticket ID (`ZD-<NNNNN>`); the CX
  focal point owns the customer comms, not us.

### First-15-minutes checklist (for the agent to help with)

1. Extract from the page: **cluster ID, ticket key, Slack channel, CX
   focal point**. If any are missing, ask before doing analysis.
2. `cluster_profile(cluster_id="#NNNN")` to confirm the cluster exists
   and see topology.
3. Read the Jira ticket for prior context — `mcp_atlassian_fetch` with
   the issue ARI. Existing bugs, past investigations, related tickets.
4. Grep VictoriaLogs for `error`/`warn` in the incident window on that
   cluster.
5. Symptom metric per §6 workflow.
6. Post findings into the incident's Slack channel (user posts; agent
   drafts). Cite queries.

### What NOT to do

- **Don't invent ticket IDs or cluster IDs to fill in a template.** Real
  IDs collide with real tickets (see 2026-07-08 lesson).
- **Don't ping SMEs or Tier 2 without the user's OK** — escalation is
  the user's decision, not the agent's.
- **Don't apply fixes, restart services, or change config from an SSH
  session without explicit user confirmation for that specific action.**
  Investigation is read-mostly; mutations are the on-call engineer's
  call.

---

## 5. Finding the Cluster

The user will usually give one of:
- **Cluster ID** — `#6958`, `6958`. Use as `{cluster="#6958"}` in PromQL
  (the `#` prefix is part of the label value in Thanos).
- **Grafana URL** — extract the cluster ID from `/cluster/<ID>/monitor/`.
- **Just a customer/ticket name** — ask for the cluster ID. Do not guess.

Sanity-check the cluster exists before doing real work:

```
mcp_prometheus-mc_cluster_profile(cluster_id="#6958")
```

This returns DCs, active service levels, and enabled features (Alternator,
CDC, CAS) in one round-trip. Cheap, fast, and immediately reveals if the
cluster ID is wrong (empty result).

---

## 4. Investigation Workflow (Default Path)

Follow this ordering unless the user's question demands a different one:

### Step 1 — Cluster profile (always)
`cluster_profile(cluster_id=...)` — DCs, features, service levels. Anchors
the investigation.

### Step 2 — Resolve the time window
User says "yesterday afternoon" / "last hour" / "since 14:00 UTC".
Translate to explicit `start` / `end` UNIX timestamps with
`resolve_time_window`. Everything downstream uses these.

### Step 3 — Symptom metric
Query the metric that reflects the user's complaint:
- "slow reads" → `scylla_storage_proxy_coordinator_read_latency`
  histograms, `scylla_reactor_utilization`
- "high CPU" → `scylla_reactor_utilization`, scheduling-group breakdown
- "disk full" → `scylla_node_filesystem_avail_bytes` per `mountpoint`
- "streaming stuck" → `scylla_streaming_total_incoming_bytes`,
  `scylla_repair_row_from_disk_bytes`
- Unknown metric name → `metrics_search(text="...")` first, don't guess.

### Step 4 — Narrow the anomaly window
For long time ranges, `promql_find_anomaly_windows` returns only the spans
where the metric was above a threshold — much cheaper than raw range
queries.

### Step 5 — Correlate with logs
Take the narrowed window and query `victorialogs` for the same `cluster` +
time range with keyword filters (`error`, `warn`, subsystem name).
**Always** narrow by both cluster and time — unbounded LogsQL queries are
slow and hit rate limits.

### Step 6 — Verify against source **at the exact version the customer runs**
If a specific error string, metric behaviour, or config default drives
the conclusion, confirm what emits it — but **never against `master` of
the local checkout by default**. Customers run enterprise releases
(2024.1.x, 2025.1.x, …), older OSS branches (6.0.x, 6.2.x, …), or
occasionally a private build. The behaviour you're chasing may not
exist there, or may exist with different semantics.

**Procedure:**

1. **Find the version the cluster actually runs.** Any of:

   ```promql
   # Version + build id from Prometheus (label values)
   scylla_scylla_build_info{cluster="#NNNN"}
   ```

   or the value of `scylla_versions` / a startup line in VictoriaLogs
   (`Scylla version 2025.1.9-... with build-id abc123...`), or on an
   SSH'd node `scylla --version` / `nodetool version`.

2. **Resolve `build_id` → git commit** with the ScyllaDB build MCP
   (category: `activate_scylla_build_tools`):

   ```
   lookup_build_id(build_id="<40-hex>")   → package URL, parent build metadata (incl. git SHA)
   search_builds(release="2025.1.9", ...) → find builds by release string
   ```

   This tells you the exact commit/tag the running binary was built
   from.

3. **Read source at that commit** — pick the cheapest tool for the job:

   - **GitHub MCP** `get_file_contents(owner, repo, path, ref=<tag|sha|branch>)`
     — no checkout needed, works on private `scylladb/scylla-enterprise`
     too. Best for reading a specific known file.
   - **GitHub MCP** `search_code(q="...", ref not settable)` — repo-wide
     grep, but only searches the default branch. **Do not use it as
     version-specific verification.**
   - **Local checkout at the right ref** — only when doing heavy
     multi-file navigation. Fetch and checkout the tag/branch:
     `git fetch --tags && git checkout <tag>`. Note that
     `~/Development/scylladb` is OSS only; enterprise sources need a
     separate clone of `scylladb/scylla-enterprise`.
   - **`clion-codenav` MCP** — semantic navigation, but **only against
     the currently-open workspace**. Only useful if the workspace's
     current branch matches the customer's version. Otherwise misleading.

4. **Branch-name conventions** (as of writing — verify with
   `list_branches` if unsure):

   | Product | Repo | Branch pattern |
   |---|---|---|
   | Enterprise | `scylladb/scylla-enterprise` (private) | `enterprise-2024.1`, `enterprise-2025.1`, tags like `enterprise-2025.1.9` |
   | OSS | `scylladb/scylladb` | `branch-6.0`, `branch-6.2`, tags like `scylla-6.2.3` |
   | Manager | `scylladb/scylla-manager` | `branch-3.x` |

5. **State the version in the finding.** Any claim from source must
   name the ref: *"In `scylladb/scylla-enterprise` at tag
   `enterprise-2025.1.9`, `stream_manager.cc:344` throws …"*. A
   version-less "the code does X" claim is worthless in a customer
   investigation.

**Anti-pattern (from prior sessions):** grepping `~/Development/scylladb`
(OSS master) for an error string, finding it, and citing line numbers —
when the customer runs enterprise 2024.1. The file may not exist at all
in that version, may be at a different path, or the surrounding logic
may differ.

### Step 7 — Report
Present verified facts with the query/tool that produced them. Any
inference goes under an explicit **Speculation:** heading.

---

## 5. Grafana Dashboard → PromQL Mapping

We can't read Grafana panels programmatically, but the user can paste the
URL and describe the panel. Common panels on `dbaas` that trip people up:

| Dashboard row / panel label | Underlying metric family | Common misread |
|---|---|---|
| **Memory: Total / Used Bytes (Sum by Instance)** | `scylla_lsa_total_space_bytes` / `scylla_lsa_used_space_bytes` | **RAM** (LSA pool), not disk. Panel titles don't say "memory" clearly |
| Disk Space / SSTable Size | `scylla_column_family_live_disk_space` | Per-shard × per-table; sum by instance for node total |
| Filesystem Used | `scylla_node_filesystem_size_bytes - scylla_node_filesystem_avail_bytes` | Sum across mounts double-counts bind mounts (see disk-accounting doc) |
| Cache Hits/Misses | `scylla_cache_partition_hits` / `scylla_cache_partition_misses` | Rates, not absolute counts |
| CPU / Reactor | `scylla_reactor_utilization` | Per-shard fraction; not directly comparable to host CPU |

**Before interpreting any panel** the user references: ask them to open
the panel's Edit view and paste the PromQL, or read the metric name from
`metrics_search`. Never assume from the label.

Standard `dbaas` production Grafana URL shape:
```
https://graphs.backoffice.prd.dbaas.scyop.net/cluster/<ID>/monitor/d/<dashboard>/<slug>?...&var-cluster=%23<ID>&...
```
- `%23` is `#` URL-encoded.
- `var-by=instance` groups by node; `var-sg=sl:default` filters
  scheduling group; `var-shard=$__all` includes all shards.

---

## 6. Common Anti-Patterns (and What to Do Instead)

### A. "Sum across everything"
`sum(scylla_column_family_live_disk_space)` gives the RF-multiplied
cluster total across all shards. Almost never what you want.
**Do:** aggregate deliberately — `sum by (instance) (...)` for
per-node, then think about RF explicitly.

### B. "Panel label = metric semantics"
Panels labelled "Bytes" / "Space" / "Used" can be any of memtable RAM,
LSA pool, live sstables, total sstables, filesystem usage, or free
space. Always confirm the metric.

### C. "One node is representative"
`dbaas` clusters routinely mix instance types — service nodes with 300 MB
of RAM alongside data nodes with 96 GB. `topk` /
`bottomk` per-instance breakdowns are essential; `avg` and cluster-wide
sums can mislead.

### D. "Metric absent = feature disabled"
Some metrics are only emitted when the subsystem is active (e.g.
compaction manager during compaction, streaming during operations). A
missing series may just mean idle. Confirm with `cluster_profile` or
by querying a related always-on metric.

### E. "`nodetool netstats` is authoritative"
It reports the legacy streaming subsystem. **RBNO (Repair-Based Node
Operations) does not show up there** — cross-check with
`scylla_repair_row_from_disk_bytes` and
`scylla_streaming_total_incoming_bytes` in Prometheus.

### F. "Log grep with no time bound"
VictoriaLogs across all time × all clusters is slow. Always include
`cluster:"#NNNN"` and `_time:[start, end]` (or the tool's native
range parameters).

### G. "Grep master, cite line numbers"
The customer runs a specific released version (enterprise-2025.1.9,
OSS 6.2.3, …). Grepping `~/Development/scylladb` at `master` and
quoting line numbers is misleading — the code may not exist there, be
at a different path, or have different logic. Always: (1) find the
customer's build_id via Prometheus / log / `nodetool version`,
(2) resolve to a commit via `lookup_build_id`, (3) read the file at
that ref via GitHub MCP `get_file_contents`. See §6 Step 6.

---

## 7. Backtrace Decoding (Crashes)

When a log line contains `Backtrace:` followed by raw addresses:

1. Find the `build_id` (search source log for `Build ID:` or query the
   `scylla_scylla_build_info` label).
2. Send the raw lines to `scylla-backtrace` MCP or POST to
   `https://backtrace.scylladb.com/api/backtrace` (see
   `scylladb-instructions.md` for the curl form).
3. Read the symbolized `stdout` field for function names + source lines.

**Never analyse a crash from raw addresses** — the build offset varies
per release.

---

## 8. Metric Discovery Aids (Prometheus MCP)

Don't guess metric names — the catalog is annotated:

- `metrics_search(text="repair progress")` — free-text over name,
  description, and enriched semantic fields.
- `metrics_catalog(prefix="scylla_streaming_")` — enumerate a namespace.
- `metrics_catalog(semantic_role="symptom", observed_problem="read_latency")`
  — find symptom metrics for a specific problem class.
- `metrics_catalog(related_to="scylla_reactor_utilization")` — find
  related/diagnostic metrics.

The enriched catalog also encodes **problem mappings** (what does
"elevated X mean") and **caveats** (known misinterpretations). Read them
before drawing conclusions from an unfamiliar metric.

---

## 9. Reporting Format

For any non-trivial investigation the response should include:

1. **What was asked** — one line restating the question so the user
   knows we understood it.
2. **Cluster context** — ID, DC count, notable features (from
   `cluster_profile`).
3. **Findings** — bulleted, each with the metric / log / source that
   produced it. Include the PromQL or LogsQL when the user might want to
   re-run it.
4. **Speculation** (if any) — clearly separated section.
5. **Next actions** — what to check next, or what to ask the customer.

Avoid stacking hypotheses. If you don't know, say so and propose the
next query.

---

## 10. Interaction with `disk-usage-accounting.md`

For any question involving disk space, `du`, `df`, or the mismatch
between filesystem view and Scylla-reported bytes, defer to
`scylla/disk-usage-accounting.md`. It covers:
- Which categories Scylla metrics report and which they don't
- The LSA-vs-disk panel confusion
- Multi-mount and per-shard summing traps
- A concrete PromQL recipe for `du` vs Prometheus reconciliation






