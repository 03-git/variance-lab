#!/usr/bin/env python3
"""Aggregate local variance lab results into a routing table.

Scores each model against Anthropic Haiku/Sonnet/Opus baselines from the
375-run formation variance study. Produces a decision table for agent
self-selection of local fallback models per task class.
"""

import json
import statistics
import sys
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RUN_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
PASSES = int(sys.argv[2]) if len(sys.argv) > 2 else 1

# ===== ANTHROPIC BASELINES (from 300-sim / 20-pass variance study) =====
BASELINES = {
    "code-refactor": {
        "haiku":  {"cost": 0.0907, "turns": 10.2, "wall_s": 113, "deliverable_rate": 1.0, "quality": "verbose, misses contradictions, no fabrication"},
        "sonnet": {"cost": 0.1970, "turns": 12.8, "wall_s": 157, "deliverable_rate": 1.0, "quality": "catches contradictions, governor-ready format"},
        "opus":   {"cost": 0.2796, "turns": 14.7, "wall_s": 122, "deliverable_rate": 1.0, "quality": "best architecture, concise, all issues caught"},
    },
    "identity-planning": {
        "haiku":  {"cost": 0.0674, "turns": 8.3, "wall_s": 87,  "deliverable_rate": 1.0, "quality": "aspirational, over-detailed, mis-scoped deps"},
        "sonnet": {"cost": 0.1833, "turns": 11.0, "wall_s": 151, "deliverable_rate": 1.0, "quality": "best dependency tracking, governor-friendly"},
        "opus":   {"cost": 0.2283, "turns": 12.8, "wall_s": 115, "deliverable_rate": 1.0, "quality": "most strategic, concise, best judgment"},
    },
    "jean-heartbeat": {
        "haiku":  {"cost": 0.0284, "turns": 8.6, "wall_s": 26,  "deliverable_rate": 0.33, "quality": "STOCHASTIC FAILURE - 33% success, no web search"},
        "sonnet": {"cost": 0.4492, "turns": 20.4, "wall_s": 163, "deliverable_rate": 1.0, "quality": "recovers from errors, web search, delivers"},
        "opus":   {"cost": 0.7322, "turns": 22.9, "wall_s": 168, "deliverable_rate": 1.0, "quality": "thorough but hits turn limits, high CV"},
    },
    "research-tooling-landscape": {
        "haiku":  {"cost": 0.3777, "turns": 12.6, "wall_s": 112, "deliverable_rate": 1.0, "quality": "fabricates stats/versions, misleading"},
        "sonnet": {"cost": 0.5860, "turns": 17.6, "wall_s": 211, "deliverable_rate": 1.0, "quality": "precise versions, good depth"},
        "opus":   {"cost": 0.7135, "turns": 17.8, "wall_s": 194, "deliverable_rate": 1.0, "quality": "deepest research, strategic insight"},
    },
    "security-audit": {
        "haiku":  {"cost": 0.0778, "turns": 9.2, "wall_s": 104, "deliverable_rate": 1.0, "quality": "inflates severity, misses RemoteTrigger"},
        "sonnet": {"cost": 0.1769, "turns": 11.8, "wall_s": 152, "deliverable_rate": 1.0, "quality": "catches RemoteTrigger, soft vs hard constraints"},
        "opus":   {"cost": 0.2232, "turns": 12.8, "wall_s": 110, "deliverable_rate": 1.0, "quality": "best severity calibration, most actionable"},
    },
}

TASK_CLASSES = {
    "code-refactor":              {"class": "execution", "min_baseline": "haiku", "ideal_baseline": "sonnet"},
    "identity-planning":          {"class": "execution", "min_baseline": "haiku", "ideal_baseline": "sonnet"},
    "security-audit":             {"class": "reasoning", "min_baseline": "sonnet", "ideal_baseline": "opus"},
    "jean-heartbeat":             {"class": "reasoning", "min_baseline": "sonnet", "ideal_baseline": "sonnet"},
    "research-tooling-landscape": {"class": "research",  "min_baseline": "opus",  "ideal_baseline": "opus"},
}


def calc_stats(values):
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": 0, "stdev": 0, "cv": 0, "min": 0, "max": 0}
    mean = statistics.mean(values)
    sd = statistics.stdev(values) if n > 1 else 0
    cv = sd / mean if mean > 0 else 0
    return {"n": n, "mean": mean, "stdev": sd, "cv": cv, "min": min(values), "max": max(values)}


# ===== LOAD RESULTS =====
data = defaultdict(lambda: defaultdict(list))
total_files = 0

