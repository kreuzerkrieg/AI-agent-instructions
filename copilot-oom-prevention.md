# Copilot Language Server — OOM Prevention (Global)

## Problem

The GitHub Copilot language server (`copilot-language-server`, Node.js) scans the **entire workspace tree** on startup — including directories that are git-ignored. In large C++ projects this routinely means 100k–700k+ files, which exhausts the V8 heap (~2 GB default) and crashes with SIGABRT.

**Key insight:** `.gitignore` does NOT prevent the crash. The server's initial filesystem walk ignores `.gitignore` — it scans everything first, then filters. Only `.copilotignore` (checked before walking) prevents the scan.

**Examples of affected projects:**

| Project | Total files | Main offenders | After `.copilotignore` |
|---------|------------|----------------|----------------------|
| ScyllaDB | ~62k (140k with testlog) | `tools/` 16k, `build/` 11k, `venv/` 8k, `seastar/` 7k, `testlog/` 0–76k | ~9,250 |
| ClickHouse | ~714k | `contrib/` 648k, `tests/` 28k, `cmake-build-*/` 22k | ~40k |

## Defense Layers

### Layer 1: `.copilotignore` (per-repo — most important)

A `.copilotignore` file at the repo root tells the Copilot language server which directories to skip **before walking them**. This is the primary defense.

**Universal patterns to always exclude:**
```gitignore
# Version control & IDE
.git/
.idea/
.cache/
.ccls-cache/
.mypy_cache/

# Build artifacts (C/C++)
build/
build_*/
build-*/
cmake-build-*/
compile_commands.json

# Python environments
venv/
.venv/
__pycache__/

# Node.js
node_modules/

# Rust build artifacts
**/target/
```

**Project-specific patterns to add:**
- **Vendored third-party** (`contrib/`, `third_party/`, `external/`, `vendor/`) — often the #1 offender
- **Submodules** that are rarely edited directly
- **Test output directories** that regrow (e.g., `testlog/`)
- **Generated files** (protobuf, IDL, ANTLR output)
- **Frozen toolchains** (`tools/`, `toolchain/`)

### Layer 2: CLion excludeRoots (IDE file watcher)

In `.idea/misc.xml`, add a `<CidrRootsConfiguration>` block listing the same directories. This prevents CLion's indexer and inotify file watcher from scanning them — reducing memory usage and preventing watch descriptor exhaustion.

```xml
<component name="CidrRootsConfiguration">
  <excludeRoots>
    <file path="$PROJECT_DIR$/build" />
    <file path="$PROJECT_DIR$/contrib" />
    <!-- ... add project-specific dirs ... -->
  </excludeRoots>
</component>
```

### Layer 3: Node.js heap limit (safety net)

```bash
# ~/.config/environment.d/copilot.conf (read by systemd user session → CLion)
NODE_OPTIONS=--max-old-space-size=8192
```

Also add to `~/.bashrc` for terminal-launched processes. This raises the crash threshold from 2 GB to 8 GB — a safety net if files accumulate beyond the ignore list.

**Requires logout/login** to take effect (systemd reads `environment.d` at session start).

Verify:
```bash
systemctl --user show-environment | grep NODE_OPTIONS
```

### Layer 4: Auto-provisioning on clone (ScyllaDB-specific)

For projects you clone frequently, a git `post-checkout` hook at `~/.config/git/templates/hooks/post-checkout` can auto-install `.copilotignore` on fresh clones. See `scylla/copilot-oom-prevention.md` for the ScyllaDB-specific implementation.

## Quick Setup for Any New Large Project

When opening a large project for the first time:

```bash
# 1. Assess the damage
find /path/to/project -type f | wc -l

# 2. Find the heavy directories
find /path/to/project -maxdepth 1 -type d -exec sh -c \
  'echo "$(find "$1" -type f 2>/dev/null | wc -l) $1"' _ {} \; | sort -rn | head -15

# 3. Create .copilotignore with the heavy dirs that aren't source code
#    (vendored deps, build output, test artifacts, toolchains)

# 4. Add to local git exclude (never committed)
echo ".copilotignore" >> /path/to/project/.git/info/exclude

# 5. Verify the reduction
find /path/to/project -type f \
  -not -path '*/.git/*' \
  -not -path '*/big_dir/*' \
  ... | wc -l
```

**Target:** keep indexable files under ~50k. The language server handles 10k–50k comfortably with the 8 GB heap.

## Rule of Thumb

If a directory meets ANY of these criteria, put it in `.copilotignore`:
1. **Not your code** — vendored/third-party/submodule
2. **Generated** — build output, compiled artifacts, protobuf output
3. **Ephemeral** — test output that gets regenerated
4. **Huge with no context value** — documentation builds, node_modules, toolchains

## Files

| File | Purpose |
|------|---------|
| `~/.config/environment.d/copilot.conf` | `NODE_OPTIONS` for systemd session |
| `~/.config/git/templates/hooks/post-checkout` | Auto-provision on ScyllaDB clones |
| `<repo>/.copilotignore` | Per-project exclusion list |
| `<repo>/.idea/misc.xml` | CLion excludeRoots |

