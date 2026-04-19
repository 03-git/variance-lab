# Finding 5 data — Governance Binding, Delivery-Path Sensitivity, and Targeted Patch Validation

Artifacts backing `subtract.ing/variance-lab.txt` Finding 5 (2026-04-19).

## Experiments

- `exp1/` — CLAUDE.md binding test (native vs stripped). Spec sha256 `965aa16a6132aa1283143e38de06c72015d131d6e87deba048df8ec777665c1e`.
- `exp2/` — CLAUDE.md delivery-path test (native vs inline prepend). Spec sha256 `8075578ce25da42639f798c413eaf644c4877a912867950cf647ccc6121eaec7`.
- `exp3/` — this was demoted to a methodology note in the 2026-04-19 late-afternoon editorial pass; retained here as scratch.
- `exp4/` — tool-surface binding test + R3/R4 patch validation. Spec sha256 `a4538a0aaf15fbaf451907665fd7618d22d461ec400ae1bf0061972f9e0affd2`.
- `exp5-editorial-audit/` — eight-voter audit of findings 1-4. Voter outputs (`voter1..8.out.md`), synthesis (`synthesis.md`), ship decisions per voter (`dec1..8.md`), and the execution log (`execute.out.md`).

## Voter model identities (exp5)

- V1: rousseau claude-opus-4-7 high
- V2: emile claude-opus-4-7 high
- V3: rousseau claude-sonnet-4-5 high
- V4: rousseau claude-sonnet-4-6 high
- V5: emile claude-sonnet-4-5 low
- V6: emile claude-sonnet-4-6 high
- V7: rousseau gemma-4-26b (via nanobot reasoning)
- V8: rousseau qwen3-coder-30b (via direct `/v1/chat/completions` on port 8084)

V7 category-errored (applied implementation-selection template to survey documents); V8 hallucinated gate results. Both outputs preserved as data per minority-voter-signal policy.
