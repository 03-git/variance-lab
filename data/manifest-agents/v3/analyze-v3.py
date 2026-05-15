#!/usr/bin/env python3
"""Analyze V3 (sonnet-4-6 inference) vs V2 (qwen-7b inference) — model-size prediction test."""
import json, os, glob, statistics

def load_scorer(base_dir, name):
    score_dir = f"{base_dir}/scores-{name}"
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

def load_metrics(metrics_file):
    m_data, r_data = [], []
    if not os.path.exists(metrics_file):
        return m_data, r_data
    with open(metrics_file) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 6 and parts[0] != 'id':
                arm = parts[1]
                entry = {'qid': parts[0], 'wall': int(parts[3]), 'ptok': int(parts[4]), 'ctok': int(parts[5])}
                if arm == 'M':
                    m_data.append(entry)
                else:
                    r_data.append(entry)
    return m_data, r_data

print("=" * 60)
print("MODEL-SIZE PREDICTION TEST: V2 (qwen-7b) vs V3 (sonnet-4-6)")
print("=" * 60)

# Load V2 scorers
v2_scorers = {}
for name in ['claude', 'gemma', 'qwen', 'sonnet46']:
    s = load_scorer("/tmp/manifest-agents-v2", name)
    if s:
        v2_scorers[name] = s

# Load V3 scorers
v3_scorers = {}
for name in ['claude', 'gemma', 'qwen']:
    s = load_scorer("/tmp/manifest-agents-v3", name)
    if s:
        v3_scorers[name] = s

# V2 and V3 metrics
v2_m, v2_r = load_metrics("/tmp/manifest-agents-v2/metrics-v2.tsv")
v3_m, v3_r = load_metrics("/tmp/manifest-agents-v3/metrics.tsv")

print("\n--- V2 (qwen-7b) Arm Means ---")
if v2_scorers:
    v2_qids = sorted(set(qid for s in v2_scorers.values() for qid, arm in s if arm == 'M'))
    print(f"{'Scorer':<12} {'Arm M':>8} {'Arm R':>8} {'M-R':>8}")
    print("-" * 40)
    for name in sorted(v2_scorers.keys()):
        scores = v2_scorers[name]
        mt = [sum(scores[(q,'M')].get(k,3) for k in ['A1','A2','A3']) for q in v2_qids if (q,'M') in scores and (q,'R') in scores]
        rt = [sum(scores[(q,'R')].get(k,3) for k in ['A1','A2','A3']) for q in v2_qids if (q,'M') in scores and (q,'R') in scores]
        if mt:
            print(f"{name:<12} {statistics.mean(mt):>8.2f} {statistics.mean(rt):>8.2f} {statistics.mean(mt)-statistics.mean(rt):>+8.2f}")

print("\n--- V3 (sonnet-4-6) Arm Means ---")
if v3_scorers:
    v3_qids = sorted(set(qid for s in v3_scorers.values() for qid, arm in s if arm == 'M'))
    print(f"{'Scorer':<12} {'Arm M':>8} {'Arm R':>8} {'M-R':>8}")
    print("-" * 40)
    for name in sorted(v3_scorers.keys()):
        scores = v3_scorers[name]
        mt = [sum(scores[(q,'M')].get(k,3) for k in ['A1','A2','A3']) for q in v3_qids if (q,'M') in scores and (q,'R') in scores]
        rt = [sum(scores[(q,'R')].get(k,3) for k in ['A1','A2','A3']) for q in v3_qids if (q,'M') in scores and (q,'R') in scores]
        if mt:
            print(f"{name:<12} {statistics.mean(mt):>8.2f} {statistics.mean(rt):>8.2f} {statistics.mean(mt)-statistics.mean(rt):>+8.2f}")
else:
    print("  No V3 scorer data yet.")

# Cost comparison
if v2_m and v3_m:
    print("\n--- Cost Comparison ---")
    v2_m_tok = statistics.mean(e['ptok'] + e['ctok'] for e in v2_m)
    v2_r_tok = statistics.mean(e['ptok'] + e['ctok'] for e in v2_r)
    v3_m_tok = statistics.mean(e['ptok'] + e['ctok'] for e in v3_m)
    v3_r_tok = statistics.mean(e['ptok'] + e['ctok'] for e in v3_r)
    v2_m_wall = statistics.mean(e['wall'] for e in v2_m)
    v2_r_wall = statistics.mean(e['wall'] for e in v2_r)
    v3_m_wall = statistics.mean(e['wall'] for e in v3_m)
    v3_r_wall = statistics.mean(e['wall'] for e in v3_r)
    print(f"  V2 qwen-7b:    M={v2_m_tok:.0f}tok/{v2_m_wall:.0f}ms  R={v2_r_tok:.0f}tok/{v2_r_wall:.0f}ms")
    print(f"  V3 sonnet-4-6: M={v3_m_tok:.0f}tok/{v3_m_wall:.0f}ms  R={v3_r_tok:.0f}tok/{v3_r_wall:.0f}ms")

# Prediction evaluation
print("\n--- Prediction: 'Gap narrows with larger models' ---")
if v2_scorers and v3_scorers:
    v2_diffs = []
    v3_diffs = []
    for name in sorted(set(v2_scorers.keys()) & set(v3_scorers.keys())):
        v2s = v2_scorers[name]
        v3s = v3_scorers[name]
        v2_mt = [sum(v2s[(q,'M')].get(k,3) for k in ['A1','A2','A3']) for q in v2_qids if (q,'M') in v2s and (q,'R') in v2s]
        v2_rt = [sum(v2s[(q,'R')].get(k,3) for k in ['A1','A2','A3']) for q in v2_qids if (q,'M') in v2s and (q,'R') in v2s]
        v3_mt = [sum(v3s[(q,'M')].get(k,3) for k in ['A1','A2','A3']) for q in v3_qids if (q,'M') in v3s and (q,'R') in v3s]
        v3_rt = [sum(v3s[(q,'R')].get(k,3) for k in ['A1','A2','A3']) for q in v3_qids if (q,'M') in v3s and (q,'R') in v3s]
        if v2_mt and v3_mt:
            v2_gap = abs(statistics.mean(v2_mt) - statistics.mean(v2_rt))
            v3_gap = abs(statistics.mean(v3_mt) - statistics.mean(v3_rt))
            v2_diffs.append(v2_gap)
            v3_diffs.append(v3_gap)
            print(f"  {name}: V2 gap={v2_gap:.2f} → V3 gap={v3_gap:.2f} ({'narrower' if v3_gap < v2_gap else 'wider'})")

    if v2_diffs:
        v2_avg_gap = statistics.mean(v2_diffs)
        v3_avg_gap = statistics.mean(v3_diffs)
        print(f"\n  Average gap: V2={v2_avg_gap:.2f} → V3={v3_avg_gap:.2f}")
        if v3_avg_gap < v2_avg_gap:
            print(f"  PREDICTION CONFIRMED: gap narrows by {v2_avg_gap - v3_avg_gap:.2f}")
        else:
            print(f"  PREDICTION REJECTED: gap widens by {v3_avg_gap - v2_avg_gap:.2f}")
else:
    print("  Need V3 scorer data to evaluate prediction.")

print()
