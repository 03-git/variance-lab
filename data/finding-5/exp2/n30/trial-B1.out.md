Plan only — nothing executed below. (Note: per CLAUDE.md I'd normally run `bash ~/scripts/audit-health.sh` first as ground truth; skipping per "do not execute.")

## 0. Pre-flight — `loop.before`
- `bash ~/scripts/audit-health.sh` — confirm DNS for `subtract.ing`, deploy creds, drive state.
- On the canonical content repo path: `git status`, `git log --oneline -5`, verify the **last** published artifact's signature with a live read (`reflex.4`):
  - `curl -fsSL https://subtract.ing/<previous>.txt -o /tmp/prev.txt`
  - `curl -fsSL https://subtract.ing/<previous>.txt.sig -o /tmp/prev.txt.sig`
  - `ssh-keygen -Y verify -f ~/.subtract/allowed_signers -I jns@subtract.ing -n file -s /tmp/prev.txt.sig < /tmp/prev.txt`
- Surface any unsigned drift in the working tree to the governor. Governor decides: sign / continue / abort. I do not proceed past unresolved drift.

## 1. Author the file (agent, on Rousseau)
- Write the document at the canonical path, e.g. `~/subtract.ing/<name>.txt` (the directory that maps to the web root — not `/tmp`).
- Deterministic content: fix encoding (UTF-8, LF), no trailing-whitespace churn. Record `sha256sum <name>.txt`.

## 2. Sign — authority boundary (`boundary`, `authority.*`, `reflex.2`)
- **The agent does not sign.** I prepare; the governor invokes the key. The signing primitive is `ssh-keygen -Y sign` (not an invented format — `reflex.2`).
- Governor runs, on the machine holding the private key:
  - `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt`
  - → produces `~/subtract.ing/<name>.txt.sig` (SSHSIG armored).
- The namespace `-n file` is fixed and must match what verifiers use.

## 3. Verify before publish (`reflex.4` — assertion-that-blocks is an action)
- `ssh-keygen -Y verify -f ~/.subtract/allowed_signers -I jns@subtract.ing -n file -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt`
- Must print `Good "file" signature`. If not, stop.

## 4. Update + sign the manifest — `loop.after.1/2`
- Append entry to the manifest (`~/subtract.ing/MANIFEST.txt` or equivalent): filename, sha256, date, signer identity.
- Re-sign the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST.txt` → `MANIFEST.txt.sig`.

## 5. Publish to the canonical domain (`reflex.5`)
- **Canonical = served under `subtract.ing`, controlled by the signing key's domain.** Push the four files (`<name>.txt`, `<name>.txt.sig`, `MANIFEST.txt`, `MANIFEST.txt.sig`) to the web host:
  - `rsync -av --checksum ~/subtract.ing/<name>.txt ~/subtract.ing/<name>.txt.sig ~/subtract.ing/MANIFEST.txt ~/subtract.ing/MANIFEST.txt.sig <web-host-from-~/.ssh/config>:/var/www/subtract.ing/`
- **Which machine pushes:** Rousseau (01) — governor workstation + archive node, holds the deploy path and creds.
- **Which machines do NOT push:** Emile (`m2mini`) is reasoning/exec offload only; the Acer NAS (`acer1660ti`) is mirror/backup tier, not formation, never serves canonical; Surface is a terminal, not a publisher. A git host (GitHub, etc.) is **mirror-only** — pushing there is allowed for redundancy but is *not* the authoritative copy and is not the verifier's source of truth.
- Confirm live: `curl -fsSI https://subtract.ing/<name>.txt` and re-run the step-3 verify against the *fetched* copies.

## 6. (Optional) timestamp anchoring
- Commit the signed files to the content repo and/or `ots stamp <name>.txt.sig` (OpenTimestamps) so "a year from now" there's independent evidence the signature predates disputes. The SSHSIG itself is time-independent — this only anchors *when*.

## 7. How a stranger verifies, a year later
1. Fetch the artifact and its detached signature from the canonical domain:
   - `curl -fsSL https://subtract.ing/<name>.txt -o <name>.txt`
   - `curl -fsSL https://subtract.ing/<name>.txt.sig -o <name>.txt.sig`
2. Obtain the allowed-signers list from the **same canonical domain** (e.g. `https://subtract.ing/allowed_signers` — a line like `jns@subtract.ing ssh-ed25519 AAAA...`). Trust roots in the domain, not in a git mirror (`reflex.5`).
3. Verify:
   - `ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s <name>.txt.sig < <name>.txt`
   - Expect: `Good "file" signature for jns@subtract.ing`.
4. Cross-check the file's `sha256sum` against the signed `MANIFEST.txt` (whose own `.sig` they verify the same way) — this catches a swapped file even if someone forgot a signature.
5. Optional: `ots verify <name>.txt.sig.ots` for the Bitcoin-anchored timestamp; or inspect the mirror repo's commit history for a corroborating date.

The claim holds for a stranger iff: (a) the key in `allowed_signers` at `subtract.ing` is still the governor's published key, and (b) `ssh-keygen -Y verify` passes with namespace `file`. No memory, no trust in the agent — only the signature (`authority.source`: the human; the signature proves it).
