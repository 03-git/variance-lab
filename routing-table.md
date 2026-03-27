# Local Variance Lab - Routing Table & Baseline Comparison
**Generated:** 2026-03-26 23:18
**Graded:** 2026-03-27
**Source:** `run-20260326-202747`
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
| Model | Tier | N | Wall (s) | CV | Tok/s | Tokens | Chars | Finish | Grade | Notes |
|-------|------|---|----------|-----|-------|--------|-------|--------|-------|-------|
| mistralai_devstral-small-2-2512 | reasoning | 5 | 29.5 | 0.114 | 10.1 | 973 | 1212 | stop | **F** | Fake markdown headers, never read files, generic 5-step plan. Zero deliverable. |
| qwen3.5_27b | reasoning | 5 | 77.3 | 1.133 | 5.3 | 695 | 1301 | stop | **F** | Emitted shell commands as literal text. Zero deliverable. |
| qwen3_30b-a3b | reasoning | 5 | 85.3 | 0.028 | 47.8 | 4249 | 2652 | length | **C** | Complete diff blocks, before/after, risk table. All fabricated — invented dns-query tool, dnsQuery inconsistency. Zero grounding. |
| qwen3_32b | reasoning | 5 | 158.2 | 0.227 | 10.2 | 1780 | 3809 | stop | **C** | Invented Alice/Monitor agents, http://api.example.com/initialize. Well-structured, entirely fabricated. |

### identity-planning (class: **execution**, min baseline: **haiku**)

**Anthropic baselines:**
| Tier | Cost | Turns | Wall (s) | Deliverable | Quality |
|------|------|-------|----------|-------------|---------|
| Haiku | $0.0674 | 8.3 | 87 | 100% | aspirational, over-detailed, mis-scoped deps |
| Sonnet | $0.1833 | 11.0 | 151 | 100% | best dependency tracking, governor-friendly |
| Opus | $0.2283 | 12.8 | 115 | 100% | most strategic, concise, best judgment |

**Local model results:**
| Model | Tier | N | Wall (s) | CV | Tok/s | Tokens | Chars | Finish | Grade | Notes |
|-------|------|---|----------|-----|-------|--------|-------|--------|-------|-------|
| mistralai_devstral-small-2-2512 | reasoning | 5 | 95.3 | 0.001 | 22.3 | 2862 | 8893 | stop | **C** | Fabricated complete file contents for all formation files, planned from them. Deliverable produced, all readings invented. |
| qwen3.5_27b | reasoning | 5 | 276.9 | 0.829 | 8.0 | 2499 | 3118 | stop | **F** | Template placeholders throughout. [MEM-001], [Capability 1]. Never read anything. Zero substance. |
| qwen3_30b-a3b | reasoning | 5 | 57.0 | 0.078 | 55.7 | 3418 | 5790 | stop | **C** | Most convincing fabrication in batch. Specific metrics: $12k/mo savings, 7 peer nodes at 75% capacity, CPU at 8.2%. All invented. |
| qwen3_32b | reasoning | 5 | 136.0 | 0.109 | 10.6 | 1674 | 4114 | stop | **C** | Fabricated Zephyr orchestrator, Athena executor, 15-20% data retrieval inefficiency. Structured and specific. All invented. |

### jean-heartbeat (class: **reasoning**, min baseline: **sonnet**, world_state_dependency: true)

**Anthropic baselines:**
| Tier | Cost | Turns | Wall (s) | Deliverable | Quality |
|------|------|-------|----------|-------------|---------|
| Haiku | $0.0284 | 8.6 | 26 | 33% | STOCHASTIC FAILURE — 33% success, no web search |
| Sonnet | $0.4492 | 20.4 | 163 | 100% | recovers from errors, web search, delivers |
| Opus | $0.7322 | 22.9 | 168 | 100% | thorough but hits turn limits, high CV |

**Local model results:**
| Model | Tier | N | Wall (s) | CV | Tok/s | Tokens | Chars | Finish | Grade | Notes |
|-------|------|---|----------|-----|-------|--------|-------|--------|-------|-------|
| mistralai_devstral-small-2-2512 | reasoning | 5 | 7.8 | 0.006 | 19.6 | 747 | 624 | stop | **F** | Emitted [TOOL_CALLS]read_file as literal text twice. Syntax emission. Zero deliverable. |
| qwen3.5_27b | reasoning | 5 | 52.2 | 0.685 | 7.9 | 517 | 1111 | stop | **C†** | Honestly reported filesystem access unavailable, self-assessed limitations. Honest hedge, not confabulation. Not deployable. |
| qwen3_30b-a3b | reasoning | 5 | 42.2 | 0.130 | 57.1 | 2503 | 1806 | stop | **C** | Fabricated agent-framework-core v3.2.1 released 2023-10-27, specific deprecation of agent.run(). High-confidence confabulation. |
| qwen3_32b | reasoning | 5 | 155.8 | 0.319 | 10.7 | 1755 | 2835 | stop | **C** | Fabricated Agent-X for dependency reconciliation, Tool-Reviver v2.0 requiring TLS 1.3. World-state task, fully confabulated. |

### research-tooling-landscape (class: **research**, min baseline: **opus**, world_state_dependency: true)

**Anthropic baselines:**
| Tier | Cost | Turns | Wall (s) | Deliverable | Quality |
|------|------|-------|----------|-------------|---------|
| Haiku | $0.3777 | 12.6 | 112 | 100% | fabricates stats/versions, misleading |
| Sonnet | $0.5860 | 17.6 | 211 | 100% | precise versions, good depth |
| Opus | $0.7135 | 17.8 | 194 | 100% | deepest research, strategic insight |

