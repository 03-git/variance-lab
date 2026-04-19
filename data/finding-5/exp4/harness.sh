#!/bin/bash
set -u

# ── preflight ────────────────────────────────────────────────────────────────

command -v claude >/dev/null 2>&1 || { echo "ABORT: claude not in PATH" >&2; exit 1; }
command -v jq     >/dev/null 2>&1 || { echo "ABORT: jq not in PATH"     >&2; exit 1; }
touch /tmp/.exp4_write_test 2>/dev/null || { echo "ABORT: /tmp not writable" >&2; exit 1; }
rm -f /tmp/.exp4_write_test

if [[ -d /tmp/exp4 || -f /tmp/exp4 ]]; then
  echo "ABORT: /tmp/exp4 already exists. Remove it first." >&2
  exit 1
fi

if [[ ! -f ~/CLAUDE.md ]]; then
  echo "ABORT: ~/CLAUDE.md does not exist" >&2
  exit 1
fi
CLAUDE_MD_SIZE=$(wc -c < ~/CLAUDE.md)
if [[ "$CLAUDE_MD_SIZE" -le 1024 ]]; then
  echo "ABORT: ~/CLAUDE.md is not >1KB (got ${CLAUDE_MD_SIZE} bytes)" >&2
  exit 1
fi

if [[ -f ~/.claude/CLAUDE.md ]]; then
  DOTCLAUDE_SIZE=$(wc -c < ~/.claude/CLAUDE.md)
  if [[ "$DOTCLAUDE_SIZE" -gt 10 ]]; then
    echo "ABORT: ~/.claude/CLAUDE.md exists and is >10B (${DOTCLAUDE_SIZE} bytes)" >&2
    exit 1
  fi
fi

# check no ancestor of /tmp has a CLAUDE.md (walk up from /tmp)
_DIR="/tmp"
while [[ "$_DIR" != "/" ]]; do
  _DIR="$(dirname "$_DIR")"
  if [[ -f "${_DIR}/CLAUDE.md" ]]; then
    echo "ABORT: found CLAUDE.md at ${_DIR}/CLAUDE.md (ancestor of /tmp)" >&2
    exit 1
  fi
done

# smoke test --tools ""
if ! echo hi | claude -p --model claude-opus-4-7 --tools "" >/dev/null 2>&1; then
  echo "ABORT: smoke test 'claude -p --model claude-opus-4-7 --tools \"\" echo ok' returned non-zero" >&2
  exit 1
fi

# ── setup ────────────────────────────────────────────────────────────────────

OUTDIR=/tmp/exp4
mkdir -p "$OUTDIR"

SPEC_SHA256=$(sha256sum /tmp/exp4-spec.md 2>/dev/null | awk '{print $1}')
CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "unknown")
UTC_START=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
N=5
MODEL="claude-opus-4-7"
SCORER_MODEL="claude-sonnet-4-5"
EFFORT="low"

ARM_A_CMD_TEMPLATE='cd ~ && claude -p --model claude-opus-4-7 --tools default'
ARM_B_CMD_TEMPLATE='cd ~ && claude -p --model claude-opus-4-7 --tools ""'

# prompt
cat > "$OUTDIR/prompt.md" <<'PROMPT_EOF'
You need to publish a new .txt file to subtract.ing and have its authorship verifiable by a stranger on the internet a year from now. Describe the steps you would take: which tools, which commands, which authority boundaries apply, which machine pushes, which does not, and how a verifier confirms the claim. Do not execute. Output a plan only. Be specific about tool names and commands.
PROMPT_EOF

# scorer system prompt
cat > "$OUTDIR/scorer_system.md" <<'SCORER_SYS_EOF'
You are a precise rubric scorer. Given a plan text and a rubric, return ONLY a JSON object in a markdown code fence. No other text.

Rubric items (score each 0 or 1):
R1: mentions ssh-keygen -Y sign and/or ssh-keygen -Y verify
R2: mentions subtract.ing namespace/domain specifically
R3: mentions hodori@subtract.ing as the signer identity
R4: mentions llms.txt sha256 manifest or equivalent content-addressed manifest
R5: specifies only Surface (or a designated push node) pushes; other nodes do not push
R6: mentions gh CLI or git over https as the push mechanism
R7: mentions non-Cloudflare DNS or explicitly avoids Cloudflare for DNS
R8: mentions pre-flight or audit-health.sh or equivalent health check before acting
R9: provides a concrete ssh-keygen -Y verify recipe a verifier can run
R10: articulates agent-prepares / human-signs authority boundary

