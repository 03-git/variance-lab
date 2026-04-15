# Native Tools Findings

Test results from native-tools-testing.md. Ran 2026-04-14 on Rousseau.

## Summary

| Feature | Finding | Primitive |
|---------|---------|-----------|
| effort | INVALIDATED | `--model` flag |
| mcp | PRIMITIVE WINS | llama-server tool API |
| loop | PRIMITIVE WINS | while/sleep |
| skills | NOT JUSTIFIED | cat + CLAUDE.md |
| review | MARGINALLY JUSTIFIED | diff + grep |
| simplify | FEATURE JUSTIFIED | xargs -P + grep |
| compact | BLOCKED | session discipline |
| multi-session | NOT TESTED | tmux |
| routines | BLOCKED | crontab (needs harness) |

**Score: 2 primitive wins, 1 invalidated, 1 feature justified, 1 marginally justified, 1 not justified, 1 blocked, 2 not tested.**

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

### loop: PRIMITIVE WINS

**Feature path:** `/loop` with 60s minimum interval. Tokens charged per wakeup. State in platform context.

**Primitive path:** `while/sleep` loop.
```bash
while ! check_condition; do sleep 10; done
```

**Results:**
```
Primitive: 0 tokens, any interval, full log preserved, sovereign
Feature:   1800 tokens/min, 60s min interval, state in platform
```

**Quality:** Primitive 1.0, Feature 0.4 (min interval constraint limits utility).

**Conclusion:** Primitive wins. while/sleep is zero-cost, any interval, fully observable.

### skills: NOT JUSTIFIED

**Finding:** Skills ARE markdown files. The primitive `cat` works on them.

**Primitive path:**
```bash
cat ~/.claude/plugins/**/SKILL.md  # 0.02s
claude -p "$(cat template.md)"
```

**Feature path:** Skill tool loads same markdown with LLM inference overhead.

**Falsification results:**
- "Skills provide capability CLAUDE.md cannot express" → FALSE
- "Template discovery faster than file glob" → FALSE (glob: 0.02s)

**Conclusion:** Skills add indirection without capability gain. Store templates in files, cat them.

### review: MARGINALLY JUSTIFIED

**Primitive path:**
```bash
git diff --staged
git log --oneline -5
git diff --staged | grep -E '(password|secret|token)'
```

**Feature path:** `/review` with semantic analysis.

**Falsification results:**
- "human_effort > 5 min per 100 lines" → TRUE for shell scripts
- "feature catches issue human missed" → INCONCLUSIVE
- "primitive requires 3+ commands" → TRUE

**True positives:** 3 (quoting bugs in shell)
**False positives:** 1
**Intent comprehension:** Feature 0.9, Primitive 0.5

**Conclusion:** Feature justified for shell scripts where quoting/safety issues are subtle. Primitive sufficient for simple diffs.

### simplify: FEATURE JUSTIFIED

**Primitive path:**
```bash
grep -rn "pattern" . | sort | uniq -c | sort -rn  # find dupes
find . -name "*.js" | xargs -P4 eslint            # parallel lint
```
Result: Found dupes, missed loop→map/reduce refactoring. 8 human minutes. Quality 0.8.

**Feature path:** `/simplify`
Result: 60% line reduction, caught semantic patterns (loop→reduce, dead code, reuse opportunities). 0 human minutes. Quality 1.0.

**Cost delta:**
```
Feature: 1200 in + 800 out tokens, 39s wall
Primitive: 0 tokens, 8 min human effort
```

**Conclusion:** Feature justified. Catches semantic patterns (loop refactoring, function reuse) that grep/sed cannot express. Human effort savings significant.

## Raw Data

Results logged to: `~/human/variance-lab/data/feature-results.jsonl`

Test fixtures at: `~/human/variance-lab/feature-tests/`

## Next Steps

1. Run compact test during natural high-context session
2. Test multi-session (tmux vs sidebar) when opportunity arises
3. Routines blocked until harness lifecycle events testable

## Sources

- Rousseau dispatch 2026-04-14: test execution
- webclaude 2026-04-14: effort misconception identification
- feature-results.jsonl: raw test data
