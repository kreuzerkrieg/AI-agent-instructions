# SCT (Scylla Cluster Tests) — Agent Instructions

**Location:** `~/.config/github-copilot/intellij/scylla/sct-instructions.md`
**Referenced from:** `~/.config/github-copilot/intellij/global-agents-instructions.md` (ScyllaDB Ecosystem table)
**Purpose:** SCT-specific conventions, analysis workflows, and metric mappings that supplement the repo-level `.github/copilot-instructions.md`.

---

## SCT Run Log Analysis

### Run Identification
Every SCT run produces logs with a consistent **8-character hex suffix** (e.g., `2730e03d`). All files from the same run share this suffix. **Always verify suffix consistency** across all downloaded files — if any file has a different suffix, warn the user immediately.

### File Inventory (typical download from Argus)
Each run produces 8 standard archives, plus optional core dump files when crashes occur:

| Archive | Contents | Key Files |
|---------|----------|-----------|
| `sct-<id>.log.tar.zst` | Main SCT framework log | Single large log with full test lifecycle |
| `sct-runner-events-<id>.tar.zst` | Event logs by severity | `events.log`, `error.log`, `critical.log`, `warning.log`, `summary.log` |
| `db-cluster-<id>.tar.zst` | DB node logs (per node) | `system.log`, `scylla.yaml`, `mem_info`, `scylla_doctor.vitals.json` |
| `loader-set-<id>.tar.zst` | Loader/stress logs | `cql-stress-*` logs with 5-sec interval samples |
| `monitor-set-<id>.tar.zst` | Monitoring stack | `prometheus_data_*.tar.zst`, Grafana screenshots, manager logs |
| `schema-logs-<id>.tar.zst` | CQL schema snapshots | `schema.log`, `schema_with_internals.log` |
| `ssl-conf-<id>.tar.zst` | TLS certificates | Per-node certs, CA, truststores |
| `builder-<id>.log.tar.gz` | Builder machine journal | Low analysis value |
| `core.scylla.*.zst` | Compressed core dumps (optional) | One file per crash — see "Core Dump Files" below |

#### Core Dump Files (when present)

When ScyllaDB crashes during a run, `systemd-coredump` captures core dumps which SCT uploads to `upload.scylladb.com` and also saves locally. These files appear alongside the standard archives with filenames like:

```
core.scylla.<uid>.<boot_id>.<pid>.<timestamp_usec>._core.scylla.<uid>.<boot_id>.<pid>.<timestamp_usec>.zst
```

**Filename components:**
- `<uid>` — UID of the scylla user (typically `106`)
- `<boot_id>` — systemd boot ID (32-char hex) — maps to a specific node
- `<pid>` — PID of the crashed scylla process
- `<timestamp_usec>` — crash timestamp in microseconds since epoch

**Mapping core dumps to nodes:** The `<boot_id>` in the filename maps to a specific node. Search the SCT log for the boot ID to find the node name:
```bash
grep '<boot_id>' sct-<id>.log | head -3
```

**Important:** When `db-cluster-<id>.tar.zst` is **not present** (e.g., user downloaded only selected files from Argus), the core dump `coredumpctl info` output is still available in the SCT main log under `CoreDumpEvent` entries. Search for it:
```bash
grep -A 100 'CoreDumpEvent.*backtrace=' sct-<id>.log | head -120
```

**Typical core dump sizes:** 20 MB–500 MB compressed (depends on shard memory usage at crash time).

### Detailed Archive Contents

#### `sct-<id>.log.tar.zst` — SCT Framework Log
Single file, typically 20–100 MB. Contains:
- Full test lifecycle: provisioning, setup, stress start/end, teardown
- Cluster events, node status changes
- Argus result submissions (contains I/O stats, data sizes, adaptive timeout results)
- `cfstats` command output (may be embedded in debug-level lines)
- Search for `"Submitting.*results to Argus"` to find node-level I/O stats (read/write bandwidth, IOPS, data size)

#### `sct-runner-events-<id>/` — Event Logs
| File | Description |
|------|-------------|
| `events.log` | **All events chronologically** — best single file for test flow overview |
| `normal.log` | NORMAL severity: YAML changes, stress start/end, nodetool, health checks |
| `warning.log` | TLS disconnect, RPC connection drops (usually benign teardown noise) |
| `error.log` | Errors — **empty = clean run** |
| `critical.log` | Critical failures — **empty = clean run** |
| `output.log` | Verbose stress command output, cfstats |
| `raw_events.log` | Machine-readable JSON event stream |
| `argus.log` | Argus test tracking integration |
| `debug.log` | Debug-level events |
| `actions.log` | Test action markers |
| `left_processes.log` | Processes still running at teardown |
| `summary.log` | `{"NORMAL": N, "WARNING": N, "DEBUG": N, "ERROR": N}` |

#### `db-cluster-<id>/` — DB Node Logs
One subdirectory per node: `<test-name>-db-node-<id>-{1..N}/`
Each node directory contains:

