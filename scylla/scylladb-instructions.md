# ScyllaDB Development Instructions

These instructions apply when working in the **scylladb/scylladb** repository (the main ScyllaDB C++ codebase). They supplement the repository-level `.github/copilot-instructions.md` and `.github/instructions/*.md`.

## Project Overview
ScyllaDB is a high-performance distributed NoSQL database (C++23, Seastar framework), API-compatible with Apache Cassandra (CQL) and Amazon DynamoDB (Alternator). Core values: **performance, correctness, readability**.

## Architecture — Key Components
- **`cql3/`** — CQL frontend: parser, grammar (`Cql.g`), statements, query processor
- **`alternator/`** — DynamoDB-compatible API layer
- **`service/storage_proxy.cc`** — Coordinator: routes reads/writes, interacts with `messaging_service` (RPC), `cdc`, `view`
- **`replica/`** — Replica-side: `database` and `table` classes (data storage)
- **`raft/`** — Raft consensus for topology/schema/metadata (replaces Gossip); `service/raft/` for Scylla-specific Raft integration
- **`sstables/`** — On-disk storage format (Sorted String Tables)
- **`compaction/`** — Compaction strategies and manager
- **`mutation/`** — Core data model: writes are mutations (timestamped diffs, combinable out-of-order)
- **`locator/`** — Replication strategies, tablets
- **`message/`** — Inter-node RPC; `idl/` defines message schemas compiled by `idl-compiler.py`
- **`seastar/`** — Git submodule: async framework (futures/promises, shared-nothing per-core architecture)
- **`schema/`** — Schema/metadata definitions (keyspaces, tables)
- **`dht/`** — Distributed hash table, token ring partitioning
- **`gms/`** — Gossip protocol (legacy, being replaced by Raft)
- **`vector_search/`** — Vector search client and filtering for vector-based queries
- **`tasks/`** — Task manager for internal background tasks (compaction, repair, etc.)
- **`rust/`** — Rust interop via CXX bridge (e.g., UDF support); see `docs/dev/rust.md`

Data flow: `cql3`/`alternator` → `storage_proxy` → `messaging_service` (RPC) → `replica/database` → `sstables`

## Build System

### configure.py + Ninja (primary)
```bash
./configure.py --mode=dev          # Configure (dev/debug/release/sanitize)
ninja build/dev/scylla             # Build Scylla binary (sufficient for Python tests)
ninja dev-build                    # Build everything including tests
ninja build/dev/test/boost/<name>  # Build specific C++ test binary
```

### CMake (alternative)
```bash
cmake -B build -DCMAKE_BUILD_TYPE=Dev    # Build types: Dev, Debug, RelWithDebInfo, Sanitize, Coverage
cmake --build build --target scylla      # Build Scylla binary
cmake --build build                      # Build everything
```
CMake also supports multi-config generators (e.g., Ninja Multi-Config). When adding/removing source files, update both `configure.py` and `CMakeLists.txt`. CMake is well-suited for IDE integration (CLion, etc.).

### Frozen toolchain (Docker)
Prefix any command with `./tools/toolchain/dbuild` to use the official build environment:
```bash
./tools/toolchain/dbuild ./configure.py --mode=dev
./tools/toolchain/dbuild ninja dev-build
```

### Building on ARM (aarch64 / AWS Graviton)

ScyllaDB builds natively on aarch64 Linux. The frozen toolchain image (`tools/toolchain/image`) is a multi-arch image that includes both `x86_64` and `aarch64` variants — Docker/Podman selects the correct one automatically on Graviton EC2 instances.

#### ARM-specific quirks

- **PGO profile absent**: `pgo/profiles/aarch64/profile.profdata.xz` is not included in the repo by default (Git LFS stub). The configure step will print:
  ```
  WARNING: pgo/profiles/aarch64/profile.profdata.xz is not an archive. Building without a profile.
  ```
  This is **expected and harmless** — the build proceeds without profile-guided optimization.

- **Silent phase after cmake outputs**: After configure prints the cmake outputs for Seastar and Abseil, there is a long *silent* phase (~5–20 minutes on Graviton2/3 depending on instance size) where configure.py:
  1. Generates the full `build.ninja` (pure Python — no output)
  2. Runs `ninja -t compdb` to generate `compile_commands.json` (no output)
  If the process appears "stuck" after the Abseil cmake output, it is **not hung — just working silently**. Verify it is still alive with:
  ```bash
  docker ps | grep scylla               # is the container still running?
  docker stats --no-stream              # CPU activity confirms progress
  ```

- **Instance size requirements**: Release builds need significant RAM. Each linker job can use 4+ GB. Recommended minimum:
  - `c7g.4xlarge` or `m7g.4xlarge` (16+ cores, 16+ GB RAM) for a comfortable build
  - `t4g.small`/`medium` will work but very slowly due to memory pressure

- **Native Ubuntu build (without Docker)**: If you prefer to skip the toolchain container:
  ```bash
  ./install-dependencies.sh        # installs all build deps on Ubuntu aarch64
  ./configure.py --mode release    # configure directly
  ninja build/release/scylla       # build
  ```

#### Personal ARM test instance (ernest's dev instance)

| Field | Value |
|-------|-------|
| **Instance ID** | `i-05ccc6ae22cf5bc94` |
| **Region** | `us-east-1` (N. Virginia) |
| **Type** | `c6g.8xlarge` (32 vCPUs, 64 GB RAM, Graviton2) |
| **OS** | Ubuntu 24.04 aarch64 |
| **SSH user** | `ubuntu` |
| **SSH key** | `~/.ssh/ernest.pem` (or `~/Downloads/ernest.pem`) |
| **AWS profile** | `797456418907-DevOpsAccessRole` |

The public IP **changes on each start**. After starting, retrieve the new IP:
```bash
aws --profile 797456418907-DevOpsAccessRole ec2 start-instances \
  --instance-ids i-05ccc6ae22cf5bc94 --region us-east-1

aws --profile 797456418907-DevOpsAccessRole ec2 wait instance-running \
  --instance-ids i-05ccc6ae22cf5bc94 --region us-east-1

aws --profile 797456418907-DevOpsAccessRole ec2 describe-instances \
  --instance-ids i-05ccc6ae22cf5bc94 --region us-east-1 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
```

When done, **stop the instance** (saves cost):
```bash
aws --profile 797456418907-DevOpsAccessRole ec2 stop-instances \
  --instance-ids i-05ccc6ae22cf5bc94 --region us-east-1
```

**Running tests on this instance** — requires `LD_LIBRARY_PATH` override because the Scylla
binary was built with the Fedora toolchain but Ubuntu's `libcares.so.2` is too old:
```bash
source ~/scylla-test-venv/bin/activate
cd ~/Development/scylladb
LD_LIBRARY_PATH=/usr/local/lib/scylla-toolchain ./test.py \
  --no-gather-metrics --mode release \
  test/cluster/object_store/test_backup.py::test_restore_tablets[gs-topology1]
```

Full setup details (Ubuntu-specific patches, library extraction, slapd config):
`scylla/arm-instance-setup.md` (in this instructions repo)

**AWS credentials** expire every ~6 hours. Ask the user for their Google Authenticator
code, then immediately run:
```bash
refresh-aws-creds <6-digit-totp-code>
```
Everything else is automated (password from `~/.config/gimme-aws-creds-pass`, factor=0, role=0).

### Common notes
- Source files and targets are tracked in `configure.py` (and `CMakeLists.txt`) — update when adding/removing files
- `test.py` does **not** auto-rebuild; you must build before running tests

### Rebuilding tests
- Many C++ tests share composite binaries (e.g., `combined_tests` in `test/boost/` contains multiple test files)
- To find which binary contains a test, check `configure.py` (primary source) or `test/<suite>/CMakeLists.txt`
- Rebuild a specific test binary: `ninja build/<mode>/test/<suite>/<binary_name>`
- Examples:
    - `ninja build/dev/test/boost/combined_tests` (contains `group0_voter_calculator_test.cc` and others)
    - `ninja build/dev/test/raft/replication_test` (standalone Raft test)

### Standalone vs combined tests
The build system used in CLion is **CMake** (`test/boost/CMakeLists.txt`). CLion knows nothing about `configure.py` — always use CMakeLists.txt to determine test targets.

