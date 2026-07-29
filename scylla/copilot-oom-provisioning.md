# Copilot OOM Prevention — ScyllaDB Specifics

> **For the general problem, defense layers, and NODE_OPTIONS setup, see the global doc:**
> `~/.config/github-copilot/intellij/copilot-oom-prevention.md`

This file covers ScyllaDB-specific provisioning only.

## ScyllaDB `.copilotignore` Template

Canonical source: `~/.config/github-copilot/intellij/scylla/templates/copilotignore`

Excludes `tools/` (16k), `build/` (11k), `venv/` (8k), `seastar/` (7k), `abseil/` (1.5k), `testlog/` (0–76k), and misc IDE/generated files. Reduces indexable files from 62k+ to ~9,250.

## Provisioning

### Automatic (on fresh clone)
The git `post-checkout` hook at `~/.config/git/templates/hooks/post-checkout` detects ScyllaDB clones and auto-installs `.copilotignore`.

### Manual (existing clones)
```bash
setup-scylla-workspace ~/Development/scylladb
setup-scylla-workspace ~/Development/scylladb_1
```

The script installs `.copilotignore`, adds it to `.git/info/exclude`, and patches `.idea/misc.xml` with CLion excludeRoots.

## Periodic Maintenance

`testlog/` regrows as tests run. If the workspace crosses ~50k total files:
```bash
rm -rf ~/Development/scylladb/testlog/*
```

