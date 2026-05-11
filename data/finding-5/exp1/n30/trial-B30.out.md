# Plan: publish a verifiable-authorship `.txt` to subtract.ing

## 0. Threat model / what "verifiable a year from now" requires
A stranger in 2027 must be able to show, without trusting subtract.ing's host, CDN, or DNS at verification time:
1. **Integrity** — the bytes they fetch are the bytes you published.
2. **Authorship** — a key you control signed those bytes, and that key is bound to your public identity.
3. **Anteriority** — the signature existed at/around publication time, not forged later.

That means the signing key must live on a machine the web stack can't reach, and the timestamp proof must not depend on a company still being alive in a year.

## 1. One-time identity setup (trusted workstation only)
- Generate (or reuse) an OpenPGP identity, ideally on a hardware token so the private key never touches disk:
  - `gpg --full-generate-key` (Ed25519/cv25519), UID `Your Name <you@subtract.ing>`
  - Move subkeys to a YubiKey: `gpg --edit-key <fpr>` → `keytocard`
  - Publish the public key:
    - **WKD**: place the exported key at `https://subtract.ing/.well-known/openpgpkey/hu/<hash>` (use `gpg-wks-client --print-wkd-hash you@subtract.ing`), plus the policy file.
    - **DNS**: an `OPENPGPKEY` RR and a `TXT` record containing the full fingerprint, at your DNS provider.
    - **Keyserver**: `gpg --keyserver keys.openpgp.org --send-keys <fpr>`
    - **Social proof**: put the fingerprint in a Mastodon/GitHub/Keybase bio you control.
- Install timestamping tooling on the workstation: `pip install opentimestamps-client` (gives `ots`), and have `openssl` for RFC-3161.
- Configure signed git commits on this machine: `git config --global user.signingkey <fpr>`, `git config --global commit.gpgsign true`, `git config --global tag.gpgsign true`.

This workstation is the **only** machine that holds: the OpenPGP private key (on token), your personal SSH key authorized to push, and your git identity.

## 2. Create and sign the file (trusted workstation)
- Write `essays/2026-05-10-title.txt`. Inside the file, state the claim in plain text ("I, Your Name, wrote this on 2026-05-10. OpenPGP fpr: …") so the signed payload itself asserts authorship.
- Detached signature: `gpg --armor --detach-sign essays/2026-05-10-title.txt` → produces `essays/2026-05-10-title.txt.asc`
- Trustless timestamp: `ots stamp essays/2026-05-10-title.txt` → `essays/2026-05-10-title.txt.ots` (anchors SHA-256 of the file into the Bitcoin chain; verifiable in a year with no third party).
- Belt-and-suspenders RFC-3161 token from a public TSA:
  - `openssl ts -query -data essays/2026-05-10-title.txt -sha256 -cert -out f.tsq`
  - `curl -s -H "Content-Type: application/timestamp-query" --data-binary @f.tsq https://freetsa.org/tsr > essays/2026-05-10-title.txt.tsr`
- Commit all four artifacts with a signed commit; tag it: `git commit -S -m "publish 2026-05-10-title"`, `git tag -s essay/2026-05-10-title -m ...`

## 3. Push and deploy — who pushes, who doesn't
- **Trusted workstation → git host**: `git push origin main --tags`. This is the only push of authored content; it carries your signature and your SSH key. **Authority boundary:** this machine can write to the repo and holds signing authority.
- **Git host (e.g. GitHub repo)**: stores the signed commit/tag. Its `GITHUB_TOKEN` / deploy key is scoped to *this repo only*. It does **not** hold the OpenPGP key.
- **CI runner (GitHub Actions / Pages build)**: builds the static site and deploys it. It runs `git checkout`, copies the `.txt`, `.asc`, `.ots`, `.tsr` verbatim into the published tree, and nothing else signing-related. **Authority boundary:** the runner may publish bytes but cannot sign or re-sign; it has no access to the token/key. Pin the workflow to a commit SHA and require the deploy to come from the signed tag.
- **Web host / CDN (Pages, Netlify, Cloudflare)**: serves the files over HTTPS; holds only the TLS key (auto-issued via ACME/Let's Encrypt, which lands the cert in Certificate Transparency logs). **Authority boundary:** can serve or even tamper with bytes, but any tampering breaks the detached signature, so it cannot forge authorship.
- **DNS provider**: serves the `OPENPGPKEY`/`TXT` key-locator records. **Authority boundary:** controls *discovery* of your key, not its content — which is why the fingerprint is also on a keyserver and in social bios, so a DNS compromise alone can't substitute a key.

Net: compromise of the CI runner, the web host, the CDN, or DNS — individually — cannot produce a forged authorship claim. Only compromise of the workstation/token can, and that's the single point you physically control.

## 4. Make publication independently dated
- After deploy, submit the live URL to `https://web.archive.org/save/https://subtract.ing/essays/2026-05-10-title.txt` (and the `.asc`). Independent dated copy.
- Optionally upgrade the OTS proof a few hours later: `ots upgrade essays/2026-05-10-title.txt.ots` and re-deploy, so the Bitcoin attestation is already complete.

## 5. How a stranger verifies, a year later
1. Fetch the artifacts: `curl -O https://subtract.ing/essays/2026-05-10-title.txt{,.asc,.ots,.tsr}`
2. Obtain your public key *without trusting subtract.ing*, via at least two channels, and confirm the fingerprints match:
   - `gpg --auto-key-locate clear,wkd,keyserver --locate-keys you@subtract.ing`
   - `dig +short OPENPGPKEY ... ` / the `TXT` fingerprint record
   - the fingerprint in your Mastodon/GitHub/Keybase profile
3. Integrity + authorship: `gpg --verify 2026-05-10-title.txt.asc 2026-05-10-title.txt` → expect `Good signature from "Your Name <you@subtract.ing>"` with the matching fpr.
4. Anteriority (trustless): `ots verify 2026-05-10-title.txt.ots` → "Bitcoin block N attests data existed as of <date>" predating/at publication.
5. Anteriority (corroborating): `openssl ts -verify -in 2026-05-10-title.txt.tsr -data 2026-05-10-title.txt -CAfile freetsa_cacert.pem`
6. Corroborate the publication date: open the archive.org snapshot; check `crt.sh?q=subtract.ing` for a TLS cert valid at that time.
7. If the repo is public: `git verify-commit <sha>` / `git verify-tag essay/2026-05-10-title` — same key, same date.

The claim a stranger ends up with: *bytes B carry a good OpenPGP signature from key K; key K is bound to "Your Name" via WKD+DNS+social proofs cross-checked; OpenTimestamps proves K signed B no later than 2026-05; subtract.ing merely served a copy and could not have forged any of it.*

## Tool inventory
`gnupg` (+ a YubiKey), `git` (signed commits/tags), `ssh` (push auth), `opentimestamps-client` (`ots`), `openssl ts` + a public TSA (freetsa/DigiCert), `gpg-wks-client` (WKD hash), your DNS provider's console (`OPENPGPKEY`/`TXT`), a static-site host with ACME TLS (GitHub Pages/Netlify/Cloudflare), GitHub Actions (build/deploy only), `curl`, `dig`, `crt.sh`, `web.archive.org`.

I have not executed any of this — plan only.
