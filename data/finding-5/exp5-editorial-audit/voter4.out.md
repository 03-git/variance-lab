## Audit: Four Findings vs. Handler Methodology

---

### Finding 1 — `delegated-agent-authorization-gap.md`

#### Gate check

| Gate | Result | Evidence |
|---|---|---|
| Pre-commitment | **MISS** | No pre-committed rubric document referenced. "methodology: parallel research across domain verticals" — no commitment timestamp or criteria file. |
| Static rubric | **MISS** | No scored rubric applied. Domain tables exist but no weighted evaluation criteria were pre-committed. |
| Functional verification | **UNKNOWABLE** | "derived empirically from a production KEYMASTER implementation where SSH credential subtraction ($0.02/call) outperformed instruction-based constraints ($0.30-0.55/call)" — test harness absent. What settles it: disclose the production comparison methodology (task set, call count, timestamp range). |
| Deliberative pass | **MISS** | No multi-model vote described. |
| Cross-lineage balance | **MISS** | No model attribution. Single-researcher synthesis. |
| Peak-hour covariate | **UNKNOWABLE** | No timing or load disclosure for the KEYMASTER cost comparison. What settles it: timestamps for each call-cost measurement. |

#### Minimal edits to retrofit

1. Add a `## Methodology` block: "This finding is a single-researcher domain synthesis. No pre-committed rubric was applied. No deliberative pass was run. The KEYMASTER cost comparison is production-derived; harness details are not preserved."
2. In the KEYMASTER cost paragraph, add a parenthetical with the task set and call count (e.g., "N=X calls, measured [date range], [node]").
3. Add to `## Limitations`: "No deliberative pass or cross-lineage model review was performed. Domain table entries reflect state as of 2026-03-28 and decay rapidly."

#### Verdict: EDITORIAL

---

### Finding 2 — `delegation-finding.md`

#### Gate check

| Gate | Result | Evidence |
|---|---|---|
| Pre-commitment | **UNKNOWABLE** | "source: production empirical (controlled comparison, identical task set)" — no pre-committed metrics document. Whether wall-clock and success-rate were specified before execution is not stated. What settles it: a rubric or experiment design file predating the run. |
| Static rubric | **MISS** | No rubric applied. Measurements are raw (wall clock, success count). No pre-committed scoring criteria. |
| Functional verification | **PASS** | Actual execution results: "Wall clock: 126 seconds vs 65 seconds." Scaling table shows task counts and success/failure. Output was measured in production runtime. |
| Deliberative pass | **MISS** | No multi-model vote on findings or methodology. |
| Cross-lineage balance | **MISS** | "Same model (subscription default)" for all conditions. Single lineage, no cross-lineage comparison. |
| Peak-hour covariate | **UNKNOWABLE** | Wall-clock is the core claim; no timestamps on individual runs. Quote: "All three rows are measured on identical task sets" — but no time-of-day disclosure. What settles it: timestamps for each row in the empirical scaling table. Peak-hour API latency variance could confound the 48% figure. |

#### Minimal edits to retrofit

1. Add a `## Pre-commitment` section: "Metrics measured: wall clock, successful tasks, rate-limit events. These were specified before execution as the dependent variables."
2. In the empirical scaling table, add a `Timestamp / UTC window` column or a footnote: "All runs conducted [date window, approximate UTC range]."
3. Add to `## Limitations`: "No pre-committed rubric. No deliberative pass. Single model lineage (subscription default). Peak-hour API latency was not controlled or disclosed; the absolute wall-clock figures may not replicate under different load conditions."

#### Verdict: EDITORIAL

---

### Finding 3 — `interaction-mode-variance.md`

#### Gate check

| Gate | Result | Evidence |
|---|---|---|
| Pre-commitment | **UNKNOWABLE** | Mode thresholds (≤1, ≤3, ≤15, >15) and correction-detection keywords appear to be pre-defined, but no commitment document or timestamp predating log extraction is referenced. What settles it: a dated spec or code file for the extraction script. |
| Static rubric | **PASS (partial)** | Mode classification is applied mechanically via human-turn count. Evidence: "Sessions classified by human turn count: Pipe (≤1), Governor (≤3), Collaborator (≤15), Passenger (>15)." Caveat: "Correction detection via keyword matching produces false positives in short sessions" — the rubric has an acknowledged instrument flaw. |
| Functional verification | **MISS** | Log analysis, not runtime execution. Keyword-based correction detection is flagged as unreliable: "Signal is reliable only in collaborator/passenger modes." No secondary verification method described. |
| Deliberative pass | **MISS** | No multi-model vote. |
| Cross-lineage balance | **MISS** | All 88 sessions used `claude-opus-4-6`. Single model, single lineage. Quote: "All sessions used claude-opus-4-6 on Max subscription." |
| Peak-hour covariate | **UNKNOWABLE** | Token-per-session and tool-call counts may be influenced by session timing and API verbosity variation. Quote: "some sessions span days due to idle time" — duration is contaminated by idle time. No timestamps per session or per-mode time distribution. What settles it: distribution of session start times by mode, or per-session timestamps already in the JSONL source. |

