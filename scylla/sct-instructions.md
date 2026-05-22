# SCT (Scylla Cluster Tests) — Agent Instructions

**Location:** `~/.config/github-copilot/intellij/scylla/sct-instructions.md`
**Referenced from:** `~/.config/github-copilot/intellij/global-agents-instructions.md` (ScyllaDB Ecosystem table)
**Purpose:** SCT-specific conventions, analysis workflows, and metric mappings that supplement the repo-level `.github/copilot-instructions.md`.

---

## SCT Run Log Analysis

### Run Identification
Every SCT run produces logs with a consistent **8-character hex suffix** (e.g., `2730e03d`). All files from the same run share this suffix. **Always verify suffix consistency** across all downloaded files — if any file has a different suffix, warn the user immediately.

**Argus URL format:** `https://argus.scylladb.com/tests/scylla-cluster-tests/<full-test-uuid>` — the project name `scylla-cluster-tests` is always part of the path. The full UUID is found in the SCT log (`test_id=<uuid>`).

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

### Stress Log Format (latte)
Latte stress logs use a different format. Filename pattern:
```
latte-<tag>-l<loader>-c<cpu>-<uuid>.log
```

**Log structure:**
1. **Init line:** `init_partition_row_distribution_preset: preset_name=<name>, total_partitions=N, total_rows=M, partitions/rows -> N:M`
2. **CONFIG section:** Cluster info, workload script, function(s), consistency, threads, concurrency, run time/op count
3. **LOG section:** Per-second interval samples:
   ```
   Time[s]  Cycles[op]  Errors[op]  Thrpt[op/s]  Min  p50  p75  p90  p95  p99  p99.9  Max  [ms/op]
   ```
4. **RESULTS section:**
   ```
   Cycles [op]   20000000
   Errors [op]          0
   Rows   [row]         0       ← result rows returned (0 for writes)
   Throughput [op/s]  18665
   Cycle latency [ms]  2.571
   ```
5. **CYCLE LATENCY histogram:** Min, p25, p50, p75, p90, p95, p98, p99, p99.9, p99.99, Max

**Key config lines to extract:**
- `Function(s)` — which latte function is running (insert, read, count_read, etc.)
- `Run time [s]` or `└─ [op]` — duration-based or count-based termination
- `Threads` / `Concurrency [req]` — parallelism settings
- `Consistency` — CL used

**Latte cycle vs row semantics:**
- One "cycle" = one call to the latte function (may produce multiple CQL requests internally)
- `--start-cycle=1 --end-cycle=20000001` = 20M cycles
- `Rows [row]` reports result rows returned to the driver (0 for writes, 1 for count(*), N for scans)
- `[row/req]` shows rows per CQL request (useful for understanding scan page sizes)

---

## Verifying Dataset Size from Prometheus Metrics

When analyzing run results, **always verify the actual on-disk data size** rather than trusting test names or Jira descriptions.

### Key Metrics

| Metric | What it reports | Per-shard? |
|--------|----------------|:---:|
| `scylla_column_family_live_disk_space` | Live SSTable bytes (compressed, on disk/S3) | **No** (per-node per-table) |
| `scylla_column_family_total_disk_space` | All SSTable bytes including pending compaction | No |
| `scylla_column_family_total_disk_space_before_compression` | Uncompressed logical size | No |
| `scylla_column_family_live_sstable` | Count of live SSTables | No |
| `scylla_column_family_tablet_count` | Number of tablet replicas on this node | No |

**Important:** These metrics do NOT have a `shard` label — they're already aggregated at the (instance, keyspace, table) level. No need to sum across shards; just sum across instances.

### Verifying Data Size

```bash
# Get per-node live disk space for a specific table (use latest timestamp values)
promtool tsdb dump --sandbox-dir-root="$TSDB" --match='{__name__="scylla_column_family_live_disk_space"}' "$TSDB" 2>/dev/null \
  | grep "<table_name>" | awk '{
  match($0, /instance="([^"]+)"/, a)
  split($0, parts, "} "); split(parts[2], vals, " ")
  val = vals[1]; ts = vals[2]
  if (ts+0 > latest_ts[a[1]]+0) { latest_ts[a[1]] = ts; latest_val[a[1]] = val }
} END {
  total = 0
  for (k in latest_val) { total += latest_val[k]; printf "  %s: %.3f GB\n", k, latest_val[k]/1073741824 }
  printf "  TOTAL: %.3f GB\n", total/1073741824
}'
```

### Cross-Checking Compression Ratio

Compare `live_disk_space` (compressed) vs `total_disk_space_before_compression` (uncompressed):
- Ratio ~1:1 → data is incompressible (random bytes or already maximally compact)
- Ratio >> 1 → effective compression (text, repeated patterns, sparse data)
- Compressed > uncompressed → compression overhead exceeds savings (very small data + framing)

