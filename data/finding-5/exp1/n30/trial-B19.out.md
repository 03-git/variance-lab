# Plan: publish `essay.txt` to subtract.ing with year-durable, stranger-verifiable authorship

## Threat model / what "verifiable authorship" will actually mean
A stranger in 2027 will be able to confirm: *the holder of OpenPGP key fingerprint `F…` signed exactly these bytes, that key is bound to `subtract.ing` through a channel independent of the web server, and the signature is not backdated.* It does **not** prove legal authorship — only key + domain control at publication time. Everything below is built to keep that claim true even if the web host or deploy pipeline is later compromised.

## Machines and authority boundaries

| Machine | Holds | May do | Must NOT do |
|---|---|---|---|
| **Authoring laptop** (offline-capable) | OpenPGP secret key (ideally on a hardware token: YubiKey/Nitrokey), revocation cert | write the file, `gpg --detach-sign`, `ots stamp` | hold deploy credentials; `git push`; `rsync` to the server |
| **Deploy host** (your CI runner or a small VPS) | SSH deploy key / Pages push token for subtract.ing | receive already-signed artifacts, `git push` / `rsync` them live | possess the signing secret key; alter file contents |
| **subtract.ing web server** | TLS key, static files | serve `essay.txt`, `.asc`, `.ots` over HTTPS | hold either the signing key or, ideally, anything that can re-sign |
| **DNS control plane** (registrar/DNS provider) | zone for subtract.ing | publish the key fingerprint as a record | — |

Boundary rationale: *signing authority* (secret key, laptop only) is disjoint from *publishing authority* (deploy host) which is disjoint from *serving authority* (web host) and *naming authority* (DNS). No single compromise both forges authorship and makes it appear on the canonical URL with a matching independent key record.

## One-time setup (do once, before the first publish)
1. Generate a long-lived signing key on the laptop, moved to a hardware token:
   `gpg --full-generate-key` (Ed25519/cv25519, expiry e.g. 2 years), then `keytocard`. Record the fingerprint `F…`.
2. Generate and print a revocation certificate, store offline:
   `gpg --output revoke-F.asc --gen-revoke 0xF…`
3. Publish the public key on channels **independent of the web server**:
   - `gpg --keyserver hkps://keys.openpgp.org --send-keys 0xF…` then complete the email-verification link.
   - Add a DNS record in the subtract.ing zone pinning the fingerprint, e.g. `TXT  _pgpkey.subtract.ing  "openpgp4fpr:F…"`, and optionally a proper `OPENPGPKEY` RRtype record (`gpg --export --export-options export-dane`).
   - Optional extra channel: a Keybase proof or a signed tag in a public Git repo.
4. Also expose it from the site itself for convenience (not as a trust root): `https://subtract.ing/.well-known/openpgp-key.asc` and a line in `humans.txt`.

## Per-file publication

### A. Author + sign (authoring laptop only)
1. Write `essay.txt`. Put an explicit in-band line inside it: `Author: <name/handle> — subtract.ing — first published 2026-05-10`, so the signature covers the *claim*, not just prose.
2. `sha256sum essay.txt > essay.txt.sha256`
3. Detached signature:
   `gpg --armor --local-user 0xF… --detach-sign essay.txt`  →  `essay.txt.asc`
   (Optionally also `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file essay.txt` → `essay.txt.sig`, as a second independent signature scheme.)
4. Independent timestamp so 2027-you can't be accused of backdating:
   - OpenTimestamps: `ots stamp essay.txt.asc` → `essay.txt.asc.ots`. Hours later: `ots upgrade essay.txt.asc.ots` once it's anchored in a Bitcoin block.
   - Belt-and-suspenders RFC-3161: `openssl ts -query -data essay.txt -sha256 -cert -out e.tsq`, POST to a free TSA (e.g. freetsa.org), save `essay.txt.tsr`.
