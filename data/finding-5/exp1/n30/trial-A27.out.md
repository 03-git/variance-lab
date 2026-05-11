# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. Plan only.

## 0. Pre-flight (Rousseau)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, creds, drives, node state before touching anything (CLAUDE.md session-start gate).
- `git -C ~/subtract.ing log --oneline -5` and `git -C ~/subtract.ing status` — know the canonical tree's current head before adding to it.
- `loop.before.1/2`: verify the last signature on whatever manifest currently covers `subtract.ing/`, surface any unsigned drift to the governor. If drift exists, stop — `loop.before.3` is the governor's call (sign / continue / abort).

## 1. Draft the file (Rousseau — drafts, does not publish)
- Author `~/subtract.ing/<path>/NEWFILE.txt` with Edit/Write. This is staging, reversible → no permission needed (`feedback_stop_asking_on_reversible`).
- Content rule: this file is now load-bearing and canonical under the signing key's domain (`reflex.5`). Treat the GitHub mirror as a mirror, never as the source.
- If drafting needs heavy/parallel work, offload to Emile via `ssh m2mini "claude -p '...'"` — never spawn a subagent. Emile is not a publisher either.

## 2. Human gate: sign it (governor's machine, governor's hands)
This is the one step the agent does **not** perform (`boundary`, `authority.source = the human`, `loop.after.2`). Agent prepares the exact command; governor runs it on the box holding the private key:

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file ~/subtract.ing/<path>/NEWFILE.txt
```

Produces `NEWFILE.txt.sig` (an SSH signature, namespace `file`, principal `jnous` — the formation signing key per memory). Warn the governor first that this is the human gate and that a macOS keychain prompt for the key passphrase may appear (`feedback_warn_human_gates`).

## 3. Verify locally before anything leaves the node (agent — required)
`reflex.4` / `loop.before`: an assertion of authenticity that will block a stranger's trust counts as an action — verify with a live read first.

- Ensure an `allowed_signers` line exists mapping the principal to the public key:
  `jnous ssh-ed25519 AAAA...` (this file is itself canonical content that must be published — see step 4).
- Run:
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s ~/subtract.ing/<path>/NEWFILE.txt.sig < ~/subtract.ing/<path>/NEWFILE.txt
```
- Expect `Good "file" signature for jnous`. If it doesn't verify, stop — do not publish, do not narrate around it (`fail.confabulation`, `fail.drift`).

## 4. Publish to the canonical domain (Surface executes the push; outward-facing → confirm first)
- Rousseau drafts, hands off simply; Surface is the governor terminal that runs the publish (`feedback_draft_rousseau_execute_surface`). Pushing an *already-signed* artifact is infra, not a new human gate (`feedback_human_gate_scope`) — but it's an externally visible mutation, so name it to the governor and get the go-ahead before pushing (`feedback_stop_asking_on_reversible`).
- Push three things together to the host that actually serves `subtract.ing` (the signing key's domain — that web root is canonical, not the git host):
  - `NEWFILE.txt`
  - `NEWFILE.txt.sig`
  - `allowed_signers` (so a stranger can get the verifying key from the same canonical domain, not from a model or a chat log — `feedback_reviewer_convergence_is_not_verification`)
- Mirror to the GitHub repo if one exists, explicitly as a mirror. A git host is never the address of record (`reflex.5`).

## Machines
- **Rousseau (01):** drafts, holds canonical `~/subtract.ing/` and `~/human/`, runs the local `ssh-keygen -Y verify`. Does not push to the public host.
- **Governor's keyholding machine:** runs `ssh-keygen -Y sign`. Nothing else in this flow.
- **Surface:** executes the push to the canonical host.
- **Emile (m2mini):** optional drafting muscle via `claude -p`. Never publishes.
- **Media (acer1660ti):** warm backup/mirror tier only. Never canonical, never the publisher. No inference on it either.

## 5. Close the loop (Rousseau, then governor)
- `loop.after.1`: update the manifest covering `subtract.ing/` to include `NEWFILE.txt` and its `.sig`.
- `loop.after.2`: governor re-signs the manifest with `ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file MANIFEST`. Agent prepares, human signs.
- Optionally refresh the SDXC air-gap snapshot if this file belongs in the frozen tier.

## How a stranger verifies it a year from now
1. Fetch from `https://subtract.ing/...`: `NEWFILE.txt`, `NEWFILE.txt.sig`, and `allowed_signers` (all from the canonical domain — that co-location is the point; the domain *is* the authority root).
2. Run:
```
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s NEWFILE.txt.sig < NEWFILE.txt
```
3. `Good "file" signature for jnous` ⇒ the bytes are exactly what the holder of the `jnous` key signed. Any edit to the `.txt` breaks it.
4. Independent corroboration of the *key* itself: the `jnous` public key / fingerprint is also pinned in `governance.conf` references and the manifest chain on the same domain; a careful verifier checks the fingerprint matches across those, not across three chatbots agreeing.

## Authority boundaries, summarized
- Draft `.txt`, build `allowed_signers`, run `ssh-keygen -Y verify`, update manifest text, mirror-push: **agent**, no gate (reversible / infra).
- `ssh-keygen -Y sign` on the new file and on the manifest: **human only** — that signature *is* the authority; the agent never holds it (`authority.signed`, `boundary`, `loop.after.2`).
- Push to the public `subtract.ing` host: agent may execute, but it's outward-facing — surface it and wait for the governor's nod first.
