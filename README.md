# Local Variance Lab

A variance testing harness for measuring local LLM reliability per task class, designed to produce routing tables for autonomous agent model selection.

## Problem

Benchmarks measure throughput. Agents need reliability.

A local model that generates 50 tok/s with low latency looks production-ready by standard metrics. But when you read the output, you find fabricated file references, hallucinated version numbers, or flat refusals. Automated metrics (tokens/second, wall time, token count) cannot detect these failures. Only structured quality grading against known baselines reveals that a model producing fast output is producing *wrong* output.

The consequence: deploying a local model based on performance benchmarks alone leads to silent failures in production. An agent that self-selects its model without task-class-aware routing will use a fast local model for tasks it cannot complete, burn cycles, and deliver garbage.

## What This Harness Does

1. **Runs multi-pass variance tests** — same prompt, same model, N passes — to measure both speed variance and quality variance
2. **Tests across task classes** — not just "can it generate text" but "can it do code refactoring, security audits, research synthesis, operational planning"
3. **Compares against API baselines** — local model results are graded against known Anthropic (Haiku/Sonnet/Opus) baseline performance from controlled studies
4. **Produces a routing table** — a per-task-class, per-model decision matrix that agents embed in their runtime configuration for model self-selection

## Key Insight

Speed variance (CV on wall time) does not predict quality variance. A model can have the lowest speed CV in the cohort and still produce confident fabrications on 100% of passes for certain task classes. The routing table must be built from quality grading, not performance metrics.

## Architecture

```
local-variance-lab/
├── models.conf              # Model registry: endpoint:model:tier
├── prompts/                 # Task-class prompt files (.md)
│   ├── code-refactor.md
│   ├── security-audit.md
│   └── ...
├── run-local-batch.sh       # Batch runner (all models × all prompts × N passes)
├── run-local-single.py      # Single model/prompt runner (Ollama or LM Studio)
├── aggregate-local.py       # Aggregates metrics, produces routing table
└── output/                  # Run results
    └── run-YYYYMMDD-HHMMSS/
        ├── manifest.json    # Run metadata
        ├── routing-table.md # Generated routing table
        └── pass-N/
            └── <prompt>/
                └── <model>/
                    ├── config.json    # Run configuration
                    ├── metrics.json   # Automated metrics
                    └── response.md    # Raw model output
```

## Usage

### 1. Configure Models

Edit `models.conf`. Format: `endpoint:model_name:tier`

```
ollama:qwen2.5:7b:execution
ollama:qwen3:14b:execution
lmstudio:mistralai/devstral-small-2-2512:reasoning
```

Supported endpoints: `ollama` (port 11434), `lmstudio` (port 1234), or any OpenAI-compatible URL.

### 2. Write Prompts

Add task-class prompts to `prompts/` as markdown files. Each prompt should represent a distinct task class your agents will encounter in production. Good prompts:

- Require grounded reasoning (reading files, following instructions, citing sources)
- Have observable success/failure criteria
- Span your expected task difficulty range

### 3. Run a Batch

```bash
# Full run: all models, all prompts, 5 passes
./run-local-batch.sh --passes 5

# Filter by tier
./run-local-batch.sh --tier execution --passes 5

# Dry run to verify configuration
./run-local-batch.sh --dry-run
```

### 4. Aggregate and Grade

```bash
# Generate routing table from automated metrics
python3 aggregate-local.py output/run-YYYYMMDD-HHMMSS 5
```

This produces `routing-table.md` with per-model, per-task performance data compared against baselines.

**Critical step:** Read the `response.md` files. Automated aggregation cannot detect fabrication, hallucination, or task refusal. Quality grades (A/B/C/F) must be assigned by comparing model output against baseline behavior:

| Grade | Meaning |
|-------|---------|
| **A** | Matches or exceeds API baseline tier for this task class |
| **B** | Usable output but misses nuances the baseline catches |
| **C** | Output produced but contains fabrication, severity inflation, or is ungrounded |
| **F** | Fails to produce deliverable or output is unusable |

### 5. Build the Routing Table

The final routing table maps task classes to models with measured grades:

```
if api_available:
    use api tier per policy
elif task_class in routing_table:
    model = routing_table[task_class][best_available]
    if model.grade >= B:
        execute locally
    elif model.grade == C:
        execute locally + flag for review
    else:
        defer (do not execute locally)
else:
    defer (unknown task class)
```

Agents embed this table in their runtime configuration. At task dispatch, the agent checks the routing table, selects the appropriate model, and falls back to API or human review when local models cannot meet the quality floor.

## What You Will Likely Find

Based on testing across multiple model families (3B-14B parameter range):

- **Execution-class tasks** (code refactoring, structured planning): some local models achieve B grade — usable output with known limitations
- **Reasoning-class tasks** (security audits, operational monitoring): local models produce output that looks correct but contains fabricated findings or misses critical issues
- **Research-class tasks** (tooling landscape analysis, strategic synthesis): local models either fabricate with confidence or honestly refuse — neither is usable

The finding that matters: **the capability floor is structural, not stochastic.** Models that fail on a task class fail on every pass, not randomly. This means routing decisions are stable — you test once, grade once, and the table holds until the model or task changes.

## Requirements

- Python 3.8+
- [Ollama](https://ollama.ai) and/or [LM Studio](https://lmstudio.ai) running locally
- Models pulled and available via the configured endpoint

## License

Apache-2.0
