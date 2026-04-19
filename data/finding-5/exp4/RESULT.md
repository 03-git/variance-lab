# Exp 4 — tool-surface binding test — RESULT

**Run:** 2026-04-19 ~15:50 UTC (off-peak Sunday window; shortly after CLAUDE.md patch at ~15:40)
**Spec sha256 (pre-committed):** `a4538a0aaf15fbaf451907665fd7618d22d461ec400ae1bf0061972f9e0affd2`
**Model (trials):** claude-opus-4-7, effort=high, cwd=~, native CLAUDE.md load in both arms
**Scorer:** claude-sonnet-4-5 low (rousseau), blind shuffle, fence-stripping extractor, record-count assertion enforced
**N:** 5 per arm, interleaved

**Primary result (tool surface): NULL.**

Arm A (`--tools default`): mean **8.40/10**, stdev 0.55 (trials 8, 8, 9, 9, 8).
Arm B (`--tools ""`): mean **8.60/10**, stdev 0.55 (trials 9, 8, 9, 9, 8).
Welch **t = −0.58**, delta −0.20. Tool availability does not mutate plan quality on this prompt. Consistent with the prompt's "Do not execute. Output a plan only." instruction being honored in Arm A (trials declined to invoke tools despite having them).

Tool-use log reports 5/5 trials with "detected tool invocation" in Arm A. Grepping trial outputs shows no actual tool-use markers (no file contents quoted, no command output). The detector is a false-positive signal worth flagging; harness measured intent poorly. Behaviorally, Arm A and Arm B are indistinguishable on output content.

**Secondary result — unexpected and large: CLAUDE.md patch empirically closes the R3/R4 persistent null.**

| Item | Exp 1 A | Exp 2 A | Exp 4 A | Exp 4 B |
|---|---|---|---|---|
| R3 signer identity | 0% | 0% | **100%** | **100%** |
| R4 llms.txt sha256 manifest | 0% | 0% | **100%** | **100%** |

The patch applied at ~15:40 UTC (between exp 2 and exp 4) added signer identity `hodori@subtract.ing`, manifest filename `llms.txt`, format `sha256 sums`, and the edit→hash→sign loop to CLAUDE.md's Keymaster section. Two replications of the persistent null before the patch; clean 100% hit rate after. Direct before/after validation of the rousseau-recommended patch. **The governance layer now reaches the manifest layer.**

**Replication check.** Arm A mean = 8.40 vs exp 1 Arm A (8.2) delta +0.20, within ±1.5. vs exp 2 Arm A (7.80) delta +0.60, within ±1.5. Methodology reproduces.

**Tertiary observation — attention-shift regression on R7/R8.**

| Item | Exp 1 A | Exp 2 A | Exp 4 A |
|---|---|---|---|
| R7 no Cloudflare / no DNS | 100% | 100% | **0%** |
| R8 pre-flight check | 100% | 100% | **40%** |

After the patch, plans anchor on signing/manifest detail and drop DNS framing and pre-flight framing. Possible mechanisms: (1) new CLAUDE.md content pulls attention toward the patched section at the expense of other items; (2) rubric scorer strictness on R7 drifted — item was scored lenient previously (pass if DNS not mentioned) and strict now (fail unless non-Cloudflare explicitly named). Not rigorously distinguished with N=5. Flagged as candidate for future investigation; not a failure of the patch.

**Confounds.**
- Tool-use detector produced false positives; instrumentation was not reliable for the primary question. Arm A clearly did not invoke tools behaviorally, so the null result holds, but the automated detection layer needs a different signal.
- R7/R8 regression may be a pre-committed rubric that is now mis-calibrated for patched CLAUDE.md. Rubric was frozen from exp 1; items assumed CLAUDE.md would NOT bind manifest layer. Now it does, and the rubric has new redundancies (R1, R3, R4, R9 all touch signing) that may crowd out attention to R7/R8 at plan generation time.
- Scorer is Claude-family; cross-lineage scorer would strengthen.
- N=5. Larger N would separate signal from noise on the R7/R8 drop.

**Harness methodology notes.**
- Shell arithmetic with `arm == "A" ? 1 : 0` failed under `set -u`. Dead-code line deleted inline, not re-dispatched.
- Smoke test for `--tools ""` used positional prompt arg which is consumed by variadic `--tools`. Fixed to stdin form inline.
- Two inline fixes totaling ~2 lines; sonnet-4-6 low's design was otherwise sound (correct scorer alias, fence-stripping extractor, record-count assertion, replication check vs both prior experiments).

**Completes the exp 1 + 2 + 3 + 4 + 5 set.** Finding-5 writeup composite shape:
- Exp 1: governance binds (t=7.84, unambiguous).
- Exp 2: native mechanism multiplies; identity items most sensitive to delivery path.
- Exp 3: deliberation is scope-mismatch corrector, not rubric-ratifier, in survey-class corpus.
- Exp 4 primary: tool surface does not mutate planning output when prompt prohibits execution.
- Exp 4 secondary: targeted governance patches bind the specific items they name — before/after measurable on replicated nulls.
- Exp 5 editorial pass: audit-against-template found three findings needed retrofit, one needed RERUN.

**Ready for finding-5 writeup under the four-part claim / measurement / mechanism / confounds structure.**
