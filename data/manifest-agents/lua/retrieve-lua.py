#!/usr/bin/env python3
"""BM25 retrieval for Lua corpus — matches manifest-agents retrieve.py interface."""
import sqlite3, sys

db_path = sys.argv[1]
question = sys.argv[2]
out_path = sys.argv[3]
max_chunks = int(sys.argv[4]) if len(sys.argv) > 4 else 12

conn = sqlite3.connect(db_path)

tokens = []
for w in question.lower().split():
    w = ''.join(c for c in w if c.isalnum())
    if len(w) > 2 and w not in {'what', 'which', 'how', 'does', 'the', 'and', 'are', 'for', 'from', 'that', 'this', 'with', 'each'}:
        tokens.append(w)

if not tokens:
    tokens = [w for w in question.lower().split() if len(w) > 1]

query = " OR ".join(tokens[:10])

rows = conn.execute(
    "SELECT path, chunk_id, content, rank FROM chunks WHERE chunks MATCH ? ORDER BY rank LIMIT ?",
    (query, max_chunks)
).fetchall()

with open(out_path, 'w') as f:
    for path, chunk_id, content, rank in rows:
        start = chunk_id * 40 + 1
        end = start + content.count('\n') - 1
        f.write(f"\n## {path} (lines {start}-{end})\n")
        f.write(content)

conn.close()
