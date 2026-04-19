# Audit: Four Variance-Lab Findings vs Handler Methodology

## 1. delegated-agent-authorization-gap.md

### Gate check
- **Pre-commitment: UNKNOWABLE.** File names "methodology: parallel research across domain verticals" but shows no committed rubric, hash, or artifact path predating the per-domain findings. Settle with: a pre-dispatch rubric artifact and timestamp.
- **Static rubric: MISS.** No scoring rubric exists; tables are descriptive ("Current Barrier / What Works Today / Infrastructure Fix"), not weighted criteria against pre-committed axes.
- **Functional verification: MISS.** Claims are categorical ("Fully agentic today"), no sourced/invoked test. The one empirical hook — "SSH credential subtraction ($0.02/call) outperformed instruction-based constraints ($0.30-0.55/call)" — is asserted, not reproduced in-file.
- **Deliberative pass: MISS.** No voters, no cross-model convergence test.
- **Cross-lineage balance: MISS.** Single author, no lineage diversity recorded.
- **Peak-hour covariate: UNKNOWABLE.** No timing data. Settle with: dispatch timestamps per cell.

### Minimal edits
- Add a Limitations section explicitly labeling the file as a **landscape survey, not a gated experiment.**
- Relabel "production empirical" → "production-observed + desk research."
- Move the $0.02 vs $0.30-0.55 claim to a cited artifact path or strike the dollar figure.
- Add explicit "gates not applied: rubric, functional, deliberative" note.

### Verdict: **EDITORIAL** — the artifact is a taxonomy, not an experiment; retrofitting requires reframing, not new data.

---

## 2. delegation-finding.md

### Gate check
- **Pre-commitment: MISS.** "10 identical tasks" described post-hoc; no committed task spec or rubric artifact referenced. Quote: "10 identical tasks: read 6 transcripts... cross-reference."
- **Static rubric: MISS.** Metrics table (wall clock, output lines, nodes) is measurement, not rubric-scored criteria.
- **Functional verification: PASS (partial).** Tasks were run; outputs counted. Quote: "134 lines" vs "104 lines," "10/10 successful." Verification of the dispatch mechanism itself is present.
- **Deliberative pass: MISS.** No multi-voter resolution; a single operator's scaling table stands alone.
- **Cross-lineage balance: MISS.** "Same model (subscription default)" — single lineage by construction.
- **Peak-hour covariate: MISS.** Rate-limit data present ("20 contexts → 20/20 rate-limited") but no time-of-day recorded. Settle with: UTC timestamps per row.

### Minimal edits
- Add artifact paths for the 10-task spec and the 6 transcripts.
- Add UTC timestamp column to the scaling table; note whether runs were contemporaneous.
- Add a Limitations block: single lineage, single operator, no pre-committed rubric, no deliberative pass.
- Strike or qualify "topology was the only variable" — rate-limit state is an unrecorded covariate.

### Verdict: **EDITORIAL** — the core latency numbers are measurements that can stand with disclosure; the causal claim ("topology is the only variable") needs softening, not rerun.

---

## 3. interaction-mode-variance.md

### Gate check
- **Pre-commitment: MISS.** Mode bins (≤1, ≤3, ≤15, >15 turns) are not shown committed before the 88-session extraction. Quote: "Sessions classified by human turn count."
- **Static rubric: PASS (weak).** Explicit thresholds exist (the four mode definitions), applied mechanically. But no weights or anti-gaming clause.
- **Functional verification: PASS.** Token counts from "API usage fields in assistant message entries"; extraction is reproducible from JSONL.
- **Deliberative pass: MISS.** Single-operator analysis; no cross-model vote on mode labels or interpretation.
- **Cross-lineage balance: MISS (by design).** "All sessions used claude-opus-4-6" — intentional single-lineage substrate, but the *interpretive* pass is also single-lineage.
- **Peak-hour covariate: UNKNOWABLE.** Timestamps exist in JSONL but not analyzed. Quote: "Duration from first to last JSONL timestamp (some sessions span days due to idle time)." Settle with: hour-of-day histogram per mode.

### Minimal edits
- Publish the classification script as an artifact path (mechanical application claim requires the tool).
- Add a "correction detection" false-positive acknowledgment is already present — tighten the caveat by listing the keyword set inline.
- Add time-of-day distribution for the 10 passenger sessions; note whether the 152k-token outlier was peak-hour.
- Add Limitations: no deliberative pass on mode definitions; 3.4%/1.1% correction-rate comparison is not apples-to-apples (already noted, but strengthen).

### Verdict: **EDITORIAL** — extraction is mechanical and preserved; gate gaps are disclosure, not data.

---

## 4. three-questions.md

### Gate check
- **Pre-commitment: UNKNOWABLE.** File claims "prior_art_status: no published framework combines these three questions in this sequence (verified against [list])" — no search-artifact, query log, or committed search protocol. Settle with: saved search queries, dates, and result sets.
- **Static rubric: MISS.** Prior-art table has three categories, no scoring. "What is novel" enumerates five elements without weight.
- **Functional verification: MISS.** The framework is not tested against a held-out workflow; the "Empirical validation" paragraph asserts dollar figures ($0.30-0.55 vs $0.02) without a linked harness. Same unverified figures as Finding 1.
- **Deliberative pass: MISS.** No cross-model audit of the novelty claim. A literature-claim of this scope would especially benefit from one (reviewer-convergence-is-not-verification applies).
- **Cross-lineage balance: MISS.** Single author, single perspective.
- **Peak-hour covariate: N/A** (no timed experiment); mark UNKNOWABLE for the cost figures' collection window.

### Minimal edits
- Downgrade "prior_art_status: no published framework combines..." to "no published framework found in searches of [list] through [date]." Add the query log as an artifact.
- Strike or cite the $0.30-0.55 vs $0.02 figures to a reproducible harness; otherwise mark them anecdotal.
- Add Limitations block identical in structure to the handler report's.
- Add a deliberative-pass note: "novelty claim not audited cross-lineage."

### Verdict: **RERUN** on the novelty claim (requires a reproducible literature-search artifact or deliberative pass); **EDITORIAL** on the three-question framing itself.

---

## Summary

| Finding | Verdict | Top gap |
|---|---|---|
| delegated-agent-authorization-gap | EDITORIAL | No gates applied; reframe as landscape survey |
| delegation-finding | EDITORIAL | Single-lineage, no pre-committed spec artifact; soften causal claim |
| interaction-mode-variance | EDITORIAL | No deliberative pass on mode definitions; no peak-hour analysis |
| three-questions | RERUN (novelty) / EDITORIAL (framework) | Unverified prior-art claim needs literature-search artifact or cross-lineage audit |