### Deriving Per-Row Size

```
per_row_bytes = total_live_disk_space / (unique_rows × RF)
```

Compare against expected schema size:
- `bigint` = 8 bytes
- `blob` = variable (check latte script for generation logic)
- SSTable overhead per row: ~20-50 bytes (flags, timestamps, cell headers)
- If per_row_bytes << expected → blobs are empty/tiny, test measures mechanics not volume

### For S3 Keyspaces

`scylla_column_family_live_disk_space` reports actual SSTable size **on S3** (not local metadata). Verified by cross-referencing: native and S3 runs with the same data show the same `live_disk_space` values. The metric is authoritative for both storage backends.

To get total data UPLOADED to S3 during writes (including intermediate flushes that get compacted away):
```bash
# Sum max values of scylla_s3_total_put_bytes for class="memtable" across all (instance, shard)
promtool tsdb dump --sandbox-dir-root="$TSDB" --match='{__name__="scylla_s3_total_put_bytes", class="memtable"}' "$TSDB" 2>/dev/null
```

This total will be LARGER than `live_disk_space` because it includes bytes from intermediate SSTables that were later compacted away.

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
| `s3` | 41 | `utils/s3/client.cc` | Object storage client: connections, per-HTTP-method bytes/latency/requests/retries (GET/PUT/HEAD/DELETE/POST/CONNECT/OPTIONS/PATCH/TRACE), prefetch, memory blocks |
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

## Argus CLI

The `argus` CLI (`~/.local/bin/argus`, v0.1.2+) provides direct access to test run data from the terminal. It is the **preferred** method for querying Argus — use it instead of manual curl/API calls.

### Prerequisites
- Binary: `~/.local/bin/argus` (installed from `scylladb/argus` releases, `cli/v*` tags)
- Cloudflared: `~/.local/bin/cloudflared` (needed for CF Access auth to argus.scylladb.com)
- Config: `~/.config/argus-cli/config.yaml` with `url: https://argus.scylladb.com` and `use_cloudflare: true`

### Authentication
Argus production is behind Cloudflare Access. Auth is browser-based via Okta SSO:
```bash
~/.local/bin/argus auth
```
This opens a browser, authenticates via Okta, stores CF JWT + Argus session in system keychain. Re-run when session expires.

The user's Argus PAT (Personal Access Token) can also be set via `ARGUS_AUTH_TOKEN` env var or stored with `argus auth headless` (requires CF service-token credentials too).

### Key Commands

| Command | Purpose |
|---------|---------|
| `argus run get --run-id <UUID>` | Basic run details (status, duration, build) |
| `argus run details --run-id <UUID>` | Full run details |
| `argus run events --run-id <UUID>` | CRITICAL and ERROR events |
| `argus run nemeses --run-id <UUID>` | Nemesis records (start/end times, status) |
| `argus run logs list --run-id <UUID>` | List available log files |
| `argus run logs download --run-id <UUID> --name <filename>` | Download a specific log |
| `argus run results --run-id <UUID>` | Result tables |
| `argus run comments --run-id <UUID>` | Comments on the run |
| `argus run activity --run-id <UUID>` | Activity log |
| `argus run list --test-id <test-UUID> --limit N` | List recent runs for a test |
| `argus api version` | Verify API connectivity |

### Output Format
- Default: JSON. Add `--text` for human-readable table format.
- Use `--no-cache` to bypass local response cache for fresh data.
- Use `--non-interactive` to prevent auth prompts (fail instead).

### Typical Analysis Workflow
```bash
# 1. Get run overview
argus run get --run-id <UUID> --text

# 2. Check for errors
argus run events --run-id <UUID>

# 3. Check nemesis history
argus run nemeses --run-id <UUID>

# 4. List and download logs for deep analysis
argus run logs list --run-id <UUID>
argus run logs download --run-id <UUID> --name "sct-<suffix>.log.tar.zst" --output /tmp/
```

---

## ScyllaDB Internal MCP Servers

These MCP servers are configured in `~/.config/github-copilot/intellij/mcp.json` and provide access to ScyllaDB-internal observability services.

| Server | URL | Auth | Purpose |
|--------|-----|------|---------|
| `victorialogs_clusters` | `https://victoria-logs-mcp.app.int.scylla.cloud/mcp` | Internal network (VPN/SSO) | Query VictoriaLogs for ScyllaDB Cloud **cluster** logs |
| `victorialogs_infra` | `https://victoria-logs-infra-mcp.app.int.scylla.cloud/mcp` | Internal network (VPN/SSO) | Query VictoriaLogs for ScyllaDB Cloud **infrastructure** logs |
| `metabase` | `https://scylladb.metabaseapp.com/api/mcp` | OAuth (browser) | Query Metabase dashboards and datasets (test analytics, fleet data) |
| `atlassian` | `https://mcp.atlassian.com/v1/mcp` | OAuth via Okta SSO | Jira issues and Confluence pages at `scylladb.atlassian.net` |

