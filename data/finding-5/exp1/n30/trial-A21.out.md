Plan only — nothing executed. (Note: `bash ~/scripts/audit-health.sh` is the normal session-start precondition; I'm not running it here per your "do not execute," but a real run starts there to confirm DNS/creds/drive state.)

## 0. Authority boundaries (fixed before any step)

- **Authoring node: Rousseau.** Canonical content for subtract.ing lives under the signing key's domain (reflex.5). The `.txt` is drafted here, in the `~/subtract.ing/` working tree (or `~/human/` if it's human-authored prose staged for promotion).
- **The agent prepares; the human signs** (`boundary`). Claude drafts the file, computes hashes, stages, and writes out the exact verify command. Claude does **not** run `ssh-keygen -Y sign`. New signing is the one hard human gate (`feedback_human_gate_scope`).
- **Publishing the *already-signed* bundle is infra, not a gate** — execute without further approval once the signature exists.
- **Git/web host is mirror-only** (reflex.5). GitHub Pages / whatever serves subtract.ing is a mirror; the canonical artifact is the signed file under the domain.
- **Push machine: Surface** (the execution node in the current formation — "Rousseau drafts, Surface executes"). Rousseau does **not** push to the public endpoint; it hands Surface the signed bundle. (After the 2026-05-22 reorg this collapses onto Rousseau, but today Surface pushes.)

## 1. Draft + provenance header (Rousseau, Claude)

- Write `~/subtract.ing/<name>.txt`.
- First lines of the file embed self-describing provenance, e.g.:
  ```
  # <name>.txt — subtract.ing
  # author: jnous
  # date: 2026-05-10
  # verify: ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
  ```
- The signature itself is **detached** (`.sig`), not inline — keeps the `.txt` byte-clean.

## 2. Reflex.2 check (format)

Before inventing anything: the format is `SSHSIG` — `ssh-keygen -Y sign` produces it, `ssh-keygen -Y verify` consumes it. No custom format. Pick one namespace string and keep it forever: use `file` (the OpenSSH convention) — record it in the manifest so the verifier knows what `-n` to pass.

## 3. loop.before (Rousseau, Claude — read-only)

- `git -C ~/subtract.ing log --oneline -5` and `git -C ~/subtract.ing status` — state what's there.
- Verify the **last** signed artifact still verifies (`ssh-keygen -Y verify ...` on the previous manifest) — confirms the chain isn't already broken.
- Surface any unsigned drift in the working tree.
- Hand the governor: the diff, the proposed `.txt`, and the exact sign command. Governor decides: sign / continue / abort.

## 4. Human gate — sign (governor only)

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt
```
→ produces `~/subtract.ing/<name>.txt.sig`. Key is `jnous`'s personal ed25519. Claude does not run this.

## 5. loop.after — update + sign the manifest (governor, with Claude prepping)

- Claude appends to `~/subtract.ing/MANIFEST` (or whatever the existing manifest file is): `<name>.txt`, its SHA-256, the namespace (`file`), the date, signer identity `jnous`.
- Governor re-signs the manifest:
  ```
  ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST
  ```
  → `MANIFEST.sig`. This is what chains the new file into the signed history.

## 6. Local verify before anything leaves Rousseau (Claude)

```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file \
  -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt
```
and the same against `MANIFEST` / `MANIFEST.sig`. If either fails → stop, do not publish.

Confirm `allowed_signers` (the line mapping `jnous` → the ed25519 public key) is present in the tree and will ship — without it a stranger has nothing to verify against.

## 7. Hand off + publish (Rousseau → Surface; Surface pushes)

- Rousseau: `scp` the bundle (`<name>.txt`, `<name>.txt.sig`, updated `MANIFEST`, `MANIFEST.sig`, `allowed_signers` if changed) to Surface — or Surface pulls from `~/subtract.ing/`. This is reversible infra; no gate.
- **Surface** runs the actual publish: `git -C <subtract.ing repo> add … && git commit && git push` to the web-host mirror, or whatever the deploy command is (`rsync` to the host). Result: `https://subtract.ing/<name>.txt`, `https://subtract.ing/<name>.txt.sig`, `https://subtract.ing/allowed_signers` all reachable.
- Rousseau does not push to the public endpoint.

## 8. Make the key independently anchorable (so "a stranger, a year later" works)

The signature only proves authorship if the verifier trusts the pubkey mapping. Belt-and-suspenders, all under the signing domain:
- `allowed_signers` served at a stable subtract.ing URL.
- The same ed25519 public key fingerprint also published somewhere a stranger can cross-check it against an independent channel — e.g. a `_subtract.ing` DNS TXT record, and/or the key already committed in earlier signed manifests (so the new sig chains to history the verifier may already have). The point: two independent paths to the same fingerprint, neither of which is "because the website said so."

## 9. How the verifier confirms it (a year later, no access to the formation)

1. `curl -O https://subtract.ing/<name>.txt`
2. `curl -O https://subtract.ing/<name>.txt.sig`
3. `curl -O https://subtract.ing/allowed_signers`
4. (trust step) compare the key in `allowed_signers` against the DNS TXT record / an older archived manifest / any other channel — confirm the fingerprint matches.
5. `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt`
   → `Good "file" signature for jnous with ED25519 key SHA256:…`
6. Optional: fetch `MANIFEST` + `MANIFEST.sig`, verify the same way, and confirm `<name>.txt`'s SHA-256 is the one listed — proves it was entered into the signed record, not slipped in later.

If step 5 prints `Good … signature`, the claim holds regardless of who's running the website by then — the authority is the signature, not the host (`reflex.5`, `authority.source`).

## What is *not* in the loop

- No "signed/unsigned" ceremony language anywhere except where `ssh-keygen -Y verify` literally runs (it does, steps 6 and 9).
- No subagents. If parallel work were needed it'd go to Emile via `ssh m2mini "claude -p …"` — not relevant here.
- No new signature format invented (reflex.2 satisfied: `SSHSIG`).