| File | Size (typical) | Use |
|------|---------------|-----|
| `system.log` | 2–35 MB | **Primary** — ScyllaDB server log: compaction, raft, tablet ops, reactor stalls, errors |
| `messages.log` | 1–18 MB | OS syslog (journald) — OOM, disk errors, kernel issues |
| `scylla.yaml` | ~10 KB | Scylla config snapshot — verify cluster settings |
| `scylla-manager-agent.yaml` | ~1 KB | Manager agent config |
| `cassandra-rackdc.properties` | ~100 B | Rack/DC assignment |
| `io-properties.yaml` | ~500 B | Disk I/O characteristics (read/write bandwidth, IOPS) |
| `cpu_info` | ~15 KB | `/proc/cpuinfo` |
| `mem_info` | ~3 KB | `/proc/meminfo` at collection time |
| `vmstat` | ~2 KB | Virtual memory statistics |
| `interrupts` | ~20 KB | `/proc/interrupts` — IRQ distribution |
| `dmesg.log` | ~100 KB | Kernel ring buffer |
| `cloud-init.log` | ~200 KB | Instance bootstrap |
| `cloud-init-output.log` | ~50 KB | Cloud-init output |
| `coredumps.info` | ~100 B | Core dump status (contains BuildID for backtrace decoding) |
| `systemctl.status` | ~5 KB | Full service status tree |
| `setup_scripts_errors.log` | ~0 B | SCT setup script errors (empty = clean) |
| `scylla_doctor.vitals.json` | ~5 KB | Automated health assessment |
| `client-facing.crt`, `db.crt` | ~2 KB each | TLS certificates |
| `cqlshrc` | ~200 B | CQL shell config |
| `kallsyms_*` | ~10 MB each | Kernel symbol table (for backtrace symbolization) |

**Key searches in `system.log`:**
```bash
grep "Reactor stalled" system.log        # Reactor stalls (latency spikes)
grep -c "compaction" system.log          # Compaction activity volume
grep -i "tablet" system.log | head       # Tablet migration operations
grep -i "error\|abort\|exception" system.log | head  # Errors
grep -i "s3\|object.store" system.log    # Object store operations (may need trace-level logging)
```

#### `loader-set-<id>/` — Loader Logs
Top-level copies + per-node subdirectories: `<test-name>-loader-node-<id>-{1..N}/`

**Stress log files** follow this naming pattern:
```
cql-stress-cassandra-stress-<op>-l<loader>-c<cpu>-k<ks>-<date>-<uuid>.log
```
Where `<op>` = `write` or `read`, `<loader>` = loader number (1, 2, ...).

A single loader may have **multiple stress log files** if the test runs multiple stress phases:
- First write phase (pre-populate)
- Second write phase (main workload)
- Read phase
- Mixed read/write phase

**Stress log internal structure:**
```
[timestamp] TAG: loader_idx:N-cpu_idx:N-keyspace_idx:N      ← identifier line
[timestamp] ******************** Stress Settings ********************
[timestamp]   Type: write/read                                ← operation type
[timestamp]   Count: 20000000                                 ← total operations
[timestamp]   Consistency Level: Quorum
[timestamp] Rate:
[timestamp]   Thread count: 80
[timestamp] Column:
[timestamp]   Size distribution: FIXED(512)
[timestamp] ...
[timestamp] total ops ,    op/s,    mean,     med,     .95,     .99,    57.9,   433.6,    5.0,      0
[timestamp]    435409,   49261,     1.6,     1.2,     3.6,     6.4,    22.0,    30.3,   10.0,      0
...                                                           ← 5-second interval samples
[timestamp] Results:
[timestamp] Op rate                   :    66693 op/s
[timestamp] Latency mean              :    1.2 ms
[timestamp] Latency median            :    0.9 ms
[timestamp] Latency 95th percentile   :    2.2 ms
[timestamp] Latency 99th percentile   :    7.4 ms
[timestamp] Latency 99.9th percentile :   20.8 ms
[timestamp] Latency max               : 1498.4 ms
[timestamp] Total operations          :   20000000
[timestamp] Total errors              :          0
[timestamp] Total operation time      : 00:04:59
```

**Parsing 5-sec samples:**
```bash
# Extract raw CSV data (strip timestamps)
grep -E '^\[2026.*\]\s+[0-9]+,' <stress-log> | sed 's/^\[.*\] //'
```

Also contains per-loader: `messages.log`, `system.log`, `cloud-init.log`

#### `monitor-set-<id>/` — Monitoring Stack
Per-monitor-node subdirectory: `<test-name>-monitor-node-<id>-1/`

