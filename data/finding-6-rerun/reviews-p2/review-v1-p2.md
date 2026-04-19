---
title: Second-pass adversarial review — rerun-draft.md
date: 2026-04-19
rubric_commit: 49d86f7
rubric_sha256: 4223396958c219045c928c77951a30d3aae86ddacc56c08bc7300891ce7bb379
target: rerun-draft.md
scope: factual errors, framing drift, missing limitations, what to cut
---

# Pre-section verification

Verified directly against TSVs before sectioning:

1. Filter arithmetic: 1075 (extractor) − 555 (subagent) = 520 dedup rows; `wc -l sessions-dedup.tsv` = 521 (520 + header). ✓
2. Qualifying decomposition via `cut -f14,15 | sort | uniq -c`: `0 0` = 5, `0 1` = 501, `1 1` = 14. Residual single-model qualifying = 501. ✓ Filter steps 3 and 4 numbers match draft lines 28–31.
3. Mixed-model mode distribution via `grep -P '\t1\t1$' | cut -f5`: 13 passenger + 1 collaborator = 14. ✓ (draft line 56)
4. Per-mode N sums to 501 (394 + 9 + 28 + 70). ✓
5. Outlier-removed recomputation from `aggregate-singlemodel.tsv`:
   - pipe: (296054 − 48072)/393 = 631.00 ✓
   - governor: (29768 − 5633)/8 = 3016.88 → reported 3017 ✓
   - collaborator: (964975 − 440735)/27 = 19416.30 ✓
   - passenger: (12197814 − 1710089)/69 = 151995.99 → reported 151996 ✓
6. Multipliers from `ratios-singlemodel.tsv` match draft lines 48–52 to reported precision. Passenger/governor 52.677 / 21.647 / 50.380; Passenger/pipe 232.029 / 512.051 / 240.881; Passenger/collaborator 5.056 / 4.632 / 7.828; Collaborator/pipe 45.889 / 110.551 / 30.770; Collaborator/governor 10.418 / 4.674 / 6.436. ✓
7. Passenger share of single-model qualifying tokens: 12,197,814 / 13,488,611 = 0.9043 → draft's 90.4%. ✓ Passenger session share 70/501 = 13.97% → "14%". ✓
8. Pipe `-tmp` confound: (296054 − 67343)/(394 − 27) = 623.19 → "from 751 to 623". ✓ 67343/296054 = 22.74% → "22.7%". ✓ 67343/13488611 = 0.499% → "0.50%". ✓
9. Correction rates: pipe 362/394 = 0.9188 ✓; governor 5/21 = 0.2381 ✓.
10. Original N=88 decomposition (19 + 34 + 25 + 10 = 88) reproduces the original percentages; 19*634 + 34*576 + 25*3505 + 10*23658 = 355,835 gives 236,580/355,835 = 66.5% → draft's "66% passenger share". ✓

All ten pass. Proceeding.

---

# 1. Factual errors

**1.1 "12×-larger" corpus comparison (line 69) mixes incomparable denominators.**
Draft compares extractor file count (1075) to the original's qualifying session count (88) to produce "12× larger". The like-for-like comparison is 501 (single-model qualifying, this rerun) vs 88 (original) = 5.7×. Using 1075 inflates the scale claim by ~2×. If the intent is "file count in this pass vs qualifying count in original", the mismatch should be stated; if the intent is qualifying-vs-qualifying, the number is wrong.

**1.2 Mode-share narrative in Mechanism §2 (line 75) is arithmetically off.**
Draft writes "higher magnitude here because this corpus has more passenger-class sessions." Passenger *session share* is 14.0% here vs 11.4% originally — essentially flat. Passenger *token share* moved 66% → 90%. The increase is driven almost entirely by per-session token growth in passenger mode (mean 23,658 → 174,254, a 7.4× jump), not by a higher fraction of passenger sessions. The stated explanation inverts cause and effect.

**1.3 Governor correction-rate framing (line 87) misnames the denominator.**
"Governor rate 0.238 is similarly sensitive at N=9." The rate is 5/21 — 5 flagged turns over 21 total human turns, not 5/9. Sensitivity is real but the denominator is `total_human_turns`, not `n_sessions`. Small fix; worth making explicit so replicators don't reconstruct it wrong.

**1.4 Mixed-model count in Measurement vs §Mixed-model sessions is consistent, but the aggregate-dedup pointer (line 56) is unverifiable from the provided artifacts.** `aggregate-dedup.tsv` exists in the directory but its contents weren't read in this review; the draft's claim "included in `aggregate-dedup.tsv` if that file is inspected" is unverified here. Not flagging as an error, flagging as reviewer-scope.

# 2. Framing drift

**2.1 Headline multiplier order inverts the rubric's order.**
Rubric §Aggregation: "Cost-multiplier-style headlines […] will be computed as ratios of `mean_tokens_per_session` and will be reported **alongside** the median ratio and the outlier-removed ratio, never in isolation." The rubric's ordering centres on means with median and outlier-removed alongside. Draft line 16 leads with "21.6× on medians (52.7× on means, 50.4× on outlier-removed means)". Leading with the smallest of the three downplays continuity with the original 41× (means) headline; the rerun's mean multiplier (52.7×) is in fact *above* the original, which is the material finding. Reorder to mean-first to match the rubric's framing and to foreground the comparable quantity.

