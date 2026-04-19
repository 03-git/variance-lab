## Audit: Four Variance-Lab Findings vs. Handler Methodology

Voter: emile-sonnet-4.6-high. Auditing against the six-gate checklist: pre-commitment, static rubric, functional verification, deliberative pass, cross-lineage balance, peak-hour covariate.

---

## Finding 1: Delegated Agent Authorization Gap

### 1. Gate Check

**Pre-commitment — UNKNOWABLE**
Evidence: `"methodology: parallel research across domain verticals"` (frontmatter). No pre-commitment artifact path referenced. No statement that classification criteria were defined before conducting the survey. What would settle it: a dated file predating 2026-03-28 containing the "gap" classification criteria.

**Static rubric — MISS**
Evidence: Per-domain tables use categorical columns (`Agent-Ready: High/Medium/Low/None`, `Write: Yes/No`) with no scoring definitions. No rubric file is cited. The tables are observations, not scored against pre-committed criteria.

**Functional verification — MISS**
Evidence: `"This was derived empirically from a production KEYMASTER implementation where SSH credential subtraction ($0.02/call) outperformed instruction-based constraints ($0.30-0.55/call)"` — this covers the cost claim only. The domain taxonomy rows (`"Gmail: OAuth2 consent requires browser"`, `"Fastmail: Fully agentic today"`) are secondary research observations with no test artifacts documented. No artifact paths, no session logs, no attempt records for any service row.

**Deliberative pass — UNKNOWABLE**
Evidence: None. No voter table, no cross-lineage dispatch referenced. What would settle it: an 8-voter dispatch table matching handler methodology format.

**Cross-lineage balance — UNKNOWABLE**
Depends on gate 4; cannot assess.

**Peak-hour covariate — UNKNOWABLE**
Evidence: KEYMASTER cost data has no timestamps. Domain observations have no temporal anchoring. What would settle it: timestamps on KEYMASTER test calls or explicit limitation note.

### 2. Minimal Edits

1. Add finding-class marker to frontmatter or abstract: `"finding_class: survey/taxonomy — handler methodology gates 1–3 map differently than for implementation experiments."`
2. Add **Pre-commitment** section: state explicitly whether classification criteria were defined before or after the survey; cite any artifact if one exists.
3. Add rubric section: define what makes a service `High` vs. `Medium` vs. `Low` agent-readiness (e.g., API exists + token-based auth + no interactive consent = High).
4. Split verification into two subsections: (a) **Empirically verified**: KEYMASTER cost comparison with artifact path; (b) **Secondary research**: domain service survey — no test artifacts preserved, claims reflect documentation state at 2026-03-28.
5. Add to Limitations: `"Domain service claims are secondary research; no test artifacts document direct access attempts. Service behavior may have changed since the survey date."`
6. Deliberative pass: dispatch existing finding to 8 voters — no new experiment needed, voter table can be added.

### 3. Verdict

**RERUN.** The finding's core content is the domain taxonomy. Functional verification of those claims requires test artifacts that are not documented here and that a secondary-research methodology cannot substitute for. The KEYMASTER cost data satisfies functional verification for that specific sub-claim only. Adding editorial notes does not bring the domain claims up to the functional verification gate.

---

## Finding 2: Delegation-Aware Execution vs. Single-Context Inline

### 1. Gate Check

**Pre-commitment — UNKNOWABLE**
Evidence: `"## Test Design / 10 identical tasks: read 6 transcripts (4,752 total lines)..."` — test design described, but no pre-commitment artifact referenced. No statement that success metrics were committed before running. What would settle it: a dated file containing evaluation metrics before the 10-task run.

**Static rubric — MISS**
Evidence: No rubric file. The metrics table (wall clock, output lines, success rate, rate limits) is descriptive. No criteria for what constitutes a meaningful improvement were pre-committed. The scaling table rows lack success thresholds.

**Functional verification — PASS**
Evidence: `"| 1 (inline) | 1 | 126s | 10/10 | 0 | baseline |"` and `"| 20 | 3 | 25s | 0/20 | 20 | wall |"` — empirical wall-clock measurements with success/rate-limit counts. `"All three rows are measured on identical task sets (10 tasks, 9 source files)."` Measurement conditions stated. Results are binary and verifiable given the same task corpus.

**Deliberative pass — MISS**
Evidence: None. No voter table or cross-lineage dispatch referenced. Would require new model dispatch but not new experiment.

