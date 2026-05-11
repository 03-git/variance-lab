# Plan: publish a verifiably-authored `.txt` to subtract.ing

Not executing — plan only. Note up front: the machine this session runs on (`/private/tmp`, not a git repo, no deploy creds, no signing key) is the *drafting* box. It must not be the box that signs or pushes. Those steps belong on your trusted workstation.

## 1. Decide what "verifiable by a stranger in a year" requires

A stranger needs four things to still be true in 12 months:
- **The artifact** — `article.txt`, byte-stable.
- **A detached signature** over it.
- **A public key bound to an identity** (`you@subtract.ing`), reachable without your help.
- **A timestamp proof** that the signature predates "a year ago," so a later forgery with a re-issued key can't masquerade as the original.

The design uses durable third parties so verification doesn't depend on your servers staying up: a PGP keyserver / WKD, the Wayback Machine, and the Bitcoin chain via OpenTimestamps. (Optional belt-and-suspenders: Sigstore/Rekor, which is a public append-only log.)

## 2. Prepare the file (drafting box — this machine is fine for this only)

```
# write the content
$EDITOR article.txt

# normalize so the bytes are stable and reproducible
file article.txt
iconv -f utf-8 -t utf-8 article.txt -o /dev/null   # confirm valid UTF-8
sed -i '' -e 's/[[:space:]]*$//' article.txt        # optional: strip trailing ws (macOS sed)
sha256sum article.txt > SHA256SUMS                   # or `shasum -a 256`
```

Hand `article.txt` + `SHA256SUMS` to the signing box (scp/USB). Do **not** generate or copy a private key onto this sandbox.

## 3. Establish the identity key (signing box: your workstation, ideally a hardware token)

If you don't already have one:
```
gpg --full-generate-key            # choose ECC (Curve 25519), uid: Your Name <you@subtract.ing>
gpg --list-secret-keys --keyid-format=long
gpg --export-secret-subkeys ... > /dev/null   # (move to YubiKey via `keytocard` if you have one)
```

Publish the **public** key so a stranger can fetch it:
```
gpg --armor --export you@subtract.ing > pubkey.asc

# (a) keys.openpgp.org — survives independent of you
gpg --keyserver hkps://keys.openpgp.org --send-keys <FPR>
# then confirm the verification email it sends

# (b) Web Key Directory on subtract.ing itself
gpg --list-keys --with-wkd-hash you@subtract.ing      # gives the hashed local-part
# place pubkey at: https://subtract.ing/.well-known/openpgpkey/hu/<hash>
# and an empty https://subtract.ing/.well-known/openpgpkey/policy
```

Pin the fingerprint in **multiple independent places** so the stranger can cross-check it: the subtract.ing site footer, a DNS `TXT` record on `subtract.ing`, your Mastodon/GitHub profile, and submit those pages to `web.archive.org/save`. The fingerprint is the trust anchor; everything else hangs off it.

Alternative if you'd rather use SSH keys: `ssh-keygen -Y sign -n file -f ~/.ssh/id_ed25519 article.txt` produces `article.txt.sig`; publish an `allowed_signers` line (`you@subtract.ing namespaces="file" ssh-ed25519 AAAA...`) at a stable URL. Same idea, different toolchain. I'll show the GPG path below.

## 4. Sign and timestamp (signing box)

```
# detached, armored signature
gpg --armor --detach-sign --local-user you@subtract.ing --output article.txt.asc article.txt

# also sign the checksum manifest (cheap, lets people verify a bundle)
gpg --armor --clearsign --output SHA256SUMS.asc SHA256SUMS

# proof-of-existence anchored to Bitcoin
pip install opentimestamps-client      # provides `ots`
ots stamp article.txt                  # -> article.txt.ots  (also: ots stamp article.txt.asc)
```

`article.txt.ots` is usable immediately (calendar attestation) and becomes Bitcoin-anchored after a few hours; you'll upgrade it in step 7.

Optional public-log path (independent of your key surviving):
```
cosign sign-blob --yes --bundle article.txt.cosign.bundle article.txt   # OIDC login, lands in Rekor
```
Record the Rekor log index it prints.

## 5. Authority boundaries (who is allowed to do what)

