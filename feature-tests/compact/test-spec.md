# /compact vs Primitive Test Specification

## Task
After a session with 50k+ tokens of context, reduce context while preserving essential information for continued work.

## Feature Path: /compact
1. Accumulate context (tool calls, code reads, discussion) until context exceeds 50k tokens
2. Invoke `/compact`
3. Capture: tokens_before, tokens_after, wall_seconds, output_summary
4. Continue with a follow-up task requiring prior context
5. Grade: did the model retain load-bearing context?

## Primitive Path: Session Discipline
1. Same context accumulation
2. Manually inspect with:
   ```bash
   wc -l < session.jsonl
   head -100 session.jsonl > head.txt
   tail -100 session.jsonl > tail.txt
   # Human decides what to keep
   ```
3. Start new session, manually paste retained context
4. Capture: tokens_preserved, wall_seconds, human_effort_minutes
5. Continue with same follow-up task
6. Grade: did manual selection retain load-bearing context?

## Follow-up Probe (same for both)
Ask: "What was the specific error message from the third file we edited?" (or similar recall question requiring mid-session context)

## Metrics
| metric | feature | primitive |
|--------|---------|-----------|
| tokens_in | measured | measured |
| tokens_out | measured | measured |
| wall_seconds | measured | measured |
| human_effort_minutes | 0 | measured |
| recall_accuracy | 0.0-1.0 | 0.0-1.0 |

## Grading Rubric (human-graded)
- 1.0: Perfect recall of probe answer + retains all structural context
- 0.8: Correct probe answer, minor structural gaps
- 0.6: Partial probe answer, some important context lost
- 0.4: Wrong probe answer, but session continues functionally
- 0.2: Session effectively lost, needs restart
- 0.0: Total failure, cannot continue

## Falsification Criteria
Feature justified if:
- quality_delta > 2x cost_delta (where cost = tokens + human_effort converted)
- Primitive setup takes >10x longer for operator who can `man tmux`