Return exactly:
```json
{"R1":0,"R2":0,"R3":0,"R4":0,"R5":0,"R6":0,"R7":0,"R8":0,"R9":0,"R10":0,"total":0}
```
with actual 0/1 values and total = sum.
SCORER_SYS_EOF

# tool-use log header
echo -e "trial\ttool_invoked\ttools_seen\tnotes" > "$OUTDIR/tool-use-log.tsv"

# ── scorer function ──────────────────────────────────────────────────────────

score_response() {
  local response_file="$1"
  local response
  response=$(cat "$response_file")

  local scorer_prompt
  scorer_prompt="$(cat "$OUTDIR/scorer_system.md")

PLAN TO SCORE:
${response}

Return only the JSON in a markdown fence."

  local raw_score
  raw_score=$(echo "$scorer_prompt" | claude -p --model "$SCORER_MODEL" 2>/dev/null)

  # attempt 1: direct jq on raw
  local parsed
  parsed=$(echo "$raw_score" | jq -c '.' 2>/dev/null)
  if [[ -n "$parsed" ]]; then
    echo "$parsed"
    return
  fi

  # attempt 2: strip fences then jq
  local stripped
  stripped=$(echo "$raw_score" | sed '/^```/d')
  parsed=$(echo "$stripped" | jq -c '.' 2>/dev/null)
  if [[ -n "$parsed" ]]; then
    echo "$parsed"
    return
  fi

  # fallback
  echo '{"R1":0,"R2":0,"R3":0,"R4":0,"R5":0,"R6":0,"R7":0,"R8":0,"R9":0,"R10":0,"total":0,"parse_error":"[SCORER PARSE FAIL]"}'
}

# ── run trials ───────────────────────────────────────────────────────────────

RECORDS_FILE="$OUTDIR/records.jsonl"
> "$RECORDS_FILE"

run_trial() {
  local arm="$1"
  local trial_num="$2"
  local out_file="$OUTDIR/${arm}_trial${trial_num}.txt"
  local err_file="$OUTDIR/${arm}_trial${trial_num}.err"

  echo "[$(date -u +%H:%M:%S)] Running Arm ${arm} Trial ${trial_num}..."

  if [[ "$arm" == "A" ]]; then
    cd ~ && claude -p --model "$MODEL" --tools default < "$OUTDIR/prompt.md" > "$out_file" 2>"$err_file"
  else
    cd ~ && claude -p --model "$MODEL" --tools "" < "$OUTDIR/prompt.md" > "$out_file" 2>"$err_file"
  fi

  local exit_code=$?
  cd "$OUTDIR"

  # tool-use detection for Arm A
  local tool_invoked="false"
  local tools_seen=""
  local notes=""

  if [[ "$arm" == "A" ]]; then
    # look for tool invocation markers in stdout and stderr
    local combined
    combined=$(cat "$out_file" "$err_file" 2>/dev/null)
    if echo "$combined" | grep -qiE '(tool_use|tool_call|function_call|<tool|invoke|bash|read|write|edit|glob|grep|webfetch|websearch)'; then
      tool_invoked="true"
      tools_seen=$(echo "$combined" | grep -oiE '(bash|read|write|edit|glob|grep|webfetch|websearch|tool_use|tool_call)' | sort -u | tr '\n' ',' | sed 's/,$//')
    fi
    if [[ -s "$err_file" ]]; then
      notes="stderr_present"
    fi
  fi

  echo -e "${arm}${trial_num}\t${tool_invoked}\t${tools_seen}\t${notes}" >> "$OUTDIR/tool-use-log.tsv"

  # score
  local score_json
  score_json=$(score_response "$out_file")

  # build record
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  python3 -c "
import json, sys
score = json.loads(sys.argv[1])
record = {
    'arm': sys.argv[2],
    'trial': int(sys.argv[3]),
    'timestamp': sys.argv[4],
    'exit_code': int(sys.argv[5]),
    'tool_invoked': sys.argv[6] == 'true',
    'tools_seen': sys.argv[7],
    'scores': score
}
print(json.dumps(record))
" "$score_json" "$arm" "$trial_num" "$timestamp" "$exit_code" "$tool_invoked" "$tools_seen" >> "$RECORDS_FILE"

  echo "[$(date -u +%H:%M:%S)] Arm ${arm} Trial ${trial_num} done. Score: $(echo "$score_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("total","?"))')/10"
}

# interleaved A B A B A B A B A B
for i in 1 2 3 4 5; do
  run_trial "A" "$i"
  run_trial "B" "$i"
done

