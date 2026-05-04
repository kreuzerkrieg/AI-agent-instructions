# Global AI Coding Agent Instructions

**This is the global instructions file** (`~/.config/github-copilot/intellij/global-agents-instructions.md`). It is loaded for every conversation regardless of which repository is open. Repository-specific instructions live in `.github/copilot-instructions.md` inside each repo.

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
| `scylla/scylladb-instructions.md` | Working in **scylladb/scylladb** repo (the main C++ database) | Build system, C++/Python code style, commit organization, PR format, test philosophy, backtrace decoding |
| `scylla/sct-instructions.md` | Working in **scylla-cluster-tests** repo (or any SCT task) | SCT-specific conventions, architecture, analysis workflows, metric mappings |
| `scylla/scylladb_all_metrics_mapping.md` | Reference for SCT metric analysis | Full mapping of ScyllaDB Prometheus metrics |

**Always read the relevant file at the start of a session** using `read_file` — do not rely on memory from prior conversations. If a file does not exist yet, notify the user so it can be created.

---

## Scratch / Temporary Files (CLion-specific)
When creating **any** temporary or scratch files — analysis docs, migration call-chain notes, diagrams, test timing reports, query results, generated tables, or any other output that is not a source-code change — save them under the CLion scratches directory instead of polluting the repository tree:
```
~/.config/JetBrains/CLion2026.1/scratches/GitHubCopilot/
```
Create the directory if it does not exist. **Never** place such files inside the repository working tree. This applies even when the user asks you to "build a table" or "save the results" — always default to the scratches directory unless the user explicitly specifies a different path.

## Version Control for Instruction Files
The instruction files directory (`~/.config/github-copilot/intellij/`) is a git repository tracked at `git@github.com:kreuzerkrieg/AI-agent-instructions.git`. **After making any edit** to files in this directory, commit and push the change:
```bash
cd ~/.config/github-copilot/intellij
git add -A && git commit -m "<short description of what changed>" && git push
```
This replaces the old backup-file approach — git history provides full versioning. Commit messages should be concise but descriptive (e.g., "Add backtrace decoding section to SCT instructions").

**Pull before starting work:** These instruction files may be edited by agents on other machines. At the **start of every session**, pull the latest version before reading or modifying any instruction file:
```bash
cd ~/.config/github-copilot/intellij && git pull --rebase
```
This avoids conflicts and ensures you are working with the most current instructions.

## Verify Everything — Trust Nothing
Never take claims at face value — not from the user, not from review comments, not from documentation, and not from your own prior reasoning. **Always verify by reading the actual code.** Before answering a question about how something works, trace the code path yourself. Before applying a reviewer's suggestion, confirm their assumptions are correct. Before stating that a function is or isn't called somewhere, grep for it. If you cannot find solid proof in the source code, say so explicitly rather than guessing.

## Terminal Command Rules

- **Leading space on every command:** Always prefix terminal commands with a single leading space (` git status`, not `git status`). Fedora's default `HISTCONTROL=ignoreboth` (which includes `ignorespace`) causes bash to skip recording commands that start with a space. This keeps the user's shell history clean of agent-generated commands.

> **⚠️ CRITICAL: You MUST NEVER run any terminal command that requires user intervention or waits for input.** This is an absolute, non-negotiable rule. Violations block the terminal and require the user to manually intervene. Offending commands include but are not limited to: `git rebase -i` (even with `--autosquash`), `git commit` without `-m`/`-F`, interactive editors (`vim`, `nano`, `less`), pagers, `read`, `select`, or any tool that prompts for input. The **only** exception is `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash` which is explicitly non-interactive because `GIT_SEQUENCE_EDITOR=true` suppresses the editor.

