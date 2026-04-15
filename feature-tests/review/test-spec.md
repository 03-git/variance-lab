# /review vs Primitive Test Specification

## Task
Review code changes (staged, committed, or PR) and surface issues, patterns, or context relevant to merge decision.

## Feature Path: /review
1. Stage or commit changes spanning 3+ files, 100+ lines
2. Invoke `/review` or `/review PR#123`
3. Capture: files_reviewed, lines_analyzed, issues_found, wall_seconds, token_cost
4. Observe: did agent surface non-obvious issues (logic bugs, missing edge cases) or only lint-level noise?
5. Grade: were findings actionable and load-bearing?

## Primitive Path: diff + git log
1. Same changes staged or committed
2. Review with primitives:
   ```bash
   # See what changed
   git diff --stat HEAD~1
   git diff HEAD~1 -- src/
   
   # Understand context
   git log --oneline -10 -- path/to/changed/file
   git blame -L 50,70 path/to/changed/file
   
   # Check for patterns
   git log --grep="similar-feature" --oneline
   ```
3. Human reads diff, traces through code, identifies issues
4. Capture: commands_run, human_review_minutes, issues_found
5. Grade: were findings actionable and load-bearing?

## Test Scenarios (use same changeset across both paths)
- Simple: 1 file, 20 lines, obvious fix (expect: "LGTM" or minor style note)
- Medium: 3 files, 100 lines, refactor (expect: note on breaking changes, test coverage)
- Complex: 10 files, 500 lines, new feature (expect: architecture concerns, edge cases, integration risks)

## Metrics
| metric | feature | primitive |
|--------|---------|-----------|
| files_reviewed | measured | measured |
| lines_analyzed | measured | measured |
| wall_seconds | measured | measured |
| token_cost | measured | 0 |
| human_effort_minutes | 0 | measured |
| issues_found | counted | counted |
| issues_actionable | 0.0-1.0 | 0.0-1.0 |
| issues_missed | counted | counted |

## Grading Rubric (human-graded)
- 1.0: All load-bearing issues found, no false positives, clear summary
- 0.8: Major issues found, 1-2 minor misses, minimal noise
- 0.6: Most issues found, but >30% noise (non-actionable findings)
- 0.4: Missed a major issue, or >50% noise
- 0.2: Review surface-level only (lint, style), missed logic issues
- 0.0: Review actively misleading or missed critical security/correctness bug

## Follow-up Probe (same for both)
After review, ask: "Would you merge this as-is, and what's the one thing that would block you?"
Compare answer quality: does it reflect actual code understanding or pattern-matching?

## Falsification Criteria
Feature justified if:
- human_effort_minutes > 10 for changeset primitive review
- Feature finds >1 issue human missed (verified by later bug/incident)
- Actionable issue rate > 70% (noise floor)
- For PRs: feature surfaces relevant git history human would have missed
