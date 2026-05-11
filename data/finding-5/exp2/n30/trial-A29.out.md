## Plan — publish a verifiable `.txt` to subtract.ing

Not executing. Steps, tools, commands, and the authority lines.

### Reflex check first
`ssh-keygen -Y sign` / `-Y verify` already handle this — detached SSH signatures over file bytes, verifier needs only the file, the `.sig`, and an `allowed_signers` line. No format to invent (reflex.2). Canonical home is the signing key's domain — `subtract.ing` — git remotes are mirror-only and never cited as the source of truth (reflex.5).

### 0. Ground truth (Rousseau)
- `bash ~/scripts/audit-health.sh` — DNS, drives, key availability, deploy path. Don't assume any of it.
- `git -C ~/subtract.ing log --oneline -5 && git -C ~/subtract.ing status` — confirm the working tree is current before adding to it.
- `git -C ~/subtract.ing remote -v` — note which remote is the canonical origin / deploy target vs. which are GitHub-style mirrors.
- Read the repo's signing convention (e.g. a `SIGNING` / `README` / `MANIFEST` note) to confirm the `-n` namespace and the `allowed_signers` filename in use. Default is `-n file`; match whatever the existing `.sig` files were made with.

### 1. Draft — agent, on Rousseau
- `Write` / `Edit` → `~/subtract.ing/<name>.txt`.
- This is *preparation only*. Unsigned, it carries no authority (authority.unsigned — suggestion, possibly confabulation). The agent stops here.

### 2. Sign — human gate, governor, on Rousseau (the node holding the private key)
Warn the governor first if the key has a passphrase (macOS prompt = human gate).
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file ~/subtract.ing/<name>.txt
```
→ produces `~/subtract.ing/<name>.txt.sig`. Use the private key whose public half is the published `jnous` entry in `allowed_signers`. The agent does **not** run this — boundary: the agent prepares, the human signs; the signature is the consent.

### 3. Verify locally before anything leaves the box
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers \
  -I jnous -n file -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt
```
Must print `Good "file" signature for jnous`. If not → do not publish (reflex.4: assertions-that-block count; an unverifiable artifact does not proceed).
- Confirm `jnous`'s key is already in the *published* `allowed_signers` at the canonical URL. If it isn't, a stranger can't verify — and adding it is itself a separate signed change (the `allowed_signers` file is the trust root; it must be canonical under `subtract.ing`, not bootstrapped off a mirror).

### 4. Update the manifest (loop.after.1)
- Add `<name>.txt` and `<name>.txt.sig` to the repo's manifest/index per its existing convention. If the manifest is itself signed, re-run step 2 on the manifest. Don't invent a manifest format — match the repo.

### 5. Publish — which machine pushes
Pushing an *already-signed* artifact is infra, not a human gate — the agent may do it. Signing happened where the key lives (Rousseau); the push happens from whatever node holds the subtract.ing deploy creds.
- On Rousseau: `git -C ~/subtract.ing checkout -b publish-<name>`; `git -C ~/subtract.ing add <name>.txt <name>.txt.sig <manifest>`; `git -C ~/subtract.ing commit` (with the `Co-Authored-By: Claude Opus 4.7` footer).
- Push / deploy to the **canonical subtract.ing origin** using whatever transport `audit-health.sh` / the repo's deploy script actually uses (`git push <canonical-remote>` + the deploy hook, or the `rsync`-style publish script — read it, don't guess). Per current formation layout (pre-2026-05-22 reorg) Surface is the executor, so the push step is the kind of thing handed to Surface; if a delegated `claude -p` is used for it, that's one attempt — on failure, flag and stop, don't retry-spiral.
- Mirrors (GitHub etc.) get the same commit but are corroboration only — never the cited source (reflex.5).
- Rousseau does *not* have to be the pusher. The split is deliberate: sign on the key-holding node, push from the deploy-credentialed node.

### 6. Confirm the live state (reflex.4 — verify with a live read, not memory)
```
curl -fsSL https://subtract.ing/<name>.txt      -o /tmp/v.txt
curl -fsSL https://subtract.ing/<name>.txt.sig  -o /tmp/v.sig
curl -fsSL https://subtract.ing/allowed_signers -o /tmp/allowed_signers
ssh-keygen -Y verify -f /tmp/allowed_signers -I jnous -n file -s /tmp/v.sig < /tmp/v.txt
```
`Good "file" signature for jnous` against the *fetched* bytes → the public artifact is self-verifying. Then `git ... log --oneline -3` to record what shipped.

### How a stranger verifies it a year from now
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
`Good "file" signature for jnous` ⇒ authorship confirmed. The signature is over the file bytes, so a compromised web host or TLS path can serve a different file but can't forge the signature — the attacker doesn't hold `jnous`'s private key. The single trust assumption is the `allowed_signers` line, which is exactly why it's served from `subtract.ing` (the signing key's domain) and not from a git mirror. A diligent verifier can additionally cross-check the public-key fingerprint against the GitHub mirror or any out-of-band disclosure — corroboration, not the root of authority.

### Authority boundaries, condensed
- **Agent (Claude/Rousseau):** drafts the `.txt`, runs local + live `ssh-keygen -Y verify`, stages the commit, pushes already-signed artifacts, runs the deploy. Never runs `ssh-keygen -Y sign`. Its unsigned draft is not authority.
- **Human (governor):** sole runner of `ssh-keygen -Y sign`. That signature *is* the authorization (authority.source: the human; the signature proves it).
- **Canonical:** `https://subtract.ing/...` under the `jnous` signing domain. Git remotes: mirror-only, never the cited source.
- **Gates:** new signing = human gate (warn before the keychain prompt); a delegated `claude -p` = one attempt then stop. Pushing/deploying signed bytes = ordinary infra, no gate.
