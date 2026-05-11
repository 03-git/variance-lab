# Plan: publish a verifiable `.txt` to subtract.ing

Working filename below: `claim.txt`. Signing identity: `jnous` (the formation signing key). No execution — this is the sequence.

## 0. Antecedent checks (reflex.2, reflex.5)
- `ssh-keygen -Y sign` is the format. Don't invent an envelope; SSH signatures are verifiable by a stranger with stock OpenSSH ≥ 8.2.
- Canonical home is the signing key's domain: `subtract.ing`. GitHub is mirror-only and never authoritative.

## 1. Draft — Rousseau (this node)
- Author `claim.txt` under `~/human/` (canonical staging for formation human-authored work), e.g. `~/human/publish/claim.txt`.
- Rousseau prepares only. It does **not** sign and does **not** push to production.

## 2. Sign — governor, on the machine holding the private key (human gate)
This is the one step the agent cannot do. Warn first that `ssh-keygen -Y sign` may prompt for the key passphrase / hardware-key touch.

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file ~/human/publish/claim.txt
```

Produces `~/human/publish/claim.txt.sig` (the namespace `file` must match what verifiers use).

## 3. Verify locally before anything leaves the node (reflex.4 — live read, not memory)
Need an `allowed_signers` line: `jnous <ssh-ed25519 AAAA...pubkey>`.

```
ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous -n file \
  -s ~/human/publish/claim.txt.sig < ~/human/publish/claim.txt
```

Exit 0 required. If it fails, stop — do not publish.

## 4. Update + sign the manifest (loop.after.1, loop.after.2)
- Add `claim.txt` (with its SHA-256) to the canonical manifest of subtract.ing content.
- Re-sign the manifest the same way (`ssh-keygen -Y sign -n file ...`). The manifest is load-bearing, so it lives under the signing domain and carries its own `.sig`.

## 5. Publish — Surface (execution terminal), not Rousseau
Pushing already-signed artifacts is infra work, no gate. Three files go to the subtract.ing web root together:
- `claim.txt`
- `claim.txt.sig`
- updated `manifest` + `manifest.sig`
- and confirm `allowed_signers` is already served at a stable URL (e.g. `https://subtract.ing/allowed_signers`); if not, publish it too.

Mechanism is whatever currently deploys the site (rsync/scp to the web host, or a commit to the deploy repo that backs `subtract.ing` — the *deploy* path, distinct from the GitHub *mirror*). GitHub mirror, if updated at all, is updated after and is explicitly non-authoritative.

## 6. Post-publish live check
From Surface, fetch back over HTTPS and re-run the step-3 verify against the *served* bytes:

```
curl -sO https://subtract.ing/claim.txt
curl -sO https://subtract.ing/claim.txt.sig
curl -sO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s claim.txt.sig < claim.txt
```

Exit 0 confirms what the world sees is what was signed.

## How a stranger verifies it a year from now
1. `curl -O https://subtract.ing/claim.txt`
2. `curl -O https://subtract.ing/claim.txt.sig`
3. `curl -O https://subtract.ing/allowed_signers` (the identity→pubkey binding, served from the same signing domain — that co-location under `subtract.ing` is the trust root, per reflex.5)
4. Run:
```
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s claim.txt.sig < claim.txt
```
Output `Good "file" signature for jnous` / exit 0 ⇒ the file is exactly what the holder of the `jnous` key signed. Optionally cross-check the file's SHA-256 against the signed `manifest`.

## Authority boundaries in play
- **Rousseau**: drafts, prepares, runs `-Y verify` (reads are free). Never signs, never pushes to production.
- **Governor (human)**: sole runner of `ssh-keygen -Y sign`. The signature *is* the authority — `authority.source = the human`. This is the only hard gate.
- **Surface**: executes the push of already-signed bytes and the post-publish live check. No gate — infra.
- **GitHub / any git host**: mirror-only. Not canonical, not consulted by the verifier, never the source of truth (reflex.5).
- **Unsigned anything** (draft in chat, "I remember the key is…", a push that skipped step 3): suggestion only, do not act on it as authoritative (`authority.unsigned`).
