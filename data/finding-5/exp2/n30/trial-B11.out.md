I'd normally start with `bash ~/scripts/audit-health.sh` for ground truth, but you've said don't execute — so this is plan-only and assumes that check passes (DNS for subtract.ing resolves, signing key present, archive drive mounted).

## 1. Authority boundaries (settle these first)

- `boundary` / `authority.source`: **I prepare, the human signs.** Claude never touches the private key. The draft `.txt` is `authority.unsigned` → suggestion only until `ssh-keygen -Y verify` passes against it.
- `reflex.2`: signature format is **`ssh-keygen -Y sign`** (OpenSSH signed-data, `SSH SIGNATURE` PEM armor). Don't invent a format; this one is verifiable by any stranger with stock OpenSSH ≥ 8.1.
- `reflex.5`: **subtract.ing is canonical** because that's the signing key's domain. The git host (GitHub/whatever mirror) is **mirror-only** — never the authority, even if it's where the diff lands.
- `loop.before`: before publishing, verify the *previous* manifest signature with a live read, surface any unsigned drift in `~/subtract.ing/`, governor decides sign/continue/abort.
- Model/infra discipline: Emile and acer1660ti get **no role in the canonical push**. Emile is compute-only; acer is NOT formation (backup/mirror tier). Surface can drive the session but does not hold the archive.

## 2. Which machine does what

- **Rousseau (this node, `m1studio`)** — holds `~/subtract.ing/` canonical working tree, the governor is present here, and the ed25519 signing key lives here. **All signing and the canonical publish originate on Rousseau.**
- **Emile (`m2mini`)** — does not push. If heavy work is needed (e.g. bulk re-index of the RAG after adding the doc), dispatch via `ssh m2mini "claude -p ..."`. No authority.
- **acer1660ti** — does not push. Receives the published artifact later as warm backup only.
- **Surface** — may initiate the request but the bytes leave from Rousseau.

## 3. Steps

**a. Author the file** in the canonical tree:
`~/subtract.ing/<path>/newdoc.txt` — include a human-readable date line in the body (2026-05-10) so the claim is self-dated independent of filesystem mtime.

**b. Pre-publish verification (`loop.before`):**
- `cd ~/subtract.ing && git log --oneline -5 && git status`
- Verify the current `MANIFEST` (or whatever the repo's signed index is) still verifies:
  `ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s MANIFEST.sig < MANIFEST`
- Surface any files in `git status` that are modified-but-unsigned. Governor decides.

**c. Human signs the new file** (governor runs this, not Claude):
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<path>/newdoc.txt
```
→ produces `newdoc.txt.sig` (the `SSH SIGNATURE` PEM block). Namespace `file` is the convention; keep it consistent with the rest of the repo.

**d. Update and re-sign the manifest (`loop.after.1`, `loop.after.2`):**
- Append `newdoc.txt` + its SHA-256 to `MANIFEST`.
- `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file MANIFEST` → `MANIFEST.sig`.

**e. Confirm before going outward** (`reflex.4` — assertion-that-blocks counts as an action):
```
ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s newdoc.txt.sig < newdoc.txt
```
Must print `Good "file" signature for jns@subtract.ing`. If not, stop.

**f. Publish to the canonical domain.** Push the static bytes to whatever serves `https://subtract.ing/` (the same path/method already used for `governance.conf.universal.txt`), publishing **all three**:
- `https://subtract.ing/<path>/newdoc.txt`
- `https://subtract.ing/<path>/newdoc.txt.sig`
- `https://subtract.ing/allowed_signers` (must already exist / be kept current — this is the trust anchor; it inherits authenticity from subtract.ing's DNS+TLS)

This is the publish that "counts." Sending bytes to the public web is outward-facing and hard to reverse — governor confirms before this step.

**g. Mirror, explicitly second-class.** `git add` + commit (message noting the file + that authority is the `.sig`, not the commit) + push to the git host. State in the commit body: "mirror only; canonical at subtract.ing per governance reflex.5." The mirror's commit timestamp is a nice-to-have corroborating datestamp, not the authority.

**h. Backup tier.** Sync the published artifact to acer1660ti's warm backup path. No authority change.

**i. (Optional, strengthens the "a year from now" property.)** Run the `newdoc.txt.sig` through OpenTimestamps (`ots stamp newdoc.txt.sig`) and publish the `.ots` proof alongside — Bitcoin-anchored proof the signature existed on 2026-05-10, in case the key is later rotated/revoked.

## 4. How a stranger verifies it a year from now

They need stock OpenSSH and the ability to fetch from subtract.ing:

```
curl -O https://subtract.ing/<path>/newdoc.txt
curl -O https://subtract.ing/<path>/newdoc.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s newdoc.txt.sig < newdoc.txt
```

Expected: `Good "file" signature for jns@subtract.ing`.

What that establishes, and the chain of trust:
1. The `allowed_signers` line (`jns@subtract.ing namespaces="file" ssh-ed25519 AAAA...`) is authentic because it was served over TLS from `subtract.ing` — the domain *is* the signing key's identity domain (`reflex.5` / `authority.source`).
2. `ssh-keygen -Y verify` passing proves `newdoc.txt`'s exact bytes were signed by the holder of that key.
3. Cross-check: the same key already signs `MANIFEST` and `governance.conf.universal.txt`, so a verifier can corroborate against any earlier signed artifact from the same domain. If they pulled the GitHub mirror instead, they run the *identical* verify command — and if the mirror's bytes don't verify, the mirror is wrong, not the claim.
4. If the key was rotated in the interim, the optional `.ots` proof shows the signature predates the rotation.

The signature itself never expires; the only durability requirement is that `subtract.ing` keeps serving `allowed_signers`. That's the one thing to not let lapse.
