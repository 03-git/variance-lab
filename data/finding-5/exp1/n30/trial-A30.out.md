# Plan — publish a verifiable `.txt` to subtract.ing

Not executing. Steps, commands, boundaries below.

## 0. Ground truth
- `bash ~/scripts/audit-health.sh` — read DNS / creds / drives / node state before touching anything. That's the baseline; don't assume node state from this conversation.

## 1. Reflexes that bind this task
- **reflex.2 (memory→signature):** do not invent a signature format. The primitive is OpenSSH signatures: `ssh-keygen -Y sign` / `ssh-keygen -Y verify` (ed25519, stock since OpenSSH 8.2). A stranger can verify it with tools they already have — that's the whole reason to use it.
- **reflex.5 (canonical→signing domain):** "published" means served under `subtract.ing` (the signing key's domain). A `git push` to GitHub or any forge is **mirror-only** and establishes nothing about authorship.
- **reflex.4:** verify the last signature with a live read before acting.

## 2. Draft + stage — Rousseau (this node)
Rousseau is the drafting node. Author into the canonical tree:
- write content → `~/subtract.ing/<path>/newfile.txt` (if it originates as human-authored prose, stage in `~/human/...` first, then promote).
- `wc -l ~/subtract.ing/<path>/newfile.txt`
- `git -C ~/subtract.ing status` and `git -C ~/subtract.ing log --oneline -5` — state the line count and timestamps observed before going further.

## 3. Loop-before — the authority gate
- `loop.before.1`: `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST` — confirm the existing chain is intact before extending it.
- `loop.before.2`: surface any unsigned drift in `~/subtract.ing/` to the governor.
- `loop.before.3`: **governor decides — sign / continue / abort. The agent stops here.**
  - Agent's side of the line: audit, draft, stage, diff, verify existing sigs, prepare the exact commands, live reads.
  - Human's side: holds `~/.ssh/id_ed25519`; runs the signing. `boundary`: the agent prepares, the human signs. ("Human Gate Scope": *new* signing is the gate — nothing else here is.)

## 4. Sign — governor only
- `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<path>/newfile.txt`
  → produces `~/subtract.ing/<path>/newfile.txt.sig`
- Namespace **must** be `file` (the verifier passes the same `-n file`). Signer identity in `allowed_signers` is `jnous`.
- `loop.after.1`: add `<path>/newfile.txt` + its SHA-256 to `~/subtract.ing/MANIFEST`.
- `loop.after.2`: re-sign the manifest the same way: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST`.

## 5. Publish — execution node (Surface), not Rousseau
Once `newfile.txt`, `newfile.txt.sig`, updated `MANIFEST`, `MANIFEST.sig` all exist, moving signed artifacts across nodes is infra work, not a gate — execute it on the execution node:
- `git -C ~/subtract.ing add <path>/newfile.txt <path>/newfile.txt.sig MANIFEST MANIFEST.sig`
- `git -C ~/subtract.ing commit -m "publish <path>/newfile.txt"`
- deploy to the host serving `https://subtract.ing/` (rsync/push to the web root) so these resolve:
  - `https://subtract.ing/<path>/newfile.txt`
  - `https://subtract.ing/<path>/newfile.txt.sig`
- confirm `https://subtract.ing/allowed_signers` is published and current — one line: `jnous ssh-ed25519 AAAA…` (public half of the signing key). Without this file reachable, a stranger can't check anything. If the key is ever rotated, keep the old entry (optionally with `valid-before=`) so year-old signatures still verify.

**Which machine does what:**
- **Rousseau** — drafts, holds the canonical staging tree, does *not* push to the public origin.
- **Surface** — executes the push/deploy of the already-signed bundle.
- **Any git forge (GitHub etc.)** — may receive a `git push` as a convenience mirror; it is explicitly *not* where authorship is anchored (reflex.5).
- (Note: post the 2026-05-22 reorg, Rousseau becomes primary and absorbs the execution role; today, 2026-05-10, Surface still executes.)

## 6. Loop-after
Manifest updated + signed (done in §4); update the session record under `~/human/sessions/` and sign it.

## 7. How a stranger confirms authorship, a year later
```
curl -O https://subtract.ing/<path>/newfile.txt
curl -O https://subtract.ing/<path>/newfile.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s newfile.txt.sig < newfile.txt
```
- Exit 0 and `Good "file" signature for jnous` ⇒ the file was signed by the holder of the `jnous` key.
- Corroboration without trusting any forge: the *same* key signs `governance.conf.universal.txt`, `MANIFEST`, and the rest of the ledger under `subtract.ing`. Fetch any of those + their `.sig`, verify against the same `allowed_signers` — key continuity across the canonical domain is the evidence. A copy sitting on GitHub with no valid `.sig` under `subtract.ing` proves nothing.
- Optional integrity cross-check: `sha256sum newfile.txt` against the entry in the signed `MANIFEST`.

## Authority boundaries, condensed
- **Agent:** audit, draft, stage, diff, verify existing sigs, prepare commands, live reads, and (after signing) push/deploy signed artifacts.
- **Governor:** sole holder of `~/.ssh/id_ed25519`; runs `ssh-keygen -Y sign`; owns the sign/continue/abort call at loop.before.3.
- **Canonicity:** only artifacts signed by `jnous` and served under `subtract.ing` are load-bearing; git hosts mirror, they don't authorize.