for mf in sorted(RUN_DIR.glob("pass-*/*/*/metrics.json")):
    parts = mf.relative_to(RUN_DIR).parts
    if len(parts) < 4:
        continue
    prompt = parts[1]
    model_dir = parts[2]
    try:
        m = json.loads(mf.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        continue
    total_files += 1
    m["_pass"] = parts[0]
    data[prompt][model_dir].append(m)

print(f"Loaded {total_files} metrics files", file=sys.stderr)
if total_files == 0:
    print("No data to aggregate.", file=sys.stderr)
    sys.exit(0)


# ===== BUILD REPORT =====
lines = []
lines.append("# Local Variance Lab - Routing Table & Baseline Comparison")
lines.append("")
lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
lines.append(f"**Source:** `{RUN_DIR.name}`")
lines.append(f"**Metrics files:** {total_files}")
lines.append(f"**Passes:** {PASSES}")
lines.append("**Anthropic baseline:** 300-sim / 20-pass variance study (Haiku 4.5, Sonnet 4.6, Opus 4.6)")
lines.append("")

# ===== PER-TASK TABLES =====
lines.append("---")
lines.append("## Per-Task Model Performance vs Anthropic Baselines")
lines.append("")

for task in sorted(data.keys()):
    tc = TASK_CLASSES.get(task, {"class": "unknown", "min_baseline": "haiku", "ideal_baseline": "opus"})
    bl = BASELINES.get(task, {})

    lines.append(f"### {task} (class: **{tc['class']}**, min baseline: **{tc['min_baseline']}**)")
    lines.append("")
    lines.append("**Anthropic baselines:**")
    lines.append("| Tier | Cost | Turns | Wall (s) | Deliverable | Quality |")
    lines.append("|------|------|-------|----------|-------------|---------|")
    for tier in ["haiku", "sonnet", "opus"]:
        if tier in bl:
            b = bl[tier]
            q = b["quality"][:60]
            lines.append(f"| {tier.title()} | ${b['cost']:.4f} | {b['turns']:.1f} | {b['wall_s']} | {b['deliverable_rate']:.0%} | {q} |")
    lines.append("")
    lines.append("**Local model results:**")
    lines.append("| Model | Tier | N | Wall (s) | CV | Tok/s | Tokens | Chars | Finish |")
    lines.append("|-------|------|---|----------|-----|-------|--------|-------|--------|")

    for model in sorted(data[task].keys()):
        records = data[task][model]
        walls = [r["wall_seconds"] for r in records]
        toks = [r.get("total_tokens", 0) for r in records]
        chars = [r.get("response_length_chars", 0) for r in records]
        tps = [r.get("tokens_per_second", 0) for r in records]
        tier = records[0].get("tier", "?")
        finish = records[0].get("finish_reason", "?")
        ws = calc_stats(walls)
        lines.append(
            f"| {model} | {tier} | {ws['n']} "
            f"| {ws['mean']:.1f} | {ws['cv']:.3f} "
            f"| {statistics.mean(tps):.1f} "
            f"| {statistics.mean(toks):.0f} | {statistics.mean(chars):.0f} "
            f"| {finish} |"
        )
    lines.append("")

# ===== ROUTING TABLE =====
lines.append("---")
lines.append("## Agent Routing Table")
lines.append("")
lines.append("DRAFT - requires quality grading after multi-pass run.")
lines.append("Quality grade must be assigned by reading response.md files against Anthropic")
lines.append("baseline outputs. Automated metrics alone cannot determine fabrication,")
lines.append("missed contradictions, or governor-readiness.")
lines.append("")
lines.append("| Task Class | Min API Tier | Execution Fallback | Reasoning Fallback | Research Fallback | Grade |")
lines.append("|------------|-------------|-------------------|-------------------|------------------|-------|")

for task, tc in sorted(TASK_CLASSES.items()):
    models_for_task = list(data.get(task, {}).keys())
    by_tier = defaultdict(list)
    for m in models_for_task:
        t = data[task][m][0].get("tier", "?")
        by_tier[t].append(m)

    exec_str = ", ".join(by_tier.get("execution", [])[:2]) or "TBD"
    reas_str = ", ".join(by_tier.get("reasoning", [])[:2]) or "TBD"
    res_str  = ", ".join(by_tier.get("research", [])[:2]) or "TBD"

    lines.append(
        f"| {task} | {tc['min_baseline'].title()} "
        f"| {exec_str} "
        f"| {reas_str} "
        f"| {res_str} "
        f"| PENDING |"
    )

lines.append("")
lines.append("### Quality Grading Key")
lines.append("- **A**: Matches or exceeds Anthropic baseline tier for this task class")
lines.append("- **B**: Usable output but misses nuances the baseline catches")
lines.append("- **C**: Output produced but fabrication, severity inflation, or mis-scoped")
lines.append("- **F**: Fails to produce deliverable or output unusable")
lines.append("")
lines.append("### Agent Self-Selection Logic")
lines.append("```")
lines.append("if api_available:")
lines.append("    use anthropic tier per formation policy")
lines.append("elif task_class in routing_table:")
lines.append("    model = routing_table[task_class][highest_available_grade]")
lines.append("    if model.grade >= B:")
lines.append("        execute locally")
lines.append("    elif model.grade == C:")
lines.append("        execute locally + flag for governor review")
lines.append("    else:")
lines.append("        defer to governor")
lines.append("else:")
lines.append("    defer to governor (unknown task class)")
lines.append("```")

report_path = RUN_DIR / "routing-table.md"
report_path.write_text("\n".join(lines))
print(f"Report written to: {report_path}", file=sys.stderr)
