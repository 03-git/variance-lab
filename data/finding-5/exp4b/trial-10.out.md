## Plan — publish a verifiable `.txt` to subtract.ing

No execution below. Commands are literal templates; paths/identities to confirm against live state first.

### 0. Ground truth
- `bash ~/scripts/audit-health.sh` — read it. Confirm DNS, the signing key is present, and the subtract.ing publish path is reachable before touching anything.

### 1. Foundation check (loop.before)
- `cd ~/subtract.ing` (or the relevant canonical tree) → `git log --oneline -5`, `git status`.
- Verify the last signed state of whatever this file builds on:
  `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous -n file -s <prev>.txt.sig < <prev>.txt`
- Surface any unsigned drift. Governor decides: sign / continue / abort. The agent does not proceed past unverified foundation (reflex.4).

### 2. Draft the file (agent, reversible — no permission needed)
- Write the content to canonical staging on **Rousseau**: `~/human/...` or `~/subtract.ing/runtime/...` depending on where it's meant to live. Rousseau:~/human/ is canonical; this is a staging write, so just do it.
- Pick the final URL path now (e.g. `https://subtract.ing/<name>.txt`) — the signature is over the file bytes, but the published location is what the verifier will fetch.

### 3. Sign — **human gate** (boundary: the agent prepares, the human signs)
- New signing is the one hard human gate. The agent does **not** run this. Hand the governor the exact command:
  ```
  ssh-keygen -Y sign -f ~/.ssh/<jnous signing key> -n file ~/path/<name>.txt
  ```
  → produces `~/path/<name>.txt.sig` (SSHSIG armored).
- Namespace `file` must match what the rest of the formation's `.sig` files use — confirm against an existing `.sig` rather than inventing one (reflex.2; the primitive is `ssh-keygen -Y`, already in use).

### 4. Verify locally before publishing (agent — a live read, not a memory claim)
```
ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous -n file -s ~/path/<name>.txt.sig < ~/path/<name>.txt
```
Expect exit 0 + `Good "file" signature for jnous`. If not, stop — do not publish.

### 5. Publish the trust root (this is what makes it verifiable by a stranger)
- The verifier needs the public key bound to identity `jnous`. That binding must live **under the signing key's own domain** — subtract.ing — not a git host (reflex.5).
- Ensure `https://subtract.ing/allowed_signers` (or equivalent, e.g. the existing `governance.conf.universal`-style canonical path) contains:
  ```
  jnous namespaces="file" ssh-ed25519 AAAA...<pubkey>
  ```
  If the key is already published there, nothing to do. If this introduces a new key, publishing it is itself a signing-domain change — governor confirms.

### 6. Push — from **Rousseau only**
- Rousseau is the governor's workstation and the canonical formation node. It pushes the artifact to whatever serves subtract.ing (web root sync / deploy repo the host pulls), e.g. `rsync -av ~/path/<name>.txt <name>.txt.sig <subtract.ing host/web root>` or a commit to the deploy repo.
- **Emile does not push** canonical content — it's an execution-offload target only (`ssh m2mini "claude -p ..."`), not a publisher.
- **Surface does not push** — pull-only mirror (and being decommissioned 2026-05-22).
- **Media/acer do not push** — mirror/backup tier, never canonical.
- Pushing already-signed bytes across nodes is plain infra; no further gate. Only the *signing* in step 3 was gated.

### 7. Git hosts are mirrors, not the claim
- A `git push` to GitHub (or any git host) is allowed as a mirror but establishes **no authority**. If asked "where is it published," the answer is the subtract.ing URL, not the repo. Don't let a green GitHub mirror stand in for the canonical publish.

### 8. Close the loop (loop.after)
- Update the manifest that lists canonical published files (the same manifest family used for the SDXC/FROZEN snapshots) with `<name>.txt` + its sig + a hash.
- Governor signs the updated manifest the same way (`ssh-keygen -Y sign -n file <manifest>`). Agent prepares, governor signs.

### 9. How a stranger verifies, one year later
1. `curl -O https://subtract.ing/<name>.txt`
2. `curl -O https://subtract.ing/<name>.txt.sig`
3. `curl -O https://subtract.ing/allowed_signers`  ← key bound to `jnous`, served from the signing key's own domain
4. ```
   ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
   ```
5. Exit 0 + `Good "file" signature for jnous` ⇒ authorship confirmed. Trust roots in the fact that the public key and the content are served from subtract.ing; GitHub copies prove nothing. No dependency on Rousseau being online, on any conversation log, or on the agent — just OpenSSH and a TLS fetch.

### Authority boundaries (summary)
| Action | Who | Why |
|---|---|---|
| Draft `.txt`, stage in `~/human/`, prepare commands | agent (Rousseau) | reversible staging writes |
| `ssh-keygen -Y sign` (the `.txt`, the manifest, any new key) | **governor only** | new signing is the human gate; the signature *is* the authority |
| `ssh-keygen -Y verify` before/after | agent | a live read, required before acting (reflex.4) |
| Push signed artifact to subtract.ing host | agent, **from Rousseau** | moving already-signed bytes is infra |
| Mirror to git host | agent, optional | mirror-only, not the canonical publish |
| Push from Emile/Surface/Media | nobody | not publishers |

One open item to resolve against live state before starting: the exact filename of the `jnous` signing key under `~/.ssh/`, the namespace string used by existing `.sig` files, and the concrete deploy path for the subtract.ing document root. `audit-health.sh` plus one `ls ~/.ssh` and one look at an existing `.sig` pins all three.
