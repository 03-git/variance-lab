# Plan: publish a verifiable-authorship `.txt` to subtract.ing

## 0. What "verifiable a year from now" requires
A stranger in May 2027 must be able to independently establish four things:
1. **Integrity** — the file they fetch is the bytes you published (hash).
2. **Authenticity** — those bytes were signed by a key you control (signature).
3. **Time** — the signature/file existed around 2026-05-10, not forged later (trusted timestamp).
4. **Identity binding** — that key is bound to "you" via channels independent of subtract.ing itself (keyserver + DNS + repo history).

Everything below serves those four. The design also keeps the **signing key** and the **deploy credentials** on different machines so neither compromise alone forges history.

---

## 1. Key material — on the *signing machine* only (your laptop or, better, an air-gapped box)

This machine is the **only** thing that ever touches the signing secret key. It has **no** hosting token, **no** DNS/registrar API key, **no** production write access.

Pick one signing scheme; GPG shown as primary (best ecosystem for year-later discovery), minisign/SSH as alternatives.

- Generate a long-lived key, expiry **2 years** (not 1 — it must outlive the verification window) or no expiry plus a stored revocation cert. Use a UID on the domain itself:
  - `gpg --expert --full-generate-key` → ECC / Curve 25519, sign-capable, UID `Your Name <you@subtract.ing>`
  - Add a signing subkey; move secret to a YubiKey if available (`gpg --edit-key <fpr>` → `keytocard`).
  - `gpg --gen-revoke <fpr> > revoke.asc` — print/store offline.
  - `gpg --export-secret-keys --armor <fpr>` — back up offline (paper/HSM/2 USB keys in 2 locations).
- Alternatives: `minisign -G -p subtracting.pub -s subtracting.key` ; or `ssh-keygen -t ed25519 -f ~/.ssh/subtracting_sign -C "subtract.ing authorship"`.

Publish the **public** key in several independent places (none of these needs the secret key, so a non-signing machine can do the DNS/web parts):
- `gpg --keyserver hkps://keys.openpgp.org --send-keys <fpr>` then confirm the verification email to `you@subtract.ing`.
- WKD: serve the key under `https://subtract.ing/.well-known/openpgpkey/...` (`gpg-wks-client --create <fpr> you@subtract.ing`).
- DNS on subtract.ing: an `OPENPGPKEY` record, plus a `TXT` record carrying the fingerprint string.
- A `keyoxide.org` profile / signed identity proofs.
- Commit `KEY-FINGERPRINT.txt` (the full fingerprint + key algo) into the site repo so it's in git history.

---

## 2. Create and sign the content — signing machine

- Write `article.txt`. Fix the canonical URL now, e.g. `https://subtract.ing/2026/article.txt`.
- Write a `MANIFEST` that states the *claim* in plain text:
  ```
  Author: Your Name <you@subtract.ing>
  File: article.txt
  SHA-256: <output of: sha256sum article.txt>
  Canonical-URL: https://subtract.ing/2026/article.txt
  Date: 2026-05-10
  Statement: I authored this file and publish it at the URL above.
  ```
- Sign **the manifest** (so the assertion is signed, not just opaque bytes) and the file:
  - `gpg --local-user <fpr> --clearsign MANIFEST` → `MANIFEST.asc`
  - `gpg --local-user <fpr> --armor --detach-sign article.txt` → `article.txt.asc`
  - (minisign: `minisign -S -s subtracting.key -m article.txt -t "subtract.ing 2026-05-10"` → `article.txt.minisig`; also produce `allowed_signers` / publish `subtracting.pub`.)
  - (SSH: `ssh-keygen -Y sign -f ~/.ssh/subtracting_sign -n file article.txt` → `article.txt.sig`; publish an `allowed_signers` line `you@subtract.ing ssh-ed25519 AAAA...`.)

---

## 3. Trusted timestamp — signing machine (proves the date without trusting subtract.ing or me)

- OpenTimestamps (anchors to Bitcoin; no trusted third party needed in 2027):
  - `pip install opentimestamps-client`
  - `ots stamp article.txt article.txt.asc MANIFEST.asc` → `.ots` files
  - Days later: `ots upgrade article.txt.ots` (once Bitcoin-confirmed). Keep the upgraded `.ots`.
- And/or an RFC 3161 TSA as a second anchor:
  - `openssl ts -query -data article.txt -sha256 -cert -out article.txt.tsq`
  - `curl -sH 'Content-Type: application/timestamp-query' --data-binary @article.txt.tsq https://freetsa.org/tsr -o article.txt.tsr`
  - Save the TSA's CA chain alongside.
- The git commit/tag in step 4 is a third, weaker time anchor (GitHub records push time).

---

## 4. Repo, commit, push, deploy — the authority boundary

Site lives in a git repo (`github.com/<org>/subtract-ing`) that builds to a static host (GitHub Pages or Netlify) serving `subtract.ing` via a `CNAME` file + DNS.

