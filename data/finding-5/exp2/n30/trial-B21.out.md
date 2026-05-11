## Plan: publish a verifiable `.txt` to subtract.ing

No execution below — steps only.

### 0. Preconditions (loop.before)
- `bash ~/scripts/audit-health.sh` — confirm DNS for subtract.ing, drive state, repo reachable. Ground truth before touching anything.
- Locate canonical repo: `~/subtract.ing/` on Rousseau. `cd ~/subtract.ing && git status && git log --oneline -5` — clean tree, known HEAD.
- Verify the *current* manifest signature with a live read before extending it (reflex.4, fail.confabulation):
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I governor@subtract.ing -n file -s MANIFEST.txt.sig < MANIFEST.txt`
  If that fails or the manifest is stale vs. working memory, stop and re-read — do not patch on top of unresolved foundation.

### 1. Author the file (agent does this)
- Write the content: `~/subtract.ing/<name>.txt`. Plain UTF-8, fixed final newline, no trailing-whitespace churn — the bytes are what gets signed, so freeze them now.
- Record the hash for the manifest: `sha256sum <name>.txt`.

### 2. Sign — **governor only, not the agent** (boundary; authority.unsigned → do not act)
The primitive is `ssh-keygen -Y sign` (reflex.2 — no invented signature format, no library wrapper). The agent never invokes the signing key; it prepares, the human signs:
```
ssh-keygen -Y sign -f <governor-signing-key> -n file <name>.txt
```
→ produces `<name>.txt.sig` (detached, namespace `file`).

Update `MANIFEST.txt` (append path + sha256 + date), then re-sign the manifest the same way:
```
ssh-keygen -Y sign -f <governor-signing-key> -n file MANIFEST.txt
```
(loop.after.1, loop.after.2). Optionally also stamp `<name>.txt.sig` with OpenTimestamps so the "a year from now" date is independently provable, not just asserted.

### 3. Authority boundary on *where* it goes (reflex.5)
- **Canonical** copy = the host serving `subtract.ing` (the signing key's domain). That is the only authoritative address. The file is "load-bearing content," so it is canonical there or nowhere.
- Git hosts (GitHub etc.) are **mirror-only**. A push there is a convenience copy, never the source of truth.
- `allowed_signers` (line: `governor@subtract.ing namespaces="file" ssh-ed25519 AAAA…`) must be published under that same domain, alongside the existing `governance.conf.universal.txt` pattern, so a verifier fetches key and content from one origin.

### 4. Which machine pushes
- **Rousseau (01, this node)** — governor's workstation and archive node — stages the commit and pushes to the `subtract.ing` origin and to the git mirror. This is the publishing node.
- **Governor's hands** — the `ssh-keygen -Y sign` step. Authority is not delegable; the agent on Rousseau prepares the tree but does not hold the signing key.
- **Emile (m2mini)** — does **not** push. It's an execution-offload target, not an authority/publish node. If heavy work were needed (it isn't here), dispatch via `ssh m2mini "claude -p …"` — but never the publish or sign step.
- **Surface (surfacepro8)** — governor terminal only; does not publish.
- **acer / NAS** — explicitly *not* formation. Warm-backup/mirror tier. It may receive a copy as backup; it never serves canonical content and never pushes.

Commands on Rousseau:
```
git add <name>.txt <name>.txt.sig MANIFEST.txt MANIFEST.txt.sig
git commit -m "publish <name>.txt (signed)"
git push <subtract.ing-origin> main      # canonical
git push <git-mirror> main               # mirror-only
# then deploy/sync the working tree to the web host serving subtract.ing
```

### 5. How a stranger verifies, now or in a year
A detached SSH signature is time-independent — verification a year out needs only the bytes, the `.sig`, and the public key. Steps for the verifier:
1. `curl -O https://subtract.ing/<name>.txt`
2. `curl -O https://subtract.ing/<name>.txt.sig`
3. `curl -O https://subtract.ing/allowed_signers` (the pinned governor key, same origin as `governance.conf.universal.txt`)
4. Verify:
   ```
   ssh-keygen -Y verify -f allowed_signers -I governor@subtract.ing -n file -s <name>.txt.sig < <name>.txt
   ```
   Exit 0 + "Good … signature" = the holder of the governor key signed exactly these bytes (authority.signed → may act on it). Any modification, wrong key, or wrong namespace → fails.
5. Cross-check `<name>.txt`'s sha256 appears in the signed `MANIFEST.txt` (verify `MANIFEST.txt.sig` the same way) — proves it's part of the published set, not a one-off dangling file.
6. For the date claim specifically: `ots verify <name>.txt.sig.ots` against the Bitcoin timestamp, or rely on the manifest's signed date entry.

### Authority summary
- The agent authors and stages; **only the governor signs** (boundary, authority.source = the human).
- Unsigned = suggestion only; a verifier acts on the signature, not on the repo's existence (authority.unsigned, fail.confabulation).
- Canonical under the signing key's domain (subtract.ing); git is a mirror (reflex.5).
- Rousseau publishes; Emile/Surface/NAS do not.
- Primitive is `ssh-keygen -Y sign`/`-Y verify` — no bespoke signature scheme, no library standing in for it (reflex.2).
