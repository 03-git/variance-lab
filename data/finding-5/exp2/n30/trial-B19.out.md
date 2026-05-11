## Plan — publish a verifiable `.txt` to subtract.ing

Not executing. This is the sequence, the boundaries, and the verify path.

### 0. Ground truth first
- `bash ~/scripts/audit-health.sh` — read DNS, creds, drive, node state before touching anything. Where subtract.ing is actually served from and which node holds its deploy credential comes from this, not from memory.

### 1. Reflex check before inventing anything (reflex.2)
- The signing format is OpenSSH's `SSHSIG` via `ssh-keygen -Y sign` / `ssh-keygen -Y verify`. That is the kernel primitive — don't wrap it, don't invent a manifest-hash scheme on top. Namespace: `file`.

### 2. Prepare the file (agent does this part)
- Write it at the canonical tree: `~/subtract.ing/<path>/thing.txt`.
- Show content to the governor for sign-off. Until it's signed it's a suggestion only (authority.unsigned).

### 3. Sign — human only (boundary; authority.source = the human)
- Governor runs, on the machine holding the signing key:
  `ssh-keygen -Y sign -f ~/.ssh/<signing_key> -n file ~/subtract.ing/<path>/thing.txt`
- Produces `thing.txt.sig` (armored SSHSIG blob).
- The agent does not hold, read, or invoke the private key. The agent prepares; the human signs.

### 4. Publish the verification anchor (`allowed_signers`)
- A stranger needs the public half bound to an identity. Publish/confirm one line:
  `jns@subtract.ing namespaces="file" ssh-ed25519 AAAA...<pubkey>`
- Host it at a stable URL **under the signing key's domain**: `https://subtract.ing/allowed_signers` (reflex.5 / reflex.canonical — load-bearing content is canonical under the signing key's domain; GitHub or any git host is mirror-only and must not be the anchor).

### 5. Push — canonical host, with explicit go-ahead
- Push target = the subtract.ing web root, served from whatever node `audit-health.sh` says hosts it / holds the deploy credential. **Not** a git mirror.
- Which machine pushes: the node that is the publish authority for subtract.ing (Rousseau, the governor's workstation/archive node, if it holds that credential — confirm via audit). **Which does not:** Emile (compute offload, not publish authority) and any git mirror. Don't `git push` the authoritative copy to a mirror and call it published.
- This is outward-facing and hard to reverse (caching/indexing) → confirm with the governor before the push, even if routine.
- Artifacts pushed: `thing.txt`, `thing.txt.sig`, and `allowed_signers` if it changed.

### 6. Close the loop (loop.after)
- Update the archive manifest: new file path + sha256 of `thing.txt` and `thing.txt.sig`.
- Governor signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/<signing_key> -n file <manifest>`.

### 7. How a stranger verifies, a year out
```
curl -O https://subtract.ing/<path>/thing.txt
curl -O https://subtract.ing/<path>/thing.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s thing.txt.sig < thing.txt
```
- Exit 0 + `Good "file" signature for jns@subtract.ing` ⇒ claim confirmed.
- Time-independence: SSHSIG carries no expiry; it verifies as long as the pubkey in `allowed_signers` is the one the governor controls. The verifier should cross-check that `allowed_signers` line against an independent channel (a mirror, a prior signed manifest, anywhere else the governor has published the same key) so they're not trusting subtract.ing's web server alone.

### Authority boundaries, summarized
- **Agent may:** run `audit-health.sh`, write/stage the file, draft the manifest, run `ssh-keygen -Y verify` (read-only check, reflex.4), prepare the push.
- **Human only:** `ssh-keygen -Y sign` (signing key), approving the push to the live host.
- **Canonical** = subtract.ing under the signing key's domain. **Git hosts = mirror-only** — never the source of truth, never the push target for the authoritative copy, never the verification anchor.
- Nothing here counts as "published" until `ssh-keygen -Y verify` passes against the published `allowed_signers`. Unsigned = suggestion, possibly confabulation — do not treat it as done.
