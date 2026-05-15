#!/usr/bin/env python3
"""v2-analysis.py — comprehensive manifest-agents v1+v2 comparison."""
import json, os, math

def load_scores(base_dir, scorer):
    sdir = f"{base_dir}/scores-{scorer}"
    if not os.path.isdir(sdir):
        return {}, {}
    shuffle = {}
    mapfile = f"{sdir}/shuffle_map.tsv"
    if os.path.exists(mapfile):
        with open(mapfile) as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    shuffle[int(parts[0])] = (parts[1], parts[2])
    scores = {}
    for fname in sorted(os.listdir(sdir)):
        if not fname.startswith('score-') or not fname.endswith('.json'):
            continue
        idx = int(fname.replace('score-', '').replace('.json', ''))
        with open(f"{sdir}/{fname}") as f:
            data = json.loads(f.read())
        if idx in shuffle:
            qid, arm = shuffle[idx]
            key = (qid, arm)
            scores[key] = data
    return scores, shuffle

def welch_t(m1, s1, n1, m2, s2, n2):
    if n1 < 2 or n2 < 2 or (s1 == 0 and s2 == 0):
        return 0.0
    se = math.sqrt(s1**2/n1 + s2**2/n2)
    if se == 0:
        return 0.0
    return (m1 - m2) / se

def stats(vals):
    if not vals:
        return 0, 0
    m = sum(vals) / len(vals)
    if len(vals) < 2:
        return m, 0
    s = math.sqrt(sum((x-m)**2 for x in vals) / (len(vals)-1))
    return m, s

scorers = ['claude', 'gemma', 'qwen']

for version, base_dir in [('V1', '/tmp/manifest-agents'), ('V2', '/tmp/manifest-agents-v2')]:
    print(f"\n{'='*70}")
    print(f"MANIFEST-AGENTS {version}")
    print(f"{'='*70}")

    all_scores = {}
    for s in scorers:
        scores, _ = load_scores(base_dir, s)
        all_scores[s] = scores

    for s in scorers:
        if s not in all_scores or not all_scores[s]:
            continue
        m_vals = []
        r_vals = []
        for (qid, arm), data in all_scores[s].items():
            comp = (data['A1'] + data['A2'] + data['A3']) / 3.0
            if arm == 'M':
                m_vals.append(comp)
            elif arm == 'R':
                r_vals.append(comp)

        m_mean, m_std = stats(m_vals)
        r_mean, r_std = stats(r_vals)
        t = welch_t(m_mean, m_std, len(m_vals), r_mean, r_std, len(r_vals))
        print(f"  {s:>8}: M={m_mean:.2f}±{m_std:.2f} (n={len(m_vals)})  R={r_mean:.2f}±{r_std:.2f} (n={len(r_vals)})  t={t:.3f}  delta={m_mean-r_mean:+.2f}")

    # aggregate across scorers
    m_all = []
    r_all = []
    for s in scorers:
        if s not in all_scores:
            continue
        for (qid, arm), data in all_scores[s].items():
            comp = (data['A1'] + data['A2'] + data['A3']) / 3.0
            if arm == 'M':
                m_all.append(comp)
            elif arm == 'R':
                r_all.append(comp)

    m_mean, m_std = stats(m_all)
    r_mean, r_std = stats(r_all)
    t = welch_t(m_mean, m_std, len(m_all), r_mean, r_std, len(r_all))
    print(f"\n  AGGREGATE: M={m_mean:.2f}±{m_std:.2f} (n={len(m_all)})  R={r_mean:.2f}±{r_std:.2f} (n={len(r_all)})")
    print(f"             Welch t={t:.3f}  delta={m_mean-r_mean:+.2f}")

    # per-dimension aggregate
    for dim in ['A1', 'A2', 'A3']:
        m_d = []
        r_d = []
        for s in scorers:
            if s not in all_scores:
                continue
            for (qid, arm), data in all_scores[s].items():
                if arm == 'M':
                    m_d.append(data[dim])
                elif arm == 'R':
                    r_d.append(data[dim])
        if m_d and r_d:
            m_m = sum(m_d)/len(m_d)
            r_m = sum(r_d)/len(r_d)
            print(f"  {dim}: M={m_m:.2f}  R={r_m:.2f}  delta={m_m-r_m:+.2f}")

# load metrics for cost comparison
for version, base_dir in [('V1', '/tmp/manifest-agents'), ('V2', '/tmp/manifest-agents-v2')]:
    metrics_file = f"{base_dir}/metrics.tsv"
    if not os.path.exists(metrics_file):
        continue
    print(f"\n{'='*70}")
    print(f"{version} COST METRICS")
    print(f"{'='*70}")
    m_wall, r_wall = [], []
    m_prompt, r_prompt = [], []
    m_comp, r_comp = [], []
    with open(metrics_file) as f:
        header = f.readline()
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 6:
                continue
            arm = parts[1]
            try:
                wall = int(parts[3])
                prompt = int(parts[4])
                comp = int(parts[5])
            except (ValueError, IndexError):
                continue
            if arm == 'M':
                m_wall.append(wall)
                m_prompt.append(prompt)
                m_comp.append(comp)
            elif arm == 'R':
                r_wall.append(wall)
                r_prompt.append(prompt)
                r_comp.append(comp)

    if m_wall and r_wall:
        print(f"  Wall time (mean ms): M={sum(m_wall)/len(m_wall):.0f}  R={sum(r_wall)/len(r_wall):.0f}")
        print(f"  Prompt tokens (mean): M={sum(m_prompt)/len(m_prompt):.0f}  R={sum(r_prompt)/len(r_prompt):.0f}")
        print(f"  Completion tokens (mean): M={sum(m_comp)/len(m_comp):.0f}  R={sum(r_comp)/len(r_comp):.0f}")
        print(f"  Total tokens: M={sum(m_prompt)+sum(m_comp)}  R={sum(r_prompt)+sum(r_comp)}")
        print(f"  Total wall: M={sum(m_wall)/1000:.0f}s  R={sum(r_wall)/1000:.0f}s")

print("\n\nDone.")