| File | Size | Description |
|------|------|-------------|
| `prometheus_data_<date>.tar.zst` | 4–50 MB | **Prometheus TSDB snapshot** — full time-series metrics |
| `monitoring_data_stack_*.tar.gz` | 20–30 MB | Complete monitoring stack (Grafana dashboards, Prometheus rules) |
| `grafana-screenshot-overview-*.png` | ~850 KB | Grafana overview dashboard screenshot |
| `grafana-screenshot-*-per-server-metrics-*.png` | ~1 MB | Per-server metrics screenshot |
| `aprom.log` | varies | Prometheus container log |
| `agraf.log` | varies | Grafana container log |
| `aalert.log` | varies | Alertmanager container log |
| `scylla_manager.log` | varies | Scylla Manager log |
| `manager_scylla_backend.log` | ~1 MB | Manager backend operations |
| `scylla-manager.yaml` | ~1 KB | Manager config |
| `messages.log`, `system.log` | varies | Monitor node OS logs |

#### `schema-logs-<id>/` — Schema Snapshots
| File | Description |
|------|-------------|
| `schema.log` | CQL `DESC SCHEMA` output — user-visible keyspaces/tables |
| `schema_with_internals.log` | Schema including internal system tables |
| `system_schema_tables.log` | `SELECT JSON * from system_schema.tables` |
| `system_truncated.log` | Truncation status |

#### `ssl-conf-<id>/` — TLS Configuration
Per-node certificates (one directory per IP), CA key/cert, client certificates, JKS truststores. Rarely needed for analysis.

#### `builder-<id>.log.tar.gz` — Builder Journal
System journal from the CI builder machine. Contains Docker setup, image pulls, SSM agent. **Low analysis value.**

---

## Extracting Cluster Topology & Node Setup

When analyzing an SCT run, the **first step** is to build a picture of the cluster: how many nodes, what hardware, what config. Here's where each piece of information lives.

### 1. SCT Config Parameters (from `sct-<id>.log`)

The SCT framework dumps all config parameters early in the log via `sct_config.py`. Extract key topology values:

```bash
grep -E "sct_config.*> (instance_type_db|instance_type_loader|instance_type_monitor|n_db_nodes|n_loaders|n_monitor_nodes|cluster_backend|availability_zone|scylla_version|nemesis_class|nemesis_selector|stress_cmd|num_tokens|tablets)" sct-<id>.log | head -20
```

**Key parameters:**

| Parameter | Meaning | Example |
|-----------|---------|---------|
| `instance_type_db` | AWS instance type for DB nodes | `i4i.4xlarge`, `i4i.xlarge` |
| `instance_type_loader` | AWS instance type for loaders | `c6i.xlarge` |
| `instance_type_monitor` | AWS instance type for monitor | `t3.large` |
| `n_db_nodes` | Number of DB nodes | `6` |
| `n_loaders` | Number of loader machines | `2` |
| `n_monitor_nodes` | Number of monitor nodes | `1` |
| `cluster_backend` | Cloud provider | `aws`, `gce`, `azure`, `docker` |
| `availability_zone` | AZ suffix | `c` → `us-east-1c` |
| `scylla_version` | ScyllaDB version (may be empty if using AMI) | `2026.2.0~dev` |

### 2. Per-Node Hardware (from `db-cluster-<id>/<node>/`)

#### CPU — `cpu_info`
```bash
# CPU model and core count
grep "model name" cpu_info | head -1
grep "cpu cores" cpu_info | head -1    # physical cores per socket
grep "siblings" cpu_info | head -1      # logical CPUs (with HT)
grep -c "^processor" cpu_info           # total vCPUs
```

#### Memory — `mem_info`
```bash
grep -E "MemTotal|MemAvailable|SwapTotal" mem_info
# MemTotal in kB → divide by 1048576 for GB
```

#### Disk I/O — `io-properties.yaml`
Contains measured I/O characteristics for `/var/lib/scylla`:
```yaml
disks:
- mountpoint: /var/lib/scylla
  read_bandwidth: 3087631104    # bytes/sec (~2.9 GB/s)
  read_iops: 385400
  write_bandwidth: 2289281280   # bytes/sec (~2.1 GB/s)
  write_iops: 240628
```
These values are from Scylla's `iotune` benchmark run at setup — they represent the **disk's raw capability**, not runtime usage.

#### Rack/DC — `cassandra-rackdc.properties`
```properties
dc = us-east-1
rack = RACK0
prefer_local = true
```
Extract rack distribution across all nodes:
```bash
for d in db-cluster-<id>/*-db-node-*/cassandra-rackdc.properties; do
  node=$(basename $(dirname "$d"))
  rack=$(grep "^rack" "$d" | cut -d= -f2 | tr -d ' ')
  echo "$node → $rack"
done
```
Typical pattern: 6 nodes across 3 racks = 2 nodes per rack.

### 3. Scylla Configuration — `scylla.yaml`

**Important settings to check:**

