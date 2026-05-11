## Plan: publish a verifiable `.txt` to subtract.ing

### 0. Reflex checks before anything
- **reflex.2 (memory→signature):** the format is already decided — don't invent one. `ssh-keygen -Y sign` / `-Y verify` (SSHSIG) is the primitive, it's on every node, detached `.sig` sidecar, no clock/network dependency. No GPG, no custom HMAC, no `.asc`.
- **reflex.5 (canonical→signing domain):** the canonical home is subtract.ing itself (the domain that also serves `governance.conf.universal.txt`). GitHub/any git host is **mirror-only** and a verifier must not treat it as authoritative.
- **Session ground truth:** `bash ~/scripts/audit-health.sh` first — confirm DNS, drive mounts, and that the subtract.ing deploy path/credential is intact before staging anything.

### 1. Draft (Rousseau, no gate)
- Author the file in the canonical human tree: `~/human/<area>/<name>.txt` on Rousseau (rousseau:~/human/ is canonical; Surface/Emile pull, they don't originate).
- Plain UTF-8 text. Freeze the byte content before signing — any later edit invalidates the signature.

### 2. Ensure the verifier-side key map exists
- An `allowed_signers` file must be published alongside content so a stranger can resolve the key:
  ```
  jnous ssh-ed25519 AAAA...governor-public-key...
  ```
- If it already exists in the subtract.ing web root, reuse it. If a new key is being introduced, that's itself human territory — surface it, don't fabricate the line.

### 3. Human gate — signing (governor only)
The agent prepares; **the human signs** (`boundary`, `loop.before.3`, "Human Gate Scope" — only *new signing* is the gate). Hand the governor the exact command; warn first if the key has a passphrase prompt:
```sh
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n subtract.ing ~/human/<area>/<name>.txt
# -> produces ~/human/<area>/<name>.txt.sig
```
(`-n subtract.ing` is the namespace; the verifier must use the same string.)

### 4. Agent verifies before acting (reflex.4 / loop.before.1)
Until `-Y verify` passes, the file is `authority.unsigned` → do not publish. Run:
```sh
ssh-keygen -Y verify -f allowed_signers -I jnous -n subtract.ing \
  -s ~/human/<area>/<name>.txt.sig < ~/human/<area>/<name>.txt
# expect: Good "subtract.ing" signature for jnous
```
Only on `Good ...` does this become `authority.signed` → act on it.

### 5. Publish (Rousseau pushes; Emile and the Surface terminal do not)
Pushing an *already-signed* artifact is plain infra, no gate ("Human Gate Scope"). The node that pushes is the one holding the subtract.ing deploy credential — **Rousseau** (primary workstation, canonical ~/human/). **Emile** is compute/memory offload, not a deploy origin. **Surface** is a governor terminal (and being decommissioned) — it never pushes canonical content.
- Push `<name>.txt`, `<name>.txt.sig`, and `allowed_signers` to the subtract.ing web root over the existing deploy path (scp/rsync to the server, or the static-site deploy step — whatever audit-health confirmed).
- Optional git-host mirror push afterward, explicitly labeled mirror-only, not canonical (reflex.5).

### 6. Close the loop (loop.after)
- `loop.after.1`: add `<name>.txt` + its `.sig` (and the file's SHA-256) to the session manifest in `~/human/sessions/`.
- `loop.after.2`: governor signs the updated manifest (`ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n subtract.ing manifest`) — second human gate. This chains the new file into the signed lineage.

### Authority boundaries in play
- **Human gates (2):** signing the `.txt` (step 3), signing the updated manifest (step 6). Nothing else.
- **No gate (reversible infra):** drafting, staging writes, the `-Y verify` check, scp/rsync of signed artifacts, the git mirror push.
- **Agent never holds a signing key.** Draft prepared on Rousseau ≠ authority; only `-Y verify` passing confers it.
- **Canonical = subtract.ing** (signing domain). Git host = mirror.

### How a stranger verifies, one year out
1. Fetch from **subtract.ing** (not the git mirror): `<name>.txt`, `<name>.txt.sig`, `allowed_signers`.
2. Anchor the key: it's served from the same TLS domain as `governance.conf.universal.txt` and matches the key used on prior signed manifests — trust root is the domain + the key's published history, not any single fetch.
3. Run:
   ```sh
   ssh-keygen -Y verify -f allowed_signers -I jnous -n subtract.ing \
     -s <name>.txt.sig < <name>.txt
   ```
   Expect `Good "subtract.ing" signature for jnous`.
4. SSHSIG is detached and self-contained — no expiry, no clock, no network call into the verify step. It returns the same result in a year. Optionally cross-check the file's SHA-256 against the signed session manifest to confirm it's the same byte sequence the governor attested.

Failure handling: if `claude -p`-style dispatch or the deploy push fails, one attempt then flag and stop — don't spiral on retries ("claude -p Is Human Gate"). If `-Y verify` fails at step 4, the publish does not happen.
