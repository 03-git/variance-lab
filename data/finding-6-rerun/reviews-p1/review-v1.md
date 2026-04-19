---
title: Adversarial review of rerun-draft.md
date: 2026-04-19
reviewer_node: rousseau (01)
rubric_commit: 49d86f7
---

# Review

Verified against `aggregate-singlemodel.tsv`, `ratios-singlemodel.tsv`, `sessions-dedup.tsv`.

## 1. Factual errors

Numeric claims verified against the TSVs (at least five required; 13 verified):

1. Per-mode N (394 / 9 / 28 / 70) — draft table row 36–39 — matches `aggregate-singlemodel.tsv` col `n_sessions`.
2. Per-mode mean_total (751 / 3,308 / 34,463 / 174,254) — draft table row 36–39 — matches TSV col `mean_total_tokens`.
3. Per-mode median_total (136 / 3,217 / 15,035 / 69,639) — draft table row 36–39 — matches TSV col `median_total_tokens`.
4. Outlier-removed means (631 / 3,017 / 19,416 / 151,996) and medians (136 / 2,899 / 14,855 / 69,398) — draft row 36–39 — matches TSV cols `*_outlier_removed`.
5. Total human turns (394 / 21 / 238 / 5,363) and total tool calls (93 / 67 / 862 / 14,823) — matches TSV.
6. Correction rates (0.919 / 0.238 / 0.273 / 0.274) — draft row 36–39 — matches TSV (0.918782, 0.238095, 0.273109, 0.273541).
7. Passenger/governor 52.7× means, 21.6× medians, 50.4× outlier-removed — draft line 45 — matches `ratios-singlemodel.tsv` row 12 (52.677 / 21.647 / 50.380).
8. Passenger/pipe 232× / 512× / 241× — draft line 46 — matches ratios row 11 (232.029 / 512.051 / 240.881).
9. Passenger/collaborator 5.06× / 4.63× — draft line 47 — matches ratios row 13 (5.056 / 4.632).
10. Mixed-model mode distribution 13 passenger / 1 collaborator — draft line 52 — confirmed by filtering `sessions-dedup.tsv` on `mixed_model==1`.
11. Filter arithmetic 1075 − 555 − 5 − 14 = 501 — draft lines 26–30 — consistent with 520-row dedup TSV (1075 − 555) and 14 mixed-model / 5 non-qualifying rows in that file.
12. Pipe output-share 92.6% — draft line 73 — 274,203 / 296,054 = 0.9262. Matches.
13. Passenger mode-share 70/501 = 13.97% — draft line 71 "14%". Matches.

Discrepancies:

- **Draft line 71: "~12.2M of ~13.7M total single-model qualifying tokens (~89%)"**. TSV totals: 296,054 + 29,768 + 964,975 + 12,197,814 = **13,488,611** (~13.5M, not ~13.7M). Passenger share = 12,197,814 / 13,488,611 = **0.9043** (~90.4%, not ~89%). Both numbers in this sentence miss.
- **Draft line 83: "Removing them shifts pipe mean from 751 to ~613"**. Arithmetic with draft's own inputs (pipe total 296,054 − 67,343; N 394 − 27): 228,711 / 367 = **623.2**. Draft value of ~613 is ~10 off. Possible digit transposition.
- **Draft line 73: passenger output-share 98.3%**. TSV: 11,998,559 / 12,197,814 = 0.98367 → **98.4%** to one decimal. Off by one unit in last place; minor.

## 2. Framing drift

- **Claim paragraph (line 15) reports 232× / 512× for passenger-vs-pipe without the outlier-removed companion** (241×, present in Multipliers §). Rubric §Aggregation: multipliers "reported **alongside** the median ratio and the outlier-removed ratio, never in isolation." The outlier-removed triple appears later, but the headline sentence isolates means + medians only. For passenger/governor the claim paragraph does cite 52.7 / 21.6 only, omitting 50.4×.
- **Line 48, collaborator-vs-governor: "order of magnitude 10× on means, ~5× on medians"** omits the outlier-removed ratio (TSV: 6.436). Same rubric §Aggregation rule. Also "~5×" rounds 4.674 upward where prior rows round to two decimals.
- **Line 47, passenger-vs-collaborator: 5.06× / 4.63× with no outlier-removed.** TSV outlier-removed ratio is **7.828** — materially higher than the mean ratio, meaning the largest collaborator session is dragging collaborator mean up more than the largest passenger session drags passenger mean up. Omitting it understates the dispersion in the collaborator cell. Rubric-non-compliant and substantively informative.
- **Line 15 "52.7× on means and 21.6× on medians"** leads with the mean, which the rubric permits but requires paired presentation. Paired in the later table; headline framing still privileges the mean by listing it first.
- **Line 69 "More turns produce more assistant output"** — correlational in this corpus is presented as mechanical ("mechanically correlated"). The paragraph does disclose the confound, but the word "mechanical" imports a causal interpretation that the rubric does not license. Mitigated by the same paragraph's "this rerun does not decompose the two."
- **Line 65 "Mode-share differences below should be read as properties of the two corpora, not as time-series evidence that the operator's behavior changed"** — appropriate hedge, no drift.
- **Line 15 "does not reproduce by coincidence of number; it is re-observed as a same-direction, different-magnitude ordering"** — accurate characterization, no drift.

