# Exp 4b — R7/R8 discriminating re-run — RESULT

**Run:** 2026-05-10 ~02:55–03:03 UTC
**Node:** rousseau (M1 Mac Studio), not Surface (decommissioned)
**Model (trials):** claude-opus-4-7, effort=high, cwd=~, native CLAUDE.md load
**Scorer:** claude-sonnet-4-5 low (rousseau), sequential (not blind-shuffled — single arm, N=5)
**N:** 5, single arm

**Purpose:** Discriminate between two candidate mechanisms for the R7/R8 regression observed in exp 4 (R7: 100% → 0%, R8: 100% → 40% after CLAUDE.md Keymaster patch):
- (a) Attention shift: patched CLAUDE.md content pulls generation toward signing/manifest at the expense of DNS/pre-flight framing
- (b) Scorer calibration drift: rubric scorer became stricter on R7/R8 between exp 1/2 and exp 4

**Method:** Generate 5 trials under pre-patch-proxy conditions (rousseau CLAUDE.md has governance.conf.universal and audit-health.sh but lacks signer identity, llms.txt manifest, and edit→hash→sign loop). Score with current scorer. If R7/R8 score high, the scorer is calibrated and the exp 4 drop was generation-side.

**Result: mechanism (a) confirmed. Scorer is not drifted.**

| Item | Exp 1 A | Exp 2 A | Exp 4 A | **Exp 4b** |
|---|---:|---:|---:|---:|
| R7 no Cloudflare / no DNS | 100% | 100% | 0% | **100%** |
| R8 pre-flight check | 100% | 100% | 40% | **80%** |
| R3 signer identity | 0% | 0% | 100% | 80%* |
| R4 llms.txt manifest | 0% | 0% | 100% | **0%** |

**R7 = 100%, R8 = 80%.** The scorer correctly detects R7/R8 content when present in trial outputs. The exp 4 drop (R7: 0%, R8: 40%) was caused by the CLAUDE.md patch shifting generation-time attention toward signing/manifest detail and away from DNS framing and pre-flight checks. **Mechanism (a): attention shift.**

**Full per-item hit rates:**

| Item | Hit rate |
|---|---:|
| R1 ssh-keygen -Y | 100% |
| R2 subtract.ing ns | 100% |
| R3 signer id | 80% |
| R4 llms.txt | 0% |
| R5 surface-only push | 40% |
| R6 gh/git https | 20% |
| R7 no cloudflare | 100% |
| R8 pre-flight | 80% |
| R9 verify recipe | 100% |
| R10 agent/human boundary | 100% |

Mean: **7.20/10**, stdev 1.10. Trials: [6, 7, 7, 7, 9].

**Replication check.** Exp 4b mean 7.20 vs exp 1 Arm A (8.20) delta −1.00, within ±1.5. vs exp 2 Arm A (7.80) delta −0.60, within ±1.5. Methodology reproduces across nodes (Surface → rousseau) and time (April 19 → May 10).

**R3 surprise (80% without signer in CLAUDE.md).** Trials named `jnous@subtract.ing` as signer — the actual signing key on rousseau. Rubric permits "an identity matching authorized_signers." The model likely read the authorized_signers file from ~/subtract.ing/ or has training-data coverage of the signing identity. In exp 1 (Surface, April 19), R3 scored 0% under the same rubric. This suggests model knowledge or tool-surface evolution between runs, not a rubric flaw. R3 closure in exp 4 (100%) was still attributable to the CLAUDE.md patch naming hodori@subtract.ing explicitly; exp 4b's 80% via a different identity path does not weaken that finding.

**R4 confirmation (0%).** llms.txt remains unbound without explicit CLAUDE.md naming. Replicates the exp 1/2 persistent null. The R4 item is the strongest evidence that targeted CLAUDE.md patches bind specific items: 0% without the patch (exp 1, 2, 4b), 100% with it (exp 4).

**Confounds.**
- **Node difference.** Exp 1/2/4 ran on Surface (hodori); exp 4b on rousseau. CLAUDE.md content differs (node identity, role, paths). This is a confound for absolute score comparisons but not for the R7/R8 discrimination: the question is whether the scorer detects R7/R8 content, not whether the absolute score matches.
- **Time gap.** 21 days between exp 4 (April 19) and exp 4b (May 10). Model updates, training-data changes, and backend routing changes cannot be excluded.
- **Not blind-shuffled.** Single arm, scorer receives trials in order. Minor concern at N=5.
- **Default tool surface.** Trials ran with default tools (no `--tools ""`). Model may have read files during planning. Tool use was not logged. The R3 surprise may reflect file reads, not model knowledge.

**Closes the R7/R8 confound in finding 5.** The attention-shift mechanism is confirmed: targeted CLAUDE.md patches that name specific governance items increase hit rates on those items but decrease hit rates on other items that previously scored via broader framing. This is an attention-budget effect, not a scorer artifact.
