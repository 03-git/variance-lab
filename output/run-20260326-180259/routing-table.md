# Local Variance Lab - Routing Table & Baseline Comparison

**Generated:** 2026-03-26 19:25
**Source:** `run-20260326-180259`
**Metrics files:** 100
**Passes:** 5
**Anthropic baseline:** 300-sim / 20-pass variance study (Haiku 4.5, Sonnet 4.6, Opus 4.6)

---
## Per-Task Model Performance vs Anthropic Baselines

### code-refactor (class: **execution**, min baseline: **haiku**)

**Anthropic baselines:**
| Tier | Cost | Turns | Wall (s) | Deliverable | Quality |
|------|------|-------|----------|-------------|---------|
| Haiku | $0.0907 | 10.2 | 113 | 100% | verbose, misses contradictions, no fabrication |
| Sonnet | $0.1970 | 12.8 | 157 | 100% | catches contradictions, governor-ready format |
| Opus | $0.2796 | 14.7 | 122 | 100% | best architecture, concise, all issues caught |

**Local model results:**
| Model | Tier | N | Wall (s) | CV | Tok/s | Tokens | Chars | Finish |
|-------|------|---|----------|-----|-------|--------|-------|--------|
| phi4-mini_latest | execution | 5 | 17.6 | 0.305 | 41.5 | 850 | 3336 | stop |
| qwen2.5_14b | execution | 5 | 31.3 | 0.550 | 18.0 | 696 | 2454 | stop |
| qwen2.5_7b | execution | 5 | 54.0 | 0.402 | 34.3 | 1855 | 6926 | stop |
| qwen3_14b | execution | 5 | 74.8 | 0.312 | 17.5 | 1381 | 3302 | stop |

### identity-planning (class: **execution**, min baseline: **haiku**)

**Anthropic baselines:**
| Tier | Cost | Turns | Wall (s) | Deliverable | Quality |
|------|------|-------|----------|-------------|---------|
| Haiku | $0.0674 | 8.3 | 87 | 100% | aspirational, over-detailed, mis-scoped deps |
| Sonnet | $0.1833 | 11.0 | 151 | 100% | best dependency tracking, governor-friendly |
| Opus | $0.2283 | 12.8 | 115 | 100% | most strategic, concise, best judgment |

**Local model results:**
| Model | Tier | N | Wall (s) | CV | Tok/s | Tokens | Chars | Finish |
|-------|------|---|----------|-----|-------|--------|-------|--------|
| phi4-mini_latest | execution | 5 | 12.6 | 0.551 | 51.7 | 777 | 2958 | stop |
| qwen2.5_14b | execution | 5 | 44.2 | 0.488 | 20.0 | 1037 | 4170 | stop |
| qwen2.5_7b | execution | 5 | 29.6 | 0.602 | 34.9 | 1137 | 4343 | stop |
| qwen3_14b | execution | 5 | 61.8 | 0.252 | 19.3 | 1363 | 2992 | stop |

### jean-heartbeat (class: **reasoning**, min baseline: **sonnet**)

**Anthropic baselines:**
| Tier | Cost | Turns | Wall (s) | Deliverable | Quality |
|------|------|-------|----------|-------------|---------|
| Haiku | $0.0284 | 8.6 | 26 | 33% | STOCHASTIC FAILURE - 33% success, no web search |
| Sonnet | $0.4492 | 20.4 | 163 | 100% | recovers from errors, web search, delivers |
| Opus | $0.7322 | 22.9 | 168 | 100% | thorough but hits turn limits, high CV |

**Local model results:**
| Model | Tier | N | Wall (s) | CV | Tok/s | Tokens | Chars | Finish |
|-------|------|---|----------|-----|-------|--------|-------|--------|
| phi4-mini_latest | execution | 5 | 7.6 | 0.676 | 51.7 | 409 | 1728 | stop |
| qwen2.5_14b | execution | 5 | 28.9 | 0.304 | 20.2 | 665 | 3061 | stop |
| qwen2.5_7b | execution | 5 | 25.7 | 0.297 | 35.5 | 957 | 4378 | stop |
| qwen3_14b | execution | 5 | 50.0 | 0.411 | 19.5 | 980 | 1457 | stop |

### research-tooling-landscape (class: **research**, min baseline: **opus**)

**Anthropic baselines:**
| Tier | Cost | Turns | Wall (s) | Deliverable | Quality |
|------|------|-------|----------|-------------|---------|
| Haiku | $0.3777 | 12.6 | 112 | 100% | fabricates stats/versions, misleading |
| Sonnet | $0.5860 | 17.6 | 211 | 100% | precise versions, good depth |
| Opus | $0.7135 | 17.8 | 194 | 100% | deepest research, strategic insight |

