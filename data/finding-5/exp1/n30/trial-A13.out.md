Plan only — nothing executed.

## 0. Reflex check first
- `reflex.2`: don't invent a signature format — `ssh-keygen -Y sign`/`-Y verify` (SSH signature, namespace `file`) already does this. Use it.
- `reflex.5`: canonical = bytes served under `https://subtract.ing/` (the signing key's domain). Any git remote is a mirror, never the authority.
- `boundary`: I prepare; the governor signs. I never run `ssh-keygen -Y sign`.

## 1. Pre-flight on rousseau (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS/drives/creds before touching anything.
- `cd ~/subtract.ing` (the canonical working tree; same root that holds `runtime/hosuni/hosuni.c` and `governance.conf.universal.txt`).
- `git log --oneline -5`, `git status` — confirm clean tree.
- Live-read the current state (`reflex.4`, don't trust the working copy): `curl -s https://subtract.ing/MANIFEST` (or whatever the manifest is named) and compare to the local file.
- Verify the existing manifest's signature so I'm building on signed ground:
  `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST` → must print `Good "file" signature for jnous`.

## 2. Author the file (agent, no permission needed — reversible staging write)
- Write `~/subtract.ing/<name>.txt` with the Write/Edit tool. Plain UTF-8, LF line endings, no BOM.
- `sha256sum <name>.txt` — record the digest.

## 3. Update the manifest (agent)
- Add the line `<sha256>  <name>.txt` to `~/subtract.ing/MANIFEST` with Edit.
- This is loop.after.1 done early so it's part of the same signed unit.

## 4. Human gate — signing (governor only, on the machine holding the private key = rousseau)
Warn the governor first: `ssh-keygen -Y sign` will read `~/.ssh/id_ed25519` and may prompt for a passphrase (macOS popup possible). Then *they* run:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST
```
Produces `<name>.txt.sig` and `MANIFEST.sig`. Signing identity is `jnous`; `allowed_signers` maps `jnous` → that ed25519 public key, and that file is itself published under subtract.ing so the verifier can fetch the trust root from the signing key's own domain.

I do not do this step. If it fails, I flag and stop — one attempt (`claude -p`-style human-gate discipline does not apply, but the don't-spiral rule does).

## 5. Commit (agent — bookkeeping, not authority)
```
git add <name>.txt <name>.txt.sig MANIFEST MANIFEST.sig
git commit -m "publish <name>.txt (signed: jnous)"
```
The commit is a mirror record. The `.sig` is what carries authority, not the git history.

## 6. Publish — the one externally-visible step
- Push the signed bytes to whatever serves `https://subtract.ing/` (deploy path / hook on rousseau, or `git push` to the deploy remote if the site builds from it).
- **Which machine pushes:** rousseau. It holds the working tree, the private key, and is the governor's workstation. Pushing *already-signed* artifacts is infra, so I can execute the push itself — but going live is an outward-facing mutation, so I confirm with the governor before it lands.
- **Which machine does not:** Surface (and Emile, Media). None of them hold the `jnous` private key; none sign. If Surface were the deploy runner it would only ship bytes that were already signed on rousseau — it's a mirror leg, not an authority.
- Post-publish live-read verification:
  ```
  curl -s https://subtract.ing/<name>.txt | sha256sum      # == manifest digest
  curl -sI https://subtract.ing/<name>.txt.sig             # 200
  ```

## 7. Close the loop (loop.after)
- Manifest updated ✓, signed ✓. Note the publish in `~/human/sessions/2026-05-10-*.md`.

## How a stranger verifies authorship a year from now
```
curl -sO https://subtract.ing/<name>.txt
curl -sO https://subtract.ing/<name>.txt.sig
curl -sO https://subtract.ing/allowed_signers       # contains: jnous ssh-ed25519 AAAA...
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
Exit 0 + `Good "file" signature for jnous` ⇒ the holder of the `jnous` key authored *those exact bytes*. Trust chain: the public key is published under `subtract.ing`'s TLS domain (the signing key's own canonical domain), so a verifier who trusts the domain trusts the key; optionally they cross-check the key fingerprint (`ssh-keygen -lf allowed_signers`) against any other channel the governor has posted it on. Git hosts, CDNs, and my assertions are irrelevant to the proof — only the signature against the domain-published key matters.

## Authority boundaries, restated
- Agent: writes the file, computes hashes, edits the manifest text, drafts the commit, runs all *verify* reads, executes the push of signed artifacts.
- Human gate: `ssh-keygen -Y sign` — and only that. New signing is the only step that requires the governor.
- Private key: rousseau only. Surface/Emile/Media never hold it, never sign, only mirror.
- Canonical: bytes under `https://subtract.ing/`. Every git remote = mirror-only.
- Outward-facing: confirm with governor before the file goes live.
