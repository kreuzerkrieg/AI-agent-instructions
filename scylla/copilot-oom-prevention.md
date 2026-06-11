# Copilot Language Server — OOM Prevention

## Problem

The GitHub Copilot language server (`copilot-language-server`, Node.js) scans the **entire workspace tree** on startup — including directories that are git-ignored. In a ScyllaDB clone this can mean 60k–140k files (`testlog/`, `build/`, `tools/`, `venv/`, `seastar/`, `abseil/`), which exhausts the V8 heap (~2 GB default) and crashes with SIGABRT.

## Defense Layers

### Layer 1: `.copilotignore` (per-repo, tells Copilot what to skip)

Every ScyllaDB clone must have a `.copilotignore` at the repo root. The canonical template lives at:
```
~/.config/github-copilot/intellij/scylla/templates/copilotignore
```

**Current exclusions** (~53k files eliminated):

| Directory | Files | Why excluded |
|-----------|------:|---|
| `tools/` | 16,626 | Frozen toolchain, vendored binaries |
| `build/` | 11,136 | Build artifacts |
| `venv/` | 8,129 | Python virtualenv |
| `seastar/` | 7,384 | Submodule (has its own repo) |
| `testlog/` | 0–76k | Test output, regrows constantly |
| `abseil/` | 1,570 | Vendored third-party |
| `.git/` | 6,172 | Version control internals |
| Others | ~1k | `.idea/`, `swagger-ui/`, `cmake-build-*/`, `rust/**/target/`, etc. |

After exclusions, only ~9,250 files remain indexable (actual source code).

### Layer 2: CLion excludeRoots (IDE file watcher)

The `.idea/misc.xml` `<CidrRootsConfiguration>` block tells CLion's file watcher and indexer to skip the same directories. This reduces IDE memory usage and prevents inotify watch exhaustion.

### Layer 3: Node.js heap limit (safety net)

```
NODE_OPTIONS=--max-old-space-size=8192
```

Set in `~/.config/environment.d/copilot.conf` (read by systemd user session → CLion) and `~/.bashrc`. Even if files accumulate, the server won't OOM until ~8 GB.

### Layer 4: Auto-provisioning on clone

A git `post-checkout` hook at `~/.config/git/templates/hooks/post-checkout` detects fresh ScyllaDB clones and auto-installs `.copilotignore`.

## Setup Commands

### New clones — automatic
The git template hook provisions `.copilotignore` on `git clone`. No action needed.

### Existing clones — run once
```bash
setup-scylla-workspace ~/Development/scylladb
setup-scylla-workspace ~/Development/scylladb_1
# ... any other clone
```

This script:
1. Copies the canonical `.copilotignore` template
2. Adds it to `.git/info/exclude` (never committed upstream)
3. Patches `.idea/misc.xml` with excludeRoots (if `.idea/` exists)

### Updating the template
Edit the canonical source, then re-provision:
```bash
vim ~/.config/github-copilot/intellij/scylla/templates/copilotignore
setup-scylla-workspace ~/Development/scylladb
setup-scylla-workspace ~/Development/scylladb_1
```

## Periodic Maintenance

`testlog/` regrows as tests run. If the workspace crosses ~50k total files:
```bash
rm -rf ~/Development/scylladb/testlog/*
```

## Key Insight

`.copilotignore` is **not** equivalent to `.gitignore` for this purpose. The language server's initial filesystem walk does **not** respect `.gitignore` — it scans everything first, then filters. So directories must be excluded via `.copilotignore` (which the server checks before walking) or the problem persists regardless of git-ignore status.

## Files

| File | Purpose |
|------|---------|
| `~/.config/github-copilot/intellij/scylla/templates/copilotignore` | Canonical template (single source of truth) |
| `~/.config/github-copilot/intellij/scylla/bin/setup-scylla-workspace` | Provisioning script |
| `~/.config/git/templates/hooks/post-checkout` | Auto-provision on clone |
| `~/.config/environment.d/copilot.conf` | `NODE_OPTIONS` for systemd session |
| `<repo>/.copilotignore` | Per-clone instance (from template) |
| `<repo>/.idea/misc.xml` | CLion excludeRoots |

