# Exp 3 — deliberative-pass independence test — RESULT

**Run:** 2026-04-19 ~14:30 UTC (off-peak Sunday window)
**Method:** retrospective on exp 5 audit8 artifacts; no new trials. Single analysis dispatch.
**Analyst:** rousseau claude-opus-4-7 effort=high (opus is voter V1 in original panel — self-observation caveat applies)
**Full report:** `/tmp/exp3/report.md` on rousseau (132 lines).

**Result: deliberation is load-bearing, in the opposite direction from the prediction's strictness framing.**

Concordance (gate-only vs deliberative verdict):
- F1 delegated-agent-authorization-gap: gate-only RERUN, deliberative EDITORIAL → deliberative looser
- F2 delegation-finding: gate-only RERUN, deliberative EDITORIAL → deliberative looser
- F3 interaction-mode-variance: gate-only RERUN, deliberative EDITORIAL(conditional) → deliberative looser at synthesis, gate-aligned after our external verification step flipped to RERUN
- F4 three-questions: gate-only RERUN, deliberative EDITORIAL → deliberative looser

**Concordance 0/4. All four divergences are deliberative-looser; zero deliberative-stricter.**

**Pre-committed prediction outcomes:**
- "Concordance ≥ 3/4 → marginal value": NOT MET.
- "Concordance < 3/4 → deliberation load-bearing": MET.
- "At least one deliberative-stricter case": NOT MET.

**What deliberation actually did — not what we predicted.** The handler gates are spec'd for implementation-selection experiments. Four of four audited findings are survey/observational/framework documents. Pure gate-only scoring treats category mismatch as gate-fail and forces RERUN on everything. Deliberation's load-bearing work was **category-error correction** — recognizing the scope mismatch and reframing verdicts accordingly. V7 (gemma) and V8 (qwen3-coder) expose the failure modes of the gate-only path: literal structural checklist (V7) and gate-result hallucination (V8). V1–V6 supplied the reframe.

**Implication.** Deliberation is not a rubric-ratifier in this corpus. If dropped, gate-only scoring would have forced RERUN on all four findings and the ship decision in commits `eab8b24` + `49d86f7` would not exist. Keep the pass, caveated: its load-bearing work in this audit was scope-mismatch catching, not gate-miss catching. A future experiment on a genuinely implementation-selection corpus may show the stricter direction the prediction anticipated.

**Voter unique-catch tally** (from `synthesis.md` explicit "UNIQUE SIGNAL" labels):
- V2 emile opus-4.7 high: **6** (38% of all uniques) — top voter
- V5 emile sonnet-4.5 **low**: 3
- V6 emile sonnet-4.6 high: 3
- V1 rousseau opus-4.7 high: 2
- V3 rousseau sonnet-4.5 high: 2
- V4 rousseau sonnet-4.6 high: 0
- V7 gemma / V8 qwen3-coder: 0 (category-error / hallucination)

**Effort-dial reinforcement:** sonnet-4.5-**low** (V5, 3 catches) outperformed sonnet-4.6-**high** (V4, 0 catches). Consistent with `feedback_effort_dial_calibration` and `feedback_minority_voter_signals`.

**Confounds.**
- Analyst (rousseau opus-4.7) was V1 in the original panel. Self-observation risk. Cross-lineage or non-participating analyst would strengthen.
- "Gate-only" verdict was derived from V7's literal-checklist pass plus cross-voter gate tables, not an independent mechanical scoring against the rubric.
- N=4 findings, all survey/framework-class. A corpus containing at least one implementation-selection finding would distinguish "deliberation as category-corrector" from "deliberation as rubric-ratifier" more cleanly.

**Pairs with exp 1 + exp 2 for composite finding-5 writeup.** Exp 1: governance binds. Exp 2: native mechanism multiplies; identity-items degrade inline. Exp 3: deliberation corrects scope mismatch. Composite picture of what governance, delivery, and deliberation each contribute.
