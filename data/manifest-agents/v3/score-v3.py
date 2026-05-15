#!/usr/bin/env python3
"""Score V3 outputs (sonnet-4-6 inference) with specified scorer."""
import json, os, random, re, sys, time, subprocess, urllib.request

OUTDIR = "/tmp/manifest-agents-v3"
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


def score_claude(prompt):
    result = subprocess.run(
        [os.path.expanduser("~/.local/bin/claude"), "-p", "--model", "claude-sonnet-4-6"],
        input=prompt, capture_output=True, text=True,
        env={**os.environ, "CLAUDE_CODE_EFFORT_LEVEL": "low"}
    )
    return result.stdout.strip()


def score_gemma(prompt):
    import socket
    payload = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 128
    })
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(180)
    sock.connect(("localhost", 8087))
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
        return data['choices'][0]['message']['content']
    return raw


def score_qwen(prompt):
    payload = json.dumps({
        "model": "qwen",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100,
        "temperature": 0.1
    }).encode()
    req = urllib.request.Request(
        "http://localhost:8086/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def parse_json(raw):
    raw = raw.strip()
    m = re.search(r'\{[^}]+\}', raw)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    return None


questions = {}
if os.path.exists(QUESTIONS_FILE):
    with open(QUESTIONS_FILE) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 3 and parts[0] != 'id':
                questions[parts[0]] = parts[2]

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

scorer_name = sys.argv[1] if len(sys.argv) > 1 else "claude"
score_fn = {"claude": score_claude, "gemma": score_gemma, "qwen": score_qwen}[scorer_name]

score_dir = f"{OUTDIR}/scores-{scorer_name}"
os.makedirs(score_dir, exist_ok=True)

with open(f"{score_dir}/shuffle_map.tsv", 'w') as f:
    for i, (qid, arm, _) in enumerate(pairs):
        f.write(f"{i}\t{qid}\t{arm}\n")

print(f"Scoring {len(pairs)} V3 items with {scorer_name}")

for i, (qid, arm, answer) in enumerate(pairs):
    score_file = f"{score_dir}/score-{i:03d}.json"
    if os.path.exists(score_file):
        print(f"  [{i}] {qid} — cached")
        continue

    question = questions.get(qid, qid)
    prompt = RUBRIC.format(question=question, answer=answer)

    print(f"  [{i}] {qid}...", end='', flush=True)
    t0 = time.time()
    try:
        raw = score_fn(prompt)
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
        with open(f"{score_dir}/raw-{i:03d}.txt", 'w') as f:
            f.write(raw)
        parsed = {"A1": 3, "A2": 3, "A3": 3}
        with open(score_file, 'w') as f:
            json.dump(parsed, f)
        print(f" PARSE FAIL ({elapsed:.0f}s)")

print("Done.")
