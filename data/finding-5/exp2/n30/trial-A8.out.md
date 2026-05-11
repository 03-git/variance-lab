# Plan: publish a verifiable `.txt` to subtract.ing

## Reflex checks first
- **reflex.2 (memory→signature):** the format is SSHSIG via `ssh-keygen -Y sign` / `-Y verify`. No new format invented; it's already verifiable by any stranger with OpenSSH ≥ 8.1.
- **reflex.5 (canonical→signing domain):** the canonical copy lives at `https://subtract.ing/<name>.txt`. GitHub or any other host is mirror-only and carries no authority.
- **reflex.4 (action→verification):** before touching the published manifest, verify its current signature with a live read.

## 1. Draft — Rousseau (this machine)
- Author the file under the canonical human-work tree: `~/human/<area>/<name>.txt`.
- This is `authority.unsigned` — a suggestion only. Nothing downstream acts on it yet.
- Compute the digest the manifest will record: `sha256sum ~/human/<area>/<name>.txt`.

## 2. Pre-sign loop (loop.before) — Rousseau prepares, governor decides
- `curl -fsSL https://subtract.ing/MANIFEST` and `...MANIFEST.sig`, then
  `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST` — confirm the live manifest is currently signed and surface any drift.
- Present to the governor: the new file, its sha256, the manifest diff. Governor decides: sign / continue / abort. **This is the human gate** (`boundary`: the agent prepares, the human signs).

## 3. Sign — governor only (human gate)
Governor runs, on the machine holding the `jnous` private key:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file ~/human/<area>/<name>.txt
```
→ produces `<name>.txt.sig`. The agent does **not** run this and does not hold the key. (`authority.source` = the human; the signature is what proves it.)

Ensure `allowed_signers` already contains the line and is itself published at `https://subtract.ing/allowed_signers`:
```
jnous namespaces="file" ssh-ed25519 AAAA...   # jnous public key
```
If not present, that file is updated and re-signed in the same gated step — a stranger can only verify if this file is reachable under the signing domain.

## 4. Update + sign the manifest (loop.after)
- Append `<name>.txt  <sha256>` to `MANIFEST` (loop.after.1).
- `ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file MANIFEST` → `MANIFEST.sig` (loop.after.2). Also governor-only.

## 5. Push to the canonical origin — Surface, not Rousseau
- Per the formation split ("Rousseau drafts, Surface executes"), Rousseau hands the four artifacts (`<name>.txt`, `<name>.txt.sig`, updated `MANIFEST`, `MANIFEST.sig`, plus `allowed_signers` if changed) to **Surface**, which holds deploy access to the subtract.ing web origin.
- Surface publishes them to the document root (e.g. `rsync`/`scp` to the origin, or whatever the site's deploy path is). **Rousseau does not push to subtract.ing.**
- Pushing already-signed artifacts is infra work, not a human gate — Surface does it without re-prompting.
- Optional: mirror the same files to the GitHub repo. Mirror-only; if it diverges from subtract.ing, subtract.ing wins.

## 6. Post-publish live read
From Rousseau: `curl -fsSL https://subtract.ing/<name>.txt | sha256sum` — confirm it matches the manifest entry and the signed bytes. Don't assert "published" until this read passes (reflex.4).

---

## How a stranger verifies, a year later
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
Expected: `Good "file" signature for jnous with ED25519 key SHA256:...`

Then the trust-anchor step (the part that makes it meaningful, not circular): cross-check that `SHA256:...` fingerprint against an independent channel — the key fingerprint as published in `governance.conf` lineage / a prior signed artifact / wherever `jnous` has previously committed it. If the fingerprint matches and `-Y verify` passes, authorship holds regardless of what GitHub, the CA, or the hosting provider did in the intervening year — the signature is over the file bytes, not the transport.

Optionally also fetch `MANIFEST` + `MANIFEST.sig`, verify the manifest signature the same way, and confirm `sha256sum <name>.txt` appears in it — that ties the file into the signed corpus rather than standing alone.

## Authority boundaries in play
- **Draft, hash, stage, write the verify command, run live reads:** agent / Rousseau — reversible, no gate.
- **`ssh-keygen -Y sign` (file, manifest, allowed_signers):** governor only — new signing is the human gate; the agent never holds `id_ed25519_jnous`.
- **Push signed artifacts to subtract.ing:** Surface — execution machine; not a gate, but not Rousseau either.
- **subtract.ing = canonical**, git host = mirror; if they disagree the signing-domain copy is authoritative (reflex.5).
