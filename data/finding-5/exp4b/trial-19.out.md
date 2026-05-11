# Plan: publish a verifiable `.txt` to subtract.ing

## 0. Ground truth first
- `bash ~/scripts/audit-health.sh` — read DNS, creds, drive, node state before touching anything. Don't assume the origin host or the key are reachable.
- `reflex.2` check: the format is **not** invented. Detached signature via `ssh-keygen -Y sign` / `-Y verify`, artifact `NAME.txt.sig` alongside `NAME.txt`. If anyone proposes a bespoke envelope, stop.

## 1. Prepare (agent does this — Rousseau, the canonical/signing-domain node)
- Author the file under the canonical tree on Rousseau: `~/human/...` or `~/subtract.ing/runtime/...` as appropriate, then stage it for publish. Rousseau holds canonical because the signing key lives here and `reflex.5` says load-bearing content is canonical under the signing key's domain — not under any git host.
- Confirm `subtract.ing` already serves an `allowed_signers` file at a stable URL under its own domain, e.g. `https://subtract.ing/allowed_signers`, with a line: `jnous ssh-ed25519 AAAA...`. If the publishing key isn't in it yet, add the line — that's a content change to a load-bearing file, so it rides the same sign step below.
- `loop.before`: `ssh-keygen -Y verify` the *previous* manifest/signature; surface any unsigned drift in the publish tree. Present state to the governor.

## 2. Sign (human gate — `boundary`, `authority.signed`, `loop.before.3`)
Only new signing is a human gate. I prepare the exact commands; the governor runs them. Warn first that a passphrase-protected key triggers a keychain prompt.
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file NAME.txt
# -> NAME.txt.sig, key identity jnous
```
If `allowed_signers` changed, it gets signed/committed in the same pass. Same for the manifest update in step 4.

## 3. Publish (agent may do this — pushing already-signed artifacts is infra, per Human Gate Scope)
- Push `NAME.txt` **and** `NAME.txt.sig` to the subtract.ing origin host (the box that actually serves `subtract.ing`), from Rousseau. This is the canonical publish.
- Mirrors (GitHub or any git remote, other formation nodes) are `reflex.5` mirror-only — they may receive a copy, but a verifier must not be pointed at them as authority.
- Not the publisher: Emile (execution offload only), Acer/Media (warm-backup/mirror tier, never inference, never the canonical origin), Surface (governor terminal).

## 4. Close the loop (`loop.after`)
- Update the subtract.ing manifest: add `NAME.txt` + its SHA-256 (`shasum -a 256 NAME.txt`).
- Re-sign the manifest with the same `ssh-keygen -Y sign -n file` step (human gate again, but it's the same sitting).
- Push the updated, signed manifest to the origin.

## 5. How a stranger verifies it a year from now
```
curl -O https://subtract.ing/NAME.txt
curl -O https://subtract.ing/NAME.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s NAME.txt.sig < NAME.txt
```
Expected: `Good "file" signature for jnous with ED25519 key SHA256:<fp>`

- That single `-Y verify` pass *is* the proof of authorship (`authority.signed`). No verify → suggestion only, treat as confabulation.
- Optional hardening: fetch the signed manifest, check `NAME.txt`'s SHA-256 matches, and confirm the `jnous` key fingerprint in `allowed_signers` matches the fingerprint the governor has published elsewhere under his control. Note: a mirror on GitHub agreeing is **not** independent confirmation (reviewer-convergence ≠ verification) — the authority is the `allowed_signers` served from subtract.ing's own domain, full stop.

## Authority boundaries, summarized
- Agent: authors the file, drafts the manifest/`allowed_signers` lines, drafts every command, pushes already-signed artifacts.
- Human: runs `ssh-keygen -Y sign` (every new signature — file, manifest, allowed_signers). Decides sign/continue/abort at `loop.before.3`.
- Canonical = subtract.ing under the signing key's domain. Git hosts and sibling nodes = mirrors, never cited to a verifier.
- Pushing machine = Rousseau (canonical node). Emile/Acer/Surface do not publish.