## 3. Missing limitations

- **Mixed-model exclusion: mode-assignment semantics for excluded sessions not specified.** Draft reports "13 passenger, 1 collaborator" mode distribution for mixed-model rows, implying `mode` was still computed. `mode` is a pure function of `human_turns`, so this is internally consistent, but the draft does not state whether the mixed-model sessions' tokens are sums across both models or are assigned to one model_id at aggregation time. A replicator cannot reproduce the 14-row mixed-model table without this.
- **Methodology-contamination disclosure is pipe-only.** Line 83 quantifies 27 pipe sessions from `-tmp/` and `-tmp-exp4/`. Draft does not state whether any governor / collaborator / passenger sessions originated from the same methodology work (e.g., handler-methodology / f5panel sessions that grew past 1 turn). If none, say so. If some, the same carve-out should be reported per mode.
- **Subagent dedup spot-check N=10 out of 555 excluded rows** (line 26 and line 85). ~1.8% sample. No false-negative analysis (subagent children whose path does not contain `/subagents/` and were therefore retained as sessions). Rubric's exclusion condition is "parent transcript already counted," which is strictly weaker than a path filter in one direction and strictly stronger in the other. The draft acknowledges the direction of deviation but not the sample's statistical reach.
- **Correction-keyword false-positive mechanism on pipe disclosed (line 89), but not on governor.** Governor N=9 with 5 correction flags across 21 turns — the rate 0.238 at this N is a 5-flag count; a single keyword-bearing "actually" or "stop" in a scoped directive moves the rate by ~0.05. The draft mentions sensitivity but does not quantify.
- **Mode-vs-tokens tautology disclosed (line 79), but no tokens-per-turn figures reported** to let a reader see the residual per-turn effect after mechanical removal. Rubric does not require it; omission is defensible. Noting it per the review-prompt checklist.
- **Draft line 65 asserts "12×-larger corpus"** — file-count ratio (1075/88 ≈ 12.2) not qualifying-session ratio (501/88 ≈ 5.7). Ratio choice not disclosed; both are defensible but the reader will assume the qualifying ratio.
- **Line 97 "adversarial review of the writeup was performed by a different model instance (different effort tier) prior to this version; the arithmetic was spot-verified by the reviewer against the TSVs"** — self-attestation, not a confound. Does not disclose scope of the spot-check (which numbers, how many).
- **Line 93 "Extractor dispatch prompt deviated from rubric at one step ... caught in spot-check and corrected at aggregation via the path filter."** Corrected-at-aggregation means the emitted extractor TSV is rubric-non-compliant as-extracted; the single-model aggregate is rubric-compliant only if the path filter is applied in every downstream consumer. A replicator running the extractor directly without the aggregator's path filter would get non-rubric output.

## 4. What to cut

- **Line 97 ("No cross-lineage extractor" confound)** — the sentence about "adversarial review of the writeup was performed by a different model instance" is meta-narrative about process, not a confound on the finding. Belongs in methodology notes if anywhere; does not serve the claim.
- **Line 99 ("Pre-commitment is filesystem-timestamped and git-committed, not hash-signed")** — this is a property of the commit mechanism, not a confound on the numeric result. The rubric-commit line in the frontmatter already establishes this; restating in Confounds adds no information about what a replicator should mistrust.
- **Line 91 ("session_id format deviates from rubric")** — a naming convention deviation with no downstream effect on any reported number. One sentence acknowledging it is sufficient; the current two-sentence treatment plus "Functionally adequate" editorializing is longer than the issue warrants.
- **Line 87 ("5 rows in the dedup TSV are non-qualifying")** — already stated in the filter-sequence bullet at line 27. Duplicates the filter-sequence disclosure; the Confounds restatement is redundant.
- **Line 73 ("Output dominates input across all modes ... so it is not a mode discriminator in this corpus")** — true but the finding does not claim output/input is a mode discriminator. The paragraph refutes a claim the rerun is not making. Trimming to one sentence or removing would tighten Mechanism §.
