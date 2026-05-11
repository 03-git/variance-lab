## Goal
Get `essay.txt` to `https://subtract.ing/essay.txt` so that a stranger in May 2027 can confirm a specific key identity authored it — even if the web host or DNS is compromised by then. The mechanism is a detached signature + independent key distribution + an independent timestamp. Three credentials stay on three sides of three boundaries.

## 1. Key material (once, on the secure machine only)

- Tool: `minisign` (Ed25519, single small self-contained `.minisig`). Alternative: GnuPG Ed25519 key on a YubiKey (`gpg --card-edit` → `keytocard`); or `signify`.
- `minisign -G -p ~/keys/subtract.pub -s ~/keys/subtract.key` — strong passphrase; back the secret up offline (paper + USB, two locations). If GPG: also generate a revocation cert now, set expiry >1 year or none.
- Advertise the **public** key in at least two venues with *different authorities* than the file's host:
  1. DNS TXT, e.g. `_minisign.subtract.ing` → `"minisign RWS…"`, zone DNSSEC-signed.
  2. A public Git repo (GitHub) containing `minisign.pub`.
  3. keys.openpgp.org or a Keyoxide claim (if using GPG).
  4. `https://subtract.ing/.well-known/minisign.pub` — convenience only; same authority as the file, so not sufficient alone.

## 2. Author + sign (secure machine — the **signing boundary**)

```
$EDITOR essay.txt
minisign -S -s ~/keys/subtract.key -m essay.txt \
  -t "essay.txt for https://subtract.ing — author <you>, key RWS… — 2026-05-10"
# -> essay.txt.minisig  (the -t string is signed)
```
Independent timestamp (proves existence date without trusting your clock or the host):
- OpenTimestamps: `ots stamp essay.txt` and `ots stamp essay.txt.minisig` → `.ots` files (Bitcoin-anchored; `ots upgrade` later).
- and/or RFC-3161: `openssl ts -query -data essay.txt -sha256 -cert -out essay.txt.tsq`, submit to a free TSA, keep `essay.txt.tsr`.

Optional second venue, same machine: `git add essay.txt essay.txt.minisig essay.txt.ots minisign.pub && git commit -S -m "publish essay.txt" && git tag -s essay-2026-05-10`.

**Holds:** signing key. **Does NOT hold:** subtract.ing deploy creds, DNS API token.

## 3. Publish (a *different* machine / CI — the **deploy boundary**)

Move only the outputs (`essay.txt`, `essay.txt.minisig`, `essay.txt.ots`, `minisign.pub`) here — via `git pull` of the repo or `scp` of those files. Private key never arrives.

Then ship bytes, per whatever subtract.ing runs:
- SSH static host: `rsync -av --checksum essay.txt essay.txt.minisig essay.txt.ots well-known/minisign.pub user@subtract.ing:/var/www/subtract.ing/`
- Cloudflare Pages: `wrangler pages deploy ./public --project-name subtract-ing`
- Netlify: `netlify deploy --prod --dir public`
- GitHub Pages: CI runner does the deploy.

If CI: the workflow secret is the deploy token/SSH key only — never the signing key; the signature is already in the committed artifact. The DNS TXT record is added by the registrar/DNS-provider credential (`dnscontrol push` or provider console) — a third credential, ideally a third context.

## 4. Hardening for the one-year horizon

- Snapshot against link rot: `https://web.archive.org/save/https://subtract.ing/essay.txt` and `…/essay.txt.minisig` (also archive.today) — dated third-party copies.
- Months later: `ots upgrade essay.txt.ots`.
- Keep the signing-key backup and (GPG) revocation cert offline.

## Authority boundaries

| Capability | Where it lives | Can it forge authorship? |
|---|---|---|
| minisign secret key | secure laptop / hardware token | yes — therefore it never leaves that machine |
| subtract.ing deploy token / SSH key / CI secret | deploy machine or CI runner | no — can deface or delete, but can't produce a valid signature; pubkey copies survive elsewhere |
| DNS / registrar credential | DNS-admin context | no — can hide the TXT record; Git/keyserver copies remain |
| GitHub account | dev machine | no alone — commit/tag signatures still need the key |

Compromise of any one of the bottom three lets an attacker remove or replace the file, but the replacement won't verify against the independently-obtained public key, and the OpenTimestamps proof shows the genuine file predates the tampering.

## How a stranger verifies it (May 2027)

1. Fetch artifact + signature: `curl -O https://subtract.ing/essay.txt`, `curl -O https://subtract.ing/essay.txt.minisig` (or from the GitHub repo / web.archive.org if the site is gone).
2. Get the public key from a channel other than the file's host: `dig +dnssec +short TXT _minisign.subtract.ing` (check DNSSEC AD flag), or `git clone` the repo and read `minisign.pub`, or keys.openpgp.org — and confirm the `RWS…` string is identical across venues.
3. Verify: `minisign -Vm essay.txt -P 'RWS…'` (or `-p minisign.pub`); read the printed trusted comment — it names the URL, author, date.
4. Verify the timestamp: `ots verify essay.txt.ots` → reports the Bitcoin block/time, i.e. "existed by <2026 date>". Optionally `openssl ts -verify -in essay.txt.tsr -data essay.txt -CAfile tsa-ca.pem`.
5. (Git path, if present) `git tag -v essay-2026-05-10` / `git log --show-signature`; GitHub also shows "Verified".

Conclusion the verifier can stand on: the exact bytes of `essay.txt` were signed by the holder of key `RWS…`; that key is advertised by the controller of `subtract.ing` (via DNSSEC) and by the same identity on GitHub/keyserver; and the signature existed by mid-2026 — independent of whatever the web host serves in 2027.
