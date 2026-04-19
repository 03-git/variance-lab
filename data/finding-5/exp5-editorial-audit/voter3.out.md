Auditing four findings against handler methodology gates.

---

## Finding 1: delegated-agent-authorization-gap.md

### Gate Check

| Gate | Status | Evidence |
|------|--------|----------|
| Pre-commitment | **MISS** | No rubric committed before data collection. Claims "derived empirically from production KEYMASTER implementation" but no pre-committed evaluation criteria. |
| Static rubric | **MISS** | No rubric present. Comparative cost data ($0.02 vs $0.30-0.55/call) is outcome, not pre-committed scoring. |
| Functional verification | **UNKNOWABLE** | Production data cited but no described verification methodology. Quote: "identical cross-node dispatch tasks" - task spec not provided. |
| Deliberative pass | **MISS** | No multi-model deliberation. Research synthesis across domains (OAuth, financial APIs, comms) is not deliberative voting. |
| Cross-lineage balance | N/A | No deliberative pass performed. |
| Peak-hour covariate | **UNKNOWABLE** | Production data timeframe not specified. No mention of rate limiting or peak-hour effects. |

### Minimal Edits to Retrofit

1. Add **Methodology** section before Core Finding:
   - State: "Research synthesis across 12 domain verticals, no controlled experiment performed."
   - Add: "Cost comparison data from production KEYMASTER logs (2026-03-XX to 2026-03-XX, N=XXX calls)."
   - Specify: "No pre-committed rubric; findings are observational."

2. Retitle **Per-Domain Findings** to **Domain Survey** (signals this is research synthesis, not experimental data).

3. Add **Limitations** section (handler methodology includes one):
   - Single-operator observation
   - No cross-implementation comparison
   - Cost data from one KEYMASTER deployment, not replicated

4. Change abstract claim: "This was derived empirically" → "This was observed in production KEYMASTER implementation."

### Verdict: **EDITORIAL**

The finding is research synthesis, not experimental. Retrofitting with methodology disclosure and limitations section makes the scope explicit without requiring new data. The cost comparison ($0.02 vs $0.30-0.55) needs sample size and date range added if available in logs.

---

## Finding 2: delegation-finding.md

### Gate Check

| Gate | Status | Evidence |
|------|--------|----------|
| Pre-commitment | **MISS** | Test design described ("10 identical tasks: read 6 transcripts") but no evidence of pre-committed evaluation criteria or rubric. |
| Static rubric | **MISS** | Wall clock time and output line count are reported as metrics, but no rubric scoring multiple criteria. |
| Functional verification | **PASS** | Quote: "Wall clock: 126s vs 65s; Output: 134 lines vs 104 lines; Nodes: 1 vs 3." Empirical execution data from actual runs. |
| Deliberative pass | **MISS** | No multi-model deliberation on which topology to ship. |
| Cross-lineage balance | N/A | No deliberative pass performed. |
| Peak-hour covariate | **PARTIAL** | "Empirical scaling data" table reports rate limiting at 10+ contexts and shows "At 20, account is fully saturated." Observed but not controlled for or analyzed as a variable. |

### Minimal Edits to Retrofit

1. Add **Pre-committed Evaluation Criteria** section before Test Design:
   ```
   Evaluation criteria committed before execution:
   - Primary: wall clock time from dispatch to completion
   - Secondary: successful task completion count
   - Control: identical task set (6 transcripts, 3 landscape docs)
   - Control: same model, same subscription
   ```

2. Add **Static Rubric** table to Test Design:
   | Criterion | Weight | Measurement |
   |-----------|--------|-------------|
   | Wall clock | Primary | Seconds from first dispatch to last completion |
   | Success rate | Binary gate | N completed / N dispatched |
   | Output validity | Binary gate | Cross-reference task produces shared weaknesses list |

3. Add date/time to **Empirical scaling data**: "Measured 2026-0X-XX, HH:MM-HH:MM UTC" for each row. Peak-hour effect is a covariate.

4. Add **Limitations**:
   - Single task type (file read + cross-reference)
   - Single account (subscription rate limits apply)
   - Rate limiting data from exploratory scaling, not controlled experiment

### Verdict: **EDITORIAL**

Core data exists and is valid. Retrofitting with pre-commitment documentation (if retrievable from session logs) and limitations section brings it to methodology compliance. If pre-commitment cannot be documented from logs, mark as "evaluation criteria applied post-hoc" in limitations.

---

## Finding 3: interaction-mode-variance.md

### Gate Check

| Gate | Status | Evidence |
|------|--------|----------|
| Pre-commitment | **UNKNOWABLE** | Mode taxonomy (Pipe/Governor/Collaborator/Passenger) is stated but no evidence it was defined before analyzing logs. Could have been defined iteratively during analysis. |
| Static rubric | **PARTIAL** | Mode classification by turn count is a rubric. Quote: "Pipe (<=1 turn), Governor (<=3), Collaborator (<=15), Passenger (>15)." But weighted scoring or selection rule not present. |
| Functional verification | N/A | Observational study of existing logs, not an implementation experiment. Verification gate does not apply to observational methodology. |
| Deliberative pass | N/A | Observational study. Deliberative pass not applicable. |
| Cross-lineage balance | N/A | No deliberative pass. |
| Peak-hour covariate | **UNKNOWABLE** | Quote: "some sessions span days due to idle time" but no analysis of whether time-of-day affects token consumption per mode. |

