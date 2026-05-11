# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. Plan only. (And before any of this runs for real: `bash ~/scripts/audit-health.sh` for ground truth on DNS/creds/drives — several steps below assume facts that audit must confirm first.)

## 0. Reflex check (before touching anything)
- **reflex.2 / fail.additive**: the signing primitive is `ssh-keygen -Y sign` / `-Y verify`. Do not invent a format, do not reach for GPG, minisign, or a sigstore wrapper. Detached SSH signature + a published `allowed_signers` file is the whole mechanism.
- **reflex.5**: the file is canonical only under the *signing key's domain* — it must be fetchable at `https://subtract.ing/...`. A GitHub copy is a mirror, not the source of truth.
- **boundary / authority**: the agent stages the artifact and writes the exact commands; **the human runs the one command that touches the private key**. The agent never holds or invokes the signing key.

## 1. Stage the document (agent, on Rousseau)
- Author `newdoc.txt` in the working tree that backs subtract.ing's web root (on Rousseau — that's where `~/subtract.ing/...` is maintained; confirm the actual deploy path/credential via audit + `~/.ssh/config`, don't assume).
- Freeze the bytes. Any later edit invalidates the signature, so treat the file as immutable from here on. Record `sha256sum newdoc.txt` for the manifest.

## 2. Sign (human/governor, on Rousseau)
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file newdoc.txt
```
→ produces `newdoc.txt.sig` (the detached signature, namespace `file`).

Publish/refresh the verifier key list — `allowed_signers`, one line:
```
jns@subtract.ing namespaces="file" ssh-ed25519 AAAAC3Nza...<pubkey>...
```
This file is itself canonical content under subtract.ing. If it already exists at a stable URL, reuse it; don't mint a new identity per document.

## 3. Publish (Rousseau pushes — nothing else does)
- Rousseau is the governor's workstation and holds the subtract.ing tree → **Rousseau deploys** the three artifacts to the web root:
  - `https://subtract.ing/newdoc.txt`
  - `https://subtract.ing/newdoc.txt.sig`
  - `https://subtract.ing/allowed_signers` (if not already live)
- **Surface does not push** — it's a WSL2 governor terminal, no deploy authority.
- **Emile does not push** — execution node; offload heavy work there, not publishing authority.
- **acer does not hold canonical content** — it's not formation; it may carry a warm-backup mirror only, same status as a GitHub mirror.
- Optional: mirror to a git host afterward for redundancy. Mirror-only — `git log` on a mirror proves nothing about authorship; the signature does.

## 4. Verify before declaring done (reflex.4 — live read, not self-narration)
From a clean shell (ideally not the publishing box):
```
curl -fSsO https://subtract.ing/newdoc.txt
curl -fSsO https://subtract.ing/newdoc.txt.sig
curl -fSsO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s newdoc.txt.sig < newdoc.txt
```
Expect: `Good "file" signature for jns@subtract.ing with ED25519 key ...`. Only after that print succeeds is the thing "published."

## 5. Close the loop (loop.after)
- Append to the formation manifest: filename, sha256, signer identity, signing key fingerprint (`ssh-keygen -lf ~/.ssh/id_ed25519`), publish URL, date.
- Sign the updated manifest the same way.

## How a stranger verifies it a year from now
1. `curl` the three files from `subtract.ing` over TLS (TLS authenticates the *host*; the SSH signature authenticates the *author* — independent layers).
2. Run the `ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s newdoc.txt.sig < newdoc.txt` command above.
3. A `Good "file" signature` result means: the bytes are exactly what the holder of `jns@subtract.ing`'s ed25519 key signed. No clock dependency, no CA, no service that has to still be alive — just the file, the sig, and the published pubkey.
4. Cross-check the key fingerprint against the signed manifest (and any other long-lived place the governor has published that fingerprint). If the verifier distrusts subtract.ing's copy of `allowed_signers`, the fingerprint has to match an out-of-band copy — that's the one trust anchor that can't live solely on the server it authenticates.

## Authority boundaries in force
- **Unsigned = suggestion only**: until step 2 completes, `newdoc.txt` is a draft with no authority, regardless of where it sits.
- **Agent prepares, human signs**: steps 1, 3, 4, 5 the agent can do; step 2's `ssh-keygen -Y sign` is the human's, because the signature *is* the authority and the agent isn't it.
- **Canonical lives under the signing domain**: subtract.ing is the address; git hosts and acer are mirrors and cannot be cited as the source.
- **No autonomous key handling, no model switching, nothing destructive** — and if step 4's live verify fails, stop and surface it; don't narrate around it.
