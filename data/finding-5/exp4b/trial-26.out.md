## Plan: publish a verifiable `.txt` to subtract.ing

### 0. Reflex check before anything (reflex.2, reflex.1)
The primitive is `ssh-keygen -Y sign` / `ssh-keygen -Y verify` (SSH signatures over a file with a namespace). It already produces a format a stranger can verify with stock OpenSSH — do **not** invent a signing scheme, do not reach for GPG/minisign/a library wrapper. Confirm the existing runtime convention first:
- `ls ~/subtract.ing/` and `grep -rl "SSH SIGNATURE" ~/subtract.ing` to see how current `.sig` files are named
- read one existing `*.sig` + the published `allowed_signers` to lock the **identity string** and **namespace** already in use (likely `jnous@subtract.ing` and namespace `subtract.ing` or `file` — match it, don't fork it)

### 1. Author the file — on Rousseau (this node)
Rousseau is canonical for `~/human/` and holds the `~/subtract.ing/runtime/` tree and the governor's signing key. Write the new file there, e.g. `~/subtract.ing/<name>.txt`, UTF-8, final content. Once signed it is byte-frozen — any later edit needs a re-sign.

### 2. Pre-flight (loop.before.1–3)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS/drives/creds
- on the canonical path: `git log --oneline -5`, `git status`, `wc -l <name>.txt`
- verify the **current** canonical state isn't drifted:
  `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous@subtract.ing -n subtract.ing -s manifest.txt.sig < manifest.txt`
- surface any unsigned drift to the governor; **governor decides: sign / continue / abort.** The agent stops here for the gate.

### 3. Sign — human gate (boundary, authority.source, loop.before.3)
The agent prepares; the governor signs. Warn first that this prompts for the key passphrase, then the governor runs:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n subtract.ing ~/subtract.ing/<name>.txt
```
→ produces `~/subtract.ing/<name>.txt.sig`. The agent does not run this and does not hold the key.

### 4. Update + sign the manifest (loop.after.1–2)
Append `<name>.txt` and its `sha256` to the runtime manifest, then the governor re-signs the manifest the same way (`ssh-keygen -Y sign -n subtract.ing manifest.txt`). The manifest is the index that says "this file is part of canonical subtract.ing as of <date>."

### 5. Publish — Rousseau pushes; nothing else does (reflex.5)
Canonical content is served under the **signing key's domain**: `https://subtract.ing/`. Push from Rousseau to the subtract.ing web origin the trio:
- `<name>.txt`
- `<name>.txt.sig`
- `allowed_signers` (must already be live: line `jnous@subtract.ing ssh-ed25519 AAAA…` — the verifier's trust anchor)
- updated `manifest.txt` + `manifest.txt.sig`

Authority boundaries on machines:
- **Rousseau** — only node that signs and pushes canonical (key + runtime live here).
- **GitHub / any git host** — mirror only. You may `git push` the same commit there, but that copy is *not authoritative*; the plan and any README must say "canonical at subtract.ing, GitHub is a mirror."
- **Acer/Media** — may hold a warm backup copy of the signed bytes; does not publish, does not sign. (Also: no inference there — irrelevant here, but it's a backup tier, not an origin.)
- **Emile, Surface** — pull-mirrors. They never push canonical and never sign.
- Moving the *already-signed* bytes Rousseau→Acer→GitHub is plain infra — execute without asking. Only the new `ssh-keygen -Y sign` in step 3/4 is the human gate.

### 6. Post-publish live verification (reflex.4 — action to verification)
Don't trust the push reported success — do a live read:
```
curl -fsS https://subtract.ing/<name>.txt        -o /tmp/v.txt
curl -fsS https://subtract.ing/<name>.txt.sig    -o /tmp/v.txt.sig
curl -fsS https://subtract.ing/allowed_signers   -o /tmp/v.signers
ssh-keygen -Y verify -f /tmp/v.signers -I jnous@subtract.ing -n subtract.ing -s /tmp/v.txt.sig < /tmp/v.txt
```
Expect: `Good "subtract.ing" signature for jnous@subtract.ing`. Also confirm the served `sha256` matches the manifest entry. If verify fails, the publish is not done.

### How a stranger verifies it a year from now
Stock OpenSSH, no accounts, no trust in any git host:
```
curl -fsSO https://subtract.ing/<name>.txt
curl -fsSO https://subtract.ing/<name>.txt.sig
curl -fsSO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n subtract.ing -s <name>.txt.sig < <name>.txt
```
`Good "subtract.ing" signature for jnous@subtract.ing` ⇒ the file is exactly what the holder of the `jnous` key published, under the subtract.ing domain. The trust chain is: the `allowed_signers` line served from subtract.ing binds the identity to the public key; the `.sig` binds the key to these bytes; the manifest (also signed) binds the file into the canonical set with a date. If they only have the GitHub mirror, they run the identical command against the mirror's bytes plus `allowed_signers` fetched from subtract.ing — the signature still proves authorship; the domain copy is what makes it canonical rather than just present.

### What I would *not* do
- Not invent a signature/hash-chain format (reflex.2) — `ssh-keygen -Y` is the primitive.
- Not treat the GitHub copy as canonical (reflex.5).
- Not run `ssh-keygen -Y sign` myself or move the key (boundary).
- Not publish without the post-publish live `-Y verify` (reflex.4).
- Not add a new namespace/identity string when the runtime already has one.
