---
title: Adversarial review of rerun-draft.md (v2)
rubric_commit: 49d86f7
reviewed_utc: 2026-04-19
---

# Review

## 1. Factual errors

Verified pairs (draft vs TSV), all matching:

- Single-model qualifying N = 501 — confirmed from `sessions-dedup.tsv` via column 14/15 tallies (501 rows with `mixed_model=0, qualifying=1`; 14 with `mixed_model=1`; 5 with `qualifying=0`).
- Per-mode N: pipe 394, governor 9, collaborator 28, passenger 70 — match `aggregate-singlemodel.tsv` col 2.
- Per-mode mean total tokens: 751 / 3,308 / 34,463 / 174,254 — match TSV col 4.
- Per-mode median total tokens: 136 / 3,217 / 15,035 / 69,639 — match TSV col 5.
- Outlier-removed means: 631 / 3,017 / 19,416 / 151,996 — match TSV col 16.
- Outlier-removed medians: 136 / 2,899 / 14,855 / 69,398 — match TSV col 17.
- Correction rates: pipe 0.919, governor 0.238, collaborator 0.273, passenger 0.274 — match TSV col 15 to three decimals (0.918782 / 0.238095 / 0.273109 / 0.273541).
- Multipliers: passenger/governor mean 52.7 (TSV 52.677), median 21.6 (TSV 21.647), outlier-removed mean 50.4 (TSV 50.380); passenger/pipe mean 232 (232.029), median 512 (512.051), outlier-removed 241 (240.881); passenger/collaborator mean 5.06 (5.056), median 4.63 (4.632).
- Mixed-model mode distribution: 13 passenger / 1 collaborator — confirmed from `sessions-dedup.tsv` rows where col 14 = 1.
- Pipe output share 92.6% — 274,203 / 296,054 = 0.9262. Match.

Discrepancies found:

- Draft §Mechanism bullet 2: "~12.2M of ~13.7M total single-model qualifying tokens (~89%)". TSV sum across modes = 296,054 + 29,768 + 964,975 + 12,197,814 = **13,488,611** (~13.49M, not ~13.7M). Passenger share = 12,197,814 / 13,488,611 = **90.43%**, not ~89%.
- Draft §Mechanism bullet 3: "passenger (98.3%)" output share. 11,998,559 / (199,255 + 11,998,559) = **98.37%**. Rounds to 98.4%, not 98.3%.
- Draft §Confounds bullet 3: "Removing them shifts pipe mean from 751 to ~613." Using the draft's own inputs (296,054 − 67,343) / (394 − 27) = 228,711 / 367 = **623.2**, not ~613. (The 22.7% of-pipe share and the 0.49% of-whole-corpus share round to 22.74% and 0.499% — the whole-corpus share is nearer 0.50% than 0.49%, a small but one-sided rounding.)

## 2. Framing drift

- Rubric §Aggregation requires multiplier-style headlines to be "reported **alongside** the median ratio and the outlier-removed ratio, never in isolation." The draft §Multipliers gives outlier-removed for passenger/governor and passenger/pipe, but **omits outlier-removed for passenger/collaborator (TSV: 7.828) and for collaborator/governor (TSV: 6.436)**. The collaborator/governor line reports only "~10× means, ~5× medians" and skips outlier-removed entirely. This violates the rubric's "never in isolation" clause for two of the four pairwise headlines.
- Claim paragraph: "The original finding's 41× headline ... does not reproduce by coincidence of number; it is re-observed as a same-direction, different-magnitude ordering on a larger, differently-composed corpus." This reframes a non-reproduction of magnitude as a reproduction of direction. The original's 41× was on means; the rerun's 52.7× is on means computed over a corpus with materially different mode-share (governor went from 38.6% → 1.8% of N). Calling this "re-observed" smuggles continuity across two corpora that the draft itself later says "is not the original corpus plus an increment."
- §Mechanism bullet 2: "Passenger sessions dominate tokens despite being 14% of single-model count" frames a mechanical consequence of the rubric (mode = f(turns); turns ≈ tokens) as a finding about operator behavior. The draft's own Mechanism bullet 1 already acknowledges this tautology; bullet 2 nevertheless rhetorically presents it as substantive domination.
- §Mechanism bullet 3: "Output dominates input across all modes. This is a property of Claude Code's tool-heavy, code-emitting workload, not of interaction mode." Causal claim ("property of ... workload") without evidence in the analysis; the TSVs show only the I/O ratio, not a mechanism.
- §Claim: "a 12×-larger ... corpus." 1075/88 = 12.2, but 1075 is the raw JSONL count and 88 was the original's qualifying N. The comparable ratio on qualifying single-model is 501/88 ≈ 5.7×. The "12×" framing compares pre-filter count to post-filter count.
- §Claim: "232× / 512× pipe-baseline multipliers per rubric §Aggregation." The phrase "per rubric §Aggregation" implies the rubric prescribes these specific headlines; it prescribes only how multipliers are reported, not which baseline is featured. Minor but smuggles normative weight onto a presentation choice.

