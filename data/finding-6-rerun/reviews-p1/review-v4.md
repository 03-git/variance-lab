---
review_of: rerun-draft.md
rubric_ref: rubric.md @ 49d86f7
tsv_sources: aggregate-singlemodel.tsv, ratios-singlemodel.tsv, sessions-dedup.tsv
single_model_qualifying: 501
reviewer_node: rousseau
date: 2026-04-19
---

# Adversarial Review — Interaction-Mode-Variance Rerun (v4)

## §1 Factual errors

**Verified pairs (5 minimum required):**

| Claim (draft) | TSV value | Match? |
|---|---|---|
| passenger/governor mean 52.7× | ratios TSV: 52.677 | ✓ |
| passenger/governor median 21.6× | ratios TSV: 21.647 | ✓ |
| passenger/pipe mean 232× | ratios TSV: 232.029 | ✓ |
| passenger/pipe median 512× | ratios TSV: 512.051 | ✓ |
| passenger/collaborator 5.06× means | ratios TSV: 5.056 | ✓ |
| passenger/collaborator 4.63× medians | ratios TSV: 4.632 | ✓ |
| outlier-removed passenger/governor mean 50.4× | ratios TSV: 50.380 | ✓ |
| pipe correction rate 0.919 | aggregate TSV: 0.918782 | ✓ |
| passenger output share 98.3% | computed 98.37% (11,998,559 / 12,197,814) | ✗ |
| total single-model tokens ~13.7M | computed sum: 13,488,611 (~13.5M) | ✗ |
| passenger token share ~89% | computed 12,197,814 / 13,488,611 = 90.4% | ✗ |

**Error 1 — Total single-model token count and derived passenger share.**
Draft (Mechanism §): "70 passenger sessions carry ~12.2M of ~13.7M total single-model qualifying tokens (~89%)."
TSV sum: 296,054 + 29,768 + 964,975 + 12,197,814 = **13,488,611** (~13.5M, not ~13.7M).
Passenger share: 12,197,814 / 13,488,611 = **90.4%**, not ~89%.
The ~13.7M figure is ~211k high; the 89% figure is understated by ~1.4 percentage points.

**Error 2 — Passenger output share.**
Draft (Mechanism §): "Output-share holds in pipe sessions (92.6%) and in passenger (98.3%)."
Computed: 11,998,559 / 12,197,814 = **98.37%**, which rounds to **98.4%**, not 98.3%.
Pipe output share 92.6% (274,203 / 296,054 = 92.62%) is correct.

---

## §2 Framing drift

**FD-1 — "12×-larger" corpus comparison mixes incompatible bases.**
Draft (Comparison §): "It is a 12×-larger, differently-scoped set of files."
The 12× figure comes from 1075 total JSONL files / 88 original qualifying sessions. These are not the same quantity. Qualifying-to-qualifying is 501 / 88 = **5.7×**. "12×-larger" overstates the corpus expansion relative to what the original measured. The sentence should specify which base is being compared (total files vs. qualifying sessions) or drop the scalar and say only "differently-scoped."

**FD-2 — Output-share conclusion drawn from two-mode sample.**
Draft (Mechanism §): "Output-share holds in pipe sessions (92.6%) and in passenger (98.3%), so it is not a mode discriminator in this corpus."
Only two of the four modes are cited; the conclusion applies to all four. The 5.8-percentage-point difference between the two cited modes is also a mode-discriminating signal, contradicting the claim. The conclusion is at best premature and at worst false. Governor (28,989 / 29,768 = 97.4%) and collaborator (942,823 / 964,975 = 97.7%) can be computed from the aggregate TSV and are omitted.

---

## §3 Missing limitations

**ML-1 — Model heterogeneity within the "single-model" pool is not disclosed.**
"Single-model" in the rubric and draft means no mid-session model switch, not that all sessions used the same model. The sessions-dedup.tsv shows at least three distinct model_ids in the single-model pool (claude-opus-4-5-20251101, claude-sonnet-4-6, claude-opus-4-7). Models differ in default verbosity and output length. The per-mode means pool heterogeneous models; a passenger-mode session on claude-opus-4-7 and one on claude-opus-4-5-20251101 are summed together. This is a confound not mentioned in §Confounds. A replicator who wants to attribute the passenger/governor multiplier to interaction mode rather than model mix cannot do so from this data.

**ML-2 — Passenger outlier size omitted; rubric-referenced size does not match.**
The rubric §Aggregation states the outlier-sensitivity metric was introduced "specifically to address the 152k-token / 53-subagent outlier's material effect on the passenger-mode average." The aggregate TSV records the actual dropped passenger session as **1,710,089 tokens** — 11.3× the rubric's referenced 152k. The draft omits this figure. A reader sees that "passenger mean = 174,254, median = 69,639" and "outlier-removed mean = 151,996" without knowing that a single session of 1.71M tokens drives that ~22k mean reduction. The magnitude of the dropped session is material to interpreting the mean/median divergence and should be stated.

---

## §4 What to cut

**Cut-1 — Self-referential attestation in "No cross-lineage extractor" bullet.**
Last two sentences: "Adversarial review of the writeup was performed by a different model instance (different effort tier) prior to this version; the arithmetic was spot-verified by the reviewer against the TSVs."
This is not a confound disclosure. It is procedural self-attestation inserted into a document currently undergoing external adversarial review. It says nothing about what the reviewer found or what was corrected; it only asserts the process occurred. Cut.

**Cut-2 — Unsupported causal attribution in governor mean/median note.**
Mechanism §: "Governor means and medians agree (3,308 vs 3,217) because N=9 and the distribution is tight."
No distribution width data (SD, IQR, range) is provided. "Distribution is tight" is asserted without evidence. Near-equality of mean and median is consistent with low skew but does not require a tight distribution. Cut the causal clause ("because N=9 and the distribution is tight"); leave only the observation that means and medians agree.
