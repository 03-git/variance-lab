#!/bin/bash
set -euo pipefail
# manifest-walk.sh — walk subtract.ing repo, output TSV manifest
# Usage: ./manifest-walk.sh /path/to/repo > manifest.tsv
# Output: path<TAB>sha256<TAB>lines<TAB>description

REPO="${1:-.}"

cd "$REPO"

find . -type f \( -name "*.txt" -o -name "*.html" -o -name "*.md" \
  -o -name "*.c" -o -name "*.h" -o -name "*.sh" -o -name "*.tsv" \
  -o -name "*.ts" -o -name "*.conf" \) \
  ! -path "./.git/*" ! -path "*/node_modules/*" \
  ! -name "stb_truetype.h" \
  | sort | while IFS= read -r f; do
    hash=$(shasum -a 256 "$f" | cut -d' ' -f1)
    lines=$(wc -l < "$f" | tr -d ' ')
    # first non-empty, non-comment line as description
    desc=$(grep -m1 -v '^\s*$' "$f" | grep -v '^\s*#\|^\s*//' | head -c 120 || echo "(no description)")
    [ -z "$desc" ] && desc=$(head -1 "$f" | head -c 120)
    printf '%s\t%s\t%s\t%s\n' "$f" "$hash" "$lines" "$desc"
done
