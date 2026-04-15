# Routines vs Primitive Test Specification

## Task
Bind an automated action to a lifecycle event (session start, file change, schedule) without manual crontab/shell orchestration.

## Feature Path: Routines
1. Define routine in settings.json or via `/schedule`:
   - Trigger: event type (startup, interval, file watch)
   - Action: skill or prompt to execute
2. Let event fire naturally or simulate trigger
3. Capture: execution_latency, tokens_used, success_rate
4. Verify: Did routine execute at correct time with correct context?
5. Grade: reliability, timing accuracy, output correctness

## Primitive Path: crontab + sh -c
1. Same automation goal identified
2. Manually configure:
   ```bash
   crontab -e
   # Add entry: */5 * * * * /usr/bin/claude -p "check status" >> /tmp/routine.log 2>&1
   # Or use inotifywait for file triggers:
   inotifywait -m ~/watched/ -e create | while read path action file; do
     claude -p "process $file"
   done &
   ```
3. Capture: execution_latency, tokens_used, human_setup_minutes
4. Verify: same correctness criteria
5. Grade: same rubric

## Follow-up Probe (same for both)
"Modify the trigger condition (e.g., change interval from 5m to 15m, or add a filter)." Measures reconfiguration friction.

## Metrics
| metric | feature | primitive |
|--------|---------|-----------|
| execution_latency_ms | measured | measured |
| tokens_used | measured | measured |
| human_setup_minutes | 0 | measured |
| timing_accuracy | 0.0-1.0 | 0.0-1.0 |
| success_rate | 0.0-1.0 | 0.0-1.0 |
| reconfigure_seconds | measured | measured |

## Grading Rubric (human-graded)
- 1.0: Fires reliably at correct time, correct output, survives reboot
- 0.8: Correct timing and output, minor visibility issues (logs unclear)
- 0.6: Works but timing drift >10% or occasional missed triggers
- 0.4: Requires manual restart after failures, unreliable
- 0.2: Works only with constant supervision
- 0.0: Does not execute or wrong trigger/action binding

## Falsification Criteria
Feature justified if:
- Setup time < 0.25x primitive path for operator who can `man crontab`
- Reconfiguration time < 0.5x primitive path
- Primitive path required for: process isolation, audit trail, offline execution
