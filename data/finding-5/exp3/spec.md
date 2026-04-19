# Experiment 3: deliberative-pass independence test

**Pre-committed:** 2026-04-19 UTC
**Signer:** hodori@subtract.ing
**Hypothesis:** The 8-voter deliberative pass in the handler methodology produces conclusions that diverge non-trivially from what a gate-only (static rubric + functional verification) scoring would produce. If deliberation just ratifies the rubric, it can be dropped. If it catches what gates miss, it is load-bearing.

## Treatment

Retrospective analysis on existing exp 5 (editorial audit) voter outputs. No new model calls for the primary analysis.

- **Arm Gate-only:** For each of the four findings audited in exp 5, derive the verdict (EDITORIAL vs RERUN) from the rubric gate-check alone. A finding passes all gates → EDITORIAL. A finding fails any gate → RERUN.
- **Arm Deliberative:** The actual verdict produced by the 8-voter synthesis in exp 5 (sonnet-4-6 low consolidation of all eight voter outputs).

Compare verdicts per finding and identify cases where the two methods diverge.

## Measurement

1. Per finding (F1 delegated-agent-authorization-gap, F2 delegation-finding, F3 interaction-mode-variance, F4 three-questions):
   - Gate-only verdict: EDITORIAL if all mandatory gates pass, RERUN if any gate fails. Use the verdict rubric from handler methodology.
   - Deliberative verdict: from `~/human/via-negativa/audit8/synthesis.md` and `decision-synth.md`.
2. Count divergences. Categorize each:
   - **Concordant** — gate-only and deliberative agree on verdict.
   - **Deliberative stricter** — gate-only says EDITORIAL, deliberative says RERUN (deliberation caught something gates missed).
   - **Deliberative looser** — gate-only says RERUN, deliberative says EDITORIAL (deliberation overrode a gate fail).
3. For each divergent case, identify the specific voter(s) whose unique signal drove the deliberative verdict.
4. If divergences exist: deliberation is load-bearing. If concordance is total: deliberation ratifies the rubric and could be dropped.

## Pre-committed predictions

- **Concordance ≥ 3/4 findings:** deliberation largely ratifies the rubric; marginal value.
- **Concordance < 3/4 findings:** deliberation is load-bearing; keep it.
- **At least one "deliberative stricter" case:** deliberation catches what gates miss; strongly supports keeping it.

## Secondary measurement (voter-level)

For each voter in the exp 5 panel, count unique catches (edits proposed by that voter alone, 1/8). Tally per model / effort level. If certain voter configurations (e.g., sonnet-4-5-low) consistently produce unique catches, that's data on which configurations the deliberative pass benefits most from including.

## Data sources

- `~/human/via-negativa/audit8/voter{1..8}.out.md` — eight voter outputs
- `~/human/via-negativa/audit8/synthesis.md` — consolidated edit list
- `~/human/via-negativa/audit8/decision-synth.md` — ship-decision verdict
- `/tmp/audit8/execute.out.md` on rousseau — what was actually executed
- Methodology gate definitions: https://subtract.ing/variance-lab-handler-methodology.txt

## Harness (no new model calls)

This experiment does not require a trial loop. It requires analysis of existing data. Appropriate dispatch: rousseau opus-4-7 high reads the above sources, produces a report.

Harness script: a shell wrapper that copies the audit8 artifacts + methodology into a dispatch prompt, sends to rousseau, saves the report.

## Outputs

- `/tmp/exp3/report.md` — per-finding gate-only verdict, deliberative verdict, divergences, voter unique-catch tally, pre-committed prediction outcome.
