---
title: Second-pass adversarial review of rerun-draft.md
date: 2026-04-19
reviewer: Claude (Rousseau node)
rubric_verified: 49d86f7, sha256 4223396958c219045c928c77951a30d3aae86ddacc56c08bc7300891ce7bb379
numeric_claims_verified: 8+
---

# Second-Pass Adversarial Review — rerun-draft.md

## Pre-review numeric verification

Verified against aggregate-singlemodel.tsv and ratios-singlemodel.tsv:

1. Single-model qualifying N=501 (394+9+28+70) ✓
2. Pipe: N=394, mean=751, median=136 ✓
3. Governor: N=9, mean=3308, median=3217 ✓
4. Collaborator: N=28, mean=34463, median=15035 ✓
5. Passenger: N=70, mean=174254, median=69639 ✓
6. Passenger/governor multiplier: 52.677/21.647/50.380 (draft rounds to 52.7×/21.6×/50.4×) ✓
7. Passenger token share: 12,197,814 / 13,488,611 = 90.43% (draft says 90.4%) ✓
8. Pipe correction rate: 0.918782 (draft says 0.919) ✓
9. Largest passenger session: 1,710,089 tokens ✓
10. Passenger outlier-removed mean: (12,197,814 - 1,710,089)/69 = 151,996 ✓

All numeric claims in draft match TSV data within stated rounding.

---

## §1. Factual errors

**Line 16 claim structure:** "The passenger-vs-governor multiplier measured in this rerun is 21.6× on medians (52.7× on means, 50.4× on outlier-removed means)"

The parenthetical order is mean first, then outlier-removed mean. The lead-in says "21.6× on medians" with no parenthetical, creating asymmetry. Rubric §Aggregation specifies reporting mean/median/outlier-removed mean as triples. The draft reports median first in the sentence lead but mean first inside the parenthetical. This is not an error of fact (the numbers are correct per TSV verification) but an ordering inconsistency that could confuse a reader cross-referencing the table at line 38.

**Line 27 subagent exclusion claim:** "Spot-check of 10 subagent paths confirmed each parent was present in the TSV; no non-subagent exclusions applied."

The phrase "no non-subagent exclusions applied" contradicts line 28, which reports 5 rows excluded for zero human turns or zero assistant responses per rubric qualification. The intent is likely "no non-subagent exclusions applied at this filter step" but the sentence as written asserts a global claim that is factually false. The filter sequence at lines 25-30 is accurate; the summary phrase at line 27 is inaccurate.

**Line 56, mixed-model mode distribution:** "13 passenger, 1 collaborator."

Rubric §Scoring criteria item 2 says mixed-model sessions are excluded from single-model comparisons. The draft does not report whether these 14 sessions had their modes assigned via the same `human_turns` thresholds as the single-model pool, or whether mode assignment occurred before or after the mixed-model flag was checked. If mode was assigned first, then filtering mixed-model sessions after mode assignment is rubric-compliant. If these 14 sessions were not mode-classified because they failed the single-model criterion before mode assignment, then reporting their mode distribution is a post-hoc reclassification. The TSV header at sessions-dedup.tsv line 1 shows `mode` as a field; this implies mode was assigned before filtering. The draft should state this explicitly or risk implying that the 13/1 split was observed in a separate pass.

**Line 85, methodology session token share:** "22.7% of pipe-mode total tokens, 0.50% of whole-corpus single-model qualifying tokens"

Pipe total tokens from TSV: 296,054. 22.7% of pipe = 67,211 tokens. 0.50% of 13,488,611 total single-model qualifying = 67,443 tokens. The two percentages do not derive from the same numerator. Either 67,343 (stated absolute value) rounds differently when divided by the two denominators, or one of the percentages is computed from a different value. Spot arithmetic: 67,343 / 296,054 = 22.7% ✓. 67,343 / 13,488,611 = 0.499% ✓ (rounds to 0.50%). No error in fact; the denominators are different as stated. Reader confusion risk is low but the sentence could clarify "of pipe-mode total, and 0.50% of whole-corpus total."

