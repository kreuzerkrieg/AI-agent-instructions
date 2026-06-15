# RTK Setup for GitHub Copilot in CLion (JetBrains IDEs)

## What is RTK?

[RTK (Rust Token Killer)](https://github.com/rtk-ai/rtk) is a CLI proxy that filters and compresses command outputs before they reach the LLM context window. It saves 60-90% tokens on verbose commands (git, build systems, test runners) with <10ms overhead per command.

## ⚠️ Read this first — JetBrains specifics

The JetBrains Copilot plugin behaves **differently** from the Copilot CLI and VS Code. Three things that cost a full day of debugging (see microsoft/copilot-intellij-feedback#1653 and rtk-ai/rtk#2443):

1. **Hooks load from the repo only.** The IntelliJ agent registers exactly one source: `<git-repo-root>/.github/hooks/**/*.json`. It is hard-wired (`register("hook", [".github/hooks/**/*.json"])`). The global `~/.copilot/hooks/` location — what `rtk init -g --copilot` creates — is **silently ignored** by the IDE (it only works for the standalone Copilot CLI). The hook file must live in each repo's `.github/hooks/`.
2. **Event names are camelCase.** Use `preToolUse`. The PascalCase `PreToolUse` (VS Code / Claude style) is rejected with a `[HookParser] Invalid event type: PreToolUse` warning in `idea.log`. (rtk's own generated template still writes both keys — the PascalCase one is harmless noise; only `preToolUse` is honored.)
3. **The IDE's terminal tool is `run_in_terminal`, and the host only honors `permissionDecision: "deny"`.** It ignores `modifiedArgs`/`updatedInput`, so transparent rewriting is impossible — rtk must use **deny-with-suggestion** (deny the raw command, suggest the `rtk …` form, the agent retries). Stock rtk ≤ 0.42.2 does **not** recognize `run_in_terminal` and produces no output → looks like the hook "does nothing". See **Patched RTK** below.

## Prerequisites

- CLion (2026.1+) with the GitHub Copilot plugin (agent mode; agent hooks shipped March 2026)
- Rust/Cargo (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
- The project opened in CLion **must be a git repo** (hook path is resolved from the git root)

## Installation

### 1. Install RTK

> **Do not use `cargo install rtk-cli` or `cargo install rtk`** — a different project named "rtk" (Rust Type Kit) squats that name on crates.io. Use one of:

```bash
cargo install --git https://github.com/rtk-ai/rtk      # from source
# or
brew install rtk                                        # macOS/Linuxbrew
# or
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
```

Verify:
```bash
~/.cargo/bin/rtk --version    # expect: rtk 0.42.2 (or newer)
```

### 2. Patched RTK (required until rtk-ai/rtk#2443 is merged)

Stock rtk doesn't recognize the IDE's camelCase `run_in_terminal` tool, so the hook is a no-op. A local patch adds `run_in_terminal` detection + deny-with-suggestion for the JetBrains host:

```bash
git clone https://github.com/rtk-ai/rtk /tmp/rtk && cd /tmp/rtk
# apply the fix from issue #2443 (detect_format + handle_copilot_ide), then:
cargo install --path . --force
```

Confirm the patched binary responds to the IDE payload:
```bash
echo '{"toolName":"run_in_terminal","toolArgs":"{\"command\":\"git status\"}"}' | ~/.cargo/bin/rtk hook copilot
# expect: {"permissionDecision":"deny","permissionDecisionReason":"RTK token optimization: re-run this command as `rtk git status` instead."}
```
Restore the official build later with `cargo install --git https://github.com/rtk-ai/rtk --force`.

### 3. Install the hook at the REPO level

> **Don't blindly run `rtk init --copilot` in a shared repo.** It writes **two** files: `./.github/hooks/rtk-rewrite.json` (fine) **and** `./.github/copilot-instructions.md` — and if that file already exists and is git-tracked (as in scylladb), init will modify it, polluting a shared file you may accidentally commit. Prefer creating the hook file manually (below) and keep rtk guidance in your **user-level** instruction dir (`~/.config/github-copilot/intellij/…`) instead. If you do run init, `git checkout .github/copilot-instructions.md` afterward to drop the injected block.

Create the hook manually. The hook runs via a non-interactive `sh -c`, which does **not** source `~/.bashrc`, so `~/.cargo/bin` is not on `$PATH` — use the full path, camelCase event only:

#### `<repo>/.github/hooks/rtk-rewrite.json`
```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      {
        "type": "command",
        "bash": "/home/ernest.zaslavsky/.cargo/bin/rtk hook copilot",
        "cwd": ".",
        "timeoutSec": 10
      }
    ]
  }
}
```

> Tip: add `.github/hooks/` to the repo's `.gitignore` (or a global gitignore) so this personal hook isn't committed to a shared repo.

### 4. Restart CLion

The agent reads `.github/hooks/` at startup; restart so it picks up changes.

## How it works (JetBrains, deny-with-suggestion)

```
Agent calls run_in_terminal: "git status"
    ↓
preToolUse hook fires → /…/rtk hook copilot   (payload: toolName=run_in_terminal, toolArgs JSON)
    ↓
RTK denies with reason: "re-run this command as `rtk git status` instead"
    ↓
Agent re-issues run_in_terminal: "rtk git status"
    ↓
rtk executes git, filters output → fewer tokens; `rtk gain` records the saving
```

Note: each rewritable command is denied once and retried — inherent to a host that can't transparently rewrite. Already-`rtk`, non-shell (MCP) and non-rewritable commands pass through silently.

## Verifying it works

Quick "did the hook even fire?" probe — drop a debug hook and watch the log:

`<repo>/.github/hooks/debug.json`
```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      {
        "type": "command",
        "bash": "printf '%s %s\\n' \"$(date -Is)\" \"$(cat)\" >> /tmp/copilot-hook-debug.log",
        "cwd": ".",
        "timeoutSec": 10
      }
    ]
  }
}
```
Restart CLion, ask the agent to run a terminal command, then `tail -f /tmp/copilot-hook-debug.log`. To keep the trace *and* run a real hook, wrap it:
```
"bash": "d=$(cat); printf '%s %s\\n' \"$(date -Is)\" \"$d\" >> /tmp/copilot-hook-debug.log; printf '%s' \"$d\" | /home/ernest.zaslavsky/.cargo/bin/rtk hook copilot"
```
(`$(cat)` consumes stdin, logs it, then re-feeds it so the hook protocol is preserved.) Remove the debug hook when done.

Then check savings:
```bash
rtk gain
```
High-savings commands: `git diff` (~60-80%), `ninja`/build output (~70-90%), test runner output (~50-80%). `cat`/short commands save little — normal.

## Troubleshooting

### Hook never fires (no log entry, command runs raw)
- **Wrong location** — the #1 cause. The file must be at `<git-root>/.github/hooks/*.json`. `~/.copilot/hooks/` does nothing in JetBrains. Confirm with the debug hook above.
- Project isn't a git repo (hook path is resolved from the git root).
- IDE wasn't restarted after adding/changing the file.

### Hook fires but nothing is rewritten (`rtk gain` empty)
- Using **stock rtk** — it ignores `run_in_terminal`. Install the patched build (step 2). Verify with the one-liner there.

### `[HookParser] Invalid event type: PreToolUse` in idea.log
- Harmless — that's the PascalCase key. Only `preToolUse` (camelCase) is honored; you can delete the `PreToolUse` block.

### "command not found: rtk"
- The hook's `sh -c` has no `~/.cargo/bin` on PATH. Use the **absolute** path in the `bash` field (as above).

## References
- rtk run_in_terminal / deny-with-suggestion bug + PoC: https://github.com/rtk-ai/rtk/issues/2443
- JetBrains hooks how-to (location, camelCase, debugging): https://github.com/microsoft/copilot-intellij-feedback/issues/1653
