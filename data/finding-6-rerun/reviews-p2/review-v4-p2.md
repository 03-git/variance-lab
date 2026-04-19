---
title: Second-Pass Adversarial Review — Interaction-Mode-Variance Rerun Draft
reviewer_pass: v4-p2
date: 2026-04-19
target: rerun-draft.md
rubric: findings/interaction-mode-variance-rubric.md @ 49d86f7
protocol: four sections (Factual errors, Framing drift, Missing limitations, What to cut)
single_model_qualifying: 501
---

# Pre-§1 Numeric Verification

All claims below were verified against aggregate-singlemodel.tsv and ratios-singlemodel.tsv before writing §1. Rubric SHA256 (4223396958c219045c928c77951a30d3aae86ddacc56c08bc7300891ce7bb379) verified against the file on disk — matches.

| Claim in draft | Source | Result |
|---|---|---|
| Single-model qualifying = 501 | 394+9+28+70 from aggregate TSV | ✓ |
| Passenger mean = 174,254 | TSV: 174254 | ✓ |
| Passenger median = 69,639 | TSV: 69639 | ✓ |
| Passenger vs governor 52.7×/21.6×/50.4× | TSV: 52.677/21.647/50.380 | ✓ |
| Passenger vs pipe 232×/512×/241× | TSV: 232.029/512.051/240.881 | ✓ |
| Passenger vs collaborator 5.06×/4.63×/7.83× | TSV: 5.056/4.632/7.828 | ✓ |
| Collaborator vs pipe 45.9×/110.6×/30.8× | TSV: 45.889/110.551/30.770 | ✓ |
| Collaborator vs governor 10.4×/4.67×/6.44× | TSV: 10.418/4.674/6.436 | ✓ |
| Passenger token share 12.20M of 13.49M = 90.4% | 12,197,814/(296,054+29,768+964,975+12,197,814) = 90.43% | ✓ |
| Largest passenger session 1,710,089; removal −12.8% | TSV: 1710089; (174,254−151,996)/174,254 = 12.78% | ✓ |
| Pipe mean 751 vs median 136 | TSV: 751, 136 | ✓ |
| Pipe correction rate 0.919 | 362/394 = 0.918782 | ✓ |
| Session count arithmetic 1075−555−5−14 = 501 | sessions-dedup.tsv = 520 data rows (1075−555); −5 qualifying=0; −14 mixed-model | ✓ |
| Methodology corpus: pipe mean 751→623 (n=367) | (296,054−67,343)/(394−27) = 228,711/367 = 623.2 | ✓ |
| Original passenger 66% share | 10×23,658/(19×634+34×576+25×3,505+10×23,658) = 236,580/355,835 = 66.5% | ✓ |

---

# §1 — Factual Errors

None found. All numeric claims verified against the TSVs above. Per-mode table values, multiplier triples (all six), token shares, outlier-removal calculations, correction rates, and session-count arithmetic are consistent with the source data. The rubric SHA256 in the draft frontmatter matches the file on disk.

---

# §2 — Framing Drift

**F1 — "12×-larger" compares incompatible denominators.**

The draft says: "It is a 12×-larger, differently-scoped set of files." The 12× is computed as 1075 raw JSONL files / 88. But 88 is the original finding's qualifying session count (the comparison table lists per-mode Ns summing to 88), not a raw file count. The sessions-dedup.tsv has 520 data rows after the subagent dedup (1075 − 555), and 501 after further filtering. The comparable figure for qualifying single-model sessions is 501/88 ≈ 5.7×. The "12×" is only valid if the original corpus also had ~88 raw JSONL files total and essentially all qualified — which is not established in the draft. Either establish that claim or replace "12×-larger" with the qualifying-session ratio.

**F2 — "inflates more" in the passenger/collaborator note is ambiguous between absolute and relative.**

The draft says: "the largest collaborator session inflates the collaborator mean more than the largest passenger session inflates the passenger mean." In absolute tokens, the passenger outlier is 3.9× larger (1,710,089 vs 440,735) — the statement is false in that reading. It is only true proportionally: removing the collaborator outlier drops the collaborator mean by 40.8%, vs 12.8% for the passenger outlier on the passenger mean. A reader who takes "inflates more" as absolute inflation forms the wrong conclusion. Add "proportionally" or restate as "the collaborator outlier's proportional effect on its mode mean exceeds the passenger outlier's proportional effect on its mode mean."

**F3 — Correction rate incommensurability is buried in Confounds, not the table.**

The per-mode results table presents pipe (0.919), governor (0.238), collaborator (0.273), passenger (0.274) in a single column with no note. The confounds section explains that pipe's rate measures "fraction of pipe sessions whose single prompt contains at least one keyword substring," which is categorically different from retroactive correction in multi-turn modes. A reader scanning the table will compare these four numbers as if they measure the same phenomenon. The warning belongs in the table caption or as a footnote marker on the pipe cell, not only in a separate section.