### Minimal Edits to Retrofit

1. Add **Methodology** section before Mode Classification:
   ```
   Observational study. Mode taxonomy defined before log analysis: <date>.
   88 JSONL conversation logs from ~/.claude/projects/, all claude-opus-4-6.
   Token counts from API usage fields. Human turn count from role=user entries.
   Correction detection: keyword match against ["no ", "don't", "stop", ...].
   ```

2. Clarify **pre-commitment status** in Methodology:
   - If taxonomy was defined before analysis: state "Mode taxonomy pre-committed <date>."
   - If taxonomy emerged during analysis: state "Mode taxonomy derived iteratively; not pre-committed."

3. Add **peak-hour covariate** to Limitations:
   - "Session timestamps span multiple days and time zones. Peak-hour effects on cost not analyzed."

4. Add **Limitations** (currently absent):
   - Single operator, single model (claude-opus-4-6)
   - Correction detection via keyword matching produces false positives in short sessions
   - Mode boundaries (<=3, <=15 turns) chosen post-hoc or pre-committed? [state which]

### Verdict: **EDITORIAL** if mode taxonomy was pre-committed, otherwise **RERUN**

The finding depends on whether the mode classification was decided before looking at the data. If yes: editorial fixes document the methodology. If no: the taxonomy is curve-fit to the data and the experiment should be replicated with pre-committed boundaries on new session logs.

**Minimal verification step**: check session logs for any file named `mode-taxonomy.txt` or equivalent with timestamp predating analysis. If absent, verdict is RERUN.

---

## Finding 4: three-questions.md

### Gate Check

| Gate | Status | Evidence |
|------|--------|----------|
| Pre-commitment | N/A | Framework paper, not an experiment. No rubric required. |
| Static rubric | N/A | Framework paper. |
| Functional verification | **UNKNOWABLE** | Quote: "Derived from building a multi-node agentic formation where each automation required answering all three questions before implementation." Application described but no verification methodology for whether the framework produces better outcomes than alternatives. |
| Deliberative pass | N/A | Framework paper. |
| Cross-lineage balance | N/A | Framework paper. |
| Peak-hour covariate | N/A | Framework paper. |

### Minimal Edits to Retrofit

This is a **framework/methodology paper**, not an experimental finding. Handler methodology gates do not directly apply. However, it can be strengthened:

1. Add **Empirical Validation** section after Application:
   ```
   Framework applied to <N> automation implementations across formation buildout.
   Cost comparison (instruction-based vs capability-subtraction) from <N> production workflows.
   Sample size: <N> workflows, <date range>.
   No controlled experiment; observational application.
   ```

2. Add **Comparison to Alternatives** in Empirical Validation:
   - State whether cost/security metrics were compared to other intake methodologies or not.
   - If yes: provide data. If no: state "No controlled comparison to alternative frameworks performed."

3. Clarify **prior art** claim:
   - Quote: "No published framework combines all five elements."
   - Add: "Literature search conducted <date>, sources: [list databases/keyword strings]."
   - Add: "Claim is falsifiable: prior work combining Q1-Q3 in this sequence would predate this finding."

4. Add **Limitations**:
   - Single-operator application
   - No controlled trial against alternative frameworks
   - Cost data from one formation, not replicated across multiple orgs

### Verdict: **EDITORIAL**

Framework papers do not require experimental gates, but this one makes empirical claims ("cost $0.02 vs $0.30-0.55/call") without methodology. Adding sample size, date range, and falsifiability conditions for the prior-art claim brings it to sufficient rigor for a methodology paper.

---

## Summary Table

| Finding | Verdict | Top Gap |
|---------|---------|---------|
| 1. delegated-agent-authorization-gap | **EDITORIAL** | No pre-committed rubric; cost data lacks sample size/date range |
| 2. delegation-finding | **EDITORIAL** | Pre-commitment not documented; peak-hour covariate observed but not controlled |
| 3. interaction-mode-variance | **EDITORIAL or RERUN** | Mode taxonomy pre-commitment status unknown; if post-hoc, must rerun with pre-committed boundaries |
| 4. three-questions | **EDITORIAL** | Framework paper with empirical claims but no validation methodology; needs sample size + falsifiability conditions |

**Cross-cutting gap**: None of the four findings include a **Limitations** section. Handler methodology requires one. All four need it added.

**Falsification path**: Finding 3 is the only one where verdict depends on a verifiable fact (mode taxonomy pre-commitment). Check logs for timestamped taxonomy file. If absent, verdict changes from EDITORIAL to RERUN.
