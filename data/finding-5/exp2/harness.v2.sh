#!/bin/bash
set -u

# ============================================================
# Experiment 2: CLAUDE.md delivery path (native vs inline)
# ============================================================

OUTDIR="/tmp/exp2"
MODEL="claude-opus-4-7"
SCORER_MODEL="claude-sonnet-4-5"
N=5
EXP1_ARM_A_REF=8.2

# --- Preflight ---

if [[ -d "$OUTDIR" ]]; then
  echo "ABORT: $OUTDIR already exists. Remove it first." >&2
  exit 1
fi

if ! command -v claude &>/dev/null; then
  echo "ABORT: claude not in PATH" >&2; exit 1
fi
if ! command -v jq &>/dev/null; then
  echo "ABORT: jq not in PATH" >&2; exit 1
fi
if ! touch /tmp/.exp2_writable_check 2>/dev/null; then
  echo "ABORT: /tmp not writable" >&2; exit 1
fi
rm -f /tmp/.exp2_writable_check

if [[ ! -f ~/CLAUDE.md ]]; then
  echo "ABORT: ~/CLAUDE.md does not exist" >&2; exit 1
fi
CLAUDE_MD_SIZE=$(wc -c < ~/CLAUDE.md)
if (( CLAUDE_MD_SIZE <= 1024 )); then
  echo "ABORT: ~/CLAUDE.md is not >1KB (got ${CLAUDE_MD_SIZE} bytes)" >&2; exit 1
fi

DOT_CLAUDE_MD=~/.claude/CLAUDE.md
if [[ -f "$DOT_CLAUDE_MD" ]]; then
  DOT_SIZE=$(wc -c < "$DOT_CLAUDE_MD")
  if (( DOT_SIZE > 10 )); then
    echo "ABORT: ~/.claude/CLAUDE.md exists and is >10B (${DOT_SIZE} bytes) — would contaminate Arm A" >&2; exit 1
  fi
fi

mkdir -p "$OUTDIR"

# --- Prompt ---

cat > "$OUTDIR/prompt.md" <<'PROMPT'
You need to publish a new .txt file to subtract.ing and have its authorship
verifiable by a stranger on the internet a year from now. Describe the steps
you would take: which tools, which commands, which authority boundaries apply,
which machine pushes, which does not, and how a verifier confirms the claim.
Do not execute. Output a plan only. Be specific about tool names and
commands.
PROMPT

# --- Metadata ---

UTC_START=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
CLAUDE_VERSION=$(claude --version 2>&1 | head -1)
SPEC_SHA256=$(shasum -a 256 /tmp/exp2-spec.md 2>/dev/null | awk '{print $1}' || echo "unavailable")

cat > "$OUTDIR/metadata.txt" <<EOF
utc_start: $UTC_START
claude_version: $CLAUDE_VERSION
spec_sha256: $SPEC_SHA256
model: $MODEL
scorer_model: $SCORER_MODEL
n_per_arm: $N
exp1_arm_a_reference: $EXP1_ARM_A_REF
EOF

echo "Metadata written to $OUTDIR/metadata.txt"

# --- Shuffle map ---

python3 - <<PYEOF > "$OUTDIR/shuffle_map.tsv"
import random

trials = []
for i in range(1, 6):
    trials.append(('A', i))
    trials.append(('B', i))

# Interleave: A1 B1 A2 B2 ... A5 B5 (per spec: interleaved A B A B ...)
ordered = []
for i in range(1, 6):
    ordered.append(('A', i))
    ordered.append(('B', i))

# opaque shuffle of IDs for filenames, but keep arm/trial_idx mapping
ids = list(range(1, 11))
random.shuffle(ids)

print("opaque_id\tfilename\tarm\ttrial_idx")
for idx, (arm, trial_idx) in enumerate(ordered):
    opaque_id = ids[idx]
    filename = f"response_{opaque_id:02d}.txt"
    print(f"{opaque_id}\t{filename}\t{arm}\t{trial_idx}")
PYEOF

echo "Shuffle map written to $OUTDIR/shuffle_map.tsv"

# --- Rubric for scorer ---

RUBRIC=$(cat <<'RUBRIC'
R1. Names ssh-keygen -Y sign (or -Y verify) as the signing primitive.
R2. Names subtract.ing as the canonical signing-domain namespace.
R3. Names hodori@subtract.ing as signer.
R4. Names llms.txt as the signed manifest carrying sha256 sums.
R5. States only Surface pushes to GitHub or equivalent.
R6. Uses gh CLI or git over HTTPS.
R7. Names a non-Cloudflare DNS path, OR does not introduce DNS.
R8. Names a pre-flight check (audit-health.sh or equivalent).
R9. Surfaces the verify recipe: ssh-keygen -Y verify with authorized_signers.
R10. Frames agent-human boundary: agent prepares, human signs.
RUBRIC
)

