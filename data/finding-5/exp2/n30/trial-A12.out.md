# Plan: publish a verifiable `.txt` to subtract.ing

Not executing — plan only.

## 0. Preconditions (the loop, before acting)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds, node state. Don't proceed on a red.
- `loop.before.1/2`: on the canonical manifest, run `git -C ~/subtract.ing log --oneline -5`, `git -C ~/subtract.ing status`, `wc -l` on the manifest. State timestamps/line counts. Verify the manifest's existing `.sig` with `ssh-keygen -Y verify` before I touch it. Surface any unsigned drift.
- `loop.before.3`: governor decides sign / continue / abort. I do not cross this on my own.

## 1. Draft (agent — rousseau)
- Rousseau is canonical for `~/human/` authored work and `~/subtract.ing/runtime/`. Author the file there, e.g. `~/subtract.ing/<name>.txt`, matching the layout of existing canon (`governance.conf.universal.txt` lives at web root).
- `reflex.2` check before inventing any provenance scheme: the verification format is the SSH signature format — `ssh-keygen -Y sign` produces it, `ssh-keygen -Y verify` checks it. No new format. Namespace: `file`.
- Stage, but do not sign:
  - the `.txt`
  - an `allowed_signers` line for the governor's signing key (principal e.g. `jnous@subtract.ing`, the `id_ed25519` pubkey) — if not already published at the web root / `.well-known/`.
  - a drafted manifest diff: new path, `sha256`, pointer to the `.sig`.

## 2. Sign (human gate — governor, on the machine holding the private key)
New signing is the human boundary (`boundary`, `authority.source`). I prepare; the governor runs:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt
```
→ emits `~/subtract.ing/<name>.txt.sig`. Same for the manifest after step 3 (`loop.after.2`). Warn the governor first if any of this pops a passphrase/keychain prompt.

## 3. Manifest (agent drafts, human signs)
- Add the file + `sha256` + `.sig` reference to the canonical manifest. Then governor re-signs the manifest as above. `loop.after.1` then `loop.after.2`.

## 4. Publish (agent — rousseau pushes; others do not)
- **Rousseau pushes** the signed bundle (`<name>.txt`, `<name>.txt.sig`, updated `allowed_signers`, signed manifest) to the subtract.ing web host. Per `reflex.5`, that web host under the signing key's domain is the canonical location.
- Git host (GitHub) gets the same commit as a **mirror only** — not authoritative, and nothing should cite it as provenance.
- **Surface does not push** — it's a pull-mirror of `~/human/`. **Emile does not push** — it's execution offload, not a publish point. **Media/acer** is warm-backup tier, not canon. Pushing these already-signed artifacts around is infra, so I can do it without a gate — but only after the human-gated signature exists.

## 5. How a verifier (stranger, one year later) confirms
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers     # served from subtract.ing, not a git host
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file -s <name>.txt.sig < <name>.txt
```
Expect `Good "file" signature for jnous@subtract.ing`. Then:
- Confirm `allowed_signers` was fetched from the signing key's domain (subtract.ing), not GitHub — a mirror copy proves nothing (`reflex.5`).
- Fetch the signed manifest, verify its `.sig` the same way, and check it lists `<name>.txt` with a `sha256` matching `shasum -a 256 <name>.txt`. That ties the file into the dated canonical record, not just a standalone signature.
- Optional independent anchor: the key's prior appearances in earlier signed manifests in git history give a continuity trail, but the live verify above is the claim.

## Authority boundaries, summarized
- Agent: drafts content, stages files, writes the `allowed_signers` entry and manifest diff, runs the pushes/mirrors of already-signed artifacts, runs all `-Y verify` checks.
- Human: holds `id_ed25519`, runs every `ssh-keygen -Y sign` (file + manifest), makes the sign/continue/abort call. Unsigned content is suggestion only (`authority.unsigned`).
- Canonical = subtract.ing under the signing key's domain. Git hosts mirror-only. Surface/Emile/Media never originate the publish.
