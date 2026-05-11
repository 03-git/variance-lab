# Plan: publish `claim.txt` to subtract.ing with stranger-verifiable authorship

## 1. What "verifiable a year from now" actually requires

Three independent bindings, each from a different authority:

- **content ↔ key**: a detached cryptographic signature over the exact bytes.
- **key ↔ domain**: the public key advertised from something only the domain owner controls (DNS), so "subtract.ing's author" is meaningful.
- **signature ↔ time**: a timestamp proof anchored in a public ledger, so the signature can't be backdated and the key-domain binding is pinned to publication time.

Plus a belt-and-suspenders **independent archive** so the verifier doesn't have to trust that subtract.ing still serves the same bytes next year.

## 2. One-time setup

- Generate a signing keypair on the machine that holds long-term secrets (laptop or, better, an offline box), ideally with the private key on a hardware token:
  - `minisign -G -p subtract.pub -s subtract.key` (clean, single-purpose), **or**
  - `gpg --full-generate-key` (ed25519) if you want WKD/keyserver distribution, **or**
  - `ssh-keygen -t ed25519 -f subtract_sign` + `ssh-keygen -Y sign` if you prefer SSH-signature tooling.
- Publish the **public** key in two places that a stranger can reach:
  1. DNS TXT record via your registrar/DNS console: `_minisign.subtract.ing TXT "<contents of subtract.pub>"` — this is the key↔domain proof.
  2. A stable URL on the site itself: `https://subtract.ing/.well-known/minisign.pub`.
- Optionally also pin it somewhere off-domain (Keybase, a signed git tag, a GitHub gist) so the binding survives even if you later lose the domain.

## 3. Machines and authority boundaries

| Role | Machine | Holds | Can it sign? | Can it publish? |
|---|---|---|---|---|
| **Signer** | your laptop / offline box (key on YubiKey ideally) | `subtract.key` (private) | yes | no — has no deploy creds |
| **DNS authority** | registrar web console (browser session) | DNS zone control | no | only the TXT record (the key↔domain binding) |
| **Publisher / pusher** | the host's deploy path — a GitHub Actions runner, or `rsync`/`scp` from a CI box | deploy key / hosting token, and the *already-signed* artifacts | no — never sees `subtract.key` | yes — writes `claim.txt`, `claim.txt.minisig`, `claim.txt.ots` into the webroot |

The separation that matters: **the machine that pushes never possesses the signing key**; it only carries files and detached signatures produced elsewhere. The signing machine never carries deploy credentials. Compromise of the web host therefore cannot forge new authored files, and compromise of the laptop cannot silently alter what's served.

## 4. Publish sequence

On the **signer**:
1. Write the file; freeze its bytes: `sha256sum claim.txt` (record this).
2. Sign it: `minisign -Sm claim.txt -s subtract.key` → produces `claim.txt.minisig`.
3. Timestamp the file (signature↔time, trustless, Bitcoin-anchored): `ots stamp claim.txt` → produces `claim.txt.ots`. (Wait for upgrade later: `ots upgrade claim.txt.ots` once the calendar attests, ~a few hours.)
4. Hand off `claim.txt`, `claim.txt.minisig`, `claim.txt.ots` to the publisher (commit to the site repo, or copy to the CI artifact dir) — **not** the key.

On the **publisher** (e.g. GitHub Actions deploy job, or a one-liner):
5. Deploy: `rsync -av claim.txt claim.txt.minisig claim.txt.ots deploy@subtract.ing:/var/www/subtract.ing/` (or `git push` triggering Pages/Netlify). Confirm `https://subtract.ing/claim.txt` etc. resolve.

Independent archive (from anywhere):
6. `curl -s "https://web.archive.org/save/https://subtract.ing/claim.txt"` and the same for `.minisig` and `.ots`. Note the returned Wayback timestamp. Optionally also `archive.today`.
7. Also snapshot the DNS state now (e.g. a dated screenshot/export of the `_minisign` TXT record, or rely on passive-DNS history providers) so the key↔domain binding at publication time is independently recorded.

## 5. How a stranger verifies, a year later

1. Fetch artifacts:
   `curl -O https://subtract.ing/claim.txt` (and `.minisig`, `.ots`), plus the pubkey: `curl -O https://subtract.ing/.well-known/minisign.pub`.
2. Confirm the key really belongs to the domain, not just to whoever served the file:
   `dig +short TXT _minisign.subtract.ing` and check it matches `minisign.pub`. Cross-check the off-domain copy (Keybase/gist) and a Wayback snapshot of `_minisign` / the `.well-known` URL from ~a year ago.
3. Verify content↔key:
   `minisign -Vm claim.txt -p minisign.pub` → must print "Signature and comment signature verified". (With GPG: `gpg --verify claim.txt.asc claim.txt`; with SSH sigs: `ssh-keygen -Y verify -f allowed_signers -I subtract.ing -n file -s claim.txt.sig < claim.txt`.)
4. Verify signature↔time:
   `ots verify claim.txt.ots` → reports the Bitcoin block height/date the bytes provably existed by. Combined with step 2's archived DNS, this shows the author-binding held when the file was published, and that nothing was backdated.
5. Corroborate independently:
   - `https://web.archive.org/web/2025*/https://subtract.ing/claim.txt` — same bytes, archived near publication.
   - `https://crt.sh/?q=subtract.ing` — Certificate Transparency log shows the domain's TLS history, i.e. continuity of control.
   - If the site is a public git repo: GitHub's commit/tag signature view and push history on that repo.

If steps 3 and 4 pass and step 2's binding checks out against at least one source the current site operator couldn't retroactively rewrite (Wayback, passive DNS, CT, Bitcoin via OTS), the verifier can conclude the holder of subtract.ing's published signing key authored exactly those bytes, at or before the anchored time.

## Notes / failure modes to plan around

- OTS only proves *existence-before*; it does not prove *who*. The "who" comes entirely from the key↔domain binding — so the DNS/`.well-known` publication and its archival are the load-bearing step, not the timestamp.
- If the private key later leaks, past OTS-anchored signatures are still trustworthy (they predate the leak); revoke and rotate the published key going forward.
- Don't let the deploy pipeline regenerate or re-sign anything; it must ship the exact `.minisig`/`.ots` produced on the signer, or the chain breaks.
- Keep the byte-exact `claim.txt` (and its `sha256`) in your own records too; trailing-newline or CRLF changes by an editor or web server will invalidate the signature.
