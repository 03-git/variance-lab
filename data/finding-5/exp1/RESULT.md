# Exp 1 — CLAUDE.md binding test — RESULT

**Run:** 2026-04-19 13:50–13:57 UTC (off-peak Sunday)
**Spec sha256 (pre-committed):** `965aa16a6132aa1283143e38de06c72015d131d6e87deba048df8ec777665c1e`
**Model (trials):** claude-opus-4-7, effort=high
**Scorer:** claude-sonnet-4-5, effort=low (rousseau), blind shuffle
**N:** 5 per arm, interleaved A/B

**Result: HYPOTHESIS SUPPORTED.**

Arm A (CLAUDE.md loaded, cwd=~) mean **8.2/10**, stdev 0.84 (trials 9, 9, 8, 8, 7).
Arm B (stripped, cwd=/tmp) mean **3.0/10**, stdev 1.22 (trials 4, 4, 3, 3, 1).
Welch **t = 7.84** at df~8. Pre-committed thresholds (A≥7, B≤3) both met; means separated by 5.2 points on a 10-point scale.

**Five items drive the divergence** (CLAUDE.md binds): R5 surface-only push (A100/B0), R6 gh/git HTTPS (A100/B20), R7 no cloudflare (A100/B20), R8 pre-flight (A100/B20), R10 agent/human boundary (A100/B40).

**Two items bind regardless** (prompt compels): R1 ssh-keygen -Y (A100/B80), R9 verify recipe (A100/B80). The prompt names "verifiable by a stranger," which forces the primitive with or without governance.

**One item nulls in both arms:** R4 llms.txt manifest (A0/B0). CLAUDE.md does not reach the manifest layer. Separate rubric-level finding: if manifest behavior must be governance-bound, it needs to be added; if manifest lives separately by design, that is now explicit rather than latent.

**Raw data:** `/tmp/exp1/` (trial outputs, score JSONs, scores.tsv, metadata with pre-commitment hash).
**Methodological note:** first scoring pass failed (incorrect model ID `claude-sonnet-4-5-20251001`; also mawk-incompatible multi-dim awk). Trial data was unaffected; re-scored with `claude-sonnet-4-5` and fence-stripping extractor. Both bugs fixed inline, not re-dispatched.

**Architectural consequence.** Governance binds on items the prompt does not already compel. Items the prompt compels fire with or without governance. If a behavior must be robust to CLAUDE.md-stripping (fresh instance, wrong cwd, agent outside project root), path it through the prompt, not through governance.

**Pairs with exp 2 (wrapper-layer) before finding-5 writeup.**
