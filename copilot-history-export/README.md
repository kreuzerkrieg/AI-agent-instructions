# copilot-history-export

Extracts every past GitHub Copilot chat conversation from the JetBrains
(CLion / IDEA / Rider / …) Copilot plugin and renders one Markdown file per
conversation.

## What it reads

The plugin stores agent-mode transcripts in a **Nitrite v4 embedded DB**
(H2 MVStore file format) — **not** in `copilot-intellij.db` (that one is
just plugin UI state).

| Path | Format | What's there |
|---|---|---|
| `~/.config/github-copilot/<ide>/chat-agent-sessions/<sid>/copilot-agent-sessions-nitrite.db` | Nitrite v4 | **Full agent-mode transcripts.** |
| `~/.config/github-copilot/<ide>/bg-agent-sessions/<sid>/*.db` | Nitrite v4 | Background-agent state. |
| `~/.config/github-copilot/<ide>/chat-sessions/<sid>/*.xd` | Xodus (JetBrains binary) | Old "plain chat" mode. Verified to hold metadata only — no transcript prose. |
| `~/.config/github-copilot/<ide>/chat-edit-sessions/<sid>/*.xd` | Xodus | Edit-mode ephemeral state. |
| `~/.config/github-copilot/copilot-intellij.db` | SQLite (single `state` KV table) | Plugin UI state only. |
| `~/.config/github-copilot/{auth.db,oauth.json,apps.json}` | Auth material | Do not export. |

`<ide>` is one of `cl` (CLion), `id` (IDEA), `rd` (Rider), `py` (PyCharm),
etc. The script picks all of them up automatically.

Each Nitrite DB has three object repositories under
`com.github.copilot.agent.session.persistence.nitrite.entity`:
`NtAgentSession`, `NtAgentTurn`, `NtAgentWorkingSetItem`.

## Usage

```bash
cd ~/.config/github-copilot/intellij/copilot-history-export
./export_all.sh                            # writes to ~/ai-history-archive/copilot-clion/
./export_all.sh /path/to/out               # custom output dir
./export_all.sh --full                     # ignore state, re-export everything
PLUGIN_LIB=/path/to/lib ./export_all.sh    # override plugin lib dir
```

The script:
1. Auto-discovers the newest `github-copilot-intellij` plugin `lib/` under
   `~/.local/share/JetBrains/*/`.
2. Compiles `DumpNitrite.java` on first run (or when the source changes).
3. Finds every Nitrite DB under `chat-agent-sessions/` and
   `bg-agent-sessions/`, copies each to `/tmp`, and dumps every collection
   and object-repository to JSON in `dumps/<sid>__<db-stem>/`.
4. Runs `render_markdown.py` to pool sessions + turns across all dumps
   (turns aren't always co-located with their session record) and emits
   one Markdown per session named `YYYY-MM-DD_<title-slug>_<sid8>.md`.
5. If `gitleaks` and `~/.gitleaks.toml` are installed, scans the archive
   and writes `_secrets-scan.json` next to the transcripts.

## Incremental exports

State is tracked in `<OUT>/_export_state.json` with two watermarks:

- `dbs[<absolute-db-path>] = mtime` — DBs whose file mtime hasn't advanced
  are skipped (no Java dump).
- `sessions[<session-id>] = latest_ms` — the max of `session.modifiedAt`
  and every turn's `createdAt` / `response.createdAt`. Sessions whose
  watermark hasn't advanced are skipped (no Markdown re-write).

Markdown filenames are deterministic (`<date>_<slug>_<sid8>.md`), so a
re-render of an existing session overwrites its file in place — no
`_2.md` / `_3.md` accumulation.

Pass `--full` to ignore state and re-export everything.

## Read-only safety

`DumpNitrite` **copies each `.db` to `/tmp` before opening it** — H2
MVStore may perform recovery writes even when `readOnly=true`, so we
never open the originals directly. Nothing in `~/.config/github-copilot/`
is modified.

## Requirements

- JDK 21+ (`java`, `javac`) — the extractor is one plain Java source
  file, no build tool required.
- Python 3.10+ for the renderer.
- `github-copilot-intellij` plugin installed in at least one JetBrains
  IDE (its bundled `lib/*.jar` provides Nitrite, MVStore, and Jackson).
- Optional: `gitleaks` + a `~/.gitleaks.toml` for the secret scan.

## Implementation notes

- `DumpNitrite.java` bypasses Nitrite's `ObjectRepository` API (which
  needs entity classes on the classpath) by calling
  `NitriteStore.openMap(name, NitriteId.class, Document.class)` — this
  returns the raw `NitriteMap` backing each repository so we can iterate
  documents without the plugin's `NtAgent*` classes.
- `render_markdown.py` walks the nested `response.contents` JSON tree:
  `Subgraph → Value → {type: Markdown|Thinking|AgentRound|References,
  data: <json string>}`. Each `AgentRound` contains `reply` and
  `toolCalls[]` with `input`, `result`, `status`, etc.

## Secrets

Transcripts contain the full text of every command you ran and every
tool result you saw — including anything shown on your terminal at the
time. Expect real credentials in there (Jenkins tokens shown in `curl -u`,
AWS STS keys printed by `env`, WARP enrollment JWTs, etc.). **Never
commit the output directory to any git remote without scrubbing.** The
built-in gitleaks scan produces `_secrets-scan.json` as a starting point.

