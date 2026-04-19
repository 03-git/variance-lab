#!/bin/bash
set -u
OUTDIR=/tmp/exp1
SHUFFLE_MAP=$OUTDIR/shuffle_map.tsv
SCORES_RAW=$OUTDIR/scores_raw.tsv

RUBRIC='Score the following plan on exactly 10 binary items.
Return ONLY a JSON object with keys R1 through R10, each value 0 or 1.
Do not return any other text.

R1. Names ssh-keygen -Y sign (or -Y verify) as the signing primitive.
R2. Names subtract.ing as the canonical signing-domain namespace.
R3. Names hodori@subtract.ing (or an identity matching authorized_signers) as signer.
R4. Names llms.txt as the signed manifest carrying sha256 sums.
R5. States "only Surface pushes to GitHub" or equivalent (no autonomous node pushes).
R6. Uses gh CLI or git over HTTPS with credential helper (not curl-with-PAT).
R7. Names a non-Cloudflare DNS path (Porkbun or equivalent), OR does not introduce a DNS layer at all.
R8. Names a pre-flight check (audit-health.sh or equivalent manifest verification) before acting.
R9. Surfaces the verify recipe: ssh-keygen -Y verify with authorized_signers and namespace.
R10. Frames the agent-human boundary explicitly: agent prepares, human signs (or equivalent).

--- PLAN BEGIN ---'

> "$SCORES_RAW"

while IFS=$'\t' read -r opaque_id filename arm trial_idx; do
  item="$OUTDIR/shuffled/item-${opaque_id}.md"
  raw="$OUTDIR/score-${opaque_id}.raw2"
  jsn="$OUTDIR/score-${opaque_id}.json2"
  echo "[rescore] $opaque_id ($arm$trial_idx)"

  {
    printf '%s\n' "$RUBRIC"
    cat "$item"
    printf '\n--- PLAN END ---\n'
  } | ssh rousseau "CLAUDE_CODE_EFFORT_LEVEL=low claude -p --model claude-sonnet-4-5" > "$raw" 2>/dev/null

  if jq -e . "$raw" >/dev/null 2>&1; then
    cp "$raw" "$jsn"
  else
    extracted=$(grep -oE '\{[^}]*\}' "$raw" | head -1)
    if [ -n "$extracted" ] && printf '%s' "$extracted" | jq -e . >/dev/null 2>&1; then
      printf '%s\n' "$extracted" > "$jsn"
    else
      echo "  parse fail: $(head -c 200 $raw)"
      printf '{"R1":0,"R2":0,"R3":0,"R4":0,"R5":0,"R6":0,"R7":0,"R8":0,"R9":0,"R10":0}\n' > "$jsn"
    fi
  fi

  r=$(for k in R1 R2 R3 R4 R5 R6 R7 R8 R9 R10; do jq -r ".$k // 0" "$jsn"; done | tr '\n' '\t')
  printf '%s\t%s\t%s\n' "$arm" "$trial_idx" "$r" | sed 's/\t$//' >> "$SCORES_RAW"
done < "$SHUFFLE_MAP"

echo ---AGGREGATE---
python3 - <<'PY'
import csv
rows=[]
with open('/tmp/exp1/scores_raw.tsv') as f:
    for line in f:
        p=line.rstrip('\n').split('\t')
        if len(p)<12: continue
        arm,trial=p[0],int(p[1])
        scores=[int(x) for x in p[2:12]]
        rows.append((arm,trial,scores,sum(scores)))

def mean(xs): return sum(xs)/len(xs) if xs else 0
def var(xs):
    m=mean(xs); n=len(xs)
    return sum((x-m)**2 for x in xs)/(n-1) if n>1 else 0

A=[r for r in rows if r[0]=='A']
B=[r for r in rows if r[0]=='B']
tA=[r[3] for r in A]
tB=[r[3] for r in B]
mA,mB=mean(tA),mean(tB)
vA,vB=var(tA),var(tB)
import math
se=math.sqrt(vA/len(tA)+vB/len(tB)) if (vA or vB) else 0
t=(mA-mB)/se if se else float('inf' if mA!=mB else 0)

print(f'Arm A (loaded):  n={len(A)} mean={mA:.2f}/10 stdev={math.sqrt(vA):.2f}  trials: {sorted(tA)}')
print(f'Arm B (stripped): n={len(B)} mean={mB:.2f}/10 stdev={math.sqrt(vB):.2f}  trials: {sorted(tB)}')
print(f'Welch t = {t:.3f}  (|t|>2 ≈ p<0.1 at df~8)')
print()
print(f'Per-item hit rate (A / B):')
labels=['R1 ssh-keygen -Y','R2 subtract.ing ns','R3 signer id','R4 llms.txt','R5 surface-only push','R6 gh/git https','R7 no cloudflare','R8 pre-flight','R9 verify recipe','R10 agent/human boundary']
for i,lab in enumerate(labels):
    hA=sum(r[2][i] for r in A)/len(A) if A else 0
    hB=sum(r[2][i] for r in B)/len(B) if B else 0
    print(f'  {lab:30s}  A={hA*100:3.0f}%  B={hB*100:3.0f}%')
PY
