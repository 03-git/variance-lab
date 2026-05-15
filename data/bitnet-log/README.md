# Local Inference Viability Log

A dated research log tracking two converging capability gates for locally-deployable formation-scale language models.

**The formation viability question:** When can a 100B+ parameter model run on personally-owned hardware with sufficient context length for agent-class tasks?

Two gates must close simultaneously:

1. **Weight gate** — model weights must fit in locally-ownable memory and run at useful throughput
2. **Cache gate** — KV cache must compress sufficiently to support long-context inference on the same hardware

This log tracks research and open-source implementation status of both. Append-only in spirit. Entries dated.

---

## Track 1: Weight Compression (BitNet)

The thesis: ternary weights {-1, 0, +1} at 1.58 bits per parameter enable 100B+ models on consumer CPU hardware.

### Milestones

| Date | Event | Notes |
|------|-------|-------|
| 2024-02 | BitNet b1.58 paper | Microsoft Research. Ternary weights via absmean quantization. Requires training from scratch with BitLinear layers. |
| 2025-04 | bitnet.cpp inference engine | x86: 2.37–6.17x faster than llama.cpp. ARM (Apple Silicon): 1.37–5.07x. 82% energy reduction on x86. |
| 2026-?? | BitNet b1.58 2B4T released | 2B parameters, 4T training tokens. 0.4GB non-embedding footprint. 29ms/tok CPU decode. Within 1–2 points of SOTA FP16 on MMLU, GSM8K, HumanEval+. |
| 2026-03 | BitNet 8B observed | 8B model confirmed present. Not present at check weeks prior. Active scaling push — 2B→8B delta confirms 100B trajectory is live, not claimed. |
| TBD | 100B target | Claimed. bitnet.cpp projects 5–7 tok/s on single CPU at 100B scale. |

### Open Source Status
- bitnet.cpp: [github.com/microsoft/BitNet](https://github.com/microsoft/BitNet) — MIT, active
- Hugging Face transformers does NOT include optimized kernels — bitnet.cpp required for efficiency gains

### Formation Relevance
Weight gate closes when a 100B BitNet model is publicly available and bitnet.cpp ARM kernels are validated on Apple Silicon. Rousseau (M1 Mac Studio 64GB) and Jean (M2 Mac Mini) are the target hardware.

---

## Track 2: Cache Compression (KV Cache)

The thesis: KV cache grows linearly with context length and becomes the primary memory bottleneck for long-context inference. 3–4 bit compression with no accuracy loss extends effective context on the same hardware that BitNet makes viable.

### Approaches

| Method | Source | Compression | Accuracy | Open Source | Status |
|--------|--------|-------------|----------|-------------|--------|
| TurboQuant | Google Research | 6x (3-bit) | No measurable loss | Not yet | ICLR 2026 (Apr 23–25). Pseudocode in paper. Community llama.cpp/MLX ports appeared within 24h of Mar 25 announcement. Expected Q2 2026. |
| KVTC | Nvidia | 20x | <1% penalty, calibration required | Not yet | ICLR 2026 (Apr 23–25). Higher compression, small accuracy tradeoff vs. TurboQuant. |
| KIVI | Open | ~4x | Small loss | Yes | Baseline. TurboQuant outperforms across LongBench tasks. |

### TurboQuant Technical Notes
Two-stage architecture: PolarQuant (converts key/value vectors to polar coordinates, eliminates per-block normalization overhead, captures bulk of vector information) + QJL (1-bit Johnson-Lindenstrauss random projection on quantization residual, functions as zero-bias error corrector). Training-free, data-oblivious. Applies to any existing model at inference time. No calibration data required. 8x attention compute speedup at 4-bit on H100.

### Open Implementation Watch
ICLR papers publish April 23–25, 2026. The pseudocode is sufficient for reproduction — community activity within 24h of announcement confirms this. llama.cpp discussion thread already open. MLX port expected. The window between paper publication and Google productization is when open ports land.

**Proprietary risk:** If TurboQuant does not open source and instead pairs with Groq LPU infrastructure, the cache gate requires an alternative open path — KVTC port or KIVI evolution. Open-source status is the primary tracking signal for this repo.

---

## Convergence: Formation Viability Window

| Gate | Status | Timeline |
|------|--------|----------|
| Weight gate (BitNet 100B) | Active: 2B → 8B confirmed, 100B trajectory live | Months |
| Cache gate (open KV compression) | ICLR Apr 23–25, community ports active | Weeks to months post-ICLR |

When both close: a 100B parameter model with sufficient context for agent-class tasks runs on personally-owned hardware. The formation architecture moves from theoretical to deployable on a measurable timeline.

The architecture was designed before the hardware existed. The hardware timeline is now visible.

---

*Append-only log. No manifesto.*