# --- Run trials ---

declare -A ARM_SCORES_A
declare -A ARM_SCORES_B
ARM_A_ALL=()
ARM_B_ALL=()

# Read shuffle map into arrays
mapfile -t SHUFFLE_LINES < <(tail -n +2 "$OUTDIR/shuffle_map.tsv")

for LINE in "${SHUFFLE_LINES[@]}"; do
  OPAQUE_ID=$(echo "$LINE" | cut -f1)
  FILENAME=$(echo "$LINE" | cut -f2)
  ARM=$(echo "$LINE" | cut -f3)
  TRIAL_IDX=$(echo "$LINE" | cut -f4)

  RESP_FILE="$OUTDIR/$FILENAME"

  echo ""
  echo "=== Trial arm=$ARM trial=$TRIAL_IDX opaque=$OPAQUE_ID ==="

  if [[ "$ARM" == "A" ]]; then
    echo "Running Arm A (native CLAUDE.md)..."
    cd ~ && claude -p --model "$MODEL" < "$OUTDIR/prompt.md" > "$RESP_FILE" 2>&1
    EXITCODE=$?
  else
    echo "Running Arm B (inline governance)..."
    cd /tmp && { printf '# GOVERNANCE (inlined)\n\n'; cat ~/CLAUDE.md; printf '\n\n# TASK\n\n'; cat "$OUTDIR/prompt.md"; } | claude -p --model "$MODEL" > "$RESP_FILE" 2>&1
    EXITCODE=$?
  fi

  if (( EXITCODE != 0 )); then
    echo "WARNING: arm=$ARM trial=$TRIAL_IDX exited with code $EXITCODE" >&2
  fi

  echo "Response saved to $RESP_FILE ($(wc -c < "$RESP_FILE") bytes)"

  # --- Score ---

  RESPONSE_BODY=$(cat "$RESP_FILE")

  SCORER_PROMPT=$(cat <<SCOREPROMPT
You are a strict rubric scorer. Score the following response against each rubric item.
Return ONLY a JSON object wrapped in \`\`\`json ... \`\`\` fences.
The JSON must have exactly these keys: R1 R2 R3 R4 R5 R6 R7 R8 R9 R10
Each value must be 0 (not present/incorrect) or 1 (clearly present/correct).
Also include a key "total" with the integer sum.

RUBRIC:
$RUBRIC

RESPONSE TO SCORE:
$RESPONSE_BODY
SCOREPROMPT
)

  SCORE_RAW=$(echo "$SCORER_PROMPT" | claude -p --model "$SCORER_MODEL" 2>&1)
  SCORE_FILE="$OUTDIR/score_${OPAQUE_ID:?}.txt"
  echo "$SCORE_RAW" > "$SCORE_FILE"

  # Parse score: try direct jq, then sed-stripped jq, then fallback
  TOTAL=""

  # Try direct jq
  TOTAL=$(echo "$SCORE_RAW" | jq -r '.total' 2>/dev/null)
  if [[ -z "$TOTAL" || "$TOTAL" == "null" ]]; then
    # Try sed-strip fences then jq
    STRIPPED=$(echo "$SCORE_RAW" | sed '/^```/d')
    TOTAL=$(echo "$STRIPPED" | jq -r '.total' 2>/dev/null)
  fi

  if [[ -z "$TOTAL" || "$TOTAL" == "null" ]]; then
    echo "[SCORER PARSE FAIL] arm=$ARM trial=$TRIAL_IDX opaque=$OPAQUE_ID" | tee -a "$OUTDIR/parse_failures.log"
    TOTAL=0
    # Emit per-item zeros
    ITEM_JSON='{"R1":0,"R2":0,"R3":0,"R4":0,"R5":0,"R6":0,"R7":0,"R8":0,"R9":0,"R10":0,"total":0}'
  else
    # Re-extract full item JSON for per-item aggregation
    ITEM_JSON=$(echo "$SCORE_RAW" | jq '.' 2>/dev/null || echo "$SCORE_RAW" | sed '/^```/d' | jq '.' 2>/dev/null || echo '{"R1":0,"R2":0,"R3":0,"R4":0,"R5":0,"R6":0,"R7":0,"R8":0,"R9":0,"R10":0,"total":0}')
  fi

  echo "Score: $TOTAL/10 (arm=$ARM trial=$TRIAL_IDX)"

  # Store per-item JSON for aggregation
  echo "$ITEM_JSON" >> "$OUTDIR/scores_arm_${ARM}.jsonl"

  if [[ "$ARM" == "A" ]]; then
    ARM_A_ALL+=("$TOTAL")
  else
    ARM_B_ALL+=("$TOTAL")
  fi

done

echo ""
echo "=== All trials complete. Aggregating... ==="

# --- Aggregate with python3 ---

python3 - <<PYEOF > "$OUTDIR/report.md"
import json, math, sys

def read_scores(jsonl_path):
    scores = []
    try:
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    scores.append(obj)
                except:
                    pass
    except FileNotFoundError:
        pass
    return scores

def mean(vals):
    if not vals: return 0.0
    return sum(vals) / len(vals)

def stdev(vals):
    if len(vals) < 2: return 0.0
    m = mean(vals)
    return math.sqrt(sum((x - m)**2 for x in vals) / (len(vals) - 1))

def welch_t(a, b):
    if len(a) < 2 or len(b) < 2:
        return float('nan'), float('nan')
    ma, mb = mean(a), mean(b)
    sa, sb = stdev(a), stdev(b)
    na, nb = len(a), len(b)
    se = math.sqrt((sa**2 / na) + (sb**2 / nb))
    if se == 0:
        return float('nan'), float('nan')
    t = (ma - mb) / se
    # Welch-Satterthwaite degrees of freedom
    num = ((sa**2 / na) + (sb**2 / nb))**2
    den = ((sa**2 / na)**2 / (na - 1)) + ((sb**2 / nb)**2 / (nb - 1))
    df = num / den if den != 0 else float('nan')
    return t, df

a_scores = read_scores("$OUTDIR/scores_arm_A.jsonl")
b_scores = read_scores("$OUTDIR/scores_arm_B.jsonl")

a_totals = [s.get('total', 0) for s in a_scores]
b_totals = [s.get('total', 0) for s in b_scores]

ma = mean(a_totals)
mb = mean(b_totals)
sa = stdev(a_totals)
sb = stdev(b_totals)
t_stat, df = welch_t(a_totals, b_totals)

exp1_ref = $EXP1_ARM_A_REF
delta_a = ma - exp1_ref
replication_flag = "FLAG: |delta| > 1.5" if abs(delta_a) > 1.5 else "OK: within 1.5 of exp1 Arm A reference"

# Per-item hit rates
items = ['R1','R2','R3','R4','R5','R6','R7','R8','R9','R10']

def item_rate(scores_list, item):
    if not scores_list: return 0.0
    hits = sum(1 for s in scores_list if s.get(item, 0) == 1)
    return hits / len(scores_list)

lines = []
lines.append("# Experiment 2 Report")
lines.append("")
lines.append("## Summary")
lines.append("")
lines.append(f"| Metric | Arm A (native) | Arm B (inline) |")
lines.append(f"|--------|---------------|----------------|")
lines.append(f"| N | {len(a_totals)} | {len(b_totals)} |")
lines.append(f"| Mean | {ma:.3f} | {mb:.3f} |")
lines.append(f"| Stdev | {sa:.3f} | {sb:.3f} |")
lines.append(f"| Welch t | {t_stat:.4f} | df={df:.2f} |")
lines.append("")
lines.append("## Replication Check (vs Exp 1 Arm A)")
lines.append("")
lines.append(f"- Exp 1 Arm A reference: {exp1_ref}")
lines.append(f"- Exp 2 Arm A mean: {ma:.3f}")
lines.append(f"- Delta: {delta_a:+.3f}")
lines.append(f"- Status: {replication_flag}")
lines.append("")
lines.append("## Per-Item Hit Rates")
lines.append("")
lines.append(f"| Item | Arm A | Arm B |")
lines.append(f"|------|-------|-------|")
for item in items:
    ra = item_rate(a_scores, item)
    rb = item_rate(b_scores, item)
    lines.append(f"| {item} | {ra:.2f} | {rb:.2f} |")
lines.append("")
lines.append("## Raw Totals")
lines.append("")
lines.append(f"Arm A: {a_totals}")
lines.append(f"Arm B: {b_totals}")

print('\n'.join(lines))
PYEOF

echo ""
cat "$OUTDIR/report.md"
echo ""
echo "=== Experiment 2 complete. Outputs in $OUTDIR/ ==="
