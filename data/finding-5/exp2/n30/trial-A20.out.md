# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. This is the sequence, the boundaries, and the verifier's check.

## 0. Ground truth first
On Rousseau: `bash ~/scripts/audit-health.sh` — read it before touching anything (DNS, drives, creds, node state). Then `cd ~/subtract.ing && git log --oneline -5 && git status && git pull`. Reconstruct state from the repo, not from this conversation (the conversation is unsigned).

## 1. Prepare — Rousseau (this node drafts, does not sign, does not push to production)
- Write the file at the canonical location: `~/subtract.ing/<name>.txt`. Content authored under `~/human/` workflow if it's human prose, then moved/copied into the subtract.ing tree — but the *canonical* copy is the one in `~/subtract.ing/` because that's the tree that deploys under the signing key's domain (reflex.5).
- `sha256sum ~/subtract.ing/<name>.txt` — record the digest.
- Verify the *current* manifest still carries a good signature before mutating it (loop.before.1–2):
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous@subtract.ing -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST`
  If that fails or the tree shows unsigned drift, stop and surface it — do not stack a new file on an unverified base.
- Add the new path + sha256 line to `~/subtract.ing/MANIFEST` (draft only — an unsigned manifest is a suggestion, authority.unsigned).
- `git add -n` / `git diff --staged` to show the governor exactly what changes. Stop here. Everything above is preparation; none of it is authority.

## 2. Sign — the human gate (governor only)
This is the irreducible step. The agent never runs `ssh-keygen -Y sign`; the signature is what proves authorship, and only the human holds the key (boundary; authority.source = the human).

Governor, on the machine holding the private key:
- `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt` → produces `~/subtract.ing/<name>.txt.sig`
- Re-sign the updated manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST` → `MANIFEST.sig`
- Confirm the new file's signature locally before it leaves the node:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous@subtract.ing -n file -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt`
  Expect: `Good "file" signature for jnous@subtract.ing with ED25519 key SHA256:…`

The `allowed_signers` file (`jnous@subtract.ing ssh-ed25519 AAAA…`) must already be in the tree and itself served from subtract.ing — that file is the trust root, and it lives under the signing key's domain, not on a git host.

Governor's three options at this gate (loop.before.3): sign, continue without signing (then it ships as non-canonical), or abort.

## 3. Push — Surface executes (Rousseau does not push to production)
Once the artifact + `.sig` are signed, moving them is just infra (human-gate scope covers *new signing* only, not propagation of already-signed bytes):
- Mirror to git: `git add <name>.txt <name>.txt.sig MANIFEST MANIFEST.sig && git commit -m "publish <name>.txt (signed jnous@subtract.ing)" && git push && git tag -s? ` — the git remote is **mirror-only**. A verifier who only inspects GitHub has not verified the claim.
- Canonical publish: deploy the tree to the host that serves `subtract.ing`'s docroot (rsync over ssh from Surface to the web node), so all three resolve over TLS:
  - `https://subtract.ing/<name>.txt`
  - `https://subtract.ing/<name>.txt.sig`
  - `https://subtract.ing/allowed_signers`
- Archive a copy of `<name>.txt` + `<name>.txt.sig` + the manifest line to the SDXC air-gap tier so the artifact survives a host migration within the year.

Rousseau's role ends at step 1; the governor's at step 2; Surface (or whatever node currently holds the deploy credential) does step 3.

## 4. How a stranger verifies it, a year out
```
curl -fsSLO https://subtract.ing/<name>.txt
curl -fsSLO https://subtract.ing/<name>.txt.sig
curl -fsSLO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file -s <name>.txt.sig < <name>.txt
```
A pass (`Good "file" signature for jnous@subtract.ing …`) means the bytes they hold were signed by the holder of the `jnous@subtract.ing` key. Independent corroboration of *which* key that is, in rough order of strength:
- the `allowed_signers` file served under `subtract.ing` itself (same domain as the content — reflex.5);
- an `SSHFP`/`TXT` record pinning the ed25519 key fingerprint in DNS, so the verifier has a path that doesn't depend on the web root;
- the `MANIFEST` (also signed) listing `<name>.txt`'s sha256, so a verifier can confirm the file wasn't swapped even if served from a mirror.

## Authority boundaries, condensed
- The `.txt` Rousseau drafts is **unsigned → suggestion only** (authority.unsigned). It does not become canonical by being committed or deployed — only by carrying a `.sig` that `ssh-keygen -Y verify` accepts (authority.signed).
- **Agent prepares, human signs** (boundary). Rousseau: write, hash, draft manifest, verify prior sigs, show the diff. Never `ssh-keygen -Y sign`.
- **Canonical lives under the signing key's domain.** subtract.ing serves the load-bearing copy; the git remote is a mirror. Don't tell the verifier to "check the repo."
- **Push ≠ gate.** Once signed, Surface propagating the artifact is ordinary infra, no further human approval needed.
- After the session: manifest is updated and signed (loop.after.1–2) — that's done in step 2, not deferred.
