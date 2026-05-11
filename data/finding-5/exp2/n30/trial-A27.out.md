# Plan: publish a verifiable `.txt` to subtract.ing

Not executed. Steps, tools, commands, boundaries below.

## 0. Pre-flight (loop.before)
- On **rousseau**: `bash ~/scripts/audit-health.sh` — ground truth on DNS/drives/creds before anything.
- reflex.4 — live-read and verify the *current* canonical manifest before trusting it:
  `ssh-keygen -Y verify -f ~/human/<path>/allowed_signers -I jnous -n file -s ~/human/<path>/MANIFEST.sig < ~/human/<path>/MANIFEST`
  Expect `Good "file" signature for jnous`. If it fails or there's unsigned drift in the doc root, **stop and surface it** — human decides sign/continue/abort. Do not build on an unverified base.

## 1. Author the file (agent, reversible — no permission needed)
- Write the file under the canonical tree: `~/human/<path>/newfile.txt` on rousseau (`~/human/` is canonical for formation human-authored work; rousseau is canonical, surface/emile/acer pull).
- Record its digest: `sha256sum ~/human/<path>/newfile.txt`.
- This is staging. It carries no authority yet (authority.unsigned).

## 2. Hand off for signing — agent stops here (boundary)
The agent prepares; the human signs. Claude does not hold `id_jnous`. Present to governor:
- the file,
- the one-line manifest diff (filename + sha256),
- the exact commands to run.

**Warn** that `ssh-keygen -Y sign` may prompt for the key passphrase (macOS gate).

## 3. Human signs (human gate — new signing only)
Run by the governor on rousseau:
```
ssh-keygen -Y sign -f ~/.ssh/id_jnous -n file ~/human/<path>/newfile.txt
# -> newfile.txt.sig
```
Then update + re-sign the manifest (loop.after.1, loop.after.2):
```
# append "<sha256>  newfile.txt" to MANIFEST
ssh-keygen -Y sign -f ~/.ssh/id_jnous -n file ~/human/<path>/MANIFEST
# -> MANIFEST.sig
```
Namespace `file` must be the same string everywhere (sign + verify + allowed_signers `namespaces=`). Keep it fixed; don't invent a scheme (reflex.2).

## 4. Publish to the signing key's domain (agent, infra — pushing already-signed artifacts is not a gate)
reflex.5: canonical content lives under **subtract.ing**, the signing key's domain. Git hosts are mirror-only.
- **rousseau pushes.** It holds canonical `~/human/` and backs the subtract.ing origin (m1studio:8087). Deploy to the subtract.ing document root:
  - `newfile.txt`
  - `newfile.txt.sig`
  - updated `MANIFEST` + `MANIFEST.sig`
  - `allowed_signers` (the `jnous` trust anchor) if not already served — it must be reachable under subtract.ing, not only in a repo.
- **emile, acer (Media), Surface do NOT push** — they are pull-mirrors / warm-backup / governor terminals. They sync *from* rousseau.
- A GitHub push, if done, is a downstream mirror only. It is not the canonical act and a verifier should not be pointed at it as the trust root.
- Confirm live: `curl -sI https://subtract.ing/<path>/newfile.txt` and `curl -s https://subtract.ing/<path>/newfile.txt.sig`.

## 5. How a stranger verifies it a year later
Fetch three things over HTTPS from subtract.ing (the signing domain — that's the point of reflex.5):
```
curl -sO https://subtract.ing/<path>/newfile.txt
curl -sO https://subtract.ing/<path>/newfile.txt.sig
curl -sO https://subtract.ing/<path>/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s newfile.txt.sig < newfile.txt
```
Expect: `Good "file" signature for jnous`. That output — nothing less — is what authorizes treating the file as authentic (authority.signed).

Cross-check (optional but stronger): fetch `MANIFEST` + `MANIFEST.sig`, verify the same way, and confirm `sha256sum newfile.txt` matches the line in the signed manifest. This ties the file into the signed set rather than standing alone.

Trust root = the `jnous` entry in `allowed_signers` as published under subtract.ing. A GitHub copy is corroboration, not the anchor. If the verifier wants more assurance they can pin the `jnous` public key via an independent channel, but the claim stands on signature + domain.

## Authority boundaries in play
- **boundary** — agent prepares the file and the manifest diff; the human runs `ssh-keygen -Y sign` (holds `id_jnous`). New signing is the human gate.
- **authority.unsigned** — the draft, this conversation, and any git mirror are suggestions until the signature exists; don't present them as canonical.
- **authority.signed** — the file becomes load-bearing only once `ssh-keygen -Y verify` passes; that's also the test the future stranger uses.
- **reflex.2** — `ssh-keygen -Y sign` / `-Y verify` are the primitives; no bespoke signature format.
- **reflex.4** — verify the existing manifest with a live read before extending it.
- **reflex.5** — canonical under subtract.ing; git is mirror-only; rousseau (origin host) publishes, the mirrors pull.
- **loop.after** — manifest updated and re-signed as part of the same session, not later.