### Authentication Notes
- **VictoriaLogs MCPs:** Require access to the internal ScyllaDB network (`.int.scylla.cloud` domain). No additional token needed — identity is from the network/SSO context.
- **Metabase MCP:** Uses OAuth via browser. First use opens a browser auth flow.
- **Atlassian MCP:** Uses OAuth via browser through the org's Okta SSO. Documented in detail in the global instructions file.

### When to Use
- **VictoriaLogs:** When investigating ScyllaDB Cloud cluster issues (not SCT test runs — those use Prometheus from the monitoring stack).
- **Metabase:** When querying historical test analytics, fleet metrics, or aggregated data across many runs.
- **Atlassian:** When creating/updating Jira issues or reading Confluence documentation.

### SCT Test Run Investigator (Planned)

A unified MCP server for investigating SCT test run failures is being developed (design doc: [Confluence page](https://scylladb.atlassian.net/wiki/spaces/RND/pages/83427349)). Once deployed, it will replace the current workflow of querying individual data sources separately.

**Architecture:**
- Single MCP server combining: Argus (metadata), Victoria Logs (SCT + DB logs), Prometheus (metrics), Knowledge Base (instructions via RAG)
- RAG-based instruction retrieval — dynamically fetches relevant investigation guidelines from `.md` files based on the query
- History — stores investigation findings for continuation, review, and team sharing

**Key design decisions:**
- Separate generic MCP servers (like the VictoriaLogs ones above) were found too generic for ScyllaDB-specific investigations — the unified server provides tailored endpoints
- Knowledge Base uses `# Description` + `# Instructions` format in `.md` files
- Supports both local (dev) and remote (production, shared history) deployment

**Status:** Design phase (v0.1, May 2025). Not yet deployed as an MCP server. Until available, continue using the individual MCP servers documented above.

---

## Confluence Knowledge Sources

Key Confluence pages in the `RND` space (`scylladb.atlassian.net`) relevant to SCT work. Use the Atlassian MCP to fetch full content when needed.

### Investigation & Triage Procedures

| Page | ID | What it contains |
|------|-----|-----------------|
| [Tier1 Longevity Tests Ownership](https://scylladb.atlassian.net/wiki/spaces/RND/pages/136642692) | 136642692 | **Investigation workflow** for weekly master-branch test runs — failure classification (flaky/persistent/new), analysis steps, Argus log review |
| [Triage tier1 SCT Argus jobs](https://scylladb.atlassian.net/wiki/spaces/RND/pages/102793710) | 102793710 | Triage quality standards — 1-week SLA, what constitutes a "good" filed issue |
| [Issue triaging](https://scylladb.atlassian.net/wiki/spaces/RND/pages/9699392) | 9699392 | General ScyllaDB triage methodology — timeboxing, distinguishing symptoms from root causes |
| [SCT Opening Issues/Tasks Procedure](https://scylladb.atlassian.net/wiki/spaces/RND/pages/65077648) | 65077648 | Rules for opening issues — type marking, assignment, labels |

### Developer Guides

| Page | ID | What it contains |
|------|-----|-----------------|
| [Getting started with SCT](https://scylladb.atlassian.net/wiki/spaces/RND/pages/81133746) | 81133746 | Onboarding — what is SCT, setup, running tests |
| [SCT developer guide](https://scylladb.atlassian.net/wiki/spaces/RND/pages/81494021) | 81494021 | Adding nemesis, ICS example, developer workflow |
| [How to create new SCT test case](https://scylladb.atlassian.net/wiki/spaces/RND/pages/82182565) | 82182565 | Longevity testing, writing nemesis, test configurations |
| [SCT Upgrade Tests HOWTO](https://scylladb.atlassian.net/wiki/spaces/RND/pages/223805468) | 223805468 | Upgrade scenarios (major/minor), GKE+AWS, reading results |

### Architecture & Design

| Page | ID | What it contains |
|------|-----|-----------------|
| [SCT/Argus Migration to Tags/Labels](https://scylladb.atlassian.net/wiki/spaces/RND/pages/163807421) | 163807421 | Folder hierarchy → tag-based test grouping |
| [Argus](https://scylladb.atlassian.net/wiki/spaces/RND/pages/106954981) | 106954981 | Argus documentation — scylla-trunk, staging, test graphs |
| [SCT Maintainers Sync](https://scylladb.atlassian.net/wiki/spaces/RND/pages/217677915) | 217677915 | Maintainer-on-duty rotation, conflict resolution, backlog |

### Cautionary Tale

- **[Decoy Directory Issue: AI Band-Aid](https://scylladb.atlassian.net/wiki/spaces/RND/pages/235962371)** (page 235962371) — Post-mortem where AI suggested ignoring an error (band-aid fix that got merged), but the real root cause was a decoy directory confusing log collection. Lesson: always push for root cause, never accept "just ignore it" from AI suggestions.

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

## SSH Access to SCT Nodes

### Key
All SCT infrastructure (runners, DB nodes, loaders, monitors) uses the same SSH key:
```
~/.ssh/scylla_test_id_ed25519
```

### Access Pattern

```
Local machine ──SSH──► SCT runner ──SSH──► DB / Loader / Monitor nodes
```

1. **SSH to SCT runner** (the machine orchestrating the test):
   ```bash
   ssh -i ~/.ssh/scylla_test_id_ed25519 ubuntu@<runner-ip>
   ```
   The runner IP comes from Argus (test run page) or from the user.

2. **From runner to cluster nodes** (DB, loader, monitor):
   ```bash
   # The same key is deployed on the runner for intra-cluster access
   ssh -i ~/.ssh/scylla_test_id_ed25519 <user>@<node-ip>
   ```
   - DB nodes: user is typically `ubuntu` or `centos` (depends on AMI)
   - Node IPs are in `~/sct-results/latest/` or from the SCT log's cluster setup output

3. **Finding node IPs on the runner**:
   ```bash
   cat ~/sct-results/latest/test_id              # Get test UUID
   grep -i "private_ip_address" ~/sct-results/latest/*.log | head -20
   # Or from the SCT framework's cluster info:
   grep "db_cluster\|loader" ~/sct-results/latest/sct-*.log | grep -oP '\d+\.\d+\.\d+\.\d+' | sort -u
   ```

### Prometheus Access from Runner

The monitoring node runs Prometheus. Once SSHed to the runner, query metrics directly:
```bash
# Find monitor IP
MONITOR_IP=$(grep "monitor" ~/sct-results/latest/sct-*.log | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1)

# Query a metric
curl -s "http://${MONITOR_IP}:9090/api/v1/query?query=scylla_s3_downloads_blocked_on_memory" | python3 -m json.tool
```

### Notes
- The runner is an ephemeral EC2 instance — it only exists while the test is running (or shortly after if teardown hasn't completed).
- If SSH fails with "connection refused", the instance may still be in cloud-init or may have been terminated.
- The key `scylla_test_id_ed25519` is SCT-specific and different from personal AWS keys.

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

## Tuning cassandra-stress Tests for Storage Backend & Instance Size

When configuring SCT stress tests (particularly `prepare_write_cmd` and `stress_cmd`), the parameters must be adjusted based on the storage backend (local NVMe vs S3), instance type resources, cluster size, and replication factor. This section captures the tuning lessons learned from running GrowShrink nemesis tests on S3-backed keyspaces.

### Key Timeout Layers (all must be coordinated)

| Layer | Setting | Default | Where configured |
|-------|---------|---------|-----------------|
| **Java driver client** | `-mode cql3 native requestTimeout=<ms>` | 12000ms | cassandra-stress CLI `-mode` section |
| **Scylla server write** | `write_request_timeout_in_ms` | 2000ms | `append_scylla_yaml` in test config |
| **Scylla server read** | `read_request_timeout_in_ms` | 5000ms | `append_scylla_yaml` in test config |

**Rule:** Client timeout > Server timeout > Expected worst-case latency. For S3 backends, use at minimum:
- Server: `write_request_timeout_in_ms: 30000`, `read_request_timeout_in_ms: 30000`
- Client: `requestTimeout=60000` (in the `-mode` section of every cassandra-stress command)

**Symptom of misconfigured timeouts:**
- `OperationTimedOutException: configured timeout: 12000ms` → Client-side (Java driver). Fix: increase `requestTimeout=` in `-mode`.
- `WriteTimeoutException` / `ReadTimeoutException` → Server-side. Fix: increase `*_timeout_in_ms` in `append_scylla_yaml`.

### Storage Backend Impact on Thread Counts

| Backend | Write throughput (per loader) | Recommended threads | Notes |
|---------|------------------------------|--------------------:|-------|
| Local NVMe (i4i) | 60–80K op/s | 80–100 | Sub-ms latency, can saturate CPU |
| S3 (object storage) | 15–25K op/s | 40–60 | 25–50ms latency per PUT; too many threads → timeout cascade |

**Why S3 needs fewer threads:** Each S3 PUT has ~25–50ms latency. With 80 threads × 4 loaders = 320 concurrent writes, the cluster can sustain this initially, but after 20–25 minutes the accumulation of S3 back-pressure (compaction flushes competing with user writes for S3 bandwidth) causes latency spikes that exceed the client timeout.

**S3-specific tuning formula:**
- Start with 60 threads per loader
- If timeouts occur at the end of the write phase (near completion), it's usually back-pressure from accumulated flushes — consider bumping `requestTimeout` rather than reducing threads further
- If timeouts occur early (first 5 min), reduce threads

### Data Sizing Calculations

For `cassandra-stress` with `-col 'n=FIXED(C) size=FIXED(S)'`:
- Row size ≈ key(48 bytes) + C × S bytes + overhead(~50 bytes)
- For `n=FIXED(8) size=FIXED(128)`: row ≈ 48 + 8×128 + 50 ≈ 1122 bytes ≈ 1 KiB

**Scaling to target data size (accounting for RF):**
```
total_rows = target_data_GiB × 1024³ / row_size_bytes
rows_per_loader = total_rows / n_loaders
data_per_node = target_data_GiB × RF / n_db_nodes
```

Example: 100 GiB target, RF=3, 6 nodes, 4 loaders:
- total_rows = 100 × 1024³ / 1024 ≈ 106M rows
- rows_per_loader = 106M / 4 = 26.5M
- data_per_node = 100 × 3 / 6 = 50 GiB (must fit on disk)

### Instance Type Selection

**DB nodes:**
- Must have enough disk for `target_data × RF / n_nodes` + headroom for compaction (2×)
- `i4i.large` (468 GB NVMe) → supports ~200 GiB data per node
- For S3 keyspaces: local disk used for commitlog, system tables, caches only — smaller instances work

**Loader nodes:**
- CPU-bound during write phase; need enough cores to drive target thread count
- `c6i.2xlarge` (8 vCPU, 16 GB) → good for 60–80 threads per loader
- `c6i.large` (2 vCPU, 4 GB) → only for ≤20 threads

### Nemesis Interaction with S3 Writes

**Critical:** GrowShrink nemesis bootstraps new nodes, which triggers tablet migration → S3 reads + writes from new nodes. If this happens during the write phase, the combined S3 pressure (user writes + migration reads/writes) overwhelms the cluster.

**Rules:**
- Always set `nemesis_during_prepare: false` for S3-backed keyspaces
- `teardown_validators: scrub` is incompatible with GrowShrink — decommissioned nodes get scrubbed and timeout. Comment it out.
- Keep stress_cmd reads at very low thread count (1–2) during nemesis to observe migration without interference

### round_robin Behavior

When `round_robin: true` is set:
- `prepare_write_cmd` entries are distributed 1-per-loader (entry[0] → loader-1, entry[1] → loader-2, etc.)
- Each loader gets exactly one command, not all commands
- Number of entries in `prepare_write_cmd` must equal `n_loaders`
- `-pop seq=` ranges must be non-overlapping and cover the full key range

### Write Phase Duration Estimation

For S3 backends with the recommended settings:
- 60 threads × 4 loaders → cluster throughput ~60–80K op/s
- 106M rows ÷ 70K op/s ≈ 25 minutes
- Add 50% safety margin for S3 back-pressure near the end → budget ~35–40 min

Set `test_duration` to accommodate: write_time + stress_duration + nemesis_buffer:
- Example: 40 min write + 60 min stress + 15 min nemesis overlap + 35 min buffer = 150 min

### Complete S3 GrowShrink Test Config Template

```yaml
test_duration: 150

pre_create_keyspace: >-
  CREATE KEYSPACE keyspace1 WITH replication =
  {'class': 'NetworkTopologyStrategy', 'replication_factor': 3}
  AND storage = {'type': 'S3', 'endpoint': 's3.<region>.amazonaws.com',
  'bucket': '<bucket-name>'};

prepare_write_cmd:  # 4 entries for 4 loaders (round_robin: true)
    - "cassandra-stress write cl=QUORUM n=26500000 -schema '...' -mode cql3 native requestTimeout=60000 -rate threads=60 -pop seq=1..26500000 -col 'n=FIXED(8) size=FIXED(128)' -log interval=5"
    - "cassandra-stress write cl=QUORUM n=26500000 -schema '...' -mode cql3 native requestTimeout=60000 -rate threads=60 -pop seq=26500001..53000000 -col 'n=FIXED(8) size=FIXED(128)' -log interval=5"
    - "cassandra-stress write cl=QUORUM n=26500000 -schema '...' -mode cql3 native requestTimeout=60000 -rate threads=60 -pop seq=53000001..79500000 -col 'n=FIXED(8) size=FIXED(128)' -log interval=5"
    - "cassandra-stress write cl=QUORUM n=26500000 -schema '...' -mode cql3 native requestTimeout=60000 -rate threads=60 -pop seq=79500001..106000000 -col 'n=FIXED(8) size=FIXED(128)' -log interval=5"

stress_cmd:  # Low-pressure reads during nemesis
    - "cassandra-stress read cl=QUORUM duration=60m -schema '...' -mode cql3 native requestTimeout=60000 -rate threads=1 -pop seq=1..106000000 -col 'n=FIXED(8) size=FIXED(128)' -log interval=5"
    - "cassandra-stress read cl=QUORUM duration=60m -schema '...' -mode cql3 native requestTimeout=60000 -rate threads=1 -pop seq=1..106000000 -col 'n=FIXED(8) size=FIXED(128)' -log interval=5"

round_robin: true
n_db_nodes: 6
n_loaders: 4
instance_type_db: 'i4i.large'
instance_type_loader: 'c6i.2xlarge'

nemesis_during_prepare: false
nemesis_interval: 3

append_scylla_yaml:
  write_request_timeout_in_ms: 30000
  read_request_timeout_in_ms: 30000

experimental_features:
  - keyspace-storage-options
```

---

## Latte Benchmark Tool Reference

**Repository:** https://github.com/scylladb/latte
**Language:** Rust + Rune scripting (`.rn` files)
**Purpose:** CQL/Alternator benchmarking tool with scriptable workloads

### Source Code Layout

| Path | Purpose |
|------|---------|
| `src/scripting/functions_common.rs` | **Built-in functions** exposed to `.rn` scripts (`blob()`, `text()`, `hash()`, `uuid()`, `normal()`, `uniform()`, `vector()`, etc.) |
| `src/scripting/row_distribution.rs` | **Partition row distribution logic** — how iterations map to partitions (round-robin, weighted groups) |
| `src/scripting/mod.rs` | Script engine setup, module registration |
| `src/scripting/cql/` | CQL-specific bindings (prepared statements, execute, result handling) |
| `src/scripting/alternator/` | DynamoDB/Alternator bindings |
| `src/config.rs` | CLI argument parsing, workload configuration |
| `src/main.rs` | Entry point, run orchestration |
| `src/exec/` | Execution engine (thread pool, rate limiting, cycle management) |
| `src/stats/` | Statistics collection and reporting |
| `src/report/` | Output formatting (text, JSON, HDR histograms) |
| `workloads/` | Built-in example `.rn` workload scripts |
| `resources/` | Embedded resource files accessible via `read_resource_*()` |

### Key Built-in Functions

All registered via `#[rune::function]` in `functions_common.rs`:

| Function | Signature | Behavior |
|----------|-----------|----------|
| `blob(seed, len)` | `(i64, usize) → Vec<u8>` | Generates `len` **pseudorandom bytes** seeded by `seed`. Each call with same seed+len produces identical output. Data is truly random (incompressible). |
| `text(seed, len)` | `(i64, usize) → String` | Generates `len` random characters from alphanumeric+symbols charset |
| `hash(i)` | `(i64) → i64` | MetroHash64 of `i`, result in `[0, i64::MAX]` |
| `hash2(a, b)` | `(i64, i64) → i64` | MetroHash64 of two values combined |
| `hash_range(i, max)` | `(i64, i64) → i64` | `hash(i) % max` — deterministic mapping to `[0, max)` |
| `hash_select(i, collection)` | `(i64, &[Value]) → Value` | Select item from collection by hash |
| `uuid(i)` | `(i64) → Uuid` | Deterministic UUID from iteration index |
| `normal(i, mean, std_dev)` | `(i64, f64, f64) → f64` | Seeded normal distribution sample |
| `uniform(i, min, max)` | `(i64, f64, f64) → f64` | Seeded uniform distribution sample |
| `vector(len, generator)` | `(usize, Function) → Vec<Value>` | Generate vector by calling generator(i) for each index |
| `now_timestamp()` | `() → i64` | Current UTC epoch seconds |
| `is_none(input)` | `(Value) → bool` | Check if value is None (workaround for Rune's None handling) |
| `read_to_string(path)` | `(&str) → String` | Read file contents |
| `read_lines(path)` | `(&str) → Vec<String>` | Read file as lines |
| `read_words(path)` | `(&str) → Vec<String>` | Read file, split into words |
| `read_resource_to_string(path)` | `(&str) → String` | Read embedded resource file |
| `join(collection, sep)` | `(&[Value], &str) → String` | Join string values with separator |

### Partition Row Distribution

The `init_partition_row_distribution_preset(name, row_count, rows_per_partition, partition_sizes)` function configures how iteration indices map to partitions.

**Parameters:**
- `row_count` — total logical rows across all partitions
- `rows_per_partition` — base number of rows per partition (before multiplier)
- `partition_sizes` — string of `"percent:multiplier"` pairs, e.g., `"100:1"` (uniform), `"80:1,15:2,5:4"` (mixed sizes)

**How it works (single group, "100:1"):**
- `n_partitions = row_count / rows_per_partition`
- Distribution is **round-robin with stride 1**: `partition_idx = idx % n_partitions`
- The `get_partition_idx(preset_name, idx)` function returns the partition index for a given iteration

**The GCD collision trap:**
When the script computes `ck = idx % rows_per_partition` and partition assignment is `idx % n_partitions`:
- Partition `p` gets idx values: `p, p + n_partitions, p + 2*n_partitions, ...`
- CK values for partition `p`: `{(p + k * n_partitions) % rows_per_partition : k=0,1,...}`
- **Unique CKs per partition = rows_per_partition / gcd(n_partitions, rows_per_partition)**
- If `n_partitions` divides `rows_per_partition` evenly: only `rows_per_partition / n_partitions` unique rows per partition!

**Example:** `n_partitions=1000`, `rows_per_partition=30000` → `gcd=1000` → only **30** unique ck values per partition. Running 20M cycles produces 30,000 unique rows total, not 20M.

**Fix:** Run enough cycles to cover all rows (`end_cycle >= row_count`), or ensure `gcd(n_partitions, rows_per_partition) = 1` (coprime values).

### Latte CLI — Key Arguments

| Argument | Meaning |
|----------|---------|
| `--function=<name>` | Which `.rn` function to call per cycle (e.g., `insert`, `read`) |
| `--start-cycle=N --end-cycle=M` | Cycle range `[N, M)` — total iterations = M - N |
| `--duration=<seconds or Nm/Nh>` | Time-bound execution (overrides cycle count if shorter) |
| `--rate=<ops/s>` | Target throughput (throttled) |
| `--threads=N` | OS threads |
| `--concurrency=N` | Max concurrent async requests |
| `--consistency=<CL>` | CQL consistency level |
| `--tag=<string>` | Tag for identifying this run in logs |
| `-P key=value` | Override `latte::param!()` parameters in the script |
| `--request-timeout=<secs>` | Per-request timeout |
| `--retry-interval='min,max'` | Retry backoff range |
| `--retry-number=N` | Max retries per request |

### Latte `param!()` Macro

Scripts declare parameters with defaults using:
```rust
const VALUE_SIZE = latte::param!("value_size", 512);
```

Override from CLI: `latte run ... -P value_size=1024 ...`

If no `-P` override is given, the default (second argument) is used. **Always check the test config YAML for `-P` overrides** before assuming default values.

### Workload Script Structure

A typical `.rn` file has these functions:

| Function | Called when | Purpose |
|----------|------------|---------|
| `schema(db)` | `latte schema ...` | Create keyspace/table (DDL) |
| `erase(db)` | `latte schema --erase ...` | Truncate table |
| `prepare(db)` | Before run starts | Prepare statements, init distribution presets |
| `insert(db, i)` | Each write cycle `i` | Insert/upsert a row |
| `read(db, i)` | Each read cycle `i` | Point/range read |
| Custom functions | `--function=<name>` | Any user-defined workload function |

The `i` parameter is the **cycle number** (from `--start-cycle` to `--end-cycle`).

### Finding Latte Scripts in SCT

1. **Upstream repo:** `scylladb/scylla-cluster-tests` → `data_dir/latte/`
2. **User forks:** If Jenkins job tag contains a username (e.g., `jsmolar-longevity-...`), check `<username>/scylla-cluster-tests` on the relevant branch
3. **Test config YAML:** The `prepare_write_cmd` / `stress_cmd` entries specify the `.rn` file path
4. **Branch identification:** Jenkins pipeline names often encode the branch name — look for it in the Argus test metadata or job URL

### Analyzing Latte Data Size from Script + Config

Given a latte script and test config, compute actual unique rows:

```
1. From script: ROW_COUNT, ROWS_PER_PARTITION, PARTITION_SIZES
2. From config: --start-cycle=S --end-cycle=E → cycles = E - S
3. Compute:
   n_partitions = ROW_COUNT / ROWS_PER_PARTITION
   unique_ck_per_partition = ROWS_PER_PARTITION / gcd(n_partitions, ROWS_PER_PARTITION)
   max_unique_rows = n_partitions × unique_ck_per_partition
   actual_unique_rows = min(max_unique_rows, cycles)
4. Per-row size: sum of all column sizes (check blob/text lengths in insert function)
5. Total data: actual_unique_rows × per_row_size
6. On-disk with RF: actual_unique_rows × per_row_size × RF (distributed across nodes)
```

**Always verify against Prometheus `scylla_column_family_live_disk_space`** — the calculation above gives logical uncompressed size; SSTable format adds ~20-50 bytes overhead per row but compression may reduce total.

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

### S3 metrics have a `class` label — always group by it (2026-05-04)
The `scylla_s3_total_*` metrics (GET/PUT/HEAD/DELETE requests, bytes, latency, retries) have a `class` label with values like `main`, `memtable`, `sl:default`. When computing counter deltas, if you key only by `(instance, shard)` and ignore `class`, multiple distinct series get merged into one list. This produces phantom deltas: e.g., the `class="main"` series stays at 0 while `class="memtable"` has actual values — the merged list shows `first=0, last=20578` = false delta of 20,578 per shard, when the real delta during that window was 0.
**Correct approach:** Always key S3 metric series by `(class, instance, shard)` — or at minimum, filter to the specific `class` value of interest (e.g., `class="sl:default"` for user-facing read/write traffic). Check all label dimensions with `sort -u` on the dump before aggregating.

### Always verify dataset size — never trust test names or Jira descriptions (2026-05-14)
The agent reported "20M rows × 10 × 512-byte blobs" based on the test name "100gb" and the table schema showing 10 blob columns. The actual on-disk size was **0.44 GB** (not 100 GB) — the latte script generated empty/tiny blobs. The test name was aspirational/leftover, and the schema alone doesn't reveal column value sizes.
**Correct approach:** (1) Check `scylla_column_family_live_disk_space` from Prometheus for the actual table. (2) Cross-reference native and S3 runs — if both show the same size, the metric is correct. (3) Compare `total_disk_space_before_compression` vs `live_disk_space` to check compression ratio. (4) Calculate per-row size = total / (unique_rows × RF) and compare against schema expectations. (5) If the latte script isn't available, derive blob sizes from on-disk evidence rather than assuming from schema.

### column_family disk metrics have NO shard label — don't key by shard (2026-05-14)
The `scylla_column_family_live_disk_space`, `total_disk_space`, `live_sstable`, and `tablet_count` metrics are per-instance per-table aggregates — they do NOT have a `shard` label. When extracting these, key by `instance` only. If you key by `(instance, shard)` you'll either get no matches or misparse the data.
**Correct approach:** For column_family metrics, use `awk` keyed on `instance` only. For most other ScyllaDB metrics (s3, sstables, cache, reactor), these DO have shard labels — check sample lines before writing extraction scripts.

### Latte partition distribution × ck computation creates GCD-based row collisions (2026-05-14)
With `PARTITION_SIZES="100:1"`, latte distributes rows round-robin across N partitions (stride=1). The `ck = idx % ROWS_PER_PARTITION` formula means partition `p` gets ck values `{(p + k*N) % ROWS_PER_PARTITION : k=0,1,...}`. The number of **unique** ck values per partition = `ROWS_PER_PARTITION / gcd(N, ROWS_PER_PARTITION)`. If `N` divides `ROWS_PER_PARTITION`, you get only `ROWS_PER_PARTITION/N` unique rows per partition — the rest are overwrites.
**Correct approach:** When analyzing latte workload data size: (1) compute `gcd(n_partitions, rows_per_partition)` to determine the overwrite multiplier, (2) unique_rows = `n_partitions × (rows_per_partition / gcd(n_partitions, rows_per_partition))`, but capped at actual cycle count. (3) Only if `end_cycle - start_cycle >= ROW_COUNT` are all rows populated. For this test: `gcd(1000, 30000)=1000` → 30 unique ck/partition × 1000 partitions = 30,000 total rows.

### When Jenkins job tag contains a username, check that user's fork first (2026-05-14)
The agent searched `scylladb/scylla-cluster-tests` upstream for a latte workload script, then searched GitHub code broadly — but the file only existed in `jsmolar/scylla-cluster-tests` on a feature branch. The Jenkins job tag (`jsmolar-longevity-v2-s3-keyspace...`) clearly contained the username.
**Correct approach:** When a Jenkins job name or branch identifier contains a GitHub username (e.g., `jsmolar-longevity-...`), immediately check that user's fork of the relevant repo at GitHub (e.g., `https://github.com/jsmolar/scylla-cluster-tests`). Feature branches with test configs are typically on personal forks before they land upstream.

### The latte benchmark tool lives at github.com/scylladb/latte (2026-05-14)
The agent couldn't find the latte tool repository when searching for "latte" under `org:scylladb` or broadly. GitHub search didn't surface it.
**Correct approach:** The latte CQL/Alternator benchmark tool is at `https://github.com/scylladb/latte`. Key source files: `src/scripting/functions_common.rs` (built-in functions like `blob()`, `text()`, `hash()`, `uuid()`), `src/scripting/row_distribution.rs` (partition row distribution logic), `src/scripting/mod.rs` (script engine setup). Latte uses the Rune scripting language (`.rn` files).
