## Plan: publish a verifiable `.txt` to subtract.ing

Output only — nothing below is executed.

### 0. Preconditions (before touching anything)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds, node state. Don't proceed if subtract.ing serving or the signing key store is degraded.
- `loop.before`: confirm the last manifest signature verifies (`ssh-keygen -Y verify` against the current manifest) and surface any unsigned drift in the web root / repo. Human decides: sign, continue, or abort. The agent does not skip this.
- `reflex.2`: the signature format is **not invented** — it is `ssh-keygen -Y sign` (SSH signature, namespace-scoped). Stock OpenSSH on the verifier's box can check it. No custom scheme.

### 1. Author the file (agent, on Rousseau)
- Write `newdoc.txt` in the subtract.ing working tree (the canonical checkout under the signing key's domain — not a `/tmp` scratch copy, per the hosuni.c discipline generalized: canonical path only).
- `wc -l newdoc.txt`, `sha256sum newdoc.txt` — record the hash; state it.
- `git add newdoc.txt` and stage a commit, but **do not commit-and-push yet** — the artifact isn't load-bearing until it's signed (`reflex.4`: unsigned = suggestion only).

### 2. The signing boundary — agent stops here
- `boundary` / `authority.source`: the agent prepares; **the human signs**. The agent does not run `ssh-keygen -Y sign`, does not touch the private key, does not switch models or keys to "help." Signing is governor territory.
- The human runs, on whichever node holds the signing key (Rousseau is the governor's workstation, so normally here):
  ```
  ssh-keygen -Y sign -f ~/.ssh/<signing_key> -n subtract.ing newdoc.txt
  ```
  → produces `newdoc.txt.sig` (a `-----BEGIN SSH SIGNATURE-----` block). Use a **stable namespace** (`-n subtract.ing`) and keep using it forever; verifiers must pass the same `-n`.
- Human confirms locally before publish:
  ```
  ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n subtract.ing -s newdoc.txt.sig < newdoc.txt
  ```

### 3. The trust root: `allowed_signers` under the domain
- `reflex.5`: the canonical artifact set lives under the **signing key's domain**, served from `https://subtract.ing/`. The GitHub repo is a **mirror only** — a verifier who trusts the GitHub copy alone has verified nothing.
- Publish/maintain at the web root:
  - `https://subtract.ing/.well-known/allowed_signers` — lines of `jns@subtract.ing namespaces="subtract.ing" valid-after="<earlier date>" ssh-ed25519 AAAA...`. If the key ever rotates, the **old** pubkey stays in the file with a `valid-before="<rotation date>"` so a year-old signature still verifies. This file is itself load-bearing → it (or the manifest listing it) must also be signed.
  - `https://subtract.ing/newdoc.txt`
  - `https://subtract.ing/newdoc.txt.sig`
  - the SHA-256 recorded in the signed manifest.

### 4. Which machine pushes, which does not
- **Rousseau pushes the canonical deploy** — it's the archive/governor node and (per audit-health) holds the deploy path to the subtract.ing web root. Mechanism: `rsync -a` / `scp` of `newdoc.txt`, `newdoc.txt.sig`, updated `allowed_signers`, updated manifest to the serving location; or `git push` to the deploy remote that backs subtract.ing — whichever audit-health says is the live serving path.
- **Emile does not push.** It's the parallel-execution target, not a publishing authority; nothing here is execution-heavy. No subagents.
- **Surface does not push.** Governor terminal only.
- The GitHub mirror push (if done at all) is secondary and explicitly labeled mirror — it never becomes the thing a verifier is pointed at.

### 5. Close the loop
- `loop.after`: update the manifest (add `newdoc.txt` + its hash + sig path), then the human signs the manifest (`ssh-keygen -Y sign -n subtract.ing manifest`). Publish the new manifest + `.sig`. Session isn't done until the manifest is signed.

### 6. How a stranger verifies, a year from now
1. `curl -O https://subtract.ing/newdoc.txt` and `curl -O https://subtract.ing/newdoc.txt.sig` — TLS to the domain is the first trust hop (`reflex.5`: the domain is the root, not the git host).
2. `curl https://subtract.ing/.well-known/allowed_signers -o allowed_signers` — and, for paranoia, verify the manifest's signature too so the `allowed_signers` file itself is vouched for by the same key chain.
3. Run, with the **same namespace** used at signing:
   ```
   ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n subtract.ing \
     -Overify-time=20260510 -s newdoc.txt.sig < newdoc.txt
   ```
   `-Overify-time` pinned to the publication date makes the check pass even after a later key rotation, as long as the `valid-after`/`valid-before` window in `allowed_signers` brackets that date.
4. Exit status 0 + `Good "subtract.ing" signature for jns@subtract.ing` ⇒ the file is byte-for-byte what the holder of that key published. Optionally cross-check `sha256sum newdoc.txt` against the signed manifest.

### Authority summary
- Agent: authors content, stages, records hashes, runs the deploy mechanics, drafts the manifest entry, runs *verification*.
- Human: holds the key, runs `ssh-keygen -Y sign` on the file and on the manifest, makes the `loop.before` sign/continue/abort call.
- Domain (`subtract.ing` over HTTPS): the trust root. GitHub: mirror, non-authoritative. Unsigned files in the web root: suggestions, not publications — verifiers should ignore them.
