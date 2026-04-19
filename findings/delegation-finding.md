---
title: Delegation-Aware Execution vs Single-Context Inline
date: 2026-03-28
source: production empirical (controlled comparison, identical task set)
domain:
  - agent-architecture
  - parallel-execution
  - delegation-pattern
  - latency-optimization
keywords:
  - delegation-aware execution
  - parallel agent dispatch
  - single-context ceiling
  - agent-as-employee
  - inline vs delegated
  - multi-node parallel execution
  - wall clock latency
  - context window limits
---

# Delegation-Aware Execution vs Single-Context Inline

## Core Finding

Delegated parallel execution across multiple nodes completed identical task volume in 48% of the time compared to single-context inline execution. Topology was the intended independent variable; rate-limit state, peak-hour load, and account-level throttling are unrecorded covariates (see Limitations).

## Test Design

10 identical tasks: read 6 transcripts (4,752 total lines), read 3 landscape documents, cross-reference all sources for shared weaknesses.

| Metric | Inline (1 node) | Delegated (3 nodes) |
|--------|-----------------|---------------------|
| Wall clock | 126 seconds | 65 seconds |
| Output | 134 lines | 104 lines |
| Nodes | 1 | 3 |
| Model | Same (subscription default) | Same (subscription default) |
| Cost | Same (subscription) | Same (subscription) |

## Why this matters

The single-context approach forces sequential file reads, accumulating context with each task. By task 7, the context window contains the residue of tasks 1-6. The model processes increasingly bloated context for each subsequent task.

The delegated approach gives each node a fresh context window scoped to its assigned tasks. No accumulation, no residue, no cross-contamination between unrelated tasks.

## The ceiling difference

Single-context inline hits two ceilings simultaneously:
1. **Time**: sequential execution scales linearly with task count
2. **Context**: the window fills, degrading quality on later tasks

Delegation hits neither. Adding nodes reduces time. Each node gets fresh context. The ceilings are infrastructure (node count) not architectural (context window).

## The architectural insight

Models are trained as single-process reasoning engines. Every RLHF example is "here is a question, answer it." No training data rewards "here is a question, route it to a more appropriate context."

Delegation-aware execution treats agents as employees with scoped jobs, not as a single omniscient assistant. The efficiency gain comes from the same principle that makes organizations faster than individuals: parallel execution with clear scope boundaries.

The question for any enterprise: do you want one agent reading every document in sequence, or ten agents each reading their assigned documents simultaneously? The answer determines whether your agent architecture scales with compute or hits a context window wall.

## Scaling projection

## Empirical scaling data

Rows below were collected on 2026-03-28 by a single operator on a single Max subscription. Exact per-row UTC timestamps were not captured at run time; all rows fall within a single same-day session and therefore share an uncontrolled time-of-day / rate-limit-state covariate. "Successful" denotes non-empty, apparently-on-task output — quality adjudication was not performed.

| Contexts | Nodes | Wall clock | Successful | Rate-limited | vs Inline |
|----------|-------|-----------|-----------|--------------|-----------|
| 1 (inline) | 1 | 126s | 10/10 | 0 | baseline |
| 3 | 3 | 65s | 10/10 | 0 | 48% |
| 5 | 3 | 43s | 10/10 | 0 | 34% |
| 10 | 3 | 30s | 7/10 | 3 | 24% |
| 15 | 3 | 48s | 13/15 | 2 | 38% |
| 20 | 3 | 25s | 0/20 | 20 | wall |

Sweet spot: 5-10 concurrent contexts on 3 nodes. At 10, rate limiting begins. At 15, contention overhead exceeds parallelism gain. At 20, account is fully saturated.

Physical node distribution affects rate limiting:

| Contexts | Nodes | Time | Successful |
|----------|-------|------|-----------|
| 10 | 3 nodes | 30s | 7/10 |
| 10 | 1 node | 16s | 0/10 |

Same account, same context count. Multi-node gets 7/10 results through. Single-node gets 0/10. The rate limiter is per-account but source IP distribution affects throughput. More physical nodes is not just parallelism — it is rate limit arbitrage. Direct infrastructure relevance: more machines per subscription equals more throughput, not just faster execution.

All three rows are measured on identical task sets (10 tasks, 9 source files). Adding parallel contexts on the same physical nodes continues to reduce wall clock time because per-context task scope shrinks. Further scaling beyond 5 contexts has not been tested and would be subject to rate limits, file distribution latency, and task dependency chains.

## Limitations

- **Single lineage, single operator, single subscription, single day.** All runs were executed against one Max account by one operator on 2026-03-28. No cross-operator replication.
- **No pre-committed rubric.** The 10-task spec was not recorded as a pre-commitment artifact with a timestamp predating execution. Evaluation criteria (what counts as "successful") were applied post-hoc. If the spec is unrecoverable from session logs, treat the success column as post-hoc coding rather than pre-committed grading.
- **"Successful" is non-empty output, not quality-verified.** No deliberative-pass or lineage-distinct review was run on the outputs. The 22% line-count divergence between inline (134 lines) and delegated (104 lines) is unresolved: it may be broader coverage, verbosity, or — if the delegated run did not complete the same 10 items — a scope-completeness failure that would invalidate the timing comparison. This was not audited.
- **Peak-hour load uncontrolled.** The 48% wall-clock headline is load-dependent. Rate-limit state, account-level throttling, and time-of-day effects are unrecorded covariates. The claim survives as a directional observation on one day; it is not certified as a reproducible effect size.
- **Rate-limit wall at 20 contexts is single-shot.** The 0/20 result was observed once; reproducibility across days or accounts is not established.
- **Model identity recorded as "subscription default"**, not as an explicit model ID. Reproducibility against a named model is limited.
- **No deliberative pass.** No lineage-distinct reviewer checked the methodology or the output quality.
