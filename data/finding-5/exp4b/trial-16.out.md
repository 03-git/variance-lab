# Plan: publish a verifiable `.txt` to subtract.ing

Not executing — plan only.

## 0. Pre-flight (loop.before — runs before any write or push)
- On **rousseau**, in the canonical tree `~/subtract.ing/`:
  - `git log --oneline -5` , `git status` , `wc -l` on the manifest — state what you observe.
  - Verify the *current* signature with a live read (reflex.4): 
    `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST`
  - Surface any unsigned drift (files present but not in the signed manifest). Stop. **Human decides: sign / continue / abort.** The agent does not clear drift on its own.

## 1. Reflex check before choosing a mechanism (reflex.2)
- The verification format is **already a kernel-adjacent primitive**: OpenSSH signatures (`ssh-keygen -Y sign` / `-Y verify`, `-n file` namespace, `allowed_signers` format). Do **not** invent a manifest signing scheme or reach for a library (minisign, gpg, sigstore…) — `ssh-keygen -Y` already verifies the format a stranger will use. This is the same primitive already in use for `governance.conf.universal` and the hosuni `.sig` files.

## 2. Author the file — on rousseau only
- Rousseau is the drafting node and holds the canonical `~/subtract.ing/` tree. Write the new file there, e.g. `~/subtract.ing/<name>.txt`, with `Write`/`Edit`.
- reflex.5: load-bearing content is canonical **under the signing key's domain** = `subtract.ing`. A GitHub or other git mirror is mirror-only and is *not* where the authorship claim lives.

## 3. Update the manifest — agent prepares (boundary: "the agent prepares, the human signs")
- Append the new file's digest to the manifest:
  `cd ~/subtract.ing && sha256sum <name>.txt >> MANIFEST` (match the existing manifest's format/sort).
- At this point the file + manifest entry are **unsigned → suggestion only** (authority.unsigned). Nothing downstream may act on it yet.

## 4. The human gate — the governor signs (authority.source = the human)
This is the one step no machine and no agent does autonomously (feedback: only *new* signing is a human gate). The governor, with the private key that never leaves their control, runs on rousseau:
- Sign the file directly (what a stranger checks):
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file <name>.txt` → produces `<name>.txt.sig`
- Re-sign the manifest (loop.after.2):
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file MANIFEST` → refreshes `MANIFEST.sig`
- Confirm locally: `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt` → must print `Good "file" signature`.

## 5. Ensure the verifier's trust anchor is on the domain
- The binding "this key == subtract.ing's owner" comes from the key being published **under the domain over TLS**. Make sure `allowed_signers` (identity `jnous` → the ed25519 public key) is itself served at a stable path, e.g. `https://subtract.ing/allowed_signers`. If it isn't already, add it in the same change. (Optional hardening: cross-post the key fingerprint somewhere out-of-band so the claim survives a domain lapse.)

## 6. Publish — which machine pushes
- **Rousseau pushes.** It owns the canonical `~/subtract.ing/` tree; the deploy goes from rousseau to the origin host that serves `subtract.ing` (rsync/scp/`git push` to that host — whatever the existing deploy path is). Pushing an *already-signed* artifact across nodes is plain infra, not a gate.
- **Surface does not push** — it's a pull-mirror of canonical (`~/human/` model), and it's being decommissioned 2026-05-22 anyway.
- **Emile (m2mini) does not push** — execution-offload target, not a publisher.
- **Acer / "Media" does not push** — it's the warm-backup tier and explicitly *not* formation; it never originates canonical content.
- A git mirror (if any) may also receive the push, but it is mirror-only (reflex.5) and is not the authorship anchor.

## 7. Close the loop (loop.after)
- `git add <name>.txt <name>.txt.sig MANIFEST MANIFEST.sig allowed_signers && git commit` in `~/subtract.ing/`; manifest is updated (loop.after.1) and signed (loop.after.2). Note the new `git log` HEAD.

---

## How a stranger verifies, a year from now
```
curl -fO https://subtract.ing/<name>.txt
curl -fO https://subtract.ing/<name>.txt.sig
curl -fO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
- Exit 0 + `Good "file" signature` ⇒ the file is exactly what the holder of the `jnous` key signed, and that key is the one published under `subtract.ing`. Authorship confirmed.
- Optional corroboration: fetch `MANIFEST` + `MANIFEST.sig`, verify the same way, then `sha256sum -c` the line for `<name>.txt`.
- Failure mode to call out to the verifier: the `-n file` namespace must match between sign and verify; and the trust is only as good as the domain/TLS control plus whatever out-of-band fingerprint was published.

## Authority boundaries in force
- **authority.unsigned**: the agent's drafted file + manifest line are a suggestion until step 4 — nothing acts on them before that.
- **boundary / "agent prepares, human signs"**: agent does steps 0–3 and 6–7; the `ssh-keygen -Y sign` in step 4 is the governor's, with a key the agent never touches.
- **Human-gate scope**: *only* the new signing is gated; verifying the prior signature (step 0) and pushing the signed result (step 6) are things the agent just does.
- **reflex.5**: canonical home is `subtract.ing` (the signing key's domain); git hosts are mirror-only.
- **reflex.4 / loop.before**: verify the last signature with a live read before publishing; surface drift; human decides.
