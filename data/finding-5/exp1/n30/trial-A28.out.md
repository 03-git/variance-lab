# Plan: publish a verifiable-authorship `.txt` to subtract.ing

Not executing. This is the sequence, the boundaries, and the verifier's check.

## 0. Pre-flight (Rousseau, before touching anything)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS/creds/drives before acting.
- reflex.4: verify the *current* canonical state with a live read before adding to it. Fetch and check the existing manifest signature:
  - `curl -fsSL https://subtract.ing/manifest.txt -o /tmp/manifest.txt`
  - `curl -fsSL https://subtract.ing/manifest.txt.sig -o /tmp/manifest.txt.sig`
  - `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s /tmp/manifest.txt.sig < /tmp/manifest.txt`
  - If that fails or the live manifest is ahead of the working tree, stop and re-sync — don't build on unverified state.
- In `~/subtract.ing/`: `git status`, `git log --oneline -5`, confirm clean tree on the canonical path (the repo on Rousseau is canonical; GitHub is a mirror — reflex.5).

## 1. Draft (Rousseau, agent does this)
- Author the file in the canonical working tree, e.g. `~/subtract.ing/<name>.txt`. `~/human/` and `~/subtract.ing/` on Rousseau are the canonical origins for formation-authored content; Emile pulls, Acer/Media never holds signing material.
- This is the agent's whole job here: prepare. The agent does **not** sign.

## 2. Sign — the human gate (governor runs this, not the agent)
- boundary / loop.before.3: the signature proves authority; the agent prepares, the human signs. New signing is the one hard gate (already-signed artifacts moving between nodes are just infra).
- Warn the governor first (it touches the key). Command the governor runs:
  - `ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file ~/subtract.ing/<name>.txt`
  - → produces `~/subtract.ing/<name>.txt.sig`
- The namespace `-n file` is load-bearing — the verifier must use the same string. Don't invent a signing scheme; `ssh-keygen -Y` is the primitive already in use (reflex.2).

## 3. Make the signer resolvable by a stranger
- A detached sig is useless to someone who doesn't already have the key. The binding identity→pubkey must be published under the signing key's own domain (reflex.5: canonical lives under the signing domain, not a git host).
- Ensure `~/subtract.ing/allowed_signers` contains the line and will be served at `https://subtract.ing/allowed_signers`:
  - `jnous namespaces="file" ssh-ed25519 AAAAC3Nza... rousseau`
- If `allowed_signers` itself changed, it gets signed too (governor: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file ~/subtract.ing/allowed_signers`). Root of trust = that pubkey, anchored by the HTTPS domain and its consistency over time.

## 4. Update + sign the manifest (loop.after.1, loop.after.2)
- Add an entry for `<name>.txt` to `~/subtract.ing/manifest.txt`: path, `sha256sum` digest, sig filename, date `2026-05-10`.
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file ~/subtract.ing/manifest.txt` → new `manifest.txt.sig`.
- Now the chain is: domain → `allowed_signers` (pubkey) → signed `manifest.txt` → digest of `<name>.txt` + its own `.sig`.

## 5. Push — which machine, which doesn't
- **Rousseau pushes.** It's the governor's workstation and the canonical home of `~/subtract.ing/`. The agent may execute this step — moving the already-signed bundle to its publish target is infra, not a new gate.
  - `git -C ~/subtract.ing add <name>.txt <name>.txt.sig manifest.txt manifest.txt.sig allowed_signers`
  - `git -C ~/subtract.ing commit -m "publish <name>.txt + sig; manifest bump"`
  - Push to the deploy remote that serves subtract.ing (the canonical target), then to the GitHub mirror second.
- **Emile** can pull a copy as warm mirror; it does **not** originate the canonical push.
- **Acer / Media** does **not** touch this at all — service-infra tier, outside the formation, holds no signing material.
- **Surface** is a governor terminal, not the canonical store; it doesn't push this.
- The signing key never leaves Rousseau. No node re-signs; everyone downstream only ever verifies.

## 6. Confirm it's live (Rousseau, agent)
- `curl -fsSL https://subtract.ing/<name>.txt` and `…/<name>.txt.sig` and `…/allowed_signers` and `…/manifest.txt[.sig]` all 200.
- Re-run the verify command from step 7 against the *served* copies, not the local ones.

## 7. How a stranger verifies, a year from now
Only `openssh` needed — no accounts, no trust in any git host.
```
curl -fsSL https://subtract.ing/<name>.txt        -o name.txt
curl -fsSL https://subtract.ing/<name>.txt.sig    -o name.txt.sig
curl -fsSL https://subtract.ing/allowed_signers   -o allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s name.txt.sig < name.txt
```
- Exit 0 + `Good "file" signature for jnous` ⇒ the file was signed by the holder of the `jnous` key. That's the authorship claim.
- Strengthen it: also pull `manifest.txt` + `manifest.txt.sig`, verify the manifest the same way, and confirm `sha256sum name.txt` matches the digest the signed manifest records (and that the manifest dates the entry to 2026-05-10). Cross-check the `ssh-ed25519 AAAA…` fingerprint in `allowed_signers` against any earlier signed artifact on the domain — continuity over time is the anchor, since there's no CA.
- The signature does not expire; verification a year out is identical to verification today.

## Authority boundaries in one view
- Agent: drafts, stages, updates manifest text, pushes the signed bundle, checks it's live.
- Governor (human gate): every `ssh-keygen -Y sign` invocation — the new file, `allowed_signers` if changed, the manifest. Nothing else.
- reflex.5: subtract.ing (signing-key domain) is canonical; GitHub is mirror-only.
- reflex.4: verify the existing signed manifest before adding to it.
- Key custody: Rousseau only. Acer/Media excluded entirely. Emile/Surface verify-only.
