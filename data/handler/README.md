# Handler methodology artifacts

Artifacts backing `subtract.ing/variance-lab-handler-methodology.txt` (2026-04-18).

What survived:
- `handler-dispatch-spec.txt` — 4,663-char prompt dispatched verbatim to five implementers.
- `handler-dispatch-rubric.txt` — pre-committed evaluation rubric.

What did not survive (ephemeral `/tmp`, not preserved across the session boundary):
- `impl-opus47.sh`, `impl-sonnet45.sh`, `impl-sonnet46.sh`, `impl-sonnet46low.sh`, `impl-qwen3coder.sh` — the five implementations.
- `ship-decision.txt` — deliberative-pass prompt.
- `vote-*.txt` — 8 voter responses.

The methodology document's Limitations section flags `/tmp` ephemerality explicitly as a pre-commitment weakness. A replicator can re-dispatch the spec under a fresh rubric-commit-then-sign protocol.
