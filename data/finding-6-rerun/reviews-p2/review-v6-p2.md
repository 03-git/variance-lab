---
review: Second-pass adversarial review
target: rerun-draft.md
rubric_commit: 49d86f7
rubric_sha256: 4223396958c219045c928c77951a30d3aae86ddacc56c08bc7300891ce7bb379
reviewer_pass: 2 (post first-panel revision)
date: 2026-04-19
protocol: four sections — Factual errors, Framing drift, Missing limitations, What to cut
---

# Review v6 — Second-Pass Adversarial

## Numeric verification (≥5 claims before §1)

All values sourced from aggregate-singlemodel.tsv and ratios-singlemodel.tsv. Column headers used for positional reference.

| Claim in draft | Source value | Match |
|---|---|---|
| N=501 single-model qualifying | 394+9+28+70=501; confirmed by grep on sessions-dedup.tsv (`mixed_model=0, qualifying=1`: 501 rows) | ✓ |
| Passenger/governor 52.7× / 21.6× / 50.4× | ratios-singlemodel: 52.677 / 21.647 / 50.380 | ✓ |
| Passenger/pipe 232× / 512× / 241× | ratios-singlemodel: 232.029 / 512.051 / 240.881 | ✓ |
| Passenger/collaborator 5.06× / 4.63× / 7.83× | ratios-singlemodel: 5.056 / 4.632 / 7.828 | ✓ |
| Collaborator/pipe 45.9× / 110.6× / 30.8× | ratios-singlemodel: 45.889 / 110.551 / 30.770 | ✓ |
| Collaborator/governor 10.4× / 4.67× / 6.44× | ratios-singlemodel: 10.418 / 4.674 / 6.436 | ✓ |
| Passenger 12.20M of 13.49M total tokens (90.4%) | 12,197,814 / (296,054+29,768+964,975+12,197,814)=12,197,814/13,488,611=90.43% | ✓ |
| Passenger outlier 1,710,089 tokens | aggregate largest_session_total_tokens for passenger | ✓ |
| Outlier removal: 174,254 → 151,996 (−12.8%) | (174,254−151,996)/174,254=12.77% | ✓ |
| 14 mixed-model qualifying sessions | grep `mixed_model=1 & qualifying=1` on sessions-dedup.tsv: 14 rows | ✓ |
| Pipe correction rate 0.919 | 362/394=0.91878 | ✓ (rounded) |
| Collaborator outlier-removed mean 19,416 | (964,975−440,735)/27=524,240/27=19,416.3 | ✓ |
| Original passenger share 66% | 10×23,658 / (19×634+34×576+25×3505+10×23658)=236,580/355,835=66.5% | ✓ |

No arithmetic errors found.

---

## §1 Factual errors

### 1.1 "12×-larger" comparison conflates raw with qualifying counts

The draft states: "It is a 12×-larger, differently-scoped set of files." 1075/88≈12.2×. This is valid only if the original N=88 was the raw JSONL file count before any filtering — i.e., all 88 original files qualified with no subagents, no zero-turn sessions, and no mixed-model exclusions. The draft never establishes this.

The mode breakdown in the comparison table sums to exactly 88, which is consistent with 88 raw files all qualifying, but it is also consistent with 88 post-filter qualifying sessions from a larger original corpus. If the original N=88 was post-filter (qualifying sessions), the apples-to-apples comparison is 501 qualifying sessions (rerun) vs 88 qualifying sessions (original), which is 5.7×, not 12×.

The "12×" figure appears in a sentence that explicitly warns the reader not to treat the corpora as comparable. If the comparison basis is ambiguous, the number should be dropped or qualified ("12× more raw files than the original's total session count, assuming the original had no subagent or zero-turn exclusions").

### 1.2 Filter arithmetic is correct but ordering is ambiguous

The filter sequence (1075 → −555 → −5 → −14 → 501) arithmetic is correct. However, the sequence as written implies mixed-model sessions were identified from the post-zero-turn-exclusion pool. Sessions with `qualifying=0` and `mixed_model=1` exist but are immaterial; the 14 mixed-model exclusion is from qualifying sessions only. The draft's language ("14 rows removed") does not make the qualifying-only scope explicit, which a replicator could misread as 14 rows from the 1070-row post-subagent pool. Not a numeric error, but the step should read "14 qualifying mixed-model sessions excluded" to prevent ambiguity.

---

## §2 Framing drift

### 2.1 Median leads the Claim without a stated rationale in that section

The Claim section opens with "21.6× on medians (52.7× on means, 50.4× on outlier-removed means)." The rubric requires all three but does not prescribe ordering. The original finding was means-only (41×). Choosing the median (21.6×) as the headline number while parenthesizing the mean (52.7×) makes the rerun appear lower-magnitude than the original — a directionally conservative framing choice.

The defense (medians are more robust against the 1.7M-token outlier) is correct but appears only in §Mechanism, not in the Claim where the ordering matters. A reader who reads only the Claim section cannot evaluate whether the lead number is the most conservative, the most representative, or a rhetorical choice. Move the rationale to the Claim, or reverse the order to match the rubric's mean-first framing ("52.7× on means / 21.6× on medians / 50.4× on outlier-removed means") and let the full triple speak.

### 2.2 Governor N=9 collapse not visible at the headline

