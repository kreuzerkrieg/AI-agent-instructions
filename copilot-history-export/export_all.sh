#!/usr/bin/env bash
# Dump every Copilot IntelliJ Nitrite session DB to JSON, then render Markdown.
#
# Read-only wrt source: DumpNitrite always copies each DB to /tmp before
# opening (H2 MVStore can do recovery writes even with readOnly=true).
#
# Usage:
#   ./export_all.sh [OUT_DIR]                 # default OUT_DIR=~/ai-history-archive/copilot-clion
#   PLUGIN_LIB=/path/to/lib ./export_all.sh   # override plugin lib dir
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$HOME/ai-history-archive/copilot-clion}

# Auto-discover the newest github-copilot-intellij plugin lib/ directory across
# every JetBrains IDE profile (CLion, IDEA, Rider, PyCharm, ...).
if [[ -z "${PLUGIN_LIB:-}" ]]; then
    PLUGIN_LIB=$(ls -td "$HOME"/.local/share/JetBrains/*/github-copilot-intellij/lib 2>/dev/null | head -1 || true)
fi
if [[ -z "$PLUGIN_LIB" || ! -d "$PLUGIN_LIB" ]]; then
    echo "error: could not find github-copilot-intellij plugin lib dir." >&2
    echo "       set PLUGIN_LIB=/path/to/JetBrains/<IDE>/github-copilot-intellij/lib" >&2
    exit 1
fi
echo "Using plugin lib: $PLUGIN_LIB"

DUMPS=$HERE/dumps
mkdir -p "$DUMPS" "$OUT"

# Compile the Java extractor if needed / outdated.
if [[ ! -f "$HERE/DumpNitrite.class" || "$HERE/DumpNitrite.java" -nt "$HERE/DumpNitrite.class" ]]; then
    echo "Compiling DumpNitrite.java..."
    javac -cp "$PLUGIN_LIB/*" -d "$HERE" "$HERE/DumpNitrite.java"
fi

# Enumerate every Nitrite DB across every IDE variant (cl/, rd/, id/, py/, ...)
# that holds agent-mode or background-agent transcripts.
mapfile -t DBS < <(
    find "$HOME/.config/github-copilot" -type f -name '*.db' 2>/dev/null \
    | grep -E '/(chat-agent-sessions|bg-agent-sessions)/'
)

echo "Found ${#DBS[@]} Nitrite DB(s)."

for DB in "${DBS[@]}"; do
    SID=$(basename "$(dirname "$DB")")
    STEM=$(basename "$DB" .db)
    TARGET="$DUMPS/${SID}__${STEM}"
    mkdir -p "$TARGET"
    echo "== $DB -> $TARGET"
    java -cp "$HERE:$PLUGIN_LIB/*" DumpNitrite "$DB" "$TARGET" 2>&1 | grep -v '^SLF4J' || true
done

echo
echo "== Rendering Markdown into: $OUT"
python3 "$HERE/render_markdown.py" "$DUMPS" "$OUT"
echo "Done."

# Optional secret scan.
if command -v gitleaks >/dev/null 2>&1 && [[ -f "$HOME/.gitleaks.toml" ]]; then
    echo
    echo "== Scanning archive with gitleaks..."
    gitleaks dir "$OUT" --config "$HOME/.gitleaks.toml" \
        --report-format json --report-path "$OUT/_secrets-scan.json" \
        --no-banner 2>&1 | tail -3 || true
    echo "Findings written to $OUT/_secrets-scan.json"
fi

