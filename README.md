# AI Agent Instructions

Personal instruction files for AI coding agents (GitHub Copilot, Claude Code, opencode) tailored to large C++ projects (ScyllaDB, ClickHouse) and SCT development workflows.

## How it works

Three tiers, distinguished by when they load:

| Tier | Loads | Contents |
|------|-------|----------|
| **Core** — `global-agents.instructions.md` | Every session, always | Rules an agent could otherwise violate without knowing to look them up: credentials, terminal discipline, verification, commit organization, prose style, scratch-file policy |
| **Playbooks** — `playbooks/*.md` | On the trigger listed in the core file's *Playbooks* table | Procedures needed only at a specific moment: PR workflow, commit splitting, machine provisioning, chat-history export, Jira/MCP |
| **Project and reference** — `scylla/*.md`, `clion-code-nav/*.md` | On the trigger listed in the core file's *Project-Specific Instructions* table | Per-repo conventions, cluster investigation, instance setup, metric mappings |

**The two routing tables in `global-agents.instructions.md` are the single source of truth for what exists and when to read it.** This README deliberately does not restate them — three hand-maintained indexes drifted apart once already, and by the time it was noticed the README was missing nine files and the routing table was missing a 704-line document.

`bin/check-index` enforces it: every tracked instruction file must be reachable from some other tracked file. It runs from the pre-commit hook installed by `bin/install-secret-hooks`.

## Layout

```
global-agents.instructions.md   # Core — always loaded
playbooks/                      # Load-on-demand procedures
scylla/                         # ScyllaDB ecosystem: repo, SCT, clusters, instances, references
  bin/                          # Installable scripts (AWS creds, secret hooks, workspace setup, WARP)
  templates/                    # Canonical .copilotignore for ScyllaDB clones
clion-code-nav/                 # CLion CodeNav MCP project
copilot-history-export/         # Nitrite DB -> Markdown transcript exporter
scratch/                        # Canonical template seeded into the CLion scratches _internal area
bin/                            # Repo-maintenance scripts
personal/                       # Private submodule (non-ScyllaDB instructions)
mcp.json                        # MCP server configuration
```

Untracked local-only files may also be present (e.g. `sampling.json`, `secrets/`); `.gitignore` excludes them.

## What does not belong here

Per-task state — investigation notes for one PR, an implementation plan for one fix, measurements from one set of runs. Those expire when the work merges and are indistinguishable from standing rules once a routing row points at them. They live in the agent's private working area under the CLion scratches `_internal/` directory. See *This repo holds durable instructions, not task state* in the core file.

## Version control

Tracked at `git@github.com:kreuzerkrieg/AI-agent-instructions.git`. After any edit, the agent commits and pushes immediately — this is the one repo exempt from the global no-push rule:

```bash
cd ~/.config/github-copilot/intellij
git add -A && git commit -m "<description>" && git push
```

The agent pulls at session start (`git pull --rebase`) to pick up edits from other machines.

`.gitignore` uses an inverted pattern (ignore everything, whitelist known files). When adding a new instruction file or subdirectory, add a matching `!name` (and `!name/**` for a directory) entry, then add a row to the appropriate routing table in the core file — `bin/check-index` fails the commit otherwise.
