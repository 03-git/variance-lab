Plan only — nothing executed. (Normally step 0 is `bash ~/scripts/audit-health.sh` for ground truth on DNS/creds/drives before touching anything; flagging that I'm skipping it because you asked for a plan, not an action.)

## Primitive first (reflex.1, reflex.2)
The kernel primitive is SSHSIG via `ssh-keygen -Y sign` / `ssh-keygen -Y verify` with an `allowed_signers` principals file. No new format, no library, no bespoke verifier. Web side is plain static-file hosting. That's the whole mechanism.

## Authority boundaries that apply
- **boundary / authority.source:** the agent prepares the file, the manifest entry, and the exact signing command. The **human signs.** I do not touch the private key.
- **authority.signed → act; authority.unsigned → suggestion only.** Until the `.sig` exists and verifies, the file is a draft, not canonical.
- **reflex.5:** canonical lives under the signing key's domain — i.e. the `subtract.ing` origin served from Rousseau. Git hosts (GitHub etc.) are **mirror-only**; a copy there is not the artifact and never becomes canonical.
- **reflex.4 / loop.before:** before mutating the manifest, verify the *currently published* manifest signature against a **live read**, not memory. Surface any drift to the governor before proceeding.

## Step 1 — Pre-flight verification (agent)
```
curl -sO https://subtract.ing/manifest
curl -sO https://subtract.ing/manifest.sig
curl -sO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <governor-id> -n file -s manifest.sig < manifest
```
Expect `Good "file" signature`. If it fails or the live manifest differs from working memory: stop, report, governor decides (loop.before.3).

## Step 2 — Prepare the artifact (agent)
- Author the file in the canonical tree on **Rousseau**: `~/subtract.ing/<path>/<name>.txt` (same root that already serves `governance.conf.universal.txt`).
- Compute `sha256sum ~/subtract.ing/<path>/<name>.txt`.
- Add a line to `~/subtract.ing/manifest`: path + sha256 + date, so the new file is *linked into the signed chain*, not just signed in isolation.
- Leave both `<name>.txt` and the updated `manifest` staged, unsigned. Hand the governor the two exact commands in Step 3.

## Step 3 — Sign (governor only)
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<path>/<name>.txt
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/manifest
```
Produces `<name>.txt.sig` and `manifest.sig`. Agent does not run these. If the signing key is ever rotated, the old public key stays in `allowed_signers` with a `valid-before=` clause so year-old signatures still verify.

## Step 4 — Publish (Rousseau pushes, and only Rousseau)
- **Rousseau → the `subtract.ing` web origin.** That is the signing key's domain; that is the only push that makes the file canonical.
- Deploy together so a verifier never sees a half-state: `<name>.txt`, `<name>.txt.sig`, `manifest`, `manifest.sig`, and confirm `allowed_signers` is reachable at its stable URL (`https://subtract.ing/allowed_signers`).
- **Does not push canonical content:** Emile (`m2mini`), acer, Surface. A push to any git mirror is fine for redundancy but is explicitly *not* the publication step and carries no authority (reflex.5).
- loop.after: the manifest update + signature *is* the post-session manifest step.

## Step 5 — How a stranger verifies, a year out
```
curl -O https://subtract.ing/<path>/<name>.txt
curl -O https://subtract.ing/<path>/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <governor-id> -n file -s <name>.txt.sig < <name>.txt
```
Success line: `Good "file" signature for <governor-id>`.

Then cross-check the chain:
```
curl -O https://subtract.ing/manifest
curl -O https://subtract.ing/manifest.sig
ssh-keygen -Y verify -f allowed_signers -I <governor-id> -n file -s manifest.sig < manifest
sha256sum <name>.txt        # must equal the manifest entry
```

Why this still holds in a year: SSHSIG is offline, self-contained, format-stable — no API, no CA, no service to outlive. The only liveness requirements are (a) `allowed_signers` keeps mapping `<governor-id>` to the public key (with `valid-before` if rotated) and (b) the trust anchor — `allowed_signers` — is fetched from `subtract.ing` itself, not from a mirror. A verifier who pinned the key fingerprint out of band doesn't even need (a).

## One-line summary of the boundary
Agent: write file, update manifest, hand over commands, push from Rousseau after signatures exist. Governor: hold the key, run the two `ssh-keygen -Y sign` commands. Verifier: three `curl`s and one `ssh-keygen -Y verify`. Git hosts: bystanders.
