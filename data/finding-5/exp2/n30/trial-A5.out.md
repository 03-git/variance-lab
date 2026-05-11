## Plan: publish a verifiable `.txt` to subtract.ing

### 0. Ground truth first
- `bash ~/scripts/audit-health.sh` on Rousseau. Read it. Confirm DNS for subtract.ing, the deploy path, and `~/.ssh/` state before assuming anything.
- **reflex.2 check:** the signature format is not invented — it's OpenSSH signatures via `ssh-keygen -Y sign` / `-Y verify`, namespace string `file`. Confirm `ssh-keygen -Y verify` can consume what `ssh-keygen -Y sign` emits (it can). No custom format.

### 1. Draft the file (Rousseau, agent does this — reversible staging write)
- Author into the canonical human tree: `~/human/pub/<name>.txt` (rousseau:~/human/ is canonical for formation human-authored work).
- Normalize bytes now, because the verifier checks bytes: UTF-8, LF line endings, single trailing newline. After this point the file is frozen — any later byte edit invalidates the signature.

### 2. Pre-sign loop (loop.before)
- `loop.before.1`: `ssh-keygen -Y verify` the existing `~/human/pub/MANIFEST` signature.
- `loop.before.2`: surface any unsigned drift in `~/human/pub/`.
- `loop.before.3`: governor decides — sign, continue, or abort. The agent stops here and presents; it does not sign.

### 3. Sign — HUMAN GATE
New signing is the human gate (`boundary`: the agent prepares, the human signs; `authority.source`: the human). Agent presents the exact command; governor runs it:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/human/pub/<name>.txt
# emits ~/human/pub/<name>.txt.sig  (-----BEGIN SSH SIGNATURE----- armored block)
```

### 4. Make authorship resolvable for a stranger — the `allowed_signers` file
A signature is worthless to a stranger without the trusted public key, served under the signing key's domain (`reflex.5`: canonical content is canonical under the signing key's domain).
- Publish `https://subtract.ing/.well-known/allowed_signers` (if not already there — if absent, publishing it is part of this task):
```
jnous valid-after="20260101",valid-before="20271231" ssh-ed25519 AAAA...governor@subtract.ing
```
- The `valid-before` window must cover the signing date and outlast the verifier's one-year horizon. If the signing key rotates inside that year, **add** the new key — never delete the old line, or every prior signature breaks.

### 5. Update + re-sign the manifest (loop.after)
```
sha256 ~/human/pub/<name>.txt   # record hash in ~/human/pub/MANIFEST
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n manifest ~/human/pub/MANIFEST   # HUMAN GATE again
```
Carry the new file + hash into the SDXC air-gap manifest set on the next `discover.sh`/refresh cycle.

### 6. Push — Rousseau pushes; others do not
The artifact is already signed, so the push is infra, not a gate — agent executes (`feedback_human_gate_scope`: moving already-signed artifacts is infra work).
- **Rousseau pushes.** It's the governor's workstation, the `~/human/` canonical node, the archive node. Deploy the three files — `<name>.txt`, `<name>.txt.sig`, and `allowed_signers` — to the subtract.ing web origin (e.g. `rsync -av ~/human/pub/<name>.txt ~/human/pub/<name>.txt.sig <subtract-origin>:/srv/subtract.ing/`, or commit+push to the repo the web host pulls). Serve raw bytes — no CRLF conversion, no trailing-newline rewrite, `Content-Type: text/plain; charset=utf-8`.
- **Emile (m2mini) does not push.** It's a dispatch/compute target (`ssh m2mini "claude -p"`), not a publish origin.
- **Media (acer1660ti) does not push.** Service infra (Jellyfin/*arr/Kiwix) + warm backup tier — not formation. Mirror only.
- **GitHub / any git host: mirror-only** (`reflex.5`). A mirror push for redundancy is fine, but it is explicitly *not* the canonical authority. The canonical copy is the one served under subtract.ing.
- **Surface** (governor terminal) could run the deploy, but the canonical content originates on Rousseau here; no reason to route through Surface.

### 7. How a verifier confirms the claim — a year from now
A stranger needs only OpenSSH and `curl`:
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/.well-known/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
Exit 0 with `Good "file" signature for jnous` ⇒ authentic. The chain: TLS to `subtract.ing` delivers `allowed_signers` (the signing key's own domain vouches for the key); the `.sig` is over the exact file bytes under namespace `file`; principal `jnous`'s validity window in `allowed_signers` covers the signing date.

Optional hardening for the one-year horizon: cross-sign `allowed_signers` itself, pin the key fingerprint in a second channel (DNS TXT, the governance file), and keep the `.sig` + hash in the signed `MANIFEST` so the file's integrity is attested in two places.

### Authority boundaries, summarized
- **Agent prepares:** drafts content, normalizes bytes, writes staging files, composes the exact `ssh-keygen` commands, runs the post-sign push (already-signed → infra), updates manifests.
- **Human signs:** every `ssh-keygen -Y sign` invocation. That signature — not the agent, not the git host — is the proof of authorship (`boundary`, `authority.signed`, `authority.source`).
- **Canonical = the signing key's domain** (subtract.ing). Git hosts are mirrors. Emile and Media never originate a publish.
