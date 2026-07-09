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

Every production data source below is behind Cloudflare Zero Trust and
requires **WARP connected with the `scylla-cloud-prod` VNet**:

```bash
warp-cli connect
warp-cli vnet 6666a685-9b3b-4f0c-bd18-36e0ae1c987d
```

For daily use: `warp-login` script (see `scylla/warp-setup.md`).
Symptom of missing VNet: MCP tool returns TLS/connection error or 403.

**What we do NOT have access to:**
- SSH to any customer node — no direct `nodetool`, `du`, `ls`,
  `journalctl`, filesystem inspection.
- The customer's application logs.
- Zendesk tickets (no MCP yet — user must paste content).
- Any credential belonging to the customer.

Anything requiring the above must be requested from the user; do not
fabricate it.

---

## 2. Available Data Sources

| Source | How to reach it | Good for | NOT for |
|---|---|---|---|
| **Prometheus / Thanos** | `prometheus-mcp` server (Thanos backend, multi-cluster). Scope with `{cluster="#NNNN"}` | Any metric — CPU, disk, memory, per-shard, per-keyspace, per-table, streaming, repair, compaction, cache, IO queue, CQL rates, errors | Log messages, config values, schema, per-request tracing |
| **VictoriaLogs** | `victorialogs` MCP server (LogsQL). Scope with `cluster:"#NNNN"` and time range | Actual `system.log` / journal lines, error stacks, streaming/repair messages, config dumps at startup, DC/rack topology from log context | Anything metric-shaped — use Prometheus instead. Broad `_time` queries with no filter can be very expensive |
| **Grafana dashboards** | Browser URL: `https://graphs.backoffice.prd.dbaas.scyop.net/cluster/<ID>/monitor/d/<dashboard>/...` | Visual confirmation, sharing a link with the user | Direct programmatic reads — we can't scrape panels. **Use the underlying PromQL via `prometheus-mcp` instead**, then optionally give the user the panel URL |
| **Backtrace symbolication** | `scylla-backtrace` MCP + `https://backtrace.scylladb.com/api/backtrace` | Turning raw addresses in crash logs into function names + source lines | Anything that isn't a backtrace |
| **ScyllaDB source** | Local clone `~/Development/scylladb` + `clion-codenav` MCP | Confirming what a metric name means, what an error message string is thrown from, what a config flag actually gates | Runtime state of a live cluster |
| **GitHub / Jira / Confluence** | GitHub MCP, Atlassian MCP | Linked issues, known-bug lookups, related PRs, past postmortems | Live cluster state |

**Rule of thumb:** if the question is *"what is happening right now / did
happen at time T"*, the answer lives in Prometheus and VictoriaLogs, and
nowhere else you can reach.

---

## 3. Finding the Cluster

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

### Step 6 — Verify against source
If a specific error string or metric behaviour drives the conclusion,
confirm what emits it: `grep_search` the local `scylladb` clone or use
`clion-codenav` to find the enclosing function. Don't infer from the
name alone.

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

