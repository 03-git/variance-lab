Plan only — nothing executed.

## 0. Reflex checks before anything
- **reflex.2 / no invented formats:** the signature is an SSH detached signature (`ssh-keygen -Y sign`/`-Y verify`, namespace `file`). No custom format, no PGP, no homemade scheme.
- **reflex.5:** the `.txt` is load-bearing → it is canonical **under the signing key's domain (subtract.ing)**. GitHub (or any git host) is a mirror only; a verifier must never treat it as authoritative.
- **reflex.4 + loop.before:** before touching the canonical tree, verify the current manifest still has a good signature and surface any unsigned drift in staging.

## 1. Draft (Rousseau — this node, canonical archive for `~/human/`)
- Write the file into the canonical tree: `~/human/<area>/foo.txt` (Write/Edit, or `vim`).
- Record the digest for the manifest: `shasum -a 256 ~/human/<area>/foo.txt`.
- This is agent work. The agent **prepares**; it does not sign and does not self-authorize the publish.

## 2. Pre-publish verification (Rousseau, agent)
```
git -C ~/human log --oneline -5
git -C ~/human status
ssh-keygen -Y verify -f ~/human/allowed_signers -I jnous -n file \
  -s ~/human/MANIFEST.sig < ~/human/MANIFEST
```
Good signature + clean/expected status → proceed to the gate. Drift → stop, surface it, human decides (loop.before.3).

## 3. The human gate — signing (governor only)
Only **new signing** is a human gate. The agent stops here and hands the commands over:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/human/<area>/foo.txt   # -> foo.txt.sig
# append entry to MANIFEST: path, sha256, sig filename
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/human/MANIFEST          # -> MANIFEST.sig  (loop.after.1/.2)
```
Signing key principal: `jnous`. `~/human/allowed_signers` must contain `jnous ssh-ed25519 AAAA…` (governor adds the line if it's a new key — also a signing-domain gate).

## 4. Publish (infra work — no gate, already-signed artifacts)
- **Rousseau pushes** to the subtract.ing origin: `rsync`/`scp` the bundle — `foo.txt`, `foo.txt.sig`, updated `MANIFEST`, `MANIFEST.sig`, `allowed_signers` — to whatever serves `https://subtract.ing/…`. Rousseau is the canonical archive node + governor workstation; it is the node that pushes canonical. (If the deploy is wired to run from Surface, Surface executes the same push — Rousseau drafts, Surface executes; still no gate, the artifact is already signed.)
- **Git mirror push** (`git -C ~/human commit … && git push <github> main`) is allowed but explicitly mirror-only.
- **Acer/Media does NOT push** — not formation, warm-backup/service tier only; it may cache subtract.ing as a downstream mirror, nothing more. **Emile does not publish canonical** — it's a reasoning/execution offload, not the publisher.

## 5. How a stranger verifies it a year later
Everything needed is fetched from the **signing key's domain**, not the git host:
```
curl -fsSLO https://subtract.ing/<area>/foo.txt
curl -fsSLO https://subtract.ing/<area>/foo.txt.sig
curl -fsSLO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s foo.txt.sig < foo.txt
```
Exit 0 + `Good "file" signature for jnous` ⇒ authorship confirmed.

Corroboration (optional but recommended):
```
curl -fsSLO https://subtract.ing/MANIFEST
curl -fsSLO https://subtract.ing/MANIFEST.sig
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST
shasum -a 256 foo.txt    # must match the MANIFEST entry
```
The `jnous` pubkey in `allowed_signers` should be cross-checked against an independent channel published under the same domain (e.g. a DNS TXT record on subtract.ing or a prior signed manifest in the chain) — that's what makes "a stranger" able to trust the principal, not just the math. If the GitHub mirror disagrees with subtract.ing, subtract.ing wins (reflex.5).

## Authority boundaries, summarized
- **Agent (Claude/Rousseau):** drafts the `.txt`, stages it, computes digests, drafts the manifest entry, prepares and runs the *push* of already-signed artifacts. Cannot sign, cannot decide to publish.
- **Human (governor):** runs `ssh-keygen -Y sign`, owns the private key, owns `allowed_signers` additions, makes the sign/continue/abort call at loop.before.3. The signature is what proves authorship — the agent prepares, the human signs.
- **Machines:** Rousseau = canonical push (and Surface may execute the deploy step). Acer/Media and Emile = no canonical push. Git host = mirror, never authority.
