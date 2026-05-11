# Plan — publish a verifiable `.txt` to subtract.ing

Not executing. This is the procedure I'd follow.

## 0. Ground truth (before anything)
- `bash ~/scripts/audit-health.sh` — confirm DNS for `subtract.ing`, drive state, creds, node state.
- Identify the signing key in `~/.ssh/` designated for the subtract.ing domain (Ed25519). Confirm an `allowed_signers` file is already published at the domain (e.g. `https://subtract.ing/allowed_signers`).
- reflex.2: the format is `ssh-keygen -Y sign` / `-Y verify`. That's the kernel primitive — don't invent a wrapper or a bespoke signature scheme.

## 1. Author the file (Rousseau, agent)
- Write the file inside the canonical working tree under the subtract.ing repo (e.g. `~/subtract.ing/.../<name>.txt`), not `/tmp`.
- Content is final before signing. No post-signature mutation — a single trailing newline change breaks the sig.

## 2. Sign — governor, not agent (authority boundary)
- I prepare the exact command; the **governor runs it**. The agent prepares, the human signs (`boundary`, `authority.source`). I cannot sign and cannot self-authorize — asserting "it's published and valid" without a live read is itself an action (reflex.4).
- Command the governor runs:
  `ssh-keygen -Y sign -f ~/.ssh/<subtract_signing_key> -n file <name>.txt`
  → produces `<name>.txt.sig` (armored SSH signature). Namespace `-n file` (or the project's established namespace) — must match what the verifier/allowed_signers expects; keep it consistent.

## 3. Publish — which machine pushes
- Canonical target = the host serving `https://subtract.ing` (the signing key's domain). Per reflex.5 that host's copy is authoritative.
- **Rousseau pushes** (node 01, governor's workstation, holds the repo): `git push` to the deploy remote, or `rsync -avz <name>.txt <name>.txt.sig <webhost>:/var/www/subtract.ing/` — whichever the site's deploy uses. Confirm the alias from `~/.ssh/config` first.
- **Emile does not push** — reasoning/execution offload only, not a publish authority.
- **acer does not push canonical** — it's NAS/service infra + warm backup; a copy there is a mirror, not the source.
- **Surface does not push** — governor terminal.
- **Git host (GitHub etc.) is mirror-only** — reflex.5. Pushing there does not make it authoritative.
- After deploy, live read-back (reflex.4):
  `curl -fsS https://subtract.ing/<name>.txt | shasum -a 256` vs local hash; `curl -fsS https://subtract.ing/<name>.txt.sig` exists and matches.

## 4. Manifest (loop.after)
- Add `<name>.txt` + its SHA-256 to the session manifest; governor re-signs the manifest with `ssh-keygen -Y sign`; publish the manifest alongside. This is the "after the session: update manifest, sign" step.

## How a stranger verifies, a year later
1. `curl -O https://subtract.ing/<name>.txt` and `curl -O https://subtract.ing/<name>.txt.sig`
2. `curl -O https://subtract.ing/allowed_signers` — the identity→pubkey map, served from the signing domain itself. The trust root is: TLS on subtract.ing + the domain being the declared canonical authority (governance.conf.universal, reflex.5).
3. `ssh-keygen -Y verify -f allowed_signers -I <identity@subtract.ing> -n file -s <name>.txt.sig < <name>.txt`
   → exit 0 + `Good "file" signature` means the holder of the subtract.ing signing key authored that exact byte sequence.
4. Corroboration (not authority): the same key signs the manifest containing the file's hash; the git mirror history shows the same blob.

### Longevity notes
- SSH signatures don't expire. Verification in a year holds as long as the `allowed_signers` entry stays published and the key isn't silently rotated.
- If the key is rotated, keep the retired pubkey in `allowed_signers` with a `valid-before="<date>"` option so old signatures still verify.

## Authority boundaries, summarized
- **Agent (Rousseau):** authors the file, drafts commands, runs live read-back, drafts the manifest update, executes the push. Cannot sign; cannot declare it valid without the live read.
- **Governor (human):** runs `ssh-keygen -Y sign`, picks identity/namespace, approves the push. The signature proves it was them.
- **Rousseau:** the only node that pushes canonical.
- **Emile / acer / Surface:** never push canonical; acer may carry a backup mirror.
- **Git host:** mirror-only.
