## Plan: publish a signed `.txt` to subtract.ing

### 0. Reflex check before touching anything
- **reflex.2 / format:** don't invent a signature format. `ssh-keygen -Y sign` emits SSHSIG (armored `-----BEGIN SSH SIGNATURE-----`), and `ssh-keygen -Y verify` consumes exactly that. That round-trip is the whole mechanism — nothing else gets built.
- **reflex.5 / canonical domain:** the authoritative copy lives under the signing key's domain (the host serving `https://subtract.ing`). GitHub or any git remote is a **mirror only** and does not establish authorship.
- **boundary / authority:** the agent (me, on Rousseau) *prepares* the file and the manifest. **The human runs the `ssh-keygen -Y sign` command.** New signing is the human gate (per `feedback_human_gate_scope`). Pushing already-signed bytes between nodes afterward is plain infra and I can do it.

### 1. Draft — Rousseau
- Author the file in the subtract.ing working tree: `~/subtract.ing/<name>.txt`.
- Keep it final-form before signing; a signature over a draft you'll edit is worthless. Verify byte content (`wc -c`, visual read) — no trailing-newline surprises, because the signature covers exact bytes.

### 2. Sign — Rousseau, human runs it (human gate)
The machine that holds the private signing key is Rousseau (governor's workstation). The governor, not the agent, runs:
```
ssh-keygen -Y sign -f ~/.ssh/<subtract_signing_key> -n file ~/subtract.ing/<name>.txt
```
- `-n file` = the SSHSIG namespace; it must be byte-identical at verify time.
- Output: `~/subtract.ing/<name>.txt.sig`.

### 3. Verify locally before publishing — Rousseau (reflex.4, loop.before.1)
Confirm with a live read, don't assume the sign worked:
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers \
  -I jnous@subtract.ing -n file \
  -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt
```
Expect: `Good "file" signature for jnous@subtract.ing`. If `allowed_signers` doesn't yet contain the signing key's public line, add it:
```
jnous@subtract.ing namespaces="file" ssh-ed25519 AAAA...    # optionally valid-after=..., valid-before=...
```

### 4. Update + sign the manifest — Rousseau (loop.after.1, loop.after.2)
- Append `<name>.txt`, principal `jnous@subtract.ing`, and date to `~/subtract.ing/MANIFEST` (or whatever the existing manifest file is).
- Re-sign the manifest the same way: `ssh-keygen -Y sign -f … -n file MANIFEST` → `MANIFEST.sig`. The human runs this too.

### 5. Publish to the canonical origin — push happens from Rousseau
- Deploy the three artifacts — `<name>.txt`, `<name>.txt.sig`, updated `allowed_signers` (and `MANIFEST` + `MANIFEST.sig`) — to the host that serves `https://subtract.ing`, via `rsync -av` / `scp` over the configured SSH alias. This step is post-signing infra; agent may execute.
- Git mirror (GitHub or similar): `git add <name>.txt <name>.txt.sig allowed_signers MANIFEST MANIFEST.sig && git commit && git push`. This is the **mirror**, explicitly not the authority — but the dated commit/tag is useful as an independent timestamp (see step 7).

### 6. Which machines do *not* act here
- **Emile, Media:** pull-mirror nodes. They receive content; they never push canonical content upstream and never originate the signature.
- **The agent:** never runs `ssh-keygen -Y sign`. Prepares, verifies, pushes signed bytes — does not sign.
- **The git host:** stores a copy; carries zero authority. A verifier who only checks GitHub has verified nothing about canonicity.

### 7. How a stranger verifies it, a year out
On any machine with OpenSSH:
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file -s <name>.txt.sig < <name>.txt
```
Success line: `Good "file" signature for jnous@subtract.ing`. That proves the holder of the `jnous@subtract.ing` private key signed exactly those bytes.

Two caveats the verifier should understand, and that the publication design must cover:
- **Trust anchor:** `allowed_signers` is served from the same domain as the content — that's the reflex.5 model (canonical under the signing key's domain). To make it robust to a single mutable endpoint, the public-key fingerprint should also be cross-published with its own timestamp: the GitHub mirror's commit/tag history, a signed git tag, or an SSHFP/TXT DNS record. A year from now the verifier compares the key in `allowed_signers` against that independently-timestamped record.
- **The "a year ago" part:** SSHSIG carries no timestamp. The date of authorship is established by an external dated artifact — the git commit/tag that introduced `<name>.txt.sig`, or an archive snapshot — not by the signature itself. If key rotation is expected, the `allowed_signers` entry should carry `valid-after`/`valid-before` so an old signature still verifies against the key that was current when it was made.

### Summary of authority boundaries
| Action | Who/where |
|---|---|
| Draft `.txt` | agent, Rousseau |
| `ssh-keygen -Y sign` (file + manifest) | **human**, Rousseau (key holder) |
| local `ssh-keygen -Y verify` pre-publish | agent, Rousseau |
| push to subtract.ing origin | agent, from Rousseau |
| push to git mirror | agent, from Rousseau — mirror only |
| Emile / Media | pull only, never push canonical, never sign |
| verifier | anyone, anywhere, with `ssh-keygen -Y verify` |
