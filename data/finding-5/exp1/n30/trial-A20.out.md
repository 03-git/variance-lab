# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. This is the procedure.

## 0. Ground truth first
- `bash ~/scripts/audit-health.sh` on Rousseau — confirm subtract.ing DNS resolves, LEDGER NVMe mounted, no credential drift, `~/subtract.ing/` canonical tree present. Don't touch the canonical tree until this is clean.

## 1. Reflex check (name the primitive — reflex.2)
- Signing primitive already exists: `ssh-keygen -Y sign` / `ssh-keygen -Y verify`, namespace `file`, trust list `allowed_signers`. No new format is invented. Signing key = governor's `~/.ssh/id_ed25519`, identity string as it appears in `subtract.ing/allowed_signers` (e.g. `jnous`).
- Canonical lives under the signing key's domain — `https://subtract.ing/...` (reflex.5). Any git host is mirror-only, never the authority.

## 2. Draft — Rousseau (node 01) drafts
- Write the file into the canonical staging tree: `~/subtract.ing/<name>.txt` on Rousseau. Rousseau is the archive/canonical node; it drafts and holds, it does **not** push to the public origin.

## 3. Pre-act loop (loop.before)
- `git -C ~/subtract.ing log --oneline -5` and `git -C ~/subtract.ing status`.
- Verify the current manifest signature before modifying anything that depends on it:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I <identity> -n file -s ~/subtract.ing/MANIFEST.txt.sig < ~/subtract.ing/MANIFEST.txt`
- Surface any unsigned drift in `~/subtract.ing/` to the governor. Governor decides: sign / continue / abort. The agent stops here for the gate.

## 4. Human gate — governor signs (Claude does NOT run these)
New signing is the only hard human gate (boundary: the agent prepares, the human signs).
- `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt` → produces `~/subtract.ing/<name>.txt.sig`

## 5. Update + re-sign the manifest (loop.after.1 / loop.after.2)
- Agent prepares the manifest line: `<name>.txt  <sha256sum>  2026-05-10` appended to `~/subtract.ing/MANIFEST.txt` (the manifest's date line is the formation's authorship timestamp — SSH sigs carry no trusted time).
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST.txt` → new `MANIFEST.txt.sig`

## 6. Verify locally before anything leaves the node (reflex.4 — live read)
- `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I <identity> -n file -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt` → expect `Good "file" signature for <identity>`
- Same for `MANIFEST.txt`. Confirm `sha256sum <name>.txt` matches the manifest line.

## 7. Durability copies (infra, no gate)
- `rsync -a ~/subtract.ing/ acer1660ti:~/subtract.ing-mirror/` — Media warm backup tier (not authority, not public).
- Refresh the SDXC air-gap snapshot per the existing manifest-swap procedure.
- These are backups; none of them serve the public file.

## 8. Publish — Surface executes the push (not Rousseau, not Emile)
Pushing already-signed artifacts is infra work, but the public origin is externally visible, so confirm with the governor before the push.
- From Surface: pull the signed set from `rousseau:~/subtract.ing/` (`<name>.txt`, `<name>.txt.sig`, `MANIFEST.txt`, `MANIFEST.txt.sig`; `allowed_signers` already published).
- Deploy to the subtract.ing web origin via the existing deploy path (git push to the mirror the origin pulls, or rsync/scp to the origin docroot — whichever the origin uses).
- Emile does **not** push. Media does **not** push. Rousseau does **not** push. Surface is the executor.

## 9. Post-publish verification from outside
- `curl -fO https://subtract.ing/<name>.txt`, `curl -fO https://subtract.ing/<name>.txt.sig`, `curl -fO https://subtract.ing/allowed_signers`
- `ssh-keygen -Y verify -f allowed_signers -I <identity> -n file -s <name>.txt.sig < <name>.txt`
- Fetch `MANIFEST.txt` + `.sig`, verify, confirm the sha256 + date line.
- Optionally have the page archived (archive.org snapshot) as independent timestamp corroboration — corroboration only, the signed manifest is the canonical record.

## Authority boundaries (summary)
- **Human gate:** `ssh-keygen -Y sign` over the file and over the manifest. Only the governor runs these. The agent never holds or uses the private key.
- **Agent (Rousseau) may do without asking:** draft the file, compute hashes, prepare the manifest line, verify signatures, rsync to backup tiers, stage for Surface.
- **Ask before doing:** the public push to the subtract.ing origin (externally visible mutation).
- **Canonical authority:** the copy served under `https://subtract.ing/` (signing key's domain). Git mirrors are corroboration, never the source of truth.

## How a stranger verifies it a year from now
1. `curl -O https://subtract.ing/<name>.txt`
2. `curl -O https://subtract.ing/<name>.txt.sig`
3. `curl -O https://subtract.ing/allowed_signers`
4. `ssh-keygen -Y verify -f allowed_signers -I <identity-listed-in-allowed_signers> -n file -s <name>.txt.sig < <name>.txt`
   → `Good "file" signature for <identity>` means the holder of that SSH key signed exactly those bytes.
5. Cross-check: fetch `MANIFEST.txt` + `MANIFEST.txt.sig`, verify the manifest signature the same way, then confirm `sha256sum <name>.txt` equals the manifest's hash for that filename and read the dated line.
- **Trust root:** the public key in `allowed_signers` is authoritative because it is served under the signing key's own domain over TLS (reflex.5). The git mirror's commit date and any archive.org snapshot are independent timestamp corroboration, not the authority.
- **Known limit:** an SSH signature has no built-in trusted timestamp; "a year ago" is established by the signed, dated manifest plus external archive/mirror history, not by the `.sig` itself. If stronger time-proof is wanted, additionally publish an OpenTimestamps `.ots` over `sha256(<name>.txt)` — additive, optional, not part of the canonical record.
