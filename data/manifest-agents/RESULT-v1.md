# Manifest-Agents Experiment — RESULT

**Run:** 2026-05-10 03:27–04:30 UTC
**Node:** rousseau (M1 Mac Studio)
**Trial model:** qwen2.5-7b-q4 (llama-server, localhost:8086, context 16384)
**Scorers:** claude-sonnet-4-5 (Anthropic), gemma-4-26B (Google, parsimony localhost:8087), qwen2.5-7b (Alibaba, localhost:8086)
**Corpus:** subtract.ing git repo (42 files, ~15K lines, excluding stb_truetype.h)
**Questions:** 30, stratified (10 traversal, 10 synthesis, 5 change detection, 5 similarity), pre-committed and signed

## Primary result: Arm R (BM25/RAG) outperforms Arm M (manifest) on answer quality.

**Composite quality (A1+A2+A3 mean):**

| Arm | Mean | Stdev | Range |
|---|---:|---:|---|
| M (manifest) | 2.76/5 | 0.64 | [1.4, 3.9] |
| R (BM25/RAG) | **3.41/5** | 0.70 | [1.7, 4.7] |

**Welch t = −3.72, delta −0.64.** Arm R produces higher-quality answers across all three quality dimensions (factual correctness, completeness, coherence). All three scorers agree on the direction; magnitude varies by scorer.

## Metric A: Answer quality (blind-scored, 3 scorers, 3 lineages)

| Dimension | Arm M | Arm R | Delta |
|---|---:|---:|---:|
| A1 Factual correctness | 2.83 | **3.54** | +0.71 |
| A2 Completeness | 2.38 | **3.10** | +0.72 |
| A3 Coherence | 3.08 | **3.58** | +0.50 |

Per-scorer breakdown shows consistent direction with calibration differences: Claude scores strictest (M=1.93, R=2.57), Gemma most generous (M=3.57, R=4.42), Qwen intermediate (M=2.79, R=3.23). All three rank R > M.

**By question type:**

| Type | N | Arm M | Arm R | Delta |
|---|---:|---:|---:|---:|
| Traversal | 10 | 2.94 | **3.77** | +0.83 |
| Synthesis | 10 | 2.73 | **3.58** | +0.85 |
| Change detection | 5 | 2.44 | 2.42 | −0.02 |
| Similarity | 5 | 2.78 | **3.33** | +0.55 |

Change detection is the only category where the arms tie. Both score poorly (~2.4/5) because neither arm provides git history — change-detection questions require commit data that neither manifest traversal nor BM25 retrieval supplies.

## Metric B: Cost per query

| Measure | Arm M | Arm R | Ratio M/R |
|---|---:|---:|---:|
| Wall time (mean ms) | 28,017 | **22,235** | 1.26x |
| Prompt tokens (mean) | 11,076 | **5,304** | 2.09x |
| Completion tokens (mean) | **363** | 495 | 0.73x |
| Total tokens (all queries) | 343,180 | **173,969** | 1.97x |
| Total wall time | 841s (14.0min) | **667s (11.1min)** | 1.26x |

Arm M consumes 2x the tokens because it includes the full manifest (~42 lines) plus entire file contents (up to 500 lines). Arm R retrieves only the most relevant 40-line chunks (top-12), producing more focused context at half the token cost. Arm R generates slightly more completion tokens (495 vs 363), possibly because it elaborates more when context is targeted vs when context is diluted.

## Metric C: Update cost

Not formally measured with the 5-file mutation protocol. Mechanical estimate: both re-walk (manifest-walk.sh) and re-index (rag-index.sh) complete in <2 seconds on this corpus. At 15K lines, neither approach has meaningful update overhead. The difference only matters at scale — re-indexing a million-line corpus would take minutes; re-walking a manifest would take seconds. **At this corpus size, C is a draw.**

## Metric D: Audit completeness

Qualitative assessment (formal independent-verifier trace not performed):

