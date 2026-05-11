# Plan: publish a verifiably-authored `.txt` to subtract.ing

## 0. Trust model (decide first)
"Authorship verifiable by a stranger" needs three independently checkable things:
1. **A signature** over the file's bytes, made by a key only you control.
2. **An identity binding** for that key (key ⇄ "the person/entity behind subtract.ing").
3. **A trusted timestamp** proving the signature predates "a year ago" so a backdate can't be faked later.

I'll use **OpenPGP (GnuPG)** for (1), **WKD + keys.openpgp.org + keyoxide** for (2), and **OpenTimestamps** (Bitcoin-anchored) for (3). `minisign`/`signify` or `ssh-keygen -Y sign` are viable substitutes for (1) but lack the domain-binding ecosystem of WKD, so PGP is the better fit here.

## 1. Key setup (one-time, on the signing workstation only)
- Generate an Ed25519 signing key bound to a domain identity:
  `gpg --quick-generate-key 'Author Name <author@subtract.ing>' ed25519 sign 2y`
  (Better: generate on a YubiKey with `gpg --card-edit` / `keytocard` so the private key never touches disk.)
- Record the fingerprint: `gpg --fingerprint author@subtract.ing`.
- Publish the public key for discovery:
  - keys.openpgp.org: `gpg --export author@subtract.ing | curl -T - https://keys.openpgp.org` (then confirm the verification email).
  - WKD: generate the advanced/direct layout — `gpg --list-options show-only-fpr-mbox --list-keys author@subtract.ing` then `gpg-wks-client --create <FPR> author@subtract.ing` — and stage the output under the site at `/.well-known/openpgpkey/subtract.ing/hu/<zbase32-localpart>` plus the `policy` file.
  - Optional but strong: add Ariadne identity claims and register at keyoxide.org so the key links bidirectionally to subtract.ing, the git host, etc.
  - Pin the fingerprint in human-readable places that get independently archived: the site footer, the repo `README`, a pinned social post. Corroboration matters a year out.

## 2. Create and sign the file (signing workstation)
- Write `essay.txt`.
- Optionally embed its own fingerprint line + date in the text (self-describing).
- Hash it for the record: `shasum -a 256 essay.txt`.
- Detached, armored signature: `gpg --armor --local-user <FPR> --detach-sign essay.txt` → `essay.txt.asc`.
- (Optional manifest approach: put `sha256  essay.txt` lines in `SHA256SUMS`, sign that instead with `gpg --clearsign SHA256SUMS` — scales to multiple files.)

