# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. Plan only.

## 0. Ground truth first
- `bash ~/scripts/audit-health.sh` — read DNS, drive, credential state before touching anything. Do not assume the `~/subtract.ing/` working tree, the signing key, or the deploy path are where I think they are.

## 1. loop.before (pre-flight, before any action)
- `loop.before.1` — verify the last signed manifest still verifies:
  `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I <principal> -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST`
- `loop.before.2` — `git -C ~/subtract.ing status` and diff against the manifest; surface any unsigned drift already sitting in the tree.
- `loop.before.3` — if there's drift, the governor decides (sign / continue / abort) before I add a new file on top.

## 2. Draft & stage — Rousseau only
- Write the new file into the canonical working tree: `~/subtract.ing/<path>/newfile.txt` (Rousseau is canonical for `~/human/` and the subtract.ing runtime tree; Surface is a pull-mirror and does not originate canonical content).
- This is staging-tier work — reversible, no human gate. I can do it.
- `reflex.5`: this file is load-bearing only once it lives under the signing key's domain (`https://subtract.ing/...`). The GitHub mirror is mirror-only and confers no authority.

## 3. Human gate — signing (the agent does NOT do this)
- `boundary` / `authority.unsigned`: I prepare; the governor signs. An unsigned file is a suggestion, not canonical.
- On the machine holding the governor's private key (Rousseau, `~/.ssh/id_ed25519` — the governor's main workstation; **Surface does not sign**), the governor runs:
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<path>/newfile.txt`
  → produces `newfile.txt.sig` (an SSH signature, namespace `file`).
- `reflex.2` is already satisfied: `ssh-keygen -Y verify` is the verification primitive — no new signature format is being invented.

## 4. Verify the signature locally before publishing
- `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I <principal> -n file -s ~/subtract.ing/<path>/newfile.txt.sig < ~/subtract.ing/<path>/newfile.txt`
- `<principal>` = the identity recorded in subtract.ing's canonical `allowed_signers` (memory has it as `jnous` — confirm against the live file, don't trust memory; `fail.confabulation`).
- Must print `Good "file" signature for <principal>`. If not, stop — `authority.unsigned`, do not publish.

## 5. Manifest — loop.after.1 + loop.after.2
- Add `newfile.txt` and its hash (e.g. `sha256sum`) to `~/subtract.ing/MANIFEST`.
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST` → new `MANIFEST.sig`.
- Re-verify the manifest the same way as step 4.

## 6. Publish — canonical push vs. mirror
- **Canonical push (Rousseau, or whatever node holds deploy creds):** push the file, its `.sig`, the updated `MANIFEST`, and `MANIFEST.sig` to the host that terminates `https://subtract.ing` — using the *existing* deploy path (the established `rsync`/`git push`-to-deploy mechanism), not a new one (`reflex.1`, `fail.additive`). This is movement of already-signed artifacts → infra work, no human gate (`Human Gate Scope`).
- **Mirror (optional):** push the same commit to the GitHub mirror. Mirror-only. If a verifier ever finds the file *only* on GitHub, that does not establish canonicity (`reflex.5`).
- **Surface:** does not sign, does not originate or push canonical content — it pulls.
- Confirm with a live read after publish (`reflex.4`): `curl -fsSL https://subtract.ing/<path>/newfile.txt` and `...newfile.txt.sig` return the bytes just pushed.

## 7. How a stranger verifies the claim a year later
Everything they need is served under the signing key's domain:
1. `curl -fsSL https://subtract.ing/<path>/newfile.txt -o newfile.txt`
2. `curl -fsSL https://subtract.ing/<path>/newfile.txt.sig -o newfile.txt.sig`
3. `curl -fsSL https://subtract.ing/allowed_signers -o allowed_signers` — the canonical identity→pubkey map, published under the same domain.
4. `ssh-keygen -Y verify -f allowed_signers -I <principal> -n file -s newfile.txt.sig < newfile.txt` → `Good "file" signature for <principal>`.
5. Optional corroboration: pull `MANIFEST` + `MANIFEST.sig` from subtract.ing, verify the manifest signature the same way, and check `sha256sum newfile.txt` against the manifest entry — ties the file into the signed set, not just a lone signature.
6. Optional out-of-band: compare the pubkey in `allowed_signers` against the key the governor has published elsewhere (it's an `ssh-ed25519` key; a stranger can cross-check it however they already trust that identity).

What does *not* count: a copy on the GitHub mirror, a copy with no `.sig`, or a signature that verifies under a principal not in the canonical `allowed_signers`.

## 8. Authority boundaries in play
- `authority.signed` → act on it; `authority.unsigned` → suggestion only. The file is canonical only after step 3–4 succeed.
- `boundary` — agent prepares (steps 0–2, 4 dry-runs, 6 push of signed bytes); human signs (steps 3, 5).
- `reflex.5` — canonical = subtract.ing (signing key's domain); git = mirror.
- `reflex.4` — verify with a live `curl` read after publishing; assertions that something is published count as actions.
- `Human Gate Scope` — only the new `ssh-keygen -Y sign` invocations are gated; staging the draft and pushing already-signed artifacts are not.
