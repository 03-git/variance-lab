# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. This is the plan only.

## 0. Pre-flight (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds, node state. Read it before anything else.
- In `~/subtract.ing/`: `git status`, `git log --oneline -5`, and verify the last manifest signature:
  `ssh-keygen -Y verify -f allowed_signers -I <governor-id> -n manifest -s MANIFEST.sig < MANIFEST`
- Surface any unsigned drift. **Human decides: sign / continue / abort.** I do not proceed past unsigned drift.

## 1. Author the file (agent prepares)
- Write the new file in the canonical working tree: `~/subtract.ing/<name>.txt`.
- Not `/tmp` — `/tmp` is never authoritative. The file is canonical only under the signing key's domain (reflex.5); git hosts will be mirror-only.

## 2. Sign it (human only — authority boundary)
- The agent never touches the signing key. The governor runs, on a machine holding the key:
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt`
- Produces `<name>.txt.sig` (armored `-----BEGIN SSH SIGNATURE-----`). Namespace is `file` — the verifier must match it.
- Do not invent a signature scheme (reflex.2); `ssh-keygen -Y` is the format a stranger can verify with stock OpenSSH.

## 3. Make the key binding fetchable
- The `allowed_signers` line (`<governor-identity> ssh-ed25519 AAAA…`) must be served **from subtract.ing itself** — e.g. `https://subtract.ing/allowed_signers`. The signing key's own domain is the trust root; a key published only on a git mirror proves nothing (reflex.5, fail.drift).
- If that entry isn't already published, add it to the deploy and have the governor confirm it.

## 4. Publish (human triggers; correct machine pushes)
- Deploy `<name>.txt` and `<name>.txt.sig` to the **subtract.ing origin** — the host that serves `subtract.ing` over TLS. That is the canonical push.
- Rousseau (this node, governor's workstation) prepares and stages; the **governor triggers the deploy**. The agent does not autonomously push load-bearing content (boundary: agent prepares, human signs/ships).
- Mirrors get it by replication, never as source: GitHub/git remotes are mirror-only; **Emile (m2mini)** and **acer1660ti** are not push targets for canonical content — acer isn't even formation, it's the NAS/backup tier. Pushing canonical text from a mirror would invert the trust direction.

## 5. Record it (loop.after)
- Add `<name>.txt` + its SHA-256 to `~/subtract.ing/MANIFEST`.
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n manifest MANIFEST`.
- Commit (`git commit`), push to mirrors. Commit is bookkeeping; the `.sig` files are the authority.

## 6. How a stranger verifies, a year out
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <governor-identity> -n file \
    -s <name>.txt.sig < <name>.txt
```
- Exit 0 + `Good "file" signature for <id>` ⇒ the file is exactly what the key-holder signed.
- Trust chain: TLS on `subtract.ing` vouches for `allowed_signers` → the listed Ed25519 key vouches for the file. No GitHub, no Claude, no node identity is in the path. If the mirror and the domain ever disagree, the domain wins (reflex.5).
- Long-term durability: the verifier needs the *same* identity string and namespace (`file`); both are fixed above and recorded in MANIFEST. As long as the key isn't rotated out of `allowed_signers` without a `valid-before`, the signature stays checkable offline.

## Authority boundaries in one line
Agent (Rousseau): writes file, stages deploy, drafts manifest, runs `-Y verify`. Human: holds the key, runs `-Y sign`, triggers the publish. Push target: subtract.ing origin only. Mirrors (git, Emile, acer): replicate, never originate.