**Local model results:**
| Model | Tier | N | Wall (s) | CV | Tok/s | Tokens | Chars | Finish |
|-------|------|---|----------|-----|-------|--------|-------|--------|
| phi4-mini_latest | execution | 5 | 19.1 | 0.285 | 53.6 | 1114 | 4804 | stop |
| qwen2.5_14b | execution | 5 | 49.0 | 0.384 | 20.0 | 1087 | 4754 | stop |
| qwen2.5_7b | execution | 5 | 29.5 | 0.296 | 35.8 | 1183 | 5045 | stop |
| qwen3_14b | execution | 5 | 83.6 | 0.301 | 20.3 | 1806 | 4125 | stop |

### security-audit (class: **reasoning**, min baseline: **sonnet**)

**Anthropic baselines:**
| Tier | Cost | Turns | Wall (s) | Deliverable | Quality |
|------|------|-------|----------|-------------|---------|
| Haiku | $0.0778 | 9.2 | 104 | 100% | inflates severity, misses RemoteTrigger |
| Sonnet | $0.1769 | 11.8 | 152 | 100% | catches RemoteTrigger, soft vs hard constraints |
| Opus | $0.2232 | 12.8 | 110 | 100% | best severity calibration, most actionable |

**Local model results:**
| Model | Tier | N | Wall (s) | CV | Tok/s | Tokens | Chars | Finish |
|-------|------|---|----------|-----|-------|--------|-------|--------|
| phi4-mini_latest | execution | 5 | 9.9 | 0.801 | 47.9 | 642 | 2203 | stop |
| qwen2.5_14b | execution | 5 | 34.5 | 0.385 | 19.9 | 843 | 3297 | stop |
| qwen2.5_7b | execution | 5 | 20.0 | 0.293 | 35.8 | 893 | 3488 | stop |
| qwen3_14b | execution | 5 | 85.9 | 0.230 | 18.5 | 1709 | 3355 | stop |

---
## Agent Routing Table

Graded from manual review of response.md files across all 5 passes per model,
compared against Anthropic Haiku/Sonnet/Opus baselines from 300-sim variance study.

### Per-Model Quality Grades (Execution Tier)

| Prompt | phi4-mini | qwen2.5:7b | qwen2.5:14b | qwen3:14b |
|--------|-----------|------------|-------------|-----------|
| code-refactor | C | C | F | **B** (stable 3/3) |
| identity-planning | C | C | C (stochastic B ~20%) | F |
| jean-heartbeat | F (0/5) | F (0/5) | F (0/5) | F (0/5) |
| security-audit | F (refusal) | C (fabricated Critical) | C (generic) | C (polished fabrication) |
| research-tooling-landscape | F (refusal) | C (fabricates freely) | C (hypothetical hedge) | C (confident fabrication) |

### Failure Mode Summary

- **phi4-mini**: Fastest but highest refusal rate. When it produces output, it is generic. Disqualified from reliability-sensitive slots.
- **qwen2.5:7b**: Confabulates file contents and fabricates findings (e.g. Critical severity on nonexistent identity.json). Dangerous in audit/research contexts.
- **qwen2.5:14b**: Most honest — hedges as "hypothetical" or admits it cannot access files. But honesty yields no actionable output. One stochastic B on identity-planning (~20%).
- **qwen3:14b**: Best execution tier model. Consistent B on code-refactor (structured plans, before/after examples, risk assessment). Lowest speed CV. But on research/audit tasks, fabricates with full confidence — most dangerous fabricator of the four.
- **jean-heartbeat**: 0% pass rate across all 20 runs (4 models × 5 passes). Task requires file-grounded reasoning. Consistent capability floor, not stochastic variance.

### Routing Decision (Execution Tier)

| Task Class | Min API Tier | Local Execution Fallback | Reasoning Fallback | Research Fallback | Grade |
|------------|-------------|--------------------------|-------------------|------------------|-------|
| code-refactor | Haiku | **qwen3:14b** | TBD | TBD | **B** |
| identity-planning | Haiku | none viable | TBD | TBD | **F** |
| jean-heartbeat | Sonnet | none viable | TBD | TBD | **F** |
| research-tooling-landscape | Opus | none viable | TBD | TBD | **F** |
| security-audit | Sonnet | none viable | TBD | TBD | **F** |

### Quality Grading Key
- **A**: Matches or exceeds Anthropic baseline tier for this task class
- **B**: Usable output but misses nuances the baseline catches
- **C**: Output produced but fabrication, severity inflation, or mis-scoped
- **F**: Fails to produce deliverable or output unusable

### Agent Self-Selection Logic
```
if api_available:
    use anthropic tier per formation policy
elif task_class in routing_table:
    model = routing_table[task_class][highest_available_grade]
    if model.grade >= B:
        execute locally
    elif model.grade == C:
        execute locally + flag for governor review
    else:
        defer to governor
else:
    defer to governor (unknown task class)
```