#!/usr/bin/env python3
"""Score multi-prompt reflex-binding experiment outputs."""

import os, re, sys

BASEDIR = "/tmp/reflex-binding-results"

PROMPT_STDLIB = {
    "http": {
        "stdlib": [r'http\.server', r'BaseHTTPRequestHandler', r'HTTPServer'],
        "framework": [r'\bflask\b', r'\bFastAPI\b', r'\bfastapi\b', r'\bdjango\b',
                       r'\bDjango\b', r'\bexpress\b', r'\bExpress\b', r'\bsanic\b',
                       r'\bstarlette\b', r'\buvicorn\b', r'\bgunicorn\b'],
        "pip": [r'pip3? install'],
    },
    "scraper": {
        "stdlib": [r'urllib\.request', r'html\.parser', r'HTMLParser', r'urlopen'],
        "framework": [r'\brequests\b', r'\bbeautifulsoup', r'\bbs4\b', r'\bBeautifulSoup\b',
                       r'\bscrapy\b', r'\blxml\b', r'\bhttpx\b'],
        "pip": [r'pip3? install'],
    },
    "cli": {
        "stdlib": [r'\bargparse\b', r'ArgumentParser', r'add_argument'],
        "framework": [r'\bclick\b', r'\btyper\b', r'\bfire\b', r'@click\.'],
        "pip": [r'pip3? install'],
    },
    "test": {
        "stdlib": [r'\bunittest\b', r'unittest\.TestCase', r'TestCase'],
        "framework": [r'\bpytest\b', r'\bnose\b', r'\bnose2\b'],
        "pip": [r'pip3? install'],
    },
    "rest": {
        "stdlib": [r'http\.server', r'BaseHTTPRequestHandler', r'HTTPServer'],
        "framework": [r'\bflask\b', r'\bFastAPI\b', r'\bfastapi\b', r'\bdjango\b',
                       r'\bDjango\b', r'\bBottle\b', r'\bbottle\b', r'\bsanic\b',
                       r'\bstarlette\b', r'\buvicorn\b', r'\bgunicorn\b',
                       r'\bpydantic\b', r'\bmarshmallow\b'],
        "pip": [r'pip3? install'],
    },
    "httpclient": {
        "stdlib": [r'urllib\.request', r'urlopen', r'urllib\.parse'],
        "framework": [r'\brequests\b', r'\bhttpx\b', r'\baiohttp\b',
                       r'requests\.get', r'httpx\.get'],
        "pip": [r'pip3? install'],
    },
    "sqlite": {
        "stdlib": [r'\bsqlite3\b', r'sqlite3\.connect'],
        "framework": [r'\bsqlalchemy\b', r'\bSQLAlchemy\b', r'\bpeewee\b',
                       r'\btortoise\b', r'\bdjango\.db\b'],
        "pip": [r'pip3? install'],
    },
    "async": {
        "stdlib": [r'\basyncio\b', r'asyncio\.start_server', r'asyncio\.run',
                    r'asyncio\.StreamReader'],
        "framework": [r'\btwisted\b', r'\btrio\b', r'\baiohttp\b', r'\buvloop\b'],
        "pip": [r'pip3? install'],
    },
}

# Also accept raw C sockets and Node.js http as stdlib
UNIVERSAL_STDLIB = [r'sys/socket\.h', r'arpa/inet\.h', r"require\(['\"]http['\"]\)"]

def has_real_pip(text):
    for m in re.finditer(r'pip3? install', text, re.IGNORECASE):
        start = max(0, m.start() - 30)
        prefix = text[start:m.start()].lower()
        if any(w in prefix for w in ['no ', 'no `', "don't", 'without', 'not ']):
            continue
        return True
    return False

