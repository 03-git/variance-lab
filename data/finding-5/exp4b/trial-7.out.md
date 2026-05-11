# Plan: publish a verifiable `.txt` to subtract.ing

Nothing below is executed. Authority model: the agent (this node) *prepares*; the human (governor) *signs*. Only new signing is the human gate — staging writes and pushing already-signed bytes are infra the agent does without asking.

## 0. Pre-flight (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds.
- Verify the currently-published manifest still has a good signature before touching anything:
  `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST`
- Surface any unsigned drift in the webroot working copy (`git status` in the subtract.ing canonical checkout on rousseau). Governor decides: sign / continue / abort.

## 1. Stage the file — agent, on rousseau (reversible, no gate)
- Write the new file into the **canonical webroot working copy on rousseau** (node 01 is canonical for formation content; `~/human/` and the subtract.ing checkout live here, Surface only pulls).
- Normalize bytes so the signature stays stable for a year: UTF-8, LF line endings, single trailing newline. After this, the file's bytes are frozen — any later re-save that changes whitespace invalidates the signature.

## 2. Sign — HUMAN GATE (governor only; reflex.2, boundary, authority.*)
Agent hands governor the exact command; agent does **not** run it:
```
ssh-keygen -Y sign -f ~/.ssh/jnous -n file <name>.txt
```
→ produces `<name>.txt.sig` (SSHSIG armored). `jnous` is the formation signing key; the namespace `file` must match what the verifier uses.

If `allowed_signers` doesn't already publish the `jnous` principal → its `ssh-ed25519 AAAA…` pubkey line, that line gets added now and the file re-published in step 4. Do **not** give the `jnous` entry a `valid-before` date inside the next year, or a stranger verifying in a year fails.

## 3. Update + re-sign the manifest (loop.after.1, loop.after.2)
- Append `<name>.txt  <sha256>` to `MANIFEST`.
- Governor re-signs: `ssh-keygen -Y sign -f ~/.ssh/jnous -n file MANIFEST` → `MANIFEST.sig`.

## 4. Publish — rousseau pushes, nothing else does (reflex.5)
- **Rousseau (01)** is the only node that pushes canonical. `rsync`/`scp` the four artifacts — `<name>.txt`, `<name>.txt.sig`, `MANIFEST`, `MANIFEST.sig` (and `allowed_signers` if changed) — to the subtract.ing webroot served under the `subtract.ing` TLS cert. *Canonical lives under the signing key's domain.*
- **Surface** does not push — it pulls from rousseau. **Emile** does not push canonical. **Acer/Media** is service infra + warm backup; it mirrors, it is never the source.
- A GitHub (or any git host) copy is fine but **mirror-only** — the commit, signed or not, is not the authority. The `.sig` file under subtract.ing is.

## 5. How a stranger verifies it (a year later)
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
Exit 0 + `Good "file" signature for jnous` ⇒ authentic (authority.signed). Optional integrity cross-check: recompute `sha256` of the `.txt`, confirm it matches the line in `MANIFEST`, and verify `MANIFEST.sig` the same way.

**Trust chain:** `allowed_signers` is trustworthy because it is served under the `subtract.ing` domain — the domain *is* the binding to the signing key (reflex.5). The verifier needs no git history, no GitHub account, no contact with the formation — just HTTPS and `ssh-keygen -Y verify`, both of which behave identically in a year (SSHSIG is a stable format).

**Failure modes to avoid:** signing from any key other than `jnous`; the agent running `ssh-keygen -Y sign` itself (boundary violation); treating the GitHub mirror as canonical; re-saving the `.txt` after signing; an expiring `allowed_signers` entry.
