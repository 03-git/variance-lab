#!/usr/bin/env python3
"""retrieve.py — BM25 retrieval from FTS5 index."""
import sqlite3, sys

db_path = sys.argv[1]
question = sys.argv[2]
output_file = sys.argv[3]
top_k = int(sys.argv[4]) if len(sys.argv) > 4 else 12

words = ''.join(c if c.isalnum() else ' ' for c in question).split()
stop = {'what','which','how','does','the','and','are','for','from','that',
        'this','with','each','one','all','its','has','was','is','in','of',
        'to','do','a','an','it','be','list','every','file','files','describe',
        'between','not','or','by'}
terms = [w for w in words if w.lower() not in stop and len(w) > 1]

if not terms:
    terms = words[:5]

fts_query = ' OR '.join(f'"{t}"' for t in terms)

con = sqlite3.connect(db_path)
try:
    rows = con.execute(
        "SELECT path, content FROM chunks WHERE chunks MATCH ? ORDER BY rank LIMIT ?",
        (fts_query, top_k)
    ).fetchall()
except Exception:
    fts_query = ' OR '.join(f'"{t}"' for t in terms[:3])
    try:
        rows = con.execute(
            "SELECT path, content FROM chunks WHERE chunks MATCH ? ORDER BY rank LIMIT ?",
            (fts_query, top_k)
        ).fetchall()
    except Exception:
        rows = []
con.close()

with open(output_file, 'w') as f:
    f.write("## Retrieved chunks (BM25, top-{})\n\n".format(top_k))
    for i, (path, content) in enumerate(rows, 1):
        f.write(f"### Chunk {i} (from {path})\n{content}\n\n")
    if not rows:
        f.write("(No matching chunks found)\n")
