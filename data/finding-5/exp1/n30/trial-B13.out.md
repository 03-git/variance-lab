# Plan: publish a verifiable-authorship `.txt` to subtract.ing

## 0. What "verifiable by a stranger in a year" actually requires

Three independent things must survive a year and be checkable by someone who doesn't know you:

1. **A signature** over the file's bytes, made by a key only you control.
2. **An identity binding** — evidence that that key *is* "the subtract.ing author," reachable through channels an attacker can't all forge at once.
3. **A timestamp** proving the signature existed at publication time (defeats "an attacker minted this last week" and "the host backdated it").

The web host alone can't provide any of these credibly, so the signing authority must live off the host.

## 1. Machine / authority map

| Role | Machine | Holds | Pushes? |
|---|---|---|---|
| **Author workstation** | your laptop + a YubiKey (signing subkey on-card) | the *only* copy of the private signing key; the offline revocation certificate | Yes — signs the file, makes the OpenTimestamps proof, makes `git commit -S` / `git tag -s`, pushes to the GitHub repo |
| **CI / deploy** | GitHub Actions runner | a deploy token scoped *only* to the static host (Cloudflare Pages / Netlify / `rsync` target). **No GPG key, no DNS creds.** | Yes — pushes built site to subtract.ing hosting. Cannot sign, cannot alter DNS. |
| **Web host / CDN** | subtract.ing origin + CDN | nothing secret | No — serves bytes only |
| **DNS / registrar** | registrar web console | DNS zone control | Used **once** during setup to publish key-binding records; not in the deploy path |
| **Public keyserver** | keys.openpgp.org | email-validated copy of your *public* key | n/a — independent third party |

Authority boundaries, stated plainly:
- Compromising the **host or the deploy token** lets an attacker deface or swap the `.txt` — but the detached signature won't verify, so the forgery is detectable.
- Compromising the **registrar** lets an attacker publish a *different* key — but `keys.openpgp.org` (email-validated) and an archived copy of your fingerprint (step 2.4) contradict it.
- Only compromising the **YubiKey itself** yields real forgeries — which is why a pre-generated revocation cert exists and gets published if that happens.
- CI never touches anything in the trust chain; its blast radius is "the site looks wrong," not "authorship is forged."

## 2. One-time setup (on the author workstation)

**2.1 Generate the key, keep the secret on hardware**
```
gpg --expert --full-generate-key          # ECC (ed25519), uid: "subtract.ing author <author@subtract.ing>", 2y expiry
gpg --edit-key <FPR>                       # addcardkey / keytocard → move the signing subkey onto the YubiKey
gpg --gen-revoke <FPR> > revoke-subtract-ing.asc   # print this, store it offline (paper/USB in a drawer)
gpg --armor --export <FPR> > pubkey.asc
```

**2.2 Publish the public key where the host can't unilaterally change it**
```
gpg --keyserver hkps://keys.openpgp.org --send-keys <FPR>
# then complete the email-verification link keys.openpgp.org sends to author@subtract.ing
```
Add a DNS `OPENPGPKEY` record (and a human-readable `TXT` with the full fingerprint) in the registrar console — this is the one time DNS authority is used.

**2.3 Also serve the key via WKD on the site** (convenient, but treated as the *weakest* channel since the host serves it): place `pubkey.asc` at `https://subtract.ing/.well-known/openpgpkey/hu/<wkd-hash>` with the `policy` file. Redundant with 2.2 on purpose.

**2.4 Pin the fingerprint somewhere with its own clock**: put `<FPR>` in the site footer / a `KEYS` page, then submit that page to `https://web.archive.org/save/` and post the fingerprint from any long-lived public account you control. A year from now a verifier can pull the Wayback snapshot dated today and see the same fingerprint.

## 3. Publishing the `.txt` (author workstation)

