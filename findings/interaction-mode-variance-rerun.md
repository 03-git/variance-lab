---
title: Interaction-Mode-Variance — Rerun under pre-committed rubric
date: 2026-04-19
rubric_commit: 49d86f7
rubric_path: findings/interaction-mode-variance-rubric.md
rubric_sha256: 4223396958c219045c928c77951a30d3aae86ddacc56c08bc7300891ce7bb379
supersedes_status: rerun of findings/interaction-mode-variance.md (flagged RERUN in editorial audit 2026-04-19, commit 08804d4)
corpus: ~/.claude/projects/ on Surface (single operator, single node)
corpus_window: 2026-03-29T02:37:27Z — 2026-04-19T17:18:25Z
---

# Interaction-Mode-Variance Rerun

## Claim

Under a pre-committed rubric (`findings/interaction-mode-variance-rubric.md` @ `49d86f7`, sha256 `4223396958c219045c928c77951a30d3aae86ddacc56c08bc7300891ce7bb379`) applied to 1075 Claude Code JSONL session files on a single operator / single node between 2026-03-29 and 2026-04-19, the ordering passenger > collaborator > governor > pipe in total tokens per session holds on means and on medians. The passenger-vs-governor multiplier is **52.7× on means** (21.6× on medians, 50.4× on outlier-removed means; governor N=9) under single-model sessions only. The original finding's 41× headline (N=88, 2026-03-30, means only) is observed here with the same ordering under a different mode distribution and a different model-pool composition.

## Measurement

Pre-commitment: `findings/interaction-mode-variance-rubric.md`, committed 2026-04-19T12:21:33Z at `49d86f7`, content sha256 above. Rubric fixes mode thresholds, human-turn definition, session qualification, correction-keyword set, and mixed-model exclusion. No post-hoc tuning.

Corpus: 1075 JSONL files under `~/.claude/projects/<project>/` on Surface (WSL2 Debian, single operator), with `utc_start` timestamps ranging 2026-03-29T02:37:27Z to 2026-04-19T17:18:25Z. Extraction and aggregation ran on Surface; review nodes (Rousseau, Emile) received copies for independent verification.

Filter sequence:

1. Extractor walks corpus, emits one row per file (1075).
2. Rubric exclusion: subagent child transcripts. Implemented as a path-regex filter `/subagents/` applied at the aggregator (not at extraction). 555 rows removed. Spot-check sample size 10 (1.8% coverage); every sampled subagent had its parent (UUID-prefix-matched file) in the corpus. A replicator can verify the rest deterministically from the TSV.
3. Rubric exclusion: sessions with zero human turns or zero assistant responses (5 rows, `qualifying=0`).
4. Rubric exclusion: mixed-model sessions (14 rows, `mixed_model=1`). Reported separately below.

Residual single-model qualifying sessions: **501**.

### Per-mode results (single-model)

| Mode | N | Mean tok | Median tok | Mean (outlier-rm) | Median (outlier-rm) | Human turns | Tokens/turn | Tool calls | Correction rate* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Pipe (h≤1) | 394 | 751 | 136 | 631 | 136 | 394 | 751 | 93 | 0.919* |
| Governor (2≤h≤3) | 9 | 3,308 | 3,217 | 3,017 | 2,899 | 21 | 1,417 | 67 | 0.238* |
| Collaborator (4≤h≤15) | 28 | 34,463 | 15,035 | 19,416 | 14,855 | 238 | 4,055 | 862 | 0.273 |
| Passenger (h>15) | 70 | 174,254 | 69,639 | 151,996 | 69,398 | 5,363 | 2,274 | 14,823 | 0.274 |

\* Correction rate is the committed-formula output applied to each mode. Pipe and governor rates are not commensurable with collaborator/passenger rates: pipe's denominator is `n_sessions` (1 turn/session), so the rate measures "fraction of pipe sessions whose single prompt contains at least one keyword substring" — not retroactive correction. Governor at N=9 is similarly sensitive to single-keyword matches. No false-positive audit was performed.

