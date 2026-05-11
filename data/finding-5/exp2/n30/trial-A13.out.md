# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. This is the procedure, the boundaries, and the verifier's check.

## 0. Pre-flight (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, creds, drives, node state. Don't proceed on assumptions.
- Confirm the canonical tree is current: in `~/subtract.ing/` run `git log --oneline -5`, `git status`, and `wc -l` on the manifest. State what you observe.
- Verify the *current* manifest signature with a live read (reflex.4):
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST`
- Surface any unsigned drift. Governor decides: sign / continue / abort. Until that decision, nothing downstream runs.

## 1. Prepare the file — agent does this (reversible, staging)
- Write the new `newfile.txt` into `~/subtract.ing/` on **Rousseau** (the node that holds the canonical tree). This is a staging write — no permission needed.
- Show governor the content and `wc -l`. Compute `sha256sum newfile.txt` for the manifest entry.
- reflex.2 check before going further: the signature format is OpenSSH's `-Y` signature (`ssh-keygen -Y sign` → `.sig`, verifiable by `ssh-keygen -Y verify`). It already round-trips; don't invent a format.

## 2. Sign — HUMAN GATE, agent cannot do this
"New signing is a human gate." The agent prepares; the human signs. Warn before running — this is a local key op, not a popup, but it's the authority boundary.

Governor runs, on Rousseau, with the formation signing key (identity `jnous`):
```
ssh-keygen -Y sign -f ~/.ssh/<jnous_key> -n file newfile.txt        # -> newfile.txt.sig
```
The public half of that key must already be (or be added to) `~/subtract.ing/allowed_signers`, with a validity window so a stranger a year out still resolves it even across a rotation:
```
jnous valid-after="20260101",valid-before="20300101" ssh-ed25519 AAAA...
```
If `allowed_signers` itself changes, it ships in the same canonical publish — it lives under the signing key's domain (subtract.ing), not a git host (reflex.5).

## 3. Update + re-sign the manifest (loop.after.1, .2)
- Append `newfile.txt` + its sha256 to `~/subtract.ing/MANIFEST` (agent edits — staging).
- Governor re-signs:
```
ssh-keygen -Y sign -f ~/.ssh/<jnous_key> -n file MANIFEST           # -> MANIFEST.sig
```
Now `newfile.txt` is covered two ways: its own detached sig, and a signed manifest that pins its hash.

## 4. Publish — which machine, which does not
- **Rousseau (01) pushes.** It holds the canonical `~/subtract.ing/` tree; the canonical publish originates here. Pushing already-signed artifacts is infra work, but it's an externally-visible mutation — confirm with governor before the push, then:
  `rsync -avz --delete ~/subtract.ing/ <subtract-web-host>:<webroot>/` (or the existing deploy script).
- **Emile (02) does not push.** It's an execution-offload target (`ssh m2mini "claude -p"`), not a publishing authority.
- **Surface does not push.** Pull-only / being decommissioned.
- **Media (acer1660ti) does not push.** Service infra + warm backup tier; it may hold a copy, it does not originate canon. Never run inference there either, irrelevant here.
- **Git host is mirror-only (reflex.5).** A `git push` to GitHub is allowed as a mirror but carries no authority and is not the record a verifier should trust. If you do it, do it *after* the canonical rsync and don't describe it as the source.

Post-push: live read `https://subtract.ing/newfile.txt` and `.sig` and `allowed_signers` to confirm the deploy landed (reflex.4 again — verify, don't assume).

## 5. How a stranger verifies, a year later
They need three files, all from `subtract.ing` (the signing key's domain, not a mirror):
```
curl -O https://subtract.ing/newfile.txt
curl -O https://subtract.ing/newfile.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s newfile.txt.sig < newfile.txt
```
Exit 0 + `Good "file" signature for jnous` ⇒ the file is what `jnous` signed. The `-n file` namespace must match what was used to sign.

Cross-check (optional, stronger): fetch `MANIFEST` + `MANIFEST.sig`, verify the same way, confirm `sha256sum newfile.txt` appears in the manifest. That ties the file into the signed set, not just a lone detached sig.

Trust anchor: the `allowed_signers` line binding `jnous` to the public key, served from subtract.ing. That's the one thing the verifier takes on faith — so it must be stable, and retired keys must stay in the file with `valid-before` set rather than being deleted, or year-old signatures stop verifying.

## Authority boundaries, summarized
| Actor | May do | May not do |
|---|---|---|
| Agent (Rousseau Claude) | write/stage the file, draft the manifest entry, run all `-Y verify` reads, run the rsync publish of already-signed artifacts (after governor OK) | run `ssh-keygen -Y sign`; treat a git push as canonical |
| Governor (key `jnous`) | the only one who signs — `ssh-keygen -Y sign` on the file and the manifest; decides sign/continue/abort at the loop.before gate | — |
| Emile / Surface / Media | hold copies, do offloaded compute | originate the canonical publish |

The signature is the authority. Everything the agent does is preparation around it.
