# /simplify vs Primitive Test Specification

## Task
After introducing a feature across multiple files, review changed code for reuse opportunities, quality issues, and inefficiency, then fix any issues found.

## Feature Path: /simplify
1. Complete a multi-file feature (3+ files changed, 100+ lines added)
2. Invoke `/simplify`
3. Capture: files_reviewed, issues_found, issues_fixed, wall_seconds, tokens_used
4. Inspect each fix: was it correct? Was it necessary?
5. Grade: did the changes improve the code without introducing regressions?

## Primitive Path: xargs + parallel + manual review
1. Same multi-file feature completed
2. Review with:
   ```bash
   git diff --stat HEAD~1
   git diff HEAD~1 -- '*.py' '*.ts' | cat
   # Human reads diff, identifies duplication / dead code / inefficiency
   # Human applies fixes manually or via sed/awk
   ```
3. Optionally parallelize lint/check across files:
   ```bash
   git diff --name-only HEAD~1 | xargs -P4 -I{} sh -c 'echo "=== {} ===" && cat {}'
   ```
4. Capture: files_reviewed, issues_found, issues_fixed, wall_seconds, human_effort_minutes
5. Grade: did manual review catch the same issues?

## Follow-up Probe (same for both)
Introduce a subtle regression in one of the "simplified" files (e.g., remove a needed null check). Run the test suite. Did the simplification path leave the code in a state where regressions are easier or harder to detect?

## Metrics
| metric | feature | primitive |
|--------|---------|-----------|
| files_reviewed | measured | measured |
| issues_found | measured | measured |
| issues_fixed | measured | measured |
| false_positives | counted | counted |
| regressions_introduced | counted | counted |
| wall_seconds | measured | measured |
| human_effort_minutes | 0 | measured |
| tokens_used | measured | 0 |

## Grading Rubric (human-graded)
- 1.0: All real issues found, no false positives, no regressions, code strictly better
- 0.8: Most issues found, <=1 false positive, no regressions
- 0.6: Some issues found, minor false positives or unnecessary churn
- 0.4: Few issues found, or a regression introduced by a "simplification"
- 0.2: More harm than help — regressions or semantic changes masked as simplification
- 0.0: Total failure — code broken or review missed obvious problems

## Falsification Criteria
Feature justified if:
- issues_found(feature) >= issues_found(primitive) AND regressions_introduced == 0
- Primitive path takes >5x longer for operator fluent in `diff`, `grep`, `xargs`
