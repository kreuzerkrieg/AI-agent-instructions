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

2. **Server log naming**: `scylla-gw<W>-<N>.log` where `W` is the pytest-xdist worker number and `N` is the server ID within that test's cluster (typically 13, 14, 15, 16 for a 4-node cluster)

3. **Cluster log**: `<worker>.<suite>.<test>.<mode>.<run#>_cluster.log` in `testlog/<mode>/` — contains cluster manager operations (server add/stop/remove)

### Useful commands for log analysis
```bash
# Find all failed test directories
find testlog/<mode>/failed_test/ -maxdepth 1 -type d

# Search for specific patterns in Scylla server logs of a failed test
grep -n "repair\|error\|timeout" testlog/<mode>/failed_test/<test_dir>/scylla-*.log

# Extract lines around a specific timestamp
sed -n '5000,5100p' testlog/<mode>/failed_test/<test_dir>/scylla-gw16-13.log
```

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

## Code Conventions
- **Seastar namespace**: `seastarx.hh` imports `using namespace seastar;` — do **not** prefix Seastar symbols with `seastar::`
- **Coding style**: [Seastar coding style](https://github.com/scylladb/seastar/blob/master/coding-style.md) — snake_case, 4-space indent
- **Headers must be self-contained**: each header compilable independently; verify with `ninja dev-headers`
- **Commit messages**: `module: short description` format (e.g., `sstables: close fd on error`)
- **Comments**: explain "why", not "what"; code should be self-documenting via clear naming
- **Prefer standard library** over custom implementations; add complexity only when clearly justified
- **Question requests**: don't blindly implement — evaluate trade-offs, identify issues, and suggest better alternatives when appropriate
- **Concurrency**: all background work must have `stop()`/`close()` to await completion; bound memory usage of concurrent ops
- **Hot paths**: avoid allocations, unbounded loops without preemption yields; use `seastar::future<>` properly
- **Invariant checking**: assert for critical invariants, throw for recoverable ones, log for ignorable

## C++ Code Style

**Important:** Always match the style and conventions of existing code in the file and directory.

### Naming
- `snake_case` for classes, functions, variables, namespaces, constants/constexpr
- `CamelCase` for template parameters (e.g., `template<typename ValueType>`)
- `_prefix` for private member variables (e.g., `int _count;`)
- No prefix for struct (value-only) members
- Files: `.hh` for headers, `.cc` for source

### Formatting
- 4 spaces indentation, never tabs; 160 character line limit
- K&R braces (opening on same line); brace all scopes, even single statements
- Namespace bodies not indented; closing `} // namespace name`
- `#pragma once` for all headers (no `#ifndef` guards)
- Continuation indent: 8 spaces (double indent)
- Space after keywords (`if (`, `while (`), not after function names
- Minimal patches: only format code you modify, never reformat entire files

### Include Order
1. Own header first (for `.cc` files)
2. C++ standard library (`<vector>`, `<map>`)
3. Seastar headers with angle brackets (`<seastar/core/future.hh>`)
4. Boost headers
5. Project-local headers with quotes (`"db/config.hh"`)

Forward declare when possible. Never `using namespace` in headers.

### Memory Management
- Stack allocation preferred; `std::unique_ptr` by default for dynamic allocations
- `new`/`delete` forbidden — use RAII
- `seastar::lw_shared_ptr` for shared ownership within same shard
- `seastar::foreign_ptr` for cross-shard; avoid `std::shared_ptr`

### Seastar Async Patterns
- `seastar::future<T>` for all async operations
- Prefer coroutines (`co_await`/`co_return`) over `.then()` chains
- `seastar::gate` for shutdown coordination; `seastar::semaphore` for resource limiting
- `maybe_yield()` in long loops to avoid reactor stalls; no blocking calls
- `sstring` (not `std::string`); `logging::logger` per module
- Many files include `seastarx.hh`, which introduces common Seastar names; follow existing file/local conventions for `seastar::` qualification

### Error Handling
- Throw exceptions for errors (futures propagate them automatically)
- In data path: use `std::expected` or `boost::outcome` instead of exceptions
- `SCYLLA_ASSERT` for critical invariants (`utils/assert.hh`)
- `on_internal_error()` for should-never-happen conditions

### Type Safety
- `bool_class<Tag>` instead of raw `bool` parameters
- `enum class` always (never unscoped `enum`)
- Strong typedefs for IDs and domain-specific types

### Forbidden
`malloc`/`free`, `printf`, raw owning pointers, `using namespace` in headers,
blocking ops (`std::sleep`, `std::mutex`), `std::atomic`, new ad-hoc macros (prefer `constexpr`/inline functions; established project macros like `SCYLLA_ASSERT` are fine).

## Python Code Style

- PEP 8; 160 character line limit; 4 spaces indentation
- Import order: standard library, third-party, local (never `from x import *`)
- Type hints for function signatures (unless directory style omits them — e.g., `test/cqlpy`, `test/alternator`)
- f-strings for formatting
- `@pytest.mark.xfail` for currently-failing tests; unmark when fixed
- Descriptive test names; docstrings explain what the test verifies and why

## Lint and Formatting Tools

- **clang-format**: config in `.clang-format`; run `clang-format --style=file -i <file>` (only format code you modify)
- **Header self-containedness**: `ninja dev-headers` (after adding/removing headers, `touch configure.py` first)
- **License header**: new `.cc`, `.hh`, `.py` files must contain `LicenseRef-ScyllaDB-Source-Available-1.0` in the first 10 lines
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

These topics are covered in the **global agent instructions** (`global-agents-instructions.md`). The global rules apply here with the following ScyllaDB-specific additions:

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
