# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. Primitive named up front (reflex.1/reflex.2): the signing/verification kernel is OpenSSH's `SSHSIG` subsystem — `ssh-keygen -Y sign` / `ssh-keygen -Y verify`. No library, no invented format.

## 0. Pre-flight (loop.before, reflex.4)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds, node state. Don't proceed past a red line.
- Locate the canonical tree and deploy path for the site: `git -C ~/subtract.ing log --oneline -5`, `git -C ~/subtract.ing status`. Confirm how `subtract.ing/*.txt` is actually served (the canonical content lives under the signing key's domain — reflex.5 — not under a git host).
- Verify the last signature on the existing manifest before touching anything:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I <principal> -n file -s manifest.sig < manifest`
  If it fails or there's unsigned drift, surface it; the human decides sign/continue/abort. Agent does not paper over it.

## 1. Author the file (agent may do this)
- Write the file in the canonical working tree, e.g. `~/subtract.ing/<name>.txt`.
- Freeze the bytes. Signature covers exact content — no post-sign edits, no CRLF surprises, trailing newline decided now.
- Record `shasum -a 256 ~/subtract.ing/<name>.txt`.

## 2. Sign — HUMAN ONLY (boundary; authority.source = the human)
The agent prepares; it does not run this. Only the governor, holding the private key:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt
```
→ produces `~/subtract.ing/<name>.txt.sig` (armored `-----BEGIN SSH SIGNATURE-----` block).
- Namespace is `file`. It must be the exact string verifiers use; document it next to the file.
- The signing key is the same ed25519 identity already published in `allowed_signers`. If it isn't, that's a key-introduction problem to solve first, not a thing to improvise.

## 3. Publish to the signing key's domain (reflex.5: canonical = signing key's domain; git = mirror-only)
- Deploy **both** `<name>.txt` and `<name>.txt.sig` to `https://subtract.ing/<name>.txt` and `https://subtract.ing/<name>.txt.sig`.
- Confirm `https://subtract.ing/allowed_signers` is reachable and contains the principal→pubkey line:
  `<principal> namespaces="file" ssh-ed25519 AAAA...` — optionally with `valid-after=` so a verifier can place the key in time.
- Push the same files to any GitHub/other mirror **after**, and treat it as a mirror only. If the mirror and subtract.ing ever disagree, subtract.ing wins.

## 4. Update + re-sign the manifest (loop.after)
- Append to the manifest: path, `sha256`, `.sig` filename, ISO date, namespace.
- Human re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/manifest` → `manifest.sig`, and deploy that too.

## Which machine pushes
- **Rousseau (this node) pushes.** Governor's workstation + archive node; the signing happens at the key's home and the deploy to subtract.ing originates here.
- **Emile (m2mini) does not push.** Execution offload only — dispatch heavy build/render work there via `ssh m2mini "claude -p ..."`, but it never publishes canonical content and never holds the signing key.
- **Surface does not push.** Governor terminal (WSL2); it can drive Rousseau but isn't the publish origin.
- **acer1660ti does not push.** NAS/service endpoint, not formation — it can hold a warm backup copy of the published bytes, never the source of truth.

## How a stranger verifies, a year out
1. Fetch over HTTPS: `https://subtract.ing/<name>.txt`, `https://subtract.ing/<name>.txt.sig`, `https://subtract.ing/allowed_signers`.
2. Trust anchor: `allowed_signers` is served from subtract.ing itself — the signing key's own domain (reflex.5). Cross-check is optional: TLS chain, an archive.org snapshot of the `allowed_signers` URL, or DNS history.
3. Verify:
   ```
   ssh-keygen -Y verify -f allowed_signers -I <principal> -n file \
     -s <name>.txt.sig < <name>.txt
   ```
   Expect: `Good "file" signature for <principal> with ED25519 key SHA256:<fp>`.
4. Optional, stronger: fetch `manifest` + `manifest.sig`, verify the same way, and check `shasum -a 256 <name>.txt` matches the manifest entry — ties the file into the signed archive history, not just a lone signature.
5. Why it survives a year: an ed25519 SSHSIG doesn't expire; verification depends only on (a) the file bytes, (b) the `.sig` bytes, (c) the pubkey line still being the one published under subtract.ing. If the key later rotates, `valid-after`/`valid-before` in `allowed_signers` lets the verifier confirm it was valid at signing time. Nothing here needs the agent — the signature, not the agent's say-so, carries the authority.

## Authority boundaries in one line
Agent: audit, draft the file, compute hashes, stage, deploy, update manifest text. Human: every `ssh-keygen -Y sign` invocation. Unsigned = suggestion only; the published `.sig` is the only thing that makes the authorship claim real.
