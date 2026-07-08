# ScyllaDB Disk Usage — Accounting Reference

Reference for reconciling **`df` / `du` / Grafana dashboards / `nodetool`** disk-space
numbers on a ScyllaDB node. Written 2026-07-08 after a confused investigation on
cluster #6958 where `/var/lib/scylla` showed 94 GiB used but column_family metrics
accounted for only ~2 GiB.

## The Core Rule

**There is no single Scylla metric that equals `du -sh /var/lib/scylla`.**
Scylla only reports the categories of files *it manages*. Anything outside those
categories is invisible to Scylla-side metrics but visible to the OS.

## The Metrics That DO Exist

| Metric | Covers |
|---|---|
| `scylla_column_family_live_disk_space` | live sstables (per shard × table — sum by instance to get node total) |
| `scylla_column_family_total_disk_space` | live + obsolete (pending-deletion) sstables |
| `scylla_commitlog_disk_total_bytes` | data commitlog, incl. preallocated segments |
| `scylla_schema_commitlog_disk_total_bytes` | schema commitlog |
| `scylla_node_filesystem_size_bytes` − `scylla_node_filesystem_avail_bytes` (per `mountpoint`) | what `df` sees for that mount |

Naming quirks:
- The metric is `scylla_column_family_live_disk_space` — **no `_used` suffix** (unlike what dashboards sometimes label them).
- `scylla_hints_manager_size_of_hints_in_progress` is an **in-memory** gauge, NOT on-disk hint file size. There is no aggregate on-disk hints metric.

## What's NOT Reported by Any Scylla Metric

These will make `du` larger than the sum of Scylla metrics — sometimes by huge
amounts:

1. **Snapshots** (`/var/lib/scylla/data/*/*/snapshots/*`) — hard-linked sstables
   from `nodetool snapshot`, Scylla Manager backups, or auto-snapshots before
   `TRUNCATE`/`DROP`. **Single biggest source of drift in practice.**
   Verify with: `nodetool listsnapshots`
2. **Scylla Manager backup staging** — `upload/` / `staging/` subdirs being
   uploaded to S3.
3. **View-build hints** — `view_hints/` directory on disk.
4. **On-disk hint files** — the metric is in-memory only.
5. **Coredumps** — on cloud/dbaas nodes `/var/lib/systemd/coredump` is often
   **bind-mounted onto the same volume as `/var/lib/scylla`**. A single Scylla
   coredump can be tens of GiB (dumps the full seastar memory pool). Check for
   this first when the gap is very large. Verify: `ls -lh /var/lib/systemd/coredump/`.
6. **Preallocated / zero-filled commitlog segments** — active-bytes gauges may
   not count them.
7. **Filesystem overhead** — XFS journal, inode tables, reserved blocks,
   `lost+found`. Small but nonzero.
8. **Foreign files** an operator dropped in place — old tarballs, `sstabledump`
   output, orphaned files from crashed compactions.

## Dashboard Panel → Metric Mapping (Common Confusions)

The **"Detailed" dashboard** exposes several panels whose names hint at "disk"
or "bytes" but come from different subsystems. Confirm the metric before drawing
conclusions.

| Panel label (approx.) | Actual metric | Notes |
|---|---|---|
| Total Bytes / Used Bytes (Sum by Instance), in a **Memory** row | `scylla_lsa_total_space_bytes` / `scylla_lsa_used_space_bytes` | **RAM**, not disk. LSA = Log-Structured Allocator: memtable + cache reserved pool. |
| Disk Space / SSTable Size | `scylla_column_family_live_disk_space` | Live sstables only |
| Filesystem Used / Available | `scylla_node_filesystem_size_bytes` − `scylla_node_filesystem_avail_bytes` | This is what matches `df`. Break down by `mountpoint` label — summing across all mounts double-counts because e.g. `/var/lib/systemd/coredump` is often a bind mount from the same volume as `/var/lib/scylla`. |

**Guideline:** Before interpreting any "bytes" panel, click Edit → read the
PromQL. Never assume from the label.

## Recipe for Reconciling `du` vs Prometheus

For a specific node `$IP` in cluster `$C`:

```promql
# 1. What df says for the data volume
(scylla_node_filesystem_size_bytes{cluster="$C",instance="$IP",mountpoint="/var/lib/scylla"}
 - scylla_node_filesystem_avail_bytes{cluster="$C",instance="$IP",mountpoint="/var/lib/scylla"})
 / (1024*1024*1024)

# 2. What Scylla accounts for
sum(scylla_column_family_live_disk_space{cluster="$C",instance="$IP"}) / (1024*1024*1024)
+ sum(scylla_commitlog_disk_total_bytes{cluster="$C",instance="$IP"}) / (1024*1024*1024)
+ sum(scylla_schema_commitlog_disk_total_bytes{cluster="$C",instance="$IP"}) / (1024*1024*1024)

# 3. Difference = snapshots + coredumps + hints on disk + staging + FS overhead + foreign
```

If the difference is large, in order of likelihood investigate:
1. **Coredumps** — `ls -lh /var/lib/systemd/coredump/` on the node (or check if
   the mount is bind-mounted onto `/var/lib/scylla`).
2. **Snapshots** — `nodetool listsnapshots` (`True size` column).
3. **Hints on disk** — `du -sh /var/lib/scylla/hints/ /var/lib/scylla/view_hints/`.
4. **SM staging** — `du -sh /var/lib/scylla/data/*/*/upload/ /var/lib/scylla/data/*/*/staging/`.
5. **Foreign files** — `du -xh --max-depth=1 /var/lib/scylla/ | sort -h`.

## Multi-Mount Trap When Summing Filesystem Metrics

`sum by (instance) (scylla_node_filesystem_size_bytes - scylla_node_filesystem_avail_bytes)`
sums **every mount** the node exposes: `/`, `/boot/efi`, `/run/*`,
`/var/lib/scylla`, `/var/lib/systemd/coredump`, etc. On cloud nodes the coredump
directory is a **bind mount** from the data volume, so its size is reported
identically to `/var/lib/scylla` — summing them double-counts the data volume.

Always filter by `mountpoint` when you want a specific meaning:
- `mountpoint="/var/lib/scylla"` → the ScyllaDB data volume
- `mountpoint="/"` → root FS (OS, logs, package files)

## Per-Shard Metric Multiplication Trap

`scylla_column_family_*_disk_space` is emitted **per shard × per keyspace ×
per table**. `sum by (instance)` is the correct aggregate for these — do not
add another `by (shard)` unless you want per-shard values. For a per-node
total: `sum by (instance) (scylla_column_family_live_disk_space{...})`.

