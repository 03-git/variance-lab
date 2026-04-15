# /loop vs Primitive Test Specification

## Task
Monitor a process, poll for state changes, or execute recurring work until a condition is met or the user intervenes.

## Feature Path: /loop
1. Start a background process: `npm run build` or `docker-compose up`
2. Invoke `/loop 30s check build status and report errors`
3. Capture: loop_count, total_wall_seconds, token_cost_per_iteration, condition_detected_at
4. Observe: did agent self-pace appropriately, or burn tokens polling too fast?
5. Grade: did loop terminate correctly when condition met?

## Primitive Path: cron/watch/at
1. Same background process
2. Set up monitoring with primitives:
   ```bash
   # Option A: watch (interactive)
   watch -n 30 'tail -5 build.log | grep -E "error|success"'
   
   # Option B: cron (persistent)
   echo "*/1 * * * * tail -5 ~/build.log >> ~/build-status.txt" | crontab -
   
   # Option C: at (one-shot delayed)
   echo "tail -20 build.log | mail -s 'build status' user" | at now + 5 minutes
   ```
3. Human monitors output and decides when to intervene
4. Capture: setup_seconds, check_count, human_intervention_count, total_wall_seconds
5. Grade: did primitive setup detect condition and surface it appropriately?

## Test Scenarios (use same scenario across both paths)
- Short poll: "Tell me when the test suite finishes" (~2-5 min expected)
- Long poll: "Alert me when disk usage drops below 80%" (hours)
- Conditional: "Keep deploying to staging until health check passes, max 5 tries"

## Metrics
| metric | feature | primitive |
|--------|---------|-----------|
| setup_seconds | 0 | measured |
| iterations | measured | measured |
| token_cost | measured | 0 |
| wall_seconds | measured | measured |
| human_interventions | measured | measured |
| condition_detected | true/false | true/false |
| detection_latency_seconds | measured | measured |

## Grading Rubric (human-graded)
- 1.0: Condition detected within one interval, clean exit, no false positives
- 0.8: Condition detected, minor delay or one unnecessary iteration
- 0.6: Condition detected, but >3 unnecessary iterations or manual stop needed
- 0.4: Condition missed on first pass, caught on retry
- 0.2: Loop ran indefinitely, required human kill
- 0.0: Loop never detected condition or caused system issues (runaway process)

## Falsification Criteria
Feature justified if:
- setup_time_primitive > 60 seconds for operator who can `man crontab`
- Feature reduces human_interventions by >50% vs primitive monitoring
- Token cost per iteration < human context-switch cost (assume 30s minimum)
- Detection latency within 2x of primitive polling interval
