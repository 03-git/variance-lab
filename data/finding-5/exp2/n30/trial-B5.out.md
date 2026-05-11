## Plan: publish a verifiable .txt to subtract.ing

Not executing. This is the procedure, the tool names, the commands, and the authority lines.

### 0. Preflight (before touching anything)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds, node state. Don't proceed if it's unhappy.
- On the canonical repo: `cd ~/subtract.ing && git status && git log --oneline -5` — confirm clean tree, no unsynced drift (loop.before.1/2).
- Confirm where subtract.ing's web root actually deploys from via a live read, not memory (reflex.4). In this context that's the governor's workstation (Rousseau). If the live read says otherwise, that node is the one that publishes — not this one.

### 1. Authority boundaries (who does what)
- **The agent (me):** authors the draft, computes the SHA-256, drafts the verifier command, stages files, can run the *mirror* push. The agent never runs `ssh-keygen -Y sign`. (`boundary`: the agent prepares, the human signs.)
- **The governor (human):** runs `ssh-keygen -Y sign`, holds `~/.ssh/id_ed25519`, controls the subtract.ing domain/TLS, and makes the publish decision (loop.before.3: sign, continue, or abort).
- The file becomes canonical/actionable only once `ssh-keygen -Y verify` passes against the *published* allowed_signers (`authority.signed`). Until then it's a draft.

### 2. Author the file
- Write it at the path that maps to the served URL, e.g. `~/subtract.ing/<name>.txt` → `https://subtract.ing/<name>.txt` (same shape as `governance.conf.universal.txt`).
- Record the digest: `shasum -a 256 ~/subtract.ing/<name>.txt` (macOS/ARM64; `sha256sum` on the Debian box). Keep this value for the manifest.

### 3. Sign — governor only
- Signing tool is `ssh-keygen -Y` (reflex.2: the format is already verifiable, don't invent one).
- Governor runs:
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt`
  → produces `~/subtract.ing/<name>.txt.sig` (an `SSHSIG` armored blob), namespace `file`.
- Ensure the identity→key mapping is published at `~/subtract.ing/allowed_signers` and contains a line pinning the signing key with validity bounds so it survives a year and a future rotation:
  `jns@subtract.ing namespaces="file" valid-after="20260101",valid-before="20270601" ssh-ed25519 AAAA... `
  This file is canonical **because it lives under the signing key's own domain** (reflex.5). A copy on GitHub does not count.

### 4. Self-verify before publishing
- Dry-run exactly what a stranger will run:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jns@subtract.ing -n file -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt`
- Expect `Good "file" signature for jns@subtract.ing` and exit 0. If not, abort — do not publish (reflex.4).

### 5. Publish — which machine pushes, which does not
- **Rousseau (this node) publishes**: deploys `<name>.txt`, `<name>.txt.sig`, and the updated `allowed_signers` to the subtract.ing web root. This is the canonical act — the content is canonical under the signing key's domain.
- **The GitHub mirror does not establish authorship.** Pushing the repo there is fine for redundancy, but it's mirror-only (reflex.5). A verifier must not be sent there for the key.
- **Emile (m2mini) does not push.** It's the execution-offload node, no publish authority. If heavy work were needed it gets a prompt via `ssh m2mini "claude -p ..."`, not the signing key.
- **Surface does not push.** Governor terminal only.
- After deploy, confirm with a live fetch from the public URL (not the local file): `curl -fsSL https://subtract.ing/<name>.txt | shasum -a 256` and compare to step 2's digest; `curl -fsSL https://subtract.ing/<name>.txt.sig | head`.

### 6. Post-session (loop.after)
- Append to the archive manifest (`~/subtract.ing/MANIFEST` or the established index — Rousseau is the formation/archive node): filename, SHA-256, signer identity, UTC date, source URL.
- Governor signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file <manifest>`, then deploy it alongside.
- Commit + push to the git mirror last (mirror, not source of truth).

### 7. How a stranger verifies it a year from now
Needs only OpenSSH (`ssh-keygen` ≥ 8.1) and `curl`:
1. `curl -O https://subtract.ing/<name>.txt`
2. `curl -O https://subtract.ing/<name>.txt.sig`
3. `curl -O https://subtract.ing/allowed_signers`  ← from subtract.ing itself, the signing key's domain
4. `ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s <name>.txt.sig < <name>.txt`
5. Pass condition: prints `Good "file" signature for jns@subtract.ing`, exit code 0. Any byte change to the .txt, wrong namespace, or a key not in `allowed_signers` → failure.
6. Trust chain the verifier should understand: the pubkey is vouched for by being served under `subtract.ing` (TLS + domain control by the author), corroborated by every other signed artifact on that domain (e.g. `governance.conf.universal.txt`) carrying the same key. GitHub is not part of this chain.

### 8. One-year durability notes
- Do not retire/rotate `id_ed25519` without leaving the old public key in `allowed_signers` bounded by `valid-before` covering the publish date — otherwise old signatures stop verifying.
- The domain and its TLS must stay under governor control; the canonical claim rests on it (reflex.5).
- Keep `<name>.txt.sig` adjacent to the file in both web root and mirror.
- Optional strengthening if proof-of-time matters: OpenTimestamps stamp on the SHA-256 (`ots stamp <name>.txt`), published next to the file. The SSH signature + signed dated manifest is the baseline; OTS is additive.
