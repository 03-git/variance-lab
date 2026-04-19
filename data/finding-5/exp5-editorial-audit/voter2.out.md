# Variance-Lab Audit: Four Findings vs. Handler Methodology

Auditor: one of eight in cross-lineage deliberative pass. Edit list only; no rewrites.

---

## Finding 1: delegated-agent-authorization-gap.md

### Gate check

| Gate | Status | Evidence |
|---|---|---|
| Pre-commitment | **MISS** | `methodology: parallel research across domain verticals` — no rubric or hypothesis committed before data collection. No hash/timestamp artifact referenced. |
| Static rubric | **MISS** | No scoring table; tables are descriptive (`Current Barrier`, `What Works Today`, `Infrastructure Fix`). No weighted criteria, no pass/fail gates. |
| Functional verification | **UNKNOWABLE** | Claims like `Alpaca ... fully agentic today` and `Fastmail ... Fully agentic today` are assertions. No test harness, no invocation artifact. Would be settled by an executable probe per row (e.g., IMAP connect + send script). |
| Deliberative pass | **MISS** | No reviewer section; no voter table. Handler template requires ≥3 lineages cross-checking findings. |
| Cross-lineage balance | **MISS** | Single author/agent context implied; no attribution to multiple model lineages. |
| Peak-hour covariate | **UNKNOWABLE** | Experiment is not timing-sensitive in the same sense, but API-status claims are time-dependent. Settled by dating each row and disclosing probe window. |

### Minimal edits (retrofit without re-running)

- Add frontmatter field `pre_commitment: none — survey-class finding, not experimental`.
- Add a **Methodology limits** section naming the three-gate template and stating which gates don't apply (survey ≠ experiment) vs. which are simply absent.
- Convert "Pattern" assertions into *Observations* labeled as unverified vs. verified; mark every table row with `verified: yes/no/unknown`.
- Add a **Review** section: even post-hoc, dispatch the draft to ≥3 lineage-distinct reviewers and record diffs (mirrors handler.sh report §Review).
- Add timestamps on each status claim (`as of 2026-03-28`) so decay is visible.

### Verdict: **EDITORIAL**

The finding is a landscape survey, not a gated experiment. Retrofitting gates as hard pass/fail would mis-categorize it; labeling it explicitly as survey-class and adding a review pass is sufficient.

---

## Finding 2: delegation-finding.md

### Gate check

| Gate | Status | Evidence |
|---|---|---|
| Pre-commitment | **UNKNOWABLE** | `10 identical tasks: read 6 transcripts (4,752 total lines)...` — task set named, but no pre-committed success rubric or hypothesis artifact. Would be settled by a `/tmp/delegation-spec.txt` analog. |
| Static rubric | **MISS** | Metrics are raw (wall clock, lines of output). `Output | 134 lines | 104 lines` — line count is not a quality rubric. No criteria for "successful" beyond binary `10/10`. |
| Functional verification | **PASS (partial)** | `Successful | 10/10` column is a functional gate. But the definition of "successful" is not provided; rate-limiting is tracked. |
| Deliberative pass | **MISS** | No cross-model review of the 104-line vs 134-line outputs. Quality delta is asserted, not adjudicated. |
| Cross-lineage balance | **MISS** | `Model | Same (subscription default) | Same (subscription default)` — single lineage by construction. The experiment varies topology, not model; cross-lineage isn't the target, but the absence of adjudication still matters. |
| Peak-hour covariate | **UNKNOWABLE** | Wall-clock measurements (`126s`, `65s`, `30s`) are sensitive to API load. No timestamp, no peak-hour control, no repetition across time windows. Settled by repeating the trial across ≥3 distinct hours and disclosing the matrix. |

### Minimal edits

- Add "success" criterion definition (what does `10/10` mean? row count? content match?).
- Add dispatch timestamps for each row in the scaling table; note peak-hour uncontrolled.
- Add a quality-adjudication note: "line count is throughput, not quality; no deliberative pass was run on outputs."
- Add rate-limit disclosure on the `20/3 nodes` row — state whether the 0/20 result is reproducible or single-shot.
- Mark `Successful` column header with footnote: `successful = task returned non-empty output, not quality-verified`.

### Verdict: **RERUN**

Wall-clock numbers without peak-hour control and without a quality rubric are load-dependent throughput observations, not a reproducible delegation finding. The headline `48%` is the load-bearing claim and it rests on the most time-sensitive measurement.

---

## Finding 3: interaction-mode-variance.md

### Gate check

