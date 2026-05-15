#!/usr/bin/env python3
"""Analyze Lua corpus manifest vs BM25 results across all scorers."""
import json, os, glob, statistics

OUTDIR = "/tmp/lua-corpus/results"

def load_scorer(name):
    score_dir = f"{OUTDIR}/scores-{name}"
    if not os.path.exists(f"{score_dir}/shuffle_map.tsv"):
        return None
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
            s = json.load(f)
        if idx in smap:
            scores[smap[idx]] = s
    return scores

def kendall_tau(x, y):
    n = len(x)
    c = d = 0
    for i in range(n):
        for j in range(i+1, n):
            sx = x[i] - x[j]
            sy = y[i] - y[j]
            if sx * sy > 0: c += 1
            elif sx * sy < 0: d += 1
    return (c - d) / (c + d) if (c + d) else 0

scorers = {}
for name in ['claude', 'gemma', 'qwen']:
    s = load_scorer(name)
    if s:
        scorers[name] = s

if not scorers:
    print("No scorer data found. Run score-lua.py first.")
    exit(1)

all_qids = sorted(set(qid for scores in scorers.values() for qid, arm in scores if arm == 'M'))

print("=" * 60)
print("LUA CORPUS — MANIFEST vs BM25")
print("=" * 60)

# Load metrics
metrics_file = f"{OUTDIR}/metrics.tsv"
if os.path.exists(metrics_file):
    m_tokens = []
    r_tokens = []
    m_wall = []
    r_wall = []
    with open(metrics_file) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 6 and parts[0] != 'id':
                arm = parts[1]
                wall = int(parts[3])
                ptok = int(parts[4])
                ctok = int(parts[5])
                if arm == 'M':
                    m_tokens.append(ptok + ctok)
                    m_wall.append(wall)
                else:
                    r_tokens.append(ptok + ctok)
                    r_wall.append(wall)
    if m_tokens:
        print(f"\n--- Cost Metrics ---")
        print(f"  Arm M: {statistics.mean(m_tokens):.0f} avg tokens, {statistics.mean(m_wall):.0f}ms avg wall")
        print(f"  Arm R: {statistics.mean(r_tokens):.0f} avg tokens, {statistics.mean(r_wall):.0f}ms avg wall")

print(f"\n--- Per-Arm Means (A1+A2+A3 composite) ---")
print(f"{'Scorer':<12} {'Arm M':>8} {'Arm R':>8} {'M-R':>8} {'M wins':>8}")
print("-" * 52)

for scorer_name in sorted(scorers.keys()):
    scores = scorers[scorer_name]
    m_totals = []
    r_totals = []
    for qid in all_qids:
        m = scores.get((qid, 'M'))
        r = scores.get((qid, 'R'))
        if m and r:
            m_totals.append(sum(m.get(k, 3) for k in ['A1', 'A2', 'A3']))
            r_totals.append(sum(r.get(k, 3) for k in ['A1', 'A2', 'A3']))
    if not m_totals:
        continue
    m_mean = statistics.mean(m_totals)
    r_mean = statistics.mean(r_totals)
    m_wins = sum(1 for mt, rt in zip(m_totals, r_totals) if mt > rt)
    print(f"{scorer_name:<12} {m_mean:>8.2f} {r_mean:>8.2f} {m_mean - r_mean:>+8.2f} {m_wins:>5}/{len(m_totals)}")

# Per-dimension for each scorer
for scorer_name in sorted(scorers.keys()):
    scores = scorers[scorer_name]
    print(f"\n--- {scorer_name} Per-Dimension ---")
    for dim in ['A1', 'A2', 'A3']:
        m_vals = [scores[(qid, 'M')].get(dim, 3) for qid in all_qids if (qid, 'M') in scores and (qid, 'R') in scores]
        r_vals = [scores[(qid, 'R')].get(dim, 3) for qid in all_qids if (qid, 'M') in scores and (qid, 'R') in scores]
        if m_vals:
            label = {'A1': 'Correctness', 'A2': 'Completeness', 'A3': 'Coherence'}[dim]
            print(f"  {dim} ({label}): M={statistics.mean(m_vals):.2f} R={statistics.mean(r_vals):.2f} diff={statistics.mean(m_vals)-statistics.mean(r_vals):+.2f}")

# Pairwise tau
scorer_names = sorted(scorers.keys())
if len(scorer_names) > 1:
    print(f"\n--- Pairwise Kendall Tau ---")
    for i, s1 in enumerate(scorer_names):
        for s2 in scorer_names[i+1:]:
            diffs1, diffs2 = [], []
            for qid in all_qids:
                m1, r1 = scorers[s1].get((qid, 'M')), scorers[s1].get((qid, 'R'))
                m2, r2 = scorers[s2].get((qid, 'M')), scorers[s2].get((qid, 'R'))
                if all([m1, r1, m2, r2]):
                    d1 = sum(m1.get(k, 3) for k in ['A1','A2','A3']) - sum(r1.get(k, 3) for k in ['A1','A2','A3'])
                    d2 = sum(m2.get(k, 3) for k in ['A1','A2','A3']) - sum(r2.get(k, 3) for k in ['A1','A2','A3'])
                    diffs1.append(d1)
                    diffs2.append(d2)
            if len(diffs1) >= 3:
                tau = kendall_tau(diffs1, diffs2)
                print(f"  {s1} vs {s2}: tau={tau:+.3f} (n={len(diffs1)})")

# Question-type breakdown
print(f"\n--- By Question Type ---")
type_map = {}
with open("/tmp/lua-corpus/questions.tsv") as f:
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) >= 3 and parts[0] != 'id':
            type_map[parts[0]] = parts[1]

for qtype in ['traversal', 'synthesis', 'similarity']:
    typed_qids = [q for q in all_qids if type_map.get(q) == qtype]
    if not typed_qids:
        continue
    print(f"\n  {qtype} (n={len(typed_qids)}):")
    for scorer_name in sorted(scorers.keys()):
        scores = scorers[scorer_name]
        m_tots = []
        r_tots = []
        for qid in typed_qids:
            m = scores.get((qid, 'M'))
            r = scores.get((qid, 'R'))
            if m and r:
                m_tots.append(sum(m.get(k, 3) for k in ['A1','A2','A3']))
                r_tots.append(sum(r.get(k, 3) for k in ['A1','A2','A3']))
        if m_tots:
            print(f"    {scorer_name}: M={statistics.mean(m_tots):.2f} R={statistics.mean(r_tots):.2f} diff={statistics.mean(m_tots)-statistics.mean(r_tots):+.2f}")

print()