**Non-monotonic per-turn cost.** Tokens/turn is highest in collaborator mode (4,055), not passenger (2,274). Per-session multipliers conflate turn-count and per-turn-cost components; the per-turn column shows they can order differently.

### Model composition of the single-model pool

The rubric permits multiple Claude model versions across sessions in the single-model pool. Session counts by `model_id`:

| Model | Sessions | Share |
|---|---:|---:|
| claude-opus-4-6 | 344 | 68.7% |
| claude-opus-4-5-20251101 | 82 | 16.4% |
| claude-opus-4-7 | 53 | 10.6% |
| claude-sonnet-4-5-20250929 | 20 | 4.0% |
| claude-sonnet-4-6 | 2 | 0.4% |

The original finding was claude-opus-4-6 only. Per-model × per-mode breakdown is out of scope per rubric §Scoring criteria; the multipliers below pool across the five models above.

### Multipliers (single-model, rerun)

All triples reported per rubric §Aggregation (mean / median / outlier-removed mean):

- Passenger vs governor: 52.7× / 21.6× / 50.4× (governor N=9)
- Passenger vs pipe: 232× / 512× / 241× (median-based exceeds mean-based; see note below)
- Passenger vs collaborator: 5.06× / 4.63× / 7.83× (outlier-removed mean exceeds mean; the largest collaborator session proportionally inflates collaborator mean more than the largest passenger session inflates passenger mean)
- Collaborator vs pipe: 45.9× / 110.6× / 30.8× (median-based exceeds mean-based)

Note on pipe-denominator multipliers: pipe median (136) is much smaller than pipe mean (751) due to pipe's long-tail distribution, so median-based multipliers against pipe are larger than mean-based. Readers using the median as a conservative estimator should be aware of the inversion.

### Output-token-weighted multiplier

Output tokens dominate total (92.6% in pipe, 98.4% in passenger). For any pricing schedule that weights output more than input, cost-weighted multipliers are slightly higher than the total-token multipliers above: passenger/governor **output-mean ratio = 53.2×** vs 52.7× total.

### Mixed-model sessions (rubric §Scoring criteria item 2 — separate)

14 sessions have more than one `model_id` across assistant messages (13 passenger, 1 collaborator). Excluded from per-mode aggregates; listed in `aggregate-dedup.tsv`. The 13-of-14 passenger concentration means the exclusion is asymmetric by mode — 15.7% of the otherwise-passenger pool is removed vs 0% of pipe and governor.

### Comparison to original finding

Original (N=88 qualifying, 2026-03-30, claude-opus-4-6, same node) reported means only.

| Mode | N orig | Avg tok orig | N rerun | Mean tok rerun | Median tok rerun |
|---|---:|---:|---:|---:|---:|
| Pipe | 19 | 634 | 394 | 751 | 136 |
| Governor | 34 | 576 | 9 | 3,308 | 3,217 |
| Collaborator | 25 | 3,505 | 28 | 34,463 | 15,035 |
| Passenger | 10 | 23,658 | 70 | 174,254 | 69,639 |

The rerun corpus is **~5.7× larger by qualifying-session count** (501 vs 88) and spans a different window. Mode-share differences should not be read as time-series evidence of operator behavior change; the two corpora have different composition (governor N collapsed 34→9, passenger per-session tokens grew 7.4×, model pool broadened from one to five Claude versions).

## Mechanism

**Mode is assigned from human-turn count; token totals are monotonically ordered by mode.** Medians: pipe 136 < governor 3,217 < collaborator 15,035 < passenger 69,639. `mode` is computed from `human_turns` with no other signal; total tokens are a sum across all turns plus tool-call outputs. The passenger/pipe multiplier therefore decomposes into turn-count and per-turn-cost components; the rerun reports both (see Per-mode results). A replicator reading "52.7× passenger/governor" should not infer a per-turn cost ratio.