| Setting | What it tells you |
|---------|-------------------|
| `cluster_name` | Full cluster identifier with test name and run ID |
| `num_tokens` | Token ring configuration (256 = default) |
| `tablets_mode_for_new_keyspaces` | `enabled` → tablets active for new keyspaces |
| `experimental_features` | Feature flags (e.g., `keyspace-storage-options`, `views-with-tablets`) |
| `client_encryption_options.enabled` | TLS for client connections |
| `server_encryption_options.internode_encryption` | `all` = full internode TLS |
| `object_storage_endpoints` | S3/GCS endpoint config (for tiered storage) |
| `kms_hosts` | KMS encryption at rest config |
| `system_info_encryption.enabled` | System table encryption |
| `user_info_encryption.enabled` | User table encryption |
| `read_request_timeout_in_ms` | Read timeout (default 5000) |
| `write_request_timeout_in_ms` | Write timeout (default 2000) |
| `stream_io_throughput_mb_per_sec` | Streaming bandwidth limit |
| `commitlog_sync` | `periodic` (default) or `batch` |
| `commitlog_sync_period_in_ms` | Flush interval (default 10000) |
| `sstable_format` | `ms` (modern), `me`, etc. |
| `endpoint_snitch` | Snitch type (usually `GossipingPropertyFileSnitch`) |
| `audit` | `table` = audit logging enabled |

**Quick extraction of non-default settings:**
```bash
# All top-level settings (skip comments, blank lines, nested items)
grep -E "^[a-z]" scylla.yaml
```

### 4. Replication Factor & Keyspace Config — `schema-logs-<id>/schema.log`

```bash
grep "CREATE KEYSPACE" schema.log
```
Output shows replication strategy, RF, storage backend, and tablet config:
```sql
CREATE KEYSPACE keyspace1 WITH replication = {
  'class': 'NetworkTopologyStrategy', 'us-east-1': ['RACK1', 'RACK2', 'RACK0']
} AND storage = {'type': 'S3', 'bucket': '...'} AND tablets = {'enabled': true};
```
- `'us-east-1': ['RACK1', 'RACK2', 'RACK0']` → RF=3 (one replica per rack)
- `storage = {'type': 'S3'}` → S3-backed (object store)
- `tablets = {'enabled': true}` → using tablets, not vnodes

### 5. Node IP-to-Rack Mapping

Combine `scylla.yaml` (broadcast_address) + `cassandra-rackdc.properties`:
```bash
for d in db-cluster-<id>/*-db-node-*/; do
  ip=$(grep "^broadcast_address:" "$d/scylla.yaml" | awk '{print $2}')
  rack=$(grep "^rack" "$d/cassandra-rackdc.properties" | cut -d= -f2 | tr -d ' ')
  echo "$(basename $d): $ip → $rack"
done
```

### Quick Cluster Summary Template

When starting analysis, always build this summary first:

```
Cluster: <cluster_name>
Backend: <aws/gce/azure/docker>
DB Nodes: <N> × <instance_type> (<vCPUs> vCPU, <RAM> GB, <disk_type>)
  Racks: <RACK0: nodes>, <RACK1: nodes>, <RACK2: nodes>
Loaders: <N> × <instance_type>
Monitor: <N> × <instance_type>
ScyllaDB: <version>
Keyspace: <name>, RF=<N>, strategy=<NTS>, storage=<local/S3>
Tablets: <enabled/disabled>
Encryption: client=<yes/no>, internode=<yes/no>, at-rest=<yes/no>
Features: <experimental_features list>
```

---

### Triage Order
1. **`sct-runner-events-<id>/error.log`** — check for errors first (empty = clean run)
2. **`sct-runner-events-<id>/summary.log`** — JSON with event counts by severity
3. **`sct-runner-events-<id>/events.log`** — chronological test flow
4. **Stress logs** — throughput/latency timelines
5. **DB node `system.log`** — compaction, reactor stalls, errors
6. **Prometheus data** — deep metric analysis

### Stress Log Format (cql-stress-cassandra-stress)
The `cql-stress-*` logs contain 5-second interval samples with columns:
```
total_ops, interval_ops, latency_mean, latency_median, latency_95th, latency_99th, latency_99.9th, latency_max, elapsed_time, errors
```
All latency values are in **milliseconds**. Final results appear after a `Results:` line at the end of the file.

---

## Prometheus TSDB Analysis

### Setup
```bash
# Extract Prometheus snapshot
tar --zstd -xf prometheus_data_*.tar.zst -C /tmp/prometheus_<id>/

# Create WAL directory (required by promtool)
mkdir -p /tmp/prometheus_<id>/<snapshot_dir>/wal

# Download promtool if not available
curl -sL https://github.com/prometheus/prometheus/releases/download/v3.3.1/prometheus-3.3.1.linux-amd64.tar.gz | tar xz prometheus-3.3.1.linux-amd64/promtool
```

### Querying Metrics
```bash
# List all metric names containing a keyword
promtool tsdb dump <tsdb_dir> 2>/dev/null | grep -oP '__name__="[^"]*cache[^"]*"' | sort -u

# Dump specific metric
promtool tsdb dump --match='{__name__="scylla_cache_row_hits"}' <tsdb_dir> 2>/dev/null > /tmp/metric.txt
```