**Cross-lineage balance — MISS**
Deliberative pass absent; cannot assess.

**Peak-hour covariate — UNKNOWABLE**
Evidence: Rate-limiting behavior (`"At 10, rate limiting begins. At 20, account is fully saturated"`) is time-of-day sensitive. No timestamps on when each concurrency level was tested. `"Same account, same context count. Multi-node gets 7/10 results through. Single-node gets 0/10."` — the rate-limit arbitrage claim may not replicate at different hours. What would settle it: timestamps per scaling row, or a note confirming tests ran within one session window.

### 2. Minimal Edits

1. Add **Pre-commitment** section: affirm that test design (task set, wall-clock and success-rate as primary metrics) was defined before running; reference any existing dated artifact.
2. Add explicit rubric: define success threshold (e.g., `>40% wall-clock reduction at equivalent success rate = meaningful finding`) and rate-limit ceiling criterion.
3. Add timestamp column to scaling table, or add to Limitations: `"Scaling tests were run at different times within a single session; peak-hour rate-limit variability was not controlled across rows."`
4. Deliberative pass: dispatch to 8 voters using existing data and tables; add voter table.

### 3. Verdict

**EDITORIAL.** Wall-clock and success-rate data are empirically solid. All gaps are in template structure (pre-commitment documentation, rubric formalization) and process (deliberative pass). No new data collection needed.

---

## Finding 3: Interaction Mode Variance in Human-AI Sessions

### 1. Gate Check

**Pre-commitment — UNKNOWABLE**
Evidence: Mode thresholds (`"Pipe (<=1 human turn, queued)"`, `"Governor (<=3 human turns)"`, `"Collaborator (<=15 human turns)"`, `"Passenger (>15 human turns)"`) are stated in the finding but no pre-commitment artifact is referenced. No statement that thresholds were defined before the 88-session analysis was run. What would settle it: a dated file containing these thresholds before analysis.

**Static rubric — PARTIAL**
Evidence: Mode classification thresholds function as a binary classification rubric. Correction detection methodology is defined and its limits self-acknowledged: `"*Correction detection via keyword matching produces false positives in short sessions. Signal is reliable only in collaborator/passenger modes."` Mode thresholds are unambiguous and reproducible. What's missing: weighted scoring criteria for mode quality (the thresholds are gates, not a weighted rubric like the handler methodology's R/H scoring).

**Functional verification — PASS**
Evidence: `"88 JSONL conversation logs from ~/.claude/projects/ on a single production node"` — fixed artifact corpus with a known path. `"Token counts from API usage fields in assistant message entries"` — machine-extractable, verifiable against the corpus. `"The 152k-token outlier correlates with the documented 53-subagent incident (2026-03-29)"` — internal cross-reference consistent with known event. Analysis is reproducible given the 88-session JSONL corpus.

**Deliberative pass — MISS**
Evidence: None. No voter table or model dispatch referenced. Note: cross-lineage balance is partially N/A for the underlying data — this finding analyzes session logs rather than model implementations. A deliberative pass would be voters evaluating the methodology and mode-classification claims, not voting on an implementation to ship.

**Cross-lineage balance — MISS**
Deliberative pass absent; N/A for the session log data itself.

**Peak-hour covariate — UNKNOWABLE**
Evidence: `"Duration from first to last JSONL timestamp (some sessions span days due to idle time)"` — sessions span varied times. The 41x token multiplier claim compares session types that may have been run at different hours. API latency variance at peak hours could affect session structure. What would settle it: timestamp distribution across hours-of-day, or explicit Limitations note.

### 2. Minimal Edits

1. Add **Pre-commitment** section: state that mode thresholds were defined before running analysis; reference any dated planning artifact (e.g., prior-session notes, CLAUDE.md entry).
2. Add weighted scoring to rubric: define 0/1/2 per mode on at least one quality axis (e.g., useful output per token) to align with handler methodology's R/H format.
3. Add to Methodology: `"Session timestamp distribution across hours-of-day not analyzed; peak-hour API behavior not controlled for as a covariate in the mode comparison."`
4. Deliberative pass: dispatch to 8 voters using existing data, findings, and mode-classification methodology. No new data needed; add voter table.

### 3. Verdict

**EDITORIAL.** The 88-session JSONL corpus is a fixed, machine-verifiable artifact. Mode classification and correction detection methodology are explicitly defined. Gaps are in pre-commitment documentation, rubric weighting, and a missing deliberative pass — all addressable without new data collection.

