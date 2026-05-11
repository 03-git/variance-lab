# Plan: publish a verifiably-authored `.txt` to subtract.ing

## 0. What "verifiable by a stranger in a year" actually requires

Three independent facts must survive a year and be checkable without trusting me or my server:

1. **Binding of bytes → key**: a cryptographic signature over the exact file.
2. **Binding of key → identity**: the public key is discoverable from places a stranger already trusts (DNS for `subtract.ing`, a code-forge `.keys` endpoint, an archive), not only from subtract.ing itself.
3. **Binding to time**: proof the signature/file existed *before* some date, so a later key compromise can't be used to back-date a forgery — OpenTimestamps (Bitcoin anchor) plus a Wayback Machine capture.

The web server is *not* in the trust path for authorship — it only serves bytes. Even fully compromised, it cannot forge a signature or a timestamp.

## 1. One-time setup — the signing identity (on the workstation only)

- Generate a dedicated signing keypair. Primary choice: **minisign** (small, purpose-built, stable format):
  - `minisign -G -p ~/keys/subtract.pub -s ~/keys/subtract.key`
  - Store `subtract.key` encrypted (its built-in passphrase) on the workstation; ideally back it up to an offline encrypted volume. The secret key **never leaves this machine**.
  - Acceptable alternatives, same role: `ssh-keygen -t ed25519 -f ~/.ssh/subtract_sign` then `ssh-keygen -Y sign` (good if the pubkey is already on `https://github.com/<user>.keys`), or a GPG Ed25519 key on a YubiKey published via WKD + keyservers. Pick one and be consistent.
- Publish the **public** key in ≥2 identity-bound places:
  - DNS TXT on the domain itself: `_minisign.subtract.ing. 3600 IN TXT "minisign-pubkey RWQ...base64..."` (signed with DNSSEC if the zone supports it).
  - A file at `https://subtract.ing/.well-known/minisign.pub` (convenience copy — not a root of trust by itself).
  - A code forge endpoint tied to your account, e.g. commit `subtract.pub` to a public GitHub repo, or use `https://github.com/<user>.keys` if you went the SSH route.
  - Optionally: a `keys.openpgp.org`/keyserver entry (GPG route) or a Keybase/`gist` post.

## 2. Machines and authority boundaries

| Machine | Holds | Can do | Cannot do |
|---|---|---|---|
| **Workstation** (laptop) | secret signing key (+ passphrase / hardware token) | author file, sign it, create OTS proof | — |
| **Deploy path** (either the workstation running `rsync`, or a CI runner like GitHub Actions) | SSH deploy key / forge token for the web host only | copy already-signed artifacts to the server | produce a valid signature (never sees the signing secret) |
| **Web server for subtract.ing** | TLS cert, static files | serve bytes over HTTPS | forge authorship; alter the OTS/Bitcoin record |
| **Bitcoin network / OTS calendar servers** | — | anchor a hash at a block height | reveal file contents (only a hash is submitted) |

Rule: **the machine that signs is not the machine that has standing credentials to the public server.** If you deploy from the workstation, do it with a separate, least-privilege SSH key scoped to the doc directory; the signing key and the deploy key are different keys with different blast radii. CI, if used, is *only* a courier of artifacts the workstation already produced.

## 3. Author and sign (workstation)

