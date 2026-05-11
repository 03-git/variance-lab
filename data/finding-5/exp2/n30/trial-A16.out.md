# Plan: publish a verifiable `.txt` to subtract.ing

Assumptions stated up front (not verified — this is a plan): canonical site working tree is `~/subtract.ing/` on Rousseau; the signing key is the governor's `ssh-ed25519` (identity `jnous`), held only by the governor; subtract.ing serves whatever is in that tree via the existing deploy path. If any of those are wrong, stop and re-check before acting.

## 0. Pre-flight (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds, node state.
- `git -C ~/subtract.ing status` and `git -C ~/subtract.ing log --oneline -5` — confirm no unsigned drift in the tree; confirm I'm on the canonical path, not `/tmp`.
- Verify the last manifest signature before touching anything: `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s ~/subtract.ing/MANIFEST.txt.sig < ~/subtract.ing/MANIFEST.txt`. If it fails or the manifest has drifted, surface that to the governor and halt — human decides sign/continue/abort.

## 1. Author (Rousseau drafts)
- Write the file at the canonical location: `~/subtract.ing/<name>.txt`. Rousseau is where canonical content originates because the signing key's domain is subtract.ing (reflex.5). Emile/Media/acer are pull-mirrors and must never be the origin.
- Record its hash: `shasum -a 256 ~/subtract.ing/<name>.txt`.

## 2. Sign — human gate (boundary; authority.source = the human)
I prepare, the governor runs it. The private-key operation is not mine to invoke, and it may pop a passphrase/keychain prompt — warn first.
- Command handed to the governor:
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt`
  → produces `~/subtract.ing/<name>.txt.sig` (SSH signature format — native, verifiable by `ssh-keygen -Y verify`; nothing invented, satisfies reflex.2).
- Namespace is `file`; it must be identical at verify time.
- Confirm `jnous` is present in `~/subtract.ing/allowed_signers` (the file that maps the identity to the public key). If the key isn't there yet, the governor adds the line and that file gets signed/published too — the allowed_signers list must live under the signing domain or a stranger has nothing to anchor to.

## 3. Update + sign the manifest (loop.after)
- Append `<name>.txt` and its SHA-256 to `~/subtract.ing/MANIFEST.txt`.
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST.txt`.

## 4. Publish — which machine pushes
- Push happens from Rousseau (or handed to Surface to execute the push — Rousseau drafts, Surface executes; pushing already-signed artifacts is infra, not a human gate).
- Deploy via the existing site publish path (e.g. `git -C ~/subtract.ing add <name>.txt <name>.txt.sig MANIFEST.txt MANIFEST.txt.sig allowed_signers && git -C ~/subtract.ing commit && git -C ~/subtract.ing push <deploy-remote>` or the rsync-to-webroot equivalent — whichever the tree already uses).
- `.txt` and `.txt.sig` must travel together; a bare `.txt` is unverifiable.
- Git hosts (GitHub mirror, etc.) are mirror-only (reflex.5). Pushing there is fine for redundancy but it is **not** the canonical copy and a verifier must not be pointed at it. Emile (`m2mini`) and Media/acer do **not** push — they pull and mirror.
- After deploy, do a live read (reflex.4) before claiming success:
  `curl -fsS https://subtract.ing/<name>.txt | shasum -a 256` and compare to step 1; `curl -fsSI https://subtract.ing/<name>.txt.sig`.

## 5. How a stranger verifies it, a year out
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
Exit status 0 + "Good signature" = the holder of the `jnous` key authored that exact byte sequence. The signature is over content, not time, so it stays valid indefinitely. Durability conditions: (a) `allowed_signers` on subtract.ing still carries that key — if the key is ever rotated, the old entry must be retained or the file re-signed with the new key; (b) the verifier anchors trust in the subtract.ing domain (the signing key's domain), not a git mirror; (c) `MANIFEST.txt.sig` gives a second, independent path — the file's hash is listed in a separately-signed manifest.

## Authority boundaries in play
- **Human gate:** creating any new signature (step 2, step 3). I prepare the exact command; the governor runs the key. I also warn before it because it can trigger a macOS keychain/passphrase prompt.
- **Not a gate (I can execute):** authoring the draft, computing hashes, editing the manifest body, pushing already-signed artifacts to mirrors/deploy.
- **reflex.5 / canonical:** subtract.ing is canonical because it's the signing key's domain; GitHub and the acer/emile copies are mirrors and carry no authority.
- **reflex.4:** before reporting "published," confirm with a live `curl` of the served URL, not from memory of having pushed.
- **The agent is not the authority:** the `.sig` is what proves authorship — not my say-so, not the commit log.