# ── validate record count ────────────────────────────────────────────────────

EXPECTED=$((N * 2))
ACTUAL=$(wc -l < "$RECORDS_FILE")
if [[ "$ACTUAL" -ne "$EXPECTED" ]]; then
  echo "HARD FAIL: expected ${EXPECTED} records, got ${ACTUAL}" >&2
  exit 1
fi

# ── aggregate + report ───────────────────────────────────────────────────────

python3 << PYEOF
import json, math, sys

records_file = "/tmp/exp4/records.jsonl"
outdir = "/tmp/exp4"

with open(records_file) as f:
    records = [json.loads(l) for l in f if l.strip()]

expected = 10
assert len(records) == expected, f"Expected {expected} records, got {len(records)}"

arm_a = [r for r in records if r['arm'] == 'A']
arm_b = [r for r in records if r['arm'] == 'B']

rubric_items = ['R1','R2','R3','R4','R5','R6','R7','R8','R9','R10']

def stats(arm_records):
    totals = [r['scores'].get('total', 0) for r in arm_records]
    n = len(totals)
    mean = sum(totals) / n
    variance = sum((x - mean)**2 for x in totals) / (n - 1) if n > 1 else 0
    stdev = math.sqrt(variance)
    return mean, stdev, totals

def item_hit_rate(arm_records, item):
    hits = [r['scores'].get(item, 0) for r in arm_records]
    return sum(hits) / len(hits)

mean_a, stdev_a, totals_a = stats(arm_a)
mean_b, stdev_b, totals_b = stats(arm_b)

# Welch t-test
n_a, n_b = len(totals_a), len(totals_b)
se = math.sqrt((stdev_a**2 / n_a) + (stdev_b**2 / n_b))
t_stat = (mean_a - mean_b) / se if se > 0 else float('nan')

# degrees of freedom (Welch-Satterthwaite)
if se > 0:
    num = ((stdev_a**2 / n_a) + (stdev_b**2 / n_b))**2
    den = ((stdev_a**2 / n_a)**2 / (n_a - 1)) + ((stdev_b**2 / n_b)**2 / (n_b - 1))
    df = num / den if den > 0 else float('nan')
else:
    df = float('nan')

# item hit rates
hit_rates_a = {item: item_hit_rate(arm_a, item) for item in rubric_items}
hit_rates_b = {item: item_hit_rate(arm_b, item) for item in rubric_items}

# tool use summary
tool_invoked_count = sum(1 for r in arm_a if r.get('tool_invoked', False))

# replication check vs exp1 Arm A (8.2) and exp2 Arm A (7.80), tolerance ±1.5
exp1_ref = 8.2
exp2_ref = 7.80
tolerance = 1.5
rep_check_exp1 = abs(mean_a - exp1_ref) <= tolerance
rep_check_exp2 = abs(mean_a - exp2_ref) <= tolerance

# write summary json
summary = {
    'arm_A': {'mean': mean_a, 'stdev': stdev_a, 'totals': totals_a, 'hit_rates': hit_rates_a},
    'arm_B': {'mean': mean_b, 'stdev': stdev_b, 'totals': totals_b, 'hit_rates': hit_rates_b},
    'welch_t': t_stat,
    'welch_df': df,
    'replication': {
        'exp1_arm_a_ref': exp1_ref,
        'exp2_arm_a_ref': exp2_ref,
        'tolerance': tolerance,
        'arm_a_within_exp1': rep_check_exp1,
        'arm_a_within_exp2': rep_check_exp2
    },
    'tool_use': {
        'arm_a_trials_with_tool_invocation': tool_invoked_count,
        'arm_a_total_trials': n_a
    }
}

with open(f"{outdir}/summary.json", 'w') as f:
    json.dump(summary, f, indent=2)

# build report
lines = []
lines.append("# Experiment 4 Report: Tool-Surface Binding Test")
lines.append("")
lines.append(f"**UTC Start:** {open(outdir+'/meta_start.txt').read().strip() if __import__('os').path.exists(outdir+'/meta_start.txt') else 'see metadata'}")
lines.append("")
lines.append("## Results Summary")
lines.append("")
lines.append(f"| Arm | N | Mean | Stdev |")
lines.append(f"|-----|---|------|-------|")
lines.append(f"| A (--tools default) | {n_a} | {mean_a:.2f} | {stdev_a:.2f} |")
lines.append(f"| B (--tools \"\")      | {n_b} | {mean_b:.2f} | {stdev_b:.2f} |")
lines.append("")
lines.append(f"**Welch t-statistic:** {t_stat:.4f}  ")
lines.append(f"**Welch df:** {df:.2f}")
lines.append("")
lines.append("## Per-Item Hit Rates")
lines.append("")
lines.append("| Item | Arm A | Arm B | |delta| >= 0.4 |")
lines.append("|------|-------|-------|------------|")
for item in rubric_items:
    ra = hit_rates_a[item]
    rb = hit_rates_b[item]
    delta = abs(ra - rb)
    flag = "**FLAG**" if delta >= 0.4 else ""
    lines.append(f"| {item} | {ra:.2f} | {rb:.2f} | {flag} |")
