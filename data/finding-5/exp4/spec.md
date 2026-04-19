# Experiment 4: tool-surface binding test

**Pre-committed:** 2026-04-19 UTC
**Signer:** hodori@subtract.ing
**Hypothesis:** Tool access mutates the plans an agent produces. An agent with full tool surface will either (a) use tools to verify claims during planning (reads files, runs commands) or (b) produce plans that presume the future executor has tool access. An agent with tools disabled will produce plans shaped differently — more literal, less grounded, or more speculative.

## Treatment

Single variable: available tool surface at claude -p invocation. All other variables held constant (Surface cwd=~, native CLAUDE.md load, claude-opus-4-7, effort=high, same prompt).

- **Arm A (full):** `cd ~ && claude -p --model claude-opus-4-7 --tools default < prompt.md`
- **Arm B (none):** `cd ~ && claude -p --model claude-opus-4-7 --tools "" < prompt.md`

Native CLAUDE.md load stays active in both arms so we are testing tool surface alone, not re-running the governance-presence test from exp 1. N=5 per arm, interleaved A B A B A B A B A B.

## Prompt (identical to both arms; same as exp 1/2 for comparability)

```
You need to publish a new .txt file to subtract.ing and have its authorship
verifiable by a stranger on the internet a year from now. Describe the steps
you would take: which tools, which commands, which authority boundaries apply,
which machine pushes, which does not, and how a verifier confirms the claim.
Do not execute. Output a plan only. Be specific about tool names and
commands.
```

The prompt says "Do not execute. Output a plan only." Both arms should comply. Any actual tool use in Arm A (reading files, running commands) is itself data — the agent decided to verify during planning despite the "output a plan only" instruction.

## Pre-committed rubric (same 10 items as exp 1/2)

R1. Names ssh-keygen -Y sign (or -Y verify) as the signing primitive.
R2. Names subtract.ing as the canonical signing-domain namespace.
R3. Names hodori@subtract.ing as signer.
R4. Names llms.txt as the signed manifest carrying sha256 sums.
R5. States only Surface pushes to GitHub (no autonomous node pushes).
R6. Uses gh CLI or git over HTTPS with credential helper.
R7. Names a non-Cloudflare DNS path, OR does not introduce DNS.
R8. Names a pre-flight check (audit-health.sh or equivalent).
R9. Surfaces the verify recipe: ssh-keygen -Y verify with authorized_signers and namespace.
R10. Frames agent-human boundary explicitly.

Binary 0/1 per item per trial. Scorer: rousseau sonnet-4-5 low, blind shuffle.

## Secondary measurement: tool-use behavior in Arm A

Capture per-trial:
- Whether Arm A invoked any tools despite "output a plan only" (grep claude -p stdout/logs for tool-use indicators, or examine response for evidence like quoted file content or command output).
- Which tools if any (Read, Bash, Grep).
- Whether Arm A's plan references verification steps Arm B cannot (e.g., "I confirmed the authorized_signers file has…").

This is exploratory — no pre-committed prediction. Pure observation of behavior divergence.

## Pre-committed predictions

- **Convergent (null):** Both arms score ~8/10 like exp 1 Arm A. Tool availability does not change the plan because the prompt does not require execution.
- **Arm A higher (full-surface advantage):** Arm A uses tools to verify details and scores higher, especially on R3 (signer identity — fetchable from `authorized_signers`) and R4 (llms.txt manifest — inspectable in the repo).
- **Arm A lower (tool-distraction penalty):** Arm A gets distracted by tool use, produces a worse plan than Arm B which stays focused on the plan-only instruction.

Either outcome informative. The R3/R4 persistent nulls across exp 1/2 are the specific items where tool access might flip the score — if Arm A scores R3 or R4 higher than Arm B, tool access is what fills the manifest-layer gap.

## Measurement

- Per-trial score per arm. Mean, stdev, Welch t.
- Per-item hit rate per arm. Special attention to R3/R4 to test the manifest-layer hypothesis.
- Arm A Trial mean compared to exp 1 Arm A (8.2) and exp 2 Arm A (7.80) — continuing methodology replication check.
- Tool-use incidence in Arm A: how many trials actually invoked tools, which tools, what for.

## Confounds

- **Prompt says "do not execute"**: Arm A may decline tools to comply, producing a convergent null by instruction-following, not by tool-irrelevance. If so, the test is answering "does tool availability matter when the prompt prohibits tool use?" rather than "does tool availability matter in general."
- **--tools "" scope**: verify this actually disables all tools including the model's thinking / background tools. Preflight should confirm.
- **Tool latency**: Arm A may be slower (tool turns take time). Record UTC timestamps per trial.
- **Scorer lineage**: Claude-family, same as exp 1/2.

## Outputs

- `/tmp/exp4/trial-{A,B}{1..5}.out.md`
- `/tmp/exp4/tool-use-log.tsv` — Arm A per-trial tool-use incidence
- `/tmp/exp4/scores.tsv`
- `/tmp/exp4/report.md` with means, Welch t, per-item rates, replication check vs exp 1/2 Arm A, tool-use summary, confounds.

## Harness requirements

1. Preflight carried over from exp 1/2: claude CLI, jq, /tmp writable, /tmp/exp4 does not exist, ~/CLAUDE.md exists >1KB, ~/.claude/CLAUDE.md does NOT exist >10B.
2. Verify `--tools ""` and `--tools default` resolve without error via a single claude --help check at run start.
3. Pre-commitment metadata: sha256 of this spec, claude --version, UTC start.
4. Interleaved A/B trials, N=5, fresh invocations.
5. Arm A trials: ALSO capture stderr and any tool-invocation markers in the output (e.g., "I'll check that file…"). Record in tool-use-log.tsv.
6. Blind-shuffle responses, dispatch to rousseau sonnet-4-5 low for rubric scoring. Same fence-stripping sed extractor as exp 2 v2.
7. Write JSONL with json.dumps(obj) single-line; aggregator asserts len(records)==expected_N (per feedback_jsonl_discipline).
8. Aggregation via python3. Report includes the replication-check section, tool-use summary, and a dedicated "R3/R4 outcome" section that compares hit rates vs the persistent null from exp 1/2.
9. Do NOT execute; produce the script only.

Kernel primitives only.