- **This sandbox / drafting box**: edits text, computes hashes. No private key, no deploy creds, never pushes. (Also: I, the agent, have no authorization to deploy to subtract.ing and no access to your key — which is why this is plan-only by construction.)
- **Signing box (your workstation + hardware token)**: the *only* place the secret key material is used. Air-gappable. It does not need deploy creds.
- **Deploy path to subtract.ing**: needs write access to the web root and is a *separate* authority from authorship. The signing key must never be placed on a CI runner or the web server — if it were, "authored by you" would degrade to "anyone with prod access." CI/web host only ever handles already-signed static files.
- **DNS + TLS cert holder for subtract.ing**: yet another authority. Needed for WKD and HTTPS delivery, but compromising it does *not* let an attacker forge the signature — it only lets them serve a wrong `pubkey.asc`, which is why the fingerprint is pinned off-domain too.

## 6. Publish (deploy box — workstation or CI, with web-root creds, *not* the signing key)

Put these in the site's published tree:
```
article.txt
article.txt.asc
article.txt.ots
SHA256SUMS  SHA256SUMS.asc
pubkey.asc                      # at https://subtract.ing/pubkey.asc
.well-known/openpgpkey/hu/<hash>
.well-known/openpgpkey/policy
article.txt.cosign.bundle       # if you did step 4's optional bit
```

Deploy with whatever subtract.ing already uses — pick one:
- static host via git: `git add . && git commit -m "publish article.txt + signature" && git push origin main` (let Netlify/Cloudflare Pages/GitHub Pages build).
- rsync to a server: `rsync -avz --checksum ./public/ deploy@subtract.ing:/var/www/subtract.ing/`
- `netlify deploy --prod --dir=public` or `wrangler pages deploy public`.

Then snapshot it: submit `https://subtract.ing/article.txt`, `.../article.txt.asc`, and `.../pubkey.asc` to `https://web.archive.org/save/`. This is what gives the stranger a *dated* third-party copy.

## 7. After Bitcoin confirms (≈ next day, deploy box)

```
ots upgrade article.txt.ots     # bakes in the Bitcoin block attestation
ots verify article.txt.ots      # sanity check locally
```
Re-deploy the upgraded `article.txt.ots`. Re-snapshot to Wayback. Done.

## 8. How a stranger verifies, a year later

```
# 1. get the files
curl -O https://subtract.ing/article.txt
curl -O https://subtract.ing/article.txt.asc
curl -O https://subtract.ing/article.txt.ots
# (or pull them from the Wayback snapshot if the site is gone)

# 2. get the key WITHOUT trusting the live site alone
gpg --auto-key-locate wkd,keyserver --locate-external-key you@subtract.ing
#   then cross-check the printed fingerprint against:
#     - the DNS TXT record:  dig +short TXT subtract.ing
#     - the archived site footer on web.archive.org
#     - the author's GitHub/Mastodon profile
#   all must show the same fingerprint.

# 3. verify the signature
gpg --verify article.txt.asc article.txt
#   -> "Good signature from Your Name <you@subtract.ing>"  +  the fingerprint from step 2

# 4. verify it existed back then
pip install opentimestamps-client
ots verify article.txt.ots
#   -> "Bitcoin block <N> attests existence as of <date>"  — must be ~ the publication date

# 5. (optional) independent public log
cosign verify-blob --bundle article.txt.cosign.bundle \
  --certificate-identity you@subtract.ing \
  --certificate-oidc-issuer https://github.com/login/oauth \
  article.txt
#   and look up the Rekor entry by index at https://search.sigstore.dev
```

If all of: *good signature*, *fingerprint matches the off-domain pins*, and *OpenTimestamps puts the file at the claimed date* — the stranger has confirmed you authored `article.txt` and did so when you said, without needing to trust subtract.ing, your servers, or you, today.

## 9. Failure modes this covers
- Site/domain lost → Wayback snapshot + keyserver copy still verify.
- Key later compromised/rotated → the OTS Bitcoin anchor proves the signature predates the compromise.
- Someone re-publishes a tampered `article.txt` → hash mismatch; signature fails.
- Attacker swaps `pubkey.asc` on the live site → fingerprint won't match the DNS TXT / archived / social pins.

What this does *not* prove: that the human behind `you@subtract.ing` is any particular real-world person — only that whoever controls that key+identity authored the file at that time. Strengthen that link separately (keybase-style proofs, a key-transparency entry, signing the key with others' keys).