To determine if a test is **standalone** (its own binary) or part of **combined_tests**:
1. Look in `test/boost/CMakeLists.txt` for the test name.
2. If it has its own `add_scylla_test(<test_name> KIND SEASTAR)` entry — it is a **standalone** binary.
3. If it is listed as a `SOURCES` entry under `add_scylla_test(combined_tests KIND SEASTAR SOURCES ...)` — it is part of the `combined_tests` binary.

Example standalone test:
```cmake
add_scylla_test(tablet_aware_restore_test
  KIND SEASTAR)
```
→ Build target: `ninja build/<mode>/test/boost/tablet_aware_restore_test`

Example combined test (part of `combined_tests`):
```cmake
add_scylla_test(combined_tests
  KIND SEASTAR
  SOURCES
    combined_tests.cc
    aggregate_fcts_test.cc
    ...
    database_test.cc
    ...)
```
→ Build target: `ninja build/<mode>/test/boost/combined_tests`

**Note:** `configure.py` has equivalent information but CLion doesn't use it. When in doubt, check `test/boost/CMakeLists.txt`.

### Build modes and sanitizers
| Mode | Sanitizers | Optimization | Purpose |
|------|-----------|--------------|---------|
| `dev` | None | `-O1` | Fast compilation for development |
| `debug` | ASan + UBSan | `-Og` | Finding memory errors, use-after-free, undefined behavior |
| `sanitize` | ASan + UBSan | `-Os` | Same sanitizers as debug but with optimizations |
| `release` | None | `-O3` | Production builds |

Both `debug` and `sanitize` link with `-fsanitize=address -fsanitize=undefined`. The `debug` mode is preferred for testing memory safety issues since it has no optimizations that might hide bugs. There is no MemorySanitizer (MSan) — only ASan and UBSan.

### Build system comparison tool
`scripts/compare_build_systems.py` verifies configure.py and CMake produce equivalent builds by parsing ninja files from both systems. It checks:
1. Per-file compilation flags
2. Link target sets
3. Per-target linker settings
4. IDL-generated file sets (from `idl-compiler.py`)

```bash
scripts/compare_build_systems.py -m dev      # Compare single mode (fast)
scripts/compare_build_systems.py             # Compare all modes
scripts/compare_build_systems.py --ci        # CI mode: quiet, strict
```

**When adding/removing IDL files:** update both the `idls` list in `configure.py` AND `idl/CMakeLists.txt`. The comparison tool now catches mismatches. See `docs/dev/compare-build-systems.md` for details.

### CMake precompiled header (PCH)
Both build systems use `stdafx.hh` as a precompiled header. In configure.py, this is applied via `-Xclang -include-pch` in the `cxx_with_pch.<mode>` rule. In CMake:
- `scylla-precompiled-header` target owns the PCH definition (`target_precompile_headers(... PRIVATE "stdafx.hh")`)
- Consumer targets (e.g., `scylla-main`) must explicitly reuse it: `target_precompile_headers(<target> REUSE_FROM scylla-precompiled-header)`
- Without `REUSE_FROM`, files relying on transitive includes from `stdafx.hh` will fail to compile under CMake

**Debugging CMake vs configure.py compile differences:** compare the compile commands:
- CMake: check `compile_commands.json` (generated in build dir, symlinked to repo root)
- configure.py: inspect `build.ninja` rules (`cxx_with_pch.<mode>` vs `cxx.<mode>`)

## Running Tests
```bash
./test.py --mode=dev test/boost/memtable_test.cc                    # C++ test file
./test.py --mode=dev test/boost/memtable_test.cc::test_case_name    # Single C++ test case
./test.py --mode=dev test/cqlpy/test_json.py                        # Python test file
./test.py --mode=dev test/cqlpy/test_json.py::test_function_name    # Single Python test
./test.py --mode=dev test/alternator/                                # All tests in directory
```
- Add `--no-gather-metrics` if cgroup permission errors occur
- New tests: validate stability with `--repeat 100 --max-failures 1`
- For Python tests, only `ninja build/dev/scylla` is needed (not full build)
- Direct execution of C++ tests: `build/dev/test/boost/<test_name> -t <test_case> -- -c1 -m1G`

## Test Suites
| Directory | Type | Description |
|-----------|------|-------------|
| `test/boost/` | C++ (Boost.Test) | Unit tests; white-box, internal API testing |
| `test/raft/` | C++ | Raft consensus unit tests |
| `test/unit/` | C++ | Stress and memory allocation tests (LSA, row cache) |
| `test/vector_search/` | C++ (Boost.Test) | Vector search client and filtering tests |
| `test/ldap/` | C++ | LDAP authentication/authorization tests |
| `test/cqlpy/` | Python (pytest) | Single-node CQL black-box tests |
| `test/alternator/` | Python (pytest) | Single-node DynamoDB API tests |
| `test/topology*/`, `test/cluster/` | Python (pytest) | Multi-node cluster tests |
| `test/nodetool/` | Python (pytest) | Nodetool command tests |
| `test/rest_api/` | Python (pytest) | Scylla REST API tests |
| `test/scylla_gdb/` | Python (pytest) | Tests for `scylla-gdb.py` helper script |
| `test/cql/` | CQL approval tests | Pre-recorded CQL input/output comparison |
| `test/perf/` | C++ | Microbenchmarks |

## Test Log Directory Structure (`testlog/`)

All test output goes under `testlog/` in the repository root. The structure is:

```
testlog/
├── <mode>/                              # e.g., dev/, debug/, release/
│   ├── failed_test/                     # Only failing tests are preserved here
│   │   └── <test_name>.<mode>.<run#>/   # One directory per failed test run
│   │       ├── pytest.log               # Python test framework log (pytest output)
│   │       ├── test_py.log              # test.py runner log
│   │       ├── stacktrace.txt           # Python exception traceback
│   │       └── scylla-<worker>-<id>.log # Scylla server log per node (e.g., scylla-gw16-13.log)
│   │                                    #   <worker> = pytest-xdist worker (gw0, gw16, etc.)
│   │                                    #   <id> = server number within the cluster
│   ├── allure/                          # Allure test report data
│   ├── <worker>.<suite>.<test>.<mode>.<run#>.log          # Per-test pytest log (all runs, not just failures)
│   ├── <worker>.<suite>.<test>.<mode>.<run#>_cluster.log  # Per-test cluster manager log
│   └── scylla-<worker>-<id>/           # Scylla node working directories (data, commitlog, etc.)
├── pytest_log/                          # Per-worker pytest logs (pytest_gw0_<hash>.log)
├── pytest_tests_logs/                   # Per-test teardown/setup logs (all tests, boost + cluster)
│   └── <suite>-<file>-<test>.dev.N-teardown-<hash>.log
├── sqlite_<hash>.db                     # SQLite database with test metrics (timing, CPU, memory)
├── s3_mock.log                          # S3/GCS mock server log (for object storage tests)
├── s3_proxy.log                         # S3 proxy log (toxiproxy)
├── minio.log                            # MinIO server log (for S3 tests)
└── report/                              # Test report output
    └── pytest_cpp_<hash>.xml            # JUnit XML: all tests with timing, skip status, skip reasons
```

### Key files for investigating test failures

1. **`testlog/<mode>/failed_test/<test_name>.<mode>.<run#>/`** — start here for failed tests:
   - `stacktrace.txt` — the Python exception/timeout traceback
   - `pytest.log` — test framework log with timestamps, cluster setup, API calls
   - `scylla-<worker>-<id>.log` — individual Scylla node logs (the most detailed; grep for `repair`, `raft_topology`, etc.)
   - `found_errors.txt` — summary of critical errors (ASAN, SEGV, abort) found across all server logs for this test. Format:
     ```
     Server <N>: found <count> critical error(s) (log: scylla-gw<W>-<N>.log)
       <first error line>
       <summary line>
     ```
     This file tells you WHICH server log to look at for the full error. Always fetch and analyze the referenced `scylla-gw<W>-<N>.log` for the full stack trace and context.

2. **Server log naming**: `scylla-gw<W>-<N>.log` where `W` is the pytest-xdist worker number and `N` is the server ID within that test's cluster (typically 13, 14, 15, 16 for a 4-node cluster)

3. **Server logs at top-level `testlog/<mode>/`**: In addition to server logs inside `failed_test/` directories, the same server logs are also available at `testlog/x86_64/<mode>/scylla-gw<W>-<N>.log` (Jenkins artifact path). When fetching from Jenkins, both paths may work depending on how artifacts are structured.
   - **Full Jenkins URL for top-level server logs:**
     ```
     https://jenkins.scylladb.com/job/scylla-master/job/scylla-ci/<BUILD>/artifact/testlog/x86_64/<mode>/scylla-gw<W>-<N>.log
     ```
   - This is the log you MUST link to in Jira issues and PR comments when `found_errors.txt` references it.