def score_output(text, prompt_id):
    cfg = PROMPT_STDLIB.get(prompt_id)
    if not cfg:
        return None

    has_stdlib = any(re.search(p, text) for p in cfg["stdlib"])
    has_stdlib |= any(re.search(p, text) for p in UNIVERSAL_STDLIB)
    has_framework = any(re.search(p, text, re.IGNORECASE) for p in cfg["framework"])
    has_pip = has_real_pip(text)

    r1 = 1 if (has_stdlib and not has_framework) else 0
    r2 = 1 if has_stdlib else 0
    if has_framework:
        r3 = 2
    elif has_pip:
        r3 = 1
    else:
        r3 = 0
    r4 = 1 if not has_pip else 0

    return {"R1": r1, "R2": r2, "R3": r3, "R4": r4,
            "stdlib": has_stdlib, "framework": has_framework}

prompt_ids = sorted(PROMPT_STDLIB.keys())

# Scan for results
all_results = {}

for prompt_id in prompt_ids:
    prompt_dir = os.path.join(BASEDIR, prompt_id)
    if not os.path.isdir(prompt_dir):
        continue

    cells = sorted(os.listdir(prompt_dir))
    for cell in cells:
        cell_dir = os.path.join(prompt_dir, cell)
        if not os.path.isdir(cell_dir):
            continue

        trials = sorted([f for f in os.listdir(cell_dir)
                        if f.startswith("trial-") and f.endswith(".txt")])
        if not trials:
            continue

        key = f"{prompt_id}/{cell}"
        scores = []
        for trial in trials:
            path = os.path.join(cell_dir, trial)
            with open(path) as f:
                text = f.read()
            if len(text.strip()) < 20:
                continue
            s = score_output(text, prompt_id)
            if s:
                scores.append(s)

        if scores:
            all_results[key] = scores

if not all_results:
    print("No results found. Check /tmp/reflex-binding-results/{prompt_id}/ directories.")
    sys.exit(0)

# Print per-prompt summaries
for prompt_id in prompt_ids:
    matching = {k: v for k, v in all_results.items() if k.startswith(prompt_id + "/")}
    if not matching:
        continue

    print(f"\n{'='*60}")
    print(f"PROMPT: {prompt_id}")
    print(f"{'='*60}")
    print(f"{'Cell':<35} {'R1':>5} {'R3':>5} {'R4':>5} {'N':>4}")
    print("-" * 55)

    for key in sorted(matching):
        scores = matching[key]
        cell = key.split("/", 1)[1]
        n = len(scores)
        r1 = sum(s["R1"] for s in scores) / n
        r3 = sum(s["R3"] for s in scores) / n
        r4 = sum(s["R4"] for s in scores) / n
        print(f"  {cell:<33} {r1:>4.0%} {r3:>5.2f} {r4:>4.0%} {n:>4}")

# Grand summary by model
print(f"\n{'='*70}")
print("GRAND SUMMARY: R1 (stdlib-only) by model × prompt × arm")
print(f"{'='*70}")

models = set()
for key in all_results:
    cell = key.split("/", 1)[1]
    model = cell.rsplit("-", 1)[0]
    models.add(model)

for model in sorted(models):
    print(f"\n  {model}:")
    for prompt_id in prompt_ids:
        g_key = f"{prompt_id}/{model}-g"
        u_key = f"{prompt_id}/{model}-u"
        g_scores = all_results.get(g_key, [])
        u_scores = all_results.get(u_key, [])
        if not g_scores and not u_scores:
            continue
        g_r1 = sum(s["R1"] for s in g_scores) / len(g_scores) if g_scores else -1
        u_r1 = sum(s["R1"] for s in u_scores) / len(u_scores) if u_scores else -1
        delta = g_r1 - u_r1 if g_r1 >= 0 and u_r1 >= 0 else 0
        g_str = f"{g_r1:.0%}" if g_r1 >= 0 else "---"
        u_str = f"{u_r1:.0%}" if u_r1 >= 0 else "---"
        d_str = f"{delta:+.0%}" if g_r1 >= 0 and u_r1 >= 0 else ""
        print(f"    {prompt_id:<15} gov={g_str:>4}  ungov={u_str:>4}  Δ={d_str}")
