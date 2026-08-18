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
| `scylla/spot-fleet-setup.md` | Running a locally-built binary (scylla or a perf test) across **many cheap throwaway instances** — spot fleet, bulk launch/teardown, local NVMe | Fedora-vs-Ubuntu AMI choice, per-architecture AMI lookup, storage-optimized families, tagging for bulk cleanup, NVMe prep, binary deployment, terminate-not-stop teardown. Sibling of the two single-instance docs below, which own the credential/SSH machinery |
| `scylla/arm-instance-setup.md` | Working with ARM/aarch64 testing or the personal ARM EC2 instance | Full reference: instance ID, AWS start/stop commands, Ubuntu-specific patches, library setup, LD_LIBRARY_PATH requirement |
| `scylla/x86-instance-setup.md` | Working with the x86 i4i.4xlarge EC2 instance (perf tests, S3 stress) | Instance ID, copying Fedora libs to Ubuntu, passing AWS creds via script, ulimit, background runs |
| `copilot-oom-prevention.md` | Copilot language server crashes (OOM/SIGABRT) in **any** large workspace | The general problem (the startup walk ignores `.gitignore`, so only `.copilotignore` helps), defense layers, `NODE_OPTIONS` heap, and the per-project assessment procedure |
| `scylla/copilot-oom-provisioning.md` | Provisioning a ScyllaDB clone against OOM | ScyllaDB-specific only: the `.copilotignore` template contents, automatic install via the git `post-checkout` hook, `setup-scylla-workspace` for existing clones, and `testlog/` maintenance |
| `scylla/rtk-setup.md` | Setting up or debugging **RTK** output compression for Copilot in a JetBrains IDE | Why the IDE ignores `~/.copilot/hooks/` and loads only `<repo>/.github/hooks/**/*.json`, why the event must be `preToolUse` not `PreToolUse`, and why rtk must use deny-with-suggestion (the host ignores `modifiedArgs`) |
| `scylla/bin/refresh-aws-creds` | Any machine that needs AWS credential refresh | Installable script — copy to `~/.local/bin/` and `chmod +x`. See new-machine setup in arm-instance-setup.md |
| `scylla/bin/setup-scylla-workspace` | Provisioning a new or existing ScyllaDB clone | Installs `.copilotignore`, CLion excludeRoots, git exclude |
| `scylla/warp-setup.md` | Installing/using Cloudflare WARP Zero Trust on Fedora | TL;DR + `warp-login` automation + Fedora-specific install (`webkit2gtk3` nodeps workaround) + lessons learned |
| `scylla/bin/warp-login` | Daily WARP enrollment automation | Symlink into `~/.local/bin/`. Opens enrollment URL, polls clipboard for the token, registers, connects, selects `scylla-cloud-prod` VNet |
| `scylla/bin/warp-login-handler` | Browser-button → `warp-login --token` glue | Symlink into `~/.local/bin/`. Invoked by the user-level `~/.local/share/applications/com.cloudflare.warp.desktop` MIME handler when the blue "Open Cloudflare WARP" button is clicked. Logs to `~/.local/state/warp-login.log` and notifies via `notify-send` |

### Personal Repos

| File | When to load | Description |
|------|-------------|-------------|
| `~/Development/weekly-reports/AGENTS.md` | User mentions **weekly report**, "this week's report", "start a new week", or asks to record accomplishments/blockers/next-week items | Private GitHub repo `kreuzerkrieg/weekly-reports`. ISO-week-numbered markdown files, template-based. Auto-push is explicitly enabled here (overrides the global no-push rule). |

**Weekly status email — never send via a Google/Gmail MCP connector.** Generate an email-ready markdown file next to the week's report at `~/Development/weekly-reports/<YYYY>/<YYYY>-W<NN>-email.md`, built fresh from `<YYYY>-W<NN>.md`: greeting "Hi Łukasz,", mirror the `##`/`###` structure, preserve bold ticket keys and Jira/PR links, omit the `## Needs your input` section and the top "Draft…" note, close with "Sincerely," / "Ernest". Then render it: `python3 tools/md2email.py 2026/<file>.md > /tmp/out.html` from the weekly-reports repo, and hand the user that path. Do not stop at the markdown. Copying a rendered markdown preview carries the viewer's theme with it, so pasting from CLion's dark scheme puts black blocks behind every heading and table in Gmail; the script emits inline light styles that Gmail's sanitizer keeps. The user opens the HTML, selects all, copies, and pastes.