4. **Cluster log**: `<worker>.<suite>.<test>.<mode>.<run#>_cluster.log` in `testlog/<mode>/` — contains cluster manager operations (server add/stop/remove)

### Useful commands for log analysis
```bash
# Find all failed test directories
find testlog/<mode>/failed_test/ -maxdepth 1 -type d

# Search for specific patterns in Scylla server logs of a failed test
grep -n "repair\|error\|timeout" testlog/<mode>/failed_test/<test_dir>/scylla-*.log

# Extract lines around a specific timestamp
sed -n '5000,5100p' testlog/<mode>/failed_test/<test_dir>/scylla-gw16-13.log
```

#### Seastar log line format — use the scheduling group to separate workload phases

Every Scylla log line is prefixed by Seastar as:
`<LEVEL>  <YYYY-MM-DD HH:MM:SS,mmm> [shard <N>: <SG>] <logger> - <message>`

The `<SG>` field is the **scheduling group** abbreviation (space-padded), and it is invaluable for slicing a log by what the database was actually doing — without any code changes. Common abbreviations: `main` (main/control plane), `mt` (memtable/write path), `mt2c` (memtable-to-cache), `comp` (compaction), `strm` (streaming), `sl:*`/`st`-like names (statement/user query path). For example, S3 object requests issued while serving a user read appear in the statement group, while inserts/flush land in `mt` and compaction in `comp`.

Two practical techniques:
- **Phase isolation by SG**: when a test writes, flushes, compacts, then reads, filter log lines by the SG (e.g. exclude `mt`/`comp`/`mt2c`) to isolate read-path activity. Cross-check with timestamps of test phase markers from the pytest log (e.g. `Executing query ...` → `Query ... returned N rows`).
- **Tabulate SG × event**: `sed -E 's/.*\[shard [0-9]+: *([a-zA-Z0-9:_]+)\] <logger> - <verb> ([A-Z]+) .*/\1 \2/' | sort | uniq -c | sort -rn` gives a quick breakdown of which scheduling group is doing what.

### Retrieving per-test execution times

#### SQLite database (preferred for Boost/C++ tests)

Each test run produces a SQLite database at `testlog/sqlite_<hash>.db` (e.g., `sqlite_0104c.db`). The `<hash>` matches the log hash used in other log filenames. This is the most accurate source for Boost test timing data.

**Schema overview:**
- **`tests`** — test identity: `id`, `test_name`, `directory`, `mode`, `run_id`
- **`test_metrics`** — per-test measurements: `time_taken` (wall-clock, sub-ms precision), `user_sec`, `system_sec` (CPU breakdown), `memory_peak` (bytes), `time_start`, `time_end`, `success`
- **`system_resource_metrics`** — system-wide CPU/memory snapshots over time
- **`cgroup_memory_metrics`** — per-test cgroup memory usage over time

**Useful queries:**
```bash
# All tests sorted by duration (longest first)
sqlite3 -header -column testlog/sqlite_*.db "
  SELECT t.test_name, tm.time_taken, tm.user_sec, tm.system_sec,
         tm.memory_peak, tm.success
  FROM tests t JOIN test_metrics tm ON t.id = tm.test_id
  ORDER BY tm.time_taken DESC;"

# Only S3/GCS tests
sqlite3 -header -column testlog/sqlite_*.db "
  SELECT t.test_name, tm.time_taken, tm.memory_peak
  FROM tests t JOIN test_metrics tm ON t.id = tm.test_id
  WHERE t.test_name LIKE '%s3%' OR t.test_name LIKE '%gcs%'
  ORDER BY tm.time_taken DESC;"

# Summary statistics
sqlite3 -header -column testlog/sqlite_*.db "
  SELECT count(*) as count, sum(success) as passed,
         round(sum(time_taken),1) as total_sec,
         round(avg(time_taken),1) as avg_sec,
         round(max(time_taken),1) as max_sec
  FROM test_metrics;"
```

**Note:** The SQLite database currently only contains Boost/C++ test metrics (not cluster/Python tests). For a unified view of all tests (including cluster/Python), use the JUnit XML report (`testlog/report/pytest_cpp_<hash>.xml`) which has timing and skip status for everything.

#### pytest worker logs (for cluster/Python tests)

Cluster and Python test durations can be extracted from `testlog/pytest_log/pytest_gw<N>_<hash>.log`. Each worker log contains timestamped "before-test" markers and "SUCCEEDED"/"FAILED" entries.

**Important parsing details:**
- **before-test URLs use URL-encoding**: brackets appear as `%5B` and `%5D` — must use `urllib.parse.unquote()` to decode
- **Test names end with `.dev.<N>` suffix** (e.g., `test_foo[s3].dev.1`) — strip this for matching
- **Parametrize flavors**: `[local]`, `[s3]`, `[gs]` (note: GCS uses `gs`, not `gcs`)
- **A single worker runs multiple tests sequentially** — track pending start times by test name (dict), not a single variable
- **SUCCEEDED/FAILED line format**: `<timestamp>...Test <worker>::<test_name>.dev.<N> SUCCEEDED`
- **before-test line format**: `<timestamp>...[ScyllaClusterManager]...before-test/<url_encoded_name>`

```bash
python3 -u -c "
import re, os
from datetime import datetime
from urllib.parse import unquote

logdir = 'testlog/pytest_log'
# Find the most recent log set by picking any gw0 file
gw0_files = sorted([f for f in os.listdir(logdir) if f.startswith('pytest_gw0_')], key=lambda f: os.path.getmtime(os.path.join(logdir, f)), reverse=True)
if not gw0_files:
    print('No pytest worker logs found'); exit()
log_hash = gw0_files[0].split('_')[-1].replace('.log', '')

tests = {}
for f in sorted(os.listdir(logdir)):
    if not f.startswith('pytest_gw') or not f.endswith(f'_{log_hash}.log') or 'main' in f:
        continue
    with open(os.path.join(logdir, f)) as fh:
        lines = fh.readlines()
    pending = {}  # test_name -> start_time (handles sequential tests per worker)
    for line in lines:
        m = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+.*\[ScyllaClusterManager\].*before-test/([^\s>]+)', line)
        if m:
            ts = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
            raw_name = unquote(m.group(2))  # decode %5B -> [, %5D -> ]
            name = re.sub(r'\.dev\.\d+$', '', raw_name)  # strip .dev.1
            pending[name] = ts
            continue
        m2 = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+.*::([\w\[\]_.%\-]+)\.dev\.\d+\s+(SUCCEEDED|FAILED)', line)
        if m2:
            ts = datetime.strptime(m2.group(1), '%Y-%m-%d %H:%M:%S')
            name = m2.group(2)
            status = m2.group(3)
            if name in pending:
                dur = (ts - pending[name]).total_seconds()
                tests[name] = (dur, status)
                del pending[name]

for name, (dur, status) in sorted(tests.items(), key=lambda x: -x[1][0]):
    mark = '✅' if status == 'SUCCEEDED' else '❌'
    print(f'{dur:7.0f}s {mark} {name}')
print(f'\nTotal: {len(tests)} tests, {sum(1 for _,(d,s) in tests.items() if s==\"SUCCEEDED\")} passed, {sum(1 for _,(d,s) in tests.items() if s==\"FAILED\")} failed')
"
```

### Test flavor naming conventions (local / S3 / GCS)

Tests that exercise multiple storage backends have "flavors" — local filesystem, S3 (MinIO), and GCS (mock). The naming convention differs between Python and C++ tests:

- **Python tests** use pytest parametrize: `test_foo[local]`, `test_foo[s3]`, `test_foo[gs]`. The flavor is always inside brackets at the end.
- **C++ Boost tests** embed the flavor **in the test name itself** — either as a suffix or before a `_test` suffix:
  - Local: `test_compaction_strategy_cleanup_method` or `compaction_manager_stop_and_drain_race_test`
  - S3: `test_compaction_strategy_cleanup_method_s3` or `compaction_manager_stop_and_drain_race_s3_test`
  - GCS: `test_compaction_strategy_cleanup_method_gcs` or `compaction_manager_stop_and_drain_race_gcs_test`

