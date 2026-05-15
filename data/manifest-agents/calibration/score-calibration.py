#!/usr/bin/env python3
"""score-calibration.py — blind-score handler implementations to calibrate scorers.
Same three scorers as manifest-agents (claude, gemma, qwen), same A1/A2/A3 format.
Ground truth from variance-lab-handler-methodology.txt enables calibration comparison.
"""
import json, os, random, re, sys, time, socket, subprocess, urllib.request

scorer = sys.argv[1]
start_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0

CALDIR = "/tmp/handler-calibration"
SCORE_DIR = f"{CALDIR}/scores-{scorer}"
os.makedirs(SCORE_DIR, exist_ok=True)

SPEC = open(f"{CALDIR}/full-spec.txt").read()

RUBRIC = """Score this bash implementation against the spec on three dimensions.
Return ONLY a JSON object on a single line with keys A1, A2, A3, each value 1-5.
No markdown fences. No explanation. Just the JSON.

A1: Correctness (1=multiple bugs or gate failures, 5=all spec requirements implemented correctly)
A2: Completeness (1=missing major features, 5=both tasks fully implemented with all required behaviors)
A3: Code quality (1=leaks variables, breaks shell conventions, 5=clean, safe, follows __subtract_* conventions)

--- SPEC ---
{spec}

--- IMPLEMENTATION ---
{impl}

--- END ---"""

items = []
for fname in sorted(os.listdir(f"{CALDIR}/impls")):
    if not fname.endswith('.sh'):
        continue
    label = fname.replace('.sh', '').replace('impl-', '')
    path = f"{CALDIR}/impls/{fname}"
    with open(path) as f:
        content = f.read()
    if len(content.strip()) < 10:
        continue
    items.append((label, content))

random.seed(99)
random.shuffle(items)

with open(f"{SCORE_DIR}/shuffle_map.tsv", 'w') as f:
    for i, (label, _) in enumerate(items):
        f.write(f"{i}\t{label}\n")


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
    m = re.search(r'\{[^}]+\}', raw)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    return None


print(f"Calibration scoring {len(items)} implementations with {scorer}")

for i, (label, impl) in enumerate(items):
    if i < start_idx:
        continue
    score_file = f"{SCORE_DIR}/score-{i:03d}.json"
    if os.path.exists(score_file):
        print(f"  [{i}] {label} — cached")
        continue

    prompt = RUBRIC.format(spec=SPEC, impl=impl)

    print(f"  [{i}] scoring...", end='', flush=True)
    t0 = time.time()
    try:
        raw = do_score(prompt)
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
