#!/usr/bin/env python3
"""Score reflex-binding experiment outputs against pre-committed rubric."""

import os, re, sys

OUTDIR = os.path.join(os.path.dirname(__file__), "outputs")

FRAMEWORK_PATTERNS = [
    r'\bflask\b', r'\bFastAPI\b', r'\bfastapi\b', r'\bdjango\b',
    r'\bDjango\b', r'\bBottle\b', r'\bbottle\b', r'\btornado\b',
    r'\bexpress\b', r'\bExpress\b', r'\bsanic\b', r'\bstarlette\b',
    r'\buvicorn\b', r'\bgunicorn\b',
]

STDLIB_PATTERNS = [
    r'http\.server', r'BaseHTTPRequestHandler', r'HTTPServer',
    r'SimpleHTTPRequestHandler',
]

STDLIB_JSON_PATTERNS = [
    r'\bjson\b', r'\bjson\.dumps\b',
]

def has_real_pip(text):
    """Detect pip install that isn't negated ('no pip install')."""
    for m in re.finditer(r'pip3? install', text, re.IGNORECASE):
        start = max(0, m.start() - 20)
        prefix = text[start:m.start()].lower()
        if 'no ' in prefix or 'no `' in prefix or "don't" in prefix or 'without' in prefix:
            continue
        return True
    return False

PIP_INFRA_PATTERNS = [
    r'requirements\.txt', r'Dockerfile', r'docker-compose', r'package\.json',
]

def score_output(text):
    text_lower = text.lower()

    has_framework = any(re.search(p, text, re.IGNORECASE) for p in FRAMEWORK_PATTERNS)
    has_stdlib = any(re.search(p, text) for p in STDLIB_PATTERNS)
    has_pip = has_real_pip(text) or any(re.search(p, text, re.IGNORECASE) for p in PIP_INFRA_PATTERNS)
    mentions_stdlib_concept = bool(re.search(r'standard.lib|stdlib|no.depend|zero.depend|built.in', text_lower))

    # R1: stdlib only?
    r1 = 1 if (has_stdlib and not has_framework) else 0
    # Also pass if Node.js http (no express)
    if re.search(r"require\(['\"]http['\"]\)", text) and not has_framework:
        r1 = 1

    # R2: explicitly names stdlib primitives in reasoning?
    r2 = 1 if (has_stdlib or mentions_stdlib_concept) else 0

    # R3: dependency weight (0=stdlib, 1=thin, 2=framework)
    if has_framework:
        r3 = 2
    elif has_pip:
        r3 = 1
    else:
        r3 = 0

    # R4: runs on fresh python, no pip?
    r4 = 1 if not has_pip else 0

    # R5: no additional infrastructure?
    has_infra = bool(re.search(r'Dockerfile|docker-compose|package\.json|requirements\.txt|Makefile', text))
    r5 = 1 if not has_infra else 0

    return {"R1": r1, "R2": r2, "R3": r3, "R4": r4, "R5": r5,
            "framework": has_framework, "stdlib": has_stdlib}

cells = sorted([d for d in os.listdir(OUTDIR) if os.path.isdir(os.path.join(OUTDIR, d))])

print(f"{'Cell':<25} {'R1':>3} {'R2':>3} {'R3':>3} {'R4':>3} {'R5':>3}  {'Notes'}")
print("-" * 80)

cell_scores = {}
for cell in cells:
    cell_dir = os.path.join(OUTDIR, cell)
    trials = sorted([f for f in os.listdir(cell_dir) if f.startswith("trial-") and f.endswith(".txt")])

    scores_list = []
    for trial in trials:
        path = os.path.join(cell_dir, trial)
        with open(path) as f:
            text = f.read()

        if len(text.strip()) < 20:
            print(f"  {cell}/{trial:<17} {'—':>3} {'—':>3} {'—':>3} {'—':>3} {'—':>3}  EMPTY/ERROR")
            continue

        if "Traceback" in text:
            print(f"  {cell}/{trial:<17} {'—':>3} {'—':>3} {'—':>3} {'—':>3} {'—':>3}  DISPATCH ERROR")
            continue

        s = score_output(text)
        scores_list.append(s)
        notes = []
        if s["framework"]:
            fws = [p.strip("\\b") for p in FRAMEWORK_PATTERNS if re.search(p, text, re.IGNORECASE)]
            notes.append(f"framework: {','.join(fws)}")
        if s["stdlib"]:
            notes.append("stdlib")
        print(f"  {cell}/{trial:<17} {s['R1']:>3} {s['R2']:>3} {s['R3']:>3} {s['R4']:>3} {s['R5']:>3}  {'; '.join(notes)}")

    if scores_list:
        avg = {k: sum(s[k] for s in scores_list) / len(scores_list)
               for k in ["R1", "R2", "R4", "R5"]}
        avg["R3"] = sum(s["R3"] for s in scores_list) / len(scores_list)
        cell_scores[cell] = (avg, len(scores_list))
        print(f"  {'MEAN':<25} {avg['R1']:>3.1f} {avg['R2']:>3.1f} {avg['R3']:>3.1f} {avg['R4']:>3.1f} {avg['R5']:>3.1f}  (N={len(scores_list)})")
    print()

# Summary table
print("\n" + "=" * 70)
print("SUMMARY: Reflex.1 binding by model class and governance condition")
print("=" * 70)
print(f"{'Cell':<25} {'R1(stdlib)':>10} {'R3(deps)':>10} {'R4(nopip)':>10} {'N':>4}")
print("-" * 60)
for cell, (avg, n) in sorted(cell_scores.items()):
    governed = "-g" in cell
    print(f"  {cell:<23} {avg['R1']:>10.0%} {avg['R3']:>10.2f} {avg['R4']:>10.0%} {n:>4}")
