#!/usr/bin/env python3
"""Infer via llama.cpp qwen-7b. Usage: infer-qwen.py prompt_file out_file met_file"""
import json, sys, time, urllib.request

prompt_file = sys.argv[1]
out_file = sys.argv[2]
met_file = sys.argv[3]

with open(prompt_file) as f:
    text = f.read()

payload = json.dumps({
    "model": "qwen",
    "messages": [{"role": "user", "content": text}],
    "max_tokens": 2048,
    "temperature": 0.3
}).encode()

t0 = int(time.time() * 1000)
try:
    req = urllib.request.Request(
        "http://localhost:8086/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    answer = data["choices"][0]["message"]["content"]
except Exception as e:
    answer = ""
    print(f"  ERROR: {e}", file=sys.stderr)

t1 = int(time.time() * 1000)
wall = t1 - t0
prompt_tok = len(text) // 4
comp_tok = len(answer) // 4

with open(out_file, 'w') as f:
    f.write(answer)
with open(met_file, 'w') as f:
    f.write(f"{wall}\t{prompt_tok}\t{comp_tok}")
