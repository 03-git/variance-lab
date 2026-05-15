#!/bin/bash
set -euo pipefail
# dispatch-v2.sh — manifest-agents experiment, corrected design
# Arm M: curated manifest as routing table → targeted chunks from matched files
# Arm R: BM25 top-12 chunks (unchanged)
# Both arms use qwen2.5-7b, same prompt template, same chunk budget

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$HOME/subtract.ing"
OUTDIR="/tmp/manifest-agents-v2"
QWEN_URL="http://localhost:8086/v1/chat/completions"
DB="/tmp/manifest-agents/rag.db"
QUESTIONS="$SCRIPT_DIR/questions.tsv"
MANIFEST="/tmp/manifest-agents/curated-manifest.tsv"
CHUNK_LINES=40
MAX_CHUNKS=12

mkdir -p "$OUTDIR/arm-m" "$OUTDIR/arm-r" "$OUTDIR/prompts"

# --- preflight ---
echo "=== Preflight ==="
curl -sf "http://localhost:8086/health" >/dev/null || { echo "FAIL: qwen not running"; exit 1; }
[ -f "$QUESTIONS" ] || { echo "FAIL: questions.tsv not found"; exit 1; }
[ -f "$MANIFEST" ] || { echo "FAIL: curated manifest not found"; exit 1; }
[ -f "$DB" ] || { echo "FAIL: rag.db not found — run rag-index.sh first"; exit 1; }
echo "qwen2.5-7b: ok"
date -u > "$OUTDIR/metadata.txt"
echo "repo: $REPO" >> "$OUTDIR/metadata.txt"
echo "model: qwen2.5-7b-q4 @ localhost:8086 ctx=16384" >> "$OUTDIR/metadata.txt"
echo "manifest: curated (frontier-generated, lookdown-style)" >> "$OUTDIR/metadata.txt"

# --- Arm M: manifest-routed chunk retrieval ---
arm_m_context() {
  local question="$1"
  local out="$2"

  # start with the manifest (37 lines, tiny)
  {
    echo "## Manifest (signed routing table)"
    echo "# path	[tag]	description"
    cat "$MANIFEST"
    echo ""
  } > "$out"

  # keyword extraction
  local keywords
  keywords=$(echo "$question" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '\n' | sort -u | \
    grep -v -E '^(what|which|how|does|the|and|are|for|from|that|this|with|each|one|all|its|has|was|is|in|of|to|do|a|an|it|be|list|every|file|files|describe|between)$' || true)

  # match keywords against manifest DESCRIPTIONS (not file contents)
  local tmpmatches
  tmpmatches=$(mktemp)
  for kw in $keywords; do
    grep -i "$kw" "$MANIFEST" 2>/dev/null | cut -f1 >> "$tmpmatches" || true
  done

  # also match against tags
  for kw in $keywords; do
    grep -i "\[$kw\]" "$MANIFEST" 2>/dev/null | cut -f1 >> "$tmpmatches" || true
  done

  local ranked
  ranked=$(sort "$tmpmatches" | uniq -c | sort -rn | head -6 | awk '{print $2}')
  rm -f "$tmpmatches"

  # read CHUNKS from matched files (not full files)
  local chunks_used=0
  for f in $ranked; do
    local fpath="$REPO/${f#./}"
    [ -f "$fpath" ] || continue
    local flines
    flines=$(wc -l < "$fpath" | tr -d ' ')

    # find the most relevant chunk within this file
    local best_start=1
    local best_score=0
    local start=1
    while [ "$start" -le "$flines" ]; do
      local end=$((start + CHUNK_LINES - 1))
      [ "$end" -gt "$flines" ] && end="$flines"
      local score=0
      local chunk_text
      chunk_text=$(sed -n "${start},${end}p" "$fpath")
      for kw in $keywords; do
        local hits
        hits=$(echo "$chunk_text" | grep -ci "$kw" 2>/dev/null || true)
        hits=${hits:-0}
        hits=$(echo "$hits" | tr -d '[:space:]')
        [ -z "$hits" ] && hits=0
        score=$((score + hits))
      done
      if [ "$score" -gt "$best_score" ]; then
        best_score=$score
        best_start=$start
      fi
      start=$((start + CHUNK_LINES))
    done

    local best_end=$((best_start + CHUNK_LINES - 1))
    [ "$best_end" -gt "$flines" ] && best_end="$flines"

    echo "" >> "$out"
    echo "## $f (lines ${best_start}-${best_end} of ${flines})" >> "$out"
    sed -n "${best_start},${best_end}p" "$fpath" >> "$out"

    chunks_used=$((chunks_used + 1))
    [ "$chunks_used" -ge "$MAX_CHUNKS" ] && break

    # if file is small enough, include a second chunk
    if [ "$flines" -gt "$CHUNK_LINES" ] && [ "$chunks_used" -lt "$MAX_CHUNKS" ]; then
      # include first chunk too if best wasn't first
      if [ "$best_start" -gt 1 ]; then
        local sec_end=$CHUNK_LINES
        [ "$sec_end" -gt "$flines" ] && sec_end="$flines"
        echo "" >> "$out"
        echo "## $f (lines 1-${sec_end} of ${flines})" >> "$out"
        sed -n "1,${sec_end}p" "$fpath" >> "$out"
        chunks_used=$((chunks_used + 1))
      fi
    fi
  done
}

# --- Arm R: BM25 chunk retrieval (reuse existing) ---
arm_r_context() {
  local question="$1"
  local out="$2"
  python3 "$SCRIPT_DIR/retrieve.py" "$DB" "$question" "$out" "$MAX_CHUNKS"
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
