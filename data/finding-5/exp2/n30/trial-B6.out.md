## Plan: publish a verifiable `.txt` to subtract.ing

Not executing — plan only. Tool names and commands below; substitute `NAME.txt` and the signer identity.

### 0. Ground truth (before anything)
- `bash ~/scripts/audit-health.sh` — confirm DNS, drives, node state. If subtract.ing origin or `allowed_signers` path is unhealthy, stop here.
- On the repo that backs the site: `git -C ~/subtract.ing status && git -C ~/subtract.ing log --oneline -5` — know what HEAD is before adding to it.
- loop.before: verify the last signature in the manifest with `ssh-keygen -Y verify`, surface any unsigned drift, let the governor decide sign/continue/abort.

### 1. Draft the file (agent may do this)
- Write `~/subtract.ing/NAME.txt`. At this point it is `authority.unsigned` — a suggestion, not load-bearing. Nothing acts on it yet.

### 2. Sign — governor only, not the agent (boundary)
The agent does **not** invoke this. The signature is what proves authorship; the human holds the key.
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/NAME.txt
```
→ produces `NAME.txt.sig` (an SSH signature blob). Namespace `file` must match what the verifier uses.

### 3. Make the verification key reachable under the signing domain (reflex.5)
- The `allowed_signers` file (lines of `identity ssh-ed25519 AAAA...`) must be served from **subtract.ing itself**, e.g. `https://subtract.ing/allowed_signers`. Canonical content lives under the signing key's domain; a copy on GitHub does not count.
- If the key isn't already published there, that publish is a prerequisite — same path, same signing discipline.

### 4. Publish to the canonical origin
- Deploy `NAME.txt` **and** `NAME.txt.sig` to the subtract.ing webroot via the normal site-deploy path (the origin host the governor controls).
- **Which machine pushes:** the node holding the subtract.ing deploy credentials and the governor's signing key — i.e. the governor's workstation (Rousseau, here, with the governor driving the signing step). 
- **Which does not:** 
  - `acer1660ti` — explicitly NOT formation, warm-backup/mirror tier only. It may receive a copy; it does not establish authorship.
  - `m2mini` (Emile) — execution offload, not in the signing domain; does not push canonical content.
  - GitHub / any git host — `git push` is **mirror-only** (reflex.5). It does not make the file authoritative and a verifier should not trust it as the source.
- After deploy, reflex.4: do not claim success from memory — confirm with a live read: `curl -fsS https://subtract.ing/NAME.txt | head` and `curl -fsS -o /dev/null -w '%{http_code}\n' https://subtract.ing/NAME.txt.sig`.

### 5. Close the loop
- loop.after.1: add `NAME.txt` (and its `.sig`) to the manifest.
- loop.after.2: sign the updated manifest with `ssh-keygen -Y sign` (governor).

### How a stranger verifies it a year later
```
curl -O https://subtract.ing/NAME.txt
curl -O https://subtract.ing/NAME.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <signer-identity> -n file -s NAME.txt.sig < NAME.txt
```
- Exit 0 + "Good signature" ⇒ the file is byte-for-byte what the holder of the key in `allowed_signers` signed.
- The verifier must fetch `allowed_signers` from `subtract.ing` (the signing key's domain), not from a git mirror — otherwise a mirror operator could swap the key. Cross-check TLS chain on that fetch.
- Optional robustness: confirm the same key via a second channel the governor controls (DNS TXT on subtract.ing, a signed pin elsewhere), so a one-year-later compromise of the webroot alone can't forge authorship.

### Authority boundaries in play
- `authority.unsigned` — the draft in step 1 binds nothing until step 2.
- boundary / "the agent prepares, the human signs" — agent does steps 0,1,4,5-manifest-edit; governor does every `ssh-keygen -Y sign`.
- reflex.5 — canonical = subtract.ing; git hosts mirror-only; acer mirror-only.
- reflex.4 — the post-deploy "it's live" claim is an action; verify with `curl`, don't assert from memory.
