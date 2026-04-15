# /effort vs Primitive Test Specification

## Task
Given a task of unknown complexity, allocate appropriate agent effort (T1=quick, T2=medium, T4=heavy) without over- or under-committing resources.

## Feature Path: /effort
1. Present task without stating complexity: "Fix the auth middleware session handling"
2. Invoke `/effort` to let agent assess and auto-escalate
3. Capture: initial_tier, final_tier, escalation_count, wall_seconds, token_cost
4. Observe: did agent start minimal and escalate only when blocked, or over-allocate upfront?
5. Grade: was effort proportional to actual task complexity?

## Primitive Path: Manual Tiering
1. Same task presentation
2. Human pre-assesses complexity by reading relevant code:
   ```bash
   git log --oneline -10 -- src/auth/
   wc -l src/auth/*.ts
   grep -c "session" src/auth/*.ts
   ```
3. Human explicitly instructs: "This is a T2 task, don't spend more than 30 minutes"
4. If agent hits limit, human re-assesses and re-tiers
5. Capture: human_assessment_minutes, tiers_assigned, total_wall_seconds, token_cost
6. Grade: was human tiering accurate, and was total effort proportional?

## Calibration Tasks (use same task across both paths)
- T1 expected: "Add a log line when session expires"
- T2 expected: "Add session refresh before expiry"
- T4 expected: "Migrate session storage from cookies to Redis"

## Metrics
| metric | feature | primitive |
|--------|---------|-----------|
| initial_tier | measured | human-assigned |
| final_tier | measured | human-assigned |
| escalation_count | measured | measured |
| wall_seconds | measured | measured |
| token_cost | measured | measured |
| human_effort_minutes | 0 | measured |
| effort_accuracy | 0.0-1.0 | 0.0-1.0 |

## Grading Rubric (human-graded)
- 1.0: Correct tier from start, no wasted effort, task completed
- 0.8: Started one tier low, escalated appropriately, completed
- 0.6: Started one tier high (over-allocated) or needed 2+ escalations
- 0.4: Significant over/under-allocation, but task completed
- 0.2: Wrong tier caused thrash or timeout, partial completion
- 0.0: Effort completely misaligned, task failed

## Falsification Criteria
Feature justified if:
- effort_accuracy_delta > 0.2 compared to human tiering
- Human pre-assessment takes >5 minutes for operator familiar with codebase
- Feature prevents >50% of unnecessary T4 escalations on T1 tasks