- **Arm M:** Manifest provides sha256 hashes for every file. Answer → source file tracing is structurally supported by the manifest TSV. If the manifest is signed (as in subtract.ing's llms.txt), the chain is cryptographically verifiable: answer cites file → manifest names file + hash → manifest is signed → verifier confirms. **D1: YES, D2: YES.**
- **Arm R:** BM25 chunks include source file paths. Answer → chunk → file tracing is possible but not cryptographically bound. Chunk boundaries are an implementation detail, not a signed artifact. **D1: YES, D2: NO.**

**Arm M wins on D.** This is the manifest approach's structural advantage: auditability is built into the artifact, not retrofitted.

## Selection rule application

Per rubric: "Arm dominance requires advantage on ≥3 of 4 metrics."

| Metric | Winner |
|---|---|
| A (quality) | **Arm R** (t=−3.72) |
| B (cost) | **Arm R** (2x fewer tokens) |
| C (update cost) | Draw (both trivial at this scale) |
| D (audit) | **Arm M** (signed manifest chain) |

**Arm R dominates on 2 of 4 metrics with 1 draw and 1 loss.** Neither arm achieves 3-metric dominance. Per the selection rule's tiebreaker: "If A is within 0.5 mean across arms → cost metrics decide." A is NOT within 0.5 (delta = 0.64), so the tiebreaker does not apply. **Result: no clean dominance. Arm R wins quality and cost; Arm M wins auditability.**

## Mechanism: why BM25 beats manifest on quality

The manifest approach retrieves **files** (100-2600 lines each). The BM25 approach retrieves **chunks** (40 lines each, top-12). On a 7B model with 16K context:

- Arm M fills ~11K tokens with manifest + full files. Much of this is irrelevant to the specific question. The model must find relevant content within large files — a needle-in-haystack task that 7B models handle poorly.
- Arm R fills ~5.3K tokens with the 12 most relevant chunks. The context is pre-filtered to question-relevant paragraphs. The model answers from concentrated evidence.

**File-level granularity is the manifest approach's weakness.** BM25 chunks provide paragraph-level precision. The manifest's structured metadata (file descriptions, hashes) does not compensate for the dilution of irrelevant file content in the context window.

This mechanism predicts that the gap would **narrow** with larger models (better at long-context needle-in-haystack) and **widen** with larger corpora (more irrelevant files in manifest context).

## Boundaries where the losing arm wins

Per rubric: "Boundaries where the losing arm wins MUST be named explicitly."

1. **Audit traceability (Metric D).** The manifest approach provides a cryptographically signed chain from answer to source. RAG cannot match this without bolting on a separate signing layer — which is exactly what the manifest already is.

2. **Change detection (tied).** Both arms fail equally, but for different reasons. A manifest-aware system COULD detect changes via mtime-filtered walks or hash comparisons; RAG re-indexing is opaque. Neither arm implemented this in the experiment because both used static snapshots.

3. **Corpus-update cost at scale (Metric C, projected).** Re-walking a manifest is O(n) on directory entries. Re-indexing BM25 after a 5-file change requires re-chunking those files and updating the FTS5 index — mechanically similar cost at small N, but embedding-based RAG (not tested here) would require re-embedding, which is much more expensive.

## Confounds

- **Self-scoring.** Qwen2.5-7b scored its own outputs. Qwen's scores directionally agree with Claude and Gemma (R > M on all dimensions), so self-scoring bias, if present, is not arm-differential. But the absolute calibration of Qwen scores is suspect.
- **File selection heuristic.** Arm M's keyword-based file selection is naive (grep keywords from question against filenames and content, rank by hit count, take top-5). A smarter selection heuristic (e.g., using the manifest descriptions as a routing table) might improve Arm M. The current implementation tests "manifest + naive file selection" not "manifest + optimal file selection."
- **Context budget asymmetry.** Arm M receives ~11K tokens of context; Arm R receives ~5.3K. Arm M's context is larger but less targeted. A fairer comparison might cap both arms at the same token budget.
- **Single corpus, single model.** Results are from one 7B model on one 15K-line repo. Generalization to larger corpora, larger models, or different repo structures is not tested.
- **No public corpus.** The rubric specified "subtract.ing repo + one public corpus." Only subtract.ing was used. The public corpus test is not performed.
- **BM25 not embedding-based RAG.** The rubric arm description says "chunk + embed + vector retrieval." This experiment used BM25 (keyword matching) not embedding-based retrieval. BM25 is simpler and cheaper but may underperform embeddings on semantic similarity queries.
- **Scorer calibration spread.** Claude, Gemma, and Qwen scorers show large calibration differences (Claude mean ~2.2, Gemma ~4.0, Qwen ~3.0). The direction is consistent but absolute scores are not comparable across scorers.

## Methodology cost disclosure

- Total metered spend: $0 (all under Max-plan subscription)
- Subscription tier: Max plan
- Local inference: qwen2.5-7b-q4 + gemma-4-26B-Q4_K_M on M1 Mac Studio 64GB
- Estimated metered cost if reproduced: ~$5-10 (60 sonnet-4-5 scoring calls; local inference free)
- Wall clock: ~90 minutes total (30 min dispatch, 30 min qwen+gemma scoring, 30 min claude scoring)
