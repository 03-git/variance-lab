# Adversarial Review of Interaction-Mode-Variance Rerun Draft

Reviewed: `rerun-draft.md`  
Rubric: `rubric.md` @ commit `49d86f7`  
Data: `aggregate-singlemodel.tsv`, `ratios-singlemodel.tsv`, `sessions-dedup.tsv`  
Date: 2026-04-19

---

## 1. Factual errors

**Line 64 token-share claim:**

Draft states: "~12.2M of ~13.7M total single-model qualifying tokens (~89%)"

TSV values (sum of `sum_total_tokens` from `aggregate-singlemodel.tsv`):
- Pipe: 296,054
- Governor: 29,768
- Collaborator: 964,975
- Passenger: 12,197,814
- **Total: 13,488,611**

Passenger share: 12,197,814 / 13,488,611 = **90.4%**, not 89%.

Total should be stated as **~13.5M**, not ~13.7M.

**Other numeric claims verified (sample of 10+):**

- 501 single-model qualifying sessions: ✓ (grep count on `sessions-dedup.tsv` col 14=0, col 15=1)
- 14 mixed-model sessions (13 passenger, 1 collaborator): ✓ (grep count on col 14=1, manual mode count)
- Per-mode N values (394, 9, 28, 70): ✓ (match `aggregate-singlemodel.tsv` col 2)
- Per-mode means (751, 3308, 34463, 174254): ✓ (match col 4)
- Per-mode medians (136, 3217, 15035, 69639): ✓ (match col 5)
- Passenger/governor multipliers (52.7×, 21.6×, 50.4×): ✓ (match `ratios-singlemodel.tsv` row 12: 52.677, 21.647, 50.380)
- Passenger/pipe multipliers (232×, 512×, 241×): ✓ (match row 11: 232.029, 512.051, 240.881)
- Human turns (394, 21, 238, 5363): ✓ (match col 12)
- Tool calls (93, 67, 862, 14823): ✓ (match col 13)
- Correction rates (0.919, 0.238, 0.273, 0.274): ✓ (match col 15, appropriately rounded to 3 decimals)
- Methodology-contamination tokens (67,343): ✓ (not independently verified from TSV but internally consistent: 67343/296054=22.74%, 67343/13488611=0.499%)

---

## 2. Framing drift

**Line 16-17 hedge complexity:** "The original finding's 41× headline (N=88, 2026-03-30) does not reproduce by coincidence of number; it is re-observed as a same-direction, different-magnitude ordering on a larger, differently-composed corpus."

"Does not reproduce by coincidence of number" is semantically unclear. The sentence establishes same-direction, different-magnitude — this is factual — but the negation framing ("does not reproduce") frontloads the difference before stating the similarity. A replicator scanning for reproduction success/failure could misparse this as "failed to reproduce" rather than "reproduced the direction but not the magnitude."

Not an overclaim, but unnecessarily complex framing for a simple statement: "The ordering reproduces; the magnitude differs (52.7× vs 41×)."

**Line 48 ~5× governor median claim:** Draft states "~5× on medians (N=9 governor makes these estimates wide)."

TSV: `ratios-singlemodel.tsv` row 9 (collaborator/governor) shows `ratio_median_total=4.674`.

Rounding 4.674 to "~5×" is reasonable, but the tilde hides a 7% gap (4.674 vs 5.0). Not a factual error, but the hedge is doing work — "4.7×" would be more precise without cost. The parenthetical about N=9 appropriately signals uncertainty.

**No causal overclaims detected.** Mechanism section (lines 68-71) appropriately labels correlation as correlation and warns against inferring per-turn cost from per-session ratios.

**No mean-vs-median privilege detected.** Both are reported throughout.

**No operator-behavior smuggling detected.** Line 65-66 explicitly warns: "Mode-share differences below should be read as properties of the two corpora, not as time-series evidence that the operator's behavior changed."

---

## 3. Missing limitations

**All rubric-specified confounds are disclosed:**

- Mixed-model exclusion: disclosed (line 50-52, 14 sessions).
- Methodology-experiment contamination: disclosed (line 82-84, 27 pipe sessions from `-tmp` directories, quantified impact on pipe mean).
- Subagent dedup approach: disclosed (line 85-86, path filter `/subagents/`, 10-session spot-check, parent presence confirmed in sample).
- Correction-keyword false-positive mechanism: disclosed (line 89-90, pipe rate 0.919 measures "fraction of pipe sessions whose single prompt contains at least one keyword substring" not retroactive corrections).
- Mode-vs-tokens tautology: disclosed (line 68-71, mechanical turn/token overlap, no turn-normalized metric reported).

**Additional confounds disclosed beyond rubric minimum:**

- N=9 governor sensitivity (line 81).
- session_id format deviation (line 91-92).
- Extractor dispatch prompt deviation (line 93-94, corrected at aggregation).
- Single operator / single node / single window (line 96).
- No cross-lineage extractor (line 97-98).
- Filesystem-timestamped pre-commitment rather than hash-signed (line 99).

**No missing limitations found.** The Confounds section is comprehensive. A replicator has sufficient detail to identify where the implementation deviates from the rubric or where the rubric's design creates interpretive constraints.

---

## 4. What to cut

**Line 16-17:** The phrase "does not reproduce by coincidence of number" does not serve the claim. The rest of the sentence ("same-direction, different-magnitude ordering") is sufficient. Cut the negation clause.

**Line 99-100 (pre-commitment signing):** "Pre-commitment is filesystem-timestamped and git-committed, not hash-signed." This confound is disclosed, but its relevance is marginal — git commit hashes *are* cryptographic hashes, and the branch/commit are externally observable. The distinction between "git commit" and "hash-signed" as pre-commitment mechanisms is not load-bearing for the finding's replicability. If the concern is about post-hoc tampering, the commit is already in the public branch history. Consider cutting unless there's a specific threat model this addresses.

**No other sections flagged for cutting.** The Mechanism, Confounds, and Comparison sections are dense but justified — each serves either the rubric's aggregation requirements or replicator needs. The correction-rate confound (line 89-90) is verbose but necessary given the counterintuitive 0.919 pipe rate.
