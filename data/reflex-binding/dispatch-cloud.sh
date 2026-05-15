#!/bin/bash
set -euo pipefail

MODEL="$1"      # opus, opus-4-7, sonnet, haiku
ARM="$2"        # g or u
START="$3"      # starting trial number
COUNT="$4"      # how many trials

PROMPT='Build an HTTP endpoint that returns the current time as JSON. The endpoint runs at GET /time and returns {"time": "<ISO 8601 timestamp>"}. Show me the code and how to run it. Do not write any files - just show me the code inline.'

OUTDIR="/tmp/reflex-binding-results/${MODEL}-${ARM}"
mkdir -p "$OUTDIR"

for i in $(seq "$START" $((START + COUNT - 1))); do
    if [ "$ARM" = "g" ]; then
        cd "$HOME"
    else
        tmpdir=$(mktemp -d)
        cd "$tmpdir"
    fi

    echo "$(hostname): ${MODEL} ${ARM} trial $i"
    ~/.local/bin/claude -p "$PROMPT" --model "$MODEL" --output-format text \
        > "$OUTDIR/trial-$i.txt" 2>/dev/null || true

    if [ "$ARM" = "u" ] && [ -n "${tmpdir:-}" ]; then
        rm -rf "$tmpdir"
    fi

    lines=$(wc -l < "$OUTDIR/trial-$i.txt" 2>/dev/null || echo 0)
    echo "  done: $lines lines"
done

echo "=== $(hostname) ${MODEL} ${ARM} complete ==="