**Always read the relevant file at the start of a session** using `read_file` — do not rely on memory from prior conversations. If a file does not exist yet, notify the user so it can be created.

### This repo holds durable instructions, not task state

Per-task handoff specs — investigation notes for one PR, an implementation plan for one fix, measurements from one set of runs — do **not** belong here. They expire when the work merges, and they are indistinguishable from standing rules once a routing-table row points at them. Keep them in the agent's private working area instead:

```
~/.config/JetBrains/CLion<version>/scratches/GitHubCopilot/_internal/<topic>/
```

Current in-flight task state living there: `_internal/s3-throttler/` (S3 send-rate throttler — PR 30775, SCYLLADB-3249, SRE-1418: fleet-run measurements, the code-level reasons the throttler does not yet work, the retry-pacing implementation plan, and the no-budget-for-more-fleet-runs constraint). **Note:** the scratches path is pinned to the CLion major version, so it does not follow a version upgrade and is not synced between machines. If a handoff spec needs to survive either, give it its own repo rather than adding it back here.

A finding only belongs in this repo once it has outlived its task and become a rule that applies to future work — at which point it goes into a standing section, not a new file.

Claude Code's memory directory (`~/.claude/projects/<mangled-project-path>/memory/`) is a second
staging area feeding this repo, and it is scoped per project *path* — it does not follow a different
clone of the same project or another machine. Split it the same way: task state and not-yet-proven
lessons live there and are **deleted** when the work merges; a rule that has outlived its task
graduates into a standing section here, and the memory file is then removed. Never leave the same
rule in both places. Rewrite on graduation — the `**Why:** / **How to apply:**` shape and the
`[[wiki-links]]` are memory-format artifacts, and a link to a memory that was never graduated points
at nothing.

---

## Playbooks — Load On Demand

Procedures that are only needed at a specific moment live in `playbooks/`. They are **not** loaded at
session start. Read the file when its trigger fires, and do not preload them "just in case".

| Playbook | Load when |
|----------|-----------|
| `playbooks/pr-workflow.md` | Creating a PR, writing or reviewing a cover letter, `$plan-review`, `$finalize-review`, "refine PR", replying to or resolving review threads |
| `playbooks/commit-splitting.md` | Splitting a WIP commit or reorganizing a commit series |
| `playbooks/machine-setup.md` | Provisioning a new machine or clone: gitleaks hooks, `.copilotignore` / Copilot OOM, AWS credential refresh |
| `playbooks/chat-history-export.md` | Exporting Copilot/CLion transcripts, rebuilding the `ai-search` indexes |
| `playbooks/mcp-and-jira.md` | Jira or Confluence work, or evaluating a new MCP server |

The rules those procedures must obey stay here in the core file — a playbook carries mechanics, never
a rule you could violate without knowing to look it up.

---

## Search Prior Conversations Before Re-Deriving

Past sessions across agents are exported to `~/ai-history-archive/` and indexed locally. Before
re-deriving something that may already be solved — a tricky build failure, a review decision, an
incident, a config fix — search that history first:

```bash
ai-search buffered_readable_file                     # keyword (BM25/FTS5): code, symbols, error strings
ai-search -s "how did we avoid streaming sstables"   # semantic: "how did I..." recall
```

Mechanics, flags, and index rebuilding: `playbooks/chat-history-export.md`.

---

## Jira and MCP — Quick Routing

Jira and Confluence are reachable through the **Atlassian MCP server** in `mcp.json` (OAuth via
browser, no token needed; instance `https://scylladb.atlassian.net`). If those tools are absent from
the session, say so rather than inventing results — see *Verify Everything*. Details, REST fallback,
and the rule for evaluating new MCP servers: `playbooks/mcp-and-jira.md`.

---

