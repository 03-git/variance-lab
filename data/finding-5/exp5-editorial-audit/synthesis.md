## Synthesis: Eight-Voter Consolidated Edit List

**Preliminary flags before per-finding breakdown:**

- **Voter 8 (qwen3-coder-30b):** Hallucinated gate results. Quoted evidence from the handler methodology report itself (e.g., "The following rubric was committed to `/tmp/handler-dispatch-rubric.txt`...") and applied it wholesale to all four findings, giving every gate PASS. These passes are fabricated. V8 verdicts (all EDITORIAL) cannot be weighted against specific gate claims — only the top-line verdict is preserved as a data point.

- **Voter 7 (gemma-4-26b):** Applied the handler's substrate-code-selection template as a literal structural checklist, concluding RERUN for all findings because none follow that exact report format. This is a category error: findings 1, 3, and 4 are survey/observational/framework papers, not implementation-selection experiments. V7's verdicts are preserved as signal of the strictest possible interpretation but should not dominate.

---

## Finding 1: delegated-agent-authorization-gap.md

### Consolidated edit list

**Edit 1.A — Add Methodology section labeling this as landscape survey, not gated experiment**
Voters: V1, V2, V3, V4, V5, V6 — **6/8**
Agreement. Cross-cutting. All six substantive auditors propose this in some form. V8 hallucinated. V7 treated absence as RERUN trigger.

**Edit 1.B — Note which gates do not apply (survey ≠ experiment) vs. which are simply absent**
Voters: V1, V2, V6 — **3/8**
Moderate agreement. Distinction between "gate inapplicable" and "gate missed" is load-bearing for verdict.

**Edit 1.C — Qualify or cite the $0.02 vs $0.30-0.55/call figures: add N, date range, artifact path, or strike**
Voters: V1, V2, V3, V4, V5, V6 — **6/8**
Agreement. Same figures recur in Finding 4; shared root artifact gap.

**Edit 1.D — Add Limitations section (single researcher, single deployment, no controlled experiment, no replication)**
Voters: V2, V3, V4, V5 — **4/8**
Strong agreement on content; framing varies.

**Edit 1.E — Add timestamps to each domain-table row ("as of 2026-03-28") so decay is visible**
Voter: V2 — **1/8** — UNIQUE SIGNAL
No other voter named this explicitly. V2 (emile opus-4.7-high) noted that API-status claims are time-dependent and that dated rows expose staleness. Governor should decide whether each row needs a date or a single global survey date suffices.

**Edit 1.F — Mark each domain table row with verified: yes / no / unknown**
Voter: V2 — **1/8** — UNIQUE SIGNAL
Related to 1.E. No other voter proposed a per-row verification flag. Could be handled via 1.G instead.

**Edit 1.G — Split functional verification claim into (a) KEYMASTER cost comparison [empirically verified] and (b) domain service survey [secondary research, no test artifacts]**
Voter: V6 — **1/8** — UNIQUE SIGNAL
V6 (emile sonnet-4.6-high) is the only voter who identified that the KEYMASTER cost data and the domain taxonomy are epistemically different claims requiring different verification labels. This is the basis for V6's RERUN verdict on Finding 1 and is not addressed by editorial labeling alone.

**Edit 1.H — Add "finding_class: survey/taxonomy" to frontmatter**
Voter: V6 — **1/8**
Mechanically implements 1.A as a machine-readable field.

**Edit 1.I — Dispatch to ≥3 lineage-distinct reviewers post-hoc; add reviewer table**
Voters: V2, V6 — **2/8**
Split: others treat deliberative pass as inapplicable to survey-class documents.

### Verdict: **EDITORIAL — 6/8**

| Vote | Voters |
|---|---|
| EDITORIAL | V1, V2, V3, V4, V5, V8 |
| RERUN | V6, V7 |

**Split named:** V6 argues RERUN because domain taxonomy claims require test artifacts (running actual API probes per row), not just editorial labeling. V7 argues RERUN on structural grounds (category error noted above). All other substantive auditors accept that survey-class scope justifies editorial retrofit.

