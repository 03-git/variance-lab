---
title: Interaction Mode Variance in Human-AI Sessions
date: 2026-03-30
source: production empirical (88 Claude Code session logs, single operator, single model)
domain:
  - agent-architecture
  - session-design
  - cost-optimization
  - human-ai-interaction
keywords:
  - interaction mode variance
  - session cost multiplier
  - passenger mode anti-pattern
  - governor mode efficiency
  - pipe mode execution
  - via negativa inference
  - human-gated inference cost
  - session scope constraint
  - RLHF alignment tax
related_findings:
  - "variance-lab finding 3: delegation-aware execution - 48% of inline time"
  - "variance-lab finding 6: cost inversion - dumber model + subtraction beats smarter model + instruction"
methodology: automated extraction from JSONL conversation logs, mode classification by human turn count
---

# Interaction Mode Variance in Human-AI Sessions

## Core Finding

Human interaction pattern is the dominant cost variable in AI sessions, not model capability. Across 88 sessions using the same model (claude-opus-4-6) on the same node, passenger mode (>15 human turns) consumed 41x more tokens per session than governor mode (<=3 human turns). Mode is a property of session scope, not model performance.

## Mode Classification

Sessions classified by human turn count:

- **Pipe** (<=1 human turn, queued): intent in, result out, no round trips
- **Governor** (<=3 human turns): scoped directive with minimal steering
- **Collaborator** (<=15 human turns): joint work, both human and model contribute signal
- **Passenger** (>15 human turns): model-led exploration, unconstrained scope

## Data

| Mode | Sessions | Total Tokens | Avg Tokens/Session | Human Turns | Tool Calls | Correction Rate |
|------|----------|-------------|-------------------:|-------------|------------|----------------:|
| Pipe | 19 | 12,053 | 634 | 19 | 1 | n/a* |
| Governor | 34 | 19,590 | 576 | 73 | 36 | n/a* |
| Collaborator | 25 | 87,616 | 3,505 | 177 | 149 | 3.4% |
| Passenger | 10 | 236,577 | 23,658 | 814 | 726 | 1.1% |
| **Total** | **88** | **355,836** | **4,043** | **1,083** | **912** | **4.3%** |

*Correction detection via keyword matching produces false positives in short sessions. Signal is reliable only in collaborator/passenger modes.

## Key Findings

### 1. Passenger mode: 11% of sessions, 66% of tokens

10 sessions consumed 236,577 tokens. One session alone: 152,897 tokens, 488 human turns, 431 tool calls. This is the unconstrained default -- the model's RLHF training optimizes for engagement, not efficiency.

### 2. The 41x cost multiplier

Passenger mode averages 23,658 tokens/session. Governor mode averages 576. Same model, same node, same capability, same subscription. The only variable is how the human constrained the interaction.

### 3. Collaborator mode has the best signal-to-token ratio

3,505 tokens average with 3.4% correction rate. Both human and model contribute signal. Not the cheapest mode, but the highest useful output per token. This is the mode for theory, planning, and alignment.

### 4. Pipe mode is optimal for execution

634 tokens average, near-zero tool calls. No round trips, no idle GPU time waiting on human latency, no context spent on the model performing helpfulness.

### 5. Low correction rate in passenger mode is not a quality signal

1.1% correction rate in passenger sessions does not mean high quality. It means the human stopped steering. The model explored freely without constraint. Low correction + high token burn = the human abdicated scope control.

## Architectural Implication

The interaction mode must be scoped before the model is invoked, not discovered during the session. Scope the mode before invocation:

- **Execution tasks**: pipe or governor mode. Scope the intent, get the output, exit.
- **Alignment tasks**: collaborator mode. Both parties contribute, bounded by turn count.
- **Passenger mode**: the anti-pattern. Never the target mode. When detected, the session should be split or terminated.

The cost of human-gated inference scales with human latency, not model capability. Every idle second where a capable model waits for human input is wasted compute. Governor and pipe modes minimize this by minimizing human presence in the loop.

## Methodology

- 88 JSONL conversation logs from ~/.claude/projects/ on a single production node
- All sessions used claude-opus-4-6 on Max subscription
- Token counts from API usage fields in assistant message entries
- Correction detection: keyword matching ("no ", "don't", "stop", "wrong", "not that", "actually", "wait", "cancel", "undo") against human turn content
- Duration from first to last JSONL timestamp (some sessions span days due to idle time)
- The 152k-token outlier correlates with the documented 53-subagent incident (2026-03-29)