- Commands whose output may exceed the terminal window (e.g. `git log`, `git diff --stat`, `git show`) **must** redirect output to a temporary file, then read it with `cat` or `read_file`. Never rely on the terminal fitting all output — if it doesn't, the command blocks waiting for user input (pager). Example: `git log --oneline HEAD~20..HEAD > /tmp/commits.txt && cat /tmp/commits.txt`
- Always use `git --no-pager` or pipe through `| cat` as an alternative when redirection is inconvenient.
- To amend an older commit, use fully non-interactive techniques:
  - **Cherry-pick rebuild:** `git reset --hard <SHA>~1`, then `git cherry-pick --no-commit <SHA> && git commit -F <msg-file>`, then `git cherry-pick <SHA>..<original-HEAD>`.
  - **Fixup + autosquash:** `git commit --fixup=<SHA>` (content) or `git commit --allow-empty --fixup=amend:<SHA> -F <msg-file>` (message), then `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <SHA>~1` — the `GIT_SEQUENCE_EDITOR=true` prevents any editor from opening, making the `-i` flag safe.
- To amend the most recent commit message: write the new message to a file, then `git commit --amend -F <msg-file>`. Never use `git commit --amend` without `-m` or `-F` — that opens an editor.

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

### Load project-specific instructions at session start — SUPERSEDED (2026-04-30, 2026-05-03, 2026-05-04)
Repeated failures to load project-specific instructions at session start despite multiple lessons-learned entries.
**Correct approach:** Moved to `## ⚠️ MANDATORY FIRST ACTIONS` section at the top of this file as a non-negotiable checklist. The checklist format prevents the agent from skipping it.

### Never push to remote without explicit permission — except the instructions repo (2026-04-30, updated 2026-05-04)
The agent force-pushed commits to a code repository's remote branch without being asked to do so.
**Correct approach:** Never `git push` (or `git push --force`) to any **code repository** remote until the user explicitly asks to push. Local commits, amends, and rebases are fine — but publishing code to a remote is the user's decision. **Exception:** The instructions repo (`~/.config/github-copilot/intellij/`, remote `git@github.com:kreuzerkrieg/AI-agent-instructions.git`) is fully agent-managed — always commit **and push** changes to it immediately, without waiting for permission.

### Never speculate in analysis reports — only state verified facts (2026-05-04)
The agent included unverified speculation in analysis reports (e.g., "~5 SSTable components", "PUTs likely from system tables/commitlog") without evidence, and didn't label them as speculation. When the user challenged these claims, they turned out to be wrong.
**Correct approach:** (1) Only include claims backed by hard evidence from metrics/logs. (2) If a claim cannot be verified but is worth mentioning, explicitly label it as "**Speculation:**" or "**Unverified:**". (3) Never present inferences as facts. (4) When computing metric deltas, always account for ALL label dimensions (e.g., `class`, `scheduling_group_name`) — aggregating across labels without awareness produces incorrect totals.

### Never use interactive rebase with reword — use cherry-pick rebuild for message amends (2026-05-04)
The agent used `GIT_SEQUENCE_EDITOR="sed -i ..." EDITOR="cp ..." git rebase -i` with `reword` to change commit messages. This violates the "never run commands that require user intervention" rule — `reword` opens an editor, and working around it with `EDITOR=` is fragile and led to blank-line formatting issues.
**Correct approach:** To amend an older commit's message: (1) `git reset --hard <SHA>`, (2) `git commit --amend -F <msg-file>`, (3) `git cherry-pick <SHA>..<original-HEAD>`. Or for content-only fixups: `git commit --fixup=<SHA>` then `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <SHA>~1`. Never use `reword` in rebase.
### Refine PR must verify diff minimality — no gratuitous blank lines (2026-05-04)
The agent added extra blank lines in refactored code and did not catch them during the "refine PR" step. The scylladb instructions explicitly state: "Never add or remove blank lines that are unrelated to the task" and "the diff should contain only the lines required for the functional change."
**Correct approach:** During "refine PR", always `git show <sha>` each commit and scan for `^+$` / `^-$` (blank line additions/removals). If any exist that aren't structurally required by new code, remove them before finalizing.
