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
├── pytest_tests_logs/                   # Per-test teardown/setup logs
├── s3_mock.log                          # S3/GCS mock server log (for object storage tests)
├── s3_proxy.log                         # S3 proxy log (toxiproxy)
├── minio.log                            # MinIO server log (for S3 tests)
└── report/                              # Test report output (allure)
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

## Commit Organization

### Principles
- Each commit should contain **one logical change** — if the commit message needs "and" or "also", that's a hint it may need to be split further.
- Every commit **must compile** and **pass all tests** (bisectability). Never leave the tree in a broken state between commits.
- A reviewer should be able to understand each commit in isolation without reading the full PR first.
- Order commits so that each builds on the previous — **dependencies flow forward**.

### Commit Message Format

#### Structure
```
module: short imperative description
                                        ← blank line is REQUIRED
Optional longer body explaining *why* the change is needed and any
non-obvious design decisions. Wrap at ~72 characters.

Fixes #1234          (optional: reference to GitHub/JIRA issue)
```

**Caution with `git commit -m`:** A single `-m` flag puts everything on one line. To get the blank line, either use an editor (`git commit` without `-m`), or pass two separate `-m` flags:
```bash
git commit -m "module: short description" -m "Body explaining why."
```

#### Subject line (first line)
- **Module prefix** matches the directory or subsystem being changed: `db:`, `sstables_loader:`, `test:`, `raft:`, `cql3:`, `compaction:`, `sstables:`, `locator:`, etc.
- Multiple modules: `cql3, transport: fix ...` — whole tree: `tree: ...`
- Keep it short — ~50 characters is ideal, 72 is the hard max.
- Use **imperative mood**: "add", "fix", "remove", "extract", "change" — not "added", "fixes", "removing".
- Describe *what* the commit does, not *how* — the diff shows the how.
- Do **not** end with a period.

#### Body (optional but encouraged for non-trivial changes)
- Separated from the subject by **one blank line**.
- Explains **why** the change is needed — motivation, context, trade-offs.
- Does **not** repeat what is obvious from the diff (avoid "changed X to Y in file Z").
- Wrap lines at ~72 characters for readability in `git log`.
- For bug-fix commits, reference the issue: `Fixes #1234` or `Refs scylladb/scylladb#1234`.

#### Examples

Good:
```
db: extract snapshot_sstables TTL into class constant

Move the TTL value used for snapshot_sstables rows from a local
variable in insert_snapshot_sstable() to a class-level constant
SNAPSHOT_SSTABLES_TTL_SECONDS, making it reusable by other methods.
```
```
sstables_loader: change sys_dist_ks to sharded reference

This allows accessing the distributed keyspace from any shard via
.local(), which will be needed to update SSTable download status
from within invoke_on_all.
```
```
test: verify progress reporting in tablet restore test
```

Bad:
```
fix stuff                              # no module prefix, vague
```
```
db: Added new column and method.       # past tense, period, "and" → split
```
```
sstables_loader: Change the _sys_dist_ks member from
db::system_distributed_keyspace& to sharded<...>&, update all
callers to use .local(), and also clean up includes
                                       # too long, mechanics not motivation, "and also" → split
```

### What Belongs in a Single Commit
- A pure refactoring (extract constant, rename, move code)
- A new type, struct, or method (declaration + implementation)
- A signature change and all its callers updated together
- A feature wired into its call site
- A test for the feature
- A pure formatting change

### What Must Be Separate Commits
- **Formatting vs. functional changes** — if you add an `if` statement and have to re-indent the code block under it, that's two commits: (1) add the `if` with minimal formatting, (2) fix indentation. Similarly, if adding arguments makes a function call too long: (1) add the arguments, (2) reformat/wrap lines.
- **Refactoring vs. new functionality** — extract a constant or change a type first, then use it.
- **Schema/data model changes vs. business logic** — add a new column/field first, then the code that uses it.
- **Infrastructure changes vs. feature code** — change a parameter type (e.g., `T&` → `sharded<T>&`) in one commit, use the new capability in the next.
- **Tests vs. implementation** — test changes in their own commit (unless trivially small and tightly coupled).

### How to Split Commits for Review

When preparing commits for contribution — whether splitting a single WIP
commit or reorganizing a series of commits that don't follow the
granularity guidelines above — use this procedure.

#### 1. Analyze the diff
```bash
git diff HEAD~1 HEAD          # Review the full change
git diff HEAD~1 HEAD --stat   # See which files changed
```

#### 2. Identify logical groups
Categorize each change into one of:
- **Pure refactoring** — extracting constants, renaming, moving code without behavior change
- **Schema/model changes** — new columns, struct fields, type changes
- **Formatting** — re-indentation, line wrapping, whitespace-only changes
- **New methods/APIs** — declarations + implementations of new functionality
- **Infrastructure/plumbing** — type changes, include cleanup, parameter changes
- **Feature wiring** — connecting new APIs to call sites
- **Tests** — new or updated test assertions

