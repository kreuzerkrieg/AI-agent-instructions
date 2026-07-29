# Global AI Coding Agent Instructions

**This is the global instructions file** (`~/.config/github-copilot/intellij/global-agents.instructions.md`). It is loaded for every conversation regardless of which repository is open. Repository-specific instructions live in `.github/copilot-instructions.md` inside each repo.

---

## 🚨 Critical Rule: Never Commit Credentials to Git — Not Even Once

> ## ‼️ THIS IS THE SINGLE MOST IMPORTANT RULE IN THIS ENTIRE FILE ‼️
>
> **CREDENTIALS — API TOKENS, PASSWORDS, SECRETS, KEYS — MUST _NEVER_ APPEAR IN ANY FILE THAT GETS COMMITTED OR PUSHED TO GIT. EVER. NO EXCEPTIONS.**
>
> ### What happened (2026-05-20):
> The agent wrote a real Jenkins API token literally into `scylladb-instructions.md` as part of a curl example, committed it, and **pushed it to a public GitHub repository**. The token had to be **immediately rotated**, the entire repo history had to be **rewritten with `git-filter-repo`** and **force-pushed**, and a **new token had to be issued**.
>
> ### The rule — memorize it:
> - ✅ **DO:** Put `<JENKINS_API_TOKEN>` or `<YOUR_TOKEN_HERE>` in docs/examples
> - ✅ **DO:** Keep real secrets in `~/.netrc` (chmod 600), never in any tracked file
> - ✅ **DO:** If you accidentally commit a secret: immediately `git-filter-repo --replace-text`, force push, AND tell the user to rotate the credential
> - ❌ **NEVER:** Put a real token, password, or key in any `.md`, `.sh`, `.json`, `.yaml`, or any other file in a git repo
> - ❌ **NEVER:** Write `password abc123xyz` in a code example — always use `password <YOUR_PASSWORD>`
> - ❌ **NEVER:** Copy a value from `~/.netrc` or any secrets file into instruction files or documentation
>
> **If you are about to write something that looks like `[a-f0-9]{32,}` or `ghp_...` or `Bearer ...` into a file — STOP. Use a placeholder instead.**

---

## Table of Contents