### Instance Label Formats
The `instance` label varies between monitoring configurations:
- Some runs: `10.12.x.x:9180` (with port)
- Some runs: `10.12.x.x` (bare IP)

**Always check** `head -1` of a dump file before filtering by instance format.

---

## Decoding Backtraces from SCT Logs

When a ScyllaDB node crashes (SEGV, abort, assertion failure) during an SCT run, the `system.log` for that node contains a raw backtrace with hex addresses. These must be symbolized to be useful.

### Finding the Build ID

The build ID is available in multiple places:

1. **`coredumps.info`** in the node's directory (`db-cluster-<id>/<node>/coredumps.info`):
   ```
   BuildID[sha1]=811da1e18fd6e0ff1b07f6fb0a8da797f1b526d6
   ```
2. **SCT run metadata** — the test runner typically records the build ID in the main SCT log.
3. **User-provided** — the build ID is often part of the test run context (e.g., from Argus or CI).

### Extracting Raw Backtraces from `system.log`

Backtraces in ScyllaDB logs look like:
```
2026-04-27T10:15:32.404  INFO | scylla[35648] Backtrace:
2026-04-27T10:15:32.404  INFO | scylla[35648]   0x55c6e07
2026-04-27T10:15:32.404  INFO | scylla[35648]   0x1a68df4
2026-04-27T10:15:32.404  INFO | scylla[35648]   /opt/scylladb/libreloc/libc.so.6+0x1a28f
```

Extract the backtrace block:
```bash
# Find all backtrace locations in a node's system.log
grep -n "Backtrace:" system.log

# Extract a specific backtrace (from "Backtrace:" until the next non-address line)
sed -n '/Backtrace:/,/^[^0-9 ]/p' system.log | head -50
```

### Symbolizing via Remote Service

Send the raw backtrace with the build ID to the symbolization API:

```bash
# 1. Extract raw backtrace lines from system.log into a variable
#    (join with \r\n as the API expects)
BT_INPUT=$(grep -A 200 "Backtrace:" system.log | head -50 | sed ':a;N;$!ba;s/\n/\\r\\n/g')

# 2. Send to symbolization service
curl -s -X POST https://staging.backtrace.scylladb.com/api/backtrace \
  -H "Content-Type: application/json" \
  -d "{
    \"build_id\": \"<BUILD_ID_HEX>\",
    \"input\": \"$BT_INPUT\"
  }" | python3 -m json.tool
```

The response JSON `stdout` field contains the fully symbolized backtrace with:
- Function names (demangled C++)
- Source file paths and line numbers
- Inlined frame expansion

### Practical Workflow for SCT Crash Analysis

1. **Identify the crashed node** — check `error.log` / `critical.log` for the node name.
2. **Find the build ID** — from `coredumps.info` in that node's directory, or from the test run context.
3. **Extract the raw backtrace** from `system.log`:
   ```bash
   grep -B 2 -A 100 "Backtrace:" db-cluster-<id>/<node>/system.log > /tmp/raw_bt.txt
   ```
4. **Symbolize** using the remote service (see above).
5. **Analyze** the symbolized output — look at the top frames for the crash site, trace the call path backward.

### `coredumpctl info` Backtraces in `CoreDumpEvent` (low-quality fallback)

> **⚠️ Prefer the remote symbolization service** (see above). `coredumpctl info` provides only mangled symbols without source locations. Use it only for quick thread-state triage (e.g., "which threads were running?"), never as the primary decode method.

When `db-cluster-<id>.tar.zst` is not available, **CoreDumpEvent** entries in `sct-<id>.log` contain `coredumpctl info` output — including per-thread stack traces with **mangled** C++ symbols. However, the **same SCT log** also contains `Backtrace:` blocks with raw hex addresses that can be sent to the remote symbolization service for much better results.

**To get properly decoded backtraces without `db-cluster-<id>.tar.zst`:**
1. Get the Build ID: `grep 'build-id' sct-<id>.log | head -1`
2. Extract raw `Backtrace:` hex addresses near the crash timestamp
3. Send to `staging.backtrace.scylladb.com/api/backtrace` (see "Symbolizing via Remote Service")

**`coredumpctl info` extraction (for thread-state triage only):**
```bash
grep -A 200 'CoreDumpEvent.*backtrace=.*PID: <PID>' sct-<id>.log | grep 'Stack trace\|#[0-9]'
```

**Key characteristics:**
- Shows **all threads** (reactor, thread_pool, alien_worker), not just the crashing shard
- Symbols are mangled (`_Z...`) — demangle with `c++filt`, but you still get no source locations
- The crashing thread is the one with `abort()` / `raise()` at the top
- Other threads: `io_pgetevents` (reactor idle), `read` (thread pool), `pthread_cond_wait` (alien worker)

### Oversized Allocation Backtraces (already decoded)

