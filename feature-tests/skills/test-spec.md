# Skills vs Primitive Test Specification

## Task
Execute a reusable, domain-specific prompt sequence (e.g., code review, commit generation) without manual prompt assembly each invocation.

## Feature Path: Skills
1. Identify a repeatable task pattern (e.g., `/commit`, `/review-pr`)
2. Invoke the skill with arguments: `/commit` or `Skill tool`
3. Capture: tokens_used, wall_seconds, output_quality
4. Verify: Did the skill produce a correctly-formatted result?
5. Grade: correctness, adherence to conventions, human edit distance

## Primitive Path: exec + CLAUDE.md + cat
1. Same task pattern identified
2. Manually construct the prompt:
   ```bash
   cat ~/.claude/prompts/commit-template.txt
   # Paste template into session
   # Manually invoke: git diff, git log, etc.
   # Assemble commit message by hand following template
   ```
3. Capture: tokens_used, wall_seconds, human_effort_minutes
4. Verify: same correctness criteria
5. Grade: same rubric

## Follow-up Probe (same for both)
"Modify the previous output to follow a different convention (e.g., Conventional Commits instead of freeform)." Measures how much context the path retains for iteration.

## Metrics
| metric | feature | primitive |
|--------|---------|-----------|
| tokens_used | measured | measured |
| wall_seconds | measured | measured |
| human_effort_minutes | 0 | measured |
| output_correctness | 0.0-1.0 | 0.0-1.0 |
| edit_distance_to_ideal | measured | measured |

## Grading Rubric (human-graded)
- 1.0: Output ready to use, no edits required, follows all conventions
- 0.8: Minor edits (typos, formatting), functionally correct
- 0.6: Correct structure, content requires human refinement
- 0.4: Partially usable, significant human intervention needed
- 0.2: Wrong format or conventions, must rewrite
- 0.0: Output unusable or skill failed to execute

## Falsification Criteria
Feature justified if:
- Time to correct output < 0.5x primitive path time for operator who knows the template
- Error rate (need to rerun) < primitive path error rate
- Source inspection available via `cat skill-definition` if determinism required
