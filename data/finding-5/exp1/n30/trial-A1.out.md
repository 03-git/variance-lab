# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. This is the plan only.

## 0. Pre-flight on rousseau (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, creds, drives, node state. Read it before anything else.
- In the canonical tree (`~/subtract.ing/`): `git status`, `git log --oneline -5`, and verify the current manifest's signature:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous@subtract.ing -n file -s MANIFEST.sha256.sig < MANIFEST.sha256`
- If that fails or there's unsigned drift in the tree: stop, surface it, human decides (sign / continue / abort). Don't build on an unverified base (reflex.4, fail.confabulation).

## 1. Author the file (rousseau — agent does this, reversible staging write)
- Write `~/subtract.ing/<name>.txt`. Rousseau is canonical for authored content; it drafts (feedback: Rousseau drafts).
- Compute the digest you'll commit to: `sha256sum ~/subtract.ing/<name>.txt`.
- No permission needed for this — it's a staging write, not an external mutation (feedback: stop asking on reversible ops).

## 2. Human gate — signing (boundary; only the human holds the key)
The agent **cannot** do this step. Prepare the exact command and hand it over. Warn first that this may pop a keychain/passphrase prompt (feedback: warn before human gates).

Governor runs, on rousseau:
```
cd ~/subtract.ing
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file <name>.txt
```
→ produces `<name>.txt.sig` (armored `-----BEGIN SSH SIGNATURE-----` block, namespace `file`).

This is `reflex.2` satisfied: `ssh-keygen -Y sign` is the format, not an invented one. It's `loop.before.3` / `boundary`: the agent prepared, the human signed.

## 3. Verify locally before publishing (reflex.4 — a live read, not an assertion)
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous@subtract.ing -n file -s <name>.txt.sig < <name>.txt
```
Must print: `Good "file" signature for jnous@subtract.ing`. If not — do not publish.

Confirm `~/subtract.ing/allowed_signers` contains the line:
`jnous@subtract.ing ssh-ed25519 AAAA... ` (the governor's signing pubkey). The verifier needs this file reachable; it must ship too (step 4).

## 4. Update + re-sign the manifest (loop.after — second human gate)
- Agent appends to `MANIFEST.sha256`: the sha256 from step 1 for `<name>.txt`, and (if not already listed) for `allowed_signers`.
- Governor re-signs:
  ```
  ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file MANIFEST.sha256
  ```
- Agent re-verifies the new `MANIFEST.sha256.sig` exactly as in step 3.

## 5. Push — which machine, which boundary
- **Canonical source of truth: rousseau** (`~/subtract.ing/`). The signing key's domain is canonical; the web host and any git remote are **mirror-only** (reflex.5).
- **Deploy/push: rousseau drives it, or hands the signed bundle to Surface to execute** (feedback: Rousseau drafts, Surface executes — Surface is still live, the 2026-05-22 reorg hasn't happened). Pushing **already-signed** artifacts is plain infra work, not a human gate (feedback: human gate scope) — the agent can run it once step 3 passed.
- Mechanism: whatever `~/subtract.ing/`'s documented deploy script does (e.g. `rsync -avz --checksum ~/subtract.ing/ <deploy-target>:<webroot>/` or `git push <mirror>` that triggers a build). Read the deploy script and state what it actually does — don't assume the transport (fail.confabulation). Push set must include: `<name>.txt`, `<name>.txt.sig`, `allowed_signers`, `MANIFEST.sha256`, `MANIFEST.sha256.sig`.
- **Emile does NOT push** — it's a pull-mirror of rousseau (it re-syncs on its own discover/sync run). **Acer/Media does NOT push** — NAS endpoint, warm backup tier, not formation, no inference and no canonical authority.

## 6. Post-publish read-back (close the loop before calling it done)
From a clean network path: `curl -s https://subtract.ing/<name>.txt | sha256sum` and compare to the value in the signed `MANIFEST.sha256`. Re-run the step-3 `ssh-keygen -Y verify` against the *fetched* copies, not the local ones.

## 7. How a stranger verifies it a year from now
They need three files and one command. No accounts, no trust in GitHub, no trust in me.
```
curl -sO https://subtract.ing/<name>.txt
curl -sO https://subtract.ing/<name>.txt.sig
curl -sO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file -s <name>.txt.sig < <name>.txt
```
Expected: `Good "file" signature for jnous@subtract.ing`.

Then, optionally, `sha256sum <name>.txt` and check it appears in `MANIFEST.sha256`, whose own signature verifies the same way.

Why this survives a year and survives mirroring:
- The SSH signature is over the **file bytes**, not the URL — a GitHub mirror, an archive.org snapshot, or a copy emailed to them verifies identically.
- The trust root is the **public key in `allowed_signers`, distributed under the signing key's own domain** (subtract.ing over HTTPS) — that's the canonical channel per reflex.5. If they obtained the pubkey through any other channel they trust (a prior signed artifact, in person), they can substitute it.
- The only thing that can't be reconstructed later is the **private key + the human's act of signing** — which is exactly the authority boundary: `authority.signed` → act on it; `authority.source` → the human; the signature is what proves it.

## Authority boundary summary
| Step | Who | Why |
|---|---|---|
| Author text, compute digests, draft manifest, write commands | agent (rousseau) | reversible staging |
| `ssh-keygen -Y sign` on the file and on the manifest | human only | holds `~/.ssh/id_ed25519`; `boundary` / `loop.before.3` |
| `ssh-keygen -Y verify` before publish | agent | `reflex.4` — verify with a live read before acting |
| `rsync`/`git push` of already-signed bundle | agent (rousseau drives, Surface may execute) | pushing signed artifacts is infra, not a gate |
| Re-fetch + re-verify from the live URL | agent | close the loop |
| Emile / Acer push | nobody | mirror / backup only, not canonical, no push authority |