**Passenger sessions dominate tokens; the shift is per-session growth, not count growth.** 70 passenger sessions carry 12.20M of 13.49M total single-model qualifying tokens (90.4%). Passenger session-share is 14.0% (rerun) vs 11.4% (original), essentially flat. The token-share rise (66% → 90.4%) is driven by per-session passenger tokens growing 7.4× (23,658 → 174,254). Drivers (operator behavior, tooling change, model-mix shift, corpus-window mix) are not disentangled in this rerun.

**Governor/pipe means and medians differ sharply for pipe only.** Governor mean 3,308 and median 3,217 are within 91 tokens at N=9 (consistent with a tight distribution but also with a symmetric distribution at modest spread; no stddev/IQR is reported). Pipe mean 751 vs median 136 (5.5×) reflects a long right tail under the 1-turn bound.

## Confounds

**Mechanical turn/token overlap in the multiplier.** A per-session token multiplier between turn-count-defined modes has a turn-count component that cannot be separated from a per-turn-cost component without a turn-normalized metric. The tokens/turn column addresses the replicator's first question but does not decompose the per-turn-cost variance itself.

**N=9 for governor mode; N=28 for collaborator.** Per-session statistics are individually sensitive. Multipliers with these modes as denominator are informative but not tight. No confidence intervals or bootstrap are reported.

**Pool of five Claude models within the single-model aggregate.** Original was one model (claude-opus-4-6, 68.7% of the rerun pool). Behavioral drift between model versions cannot be separated from the turn-count-driven signal at this granularity. Per-model × per-mode analysis is out of scope per rubric.

**Corpus includes sessions produced by the experiments that produced this methodology.** `-tmp/` and `-tmp-exp4/` contribute 27 pipe-mode sessions totaling 67,343 tokens (22.7% of pipe-mode total, 0.50% of whole-corpus single-model qualifying tokens). Removing them shifts pipe mean 751 → 623 (n=367, −17.0%) and does not change mode ordering or any multiplier direction. No downstream multiplier moves by more than a fraction of a percent.

**Passenger outlier.** The largest single-model passenger session contains 1,710,089 tokens. Removal drops passenger mean 174,254 → 151,996 (−12.8%). This session's nature (legitimate long-context task vs runaway) was not inspected.

**Subagent path-filter coverage.** Filter pattern: `path ~ /\/subagents\//`. 555 rows matched across the dedup step. Spot-check N=10 (1.8% of filtered rows) confirmed parents present; remaining 545 not individually verified. Replicators can verify parent presence deterministically from `sessions-dedup.tsv`.

**Extractor did not implement the rubric's parent-child dedup; a `/subagents/` path filter was applied at aggregation as the correction.** Replication implication: running the extractor alone (without the aggregator's path filter) produces a rubric-non-compliant TSV. The path filter must be re-applied before any aggregation, and is a string match on `/subagents/` — non-conforming path conventions would survive.

**session_id is a relative file path, not sha/hash.** Rubric §Scoring criteria item 1 specifies sha/hash. Consequence for this rerun: none (paths are unique within the corpus). Consequence for cross-node or cross-corpus replication: path collisions possible if directory names repeat.

**Correction-rate false-positive audit was not performed.** The rubric fixes the keyword set; no sample of matched-but-not-correction utterances was logged. The pipe/governor rates are not commensurable with collaborator/passenger rates and should not be scan-compared in the table.

**Extractor/aggregator tooling.** Both are Python 3 stdlib scripts (kernel primitive for JSON is `jq`; Python fallback chosen because multi-pass per-session state — model-set, token sums, XML-tag stripping, compaction-preamble detection — crossed the jq-readability threshold, declared in each script's header comment). `statistics.median` for medians. Arithmetic was spot-verified by cross-lineage reviewers against the TSVs before writeup.

**Token counts are client-logged (API `usage` fields), not billing-verified.** Rubric lists billing verification as a nice-to-have, not in scope for this rerun.
