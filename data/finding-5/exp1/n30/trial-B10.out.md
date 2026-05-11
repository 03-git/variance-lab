# Plan: publish a verifiable `.txt` to `subtract.ing`

## What "verifiable authorship a year later" decomposes into
1. **Bytes are fixed** — a hash everyone can recompute.
2. **A key signed those exact bytes** — detached cryptographic signature.
3. **That key belongs to you** — key↔identity binding published on channels you don't solely control (keyserver, WKD, DNS, git history, social).
4. **It existed by a certain date** — an independent timestamp, so a stranger doesn't have to trust your server's clock or that the file wasn't backdated.

The site serving over HTTPS proves *who controls the domain right now* — not authorship, and not in a year. So HTTPS is necessary for distribution and key-binding, but the signature + timestamp carry the actual claim.

## Machines and authority boundaries

| Role | Machine | Holds | Never has |
|---|---|---|---|
| **Signer** | Offline/air-gapped laptop (or any laptop + a YubiKey holding the secret subkey) | OpenPGP secret key, PIN | Deploy keys, registrar creds, network during signing |
| **Publisher** | Everyday workstation | Git deploy key / CI token for the `subtract.ing` repo | The OpenPGP secret key |
| **Domain owner** | (account, not a machine) | `.ing` registrar login (Google Registry's registrar), DNS control, ACME/Let's Encrypt | n/a |
| **Timestamp** | external — OpenTimestamps calendar servers (Bitcoin chain), an RFC-3161 TSA (e.g. freetsa.org) | nothing of yours | n/a — the point is you don't control it |

Data flows **offline-signer → USB stick → publisher → repo → site**. Secrets never flow the other way. Compromise of the publisher lets an attacker replace the file but **cannot forge a good signature**; compromise of the registrar lets them re-point DNS but still can't forge the signature; compromise of the signing key is the only thing that breaks authorship — hence it lives on a hardware token / offline box.

## One-time setup (on the offline signer)

```bash
# Ed25519 primary + signing subkey; set expiry well past a year (or none) and keep a revcert
gpg --expert --full-generate-key            # choose ECC (ed25519); or generate on-card: gpg --card-edit -> generate
gpg --output revoke-<fpr>.asc --gen-revoke <fpr>     # store offline, separately
gpg --armor --export <fpr> > subtract.ing-pubkey.asc
```

Bind the key to the identity over channels a verifier can reach independently:
- Upload public key: `gpg --keyserver keys.openpgp.org --send-keys <fpr>` (then confirm the verification email so the UID is searchable).
- **WKD**: publish the key at `https://subtract.ing/.well-known/openpgpkey/hu/<hash>` (use `gpg-wks-client --print-wkd-hash hello@subtract.ing` for the path) plus the `policy` file.
- **DNS** (registrar account): add an `OPENPGPKEY` RR and/or a `TXT` record like `openpgp-fpr=<full fingerprint>`.
- Print the fingerprint in the site footer / an `about` page, in the first git commit message, and on any social account (Mastodon profile metadata, etc.). Redundancy is the binding.

(Lighter-weight alternative to all of GPG: `ssh-keygen -Y sign` with an Ed25519 key and publish an `allowed_signers` file at a stable URL. Same shape — secret on a hardware key, public identity published widely. GPG chosen here for the mature WKD/keyserver/timestamp ecosystem.)

## Publishing the file

On the **offline signer**:
```bash
# author it
$EDITOR note.txt

# pin the bytes
sha256sum note.txt > note.txt.sha256

# authoritative authorship artifact: detached, armored signature
gpg --armor --detach-sign --output note.txt.asc note.txt
```
Copy `note.txt`, `note.txt.asc`, `note.txt.sha256` to a USB stick. Done on this machine — it goes back in the drawer.

On the **publisher** (now networked):
```bash
# independent existence proof #1: OpenTimestamps (anchors the hash to Bitcoin)
pip install opentimestamps-client
ots stamp note.txt                 # -> note.txt.ots  (only the hash leaves the machine)

# independent existence proof #2: RFC-3161 TSA, belt-and-suspenders
openssl ts -query -data note.txt -sha256 -cert -out note.tsq
curl -s -H 'Content-Type: application/timestamp-query' \
     --data-binary @note.tsq https://freetsa.org/tsr -o note.txt.tsr

# deploy: subtract.ing is a static site in a git repo (Pages/Netlify/VPS+nginx)
git clone git@github.com:<you>/subtract.ing.git && cd subtract.ing
mkdir -p files
cp /media/usb/note.txt /media/usb/note.txt.asc /media/usb/note.txt.sha256 files/
cp ../note.txt.ots ../note.txt.tsr files/
git add files/note.txt*
git commit -m "publish note.txt; sig key fpr <fpr>"   # optionally -S with a separate ssh commit-signing key
git push                                               # <-- THIS machine pushes
```
Then:
```bash
curl -sSI https://subtract.ing/files/note.txt          # confirm it's live over TLS
ots upgrade note.txt.ots                                # ~a few hours later, once Bitcoin confirms; re-commit the upgraded .ots
# independent dated mirrors:
curl -s "https://web.archive.org/save/https://subtract.ing/files/note.txt"
# (and archive.today) — gives a third party holding a dated copy
```

## How a stranger verifies, a year from now

```bash
# 1. fetch the bundle from the site
base=https://subtract.ing/files/note.txt
curl -O $base -O $base.asc -O $base.sha256 -O $base.ots -O $base.tsr

# 2. bytes are what they are
sha256sum -c note.txt.sha256

# 3. get the alleged author's key from a channel the site doesn't fully control,
#    and cross-check the fingerprint against DNS / footer / git history
gpg --auto-key-locate clear,wkd,keyserver --locate-keys hello@subtract.ing
dig +short TYPE61 subtract.ing            # OPENPGPKEY  (or the TXT openpgp-fpr record)
gpg --fingerprint <fpr>                   # must match every place it's published

# 4. the key signed exactly these bytes
gpg --verify note.txt.asc note.txt        # -> "Good signature from ... <fpr>"

# 5. it existed by some date — and you don't have to trust subtract.ing for that
ots verify note.txt.ots                    # -> "success! Bitcoin block <N> attests existence as of <date>"
openssl ts -verify -data note.txt -in note.txt.tsr -CAfile freetsa_cacert.pem

# 6. optional corroboration
#    Wayback Machine snapshot of .../files/note.txt dated near publication.
```

Conclusion the verifier can stand behind: *the holder of OpenPGP key `<fpr>` — which is bound to `subtract.ing` via WKD, the keyserver UID, and a DNS record — produced a signature over exactly these bytes, and the bytes provably existed no later than `<timestamp date>`.* No trust in the web server, the registrar, or your clock is required for the authorship + date claim; HTTPS only vouches for "this is the copy `subtract.ing` is serving today."

## Longevity notes
- Set the signing (sub)key expiry beyond the verification horizon, or to never-expire with a stored revocation cert; an expired key still verifies old signatures but a naive `gpg --verify` will warn.
- Keep the `.ots` proof *upgraded* (post-Bitcoin-confirmation) in the repo — an un-upgraded proof needs a live calendar server to complete.
- Keep `note.txt.asc`, `note.txt.ots`, `note.txt.tsr`, and the public key in the git history (and the Wayback mirror), so the evidence survives even if the live site changes.