#### Minimal edits to retrofit

1. Add a `## Pre-commitment` section: "Mode thresholds and correction-detection keywords were fixed in [script name] before log extraction. [Commit hash or dated file reference if available.]"
2. Add to `## Limitations`: "Peak-hour covariate not controlled. Sessions span 2026-03-xx to 2026-03-xx; mode distribution over time was not analyzed. The 41× multiplier reflects aggregate behavior; per-session token variance within modes was not measured."
3. Add to `## Limitations`: "Single model and lineage (claude-opus-4-6). Mode classification thresholds are not validated against other models or lineages."
4. On the 152k-token outlier note: cross-link explicitly — "The 152k-token session is the 53-subagent incident documented at [cross-reference]. Its inclusion materially affects passenger-mode averages."

#### Verdict: EDITORIAL

---

### Finding 4 — `three-questions.md`

#### Gate check

| Gate | Result | Evidence |
|---|---|---|
| Pre-commitment | **MISS** | "source: production empirical (consulting methodology derived from formation buildout)" — methodology was evolved from practice, not pre-committed. No rubric document predates the finding. |
| Static rubric | **MISS** | No rubric. The prior-art table (Technology-first / Process-first / ROI-first) is categorical analysis without scoring criteria. |
| Functional verification | **MISS** | No test harness. The empirical validation claim — "Cost data from production: instruction-based constraints cost $0.30-0.55/call" — has no disclosed task set, call count, or harness. Quote: "Derived from building a multi-node agentic formation where each automation required answering all three questions." Process description, not reproducible test. |
| Deliberative pass | **MISS** | No multi-model vote. |
| Cross-lineage balance | **MISS** | No model attribution for framework derivation. |
| Peak-hour covariate | **UNKNOWABLE** | The cost comparison ($0.02 vs $0.30-0.55/call) has no time or load context. What settles it: task set, date range, and call count for each cost figure. |

#### Minimal edits to retrofit

1. Add a `## Methodology` block: "Framework derived inductively from production formation buildout, not from a pre-committed experimental design. No deliberative pass or cross-lineage review was performed. The cost figures ($0.02/call, $0.30-0.55/call) are production measurements from [node], [date range], [N calls]; harness not preserved as a reproducible script."
2. Add to `## Limitations` (create section if absent): "No pre-committed rubric. Prior-art gap claim ('no published framework combines all five elements') was verified by single-researcher literature review as of 2025; no cross-lineage model deliberation was used to validate the claim."
3. In `## Empirical validation`, annotate the cost figures with N and date, or note: "Call counts and date range not preserved; figures are production estimates."

#### Verdict: EDITORIAL

---

## Summary Table

| Finding | Verdict | Top gap |
|---|---|---|
| delegated-agent-authorization-gap.md | EDITORIAL | No pre-commitment, no deliberative pass, KEYMASTER cost comparison has no disclosed harness |
| delegation-finding.md | EDITORIAL | Peak-hour covariate undisclosed — timestamps absent for wall-clock comparisons that are the core claim |
| interaction-mode-variance.md | EDITORIAL | Single lineage (all sessions same model); peak-hour covariate not controlled; pre-commitment of mode thresholds not verifiable |
| three-questions.md | EDITORIAL | No pre-commitment, no functional verification, cost-comparison methodology not preserved |

**Cross-cutting note on peak-hour covariate:** The handler methodology template does not define this gate or specify what disclosure satisfies it. All four findings are UNKNOWABLE on this gate by that standard. The edits above treat it as a disclosure gap (add timestamps/conditions) rather than a re-run trigger, consistent with how the handler methodology handles its own limitations ("pre-commitment is not cryptographically verifiable").
