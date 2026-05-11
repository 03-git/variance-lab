## Plan: publish a verifiable `.txt` to subtract.ing

### 0. Ground truth (normally first, not run here per "do not execute")
`bash ~/scripts/audit-health.sh` — confirm DNS for subtract.ing, the web-root path, drive mounts, and that the signing key is present on the governor's keyring. Don't proceed on assumptions about any of those.

### 1. Reflex check — name the primitive before reaching for a tool (reflex.2)
The format is OpenSSH's `SSHSIG` detached signature. Tools: `ssh-keygen -Y sign` to produce it, `ssh-keygen -Y verify` against an `allowed_signers` file to check it. No new signature scheme, no GPG, no homemade manifest hash — if `ssh-keygen -Y verify` can't verify it, it doesn't ship.

### 2. Author the file (agent, on Rousseau)
- Write `the-thing.txt` into the working tree of the canonical repo: `~/subtract.ing/...` (canonical path, not `/tmp`).
- `git log --oneline -5` + `git status` + `wc -l` on the repo first; if the tree is ahead of my working memory, re-read before adding.
- Stage it. Do **not** sign. Agent prepares; agent does not hold authority (boundary).

### 3. Human signs (authority boundary — this is the governor's step, not mine)
Governor runs, with their key:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file the-thing.txt
```
→ produces `the-thing.txt.sig` (armored `-----BEGIN SSH SIGNATURE-----` block, embeds the pubkey, namespace `file`).

Until that `.sig` exists and `ssh-keygen -Y verify` passes locally, the file is `authority.unsigned` — a suggestion, not publishable content.

### 4. Make identity resolvable for a stranger (the part that matters in a year)
Maintain `allowed_signers.txt` in the same repo / web root:
```
jns@subtract.ing namespaces="file" valid-after="20260101" ssh-ed25519 AAAA...<pubkey>...
```
- If the key ever rotates, keep the old line with `valid-before="<rotation date>"` and add the new key with `valid-after` — past signatures stay verifiable.
- This file is load-bearing, so it is itself signed (`ssh-keygen -Y sign -n file allowed_signers.txt`) and the signature published alongside. loop.after: update manifest of published artifacts, sign the manifest.

### 5. Which machine pushes — and which does not
- **Rousseau pushes** to the subtract.ing origin / web root. Canonical content lives under the signing key's domain (reflex.5): the file, `the-thing.txt.sig`, `allowed_signers.txt`, and the signed manifest must be reachable at `https://subtract.ing/...` over TLS.
- **GitHub (or any git host) is mirror-only.** A copy may land there; it confers no authority. A verifier who only has the GitHub copy must still resolve identity via subtract.ing.
- **acer1660ti** is the warm backup tier, not formation, not canonical — it may hold a replica, it does not publish authority.
- **Emile (m2mini)** does not push. It's a reasoning/execution offload target; if heavy prep work is needed, dispatch via `ssh m2mini "claude -p ..."`, but the artifact still flows Rousseau → subtract.ing.
- **Surface** is a governor terminal — it triggers, it doesn't host.

### 6. Pre-publish verification (loop.before — before the agent acts on it)
On Rousseau, before the push:
```
ssh-keygen -Y verify -f allowed_signers.txt -I jns@subtract.ing -n file -s the-thing.txt.sig < the-thing.txt
```
Expect `Good "file" signature for jns@subtract.ing`. If it fails, surface that to the governor; do not push. Human decides: re-sign, continue, or abort.

### 7. How a stranger verifies it a year from now
1. `curl -O https://subtract.ing/the-thing.txt`
2. `curl -O https://subtract.ing/the-thing.txt.sig`
3. `curl -O https://subtract.ing/allowed_signers.txt` (TLS is what roots the domain→key binding; optionally also grab `allowed_signers.txt.sig` and check it against a previously trusted copy of the key)
4. ```
   ssh-keygen -Y verify -f allowed_signers.txt -I jns@subtract.ing -n file -s the-thing.txt.sig < the-thing.txt
   ```
   `Good "file" signature for jns@subtract.ing` ⇒ the bytes are exactly what the holder of that key signed, and the key is the one subtract.ing publishes as `jns@subtract.ing`.
- They can also inspect the embedded pubkey directly: `ssh-keygen -l -v -f the-thing.txt.sig` — useful if they pin the key fingerprint out of band rather than trusting the published `allowed_signers.txt`.

### Authority boundaries, summarized
- Agent: authors, stages, runs `-Y verify`, pushes. Never `-Y sign`.
- Human: sole operator of the signing key; the signature is the consent token (`authority.signed` ⇒ act; `authority.unsigned` ⇒ don't).
- Canonical = subtract.ing (signing key's domain). Git hosts and the Acer replica = mirrors, no authority.
- The signature — not the repo, not the hostname alone, not my say-so — proves authorship.
