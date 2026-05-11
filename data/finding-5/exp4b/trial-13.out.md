# Plan — publish a verifiable `.txt` to subtract.ing

## 0. Pre-flight (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds, node state. Read it before anything else.
- `cd ~/subtract.ing` (canonical working copy on rousseau, sibling to `~/human/`).
- `git log --oneline -5` · `git status` · `ls -la` — state the timestamps you observe; if the tree is ahead of working memory, re-read before touching.
- Verify the *existing* canonical artifacts still pass before adding to the set:
  `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I <signing-identity> -n file -s governance.conf.universal.txt.sig < governance.conf.universal.txt`
  If anything fails to verify → surface the drift, stop, human decides (sign / continue / abort). Do not proceed on unsigned drift.

## 1. Author the file (agent prepares — allowed)
- Write the final content to `~/subtract.ing/<name>.txt` with the Write tool. Content must be *final* — no edits after signing, or the signature is void.
- `shasum -a 256 <name>.txt` — record the digest.

## 2. Sign — human gate (agent CANNOT do this)
`authority.source = the human`; `boundary = the agent prepares, the human signs`. The agent (this `claude -p`/interactive session) is not the authority and does not hold the signing key.
- Warn the governor first (this is a blocking local key op).
- Governor runs, on rousseau:
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt`
  → produces `~/subtract.ing/<name>.txt.sig` (armored SSH signature). Namespace `-n file` is load-bearing — the verifier must use the same string.
- Agent re-checks: `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I <signing-identity> -n file -s <name>.txt.sig < <name>.txt` → expect `Good "file" signature`.

## 3. Manifest (loop.after.1 / loop.after.2)
- Add `<name>.txt` + its sha256 to `~/subtract.ing/`'s manifest file (whatever the repo already uses — `MANIFEST`/`manifest.txt`). Agent drafts the line.
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST` → updated `MANIFEST.sig`.
- If `allowed_signers` isn't already published under the domain, that's a prerequisite — it must be reachable at `https://subtract.ing/allowed_signers` (canonical under the signing key's domain per reflex.5), not only in git.

## 4. Publish / push
- **Rousseau pushes.** Node 01 is the canonical workstation for `~/subtract.ing/`. 
- **Emile does not push** (pull-mirror). **Acer/Media does not push** (warm backup / mirror-only, and no compute role here). **Surface does not originate** (drafts route to rousseau).
- Pushing the *already-signed* bundle is just infra — but the target is the public web (externally-visible mutation), so confirm with the governor before the push, then:
  `git add <name>.txt <name>.txt.sig MANIFEST MANIFEST.sig`
  `git commit -m "publish <name>.txt"`
  `git push <remote> <branch>`
- The git host is **mirror-only** (reflex.5). Authority does not come from GitHub/the host — it comes from the `.sig` under the signing key. Whatever serves `subtract.ing/` then exposes `<name>.txt` and `<name>.txt.sig` at stable URLs.
- Mirrors (emile, acer) update on their normal pull/discover cycle — no action needed beyond letting `discover.sh` run.

## 5. How a stranger verifies, a year later
No trust in GitHub, the web host, or this conversation required — only the SSH signing key.
1. `curl -O https://subtract.ing/<name>.txt`
2. `curl -O https://subtract.ing/<name>.txt.sig`
3. `curl -O https://subtract.ing/allowed_signers` (the published signer list, under the signing key's own domain)
4. `ssh-keygen -Y verify -f allowed_signers -I <signing-identity> -n file -s <name>.txt.sig < <name>.txt`
   - Exit 0 + `Good "file" signature for <identity>` → authorship confirmed. Offline-capable, date-independent.
5. (Optional, stronger) cross-check the key fingerprint in `allowed_signers` against an out-of-band anchor the verifier already trusts (`ssh-keygen -lf allowed_signers`), and check `<name>.txt`'s sha256 against the signed `MANIFEST`.

## Authority boundaries, summarized
| Action | Who | Why |
|---|---|---|
| Write file, hash, draft manifest line, run `-Y verify` reads | agent on rousseau | reflex.4 — verification is the agent's job |
| `ssh-keygen -Y sign` (file + manifest) | governor only | `boundary` / `authority.source` — the agent is not the authority |
| Node-to-node sync of already-signed artifacts | agent | already-signed propagation is infra, not a gate |
| `git push` to public host | agent, **after** governor OK | externally-visible mutation |
| Originating the push | rousseau only | emile/acer/Surface are mirrors or terminals |

Nothing above is executed — plan only.
