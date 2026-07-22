#!/usr/bin/env python3
"""
Render Copilot IntelliJ agent-session JSON dumps to human-readable Markdown.

Input:  a directory containing per-session subdirs, each with
        repo__com.github.copilot.agent.session.persistence.nitrite.entity.NtAgentSession.json
        repo__...NtAgentTurn.json
        repo__...NtAgentWorkingSetItem.json
Output: one Markdown file per NtAgentSession, named "<YYYY-MM-DD>_<slug>.md",
        written to the requested output directory. Filenames are unique
        (a numeric suffix is appended if two sessions collide).

The plugin stores response content as a nested tree:
    Document.contents = JSON dict {uuid: {type: "Subgraph"|"Value", value: <str>}}
Each Value's `value` is a JSON string {type, data}, where `data` is itself a
JSON string. We walk that tree and render:
    - Markdown  -> plain text
    - Thinking  -> blockquote
    - AgentRound.reply           -> assistant text
    - AgentRound.toolCalls[]     -> "🔧 tool `name` (input) -> result"
    - References                 -> skipped (usually [])
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SESSION_ENTITY = ("repo__com.github.copilot.agent.session.persistence."
                  "nitrite.entity.NtAgentSession.json")
TURN_ENTITY = ("repo__com.github.copilot.agent.session.persistence."
               "nitrite.entity.NtAgentTurn.json")


def load_json(path: Path) -> Any:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def slugify(text: str, max_len: int = 60) -> str:
    text = re.sub(r"[^\w\s-]", "", text or "", flags=re.UNICODE).strip()
    text = re.sub(r"[\s]+", "-", text)
    text = text[:max_len].strip("-_")
    return text or "untitled"


def ts_ms_to_iso(ms: int | None) -> str:
    if not ms:
        return ""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).astimezone().isoformat(timespec="seconds")


def ts_ms_to_date(ms: int | None) -> str:
    if not ms:
        return "unknown-date"
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).astimezone().strftime("%Y-%m-%d")


def try_json(s: Any) -> Any:
    """Return json.loads(s) if s is a JSON string, else s untouched."""
    if not isinstance(s, str):
        return s
    if not s or s[0] not in "{[\"":
        return s
    try:
        return json.loads(s)
    except (json.JSONDecodeError, ValueError):
        return s


def render_tool_call(tc: dict, out: list[str]) -> None:
    name = tc.get("name") or "?"
    tool_input = tc.get("input")
    if isinstance(tool_input, (dict, list)):
        input_str = json.dumps(tool_input, ensure_ascii=False, indent=2)
    else:
        input_str = str(tool_input) if tool_input is not None else ""

    out.append(f"**🔧 tool: `{name}`**")
    if input_str:
        out.append("")
        out.append("Input:")
        out.append("```json")
        out.append(input_str)
        out.append("```")

    results = tc.get("result") or []
    if isinstance(results, list):
        pieces: list[str] = []
        for r in results:
            if isinstance(r, dict):
                v = r.get("value") or r.get("text") or r.get("content")
                if v is not None:
                    pieces.append(str(v))
            else:
                pieces.append(str(r))
        if pieces:
            out.append("")
            out.append("Result:")
            out.append("```")
            out.append("\n".join(pieces).rstrip())
            out.append("```")
    out.append("")


def render_value_node(inner: dict, out: list[str]) -> None:
    """Render one {type, data} value node."""
    itype = inner.get("type")
    data = try_json(inner.get("data"))

    if itype == "Markdown":
        if isinstance(data, dict):
            text = data.get("text") or ""
        else:
            text = str(data or "")
        if text:
            out.append(text.rstrip())
            out.append("")
    elif itype == "Thinking":
        content = data.get("content") if isinstance(data, dict) else str(data or "")
        title = data.get("title") if isinstance(data, dict) else None
        if content:
            hdr = f"> _💭 thinking_"
            if title:
                hdr += f" — _{title}_"
            out.append(hdr)
            for line in str(content).splitlines() or [""]:
                out.append(f"> {line}")
            out.append("")
    elif itype == "AgentRound":
        if not isinstance(data, dict):
            return
        reply = (data.get("reply") or "").rstrip()
        if reply:
            out.append(reply)
            out.append("")
        for tc in data.get("toolCalls") or []:
            render_tool_call(tc, out)
    elif itype == "References":
        # data is typically []; skip when empty
        if data and data != []:
            out.append(f"_(references: {json.dumps(data, ensure_ascii=False)[:200]})_")
            out.append("")
    elif itype == "FixedContextPanel":
        # Not conversational; skip.
        return
    else:
        # Unknown but preserve for archival value.
        payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)[:400]
        out.append(f"_({itype}: {payload})_")
        out.append("")


def walk_contents(node: Any, out: list[str]) -> None:
    """Contents is a dict {uuid: {type: 'Subgraph'|'Value', value: str}}. Order preserved."""
    if not isinstance(node, dict):
        return
    for _uuid, entry in node.items():
        if not isinstance(entry, dict):
            continue
        etype = entry.get("type")
        raw = entry.get("value")
        if etype == "Subgraph":
            walk_contents(try_json(raw), out)
        elif etype == "Value":
            inner = try_json(raw)
            if isinstance(inner, dict):
                render_value_node(inner, out)


def extract_user_text(turn: dict) -> str:
    text = (turn.get("request.stringContent") or "").strip()
    if text:
        return text
    contents = try_json(turn.get("request.contents"))
    if isinstance(contents, dict):
        for _u, entry in contents.items():
            if not isinstance(entry, dict) or entry.get("type") != "Value":
                continue
            inner = try_json(entry.get("value"))
            if isinstance(inner, dict) and inner.get("type") == "Markdown":
                data = try_json(inner.get("data"))
                if isinstance(data, dict):
                    t = data.get("text")
                    if t:
                        return t
    return ""


def render_session(session: dict, turns: list[dict], out_dir: Path) -> Path:
    sid = session.get("id") or "unknown-id"
    title = session.get("name.value") or "untitled"
    created = session.get("createdAt")
    modified = session.get("modifiedAt")
    date = ts_ms_to_date(created)

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"- **Session id:** `{sid}`")
    lines.append(f"- **Conversation id:** `{session.get('conversationId', '')}`")
    lines.append(f"- **Created:** {ts_ms_to_iso(created)}")
    lines.append(f"- **Last active:** {ts_ms_to_iso(modified)}")
    lines.append(f"- **Model:** {session.get('modelName') or session.get('modelIdType') or ''}")
    lines.append(f"- **Mode:** {session.get('modeId') or ''}  |  **Chat type:** {session.get('chatType') or ''}")
    lines.append(f"- **User:** {session.get('user', '')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Sort turns by createdAt so the transcript is chronological.
    turns_sorted = sorted(turns, key=lambda t: t.get("createdAt") or 0)
    if not turns_sorted:
        lines.append("_(no turns recorded)_")
    for i, turn in enumerate(turns_sorted, 1):
        ts = ts_ms_to_iso(turn.get("createdAt"))
        lines.append(f"## Turn {i} — {ts}")
        lines.append("")

        user = extract_user_text(turn)
        lines.append("### 👤 User")
        lines.append("")
        if user:
            lines.append(user.rstrip())
        else:
            lines.append("_(no user text captured)_")
        lines.append("")

        lines.append("### 🤖 Assistant")
        lines.append("")
        response_text = (turn.get("response.stringContent") or "").strip()
        if response_text:
            lines.append(response_text)
            lines.append("")
        contents = try_json(turn.get("response.contents"))
        if isinstance(contents, dict):
            walk_contents(contents, lines)
        elif not response_text:
            lines.append("_(no assistant content captured)_")
            lines.append("")

        lines.append("---")
        lines.append("")

    base = f"{date}_{slugify(title)}_{sid[:8]}"
    out_path = out_dir / f"{base}.md"
    n = 1
    while out_path.exists():
        n += 1
        out_path = out_dir / f"{base}_{n}.md"
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return out_path


def process_dump_dir(dump_dir: Path) -> tuple[list[dict], list[dict]]:
    return load_json(dump_dir / SESSION_ENTITY), load_json(dump_dir / TURN_ENTITY)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: render_markdown.py <dumps-root> <out-dir>", file=sys.stderr)
        return 2
    dumps_root = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Pool everything across dumps: turns and sessions can be split across DBs.
    all_sessions: dict[str, dict] = {}
    all_turns: list[dict] = []
    for dump_dir in sorted(p for p in dumps_root.iterdir() if p.is_dir()):
        sessions, turns = process_dump_dir(dump_dir)
        for s in sessions:
            sid = s.get("id")
            if sid and sid not in all_sessions:
                all_sessions[sid] = s
        all_turns.extend(turns)

    by_session: dict[str, list[dict]] = {}
    for t in all_turns:
        by_session.setdefault(t.get("sessionId", ""), []).append(t)

    # Also emit stub sessions for turn.sessionId values with no session record
    # (shouldn't happen often but ensures no turn is lost).
    for orphan_sid in set(by_session) - set(all_sessions):
        if orphan_sid:
            all_sessions[orphan_sid] = {"id": orphan_sid, "name.value": "orphaned-turns"}

    written: list[Path] = []
    empty: list[str] = []
    for sid, s in all_sessions.items():
        turns = by_session.get(sid, [])
        if not turns:
            empty.append(f"{sid}  {s.get('name.value','')}")
            continue
        try:
            p = render_session(s, turns, out_dir)
            written.append(p)
        except Exception as exc:  # noqa: BLE001
            print(f"WARN {sid}: {exc}", file=sys.stderr)

    print(f"\nWrote {len(written)} markdown files.")
    if empty:
        (out_dir / "_sessions-without-turns.txt").write_text(
            "\n".join(sorted(empty)) + "\n", encoding="utf-8"
        )
        print(f"Skipped {len(empty)} sessions with no turns "
              f"(see {out_dir}/_sessions-without-turns.txt).")
    return 0


if __name__ == "__main__":
    sys.exit(main())


