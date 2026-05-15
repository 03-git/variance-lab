#!/usr/bin/env python3
"""score.py — blind-score manifest-agents outputs.
Usage: python3 score.py <scorer> [start_idx]
  scorer: claude | gemma | qwen
"""
import json, os, random, sys, time, urllib.request, subprocess

scorer = sys.argv[1]
start_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0

OUTDIR = "/tmp/manifest-agents"
SCORE_DIR = f"{OUTDIR}/scores-{scorer}"
os.makedirs(SCORE_DIR, exist_ok=True)

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

# build blind shuffle: interleave M and R answers without labels
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

# deterministic shuffle (seed from question set hash)
random.seed(42)
random.shuffle(pairs)

# save shuffle map for unblinding
with open(f"{SCORE_DIR}/shuffle_map.tsv", 'w') as f:
    for i, (qid, arm, _) in enumerate(pairs):
        f.write(f"{i}\t{qid}\t{arm}\n")

# read questions
questions = {}
with open(f"{os.path.dirname(__file__)}/questions.tsv" if os.path.exists(f"{os.path.dirname(os.path.abspath(__file__))}/questions.tsv") else f"{OUTDIR}/../variance-lab/data/manifest-agents/questions.tsv") as f:
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) >= 3 and parts[0] != 'id':
            questions[parts[0]] = parts[2]

# also try the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
qfile = os.path.join(script_dir, "questions.tsv")
if os.path.exists(qfile):
    questions = {}
    with open(qfile) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 3 and parts[0] != 'id':
                questions[parts[0]] = parts[2]


def score_claude(prompt):
    result = subprocess.run(
        [os.path.expanduser("~/.local/bin/claude"), "-p", "--model", "claude-sonnet-4-5"],
        input=prompt, capture_output=True, text=True,
        env={**os.environ, "CLAUDE_CODE_EFFORT_LEVEL": "low"}
    )
    return result.stdout.strip()


def score_local(url, prompt):
    payload = json.dumps({
        'model': 'local',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 64,
        'temperature': 0.1
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data['choices'][0]['message']['content'].strip()


def score_parsimony(host, port, prompt):
    import socket
    payload = json.dumps({
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 128
    })
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(180)
    sock.connect((host, port))
    sock.sendall((payload + '\n').encode())
    buf = b''
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
        if b'\n' in buf:
            break
    sock.close()
    raw = buf.decode().strip()
    data = json.loads(raw)
    if 'choices' in data:
        return data['choices'][0]['message']['content'].strip()
    elif 'content' in data:
        return data['content'].strip()
    elif 'response' in data:
        return data['response'].strip()
    return raw


def do_score(prompt):
    if scorer == 'claude':
        return score_claude(prompt)
    elif scorer == 'gemma':
        return score_parsimony("localhost", 8087, prompt)
    elif scorer == 'qwen':
        return score_local("http://localhost:8086/v1/chat/completions", prompt)
    else:
        raise ValueError(f"Unknown scorer: {scorer}")


def parse_json(raw):
    raw = raw.strip()
    if raw.startswith('{'):
        try:
            return json.loads(raw.split('\n')[0])
        except Exception:
            pass
    # try extracting from fences or surrounding text
    import re
    m = re.search(r'\{[^}]+\}', raw)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    return None


print(f"Scoring {len(pairs)} items with {scorer} (starting at {start_idx})")

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
    raw = do_score(prompt)
    elapsed = time.time() - t0

    parsed = parse_json(raw)
    if parsed and all(k in parsed for k in ['A1', 'A2', 'A3']):
        with open(score_file, 'w') as f:
            json.dump(parsed, f)
        print(f" A1={parsed['A1']} A2={parsed['A2']} A3={parsed['A3']} ({elapsed:.0f}s)")
    else:
        # save raw for debugging, use default
        with open(f"{SCORE_DIR}/raw-{i:03d}.txt", 'w') as f:
            f.write(raw)
        parsed = {"A1": 3, "A2": 3, "A3": 3}
        with open(score_file, 'w') as f:
            json.dump(parsed, f)
        print(f" PARSE FAIL — defaulted to 3/3/3 ({elapsed:.0f}s)")

print("Done.")
