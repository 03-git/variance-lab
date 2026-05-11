# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. Steps, tools, boundaries below.

## 0. Pre-flight (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, credentials, node state. Don't touch the canonical tree until this is clean.
- In the canonical working tree (`~/subtract.ing/`, the same tree whose `runtime/...` paths are authoritative on every node): `git -C ~/subtract.ing log --oneline -5`, `git -C ~/subtract.ing status`. Confirm HEAD matches what you think it is; if the tree is newer than working memory, re-read before adding anything.
- Verify the last signature on whatever manifest/index already governs published files (`ssh-keygen -Y verify ...` on its `.sig`) before mutating anything. Surface any unsigned drift to the governor. Human decides: sign / continue / abort. (loop.before.1–3)

## 1. Agent prepares the file
- Write `~/subtract.ing/<name>.txt` in the canonical tree on **rousseau** (node 01). This is the signing key's domain — load-bearing content is canonical here, not on any git host (reflex.5).
- The agent does only this. It does not sign. (boundary: the agent prepares, the human signs.)

## 2. Human gate: signing (reflex.2 — use the SSH signature primitive, don't invent a format)
- Governor runs, on rousseau, with the `jnous` signing key:
  ```
  ssh-keygen -Y sign -f ~/.ssh/<jnous_key> -n file ~/subtract.ing/<name>.txt
  ```
  → produces `~/subtract.ing/<name>.txt.sig` (SSH signature, namespace `file`).
- This is the only step that is a true human gate. Warn the governor first if the key touch/passphrase will pop a prompt. (feedback_human_gate_scope, feedback_warn_human_gates)
- Confirm immediately with a live read, not memory:
  ```
  ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt
  ```
  Must exit 0. (reflex.4 — assertion-that-blocks counts as an action, so verify live.)

## 3. Publish (infra — agent executes, no gate; pushing already-signed artifacts is not a human gate)
- Deploy `<name>.txt` **and** `<name>.txt.sig` to the subtract.ing web root via whatever the audit/repo state shows is the deploy path (commit + push to the deploy remote, or rsync to the web host — confirm from `git remote -v` / deploy script, don't assume).
- Ensure `allowed_signers` is already published at a stable URL under `subtract.ing` and contains the line `jnous <ssh-ed25519 pubkey>`. If not, that file is the real trust anchor and must ship under the signing domain over TLS — add it the same way (it itself can be covered by the signed manifest).
- Update the canonical manifest/index to list `<name>.txt` + its hash; re-sign the manifest with the `jnous` key (loop.after.1–2). Push that too.

### Which machine pushes
- **rousseau (01)** authors, holds the signing key, signs, and runs the deploy. It is the publisher.
- **emile (m2mini)** — execution offload only (heavy verify/build via `ssh m2mini "claude -p ..."`). Does **not** push canonical content.
- **acer / "Media"** — not formation, service + warm-backup tier only. Does **not** push canonical; may hold a mirror copy at most.
- **surface** — governor terminal, pull-only, mid-decommission. Does **not** push canonical.
- Any GitHub/git remote is **mirror-only** (reflex.5) — fine to push for redundancy, never cited as the source of truth.

## 4. How a stranger verifies it a year later
On any machine with OpenSSH:
```
curl -fsSO https://subtract.ing/<name>.txt
curl -fsSO https://subtract.ing/<name>.txt.sig
curl -fsSO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
- Exit status 0 + `Good "file" signature for jnous` ⇒ the file is byte-for-byte what the `jnous` key signed.
- Trust chain: the verifier trusts `allowed_signers` because it is served under `subtract.ing` over TLS — the signing key's own domain — not because a git host says so. The signature covers the file content; the manifest (also signed) covers the fact that this filename is a sanctioned canonical artifact.
- Nothing here expires: SSH signatures have no validity window, so "a year from now" is the same check as today, as long as the `jnous` entry in `allowed_signers` is unchanged (or the verifier pins the pubkey).

## Authority boundaries in force
- `authority.unsigned` → the agent's draft in step 1 is a suggestion until step 2; act on it only after `ssh-keygen -Y verify` passes (`authority.signed`).
- `boundary` → agent prepares (1) and ships already-signed bytes (3); governor alone runs `ssh-keygen -Y sign` (2).
- `reflex.5` → canonical = `subtract.ing`; git is mirror-only.
- `reflex.2` / `reflex.4` → reuse `ssh-keygen -Y`; verify with a live read before treating publication as done.
- `loop.after` → manifest updated and re-signed, or the session isn't finished.