---

## Finding 4: Three Questions for Agentic Autonomy

### 1. Gate Check

**Pre-commitment — UNKNOWABLE**
Evidence: `"source: production empirical (consulting methodology derived from formation buildout)"` — the framework is described as "derived from" production work, implying post-hoc formalization. No artifact predating the production deployment documents the three-question sequence. What would settle it: a dated file showing the three questions were committed as a sequence before being applied in practice.

**Static rubric — MISS**
Evidence: The prior-art comparison table lists frameworks against five properties, but no pre-committed scoring rubric defines how each framework was evaluated against them. The claim `"prior_art_status: no published framework combines these three questions in this sequence (verified against Davenport, Brynjolfsson, Autor, McKinsey, Gartner, RPA methodologies...)"` uses "verified" without citing methodology. No scoring file.

**Functional verification — PARTIAL**
Evidence: `"Cost data from production: instruction-based constraints cost $0.30-0.55/call when the agent could bypass them. Capability subtraction (derived from question 3 answers) cost $0.02/call with no bypass possible."` — cost data is referenced, but no artifact path, session log reference, or measurement script is cited. Same figures appear in Finding 1 (`"SSH credential subtraction ($0.02/call) outperformed instruction-based constraints ($0.30-0.55/call)"`) without cross-reference to a shared artifact. The prior-art "verified" claim lacks any artifact or search methodology.

**Deliberative pass — UNKNOWABLE**
Evidence: None. No voter table or cross-lineage dispatch referenced. What would settle it: 8-voter dispatch table.

**Cross-lineage balance — UNKNOWABLE**
Depends on gate 4.

**Peak-hour covariate — UNKNOWABLE**
Evidence: Cost figures ($0.02 vs. $0.30–0.55/call) have no temporal anchoring. No statement that test calls were controlled for time of day. What would settle it: timestamps on KEYMASTER test calls (same artifact gap as Finding 1).

### 2. Minimal Edits

1. Add **Pre-commitment** section: explicitly state whether the three-question sequence was formalized before or after the production experiments. If post-hoc, state this and classify the finding as `"retrospective framework derivation"` rather than prospective methodology validation.
2. Add rubric for prior-art analysis: define the five properties as binary pass/fail criteria with explicit definitions, then score each cited framework against them in a table. This converts the textual "verified" claim into a falsifiable table.
3. Add artifact cross-reference for cost data: cite the same session logs or measurement artifacts used in Finding 1's KEYMASTER claim, or add a path reference (e.g., `~/.keymaster/dispatch-logs/`) with the measurement methodology.
4. Deliberative pass: dispatch to 8 voters using existing finding and prior-art table. No new experiment needed; add voter table.
5. Add to Limitations: `"Cost figures lack temporal controls; the production experiments were not run at controlled hours. The prior-art survey covered literature through 2025 via the evaluator's own review; no independent verification was performed."`

### 3. Verdict

**RERUN.** Two core claims require artifacts that are absent. (1) The cost figures ($0.02 vs $0.30–0.55/call) are referenced but not documented — no artifact paths, no measurement methodology, no session logs. If these artifacts exist on-node, referencing them is an editorial edit; if they were never formally recorded, the figures cannot be certified under the functional verification gate. (2) The prior-art "verified" claim has no methodology — it cannot be validated editorially. The framework itself may be sound, but the handler methodology's gates require documented evidence that these claims were tested, not just stated.

---

## Summary Table

| Finding | Verdict | Top Gap |
|---|---|---|
| Delegated Agent Authorization Gap | **RERUN** | Functional verification: domain taxonomy claims are secondary research with no test artifacts; KEYMASTER data covers cost sub-claim only |
| Delegation-Aware Execution vs. Single-Context Inline | **EDITORIAL** | Pre-commitment: evaluation criteria (success threshold, wall-clock improvement baseline) not committed before running; empirical timing data is solid |
| Interaction Mode Variance in Human-AI Sessions | **EDITORIAL** | Deliberative pass: no multi-model review documented; 88-session JSONL corpus is machine-verifiable and no new data collection needed |
| Three Questions for Agentic Autonomy | **RERUN** | Functional verification: cost figures ($0.02/$0.30-0.55) lack artifact paths; prior-art "verified" claim lacks scoring methodology; both are load-bearing claims that can't be certified editorially without the underlying records |
