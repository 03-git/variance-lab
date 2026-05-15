#!/bin/bash
set -euo pipefail
# dispatch.sh — run both arms of manifest-agents experiment

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$HOME/subtract.ing"
OUTDIR="/tmp/manifest-agents"
QWEN_URL="http://localhost:8086/v1/chat/completions"
DB="$OUTDIR/rag.db"
QUESTIONS="$SCRIPT_DIR/questions.tsv"
MANIFEST="$OUTDIR/manifest.tsv"
MAX_CONTEXT_LINES=500

mkdir -p "$OUTDIR/arm-m" "$OUTDIR/arm-r" "$OUTDIR/prompts"

# --- preflight ---
echo "=== Preflight ==="
curl -sf "http://localhost:8086/health" >/dev/null || { echo "FAIL: qwen not running"; exit 1; }
[ -f "$QUESTIONS" ] || { echo "FAIL: questions.tsv not found"; exit 1; }
echo "qwen2.5-7b: ok"
date -u > "$OUTDIR/metadata.txt"
echo "repo: $REPO" >> "$OUTDIR/metadata.txt"
echo "model: qwen2.5-7b-q4 @ localhost:8086" >> "$OUTDIR/metadata.txt"

# --- build manifest ---
echo "=== Building manifest ==="
bash "$SCRIPT_DIR/manifest-walk.sh" "$REPO" > "$MANIFEST"
echo "Manifest: $(wc -l < "$MANIFEST" | tr -d ' ') files"

# --- build FTS5 index ---
echo "=== Building RAG index ==="
bash "$SCRIPT_DIR/rag-index.sh" "$REPO" "$DB"

# --- Arm M: build context for a question ---
arm_m_context() {
  local question="$1"
  local out="$2"

  # start with the full manifest
  {
    echo "## File manifest (path, sha256, lines, first_line)"
    echo ""
    cat "$MANIFEST"
    echo ""
  } > "$out"

  # extract keywords from question
  local keywords
  keywords=$(echo "$question" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '\n' | sort -u | \
    grep -v -E '^(what|which|how|does|the|and|are|for|from|that|this|with|each|one|all|its|has|was|is|in|of|to|do|a|an|it|be|list|every|file|files|describe|between)$' || true)

  # search repo files for keyword hits, rank by frequency
  local tmpmatches
  tmpmatches=$(mktemp)
  for kw in $keywords; do
    cd "$REPO" && grep -rl --include="*.txt" --include="*.c" --include="*.h" \
      --include="*.sh" --include="*.html" --include="*.tsv" --include="*.ts" \
      -il "$kw" . 2>/dev/null >> "$tmpmatches" || true
  done

  local ranked
  ranked=$(sort "$tmpmatches" | uniq -c | sort -rn | head -5 | awk '{print $2}')
  rm -f "$tmpmatches"

  local total_lines=0
  for f in $ranked; do
    local fpath="$REPO/${f#./}"
    [ -f "$fpath" ] || continue
    local flines
    flines=$(wc -l < "$fpath" | tr -d ' ')
    if [ $((total_lines + flines)) -gt $MAX_CONTEXT_LINES ]; then
      local remaining=$((MAX_CONTEXT_LINES - total_lines))
      if [ "$remaining" -gt 10 ]; then
        echo "" >> "$out"
        echo "## File: $f (truncated to $remaining/$flines lines)" >> "$out"
        echo "" >> "$out"
        head -n "$remaining" "$fpath" >> "$out"
      fi
      break
    fi
    echo "" >> "$out"
    echo "## File: $f ($flines lines)" >> "$out"
    echo "" >> "$out"
    cat "$fpath" >> "$out"
    total_lines=$((total_lines + flines))
  done
}

# --- Arm R: build context for a question ---
arm_r_context() {
  local question="$1"
  local out="$2"
  python3 "$SCRIPT_DIR/retrieve.py" "$DB" "$question" "$out" 12
}

# --- dispatch loop ---
echo "=== Dispatching ==="
echo -e "id\tarm\tquestion\twall_ms\tprompt_tokens\tcompletion_tokens" > "$OUTDIR/metrics.tsv"

SYSPROMPT="You are answering questions about the subtract.ing codebase. Use ONLY the provided context to answer. Be specific — cite file names and quote relevant content."

tail -n +2 "$QUESTIONS" | while IFS=$'\t' read -r qid qtype question; do
  echo "[$(date -u +%H:%M:%S)] $qid ($qtype)"

  # --- Arm M ---
  echo -n "  M..."
  arm_m_context "$question" "$OUTDIR/prompts/${qid}_m_ctx.txt"
  {
    echo "$SYSPROMPT"
    echo ""
    cat "$OUTDIR/prompts/${qid}_m_ctx.txt"
    echo ""
    echo "## Question"
    echo "$question"
  } > "$OUTDIR/prompts/${qid}_m.txt"

  python3 "$SCRIPT_DIR/infer.py" "$QWEN_URL" "$OUTDIR/prompts/${qid}_m.txt" "$OUTDIR/arm-m/${qid}.md" "$OUTDIR/prompts/${qid}_m_met.txt"
  m_met=$(cat "$OUTDIR/prompts/${qid}_m_met.txt")
  echo -e "${qid}\tM\t${question}\t${m_met}" >> "$OUTDIR/metrics.tsv"
  echo " done ($(echo "$m_met" | cut -f1)ms)"

  # --- Arm R ---
  echo -n "  R..."
  arm_r_context "$question" "$OUTDIR/prompts/${qid}_r_ctx.txt"
  {
    echo "$SYSPROMPT"
    echo ""
    cat "$OUTDIR/prompts/${qid}_r_ctx.txt"
    echo ""
    echo "## Question"
    echo "$question"
  } > "$OUTDIR/prompts/${qid}_r.txt"

  python3 "$SCRIPT_DIR/infer.py" "$QWEN_URL" "$OUTDIR/prompts/${qid}_r.txt" "$OUTDIR/arm-r/${qid}.md" "$OUTDIR/prompts/${qid}_r_met.txt"
  r_met=$(cat "$OUTDIR/prompts/${qid}_r_met.txt")
  echo -e "${qid}\tR\t${question}\t${r_met}" >> "$OUTDIR/metrics.tsv"
  echo " done ($(echo "$r_met" | cut -f1)ms)"

done

echo "=== Complete ==="
echo "Outputs: $OUTDIR/arm-{m,r}/"
echo "Metrics: $OUTDIR/metrics.tsv"
