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
| `scylla/scylladb-instructions.md` | Working in **scylladb/scylladb** repo (the main C++ database) | Build system, C++/Python code style, test philosophy, backtrace decoding |
| `scylla/sct-instructions.md` | Working in **scylla-cluster-tests** repo (or any SCT task) | SCT-specific conventions, architecture, analysis workflows, metric mappings |
| `scylla/scylladb_all_metrics_mapping.md` | Reference for SCT metric analysis | Full mapping of ScyllaDB Prometheus metrics |

**Always read the relevant file at the start of a session** using `read_file` — do not rely on memory from prior conversations. If a file does not exist yet, notify the user so it can be created.

ni### Personal / Cross-Project (`personal/`)

| File | When to load | Description |
|------|-------------|-------------|
| `personal/linkedin-from-git-instructions.md` | User asks to generate a LinkedIn job description from git history | Step-by-step procedure for analyzing a contributor's commits and producing a professional job description |

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

**Adding new instruction files:** The `.gitignore` uses an inverted pattern (ignore everything, whitelist known files). When adding a new instruction file or subdirectory, you **must** add a corresponding `!filename` or `!dirname/` + `!dirname/**` entry to `.gitignore` so git tracks it.

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

## Refine PR

When the user says **"refine PR"**, perform the following sequence:

1. **List all commits** in the PR (e.g., `git log --oneline upstream/master..HEAD` or equivalent for the project's main branch).
2. **For each commit**, review the diff (`git show <sha>`) and check:
   - **Commit message**: subject follows `module: short description` format, blank line separates subject from body, body explains *why* not *what*, wrapped at ~72 chars.
   - **Single logical change**: if the commit message needs "and" or "also", it likely needs splitting.
   - **No unrelated changes**: formatting fixes, renames, include cleanups, or test skips that don't belong with the functional change must be in separate commits or removed.
   - **Comments in code**: verify that added comments accurately describe what the code actually does — not what a previous iteration did or what was planned but not implemented.
   - **No unnecessary changes**: no gratuitous renames, no style-only changes mixed with logic, no dead code additions.
3. **Split commits** that contain unrelated changes (e.g., a commit that both changes storage logic and adds test skips should be split so each change goes to its logical home).
4. **Squash or reorder** commits where one undoes or replaces another (e.g., commit A adds a try/fallback approach, commit B replaces it with a different approach → combine into one commit with the final approach).
5. **Move misplaced hunks** to the commit they logically belong to (e.g., test skips belong in the commit that adds the test parametrization, not in an unrelated commit).
6. **Verify compilability**: mentally confirm that each commit in the final sequence compiles independently — removing any later commit should not break the build.
7. **Final diff check**: `git diff <original_HEAD> HEAD --stat` should show only intentional differences (removed noise, fixed skips, etc.) — no accidental content loss.

---

## PR Interaction Workflow

### Tools
Use `gh` CLI for all GitHub PR interactions. Key commands:
- `gh pr view <number> --json <fields>` — fetch metadata
- `gh pr edit <number> --remove-label / --add-label` — manage labels
- `gh pr comment <number> --body '...'` — post comments
- `gh api graphql -f query='...'` — for review thread replies, resolution, and comment deletion

### Fetching PR Data
```bash
# Metadata (title, body, labels, state, commits)
gh pr view <number> --json title,body,labels,state,commits,reviews,reviewRequests

# Review threads with IDs (needed for replies/resolution)
gh api graphql -f query='{
  repository(owner: "<OWNER>", name: "<REPO>") {
    pullRequest(number: <N>) {
      reviewThreads(first: 50) {
        nodes {
          id
          isResolved
          comments(first: 10) {
            nodes { id body author { login } path }
          }
        }
      }
    }
  }
}'
```

### PR Review Comments — Two-Phase Workflow

When the user asks to address PR review comments, follow this **two-phase** process:

#### Phase 1: Plan (present to user, wait for approval)
1. Fetch all review threads (see "Fetching PR Data" above).
2. For each **unresolved** thread, present a numbered list with:
   - **File:line** — where the comment is
   - **Reviewer says** — one-line summary of the comment
   - **Planned response** — what you intend to do (code change description OR reply-only with reasoning)
3. **Stop and wait** for the user to approve/reject/modify each item.

#### Phase 2: Execute (only after user says go)
- Apply code changes only for approved items.
- Post replies only for approved items.
- Follow the rules below for amending commits, replying, and resolving threads.

**Never make code changes or post replies before the user confirms the plan.**

### Addressing Review Comments (Code Changes)
1. **Analyze each comment** — verify the reviewer's assumptions against actual code before acting (see "Handling Review Comments" above).
2. **Make code changes** in the working tree.
3. **Amend the correct commit** — use `git commit --fixup=<SHA>` + `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <SHA>~1`.
4. **Separate unrelated fixes** — if a reviewer points out a pre-existing bug or a formatting issue, put the fix in its own commit (not bundled with functional changes).

### Replying to Review Comments
- For comments addressed in code: reply with a short confirmation — "Done.", "Addressed.", or "Done — <brief note>." (e.g., "Done — moved to a separate commit.").
- For pushback: leave as-is for the user to handle, or draft a reply explaining why the current code is correct.
- Batch replies using GraphQL mutations (max ~4 per request to avoid 502):
```bash
gh api graphql -f query='mutation {
  t1: addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: "<ID>", body: "Done."}) { comment { id } }
  t2: addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: "<ID>", body: "Addressed."}) { comment { id } }
}'
```

### Resolving Review Threads
After replying, resolve threads that are fully addressed:
```bash
gh api graphql -f query='mutation {
  t1: resolveReviewThread(input: {threadId: "<THREAD_ID>"}) { thread { id } }
  t2: resolveReviewThread(input: {threadId: "<THREAD_ID>"}) { thread { id } }
}'
```
**Important:** If a GraphQL mutation returns 502, some operations may have succeeded. Always re-fetch thread state before retrying to avoid duplicate replies. If duplicates occur, delete them:
```bash
gh api graphql -f query='mutation { deletePullRequestReviewComment(input: {id: "<COMMENT_ID>"}) { pullRequestReviewComment { id } } }'
```

### Managing Labels
- Remove `conflicts` after rebasing: `gh pr edit <number> --remove-label conflicts`
- Add/remove other labels as appropriate: `gh pr edit <number> --add-label <name>`

### PR Cover Letter Review
- Review the title and body against the current commit series.
- Verify the body follows the format defined in "PR Cover Letter" above: Problem → Changes → Issue reference → Backport decision.
- Update if the commit series has materially changed (new commits added/removed, major restructuring). Minor code-level tweaks don't require body updates.

### Push Summary Comment
After pushing changes that address review comments, post a summary comment on the PR listing what was changed. Format:
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

### Argus URL format includes the project name in the path (2026-05-07)
The agent constructed the Argus link as `https://argus.scylladb.com/tests/<test_id>`, omitting the project segment.
**Correct approach:** The correct Argus URL format is `https://argus.scylladb.com/tests/scylla-cluster-tests/<test_id>`. Always include the project name (`scylla-cluster-tests`) between `/tests/` and the UUID.