When grouping C++ tests by flavor, strip `_s3` or `_gcs` from the name (first occurrence) to get the base (local) test name. The token is **not** always a suffix — it can appear before `_test`.

**Comparing parametrize flavors (local vs s3/gs):**
```bash
python3 -u -c "
# After collecting 'tests' dict as above, group by base name and compare flavors:
from collections import defaultdict
grouped = defaultdict(dict)
for name, (dur, status) in tests.items():
    m = re.match(r'(.+)\[(local|s3|gs)\]$', name)
    if m:
        grouped[m.group(1)][m.group(2)] = (dur, status)

for base, flavors in sorted(grouped.items(), key=lambda x: max(v[0] for v in x[1].values()), reverse=True):
    if 'local' in flavors and ('s3' in flavors or 'gs' in flavors):
        obj_key = 's3' if 's3' in flavors else 'gs'
        delta = flavors[obj_key][0] - flavors['local'][0]
        print(f'{base:<70} local={flavors[\"local\"][0]:>5.0f}s  {obj_key}={flavors[obj_key][0]:>5.0f}s  delta={delta:+.0f}s')
"
```

**Key points:**
- The log hash (e.g., `cd00f`) identifies a specific test run; the script auto-detects the most recent one
- Timestamps are second-granularity (from log lines), so sub-second tests show as 0–1s
- Skip `pytest_main_<hash>.log` (main process log, not a worker)
- Wall-clock time of the entire run: check timestamps of first and last "SUCCEEDED" entries across all worker logs

#### pytest_tests_logs (per-test teardown logs)

`testlog/pytest_tests_logs/` contains one log file per test case (both Boost and cluster), named `<suite>-<file>-<test>.dev.N-teardown-<hash>.log`. These contain setup/teardown output and the last 300 lines of C++ test stdout (for Boost tests). Timestamps are embedded in log lines:
- **Boost tests:** `INFO  2026-05-10 10:29:01,869 ...` (Seastar logger format)
- **Cluster tests:** `10:29:50.651 \x1b[32mINFO\x1b[0m> ...` (pytest format with ANSI color codes)

Duration can be computed from first-to-last timestamp in each file. Note that cluster test timestamps include ANSI escape codes that must be handled in regex patterns.

#### JUnit XML report (definitive skip detection + accurate timing)

The test run produces a JUnit XML report at `testlog/report/pytest_cpp_<hash>.xml` (e.g., `pytest_cpp_cd00f.xml`). This is the **authoritative source** for:
- **Skipped tests**: `<testcase>` elements containing a `<skipped>` child element with a `message` attribute and `<properties>` containing `skip_reason` and `skip_type`.
- **Accurate per-test timing**: the `time` attribute on each `<testcase>` (sub-second precision).
- **Test identity**: `classname` (e.g., `cluster.test_tablets_migration`), `name` (full parametrized name), and `function_path`.

**Structure of a skipped test entry:**
```xml
<testcase classname="cluster.test_tablets_migration"
          name="test_node_failure_during_tablet_migration[gs-revert_migration-destination].dev.1"
          time="10.761"
          function_path="test/cluster/test_tablets_migration.py::test_node_failure_during_tablet_migration">
  <properties>
    <property name="skip_type" value="env" />
    <property name="skip_reason" value="GCS flavor of this test gets stuck, deeper investigation is needed" />
  </properties>
  <skipped type="pytest.skip" message="[env] GCS flavor of this test gets stuck, deeper investigation is needed">...</skipped>
</testcase>
```

**Important:** Skipped tests still have a non-zero `time` attribute (time spent in setup/teardown before the skip was triggered). **Never use duration heuristics** to detect skips — always check for the `<skipped>` element in the XML.

**Useful queries:**
```python
import xml.etree.ElementTree as ET

tree = ET.parse('testlog/report/pytest_cpp_<hash>.xml')
root = tree.getroot()

# Get all skipped tests with reasons
for tc in root.iter('testcase'):
    skip_el = tc.find('skipped')
    if skip_el is not None:
        print(f"{tc.get('name')}: {skip_el.get('message')}")

# Get all non-skipped tests sorted by duration
tests = [(tc.get('name'), float(tc.get('time', 0)))
         for tc in root.iter('testcase') if tc.find('skipped') is None]
for name, t in sorted(tests, key=lambda x: -x[1])[:20]:
    print(f"{t:7.1f}s  {name}")
```

**Key points:**
- The XML covers **all tests** (both Boost/C++ and cluster/Python) in a single file
- `skip_type` values: `"env"` (environment/infrastructure reason), `"bug"` (known bug reference)
- When comparing flavors (local vs s3 vs gs), always exclude skipped tests from timing comparisons — their `time` value is meaningless for performance analysis
- The `<hash>` in the filename matches the hash used in pytest worker logs and other log files

## Useful `test.py` Command-Line Arguments

```bash
# Basic usage
./test.py --mode=dev test/cluster/test_tablets_migration.py::test_name

# Repeat a test N times (for flakiness investigation)
./test.py --mode=dev --repeat 100 test/path.py::test_name

# Stop after first failure (useful with --repeat)
./test.py --mode=dev --repeat 100 --max-failures 1 test/path.py::test_name

# Verbose output
./test.py --mode=dev -v test/path.py::test_name

# Keep logs even for passing tests (default: only failed test logs are kept)
./test.py --mode=dev --save-log-on-success test/path.py::test_name

# Filter tests by expression (pytest -k style)
./test.py --mode=dev -k "use_new and destination" test/cluster/test_tablets_migration.py

# Pass extra Scylla command-line options to ALL tests
./test.py --mode=dev --extra-scylla-cmdline-options='--logger-log-level repair=trace' test/path.py

# Pass additional pytest arguments
./test.py --mode=dev --pytest-arg="-v -x" test/path.py

# Limit parallelism (useful for debugging)
./test.py --mode=dev -j 1 test/path.py::test_name

# Custom timeout for long tests
./test.py --mode=dev --timeout 3600 test/path.py::test_name

# Skip tests matching pattern
./test.py --mode=dev --skip "slow_test" test/path.py
```

**Important notes:**
- `test.py` does **not** auto-rebuild; build before running
- `--save-log-on-success` is essential when you need passing-test logs for comparison
- `--extra-scylla-cmdline-options` applies to all Scylla nodes in all tests; for per-test logging, modify the test's `cmdline` parameter instead
- Failed test logs are in `testlog/<mode>/failed_test/`; passing test logs are deleted unless `--save-log-on-success` is used
- The `--no-gather-metrics` flag may be needed if cgroup permission errors occur

## Code Style

C++ and Python style are governed by the repository's own instruction files, which Copilot auto-loads when you edit matching files. **Do not duplicate or restate them here** — follow them directly:
- `.github/copilot-instructions.md` — project values, build/test commands, license header
- `.github/instructions/cpp.instructions.md` — C++ style, Seastar patterns, memory management, error handling, naming, forbidden constructs
- `.github/instructions/python.instructions.md` — Python style and testing conventions

Always match the existing style of the file and directory you edit. Some directories (e.g. `test/cqlpy`, `test/alternator`) deliberately omit type hints and docstrings.

### ScyllaDB-specific reminders (not always emphasized in the repo files)
- `seastarx.hh` brings in `using namespace seastar;` — do **not** prefix Seastar symbols with `seastar::`
- Headers must be self-contained — verify with `ninja dev-headers`
- Prefer `bool_class<Tag>` over raw `bool` parameters; use strong typedefs for IDs and domain types
- All background work must have `stop()`/`close()` to await completion; bound the memory of concurrent operations

## Lint and Formatting Tools

- **clang-format**: config in `.clang-format`; run `clang-format --style=file -i <file>` (only format code you modify)
- **Header self-containedness**: `ninja dev-headers` (after adding/removing headers, `touch configure.py` first)
- **License header**: new `.cc`, `.hh`, `.py` files must contain `LicenseRef-ScyllaDB-Source-Available-1.1` in the first 10 lines
- **clang-tidy**: runs in CI on PRs; checks `bugprone-use-after-move`
- **Build system alignment**: `scripts/compare_build_systems.py` — when reviewing or making changes to `CMakeLists.txt`, `configure.py`, or `cmake/mode.*.cmake`, run this script to verify both build systems stay in sync (see below)

## Build System Verification (Agent Review Checklist)

When a PR touches build system files (`CMakeLists.txt`, `configure.py`,
`cmake/mode.*.cmake`, `test/*/CMakeLists.txt`), verify alignment:

