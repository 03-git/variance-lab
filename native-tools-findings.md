# Native Tools Findings

Test results from native-tools-testing.md. Ran 2026-04-14 on Rousseau.

## Summary

| Feature | Finding | Primitive |
|---------|---------|-----------|
| effort | INVALIDATED | `--model` flag |
| mcp | PRIMITIVE WINS | llama-server tool API |
| compact | BLOCKED | session discipline |
| review | NOT TESTED | diff(1), git log |
| simplify | NOT TESTED | xargs -P |
| loop | NOT TESTED | cron, at |
| routines | NOT TESTED | crontab |
| skills | NOT TESTED | CLAUDE.md, exec |
| multi-session | NOT TESTED | tmux |

**Score: 1 invalidated, 1 primitive wins, 1 blocked, 6 not tested.**

**Structural finding:** Every feature wraps IPC, timers, or diff. Wrappers add LLM judgment, remove determinism and auditability.

## Findings

### effort: INVALIDATED

**Spec assumed:** `/effort low|medium|high` routes to T1/T2/T4 models.

**Reality:** `--effort` adjusts reasoning depth within the SAME model. Does not change which model runs.

**Primitive:** `--model` flag achieves intended behavior.

```bash
# T1 routing (what spec intended)
claude -p --model claude-haiku-4-5-20251001 "..."

# T2 routing
ollama run qwen3:32b "..."

# T4 routing
claude -p "..."  # defaults to session model
```

**Cost delta:**
```
Feature path (Opus 4.5):  15470 in + 29 out = $0.00885
Primitive path (Haiku):   15470 in + 29 out = $0.00342
Savings: $0.00543 / $0.00885 = 61%
```

**Conclusion:** Spec error. `/effort` and model routing are orthogonal features. T1-T2-T4 escalation is genuinely novel, not a reimplementation of `/effort`.

### mcp: PRIMITIVE WINS

**Spec assumed:** MCP provides tool integration that primitives cannot.

**Reality:** llama-server exposes OpenAI-compatible tool-calling API with built-in tools.

**Primitive:** llama-server `--tools` flag.

```bash
# Built-in tools available:
# read_file, write_file, edit_file, apply_diff,
# file_glob_search, grep_search, exec_shell_command

# qwen3-32b successfully chains 3-step tool sequences
# (query -> transform -> write)
```

**Sovereignty:** Works without platform dependency. Local execution.

**Conclusion:** MCP is JSON-RPC wrapper around capability llama-server already has.

### compact: TEST BLOCKED

**Reason:** Requires 50k+ token context accumulation. Fresh session cannot test meaningfully.

**Spec correction:** Session storage is per-UUID files (`~/.claude/projects/{project}/{uuid}.jsonl`), not single `session.jsonl`.

**Primitive path (updated):**
```bash
# Inspect session size
wc -l ~/.claude/projects/{project}/*.jsonl

# View recent context
tail -100 ~/.claude/projects/{project}/{uuid}.jsonl

# Start fresh session when context dense
# Zero tokens, deterministic, operator controls discard
```

**Recommendation:** Run test during natural high-context session, not artificially constructed.

## Raw Data

Results logged to: `~/human/variance-lab/data/feature-results.jsonl`

Test fixtures at: `~/human/variance-lab/feature-tests/`

## Next Steps

1. Test remaining features (review, simplify, loop, routines, skills, multi-session)
2. Run compact test during natural high-context session
3. Update spec with effort correction

## Sources

- Rousseau dispatch 2026-04-14: test execution
- webclaude 2026-04-14: effort misconception identification
- feature-results.jsonl: raw test data
