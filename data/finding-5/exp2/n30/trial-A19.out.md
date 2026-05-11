## Plan: publish a verifiable `.txt` to subtract.ing

### 0. Reflex checks before touching anything
- **reflex.2 (memory→signature):** don't invent a signature format. `ssh-keygen -Y sign` / `-Y verify` already does this. Artifact = plain UTF-8 `newfile.txt` + detached `newfile.txt.sig`. Nothing else.
- **reflex.5 (canonical→signing domain):** canonical home is `https://subtract.ing/newfile.txt`. Any git host (GitHub etc.) is a **mirror only** — pushing there does not establish authorship.
- **boundary:** I (agent, on Rousseau) prepare. The human signs. New signing is a human gate; I do not sign and do not self-authorize the publish of new signed content.
- Session start: `bash ~/scripts/audit-health.sh` first — confirm DNS/drives/state before acting.

### 1. Author the file — on Rousseau (this node)
Rousseau holds the canonical tree and is the governor's workstation.
- Write `~/subtract.ing/newfile.txt` (or the runtime subtree it belongs in).
- `git -C ~/subtract.ing status` / `git log --oneline -5` first to confirm the tree isn't behind.
- `git -C ~/subtract.ing add newfile.txt` — stage, do not commit yet.

### 2. Human gate — signing (only the human, on Rousseau)
I surface the staged file; the human runs:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/newfile.txt
```
→ produces `~/subtract.ing/newfile.txt.sig`. The signing identity is the one already in `allowed_signers` (principal `jnous`). This signature *is* the consent record (`authority.signed`). loop.before.3: human decides sign / continue / abort here.

### 3. Verify locally before publishing (reflex.4, loop.before.1)
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file \
  -s ~/subtract.ing/newfile.txt.sig < ~/subtract.ing/newfile.txt
```
Must print `Good "file" signature for jnous ...`. If it doesn't verify, stop — do not publish.

### 4. Update + sign the manifest (loop.after.1, loop.after.2)
- Add `newfile.txt` and its `sha256` to the manifest in `~/subtract.ing/`.
- Human re-signs the manifest the same way (`ssh-keygen -Y sign -n file MANIFEST`).
- `git -C ~/subtract.ing add -A && git commit -m "publish newfile.txt + sig"`.

### 5. Publish — Rousseau pushes; nothing else does
- **Rousseau** deploys to the subtract.ing web origin via the existing deploy path (rsync/git push to the origin host). It ships **three** files reachable under the domain:
  - `https://subtract.ing/newfile.txt`
  - `https://subtract.ing/newfile.txt.sig`
  - `https://subtract.ing/allowed_signers` (the trust root — confirm it's already served; it must be, or the signature is unanchored)
- **Does not push:** Emile (compute node, not a publishing path), Media/acer1660ti (service infra, explicitly *not* formation), Surface (governor terminal, not a server). A GitHub mirror may receive the same commit but is mirror-only and carries no authority.
- Pushing these *already-signed* bytes across nodes/mirrors is plain infra — I can do it. The signing and the decision to publish were the gated parts.

### 6. How a stranger verifies, a year later
```
curl -O https://subtract.ing/newfile.txt
curl -O https://subtract.ing/newfile.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s newfile.txt.sig < newfile.txt
```
Expect: `Good "file" signature for jnous with ED25519 key SHA256:...`.

Why it holds:
- **Trust anchor = the signing key's domain.** `allowed_signers` is served from subtract.ing itself — the same domain making the authorship claim (reflex.5). Bytes fetched from a git mirror are fine, but the claim is only as good as re-running `-Y verify` against the domain-served `allowed_signers`.
- **Key continuity:** the ed25519 public key that signed must still be listed a year out. On rotation, the old key stays in `allowed_signers` with `valid-before="..."` / `valid-after="..."` fields so historical signatures keep verifying.
- A verifier wanting more can check the manifest (also signed) lists `newfile.txt` with a matching `sha256`.

### Authority boundaries, summarized
| Action | Who |
|---|---|
| author file, stage, update manifest draft, run `-Y verify`, run the deploy | agent (Rousseau) |
| `ssh-keygen -Y sign` on file and manifest; decide to publish | human only |
| canonical location | `subtract.ing` domain — git hosts are mirrors, never authoritative |
| nodes that publish | Rousseau only; not Emile, not Media, not Surface |
