## Plan — publish a verifiable `.txt` to subtract.ing

### 0. Ground truth
- `bash ~/scripts/audit-health.sh` — confirm DNS, creds, drives, node state before touching anything (don't assume from this conversation; reflex.4).

### 1. Pre-act loop (loop.before)
- Verify the current canonical manifest's signature before adding to it:
  `ssh-keygen -Y verify -f allowed_signers -I jnous -n subtract.ing -s MANIFEST.sig < MANIFEST`
  Expect `Good "subtract.ing" signature for jnous ...`. If it fails or the tree shows unsigned drift, stop and surface it — the human decides (sign / continue / abort).
- reflex.2 check: the format is plain SSH signatures — `ssh-keygen -Y sign` produces what `ssh-keygen -Y verify` consumes. No new scheme invented.

### 2. Draft (agent prepares — unsigned, no authority yet)
- Author the file on **Rousseau** (canonical home for `~/human/` and the workstation): `~/subtract.ing/<path>/newfile.txt`.
- Compute `sha256 newfile.txt`; stage the new MANIFEST line (path, sha256, sig filename). Do **not** present any of this as authoritative — it's a suggestion until signed (authority.unsigned).

### 3. Sign (human gate — the agent does not cross this)
Only *new* signing is a human gate (pushing already-signed bytes later is just infra). `ssh-keygen -Y sign` will pop a passphrase dialog on macOS — warn the governor first, then he runs, on Rousseau:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n subtract.ing ~/subtract.ing/<path>/newfile.txt
# -> newfile.txt.sig
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n subtract.ing ~/subtract.ing/MANIFEST
# -> MANIFEST.sig   (re-sign the manifest now that it includes the new file)
```
Namespace `-n subtract.ing` must be identical at sign and verify time — keep it constant across the repo.

### 4. Trust anchor
- Ensure `allowed_signers` is published at a stable subtract.ing URL and contains the signer line:
  `jnous namespaces="subtract.ing" ssh-ed25519 AAAA...` (the public half of `~/.ssh/id_ed25519`).
- This file is the verifier's root of trust, so it must live under the **signing key's own domain** (reflex.5), not be sourced from a git host.

### 5. Publish (infra — agent executes, reversible)
- From the node that serves the subtract.ing web origin (the canonical/signing domain — Rousseau in the current formation), deploy: `newfile.txt`, `newfile.txt.sig`, updated `MANIFEST`, `MANIFEST.sig`, and `allowed_signers` if changed. `rsync`/`scp` to the deploy root, or `git push` to whatever drives the site build.
- **GitHub (or any git host) push is mirror-only** (reflex.5). It may carry copies, but the commit/README should state that canonical + authoritative `allowed_signers` is `https://subtract.ing/...`. A verifier pointed only at the mirror has not verified the claim.
- Emile and Media/acer do **not** push canonical content; acer is warm-backup tier, never an authority source.

### 6. Post-act loop (loop.after)
- Manifest updated ✓, signed ✓. Drop a session note in `~/human/sessions/`.

### How a stranger verifies, a year later
```
curl -O https://subtract.ing/<path>/newfile.txt
curl -O https://subtract.ing/<path>/newfile.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n subtract.ing -s newfile.txt.sig < newfile.txt
```
Expect: `Good "subtract.ing" signature for jnous with ED25519 key SHA256:...`.
Then corroborate provenance: `sha256 newfile.txt` must match the entry in `MANIFEST`, and
`ssh-keygen -Y verify -f allowed_signers -I jnous -n subtract.ing -s MANIFEST.sig < MANIFEST` must also pass — so the file is bound into the signed canonical set, not just individually signed. (`ssh-keygen -Y check-novalidate -n subtract.ing -s newfile.txt.sig < newfile.txt` lets them inspect the sig before trusting `allowed_signers`.)

### Authority boundaries, summarized
- Agent: drafts the file, hashes it, stages the manifest line, writes the verify command, and later pushes the already-signed bytes to the origin and mirrors.
- Human: holds `~/.ssh/id_ed25519` (identity `jnous`) and runs every `ssh-keygen -Y sign`. The signature — not the agent, not the git host — is what proves authorship (boundary; authority.source = the human).
- Canonical = subtract.ing (signing key's domain). Git hosts = mirror-only. Rousseau drafts/signs/serves; Emile and acer do not publish canonical.
