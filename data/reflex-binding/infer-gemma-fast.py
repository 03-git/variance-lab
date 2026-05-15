#!/usr/bin/env python3
import socket, json, sys, time

system_prompt = sys.argv[1] if len(sys.argv) > 1 else ""
user_prompt = sys.argv[2] if len(sys.argv) > 2 else ""

msgs = []
if system_prompt:
    msgs.append({"role": "system", "content": system_prompt})
msgs.append({"role": "user", "content": user_prompt})

payload = json.dumps({"messages": msgs, "temperature": 0.7, "max_tokens": 512})

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(600)
sock.connect(("localhost", 8087))
sock.sendall((payload + "\n").encode())

buf = b""
while True:
    try:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    except socket.timeout:
        break
sock.close()

text = buf.decode("utf-8", errors="replace")
try:
    resp = json.loads(text)
    content = resp["choices"][0]["message"]["content"]
    if "<channel|>" in content:
        content = content.split("<channel|>", 1)[-1]
    print(content)
except (json.JSONDecodeError, KeyError, IndexError):
    print(text)
