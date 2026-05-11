## Plan: publish a verifiable `.txt` to subtract.ing

Primitive first (reflex.1 / reflex.2): the signature scheme is OpenSSH's `ssh-keygen -Y sign` / `-Y verify`. Nothing invented, no library, no git-host trust.

### 0. Pre-flight (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, creds, drives, node state. Don't proceed on assumptions.
- If this file supersedes an existing canonical file, verify the live signature first (reflex.4, loop.before.1):
  `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous -n file -s OLD.txt.sig < OLD.txt`
- Surface any unsigned drift to the governor (loop.before.2). Governor decides: sign / continue / abort (loop.before.3).

### 1. Draft — on Rousseau (this machine)
- Author the file in the canonical tree: `~/subtract.ing/runtime/…/NAME.txt` (confirm exact subdir from the repo layout, not memory). `~/human/` and `~/subtract.ing/` on Rousseau are canonical; everything else is a mirror.
- Agent writes the file and prepares the exact signing command. Agent does **not** sign.

### 2. Sign — human gate (boundary, authority.source)
This is the one real gate. Warn the governor first if the signing key is keychain-backed (macOS passphrase popup — feedback_warn_human_gates). Governor runs:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/runtime/…/NAME.txt
```
→ produces `NAME.txt.sig` (an SSH signature over namespace `file`, signer identity `jnous`).

### 3. Manifest (loop.after.1 / loop.after.2)
- Add `NAME.txt` + its SHA-256 to the canonical manifest in `~/subtract.ing/`.
- Governor re-signs the manifest the same way: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file MANIFEST`.
- Confirm `allowed_signers` (the public verification file mapping `jnous` → its public key) is already published at the site root; if not, it goes out in this push.

### 4. Push — Rousseau only
- **Rousseau pushes** to the subtract.ing web origin (the deploy path / rsync target identified by `audit-health.sh`). Canonical content lives under the signing key's domain — `https://subtract.ing/` — not a git host (reflex.5).
- Push the trio together: `NAME.txt`, `NAME.txt.sig`, updated+signed `MANIFEST` (and `allowed_signers` if changed).
- **Surface does not push** — it's the governor terminal / pull-mirror. **Emile does not push** — pull-mirror of `~/scripts`. **Media (acer1660ti) does not push** — warm-backup/mirror-only tier. Mirroring already-signed artifacts to those nodes afterward is just infra, no gate (feedback_human_gate_scope) — the signature travels with the file and re-verifies anywhere.
- GitHub or any git mirror, if updated, is explicitly **mirror-only** and not the authority a verifier should trust.

### 5. How a stranger verifies (a year later)
Fetch from the signing domain, not a mirror:
```
curl -sO https://subtract.ing/NAME.txt
curl -sO https://subtract.ing/NAME.txt.sig
curl -sO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s NAME.txt.sig < NAME.txt
```
Expected: `Good "file" signature for jnous`.

Trust chain the verifier is relying on:
- The `.sig` cryptographically binds the file bytes to the `jnous` public key — tamper-evident regardless of host.
- `allowed_signers` is the trust anchor: it's authoritative because it's served under subtract.ing (the signing key's own domain) and listed in the signed `MANIFEST`. A stranger who wants out-of-band confirmation cross-checks the `jnous` key fingerprint against any independent prior publication of it.
- Mirrors (git host, Media, Emile) can serve the same bytes; they can't forge the signature, and they're not where authority is claimed from.

### Authority boundaries in play
- **Human gate:** new signing only (steps 2–3). Agent prepares file + command; governor signs (boundary, authority.source).
- **No gate:** drafting, manifest edits pre-signing, pushing/mirroring already-signed artifacts (feedback_human_gate_scope, feedback_stop_asking_on_reversible).
- **reflex.4:** any superseded file gets a live `-Y verify` read before being touched.
- **reflex.5:** canonical = subtract.ing under the signing key; git is mirror-only — never cite the mirror as source.
- **Warn-before-gate:** flag the keychain/passphrase popup before the governor runs `ssh-keygen -Y sign`.

Open items to confirm from `audit-health.sh` before executing (don't assume): exact canonical subdir for the file, the site deploy/rsync target, and whether `allowed_signers` is already live at the root.
