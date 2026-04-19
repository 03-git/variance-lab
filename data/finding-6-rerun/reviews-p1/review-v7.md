---CONTENT---
1. Factual errors
none found

2. Framing drift
none found

3. Missing limitations
none found

4. What to cut
none found
---REASONING---
*   Role: One voter of an 8-model cross-review panel.
    *   Task: Adversarial review of the provided "Interaction-Mode-Variance rerun" document.
    *   Constraints: Four sections only (1. Factual errors, 2. Framing drift, 3. Missing limitations, 4. What to cut). No rewriting. If nothing in a section, say 'none found'.
    *   Input: A detailed report including a pre-committed rubric, TSV data (Aggregate and Ratios), and a Draft report.

    *   *Rubric:* Defines modes (Pipe, Governor, Collaborator, Passenger) based on `human_turns`. Defines "human turn", "session", "scoring criteria", "correction detection keyword set", "aggregation", and "non-goals".
    *   *TSV Data:*
        *   Pipe: 394 sessions, mean 751, median 136.
        *   Governor: 9 sessions, mean 3308, median 3217.
        *   Collaborator: 28 sessions, mean 34463, median 15035.
        *   Passenger: 70 sessions, mean 174254, median 69639.
        *   Ratios: Passenger/Governor mean = 52.7, median = 21.6.
    *   *Draft Report:*
        *   Claim: Passenger > Collaborator > Governor > Pipe in tokens.
        *   Measurement: Details on corpus, filters, and single-model qualifying sessions (501).
        *   Per-mode results: Matches TSV.
        *   Multipliers: Matches TSV.
        *   Mixed-model sessions: 14 sessions.
        *   Comparison to original: Compares N and tokens.
        *   Mechanism: Explains mechanical correlation and output dominance.
        *   Confounds: Lists several (mechanical overlap, N=9, experiment sessions, subagent dedup method, correction rate mechanics, session_id format, extractor prompt deviation).

    *   **Section 1: Factual errors**
        *   Check math:
            *   Passenger vs Governor mean ratio: $174254 / 3308 \approx 52.676$. Draft says 52.7x. Correct.
            *   Passenger vs Governor median ratio: $69639 / 3217 \approx 21.65$. Draft says 21.6x. Correct.
            *   Passenger vs Pipe mean ratio: $174254 / 751 \approx 232.0$. Draft says 232x. Correct.
            *   Passenger vs Pipe median ratio: $69639 / 136 \approx 512.05$. Draft says 512x. Correct.
            *   Collaborator vs Governor mean ratio: $34463 / 3308 \approx 10.41$. Draft says "order of magnitude 10x". Correct.
            *   Collaborator vs Governor median ratio: $15035 / 3217 \approx 4.67$. Draft says "~5x". Correct.
            *   Total single-model qualifying sessions: $394 + 9 + 28 + 70 = 501$. Draft says 501. Correct.
            *   Total sessions in corpus: 1075.
            *   Subagent removal: $1075 - 555 = 520$.
            *   Zero human/assistant removal: $520 - 5 = 515$.
            *   Mixed-model removal: $515 - 14 = 501$. Correct.
        *   Check logic: The draft claims "Passenger sessions dominate tokens... 70 passenger sessions carry ~12.2M of ~13.7M total single-model qualifying tokens".
            *   Sum of single-model tokens: $296054 + 29768 + 964975 + 12197814 = 13588611$.
            *   Passenger tokens: $12197814$.
            *   $12197814 / 13588611 \approx 0.8976$ (89.7%). Draft says ~89%. Correct.
        *   Check "Correction rate" in Pipe: $362 / 394 \approx 0.91878$. Draft says 0.919. Correct.
        *   Check "Correction rate" in Governor: $5 / 21 \approx 0.23809$. Draft says 0.238. Correct.
        *   Check "Correction rate" in Collaborator: $65 / 238 \approx 0.2731$. Draft says 0.273. Correct.
        *   Check "Correction rate" in Passenger: $1467 / 5363 \approx 0.2735$. Draft says 0.274. Correct.
        *   *Self-Correction/Refinement:* The draft says "Passenger vs governor: 52.7x on means, 21.6x on medians, 50.4x on outlier-removed means."
            *   Outlier-removed mean Passenger: 151996.
            *   Outlier-removed mean Governor: 3017.
            *   $151996 / 3017 \approx 50.38$. Draft says 50.4x. Correct.

    *   **Section 2: Framing drift**
        *   Does the draft deviate from the rubric?
        *   The rubric is "pre-committed". The draft adheres to the definitions of modes, human turns, and aggregation.
        *   The draft explicitly mentions the "mechanical component" of the multiplier, which prevents the reader from misinterpreting the finding as a "per-turn cost" finding. This is a strength, not drift.
        *   The draft addresses the "mixed-model" exclusion as required by the rubric.
        *   The draft addresses the "outlier-removed" requirement.
        *   The draft includes "Confounds" which are actually disclosures of deviations (like the extractor prompt deviation). This is transparency, not drift.
        *   *Wait:* Is there any drift in the "Claim"? The claim states the ordering is present on both means and medians. This is a direct interpretation of the data.
        *   *Potential issue:* The draft mentions "The original finding's 41x headline... is re-observed as a same-direction, different-magnitude ordering". This is a comparison, not a drift.

    *   **Section 3: Missing limitations**
        *   The "Confounds" section is very thorough. It covers:
            *   Mechanical overlap.
            *   Small N for Governor.
            *   Methodology-producing sessions.
            *   Subagent dedup implementation details.
            *   Non-qualifying rows.
            *   Correction rate mechanics.
            *   Session ID format.
            *   Extractor prompt deviation.
            *   Single operator/node/window.
            *   Single-lineage extractor.
        *   Is anything missing?
            *   The "Correction rate" is noted as being sensitive to the keyword set, but the rubric *fixed* the keyword set, so the limitation is already acknowledged.
            *   The "outlier-removed" section is present.
            *   The "mixed-model" exclusion is present.
            *   The "N=9" sensitivity is present.
        *   One possible missing limitation: The "Correction rate" is reported, but the draft doesn't explicitly state if the *correction rate itself* shows a trend across modes (though it's implied by the numbers). However, the rubric says "The correction rate is reported per mode. It is NOT used to redefine modes." The draft follows this.
        *   The draft mentions "The rerun does not decompose the two [mechanical vs per-turn cost]". This is a limitation.

    *   **Section 4: What to cut**
        *   The "Mechanism" section is quite long. However, it is necessary to prevent the "mechanical correlation" misinterpretation, which is a major risk in this specific dataset.
        *   The "Confounds" section is long, but it contains critical disclosures (like the extractor prompt deviation and the subagent dedup method).
        *   The "Comparison to original finding" table is useful for context.
        *   The "Mixed-model sessions" section is required by the rubric.
        *   Nothing seems superfluous or distracting from the core finding.

    *   Factual errors: none found.
    *   Framing drift: none found.
    *   Missing limitations: none found.
    *   What to cut: none found.

    *Wait, let me double-check the "Comparison to original finding" section.*
    Original: N=88.
    Rerun: N=501.
    The draft says: "The rerun corpus is not the original corpus plus an increment. It is a 12×-larger, differently-scoped set of files."
    $501 / 88 \approx 5.69$.
    Wait, the draft says "12x-larger".
    Let's look at the total sessions.
    Original N = 88.
    Rerun total sessions = 1075 (initial) -> 501 (qualifying).
    If we compare 501 to 88, it's ~5.7x.
    If we compare 1075 to 88, it's ~12.2x.
    The draft says "12x-larger, differently-scoped set of files." This refers to the *corpus* (1075 files), not the *qualifying sessions* (501). This is technically accurate.

    *Let me check the "Mechanism" section again.*
    "Passenger sessions dominate tokens despite being 14% of single-model count."
    $70 / 501 = 0.1397$ (13.97%). Draft says 14%. Correct.

    *Let me check the "Confounds" section regarding the extractor prompt.*
    "The prompt instructed the extractor to skip parent-child subagent dedup and emit all files. The rubric requires the exclusion. Deviation was caught in spot-check and corrected at aggregation via the path filter above."
    This is a very honest disclosure.

    *Is there any framing drift in the "Claim"?*
    "The passenger-vs-governor multiplier measured in this rerun is 52.7× on means and 21.6× on medians... reported alongside the 232× / 512× pipe-baseline multipliers per rubric §Aggregation."
    The rubric says: "Cost-multiplier-style headlines... will be computed as ratios of mean_tokens_per_session and will be reported alongside the median ratio and the outlier-removed ratio, never in isolation."
    The draft reports:
    1. Mean (52.7x)
    2. Median (21.6x)
    3. Outlier-removed mean (50.4x)
    4. Pipe-baseline (232x/512x)
    This adheres perfectly to the rubric's instruction to avoid reporting the mean in isolation.

    *Final check on "Factual errors":*
    In the "Comparison to original finding" table:
    Pipe: N orig 19 (21.6%). $19/88 = 0.2159$. Correct.
    Governor: N orig 34 (38.6%). $34/88 = 0.3863$. Correct.
    Collaborator: N orig 25 (28.4%). $25/88 = 0.2840$. Correct.
    Passenger: N orig 10 (11.4%). $10/88 = 0.1136$. Correct.
    Rerun (single-model):
    Pipe: 394 (78.6%). $394/501 = 0.7864$. Correct.
    Governor: 9 (1.8%). $9/501 = 0.0179$. Correct.
    Collaborator: 28 (5.6%). $28/501 = 0.0558$. Correct.
    Passenger: 70 (14.0%). $70/501 = 0.1397$. Correct.

    Everything looks solid.

    *Wait, one tiny detail:*
    In "Per-mode results (single-model)" table:
    Governor Mean (outlier-removed) is 3,017.
    Governor Median (outlier-removed) is 2,899.
    In the TSV:
    Governor Mean (outlier-removed) is 3017.
    Governor Median (outlier-removed) is 2899.
    Matches.

    In "Multipliers" section:
    "Passenger vs governor: 52.7× on means, 21.6× on medians, 50.4× on outlier-removed means."
    Matches calculations.

    The report is extremely high quality and follows the rubric strictly.

    *One potential "Missing Limitation":*
    The draft mentions the "Correction rate on short modes" as a confound. It explains why the Pipe rate is high. It doesn't explicitly say if the *high* correction rate in Pipe is a "finding" or just a "mechanical artifact". It says "The rate therefore measures [X] — a different quantity from the 'retroactive correction' connotation...". This is a limitation/explanation.

    *One potential "What to cut":*
    The "Mechanism" section is a bit wordy, but given the "Adversarial" context, it's better to have it than not.

    *Conclusion:* No errors, no drift, no missing limitations, no unnecessary content.

    *Wait, let me look at the "Comparison to original finding" table again.*
    The table compares "Avg tok orig" to "Mean tok rerun" and "Median tok rerun".
    Original:
    Pipe: 634
    Governor: 576
    Collaborator: 3,505
    Passenger: 23,658
    Rerun:
    Pipe: 751 / 136
    Governor: 3,308 / 3,217
    Collaborator: 34,463 / 15,035
    Passenger: 174,254 / 69,639
    The table in the draft only shows "Mean tok rerun" and "Median tok rerun" columns.
    Wait, the table header says:
    `| Mode | N orig | Avg tok orig | N rerun (single-model) | Mean tok rerun | Median tok rerun |`
    This is correct.

    *Wait, I found a potential "Factual error" in the "Mechanism" section:*
    "Output-share holds in pipe sessions (92.6%) and in passenger (98.3%), so it is not a mode discriminator in this corpus."
    Let's check the TSV for these percentages.
    Pipe: `sum_output_tokens` = 274203. `sum_total_tokens` = 296054.
    $274203 / 296054 = 0.9261$. (92.6%). Correct.
    Passenger: `sum_output_tokens` = 11998559. `sum_total_tokens` = 12197814.
    $11998559 / 12197814 = 0.9836$. (98.3%). Correct.

    Everything is correct.

    *Final check on "Framing drift":*
    The rubric says: "The correction rate is reported per mode. It is NOT used to redefine modes."
    The draft says: "The correction rate is reported per mode. It is NOT used to redefine modes." (Wait, it doesn't say that, it says "The correction rate is reported per mode" in the TSV and then discusses it in "Confounds").
    Actually, the draft says: "The correction rate is reported per mode. It is NOT used to redefine modes." in the *Rubric*, but in the *Draft* it says: "The correction rate is reported per mode. It is NOT used to redefine modes." (No, it doesn't say that in the draft).
    The draft says: "The correction rate is reported per mode. It is NOT used to redefine modes." ... wait, I am misreading.
    The *Rubric* says: "The correction rate is reported per mode. It is NOT used to redefine modes."
    The *Draft* says: "The correction rate is reported per mode. It is NOT used to redefine modes." ... No, I'm looking at the rubric.
    The *Draft* says: "The correction rate is reported per mode. It is NOT used to redefine modes." ... I cannot find that sentence in the draft.
    The *Draft* says: "The correction rate is reported per mode. It is NOT used to redefine modes." ... I am hallucinating that sentence in the draft.
    Let me re-read the Draft.
    The Draft says: "The correction rate is reported per mode. It is NOT used to redefine modes." ... NO.
    The Draft says: "Correction rate: 0.919... 0.238... 0.273... 0.274".
    The Draft says: "The correction rate is reported per mode. It is NOT used to redefine modes." ... I am looking at the *Rubric* again.
    Okay, the Draft does *not* need to repeat the rubric's rules, it just needs to follow them. The Draft follows them.

    One last check:
    "The passenger-vs-governor multiplier measured in this rerun is 52.7× on means and 21.6× on medians under single-model sessions only, reported alongside the 232× / 512× pipe-baseline multipliers per rubric §Aggregation."
    The rubric says: "Cost-multiplier-style headlines... will be computed as ratios of mean_tokens_per_session and will be reported alongside the median ratio and the outlier-removed ratio, never in isolation."
    The draft reports the mean, the median, and the outlier-removed mean. It also reports the pipe-baseline. This is a very thorough way of following the "never in isolation" rule.

    The draft is solid.

    *Wait, one more check:*
    "The original finding's 41× headline (N=88, 2026-03-30) does not reproduce by coincidence of number; it is re-observed as a same-direction, different-magnitude ordering on a larger, differently-composed corpus."
    Is "41x" correct for the original? The draft says "The original finding's 41x headline...". I have to assume this is a factual statement about the *original* finding which I don't have the text for, but within the context of this document, it's presented as a fact.

    *Wait, I found a potential issue:*
    In "Confounds": "The rubric specifies 'same corpus as the original finding (single operator, single node)' and does not carve out methodology-producing sessions; they are retained, disclosed, and quantified here."
    This is a very good, transparent way to handle it.

    *Wait, I found a potential issue:*
    In "Confounds": "Subagent dedup was implemented as a path filter (`/subagents/`), not as a parent-UUID-matched dedup. The rubric states 'parent transcript already counted' as the exclusion condition. A path filter is a superset of the rubric condition; it excludes subagent children unconditionally."
    This is a very good, transparent way to handle it.

    The document is excellent.

    *One final check on "Factual errors":*
    The draft says: "Residual single-model qualifying sessions: 501."
    My calculation: $394 + 9 + 28 + 70 = 501$. Correct.
    The draft says: "14 sessions in the single-operator dedup corpus have more than one model_id recorded... Mode distribution among them: 13 passenger, 1 collaborator."
    Let's check the "Mixed-model sessions" section in the TSV? No, the TSV provided is "Aggregate TSV (single-model...)".
    The "Mixed-model sessions" are mentioned in the text but not in the TSV. This is consistent with the rubric ("sessions with mixed models are excluded from single-model comparisons and reported separately").

    Everything is consistent.
