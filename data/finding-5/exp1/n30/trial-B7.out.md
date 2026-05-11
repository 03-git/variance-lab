# Plan: publish a verifiably-authored `.txt` to subtract.ing

## Threat model / what "verifiable" requires
A stranger in a year must be able to confirm three independent things:
1. **Who** signed the file → a detached cryptographic signature over the exact bytes.
2. **That the key is really yours** → the public key reachable through multiple channels bound to `subtract.ing`.
3. **When** it existed → a trustless timestamp that doesn't depend on the web host's clock or continued existence.

The web host and CI are *untrusted for authorship*: they can serve, withhold, or replace bytes, but must not be able to forge a signature. So the signing key never touches them.

## Machines & authority boundaries

| Authority | Credential | Where it lives | What it can do |
|---|---|---|---|
| **Signing** | OpenPGP signing subkey (ideally on a YubiKey) | Personal workstation only | Sign artifacts. Cannot deploy. |
| **Publishing** | SSH deploy key (forced-command) or host API token | CI runner (e.g. GitHub Actions secret) | Push bytes to subtract.ing. Cannot sign. |
| **Naming** | Registrar / DNS account | Used once, interactively | Set DNSSEC + key-fingerprint TXT / WKD. |
| **Source of record** | Git push credential | Workstation | Commit signed artifacts to a public repo. |

- **Pushes to subtract.ing:** the CI runner (after a push to the repo triggers it).
- **Does *not* push to subtract.ing:** the workstation that holds the GPG private key. It only produces signed artifacts and commits them; CI deploys. The signing key and the deploy token are never co-resident.

## One-time setup
1. **Key:** `gpg --full-generate-key` (Ed25519, expiry > 18 months so it's still valid in a year), or move a signing subkey to a YubiKey with `keytocard`. Note the fingerprint.
2. **Publish the public key on ≥3 channels so no single compromise lets someone substitute a key:**
   - On the site: `https://subtract.ing/pgp-key.asc` and the WKD path `https://subtract.ing/.well-known/openpgpkey/hu/<hash>` (built with `gpg-wks-client`).
   - DNS: a TXT record at `subtract.ing` with the fingerprint, and enable **DNSSEC** at the registrar.
   - Keyserver: `gpg --keyserver keys.openpgp.org --send-keys <fpr>` then confirm the verification email so the user-id (`you@subtract.ing`) is bound.
3. **CI deploy path:** create an SSH key restricted by `command="..."` in `authorized_keys` on the VPS (or a scoped Netlify/Cloudflare token); store it as a CI secret. CI gets *only* this.

## Publishing the file
On the **workstation**:
1. Finalize `article.txt`. Record the hash: `sha256sum article.txt`.
2. Sign (detached, ASCII): `gpg --armor --detach-sign --local-user <fpr> article.txt` → `article.txt.asc`.
3. Trustless timestamp: `ots stamp article.txt` → `article.txt.ots` (OpenTimestamps; anchors the hash in the Bitcoin blockchain).
4. Commit `article.txt`, `article.txt.asc`, `article.txt.ots` to the public Git repo with a signed commit: `git commit -S -m "publish article.txt"`, `git tag -s`, `git push`. (Git history + GitHub give a second, independent timestamp.)
5. CI fires on the push and deploys the three files (and `pgp-key.asc`, `.well-known/...`) to `subtract.ing` via the scoped deploy credential — e.g. `rsync -a ./public/ deploy@subtract.ing:/var/www/subtract.ing/`.
6. ~24 h later, on the workstation: `ots upgrade article.txt.ots` (folds in the Bitcoin block proof), commit the upgraded `.ots`, let CI redeploy it.
7. Optional corroboration: trigger a Wayback Machine capture of the three URLs, and post the SHA-256 somewhere append-only (a dated note / social post). More independent timestamps = stronger.

## How a stranger verifies, a year later
1. Download `https://subtract.ing/article.txt` and `https://subtract.ing/article.txt.asc` (TLS binds the bytes to the name at fetch time).
2. Obtain the public key through channels that *don't* trust the web server alone:
   - `gpg --locate-external-keys you@subtract.ing` (WKD), and
   - `dig +dnssec TXT subtract.ing` to check the fingerprint, and
   - `gpg --keyserver keys.openpgp.org --recv-keys <fpr>`.
   Confirm all three show the **same fingerprint**.
3. `gpg --verify article.txt.asc article.txt` → expect `Good signature from "… <you@subtract.ing>"` with that fingerprint. This proves **who**.
4. `ots verify article.txt.ots` → reports the Bitcoin block height/time the file's hash was committed; cross-check against the Git commit/tag date and any archived snapshot. This proves **when** — and survives even if subtract.ing is gone, because the proof is in the blockchain and the repo.
5. (If the key later expired or was revoked, the signature + OTS timestamp still show it was valid *at signing time*.)

## Why each boundary matters
- Web host compromised → can't alter `article.txt` undetected (signature breaks) and can't forge a new one (no private key).
- CI/deploy token leaked → attacker can publish junk but can't sign as you; the repo and OTS proofs contradict them.
- DNS hijack → DNSSEC + the keyserver/WKD cross-check expose the mismatch; TLS cert issuance is also constrained.
- Workstation compromised → the only real exposure; mitigated by keeping the signing key on a YubiKey (touch-to-sign, non-exfiltratable).

Net: signature = identity, OpenTimestamps + Git + archive = time, multi-channel key distribution + DNSSEC = name-to-key binding. The signing machine and the publishing machine are deliberately different credentials so neither alone can fabricate the claim.
