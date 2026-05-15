#!/usr/bin/env python3
"""analyze-calibration.py — compare scorer rankings against handler methodology ground truth.

Ground truth from variance-lab-handler-methodology.txt:
- A (opus47): rubric 14, functional pass, 108 LoC — HIGH quality
- B (sonnet45): rubric 14, functional FAIL (markdown fence) — MEDIUM (good code, non-executable)
- C (sonnet46): rubric 13, functional pass — HIGH quality
- D (sonnet46low): rubric 13, functional pass, deliberative winner — HIGH quality
- E (qwen2.5-7b): expected lower quality (7B model, similar to original qwen3coder elimination)

Ground truth tiers:
  Tier 1 (good): A, C, D
  Tier 2 (flawed but substantive): B
  Tier 3 (significant defects expected): E

In the re-dispatch, implementations may differ from originals. We assess:
1. Can scorers distinguish quality tiers?
2. Do scorers agree on relative ranking?
3. Calibration spread across scorers (same as manifest-agents observation)
"""
import json, os, sys

CALDIR = "/tmp/handler-calibration"
scorers = ['claude', 'gemma', 'qwen']

# load shuffle maps and scores
results = {}  # {scorer: {label: {A1, A2, A3}}}
for s in scorers:
    sdir = f"{CALDIR}/scores-{s}"
    if not os.path.isdir(sdir):
        continue
    # read shuffle map
    shuffle_map = {}
    mapfile = f"{sdir}/shuffle_map.tsv"
    if os.path.exists(mapfile):
        with open(mapfile) as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    shuffle_map[int(parts[0])] = parts[1]

    scores = {}
    for fname in sorted(os.listdir(sdir)):
        if not fname.startswith('score-') or not fname.endswith('.json'):
            continue
        idx = int(fname.replace('score-', '').replace('.json', ''))
        label = shuffle_map.get(idx, f"unknown-{idx}")
        with open(f"{sdir}/{fname}") as f:
            data = json.loads(f.read())
        scores[label] = data
    results[s] = scores

if not results:
    print("No scorer data found.")
    sys.exit(1)

# implementation metadata
impl_info = {}
for fname in sorted(os.listdir(f"{CALDIR}/impls")):
    if not fname.endswith('.sh'):
        continue
    label = fname.replace('.sh', '').replace('impl-', '')
    path = f"{CALDIR}/impls/{fname}"
    with open(path) as f:
        content = f.read()
    lines = len(content.strip().split('\n')) if content.strip() else 0
    has_fence = content.strip().startswith('```')
    impl_info[label] = {'lines': lines, 'has_fence': has_fence, 'chars': len(content)}

print("=" * 70)
print("HANDLER METHODOLOGY SCORER CALIBRATION")
print("=" * 70)

# table: per-impl scores by scorer
all_labels = sorted(set().union(*[r.keys() for r in results.values()]))
print(f"\n{'Impl':<6}", end='')
for s in scorers:
    if s in results:
        print(f"  {s:>8} A1 A2 A3  comp", end='')
print()
print("-" * 70)

for label in all_labels:
    info = impl_info.get(label, {})
    fence_marker = " [FENCE]" if info.get('has_fence') else ""
    print(f"{label:<6}", end='')
    for s in scorers:
        if s in results and label in results[s]:
            d = results[s][label]
            comp = (d['A1'] + d['A2'] + d['A3']) / 3.0
            print(f"  {s:>8} {d['A1']:>2} {d['A2']:>2} {d['A3']:>2}  {comp:.2f}", end='')
    print(f"  ({info.get('lines', '?')} lines{fence_marker})")

# composite by scorer
print(f"\n{'='*70}")
print("COMPOSITE MEANS BY SCORER")
print(f"{'='*70}")
for s in scorers:
    if s not in results:
        continue
    scores_list = list(results[s].values())
    if not scores_list:
        continue
    mean_a1 = sum(d['A1'] for d in scores_list) / len(scores_list)
    mean_a2 = sum(d['A2'] for d in scores_list) / len(scores_list)
    mean_a3 = sum(d['A3'] for d in scores_list) / len(scores_list)
    mean_comp = (mean_a1 + mean_a2 + mean_a3) / 3.0
    print(f"  {s:>8}: A1={mean_a1:.2f} A2={mean_a2:.2f} A3={mean_a3:.2f} composite={mean_comp:.2f}")

