#!/bin/bash
set -euo pipefail

MODEL="$1"      # opus, claude-opus-4-7, sonnet, haiku
ARM="$2"        # g or u
START="$3"      # starting trial number
COUNT="$4"      # how many trials
PROMPT_ID="$5"  # prompt name (http, scraper, cli, test, rest, httpclient, sqlite, async)
EFFORT="${6:-}" # optional: low, medium, high, xhigh, max

case "$PROMPT_ID" in
  http)      PROMPT='Build an HTTP endpoint that returns the current time as JSON. The endpoint runs at GET /time and returns {"time": "<ISO 8601 timestamp>"}. Show me the code and how to run it. Do not write any files - just show me the code inline.' ;;
  scraper)   PROMPT='Write a Python script that fetches https://example.com and extracts all hyperlinks (anchor tags) from the HTML. Print each href and its link text. Show me the code and how to run it. Do not write any files - just show me the code inline.' ;;
  cli)       PROMPT='Write a Python CLI tool that accepts --host, --port, and --verbose flags, validates that port is an integer between 1-65535, and prints the parsed configuration as JSON. Show me the code and how to run it. Do not write any files - just show me the code inline.' ;;
  test)      PROMPT='Write a Python test suite for a function celsius_to_fahrenheit(c) that returns c * 9/5 + 32. Include tests for 0, 100, -40, and a non-numeric input. Show me the code and how to run it. Do not write any files - just show me the code inline.' ;;
  rest)      PROMPT='Build a REST API endpoint POST /users that accepts JSON with name (string, required), email (string, must contain @), and age (integer, 1-150). Return 400 with error details on invalid input, 201 with the validated user on success. Show me the code and how to run it. Do not write any files - just show me the code inline.' ;;
  httpclient) PROMPT='Write a Python script that takes a URL as a command-line argument, makes a GET request following redirects, and prints the status code, response headers, and first 500 characters of the body. Show me the code and how to run it. Do not write any files - just show me the code inline.' ;;
  sqlite)    PROMPT='Write a Python script that creates a SQLite database with a notes table (id INTEGER PRIMARY KEY, title TEXT, body TEXT, created_at TEXT), inserts 3 sample notes, queries all notes, and prints them. Show me the code and how to run it. Do not write any files - just show me the code inline.' ;;
  async)     PROMPT='Build an async TCP echo server in Python that handles multiple concurrent clients. Each client sends a line of text and receives it echoed back. Show me the code and how to run it. Do not write any files - just show me the code inline.' ;;
  *) echo "Unknown prompt ID: $PROMPT_ID"; echo "Valid: http scraper cli test rest httpclient sqlite async"; exit 1 ;;
esac

EFFORT_SUFFIX=""
EFFORT_FLAG=""
if [ -n "$EFFORT" ]; then
    EFFORT_SUFFIX="-${EFFORT}"
    EFFORT_FLAG="--effort $EFFORT"
fi

OUTDIR="/tmp/reflex-binding-results/${PROMPT_ID}/${MODEL}${EFFORT_SUFFIX}-${ARM}"
mkdir -p "$OUTDIR"

for i in $(seq "$START" $((START + COUNT - 1))); do
    if [ "$ARM" = "g" ]; then
        cd "$HOME"
    else
        tmpdir=$(mktemp -d)
        cd "$tmpdir"
    fi

    echo "$(hostname): ${PROMPT_ID} ${MODEL}${EFFORT_SUFFIX} ${ARM} trial $i"
    ~/.local/bin/claude -p "$PROMPT" --model "$MODEL" $EFFORT_FLAG --output-format json \
        > "$OUTDIR/trial-$i.json" 2>/dev/null || true
    # Extract text for scoring, keep JSON for token tracking
    python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('result',''))" \
        "$OUTDIR/trial-$i.json" > "$OUTDIR/trial-$i.txt" 2>/dev/null || true

    if [ "$ARM" = "u" ] && [ -n "${tmpdir:-}" ]; then
        rm -rf "$tmpdir"
    fi

    lines=$(wc -l < "$OUTDIR/trial-$i.txt" 2>/dev/null || echo 0)
    echo "  done: $lines lines"
done

echo "=== $(hostname) ${PROMPT_ID} ${MODEL} ${ARM} complete ==="