## Scratch / Temporary Files (CLion-specific)
When creating **any** temporary or scratch files — analysis docs, migration call-chain notes, diagrams, test timing reports, query results, generated tables, or any other output that is not a source-code change — save them under the CLion scratches directory instead of polluting the repository tree:
```
~/.config/JetBrains/CLion<version>/scratches/GitHubCopilot/
```
Resolve `<version>` from the newest directory present: `ls -dt ~/.config/JetBrains/CLion*/ | head -1`. The path is pinned to the CLion major version and does **not** follow an IDE upgrade, so a stale hard-coded version silently writes into an abandoned directory.
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
DST="$(ls -dt ~/.config/JetBrains/CLion*/ | head -1)scratches/GitHubCopilot/_internal/README.md"
mkdir -p "$(dirname "$DST")"
[ ! -f "$DST" ] || [ "$SRC" -nt "$DST" ] && cp "$SRC" "$DST"
```
Keep machine-specific item tracking in a separate **local** `_internal/INVENTORY.md` (untracked) —
a short table of each item, its purpose, and when it's safe to delete — so the README stays a
clean, overwrite-safe copy of the repo template.

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

## `$cmd` — List All Commands

When the user types **`$cmd`**, list all defined `$`-prefixed commands with a one-line description of each. Scan both global and project-specific instruction files for command definitions. Current commands:

| Command | Defined in | Description |
|---------|-----------|-------------|
| `$cmd` | global | List all defined `$` commands |
| `$plan-review` | `playbooks/pr-workflow.md` | Phase 1: plan responses to PR review comments (no changes until approved) |
| `$finalize-review` | `playbooks/pr-workflow.md` | Phase 2: execute approved plan from `$plan-review` |
| `$debunk <URL>` | scylladb | Triage a PR bot CI failure comment — verify each claim, propose Jira issues |
| `$analyze-ci` | scylladb | Analyze PR/CI test failures by error signature, classify, and draft Jira issues |

**Maintenance:** When adding a new `$` command to any instruction file, also add it to this table.

---

## Prose Style

Applies to PR bodies, commit message bodies, Jira comments, code comments, review replies, and status reports:

- No marketing adjectives: seamless, robust, powerful, cutting-edge, effortless, next-generation.
- Active voice with a named actor: "the parser reads the file", not "the file is read".
- Use a verb for an action: "analyze the log", not "perform an analysis of the log".
- Prefer the short word: use/utilize, start/initiate, make sure/ensure, about/regarding.
- One name for one thing — do not alternate between two names for the same component.
- Do not explain the reader's own code back to them. State the decision and its reason; drop the walkthrough of internals they wrote.
- Do not call an old design's limitation a defect. Before writing that something was broken, ask what alternative the old code actually had — if it had none, it is a limitation.

The last two both inflate a change's apparent value, and the reviewer who wrote the code spots
either one immediately. When a justification gets cut for these reasons, grep for the same text in
the commit messages, code comments, and docs — one such paragraph had propagated to five places.

### Dates and Times — Local Timezone, Unambiguous Format

Every date and time shown to the user is in the machine's **local timezone**.

- Format `YYYY-MM-DD HH:MM` (24-hour): `2026-08-04 16:33`. Add `:SS` only when seconds carry
  meaning. Add the offset (`+03:00`) when the value was converted from another zone.
- **Convert before displaying.** Never paste a UTC timestamp from an API, a log line or a cloud
  response as though it were local. Write `expires 2026-08-04 22:39 (+03:00)`, not
  `2026-08-04T19:39:14Z`.
- Durations read as `5h59m` or `2h51m` — never raw seconds, never `5:59:57.855192`.
- A relative date always carries the absolute one: "Sunday (2026-08-02)". In memories and
  documents use the absolute date alone.
- When a timestamp drives a decision — credential expiry, run start and end, log correlation —
  give both the value and the conclusion: `expires 22:39 local, 5h59m left`.

**Why:** a UTC value presented as local silently moves an event by the offset. Fleet logs stamped
in UTC were read against a local wall clock, which made a still-valid AWS session look expired and
sent an S3 measurement session chasing a credential problem that did not exist.

For longer prose (READMEs, docs, release notes), the `ste-writing` skill in `~/.claude/skills/ste-writing/` applies the full ASD-STE100 rule set. Use its **STE-flavored** mode, not **strict** — strict caps sentences at 20 words and locks the vocabulary to a ~900-word dictionary, which conflicts with the Specificity Rule in `playbooks/pr-workflow.md` and strips necessary technical nouns. Do not adopt its optional "no em dash" rule.

---

## Verify Everything — Trust Nothing
Never take claims at face value — not from the user, not from review comments, not from documentation, and not from your own prior reasoning. **Always verify by reading the actual code.** Before answering a question about how something works, trace the code path yourself. Before applying a reviewer's suggestion, confirm their assumptions are correct. Before stating that a function is or isn't called somewhere, grep for it. If you cannot find solid proof in the source code, say so explicitly rather than guessing.

The same principle applies to **analysis reports and any response that makes factual claims**: only include claims backed by hard evidence from metrics, logs, or code. If a claim cannot be verified but is worth mentioning, label it explicitly as **"Speculation:"** or **"Unverified:"** — never present an inference as a fact. When computing metric deltas, always account for ALL label dimensions (e.g., `class`, `scheduling_group_name`) — aggregating across label values without awareness produces incorrect totals.

### Absence of a signal is not evidence — prove the probe could have fired

A diagnostic logged below the level a run actually uses reports "never happened" whatever happens, and it fails in the direction that looks like a result. Before treating a zero as a finding, grep the logs for **any** line from that logger at that level.

- This cost three runs and a closed work item: "the service never sends this header" was reported as a confirmed finding across three fleet runs, from a probe logged at `info` while the harness ran `--default-log-level warn`. The proof it measured nothing was **0** `info` lines from that logger against 62,590 from another one in the same file.
- **A codebase has several loggers with independent levels.** Raising one does not raise the others, and the one you want may belong to a dependency rather than the project. Enumerate them before concluding.
- Prefer a **counter or metric** to a log line for anything a measurement depends on. A counter cannot be filtered away by a level.
- **Never draw a conclusion from a snapshot of an in-flight measurement.** A mechanism reported "barely engaging, unlikely to explain anything" from 2 observed events mid-pass turned out to have fired 15,750 times by the end. Wait for the run, or say explicitly that the number is partial.

### Never fabricate specifics

Never write a log line, timestamp, ticket ID, cluster ID, error message, DC/rack name, customer name, commit SHA, or any other specific fact that requires a data source, unless that data source has been queried **in this session**. Prior-session memory does not count.

- If no tools have been called yet, say so explicitly ("I have no data on this cluster — let me query…") and call them. Never open a reply with a situation report assembled from plausible-sounding details.
- Speculation is allowed, but must be prefixed **"Speculation:"** / **"Hypothesis:"** and kept separate from anything presented as fact.
- **Landing on a real identifier by chance is worse than obvious nonsense** — it makes the confabulation hard to spot and can leak into an incident channel. This has happened: three invented IDs all turned out to reference a real ticket.
- **"X does not exist" is a positive claim and needs the same evidence.** Never declare a Jira issue, GitHub issue, Confluence page, PR number, or commit SHA nonexistent without an actual query. If the tool is unavailable, write "cannot verify — treating as unverified", not a nonexistence verdict.

### Read the implementation — never infer behavior from a name

For any function whose name implies a lifecycle transition (`after_test`, `stop`, `shutdown`, `teardown`, `cleanup`, `finalize`, `destroy`, `close`, `dispose`), never infer its side-effects from the name or from where it is called. Open it and read it. Names in test-harness code particularly love to lie: `after_test` often means "notify and validate", not "stop everything", and `close`/`cleanup` may release only a subset of resources. Getting this wrong once placed teardown callbacks against a still-running cluster and reproduced the exact race the change was meant to fix.

### `git blame` credits the last mover, not the author

Blame attributes a line to whoever last touched it, so any refactor that moves code steals
authorship. Chasing "who added this hack" via blame named a refactoring commit whose diff was purely
mechanical, and the real author was three months earlier. Confirm origin with a content search
before naming anyone:

```bash
 git log -S '<distinctive token from the line>' --format='%h %ad %an | %s' --date=short -- <path>
