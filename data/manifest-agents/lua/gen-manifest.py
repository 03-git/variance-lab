#!/usr/bin/env python3
"""Generate curated manifest for Lua corpus via claude -p."""
import subprocess, os, glob

CORPUS = "/tmp/lua-corpus"
files = sorted(glob.glob(f"{CORPUS}/*.c") + glob.glob(f"{CORPUS}/*.h") + [f"{CORPUS}/Makefile"])

file_summaries = []
for fpath in files:
    fname = os.path.basename(fpath)
    with open(fpath) as f:
        lines = f.readlines()
    head = "".join(lines[:30])
    file_summaries.append(f"=== {fname} ({len(lines)} lines) ===\n{head}\n")

context = "\n".join(file_summaries)

prompt = f"""You are analyzing the Lua 5.4 source code. Generate a curated manifest in TSV format.
Each line: path<TAB>[tag]<TAB>description

Tags should categorize by subsystem: [parser], [compiler], [vm], [gc], [api], [stdlib], [debug], [io], [core], [build], [string], [table], [math], [coroutine], [memory], [aux].

For each file, write a specific 1-line description of what it does — not generic, cite key functions or data structures.

Output ONLY the TSV lines, no headers, no markdown fences.

Here are the first 30 lines of each file:

{context}"""

result = subprocess.run(
    [os.path.expanduser("~/.local/bin/claude"), "-p", "--model", "claude-sonnet-4-6"],
    input=prompt, capture_output=True, text=True,
    env={**os.environ, "CLAUDE_CODE_EFFORT_LEVEL": "low"}
)

out = result.stdout.strip()
# Clean any markdown fences
lines = []
for line in out.split('\n'):
    line = line.strip()
    if line.startswith('```') or not line:
        continue
    lines.append(line)

with open(f"{CORPUS}/curated-manifest.tsv", 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f"Wrote {len(lines)} manifest entries")
