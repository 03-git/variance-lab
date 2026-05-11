# Plan: publish a verifiably-authored `.txt` to subtract.ing

## 0. Threat model / what "verifiable" requires
TLS on subtract.ing only proves *the server served these bytes* — not who wrote them, and it won't help a year out if the host is compromised or the file is edited. So authorship = a **detached cryptographic signature** over the file, plus a **public key the verifier can anchor through a channel independent of the web server**, plus an **independent timestamp**. Three separate secrets, three separate machines.

## 1. Authority boundaries (decide these first)
- **Signing key = identity authority.** A `minisign` secret key (or GPG key on a YubiKey). Lives *only* on your workstation, passphrase-protected / in hardware. Never on CI, never on the web host. Its only job: assert "I wrote this."
- **Deploy credential = publication authority.** An SSH deploy key or a scoped `wrangler`/Cloudflare Pages API token or GitHub Actions OIDC. Lives on the push machine / CI runner. Can put bytes on subtract.ing; **cannot forge a signature**.
- **DNS/registrar credential = anchoring authority.** Controls the `TXT` record that publishes your key fingerprint. Separate account, separate creds. Compromising the web host must not let anyone re-anchor a new key.
- **TLS cert on the web server**: proves domain control at serve time, nothing about authorship. Not part of the trust chain for the claim.

Which machine pushes: the **CI runner / deploy box** with the scoped deploy token. Which does **not**: the **workstation with the signing key** — it signs and commits, then hands off; it never holds the deploy token.

## 2. One-time setup
1. Generate the signing keypair on the workstation:
   `minisign -G -p subtracting.pub -s subtracting.key`
   (or, GPG route: `gpg --quick-generate-key 'you@subtract.ing' ed25519 sign 2y`, moved to a YubiKey via `keytocard`; or SSH route: `ssh-keygen -t ed25519 -f id_sign` + an `allowed_signers` file.)
2. Anchor the public key independently of the web server:
   - DNS TXT at the apex: `subtract.ing. TXT "minisign-key=RWQ...base64..."`, set through the registrar/Cloudflare dashboard or API. Enable **DNSSEC** on the zone so the record itself is signed.
   - Belt-and-suspenders: also publish `subtracting.pub` in a public git repo and on `keys.openpgp.org` (GPG route) / Keybase. More anchors = more robust a year out.
3. Create/choose a public git repo (e.g. GitHub `subtract-ing-site`) that holds the site content. This gives an append-only, timestamped third-party record.

## 3. Create and sign the file (workstation only)
1. Write the file: `notes-2026-05-10.txt`.
2. Detached signature:
   `minisign -S -s subtracting.key -m notes-2026-05-10.txt -t "subtract.ing 2026-05-10; author=<you>"`
   → produces `notes-2026-05-10.txt.minisig`. (GPG: `gpg --armor --detach-sign notes-2026-05-10.txt` → `.asc`. SSH: `ssh-keygen -Y sign -f id_sign -n file notes-2026-05-10.txt` → `.sig`.)
3. Independent timestamp on the *content hash*:
   `ots stamp notes-2026-05-10.txt` (OpenTimestamps → anchors SHA256 into Bitcoin; produces `.ots`). Optionally also an RFC-3161 token: `openssl ts -query -data notes-2026-05-10.txt -sha256 -cert -out f.tsq` then submit to freetsa.org and save the `.tsr`.
4. Record the hash: `sha256sum notes-2026-05-10.txt notes-2026-05-10.txt.minisig`.
5. Commit all of it to the git repo and sign the commit/tag:
   `git add notes-2026-05-10.txt notes-2026-05-10.txt.minisig notes-2026-05-10.txt.ots`
   `git commit -S -m "Publish notes-2026-05-10.txt"`
   `git tag -s notes-2026-05-10 -m "..."`
   `git push origin main --tags`

## 4. Publish to subtract.ing (push machine / CI — no signing key present)
- If static-hosted on your own box: `rsync -avz --checksum notes-2026-05-10.txt notes-2026-05-10.txt.minisig notes-2026-05-10.txt.ots deploy@subtract.ing:/var/www/subtract.ing/` over an SSH key that is *only* a deploy key.
- If Cloudflare Pages: `wrangler pages deploy ./public --project-name subtract-ing` using a Pages-scoped API token in CI.
- If GitHub Pages / Netlify: let the Action triggered by the `git push` build and deploy; the runner uses OIDC / a deploy token, never the signing key.
- The `.txt`, the `.minisig` (and `.ots`) all ship together at predictable URLs:
  `https://subtract.ing/notes-2026-05-10.txt`, `…​.txt.minisig`, `…​.txt.ots`.
- After it's live, capture an independent snapshot: submit both URLs to the Wayback Machine (`https://web.archive.org/save/https://subtract.ing/notes-2026-05-10.txt` and the `.minisig`). That's a fourth-party time anchor.

## 5. How a stranger verifies it a year later
1. Download the artifact and its signature:
   `curl -O https://subtract.ing/notes-2026-05-10.txt`
   `curl -O https://subtract.ing/notes-2026-05-10.txt.minisig`
2. Get the public key from a channel that doesn't depend on trusting the web server *today*:
   `dig +dnssec TXT subtract.ing` — read `minisign-key=…`, and check the `ad` flag / RRSIG so they know the TXT wasn't spoofed. (Or pull `subtracting.pub` from the public git repo, or `keys.openpgp.org`.)
3. Verify the signature:
   `minisign -Vm notes-2026-05-10.txt -P RWQ...` → expect `Signature and comment signature verified` and the trusted comment showing the author/date. (GPG: `gpg --verify notes-2026-05-10.txt.asc notes-2026-05-10.txt`. SSH: `ssh-keygen -Y verify -f allowed_signers -I you@subtract.ing -n file -s notes-2026-05-10.txt.sig < notes-2026-05-10.txt`.)
4. Check the timestamp: `ots verify notes-2026-05-10.txt.ots` → confirms the bytes existed by the claimed date, anchored in Bitcoin (no need to trust subtract.ing or me for the date).
5. Cross-check: the SHA256 of the downloaded file matches the hash in the signed git tag `notes-2026-05-10` (`git verify-tag`), and matches the Wayback Machine snapshot taken on the publish date. Three independent records (DNSSEC-anchored key, OpenTimestamps, git tag + Wayback) all agreeing → a stranger can conclude the holder of that key authored that file by that date, even if subtract.ing is long gone or compromised.

## Why this works
Authorship rides on the signing key, which never leaves the workstation; publication rides on a deploy token that can't forge signatures; the key is anchored through DNSSEC (and git/keyservers) so it survives a web-host compromise; and OpenTimestamps + git + Wayback pin the date without anyone having to trust subtract.ing or you. A breach of any single machine — web host, CI runner, or registrar — degrades one leg without letting an attacker manufacture a false authorship claim.
