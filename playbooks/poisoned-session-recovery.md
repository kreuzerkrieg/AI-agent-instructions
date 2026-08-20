<!-- Playbook. Not loaded at session start. Load it when the trigger in the
     Playbooks table of global-agents.instructions.md fires. -->

# Playbook: Recover a Poisoned Claude Code Session

Load when a Claude Code session fails **every** turn within one or two seconds with

```
API Error: 400 Tool reference '<name>' not found in available tools
```

The session is not overloaded and not out of context. It is poisoned, and it can never be sent
again without an edit to its transcript on disk.

---

## Why it happens

When the model runs a server-side tool search, the transcript gains a `server_tool_use` block and
a `tool_search_tool_result` block. The result block holds a `tool_references` snapshot of the tool
roster at that instant. The API re-validates every pinned name against the *current* `tools`
payload on every later request. Once any pinned name stops being sent — an MCP server disconnects,
or the harness renames a tool — the whole session is unsendable. Retrying, `/compact`, and forking
all replay the same block.

Two renames have caused this so far: `tool_search_tool_regex` became `ToolSearch`, and the
`headroom` plugin's `headroom_retrieve` went away with the plugin.

## Diagnose

Transcripts live at `~/.claude/projects/<encoded-cwd>/<uuid>.jsonl`, one JSON object per line.
The failing turns are `assistant` entries with `"model":"<synthetic>"`, and the session title is
the last `ai-title` entry's `aiTitle` field. Confirm the cause by block type, never by grepping
for the tool name — the string also appears in ordinary prose and in the harmless
`usage.server_tool_use` accounting field:

```bash
 bin/unpoison-session ~/.claude/projects/<encoded-cwd>/<uuid>.jsonl        # dry run
```

The dry run prints each entry it would drop, the pinned names, and whether the `parentUuid` chain
survives. It writes nothing.

Distinguish this failure from a 529 (the server shedding load) and from `400 prompt is too long`
(the real context wall). Both of those vary between attempts; a poisoned session fails identically
every time.

## Fix

```bash
 bin/unpoison-session <transcript.jsonl> --apply
```

The script drops every entry holding a `server_tool_use` or `tool_search_tool_result` block and
reparents each dropped entry's children onto the nearest surviving ancestor, so the `parentUuid`
chain stays whole. It refuses to write if any parent would dangle, and it keeps a
`<transcript>.poisoned.bak` beside the original. Each offending block sits on its own entry with
no text or thinking beside it, so nothing readable is lost.

Sweep every transcript, not only the one that failed. A rename kills every session that pinned the
old name, and the rest stay silent until the day you resume one:

```bash
 cd ~/.claude/projects
 for f in */*.jsonl; do ~/.config/github-copilot/intellij/bin/unpoison-session "$f" --apply; done
```

## After the fix

A running instance keeps its history in memory, so it goes on failing until it restarts. Exit that
session and reopen it with `claude --resume`. Do not edit the transcript of the session you are
working in — skip it in any sweep.

The transcript is append-only and Claude Code does not hold the file open between turns, so the
edit is safe even while the session is live. The restart is what makes it take effect.

## Traps

- **Every project directory name here starts with `-`.** The encoded cwd is `-home-ernest-...`, so
  a relative path from `~/.claude/projects` reaches a command as options: `grep`, `wc`, `head` and
  `stat` all reject `-home-.../x.jsonl`, grep with the misleading `invalid max count` (it read
  `-h -o -m e-...`). Write `./"$f"`, pass `--` before the path, or use absolute paths. A sweep loop
  that gates on such a command's exit status skips every file and reports success — always assert
  the loop's counters against the number of files you expected to touch.
- **Do not gate on the string.** `grep -c tool_search_tool_regex` counts prose mentions and the
  `usage.server_tool_use` accounting field. Only the block type proves poison.

Worked examples: `2ea3d876` ("S3 SlowDown Test Part 2") died on 2026-08-16, 15 s after six
searches pinned a 17-name snapshot. `b5979bae` ("Load weekly report instructions") died on
2026-08-20; the sweep that followed found 31 more transcripts pinning `tool_search_tool_regex`,
every one of them dead on resume.
