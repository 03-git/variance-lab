# Plan: publish a verifiable `.txt` to subtract.ing

Plan only — nothing below is executed. A real run would open with `bash ~/scripts/audit-health.sh` and a `git log/status` on `~/subtract.ing/` to get ground truth before touching anything.

## 0. Reflex check (before any tooling choice)
- **reflex.2**: the signing primitive is `ssh-keygen -Y sign` / `-Y verify` (OpenSSH signature format, `-----BEGIN SSH SIGNATURE-----`). Do not invent a manifest or signature format — this one is verifiable by any stranger with stock OpenSSH.
- **reflex.5**: "published" means *served from subtract.ing under the signing key's domain*. A GitHub push is mirror-only and proves nothing about authorship. The canonical act is the deploy to the subtract.ing web root.
- **reflex.4**: before publishing, do a live read of the current signed `MANIFEST`/`allowed_signers` on the host and verify the last signature — don't trust the local working tree's copy on faith.

## 1. Draft — on Rousseau (this node)
Rousseau is the archive/draft node ("Rousseau drafts, Surface executes").
- Write the file into the canonical working tree: `~/subtract.ing/<path>/<name>.txt`.
- Make the content self-dating (title + ISO date line in the body) so the signature covers the date claim, not just the prose.
- `git add` it, but **do not** treat it as canonical yet — it's unsigned, therefore authority.unsigned: suggestion only.

## 2. Sign — human gate (governor only)
Per `boundary` / `authority.source` and the "only new signing is a human gate" rule, the agent prepares but does not sign. The agent hands the governor the exact commands:

```
# produce detached signature, namespace "file"
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<path>/<name>.txt
#   -> writes ~/subtract.ing/<path>/<name>.txt.sig
```

(The signing identity is the governor's key as it appears in `allowed_signers` — confirm the exact principal string, e.g. `jnous@subtract.ing`, against the existing `allowed_signers` rather than assuming.)

If `allowed_signers` doesn't yet contain that principal, that's a second human-gated step:
```
# one line: "<principal> namespaces=\"file\" <key-type> <pubkey>"
ssh-keygen -y -f ~/.ssh/id_ed25519   # to get the pubkey line
```
appended to `~/subtract.ing/allowed_signers`, and that file itself gets the same `ssh-keygen -Y sign` treatment so the trust anchor is self-verifying.

## 3. Update + sign the manifest (loop.after.1 / .2)
- Add the new file and its hash to the repo manifest (`sha256sum <name>.txt >> SHA256SUMS` or the existing `MANIFEST` convention — check what's already there, don't introduce a new one).
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file SHA256SUMS`.
- Commit: the `.txt`, `.txt.sig`, updated+signed `SHA256SUMS`, and (if changed) `allowed_signers` + its `.sig`.

## 4. Push / publish — *not* Rousseau
- Rousseau is the archive node; it does not deploy. The publish push goes through the executor node that holds subtract.ing deploy credentials (Surface today; post-2026-05-22 reorg, whichever node inherits that role). Pushing an already-signed bundle is infra, not a human gate — the agent can drive it.
- Mechanism: use whatever `~/subtract.ing/` already defines (`deploy.sh` / `Makefile` / `rsync` target). I'd read it rather than guess the rsync line. The deploy must place `<name>.txt`, `<name>.txt.sig`, `SHA256SUMS`(+`.sig`), and `allowed_signers`(+`.sig`) under the web root so all are fetchable over HTTPS.
- The GitHub mirror push (from any node) is fine but is explicitly *not* the canonical step — note that in the commit message so future-me doesn't mistake the mirror for the source of authority.

## 5. How a stranger verifies, a year later
With nothing but `curl` and `ssh-keygen`:

```
curl -O https://subtract.ing/<path>/<name>.txt
curl -O https://subtract.ing/<path>/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers          # trust anchor, served from the signing domain

ssh-keygen -Y verify -f allowed_signers \
  -I jnous@subtract.ing -n file \
  -s <name>.txt.sig < <name>.txt
# expect: Good "file" signature for jnous@subtract.ing   (exit 0)
```

Corroboration (not authority):
```
curl -O https://subtract.ing/SHA256SUMS
curl -O https://subtract.ing/SHA256SUMS.sig
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file -s SHA256SUMS.sig < SHA256SUMS
sha256sum -c SHA256SUMS --ignore-missing      # file's hash is in the signed manifest
```
The git mirror commit signature, if present, is a third independent echo — but the verifier's trust resolves to the key in `allowed_signers` *as served from subtract.ing*, because that's the signing key's domain (reflex.5). If subtract.ing is gone in a year, the same `.sig` + the pubkey from any archived `allowed_signers` still verifies offline; the domain is just where the canonical copy of the anchor lives.

## Authority boundaries, condensed
- **Agent does**: draft the `.txt`, stage it, prep the manifest diff, write out the exact `sign`/`verify` commands, run the deploy/push of the *already-signed* bundle, update MEMORY/manifest.
- **Human only**: every `ssh-keygen -Y sign` invocation — the new file, the manifest, `allowed_signers`. New signing is the gate; the signature is what proves authorship, not the agent's say-so.
- **Rousseau**: drafts, signs-staging, archives. Does not deploy.
- **Executor node (Surface / its successor)**: pushes to the subtract.ing web root. That push is the canonical publish.
- **GitHub**: mirror only — never the authority, never load-bearing.
