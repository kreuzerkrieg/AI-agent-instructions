# RTK Setup for GitHub Copilot in CLion

## What is RTK?

[RTK (Rust Token Killer)](https://github.com/rtk-ai/rtk) is a CLI proxy that filters and compresses command outputs before they reach the LLM context window. It saves 60-90% tokens on verbose commands (git, build systems, test runners) with <10ms overhead per command.

## Prerequisites

- CLion with GitHub Copilot plugin (nightly build recommended for agent hooks support)
- Rust/Cargo installed (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)

## Installation

### 1. Install RTK

```bash
cargo install rtk-cli
```

Verify:
```bash
~/.cargo/bin/rtk --version
# Expected: rtk 0.42.2 (or newer)
```

### 2. Ensure RTK is in PATH

Add to `~/.bashrc` or `~/.bash_profile`:
```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

Reload: `source ~/.bashrc`

### 3. Initialize RTK hooks

```bash
rtk init -g --copilot
```

This creates `~/.copilot/hooks/rtk-rewrite.json` and `~/.copilot/copilot-instructions.md`.

**If `rtk init -g --copilot` doesn't work** (older RTK version or unsupported flag), create the files manually:

#### `~/.copilot/hooks/rtk-rewrite.json`
```json
{
  "version": 1,
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "rtk hook copilot",
        "cwd": ".",
        "timeout": 5
      }
    ],
    "preToolUse": [
      {
        "type": "command",
        "bash": "rtk hook copilot",
        "cwd": ".",
        "timeoutSec": 5
      }
    ]
  }
}
```

#### `~/.copilot/copilot-instructions.md`
```markdown
<!-- rtk-instructions v2 -->
# RTK — Token-Optimized CLI

**rtk** is a CLI proxy that filters and compresses command outputs, saving 60-90% tokens.

## Rule

Always prefix shell commands with `rtk`:

# Instead of:              Use:
git status                 rtk git status
git log -10                rtk git log -10
ninja build/dev/scylla     rtk ninja build/dev/scylla
./test.py --mode=dev ...   rtk ./test.py --mode=dev ...

## Meta commands (use directly)

rtk gain              # Token savings dashboard
rtk gain --history    # Per-command savings history
rtk discover          # Find missed rtk opportunities
rtk proxy <cmd>       # Run raw (no filtering) but track usage
<!-- /rtk-instructions -->
```

### 4. (Optional) Also set up for Claude Code CLI

If the CLion nightly plugin delegates to Claude Code:

```bash
rtk init --claude-code
```

Or manually add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "rtk hook claude"
          }
        ]
      }
    ]
  }
}
```

And create `~/.claude/RTK.md` with meta-command reference (RTK uses this for self-awareness).

### 5. Restart CLion

The plugin needs to pick up the new hook files on startup.

## How it works

```
Agent issues command: "git status"
    ↓
PreToolUse hook fires → calls "rtk hook copilot"
    ↓
RTK rewrites: "git status" → "rtk git status"
    ↓
rtk executes git, filters output (strips ANSI, deduplicates, compresses)
    ↓
Compressed output returned to agent context (35-90% fewer tokens)
```

## Verifying it works

After restart, ask the agent to run:
```bash
rtk gain
```

You should see tracked commands with savings percentages. High-savings commands:
- `git status` — ~35% savings
- `git diff` — ~60-80% savings
- `ninja` build output — ~70-90% savings
- Test runner output — ~50-80% savings

## Troubleshooting

### "command not found: rtk"
RTK isn't in PATH for the shell the plugin uses. Fix:
- Ensure `~/.bashrc` exports `$HOME/.cargo/bin` in PATH
- Or use absolute paths in hook files: `/home/<user>/.cargo/bin/rtk hook copilot`

### Hook not firing (no automatic rewrite)
- Check that the nightly plugin supports agent hooks (March 2026+)
- Verify hook file exists: `ls ~/.copilot/hooks/rtk-rewrite.json`
- The plugin may use a different hook path — check plugin docs for the correct location
- Fallback: the instruction-based approach (`copilot-instructions.md`) tells the agent to prefix commands manually

### Low savings percentage
- `cat` and short commands won't save much — that's normal
- Savings compound on verbose commands (builds, diffs, test output)
- After a real coding session, expect 40-60% overall savings

## Token savings from this setup session

```
Total commands:    7
Tokens saved:     15 (6.0%)
Best command:     git status — 35.1% savings
```

Low overall because we mostly read small config files. Real development sessions with builds and tests yield much higher savings.

