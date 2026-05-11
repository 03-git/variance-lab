# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. Order matters; each layer waits on the one below it.

## 0. Pre-flight (ground truth, no assumptions)
- `bash ~/scripts/audit-health.sh` — DNS, creds, drives, node state.
- Confirm the actual subtract.ing deploy path before touching anything: `git -C ~/subtract.ing log --oneline -5`, `git -C ~/subtract.ing status`, and whatever publish hook/rsync target that repo uses. Do not assume the mechanism — read it.
- Identify the signing identity and its `allowed_signers` line already in use for subtract.ing content (the key is the governor's; published under the subtract.ing domain). Decide the signature namespace and reuse it consistently (`-n file` below — match whatever existing `.sig` files on subtract.ing use; check one with `ssh-keygen -Y check-novalidate -n file -s existing.txt.sig < existing.txt`).

## 1. Author — rousseau, staging, no gate
- Write the file at `~/human/<area>/newfile.txt` on **rousseau** (node 01, canonical holder of `~/human/`, governor's workstation). This is reversible staging — rousseau drafts, no permission needed.

## 2. Sign — HUMAN GATE (governor only)
New signing is the one hard gate (`boundary`, `authority.signed`, `loop.before.3`). The agent prepares the exact command; the governor runs it. Warn first that `ssh-keygen` may prompt for the key passphrase (macOS/agent popup).
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/human/<area>/newfile.txt
# produces newfile.txt.sig
```
The agent does **not** run this and does not proxy it over SSH.

## 3. Verify locally before publishing (`reflex.4`, `loop.before.1`)
```
ssh-keygen -Y verify -f ~/.ssh/allowed_signers \
  -I <signing-identity> -n file \
  -s ~/human/<area>/newfile.txt.sig < ~/human/<area>/newfile.txt
```
Must print `Good "file" signature for <identity>`. If not, stop — do not publish.

## 4. Manifest (`loop.after.1`, `loop.after.2`)
- Add `newfile.txt` + its SHA-256 to the subtract.ing manifest.
- Governor re-signs the manifest (same `ssh-keygen -Y sign` gate as step 2).
- Verify the manifest signature with `ssh-keygen -Y verify` the same way.

## 5. Publish — rousseau pushes; the canonical target is subtract.ing, not a git host
- `reflex.5`: canonical content lives under the signing key's domain — **subtract.ing**. GitHub or any git remote is **mirror-only**; pushing there is fine but is never the address you cite and never the thing a verifier trusts.
- Artifacts to publish together: `newfile.txt`, `newfile.txt.sig`, the updated manifest + `manifest.sig`, and the `allowed_signers` (or however the public key is already exposed on the domain — `.well-known`, SSHFP, an existing `allowed_signers.txt`; reuse the existing convention, don't invent one — `reflex.2`).
- Push via the deploy mechanism confirmed in step 0 (rsync/git-to-origin/whatever it actually is). This moves **already-signed** artifacts → infra work, not a gate → the agent can do it.
- **Which machine pushes:** rousseau (01). **Which does not:** Emile (m2mini) and Surface are not canonical publishers; Media/acer1660ti is a non-formation warm-backup tier and never pushes canonical. If parallel/heavy work were needed it'd go to Emile via `ssh m2mini "claude -p"` — but publishing isn't that.

## 6. Live-read confirmation (`reflex.4` — don't assert it's published until you've read it back)
```
curl -fsSLO https://subtract.ing/newfile.txt
curl -fsSLO https://subtract.ing/newfile.txt.sig
ssh-keygen -Y verify -f <fetched allowed_signers> -I <signing-identity> -n file \
  -s newfile.txt.sig < newfile.txt
```
Only after this prints `Good "file" signature` does the agent state the file is published and verifiable.

## How a stranger confirms it, a year later
1. `curl -O https://subtract.ing/newfile.txt` and `curl -O https://subtract.ing/newfile.txt.sig`.
2. Obtain the signer's allowed-signers entry from subtract.ing's published location (the same domain — TLS + domain provenance is the trust root; `reflex.5` says the domain, not a git mirror, is canonical). Optionally cross-check that key against any out-of-band copy they have.
3. ```
   ssh-keygen -Y verify -f allowed_signers -I <signing-identity> -n file \
     -s newfile.txt.sig < newfile.txt
   ```
   `Good "file" signature for <identity>` → authorship confirmed. The signature is over the file bytes, so it survives mirroring; it stays valid as long as the key in `allowed_signers` is the one the governor controls.
4. Optional integrity cross-check: fetch the signed manifest, verify its signature the same way, and confirm `newfile.txt`'s SHA-256 matches the manifest entry.

Note for the verifier: a GitHub "Verified" badge or a signed git commit on a mirror proves nothing here — `reflex.5`. The only authority is the `ssh-keygen -Y verify` pass against the key published under subtract.ing.

## Authority boundaries in one line each
- New signing (steps 2, 4): human gate, governor only — `boundary`, `authority.signed`.
- Authoring/staging in `~/human/` (step 1): reversible, agent acts freely.
- Pushing already-signed artifacts (step 5): infra work, agent acts — `feedback_human_gate_scope`.
- Asserting "it's published/verifiable" (step 6): counts as an action — requires a live read first, `reflex.4`.
- Canonical = subtract.ing under the signing key; git hosts are mirrors — `reflex.5`.