**2.2 Bold on 7.83× in the Passenger-vs-collaborator row (line 50) is editorial.**
Other multiplier rows use plain formatting. The bolded value is specifically the outlier-removed mean, which is the most passenger-favorable of the three. The parenthetical explanation is technically correct, but the bold signals "this is the real number" when the rubric requires all three reported as a triple without hierarchy.

**2.3 "Same direction as the original" elides a 7.4× per-session growth.**
Mechanism §2 reports "same direction" and shifts the explanation onto session composition. The more honest framing: ordering direction is preserved *and* per-session passenger tokens grew ~7× between the two corpora. Whether that growth is behavior, tooling (subagent/tool-call patterns), model-mix, or window-length drift is not knowable from this rerun — which is itself the point. Saying "same direction" without flagging the magnitude shift under-reports what the data show.

**2.4 "Single-model" label understates intra-pool model heterogeneity.**
Pool composition (verified via `cut -f3` on rows with `mixed_model=0, qualifying=1`): 82 opus-4-5-20251101, 344 opus-4-6, 53 opus-4-7, 20 sonnet-4-5, 2 sonnet-4-6. "Single-model" means "one model per session", not "one model across the pool". A reader skimming the headline may assume within-model comparison; the per-mode aggregates pool across five distinct Claude models. See also §3.1.

# 3. Missing limitations

**3.1 No check that model-mix is balanced across modes.**
The single-model pool contains 5 distinct Claude models. If pipe mode is dominated by one model (e.g., dispatched `claude -p` defaults) and passenger mode by another, per-mode token differences partially reflect model-level differences rather than interaction-mode differences. Draft line 89 declares per-model breakdown out of scope; the cost of that decision is not disclosed. Minimum viable disclosure: a model × mode count table in a footnote.

**3.2 No confidence intervals or variance reporting on any multiplier.**
Governor N=9 is called "not tight" (line 83). No CI, no interquartile range, no bootstrap. Collaborator N=28 and even passenger N=70 are similarly un-bracketed. The rubric does not mandate CIs, so this is a limitation of the rubric-as-scoped, not a rubric violation — but a replicator cannot tell whether 52.7× and, say, 35× are statistically distinguishable from what is reported.

**3.3 Correction-keyword false-positive rate is not estimated.**
Rubric §Correction detection acknowledges false-positive risk and fixes the set. Draft handles pipe's 0.919 by reframing the semantic ("different quantity from retroactive-correction connotation"). Collaborator (0.273) and passenger (0.274) rates are left without a false-positive estimate. A hand-audit of even 20 randomly sampled flagged turns per mode would bound the rate; its absence is worth naming as a limitation rather than eliding.

**3.4 Passenger-mode multi-day sessions are not separated.**
Duration field is reported but not examined. Some passenger sessions span many hours (from the mixed-model rows alone: 66420s, 61851s, 57842s, 28899s, 25265s, 25026s). Rubric §What counts as a session explicitly permits multi-calendar-day sessions; this is correct per rubric. The limitation to surface: "passenger mode" as defined includes sessions that are structurally resumed dialogues, and per-session token totals are not comparable to single-sitting sessions. Not a rubric violation, a scope disclosure.

**3.5 Subagent dedup was done post-extraction by path filter.**
Line 93 discloses this and is frank. The missing piece: no number on how many `/subagents/` path rows existed in the pre-filter TSV beyond the 555 mentioned. A replicator needs the exact filter pattern to reproduce — the draft says "a `/subagents/` path filter" but does not pin the regex. Add the literal pattern.

**3.6 `session_id` format deviation (line 95) is noted but consequences are not.**
Rubric §Scoring criteria item 1 specifies "sha or path-hash, not free-text." Extractor emits relative file paths. Consequence for this rerun: none, because path is unique per session. Consequence for cross-corpus joins (if anyone tries one): path collisions across projects if directory names repeat. Worth one sentence.

# 4. What to cut

**4.1 Bold on line 50.** Per §2.2. Remove the `**…**` around 7.83×; keep the parenthetical explanation.

**4.2 Redundant confound entry "Mechanical turn/token overlap" (lines 81).** The same point is made fully in Mechanism §1 (line 73). The Confounds repetition adds no content; it can be reduced to a single back-reference line: "See Mechanism §1 — the multiplier is not decomposable into a per-turn cost without a turn-normalized metric."

**4.3 Line 16 trailing sentence on the original 41× headline.** The §Comparison to original finding section already carries this. The Claim paragraph can stop at the triple and gain headline sharpness; the re-observation language belongs below the table, not in the Claim.

**4.4 Line 89 "Mixed-model flag mechanism" confound is extractor-provenance, not a confound on the finding.** The paragraph describes how the flag is computed and declares per-model breakdown out of scope. That belongs in Measurement or in an Extractor notes subsection, not under Confounds — a confound is something that could bias the reported direction or magnitude. Move or retitle.

**4.5 Final paragraph (line 97) "Single operator, single node, single window."** This is scope, not a confound, and duplicates the corpus line at the top of Measurement. Either cut or move to a `## Scope` section.

---

# Items explicitly looked for and not found

- Arithmetic errors in the per-mode table or multiplier triples: **none found** (all ten pre-section checks pass).
- Rubric violations (threshold changes, new modes, keyword-set edits, post-hoc rescoping): **none found**.
- Undisclosed exclusions or filters: **none found** beyond the disclosed subagent path filter and the disclosed methodology-producing `-tmp` sessions.
- Citations of sessions or numbers absent from the TSVs: **none found**.
