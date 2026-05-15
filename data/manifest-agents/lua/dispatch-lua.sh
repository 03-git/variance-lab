#!/bin/bash
set -euo pipefail
# dispatch-lua.sh — manifest-agents Lua public corpus test
# Same arms as subtract.ing V2, applied to Lua 5.4 source.
# Uses qwen-7b (via llama.cpp) to match V2 methodology.

CORPUS="/tmp/lua-corpus"
OUTDIR="/tmp/lua-corpus/results"
DB="$CORPUS/rag.db"
QUESTIONS="$CORPUS/questions.tsv"
MANIFEST="$CORPUS/curated-manifest.tsv"
CHUNK_LINES=40
MAX_CHUNKS=12
LLAMA_PORT=8086

mkdir -p "$OUTDIR/arm-m" "$OUTDIR/arm-r" "$OUTDIR/prompts"

echo "=== Lua Corpus Dispatch ==="
[ -f "$QUESTIONS" ] || { echo "FAIL: questions.tsv not found"; exit 1; }
[ -f "$MANIFEST" ] || { echo "FAIL: manifest not found"; exit 1; }
[ -f "$DB" ] || { echo "FAIL: rag.db not found"; exit 1; }

date -u > "$OUTDIR/metadata.txt"
echo "corpus: lua-5.4" >> "$OUTDIR/metadata.txt"
echo "model: qwen2.5-7b (llama.cpp)" >> "$OUTDIR/metadata.txt"
echo "manifest: curated via sonnet-4-6" >> "$OUTDIR/metadata.txt"

# --- Arm M: manifest-routed ---
arm_m_context() {
  local question="$1"
  local out="$2"

  {
    echo "## Manifest (routing table for Lua 5.4 source)"
    echo "# path	[tag]	description"
    cat "$MANIFEST"
    echo ""
  } > "$out"

  local keywords
  keywords=$(echo "$question" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '\n' | sort -u | \
    grep -v -E '^(what|which|how|does|the|and|are|for|from|that|this|with|each|one|all|its|has|was|is|in|of|to|do|a|an|it|be|list|every|file|files|describe|between)$' || true)

  local tmpmatches
  tmpmatches=$(mktemp)
  for kw in $keywords; do
    grep -i "$kw" "$MANIFEST" 2>/dev/null | cut -f1 >> "$tmpmatches" || true
  done

  local ranked
  ranked=$(sort "$tmpmatches" | uniq -c | sort -rn | head -6 | awk '{print $2}')
  rm -f "$tmpmatches"

  local chunks_used=0
  for f in $ranked; do
    local fpath="$CORPUS/$f"
    [ -f "$fpath" ] || continue
    local flines
    flines=$(wc -l < "$fpath" | tr -d ' ')

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

    if [ "$flines" -gt "$CHUNK_LINES" ] && [ "$chunks_used" -lt "$MAX_CHUNKS" ]; then
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

# --- Arm R: BM25 retrieval ---
arm_r_context() {
  local question="$1"
  local out="$2"
  python3 "$CORPUS/retrieve-lua.py" "$DB" "$question" "$out" "$MAX_CHUNKS"
}

# --- infer via llama.cpp qwen-7b ---
infer_qwen() {
  local prompt_file="$1"
  local out_file="$2"
  local met_file="$3"
  python3 "$CORPUS/infer-qwen.py" "$prompt_file" "$out_file" "$met_file"
}

# --- dispatch loop ---
echo "=== Dispatching ==="
echo -e "id\tarm\tquestion\twall_ms\tprompt_tokens\tcompletion_tokens" > "$OUTDIR/metrics.tsv"

SYSPROMPT="You are answering questions about the Lua 5.4 source code. Use ONLY the provided context to answer. Be specific — cite file names, function names, and quote relevant code."

tail -n +2 "$QUESTIONS" | while IFS=$'\t' read -r qid qtype question; do
  echo "[$(date -u +%H:%M:%S)] $qid ($qtype)"

  # --- Arm M ---
  if [ ! -f "$OUTDIR/arm-m/${qid}.md" ]; then
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

    infer_qwen "$OUTDIR/prompts/${qid}_m.txt" "$OUTDIR/arm-m/${qid}.md" "$OUTDIR/prompts/${qid}_m_met.txt"
    m_met=$(cat "$OUTDIR/prompts/${qid}_m_met.txt")
    echo -e "${qid}\tM\t${question}\t${m_met}" >> "$OUTDIR/metrics.tsv"
    echo " done ($(echo "$m_met" | cut -f1)ms)"
  else
    echo "  M... cached"
  fi

  # --- Arm R ---
  if [ ! -f "$OUTDIR/arm-r/${qid}.md" ]; then
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

    infer_qwen "$OUTDIR/prompts/${qid}_r.txt" "$OUTDIR/arm-r/${qid}.md" "$OUTDIR/prompts/${qid}_r_met.txt"
    r_met=$(cat "$OUTDIR/prompts/${qid}_r_met.txt")
    echo -e "${qid}\tR\t${question}\t${r_met}" >> "$OUTDIR/metrics.tsv"
    echo " done ($(echo "$r_met" | cut -f1)ms)"
  else
    echo "  R... cached"
  fi

done

echo "=== Complete ==="
echo "Outputs: $OUTDIR/arm-{m,r}/"
echo "Metrics: $OUTDIR/metrics.tsv"
