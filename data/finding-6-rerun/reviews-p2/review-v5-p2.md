---
title: Second-pass adversarial review — rerun-draft.md
reviewer_role: independent verification node
date: 2026-04-19
numeric_claims_verified: 8
rubric_commit: 49d86f7
rubric_sha256: 4223396958c219045c928c77951a30d3aae86ddacc56c08bc7300891ce7bb379
---

# Second-Pass Adversarial Review: rerun-draft.md

## Pre-flight numeric verification

Verified against TSV files before conducting review:

1. Single-model qualifying sessions: 501 (aggregate sum: 394+9+28+70=501; grep count in sessions-dedup.tsv: 501) ✓
2. Pipe mode (N=394, mean=751, median=136): matches aggregate-singlemodel.tsv line 2 ✓
3. Governor mode (N=9, mean=3,308, median=3,217): matches aggregate-singlemodel.tsv line 3 ✓
4. Collaborator mode (N=28, mean=34,463, median=15,035): matches aggregate-singlemodel.tsv line 4 ✓
5. Passenger mode (N=70, mean=174,254, median=69,639): matches aggregate-singlemodel.tsv line 5 ✓
6. Passenger/governor multiplier (52.7× / 21.6× / 50.4×): matches ratios-singlemodel.tsv line 12 (52.677/21.647/50.380) ✓
7. Mixed-model session count (14): grep count in sessions-dedup.tsv ✓
8. Passenger token dominance (12.20M of 13.49M, 90.4%): computed from aggregate sums = 12,197,814/13,488,611 = 90.43% ✓

All verified numeric claims are accurate to stated precision.

---

## §1. Factual errors

**None found.**

All numeric claims, percentages, and table values cross-check against source TSV files. Mode ordering (passenger > collaborator > governor > pipe) holds on both means and medians. Filter sequence (1075 → 555 subagent → 5 qualifying=0 → 14 mixed-model → 501 residual) is arithmetically consistent. Outlier-removal computations match TSV outlier-removed columns. Correction rates match TSV (pipe 0.919 rounds from 0.918782; passenger 0.274 rounds from 0.273541). Original finding comparison (41× from 23,658/576) is correctly computed.

---

## §2. Framing drift

**Line 77:** "Governor means and medians agree (3,308 vs 3,217)"  
"Agree" overstates closeness. 3,308/3,217 = 1.028× ratio. More accurate: "converge" or "closely aligned." The claim is directionally true (smallest mean/median ratio across modes) but "agree" implies tighter tolerance than a 91-token gap.

**Line 16:** "The original finding's 41× headline (N=88, 2026-03-30, means only) is re-observed in this rerun as a same-direction, different-magnitude ordering"  
Ambiguous magnitude direction. Original passenger/governor mean ratio was 41× (23,658/576). Rerun mean ratio is 52.7×, which is *higher*. Rerun median ratio is 21.6×, which is *lower*. "Different-magnitude" is true but doesn't specify up or down. The parenthetical "(52.7× on means, 50.4× on outlier-removed means)" shows means increased, but "different-magnitude" alone could mislead a skim-reader into thinking the effect weakened.

**Line 76:** "Passenger sessions dominate tokens despite being 14% of single-model count."  
"Despite" frames 90.4% token share as surprising. But Mechanism §2 (line 73) correctly states mode is a function of turn count, and turn count mechanically drives token accumulation. The "despite" framing conflicts with the mechanical explanation. If the effect is expected (more turns → more tokens), "despite" is inappropriate.

**Line 73:** "turn count is correlated with total tokens in this corpus"  
Understates causality. Turn count doesn't merely correlate — it mechanically drives token accumulation via context expansion on each assistant response. "Correlated with" is weaker than the relationship warrants. This doesn't misstate a fact, but it frames a causal mechanism as a correlation.

**Line 48-49 emphasis ordering:** Claim (line 16) leads with median (21.6×) before mean (52.7×). Multiplier table (line 48) orders as mean/median/outlier-removed. Leading with the smaller metric (median) in the Claim could anchor readers to the lower bound when the mean ratio is 2.4× higher. Rubric requires both; draft correctly reports both; but headline ordering choice affects reader impression.

**Lines 62-69:** Comparison table to original finding (line 62-67) followed by non-comparability warning (line 69: "not the original corpus plus an increment. It is a 12×-larger, differently-scoped set"). Table structure invites time-series interpretation ("mode distribution shifted from X to Y") while the warning discourages it. Juxtaposition creates tension. Not factually wrong, but the table's utility is undercut by its own disclaimer.

---

## §3. Missing limitations

**No model breakdown within single-model pool.** Draft reports "single-model qualifying sessions" (line 31) but doesn't specify which models. Sessions-dedup.tsv contains model_id field showing claude-opus-4-5-20251101, claude-opus-4-6, etc. Original finding was claude-opus-4-6 only (line 60 footnote). Rerun mixes models across sessions (not within-session mixing, which is excluded). No per-model per-mode breakdown reported. Passenger/governor multiplier could differ between opus-4-5 and opus-4-6 cohorts; this is unexamined.

