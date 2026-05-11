## Plan — publish a verifiable `<name>.txt` to subtract.ing

### 0. Pre-flight (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, node state before anything.
- Verify the *current* canonical manifest before touching the webroot:
  `ssh-keygen -Y verify -f ~/.subtract/allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST`
- Surface any unsigned drift in the staging tree / webroot. Governor decides: sign, continue, or abort. The agent does not proceed past unresolved drift.

### 1. Draft — agent prepares, on rousseau (node 01)
- Write the file at its canonical staging path under the signing domain's tree (e.g. `~/subtract.ing/runtime/<name>.txt`; confirm the actual webroot source dir from audit-health, don't assume). Plain UTF-8, LF line endings, trailing newline.
- This is a reversible staging write — no permission gate.

### 2. Sign — human gate, governor only, key `jnous`
- The agent does **not** run this. Prepare the command for the governor and warn first if a passphrase/agent popup will fire:
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/runtime/<name>.txt`
  → emits `<name>.txt.sig` (armored `-----BEGIN SSH SIGNATURE-----`).
- Namespace is the stock `file` — per reflex.2, don't invent a format `ssh-keygen -Y` can't already verify.
- This is the only step that confers authority. The signature is the proof, not the agent.

### 3. Verify locally before publishing — agent
- `ssh-keygen -Y verify -f ~/.subtract/allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt`
  must print `Good "file" signature for jnous` and exit 0. Anything else → stop, do not publish.
- `shasum -a 256 <name>.txt` — record the digest.

### 4. Manifest (loop.after.1 / .2)
- Append `<name>.txt` + its SHA256 to the canonical manifest under the signing domain.
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file MANIFEST` (second and last human gate).

### 5. Publish — rousseau pushes, nothing else does
- subtract.ing is served from node 01 (rousseau, the `subtract→m1studio:8087` endpoint). The canonical push happens here: place `<name>.txt`, `<name>.txt.sig`, updated `MANIFEST`, `MANIFEST.sig`, and the published `allowed_signers` into the webroot.
- **Emile** is a pull-mirror — it does not push canonical content. **Media (acer1660ti)** is service infra + warm backup tier, not formation canonical — it does not push. **GitHub / any git host** is mirror-only (reflex.5): it may receive a copy, but the canonical address is `https://subtract.ing/<name>.txt` and the git URL must never be presented as the source of truth.
- Confirm with a live read (reflex.4): `curl -fsSL https://subtract.ing/<name>.txt | shasum -a 256` matches step 3, and `curl -fsSL https://subtract.ing/<name>.txt.sig` returns the armored signature.

### 6. How a stranger verifies it a year later
1. `curl -fsSL https://subtract.ing/<name>.txt -o f.txt`
2. `curl -fsSL https://subtract.ing/<name>.txt.sig -o f.txt.sig`
3. `curl -fsSL https://subtract.ing/allowed_signers -o allowed_signers` — fetched from the **signing domain itself** over TLS, not from a git mirror (reflex.5). The `-I` identity used below must match the principal listed in that file (`jnous`, or `jnous@subtract.ing` — whichever the file actually carries).
4. `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s f.txt.sig < f.txt`
   → `Good "file" signature for jnous`, exit 0 ⇒ the holder of the `jnous` key authored exactly these bytes.
5. Corroborate: the file's SHA256 appears in `MANIFEST`, and `MANIFEST.sig` verifies the same way; subtract.ing's TLS chain is valid; the `allowed_signers` key fingerprint matches any out-of-band copy the verifier already trusts (the chain of trust is the key, not the hosting).

### Authority boundaries, one line
The agent on rousseau drafts, verifies, updates the manifest text, and pushes already-signed bytes; the governor's two `ssh-keygen -Y sign` invocations (file + manifest) are the only authority-conferring acts; rousseau is the sole canonical publisher; Emile, Media, and GitHub are mirrors and never the source of truth.
