## Plan — publish a verifiable `NAME.txt` to subtract.ing

Assumptions I'd lock down first: the final file name (`NAME.txt`), and the signer identity string that goes in the signature — the governor's published signing identity (e.g. `jnous`), which must match an entry in the canonical `allowed_signers`. `reflex.2` check up front: nothing to invent — this system already uses `ssh-keygen -Y` SSH signatures, so the format is fixed and verifier-reproducible. Don't roll a new one.

### 0. Pre-flight on Rousseau (agent) — `loop.before`
- `bash ~/scripts/audit-health.sh` — ground truth on DNS/creds/drives before touching anything.
- `cd ~/subtract.ing && git log --oneline -5 && git status` — know the canonical state.
- Verify the current canonical index is intact before extending it:
  `ssh-keygen -Y verify -f ~/.subtract/allowed_signers -I <signer-id> -n file -s MANIFEST.sig < MANIFEST`
- Surface any unsigned drift; governor decides sign / continue / abort (`loop.before.3`).

### 1. Draft on Rousseau (agent) — drafting/archive node
- Write `~/subtract.ing/NAME.txt` in the canonical tree (Rousseau drafts; `~/subtract.ing` here is canonical, git hosts are not — `reflex.5`).
- Treat the bytes as frozen once you move on: the signature is over exact bytes, any later whitespace edit silently invalidates it.

### 2. Update the manifest (agent) — `loop.after.1`
- Add `NAME.txt` and its `sha256` to `~/subtract.ing/MANIFEST`. Agent prepares; doesn't sign.

### 3. Sign — **HUMAN GATE. Agent does not do this.** — `loop.after.2`, `boundary`, `authority.source`
Hand the governor the exact commands; warn that this needs the private key and is a blocking step; then stop (no retry loop):
- `ssh-keygen -Y sign -f ~/.ssh/<signing-key> -n file ~/subtract.ing/NAME.txt` → `NAME.txt.sig`
- `ssh-keygen -Y sign -f ~/.ssh/<signing-key> -n file ~/subtract.ing/MANIFEST` → refreshed `MANIFEST.sig`

The agent prepares; the human signs; the signature is the authority. Only *new signing* is the gate — everything before and after is the agent's.

### 4. Verify before publishing (agent, Rousseau) — `reflex.4`
- `ssh-keygen -Y verify -f ~/.subtract/allowed_signers -I <signer-id> -n file -s ~/subtract.ing/NAME.txt.sig < ~/subtract.ing/NAME.txt` — must exit 0.
- Same for `MANIFEST` / `MANIFEST.sig`. If either fails, stop — don't publish.

### 5. Publish to the canonical domain (agent, from Rousseau)
- rsync the signed bundle — `NAME.txt`, `NAME.txt.sig`, updated `MANIFEST`, `MANIFEST.sig`, and `allowed_signers` if not already live — to the subtract.ing web host:
  `rsync -avz --checksum ~/subtract.ing/ <subtract-web-host>:/var/www/subtract.ing/`
- This is the publish that establishes the claim (`reflex.5`: canonical lives under the signing key's domain). Pushing already-signed artifacts is infra work, not a gate — agent executes it.

### 6. Mirror — optional, non-authoritative
- `git -C ~/subtract.ing add NAME.txt NAME.txt.sig MANIFEST MANIFEST.sig && git commit -m "publish NAME.txt" && git push <github-remote>`
- Mirror only. A verifier must not treat the GitHub copy as proof of *who* — `reflex.5`.

### Which machine pushes, which doesn't
- **Rousseau** — holds canonical `~/subtract.ing/`, runs verification, performs the canonical rsync to the web host. ✅
- **Governor's private-key machine** — performs the `ssh-keygen -Y sign`. Not an agent action. ✅ (authority)
- **GitHub / any git remote** — receives a mirror push; proves nothing about authorship. ❌ as a trust source.
- **Emile / Media (acer) / Surface** — not involved. Media is service infra, not formation canonical; don't push canonical from there.

### How a stranger verifies it a year later
1. `curl -O https://subtract.ing/NAME.txt`
2. `curl -O https://subtract.ing/NAME.txt.sig`
3. `curl -O https://subtract.ing/allowed_signers` — the trust root, served from the signing key's own domain. That co-location is the point: the domain vouches for the key, the key vouches for the file.
4. `ssh-keygen -Y verify -f allowed_signers -I <signer-id> -n file -s NAME.txt.sig < NAME.txt`
   → `Good "file" signature for <signer-id>`, exit 0. That's the confirmation.
5. Optional corroboration: check `NAME.txt`'s `sha256` is listed in `MANIFEST` and that `MANIFEST.sig` verifies the same way — shows the file is part of the canonical set, not a stray signed blob.

### Durability notes for the year-later case
- The signature is over bytes and doesn't expire; it stays valid even if the domain lapses — *provided the verifier has a trusted copy of the signer's public key*. So the pubkey should also be discoverable off-domain (governor's other published identities), with subtract.ing remaining the canonical assertion.
- If only the GitHub mirror survives, the `.sig` still verifies against an independently-obtained pubkey. What the mirror *cannot* be is the authority for *which* key is the right one — that's why `allowed_signers` must be fetched from the signing domain, not the mirror.

No commands executed — plan only.