**No corpus start date.** Line 9: "corpus_window: through 2026-04-19T17:18:25Z" but no start boundary. Original was 2026-03-30 (line 60). Does rerun corpus start then, earlier, or at first available JSONL? Temporal span affects session composition (operator workflow may have changed over time). Start date is determinable from sessions-dedup.tsv utc_start column but not disclosed in draft.

**Subagent parent-child detection method unspecified.** Line 27: "Spot-check of 10 subagent paths confirmed each parent was present in the TSV." How is parent-child relationship determined? Draft mentions `/subagents/` path filter (line 93) but doesn't explain detection logic. Why 10 spot-checks? Random sample or targeted? Rubric says "avoid double-counting the same human's steering" (rubric line 64) but parent detection mechanism is undocumented. If path-based, could non-subagent sessions in `/subagents/` directories be wrongly excluded?

**Correction keyword false-positive examples not provided.** Rubric acknowledges false-positive rate (rubric line 86: "False-positive rate is acknowledged; the set is fixed here so it cannot be tuned to flatter the finding"). Draft reports pipe correction rate 0.919 (line 87) and explains denominator semantics but gives no examples of what matched. What pipe prompts contained "no," "stop," "wrong"? Without examples, readers can't assess whether 0.919 is plausible or inflated by non-correction matches.

**No discussion of what constitutes a "tool call."** Draft reports total_tool_calls per mode (line 37-40 table) but doesn't define the unit. Does a failed tool call count? A retried call? A tool invocation that errors before execution? Rubric line 76 says "count of assistant-emitted tool invocations" but doesn't specify success-only vs all-attempts. Sessions-dedup.tsv tool_calls field exists but its counting rule is undocumented.

**Outlier-removal criterion unexplained.** Draft reports outlier-removed statistics (line 42, table column 4-5) using single-largest-session removal. Rubric specifies this (rubric line 108) but doesn't justify the choice. Why one session, not top 5%? Why not stddev threshold? Draft inherits rubric's choice but doesn't explain rationale. A reader comparing to other studies using 2σ or IQR outlier definitions can't assess method equivalence.

**Largest passenger session (1.71M tokens) not contextualized.** Line 91: "The largest single-model passenger session contains 1,710,089 total tokens." What was this session doing? Legitimate use case (e.g., long research task) or aberration (e.g., runaway loop, model bug)? Session ID is in aggregate-singlemodel.tsv (line 5: -home-hodori/5e5a3487-7d0d-4245-b04a-9df126fa542f.jsonl) but not inspected. Readers can't judge if outlier is signal (extreme but valid workflow) or noise (data quality issue).

**Methodology-producing sessions: magnitude effect unreported.** Line 85: Removing 27 pipe sessions from `-tmp/` and `-tmp-exp4/` directories "does not change the mode ordering or the direction of any multiplier." But what about magnitude? Did passenger/governor shift from 52.7× to 51.9× or to 45.2×? Direction-preservation is reported; magnitude effect is not. If negligible, state it; if material, report it.

**Extraction/aggregation tooling unspecified.** Line 22: "Extraction and aggregation ran on Surface against the same filesystem; the review node received a copy for independent inspection." What ran? Python script? Bash pipeline? The extractor was "dispatched" (line 93 mentions "dispatched extractor prompt"), implying Claude-generated code, but this is not explicit. Replication requires knowing what produced the TSVs.

**Spot-verification scope unclear.** Line 96: "aggregator arithmetic was spot-verified by cross-lineage reviewers against the TSVs prior to writeup." What was verified? Mode assignment? Token sums? Median computations? Who are "cross-lineage reviewers" (different people, different tools, different models)? "Spot-verified" implies incomplete coverage — what wasn't verified?

**No discussion of session compaction effects.** Rubric line 57: "Sessions that were compacted mid-run (compaction is internal; the session continues)" are included. How many sessions were compacted? Does compaction affect token counts (e.g., if compaction summarizes prior turns, does the summary's token cost appear in the totals)? Draft mentions compaction as a rubric criterion but doesn't report compaction prevalence or effects.

**No discussion of API rate limits or failures.** Did any sessions in the corpus fail mid-run due to rate limits, quotas, or API errors? Would partial sessions (human turn → assistant response starts → API error before completion) be included or excluded? Rubric line 63: "Sessions shorter than a single assistant response (user prompt issued but no model completion recorded)" are excluded, but what about sessions where the assistant response was truncated? Not discussed.

**"Single window" undefined.** Line 97: "Single operator, single node, single window." What is the window? Time span (see corpus start date limitation above)? API quota window? Clarify or cut.

**Per-model per-mode reporting absence not justified.** Line 89: "Per-model per-mode reporting is not produced." Why? Scope limit, data insufficiency, or methodological choice? If opus-4-5 and opus-4-6 have different token costs per turn, aggregating them into a single "single-model" pool could obscure per-model effects. Justification for this exclusion is not provided.

---

## §4. What to cut

**Line 77 side observation:** "Governor means and medians agree (3,308 vs 3,217) because N=9 and the distribution is tight."  
This is a mode-internal observation that doesn't serve the cross-mode comparison (the finding's core). If governor N=9 makes ratios unstable (Confounds line 83), then "distribution is tight" is a detail, not a limitation. Cut or consolidate into the N=9 confound.

