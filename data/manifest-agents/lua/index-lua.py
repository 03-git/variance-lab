#!/usr/bin/env python3
"""Build FTS5/BM25 index for Lua corpus — same schema as manifest-agents rag.db."""
import os, sqlite3, glob

DB = "/tmp/lua-corpus/rag.db"
CORPUS = "/tmp/lua-corpus"
CHUNK = 40

if os.path.exists(DB):
    os.remove(DB)

conn = sqlite3.connect(DB)
conn.execute("CREATE VIRTUAL TABLE chunks USING fts5(path, chunk_id, content)")

files = sorted(glob.glob(f"{CORPUS}/*.c") + glob.glob(f"{CORPUS}/*.h") + [f"{CORPUS}/Makefile"])
total_chunks = 0

for fpath in files:
    fname = os.path.basename(fpath)
    with open(fpath) as f:
        lines = f.readlines()
    for i in range(0, len(lines), CHUNK):
        chunk_lines = lines[i:i+CHUNK]
        content = "".join(chunk_lines)
        chunk_id = i // CHUNK
        conn.execute("INSERT INTO chunks VALUES (?, ?, ?)", (fname, chunk_id, content))
        total_chunks += 1

conn.commit()
conn.close()
print(f"Indexed {len(files)} files, {total_chunks} chunks into {DB}")
