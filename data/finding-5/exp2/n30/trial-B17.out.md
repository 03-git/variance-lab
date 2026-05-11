# Plan — publish a verifiable `.txt` to subtract.ing

Output only. Nothing below is executed.

## 0. Ground truth first
- `bash ~/scripts/audit-health.sh` — read DNS, credentials, drive, node state. If subtract.ing DNS, the deploy credential, or the site working tree is red, stop here.
- If the target is the site repo: on the canonical path, `git status`, `git log --oneline -5`, `wc -l` on any file I'm about to touch. State what I observe before editing.

## 1. Author the file in the canonical location
- **reflex.5**: load-bearing content is canonical under the *signing key's domain*, not a git host. So the file is authored into the subtract.ing site working tree on Rousseau, e.g. `/Users/jns/subtract.ing/<slug>.txt`.
- Claude writes the content with `Write`/`Edit`. Claude does **not** sign and does **not** publish yet. An unsigned `.txt` is a draft (**authority.unsigned** → suggestion only).

## 2. The human signs — authority boundary
- **boundary / authority.source**: the agent prepares, the human signs; the signature proves authority. Claude never holds or uses the private key.
- Governor runs, on the machine holding the key:
  - `shasum -a 256 /Users/jns/subtract.ing/<slug>.txt` (record the digest)
  - `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file /Users/jns/subtract.ing/<slug>.txt`
  - → produces `/Users/jns/subtract.ing/<slug>.txt.sig` (SSH detached signature — **reflex.2**, the format `ssh-keygen -Y verify` can check).

## 3. Manifest + verifying key (loop.after.1, loop.after.2)
- Append to the site manifest: path, sha256, ISO date, signer key fingerprint (`ssh-keygen -lf ~/.ssh/id_ed25519`).
- Re-sign the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file /Users/jns/subtract.ing/MANIFEST` → `MANIFEST.sig`.
- Ensure the verifying key is published at a stable path under the domain so a stranger can fetch it — `https://subtract.ing/.well-known/allowed_signers` (or equivalent already wired), lines of the form:
  `jns@subtract.ing namespaces="file" ssh-ed25519 AAAA...`
  TLS + DNS is what binds the key to "subtract.ing"; the manifest signature chains the new file to that key.

## 4. Which machine pushes
- **Rousseau (01) pushes.** It is the governor's workstation, holds the site working tree and the deploy credential. The "publish" is the deploy step that updates the subtract.ing *origin* (the rsync/deploy script audit-health confirms is wired) — that static file under the domain is the authoritative artifact.
- A `git push` to a git host (GitHub/etc.) is **mirror-only** — **reflex.5**. It is not publication and verifiers must not be pointed at it as the source of truth.
- **Emile (m2mini)** does not push — it's an execution/offload node. **Surface** does not push — it's the governor terminal, not a deploy node. **Acer/NAS** does not push — not formation; it's a warm backup/service tier and at most receives a mirror after the fact.

## 5. How a stranger verifies, a year later
1. Fetch over HTTPS from subtract.ing: `<slug>.txt`, `<slug>.txt.sig`, `allowed_signers` (the `.well-known` copy), and `MANIFEST` + `MANIFEST.sig`.
2. Verify the file:
   `ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s <slug>.txt.sig < <slug>.txt`
   → expect `Good "file" signature for jns@subtract.ing`.
3. Verify the manifest the same way (`-s MANIFEST.sig < MANIFEST`) and confirm `<slug>.txt`'s sha256 (`shasum -a 256 <slug>.txt`) matches its MANIFEST entry.
4. Confirm the key is the domain's: `allowed_signers` is served under subtract.ing itself (TLS+DNS binding) and its fingerprint matches the one published in the governance/identity docs out of band. Root of trust is the **key**, not the host or any git mirror.
- Survives a year because: SSH signature format is stable and fully offline-verifiable; verification needs only static files, no live service or API; if the git mirror or even the host moves, the signature still checks against the key.

## Authority boundaries — summary
- **Claude (Rousseau)**: writes file content, edits the manifest text, may run the non-interactive deploy command if audit-health shows the credential present and authorized; surfaces the last signature state and any unsigned drift before acting (**loop.before**). Does not sign. Does not invent a signature format.
- **Governor (human, key holder)**: reviews content, runs `ssh-keygen -Y sign` for the file and the manifest, decides sign/continue/abort.
- Until step 2's signatures exist, the `.txt` is not published — it's a draft.
