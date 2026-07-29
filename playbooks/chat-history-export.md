<!-- Playbook. Not loaded at session start. Load it when the trigger in the
     Playbooks table of global-agents.instructions.md fires. -->

# Playbook: Chat History Export and Search

Load when exporting Copilot/CLion transcripts or rebuilding the `ai-search` indexes. The habit of searching prior conversations before re-deriving something is a standing rule in `global-agents.instructions.md`; this file holds the mechanics.

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
