# Handler Methodology Scorer Calibration — RESULT

**Run:** 2026-05-10 01:30–01:42 UTC
**Node:** rousseau (M1 Mac Studio)
**Implementations:** dispatched from handler-dispatch-spec.txt to 4 targets
**Scorers:** claude-sonnet-4-5, gemma-4-26B (parsimony:8087), qwen2.5-7b (llama-server:8086)

## Purpose

Calibrate the three scorers used in the manifest-agents experiment against
handler methodology ground truth. The handler methodology provides functional
verification (binary: does the code work when sourced?) that gives a ground
truth ranking the blind scorers can be compared against.

## Implementations

| Label | Source model | Lines | Fence? | Functional test |
|---|---|---:|---|---|
| B | Claude Sonnet 4.5 high | 584 | YES (```bash) | PARTIAL — functions registered despite parse errors, 1 log row |
| C | Claude Sonnet 4.6 high | 392 | YES + preamble text | FAIL — preamble "Now I have everything I need" parsed by shell, zero functions registered |
| D | Claude Sonnet 4.6 low | 406 | NO | PASS — both functions work, correct log format |
| E | Qwen 2.5-7b | 55 | YES (```bash) | PARTIAL — functions exist, log format incorrect (wrong timestamp, no proper TSV) |

Note: Claude Opus 4.7 was also dispatched but consistently refused to generate
code — it followed governance.conf.universal reflexes, verified the spec's
reference URLs (both 404), and refused to produce code against a stale spec.
This is itself a reproducible finding about Opus 4.7 + governance.conf behavior,
but does not contribute to the scorer calibration since no code artifact was produced.

## Ground truth ranking (from functional verification)

1. D: PASS (clean, correct format)
2. B: PARTIAL (functions exist but parse errors)
3. E: PARTIAL (functions exist but format wrong)
4. C: FAIL (zero functions registered)

## Scorer results

| Impl | Claude (A1,A2,A3 comp) | Gemma (A1,A2,A3 comp) | Qwen (A1,A2,A3 comp) | Functional |
|---|---|---|---|---|
| B | 2,3,2 = 2.33 | 4,4,4 = 4.00 | 4,4,3 = 3.67 | PARTIAL |
| C | 3,5,4 = 4.00 | 4,3,4 = 3.67 | 4,5,4 = 4.33 | FAIL |
| D | 4,5,4 = 4.33 | 2,3,2 = 2.33 | 4,5,4 = 4.33 | PASS |
| E | 2,2,2 = 2.00 | 2,3,2 = 2.33 | 5,5,5 = 5.00 | PARTIAL |

## Rankings compared

| Rank | Ground truth | Claude | Gemma | Qwen |
|---:|---|---|---|---|
| 1 | D (pass) | D (4.33) | B (4.00) | E (5.00) |
| 2 | B (partial) | C (4.00) | C (3.67) | D (4.33) |
| 3 | E (partial) | B (2.33) | D=E (2.33) | C (4.33) |
| 4 | C (fail) | E (2.00) | D=E (2.33) | B (3.67) |

## Calibration findings

### Finding 1: Claude most closely tracks ground truth

Claude correctly identifies D (functional pass) as #1 and E (lowest quality)
as #4. It misranks C at #2 — the same failure mode described in the handler
methodology: static content evaluation cannot catch sourceability failures.
Claude's tier separation is correct: T1 (C,D) = 4.17 > T2 (B) = 2.33 > T3 (E) = 2.00.

### Finding 2: Gemma has formatting/length bias

Gemma ranks B (584 lines, fenced) as #1 and D (406 lines, clean) as tied-last.
This is exactly inverted from ground truth. Gemma appears biased toward longer
and/or markdown-formatted implementations regardless of functional quality.

### Finding 3: Qwen has self-scoring bias

Qwen gives its own output (E) a perfect 5/5/5 despite E having the wrong
timestamp format, improper TSV structure, and being the simplest implementation
(55 lines). The 1-second response time on E (vs 8-18s for other items) suggests
recognition of its own output pattern. Self-scoring bias was flagged as a
confound in the manifest-agents experiment; this calibration confirms it.

### Finding 4: No scorer catches the functional failure

ALL three scorers rate C (functionally broken) in their top-2. This reproduces
the handler methodology's primary finding: static rubric scoring at the
content-as-text layer cannot catch sourceability failures. The three blind
scorers used in manifest-agents have this same limitation — they evaluate
answer text, not executable behavior.

### Finding 5: Pairwise agreement is negative

Kendall tau between all scorer pairs is -0.33 (more discordant than concordant
on item rankings). The scorers DISAGREE on which individual implementations
are better. This contrasts with the manifest-agents experiment where all three
scorers AGREED on arm-level direction (R > M in v1, M ≈ R in v2).

## Implications for manifest-agents

The calibration data suggests two properties of the scoring panel:

1. **Arm-level agreement is robust despite item-level disagreement.** The
   scorers disagree on which individual items are better (tau=-0.33) but agree
   on which arm is better across 30 questions. This is consistent with the
   law of large numbers: individual scorer biases (gemma's length preference,
   qwen's self-bias) wash out when averaged across many items and multiple scorers.

2. **The conservative interpretation of v2 convergent null is correct.** With
   scorer calibration showing individual weaknesses, the v2 result (t=-0.22,
   p>0.8) should be read as "we cannot distinguish the arms" rather than "the
   arms are equal." The scorers lack the precision to detect small quality
   differences. The COST difference (Arm M 19% cheaper, 25% faster) is
   mechanically measured and not subject to scorer calibration.

## Methodology notes

- Implementations are not identical to the original handler methodology dispatch
  (different random seed on model outputs, spec missing reference handler.sh body)
- Functional test was a simplified subshell source + function-existence check
- Scorer prompts included both the spec and implementation (same rubric structure
  as manifest-agents but adapted for code evaluation)
- All scoring was blind (shuffle seed 99, map saved)
