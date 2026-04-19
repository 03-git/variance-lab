# variance-lab / data

Reproducibility layer for findings published under `subtract.ing/variance-lab.txt` and `subtract.ing/variance-lab-handler-methodology.txt`.

Each subdirectory holds the artifacts backing a specific finding: specs, rubrics, harness scripts, run logs, review outputs, and aggregated numeric outputs (TSVs). Artifacts were ephemeral (`/tmp`) in the original runs; what survived is preserved here.

## Layout

    handler/            — handler-methodology (2026-04-18): spec + rubric (implementations, votes, and ship-decision did not survive)
    finding-5/          — governance binding, delivery path, targeted patch (2026-04-19): exp1-4 specs/harnesses/logs + exp5 editorial audit (8 voters, synthesis, ship decisions)
    finding-6-rerun/    — interaction-mode rerun under pre-committed rubric (2026-04-19): extractor, aggregator, rubric, TSVs, two-pass adversarial review (12 voter outputs)

## What's published vs what's not

Per the parent methodology's Limitations sections, `/tmp`-only artifacts did not cryptographically pre-commit. This directory is the best-effort preservation layer. Files present: reproducible. Files named in parent documents but not present here: did not survive.

## Pre-committed rubric hashes

For rubrics that were git-committed at pre-commitment time (as opposed to `/tmp`-only):

- Finding 6 rerun rubric: commit `49d86f7` on branch `rerun/finding-3`, content sha256 `4223396958c219045c928c77951a30d3aae86ddacc56c08bc7300891ce7bb379`.

## Verifying signatures on the canonical claim layer

    curl -sO https://subtract.ing/llms.txt
    curl -sO https://subtract.ing/llms.txt.sig
    curl -sO https://subtract.ing/authorized_signers
    ssh-keygen -Y verify -f authorized_signers -I hodori@subtract.ing -n subtract.ing -s llms.txt.sig < llms.txt
