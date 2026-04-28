# AI Agent Instructions

Personal instruction files for AI coding agents (GitHub Copilot, Claude Code) tailored to ScyllaDB and SCT development workflows.

## What's Here

| File | Purpose |
|------|---------|
| `global-agents-instructions.md` | Global instructions loaded for every conversation regardless of repository. Covers ScyllaDB C++ conventions, build system, commit organization, test workflows, backtrace decoding, and general agent behavior rules. |
| `sct-instructions.md` | SCT (Scylla Cluster Tests) specific instructions. Covers SCT log analysis, archive structure, cluster topology extraction, Prometheus TSDB analysis, backtrace decoding from SCT logs, and metric interpretation. |
| `scylladb_all_metrics_mapping.md` | Complete mapping of 617 ScyllaDB Prometheus metrics to their C++ source code registration sites, plus appendices for recording-rule aliases, dynamic group names, and derived metrics. |

## How It Works

- **`global-agents-instructions.md`** is loaded at `~/.config/github-copilot/intellij/global-agents-instructions.md` and applies to all JetBrains IDE sessions.
- **`sct-instructions.md`** is referenced from the global file and read on demand when the active workspace is the `scylla-cluster-tests` repository.
- **`scylladb_all_metrics_mapping.md`** is referenced from the SCT instructions and consulted during Prometheus metric analysis.

Both instruction files contain self-updating **Lessons Learned** sections where the agent records corrections and insights to avoid repeating mistakes across sessions.

## Version Control

This directory is the git working tree. After any edit to instruction files, the agent commits and pushes:

```bash
cd ~/.config/github-copilot/intellij
git add -A && git commit -m "<description>" && git push
```

Git history replaces the old timestamped-backup-file approach.

## Not Tracked

- `mcp.json` — MCP server configuration (contains local paths)
- `*_backup_*` — Legacy backup files (superseded by git)
- Empty placeholder files (`global-copilot-instructions.md`, `global-git-commit-instructions.md`)
