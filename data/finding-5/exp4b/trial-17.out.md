## Plan: publish a verifiable `.txt` to subtract.ing

### 0. Preconditions (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds before touching anything.
- In `~/subtract.ing`: `git log --oneline -5`, `git status` — confirm the working tree matches canonical, no unsigned drift sitting in it.
- Confirm the signing primitive *before* inventing anything (reflex.2): `ssh-keygen -Y sign` / `-Y verify` with the `jnous` key is the format. No bespoke signature scheme.

### 1. Draft (Rousseau drafts)
- Write the file at `~/human/<area>/<name>.txt` on **Rousseau** (this node — canonical for formation human-authored work). Use `Write`/`$EDITOR`. At this point it is `authority.unsigned` — a suggestion, nothing acts on it.
- Stage it into the publish tree: `~/subtract.ing/<path>/<name>.txt`.

### 2. Sign — HUMAN GATE (boundary: the agent prepares, the human signs)
I do **not** run this. I surface the staged file and stop. The governor runs:
```
ssh-keygen -Y sign -f ~/.ssh/<jnous_key> -n file ~/subtract.ing/<path>/<name>.txt
```
→ produces `<name>.txt.sig` (SSH signature, namespace `file`). New signing is the one irreducible human action; pushing it afterward is just infra.

### 3. Verify before acting (reflex.4, loop.before.1)
Before publishing, confirm the signature actually verifies — assertions that block count as actions, so this is a live read, not a memory claim:
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file \
  -s ~/subtract.ing/<path>/<name>.txt.sig < ~/subtract.ing/<path>/<name>.txt
```
Must print `Good "file" signature for jnous`. If not — stop, do not publish.

### 4. Manifest (loop.after.1 / .2)
- Add `<name>.txt` + `<name>.txt.sig` to the subtract.ing manifest.
- Governor re-signs the manifest the same way (`ssh-keygen -Y sign ... MANIFEST`). The manifest is itself load-bearing, so it cannot be left unsigned.

### 5. Publish — which machine pushes
- **Rousseau pushes.** subtract.ing is canonical under the signing key's domain and is served from this node (`subtract→m1studio:8087`). `git -C ~/subtract.ing add <path>/<name>.txt <path>/<name>.txt.sig MANIFEST* && git commit && <deploy step>` so it appears at `https://subtract.ing/<path>/<name>.txt`.
- **Surface does not push** — it pulls.
- **Emile does not push** — pull-mirror, picks it up on its next `discover.sh` sync.
- **Media (acer1660ti) does not push** — warm backup / mirror tier only.
- **GitHub (or any git host) is mirror-only** (reflex.5). A copy may land there, but it is never the authority and a verifier should not be pointed at it.

### 6. How a stranger verifies it a year from now
1. Fetch all three from the signing key's domain (not a git mirror):
   - `curl -O https://subtract.ing/<path>/<name>.txt`
   - `curl -O https://subtract.ing/<path>/<name>.txt.sig`
   - `curl -O https://subtract.ing/allowed_signers`  ← `jnous`'s public key, published canonically alongside the content
2. Run:
   ```
   ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
   ```
3. `Good "file" signature for jnous` → the human authored it. The signature is the proof of authority; the agent that prepared the file is not in the trust path. Optional cross-check: the manifest entry for `<name>.txt` and the manifest's own signature.

### Authority boundaries in force
- `authority.unsigned` → do not act: between step 1 and step 3 the file is a draft, nothing downstream consumes it.
- `boundary` → agent stages (steps 1, 4-staging, 5); human signs (steps 2, 4-signing). I never invoke `ssh-keygen -Y sign`.
- `reflex.5` → canonical = subtract.ing under the `jnous` domain; git hosts mirror only.
- `loop.before` → verify last signature + surface any drift in `~/subtract.ing` before the publish commit; governor decides sign/continue/abort.
- `loop.after` → manifest updated and re-signed, or the session isn't done.
