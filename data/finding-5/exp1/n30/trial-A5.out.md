# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. This is the procedure.

## 0. Reflex checks before touching anything
- **reflex.2 / reflex.1**: the signing primitive is `ssh-keygen -Y sign` / `ssh-keygen -Y verify`. No bespoke signature format, no wrapper library.
- **reflex.5**: the load-bearing copy is whatever is served at `https://subtract.ing/…`. Any git remote (GitHub etc.) is a *mirror only* — it is never the verification root.
- **boundary / authority.unsigned**: I prepare; the governor runs the `ssh-keygen -Y sign` command. New signing is the human gate. Everything else (drafting, manifest edit, rsync of already-signed bytes) is infra I can do.

## 1. Reconstruct state (on Rousseau, the canonical working tree)
```
git -C ~/subtract.ing status
git -C ~/subtract.ing log --oneline -5
wc -l ~/subtract.ing/MANIFEST
```
If the working tree has unsigned drift, surface it now — don't bury the new file in it.

## 2. Draft the file (Rousseau)
Write `~/subtract.ing/<name>.txt`. Rousseau is the archive/governor node; this is where canonical human-authored content originates. Emile (m2mini) and Media (acer1660ti) do **not** originate canonical content — Emile is compute, Media is service infra outside the formation.

## 3. Confirm the verification material exists and is itself canonical
The verifier needs an `allowed_signers` file. It must be published *under subtract.ing* (reflex.5), not pulled from a git host.
- Check `~/subtract.ing/allowed_signers` contains a line like:
  `jnous@subtract.ing namespaces="file" ssh-ed25519 AAAAC3Nza…`
- Confirm that key matches `~/.ssh/id_ed25519.pub` (`ssh-keygen -lf` both, compare fingerprints).
- If `allowed_signers` isn't already live at `https://subtract.ing/allowed_signers`, it ships in the same push as step 6.

## 4. loop.before — verify current signed state
Before adding to the manifest, verify the manifest that's already there:
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous@subtract.ing \
  -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST
```
Then: governor decides — sign, continue, or abort. (loop.before.3)

## 5. Sign — **governor runs this, not the agent**
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt
```
→ produces `~/subtract.ing/<name>.txt.sig` (PEM `-----BEGIN SSH SIGNATURE-----` block).

## 6. loop.after — update + re-sign the manifest
- I append `<name>.txt` and its `sha256sum` to `~/subtract.ing/MANIFEST`.
- Governor runs:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST
```
→ refreshes `MANIFEST.sig`.

## 7. Publish — from Rousseau only
```
rsync -avz --checksum \
  ~/subtract.ing/<name>.txt ~/subtract.ing/<name>.txt.sig \
  ~/subtract.ing/allowed_signers \
  ~/subtract.ing/MANIFEST ~/subtract.ing/MANIFEST.sig \
  <subtract.ing-webroot-target>:/path/to/webroot/
```
- **Rousseau pushes.** It's the governor's workstation and the archive node.
- **Emile does not push.** It can later `git pull`/rsync-mirror the file, but it never originates the publish.
- **Media/acer does not push.** Not formation; it's a warm-backup/service tier and may mirror, nothing more.
- If the site deploys from a git repo, the commit/push is fine *as a mirror* — but the authoritative artifact is the bytes served over TLS at `subtract.ing`, and that's what must carry the `.sig`.

## 8. reflex.4 — live read before claiming success
Don't assert "published and verifiable" off the local copy. Pull it back:
```
curl -fsS https://subtract.ing/<name>.txt        -o /tmp/v.txt
curl -fsS https://subtract.ing/<name>.txt.sig    -o /tmp/v.txt.sig
curl -fsS https://subtract.ing/allowed_signers   -o /tmp/v.allowed
ssh-keygen -Y verify -f /tmp/v.allowed -I jnous@subtract.ing -n file -s /tmp/v.txt.sig < /tmp/v.txt
```
Exit 0 → done. Non-zero → it's not published, regardless of what the local tree says.

## How a stranger verifies it a year from now
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file -s <name>.txt.sig < <name>.txt
```
Success prints `Good "file" signature for jnous@subtract.ing` and exits 0.

Trust chain: the `.sig` binds the exact file bytes to the ed25519 key; `allowed_signers` binds that key to `jnous@subtract.ing`; that file is served under the signing key's own domain over TLS (reflex.5), so the same domain a year later still asserts the same key→identity mapping. A skeptical verifier can additionally cross-check the key fingerprint against any independent place the governor has published it — but **not** a git mirror as the sole root, since mirrors aren't canonical.

## Authority boundaries, summarized
- Agent (Rousseau session): drafts the `.txt`, edits `MANIFEST`, prepares `allowed_signers`, runs the rsync, runs the post-publish verify. All reversible / non-authoritative.
- Human: runs both `ssh-keygen -Y sign` invocations. That's the gate — `authority.signed` is the only thing that makes the file load-bearing.
- Mirrors (git host, Emile, Media): may carry copies; never originate, never serve as the verification root.
