## Plan — publish a verifiable `.txt` to subtract.ing

### 0. Pre-flight (loop.before — before the agent acts)
On **Rousseau** (authoring/archive node):
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds.
- In `~/subtract.ing/`: `git log --oneline -5`, `git status`, and `ssh-keygen -Y verify` against the current signed manifest to confirm the working tree matches the last signed state. Surface any unsigned drift to the governor. Do not proceed past unresolved drift.

### 1. Draft (agent prepares — Rousseau)
- Write the file in the canonical working tree: `~/subtract.ing/<name>.txt`. Final filename is the one that will be served at `https://subtract.ing/<name>.txt`.
- Record the content hash for the manifest: `sha256sum ~/subtract.ing/<name>.txt`.
- The agent stops here. It does **not** hold or invoke the signing key. (`boundary`: the agent prepares, the human signs.)

### 2. Sign (human gate — governor, on the node holding the private key)
Reflex.2 says use the SSH primitive, not an invented format. Detached SSH signature, namespace `file`:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt
# -> produces ~/subtract.ing/<name>.txt.sig
```
This is the one step that is a human gate (new signing). Identity in the allowed-signers file is `jnous`.

### 3. Update + sign the manifest (loop.after.1 / loop.after.2)
- Append `<name>.txt` and its SHA-256 to `~/subtract.ing/MANIFEST` (or the existing manifest file).
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST` → `MANIFEST.sig`.
- Confirm: `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST`.

### 4. Ensure the key binding is publishable
For a stranger to verify, the public key→identity binding must be reachable and anchored to the **signing key's domain** (reflex.5), not just a git host:
- `allowed_signers` (line: `jnous ssh-ed25519 AAAA… `) must be served at `https://subtract.ing/allowed_signers` — TLS on subtract.ing is the trust root for the binding.
- Belt-and-suspenders anchor: publish the key fingerprint as a DNS TXT record on the subtract.ing zone (`_signers.subtract.ing`), so the binding rests on DNSSEC/registrar control of the same domain. This is what makes the claim survive a year — the verifier doesn't need to trust GitHub or me, only the domain.

### 5. Publish — machine boundaries
- **Rousseau does NOT push to the public origin.** It is the archive/authoring/staging node. It pushes nothing externally-visible.
- The push to the public web origin (and the GitHub mirror) is run from the governor's execution terminal — **Surface** today (pre-2026-05-22 reorg). Warn the governor before the push; it's an outward-facing mutation.
  - Canonical: `rsync -a ~/subtract.ing/<name>.txt <name>.txt.sig MANIFEST MANIFEST.sig allowed_signers <origin>:/var/www/subtract.ing/` (or whatever the established deploy path is).
  - Mirror only (reflex.5 — git hosts are mirror-only, not authoritative): `git add … && git commit && git push origin main` to the GitHub repo.
- Verify the live copy after deploy: `curl -fsSL https://subtract.ing/<name>.txt | sha256sum` matches step 1; `curl -fsSL https://subtract.ing/<name>.txt.sig` is non-empty.

### 6. Archive anchor (durability for "a year from now")
Back on Rousseau, fold the new file + sigs into the cold tiers so the artifact survives origin loss: SDXC air-gap manifest refresh and FROZEN/`~/human/` snapshot per the existing `discover.sh`/SDXC-refresh procedure. The detached `.sig` is self-contained — verification later needs only the three files, not a live subtract.ing.

### How a stranger verifies (a year later)
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
Expected: `Good "file" signature for jnous with ED25519 key SHA256:<fp>`.

Then anchor the key itself: confirm `<fp>` matches the TXT record (`dig +short TXT _signers.subtract.ing`) and the signed `MANIFEST`. Residual trust assumption, stated plainly: the identity↔key binding rests on whoever controls the subtract.ing domain (TLS + DNS). That's the irreducible root — everything else (git, mirrors, my say-so) is non-authoritative.

### Authority boundaries summary
- **Agent (Claude/Rousseau):** drafts text, computes hashes, stages files, updates the manifest draft, writes/runs `ssh-keygen -Y verify`, prepares the deploy command. Never touches the private key.
- **Human (governor):** runs `ssh-keygen -Y sign` for the file and the manifest. Only new signing is the gate.
- **Rousseau:** authors, signs-staging-verifies, archives. No public push.
- **Surface (current execution terminal):** pushes canonical copy to the subtract.ing origin and to the GitHub mirror, after a heads-up.
- **GitHub:** receives the push, is explicitly a mirror — not where authorship is proven.

Note on tool choice: this is `ssh-keygen -Y`, not `gpg` and not any signing library — the kernel primitive already in the formation, keyed to `jnous` (reflex.1, fail.additive).
