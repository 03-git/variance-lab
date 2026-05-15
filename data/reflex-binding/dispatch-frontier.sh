#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PROMPT=$(cat "$DIR/prompt.txt")
OUTDIR="$DIR/outputs"
mkdir -p "$OUTDIR"/{claude-rousseau-g,claude-rousseau-u,claude-surface-g,claude-surface-u}

echo "=== Frontier dispatches ==="

# Rousseau governed (from ~/ where CLAUDE.md loads natively)
for i in 1 2 3 4 5; do
    echo "--- Rousseau governed trial $i ---"
    cd /Users/jns
    ~/.local/bin/claude -p "$PROMPT" --output-format text \
        > "$OUTDIR/claude-rousseau-g/trial-$i.txt" 2>/dev/null
    echo "done"
done

# Rousseau ungoverned (from /tmp, no CLAUDE.md)
for i in 1 2 3 4 5; do
    echo "--- Rousseau ungoverned trial $i ---"
    cd /tmp
    /Users/jns/.local/bin/claude -p "$PROMPT" --output-format text \
        > "$OUTDIR/claude-rousseau-u/trial-$i.txt" 2>/dev/null
    echo "done"
done

echo "=== Rousseau frontier complete ==="

# Surface governed
for i in 1 2 3 4 5; do
    echo "--- Surface governed trial $i ---"
    ssh i7surfacepro8 "cd ~ && ~/.local/bin/claude -p '$PROMPT' --output-format text" \
        > "$OUTDIR/claude-surface-g/trial-$i.txt" 2>/dev/null
    echo "done"
done

# Surface ungoverned
for i in 1 2 3 4 5; do
    echo "--- Surface ungoverned trial $i ---"
    ssh i7surfacepro8 "cd /tmp && ~/.local/bin/claude -p '$PROMPT' --output-format text" \
        > "$OUTDIR/claude-surface-u/trial-$i.txt" 2>/dev/null
    echo "done"
done

echo "=== All frontier dispatches complete ==="