```bash
scripts/compare_build_systems.py    # configures both systems in a temp dir, compares all modes
```

If the user pastes the script's summary output showing mismatches, fix them:
1. **Sources only in configure.py** → add the missing source to the appropriate `CMakeLists.txt`
2. **Sources only in CMake** → add the missing source to `configure.py` (or remove the erroneous CMake entry)
3. **Link targets only in one side** → add the missing test/binary to the other build system
4. **Library diffs** → trace which `target_link_libraries` call adds the extra library and fix or remove it
5. **Compilation flag diffs** → align defines/flags in `cmake/mode.*.cmake` or `CMakeLists.txt`

After fixing, re-run the script to confirm all modes show `✓ MATCH`.
Commit each fix to the commit it logically belongs to.
See `docs/dev/compare-build-systems.md` for full documentation.

## Commit Organization, PR Cover Letter, and Refine PR

These topics are covered in the **global agent instructions** (`global-agents.instructions.md`). The global rules apply here with the following ScyllaDB-specific additions:

### ScyllaDB Module Prefixes
Common module prefixes for commit messages: `db:`, `sstables_loader:`, `raft:`, `cql3:`, `compaction:`, `sstables:`, `locator:`, `alternator:`, `service:`, `replica:`, `test:`, `dht:`, `gms:`, `message:`.

### Formatting Commits (C++)
When creating pure-formatting commits, always use the project's `.clang-format` rather than formatting by hand:
```bash
# Format specific lines in a file
clang-format --style=file -i --lines=<start>:<end> <file>

# Format an entire file (use with caution)
clang-format --style=file -i <file>
```
Key `.clang-format` settings to be aware of: `AlignAfterOpenBracket: Align` (arguments align to opening paren), `BinPackArguments: false` / `BinPackParameters: false` (one arg per line when wrapping), `ColumnLimit: 160`, `IndentWidth: 4`.

### PR Issue References
Use full JIRA URLs for issue references: `Fixes: https://scylladb.atlassian.net/browse/SCYLLADB-986`.

### Doxygen Comments
Never add Doxygen-style `///` comments to declarations/definitions unless the project already uses `///` in that file or the user explicitly requests it. The project convention for regular comments is `//`.

## Test Philosophy
- **No sleeps** — use condition-based waiting; sleeps cause flakiness and slow tests
- **Deterministic** — avoid random inputs; tests must be repeatable
- **Focused** — unit tests should ideally test one thing and one thing only
- **Minimal resources** — prefer single-node tests when sufficient
- **Bug fix tests** — must reference the issue (GitHub/JIRA) in comments, and demonstrate failure before the fix
- **Debug mode** is slower — reduce iterations/data size for debug builds

## Decoding Backtraces from Production/Test Logs

When investigating crashes (SEGV, abort, etc.) from ScyllaDB test runs or production logs, raw backtraces contain only hex addresses. Use the remote symbolization service to decode them into source file/line information.

### Finding the Build ID

The build ID is typically found in the `coredumps.info` file or system logs. Look for lines like:
```
BuildID[sha1]=f8c51f5b98a5dd972f7354a334146c46096d8919
```
Or extract it from the Scylla binary itself.

### Decoding via Remote Service

Send the raw backtrace with the build ID to the backtrace symbolization API:

```bash
curl -s -X POST https://staging.backtrace.scylladb.com/api/backtrace \
  -H "Content-Type: application/json" \
  -d '{
    "build_id": "<BUILD_ID_HEX>",
    "input": "<RAW_LOG_LINES_WITH_BACKTRACE>"
  }'
```

The `input` field should contain the raw log lines including the "Backtrace:" header and all address lines (e.g., `0x55c6e07`, `/opt/scylladb/libreloc/libc.so.6+0x1a28f`), with `\r\n` as line separators.

The response JSON contains a `stdout` field with the fully symbolized backtrace, including function names, source files, and line numbers, as well as inlined frames.

### Example

```bash
curl -s -X POST https://staging.backtrace.scylladb.com/api/backtrace \
  -H "Content-Type: application/json" \
  -d '{
    "build_id": "f8c51f5b98a5dd972f7354a334146c46096d8919",
    "input": "2026-03-28T21:12:14.404 node3  !INFO | scylla[35648] Backtrace:\r\n2026-03-28T21:12:14.404 node3  !INFO | scylla[35648]   0x55c6e07\r\n2026-03-28T21:12:14.404 node3  !INFO | scylla[35648]   0x1a68df4"
  }' | python3 -m json.tool
```

**Always decode backtraces before analyzing crashes** — raw addresses are not useful for diagnosis.

## Creating a Pull Request (ScyllaDB)

### Checklist
When creating a PR in `scylladb/scylladb`, always perform these steps:

> ❌ **STRICTLY PROHIBITED: Never push to remote (`git push` / `git push --force`) unless the user explicitly asks you to push.** All local commits, amends, and rebases are fine, but publishing to a remote branch is the user's decision.

1. **Push the branch** to the user's fork (e.g., `origin`) — **only when the user explicitly asks to create/push the PR**.
2. **Create the PR as a draft** (`draft: true`) targeting `master` on `scylladb/scylladb`.
3. **Set `maintainer_can_modify: true`** — required for CI and maintainer collaboration.
4. **Assign the PR** to the user who opened it (`--add-assignee <username>`).
5. **Apply labels:**
   - **`ai-assisted`** — always add when any part of the PR was AI-assisted
   - **`area/*`** — match the subsystem (e.g., `area/build`, `area/raft`, `area/cql`, `area/alternator`, `area/compaction`, `area/sstable`, `area/streaming`, etc.)
   - **`backport/none`** — if the PR cover letter states no backport is needed (new features, refactoring, build-only changes)
   - **`backport/<version>`** — if backporting is needed (bug fixes affecting released versions)
   - Other labels as appropriate: `bug`, `enhancement`, `type/code_cleanup`, `area/test`
6. **PR cover letter** must follow the format in the global instructions (Problem → Changes → Issue reference → Backport decision). The backport decision and the label **must be consistent**.

### Commands reference
```bash
# Push branch
git push origin <branch-name>

# Assign + label (using gh CLI — no MCP equivalent for labels)
gh pr edit <number> --add-assignee <username> --add-label "ai-assisted" --add-label "area/build" --add-label "backport/none"
```

### MCP tools for PR creation
```
create_pull_request  → create the PR (set draft=true, maintainer_can_modify=true)
update_pull_request  → enable maintainer_can_modify after creation if forgotten
```

### Common area labels
| Label | When to use |
|-------|-------------|
| `area/build` | Changes to configure.py, CMakeLists.txt, cmake/, build scripts |
| `area/test` | Test infrastructure, test utilities, test framework |
| `area/raft` | Raft consensus, group0, topology coordinator |
| `area/cql` | CQL parser, statements, query processor |
| `area/alternator` | DynamoDB-compatible API |
| `area/compaction` | Compaction strategies and manager |
| `area/sstable` | SSTable format, readers, writers |
| `area/streaming` | Streaming, repair-based operations |
| `area/schema_changes` | Schema mutations, schema tables |
| `area/topology_changes` | Node join/leave/replace/decommission |
| `type/code_cleanup` | Pure refactoring, no behavior change |

## Key Files for Orientation
- `docs/dev/repository_layout.md` — Full directory-by-directory guide
- `docs/dev/modules.md` — Module interaction diagram
- `docs/dev/review-checklist.md` — Code review standards
- `configure.py` — Build targets, test binary mappings, source file registry
- `test/README.md` — Test suite organization and `suite.ini` conventions
- `.github/copilot-instructions.md` — Primary AI assistant instructions
- `.github/instructions/cpp.instructions.md` — Detailed C++ rules
- `.github/instructions/python.instructions.md` — Detailed Python rules
- `CONTRIBUTING.md`, `HACKING.md` — Contributor onboarding

## SCYLLADB Jira Project Reference

### Field IDs (discovered via `getJiraIssueTypeMetaWithFields`, 2026-05-13)

| Field | ID / Key | Notes |
|-------|----------|-------|
| **Issue types** | Task=`10011`, Sub-Task=`10012`, Bug=`10013`, Story=`10014`, Epic=`10000` | |
| **Hierarchy** | Epic (level 1) → Task/Bug/Story (level 0) → Sub-Task (level -1) | No epic-under-epic |
| **Team** | `customfield_10001` (type: team) | **Broken via MCP** — see below |
| **Scylla components** | `customfield_10321` (multiselect) | Object Storage=`11501` |
| **T-Shirt Size** | `customfield_10985` (radio) | XS=`11985`, S=`11986`, M=`11987`, L=`11988`, XL=`11989` |
| **Priority** | P1=`1`, P2=`2`, P3=`4`, P4=`5` | |
| **Parent epic** | `parent` field | e.g., `{"key": "SCYLLADB-412"}` |

