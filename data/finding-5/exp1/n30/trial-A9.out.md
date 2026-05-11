## Plan: publish a signed `.txt` to subtract.ing with year-out verifiability

### 0. Reflex checks before touching anything
- **reflex.2 (memory→signature):** the format is not invented — it's `ssh-keygen -Y sign` / `ssh-keygen -Y verify` (OpenSSH `-----BEGIN SSH SIGNATURE-----`, RFC-ish, ships with every OpenSSH ≥ 8.2). Name it, use it, don't roll a custom scheme.
- **reflex.5 (canonical→signing domain):** the file's canonical home is `subtract.ing` itself (the signing key's domain). Any GitHub/Pages/CDN copy is a mirror, not authority.
- **boundary / feedback_human_gate_scope:** I prepare, stage, and self-verify; the governor runs the one command that touches the private key. Pushing the *already-signed* artifact afterward is plain infra and needs no gate.
- Recon (read-only, no mutation): in `~/subtract.ing` run `git remote -v`, `git log --oneline -5`, look for a deploy script, and `ssh-keygen -Y check-novalidate -n <ns> -s <some-existing>.txt.sig < <some-existing>.txt` to read the **identity string and namespace the formation already uses**. Reuse that convention; don't fork it. Memory says the signing identity is `jnous`-prefixed (`feedback_verify_signatures_before_editing`) — confirm the exact principal, e.g. `jnous@subtract.ing`.

### 1. Prepare the file (Rousseau; agent does this)
- Draft into the canonical tree, e.g. `~/subtract.ing/<path>/foo.txt`.
- Normalize: UTF-8, LF endings, trailing newline. Sanity-check with `file foo.txt` and `cat -A foo.txt | tail`.
- Lock the identity (`-I jnous@subtract.ing`) and namespace (`-n file`, or whatever step 0 revealed) **now** — the verifier must reproduce both exactly.
- Make sure `~/subtract.ing/allowed_signers` exists and contains the signing pubkey line, e.g.:
  `jnous@subtract.ing namespaces="file" ssh-ed25519 AAAA...`
  and that this file is in the set that gets published (a verifier can't use a key they can't fetch).

### 2. Pre-sign loop (`loop.before.*`)
- State observed ground truth: `git status`, `git log --oneline -5`, `wc -l foo.txt`.
- Verify the current head of the manifest chain still passes:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous@subtract.ing -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST`
- Surface any unsigned drift. Governor decides: sign / continue / abort. Do not proceed past unresolved drift.

### 3. Human signs — the gate (governor, on Rousseau only)
Warn first that this hits the private key / ssh-agent and may prompt (`feedback_warn_human_gates`). Commands the **governor** runs:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<path>/foo.txt
# -> ~/subtract.ing/<path>/foo.txt.sig
sha256sum ~/subtract.ing/<path>/foo.txt >> ~/subtract.ing/MANIFEST
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST
# -> regenerated ~/subtract.ing/MANIFEST.sig   (loop.after.1)
```
The agent does **not** run `ssh-keygen -Y sign`.

### 4. Self-verify before publishing (agent, on Rousseau)
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous@subtract.ing -n file -s ~/subtract.ing/<path>/foo.txt.sig < ~/subtract.ing/<path>/foo.txt
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous@subtract.ing -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST
```
Both must print `Good "file" signature for jnous@subtract.ing ...`. If either fails, stop and report — do not publish.
Also drop a `foo.txt.VERIFY.txt` next to the file containing the **exact** verify command (identity + namespace baked in), so a stranger doesn't have to guess.

### 5. Publish — who pushes
- **Rousseau pushes.** It's the canonical archive node and the governor's workstation; the publish originates here. Push the set: `foo.txt`, `foo.txt.sig`, `foo.txt.VERIFY.txt`, updated `MANIFEST` + `MANIFEST.sig`, and `allowed_signers` (at a stable URL, e.g. `https://subtract.ing/allowed_signers`). Use whatever deploy `~/subtract.ing` already wires (rsync to docroot / git push to the serving repo) — this is mirror plumbing, fine post-signing.
- **Surface does not push.** Terminal / pull-only.
- **Emile does not push.** Pull-mirror of canonical.
- **Media (acer1660ti) does not originate.** Warm backup + git mirror tier — mirror-only by reflex.5. If subtract.ing is fronted by a git host or CDN, that's also just a mirror; the signature is what makes any mirror trustworthy.
- `loop.after.2`: commit the canonical repo, note the session under `~/human/sessions/`.

### 6. How a stranger verifies, a year out
On any box with OpenSSH ≥ 8.2, no other dependencies:
```
curl -O https://subtract.ing/<path>/foo.txt
curl -O https://subtract.ing/<path>/foo.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file -s foo.txt.sig < foo.txt
```
Expected: `Good "file" signature for jnous@subtract.ing with ED25519 key SHA256:<fp>`.

Trust chain they can walk:
1. The verifying key is published under `subtract.ing` — the signing key's **own** domain (reflex.5), so it's self-certifying for that domain.
2. Cross-check the fingerprint: the same key signs `https://subtract.ing/governance.conf.universal.txt`, `MANIFEST`, and the formation's other published `.sig` artifacts. Consistent reuse across independently-fetched files = the key is the domain's, not a one-off.
3. Second, independent path: fetch `MANIFEST` + `MANIFEST.sig`, verify the manifest signature, then confirm `sha256sum foo.txt` equals the manifest line. This holds even if the per-file `.sig` were lost.
4. Nothing in the path needs GitHub, a CA, or a third party. HTTPS authenticates the *transport*; the OpenSSH signature authenticates the *authorship* and survives domain transfer, CDN swap, or mirror (`authority.signed`).

### 7. Caveats to bake in now
- `-n` namespace and `-I` identity must match signing exactly — that's why they're shipped in `VERIFY.txt`.
- If the signing key rotates within the year, keep the old key in `allowed_signers` with `valid-before="<timestamp>"` (and sign with `valid-after`) so the year-old `.sig` still validates against a key the verifier can see.
- `ssh-keygen -Y check-novalidate -n file -s foo.txt.sig < foo.txt` is the fallback if the verifier can't get `allowed_signers` — it confirms the signature is well-formed and shows the signing key fingerprint, which they can then match against the published one by hand.