**Line 50 parenthetical explanation:** "(outlier-removed ratio exceeds mean ratio — the largest collaborator session inflates the collaborator mean more than the largest passenger session inflates the passenger mean)"  
Correct but dense. Breaks flow of multiplier table. This is a Confound-class observation (sensitivity to single sessions). Move to §Confounds or cut. The outlier-removed column already shows the effect; explaining *why* it's non-monotonic is optional.

**Lines 48-52 non-passenger multipliers:** Full pairwise table includes pipe/governor (4.4×), governor/collaborator (10.4×), pipe/collaborator (45.9×), and inverses. Rubric requires reporting mean/median/outlier-removed triples (rubric line 110) but doesn't require all mode pairs. Finding is about passenger vs non-passenger. Reporting passenger/pipe, passenger/governor, passenger/collaborator suffices. Cutting rows 2-9 of the multiplier list reduces noise. (Keep collaborator/pipe if showing non-passenger ordering matters, but pipe/governor and inverses add little.)

**Line 95 metadata deviation:** "session_id format deviates from rubric."  
Rubric specifies sha/hash (rubric line 71); extractor emits paths. This doesn't affect findings (session_id is an index, not an analysis input). Confounds §3 is for limitations affecting interpretation, not metadata format. Cut or move to a "Non-material deviations" appendix if one exists.

**Lines 62-67 comparison table:** Original vs rerun table shows mode count shifts (pipe 21.6% → 78.6%, governor 38.6% → 1.8%) but line 69 warns "The rerun corpus is not the original corpus plus an increment." If the corpora aren't comparable, the table invites a discouraged comparison. Either cut the table and report only the original's 41× for context, or keep the table but remove the non-comparability warning (if the user wants the comparison despite non-equivalence). Current state is contradictory.

**Lines 85-86 methodology session removal test:** Draft reports removing 27 pipe sessions "does not change the mode ordering or the direction of any multiplier" but then includes them in the final counts. If removal doesn't matter and they're included, why discuss removal? Either report the magnitude effect (if material) or cut the paragraph (if immaterial). Current form discloses a test but not its outcome.

**Line 89-90 mixed-model flag mechanism detail:** "The extractor sets `mixed_model=1` when the set of distinct `message.model` strings across assistant messages in a single JSONL file has cardinality > 1."  
This is implementation detail. The finding is that 14 mixed-model sessions were excluded (line 56). How the flag was computed is a replication detail, not a limitation. Cut or condense to "Mixed-model sessions detected via model_id field; 14 excluded."

**Lines 93-94 subagent dedup implementation path:** "The dispatched extractor prompt instructed skipping parent-child dedup; the rubric requires it. The deviation was caught in spot-check (N=10 subagent paths, all parents present in corpus) and corrected downstream via a `/subagents/` path filter at aggregation."  
This is a process confession (extraction deviated from rubric, fixed in aggregation). The finding's TSVs are post-fix. The confession matters for replicators (don't trust extractor output alone) but doesn't affect this draft's results. Consider moving to a "Replication notes" section or cutting. If kept, belongs in Confounds as "subagent dedup validation method" (currently under Missing Limitations §3).

**Line 87-88 correction rate interpretation:** Pipe and governor correction rates are reported (0.919, 0.238) with explanation that pipe rate measures "fraction of pipe sessions whose single prompt contains at least one keyword substring — a different quantity from the retroactive-correction connotation in collaborator and passenger modes."  
If correction rate means different things in different modes, its cross-mode comparability is broken. Rubric requires reporting it (rubric line 108), but the draft could say "Correction rate reported per rubric; not interpretable across modes due to denominator semantics" and cut the detailed pipe-specific explanation. Current form explains why the metric is problematic but still reports it in the table without caveat.

---

## Summary

- Factual errors: none.
- Framing drift: 6 instances (mostly word choice: "agree," "despite," "correlated"; one headline ordering choice).
- Missing limitations: 13 gaps (largest: no model breakdown, no corpus start date, no correction false-positive examples, no outlier-removal justification).
- Cuttable: 8 sections/details (side observations, non-passenger multipliers, metadata deviations, contradictory comparison table, process confessions).

Draft is numerically sound. Core finding (mode ordering holds, passenger/governor 21.6× median / 52.7× mean) is well-supported. Disclosure of confounds is strong (mechanical turn/token overlap, N=9 governor sensitivity, outlier effects). Weaknesses are in framing (overclaiming agreement, understating causality) and missing context (no model breakdown, no false-positive examples, no tooling disclosure). Cuttable material is mostly non-load-bearing detail that could tighten the draft without loss of rigor.
