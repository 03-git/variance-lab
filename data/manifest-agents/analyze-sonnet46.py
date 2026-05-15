#!/usr/bin/env python3
"""Analyze sonnet-4-6 as 4th scorer on V2 outputs, compare with existing 3 scorers."""
import json, os, glob
import statistics

SCORE_DIR = "/tmp/manifest-agents-v2/scores-sonnet46"
OUTDIR = "/tmp/manifest-agents-v2"

# Load shuffle map
shuffle_map = {}
with open(f"{SCORE_DIR}/shuffle_map.tsv") as f:
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) == 3:
            shuffle_map[int(parts[0])] = (parts[1], parts[2])

# Load sonnet-4-6 scores
sonnet46_scores = {}
for sf in sorted(glob.glob(f"{SCORE_DIR}/score-*.json")):
    idx = int(os.path.basename(sf).replace('score-', '').replace('.json', ''))
    with open(sf) as f:
        scores = json.load(f)
    qid, arm = shuffle_map[idx]
    sonnet46_scores[(qid, arm)] = scores

# Load existing scorer data
def load_scorer(name, score_dir):
    smap = {}
    with open(f"{score_dir}/shuffle_map.tsv") as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 3:
                smap[int(parts[0])] = (parts[1], parts[2])

    scores = {}
    for sf in sorted(glob.glob(f"{score_dir}/score-*.json")):
        idx = int(os.path.basename(sf).replace('score-', '').replace('.json', ''))
        with open(sf) as f:
            s = json.load(sf)
        qid, arm = smap[idx]
        scores[(qid, arm)] = s
    return scores

# Try to load other scorers
scorer_dirs = {
    'claude': f"{OUTDIR}/scores-claude",
    'gemma': f"{OUTDIR}/scores-gemma",
    'qwen': f"{OUTDIR}/scores-qwen",
}

all_scorers = {'sonnet46': sonnet46_scores}

for name, sdir in scorer_dirs.items():
    if not os.path.exists(f"{sdir}/shuffle_map.tsv"):
        continue
    smap = {}
    with open(f"{sdir}/shuffle_map.tsv") as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 3:
                smap[int(parts[0])] = (parts[1], parts[2])

    scores = {}
    for sf in sorted(glob.glob(f"{sdir}/score-*.json")):
        idx = int(os.path.basename(sf).replace('score-', '').replace('.json', ''))
        with open(sf) as f:
            s = json.load(f)
        qid, arm = smap[idx]
        scores[(qid, arm)] = s
    all_scorers[name] = scores

# Get all question IDs
all_qids = sorted(set(qid for qid, arm in sonnet46_scores.keys()))

print("=" * 60)
print("SONNET-4-6 AS 4TH SCORER — V2 MANIFEST-AGENTS")
print("=" * 60)

# Per-arm means for each scorer
print("\n--- Per-Arm Means (A1+A2+A3 composite) ---")
print(f"{'Scorer':<12} {'Arm M':>8} {'Arm R':>8} {'M-R':>8} {'M wins':>8}")
print("-" * 52)

arm_level_results = {}
for scorer_name, scores in sorted(all_scorers.items()):
    m_totals = []
    r_totals = []
    for qid in all_qids:
        m_key = (qid, 'M')
        r_key = (qid, 'R')
        if m_key in scores and r_key in scores:
            m_tot = sum(scores[m_key].get(k, 3) for k in ['A1', 'A2', 'A3'])
            r_tot = sum(scores[r_key].get(k, 3) for k in ['A1', 'A2', 'A3'])
            m_totals.append(m_tot)
            r_totals.append(r_tot)

    m_mean = statistics.mean(m_totals) if m_totals else 0
    r_mean = statistics.mean(r_totals) if r_totals else 0
    m_wins = sum(1 for m, r in zip(m_totals, r_totals) if m > r)
    n = len(m_totals)
    arm_level_results[scorer_name] = {'m_mean': m_mean, 'r_mean': r_mean, 'diff': m_mean - r_mean, 'm_wins': m_wins, 'n': n}
    print(f"{scorer_name:<12} {m_mean:>8.2f} {r_mean:>8.2f} {m_mean - r_mean:>+8.2f} {m_wins:>5}/{n}")

# Per-dimension breakdown for sonnet-4-6
print("\n--- Sonnet-4-6 Per-Dimension Breakdown ---")
for dim in ['A1', 'A2', 'A3']:
    m_vals = []
    r_vals = []
    for qid in all_qids:
        m_key = (qid, 'M')
        r_key = (qid, 'R')
        if m_key in sonnet46_scores and r_key in sonnet46_scores:
            m_vals.append(sonnet46_scores[m_key].get(dim, 3))
            r_vals.append(sonnet46_scores[r_key].get(dim, 3))
    m_mean = statistics.mean(m_vals) if m_vals else 0
    r_mean = statistics.mean(r_vals) if r_vals else 0
    label = {'A1': 'Correctness', 'A2': 'Completeness', 'A3': 'Coherence'}[dim]
    print(f"  {dim} ({label}): M={m_mean:.2f} R={r_mean:.2f} diff={m_mean-r_mean:+.2f}")

# Kendall tau between scorer pairs (on composite totals)
print("\n--- Pairwise Kendall Tau (item-level rankings) ---")
scorer_names = sorted(all_scorers.keys())

def kendall_tau(x, y):
    n = len(x)
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i+1, n):
            sign_x = (x[i] - x[j])
            sign_y = (y[i] - y[j])
            if sign_x * sign_y > 0:
                concordant += 1
            elif sign_x * sign_y < 0:
                discordant += 1
    denom = concordant + discordant
    if denom == 0:
        return 0
    return (concordant - discordant) / denom

for i, s1 in enumerate(scorer_names):
    for s2 in scorer_names[i+1:]:
        # Build paired M-R differences for shared questions
        diffs1 = []
        diffs2 = []
        for qid in all_qids:
            m1 = all_scorers[s1].get((qid, 'M'))
            r1 = all_scorers[s1].get((qid, 'R'))
            m2 = all_scorers[s2].get((qid, 'M'))
            r2 = all_scorers[s2].get((qid, 'R'))
            if all([m1, r1, m2, r2]):
                d1 = sum(m1.get(k, 3) for k in ['A1','A2','A3']) - sum(r1.get(k, 3) for k in ['A1','A2','A3'])
                d2 = sum(m2.get(k, 3) for k in ['A1','A2','A3']) - sum(r2.get(k, 3) for k in ['A1','A2','A3'])
                diffs1.append(d1)
                diffs2.append(d2)
        if len(diffs1) >= 3:
            tau = kendall_tau(diffs1, diffs2)
            print(f"  {s1} vs {s2}: tau={tau:+.3f} (n={len(diffs1)})")

# Arm agreement summary
print("\n--- Arm Direction Agreement ---")
agrees = 0
total = 0
for scorer_name in scorer_names:
    result = arm_level_results[scorer_name]
    direction = "M" if result['diff'] > 0 else ("R" if result['diff'] < 0 else "tie")
    total += 1
    if result['diff'] >= 0:
        agrees += 1
    print(f"  {scorer_name}: {'M favored' if result['diff'] > 0 else ('R favored' if result['diff'] < 0 else 'tied')} ({result['diff']:+.2f})")

print(f"\n  {agrees}/{total} scorers favor Arm M or tie")
print()
