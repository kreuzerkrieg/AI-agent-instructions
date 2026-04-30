# AI Agent Instructions

Personal instruction files for AI coding agents (GitHub Copilot, Claude Code) tailored to ScyllaDB and SCT development workflows.

## Structure

```
~/.config/github-copilot/intellij/
├── global-agents-instructions.md          # Loaded for every conversation (agent behavior, terminal rules, lessons learned)
├── global-copilot-instructions.md         # Copilot-specific global instructions
├── global-git-commit-instructions.md      # Git commit message conventions
├── README.md                              # This file
└── scylla/
    ├── scylladb-instructions.md           # ScyllaDB C++ repo: build, test, code style, commit organization, PR format
    ├── sct-instructions.md                # SCT (Scylla Cluster Tests): log analysis, metrics, architecture
    └── scylladb_all_metrics_mapping.md    # Complete mapping of 617+ ScyllaDB Prometheus metrics to C++ source
```

## How It Works

- **`global-agents-instructions.md`** is loaded at session start for all JetBrains IDE sessions. It contains:
  - Project-specific instruction routing table
  - Terminal command rules (leading space, no interactive commands, output redirection)
  - Scratch file policy (save temp files under CLion scratches, not the repo)
  - Self-updating Lessons Learned section

- **`scylla/scylladb-instructions.md`** is loaded when working in the `scylladb/scylladb` repository. Covers build system, test runner, code style, commit organization, PR cover letter format, and review comment handling.

- **`scylla/sct-instructions.md`** is loaded when working in the `scylla-cluster-tests` repository. Covers SCT log analysis, archive structure, Prometheus TSDB analysis, and metric interpretation.

- **`scylla/scylladb_all_metrics_mapping.md`** is a reference file consulted during Prometheus metric analysis.

## Version Control

This directory is a git repository tracked at `git@github.com:kreuzerkrieg/AI-agent-instructions.git`. After any edit to instruction files, the agent commits and pushes:

```bash
cd ~/.config/github-copilot/intellij
git add -A && git commit -m "<description>" && git push
```

The agent pulls at session start (`git pull --rebase`) to stay current with edits from other machines.
