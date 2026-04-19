---
title: Second-pass adversarial review of rerun-draft.md
rubric_commit: 49d86f7
rubric_sha256: 4223396958c219045c928c77951a30d3aae86ddacc56c08bc7300891ce7bb379
reviewed_utc: 2026-04-19
---

# Pre-review numeric verification

Verified against aggregate-singlemodel.tsv, ratios-singlemodel.tsv, sessions-dedup.tsv:

1. N pipeline: 520 rows in sessions-dedup.tsv − 5 (qualifying=0) − 14 (mixed_model=1, qualifying=1) = 501 single-model qualifying. ✓
2. Means (sum/n from aggregate TSV): pipe 296054/394=751.4, governor 29768/9=3307.6, collab 964975/28=34463.4, passenger 12197814/70=174254.5. All ✓.
3. Multipliers against ratios-singlemodel.tsv: 174254/3308=52.68 (52.7×), 69639/3217=21.65 (21.6×), 151996/3017=50.38 (50.4×), 69639/136=512.05, 151996/19416=7.83. ✓
4. Correction rates: 362/394=0.9188, 5/21=0.2381, 65/238=0.2731, 1467/5363=0.2735. ✓
5. Passenger outlier drop: (12197814−1710089)/69 = 151996.01; (174254−151996)/174254 = 12.77%. ✓
6. Mode-share recomputes (394/501=78.64%, 9/501=1.80%, 28/501=5.59%, 70/501=13.97%). ✓
7. Original comparison shares (19/88=21.59%, 34/88=38.64%, 25/88=28.41%, 10/88=11.36%) and original 41× = 23658/576=41.07. ✓
8. Passenger token share 12197814 / (296054+29768+964975+12197814) = 12197814/13488611 = 90.43%. ✓
9. Pipe recompute without -tmp: (296054−67343)/367 = 623.19, and 67343/296054 = 22.75%, 67343/13488611 = 0.499%. ✓
10. Rubric sha256 and commit 49d86f7 match the hash / commit asserted in the draft's front-matter. ✓

Numerics in the draft are internally consistent with the supplied TSVs. Nothing in the body contradicts the tables. Issues below are about framing, not arithmetic.

---

## 1. Factual errors

- **"12×-larger" corpus comparison mixes pre-filter and post-filter populations.** The draft writes "The rerun corpus is not the original corpus plus an increment. It is a 12×-larger, differently-scoped set of files." The original N=88 was already post-qualifying (pipe 19 + governor 34 + collaborator 25 + passenger 10 = 88). The rerun's 1075 is the pre-filter file count; the post-filter, post-dedup, single-model qualifying count is 501 (ratio 5.69×) and the qualifying-before-mixed-model count is 520 (ratio 5.91×). "12×" is only true if you compare raw-file-count-rerun to qualifying-session-count-original, which is the wrong comparison. Fix: say "~5.7× larger by qualifying-session count" or "~12× larger by raw JSONL file count (1075 vs the original's unfiltered intake, not its 88 qualifying sessions)."

- **"13 passenger, 1 collaborator" mixed-model count is reported but the distributional implication is not acknowledged as factual content.** 13 of 14 excluded-as-mixed-model sessions are passengers; that is 13/(13+70) = 15.7% of the otherwise-passenger pool lost to the exclusion, vs 1/29 = 3.4% of the collaborator pool and 0% of pipe/governor. The exclusion is rubric-mandated, but the draft's Mixed-model section describes this as "not informative for single-model comparisons" without noting that the exclusion disproportionately trims the high-token mode. That shifts the passenger aggregate in unknown ways. (Not an arithmetic error — a factual claim of symmetric treatment that isn't quite right.)

## 2. Framing drift

- **"Re-observed as a same-direction, different-magnitude ordering" (Claim).** The original headline was passenger/governor = 41×; the rerun produces 52.7× mean / 21.6× median / 50.4× outlier-removed. The median is half the original headline. Calling this "re-observed" is defensible on ordering alone but the draft leans on it to do rehabilitation work for the original finding. Suggested reframing: "ordering re-observed; the specific magnitude does not reproduce — original 41× sits between the rerun's mean and median, closer to neither than to the other."

- **Bolding of passenger-vs-collaborator 7.83× outlier-removed ratio.** The three bolded numbers in the Claim and Multipliers section (21.6×, 52.7×, 50.4×, 7.83×) are the largest or most-headline-friendly values in each triple. The draft does explain the 7.83× anomaly, but bolding it still gives visual weight to the highest number rather than (e.g.) the median-based one. Per rubric §Aggregation "never in isolation" — the triples are all present, but typographic emphasis amounts to selecting within the triple.

- **Correction rate framing for pipe.** The draft calls pipe's 0.919 "the committed computation" and explains it, but the sentence "a different quantity from the retroactive-correction connotation in collaborator and passenger modes" buries the lede. 91.9% of single-shot pipe prompts containing one of {no, don't, fix, ...} as a substring is almost certainly keyword-noise (e.g., "no " as part of "note", "fix" as part of "fixture", "actually" as polite hedging) and the correction-rate column for pipe is probably meaningless as a correction signal. Rubric fixed the keyword set pre-commit, so the number must be reported, but the framing understates how empty it is.

