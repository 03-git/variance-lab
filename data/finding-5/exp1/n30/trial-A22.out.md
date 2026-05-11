# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. This is the sequence, the boundaries, and the verifier's side.

## 0. Ground truth first
- `bash ~/scripts/audit-health.sh` — confirm DNS, drives, the subtract.ing working tree, and the signing key are all where they're supposed to be before touching anything. Don't assume node state from this conversation.

## 1. Reflex checks before drafting
- **reflex.2 (memory→signature):** the format is not invented. The artifact is signed with `ssh-keygen -Y sign` producing an OpenSSH armored signature (`-----BEGIN SSH SIGNATURE-----`), namespace `file`. A stranger verifies with `ssh-keygen -Y verify`. Confirm that's the format before writing a line of the file.
- **reflex.5 (canonical→signing domain):** canonical address is `https://subtract.ing/<name>.txt`. GitHub or any git host is **mirror-only** and never cited as the source of authority.
- **reflex.4 (action→verification):** before publishing over the existing tree, do a live read + `ssh-keygen -Y verify` on the current manifest signature so we're not stacking onto drifted state.

## 2. Draft (Rousseau — prepares, does not sign, does not push to web)
- Write the file in the canonical working tree: `~/subtract.ing/<name>.txt` (human-authored source under `~/human/` first if it originates there, then placed in the publish tree). Rousseau is the drafting/reasoning node and holds canonical `~/subtract.ing/`.
- Ensure the signer's public key is present and identity-bound in the **published** `allowed_signers` file in that tree, e.g.:
  `jnous@subtract.ing ssh-ed25519 AAAA...`
  If it isn't already published at `https://subtract.ing/allowed_signers`, that file ships in the same push — a stranger cannot verify without it. This is the actual linchpin for "verifiable by a stranger a year from now."
- Stage, show the governor: the file contents, the exact signing command, the diff to `allowed_signers` (if any), and the manifest entry that will be added.

## 3. Sign (human gate — governor only)
- **boundary / loop.before.3:** the agent prepares; the human signs. New signing is the one hard human gate. The agent does **not** run this:
  ```
  ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file <name>.txt
  ```
  → produces `<name>.txt.sig`. Governor runs it with the `jnous` key. The signature covers the content bytes, so it stays valid regardless of transport, host, or time.
- Governor's three options at the gate (loop.before): sign, continue without, or abort. Only "sign" proceeds to publish.

## 4. Publish (Surface executes; Rousseau does not push to the public host)
- Per "Rousseau drafts, Surface executes": Rousseau hands off the signed bundle (`<name>.txt`, `<name>.txt.sig`, updated `allowed_signers` if changed); **Surface** (governor terminal) does the push to the subtract.ing web host — `git push` to the deploy remote / `rsync` to the webroot, whatever the existing publish path is.
- Pushing an *already-signed* artifact across nodes / to the mirror is infra, not a gate — but the *canonical* publish target is the signing key's domain (subtract.ing), and the GitHub mirror push (if any) is explicitly secondary and not the cited address.
- Verify the live URL after deploy: `curl -fsSL https://subtract.ing/<name>.txt` and `…/<name>.txt.sig` and `…/allowed_signers` all return the bytes that were signed.

## 5. Close the loop (loop.after)
- Add `<name>.txt` to the relevant manifest, re-sign the manifest (`ssh-keygen -Y sign` — governor), commit. Refresh the SDXC/FROZEN air-gap tier if this file is load-bearing.

## How a stranger verifies, a year later
1. Download three files from `https://subtract.ing/`: `<name>.txt`, `<name>.txt.sig`, `allowed_signers`.
2. Run:
   ```
   ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file -s <name>.txt.sig < <name>.txt
   ```
3. Exit status `0` + `Good "file" signature for jnous@subtract.ing` = the file is exactly what the holder of the `jnous` key signed. Any byte change to the `.txt`, or a key not in `allowed_signers`, fails.
4. Trust root: `allowed_signers` is served from subtract.ing itself (the signing key's domain) — the binding of pubkey→identity lives under the same authority as the content. The GitHub mirror is not part of the trust path. Durability over a year requires only that subtract.ing keeps serving `allowed_signers` and the old pubkey is retained there even if a new one is added.

## Authority boundary summary
- **Agent (Rousseau session):** audits, drafts the `.txt`, stages the `allowed_signers` / manifest changes, writes out the exact commands, verifies existing signatures with `ssh-keygen -Y verify`, hands off the bundle. Does **not** sign. Does **not** push to the public host. Does **not** switch models.
- **Governor (human):** runs `ssh-keygen -Y sign` for the file and the manifest. This is the only step that confers authority.
- **Surface:** executes the publish push to subtract.ing.
- **GitHub / any git host:** mirror only — never the canonical citation.