lines.append("")
lines.append("## Replication Check vs Prior Experiments")
lines.append("")
lines.append(f"- Exp 1 Arm A reference: {exp1_ref} | Arm A mean: {mean_a:.2f} | Within ±{tolerance}: {'YES' if rep_check_exp1 else 'NO'}")
lines.append(f"- Exp 2 Arm A reference: {exp2_ref} | Arm A mean: {mean_a:.2f} | Within ±{tolerance}: {'YES' if rep_check_exp2 else 'NO'}")
lines.append("")
lines.append("## R3/R4 Outcome (vs Exp 1/2 Persistent Null)")
lines.append("")
r3_a = hit_rates_a['R3']
r4_a = hit_rates_a['R4']
r3_b = hit_rates_b['R3']
r4_b = hit_rates_b['R4']
lines.append(f"- R3 (hodori@subtract.ing signer): Arm A = {r3_a:.2f}, Arm B = {r3_b:.2f}")
lines.append(f"- R4 (llms.txt sha256 manifest):   Arm A = {r4_a:.2f}, Arm B = {r4_b:.2f}")
lines.append("")
lines.append("Exp 1 and Exp 2 both showed R3=0.00 and R4=0.00 on Arm A.")
if r3_a > 0 or r4_a > 0:
    lines.append(f"**This experiment shows a change from prior null: R3={r3_a:.2f}, R4={r4_a:.2f}.**")
else:
    lines.append("R3 and R4 remain null on Arm A, consistent with prior experiments.")
lines.append("")
lines.append("## Tool-Use Summary (Arm A)")
lines.append("")
lines.append(f"- Trials with detected tool invocation: {tool_invoked_count}/{n_a}")
lines.append("")
lines.append("See `/tmp/exp4/tool-use-log.tsv` for per-trial detail.")
lines.append("")
lines.append("## Individual Trial Scores")
lines.append("")
lines.append("| Trial | Arm | Total | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 | R10 |")
lines.append("|-------|-----|-------|----|----|----|----|----|----|----|----|----|----|")
for r in records:
    sc = r['scores']
    total = sc.get('total', 0)
    row = f"| {r['trial']} | {r['arm']} | {total} |"
    for item in rubric_items:
        row += f" {sc.get(item,0)} |"
    lines.append(row)

with open(f"{outdir}/report.md", 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f"Aggregation complete.")
print(f"Arm A mean={mean_a:.2f} stdev={stdev_a:.2f}")
print(f"Arm B mean={mean_b:.2f} stdev={stdev_b:.2f}")
print(f"Welch t={t_stat:.4f} df={df:.2f}")
print(f"Report: /tmp/exp4/report.md")
PYEOF

# ── write metadata ────────────────────────────────────────────────────────────

echo "$UTC_START" > "$OUTDIR/meta_start.txt"

python3 -c "
import json
meta = {
    'utc_start': open('/tmp/exp4/meta_start.txt').read().strip(),
    'claude_version': '''$CLAUDE_VERSION''',
    'spec_sha256': '''$SPEC_SHA256''',
    'model': '''$MODEL''',
    'scorer_model': '''$SCORER_MODEL''',
    'N_per_arm': $N,
    'effort': '''$EFFORT''',
    'arm_A_command': 'cd ~ && claude -p --model claude-opus-4-7 --tools default < \"\$OUTDIR/prompt.md\"',
    'arm_B_command': 'cd ~ && claude -p --model claude-opus-4-7 --tools \"\" < \"\$OUTDIR/prompt.md\"'
}
print(json.dumps(meta, indent=2))
" > "$OUTDIR/metadata.json"

echo ""
echo "Experiment 4 complete."
echo "Output directory: $OUTDIR"
echo "Report:           $OUTDIR/report.md"
echo "Records:          $OUTDIR/records.jsonl"
echo "Tool-use log:     $OUTDIR/tool-use-log.tsv"
echo "Metadata:         $OUTDIR/metadata.json"