| Gate | Status | Evidence |
|---|---|---|
| Pre-commitment | **UNKNOWABLE** | Mode thresholds `<=1, <=3, <=15, >15 human turns` — file does not state whether thresholds were committed before viewing the 88 logs or fit post-hoc to produce separation. Settled by a rubric artifact predating the extraction script. |
| Static rubric | **PASS (partial)** | Mode classification is a rubric; token counts from `API usage fields` are objective. But correction detection is keyword matching with known false positives (`*Correction detection via keyword matching produces false positives in short sessions`) — self-acknowledged weak axis. |
| Functional verification | **PASS** | `Token counts from API usage fields in assistant message entries` — direct measurement, reproducible from JSONL. |
| Deliberative pass | **MISS** | No cross-model review of the classification or the conclusions. Categorical claims (`Passenger mode: 11% of sessions, 66% of tokens`) unadjudicated. |
| Cross-lineage balance | **MISS** | `All sessions used claude-opus-4-6 on Max subscription` — single model, single operator, single node. Acknowledged as limitation implicitly but not flagged as lineage gap. |
| Peak-hour covariate | **UNKNOWABLE** | `Duration from first to last JSONL timestamp (some sessions span days due to idle time)` — peak-hour not controlled or analyzed. Settled by sharding sessions by UTC hour and checking mode-distribution stability. |

### Minimal edits

- State whether the `<=1/<=3/<=15/>15` thresholds were committed pre-extraction or fit post-hoc. If post-hoc, relabel as "descriptive bins, not hypothesis-tested."
- Add a **Limitations** section: single operator, single model, post-hoc classification, keyword-based correction detection.
- Drop or caveat the `41x cost multiplier` headline — this is ratio arithmetic between two post-hoc bins, not a tested effect size.
- Add review note: dispatch draft to ≥3 lineage-distinct reviewers and attach diffs.
- Clarify that the 152k-token outlier is a single event (`documented 53-subagent incident`) and disclose passenger-mode stats with and without the outlier.

### Verdict: **EDITORIAL**

The raw data (token counts from JSONL) is reproducible and the methodology is disclosed. The gaps are framing (post-hoc bins presented as discovery) and missing deliberative/lineage gates — patchable via disclaimers and a review pass without new data collection.

---

## Finding 4: three-questions.md

### Gate check

| Gate | Status | Evidence |
|---|---|---|
| Pre-commitment | **MISS** | No rubric; the three questions ARE the artifact. But `prior_art_status: no published framework combines these three questions in this sequence (verified against Davenport, Brynjolfsson...)` — "verified against" has no methodology stated. |
| Static rubric | **UNKNOWABLE** | The prior-art table has an implicit 5-element rubric (`Human capability as... Blocker as... Infrastructure vs capability... Per-workflow decomposition... Access scope derived...`). Not pre-committed; applied to survey the literature. Settled by a pre-commit artifact. |
| Functional verification | **UNKNOWABLE** | `$0.30-0.55/call vs $0.02/call` empirical claim but methodology absent in this file (presumably from KEYMASTER finding). Settled by citing the source measurement artifact. |
| Deliberative pass | **MISS** | No reviewer section. Novelty claim (`no published framework combines all five elements`) is exactly the kind of claim that needs cross-lineage adjudication — another lineage might surface prior art the author missed. |
| Cross-lineage balance | **MISS** | Single-author framework proposal. No diverse-lineage review of the novelty claim. |
| Peak-hour covariate | **UNKNOWABLE** | Not obviously applicable to a framework proposal. N/A unless the empirical cost numbers are re-run. |

### Minimal edits

- Downgrade `prior_art_status` claim: explicitly state search methodology (databases, date range, search terms) or soften to "no framework known to the author."
- Add a review section with ≥3 lineage-distinct reviewers specifically asked to find counter-prior-art.
- Cite the KEYMASTER measurement source for the `$0.30-0.55 vs $0.02` claim with an artifact path.
- Reframe as **proposal + empirical anchor** rather than validated framework.

### Verdict: **EDITORIAL**

This is a framework proposal with empirical anchoring elsewhere. The gates mostly don't apply to propositional content; the fix is to narrow claims and add a deliberative pass specifically targeting the novelty assertion.

---

## Summary

| Finding | Verdict | Top gap |
|---|:---:|---|
| delegated-agent-authorization-gap | EDITORIAL | survey-class finding not labeled as such; no deliberative/review pass |
| delegation-finding | **RERUN** | wall-clock is peak-hour-sensitive and no quality rubric gates the 48% headline |
| interaction-mode-variance | EDITORIAL | post-hoc bin thresholds presented as discovery; single-lineage, no review |
| three-questions | EDITORIAL | unsupported novelty claim ("no published framework combines...") without cross-lineage adjudication |
