---
title: Three Questions for Agentic Autonomy
date: 2026-03-28
source: production empirical (consulting methodology derived from formation buildout)
domain:
  - agentic-consulting
  - workflow-automation
  - autonomy-assessment
  - human-ai-task-allocation
keywords:
  - agentic autonomy assessment
  - consulting intake protocol
  - workflow automation assessment
  - human KPI identification
  - via negativa methodology
  - autonomy blocker taxonomy
  - agent permission design
  - infrastructure vs capability barriers
prior_art_status: no framework known to author combines these three questions in this sequence as of 2026-03-28. Search was an informal literature scan (not a systematic review) across Davenport, Brynjolfsson, Autor, McKinsey, Gartner, RPA vendor methodologies, platform-engineering literature (Skelton & Pais), and agent-infrastructure writeups (LangChain, Anthropic) published through 2025. No database query strings, inclusion/exclusion criteria, or cross-lineage review were applied; the claim is a negative assertion subject to the limits of the author's scan.
---

# Three Questions for Agentic Autonomy

Every workflow automation, every agent deployment, every consulting engagement starts with three questions:

1. **What can you do that an agent cannot?**
2. **What prevents the workflow from being autonomous?**
3. **What should the agent have access to?**

The answers are domain-specific. The questions are universal. The sequence matters.

## Why the sequence matters

Starting from question 1 (human capability boundary) forces a different inventory than starting from "what can AI do." It surfaces tacit knowledge, judgment under ambiguity, relational capital, and contextual authority -- capabilities that a technology-first scan would never surface because they don't map to automatable task categories.

Starting from question 2 (autonomy blockers) assumes the agent is capable and asks what environmental barriers remain. This inverts the standard framing where "why not automate?" defaults to "AI isn't good enough yet." Most blockers are infrastructure problems (authentication gates, GUI-only interfaces, missing APIs), not capability problems.

Starting from question 3 (access scope) after questions 1 and 2 leads to subtractive security: the agent gets only what the blocker analysis says it needs. Reversing the order (starting with access) leads to additive security -- granting broad access and layering restrictions.

## Prior art

Every major published framework follows one of three starting points:

| Starting point | Examples | Gap |
|---|---|---|
| Technology-first: what can AI do? | Brynjolfsson & Mitchell (2017), Kai-Fu Lee (2018), McKinsey (2017) | Human capability is the residual, not the starting point |
| Process-first: map workflow, allocate tasks | Wilson & Daugherty/Accenture (2018), RPA feasibility (UiPath, Automation Anywhere) | Process is the unit of analysis, not the blocker |
| ROI-first: where are the efficiency gains? | Gartner hyperautomation (2020-2024), Big 4 assessments | Automation candidacy scoring, not blocker enumeration |

**What is novel in the three-question sequence:**

1. Human capability as the generative starting point, not the residual after AI capability mapping
2. Blocker as the unit of analysis, not process or capability
3. Infrastructure vs capability as a first-class distinction (the agent could do it, but auth/API/GUI prevents it)
4. Per-workflow blocker decomposition that is directly actionable (remove this blocker, unlock this autonomy)
5. Access scope derived from blocker analysis, producing subtractive security by construction

No published framework combines all five elements. The individual concepts appear in isolation across platform engineering (Skelton & Pais), automation candidacy scoring (McKinsey/Gartner), agent infrastructure literature (LangChain, Anthropic), and security frameworks (least privilege). The composition and sequencing are unoccupied.

## Application

These questions apply at every scale:

- **Individual workflow**: "What do I still do manually that I should not?" leads to question 1.
- **Small practice (clinician, designer, freelancer)**: Questions 1-3 are the entire consulting intake. The client answers from domain expertise. The consultant maps answers to infrastructure.
- **Enterprise**: The same questions, asked per department, per workflow, per role. The aggregated answers define the agent architecture.

## Empirical validation

Derived from building a multi-node agentic formation where each automation required answering all three questions before implementation. The sequence produces architectures that are cheaper, more secure, and require less human oversight than additive approaches.

> **Unsourced figures struck:** Earlier revisions cited "$0.30-0.55/call" (instruction-based) and "$0.02/call" (capability subtraction) as the comparative cost anchor. No artifact path, sample size, date range, or measurement methodology exists in this repo (the same figures appear in the delegated-agent-authorization-gap finding and are struck there for the same reason). The *directional* claim — that capability subtraction is substantially cheaper than instruction-based constraint — stands as operator observation; the numeric magnitudes are unsourced anecdote pending a reproducible measurement artifact.

## Limitations

- **Single-operator derivation.** The sequence was abstracted from one governor's buildout of one agentic formation. No cross-operator replication.
- **Single implementation context.** The production validation is internal (the same formation the sequence was derived from). This is self-confirming, not external.
- **Prior-art claim is a scan, not a systematic review.** See frontmatter `prior_art_status`. A published framework combining Q1-Q3 in this sequence predating 2026-03 would preempt the novelty claim; no such artifact is known to the author, but the search was informal. The novelty claim is load-bearing and has not received a deliberative pass from lineage-distinct reviewers.
- **No falsifiability conditions encoded.** The "five novel elements" list (human capability as generative, blocker as unit, infra-vs-capability distinction, per-workflow decomposition, subtractive access) is not expressed as a scored rubric against named frameworks.
- **Empirical anchor figures are unsourced** (see strikethrough above). The cost comparison is directional operator observation, not measured data with a reproducible artifact.
- **Document class.** This finding is framework synthesis with production validation, not a gated empirical experiment. Readers should not treat it as "validated methodology" in the sense that a pre-committed, lineage-reviewed trial would warrant.
