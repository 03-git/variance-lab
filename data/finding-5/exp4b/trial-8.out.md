# Plan: publish a verifiable signed .txt to subtract.ing

## 0. Pre-flight (loop.before, reflexes)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, creds, drives, node state. Don't proceed if it's unhappy.
- Live-read current state (reflex.4): `curl -fsSL https://subtract.ing/MANIFEST` (or whatever the canonical manifest path is) and `curl -fsSL https://subtract.ing/allowed_signers` — confirm the last manifest signature verifies before adding to it:
  `ssh-keygen -Y verify -f <(curl -fsSL https://subtract.ing/allowed_signers) -I jnous -n file -s MANIFEST.sig < MANIFEST`
- Surface any unsigned drift in `~/human/` / `~/subtract.ing/` working tree (`git status`, `git log --oneline -5`). Governor decides: sign, continue, or abort. **This is a human gate — I stop here for a decision.**

## 1. Author the file (agent does this)
- Write `the-new-doc.txt` in the canonical tree on **Rousseau**: `~/subtract.ing/<path>/the-new-doc.txt` (canonical lives under the signing key's domain; the git host is a mirror only — reflex.5).
- `git add` + commit the *content* on Rousseau. No signing yet.
- Compute and record the digest for the manifest: `sha256sum the-new-doc.txt`.

## 2. Prepare signing inputs (agent prepares, does NOT sign — `boundary`)
- Confirm the identity line for `jnous` is present in the repo's `allowed_signers` file (format: `jnous ssh-ed25519 AAAA...`). If the file is new, draft it; adding it is still part of what the human signs.
- Draft the manifest entry: filename, sha256, date, pointer to `the-new-doc.txt.sig`.
- Hand off to the governor with the exact command to run (next step). I do not have the private key; `claude -p`-style autonomy does not extend to `ssh-keygen -Y sign`.

## 3. Sign (governor only — the human gate)
On the machine holding the `jnous` private key (governor's terminal, e.g. Surface — not a formation service node):
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file the-new-doc.txt
```
→ produces `the-new-doc.txt.sig`. Same for the updated `MANIFEST`:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file MANIFEST
```
Namespace `-n file` must be identical on sign and verify — pin it.

## 4. Verify locally before publishing (reflex.4 again)
```
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s the-new-doc.txt.sig < the-new-doc.txt
echo $?   # must be 0
```
Same for `MANIFEST.sig`. If non-zero, stop — do not push.

## 5. Push / publish
- **Canonical push**: the node with the subtract.ing web-root deploy credential pushes `the-new-doc.txt`, `the-new-doc.txt.sig`, the updated `MANIFEST` + `MANIFEST.sig`, and `allowed_signers` to the live document root under `https://subtract.ing/`. Pushing already-signed artifacts across nodes is infra, not a gate — execute it once the signatures verify. (`rsync -av --checksum` over ssh, or whatever the existing deploy path is — match what `audit-health.sh` and the repo's deploy script already use; don't invent one.)
- **Mirror push** (optional, non-authoritative): `git push` to the GitHub mirror. This is a mirror only — a verifier must not treat the git host as the source of truth (reflex.5).
- Post-publish live read: `curl -fsSL https://subtract.ing/the-new-doc.txt | sha256sum` and confirm it matches step 1, and re-run the step-4 verify against the *fetched* copies.

## 6. Close the loop (loop.after)
- Update the local manifest record + `~/human/sessions/` note with the sha256 and date.
- The manifest is already signed (step 3). Commit the signed state on Rousseau (canonical) and let Surface/mirror pull.

## Authority boundaries (summary)
- **Agent (Rousseau session)**: authors content, computes hashes, drafts manifest + allowed_signers entries, runs `ssh-keygen -Y verify`, performs the deploy push of already-signed bytes, runs live-read checks.
- **Governor only**: `ssh-keygen -Y sign` with the `jnous` private key. New signatures are the human gate; the agent prepares, the human signs.
- **Canonical vs mirror**: `https://subtract.ing/` (signing key's domain) is canonical. GitHub/git remotes are mirror-only.
- **Machine roles**: Rousseau drafts/holds canonical/deploys; the governor's own terminal (Surface today) signs; service nodes (Emile, Media/acer) are not in this path.

## How a stranger verifies it a year from now
1. Fetch the artifact and its signature from the **signing key's domain** (not GitHub):
   ```
   curl -fsSLO https://subtract.ing/the-new-doc.txt
   curl -fsSLO https://subtract.ing/the-new-doc.txt.sig
   curl -fsSLO https://subtract.ing/allowed_signers
   ```
2. Verify:
   ```
   ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s the-new-doc.txt.sig < the-new-doc.txt
   ```
   Exit status `0` and `Good "file" signature for jnous` = the file is authored by the holder of the `jnous` key, unchanged since signing.
3. Trust anchor for `allowed_signers`: it's served from `subtract.ing` itself (the domain *is* the claim of authority per the governance file). A cautious verifier cross-checks the `jnous` ed25519 public-key fingerprint against an independent publication of it (e.g. the key line committed in the manifest history / mirror) and against `https://subtract.ing/governance.conf.universal.txt`'s stated signing domain. Convergence of multiple mirrors is not proof — the domain-served `allowed_signers` is the reference.
4. Optional integrity cross-check: `sha256sum the-new-doc.txt` against the signed `MANIFEST` entry, and verify `MANIFEST.sig` the same way.

Nothing above is executed — this is the plan only. The first thing I'd actually do is run `audit-health.sh` and the step-0 live verify, then bring the signing command to you.