ScyllaDB's seastar memory allocator logs **oversized allocation** warnings with **fully decoded** backtraces (including source file and line numbers). These appear in `system.log` or in SCT `error.log` entries with regex `seastar_memory - oversized allocation`:

```
[shard 1:strm] seastar_memory - oversized allocation: 1212416 bytes.
  at 0x1949d3f 0x354c890 ...
seastar::current_backtrace_tasklocal() at ./seastar/include/seastar/util/backtrace.hh:85
seastar::memory::cpu_pages::warn_large_allocation(unsigned long) at ./seastar/src/core/memory.cc:865
utils::small_vector<...>::expand(unsigned long) at ././utils/small_vector.hh:72
```

**These backtraces don't need decoding** — they already contain demangled function names and source locations. They often precede a crash (the oversized allocation may succeed as a warning, but eventually OOM → abort). Cross-reference the shard ID and scheduling group (`strm` = streaming, `gms` = gossip, `mant` = maintenance) with the `coredumpctl info` to confirm the same code path.

### Multiple Backtraces

A single `system.log` may contain **multiple backtraces** (e.g., assertion + subsequent shutdown). Extract each separately:
```bash
# List all backtrace start points with line numbers
grep -n "Backtrace:\|Aborting\|Segmentation fault\|SCYLLA_ASSERT" system.log
```
Focus on the **first** backtrace — later ones are often cascading failures from the same root cause.

---

## ScyllaDB Prometheus Metrics — Full Source Code Mapping

**Complete reference:** `~/.config/github-copilot/intellij/scylla/scylladb_all_metrics_mapping.md`

This file contains **617 unique metrics** extracted from 55 C++ source files, plus appendices covering:
- **Appendix A1:** `scylla_cql_*` → `scylla_query_processor_*` recording rule aliases
- **Appendix A2:** `scylla_coordinator_*` histogram-derived aliases
- **Appendix A3:** Dynamic group names (`hints_manager`, `hints_for_views_manager`, `load_balancer`, `alternator_<Op>`, `schema_commitlog`, `transport`)
- **Appendix A4:** `*_ag` aggregated recording rules
- **Appendix A5:** Histogram sub-metrics (`_bucket`, `_count`, `_sum`)
- **Appendix A6:** Non-ScyllaDB metrics (Manager Agent, node exporter, monitoring stack)
- **Appendix A7:** Seastar execution stage metrics
- **Appendix A8:** `storage_proxy` split_stats metrics with per-node labels
- **Appendix B:** Step-by-step procedure for tracing unknown metrics

### Unmapped Metric Procedure (MANDATORY)

When analyzing a Prometheus dump and you encounter a metric **not in the mapping file**, you MUST:

1. **Check the mapping file first** — search for the metric name or a partial match.
2. **Check derived/alias patterns** — is it `_bucket`/`_count`/`_sum`/`_ag`/`scylla_ag_*`? If so, it's derived from a base metric.
3. **If truly unmapped**, trace it in the ScyllaDB C++ source:
   ```bash
   cd ~/Development/scylladb
   # Strip the scylla_ prefix and group to get the short name
   grep -rn '"<short_name>"' --include="*.cc" --include="*.hh" | grep -v test/
   # Look for the add_group call nearby to determine the full Prometheus name
   ```
4. **Add the mapping** to `scylladb_all_metrics_mapping.md` in the appropriate section.
5. **Report the addition** to the user: "Found unmapped metric `scylla_X_Y`, traced to `<file>:<line>`, meaning: `<description>`. Added to mapping."

This ensures the mapping stays current as ScyllaDB evolves.

### Quick Reference — Most Used Metric Groups

| Group | Count | Key Source File | What it Covers |
|-------|-------|----------------|----------------|
| `storage_proxy_coordinator` | 42 | `service/storage_proxy.cc` | Coordinator-side: read/write latency, timeouts, CAS, read repairs, MV flow control |
| `database` | 49 | `replica/database.cc`, `reader_concurrency_semaphore.cc` | Reads (active/queued/paused), writes, view updates, querier cache, bloom filters |
| `query_processor` | 47 | `cql3/query_processor.cc` | CQL operations (reads/inserts/deletes/updates per KS), filtering, batches, prepared cache |
| `sstables` | 45 | `sstables/sstables.cc` | SSTable I/O: reads/writes, index page cache, promoted index cache, bloom filter memory |
| `cache` | 35 | `db/row_cache.cc` | Row cache: hits/misses, evictions, insertions, memtable flush merges |
| `column_family` | 28 | `replica/table.cc`, `db/view/view.cc` | Per-table: latency histograms, disk space, memtable ops, view updates, CAS latency |
| `reactor` | 27 | `seastar/src/core/reactor.cc` | CPU utilization, AIO ops, stalls, fstream reads, tasks, exceptions |
| `raft` | 24 | `raft/server.cc` | Raft consensus: entries, messages, log state, snapshots |
| `commitlog` | 20 | `db/commitlog/commitlog.cc` | Commitlog: segments, bytes written/flushed, disk usage, pending ops |
| `io_queue` | 19 | `seastar/src/core/io_queue.cc` | Disk I/O scheduling: bytes, ops, latency, queue depth, starvation |
| `rpc` | 17 | `seastar/src/rpc/rpc.cc`, `message/advanced_rpc_compressor.cc` | Inter-node RPC: messages, timeouts, compression ratio |
| `transport` | 15 | `transport/server.cc` | CQL transport: connections, request serving, forwarding, shedding |
| `lsa` | 13 | `utils/logalloc.cc` | Log-Structured Allocator: memory usage, compaction, eviction, reclaim |
| `s3` | 11 | `utils/s3/client.cc` | Object storage client: connections, read/write bytes/latency |
| `repair` | 11 | `repair/row_level.cc` | Repair: rows/hashes/bytes sent/received, SSTable reads |
| `compaction_manager` | 8 | `compaction/compaction_manager.cc` | Compaction: active/pending/completed/failed, backlog |
| `scheduler` | 7 | `seastar/src/core/reactor.cc` | Per-scheduling-group: runtime, wait time, starve time, queue length |

