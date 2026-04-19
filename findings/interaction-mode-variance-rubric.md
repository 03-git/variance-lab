---
title: Interaction-Mode-Variance Rerun — Pre-Committed Rubric
rubric_committed_utc: 2026-04-19T12:21:33Z
rubric_commit_purpose: pre-commitment artifact for rerun of findings/interaction-mode-variance.md (status: RERUN) — this rubric must predate any log extraction, classification, or analysis run against the corpus.
relates_to: findings/interaction-mode-variance.md
status: stub — analysis NOT performed, only rubric fixed
---

# Pre-Committed Rubric for Interaction-Mode-Variance Rerun

This file fixes the classification rubric **before** the rerun's log extraction, classification, and aggregation. It is the pre-commitment artifact whose absence caused the original finding to be flagged RERUN.

No analysis is performed in this file. No token counts, no session counts, no multipliers. Those belong in the rerun output, which must cite this rubric by commit hash.

---

## Turn thresholds (mode boundaries)

The thresholds below are fixed. They will not be re-fit against the observed data. If the observed distribution suggests different natural bins, that is a separate finding, not a reason to re-cut these boundaries.

| Mode | Bound | Definition |
|------|-------|------------|
| Pipe | `human_turns <= 1` | A single queued intent. Human appears at most once (the initial prompt). No round-trips, no mid-session steering. |
| Governor | `2 <= human_turns <= 3` | Scoped directive with minimal steering. The human sets scope and at most one correction or follow-up. |
| Collaborator | `4 <= human_turns <= 15` | Joint work. Both human and model contribute signal across multiple exchanges, bounded. |
| Passenger | `human_turns > 15` | Model-led exploration. The human has either abdicated scope control or is using the session as open-ended dialogue. |

**Turn-count precedence:** if a session's `human_turns` falls exactly on a bin boundary (e.g., 1, 3, 15), the mode is determined by the `<=` side of the table above. Boundaries are inclusive on the upper bound of the lower mode.

---

## What is a "human turn"

A human turn is **one contiguous user-authored message** recorded in the JSONL log with `role == "user"` where the content is not purely a tool result, system-injected reminder, or transcript compaction artifact.

**Counts as a human turn:**
- Free-text user messages (prompts, corrections, follow-ups, "continue", "stop").
- User messages that contain both text and attached tool results, provided the text portion is non-empty and human-authored.

**Does NOT count as a human turn:**
- Tool-call results returned to the model (`tool_result` content blocks without human prose).
- System-injected `<system-reminder>` / `<command-message>` payloads with no human prose.
- Automatic compaction summaries or session-restore preambles.
- Messages authored by another agent in a delegation chain (those are agent-to-agent, not human-to-agent).

Implementation note for the rerun: the classifier must count `role == "user"` messages whose text content, after stripping tool-result and system-reminder blocks, is non-empty.

---

## What counts as a session

A session is **one JSONL file under `~/.claude/projects/<project>/`** representing one Claude Code conversation thread, from first human turn to last recorded event.

**Counts as a session:**
- A JSONL file with at least one human turn (as defined above) AND at least one assistant response.
- Sessions that span multiple calendar days due to idle resume (the boundary is the file, not the clock).
- Sessions that were compacted mid-run (compaction is internal; the session continues).

**Does NOT count as a session:**
- JSONL files with zero human turns (pure automated / dispatched runs with no interactive component).
- JSONL files that contain only a tool-test harness or model-load probe with no actual task.
- Files that failed to initialize (malformed JSONL, truncated before the first assistant response).
- Sessions shorter than a single assistant response (user prompt issued but no model completion recorded).
- Subagent child transcripts when the parent transcript is already counted (avoid double-counting the same human's steering).

---

## Scoring criteria (per session)

For each qualifying session, the rerun extracts:

1. `session_id` — JSONL filename (sha or path-hash, not free-text).
2. `model_id` — exact model string from API usage fields; sessions with mixed models are excluded from single-model comparisons and reported separately.
3. `human_turns` — integer count per the definition above.
4. `mode` — derived from `human_turns` via the turn-threshold table. No other signal is used to assign mode.
5. `total_input_tokens`, `total_output_tokens`, `total_tokens` — summed from API usage fields across all assistant messages in the session.
6. `tool_calls` — count of assistant-emitted tool invocations.
7. `duration_utc_seconds` — last timestamp minus first timestamp, in seconds. Reported but NOT used as a cost metric (idle time inflates this).
8. `correction_flag_count` — count of human turns matching the correction keyword set below. Reported, not used for mode assignment.
9. `utc_start`, `utc_end` — ISO 8601 timestamps from the first and last JSONL events.

---

## Correction detection keyword set (fixed pre-commitment)

The rerun will use exactly this keyword set, matched case-insensitively against the text of each human turn. False-positive rate is acknowledged; the set is fixed here so it cannot be tuned to flatter the finding.

```
no, don't, do not, stop, wrong, not that, actually, wait, cancel, undo,
revert, that's wrong, that is wrong, incorrect, fix, redo
```

A human turn matches if any listed phrase appears as a token-bounded substring (word-boundary regex). Whole-turn match is not required.

The correction rate is reported per mode. It is NOT used to redefine modes.

---

## Aggregation

For each mode the rerun will report:

- `n_sessions`
- `total_tokens`, `mean_tokens_per_session`, `median_tokens_per_session`
- Same for `input_tokens` and `output_tokens` separately.
- `total_human_turns`, `total_tool_calls`
- `correction_rate = correction_flag_count / human_turns` (mode-aggregate)
- `outlier_sensitivity`: the mode-aggregate recomputed with the single largest-token session removed. Reported alongside the full aggregate. This is specifically to address the 152k-token / 53-subagent outlier's material effect on the passenger-mode average.

Cost-multiplier-style headlines (e.g., "Nx more tokens in passenger vs governor") will be computed as ratios of `mean_tokens_per_session` and will be reported **alongside** the median ratio and the outlier-removed ratio, never in isolation.

---

## Explicit non-goals

The rerun does **not**:

- Re-fit thresholds to the observed distribution.
- Add new modes after the fact.
- Change keyword sets after seeing results.
- Verify token counts against billing data (nice-to-have, not in scope for this rerun; if performed it would be a separate verification finding).
- Include sessions from other operators or other nodes. Same corpus as the original finding (single operator, single node, Claude Code JSONL logs) unless the corpus is explicitly re-scoped in a follow-on rerun.

---

## Commit contract

The first commit of this file on branch `rerun/finding-3` is the pre-commitment. Any subsequent edit that would change the thresholds, definitions, keyword set, aggregation, or non-goals after the rerun has begun extraction invalidates the pre-commitment and requires a fresh rubric file with a new timestamp.

Analysis commits on this branch must cite this file by commit hash in their commit message.
