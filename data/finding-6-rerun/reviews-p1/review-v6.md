---
review_of: rerun-draft.md
rubric: findings/interaction-mode-variance-rubric.md @ 49d86f7
tsv_inputs: aggregate-singlemodel.tsv, ratios-singlemodel.tsv, sessions-dedup.tsv
reviewer_model: claude-sonnet-4-6
date: 2026-04-19
single_model_qualifying: 501
---

# Adversarial Review — Interaction-Mode-Variance Rerun

## §1 Factual errors

Verified ≥5 numeric claims against TSVs before writing this section.

**Verified correct (pairs checked):**
| Draft claim | TSV source | Value | Match |
|---|---|---|---|
| 52.7× passenger/governor means | ratios-singlemodel.tsv row passenger/governor | 52.677 | ✓ |
| 21.6× passenger/governor medians | ratios-singlemodel.tsv | 21.647 | ✓ |
| 232× passenger/pipe means | ratios-singlemodel.tsv | 232.029 | ✓ |
| 512× passenger/pipe medians | ratios-singlemodel.tsv | 512.051 | ✓ |
| 241× outlier-removed means passenger/pipe | ratios-singlemodel.tsv | 240.881 | ✓ |
| Pipe mean 751, median 136 | aggregate-singlemodel.tsv | 751, 136 | ✓ |
| Collaborator mean 34,463, median 15,035 | aggregate-singlemodel.tsv | 34463, 15035 | ✓ |
| Passenger mean 174,254, median 69,639 | aggregate-singlemodel.tsv | 174254, 69639 | ✓ |
| 27 -tmp/-tmp-exp4 sessions totaling 67,343 tokens | sessions-dedup.tsv rows 495–521 | 10 + 17 = 27 sessions; sum = 67,343 | ✓ |
| Correction rates 0.919 / 0.238 / 0.273 / 0.274 | aggregate-singlemodel.tsv | 0.918782 / 0.238095 / 0.273109 / 0.273541 | ✓ (within stated rounding) |

**Errors found:**

**Error 1 — total single-model token count and passenger share (Mechanism section).**

Draft states: "70 passenger sessions carry ~12.2M of ~13.7M total single-model qualifying tokens (~89%)."

From aggregate-singlemodel.tsv, sum of `sum_total_tokens`:
296,054 + 29,768 + 964,975 + 12,197,814 = **13,488,611** (~13.5M, not ~13.7M).

Passenger share: 12,197,814 / 13,488,611 = **90.4%**, not 89%.

The 13.7M figure is overstated by ~211K tokens (~1.6%). The 89% claim underestimates the passenger share by ~1.4 percentage points.

**Error 2 — pipe mean after methodology-session removal (Confounds section).**

Draft states: "Removing them shifts pipe mean from 751 to ~613."

Calculation from TSV: (296,054 − 67,343) / (394 − 27) = 228,711 / 367 = **~623**, not ~613.

The draft's stated removal effect is off by ~10 tokens per session. The directional claim ("does not change the mode ordering") is unaffected, but the stated value is wrong.

---

## §2 Framing drift

**Unsupported causal attribution (Mechanism section, paragraph 3).**

Draft states: "Output dominates input across all modes. This is a property of Claude Code's tool-heavy, code-emitting workload, not of interaction mode."

The observation that output/input ratios do not discriminate mode is supported by the data. The attribution to "tool-heavy, code-emitting workload" as the *cause* is not derivable from this corpus: the data shows ratios, not workload categories. This is a causal claim where the evidence is observational. The phrase "not of interaction mode" is also inferential — the corpus cannot rule out mode-correlated workload variation; it observes that the ratio does not vary strongly across modes.

No other significant framing drift found.

---

## §3 Missing limitations

**Mixed-model exclusion implementation not described.**

The draft states 14 sessions were excluded as mixed-model ("sessions with more than one `model_id` recorded across assistant messages") but does not describe how the extractor detected this. The `sessions-dedup.tsv` has a `mixed_model` flag in column 14, but the mechanism that sets that flag — e.g., whether it counts distinct `model_id` values across all assistant messages, whether it captures mid-session model switches vs. multi-model comparisons, whether it was set by the extractor or injected at aggregation — is not disclosed. A replicator implementing their own extractor has no specification to follow for this step.

No other missing limitations found. The draft discloses: mode-vs-tokens tautology (§Mechanism and §Confounds), methodology-experiment contamination with quantified effect (§Confounds), subagent dedup via path filter with spot-check sample and caveats (§Confounds), correction-keyword false-positive behavior on pipe mode (§Confounds), session_id format deviation from rubric (§Confounds), and extractor dispatch prompt deviation (§Confounds).

---

## §4 What to cut

**Cut 1 — causal attribution sentence in Mechanism.**

"This is a property of Claude Code's tool-heavy, code-emitting workload, not of interaction mode." (Mechanism section, paragraph 3, second sentence.) This is framing drift (§2 above). The immediately following observation ("Output-share holds in pipe sessions (92.6%) and in passenger (98.3%), so it is not a mode discriminator in this corpus") stands without it.

**Cut 2 — subagent spot-check in Measurement section.**

Measurement section, filter step 2: "Spot-check of 10 subagent paths confirmed each parent was present in the TSV; no non-subagent exclusions applied." This is substantially duplicated by the Confounds bullet: "Spot-check on 10 randomly selected subagent files confirmed each parent (UUID-prefix-matched file) was in the corpus, so the path filter did not over-exclude in the sampled set. Sample size is 10; a replicator can compute parent presence deterministically from the TSV." The Confounds version is more complete. The Measurement mention adds nothing a reader of Confounds does not already have.

**Cut 3 — terminal Confounds bullet.**

"Single operator, single node, single window. Same corpus-class as the original. No cross-operator or cross-node replication." This is fully covered by the header (`corpus:` field) and the Claim section ("single operator / single node," "same corpus as the original finding"). As a confounds bullet it adds nothing a replicator cannot read from the header.