### Useful Derived Metrics (PromQL)
```promql
# Row cache hit rate
rate(scylla_cache_row_hits[1m]) / (rate(scylla_cache_row_hits[1m]) + rate(scylla_cache_row_misses[1m]))

# Cold read ratio (reads that hit SSTables)
rate(scylla_cache_reads_with_misses[1m]) / rate(scylla_cache_reads[1m])

# Cache utilization
scylla_cache_bytes_used / scylla_cache_bytes_total

# Write throughput (coordinator)
rate(scylla_storage_proxy_coordinator_write_latency_count[1m])

# Read throughput (coordinator)
rate(scylla_storage_proxy_coordinator_read_latency_count[1m])

# Compaction backlog per shard
scylla_compaction_manager_backlog

# Reactor utilization
scylla_reactor_utilization

# Disk I/O throughput (read)
rate(scylla_io_queue_total_read_bytes[1m])

# Hint queue growth (indicates node down)
scylla_hints_manager_size_of_hints_in_progress
```

---

## Argus Test Run Links

Every SCT run is tracked in [Argus](https://argus.scylladb.com), the test result tracking service. Each run has a unique UUID (`test_id`) that maps to an Argus URL.

### Argus URL Format
```
https://argus.scylladb.com/tests/scylla-cluster-tests/<test_id>
```

> **⚠️ CRITICAL:** `<test_id>` is always the **full 36-character UUID** with dashes (e.g., `652145e6-03d2-47f0-8459-800926104f49`). **Never** use a truncated/short prefix (e.g., `652145e6`) — Argus will not resolve it. The log directory names use a short prefix, but the Argus URL requires the complete UUID from the `test_id` file.

### Retrieving the Test ID

1. **From the log directory** — `test_id` is written to a file by `TestConfig.set_test_id()`:
   ```bash
   cat ~/sct-results/latest/test_id          # Most recent run
   cat ~/sct-results/<run_dir>/test_id        # Specific run
   ```

2. **From the SCT framework log** (`sct-<id>.log`) — the test ID appears early in the log during initialization. Search for:
   ```bash
   grep -i "test_id\|TestId" sct-<id>.log | head -5
   ```

3. **From cluster reuse** — when reusing a cluster, the test ID is obtained via:
   ```bash
   export SCT_REUSE_CLUSTER=$(cat ~/sct-results/latest/test_id)
   ```

4. **From Jenkins** — the Argus link is embedded in the Jenkins build description (see `vars/createArgusTestRun.groovy`).

### Argus Log Download URLs

Individual log archives can be downloaded directly from Argus:
```
https://argus.scylladb.com/api/v1/tests/scylla-cluster-tests/<test_id>/log/<filename>/download
```
Where `<filename>` matches the archive names listed in the "File Inventory" section (e.g., `sct-<id>.log.tar.zst`, `db-cluster-<id>.tar.zst`).

### Quick One-Liner — Argus Link for Latest Run
```bash
echo "https://argus.scylladb.com/tests/scylla-cluster-tests/$(cat ~/sct-results/latest/test_id)"
```

---

## Analysis Report Locations

All generated analysis files go to the CLion scratches directory:
```
~/.config/JetBrains/CLion2026.1/scratches/GitHubCopilot/
```

Naming convention: `sct_run_<suffix>_<report_type>.md`

Examples:
- `sct_run_2730e03d_overview.md` — run structure and file inventory
- `sct_run_2730e03d_performance_report.md` — throughput/latency analysis

### Persistent Reference Files (in `~/.config/github-copilot/intellij/scylla/`)
- `scylladb_all_metrics_mapping.md` — complete Prometheus-to-C++ source mapping (617 metrics + aliases)

---

## Lessons Learned — Self-Updating Section (SCT-specific)

This section is **written and maintained by the agent itself**, following the same rules as the global Lessons Learned section in `global-agents-instructions.md`. Entries here are **SCT-specific** — general insights go in the global file instead.

### When to add an entry
- The user corrects the agent on an SCT-specific workflow, file location, log format, metric interpretation, or analysis technique.
- An SCT tool/API/convention turns out to work differently than assumed.
- The user says "remember this" and the insight is SCT-related.

### When NOT to add an entry
- The insight is general (not SCT-specific) — add it to the global file instead.
- It's a one-time, run-specific observation (e.g., "this particular run had 6 nodes").
- Already covered elsewhere in this file.

### Format
Each entry: a short title, the date, and a concise explanation. Keep entries to 3–5 lines max.

### Procedure
1. Append the new entry at the bottom of this section.
2. If an older entry is superseded, update or remove it.
3. Commit and push the change (see "Version Control for Instruction Files" in global instructions).

---

### ScyllaDB metrics use dynamic group names (2026-04-28)
Many ScyllaDB Prometheus metrics are registered with a runtime `group_name` variable (e.g., in `db/hints/manager.cc`, `service/tablet_allocator.cc`, `alternator/stats.cc`), making them invisible to naive `grep 'add_group("...'` extraction. The actual Prometheus name depends on the group name passed at object construction time (e.g., `hints_manager`, `load_balancer`, `alternator_GetItem`).
**Correct approach:** When a metric is not found by searching the literal Prometheus name in C++, strip the `scylla_` prefix and group, then search for the short metric name (e.g., `"written"`, `"dropped"`). Check the known dynamic-group files listed in Appendix A3.

### Always trace unmapped metrics back to C++ source (2026-04-28)
When encountering a Prometheus metric during SCT analysis that is not in the mapping file, do not guess its meaning from the name alone. Trace it back to the C++ registration site (`add_group` + `make_counter`/`make_gauge`) to get the actual description. Then add it to the mapping file.
**Correct approach:** Follow the "Unmapped Metric Procedure" above and update `scylladb_all_metrics_mapping.md`.

### promtool tsdb dump requires --sandbox-dir-root with snapshot directories (2026-04-29)
When using `promtool tsdb dump` on a Prometheus snapshot directory (extracted from `prometheus_data_*.tar.zst`), the command fails silently with "setting up sandbox dir: stat data/: no such file or directory" unless you pass `--sandbox-dir-root="<tsdb_path>"`. Without this flag, promtool looks for a `data/` directory relative to CWD and produces no output.
**Correct approach:** Always use `promtool tsdb dump --sandbox-dir-root="$TSDB" --match='{...}' "$TSDB"` when querying snapshot directories.

### Cache hit rate must use correct read-phase time window (2026-04-29)
When calculating cache hit rates from Prometheus counter deltas, the time window MUST correspond exactly to the read stress phase (check stress log timestamps). Using the full TSDB range or test duration gives incorrect averages because it includes the write/prepare phase where the cache is being populated (high misses) or idle periods.
**Correct approach:** Extract read start/end timestamps from the stress log (`head -1` and `grep "Results:"` lines), convert to epoch ms, then filter Prometheus samples to that window only.

### Always use remote symbolization service for backtraces — never coredumpctl info + c++filt (2026-05-04)
The agent used `coredumpctl info` output from `CoreDumpEvent` entries in the SCT log and decoded mangled symbols with `c++filt`. This produces incomplete results: no source file/line, no inlined frames, wrong function attribution (e.g., showed `utils::small_vector::expand()` when the actual crash was in `utils::chunked_vector::new_chunk()`).
**Correct approach:** (1) Find the Build ID via `grep 'build-id' sct-<id>.log`, (2) extract raw hex addresses from `Backtrace:` blocks in the SCT log, (3) send to `staging.backtrace.scylladb.com/api/backtrace` with the build ID. This returns fully symbolized output with source file:line, inlined frames, and demangled names — the same quality as `system.log` reactor stall backtraces.

### Always use Prometheus TSDB for metrics — never rely on nodetool or other approximations (2026-04-29)
When reporting metrics like cache hit rate, throughput counters, or any time-series data, ALWAYS retrieve the data from the Prometheus TSDB snapshot (in `monitor-set-<id>/prometheus_data_*.tar.zst`). Do NOT use `nodetool info`, `nodetool cfstats`, gossip state, or system.log entries as substitutes — these provide point-in-time or cumulative snapshots that do not accurately reflect behavior during a specific test phase. In this analysis, `nodetool info` reported ~50% cache hit rate for local_4xlarge while Prometheus showed the correct value of 90.1% during the read phase.
**Correct approach:** Extract the Prometheus TSDB, use `promtool tsdb dump --sandbox-dir-root="$TSDB" --match='{__name__="<metric>"}' "$TSDB"`, filter to the exact time window of interest, and compute deltas per (instance, shard).