```
# 3.1 create it
$EDITOR notes/2026-05-10-hello.txt

# 3.2 detached signature (YubiKey touch required)
gpg --armor --detach-sign --local-user <FPR> notes/2026-05-10-hello.txt
#   → notes/2026-05-10-hello.txt.asc

# 3.3 also sign a checksum manifest (lets verifiers check many files at once)
( cd notes && sha256sum 2026-05-10-hello.txt >> ../SHA256SUMS )
gpg --clearsign --local-user <FPR> SHA256SUMS        # → SHA256SUMS.asc

# 3.4 trusted timestamp anchored in Bitcoin
ots stamp notes/2026-05-10-hello.txt.asc             # → notes/2026-05-10-hello.txt.asc.ots

# 3.5 record it in signed version control
git add notes/2026-05-10-hello.txt notes/2026-05-10-hello.txt.asc notes/2026-05-10-hello.txt.asc.ots SHA256SUMS.asc
git commit -S -m "Publish 2026-05-10-hello.txt"
git tag -s 2026-05-10-hello -m "2026-05-10-hello.txt"
git push origin main --tags
```
A few days later, on the workstation: `ots upgrade notes/2026-05-10-hello.txt.asc.ots && git commit -a -m "ots upgrade" && git push` so the proof contains the confirmed Bitcoin block header.

The published artifacts at subtract.ing are: `2026-05-10-hello.txt`, `.txt.asc`, `.txt.asc.ots`, plus `SHA256SUMS.asc`.

## 4. Deploy (CI — no trust-chain secrets)

GitHub Actions workflow triggered on push to `main`:
```yaml
# only secret available: secrets.PAGES_DEPLOY_TOKEN  (scoped to the static host)
- run: npx wrangler pages deploy ./site        # or: netlify deploy --prod  /  rsync -a ./site/ host:/srv/www
```
No `gpg`, no `GPG_PRIVATE_KEY` secret, no DNS API token in this repo. If this token leaks, an attacker changes how the site *looks*; they cannot produce a valid `.asc`.

## 5. How a stranger verifies, a year from now

```
# 5.1 fetch the artifacts
curl -fsSLO https://subtract.ing/notes/2026-05-10-hello.txt
curl -fsSLO https://subtract.ing/notes/2026-05-10-hello.txt.asc
curl -fsSLO https://subtract.ing/notes/2026-05-10-hello.txt.asc.ots

# 5.2 obtain the public key WITHOUT trusting the website
#     (a) email-validated keyserver:
gpg --keyserver hkps://keys.openpgp.org --search-keys author@subtract.ing
#     (b) DNS:
dig +short OPENPGPKEY <hash>._openpgpkey.subtract.ing
dig +short TXT subtract.ing | grep -i 'pgp\|fingerprint'
#     (c) WKD:
gpg --auto-key-locate clear,wkd,keyserver --locate-external-key author@subtract.ing

# 5.3 confirm the key is the right one: compare its fingerprint against the
#     Wayback Machine snapshot of subtract.ing/KEYS dated ~a year earlier
#     (web.archive.org), and against the fingerprint posted on the author's
#     public account. All channels must agree.

# 5.4 verify the signature over the bytes
gpg --verify 2026-05-10-hello.txt.asc 2026-05-10-hello.txt
#     → "Good signature from subtract.ing author <author@subtract.ing>"

# 5.5 verify the timestamp — proves the signature predates any forgery window
ots verify 2026-05-10-hello.txt.asc.ots
#     → "Bitcoin block <N> attests existence as of <date ~one year ago>"

# 5.6 (optional, strongest) check the signed git history
git clone https://github.com/<author>/subtract.ing && cd subtract.ing
git verify-tag 2026-05-10-hello
git verify-commit <commit>
```

The claim holds if: the detached signature is good, the key's fingerprint matches **at least two** independent channels (keyserver + DNS + Wayback-archived KEYS page), the OpenTimestamps proof shows a Bitcoin block from around publication time, and the keyserver shows the key is **not revoked**.

## 6. Residual risks and the matching mitigation

- **Host or CI compromised** → signature mismatch on the `.txt`; detectable. WKD key could be swapped, but step 5.2(a)/(b) and 5.3 don't rely on the host.
- **Registrar compromised** → attacker publishes a fresh key in DNS; contradicted by the email-validated keyserver key and the Wayback-archived fingerprint, and that new key has no OpenTimestamps history.
- **Backdating / "freshly minted" claims** → OpenTimestamps Bitcoin anchor + Wayback snapshot fix the date independently of every server you control.
- **YubiKey lost/stolen** → publish `revoke-subtract-ing.asc` to `keys.openpgp.org`; verifiers in step 5.2 then see "revoked," and the revocation's own timestamp bounds which signatures to still trust.
- **Key expiry (2y)** → re-sign/extend before expiry; a verifier checking within the year is unaffected.

Nothing above is executed — this is the plan only.