1. Write the file, fixing its bytes exactly: `notes-2026-05-10.txt`. Decide encoding/newlines now; any later change invalidates the signature (that's the point).
2. Record a content hash for your own logs: `sha256sum notes-2026-05-10.txt | tee notes-2026-05-10.txt.sha256`.
3. Sign, embedding a trusted comment that names the claim:
   - `minisign -S -s ~/keys/subtract.key -m notes-2026-05-10.txt -t "subtract.ing — <name> — 2026-05-10"` → produces `notes-2026-05-10.txt.minisig`.
   - (SSH route equivalent: `ssh-keygen -Y sign -f ~/.ssh/subtract_sign -n file notes-2026-05-10.txt` → `.sig`. GPG route: `gpg --armor --detach-sign notes-2026-05-10.txt` → `.asc`.)

## 4. Timestamp (workstation)

- Install the OpenTimestamps client: `pipx install opentimestamps-client`.
- Stamp **both** the file and the signature so neither can be re-dated later:
  - `ots stamp notes-2026-05-10.txt`
  - `ots stamp notes-2026-05-10.txt.minisig`
  - This yields `.ots` proofs; they're "pending" until a Bitcoin block confirms (minutes to hours). Re-run `ots upgrade *.ots` later that day to fold in the block header, then keep the upgraded `.ots` files.
- This is the load-bearing time anchor. A Wayback capture (step 5) is the human-friendly corroboration.

## 5. Publish (deploy path — courier only)

Artifacts to ship: `notes-2026-05-10.txt`, `notes-2026-05-10.txt.minisig`, `notes-2026-05-10.txt.ots`, `notes-2026-05-10.txt.minisig.ots`, and (convenience) `subtract.pub`.

- If subtract.ing is a static site you host directly:
  - `rsync -av --checksum notes-2026-05-10.txt notes-2026-05-10.txt.minisig notes-2026-05-10.txt.ots notes-2026-05-10.txt.minisig.ots deploy@subtract.ing:/srv/www/subtract.ing/docs/`
  - Confirm it serves over HTTPS with the right `Content-Type` and isn't being rewritten by the server: `curl -sSf https://subtract.ing/docs/notes-2026-05-10.txt | sha256sum` and compare to step 3's hash.
- If it's forge-backed (GitHub Pages / Netlify): commit the same files to the site repo (`git add … && git commit -m … && git push`); the CI build is just publishing files, it does no signing.
- Ensure the DNS TXT pubkey record from step 1 is live: `dig +short TXT _minisign.subtract.ing`.
- Trigger an archive snapshot so the claim is pinned off your infrastructure: submit `https://subtract.ing/docs/notes-2026-05-10.txt` (and the `.minisig`) to `https://web.archive.org/save/` (or `archivebox`). Note the resulting timestamped Wayback URLs.

## 6. Leave a verification breadcrumb

Add a short `https://subtract.ing/docs/notes-2026-05-10.txt.VERIFY.md` that states: the pubkey fingerprint, where the pubkey is independently published (DNS name, forge URL), and the exact verify commands below. Sign that file too, or at least it's covered by the Wayback capture. This is courtesy, not a trust root — every fact in it is independently checkable.

## 7. How a stranger verifies, a year later

1. **Fetch artifacts** from subtract.ing (or, if the site is gone, from the Wayback URLs):
   - `curl -O https://subtract.ing/docs/notes-2026-05-10.txt`
   - `curl -O https://subtract.ing/docs/notes-2026-05-10.txt.minisig`
   - `curl -O https://subtract.ing/docs/notes-2026-05-10.txt.ots`
2. **Get the public key from an independent source**, not from subtract.ing's `.well-known`:
   - `dig +short TXT _minisign.subtract.ing` (and check the zone's DNSSEC chain with `delv` / `dig +dnssec`), or pull `subtract.pub` from the published GitHub repo / `https://github.com/<user>.keys`.
   - Cross-check that the key from DNS, the forge, and the site's `.well-known` copy are byte-identical.
3. **Verify the signature**:
   - `minisign -Vm notes-2026-05-10.txt -P "RWQ...the published pubkey..."` → expects `Signature and comment signature verified`, and shows the trusted comment naming the author + date.
   - (SSH route: build an `allowed_signers` line `who@subtract.ing ssh-ed25519 AAAA…` from the forge `.keys`, then `ssh-keygen -Y verify -f allowed_signers -I who@subtract.ing -n file -s notes-2026-05-10.txt.sig < notes-2026-05-10.txt`. GPG route: `gpg --verify notes-2026-05-10.txt.asc notes-2026-05-10.txt` after fetching the key by fingerprint from a keyserver/WKD.)
4. **Verify the timestamp**:
   - `ots verify notes-2026-05-10.txt.ots` → reports the Bitcoin block and date the file's hash was anchored. Confirms the bytes existed by ~2026-05-10, independent of any server clock. Needs either a Bitcoin node or a trusted block-explorer lookup; `ots` will say which block to check.
5. **Corroborate** with the Wayback Machine snapshot of the same URL at publish time.
6. **Conclusion the stranger can stand behind**: "These exact bytes were signed by the holder of key `RWQ…`; that key is published in `subtract.ing`'s DNSSEC-signed zone and on `<forge>`; and the bytes were timestamped into Bitcoin on/before 2026-05-10." The web server, the CI runner, and even a later theft of the laptop key cannot retroactively manufacture that combination.

## 8. Failure modes to pre-empt

- **Key compromise later**: publish a signed revocation (`minisign` re-sign of a `REVOKED-<date>` notice) and update the DNS TXT; the OTS anchor still protects everything signed *before* the revocation date — that's why timestamping is non-optional.
- **subtract.ing disappears**: the Wayback capture + the OTS proof + the forge-hosted pubkey are sufficient on their own; that's the reason artifacts live in ≥2 places off your server.
- **Silent byte mangling by the host** (CDN minify, newline rewrite): caught immediately by the `curl … | sha256sum` check in step 5 and by `minisign -V` failing.
- **Don't** sign on the web server, don't put the secret key in CI, don't rely solely on HTTPS/the site for key distribution — each of those collapses two trust roots into one.