---

## Finding 2: delegation-finding.md

### Consolidated edit list

**Edit 2.A — Add UTC timestamps to each scaling table row; note peak-hour uncontrolled**
Voters: V1, V2, V3, V4, V5, V6 — **6/8**
Consensus. The wall-clock headline (48% improvement) is the load-bearing claim and it is time-of-day sensitive. Whether this is editorial or requires rerun is the central split.

**Edit 2.B — Add Limitations block: single lineage, no pre-committed rubric, no deliberative pass, peak-hour uncontrolled**
Voters: V1, V2, V3, V4, V5, V6 — **6/8**
Consensus on content.

**Edit 2.C — Document or retrieve the 10-task spec as a pre-commitment artifact; if unrecoverable, mark "evaluation criteria applied post-hoc"**
Voters: V1, V2, V3, V4, V5 — **5/8**
Agreement. V6 did not flag pre-commitment as a structural gap.

**Edit 2.D — Define "success" criterion: what does 10/10 mean? Row count? Content match? Non-empty output?**
Voters: V2, V5 — **2/8**
Split: V2 and V5 flag this explicitly; others treat "10/10 successful" as sufficient.

**Edit 2.E — Add explicit model ID (not "subscription default")**
Voters: V4, V5 — **2/8**
Split: minor but reproducibility-relevant.

**Edit 2.F — Soften the causal claim "topology was the only variable" — rate-limit state is an unrecorded covariate**
Voter: V1 — **1/8** — UNIQUE SIGNAL
V1 (rousseau opus-4.7-high) is the only voter to isolate this specific causal overclaim. All others note peak-hour as a covariate but none name the explicit overclaim in the text. This edit is linguistically small but epistemically important.

**Edit 2.G — Add quality-adjudication note: line count (134 vs 104) is throughput, not quality; no deliberative pass run on outputs**
Voter: V2 — **1/8** — UNIQUE SIGNAL
No other voter flagged that the output divergence (22% more lines inline vs delegated) is itself an unresolved quality question. If "more lines" means broader coverage or just verbosity, the finding's interpretation changes.

**Edit 2.H — Note whether 0/20 rate-limit result at 20 contexts is reproducible or single-shot**
Voter: V2 — **1/8** — UNIQUE SIGNAL
The 0/20 failure mode is cited as a hard ceiling. V2 alone asks whether this was tested once or confirmed stable.

**Edit 2.I — Verify both trials completed all 10 tasks: output line count differs (134 vs 104), "identical task volume" claim may not hold**
Voter: V5 — **1/8** — UNIQUE SIGNAL
V5 (emile sonnet-4.5-low) is the only voter who identified the output line discrepancy as a potential scope-completeness issue, not just a quality issue. If the delegated run did not complete the same 10 items, the timing comparison is invalid.

**Edit 2.J — Mark "Successful" column header with footnote: "non-empty output, not quality-verified"**
Voter: V2 — **1/8**
Mechanically implements 2.D.

### Verdict: **EDITORIAL — 6/8**

| Vote | Voters |
|---|---|
| EDITORIAL | V1, V3, V4, V5, V6, V8 |
| RERUN | V2, V7 |

**Split named:** V2 (emile opus-4.7-high) argues RERUN because wall-clock measurements without peak-hour controls are load-dependent observations, not reproducible findings — the 48% headline cannot be certified editorially. V7 on category-error grounds. The EDITORIAL majority holds that the timing data is real and the gaps are disclosure, not invalidation. Governor should note V2's dissent is the strongest substantive RERUN argument in the corpus.

---

## Finding 3: interaction-mode-variance.md

### Consolidated edit list

**Edit 3.A — State whether the ≤1/≤3/≤15/>15 turn thresholds were committed before log extraction or fit post-hoc; cite a dated artifact if one exists**
Voters: V1, V2, V3, V4, V5, V6 — **6/8**
Consensus. This is the single gate question that changes the verdict from EDITORIAL to RERUN.

