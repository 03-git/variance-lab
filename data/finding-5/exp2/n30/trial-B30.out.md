# Plan: publish a verifiable .txt to subtract.ing

No execution below — plan only.

## 0. Pre-flight (Rousseau)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds before touching anything.
- `cd ~/subtract.ing && git log --oneline -5 && git status` — confirm the canonical working tree is clean and current. Canonical path only; `/tmp` copies are never authoritative.

## 1. Author the file (agent may do this)
- Write the new file inside the canonical repo, e.g. `~/subtract.ing/<name>.txt`. UTF-8, final newline, content frozen before signing (the signature covers exact bytes).
- This is the limit of agent authority: **prepare**, not sign. (`boundary`: the agent prepares, the human signs.)

## 2. Pick the signing identity (reflex.2, reflex.5)
- The trust anchor is an SSH key whose principal is in the **subtract.ing signing domain** — i.e. the identity already listed in the published `allowed_signers` (something like `governor@subtract.ing`). Confirm it: `cat ~/subtract.ing/allowed_signers` (or wherever the site serves it).
- Format check before inventing anything: `ssh-keygen -Y sign` / `ssh-keygen -Y verify` with namespace `file` is the format. Nothing custom.
- If no `allowed_signers` is published yet, that bootstrap (publishing the public key as the trust root) has to happen first and out of band — a verifier a year out needs that file at a stable subtract.ing URL.

## 3. Sign — **human only**
The governor runs, not the agent (private key never reaches the agent):
```
ssh-keygen -Y sign -f ~/.ssh/<signing_key> -n file ~/subtract.ing/<name>.txt
```
→ produces `~/subtract.ing/<name>.txt.sig` (the SSHSIG armored blob).

Optionally re-verify locally before publishing (`reflex.4` — verify with a live read before acting):
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers \
  -I <governor@subtract.ing> -n file \
  -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt
```

## 4. Publish — which machine pushes
- **Rousseau pushes.** It is node 01, the archive node and governor's workstation, and it holds the canonical `~/subtract.ing` tree.
- **Emile does not push.** Heavy/parallel work can be dispatched to `ssh m2mini "claude -p"`, but it is not the canonical origin for site content.
- **acer1660ti does not push.** Not formation — it's a service/warm-backup tier, not a publish origin.
- Commit both artifacts together:
  ```
  cd ~/subtract.ing
  git add <name>.txt <name>.txt.sig
  git commit -m "publish <name>.txt + sshsig"
  ```
- Deploy to the **subtract.ing host itself** — that deploy (rsync/git pull on the web server, whatever the existing mechanism is) is what makes the file canonical. Per `reflex.5`, pushing to GitHub or any git mirror does **not** make it canonical; mirrors are mirror-only. The file, its `.sig`, and `allowed_signers` must all be reachable over HTTPS under `subtract.ing/`.

## 5. Close the loop (loop.after)
- Update the archive/manifest entry for the new file (`loop.after.1`).
- Sign the manifest (`loop.after.2`) — again, human runs `ssh-keygen -Y sign`.

## Authority boundaries in play
- `authority.signed` / `authority.unsigned`: the .txt is authoritative only once `ssh-keygen -Y verify` passes against the published `allowed_signers`. Until then it's just bytes on a server.
- `boundary`: agent writes the file and stages the commit; **human** produces the signature. No agent path to the private key.
- `reflex.4`: verify the existing signature with a live read before the deploy step.
- `reflex.5`: canonical = the signing key's domain (`subtract.ing`). Tell verifiers to fetch from there, not from a git host.

## How a stranger verifies, a year later
On any machine with OpenSSH (≥ 8.1 for `-Y`):
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers \
  -I <governor@subtract.ing> -n file \
  -s <name>.txt.sig < <name>.txt
```
Expected: `Good "file" signature for <governor@subtract.ing> with ED25519 key SHA256:…`

That line is the claim confirmed: the bytes of `<name>.txt` were signed by the key that subtract.ing's published `allowed_signers` names as the author. No dependency on GitHub, on Rousseau being online, or on me — only on the key and the published trust anchor. If `allowed_signers` itself needs vouching, it should be cross-published / signed by the same key chain so the anchor is independently checkable.
