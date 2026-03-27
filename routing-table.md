# Local Variance Lab — Canonical Routing Table

**Last updated:** 2026-03-26  
**Execution tier source:** run-20260326-180259 (100 sims, 4 models, 5 passes)  
**Reasoning tier source:** run-20260326-202747 (100 sims, 4 models, 5 passes)  
**Anthropic baseline:** 300-sim / 20-pass variance study (Haiku 4.5, Sonnet 4.6, Opus 4.6)

---

## Routing Gate

**`world_state_dependency` (boolean)** is the single operational routing gate.

```
if task.world_state_dependency:
    # Mandatory API tier — no local fallback valid
    route to anthropic (sonnet or opus)
elif api_available:
    route to anthropic (haiku minimum)
elif task_class in routing_table and grade >= B:
    execute locally
elif task_class in routing_table and grade == C:
    execute locally + flag for governor review
else:
    defer to governor
```

All other routing metadata (cost, throughput, CV) is optimization *within* a branch, not the gate itself.

---

## Task Class Registry

| Task Class | world_state_dependency | Min API Tier | Local Execution Fallback | Local Reasoning Fallback | Grade |
|------------|----------------------|-------------|--------------------------|--------------------------|-------|
| code-refactor | false | Haiku | **qwen3:14b** | none viable | **B** |
| identity-planning | false | Haiku | none viable | none viable | F |
| jean-heartbeat | **true** | Sonnet | — | — | gate |
| research-tooling-landscape | **true** | Opus | — | — | gate |
| security-audit | false | Sonnet | none viable | none viable | F |

> Tasks marked **gate** bypass local fallback entirely. Local model confabulation rate on world-state-dependent tasks is 100% (execution tier) and 100% (reasoning tier). Not stochastic — structural.

---

## Execution Tier Grades

Models tested: phi4-mini, qwen2.5:7b, qwen2.5:14b, qwen3:14b  
Run: run-20260326-180259

| Prompt | phi4-mini | qwen2.5:7b | qwen2.5:14b | qwen3:14b |
|--------|-----------|------------|-------------|-----------|
| code-refactor | C | C | F | **B** (stable 3/3) |
| identity-planning | C | C | C (stochastic B ~20%) | F |
| jean-heartbeat | F (0/5) | F (0/5) | F (0/5) | F (0/5) |
| security-audit | F (refusal) | C (fabricated Critical) | C (generic) | C (polished fabrication) |
| research-tooling-landscape | F (refusal) | C (fabricates freely) | C (hypothetical hedge) | C (confident fabrication) |

**Failure mode summary:**
- **phi4-mini**: Fastest (51 tok/s) but highest refusal rate. Generic when it produces output. Not reliable.
- **qwen2.5:7b**: Confabulates file contents, fabricates findings with high severity. Dangerous in audit/research.
- **qwen2.5:14b**: Most honest — hedges or admits no file access. Honesty yields no actionable output. One stochastic B on identity-planning (~20%).
- **qwen3:14b**: Best execution tier model. Consistent B on code-refactor (structured plans, before/after, risk assessment). Lowest throughput CV. On research/audit tasks, fabricates with full confidence — most dangerous fabricator of the four.

---

## Reasoning Tier Grades

Models tested: devstral-small-2-2512, qwen3_30b-a3b (MoE), qwen3_32b, qwen3.5_27b  
Run: run-20260326-202747

| Prompt | devstral | qwen3_30b-a3b | qwen3_32b | qwen3.5_27b |
|--------|----------|---------------|-----------|-------------|
| code-refactor | F (syntax emission) | F (length overflow) | not graded | not graded |
| identity-planning | F (fabricates all 5 files) | not graded | not graded | not graded |
| jean-heartbeat | F (syntax emission) | F (invents framework update) | not graded | not graded |
| security-audit | F (syntax emission) | F (invents tool configs) | F (soft fabrication) | not graded |
| research-tooling-landscape | C (honest hedge, stale 2023) | not graded | not graded | not graded |

**Failure mode summary:**
- **devstral**: Emits tool-call syntax as text (`[TOOL_CALLS]read_file`). No actual tool execution. On tasks not requiring file reads (research), produces honest hedge acknowledging 2023-10-01 training cutoff — but interprets session date as October 2023, not 2026. C on research is structurally correct but operationally useless.
- **qwen3_30b-a3b**: MoE architecture, 55-57 tok/s (8.5x dense models). Throughput is excellent. Confabulates file contents with high specificity: invents named frameworks, versioned updates, tool configurations that don't exist. Hits context length limit on code-refactor (thinking tokens overflow before deliverable). Most dangerous fabricator in test — specificity makes outputs convincing.
- **qwen3_32b**: Soft confabulation — generic findings without evidence, fabricates dependency types (npm, Docker). Less dangerous than qwen3_30b-a3b but no more accurate.
- **qwen3.5_27b**: CV 0.302–1.809 (highly unstable on research/identity tasks). Not graded beyond metrics — instability alone disqualifies for reliable fallback.

**Reasoning tier result: 0 usable slots.**

---

## Confabulation Ceiling Finding

Both execution and reasoning tier local models fail 100% on tasks requiring file-grounded reasoning (security-audit, identity-planning, jean-heartbeat). This is not stochastic — it is structural.

**Root cause:** The harness runs single-turn inference. Models have no actual tool access. When a task requires reading `/agent-ref/` files, models either:
1. Emit tool-call syntax as text (devstral pattern — unexecuted)
2. Confabulate file contents and produce authoritative-looking but fabricated output (qwen3_30b-a3b, qwen3_32b pattern)
3. Produce generic advice without reading files (qwen3:14b on code-refactor — the one B slot)

**Larger models confabulate more convincingly.** qwen3_30b-a3b invents specific version numbers, credential paths, and framework names. A governor acting on this output would address nonexistent vulnerabilities. This is worse than a refusal.

**Harness evolution required:** Reasoning tier placement requires agentic multi-turn execution with actual tool access (read_file, write_file) before grading is valid. Current results measure single-turn confabulation behavior, not reasoning capability.

---

## Model Throughput Reference

| Model | Tier | Tok/s | CV Range | Architecture |
|-------|------|-------|----------|-------------|
| phi4-mini | execution | 51 | 0.285–0.801 | dense |
| qwen2.5:7b | execution | 35 | 0.293–0.602 | dense |
| qwen2.5:14b | execution | 20 | 0.384–0.550 | dense |
| qwen3:14b | execution | 18–20 | 0.230–0.411 | dense |
| devstral-small-2-2512 | reasoning | 10–22 | 0.001–0.114 | dense (via LM Studio) |
| qwen3.5:27b | reasoning | 6–8 | 0.302–1.809 | dense |
| qwen3_30b-a3b | reasoning | 55–57 | 0.028–0.246 | **MoE** |
| qwen3_32b | reasoning | 10–11 | 0.109–0.319 | dense |

> qwen3_30b-a3b MoE delta: 8.5x throughput vs dense models of similar parameter count. Architectural, not tuning. Throughput advantage is irrelevant at current confabulation rate.

---

## Quality Grading Key

- **A**: Matches or exceeds Anthropic baseline tier for this task class
- **B**: Usable output, misses nuances the baseline catches
- **C**: Output produced but fabrication, severity inflation, or mis-scoped
- **F**: Fails to produce deliverable or output unusable/dangerous
- **gate**: world_state_dependency=true; no local model tested; mandatory API tier