#### 3. Determine dependency order
Build a dependency graph: which changes require others to compile?
```
refactoring → schema changes → new methods → plumbing → wiring → tests
                                              ↑
                                    formatting (independent)
```

#### 4. Execute the split
```bash
# Save the current state
git stash                              # Stash any uncommitted work
WIP_SHA=$(git rev-parse HEAD)          # Remember the WIP commit

# Reset to parent
git reset --hard HEAD~1

# For each logical commit, apply just those changes:
#   - Use python/sed for precise file edits, or
#   - Copy the final file state and use `git add -p` for partial staging
#   - Verify with: diff <(git show $WIP_SHA:<file>) <file>

# After all commits, verify the final state matches the original:
git diff $WIP_SHA HEAD --stat          # Should be empty or trivial whitespace
```

#### 5. Verify
- `git log --oneline` — read commit subjects as a story; each should make sense alone.
- `git diff <original_wip> HEAD --stat` — final state should match the original (or improve on it).
- If you find yourself writing "and" or "also" in a commit message, that's a hint you may need to split further.

### Example Split

A WIP commit that "adds download tracking with progress reporting" might split into:

| Order | Commit | Type |
|-------|--------|------|
| 1 | `db: extract snapshot_sstables TTL into class constant` | Refactoring |
| 2 | `db: add downloaded column to snapshot_sstables` | Schema change |
| 3 | `db: reformat read_row lambda in get_snapshot_sstables` | Formatting |
| 4 | `db: add update_sstable_download_status method` | New API |
| 5 | `sstables_loader: clean up includes` | Include cleanup |
| 6 | `sstables_loader: change sys_dist_ks to sharded reference` | Plumbing |
| 7 | `sstables_loader: return shared_sstable from attach_sstable` | Plumbing |
| 8 | `sstables_loader: mark sstables as downloaded after attaching` | Feature wiring |
| 9 | `sstables_loader: add progress tracking to tablet restore task` | Feature |
| 10 | `test: verify progress reporting in tablet restore test` | Test |

### Formatting Commits
When creating pure-formatting commits, always use the project's `.clang-format` rather than formatting by hand:
```bash
# Format specific lines in a file
clang-format --style=file -i --lines=<start>:<end> <file>

# Format an entire file (use with caution)
clang-format --style=file -i <file>
```
Key `.clang-format` settings to be aware of: `AlignAfterOpenBracket: Align` (arguments align to opening paren), `BinPackArguments: false` / `BinPackParameters: false` (one arg per line when wrapping), `ColumnLimit: 160`, `IndentWidth: 4`.

### Common Pitfalls
- **Mixing formatting with logic** — the #1 review complaint. Always separate.
- **Changing a signature and adding new callers in the same commit** — split into: (1) change signature + update existing callers, (2) add new callers.
- **Including unrelated cleanup** — include hygiene (adding missing `#include`s, removing duplicates), trailing whitespace fixes, or other mechanical cleanup must be in their own commit. Even if you're already touching the same file for a functional change, don't bundle cleanup into it — the "also" in your commit message ("change type, and also clean up includes") is a clear signal to split.
- **Reordering functions alongside functional changes** — never reorder (move) function definitions in the same commit that applies functional changes to the code. Reordering inflates the diff, obscures the real change, and makes review painful. If reordering is necessary, put it in a separate commit.
- **Giant "add feature" commits** — break into: model → API → wiring → tests.
- **Forgetting compilability** — after planning the split, mentally verify that removing any later commit leaves a compiling tree.

### Minimal Diffs — Do Not Touch What You Don't Need To
- **Never rename existing variables** unless the rename is the explicit purpose of the commit. If a variable is called `cln`, keep it `cln`; do not rename it to `client` (or vice versa) just because you think it reads better. Gratuitous renames inflate the diff and add reviewer burden for zero functional value.
- **Never change comment style** without a functional reason. Do not replace `//` with `///` (or vice versa), do not rephrase comments that already convey the same meaning, and do not "beautify" or reword comments whose content is not changing. Leave existing comments untouched unless the code they describe is changing.
- **Never add or remove blank lines, comments, or commented-out code** that is unrelated to the task. If it existed before and is not part of the change, leave it as-is.
- **Never add Doxygen-style `///` comments** to declarations/definitions unless the project already uses `///` in that file or the user explicitly requests it. The project convention for regular comments is `//`.
- **Preserve existing code structure** — do not reorder includes, reorder function parameters, or change formatting unless that is the explicit task.
- In short: the diff should contain **only** the lines required for the functional change. Every extra line the reviewer has to read is wasted effort.

