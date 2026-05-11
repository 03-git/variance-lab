# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. This is the sequence, the boundaries, and the verifier path.

## 0. Preconditions (loop.before)
- `bash ~/scripts/audit-health.sh` — confirm DNS for subtract.ing, drives, creds are green before touching anything.
- In `~/subtract.ing/`: `git log --oneline -5`, `git status`, confirm clean tree and that my working memory matches HEAD.
- Verify the *last* published artifact's signature still passes (`ssh-keygen -Y verify …` on the most recent entry) — surface any unsigned drift to the governor before adding more. Human decides: sign / continue / abort.

## 1. Reflex check (reflex.2)
Before inventing any envelope: `ssh-keygen -Y sign` / `ssh-keygen -Y verify` (SSHSIG format) is the primitive. It verifies a detached `.sig` against an `allowed_signers` file. No custom format, no GPG, no wrapper. Stop here if that primitive can't express the claim — it can.

## 2. Prepare the file (agent — Rousseau)
- Write content to `~/subtract.ing/<name>.txt`. Final bytes, frozen — the signature covers exact bytes, so no post-sign edits (even whitespace).
- This is the boundary: **I prepare, I do not sign.** The agent is not the authority.

## 3. Sign (governor only — Rousseau is the workstation, the key is the governor's)
Governor runs, with the subtract.ing signing key:
```
ssh-keygen -Y sign -f ~/.ssh/<subtract_signing_key> -n file ~/subtract.ing/<name>.txt
```
→ produces `~/subtract.ing/<name>.txt.sig` (SSHSIG, namespace `file`).

Confirm `allowed_signers` already maps the signer identity → pubkey, e.g. a line:
```
governor@subtract.ing namespaces="file" ssh-ed25519 AAAA...
```
If that identity/key isn't already published under the domain, that's a separate governor decision — don't auto-add.

## 4. Update the manifest (loop.after.1)
- Add `<name>.txt` + its `.sig` to the repo manifest (the existing manifest file in `~/subtract.ing/`), with the date and the signer identity.
- `git add <name>.txt <name>.txt.sig <manifest>` and commit. Re-sign the manifest itself if that's the established pattern (loop.after.2).

## 5. Publish — canonical vs mirror (reflex.5)
- **Canonical:** the file, the `.sig`, and `allowed_signers` must be reachable under the signing key's own domain — `https://subtract.ing/<name>.txt`, `.../<name>.txt.sig`, `.../allowed_signers` (or `.../.well-known/...`). Load-bearing content is canonical *only* under that domain. Deploy via whatever serves subtract.ing from Rousseau (the archive/governor node owns this).
- **Mirror only:** pushing the repo to GitHub/git host is a mirror. A stranger must not have to trust the git host. If the domain and the mirror disagree, the domain wins.

## 6. Which machine does what
- **Rousseau (01, this node):** prepares the file, holds the repo, serves/deploys subtract.ing, pushes the canonical artifacts. Governor signs here.
- **Emile (m2mini):** does **not** push or publish. Execution-offload target only (`ssh m2mini "claude -p …"`) — e.g. if I needed to bulk-lint or render something. No authority, no publish path.
- **Surface (surfacepro8):** governor terminal, no publish role.
- **acer1660ti:** **not formation** — service infra + warm backup tier. It is a mirror endpoint at most; it never originates the canonical copy. Do not push the authoritative file there as the source of truth.

## 7. How a stranger verifies, a year out
They need three files, all fetched from `subtract.ing` (not the git mirror):
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I governor@subtract.ing -n file \
  -s <name>.txt.sig < <name>.txt
```
→ `Good "file" signature for governor@subtract.ing with ED25519 key SHA256:…`

That proves: the bytes of `<name>.txt` were signed by the key that `allowed_signers` — served from the subtract.ing domain — attributes to the governor. Authority comes from the signature under the domain, not from "Rousseau said so" and not from the git host. The agent prepared it; the signature is what a stranger trusts.

## Authority boundaries, condensed
- `authority.signed` → a verifier acts on the `.txt` only because `ssh-keygen -Y verify` passes; unsigned, it's a suggestion.
- `boundary` → I (agent) stage and publish; the **governor signs**. I never hold or use the signing key autonomously.
- `reflex.5` → canonical = subtract.ing domain; git = mirror.
- `loop.after` → manifest updated and signed after the session.
