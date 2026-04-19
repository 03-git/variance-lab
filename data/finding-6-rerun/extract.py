#!/usr/bin/env python3
# rubric_commit: 49d86f7
# rubric_path: findings/interaction-mode-variance-rubric.md
#
# Fallback to python3 (stdlib only): jq pipeline would require multi-pass
# per-file state (model set, token sums, human-turn stripping, correction
# matching) that cannot be expressed readably in a single jq invocation.
# awk could accumulate state but the stripping logic (regex XML removal,
# compaction preamble, block-type filtering) crosses the readable threshold.

import sys
import os
import json
import re
import argparse
from datetime import datetime, timezone

CORRECTION_PATTERN = re.compile(
    r'\b(no|don\'t|do not|stop|wrong|not that|actually|wait|cancel|undo|revert|incorrect|fix|redo)\b'
    r'|that\'s wrong|that is wrong',
    re.IGNORECASE
)

STRIP_TAGS = re.compile(
    r'<(system-reminder|command-message|command-name|local-command-stdout|session-restore|stderr)>'
    r'.*?</\1>',
    re.DOTALL
)

COMPACTION_PREAMBLE = re.compile(
    r'^This session is being continued from a previous conversation.*?(?=\n\n|\Z)',
    re.DOTALL
)

HEADER = (
    'session_id\tproject\tmodel_id\thuman_turns\tmode\ttotal_input_tokens\t'
    'total_output_tokens\ttotal_tokens\ttool_calls\tcorrection_flag_count\t'
    'duration_utc_seconds\tutc_start\tutc_end\tmixed_model\tqualifying'
)


def strip_human_text(content):
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                parts.append(block.get('text', ''))
        text = ''.join(parts)
    else:
        return ''
    text = STRIP_TAGS.sub('', text)
    text = COMPACTION_PREAMBLE.sub('', text)
    return text.strip()


def ts_to_dt(ts):
    if ts is None:
        return None
    try:
        s = ts.rstrip('Z')
        if '.' in s:
            dt = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
        else:
            dt = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        try:
            return datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except Exception:
            return None


def fmt_dt(dt):
    if dt is None:
        return ''
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def mode_from_turns(n):
    if n <= 1:
        return 'pipe'
    elif n <= 3:
        return 'governor'
    elif n <= 15:
        return 'collaborator'
    else:
        return 'passenger'


def process_file(filepath, corpus_root):
    rel = os.path.relpath(filepath, corpus_root)
    parts = rel.split(os.sep)
    project = parts[0] if len(parts) > 1 else ''
    session_id = '/'.join(parts)

    blank = {
        'session_id': session_id,
        'project': project,
        'model_id': '',
        'human_turns': 0,
        'mode': 'pipe',
        'total_input_tokens': 0,
        'total_output_tokens': 0,
        'total_tokens': 0,
        'tool_calls': 0,
        'correction_flag_count': 0,
        'duration_utc_seconds': 0,
        'utc_start': '',
        'utc_end': '',
        'mixed_model': 0,
        'qualifying': 0,
    }

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            raw = f.read()
    except Exception:
        return blank

    lines = [l for l in raw.splitlines() if l.strip()]
    if not lines:
        return blank

    human_turns = 0
    correction_count = 0
    total_input = 0
    total_output = 0
    tool_calls = 0
    models = []
    timestamps = []
    has_assistant = False

    for line in lines:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        ts = obj.get('timestamp')
        if ts:
            dt = ts_to_dt(ts)
            if dt:
                timestamps.append(dt)

        typ = obj.get('type')

        if typ == 'user':
            msg = obj.get('message', {})
            content = msg.get('content', '')
            text = strip_human_text(content)
            if text:
                human_turns += 1
                if CORRECTION_PATTERN.search(text):
                    correction_count += 1

        elif typ == 'assistant':
            has_assistant = True
            msg = obj.get('message', {})
            model = msg.get('model')
            if model:
                models.append(model)
            usage = msg.get('usage', {})
            total_input += usage.get('input_tokens', 0) or 0
            total_output += usage.get('output_tokens', 0) or 0
            content = msg.get('content', [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'tool_use':
                        tool_calls += 1

    model_set = list(dict.fromkeys(models))
    first_model = model_set[0] if model_set else ''
    mixed = 1 if len(model_set) > 1 else 0

    utc_start = min(timestamps) if timestamps else None
    utc_end = max(timestamps) if timestamps else None
    duration = int((utc_end - utc_start).total_seconds()) if (utc_start and utc_end) else 0

    qualifying = 1 if (human_turns >= 1 and has_assistant) else 0
    mode = mode_from_turns(human_turns)
    total_tokens = total_input + total_output

    return {
        'session_id': session_id,
        'project': project,
        'model_id': first_model,
        'human_turns': human_turns,
        'mode': mode,
        'total_input_tokens': total_input,
        'total_output_tokens': total_output,
        'total_tokens': total_tokens,
        'tool_calls': tool_calls,
        'correction_flag_count': correction_count,
        'duration_utc_seconds': duration,
        'utc_start': fmt_dt(utc_start),
        'utc_end': fmt_dt(utc_end),
        'mixed_model': mixed,
        'qualifying': qualifying,
    }


def row(r):
    return '\t'.join(str(r[k]) for k in [
        'session_id', 'project', 'model_id', 'human_turns', 'mode',
        'total_input_tokens', 'total_output_tokens', 'total_tokens',
        'tool_calls', 'correction_flag_count', 'duration_utc_seconds',
        'utc_start', 'utc_end', 'mixed_model', 'qualifying',
    ])


def collect_jsonl(corpus_root):
    paths = []
    for dirpath, dirnames, filenames in os.walk(corpus_root):
        dirnames.sort()
        for fn in sorted(filenames):
            if fn.endswith('.jsonl'):
                paths.append(os.path.join(dirpath, fn))
    return sorted(paths)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('corpus_root')
    parser.add_argument('output_tsv')
    args = parser.parse_args()

    corpus_root = os.path.abspath(args.corpus_root)
    files = collect_jsonl(corpus_root)

    rows = []
    for fp in files:
        rows.append(process_file(fp, corpus_root))

    try:
        with open(args.output_tsv, 'w', encoding='utf-8') as out:
            out.write(HEADER + '\n')
            for r in rows:
                out.write(row(r) + '\n')
    except Exception as e:
        print(f'ERROR writing output: {e}', file=sys.stderr)
        sys.exit(1)

    qualifying = sum(r['qualifying'] for r in rows)
    total = len(rows)
    print(f'extracted {qualifying} qualifying / {total} total sessions -> {args.output_tsv}', file=sys.stderr)
    sys.exit(0)


if __name__ == '__main__':
    main()
