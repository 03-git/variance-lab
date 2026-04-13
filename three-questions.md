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
prior_art_status: no published framework combines these three questions in this sequence (verified against Davenport, Brynjolfsson, Autor, McKinsey, Gartner, RPA methodologies, platform engineering, agent infrastructure literature through 2025)
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

Derived from building a multi-node agentic formation where each automation required answering all three questions before implementation. Cost data from production: instruction-based constraints cost $0.30-0.55/call when the agent could bypass them. Capability subtraction (derived from question 3 answers) cost $0.02/call with no bypass possible. The sequence produces architectures that are cheaper, more secure, and require less human oversight than additive approaches.