---

# §3 — Missing Limitations

**M1 — No model composition breakdown within the single-model qualifying pool.**

The sessions-dedup.tsv contains at least four distinct model_ids in qualifying sessions (claude-opus-4-5-20251101, claude-opus-4-6, claude-opus-4-7, claude-sonnet-4-6), and the "single-model" filter only excludes sessions that mix models within a single file, not sessions using different models across files. The per-mode aggregates therefore pool sessions from models with different context windows, generation behavior, and default verbosity. A mode like passenger (N=70) dominated by one model would produce a different mean than the same 70 sessions spread across models. The draft notes "A per-model breakdown is out of scope for this rerun" but does not disclose the model composition of the qualifying pool. Reporting model_id counts per mode, or at minimum for the full single-model pool, is a missing limitation.

**M2 — Input/output token split not carried through the multipliers, despite pricing asymmetry.**

The per-mode table reports mean input and output tokens separately. The aggregate TSV has the data. The draft computes all multipliers on total tokens, then stops. For all modes in this corpus, output tokens dominate total tokens by a large margin:

| Mode | Mean input | Mean output | Output share |
|---|---|---|---|
| Pipe | 55 | 696 | 93% |
| Governor | 87 | 3,221 | 97% |
| Collaborator | 791 | 33,672 | 98% |
| Passenger | 2,846 | 171,408 | 98% |

The passenger/governor output-token ratio is 171,408/3,221 = 53.2× vs the total-token ratio of 52.7×. The input ratio is 2,846/87 = 32.7×. For models priced with output tokens at a multiple of input tokens, the cost multiplier is higher than the total-token multiplier implies. The omission is not fatal — the draft is about token variance, not cost — but the draft's Mechanism section should note that its multipliers slightly understate cost-weighted multipliers for any pricing schedule that weights output more than input.

**M3 — Tokens-per-turn by mode not reported, despite confound being disclosed.**

The Mechanism section discloses the turn-count/token confound: "a per-session token multiplier between turn-count-defined modes is not separable into a pure per-turn-cost effect without a turn-normalized metric." The rubric does not require a turn-normalized metric. But computing it is straightforward from the reported data (total_tokens / mean_human_turns per mode), and omitting it leaves readers unable to estimate how much of the multiplier is "more turns" vs "more tokens per turn":

| Mode | Mean tok/session | Mean turns | Approx tok/turn |
|---|---|---|---|
| Pipe | 751 | 1.0 | 751 |
| Governor | 3,308 | 2.3 | 1,419 |
| Collaborator | 34,463 | 8.5 | 4,054 |
| Passenger | 174,254 | 76.6 | 2,274 |

Collaborator sessions cost more per turn than passenger sessions on this metric (~4,054 vs ~2,274 tokens/turn), despite being cheaper per session. This finding cannot be inferred from the per-session multipliers alone and is absent from the draft. Even a one-sentence note that "tokens-per-turn is higher in collaborator than passenger, indicating the multiplier is not monotonic with per-turn cost" would close the gap.

---

# §4 — What to Cut

**C1 — "Same direction as the original (66% passenger share at N=10)" in Mechanism.**

This sentence claims the two corpora agree on direction using a quantity (66% passenger token share for the original) that is computed from the comparison table's mean×N products, not from any separately reported figure. The comparison table already shows the same-direction ordering directly. The 66% figure is derived, not primary, and the comparison table above it does the work more clearly. Cut the sentence; the table is sufficient.

**C2 — Mode-share percentages in the comparison table.**

The columns "(21.6%)", "(1.8%)", etc. in the per-mode rerun rows are recoverable by dividing N by 501. They add visual weight and invite cross-corpus percentage comparisons (e.g., original 38.6% governor vs rerun 1.8% governor) that the draft explicitly warns against in the paragraph below the table. The warning and the percentages work against each other. Remove the percentages from the table; leave the warning.

**C3 — Vague causal framing in the subagent-dedup deviation paragraph.**

"The dispatched extractor prompt instructed skipping parent-child dedup" is ambiguous: it could mean the extractor was told to skip it (a deliberate choice) or that it was supposed to do it and didn't (a bug). The sentence "the rubric requires it" immediately after suggests the latter. The vague phrasing invites a re-reader to misclassify this as an intentional protocol deviation rather than a correction applied post-hoc. Sharpen to: "The extractor did not implement the rubric's parent-child dedup; a /subagents/ path filter was applied at aggregation as a correction." Keep the replication consequence note that follows — it is load-bearing.
