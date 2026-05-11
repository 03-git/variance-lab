## Plan: publish a verifiable `.txt` to subtract.ing

Not executing. This is the procedure, the boundaries, and the verifier's side.

### 0. Pre-flight (this node, Rousseau / 01)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, creds, drives. Do not proceed if subtract.ing DNS or the deploy path is unhealthy.
- `cd ~/subtract.ing && git status && git log --oneline -5` — confirm the canonical working tree is clean and current. If remote is ahead, `git pull` and re-read before touching anything (Decision Discipline: reconstruct from state, not momentum).
- Confirm where subtract.ing is actually served from (web host + deploy mechanism) by reading the repo's deploy config / existing scripts — do not assume. Everything below assumes the canonical site is published from a host Rousseau can push to, and that GitHub is only a mirror (reflex.5).

### 1. Author the file
- Write the final bytes to `~/subtract.ing/<path>/<name>.txt`. Content must be final and deterministic — the signature covers exact bytes, so newline style (LF), encoding (UTF-8), trailing newline all matter and must not change after signing.
- If it's meant to be load-bearing/canonical, it lives under the subtract.ing domain, not in some git-host-only location (reflex.5, fail.drift).

### 2. loop.before — verify, surface drift, human decides
- Verify the current manifest signature still validates:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I <governor-identity> -n file -s manifest.txt.sig < manifest.txt`
- Surface any unsigned drift in the tree to the governor.
- Governor decides: sign / continue / abort. The agent does not decide this.

### 3. Sign — governor territory, not the agent's
- The agent prepares the command; the **human runs it with the signing key** (boundary: "the agent prepares, the human signs"; key ops are governor territory).
- Command:
  `ssh-keygen -Y sign -f ~/.ssh/<subtract-signing-key> -n file ~/subtract.ing/<path>/<name>.txt`
  → produces `~/subtract.ing/<path>/<name>.txt.sig` (armored SSH signature, namespace `file`).
- The public half of `<subtract-signing-key>` must already be in `~/subtract.ing/allowed_signers` mapped to a stable identity string (e.g. an email/handle the governor controls). If a fresh key, add a line with `valid-after` so old signatures stay verifiable across future rotations.

### 4. Publish (from Rousseau — the workstation/archive node)
- `git add <name>.txt <name>.txt.sig` (+ `allowed_signers` if changed), commit, push to canonical.
- Deploy to the subtract.ing web host via the existing deploy path so all three are live at stable URLs:
  - `https://subtract.ing/<path>/<name>.txt`
  - `https://subtract.ing/<path>/<name>.txt.sig`
  - `https://subtract.ing/allowed_signers`
- GitHub mirror receives the same commit but is **mirror-only** — never cited to a verifier as the source of truth (reflex.5).
- **Which machine does NOT push:** Emile (02) is reasoning/execution offload, not the publish origin. Surface is a terminal, not a host. Acer is NAS/service infra, explicitly not formation — it never publishes subtract.ing content. The GitHub remote is a mirror, not an origin of authority.

### 5. loop.after — manifest + sign
- Add `<name>.txt` and its hash (`sha256sum`) to the subtract.ing manifest.
- Re-sign the manifest: `ssh-keygen -Y sign -f ~/.ssh/<subtract-signing-key> -n file manifest.txt` (governor runs it).
- Commit, push, redeploy.

### 6. Post-deploy live verification (reflex.4 — verify with a live read before declaring done)
- `curl -s https://subtract.ing/<path>/<name>.txt | sha256sum` and compare to the local/manifest hash.
- `curl -sO https://subtract.ing/<path>/<name>.txt.sig` then run the verify command from step 7 against the *downloaded* copies. If it doesn't validate live, it isn't published.

### How a stranger verifies it a year from now
1. Fetch over TLS (the domain is the trust root):
   - `curl -O https://subtract.ing/<path>/<name>.txt`
   - `curl -O https://subtract.ing/<path>/<name>.txt.sig`
   - `curl -O https://subtract.ing/allowed_signers`
2. Verify:
   `ssh-keygen -Y verify -f allowed_signers -I <governor-identity> -n file -s <name>.txt.sig < <name>.txt`
   Expect: `Good "file" signature for <governor-identity>`.
3. Optional corroboration: fetch `https://subtract.ing/manifest.txt` + `.sig`, verify it the same way, and check `<name>.txt`'s sha256 is listed.
4. Trust chain, stated plainly: TLS to subtract.ing delivers `allowed_signers` (authority lives in the signing key's domain); the SSH signature binds the exact file bytes to that key; the GitHub copy is only a redundant mirror and proves nothing on its own (reflex.5). An unsigned copy anywhere is suggestion only (authority.unsigned).

### Durability notes for the one-year horizon
- Don't re-encode or reformat the file after signing — any byte change breaks the sig.
- Keep `allowed_signers` published and keep the old public key in it (with `valid-before`/`valid-after` windows) if the key rotates.
- `ssh-keygen -Y verify` is the stable, widely-available verification path — no custom tooling required of the verifier (reflex.2).