## 3. Independent timestamp (signing workstation)
- Install `opentimestamps-client`.
- `ots stamp essay.txt.asc` → `essay.txt.asc.ots` (stamp the signature, which transitively commits to the file's hash; or stamp both).
- Wait for Bitcoin confirmation (a few hours), then `ots upgrade essay.txt.asc.ots` to fold in the block-header path so the proof is self-contained.
- This is what makes "a year from now" robust: the `.ots` proof is verifiable forever against Bitcoin block headers, with no dependency on subtract.ing still existing.

## 4. Commit to source control (signing workstation pushes here)
- In the site repo, with `git config commit.gpgsign true` and `user.signingkey <FPR>`:
  `git add essay.txt essay.txt.asc essay.txt.asc.ots .well-known/openpgpkey/...`
  `git commit -S -m "Publish essay.txt"`
  `git tag -s essay-v1 -m "essay.txt as published"`
  `git push origin main --tags`
- The signed commit/tag and the repo's history give a second (weaker, forgeable-date) timestamp; GitHub/Codeberg will show a "Verified" badge once it knows the key.

## 5. Deploy to subtract.ing (a *different* machine pushes here)
- CI runner (e.g., GitHub Actions / Netlify build) triggers on the push, builds the static site, and publishes — `rsync -az --delete ./public/ deploy@host:/var/www/subtract.ing/`, or `actions/deploy-pages`, or `netlify deploy --prod`.
- TLS via Let's Encrypt (`certbot` / Caddy auto-HTTPS) so visitors authenticate the domain.
- Verify it's live: `curl -fsSL https://subtract.ing/essay.txt | shasum -a 256` matches step 2; `curl -I https://subtract.ing/.well-known/openpgpkey/subtract.ing/policy` returns 200.
- Submit to an independent archive immediately: Wayback Machine "Save Page Now" for `essay.txt`, `essay.txt.asc`, `essay.txt.asc.ots`, and the WKD URLs. Optionally `ipfs add` and pin. This guarantees a verifier in a year has a copy even if the site is gone.

## 6. Authority boundaries (who can do what)
- **Signing key (YubiKey / signing workstation only):** the *only* thing that can create a valid authorship signature. Never in CI secrets, never on the web server, never in the repo. Compromise here = forged authorship; everything else is recoverable.
- **DNS / domain registrar account (2FA, separate):** load-bearing for the *identity binding* — WKD and cert issuance flow from domain control. If your identity claim is "author = controller of subtract.ing," this is the root of trust; if it's "author = this long-lived keyoxide identity," the registrar matters less. Consider DNSSEC + an `OPENPGPKEY` RR as a second binding.
- **Git hosting account:** can alter/withhold source and the "Verified" badge; cannot forge a signature. Protect with 2FA; branch protection on `main`.
- **CI / deploy token:** scoped to deploy only. A compromised CI can publish or suppress files but cannot sign — so the authorship claim survives; only availability is at risk.
- **Web/edge server (holds TLS key only):** serves bytes. Compromise = tamper or remove files; detectable, because `gpg --verify` fails on altered bytes and the OTS-stamped original still verifies from the archive/repo.

Summary of "which machine pushes": the **signing workstation** does the secret-bearing operations (sign, OTS-stamp, signed commit) and pushes *to the source repo*. The **CI/deploy runner** pushes *to the web host*, holding only a deploy token. The **web server pushes nowhere** and holds no signing or push credentials. Secrets and network-exposure are kept on separate machines.

## 7. How a stranger verifies, a year later
1. Fetch `essay.txt`, `essay.txt.asc`, `essay.txt.asc.ots` — from subtract.ing, or, if it's gone, from the git repo or the Wayback Machine snapshot.
2. Get the public key by domain, not by trusting the file: `gpg --auto-key-locate clear,wkd,keyserver --locate-keys author@subtract.ing`. Confirm the fingerprint matches what's pinned on keys.openpgp.org and keyoxide.org/<fingerprint> (which shows the verified link back to subtract.ing / the git host).
3. Verify the signature: `gpg --verify essay.txt.asc essay.txt` → expect `Good signature from "Author Name <author@subtract.ing>"`.
4. Verify the timestamp: `ots verify essay.txt.asc.ots` (with `essay.txt.asc` alongside) → reports the Bitcoin block and UTC time the data was committed; check that time is ≥ ~1 year ago. This step needs only Bitcoin block headers — no live subtract.ing, no live keyserver.
5. (Corroborating) `git log --show-signature` on the repo shows the signed commit and `essay-v1` tag; the host shows "Verified"; the commit date roughly agrees with the OTS time.
6. Conclusion the stranger can stand behind: *the key bound to subtract.ing signed exactly these bytes, and an independent blockchain anchor shows it happened by date X* — and none of that conclusion depends on the website, CI, or git host being honest or even online at verification time.

## Tools referenced
`gnupg` (`gpg`, `gpg-wks-client`, `gpg --card-edit`), YubiKey, `opentimestamps-client` (`ots`), `git` (signed commits/tags), `shasum`/`sha256sum`, static deploy (`rsync`/`actions/deploy-pages`/`netlify`), `certbot`/Caddy for TLS, `dig` + `curl` for post-deploy checks, Wayback Machine "Save Page Now" (and optionally IPFS) for independent archival, keys.openpgp.org + keyoxide.org for identity binding. Substitutes: `minisign`/`signify` or `ssh-keygen -Y sign` in place of PGP for step 2 (lose WKD-style domain binding); a Sigstore/`cosign` blob signature as an alternative transparency-log-backed path.
