#!/usr/bin/env python3
"""infer.py — send a prompt file to qwen2.5-7b, return answer + metrics."""
import json, sys, time, urllib.request

url = sys.argv[1]  # e.g. http://localhost:8086/v1/chat/completions
prompt_file = sys.argv[2]
output_file = sys.argv[3]
metrics_file = sys.argv[4]

with open(prompt_file, 'r') as f:
    prompt = f.read()

payload = json.dumps({
    'model': 'qwen2.5-7b',
    'messages': [{'role': 'user', 'content': prompt}],
    'max_tokens': 1024,
    'temperature': 0.1
}).encode()

req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
t0 = time.time()
with urllib.request.urlopen(req, timeout=120) as resp:
    data = json.loads(resp.read())
wall_ms = int((time.time() - t0) * 1000)

answer = data['choices'][0]['message']['content']
pt = data.get('usage', {}).get('prompt_tokens', 0)
ct = data.get('usage', {}).get('completion_tokens', 0)

with open(output_file, 'w') as f:
    f.write(answer)

with open(metrics_file, 'w') as f:
    f.write(f"{wall_ms}\t{pt}\t{ct}\n")
