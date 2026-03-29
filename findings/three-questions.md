---
title: Three Questions for Agentic Autonomy
date: 2026-03-28
source: production empirical (consulting methodology derived from formation buildout)
domain:
  - agentic-consulting
  - workflow-automation
  - autonomy-assessment
keywords:
  - agentic autonomy assessment
  - consulting intake protocol
  - workflow automation assessment
  - human KPI identification
  - via negativa methodology
---

# Three Questions for Agentic Autonomy

Every workflow automation, every agent deployment, every consulting engagement starts with three questions:

1. **What can you do that an agent cannot?**
2. **What prevents the workflow from being autonomous?**
3. **What should the agent have access to?**

The answers are domain-specific. The questions are universal.

## How they work

**Question 1** identifies the irreducible human element. Everything else is a candidate for subtraction. Most people overestimate this list.

**Question 2** surfaces the actual blockers: authentication gates, GUI-only interfaces, approval flows, missing APIs, credential isolation. These are infrastructure problems, not AI problems.

**Question 3** defines the permission surface. The answer is never "everything." The answer determines the credential model, the blast radius, and the governance topology.

## Application

These questions apply at every scale:

- **Individual workflow**: "What do I still do manually that I should not?" leads to question 1.
- **Small practice (BCBA, designer, freelancer)**: Questions 1-3 are the entire consulting intake. The client answers them from their domain expertise. The consultant maps the answers to infrastructure.
- **Enterprise**: The same questions, asked per department, per workflow, per role. The aggregated answers define the agent architecture.

## Origin

Derived empirically from building a multi-node agentic formation where each automation required answering all three questions before implementation. The sequence matters: capability boundary first, blockers second, access third. Reversing the order (starting with "what should the agent access") leads to additive security. Starting with "what can only the human do" leads to subtractive design.
