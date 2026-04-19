---
title: Adversarial Review of Interaction-Mode-Variance Rerun Draft
reviewer: Claude Sonnet 4.5 (execution seat 02)
date: 2026-04-19
draft_reviewed: rerun-draft.md
---

# Review of rerun-draft.md

## 1. Factual errors

**Line 71: Token totals and passenger share**

Draft states: "70 passenger sessions carry ~12.2M of ~13.7M total single-model qualifying tokens (~89%)."

TSV verification:
- Passenger tokens: 12,197,814 ≈ 12.2M ✓
- Total tokens: 296,054 + 29,768 + 964,975 + 12,197,814 = 13,488,611 ≈ 13.5M (not 13.7M)
- Passenger share: 12,197,814 / 13,488,611 = 0.9043 = 90.4% (not 89%)

Two errors:
1. Total should be ~13.5M, not ~13.7M
2. Passenger share should be ~90%, not ~89%

**All other numeric claims verified (sample of 25+ checks):**
- N=501 single-model qualifying ✓
- Table line 36-39: all mode counts, means, medians, outlier-removed values, human turns, tool calls match TSVs exactly ✓
- Multipliers line 45-48: all match ratios-singlemodel.tsv (52.677→52.7×, 21.647→21.6×, etc.) ✓
- Correction rates line 36-39: match aggregate-singlemodel.tsv with standard rounding (0.918782→0.919, etc.) ✓
- Output share line 73: pipe 92.6% = 274,203/296,054 ✓; passenger 98.3% = 11,998,559/12,197,814 ✓
- Comparison table line 60-63: all N values and percentages correct ✓

## 2. Framing drift

**Line 65: Corpus size comparison**

"It is a 12×-larger, differently-scoped set of files."

This refers to raw file count (1075 vs 88), but the comparison table compares qualifying sessions (501 vs 88, a 5.7× ratio). Using "12×" in proximity to a session-count comparison table creates ambiguity about which denominator applies. The statement is literally correct (1075/88 = 12.2×) but the framing invites misreading.

**Line 48: "order of magnitude 10×"**

"Collaborator vs governor: order of magnitude 10× on means"

TSV shows ratio_mean_total = 10.418. Saying "order of magnitude 10×" when the value is 10.418× is technically defensible but imprecise. The phrase "order of magnitude" typically implies ~10× vs ~100×, not a literal 10.418. Clearer to state "10.4× on means" directly.

**No other drift found.** Headlines privilege means but report medians and outlier-removed ratios alongside per rubric §Aggregation. Mechanism section (line 68-76) correctly identifies the mechanical turn/token correlation without overclaiming separability.

## 3. Missing limitations

None found. The draft discloses:
- Mixed-model exclusion implementation (line 28, 50-52): 14 sessions removed, all passenger/collaborator
- Methodology-experiment contamination (line 82-84): 27 pipe sessions, 67k tokens quantified
- Subagent dedup approach (line 85-86): path filter, spot-check N=10
- Correction-keyword false-positive mechanism (line 89-90): denominator difference between pipe and other modes explained
- Mode-vs-tokens tautology (line 68-70): mechanical component disclosed, turn-normalized metric absence noted

Session_id format deviation (line 91) and extractor dispatch prompt deviation (line 93) are disclosed in Confounds. Pre-commitment implementation (line 99) notes filesystem/git timestamp vs hash-signature.

## 4. What to cut

**Line 73-75: Output-dominates-input paragraph**

"Output dominates input across all modes. This is a property of Claude Code's tool-heavy, code-emitting workload, not of interaction mode. Output-share holds in pipe sessions (92.6%) and in passenger (98.3%), so it is not a mode discriminator in this corpus."

This observation does not serve the main claim (mode variance in total tokens per session). The claim is about between-mode multipliers, not input/output ratios. Output-dominance is a within-mode property that applies uniformly. The paragraph verifies a non-discriminator, which is methodologically sound but not load-bearing for the finding. Cut unless the purpose is to preempt a specific expected objection.

**No other cuts recommended.** The Confounds section is dense but necessary for replication. The comparison table (line 58-64) contextualizes the rerun against the original; without it, "rerun" is underspecified. The Mechanism section (line 67-76) is required to interpret the multipliers correctly.
