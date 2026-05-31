# AI Agent Instructions

Personal instruction files for AI coding agents (GitHub Copilot, Claude Code) tailored to ScyllaDB and SCT development workflows.

## Structure

```
~/.config/github-copilot/intellij/
├── global-agents.instructions.md          # Loaded for every conversation (agent behavior, terminal rules, lessons learned)
├── mcp.json                               # MCP server configuration (Atlassian, etc.)
├── README.md                              # This file
├── personal/                              # Git submodule (private, non-ScyllaDB instructions)
└── scylla/
    ├── scylladb-instructions.md           # ScyllaDB C++ repo: build, test, code style, commit organization, PR format
    ├── sct-instructions.md                # SCT (Scylla Cluster Tests): log analysis, metrics, architecture
    ├── scylladb_all_metrics_mapping.md    # Complete mapping of ScyllaDB Prometheus metrics to C++ source
    ├── arm-instance-setup.md              # Personal ARM EC2 instance setup, AWS commands, Ubuntu-specific patches
    ├── x86-instance-setup.md              # Personal x86 EC2 instance (perf tests, S3 stress) setup
    ├── gitleaks.toml                      # Custom gitleaks config for detecting credentials
    └── bin/
        ├── refresh-aws-creds              # Script: refresh AWS credentials via TOTP
        └── install-secret-hooks           # Script: install gitleaks pre-commit/pre-push hooks
```

> Untracked local-only files may also be present (e.g. `sampling.json`, `secrets/`); these are excluded by `.gitignore`.

## How It Works

- **`global-agents.instructions.md`** is loaded at session start for all JetBrains IDE sessions. It contains:
  - Project-specific instruction routing table
  - Terminal command rules (leading space, no interactive commands, output redirection, **no push without explicit permission**)
  - Scratch file policy (save temp files under CLion scratches, not the repo)
  - PR interaction workflow (plan-review / finalize-review two-phase process)
  - `$`-prefixed command system (`$cmd` lists all available commands)
  - Self-updating Lessons Learned section (periodically graduated into standing sections)

- **`scylla/scylladb-instructions.md`** is loaded when working in the `scylladb/scylladb` repository. Covers build system, test runner, code style, commit organization, PR cover letter format, and review comment handling.

- **`scylla/sct-instructions.md`** is loaded when working in the `scylla-cluster-tests` repository. Covers SCT log analysis, archive structure, Prometheus TSDB analysis, and metric interpretation.

- **`scylla/scylladb_all_metrics_mapping.md`** is a reference file consulted during Prometheus metric analysis.

- **`scylla/arm-instance-setup.md`** covers the personal ARM EC2 instance (`i-05ccc6ae22cf5bc94`): start/stop commands, SSH access, Ubuntu-specific patches, LD_LIBRARY_PATH setup.


## Version Control

This directory is a git repository tracked at `git@github.com:kreuzerkrieg/AI-agent-instructions.git`. After any edit to instruction files, the agent commits and pushes:

```bash
cd ~/.config/github-copilot/intellij
git add -A && git commit -m "<description>" && git push
```

The agent pulls at session start (`git pull --rebase`) to stay current with edits from other machines.