- [MANDATORY FIRST ACTIONS — Execute Before Anything Else](#-mandatory-first-actions--execute-before-anything-else)
- [Project-Specific Instructions](#project-specific-instructions)
- [Copilot OOM Prevention](#copilot-oom-prevention)
- [Scratch / Temporary Files (CLion-specific)](#scratch--temporary-files-clion-specific)
- [MCP Discovery — Opportunistic Search for New Tools](#mcp-discovery--opportunistic-search-for-new-tools)
- [Markdown Conversion — Tool Routing](#markdown-conversion--tool-routing)
- [Export Copilot IntelliJ Chat History](#export-copilot-intellij-chat-history)
- [Prior-Conversation Search](#prior-conversation-search)
- [`$cmd` — List All Commands](#cmd--list-all-commands)
- [Jira Integration (Atlassian MCP)](#jira-integration-atlassian-mcp)
- [Verify Everything — Trust Nothing](#verify-everything--trust-nothing)
- [Code Review Principles](#code-review-principles)
- [Engineering Principles](#engineering-principles)
- [Terminal Command Rules](#terminal-command-rules)
- [Version Control for Instruction Files](#version-control-for-instruction-files)
- [Secret Scanning — Git Hooks](#secret-scanning--git-hooks)
- [Commit Organization](#commit-organization)
- [PR Cover Letter](#pr-cover-letter)
- [Refine PR](#refine-pr)
- [PR Interaction Workflow](#pr-interaction-workflow)
- [Lessons Learned — Self-Updating Section](#lessons-learned--self-updating-section)

---

## ⚠️ MANDATORY FIRST ACTIONS — Execute Before Anything Else

**These steps MUST be the very first tool calls in every session/conversation, before responding to the user's question or performing any task.** No exceptions. Do not skip them even if the user's request seems urgent or trivial.

1. **Pull latest instructions:**
   ```bash
   cd ~/.config/github-copilot/intellij && git pull --rebase
   ```

2. **Identify the active workspace** from `<workspace_info>` and **immediately `read_file`** the corresponding project-specific instructions:

   | Workspace contains | File to load |
   |-------------------|--------------|
   | `scylladb/scylladb` | `~/.config/github-copilot/intellij/scylla/scylladb-instructions.md` |
   | `scylla-cluster-tests` | `~/.config/github-copilot/intellij/scylla/sct-instructions.md` |
   | `clion-code-nav` | `~/.config/github-copilot/intellij/clion-code-nav/clion-code-nav-instructions.md` |

3. **Only then** begin working on the user's request.

**Trigger phrase — "suit up":** Ernest often opens a work session by saying **"suit up"** (or "suite up"). Treat it as an explicit instruction to run these mandatory first actions and get ready to work — do not ask for clarification. It is usually followed immediately by a task, code review, or a `$debunk`/`$analyze-ci` request.

**Why this exists:** The agent has repeatedly failed to load project-specific instructions at session start (2026-04-30, 2026-05-03, 2026-05-04), despite having "lessons learned" entries and prose instructions about it. Burying the requirement in prose doesn't work — it must be a non-negotiable checklist at the top of the file.

---

## Project-Specific Instructions

Project-specific instructions are organized under subdirectories of this config directory. When the active workspace matches a project, read and follow the corresponding instructions file.

### ScyllaDB Ecosystem (`scylla/`)

| File | When to load | Description |
|------|-------------|-------------|
| `scylla/scylladb-instructions.md` | Working in **scylladb/scylladb** repo (the main C++ database) | Build system, C++/Python code style, test philosophy, backtrace decoding |
| `scylla/sct-instructions.md` | Working in **scylla-cluster-tests** repo (or any SCT task) | SCT-specific conventions, architecture, analysis workflows, metric mappings |
| `scylla/scylladb_all_metrics_mapping.md` | Reference for SCT metric analysis | Full mapping of ScyllaDB Prometheus metrics |
| `scylla/production-cluster-investigation.md` | **Any investigation of a live customer/dbaas cluster** — perf issue, stall, error spike, disk concern, incident triage, on-call page, ticket referencing a cluster ID | Access prerequisites (WARP + StrongDM SSH), available data sources (Prometheus/Thanos, VictoriaLogs, Grafana, backtrace) with when-to-use, on-node commands to run once SSH'd in, on-call context (rotations, tiers, DataDog paging, Slack war rooms), default investigation workflow, Grafana-panel → PromQL mapping, common anti-patterns, reporting format |
| `scylla/disk-usage-accounting.md` | Investigating disk-space discrepancies (`du` vs Grafana vs `nodetool`) — sub-reference of production-cluster-investigation.md | Explains which categories are/aren't reported by Scylla metrics, the LSA-vs-disk panel confusion, multi-mount and per-shard summing traps, and a reconciliation recipe |
| `scylla/arm-instance-setup.md` | Working with ARM/aarch64 testing or the personal ARM EC2 instance | Full reference: instance ID, AWS start/stop commands, Ubuntu-specific patches, library setup, LD_LIBRARY_PATH requirement |
| `scylla/x86-instance-setup.md` | Working with the x86 i4i.4xlarge EC2 instance (perf tests, S3 stress) | Instance ID, copying Fedora libs to Ubuntu, passing AWS creds via script, ulimit, background runs |
| `scylla/copilot-oom-prevention.md` | Copilot crashes (OOM/SIGABRT) in a ScyllaDB workspace | ScyllaDB-specific `.copilotignore` template, auto-provisioning. Points to global `copilot-oom-prevention.md` |
| `scylla/bin/refresh-aws-creds` | Any machine that needs AWS credential refresh | Installable script — copy to `~/.local/bin/` and `chmod +x`. See new-machine setup in arm-instance-setup.md |
| `scylla/bin/setup-scylla-workspace` | Provisioning a new or existing ScyllaDB clone | Installs `.copilotignore`, CLion excludeRoots, git exclude |
| `scylla/warp-setup.md` | Installing/using Cloudflare WARP Zero Trust on Fedora | TL;DR + `warp-login` automation + Fedora-specific install (`webkit2gtk3` nodeps workaround) + lessons learned |
| `scylla/bin/warp-login` | Daily WARP enrollment automation | Symlink into `~/.local/bin/`. Opens enrollment URL, polls clipboard for the token, registers, connects, selects `scylla-cloud-prod` VNet |
| `scylla/bin/warp-login-handler` | Browser-button → `warp-login --token` glue | Symlink into `~/.local/bin/`. Invoked by the user-level `~/.local/share/applications/com.cloudflare.warp.desktop` MIME handler when the blue "Open Cloudflare WARP" button is clicked. Logs to `~/.local/state/warp-login.log` and notifies via `notify-send` |

### Personal Repos

| File | When to load | Description |
|------|-------------|-------------|
| `~/Development/weekly-reports/AGENTS.md` | User mentions **weekly report**, "this week's report", "start a new week", or asks to record accomplishments/blockers/next-week items | Private GitHub repo `kreuzerkrieg/weekly-reports`. ISO-week-numbered markdown files, template-based. Auto-push is explicitly enabled here (overrides the global no-push rule). |

**Weekly status email — never send via a Google/Gmail MCP connector.** Generate an email-ready markdown file next to the week's report at `~/Development/weekly-reports/<YYYY>/<YYYY>-W<NN>-email.md`, built fresh from `<YYYY>-W<NN>.md`: greeting "Hi Łukasz,", mirror the `##`/`###` structure, preserve bold ticket keys and Jira/PR links, omit the `## Needs your input` section and the top "Draft…" note, close with "Sincerely," / "Ernest". The user renders it and copy-pastes into Gmail.

**Always read the relevant file at the start of a session** using `read_file` — do not rely on memory from prior conversations. If a file does not exist yet, notify the user so it can be created.

### This repo holds durable instructions, not task state

Per-task handoff specs — investigation notes for one PR, an implementation plan for one fix, measurements from one set of runs — do **not** belong here. They expire when the work merges, and they are indistinguishable from standing rules once a routing-table row points at them. Keep them in the agent's private working area instead:

```
~/.config/JetBrains/CLion<version>/scratches/GitHubCopilot/_internal/<topic>/
```

Current in-flight task state living there: `_internal/s3-throttler/` (S3 send-rate throttler — PR 30775, SCYLLADB-3249, SRE-1418: fleet-run measurements, the code-level reasons the throttler does not yet work, the retry-pacing implementation plan, and the no-budget-for-more-fleet-runs constraint). **Note:** the scratches path is pinned to the CLion major version, so it does not follow a version upgrade and is not synced between machines. If a handoff spec needs to survive either, give it its own repo rather than adding it back here.

A finding only belongs in this repo once it has outlived its task and become a rule that applies to future work — at which point it goes into a standing section, not a new file.

---

## Copilot OOM Prevention

Large C++ projects (ScyllaDB ~62k files, ClickHouse ~714k files) crash the Copilot language server via V8 heap exhaustion. Every workspace with >50k files needs a `.copilotignore` at the repo root.

**Full documentation:** `~/.config/github-copilot/intellij/copilot-oom-prevention.md`

Quick reference — the global `NODE_OPTIONS=--max-old-space-size=8192` is set in `~/.config/environment.d/copilot.conf`. When opening any new large project, run the assessment commands from the doc to identify heavy directories and create a `.copilotignore`.

---

## Scratch / Temporary Files (CLion-specific)
When creating **any** temporary or scratch files — analysis docs, migration call-chain notes, diagrams, test timing reports, query results, generated tables, or any other output that is not a source-code change — save them under the CLion scratches directory instead of polluting the repository tree:
```
~/.config/JetBrains/CLion2026.1/scratches/GitHubCopilot/
```
Create the directory if it does not exist. **Never** place such files inside the repository working tree. This applies even when the user asks you to "build a table" or "save the results" — always default to the scratches directory unless the user explicitly specifies a different path.

### Two-tier layout: user-facing vs agent-internal
The scratches directory has **two tiers** — keep them strictly separated:

- **`GitHubCopilot/`** (top level) — **user-facing only.** Reports, analyses, documents, and any
  deliverable the user expects to read. Treat it as the clean "output" surface.
- **`GitHubCopilot/_internal/`** — **the agent's private working area.** Put everything you need
  for *yourself* here: helper scripts, follow-up notes, intermediate/derived data, and **slim log
  snapshots** you take to preserve state across runs. The user does not expect to browse this.

Default rule: if an artifact is something *you* need to do the work, it goes in `_internal/`;
if it's something the *user* asked to see or will read, it goes at the top level. Create
`_internal/` if it does not exist.

**Log snapshots:** when a run's output dir (e.g. `~/Development/scylladb/testlog/`) will be
overwritten by the next run and you need to diff against it later, copy a snapshot into
`_internal/`. **Snapshot logs only** — never `cp -r` a whole `testlog/` (it contains the data
directory / sstables and can be hundreds of GB); copy just the `*.log` files you actually parse.

**Cleanup discipline:** `_internal/` is disposable. Periodically prune it — delete snapshots and
scripts once their analysis is finalized into a user-facing report, and scrub anything you are
100% sure is obsolete. When in doubt, keep — but don't let it grow unbounded.

**README bootstrap (do not rely on the local copy surviving):** `_internal/README.md` documents
the area's purpose + cleanup policy and is tracked canonically in this repo at
`scratch/_internal-README.md`. When you first touch `_internal/` in a session, if
`_internal/README.md` is **absent or older than** the repo template, copy it over:
```bash
SRC=~/.config/github-copilot/intellij/scratch/_internal-README.md
DST=~/.config/JetBrains/CLion2026.1/scratches/GitHubCopilot/_internal/README.md
mkdir -p "$(dirname "$DST")"
[ ! -f "$DST" ] || [ "$SRC" -nt "$DST" ] && cp "$SRC" "$DST"
```
Keep machine-specific item tracking in a separate **local** `_internal/INVENTORY.md` (untracked) —
a short table of each item, its purpose, and when it's safe to delete — so the README stays a
clean, overwrite-safe copy of the repo template.

---

## MCP Discovery — Opportunistic Search for New Tools

When you encounter a **tool, service, or platform** during the session that is:
1. mentioned in the codebase, instructions, or by the user, **and**
2. not already configured as an MCP server (check `~/.config/github-copilot/intellij/mcp.json`), **and**
3. a persistent service (not ephemeral infrastructure that only exists during test runs)

…then **once per session**, do a background search for an MCP server:
```
search GitHub: "mcp server <tool-name>" sorted by stars
```
Also check **[cursor.directory](https://cursor.directory/)** — a community-curated directory of MCP servers. It aggregates servers across categories and can surface options that GitHub search misses.

**Evaluation criteria** (all must be met to recommend):
- ≥100 stars (maturity signal)
- Official or well-maintained (recent commits, not archived)
- The user actually interacts with the tool regularly (not just referenced in docs)
- The tool has a stable, persistent endpoint the agent can connect to

**If a good candidate is found**, briefly mention it to the user: *"Found an MCP server for X (N stars, official). Want me to add it?"* — do not add it without asking.

**If nothing qualifies**, silently move on. Do not mention failed searches.

**Track searched tools** in memory for the session to avoid redundant searches. Only search once per tool per session.

**Never use `--prerelease allow` in an MCP `uvx` config** unless an alpha is specifically needed. It once resolved pydantic to `2.14.0a1`, which dropped a symbol the `mcp` SDK imports, crashing the server on startup. Pin the transitive constraint to the latest stable major instead: `--with 'pydantic>=2.10,<2.14'`. To debug an MCP startup `ImportError`: read the traceback, find the resolved archive under `~/.cache/uv/archive-v0/<hash>/lib/python*/site-packages/`, check the installed version, then tighten the constraint in `mcp.json`.

---

## Tool Routing

### Check the MCP tool list before reaching for curl

Before using `curl` / REST / `gh api`, scan the current tool list for an MCP that already speaks the target service. Falling back to REST when an MCP is configured is wasteful and can expose credentials needlessly — it once led to writing a Jira API token into `~/.netrc` when `mcp_atlassian_fetch` was available the whole time. Only fall back when the MCP is genuinely absent, and even then prefer existing `~/.netrc` entries over asking for new credentials.

### Markdown conversion

Use **`microsoft/markitdown`**'s `convert_to_markdown` for all markdown conversion. It accepts local file paths and URIs (http:, https:, data:) and handles PDF, DOCX, XLSX, PPTX, images, audio, and web pages.

### Code navigation — accuracy versus cost

Use CLion CodeNav MCP for **accuracy**, not token savings. Measured on a real call graph, MCP cost more than grep (`light_index` dumps 60–100 symbols when one is needed; a misfired `usages` call returned 101 irrelevant results).

- Quick "where is this called?" on a unique symbol → `grep_search` wins on cost.
- Ambiguous names, virtual dispatch, or a full call graph with zero false positives → `clion_codenav_usages`. It cannot miss a call site through a naming variant and does not need file content to find enclosing function boundaries.

### Reading files

Prefer `read_file` for any file also touched by an edit tool — it deduplicates content and keeps formatting consistent. Use `cat` only for one-off reads of files not involved in edits.

### MCP string parameters take real newlines

Never use `\n` or `\\n` escape sequences in MCP tool string parameters. The value is stored raw, so the escape renders literally — this has corrupted PR bodies three times. Write actual line breaks; the JSON transport handles them.

### "Session expired" is often a payload timeout

When a hosted MCP connector reports "MCP server session expired", first check whether a read and a tiny write succeed before assuming auth failure. A large payload timing out is frequently mislabeled as a session error, and reconnecting will not fix it. Diagnosed the hard way on the Gmail connector, where `list_labels` and a one-word draft both worked while the full HTML body failed every time — and the probe write clobbered the real draft.

---

## Export Copilot IntelliJ Chat History

The GitHub Copilot IntelliJ plugin (CLion / IDEA / Rider / PyCharm / …) stores
past **agent-mode** conversations in a bundled **Nitrite v4 embedded DB**
(H2 MVStore file format) — **not** in `copilot-intellij.db` (that's just plugin
UI state, a single `state` KV table).

**Where the real transcripts live:**

- `~/.config/github-copilot/<ide>/chat-agent-sessions/<sid>/copilot-agent-sessions-nitrite.db`
  — full agent transcripts (`NtAgentSession`, `NtAgentTurn`, `NtAgentWorkingSetItem`).
- `~/.config/github-copilot/<ide>/bg-agent-sessions/<sid>/*.db` — background-agent state.
- `~/.config/github-copilot/<ide>/chat-sessions/*.xd` and `chat-edit-sessions/*.xd`
  — old "plain chat" and edit-mode state in **Xodus** binary format. Verified to hold
  metadata only, no transcript prose.

`<ide>` is `cl` (CLion), `id` (IDEA), `rd` (Rider), `py` (PyCharm), etc.

**Exporter tooling** lives in this repo at `copilot-history-export/`:

```bash
cd ~/.config/github-copilot/intellij/copilot-history-export
./export_all.sh                            # → ~/ai-history-archive/copilot-clion/
./export_all.sh /custom/out                # custom output dir
PLUGIN_LIB=/path/to/lib ./export_all.sh    # override plugin lib dir
```

The script auto-discovers the newest bundled `github-copilot-intellij/lib/` under
`~/.local/share/JetBrains/*/`, compiles the Java extractor if needed, iterates
every Nitrite DB across every IDE variant, dumps each to JSON, and renders one
Markdown file per session (`YYYY-MM-DD_<title-slug>_<sid8>.md`) with full turns:
user prompt, thinking blocks, prose reply, and each tool call with input + full
result output. If `gitleaks` + `~/.gitleaks.toml` are installed it also writes
`_secrets-scan.json` next to the transcripts.

**Read-only wrt source:** `DumpNitrite` copies each `.db` to `/tmp` before opening
(H2 MVStore may perform recovery writes even in `readOnly=true`). Nothing in
`~/.config/github-copilot/` is modified.

**Cadence:** re-run any time you want to feed new conversations into
`~/ai-history-archive/copilot-clion/` — then rebuild the search indexes (see
next section). Roughly weekly is sensible. **Runs are incremental** (state in
`<OUT>/_export_state.json`): DBs whose mtime hasn't advanced are skipped, and
sessions whose latest turn hasn't advanced are not re-rendered. Pass `--full`
to force a complete re-export.

**Secrets warning:** transcripts contain raw terminal output — expect real
credentials (Jenkins tokens in `curl -u`, AWS STS keys, WARP JWTs, etc.).
**Never commit the export directory to a git remote without scrubbing.** See
the tool's `README.md` for full implementation notes.

---

## Prior-Conversation Search

Past AI-assistant conversations across agents (opencode, Copilot/CLion) are
exported to `~/ai-history-archive/` and indexed locally. **Before re-deriving
something that may already have been solved** — a tricky build failure, a review
decision, an incident, a config fix — search that history first via `ai-search`:

```bash
ai-search buffered_readable_file                     # keyword (BM25/FTS5): code, symbols, error strings
ai-search -s "how did we avoid streaming sstables"   # semantic (-s): meaning-based "how did I..." recall
```

Flags: `--agent {opencode,copilot-clion}`, `--after`/`--before YYYY-MM-DD`,
`-n/--limit`. Each hit prints the source transcript path. Fully on-box (SQLite
FTS5 + local Ollama embeddings — nothing leaves the machine). Rebuild after
re-exporting: `python3 ~/ai-history-archive/_index/build_index.py` (keyword) and
`build_embeddings.py` (semantic). Details: `~/ai-history-archive/_index/README.md`.

---

## `$cmd` — List All Commands

When the user types **`$cmd`**, list all defined `$`-prefixed commands with a one-line description of each. Scan both global and project-specific instruction files for command definitions. Current commands:

| Command | Defined in | Description |
|---------|-----------|-------------|
| `$cmd` | global | List all defined `$` commands |
| `$plan-review` | global | Phase 1: plan responses to PR review comments (no changes until approved) |
| `$finalize-review` | global | Phase 2: execute approved plan from `$plan-review` |
| `$debunk <URL>` | scylladb | Triage a PR bot CI failure comment — verify each claim, propose Jira issues |
| `$analyze-ci` | scylladb | Analyze PR/CI test failures by error signature, classify, and draft Jira issues |

**Maintenance:** When adding a new `$` command to any instruction file, also add it to this table.

---

## Jira Integration (Atlassian MCP)

Jira access is available via the **Atlassian MCP server** configured in `~/.config/github-copilot/intellij/mcp.json`:

```json
"atlassian": {
  "type": "http",
  "url": "https://mcp.atlassian.com/v1/mcp"
}
```

### How it works
- The MCP server uses **OAuth via browser** — no API token needed. Authentication goes through the org's Okta SSO.
- On first use in a session, Copilot connects to the MCP server which handles auth transparently.
- The Jira instance is `https://scylladb.atlassian.net`.

### Capabilities
Once connected, the agent can:
- Search Jira issues (JQL queries)
- Create issues (tasks, subtasks, bugs, stories)
- Update issues (status, assignee, description, labels)
- Add comments
- Read Confluence pages

### Usage notes
- The user may need to say "use Atlassian MCP" or similar in their prompt to hint that Jira tools should be used.
- If the MCP tools are not available in the current session's tool list, the Atlassian MCP server may not be connected — ask the user to check MCP server status in CLion settings.

### Alternative: API token via ~/.netrc
If MCP is unavailable, Jira can also be accessed via REST API with an API token stored in `~/.netrc`:
```
machine scylladb.atlassian.net
  login your.email@scylladb.com
  password YOUR_JIRA_API_TOKEN
```
Generate tokens at: https://id.atlassian.com/manage-profile/security/api-tokens (requires admin permission).

---

## Verify Everything — Trust Nothing
Never take claims at face value — not from the user, not from review comments, not from documentation, and not from your own prior reasoning. **Always verify by reading the actual code.** Before answering a question about how something works, trace the code path yourself. Before applying a reviewer's suggestion, confirm their assumptions are correct. Before stating that a function is or isn't called somewhere, grep for it. If you cannot find solid proof in the source code, say so explicitly rather than guessing.

The same principle applies to **analysis reports and any response that makes factual claims**: only include claims backed by hard evidence from metrics, logs, or code. If a claim cannot be verified but is worth mentioning, label it explicitly as **"Speculation:"** or **"Unverified:"** — never present an inference as a fact. When computing metric deltas, always account for ALL label dimensions (e.g., `class`, `scheduling_group_name`) — aggregating across label values without awareness produces incorrect totals.

### Never fabricate specifics

Never write a log line, timestamp, ticket ID, cluster ID, error message, DC/rack name, customer name, commit SHA, or any other specific fact that requires a data source, unless that data source has been queried **in this session**. Prior-session memory does not count.

- If no tools have been called yet, say so explicitly ("I have no data on this cluster — let me query…") and call them. Never open a reply with a situation report assembled from plausible-sounding details.
- Speculation is allowed, but must be prefixed **"Speculation:"** / **"Hypothesis:"** and kept separate from anything presented as fact.
- **Landing on a real identifier by chance is worse than obvious nonsense** — it makes the confabulation hard to spot and can leak into an incident channel. This has happened: three invented IDs all turned out to reference a real ticket.
- **"X does not exist" is a positive claim and needs the same evidence.** Never declare a Jira issue, GitHub issue, Confluence page, PR number, or commit SHA nonexistent without an actual query. If the tool is unavailable, write "cannot verify — treating as unverified", not a nonexistence verdict.

### Read the implementation — never infer behavior from a name

For any function whose name implies a lifecycle transition (`after_test`, `stop`, `shutdown`, `teardown`, `cleanup`, `finalize`, `destroy`, `close`, `dispose`), never infer its side-effects from the name or from where it is called. Open it and read it. Names in test-harness code particularly love to lie: `after_test` often means "notify and validate", not "stop everything", and `close`/`cleanup` may release only a subset of resources. Getting this wrong once placed teardown callbacks against a still-running cluster and reproduced the exact race the change was meant to fix.

### Verify that file edits actually landed

Edit tools can report success, and even echo the new content back, while writing nothing. Three separate incidents: a dropped import line, a dropped multi-line structural edit, and `insert_edit_into_file` with `// ...existing code...` anchors silently deleting ~101 unseen lines from this very file.

- After any structural or multi-line edit, `grep` the file for a unique new symbol the edit introduced. Do not trust the success message or the echoed "after" state.
- Syntax checks do not prove an edit landed. `py_compile` validates syntax only — never name resolution or imports — and a partially-applied edit is usually still syntactically valid.
- **Never** bracket regions you have not just read with `// ...existing code...`. For append-only edits to a long file, either read the tail first and anchor on its actual last line, or append with `printf ... >> file`.
- Safety check after any supposedly-additive edit: `git show HEAD --stat`. Deletions greatly exceeding insertions is proof of destruction — revert immediately with `git revert --no-edit HEAD`.
- When an anchor keeps failing, fall back to a script that asserts first: `assert old in src; src = src.replace(old, new, 1)`. The assertion fails loudly instead of silently no-op'ing.

---

## Code Review Principles

When performing a code review — whether reviewing a colleague's PR, reviewing AI-generated code before committing, or auditing a change for correctness — apply these principles.

### Contract-First Review

Before examining the code, derive the **behavioral contract** the PR promises: what it claims to do, from the title, description, linked issues, changelog entries, and tests. Then verify that the code actually fulfills that contract.

- Treat PR metadata as part of the promise: a `Performance Improvement` PR claims measurable benefit; a `Bug Fix` claims the bug is fixed.
- State findings as **violated invariants**, not checklist matches. Example: "This PR promises cached results are partitioned by all semantics-affecting inputs, but field Y is omitted, so two different plans can share one cache entry."
- Do not approve based on plausibility alone. Map each material claim to proof before approving.

### Impacted Surface Tracing

When a PR changes an invariant, follow it through the **entire** system, not just the touched code:

- All callers and callees (not only those in the diff)
- Sibling implementations (if fixing behavior in component A, check component B for the same issue)
- Lifecycle transitions: startup, steady state, shutdown, retry, cancellation, exceptions
- Settings and feature flags that interact with the changed behavior
- Anything that can still mutate **after** a guard or role check fires

**Anti-pattern to avoid:** finding suspicious code, reasoning abstractly "this is safe because [memory layout / practical likelihood]", and moving on. If you cannot prove safety via a concrete trace with real values, report it as a concern or request the test that would prove it.

**Signature changes need a repo-wide grep, before the change lands.** Any top-level function, class, or context manager can be imported by files you are not looking at. Changing two test helpers' signatures without checking cross-module importers produced two `TypeError` regressions that only the full suite caught:

```bash
grep -rn "\b<name>\b" --include='*.py' | grep -v <owning-file>
```

When external callers exist, pick one: keep the old signature and introduce a new name for the new shape; make the new parameters optional; or migrate every caller in the same series. This is the static-analysis counterpart of tracing polymorphic dispatch.

### Reviewing a Commit Series

When reviewing commit N of a series, every file reference — line numbers, snippets, attribution — must be against the code **as it exists at that commit**. Read it with `git show <sha>:<file>`. Citing line numbers from the final branch HEAD while attributing an issue to an earlier commit makes the review wrong: a file with 489 lines at commit 18 does not have the line 528 that commit 21 creates.

### Evidence Requirements by Claim Type

Map each claim type to the required proof before approving:

- **Performance Improvement** → before/after measurements, a benchmark, or a focused performance test
- **Bug Fix** → regression test, or a clear documented reason one is impractical
- **New invariant** → tests at the boundary where violation would matter, not only at the helper or code path touched by the patch

Missing proof for important behavior is a review concern even when the code looks plausible.

### Tests Weaker Than the Contract

If a test would pass even if the new feature were removed, incorrectly wired, or broken in a realistic way, it is **not evidence** — it is suspicious. Broad existing tests are insufficient unless they would fail if the new behavior were absent.

When writing or reviewing tests, ask: *"Would this test catch the bug if I reverted the fix?"* If not, the test is too weak.

---

## Engineering Principles

### Fail-Close: Avoid Fallback Paths

When an operation fails, prefer **letting the error propagate** over silently substituting a default value or alternate behavior. Fallbacks hide bugs and make incidents harder to diagnose.

If a fallback is genuinely necessary, follow the **fail-close principle**: never perform a destructive, expensive, or consequential action on the fallback path. Skip the operation and surface the error instead.

Concrete example: when attribution data is unavailable, do not assume a safe default and proceed with a side-effecting action — let the run fail and retry once the data is available. **On uncertainty, do less, not more.**

### New Validation on Existing Data = Backward Incompatibility

Adding a new constraint, check, or validation that applies to **already-existing** data or configuration is a breaking change, even if the code change looks purely additive. A stricter validator that rejects previously-valid configs, a new schema check that throws on data created by an older version, or a new startup assertion that triggers on an existing cluster — all are backward-incompatible.

Before adding any new enforcement: ask "does this apply to things that were valid before?" If yes, either gate it behind a setting, apply it only to newly created objects, or document it explicitly as a breaking change.

### Instrumentation: Find the Chokepoint, Verify the Concrete Type

For "how many / what kind of operations are we doing" questions, instrument the **single layer every operation passes through**, not each producer. A counter added to `download_source` never fired because the read path actually built `chunked_download_source` through a factory chain (`make_source` → `make_download_source` → `make_chunked_download_source`). The fix was one log line at the shared `make_request` chokepoint: a smaller diff, impossible to miss a path, and it caught all verbs (GET/HEAD/PUT/DELETE), surfacing excessive HEADs that per-source GET counting would never have revealed.

- Before instrumenting any interface or factory-dispatched path, trace the dispatch to the concrete class that path actually creates. Name similarity is not proof — read the wiring.
- Caveat to state in the results: a logical-call chokepoint counts logical calls, not lower-level retries. Call this out explicitly when retries live below the instrumented layer.

---

## Terminal Command Rules

> ## 🟦 ALWAYS START EVERY TERMINAL COMMAND WITH A LEADING SPACE 🟦
>
> **This is a non-negotiable, every-single-command rule — not an occasional nicety.** Before running *any* command, the first character you type MUST be a space (` git status`, never `git status`).
>
> - ✅ **DO:** ` ninja build/dev/scylla`, ` ls -la`, ` cat /tmp/out.txt`
> - ❌ **NEVER:** `ninja build/dev/scylla`, `ls -la`, `cat /tmp/out.txt`
>
> **Why:** `HISTCONTROL=ignoreboth` makes bash skip recording any command that starts with a space, keeping the user's shell history free of agent-generated noise. A single forgotten space permanently pollutes that history. This is NOT a default — it was added manually to `~/.bashrc` (`export HISTCONTROL=ignoreboth`). If the trick stops working, check `echo $HISTCONTROL`.
>
> **If you ever notice you forgot the leading space, treat it as a lapse to correct immediately and resume prefixing every command.**

> **⚠️ CRITICAL: You MUST NEVER run any terminal command that requires user intervention or waits for input.** This is an absolute, non-negotiable rule. Violations block the terminal and require the user to manually intervene. Offending commands include but are not limited to: `git rebase -i` (even with `--autosquash`), `git commit` without `-m`/`-F`, interactive editors (`vim`, `nano`, `less`), pagers, `read`, `select`, or any tool that prompts for input. The **only** exception is `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash` which is explicitly non-interactive because `GIT_SEQUENCE_EDITOR=true` suppresses the editor.

- Commands whose output may exceed the terminal window (e.g. `git log`, `git diff --stat`, `git show`) **must** redirect output to a temporary file, then read it with `cat` or `read_file`. Never rely on the terminal fitting all output — if it doesn't, the command blocks waiting for user input (pager). Example: `git log --oneline HEAD~20..HEAD > /tmp/commits.txt && cat /tmp/commits.txt`
- Always use `git --no-pager` or pipe through `| cat` as an alternative when redirection is inconvenient.
- To amend an older commit, use fully non-interactive techniques:
  - **Cherry-pick rebuild:** `git reset --hard <SHA>~1`, then `git cherry-pick --no-commit <SHA> && git commit -F <msg-file>`, then `git cherry-pick <SHA>..<original-HEAD>`.
  - **Fixup + autosquash:** `git commit --fixup=<SHA>` (content) or `git commit --allow-empty --fixup=amend:<SHA> -F <msg-file>` (message), then `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <SHA>~1` — the `GIT_SEQUENCE_EDITOR=true` prevents any editor from opening, making the `-i` flag safe.
- To amend the most recent commit message: write the new message to a file, then `git commit --amend -F <msg-file>`. Never use `git commit --amend` without `-m` or `-F` — that opens an editor.
- **Commit message temp files:** always use `printf '...\n\n...\n' > /tmp/msg.txt` rather than bash heredocs. Heredocs silently drop blank lines, causing the subject and body to merge onto one line. Alternatively, use the `create_file` tool.
- **Before any destructive command** (`git reset --hard`, `git checkout -- .`, force-push): **prove safety first** by running `git diff <local> <remote>` to confirm no unique local content would be lost. Never proceed on an assumption of safety — verify with evidence, then execute.

> ❌ **STRICTLY PROHIBITED: `git push` / `git push --force` to any CODE REPOSITORY remote without explicit user instruction.** Local commits, amends, and rebases are always fine — but publishing code to a remote is the user's decision. Never push spontaneously after refining commits, addressing review comments, or rebasing. **Only exception:** the instructions repo (`~/.config/github-copilot/intellij/`) is always pushed immediately after edits. *This is the **canonical no-push rule** referenced throughout the PR workflow sections below.*

---

## Version Control for Instruction Files
The instruction files directory (`~/.config/github-copilot/intellij/`) is a git repository tracked at `git@github.com:kreuzerkrieg/AI-agent-instructions.git`. **After making any edit** to files in this directory, commit and push the change:
```bash
cd ~/.config/github-copilot/intellij
git add -A && git commit -m "<short description of what changed>" && git push
```
This replaces the old backup-file approach — git history provides full versioning. Commit messages should be concise but descriptive (e.g., "Add backtrace decoding section to SCT instructions").

**Adding new instruction files:** The `.gitignore` uses an inverted pattern (ignore everything, whitelist known files). When adding a new instruction file or subdirectory, you **must** add a corresponding `!filename` or `!dirname/` + `!dirname/**` entry to `.gitignore` so git tracks it.

**Pull before starting work:** These instruction files may be edited by agents on other machines, so always work from the latest version. The session-start `git pull --rebase` is already covered by step 1 of *Mandatory First Actions* above — don't skip it.

---

## Secret Scanning — Git Hooks

Every machine and repo must have **gitleaks** pre-commit/pre-push hooks installed. These hooks
stop credentials from ever being committed or pushed.

### New-machine setup (run once per machine)

```bash
# 1. Install gitleaks
sudo dnf install gitleaks          # Fedora/RHEL
# brew install gitleaks             # macOS

# 2. Install the custom config (catches Jenkins tokens, netrc patterns, etc.)
cp ~/.config/github-copilot/intellij/scylla/gitleaks.toml ~/.gitleaks.toml

# 3. Install hooks into any repo you work with
bash ~/.config/github-copilot/intellij/scylla/bin/install-secret-hooks ~/Development/scylladb
bash ~/.config/github-copilot/intellij/scylla/bin/install-secret-hooks ~/.config/github-copilot/intellij
# Run for any other repos as needed
```

### What the hooks catch
- **pre-commit**: scans the staged diff before every commit — blocks the commit if a secret is found
- **pre-push**: scans all unpushed commits before push — last-chance safety net
- Custom rules cover: Jenkins API tokens (hex 32-40 chars), netrc `password` lines, high-entropy strings near credential keywords, GitHub PATs (`ghp_...`), AWS access keys

### If a hook fires
1. Remove the secret from the file
2. Use a placeholder: `<JENKINS_API_TOKEN>`, `<YOUR_PASSWORD>`, etc.
3. `git add` and retry the commit
4. If it's a genuine false positive (e.g., a test vector): `git commit --no-verify` — but use this extremely rarely and only after confirming it's not a real credential

### If a secret was already committed
1. `git-filter-repo --replace-text <(echo 'SECRET==>PLACEHOLDER')` — rewrites all history
2. `git push --force`
3. **Rotate the credential immediately** — assume it's compromised

---

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
- **Module prefix** matches the directory or subsystem being changed (e.g., `db:`, `raft:`, `api:`, `test:`, etc.).
- Multiple modules: `cql3, transport: fix ...` — whole tree: `tree: ...`
- Keep it short — ~50 characters is ideal, 72 is the hard max.
- Use **imperative mood**: "add", "fix", "remove", "extract", "change" — not "added", "fixes", "removing".
- Describe *what* the commit does, not *how* — the diff shows the how.
- **Describe what the commit actually changes, not how it was developed.** A commit that adds a new feature says "add", not "fix". Review the actual diff before writing the message — the subject must match what the diff shows.
- Do **not** end with a period.

#### Body (optional but encouraged for non-trivial changes)
- Separated from the subject by **one blank line**.
- Explains **why** the change is needed — motivation, context, trade-offs.
- Does **not** repeat what is obvious from the diff (avoid "changed X to Y in file Z").
- Wrap lines at ~72 characters for readability in `git log`.
- For bug-fix commits, reference the issue: `Fixes #1234` or `Refs org/repo#1234`.

#### Examples

Good:
```
db: extract snapshot TTL into class constant

Move the TTL value from a local variable in insert_snapshot()
to a class-level constant SNAPSHOT_TTL_SECONDS, making it
reusable by other methods.
```
```
loader: change dependency to sharded reference

This allows accessing the service from any shard via .local(),
which will be needed to update download status from within
invoke_on_all.
```
```
test: verify progress reporting in restore test
```

Bad:
```
fix stuff                              # no module prefix, vague
```
```
db: Added new column and method.       # past tense, period, "and" → split
```
```
loader: Change the member from T& to sharded<T>&, update all
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
| 1 | `db: extract snapshot TTL into class constant` | Refactoring |
| 2 | `db: add downloaded column to snapshot table` | Schema change |
| 3 | `db: reformat read_row lambda` | Formatting |
| 4 | `db: add update_download_status method` | New API |
| 5 | `loader: clean up includes` | Include cleanup |
| 6 | `loader: change dependency to sharded reference` | Plumbing |
| 7 | `loader: return shared object from attach method` | Plumbing |
| 8 | `loader: mark items as downloaded after attaching` | Feature wiring |
| 9 | `loader: add progress tracking to restore task` | Feature |
| 10 | `test: verify progress reporting in restore test` | Test |

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
- **Never add Doxygen-style `///` comments** to declarations/definitions unless the project already uses `///` in that file or the user explicitly requests it.
- **Preserve existing code structure** — do not reorder includes, reorder function parameters, or change formatting unless that is the explicit task.
- In short: the diff should contain **only** the lines required for the functional change. Every extra line the reviewer has to read is wasted effort.

#### Rewriting a file on top of newer upstream

Treat this as "apply the smallest transformation that achieves the migration", never "redo the file". Rebuilding a test file on top of ~20 upstream commits leaked in three kinds of noise: a dropped narrative comment block, editorial commentary added on top of new code, and cosmetic edits inside an untouched compat helper. Verify before amending:

- `git diff upstream/master HEAD -- <file> | grep '^-.*#'` — every removed comment must have a matching `+` (re-added, possibly re-indented) or belong to a deleted block. Anything else is an accidental drop.
- `git diff upstream/master HEAD -- <file> | grep '^+.*#'` — added comments belong only on genuinely new code, never as commentary about migrated code.
- For any *existing* helper you touch, diff it in isolation: `git show upstream/master:<file> > /tmp/orig && diff /tmp/orig <(sed -n '<start>,<end>p' <file>)`. The result must show only the deliberate change.
- Do not add docstrings to functions that already existed. A reviewer's request for docstrings applies to the new wrapper, not to functions you lightly modified.

### Handling Review Comments — Think Before You Apply
- **Never blindly apply review comments.** Invest time in understanding what the reviewer is actually asking and whether the comment is correct. Reviewers can misread the code, misunderstand the intent, or miss context that you (the author) have.
- **Verify the reviewer's assumptions.** Does the reviewer understand how the internal machinery works? Did they trace the actual code path, or are they guessing based on a surface reading?
- **Evaluate whether the suggestion improves correctness or just reshuffles code.** Some review comments are cosmetic preferences disguised as bug reports.
- **Consider whether the change would break the test's intent.** Tests are written a specific way for a reason.
- **Dead code observations may be wrong.** A parameter that looks unused in one function may exist because callers rely on the signature for consistency, or because it documents an intent that will be used in a follow-up. Don't delete parameters just because a reviewer says "dead code" — verify the full picture first.
- **When in doubt, present your reasoning to the user** rather than silently applying the change. Say "the reviewer suggests X, but I believe the current code is correct because Y — should I apply it anyway?"

---

## PR Cover Letter

Every PR needs a **title** and a **description body**. The description should give a reviewer enough context to understand the change without reading every commit first.

### Title
Use the same `module: short description` format as commit messages. If the PR spans multiple modules, use the primary one or a broader scope.

### Body Format
- The PR body is rendered as **Markdown** — use `###` headings, `**bold**`, backtick-quoted symbols, etc.
- Do **not** hard-wrap lines in the PR body; let the platform handle wrapping. Each paragraph should be a single long line.
- This is different from commit message bodies, which are wrapped at ~72 characters.

### Body Structure

1. **Problem** — what is broken, missing, or inadequate. One or two sentences.
2. **Changes** — a summary of what the series does, grouped logically. Not a commit-by-commit list — describe the *what* and *why* at a higher level than individual commits.
3. **Issue reference** — `Fixes: <URL>` on its own line (e.g., `Fixes: https://github.com/org/repo/issues/123` or a JIRA URL).
4. **Backport decision** — one line stating whether backporting is needed and why:
    - **Bug fix (especially critical/production)** → backport to all affected supported versions.
    - **New feature** → no backport needed.
    - **Refactoring only** → no backport needed.

### Specificity Rule

- **Always name the exact thing that changed.** Never write "Fix a bug" or "Improve performance" without saying what specifically. The reader scanning a changelog needs to know "does this affect me?" — vague entries answer nothing.
- **For backward-incompatible changes:** always state (a) the old behavior, (b) the new behavior, and (c) how to restore the old behavior when possible. A reader upgrading an existing deployment needs all three.

### Prose style

Applies to PR bodies, commit message bodies, review replies, and status reports:

- No marketing adjectives: seamless, robust, powerful, cutting-edge, effortless, next-generation.
- Active voice with a named actor: "the parser reads the file", not "the file is read".
- Use a verb for an action: "analyze the log", not "perform an analysis of the log".
- Prefer the short word: use/utilize, start/initiate, make sure/ensure, about/regarding.
- One name for one thing — do not alternate between two names for the same component.

For longer prose (READMEs, docs, release notes), the `ste-writing` skill in `~/.claude/skills/ste-writing/` applies the full ASD-STE100 rule set. Use its **STE-flavored** mode, not **strict** — strict caps sentences at 20 words and locks the vocabulary to a ~900-word dictionary, which conflicts with the Specificity Rule above and strips necessary technical nouns. Do not adopt its optional "no em dash" rule.

### Example
```
loader: add progress tracking to restore task

This series adds per-item progress tracking to the restore task. Previously, the task reported no progress — `progress_total` and `progress_completed` were always zero, making it impossible to monitor how far along a restore operation is.

### Changes

A `downloaded` boolean column added to `snapshot_items`, with a method to update it. After each item is attached during restore, it is marked as downloaded.

Infrastructure plumbing: dependency changed to a sharded reference and `attach_item` changed to return the attached object.

A periodic timer that queries `snapshot_items` every 5 seconds and exposes downloaded/total counts via `get_progress()`.

A test assertion verifying `progress_total > 0` and `progress_completed == progress_total` after a successful restore.

Fixes: https://github.com/org/repo/issues/986

No backport needed since this is a new feature.
```

---

## Refine PR

When the user says **"refine PR"**, perform the following sequence:

1. **List all commits** in the PR (e.g., `git log --oneline upstream/master..HEAD` or equivalent for the project's main branch).
2. **For each commit**, review the diff (`git show <sha>`) and check:
   - **Commit message**: subject follows `module: short description` format, blank line separates subject from body, body explains *why* not *what*, wrapped at ~72 chars.
   - **Single logical change**: if the commit message needs "and" or "also", it likely needs splitting.
   - **No unrelated changes**: formatting fixes, renames, include cleanups, or test skips that don't belong with the functional change must be in separate commits or removed.
   - **Comments in code**: verify that added comments accurately describe what the code actually does — not what a previous iteration did or what was planned but not implemented.
   - **No unnecessary changes**: no gratuitous renames, no style-only changes mixed with logic, no dead code additions.
   - **Blank line hygiene**: scan each commit for `^+$` / `^-$` (blank line additions/removals). Remove any that aren't structurally required by new code.
3. **Split commits** that contain unrelated changes (e.g., a commit that both changes storage logic and adds test skips should be split so each change goes to its logical home).
4. **Squash or reorder** commits where one undoes or replaces another (e.g., commit A adds a try/fallback approach, commit B replaces it with a different approach → combine into one commit with the final approach).
5. **Move misplaced hunks** to the commit they logically belong to (e.g., test skips belong in the commit that adds the test parametrization, not in an unrelated commit).
6. **Verify compilability**: mentally confirm that each commit in the final sequence compiles independently — removing any later commit should not break the build.
7. **Final diff check**: `git diff <original_HEAD> HEAD --stat` should show only intentional differences (removed noise, fixed skips, etc.) — no accidental content loss.
8. **Do NOT push** — wait for explicit user instruction (canonical no-push rule in *Terminal Command Rules*).

---

## PR Interaction Workflow

### Tools — GitHub MCP (preferred) + `gh` CLI (fallback)

**Primary:** Use GitHub MCP tools for all PR interactions. They return structured data directly, avoid terminal pager/truncation risks, and don't require JSON parsing.

**Fallback (`gh` CLI):** Use only for operations not covered by MCP:
- `gh pr edit <number> --remove-label / --add-label` — manage labels (no MCP equivalent)
- `gh api graphql -f query='mutation { deletePullRequestReviewComment(...) }'` — delete duplicate comments (no MCP equivalent)

### Fetching PR Data

| What | MCP Tool | Method |
|------|----------|--------|
| PR metadata (title, body, state, commits) | `pull_request_read` | `get` |
| PR diff | `pull_request_read` | `get_diff` |
| Changed files | `pull_request_read` | `get_files` |
| Review threads (with thread IDs, isResolved) | `pull_request_read` | `get_review_comments` |
| Reviews (approvals, request-changes) | `pull_request_read` | `get_reviews` |
| PR comments (non-review) | `pull_request_read` | `get_comments` |
| CI check runs | `pull_request_read` | `get_check_runs` |
| Combined commit status | `pull_request_read` | `get_status` |

### PR Review Comments — Two-Phase Workflow

When the user asks to address PR review comments, follow this **two-phase** process:

#### Phase 1: Plan — `$plan-review`
1. Fetch all review threads via `pull_request_read` with method `get_review_comments`.
2. For each **unresolved** thread, build a numbered list with:
   - **File:line** — where the comment is
   - **Reviewer says** — one-line summary of the comment
   - **Planned response** — what you intend to do (code change description OR reply-only with reasoning)
3. **Save the plan to a scratch file** (e.g., `~/.config/JetBrains/CLion2026.1/scratches/GitHubCopilot/plan-review-PR<number>.md`) and open it for the user. This is easier to read than inline agent output.
4. **Stop and wait** for the user to approve/reject/modify each item.

The user triggers this phase by saying **`$plan-review`**.

#### Phase 2: Execute — `$finalize-review`
- Apply code changes only for approved items.
- Post replies only for approved items.
- Follow the rules below for amending commits, replying, and resolving threads.
- **Before the user pushes:** remove the `conflicts` label if present: `gh pr edit <number> --remove-label conflicts`
- ❌ **Do NOT push** — wait for explicit user instruction (canonical no-push rule in *Terminal Command Rules*).

The user triggers this phase by saying **`$finalize-review`**.

**Never make code changes or post replies before the user confirms the plan.**

### Addressing Review Comments (Code Changes)
1. **Analyze each comment** — verify the reviewer's assumptions against actual code before acting (see "Handling Review Comments" above).
2. **Make code changes** in the working tree.
3. **Amend the correct commit** — use `git commit --fixup=<SHA>` + `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <SHA>~1`.
4. **Separate unrelated fixes** — if a reviewer points out a pre-existing bug or a formatting issue, put the fix in its own commit (not bundled with functional changes).
5. ❌ **Do NOT push** — wait for explicit user instruction (canonical no-push rule in *Terminal Command Rules*).

### Replying to Review Comments
- For comments addressed in code: reply with a short confirmation — "Done.", "Addressed.", or "Done — <brief note>." (e.g., "Done — moved to a separate commit.").
- For pushback: leave as-is for the user to handle, or draft a reply explaining why the current code is correct.
- Use `add_reply_to_pull_request_comment` with the comment ID from the review thread.

### Resolving Review Threads
After replying, resolve threads that are fully addressed using `pull_request_review_write` with method `resolve_thread` and the thread's node ID (`threadId`).

To unresolve a thread: use method `unresolve_thread`.

**If duplicate replies occur** (e.g., from a retry after a timeout), delete them via `gh` CLI:
```bash
gh api graphql -f query='mutation { deletePullRequestReviewComment(input: {id: "<COMMENT_ID>"}) { pullRequestReviewComment { id } } }'
```

### Creating Reviews
Use `pull_request_review_write` with method `create`:
- With `event` (`APPROVE`, `REQUEST_CHANGES`, `COMMENT`) — creates and submits immediately.
- Without `event` — creates a **pending review**. Add comments via `add_comment_to_pending_review`, then submit via `pull_request_review_write` method `submit_pending`.

### Managing Labels
No MCP equivalent — use `gh` CLI:
- Remove `conflicts` after rebasing: `gh pr edit <number> --remove-label conflicts`
- Add/remove other labels as appropriate: `gh pr edit <number> --add-label <name>`

### Updating PR Metadata
Use `update_pull_request` to change title, body, state, draft status, or request reviewers.

### Creating Pull Requests — Mandatory Steps (Global)
When creating any PR on GitHub, regardless of repository:
1. Add the `ai-assisted` label: `gh pr edit <number> --add-label ai-assisted`
2. Assign the PR to the user: `gh pr edit <number> --add-assignee <username>`

Repository-specific checklists (e.g., ScyllaDB) add further required steps on top of these.

**Labels are a separate deliverable from the cover letter, and must agree with it.** Writing a decision in prose does not satisfy a label requirement — stating "no backport needed" in a body while omitting `backport/none` left the user to add the label by hand. Apply every required label in the same `gh pr edit` call as `ai-assisted` and the assignee, and check that each one matches what the body claims. If you cannot tell which label applies (e.g. which versions a fix affects), ask before creating the PR.

### PR Cover Letter Review
- Review the title and body against the current commit series.
- Verify the body follows the format defined in "PR Cover Letter" above: Problem → Changes → Issue reference → Backport decision.
- Update if the commit series has materially changed (new commits added/removed, major restructuring). Minor code-level tweaks don't require body updates.

### Push Summary Comment
After the **user** pushes changes that address review comments, post a summary comment on the PR using `add_issue_comment` (pass PR number as `issue_number`). ❌ **Do NOT push yourself** (canonical no-push rule) — wait for the user to push, then post this comment. Format:
```
v next:

- <change 1>
- <change 2>
- ...
```
Example:
```
v next:

- `is_object_storage()` made pure virtual, added override in subclass
- removed unrelated changes (gratuitous blank lines, initialization rewrite)
- logging enhancement split into its own commit
- extracted unrelated typo fix into a standalone commit
```
This helps the reviewer see at a glance what changed without re-reading the full diff. Each bullet should be concise — one line per logical change.

---

## Lessons Learned — Self-Updating Section

This section is **written and maintained by the agent itself**. When the user corrects the agent's approach, points out a wrong assumption, or explains that something should be done differently — and the insight is **general enough to apply in future sessions** — the agent **must** append it here so the mistake is not repeated.

### When to add an entry
- The user says "that's wrong, do it this way instead" and the correction reflects a **recurring pattern**, not a one-off preference.
- The agent's conclusion about how a system/tool/API works turns out to be incorrect, and the correct understanding is non-obvious.
- A workflow or technique that the agent assumed would work fails, and the user provides the working alternative.
- The user explicitly says "remember this" or "write this down".

### When NOT to add an entry
- The correction is trivially obvious or already covered elsewhere in this file.
- It's a one-time, context-specific decision (e.g., "use 3 nodes for this particular test").
- Adding it would contradict an existing instruction — in that case, **discuss with the user first** before updating the existing instruction. Never silently modify established instructions.

### Format
Each entry: a short title, the date, and a concise explanation of what was wrong and what the correct approach is. Keep entries factual and actionable.

### <Short title> (YYYY-MM-DD)
<What the agent assumed or did wrong.>
**Correct approach:** <What to do instead.>

### Procedure
1. Append the new entry at the bottom of this section.
2. Keep entries concise — no more than 3–5 lines each.
3. If an older entry is superseded, update or remove it rather than adding a contradictory one.
4. Commit and push the change (see "Version Control for Instruction Files" above).

### Periodic graduation (squash into standing sections)
This section is a **staging area**, not a permanent home. Periodically review it and **graduate** entries into the appropriate standing section of the instruction files so the knowledge becomes a first-class rule rather than an append-only log.

- **When to graduate:** an entry has proven stable across several sessions, multiple entries cluster around the same theme, or an entry clearly belongs in an existing section (e.g., a terminal lesson → "Terminal Command Rules", a commit lesson → "Commit Organization").
- **How:** fold the insight into the relevant standing section (rewriting for consistency with surrounding prose), then remove the now-redundant entry here. Don't leave the same rule in two places.
- **Cadence:** do a graduation pass whenever this section grows past ~5–7 entries, or when explicitly asked. Leave a dated HTML comment noting when the last graduation happened.
- Graduating is itself an instruction-file edit — commit and push it (see "Version Control for Instruction Files").

<!-- Graduated: all prior entries folded into standing sections on 2026-05-24 and again on 2026-07-29. The section starts fresh below. -->
