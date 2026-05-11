# Plan — publish `foo.txt` to subtract.ing with stranger-verifiable authorship

## 0. Ground truth (before anything)
- `bash ~/scripts/audit-health.sh` — DNS, drives, node state. Read it, don't assume.
- `cd ~/subtract.ing && git log --oneline -5 && git status` — know what the docroot looks like before touching it.
- Verify the current manifest's last signature: `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n manifest -s MANIFEST.sig < MANIFEST`. If it fails or there's unsigned drift, stop and surface it (loop.before.1/.2) — the governor decides sign/continue/abort before I act.

## 1. Prepare the file (agent — preparation, not authority)
- Write the content to the canonical docroot on **Rousseau**: `~/subtract.ing/foo.txt`. Staging write, reversible — no permission gate.
- `sha256sum ~/subtract.ing/foo.txt` — record the hash for the manifest.
- Confirm the trust root is publishable: `~/subtract.ing/allowed_signers` exists and contains `jnous <keytype> <pubkey>`. This file is canonical **under the signing key's domain** (reflex.5) — it ships from subtract.ing itself, never "trust the GitHub copy."

## 2. Sign — the one human gate (authority boundary)
The agent does **not** run this. New signing is governor territory (`boundary`: the agent prepares, the human signs). Warn first that a passphrase-protected key will pop a macOS prompt. Governor runs, on Rousseau:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/foo.txt
```
→ produces `~/subtract.ing/foo.txt.sig` (detached SSH signature, namespace `file`). Format is `ssh-keygen -Y verify`-checkable (reflex.2) — no invented scheme.

Then update and sign the manifest (loop.after.1/.2): append `foo.txt  <sha256>` to `~/subtract.ing/MANIFEST`, then governor runs `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n manifest ~/subtract.ing/MANIFEST` → `MANIFEST.sig`.

## 3. Publish (agent — pushing already-signed artifacts is plain infra)
- Rousseau **is** the canonical host (subtract.ing serves from m1studio). The live docroot now contains `foo.txt`, `foo.txt.sig`, `allowed_signers`, `MANIFEST`, `MANIFEST.sig`. Reload/serve as that host normally does.
- Mirror push (e.g. `git add foo.txt foo.txt.sig MANIFEST* && git commit && git push`) to any GitHub remote is allowed but **mirror-only** (reflex.5) — it corroborates a timestamp, it is not the authority.
- **Machines that do not push canonical:** Surface (governor terminal, no host role), Emile (compute node), Media/acer (NAS + warm-backup tier, mirror only). Only Rousseau publishes the load-bearing copy.

## 4. Self-check before calling it done
The claim is not authoritative until verify passes (`authority.unsigned` = suggestion only). From a clean dir:
```
curl -O https://subtract.ing/foo.txt
curl -O https://subtract.ing/foo.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s foo.txt.sig < foo.txt
```
Expect: `Good "file" signature for jnous`. Anything else → not published.

## How a stranger confirms it a year from now
1. `curl -O https://subtract.ing/foo.txt` `foo.txt.sig` `allowed_signers` `MANIFEST` `MANIFEST.sig` — TLS cert proves the bytes came from the subtract.ing domain.
2. `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s foo.txt.sig < foo.txt` → `Good "file" signature for jnous`. The key is pinned by `allowed_signers` fetched **from the same domain** — domain control + key control are the same authority.
3. Cross-check the manifest: `ssh-keygen -Y verify -f allowed_signers -I jnous -n manifest -s MANIFEST.sig < MANIFEST`, then `sha256sum foo.txt` and grep the hash in `MANIFEST` — ties the file into the signed session record.
4. Independent of subtract.ing being up: the `.sig` is detached and self-contained, so a verifier who kept `foo.txt` + `foo.txt.sig` + the `jnous` pubkey can verify offline forever. A GitHub mirror, if present, only adds a timestamp witness — it's never the thing that proves authorship.

## Authority boundaries, summarized
- **Agent may:** run audit-health, read git state, stage `foo.txt` in the docroot, draft the manifest line, push signed artifacts to the live host and to mirrors, run `ssh-keygen -Y verify`.
- **Governor only:** `ssh-keygen -Y sign` on `foo.txt` and on `MANIFEST` — and the sign/continue/abort decision in step 0.
- **Canonical push:** Rousseau. **Not:** Surface, Emile, Media.
- Until step 4's verify returns `Good signature`, I treat the publish as unconfirmed and say so.