# ranking comparison
print(f"\n{'='*70}")
print("RANKINGS BY SCORER (composite, descending)")
print(f"{'='*70}")
for s in scorers:
    if s not in results:
        continue
    ranked = sorted(results[s].items(), key=lambda x: -(x[1]['A1'] + x[1]['A2'] + x[1]['A3']) / 3.0)
    print(f"  {s:>8}: ", end='')
    for label, d in ranked:
        comp = (d['A1'] + d['A2'] + d['A3']) / 3.0
        print(f"{label}({comp:.1f}) ", end='')
    print()

# ground truth comparison
print(f"\n{'='*70}")
print("GROUND TRUTH COMPARISON")
print(f"{'='*70}")
print("Expected tiers: Tier 1 (A,C,D high) > Tier 2 (B medium) > Tier 3 (E low)")
print("Expected from methodology: frontier models produce better code than 7B")
print()

for s in scorers:
    if s not in results:
        continue
    r = results[s]
    tier1 = []
    tier2 = []
    tier3 = []
    for label in all_labels:
        if label not in r:
            continue
        comp = (r[label]['A1'] + r[label]['A2'] + r[label]['A3']) / 3.0
        if label in ('A', 'C', 'D'):
            tier1.append(comp)
        elif label == 'B':
            tier2.append(comp)
        elif label == 'E':
            tier3.append(comp)

    t1_mean = sum(tier1) / len(tier1) if tier1 else 0
    t2_mean = sum(tier2) / len(tier2) if tier2 else 0
    t3_mean = sum(tier3) / len(tier3) if tier3 else 0

    t1_gt_t3 = t1_mean > t3_mean
    print(f"  {s:>8}: Tier1={t1_mean:.2f} Tier2={t2_mean:.2f} Tier3={t3_mean:.2f}  "
          f"T1>T3={'YES' if t1_gt_t3 else 'NO'}")

# scorer agreement (pairwise rank correlation)
print(f"\n{'='*70}")
print("SCORER AGREEMENT (pairwise on composite ranking)")
print(f"{'='*70}")
available_scorers = [s for s in scorers if s in results]
for i, s1 in enumerate(available_scorers):
    for s2 in available_scorers[i+1:]:
        common = set(results[s1].keys()) & set(results[s2].keys())
        if len(common) < 2:
            continue
        rank1 = sorted(common, key=lambda l: -(results[s1][l]['A1'] + results[s1][l]['A2'] + results[s1][l]['A3']))
        rank2 = sorted(common, key=lambda l: -(results[s2][l]['A1'] + results[s2][l]['A2'] + results[s2][l]['A3']))
        # Kendall tau-b (simplified concordant/discordant pairs)
        concordant = 0
        discordant = 0
        labels_list = list(common)
        for ii in range(len(labels_list)):
            for jj in range(ii+1, len(labels_list)):
                a, b = labels_list[ii], labels_list[jj]
                r1_a = rank1.index(a)
                r1_b = rank1.index(b)
                r2_a = rank2.index(a)
                r2_b = rank2.index(b)
                if (r1_a - r1_b) * (r2_a - r2_b) > 0:
                    concordant += 1
                elif (r1_a - r1_b) * (r2_a - r2_b) < 0:
                    discordant += 1
        total = concordant + discordant
        tau = (concordant - discordant) / total if total > 0 else 0
        print(f"  {s1} vs {s2}: tau={tau:.2f} (concordant={concordant}, discordant={discordant})")

print(f"\n{'='*70}")
print("CALIBRATION SPREAD (same phenomenon as manifest-agents)")
print(f"{'='*70}")
for s in available_scorers:
    all_composites = [(r[1]['A1'] + r[1]['A2'] + r[1]['A3']) / 3.0 for r in results[s].items()]
    if all_composites:
        print(f"  {s:>8}: range [{min(all_composites):.1f}, {max(all_composites):.1f}]  "
              f"mean={sum(all_composites)/len(all_composites):.2f}")

print("\nDone.")