- **"The 41× headline ... is re-observed" collides with the draft's own median emphasis.** If medians are the stable-against-outlier metric that justified adding them to the rubric, the median-ratio of 21.6× is the comparable figure to the original headline. The draft presents both but the Claim paragraph puts the mean (52.7×) first and leads with it. This reads as preserving-the-original-direction-of-surprise rather than presenting the median-first frame the rubric's outlier-sensitivity machinery implies.

## 3. Missing limitations

- **Within-single-model pool, model identity is not controlled.** The draft's Mechanism and Confounds sections flag that per-model breakdown is out of scope, but do not note that the single-model pool can still mix Opus / Sonnet / Haiku across sessions. A passenger-mode Opus 4.7 session vs a pipe-mode Haiku 4.5 session produces a token ratio that partly reflects model choice. Rubric §Scoring item 2 handles within-session model mixing; it is silent on across-session model heterogeneity, and the draft inherits that silence.

- **Subagent dedup via `/subagents/` path filter is a string-match heuristic.** The draft discloses that dedup was done via path filter rather than rubric-compliant parent-child matching and that a spot-check of 10 subagent paths confirmed parents present. It does not state what fraction of 555 removed rows were verified, nor whether any non-`/subagents/` path convention exists in the corpus that would leave a subagent child un-matched. 10/555 = 1.8% spot-check coverage; the confidence it grants is limited.

- **session_id deviation from rubric is flagged but its implication for replication is not stated.** Rubric §Scoring item 1 fixes sha/hash; extractor emits file paths. The draft notes the deviation in the Confounds section's last two bullets but does not state that this makes cross-node replication (if ever attempted) harder because file paths are local to the node.

- **Corpus window is a snapshot, not a stratum.** Draft writes "through 2026-04-19T17:18:25Z" but does not state the earliest timestamp in the corpus. Without the window start, the reader cannot judge whether the single-operator behavior being measured is stable, seasonal, or trending. The original finding had a single date (2026-03-30); the rerun has a right-boundary only.

- **No check that the mixed-model sessions' mode distribution is consistent with the rubric-excluded behavior being uninformative.** The draft reports the 13-passenger / 1-collaborator split and then states these are "not informative for single-model comparisons." A one-sentence sanity check on their total token volume vs the single-model aggregate would let the reader see how much mass was moved outside the comparison.

- **Pipe correction-rate confound is stated but its effect on cross-mode comparison is not.** Because pipe's correction rate is keyword-substring noise and governor/collaborator/passenger are closer to retroactive-correction signal, the mode-over-mode correction-rate column is not a like-for-like comparison. The draft's Confounds bullet acknowledges the meaning difference for pipe but does not explicitly warn readers off cross-mode correction-rate comparisons.

## 4. What to cut

- **Collaborator-vs-governor multiplier bullet** ("10.4× / 4.67× / 6.44× (N=9 governor makes these wide)"). Governor N=9; the bullet adds a triple that the draft itself caveats as un-tight, and none of the Mechanism or Claim discussion leans on it. Keep the single headline passenger/governor line; drop this one.

- **"No non-subagent exclusions applied"** (Measurement filter-sequence item 2). Dead clause — it states that a non-applied filter was not applied. If all exclusions are enumerated in the list, the absence of others is implicit.

- **"Extractor is single-implementation; aggregator arithmetic was spot-verified by cross-lineage reviewers against the TSVs prior to writeup"** (final Confounds bullet). This is methodology-hygiene self-assurance that belongs in a pre-commit contract, not a confounds list. The interesting single-operator / single-node / single-window caveat in the same sentence should stand alone.

- **Comparison-to-original sub-table governor row.** Original governor N=34 (38.6%) vs rerun N=9 (1.8%) is a 21× mode-share shift. The draft footnote says not to read this as time-series evidence, which is correct — so the table invites a reading the draft tells the reader not to make. Either cut the table (keep only the passenger-share-and-tokens narrative in Mechanism) or replace with a one-line "mode-share composition differs sharply; do not interpret as drift."

- **"Full per-mode file: `aggregate-singlemodel.tsv`"** pointer at end of per-mode table. Already front-matter-adjacent and redundant with the artifacts listed in the supersedes/corpus header block — trim if the finding is published with its artifacts co-located.

---

## Residual

None of the above invalidates the ordering claim (passenger > collaborator > governor > pipe on both means and medians) or the magnitudes in the TSVs. The rerun is rubric-compliant on every gate the rubric actually sets (thresholds, keyword set, aggregation triples, mixed-model exclusion, outlier-sensitivity). The issues above concern (a) one corpus-size comparison that inflates the apparent scale jump from original to rerun, (b) framing choices around which number in each triple leads, and (c) a handful of omitted limitations that a skeptical replicator would want stated.