5. Verify locally before anything leaves the laptop: `gpg --verify essay.txt.asc essay.txt`.

### B. Hand off to the deploy host (no secret material crosses)
`scp essay.txt essay.txt.asc essay.txt.asc.ots essay.txt.tsr essay.txt.sha256 deploy@build-host:/incoming/`
Only signed, public artifacts move. The token/SSH key needed for the next step never existed on the laptop.

### C. Publish (deploy host only)
- If subtract.ing is a static-site Git repo (GitHub/Codeberg Pages, Neocities-with-git, etc.):
  `git -C site add essay.txt essay.txt.asc essay.txt.asc.ots essay.txt.tsr`
  `git -C site commit -m "Publish essay.txt + detached signature"`
  `git -C site push origin main`
  (The hosting platform's commit timestamp becomes yet another corroborating clock; you are not relying on it.)
- Or plain hosting: `rsync -avz --chmod=F644 /incoming/essay.txt* deploy@subtract.ing:/var/www/subtract.ing/`

### D. Capture a public record of *when it was live*
- Force a Wayback snapshot of each URL: `curl -sI "https://web.archive.org/save/https://subtract.ing/essay.txt"` and again for `…/essay.txt.asc`. Save the returned `Content-Location` archive URLs.
- The site's TLS cert + Certificate Transparency logs already bind the hostname around that date; Wayback adds the content-date binding.
- Stash a copy of `essay.txt`, `essay.txt.asc`, `essay.txt.asc.ots`, `essay.txt.tsr`, fingerprint `F…`, and the archive URLs somewhere you control.

## How a stranger verifies, a year later
1. Fetch the artifacts: `curl -O https://subtract.ing/essay.txt`, `curl -O https://subtract.ing/essay.txt.asc`, `curl -O https://subtract.ing/essay.txt.asc.ots`.
2. Obtain the public key **without trusting the web server**:
   `dig +short TXT _pgpkey.subtract.ing` (or `dig OPENPGPKEY …`) to learn fingerprint `F…`; then `gpg --keyserver hkps://keys.openpgp.org --recv-keys 0xF…`. The fact that DNS (domain owner) and keys.openpgp.org (verified email) and the file agree on one fingerprint is the trust anchor.
3. Verify the signature: `gpg --verify essay.txt.asc essay.txt` → expect "Good signature from … F…". (And/or `ssh-keygen -Y verify` against an `allowed_signers` line carrying the same identity.)
4. Verify it isn't backdated: `ots verify essay.txt.asc.ots` → reports the Bitcoin block (≈May 2026) that already committed to this signature. Cross-check `openssl ts -verify -data essay.txt -in essay.txt.tsr -CAfile tsa-ca.pem`.
5. Verify it was actually published there then: open `http://web.archive.org/web/2026*/https://subtract.ing/essay.txt` and confirm the archived bytes hash-match (`sha256sum`) the file they downloaded.
6. Optional: check that key `F…` has not been *revoked before* the OTS timestamp — `gpg --recv-keys 0xF…` shows revocation status; OTS proves the signature predates any later revocation.

Conclusion the verifier can stand behind: these exact bytes were signed by the controller of key `F…`, that key is the one the subtract.ing domain owner published, and the signature provably existed by ~May 2026 — independent of whether subtract.ing, its deploy pipeline, or any keyserver is still trustworthy in 2027.

## Failure-mode notes
- Never let CI/the deploy host hold the signing key — that collapses the signing/publishing boundary and a pipeline breach becomes an authorship forgery.
- If the laptop/token is lost: publish `revoke-F.asc`; past OTS-anchored signatures remain valid because they predate revocation. Start a new key with a transition statement signed by the old one if it's still usable.
- Keep the `.asc`, `.ots`, and `.tsr` files served from the same site *and* in your own archive; if the site dies, the Wayback copies + your archive + the public key channels still let a stranger complete steps 2–5.
