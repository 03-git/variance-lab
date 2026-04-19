# Exp 2 — CLAUDE.md delivery-path test — RESULT

**Run:** 2026-04-19 ~14:00–14:10 UTC (off-peak Sunday, same known-quantity window as exp 1)
**Spec sha256 (pre-committed):** `8075578ce25da42639f798c413eaf644c4877a912867950cf647ccc6121eaec7`
**Model (trials):** claude-opus-4-7, effort=high
**Scorer:** claude-sonnet-4-5 low (rousseau), blind shuffle
**N:** 5 per arm, interleaved

**Result: directional signal; pre-committed thresholds not fully met.**

Arm A (native ~/CLAUDE.md load, cwd=~) mean **7.80/10**, stdev 0.45 (trials 8, 8, 8, 8, 7).
Arm B (inline CLAUDE.md prepended to user prompt, cwd=/tmp) mean **6.80/10**, stdev 0.84 (trials 8, 7, 7, 6, 6).
Welch **t = 2.36**, delta **+1.00**.

Pre-committed predictions in the spec were: (a) convergent null at ~8/8, or (b) divergent with inline arm <6/10. Arm B landed 6.80 — just above the divergence threshold. Neither prediction fully met; result is intermediate and directional.

**Replication check: PASS.** Arm A (exp 2) = 7.80 vs Arm A (exp 1) = 8.2, delta −0.40 (pre-committed tolerance ±1.5). The methodology reproduces the exp 1 baseline within tolerance across separated runs, supporting that exp 2's delta is a real measurement, not apparatus drift.

**Binding gradient (exp 1 + exp 2 combined):**
- No governance (exp 1 B, cwd=/tmp): 3.0
- Inline governance (exp 2 B, content in user prompt): 6.80
- Native governance (exp 2 A / exp 1 A averaged): ~8.0

Any delivery of governance content contributes ~3.8 points of the ~5.0-point range. Native mechanism adds ~1.2 points on top of inline. Content is the primary binding force; mechanism is a secondary multiplier. **Do not frame as a clean 80/20 content-vs-mechanism decomposition — the deltas are not cleanly additive components and the wording would overstate the evidence.**

**The load-bearing finding lives at the item level, not the aggregate.**
R2 (subtract.ing namespace): Arm A **80%** → Arm B **0%**. Four-point binary collapse on a single item. When governance loads natively, the agent names the namespace 4/5 trials; when inlined, never.
R10 (agent/human boundary): Arm A 100% → Arm B 60%. Smaller but same direction.

**Proposed principle (inductive, one experiment).** Behaviors that require the agent to *identify with* a namespace or authority role (R2 namespace, R10 boundary) degrade more under inline delivery. Behaviors that require the agent to *follow specific instructions* (R1 ssh-keygen, R5 surface-only push, R6 gh CLI, R7 no cloudflare, R8 pre-flight, R9 verify recipe) survive inline delivery intact. Governance design implication: identity-level claims need native delivery; instruction-level claims survive inline.

**Persistent null across exp 1 + exp 2.** R3 (signer identity) and R4 (llms.txt manifest) score 0% in both arms of both experiments. Two replications. This is a replicable gap in `/home/hodori/CLAUDE.md`: the file does not reach the manifest/signer layer regardless of how it is delivered. Decision point: mark as by-design (manifest lives separately) or patch (add reflex or section covering manifest format and signer invocation).

**Methodology notes.**
- **Aggregator bug caught post-run.** Harness wrote "jsonl" files as pretty-printed multi-line JSON; JSONL parser read line-by-line and silently dropped all records. Initial report showed N=0 mean=0. Re-aggregated inline from raw files. Fix pattern saved to memory: `json.dumps(obj)` single-line for JSONL; verify record count matches expected before parsing; add the record-count assertion to the harness itself rather than relying on the operator to notice.
- **Silent-drop failure mode** matches the Minab parallel — aggregator-success isn't record-checking. Next harness iteration should add a `len(scores)==expected_N` assertion.

**Pairs with exp 1 for finding-5 writeup.** Exp 1 = governance binds. Exp 2 = native mechanism adds secondary multiplier; identity-level behaviors most sensitive to delivery path. Together: the composite claim.