**Edit 3.B — Add Limitations section: single operator, single model (claude-opus-4-6), keyword-based correction detection with acknowledged false positives, peak-hour not controlled**
Voters: V1, V2, V3, V4, V5, V6 — **6/8**
Consensus.

**Edit 3.C — Add time-of-day distribution for sessions, or at minimum a note that peak-hour effects were not analyzed**
Voters: V1, V2, V3, V4, V5, V6 — **6/8**
Consensus.

**Edit 3.D — Cross-link the 152k-token outlier explicitly to the 53-subagent incident; report passenger-mode averages with and without the outlier**
Voters: V2, V4, V5 — **3/8**
Moderate agreement. The outlier's material effect on the aggregate is agreed; whether sensitivity analysis is editorial or required varies.

**Edit 3.E — List the correction-detection keyword set inline (not just describe it as "keyword matching")**
Voters: V1, V5 — **2/8**
Split. Others note the limitation but don't require the list to be published.

**Edit 3.F — Publish the classification script as an artifact path; mechanical application claim requires the tool**
Voter: V1 — **1/8** — UNIQUE SIGNAL
V1 is the only voter who requires the script itself, not just a description of the methodology. If the script doesn't exist as a file, the "mechanical application" claim is unverifiable.

**Edit 3.G — Drop or caveat the 41x cost multiplier headline — this is ratio arithmetic between two post-hoc bins, not a tested effect size**
Voter: V2 — **1/8** — UNIQUE SIGNAL
No other voter challenges the 41x figure's framing as discovery. V2 distinguishes between "ratio of bin averages" and "tested effect." This is the sharpest editorial challenge to Finding 3's main claim.

**Edit 3.H — Dispatch to ≥3 lineage-distinct reviewers; add reviewer table**
Voter: V2 — **1/8**
V2 applies deliberative pass requirement here as it did to Finding 1. Others treat it as inapplicable to observational studies.

**Edit 3.I — Check session logs for a timestamped taxonomy file predating the analysis; if absent, verdict upgrades to RERUN**
Voter: V3 — **1/8** — UNIQUE SIGNAL
V3 (rousseau sonnet-4.5-high) is the only voter who named a specific verification step that can settle the EDITORIAL vs RERUN question without new data collection. This is the correct next action before final verdict.

**Edit 3.J — Add weighted scoring to the rubric (not just binary turn-count thresholds) to match handler methodology's R/H format**
Voter: V6 — **1/8** — UNIQUE SIGNAL
V6 notes that classification thresholds are gates, not a weighted rubric. This edit is structural (adds a quality axis to the classification rubric). No other voter required this.

**Edit 3.K — Verify token counts against billing data as independent confirmation**
Voter: V5 — **1/8** — UNIQUE SIGNAL
No other voter proposed external verification of the API usage fields. V5 notes these are self-reported by the API.

### Verdict: **EDITORIAL (conditional) — 6/8**

| Vote | Voters |
|---|---|
| EDITORIAL (unconditional) | V1, V2, V4, V5, V6, V8 |
| EDITORIAL if pre-committed / RERUN if post-hoc | V3 |
| RERUN | V7 |

**Split named:** V3 uniquely conditions the verdict on a verifiable fact (Edit 3.I above). The pre-commitment question is not answerable from the finding text alone. If the taxonomy file predating analysis does not exist, V3's conditional becomes RERUN, changing the count to 5 EDITORIAL / 2 RERUN. Recommend executing Edit 3.I before closing Finding 3.

---

## Finding 4: three-questions.md

### Consolidated edit list

**Edit 4.A — Downgrade prior_art_status claim: add search methodology (databases, date range, query strings) or soften to "no framework known to author as of [date]"**
Voters: V1, V2, V3, V4, V5, V6 — **6/8**
Consensus. The "verified against Davenport, Brynjolfsson..." claim is the most contested language across all eight voters.

**Edit 4.B — Strike or cite the $0.30-0.55 vs $0.02 figures with a reproducible artifact path, N, and date range**
Voters: V1, V2, V3, V4, V5, V6 — **6/8**
Consensus. Same figures appear in Finding 1; same root gap. If the shared source artifact exists, one cross-reference fixes both.