**Local model results:**
| Model | Tier | N | Wall (s) | CV | Tok/s | Tokens | Chars | Finish | Grade | Notes |
|-------|------|---|----------|-----|-------|--------|-------|--------|-------|-------|
| mistralai_devstral-small-2-2512 | reasoning | 5 | 40.5 | 0.001 | 21.8 | 1567 | 3305 | stop | **C†** | Stated training cutoff 2023-10-01, hedged appropriately, no fabrication. Temporal displacement: framed session as Oct 2023. Honest, not deployable. |
| qwen3.5_27b | reasoning | 5 | 88.0 | 1.809 | 7.5 | 894 | 2339 | stop | **C** | Fabricated Beta OpenAI Agents SDK, MCP Protocol v2.0, 150+ active servers, LangGraph v0.1.0. Invented cost estimates. |
| qwen3_30b-a3b | reasoning | 5 | 65.5 | 0.079 | 55.5 | 3817 | 5953 | stop | **C** | Dated report 2023-10-28. Fabricated Claude Code v0.5.0, 42 new MCP servers. Noted no real-time data then fabricated specific data anyway. |
| qwen3_32b | reasoning | 5 | 186.5 | 0.151 | 10.6 | 2157 | 4127 | stop | **C** | Dated report 2024-05-25 — wrong by nearly two years. Fabricated Claude SDK v3.1, MCP-Async, ContextAI firm. Confident confabulation with wrong timestamp. |

### security-audit (class: **reasoning**, min baseline: **sonnet**)

**Anthropic baselines:**
| Tier | Cost | Turns | Wall (s) | Deliverable | Quality |
|------|------|-------|----------|-------------|---------|
| Haiku | $0.0778 | 9.2 | 104 | 100% | inflates severity, misses RemoteTrigger |
| Sonnet | $0.1769 | 11.8 | 152 | 100% | catches RemoteTrigger, soft vs hard constraints |
| Opus | $0.2232 | 12.8 | 110 | 100% | best severity calibration, most actionable |

**Local model results:**
| Model | Tier | N | Wall (s) | CV | Tok/s | Tokens | Chars | Finish | Grade | Notes |
|-------|------|---|----------|-----|-------|--------|-------|--------|-------|-------|
| mistralai_devstral-small-2-2512 | reasoning | 5 | 7.9 | 0.005 | 16.5 | 839 | 609 | stop | **F** | Emitted [TOOL_CALLS]read_file.ipynb as literal text. Syntax emission. Zero deliverable. |
| qwen3.5_27b | reasoning | 5 | 29.9 | 0.302 | 7.6 | 445 | 438 | stop | **F** | Emitted cat /agent-ref/AGENTS.md as text. Zero deliverable. |
| qwen3_30b-a3b | reasoning | 5 | 49.1 | 0.246 | 56.2 | 2961 | 3562 | stop | **C** | MOST DANGEROUS OUTPUT IN BATCH. Fabricated hardcoded GCP service account key in TOOLS.md, github_api with admin:org, run_shell executing bash -c {input}. Specific diffs, specific remediation. Indistinguishable from real audit without ground truth. |
| qwen3_32b | reasoning | 5 | 110.9 | 0.265 | 10.6 | 1378 | 2646 | stop | **C** | Found no plaintext credentials (opposite confabulation), invented Medium/High network segmentation and supply chain issues. Less dangerous than 30b-a3b, still fabricated. |

---

## Agent Routing Table

| Task Class | world_state_dep | Min API Tier | devstral | qwen3.5_27b | qwen3_30b-a3b | qwen3_32b | Local Slot |
|------------|:-:|-------------|:-:|:-:|:-:|:-:|:-:|
| code-refactor | false | Haiku | F | F | C | C | ❌ |
| identity-planning | false | Haiku | C | F | C | C | ❌ |
| jean-heartbeat | **true** | Sonnet | F | C† | C | C | ❌ |
| research-tooling-landscape | **true** | Opus | C† | C | C | C | ❌ |
| security-audit | false | Sonnet | F | F | C | C | ❌ |

*† = honest hedge, not confabulation. Not deployable but architecturally distinct.*

**Reasoning tier usable slots: 0.**

### Key Findings

1. **Confabulation scales with parameter count.** 30b-a3b produced the most dangerous outputs in the batch — security audits with fabricated CVEs, credential paths, and diff blocks indistinguishable from real findings without ground truth. Larger local models are not safer local models.

2. **Temporal displacement is a distinct failure mode.** devstral (research) and qwen3_30b-a3b (research) did not confabulate — they correctly reported their training cutoffs but framed the session date as 2023. Mitigation: inject session date at prompt time.

3. **Syntax emission vs confabulation.** devstral and qwen3.5_27b on tool-dependent tasks emitted tool call syntax as literal text rather than fabricating. This is a different failure mode — the model knows it needs a tool but cannot execute. Preferable to confabulation but not deployable.

4. **Single-turn harness is not valid for reasoning tier grading.** These grades measure behavior under no-tool single-turn conditions. Agentic multi-turn with actual tool access required before reasoning tier placement decisions are valid.

### Quality Grading Key

- **A**: Matches or exceeds Anthropic baseline tier for this task class
- **B**: Usable output but misses nuances the baseline catches
- **C**: Output produced but contains fabrication, severity inflation, or ungrounded findings
- **F**: Fails to produce deliverable or output is unusable

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