**Signing machine** does only this:
```
git add article.txt article.txt.asc article.txt.sha256 \
        MANIFEST MANIFEST.asc article.txt.ots KEY-FINGERPRINT.txt
git commit -S -m "Publish article.txt (signed + timestamped)"
git tag -s article-2026-05-10 -m "Signed publication 2026-05-10"
git push origin main --tags
```
It holds the GPG signing key. It does **not** hold the Pages deploy token, the Netlify token, or the DNS/registrar API key.

**Publishing path** (one of):
- *CI (preferred):* a `.github/workflows/pages.yml` with `permissions: pages: write, id-token: write` builds and deploys to GitHub Pages. The signing secret key is **never** a CI secret. CI only moves already-signed bytes.
- *Deploy host:* a separate machine/account holding the SSH key or Netlify token runs `netlify deploy --prod` / `rsync` to the web root. Same rule: it never has the signing key.

**DNS path:** whoever holds the registrar/DNS creds sets the Pages/Netlify A/AAAA/CNAME records and the `OPENPGPKEY` + fingerprint `TXT` records. That's a third credential boundary; importantly it only ever publishes the *public* key.

Why this matters:
- Web-host or CI compromise → attacker can change the live file, but can't produce a valid signature → `gpg --verify` fails → forgery detected.
- Signing-laptop compromise → attacker can sign things, but can't deploy to subtract.ing without the separate deploy creds, and can't backdate past the OpenTimestamps anchor.
- Even later compromise of both → the historical signed+timestamped artifact (in git, in the Wayback Machine, on keyservers) still stands on its own.

Verify the live result yourself:
```
curl -fsSL https://subtract.ing/2026/article.txt | sha256sum   # matches MANIFEST
curl -fsSL https://subtract.ing/2026/article.txt.asc
curl -fsSL https://subtract.ing/2026/MANIFEST.asc
```

---

## 5. Redundancy so the claim survives the site changing

- Archive every artifact URL:
  ```
  for f in article.txt article.txt.asc MANIFEST.asc article.txt.ots KEY-FINGERPRINT.txt; do
    curl -s "https://web.archive.org/save/https://subtract.ing/2026/$f" >/dev/null
  done
  ```
- Post the fingerprint + SHA-256 + a copy of `MANIFEST.asc` to one more public, dated place (a Gist, a mailing-list archive). More independent anchors = less disputable.

---

## 6. How a stranger verifies in May 2027

1. **Fetch** `article.txt`, `article.txt.asc`, `MANIFEST.asc`, `article.txt.ots` from `https://subtract.ing/2026/...` — or from the Wayback Machine snapshot if the site is gone.
2. **Get the public key independently of subtract.ing:**
   - `gpg --locate-external-key you@subtract.ing` (uses WKD), and
   - `gpg --keyserver hkps://keys.openpgp.org --recv-keys <fpr>`, and
   - `dig +short OPENPGPKEY ...` / `dig +short TXT subtract.ing`, and
   - the `KEY-FINGERPRINT.txt` committed in git, and keyoxide proofs.
   - Confirm the **same fingerprint** appears across all of them — that's the identity binding.
3. **Verify signatures:**
   - `gpg --verify MANIFEST.asc` → "Good signature from Your Name <you@subtract.ing>"
   - `gpg --verify article.txt.asc article.txt` → good signature
   - check the SHA-256 in `MANIFEST` equals `sha256sum article.txt`
   - (minisign: `minisign -Vp subtracting.pub -m article.txt`; SSH: `ssh-keygen -Y verify -f allowed_signers -I you@subtract.ing -n file -s article.txt.sig < article.txt`)
4. **Verify the timestamp:** `ots verify article.txt.ots` → confirms the bytes were committed to a Bitcoin block dated ~2026-05-10. (`openssl ts -verify -in article.txt.tsr -data article.txt -CAfile tsa-ca.pem` for the RFC 3161 anchor.) Combined with the key's creation date and the signed `Date:` line, the "authored as of May 2026" claim holds even though it's being checked a year later.
5. **Check status:** `gpg --refresh-keys` — a revocation/expiry *after* the timestamp doesn't void the historical signature, but the verifier should see it.
6. **Optional corroboration:** the signed git tag `article-2026-05-10` and the CI deploy log on GitHub, plus the Wayback snapshot timestamps.

---

## Tool checklist
- `gpg` (GnuPG) — keygen, signing, WKD, keyserver — *or* `minisign` *or* `ssh-keygen -Y` for sign/verify.
- `opentimestamps-client` (`ots`) — blockchain timestamp; `openssl ts` — RFC 3161 timestamp.
- `git` / `gh` — signed commit + tag, push to repo.
- GitHub Pages workflow *or* `netlify` CLI *or* `rsync`/`ssh` — deploy (on a machine without the signing key).
- `dig` — DNS `OPENPGPKEY` / `TXT` checks.
- `curl` + `sha256sum` — fetch/verify live bytes; `curl .../web.archive.org/save/...` — archival.

**Machine that pushes/deploys:** the CI runner or dedicated deploy host (holds Pages/Netlify/SSH creds, no signing key).
**Machine that does *not* push to production:** the signing machine (holds the GPG secret key, can `git push` to the repo at most, never deploys).
**Third boundary:** the DNS/registrar credential holder — publishes only the public key + site records.