**Line 94, subagent dedup deviation:** "The dispatched extractor prompt instructed skipping parent-child dedup; the rubric requires it."

This sentence asserts that the extractor prompt instructed skipping dedup AND that the rubric requires dedup. Both cannot be true if the implementation is rubric-compliant. The next sentence clarifies that dedup was performed downstream. The phrase "instructed skipping" should read "did not implement" or "deferred" to avoid asserting intentional non-compliance. As written, it implies the extractor was told to violate the rubric, which is a compliance-failure framing rather than an implementation-choice framing.

**None found beyond the above.** Numeric claims verified. Table values match TSV. Multiplier arithmetic spot-checked. No invented sessions, no misattributed modes, no hallucinated N-counts.

---

## §2. Framing drift

**Lines 14-17, claim paragraph:** The original finding reported a 41× mean-based passenger/governor multiplier at N=88. The rerun observes 52.7× on means at N=501. The claim paragraph says "re-observed in this rerun as a same-direction, different-magnitude ordering on a larger, differently-composed corpus." The phrase "same-direction, different-magnitude" understates the match: 41× and 52.7× are both order-of-magnitude similar AND directionally consistent. "Different-magnitude" connotes a material delta (e.g., 41× vs 400×), not a 29% increase on a 12× larger corpus. Framing drifts conservative when the finding strengthened.

**Line 73, mechanism claim:** "Mode is a pure function of human-turn count, and turn count is correlated with total tokens in this corpus."

The word "correlated" is weaker than the observed relationship. The table at lines 36-40 shows monotonic increase in median tokens across modes defined by increasing turn thresholds: 136 (pipe) < 3,217 (governor) < 15,035 (collaborator) < 69,639 (passenger). "Correlated" permits non-monotonic scatter; "monotonically ordered" or "monotonically increasing" would match the observed data. The draft hedges where the data is clean.

**Line 75, passenger token dominance:** "Passenger sessions dominate tokens despite being 14% of single-model count."

The phrase "despite being 14%" frames 14% as a small minority. In a uniform distribution across 4 modes, 25% is the null expectation. 14% is below-null. But in the original finding (N=88), passenger was 11.4% of count; in the rerun it is 14.0%. The direction of change (more passenger sessions in the rerun corpus) is not disclosed in this sentence. "Despite" frames the 14% as surprising; the comparison to the original or to a null baseline would contextualize it.

**Line 81-82, turn/token confound framing:** "The passenger/pipe multiplier therefore has a turn-count component ("more turns ⇒ more tokens accumulate across those turns") and a per-turn-cost component ("each passenger turn may cost more or less than each pipe turn")."

The phrase "may cost more or less" is correct but symmetrically hedged. The observed median token/turn can be computed from the TSV: passenger median total 69,639 on median human_turns = 5,363 total / 70 sessions = 76.6 turns/session (approximate, assuming uniform). Pipe median total 136 on 1 turn/session. Passenger median tokens/turn ≈ 69,639/76.6 ≈ 909. Pipe median tokens/turn = 136/1 = 136. The per-turn cost is directionally "more" for passenger, not "may be more or less." The draft avoids claiming a per-turn metric because the rubric does not specify one, but the hedge "may cost more or less" is stronger than necessary. "Likely differ" or "the rerun does not report a per-turn metric" would avoid false symmetry.

**Line 87, correction rate interpretation:** "Pipe correction rate 0.919 is the committed computation. Pipe denominator equals `n_sessions` (one turn per session); the rate measures 'fraction of pipe sessions whose single prompt contains at least one keyword substring' — a different quantity from the retroactive-correction connotation in collaborator and passenger modes."

This is accurate and important. It is buried in §Confounds rather than surfaced in the correction-rate column header or table footnote. A reader comparing correction rates across modes will miss this unless they read the confounds in full. The framing buries a measurement-validity warning.

