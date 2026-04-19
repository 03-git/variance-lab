# Finding 6 data — Interaction-Mode-Variance Rerun

Artifacts backing `subtract.ing/variance-lab.txt` Finding 6 and `findings/interaction-mode-variance-rerun.md` (on branch `rerun/finding-3`).

## Pre-commitment

- Rubric: `rubric.md` (also at `findings/interaction-mode-variance-rubric.md` on branch `rerun/finding-3`)
- Rubric commit: `49d86f7`
- Rubric sha256: `4223396958c219045c928c77951a30d3aae86ddacc56c08bc7300891ce7bb379`

## Scripts

- `extract.py` — walks corpus of Claude Code JSONL session logs, emits per-session TSV. Python stdlib only.
- `aggregate.py` — reads per-session TSV, emits per-mode aggregate + pairwise ratios. Python stdlib only.

## Invocation

    python3 extract.py <corpus_root> <output_tsv>
    python3 aggregate.py <sessions_tsv> <aggregate_tsv> <ratios_tsv>

## Numeric outputs

- `sessions-dedup.tsv` — per-session rows after `/subagents/` path filter (520 rows, one row per qualifying session plus 5 non-qualifying rows with `qualifying=0` for auditability).
- `aggregate-singlemodel.tsv` — per-mode aggregate with mixed-model sessions excluded (501 qualifying).
- `ratios-singlemodel.tsv` — pairwise multiplier ratios (mean, median, outlier-removed mean).

## Reviews

Two-pass adversarial review, six Claude voters each pass, zero arithmetic errors on pass two.

- `reviews-p1/` — first pass across rousseau/emile × opus-4-7 / sonnet-4-5 / sonnet-4-6 × high/low.
- `reviews-p2/` — second pass against the post-p1-revision draft.

Voter map same as Finding 5 (see `../finding-5/README.md`).

## Known issue (not affecting this output)

`aggregate.py`'s `safe_ratio` function will raise if a mode reaches N=1 (outlier-removed pool of size zero). This does not affect the Finding 6 output (smallest mode was governor N=9). Document-only; fix required before any future rerun where a mode could hit N≤1.