**Edit 4.C — Add Limitations section: single-operator derivation, single implementation validation, prior-art search snapshot, no cross-operator replication**
Voters: V1, V2, V3, V4, V5, V6 — **6/8**
Consensus.

**Edit 4.D — Add a deliberative pass specifically targeting the novelty claim (cross-lineage review of prior-art literature)**
Voters: V1, V2 — **2/8**
Split. V1 and V2 treat this as a hard requirement for a literature-scope claim. Others treat the editorial softening (4.A) as sufficient.

**Edit 4.E — Reclassify document type in frontmatter: "framework synthesis with production validation" not "production empirical"**
Voter: V5 — **1/8** — UNIQUE SIGNAL
V5 (emile sonnet-4.5-low) is the only voter to name the document-class mislabeling as an edit, rather than just noting the gates don't apply. This is a frontmatter correction that changes how downstream readers interpret the finding's evidential status.

**Edit 4.F — Convert the prior-art table to a binary pass/fail rubric with explicit property definitions scored per framework**
Voter: V6 — **1/8** — UNIQUE SIGNAL
V6 proposes converting the textual "verified against" claim into a falsifiable scored table (five properties × N frameworks). No other voter required this level of structural change to the prior-art section. V6's RERUN verdict on Finding 4 rests partly on this gap being unresolvable editorially.

**Edit 4.G — Reframe as "proposal + empirical anchor" rather than "validated framework"**
Voter: V2 — **1/8** — UNIQUE SIGNAL
Linguistically distinct from 4.E. V2 targets the claim that the framework is *validated*, not just the source label. The distinction matters for whether downstream citations can treat this as a confirmed methodology.

**Edit 4.H — Add explicit falsifiability conditions for the prior-art claim: what prior work would invalidate it?**
Voter: V3 — **1/8** — UNIQUE SIGNAL
V3 is the only voter to require the novelty claim to be made falsifiable, not just softened. A sentence naming what would preempt it (e.g., "a published framework combining Q1-Q3 in this sequence predating 2026-03") is a different edit than adding search metadata.

### Verdict: **EDITORIAL — 7/8**

| Vote | Voters |
|---|---|
| EDITORIAL | V1 (framework portion), V2, V3, V4, V5, V6 (framework), V8 |
| RERUN (novelty claim) | V1 (novelty sub-claim), V6 |
| RERUN (structural) | V7 |

**Split named:** V1 splits the finding — EDITORIAL for the three-question framework itself, RERUN for the specific novelty claim pending a literature-search artifact or deliberative pass. V6 agrees the novelty claim is unresolvable editorially. If the governor treats the novelty claim as load-bearing (it is cited in frontmatter as `prior_art_status`), the effective verdict is RERUN on that sub-claim. Framework content is salvageable editorially regardless.

---

## Summary Table

| Finding | Verdict | N EDITORIAL | N RERUN | Top unique insight (voter) |
|---|---|---|---|---|
| delegated-agent-authorization-gap | **EDITORIAL** | 6 | 2 | Domain taxonomy claims and KEYMASTER cost claim are epistemically distinct and require different verification labels — editorial relabeling does not cover both (V6) |
| delegation-finding | **EDITORIAL** | 6 | 2 | Output line count divergence (134 vs 104) is a potential scope-completeness failure, not just a quality question — "identical task volume" may not hold (V5) |
| interaction-mode-variance | **EDITORIAL (conditional)** | 6 | 1+conditional | Check session logs for timestamped taxonomy file predating analysis; if absent, verdict upgrades to RERUN without new data collection (V3) |
| three-questions | **EDITORIAL** | 7 | 1+sub-claim | Novelty claim requires falsifiability conditions, not just softened language — name what prior work would preempt it (V3); reclassify document type in frontmatter (V5) |

**Cross-cutting:** The $0.02 vs $0.30-0.55/call figures appear as load-bearing evidence in both Finding 1 and Finding 4 with no shared artifact citation. Resolving the source artifact once closes both gaps. No voter named this cross-finding entanglement explicitly — it emerges from the synthesis.
