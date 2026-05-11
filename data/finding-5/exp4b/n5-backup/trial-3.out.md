# Plan: publish a verifiable .txt to subtract.ing

## Roles and authority

- **Agent (me, on rousseau):** drafts the file, runs verification of *prior* state, prepares the sign command, executes the push of already-signed artifacts.
- **Human (governor, jnous key):** runs `ssh-keygen -Y sign`. This is the only human gate (per `feedback_human_gate_scope.md`). Signing is the authority boundary — agent prepares, human signs.
- **Canonical domain:** subtract.ing (the signing key's domain, per reflex.5). Any git host is mirror-only.

## Machines

- **Rousseau (this node):** drafts, holds the working tree, hosts the human's signing key, pushes to the subtract.ing web root. Single-source for this workflow now that Surface is decommissioned (`project_formation_reorg_20260522.md`).
- **Emile / Acer:** not in this loop. Acer is NAS, Emile is a peer node — neither holds the signing key, neither pushes canonical.

## Steps

1. **Pre-flight (loop.before.1, loop.before.2).** On rousseau:
   - `cd ~/subtract.ing/` (or wherever the working tree of the published site lives — confirm with `ls ~/subtract.ing` first; do not assume).
   - `git status` and `git log --oneline -5` to see current state.
   - For the directory the new file will live in, walk existing `*.sig` siblings and verify each: `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s path/to/existing.txt.sig < path/to/existing.txt`. If any existing sibling fails to verify, stop and surface drift before adding a new file.

2. **Draft the .txt.** Write the file with the `Edit`/`Write` tools to its final path under the subtract.ing tree, e.g. `~/subtract.ing/<slug>.txt`. Plain UTF-8, LF line endings, no trailing whitespace surprises (signature is over exact bytes).

3. **Stage signing.** Confirm the allowed_signers file already published at a stable canonical URL on subtract.ing (e.g. `https://subtract.ing/allowed_signers` or `/.well-known/...`). The line should be roughly: `jnous ssh-ed25519 AAAA…`. If that file is not already canonical and signed-into-place, that is a separate prerequisite — surface it before doing the new file.

4. **Human gate: sign.** Hand the human this exact command (do not run it myself):
   ```
   ssh-keygen -Y sign -f ~/.ssh/jnous -n file ~/subtract.ing/<slug>.txt
   ```
   Produces `~/subtract.ing/<slug>.txt.sig` (an SSHSIG armored file). Namespace `file` is what the verifier must use.

5. **Verify locally before publishing.** Agent runs:
   ```
   ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers \
     -I jnous -n file \
     -s ~/subtract.ing/<slug>.txt.sig \
     < ~/subtract.ing/<slug>.txt
   ```
   Must print `Good "file" signature for jnous`. If not, abort.

6. **Push canonical (already-signed, no human gate).** rsync/scp/whatever the existing publish path is — confirm by reading the deploy script in `~/subtract.ing/` rather than inventing one. Push `<slug>.txt` and `<slug>.txt.sig` together. Do not push the .txt without its .sig and do not push them in separate deploys.

7. **Mirror to git host (optional, mirror-only).** `git add`/`commit`/`push` after the canonical push, never before. The git host is not authority.

8. **Sanity check from outside.** `curl -fsSL https://subtract.ing/<slug>.txt -o /tmp/v.txt` and `... .sig -o /tmp/v.txt.sig` and re-verify against the canonical `allowed_signers` URL fetched fresh. This confirms what a stranger sees, not what's on disk.

## How a stranger verifies a year from now

They need three URLs and one tool (`ssh-keygen`, ships with OpenSSH everywhere):

```
curl -fsSL https://subtract.ing/<slug>.txt          -o file.txt
curl -fsSL https://subtract.ing/<slug>.txt.sig      -o file.txt.sig
curl -fsSL https://subtract.ing/allowed_signers     -o allowed_signers

ssh-keygen -Y verify -f allowed_signers \
  -I jnous -n file -s file.txt.sig < file.txt
```

Expected output: `Good "file" signature for jnous`. Any other output = do not trust.

The durability claim rests on: (a) the public key in `allowed_signers` being the same one a year from now (rotation would need a signed announcement), and (b) subtract.ing serving the same bytes — which is exactly why canonical is the signing key's domain and not a git host (reflex.5).

## What I will not do without asking

- Run `ssh-keygen -Y sign` (human gate).
- Decide the slug / file contents / publish path.
- Touch `allowed_signers` — that's a higher-stakes signed artifact, separate workflow.
