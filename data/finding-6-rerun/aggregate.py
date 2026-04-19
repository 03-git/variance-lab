#!/usr/bin/env python3
# rubric_commit: 49d86f7
# rubric_path: findings/interaction-mode-variance-rubric.md
# median method: statistics.median (rounds half to even via Python's built-in)

import sys
import csv
import statistics

def main():
    src, out_agg, out_rat = sys.argv[1], sys.argv[2], sys.argv[3]

    MODES = ["pipe", "governor", "collaborator", "passenger"]

    rows = {m: [] for m in MODES}
    with open(src, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["qualifying"].strip() != "1":
                continue
            m = row["mode"].strip()
            if m not in rows:
                continue
            rows[m].append({
                "session_id": row["session_id"],
                "total_tokens": int(row["total_tokens"]),
                "total_input_tokens": int(row["total_input_tokens"]),
                "total_output_tokens": int(row["total_output_tokens"]),
                "human_turns": int(row["human_turns"]),
                "tool_calls": int(row["tool_calls"]),
                "correction_flags": int(row["correction_flag_count"]),
            })

    agg = {}
    for m in MODES:
        data = rows[m]
        n = len(data)
        if n == 0:
            agg[m] = {"n": 0}
            continue

        tot = [r["total_tokens"] for r in data]
        inp = [r["total_input_tokens"] for r in data]
        out = [r["total_output_tokens"] for r in data]
        ht = sum(r["human_turns"] for r in data)
        tc = sum(r["tool_calls"] for r in data)
        cf = sum(r["correction_flags"] for r in data)

        # find outlier (largest total_tokens)
        max_row = max(data, key=lambda r: r["total_tokens"])

        if n > 1:
            trimmed = [r for r in data if r is not max_row]
            tot_t = [r["total_tokens"] for r in trimmed]
            mean_or = round(statistics.mean(tot_t))
            median_or = round(statistics.median(tot_t))
            drop_id = max_row["session_id"]
            drop_tok = max_row["total_tokens"]
        else:
            mean_or = median_or = drop_id = drop_tok = ""

        agg[m] = {
            "n": n,
            "sum_total": sum(tot),
            "mean_total": round(statistics.mean(tot)),
            "median_total": round(statistics.median(tot)),
            "sum_input": sum(inp),
            "mean_input": round(statistics.mean(inp)),
            "median_input": round(statistics.median(inp)),
            "sum_output": sum(out),
            "mean_output": round(statistics.mean(out)),
            "median_output": round(statistics.median(out)),
            "total_ht": ht,
            "total_tc": tc,
            "total_cf": cf,
            "correction_rate": f"{cf/ht:.6f}" if ht > 0 else "0.000000",
            "mean_or": mean_or,
            "median_or": median_or,
            "drop_id": drop_id,
            "drop_tok": drop_tok,
        }

    agg_header = [
        "mode", "n_sessions", "sum_total_tokens", "mean_total_tokens",
        "median_total_tokens", "sum_input_tokens", "mean_input_tokens",
        "median_input_tokens", "sum_output_tokens", "mean_output_tokens",
        "median_output_tokens", "total_human_turns", "total_tool_calls",
        "total_correction_flags", "correction_rate",
        "mean_total_tokens_outlier_removed", "median_total_tokens_outlier_removed",
        "largest_session_id_dropped", "largest_session_total_tokens",
    ]

    with open(out_agg, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(agg_header)
        for m in MODES:
            a = agg[m]
            if a["n"] == 0:
                w.writerow([m, 0] + [""] * 17)
            else:
                w.writerow([
                    m, a["n"], a["sum_total"], a["mean_total"], a["median_total"],
                    a["sum_input"], a["mean_input"], a["median_input"],
                    a["sum_output"], a["mean_output"], a["median_output"],
                    a["total_ht"], a["total_tc"], a["total_cf"],
                    a["correction_rate"],
                    a["mean_or"], a["median_or"],
                    a["drop_id"], a["drop_tok"],
                ])

    rat_header = [
        "numerator_mode", "denominator_mode",
        "ratio_mean_total", "ratio_median_total", "ratio_mean_outlier_removed",
    ]

    def safe_ratio(num, den):
        if den == "" or den == 0:
            return ""
        return f"{num/den:.3f}"

    with open(out_rat, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(rat_header)
        for nm in MODES:
            for dm in MODES:
                if nm == dm:
                    continue
                an, ad = agg[nm], agg[dm]
                if an["n"] == 0:
                    rm, rmed, ror = "", "", ""
                elif ad["n"] == 0:
                    rm, rmed, ror = "", "", ""
                else:
                    rm = safe_ratio(an["mean_total"], ad["mean_total"])
                    rmed = safe_ratio(an["median_total"], ad["median_total"])
                    ror = safe_ratio(an["mean_or"] if an["mean_or"] != "" else None,
                                     ad["mean_or"] if ad["mean_or"] != "" else None)
                w.writerow([nm, dm, rm, rmed, ror])

    print(f"done: {out_agg}, {out_rat}")

if __name__ == "__main__":
    main()
