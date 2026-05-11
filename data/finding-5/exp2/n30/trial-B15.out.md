# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. This is the procedure only. (In a real run this is preceded by `bash ~/scripts/audit-health.sh` and a `git log/status/wc -l` on whatever canonical tree is touched — skipped here per instruction.)

## 0. Reflex check (before anything)
- **Format**: don't invent a signature scheme. The primitive is OpenSSH's signed-message format — `ssh-keygen -Y sign` / `-Y verify`, armored `SSHSIG`, namespace `file`. A stranger with stock OpenSSH (≥8.2) can verify it; nothing else needed. (reflex.2 satisfied: the format is verifiable by `ssh-keygen -Y verify`.)
- **Canonical domain**: the authoritative copy lives under `subtract.ing` (the signing key's domain). GitHub or any other git remote is **mirror-only** (reflex.5). A `git push` is not "publishing."

## 1. Pre-flight (loop.before)
- Verify the current manifest signature before touching the tree:
  `ssh-keygen -Y verify -f ~/.subtract/allowed_signers -I <governor-id> -n file -s MANIFEST.sig < MANIFEST`
- `git status` on the site tree; surface any unsigned drift already present.
- Governor decides: sign existing drift, continue, or abort (loop.before.3).

## 2. Author the file (agent may do this)
- Write the content to the site tree, e.g. `/Users/jns/subtract.ing/<name>.txt`.
- Fix the bytes now — the signature covers exact bytes. No post-sign edits, no CRLF surprises, trailing newline decided up front.
- `sha256sum <name>.txt` — record it.

## 3. Sign — **governor only, not the agent** (authority boundary)
- The agent prepares; the human signs. The agent does **not** run this with the private key:
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file <name>.txt`
  → produces `<name>.txt.sig`.
- Use the ed25519 key (no expiry on the signature itself, so "a year from now" is fine; if a validity window is wanted, `-Ovalid-after=... -Ovalid-before=...`, but a year-out verifier argues for *no* upper bound).
- Until this step completes the `.txt` is `authority.unsigned` — suggestion only.

## 4. Publish artifacts (what actually goes on the wire)
Three files must be reachable under the canonical domain:
1. `https://subtract.ing/<name>.txt`
2. `https://subtract.ing/<name>.txt.sig`
3. `https://subtract.ing/allowed_signers` — the line `<governor-id> ssh-ed25519 AAAA...` so a stranger has the public key. (This is the trust anchor; ideally the same key is also discoverable via a second channel — the governance domain / DNS TXT / `meta` page — so it isn't pure TOFU.)

## 5. Push — which machine
- **Rousseau (01, this box) pushes.** It is the governor's workstation and where the signing key lives; the deploy goes from here to the host serving `subtract.ing` (rsync/scp/ssh deploy, or commit-then-deploy if the web host pulls).
- **Emile (m2mini) does not push.** Compute/parallel node, no authority over the canonical domain.
- **Acer is not formation** — never the source of truth; at most a warm backup tier.
- **Surface** is a terminal, not a publisher.
- Any `git push` to GitHub/etc. happens *after* and is explicitly the mirror, not the publish event.

## 6. Verify live (reflex.4 — verify with a live read before claiming done)
From a clean fetch, not the local tree:
```
curl -fsSL https://subtract.ing/<name>.txt        -o /tmp/v.txt
curl -fsSL https://subtract.ing/<name>.txt.sig    -o /tmp/v.txt.sig
curl -fsSL https://subtract.ing/allowed_signers   -o /tmp/v.signers
ssh-keygen -Y verify -f /tmp/v.signers -I <governor-id> -n file -s /tmp/v.txt.sig < /tmp/v.txt
sha256sum /tmp/v.txt   # matches step 2
```
Exit 0 + matching hash = published. Otherwise it isn't, regardless of what the deploy script said.

## 7. Close the loop (loop.after)
- Add `<name>.txt` + `<name>.txt.sig` to `MANIFEST`.
- Re-sign the manifest (governor): `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file MANIFEST`.
- Deploy the updated `MANIFEST` / `MANIFEST.sig` the same way (step 5).

## 8. How a stranger verifies, a year later
1. `curl -fsSL https://subtract.ing/<name>.txt`, `.../<name>.txt.sig`, `.../allowed_signers`.
2. `ssh-keygen -Y verify -f allowed_signers -I <governor-id> -n file -s <name>.txt.sig < <name>.txt` → exit 0.
3. Confirm the pubkey in `allowed_signers` is the one the governor advertises elsewhere (governance domain / DNS / a previously trusted manifest). That cross-check is what upgrades "some key signed this" to "*the governor* signed this."
4. Optional: `git log` on a mirror shows the same blob hash — corroborating, not authoritative.

Nothing here depends on a CA, a timestamp service, or the git host staying up — only on the three files remaining fetchable and OpenSSH existing. That's why it survives a year.

## Authority boundaries in play
- **Agent prepares, human signs** — the agent writes `<name>.txt`, stages the deploy, runs verification reads; it never invokes `ssh-keygen -Y sign` with the governor's private key.
- **Unsigned = inert** — before step 3 the file has no authority; don't deploy it as canonical, don't cite it.
- **Canonical vs mirror** — `subtract.ing` under the signing key's domain is canonical; every git remote is a mirror (reflex.5). Pushing to a mirror is not publishing.
- **Push origin** — Rousseau only; Emile/Acer/Surface do not push the canonical artifact.
- **Live read before "done"** — the claim "it's published and verifiable" is an action; it requires the step-6 fetch+verify first (reflex.4).
