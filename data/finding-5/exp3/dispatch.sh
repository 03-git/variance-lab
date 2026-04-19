#!/bin/bash
set -u
mkdir -p /tmp/exp3
scp /tmp/exp3-spec.md rousseau:/tmp/exp3-spec.md
scp ~/human/via-negativa/audit8/*.md rousseau:/tmp/audit8/ 2>/dev/null
ssh rousseau "cat > /tmp/exp3-prompt.md << 'PROMPT'
Perform the analysis specified in /tmp/exp3-spec.md. Read the spec in full. Read the data sources named in the spec (voter files, synthesis, decision-synth, execute.out, methodology URL).

Produce /tmp/exp3/report.md with:
1. Per-finding (F1-F4) gate-only verdict derivation: which gates pass, which fail, what the gate-only-derived verdict is.
2. Deliberative verdict from synthesis/decision-synth.
3. Divergence classification: concordant / deliberative stricter / deliberative looser.
4. For each divergent case, name the voter(s) whose unique signal drove the deliberative verdict.
5. Secondary: voter-level unique-catch tally.
6. Pre-committed prediction outcome statement.

Terse. No preamble. No scope creep. Do not propose new experiments. Do not rewrite the findings. Answer the spec questions.
PROMPT
mkdir -p /tmp/exp3
CLAUDE_CODE_EFFORT_LEVEL=high claude -p --model claude-opus-4-7 < /tmp/exp3-prompt.md > /tmp/exp3/report.md 2> /tmp/exp3/err"
