#!/bin/bash
set -euo pipefail
# rag-index.sh — chunk subtract.ing repo into sqlite FTS5 index
# Usage: ./rag-index.sh /path/to/repo /path/to/index.db

REPO="${1:-.}"
DB="${2:-/tmp/manifest-agents/rag.db}"

mkdir -p "$(dirname "$DB")"
rm -f "$DB"

python3 - "$REPO" "$DB" <<'PY'
import sqlite3, os, sys

repo = sys.argv[1]
db_path = sys.argv[2]
CHUNK = 40
OVERLAP = 5

con = sqlite3.connect(db_path)
con.execute("CREATE VIRTUAL TABLE chunks USING fts5(path, chunk_id, content, tokenize='porter unicode61')")

exts = {'.txt','.html','.md','.c','.h','.sh','.tsv','.ts','.conf'}
skip = {'stb_truetype.h'}
chunk_id = 0

for root, dirs, files in sorted(os.walk(repo)):
    dirs[:] = [d for d in dirs if d != '.git' and d != 'node_modules']
    for fname in sorted(files):
        if fname in skip:
            continue
        if os.path.splitext(fname)[1] not in exts:
            continue
        fpath = os.path.join(root, fname)
        relpath = os.path.relpath(fpath, repo)
        try:
            with open(fpath, 'r', errors='replace') as f:
                lines = f.readlines()
        except Exception:
            continue
        if not lines:
            continue
        start = 0
        while start < len(lines):
            end = min(start + CHUNK, len(lines))
            content = ''.join(lines[start:end])
            con.execute("INSERT INTO chunks(path, chunk_id, content) VALUES (?, ?, ?)",
                        (relpath, chunk_id, content))
            chunk_id += 1
            if end >= len(lines):
                break
            start = end - OVERLAP

con.commit()
count = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
print(f"Indexed {count} chunks from {repo} into {db_path}")
con.close()
PY