## 3. Missing limitations

- **Mixed-model exclusion is not mode-balanced.** 13 of 14 excluded mixed-model sessions are passenger, 1 is collaborator. The exclusion removes ~15.7% of passenger-class sessions (13/83) but <4% of collaborator-class (1/29) and 0% of governor/pipe. The draft reports the counts but does not flag that the mixed-model filter is a selective trim of the passenger tail — the same tail whose mean drives the 52.7× headline. A replicator comparing to a dataset without this exclusion would see a different passenger mean.
- **Methodology-experiment contamination is only partially enumerated.** The draft carves out `-tmp/` and `-tmp-exp4/` (27 pipe-mode sessions). It does not check whether sessions in other project directories (e.g., `-home-hodori`, `-f3rerun`, the rerun's own extractor/aggregator dispatches) were produced by the analysis pipeline itself. The current rerun is itself a methodology-producing session set; some of its dispatched runs may already be in the corpus_window ending 2026-04-19T17:18:25Z.
- **Subagent dedup spot-check sample = 10.** The path filter removed 555 rows; a replicator cannot infer parent-UUID coverage from a 10-file sample. The draft notes a replicator "can compute parent presence deterministically from the TSV" but does not perform the full computation itself.
- **Correction-keyword false-positive mechanism on pipe is acknowledged but not quantified.** The draft explains the pipe rate 0.919 measures "fraction of pipe sessions whose single prompt contains at least one keyword substring," but does not disclose which keyword(s) dominate the matches on pipe prompts (e.g., how many matches come from "fix" or "stop" appearing innocuously in a single-shot prompt). Without that breakdown the 0.919 is uninterpretable.
- **Mode-vs-tokens tautology is disclosed in Mechanism but not gated in the headline Claim.** The Claim paragraph reports the 52.7× multiplier without the turn-normalization caveat that Mechanism/Confounds carry. A reader stopping at the Claim gets an un-gated number.
- **No stratification by model_id across single-model.** "Single-model" here groups claude-opus-4-5-20251101, claude-opus-4-6, claude-opus-4-7 (and possibly others) within the same mode aggregate. A replicator cannot tell from the published aggregate whether the mode ordering holds within each model, or whether the ratios shift across model versions.
- **No billing-data verification** (rubric lists as out-of-scope but the draft does not restate this in Confounds).
- **Non-qualifying row count (5) is disclosed but not broken down.** Draft does not say how many are zero-human-turn vs zero-assistant-response.
- **Single window.** Confound list mentions single operator / single node / single window but does not note that passenger-class sessions are concentrated in specific date ranges (visible in `sessions-dedup.tsv` utc_start column); mode-share may be a window artifact.

## 4. What to cut

- §Claim, sentence beginning "The original finding's 41× headline ... does not reproduce by coincidence of number": rhetorical flourish, adds no number. Cut or replace with bare "does not reproduce in magnitude."
- §Measurement "Filter sequence" item 2 parenthetical "Spot-check of 10 subagent paths confirmed each parent was present in the TSV; no non-subagent exclusions applied." — duplicates the §Confounds subagent-dedup bullet. Keep one.
- §Mechanism bullet 3 ("Output dominates input across all modes. ... not a mode discriminator in this corpus.") — not tied to the claim; if kept, it should be moved to a descriptive appendix rather than Mechanism.
- §Comparison to original finding, final paragraph "The rerun corpus is not the original corpus plus an increment..." — the disclaimer is correct but redundant with §Confounds' corpus-scope bullet. One location is enough.
- §Confounds bullet "session_id format deviates from rubric." — rubric-compliance nit with no effect on any numeric claim. Move to a compliance note or cut.
- §Confounds bullet "No cross-lineage extractor. ... Adversarial review of the writeup was performed by a different model instance" — the review-process self-reference does not belong in the Confounds list of the artifact under review.
- §Confounds final bullet "Pre-commitment is filesystem-timestamped and git-committed, not hash-signed." — commit-contract provenance, not a confound of the measurement. Move to front-matter or cut.