### Team field workaround (MCP)

Setting `customfield_10001` (Team) via `createJiraIssue` fails with `"Team id 'JsonData{data={id=...}}' is not valid."` regardless of format (`{"id": "UUID"}` or `{"id": "UUID", "name": "Name"}`).

**Workaround:** Omit `customfield_10001` when creating issues via MCP. Set the Team field manually in Jira after creation. All other custom fields work fine: `customfield_10321` as `[{"id": "ID"}]`, `customfield_10985` as `{"id": "ID"}`, and `priority` as `{"id": "ID"}`.


## CI Failure Analysis

### Context

When PR CI fails, `scylladbbot` posts two comments:
1. **Status report** — raw Jenkins data: stage table, failed test list, Elasticsearch historical failure rates
2. **AI analysis follow-up** — verdicts per test (Known flaky / Pre-existing / Infrastructure / Unrelated)

**The follow-up analysis cannot be trusted.** It matches by test name only, without verifying that the error signature (stack trace, error message) matches the linked Jira issue. This leads to:
- Marking genuinely new bugs as "Known flaky" (e.g., `test_raft_snapshot_truncation` linked to SCYLLADB-1471 when the actual failure was completely different)
- Developers skipping investigation of real regressions
- Erosion of trust in the CI system

### Our Analyzer: Design Principles

We build a **first-class CI failure analyzer** that the agent runs when the user asks to analyze CI failures. The key differentiator: **match by error signature, not just test name**.

#### Verdict Categories
| Verdict | Criteria | Action |
|---------|----------|--------|
| **Known issue** | Same test + same error message/stack trace pattern as an open Jira issue | Link Jira issue, safe to re-trigger |
| **Likely known** | Same test + similar (but not identical) error pattern; or same test failing on `next` with same error | Link probable Jira issue, flag for quick manual verification |
| **Infrastructure** | Disk full, OOM, worker crash, network timeout unrelated to test logic | Safe to re-trigger |
| **New failure** | No matching Jira issue; error pattern not seen before or only on this PR | Requires investigation; may need new Jira issue |
| **PR-related** | Test touches code paths modified by the PR; error is new | Definite regression, fix needed |

