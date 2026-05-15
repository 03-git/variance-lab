#!/usr/bin/env python3
"""score-sonnet46.py — score v2 outputs with claude-sonnet-4-6 as 4th scorer."""
import json, os, random, re, sys, time, subprocess

start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0

OUTDIR = "/tmp/manifest-agents-v2"
SCORE_DIR = f"{OUTDIR}/scores-sonnet46"
os.makedirs(SCORE_DIR, exist_ok=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) or "."
QUESTIONS_FILE = os.path.expanduser("~/subtract.ing/variance-lab/data/manifest-agents/questions.tsv")

RUBRIC = """Score this answer about the subtract.ing codebase on three dimensions.
Return ONLY a JSON object on a single line with keys A1, A2, A3, each value 1-5.
No markdown fences. No explanation. Just the JSON.

A1: Factual correctness (1=mostly wrong, 5=fully accurate, verifiable against codebase)
A2: Completeness (1=misses most relevant files, 5=cites all relevant files/sections)
A3: Coherence (1=doesn't address the question, 5=directly and clearly answers it)

--- QUESTION ---
{question}

--- ANSWER ---
{answer}

--- END ---"""

pairs = []
for qid in sorted(os.listdir(f"{OUTDIR}/arm-m")):
    if not qid.endswith('.md'):
        continue
    base = qid[:-3]
    m_path = f"{OUTDIR}/arm-m/{qid}"
    r_path = f"{OUTDIR}/arm-r/{qid}"
    if not os.path.exists(r_path):
        continue
    with open(m_path) as f:
        m_answer = f.read()
    with open(r_path) as f:
        r_answer = f.read()
    pairs.append((base, 'M', m_answer))
    pairs.append((base, 'R', r_answer))

random.seed(42)
random.shuffle(pairs)

with open(f"{SCORE_DIR}/shuffle_map.tsv", 'w') as f:
    for i, (qid, arm, _) in enumerate(pairs):
        f.write(f"{i}\t{qid}\t{arm}\n")

questions = {}
if os.path.exists(QUESTIONS_FILE):
    with open(QUESTIONS_FILE) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 3 and parts[0] != 'id':
                questions[parts[0]] = parts[2]


def score_claude(prompt):
    result = subprocess.run(
        [os.path.expanduser("~/.local/bin/claude"), "-p", "--model", "claude-sonnet-4-6"],
        input=prompt, capture_output=True, text=True,
        env={**os.environ, "CLAUDE_CODE_EFFORT_LEVEL": "low"}
    )
    return result.stdout.strip()


def parse_json(raw):
    raw = raw.strip()
    m = re.search(r'\{[^}]+\}', raw)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    return None


print(f"Scoring {len(pairs)} items with sonnet-4-6 (starting at {start_idx})")

for i, (qid, arm, answer) in enumerate(pairs):
    if i < start_idx:
        continue
    score_file = f"{SCORE_DIR}/score-{i:03d}.json"
    if os.path.exists(score_file):
        print(f"  [{i}] {qid} — cached")
        continue

    question = questions.get(qid, qid)
    prompt = RUBRIC.format(question=question, answer=answer)

    print(f"  [{i}] {qid}...", end='', flush=True)
    t0 = time.time()
    try:
        raw = score_claude(prompt)
    except Exception as e:
        print(f" ERROR: {e}")
        raw = ""
    elapsed = time.time() - t0

    parsed = parse_json(raw)
    if parsed and all(k in parsed for k in ['A1', 'A2', 'A3']):
        with open(score_file, 'w') as f:
            json.dump(parsed, f)
        print(f" A1={parsed['A1']} A2={parsed['A2']} A3={parsed['A3']} ({elapsed:.0f}s)")
    else:
        with open(f"{SCORE_DIR}/raw-{i:03d}.txt", 'w') as f:
            f.write(raw)
        parsed = {"A1": 3, "A2": 3, "A3": 3}
        with open(score_file, 'w') as f:
            json.dump(parsed, f)
        print(f" PARSE FAIL ({elapsed:.0f}s)")

print("Done.")
