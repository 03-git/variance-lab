Plan only — nothing executed. (Session-start note: I'd normally run `bash ~/scripts/audit-health.sh` first for ground truth; skipped here because the task says do not execute. Real run starts there.)

## 0. Reflex check (governance.conf reflex.2)
Before inventing any format: the signature format is **SSHSIG via `ssh-keygen -Y sign` / `-Y verify`** — already a verifiable primitive, no custom scheme. Signing domain = `subtract.ing` (reflex.5: canonical lives under the signing key's domain; GitHub/any git host is mirror-only).

## 1. Prepare (agent does this — Rousseau, the archive/workstation node)
- Author the file in the canonical working tree, e.g. `~/subtract.ing/<name>.txt`. `/tmp` is never authoritative.
- `git -C ~/subtract.ing status` / `git log --oneline -5` — confirm clean base, state observed timestamps.
- Compute digest for the manifest: `sha256sum <name>.txt`.
- Update the manifest (loop.after.1): append filename + SHA-256 + ISO-8601 date to `~/subtract.ing/MANIFEST` (the SSHSIG blob carries no timestamp, so the date must live in signed content for the "one year later" claim to mean anything).
- Ensure `~/subtract.ing/allowed_signers` exists and is web-served — lines of the form:
  `governor@subtract.ing ssh-ed25519 AAAA...`
  with `valid-after`/`valid-before` options on rotated keys so old signatures still verify a year out.
- Stage everything; do **not** commit-sign or push yet. authority.unsigned → this is a suggestion until the human acts.

## 2. Authority boundary — the human signs, not the agent (governance `boundary`, authority.source)
Governor runs, with their key (agent never touches the private key):
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST
```
→ produces `<name>.txt.sig` and `MANIFEST.sig`. Namespace `-n file` is fixed and must match at verify time.

## 3. Pre-push loop (loop.before, reflex.4)
- Agent verifies the just-made signature with a **live read** before treating it as authority:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I governor@subtract.ing -n file -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt` → must print `Good "file" signature`.
- Surface any unsigned drift in the tree. Human decides: sign / continue / abort.

## 4. Push — which machine, which not
- **Rousseau pushes.** It's the archive node and governor workstation and holds the canonical tree. Push to the origin that serves `subtract.ing` over HTTPS (the signing key's domain — reflex.5), then deploy so `https://subtract.ing/<name>.txt`, `.../<name>.txt.sig`, `.../allowed_signers`, `.../MANIFEST`, `.../MANIFEST.sig` are all fetchable.
- **Emile does not push.** Compute-offload node only; dispatch heavy work there via `ssh m2mini "claude -p"`, never canonical publication.
- **Surface does not push.** Governor terminal, not a publication origin.
- **Acer NAS does not push.** Not formation — service infra / warm backup only. It may mirror the file after the fact; a mirror is never the authority.
- A GitHub mirror, if any, is mirror-only and carries no authority.

## 5. How a stranger verifies, a year later
```
curl -fSO https://subtract.ing/<name>.txt
curl -fSO https://subtract.ing/<name>.txt.sig
curl -fSO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I governor@subtract.ing -n file -s <name>.txt.sig < <name>.txt
```
- Exit 0 + `Good "file" signature for governor@subtract.ing` ⇒ the bytes are exactly what the key-holder signed.
- Trust chain for "who is governor@subtract.ing": `allowed_signers` is itself load-bearing, fetched over TLS from `subtract.ing` — the cert + DNS prove the domain vouches for that pubkey (reflex.5). Strengthen by also publishing the key fingerprint somewhere independent (DNS TXT, the governance manifest) so the verifier can cross-check without trusting a single host.
- For provenance/date: `curl -fSO https://subtract.ing/MANIFEST{,.sig}`, verify the same way, read the recorded SHA-256 + date, and confirm `sha256sum <name>.txt` matches. Optionally `ssh-keygen -Y verify ... -Overify-time=20260510` if a time-bounded key is in play.
- Mirrors (GitHub, Acer) are acceptable to *fetch* from only if the `.sig` still verifies against the domain-served `allowed_signers`. The signature, not the host, is the authority (authority.signed).

## 6. After (loop.after)
Manifest already updated in step 1; signed in step 2; both pushed in step 4. Session close = manifest current + signed. Done.