### Handling Review Comments — Think Before You Apply
- **Never blindly apply review comments.** Invest time in understanding what the reviewer is actually asking and whether the comment is correct. Reviewers can misread the code, misunderstand the intent, or miss context that you (the author) have.
- **Verify the reviewer's assumptions.** Does the reviewer understand how the internal machinery works? Did they trace the actual code path, or are they guessing based on a surface reading? For example, a reviewer may claim "this will throw because X calls Y" — check whether X actually calls Y in this context before changing anything.
- **Evaluate whether the suggestion improves correctness or just reshuffles code.** Some review comments are cosmetic preferences disguised as bug reports. If a comment would cause you to split a simple function into two clients, add extra semaphores, or restructure working code with no measurable benefit, push back or ask for clarification.
- **Consider whether the change would break the test's intent.** Tests are written a specific way for a reason. If a reviewer suggests "use a separate client here", ask yourself whether the test is *supposed* to exercise the fixture with that exact semaphore — maybe the whole point is to verify the fixture handles constrained resources.
- **Dead code observations may be wrong.** A parameter that looks unused in one function may exist because callers rely on the signature for consistency, or because it documents an intent that will be used in a follow-up. Don't delete parameters just because a reviewer says "dead code" — verify the full picture first.
- **When in doubt, present your reasoning to the user** rather than silently applying the change. Say "the reviewer suggests X, but I believe the current code is correct because Y — should I apply it anyway?"

## PR Cover Letter

Every GitHub PR needs a **title** and a **description body**. The description should give a reviewer enough context to understand the change without reading every commit first.

### Title
Use the same `module: short description` format as commit messages. If the PR spans multiple modules, use the primary one or a broader scope (e.g., `sstables_loader: add progress tracking to tablet restore task`).

### Body Format
- The PR body is rendered as **GitHub Markdown** — use `###` headings, `**bold**`, backtick-quoted symbols, etc.
- Do **not** hard-wrap lines in the PR body; let GitHub handle wrapping. Each paragraph should be a single long line.
- This is different from commit message bodies, which are wrapped at ~72 characters.

### Body Structure

1. **Problem** — what is broken, missing, or inadequate. One or two sentences.
2. **Changes** — a summary of what the series does, grouped logically. Not a commit-by-commit list — describe the *what* and *why* at a higher level than individual commits.
3. **Issue reference** — `Fixes: <URL>` on its own line. Use the full JIRA URL (e.g., `Fixes: https://scylladb.atlassian.net/browse/SCYLLADB-986`).
4. **Backport decision** — one line stating whether backporting is needed and why:
    - **Bug fix (especially critical/production)** → backport to all affected supported versions.
    - **New feature** → no backport needed.
    - **Refactoring only** → no backport needed.

### Example
```
sstables_loader: add progress tracking to tablet restore task

This series adds per-SSTable progress tracking to the tablet restore task. Previously, the `restore_tablets` task reported no progress — `progress_total` and `progress_completed` were always zero, making it impossible to monitor how far along a restore operation is.

### Changes

A `downloaded` boolean column added to `snapshot_sstables`, with a method to update it. After each SSTable is attached during restore, it is marked as downloaded.

Infrastructure plumbing: `sys_dist_ks` changed to a sharded reference and `attach_sstable` changed to return the attached SSTable.

A periodic timer that queries `snapshot_sstables` every 5 seconds and exposes downloaded/total counts via `get_progress()`.

A test assertion verifying `progress_total > 0` and `progress_completed == progress_total` after a successful restore.

Fixes: https://scylladb.atlassian.net/browse/SCYLLADB-986

No backport needed since this is a new feature targeting tablet-aware restore.
```

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

## Refine PR

When the user says **"refine PR"**, perform the following sequence:

1. **List all commits** in the PR (`git log --oneline upstream/master..HEAD`).
2. **For each commit**, review the diff (`git show <sha>`) and check:
   - **Commit message**: subject follows `module: short description` format, blank line separates subject from body, body explains *why* not *what*, wrapped at ~72 chars.
   - **Single logical change**: if the commit message needs "and" or "also", it likely needs splitting.
   - **No unrelated changes**: formatting fixes, renames, include cleanups, or test skips that don't belong with the functional change must be in separate commits or removed.
   - **Comments in code**: verify that added comments accurately describe what the code actually does — not what a previous iteration did or what was planned but not implemented.
   - **No unnecessary changes**: no gratuitous renames, no style-only changes mixed with logic, no dead code additions.
3. **Split commits** that contain unrelated changes (e.g., a commit that both changes storage logic and adds test skips should be split so each change goes to its logical home).
4. **Squash or reorder** commits where one undoes or replaces another (e.g., commit A adds a try/fallback approach, commit B replaces it with a different approach → combine into one commit with the final approach).
5. **Move misplaced hunks** to the commit they logically belong to (e.g., test skips belong in the commit that adds the test parametrization, not in an unrelated sstables commit).
6. **Verify compilability**: mentally confirm that each commit in the final sequence compiles independently — removing any later commit should not break the build.
7. **Final diff check**: `git diff <original_HEAD> HEAD --stat` should show only intentional differences (removed noise, fixed skips, etc.) — no accidental content loss.

