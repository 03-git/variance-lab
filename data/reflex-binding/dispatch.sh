#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PROMPT=$(cat "$DIR/prompt.txt")
GOV=$(cat /Users/jns/subtract.ing/governance.conf.universal.txt 2>/dev/null || echo "")

OUTDIR="$DIR/outputs"
mkdir -p "$OUTDIR"/{qwen-g,qwen-u,gemma-g,gemma-u}

QWEN_PORT=8086
GEMMA_PORT=8087

infer_qwen() {
    local sysprompt="$1"
    local userprompt="$2"
    python3 -c "
import urllib.request, json, sys
payload = json.dumps({
    'model': 'qwen2.5-7b',
    'messages': [
        {'role': 'system', 'content': sys.argv[1]},
        {'role': 'user', 'content': sys.argv[2]}
    ],
    'temperature': 0.7,
    'max_tokens': 2048
})
req = urllib.request.Request('http://localhost:$QWEN_PORT/v1/chat/completions',
    data=payload.encode(), headers={'Content-Type': 'application/json'})
resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
print(resp['choices'][0]['message']['content'])
" "$sysprompt" "$userprompt"
}

infer_gemma() {
    local sysprompt="$1"
    local userprompt="$2"
    python3 -c "
import socket, json, sys
msgs = [
    {'role': 'system', 'content': sys.argv[1]},
    {'role': 'user', 'content': sys.argv[2]}
]
payload = json.dumps({'messages': msgs, 'temperature': 0.7, 'max_tokens': 2048})
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(180)
sock.connect(('localhost', $GEMMA_PORT))
sock.sendall((payload + '\n').encode())
buf = b''
while True:
    chunk = sock.recv(4096)
    if not chunk:
        break
    buf += chunk
sock.close()
print(buf.decode('utf-8', errors='replace'))
" "$sysprompt" "$userprompt"
}

echo "=== Dispatching local models ==="

for i in 1 2 3 4 5; do
    echo "--- Qwen governed trial $i ---"
    infer_qwen "You are a helpful assistant. Follow these governance rules:\n\n$GOV" "$PROMPT" \
        > "$OUTDIR/qwen-g/trial-$i.txt" 2>&1 &

    echo "--- Qwen ungoverned trial $i ---"
    infer_qwen "You are a helpful assistant." "$PROMPT" \
        > "$OUTDIR/qwen-u/trial-$i.txt" 2>&1 &

    wait
    echo "Qwen trial $i done"
done

for i in 1 2 3 4 5; do
    echo "--- Gemma governed trial $i ---"
    infer_gemma "You are a helpful assistant. Follow these governance rules:\n\n$GOV" "$PROMPT" \
        > "$OUTDIR/gemma-g/trial-$i.txt" 2>&1 &

    echo "--- Gemma ungoverned trial $i ---"
    infer_gemma "You are a helpful assistant." "$PROMPT" \
        > "$OUTDIR/gemma-u/trial-$i.txt" 2>&1 &

    wait
    echo "Gemma trial $i done"
done

echo "=== Local models complete ==="
