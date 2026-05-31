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
- [Scratch / Temporary Files (CLion-specific)](#scratch--temporary-files-clion-specific)
- [MCP Discovery — Opportunistic Search for New Tools](#mcp-discovery--opportunistic-search-for-new-tools)
- [`$cmd` — List All Commands](#cmd--list-all-commands)
- [Jira Integration (Atlassian MCP)](#jira-integration-atlassian-mcp)
- [Verify Everything — Trust Nothing](#verify-everything--trust-nothing)
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

3. **Only then** begin working on the user's request.

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
| `scylla/arm-instance-setup.md` | Working with ARM/aarch64 testing or the personal ARM EC2 instance | Full reference: instance ID, AWS start/stop commands, Ubuntu-specific patches, library setup, LD_LIBRARY_PATH requirement |
| `scylla/x86-instance-setup.md` | Working with the x86 i4i.4xlarge EC2 instance (perf tests, S3 stress) | Instance ID, copying Fedora libs to Ubuntu, passing AWS creds via script, ulimit, background runs |
| `scylla/bin/refresh-aws-creds` | Any machine that needs AWS credential refresh | Installable script — copy to `~/.local/bin/` and `chmod +x`. See new-machine setup in arm-instance-setup.md |

**Always read the relevant file at the start of a session** using `read_file` — do not rely on memory from prior conversations. If a file does not exist yet, notify the user so it can be created.

---

## Scratch / Temporary Files (CLion-specific)
When creating **any** temporary or scratch files — analysis docs, migration call-chain notes, diagrams, test timing reports, query results, generated tables, or any other output that is not a source-code change — save them under the CLion scratches directory instead of polluting the repository tree:
```
~/.config/JetBrains/CLion2026.1/scratches/GitHubCopilot/
```
Create the directory if it does not exist. **Never** place such files inside the repository working tree. This applies even when the user asks you to "build a table" or "save the results" — always default to the scratches directory unless the user explicitly specifies a different path.

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

---

## Terminal Command Rules

- **Leading space on every command:** Always prefix terminal commands with a single leading space (` git status`, not `git status`). This relies on `HISTCONTROL` containing `ignorespace` (or `ignoreboth`), which causes bash to skip recording commands that start with a space, keeping the user's shell history clean of agent-generated commands. **Note:** this is NOT set by default on this machine — it was added manually to `~/.bashrc` (`export HISTCONTROL=ignoreboth`). If the leading-space trick stops working, verify the setting with `echo $HISTCONTROL`.

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

<!-- All prior entries were graduated into standing sections on 2026-05-24. The section starts fresh below. -->

### insert_edit_into_file can silently duplicate blocks in large files (2026-05-31)
The `insert_edit_into_file` tool duplicated a block when editing this large file, and the duplicate survived to the pushed version because verification only compared section content as an unordered set — which cannot detect a pre-existing duplicate carried through unchanged.
**Correct approach:** For structural edits to large files, prefer deterministic file-based scripts (read → transform → write), and after any edit grep for duplicate headings/blocks (e.g. `grep -c "### Heading"`) rather than relying on set/checksum equality.