#### Data Sources
1. **Jenkins API** (`jenkins.scylladb.com`, auth in `~/.netrc`) — test report with full `errorDetails` + `errorStackTrace`
2. **Jira** (Atlassian MCP) — search for open issues matching the error pattern
3. **Elasticsearch data** (from bot's Comment 1) — historical failure rates, timestamps, nodes
4. **PR diff** (GitHub MCP) — which files/functions the PR modifies (to determine if failure could be PR-related)
5. **`next` pipeline status** — if the same test fails on `next` (no PR involved), it's pre-existing

#### Error Signature Extraction

From Jenkins `errorDetails` + `errorStackTrace`, extract:
1. **Exception type** — e.g., `RuntimeError`, `TimeoutError`, `HTTPError`, `AssertionError`
2. **Key error message** — the first meaningful line (strip paths, timestamps, node IDs)
3. **Failure location** — file:line where the assertion/error fires (from stack trace)
4. **Error pattern** — normalized form for comparison (strip run-specific data like UUIDs, ports, PIDs)

Example normalization:
```
Raw:    "failed to start the node, server_id 120, IP 127.7.187.6, workdir scylla-gw6-120, host_id c4c5fc8c-..."
Normal: "failed to start the node, server_id <N>, IP <IP>, workdir scylla-gw<W>-<N>, host_id <UUID>"
```

#### Workflow

When the user says **`$analyze-ci`** (or asks to analyze CI failures):

1. **Parse the bot's status comment** — extract failed test names and Jenkins build URL
2. **Fetch failure details from Jenkins API** — for each failed test, get `errorDetails` + `errorStackTrace`
3. **Classify infrastructure failures** — detect disk full, OOM, worker crash patterns:
   - `"no space left on device"` or `"Critical disk utilization"`
   - `"Out of memory"` or worker crash with no test output
   - `"control_connection is not None"` assertion (known infra bug SCYLLADB-2065)
4. **Extract error signatures** — normalize each failure's error pattern
5. **Search Jira** — for each non-infra failure:
   - Search by test name + key error phrases
   - Compare the Jira issue description/comments against the actual error signature
   - Only declare "Known issue" if the **error pattern matches**, not just the test name
6. **Check `next` pipeline** — if the same test+error appears on `next` recently, it's pre-existing
7. **Check PR overlap** — compare failed test's code path against PR's changed files
8. **Produce verdict table** — with evidence links for each determination

#### Jenkins API Patterns

```bash
# Get test report for a build
curl -s --netrc "https://jenkins.scylladb.com/job/scylla-master/job/scylla-ci/<BUILD>/testReport/api/json?tree=suites[cases[name,className,status,errorDetails,errorStackTrace,duration]]"

# Get specific failed test details
curl -s --netrc "https://jenkins.scylladb.com/job/scylla-master/job/scylla-ci/<BUILD>/testReport/junit/<package>/<class>/<test>/api/json"

# Get build info (SCM changes, parameters)
curl -s --netrc "https://jenkins.scylladb.com/job/scylla-master/job/scylla-ci/<BUILD>/api/json"
```

#### Jira Search Patterns

```
# Search for open issues matching a test name and error pattern
text ~ "test_name" AND text ~ "key_error_phrase" AND status != Done

# Search by Scylla component
project = SCYLLADB AND "Scylla components" = "Object Storage" AND text ~ "error_pattern"
```

#### Infrastructure Failure Signatures (auto-detect)

| Pattern | Verdict |
|---------|---------|
| `no space left on device` | Infrastructure: disk full |
| `Critical disk utilization: rejected write` | Infrastructure: disk full |
| `WORKER CRASHED` or `gw<N> crashed` | Infrastructure: worker OOM |
| `assert server.control_connection is not None` | Infrastructure: SCYLLADB-2065 |
| All failures on same node + same timestamp range | Infrastructure: node-wide issue |
| `Failed to add server` + OOM in server log | Infrastructure: OOM |

#### Output Format

```markdown
## CI Failure Analysis — Build #<N>

| # | Test | Verdict | Evidence |
|---|------|---------|----------|
| 1 | `test_foo.dev.1` | **Known issue** | [SCYLLADB-1234] — same `TimeoutError` in `repair.cc:456`. Jira has identical stack. |
| 2 | `test_bar.dev.5` | **Infrastructure** | Disk full on spider7 — all 32 failures on same node |
| 3 | `test_baz[s3].dev.2` | **New failure** | `S3 request failed: 404 Not Found` — never seen before. PR modifies `sstables/sstables.cc`. Needs investigation. |
| 4 | `test_qux.dev.79` | **Likely known** | Same test fails on `next` (job#10889, 2 days ago) with similar error. Probable: [SCYLLADB-2074] |

### Recommendation
- Tests 1, 2, 4: Safe to re-trigger (`@scylladbbot trigger-ci`)
- Test 3: Investigate — may be a regression introduced by this PR
```

### Deep Investigation Workflow (for "New failure" verdicts)

When a failure is classified as **New failure**, perform a full investigation to gather enough information for a high-quality Jira issue.

#### Step 1: Identify the build commit

Extract the exact commit SHA from the Jenkins build. This is the revision the tests ran against — **never use the local working copy** for investigation.

```bash
# Get the build's SCM revision
curl -s --netrc "https://jenkins.scylladb.com/job/scylla-master/job/scylla-ci/<BUILD>/api/json?tree=actions[lastBuiltRevision[SHA1],buildsByBranchName[*[*]]]" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for action in data.get('actions', []):
    rev = action.get('lastBuiltRevision', {}).get('SHA1')
    if rev:
        print(rev)
        break
"
```

Use GitHub MCP `get_file_contents` with `sha=<commit>` (or `ref=<commit>`) to read source files at that exact revision. **Do not** use the local checkout — the test may have run against a different version of the code.

#### Step 2: Navigate Jenkins artifacts to get test logs

Test logs are stored as build artifacts with a structure mirroring local `testlog/`:

```
https://jenkins.scylladb.com/job/scylla-master/job/scylla-ci/<BUILD>/artifact/testlog/x86_64/<mode>/failed_test/<test_dir>/
```

**Constructing the test directory name** from the Jenkins test report URL:
- Test report URL: `.../testReport/junit/<package>/<class>/Unit_Tests_Custom___<mode>___<test_name>__<mode>_<iteration>/`
- Extract: test name, pytest params, mode, iteration
- Test name anatomy: `test_foo[param].mode.iteration`
- Artifact URL encoding: `[` → `(`, `]` → `)` in the directory name

Example:
```
Test: test_split_and_incremental_repair_synchronization[True].dev.89
URL:  .../artifact/testlog/x86_64/dev/failed_test/test_split_and_incremental_repair_synchronization(True).dev.89/
```

**Fetching the artifact directory listing:**
```bash
curl -s --netrc "https://jenkins.scylladb.com/job/scylla-master/job/scylla-ci/<BUILD>/artifact/testlog/x86_64/<mode>/failed_test/<test_dir>/" \
  | grep -oP 'href="[^"]*"' | grep -v '\.\.'
```

**Key files to fetch (in priority order):**
1. `stacktrace.txt` — Python exception traceback (quick overview)
2. `pytest.log` — full test framework log with timestamps
3. `scylla-<worker>-<id>.log` — Scylla server logs (the real diagnostic data)

```bash
# Fetch a specific artifact file
curl -s --netrc "https://jenkins.scylladb.com/job/scylla-master/job/scylla-ci/<BUILD>/artifact/testlog/x86_64/<mode>/failed_test/<test_dir>/<filename>"
```

#### Step 3: Analyze server logs

**CRITICAL RULES:**
- **State facts only.** Never speculate about causes. If the cause is not obvious from the logs, say "cause unclear — needs further investigation."
- **Check errors/warnings first** — grep for `ERROR` and `WARN` level messages. These are the primary diagnostic data.
- **Ignore reactor stalls** during initial analysis. Stalls on dev/debug builds are routine and expected (dev mode has `-O1`, debug has `-Og`). Only mention stalls if they directly correlate with important events AND exceed extreme thresholds (>10s).
- **Trace the test logic** through the logs. The test code defines what SHOULD happen; the logs show what DID happen. Find where they diverge.
- **Never assume infrastructure issues.** The fact that nodes become unreachable doesn't mean "overloaded worker" — trace the actual cause through the logs.

**Analysis order:**
1. **Grep for ERROR/WARN** — these are the facts:
   ```bash
   grep "^ERROR\|^WARN" /tmp/scylla_server.log
   ```
2. **Trace the test's code path through the logs** — the test uses injections, API calls, and log waits. Find each step in the server log:
   - Did the injection get enabled? (`debug_error_injection`)
   - Did the expected operation start? (e.g., `load_balancer`, `raft_topology`, `repair`)
   - Where did it stop progressing?
3. **Identify the blocking point** — what was the last thing the server was doing when it stopped making progress?
4. **Check for crashes** (only if nodes went down):
   - `Segmentation fault` / `SIGSEGV` → crash, decode backtrace
   - `Aborting` / `SIGABRT` / `SCYLLA_ASSERT` → assertion failure
   - `std::bad_alloc` → OOM
   - Process simply stopped logging → check if it was killed externally

If a crash backtrace is found, decode it using the backtrace symbolization service (see "Decoding Backtraces" section above). The build ID can be extracted from the server log's startup banner or `coredumps.info` artifact.

**Key principle:** The analysis must follow the test's logic. Read the test code, understand what sequence of events it expects, then verify in the logs whether each step happened. The point of divergence is where the bug is.

#### Step 4: Examine the relevant source code at build revision

Once you identify the failing code path (from stack traces, error messages, or log context):

1. **Read the source at the build's commit** — use GitHub MCP:
   ```
   get_file_contents(owner="scylladb", repo="scylladb", path="<file>", sha="<build_commit>")
   ```
   
2. **Read the test source** at the same commit to understand test expectations:
   ```
   get_file_contents(owner="scylladb", repo="scylladb", path="test/<suite>/<test_file>", sha="<build_commit>")
   ```

3. **Trace the failing code path** — follow the call chain from the error location. Understand what the code is supposed to do and why it might have failed.

**Never analyze using local files** unless you've verified they match the build commit. The local tree may have diverged (rebased, amended, or on a different branch).

#### Step 5: Determine ownership via file history

To assign the Jira issue correctly, identify who owns the relevant code:

```bash
# Check recent commits to the failing file (using GitHub MCP)
list_commits(owner="scylladb", repo="scylladb", path="<failing_file>", perPage=10)

# Or via gh CLI for blame info
gh api repos/scylladb/scylladb/commits?path=<file>&per_page=10 --jq '.[].author.login'
```

**Assignment heuristic (in priority order):**
1. **Author of the triggering change** — if git blame shows a recent commit that introduced/modified the failing code path, assign to that author
2. **Most active recent contributor** — the person with the most commits to the file in the last 3-6 months
3. **Test author** — if the test itself is new or recently modified, the test author may own the area
4. **Module owner** — based on CODEOWNERS or team knowledge (e.g., `raft/` → Raft team, `sstables/` → Storage team)

Use `list_commits` with `path=` to get recent contributors. Cross-reference with `git blame` output (via `get_file_contents` at specific lines if needed).

#### Step 6: Create Jira issue

Create a **high-quality Jira issue** with all gathered evidence:

**Title format:** `<module>: <concise description of the failure>`

**Description structure:**
```markdown
### Failure
- **Test:** `test_name[params].mode.iteration`
- **Build:** [#BUILD](https://jenkins.scylladb.com/job/scylla-master/job/scylla-ci/BUILD/)
- **Commit:** `<sha>` (link to GitHub)
- **First seen:** <date> (or "first failure in N runs" from Elasticsearch data)
- **Frequency:** <N failures in M runs over period> (or "first occurrence")

### Error
```
<cleaned-up error message / stack trace>
```

### Analysis
<what the investigation revealed — timeline, root cause hypothesis, affected code path>

### Relevant code
- `<file>:<line>` — <brief description of what this code does>
- Recent change: <commit SHA> by @<author> — "<commit message>" (if a recent change is suspicious)

### Logs
- [pytest.log](<artifact URL>)
- [scylla server log](<artifact URL>)
- [stacktrace.txt](<artifact URL>)
```

**Jira fields:**
- **Project:** SCYLLADB
- **Type:** Bug
- **Priority:** P2 (default for test failures; P1 if crash/data loss; P3 if cosmetic)
- **Assignee:** do NOT set — Jira automation assigns team and assignee automatically based on Scylla components
- **Team:** do NOT set — same as above
- **Labels:**
  - `CI-Stability` — primary label for all CI test failures (capital C, hyphen)
  - `ci_stability` — also add (underscore variant, used by some dashboards)
  - `ai-assisted` — always add when the issue is created/analyzed by the AI agent
- **Problem Symptom:** `ci stability` (custom field if available)
- **Scylla components:** match the module (`customfield_10321`) — this drives automatic team/assignee routing

#### Summary of the full investigation flow

```
Jenkins test report → error signature → artifacts (logs) → server crash analysis
    → source code at build commit → code path tracing → file history for ownership
    → Jira issue creation with full evidence
```

## Jenkins BYO Job — Triggering Custom Builds and Tests

The **`byo_build_tests_dtest`** job ("Bring Your Own") at
`https://jenkins.scylladb.com/job/scylla-master/job/byo/job/byo_build_tests_dtest/`
is a fully configurable CI job that builds Scylla from any branch and runs any combination of
unit tests, cluster/Python tests (`test/cluster/`, `test/cqlpy/`, etc.), and dtests on real
Fedora CI nodes — including **aarch64 Graviton** workers. This is the right tool for:
- Reproducing a flaky test with many repetitions
- Running tests on aarch64 (native Fedora, no Ubuntu workarounds)
- Running a single specific test in debug/dev mode

### Authentication

Jenkins credentials are stored in `~/.netrc`:
```
machine jenkins.scylladb.com
  login ernest.zaslavsky@scylladb.com
  password <JENKINS_API_TOKEN>
```

All API calls use `--user "ernest.zaslavsky@scylladb.com:<token>"` (Basic Auth). The token
is a Jenkins API token, NOT an SSO password.

### Triggering a Build via API

Jenkins requires a **CSRF crumb** for every POST. Always fetch it fresh immediately before triggering:

```bash
CRUMB=$(curl -s --user "ernest.zaslavsky@scylladb.com:<JENKINS_API_TOKEN>" \
  "https://jenkins.scylladb.com/crumbIssuer/api/json" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['crumb'])")

curl -v --user "ernest.zaslavsky@scylladb.com:<JENKINS_API_TOKEN>" \
  -H "Jenkins-Crumb: $CRUMB" \
  -X POST \
  "https://jenkins.scylladb.com/job/scylla-master/job/byo/job/byo_build_tests_dtest/buildWithParameters" \
  --data-urlencode "BUILD_ARM=true" \
  --data-urlencode "BUILD_MODE=debug" \
  --data-urlencode "RUN_UNIT_TESTS=true" \
  --data-urlencode "INCLUDE_TESTS=test/cluster/object_store/test_backup.py::test_restore_tablets[gs-topology1]" \
  --data-urlencode "ARM_NUM_OF_UNITTEST_REPEATS=1000" \
  --data-urlencode "RUN_DTEST=false" \
  --data-urlencode "INCLUDE_DTESTS=" \
  --data-urlencode "DEBUG_MAIL=true" \
  --data-urlencode "DEFAULT_BRANCH=master"
```

A successful trigger returns **HTTP 201 Created** with a `Location: .../queue/item/<N>/` header.
Wait a few seconds and resolve the queue item to get the actual build number:

```bash
curl -s --user "ernest.zaslavsky@scylladb.com:<JENKINS_API_TOKEN>" \
  "https://jenkins.scylladb.com/queue/item/<N>/api/json" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); exe=d.get('executable'); print(exe['url'] if exe else 'still queued')"
```

### Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `BUILD_ARM` | bool | `false` | Build and run tests on **aarch64 Fedora** CI nodes |
| `BUILD_MODE` | choice | `release` | `release` / `debug` / `dev` / `ALL` |
| `RUN_UNIT_TESTS` | bool | `true` | Run `test.py` tests (covers ALL test suites: boost, cluster, cqlpy, etc.) |
| `INCLUDE_TESTS` | string | *(all)* | Specific test(s) to run via `test.py` — e.g., `test/cluster/object_store/test_backup.py::test_restore_tablets[gs-topology1]`. Leave empty for all. |
| `ARM_NUM_OF_UNITTEST_REPEATS` | string | `1` | Number of repetitions per test on ARM. Use `1000` for flakiness investigations. |
| `X86_NUM_OF_UNITTEST_REPEATS` | string | `1` | Same but for x86_64. |
| `UNIT_TESTS_MARKERS` | string | `"not non_gating"` | pytest `-m` expression to filter tests. Default skips non-gating. |
| `RUN_DTEST` | bool | `true` | Set `false` to skip Cassandra-style dtests entirely. |
| `INCLUDE_DTESTS` | string | `-m 'not skip and next_gating'` | dtest filter (irrelevant when `RUN_DTEST=false`). |
| `DEFAULT_BRANCH` | choice | `master` | Default branch for all repos. |
| `SCYLLA_FORK_REPO` + `SCYLLA_FORK_BRANCH` | string | *(empty)* | Use a fork/branch instead of main scylla.git. |
| `DEBUG_MAIL` | bool | `true` | Send results only to the triggering user (not `jenkins-notifications@`). Keep `true`. |
| `GATHER_METRICS` | bool | `true` | Collect test metrics. |
| `CREATE_*` | bool | `false` | Package/image creation flags — keep all `false` for test-only runs. |

### Checking Build Status / Parameters

```bash
# Check if a build is still running and see its parameters
curl -s --user "ernest.zaslavsky@scylladb.com:<JENKINS_API_TOKEN>" \
  "https://jenkins.scylladb.com/job/scylla-master/job/byo/job/byo_build_tests_dtest/<BUILD>/api/json" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Building:', d.get('building'), '  Result:', d.get('result'))
for a in d.get('actions', []):
    for p in (a.get('parameters') or []):
        if p.get('value') not in (None, '', False, 1, True):
            print(f'  {p[\"name\"]} = {p[\"value\"]}')
"
```

### Stopping a Build

```bash
CRUMB=$(curl -s --user "ernest.zaslavsky@scylladb.com:<JENKINS_API_TOKEN>" \
  "https://jenkins.scylladb.com/crumbIssuer/api/json" | python3 -c "import sys,json; print(json.load(sys.stdin)['crumb'])")

curl -s --user "ernest.zaslavsky@scylladb.com:<JENKINS_API_TOKEN>" \
  -H "Jenkins-Crumb: $CRUMB" \
  -X POST \
  "https://jenkins.scylladb.com/job/scylla-master/job/byo/job/byo_build_tests_dtest/<BUILD>/stop"
```

### Important Caveats

- **Parameters are defined in pipeline code, not the GUI.** The GUI shows stale values from the last run. Always submit parameters explicitly via API; never rely on GUI defaults reflecting the current pipeline.
- **Concurrent builds are allowed** (`concurrentBuild: true`) — multiple BYO builds can run simultaneously.
- **`INCLUDE_TESTS` works for all `test.py` test types** — boost C++ tests (`test/boost/foo.cc::test_case`), cluster Python tests (`test/cluster/foo.py::test_case`), cqlpy, alternator, etc. The format mirrors `./test.py` invocation.
- **aarch64 CI nodes are native Fedora** — no Ubuntu workarounds needed, unlike the personal ARM EC2 instance.

---

## `$debunk` — PR Bot Comment Triage Workflow

### Trigger
User says `$debunk <URL>` where URL is a PR bot comment containing CI failure results (e.g., `$debunk https://github.com/scylladb/scylladb/pull/NNN#issuecomment-XXXX`).

### Workflow

**For each failed test in the bot's comment:**

1. **Check bot's Jira link** — did the bot claim a matching issue exists?
2. **Analyze the actual failure** — fetch error details from Jenkins (error message, stack trace, key log snippets from artifacts)
3. **Verify bot's claim (if Jira link present):**
   - Read the linked Jira issue description/comments
   - Compare the actual error signature (exception type, message, stack location) against the Jira issue
   - ✅ **Match** → verdict: "Confirmed — matches [SCYLLADB-NNNN]"
   - ❌ **No match** → verdict: "Mismatch — bot linked [SCYLLADB-NNNN] but error signature differs. Candidate for new issue."
4. **If no Jira link from bot** → candidate for new issue
5. **Always search Jira** — regardless of bot's claim, search for:
   - Test name (exact and partial)
   - Key error message phrases
   - Exception type + failing module
   - This catches cases where an issue exists but the bot missed it

### Output (draft file for user review)

Save to `~/.config/JetBrains/CLion2026.1/scratches/GitHubCopilot/analyze-ci-PR<number>-build<N>.md`:

1. **Verdict table** — one row per failed test with: test name, verdict, evidence summary, Jira link (existing or "new needed")
2. **For "new issue" candidates** — full Jira issue draft (following the template in "Step 6: Create Jira issue" above)
3. **Draft PR reply comment** — concise response to be posted on the PR, summarizing findings

### User approval → execution

After user reviews and approves:
1. Create Jira issues for approved "new issue" candidates
2. Post the reply comment on the PR (via `add_issue_comment` with PR number)

### Important rules
- **Never trust the bot's verdict** — always verify by comparing actual error signatures
- **Never create Jira issues without user approval** — always draft first
- **Never post PR comments without user approval** — always draft first
- **Copy critical log snippets into Jira issues** — Jenkins artifacts expire in ~2 weeks
- **Infrastructure failures** (disk full, OOM, worker crash) don't need Jira issues — just note in the reply
- **Identifying the latest CI failure:** compare **build numbers** (higher = newer), not comment position. The latest failure is the bot CI result comment with the highest build number. Ignore non-CI comments (user replies, analysis)  when determining which is the latest.
- **CI retrigger:** If the analyzed comment is the **latest** CI failure on the PR, ask the user if they want to retrigger CI. If yes, append `@scylladbbot trigger-ci` at the end of the PR reply comment.
- **Duplicate detection:** Before starting analysis, check if a reply to the bot's CI result comment already exists from the user (`kreuzerkrieg`) or contains a verdict table (markdown table with "Verdict" column). If so, warn the user: "This comment was already debunked — see [link to existing reply]. Want me to redo it?" Do NOT proceed without confirmation.