The draft buries the denominator context in a parenthetical footnote of the multiplier table: "(N=9 governor makes these wide)." The headline multiplier — 52.7× passenger/governor — appears in the Claim section and in the multiplier list without any inline governor N. A reader scanning the Claim sees a 52.7× claim; the note that the denominator comes from 9 sessions does not appear until several sections later. The original finding's 41× was computed with N=34 governor sessions (38.6% of the corpus). The rerun's 52.7× is computed with N=9 (1.8%). These are not the same kind of estimate. The Claim section should carry an inline qualifier: "(governor N=9)".

### 2.3 "Re-observed" language is stronger than the corpus difference warrants

The Claim section says the original finding "is re-observed in this rerun as a same-direction, different-magnitude ordering." "Re-observed" implies the same phenomenon measured again on more data. But the governor N collapsed from 34 to 9, the model pool changed (original: claude-opus-4-6 only; rerun: mixed single-model sessions), and the mode distribution reversed (governor was the plurality in the original; pipe is now 78.6%). The ordering is the same, but the structural conditions that produced the original denominator (a healthy N=34 governor pool on a single model) no longer hold. "Same ordering observed under a different corpus composition" is more accurate than "re-observed."

---

## §3 Missing limitations

### 3.1 No hypothesis for the governor collapse (38.6% → 1.8%)

The comparison table shows governor going from the plurality mode (38.6% of original sessions) to the rarest mode (1.8% of rerun sessions). The draft notes "Mode-share differences below should be read as properties of the two corpora, not as time-series evidence." This disclaimer redirects the question without answering it. The governor N=9 is the single most consequential structural difference between the original and rerun corpora: it turns the headline multiplier (52.7×) into a nine-session estimate with no uncertainty bound. The draft should flag that without a hypothesis for why governor sessions became rare, the rerun multiplier is not a stable estimate of the passenger/governor ratio for this operator.

### 3.2 Single-model pool mixes Claude model versions; comparison to original is confounded

The original finding was on claude-opus-4-6 only. The sessions-dedup.tsv shows at minimum claude-opus-4-5-20251101 in the single-model pool (visible in the first rows). The rerun's §Confounds acknowledges that per-model breakdown is out of scope, but does not flag this as a confound on the comparison to the original. If passenger sessions in the rerun are disproportionately on newer or more token-intensive models, the increase from 41× (original) to 52.7× (rerun) could reflect model composition differences rather than any behavioral or structural signal. The draft should note this as a limitation on the original-vs-rerun comparison specifically, not just as a scoping note.

### 3.3 "Tight distribution" for governor is asserted without evidence

Mechanism section: "Governor means and medians agree (3,308 vs 3,217) because N=9 and the distribution is tight." Neither the aggregate TSV nor any other provided artifact contains a standard deviation, IQR, or range for governor. The claim that the distribution is tight is not verifiable from supplied data. The observed agreement between mean and median at N=9 is consistent with a tight distribution but also consistent with a symmetric distribution with modest spread. The causal "because" is unsupported.

### 3.4 Path filter for subagent dedup is an unverified proxy

The confounds section discloses that subagent dedup was implemented as a `/subagents/` path filter at aggregation. The spot-check confirmed N=10 subagent paths had parents present, but the path filter's completeness depends on all subagent transcripts following the `/subagents/` path convention. Transcripts in non-standard project directories or with non-standard naming would survive the filter undetected. The draft does not flag this as a residual dedup uncertainty. If any non-`/subagents/`-path child transcripts survived, the 501 qualifying count is inflated and the per-mode token means are biased upward in modes that contain those sessions.

### 3.5 Pipe median/mean ratio is not explained; median-based multipliers for pipe baseline are counterintuitive

Pipe mean is 751, pipe median is 136 — a 5.5× within-mode ratio, the most extreme of any mode. This produces counterintuitive median-based multipliers: collaborator/pipe median is 110.6× while mean-based is 45.9×; passenger/pipe median is 512× while mean-based is 232×. The Mechanism section states "Means exceed medians in every non-trivial mode" (correct) but does not explain that the pipe mode's extreme mean/median ratio inverts the expected relationship between mean-based and median-based multipliers when pipe is the denominator. A reader using median-based multipliers as a conservative estimate would unknowingly get a *larger* number than the mean-based estimate for pipe-denominator comparisons. This should be flagged explicitly.

---

## §4 What to cut

### 4.1 "because N=9 and the distribution is tight" (Mechanism section)

Cut the causal clause. The mean/median agreement is a fact in the data; the explanation is unverified (see §3.3). Retain: "Governor means and medians are close (3,308 vs 3,217)." Cut: "because N=9 and the distribution is tight."

### 4.2 "higher magnitude here because this corpus has more passenger-class sessions" (Mechanism section)

The sentence: "Same direction as the original (66% passenger share at N=10); higher magnitude here because this corpus has more passenger-class sessions." The 66% figure is verifiable and worth keeping. The causal "because" is circular (higher passenger share → higher passenger concentration) and doesn't add information beyond what the tables already show. Cut: "higher magnitude here because this corpus has more passenger-class sessions." The table already shows 70 vs 10 passenger sessions and 90.4% vs 66.5% share; the explanation is redundant and slightly glosses what should be flagged as a confound.

### 4.3 "the committed computation" in the confounds section

Confounds: "Pipe correction rate 0.919 is the committed computation." The rubric commits to the keyword set and the formula, not to the output value. Calling a computed output "the committed computation" is inaccurate; it risks being read as asserting the rubric pre-specifies the value. Replace with "Pipe correction rate 0.919 is the output of the committed formula applied to the pipe-mode rows."

---

*No section has been left empty after actually looking.*
