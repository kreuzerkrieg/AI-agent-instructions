<!-- Playbook. Not loaded at session start. Load it when the trigger in the
     Playbooks table of global-agents.instructions.md fires. -->

# Playbook: Pull Request Workflow

Load when creating a PR, writing or reviewing a cover letter, running `$plan-review` / `$finalize-review`, refining a commit series for review, or replying to and resolving review threads.

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
8. **Do NOT push** — wait for explicit user instruction (canonical no-push rule in *Terminal Command Rules*, `global-agents.instructions.md`).

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
3. **Save the plan to a scratch file** (e.g., `~/.config/JetBrains/CLion<version>/scratches/GitHubCopilot/plan-review-PR<number>.md`) and open it for the user. This is easier to read than inline agent output.
4. **Stop and wait** for the user to approve/reject/modify each item.

The user triggers this phase by saying **`$plan-review`**.

#### Phase 2: Execute — `$finalize-review`
- Apply code changes only for approved items.
- Post replies only for approved items.
- Follow the rules below for amending commits, replying, and resolving threads.
- **Before the user pushes:** remove the `conflicts` label if present: `gh pr edit <number> --remove-label conflicts`
- ❌ **Do NOT push** — wait for explicit user instruction (canonical no-push rule in *Terminal Command Rules*, `global-agents.instructions.md`).

The user triggers this phase by saying **`$finalize-review`**.

**Never make code changes or post replies before the user confirms the plan.**

### Addressing Review Comments (Code Changes)
1. **Analyze each comment** — verify the reviewer's assumptions against actual code before acting (see *Commit Organization → Handling Review Comments* in `global-agents.instructions.md`).
2. **Make code changes** in the working tree.
3. **Amend the correct commit** — use `git commit --fixup=<SHA>` + `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <SHA>~1`.
4. **Separate unrelated fixes** — if a reviewer points out a pre-existing bug or a formatting issue, put the fix in its own commit (not bundled with functional changes).
5. ❌ **Do NOT push** — wait for explicit user instruction (canonical no-push rule in *Terminal Command Rules*, `global-agents.instructions.md`).

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
- Verify the body follows the *PR Cover Letter* format above: Problem → Changes → Issue reference → Backport decision.
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