**Line 91, mixed-model cardinality check:** "The extractor sets `mixed_model=1` when the set of distinct `message.model` strings across assistant messages in a single JSONL file has cardinality > 1."

The phrase "cardinality > 1" is precise but jargon-heavy. "More than one distinct model ID" would communicate the same criterion to a broader audience. The draft uses technical framing where plain framing would serve replication better.

---

## §3. Missing limitations

**No comparison to billing data:** Rubric §Explicit non-goals says "Verify token counts against billing data (nice-to-have, not in scope for this rerun)." The draft does not state whether the JSONL-logged token counts were spot-checked against API billing records or Anthropic dashboard usage. If no verification was performed, the limitation "token counts are client-logged, not billing-verified" should be disclosed. If verification was performed and is out-of-scope for reporting, the draft should state "not verified" rather than omitting the question.

**No cross-session model distribution:** The draft excludes 14 mixed-model sessions and reports the remaining 501 as single-model. It does not report how many distinct models appear across the 501 single-model sessions (e.g., all opus-4-6, or a mix of opus/sonnet within-session-homogeneous). Rubric §Confounds item "Mixed-model flag mechanism" says "within the single-model pool, individual sessions may use different Claude models (mix across sessions is not analyzed)." This limitation is stated but the model distribution is not reported. A reader asking "what fraction of sessions are opus-4-6 vs sonnet-4-5" cannot answer from the draft.

**No temporal distribution:** The corpus window is "through 2026-04-19T17:18:25Z" but no start date is reported. The original finding was dated 2026-03-30. The rerun corpus is described as "12×-larger, differently-scoped" but the temporal difference (18 days? 3 months? all-time?) is not stated. A reader asking "does this rerun include the original 88 sessions plus 413 new ones" cannot answer. The limitation "corpus composition is undisclosed beyond single-operator single-node" should be stated.

**No subagent dedup verification beyond spot-check:** Line 27 says "Spot-check of 10 subagent paths confirmed each parent was present in the TSV." 555 subagent sessions were excluded. 10/555 = 1.8% verification coverage. The limitation "subagent parent-presence was spot-checked on 1.8% of excluded sessions; the remainder assumed compliant based on path-filter logic" is not stated. If all 555 were verified, the draft should state "all 555"; if only 10 were verified, the limitation should be disclosed.

**No tool-call or duration analysis:** The TSV includes `tool_calls` and `duration_utc_seconds` per rubric §Scoring criteria. The aggregate table reports total tool calls per mode but does not report medians, means, or tool-calls-per-turn. The rubric says duration is "reported but NOT used as a cost metric"; the draft does not report it at all. The limitation "duration and per-session tool-call distributions are in the TSV but not analyzed in this writeup" is not stated.

**No per-model per-mode breakdown:** Rubric §Confounds says "A per-model breakdown is out of scope for this rerun." The limitation is stated. No missing disclosure here.

**Outlier-removal is single-largest only:** The rubric specifies "the single largest-token session removed" for outlier-sensitivity. The draft reports outlier-removed means but does not state whether higher-order outliers (top 5%, top 10%, etc.) were analyzed. The limitation "outlier-sensitivity is single-session removal only; multi-outlier or percentile-trim analysis not performed" is not stated.

**No replication package:** The draft cites TSV files but does not specify whether the extractor/aggregator code, the JSONL corpus, or the intermediate TSVs are archived or published. A replicator reading this draft cannot determine where to obtain the materials. The limitation "replication materials not published; TSVs shared with review panel only" or equivalent is not stated.

---

## §4. What to cut

**Line 69, mode-share differences sentence:** "Mode-share differences below should be read as properties of the two corpora, not as time-series evidence that the operator's behavior changed."

This sentence tells the reader how to interpret the comparison table at lines 62-67 but does not add information. The table already shows N and percentages for both corpora. The interpretive guardrail is appropriate for a findings document aimed at non-technical readers; in a technical rerun against a pre-committed rubric, the reader is assumed capable of reading a comparison table without inferring causality. Cut candidate unless the draft is aimed at a broad audience.