```

Prefer a token unlikely to appear elsewhere (a magic constant, an unusual phrase from a comment).

### Reachable in code is not the same as observed in production

Tracing a path to `abort()` or to data loss proves it *can* happen, not that it *did*. Before calling
something an availability risk or an incident, grep a real run for the symptom — the abort message,
the coredump, the restart — and say which it is. An artificial reproduction (a patched build, an
injected error) is evidence the mechanism is real, never evidence of production impact. Getting this
backwards inflated a defect worth 69 log lines into a claimed node-crash risk, and the user caught it
by asking "do you see from logs that the node was terminated?" — the answer was no.

### A workaround's comment explains itself; that does not make it right

When a comment justifies a hack ("minio treats a zero-sized upload as a no-op"), treat the *necessity*
of the hack and the *stated cause* as two separate claims and test them separately. The hack can be
load-bearing while its explanation is wrong — in that case the comment sends the next reader at the
wrong layer. Necessity is settled by removing it and measuring; the stated cause is settled by
probing the dependency directly (a signed `curl` against the endpoint, a unit test at the API
boundary).

Always take the baseline: run the suite unmodified, with the workaround removed, and with the
candidate fix. Three numbers attribute the failure; two do not. Removing 7 lines gave 37 failed / 94
passed against a 131-passed baseline, which is what made the argument reviewable.

### A wrapper's diagnosis is not the error

A script that classifies failures by grepping a fixed list of error names reports its fallback category for everything it does not recognise. A launch script printed "no capacity" for two configuration bugs — subnets enumerated without a VPC filter, and an AZ that does not offer the instance type at all — and half an hour went into chasing a phantom AWS capacity drought.

- When a wrapper reports the same generic cause for every attempt, that uniformity is the tell. Reproduce one attempt by hand and read the raw error before believing the summary.
- Run any newly patched CLI invocation standalone once and read its output. A CLI *parse* error looks identical to a service error once a wrapper has classified it.
- When writing such a classifier, make the fallback branch print the raw error text, never a guessed category.

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

### Diff a run against its baseline before paying for it

A measurement that extends an existing series only answers anything if every load-bearing parameter matches the series. A 16-node fleet run launched at the launcher's default instance size (8xlarge, 32 shards) while the whole earlier series used 16xlarge (64 shards) produced 1 throttling response in 3 million requests and measured nothing — request amplification is a per-node shard-count effect, and the data proving 8xlarge was wrong was already in hand.

Before launching, write the baseline's parameters and the new run's side by side — instance type *and size*, shard/CPU count, node count, phases, duration, target — and state the diff. If a load-bearing parameter differs, fix it or say up front what the run cannot answer. Defaults in a launcher are not the series' parameters.

### An upstream default is not an argument for our parameter

Constants imported from another project are calibrated against *that* project's policy. Having imported aws-sdk-cpp's retry-quota constants, which are tuned for its `maxAttempts=3`, recommending our retry depth drop from 10 to 3 "because AWS ships 3" inverted the argument — and our own measurements pointed the other way, since losses had fallen as the retry window got *longer*.

Check what policy an imported constant was tuned against, resize the constant to our policy, and document the derivation. If the borrowed budget conflicts with our policy, resize the budget, not the policy. Never let "upstream ships this" be the whole argument.

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

### Processes, fan-out loops, and long-running commands

- **Never use `pgrep -f` / `pkill -f` from a tool shell.** The pattern text appears in the tool's own `bash -c` command line, so it always self-matches: `pkill -f "s3-fleet.sh launch"` killed the agent's own shell, and `pgrep -f "s3-fleet"` reported a finished setup as still running. List with `ps -eo pid,etime,cmd | grep -E <pat> | grep -v grep`, then act on the PID. Kill orphaned children (e.g. `aws ec2 wait`) separately — they outlive the parent.
- **`ssh` inside a `while read` loop eats the loop's input.** Always `ssh -n` (or `< /dev/null`) in a read loop, and print a count at the end of every fan-out, asserting it equals the expected host count. A 16-node check that silently visited one host reported `checked 1`, which reads exactly like 15 unreachable nodes.
- **`setsid` forks, so `$!` is not the process you started.** The captured PID exits immediately while the real work continues under a new one, so `ps -p $!` reports "finished" while a build is still linking. Poll the **log** for a completion marker, never the PID. Corollary: a leftover artifact on disk makes a failed build look green — check the log for `error:`/`FAILED` **and** that the artifact is newer than every source you changed, before claiming a build passed. Both of these produced a false "build OK" in one session.
- **The terminal tool SIGTERMs at ~10 minutes regardless of the timeout requested.** Start anything that may exceed ~8 minutes detached — `setsid nohup ./cmd > "$SCRATCH/cmd.log" 2>&1 &`, or the harness's background mode where it has one — and poll the log in short calls. If a resource-provisioning command is killed, query the provider for what was actually created *before* retrying, or the retry doubles the resources.

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

<!-- Graduated: all prior entries folded into standing sections on 2026-05-24, 2026-07-29, and again on 2026-08-03. The section starts fresh below. -->

### Weekly status email written from memory, without links or the render step (2026-08-13)

Generated `<YYYY>-W<NN>-email.md` from memory of the format instead of re-reading this
spec and `~/Development/weekly-reports/AGENTS.md`. The result dropped every Jira/PR link
and bold ticket key (37 links in the corrected version, 0 in mine), invented its own
section headings rather than mirroring the report, used a bare "Ernest" instead of
"Sincerely," / "Ernest", and never ran `tools/md2email.py` — so the known dark-theme
background bug went unaddressed. The same defect is already committed in W31's email.
**Correct approach:** re-read both files before generating any recurring deliverable. A
format you have produced before is exactly the kind you will misremember, and the spec
spans two files — content shape here, rendering in the repo's own AGENTS.md.

