# Plan: publish a verifiable `.txt` to subtract.ing

## 0. Pre-flight (the loop, before acting)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, creds, drives, node state. Don't proceed past a red line.
- Verify the *current* canonical state before touching it: `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I <signer> -n file -s <existing-manifest>.sig < <existing-manifest>`. If it doesn't print `Good "file" signature...`, stop and surface the drift — don't add a file on top of an unverified base (reflex.4, loop.before.1–2).
- Confirm `~/.ssh/allowed_signers` exists and contains the governor's principal → ed25519 pubkey line. That file (and its published copy) is the trust anchor.

## 1. Draft — agent does this (reversible, no gate)
- Write the file into the subtract.ing staging tree on **rousseau** (canonical `~/human/` node, governor's workstation): `~/human/.../newfile.txt`. Use the `Write` tool. Staging writes are reversible → execute without asking.
- Record `sha256sum newfile.txt` for the manifest update.

## 2. Sign — human gate, agent only prepares
The agent does **not** hold or use the signing key (boundary: the agent prepares, the human signs; loop.before.3). The agent hands the governor the exact command and warns that it may prompt for a key passphrase (popup → warn first):

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/human/.../newfile.txt
```

Produces `newfile.txt.sig` — an armored `SSHSIG` block. Namespace is `file` (must match at verify time). This is "new signing" = the one real human gate. The governor runs it; the agent waits.

## 3. Verify locally before publishing (reflex.4)
```
ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I <signer> -n file \
  -s ~/human/.../newfile.txt.sig < ~/human/.../newfile.txt
```
Must print `Good "file" signature for <signer> with ED25519 key SHA256:…`. If not → abort, don't publish.

## 4. Publish — agent executes (already-signed artifact = infra, not a gate)
- **Push from rousseau only.** Rousseau is the canonical node and governor's workstation. Emile (reasoning offload / scripts pull-mirror), Media/acer1660ti (warm backup + Jellyfin/*arr service box, explicitly *not* formation-canonical), and Surface (governor terminal, pull-only) do **not** push canonical web content.
- Canonical target is the host that serves `subtract.ing` over TLS — push there, not to any git host. Git mirrors (GitHub etc.) are mirror-only and pushing to them is not publishing (reflex.5).
  ```
  rsync -av --checksum ~/human/.../newfile.txt ~/human/.../newfile.txt.sig \
    <subtract-host>:<web-root>/
  ```
  (or `scp` the two files over the configured ssh alias).
- Ensure `allowed_signers` is reachable under the same domain (`https://subtract.ing/allowed_signers`) so a stranger can fetch the trust anchor from the signing key's own domain. If the key may rotate within the year, give the allowed_signers line a `valid-after=YYYYMMDD` (and retain superseded keys) so old signatures still verify.
- Update the manifest: append `newfile.txt` + its sha256 (loop.after.1), then the governor re-signs the manifest with the same `ssh-keygen -Y sign` (loop.after.2) and that `.sig` is pushed too.

## 5. How a stranger verifies it a year later
```
curl -O https://subtract.ing/newfile.txt
curl -O https://subtract.ing/newfile.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <signer> -n file \
  -s newfile.txt.sig < newfile.txt
```
Expect `Good "file" signature for <signer> with ED25519 key SHA256:…`.

Chain of trust the verifier is relying on:
- **TLS on subtract.ing** proves the bytes (file, sig, allowed_signers) came from the domain.
- **allowed_signers served under that domain** binds the principal name to a specific ed25519 public key (canonical under the signing key's domain — reflex.5).
- **The SSHSIG** proves whoever holds that private key signed exactly these bytes under namespace `file`.
- SSHSIG verification is fully offline — no CA, no timestamp expiry inside the signature — so it still verifies in a year as long as the key isn't rotated out of `allowed_signers` without a validity window. A cautious verifier also cross-checks the `SHA256:` key fingerprint against any independently pinned copy (e.g. the key referenced from the governance.conf domain, or one obtained out of band).

## Authority boundaries, summarized
- Agent: drafts the file, computes hashes, drafts the sign command, runs `-Y verify`, pushes the *signed* artifact, updates manifest text. Never signs, never holds the key.
- Human (governor): runs `ssh-keygen -Y sign` for both the file and the updated manifest. That's the gate.
- Canonical = subtract.ing over TLS. Git hosts = mirror-only, never the publish target.
- Push origin = rousseau. Emile / Media / Surface do not push canonical content.