**Lines 81-82, per-turn-cost decomposition explanation:** The full sentence starting "The passenger/pipe multiplier therefore has a turn-count component..." explains why no per-turn metric is reported. This is important context. However, the explanation could be compressed to "The rubric does not specify a per-turn metric; the reported multipliers are per-session and include both turn-count and per-turn-cost effects." The current two-part parenthetical explanation is expository bulk in a section labeled Mechanism. Compress, do not cut entirely.

**Line 56, mixed-model mode distribution:** "Mode distribution among them: 13 passenger, 1 collaborator."

This is a three-session delta (14 total, 13+1 split). The rubric excludes mixed-model sessions from single-model comparisons and says they are "reported separately." The separate report is one sentence. If the 14 sessions are not analyzed further (no token distributions, no turn counts, no multipliers), the mode split is trivia. The sentence could be cut or expanded to a full row (N / tokens / turns) to justify its inclusion.

**Line 93, subagent dedup implementation detail:** "The dispatched extractor prompt instructed skipping parent-child dedup; the rubric requires it. The deviation was caught in spot-check..."

This explains why a rubric-compliant output required a post-extraction filter. It is process transparency. However, the next sentence already states the consequence for replication: "a replicator running the extractor alone (without the aggregator's path filter) would produce a rubric-non-compliant TSV." The first sentence (why the deviation occurred) is internals; the second sentence (what a replicator must do) is the actionable warning. The first sentence could be cut if space is constrained; the second must remain.

**Line 85-86, methodology session retention justification:** "The rubric specifies 'same corpus as the original finding (single operator, single node)' and does not carve out methodology-producing sessions; they are retained, disclosed, and quantified here."

This defends the decision to include `-tmp/` and `-tmp-exp4/` sessions. The defense is valid but the sentence is justification for a decision that could instead be stated as fact: "Methodology sessions retained per rubric (same-corpus requirement)." The current phrasing anticipates an objection. If no objection was raised in the first-pass review, the justification is preemptive bulk. Compress or cut.

**Line 97, session_id format deviation:** "Rubric §Scoring criteria item 1 specifies sha/hash; extractor emits relative file paths."

This is a rubric-noncompliance disclosure. It does not affect the numeric results (session_id is an identifier, not a measured value). If the TSV is never published or shared beyond the review panel, the format deviation is internal trivia. If the TSV is a replication artifact, the deviation is a schema warning. The draft does not specify the TSV's intended audience; the sentence could be cut if TSVs are review-panel-only, or expanded if they are replication artifacts.

**Overall cut budget:** Of the 98 lines in the draft, §Confounds (lines 80-97) contains the highest density of process-transparency detail that a replication-focused reader needs but a findings-summary reader could skip. If the draft must compress, §Confounds is the cut target. Lines 93-97 (implementation deviations) could move to a footnote or appendix. Lines 87-89 (correction rate denominator, mixed-model cardinality phrasing) could compress without information loss.

---

## Summary

**Factual errors:** Five items identified, all phrasing/framing ambiguities rather than incorrect numerics. Most significant: line 27 "no non-subagent exclusions" contradicts line 28; line 94 "instructed skipping" overstates non-compliance intent.

**Framing drift:** Four items. Most significant: "correlated" undersells monotonic ordering (line 73); "may cost more or less" false-symmetry hedge (line 82); correction-rate validity warning buried in confounds rather than table footnote (line 87).

**Missing limitations:** Eight items. Most significant: no billing verification disclosed, no temporal corpus bounds stated, subagent dedup verified on 1.8% sample not disclosed, no replication package availability stated.

**Cut candidates:** Six items, primarily in §Confounds. Largest: lines 93-97 (implementation deviations) could move to appendix; line 69 (interpretive guardrail) could cut if audience is technical.

No numeric errors found. All multipliers, N-counts, and aggregate values verified against TSVs. Draft is factually sound; review targets framing precision and completeness of limitation disclosure.
