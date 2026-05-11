# Plan — publish a verifiable `.txt` to subtract.ing

Authorship is provable a year out only if the artifact carries an `ssh-keygen -Y` signature from the `jnous` key and the `allowed_signers` list is served from the signing key's own domain. Everything below routes around that.

## 0. Pre-flight (loop.before, reflex.4)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, creds, drives, which docroot actually serves subtract.ing. Don't assume.
- On rousseau: `cd ~/subtract.ing && git status && git log --oneline -5` — working tree clean, matches deployed state, no unsigned drift already sitting there.
- Verify the existing manifest before stacking anything on it:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous@subtract.ing -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST`
  If that fails or the manifest has drifted → stop, surface it, let the governor decide (sign current state / continue / abort). A new file on an unverified base is not OK.

## 1. Stage the file (agent — reversible, `authority.unsigned`)
- Write `~/subtract.ing/<name>.txt` into the canonical working tree on rousseau. This is staging, not publication — an unsigned file in the tree is a suggestion, not authority. Agent may do this without a gate.
- Fix the namespace now and never change it: `-n file`. If existing `.sig` files on subtract.ing use a different namespace, match them — check one with `ssh-keygen -Y check-novalidate -n file -s some.sig < somefile`. Don't invent a format `ssh-keygen -Y` can't already verify (reflex.2).

## 2. Sign — HUMAN GATE (boundary; "only new signing is a human gate")
- Agent does **not** run this. Warn the governor first: `ssh-keygen -Y sign` will prompt for the `id_ed25519` passphrase (terminal/macOS prompt — see "warn before human gates").
- Governor, on rousseau (the only node that holds the `jnous` private key — never copy that key elsewhere to sign):
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt`
  → produces `~/subtract.ing/<name>.txt.sig`
- Confirm the matching public key is already a line in `~/subtract.ing/allowed_signers` as `jnous@subtract.ing ssh-ed25519 AAAA...` — that's the `-I` identity the verifier will use. Adding a new signer line is also governor territory, not the agent's.

## 3. Update + re-sign the manifest (loop.after.1 / loop.after.2)
- Agent stages: append `<name>.txt` + its `sha256sum` to `~/subtract.ing/MANIFEST` in the existing format (match it, don't redesign).
- Governor re-signs: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST` → `MANIFEST.sig`

## 4. Local verify before anything ships (reflex.4)
- `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous@subtract.ing -n file -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt` → must exit 0, `Good "file" signature for jnous@subtract.ing`.
- Same for `MANIFEST.sig`. Either fails → stop.

## 5. Publish — rousseau pushes, nothing else does (reflex.5)
- subtract.ing is canonical **under the signing key's domain**, and that domain is served from rousseau (`subtract → m1studio:8087`). Rousseau is the machine that writes the live files: `<name>.txt`, `<name>.txt.sig`, `MANIFEST`, `MANIFEST.sig`, and `allowed_signers` if it changed.
- `cd ~/subtract.ing && git add <name>.txt <name>.txt.sig MANIFEST MANIFEST.sig allowed_signers && git commit -m "publish <name>.txt"`, then deploy to the served docroot via the existing mechanism (confirm the path from audit-health output — don't guess).
- **Mirror-only, never authority:** any GitHub/git host, Emile, Media's warm-backup tier. They may receive a `git push` / rsync *after* publication — that's plain infra, agent can do it ("pushing already-signed artifacts across nodes is just infra work"). A verifier must never be pointed at them.
- **Do not push from:** Emile, Media, Surface — none originate canonical content. Media keeps a backup copy and originates nothing. Signing stayed on rousseau because that's where the key is.

## 6. Live read-back (reflex.4, loop.after)
- `curl -fsS https://subtract.ing/<name>.txt | sha256sum` → compare to the manifest line.
- `curl -fsS -O https://subtract.ing/<name>.txt.sig`, then re-run the `ssh-keygen -Y verify` from §4 against the **fetched** copies — proves what's actually served verifies, not just the local tree.
- Update the session/manifest note in formation memory.

## How a stranger verifies it, a year later
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers          # MUST come from subtract.ing itself
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file -s <name>.txt.sig < <name>.txt
```
Exit 0 + `Good "file" signature for jnous@subtract.ing` ⇒ the file was signed by the holder of the `jnous` key. No CA, no DNS trust, no faith in GitHub — just the SSH signature plus the `allowed_signers` list, and that list is trustworthy precisely because it came off the signing key's own domain (reflex.5), not a mirror.
Optional completeness check: fetch `MANIFEST` + `MANIFEST.sig`, verify the same way, confirm `<name>.txt`'s hash is in it — proves the file is part of the published set, not an orphan.

## Boundaries, restated
- Agent: stages the `.txt`, edits the manifest, runs all `-Y verify` checks, does mirror pushes, does the curl read-back.
- Human gate: every `ssh-keygen -Y sign` invocation, and any change to `allowed_signers`. Warn before each (passphrase prompt).
- Authority: an unsigned file in the tree is a suggestion; it becomes canonical only once `ssh-keygen -Y verify` passes against the published copy.
- Load-bearing constants to record in the manifest and never change: namespace `file`, identity `jnous@subtract.ing`. If the `jnous` key ever rotates, keep the old pubkey in `allowed_signers` with a `valid-before` date or year-old signatures stop verifying.
