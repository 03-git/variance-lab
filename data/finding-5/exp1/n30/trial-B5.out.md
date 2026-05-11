# Plan: publish a verifiably-authored `.txt` to subtract.ing

Goal restated: a stranger, a year out, with only standard tools and no trust in me or in the live web server, can confirm "the person who controls subtract.ing wrote this file, around this date."

That requires three independent things: a **signature** over the bytes, a **public key bound to the domain through anchors that outlive a server compromise**, and a **timestamp that doesn't depend on the site being up**. Below, nothing secret ever touches the web server or CI.

## Tools

- `ssh-keygen -Y sign/verify` — detached signatures (SSH-signature format, `file` namespace). Primary because every verifier already has it. (GnuPG `gpg --detach-sign` is the fallback if you'd rather anchor to the OpenPGP web of trust.)
- `opentimestamps-client` (`ots`) — Bitcoin-anchored timestamp; survives subtract.ing going dark.
- `git` with `-S` signed commits / `-s` signed tags — second, self-consistent record of order and date.
- `dig`, `curl`, a browser + `web.archive.org` — for publishing/retrieving the key-to-domain binding.
- Deploy path: whatever subtract.ing actually uses — `rsync` over SSH, or `git push` to a host like Cloudflare Pages / Netlify. The plan assumes a static site; the signing steps are deploy-agnostic.

## One-time setup (on your workstation only)

1. Generate a dedicated signing key, ideally hardware-backed so it physically can't be copied off the machine:
   ```
   ssh-keygen -t ed25519-sk -f ~/.ssh/subtracting_authorship -C authorship@subtract.ing
   ```
   (Plain `-t ed25519` with a strong passphrase if no FIDO2 key.)
2. Publish the **public** key through ≥3 independent anchors so no single compromise can rewrite the binding:
   - `https://subtract.ing/.well-known/authorship.pub` (and reference it from `humans.txt`)
   - DNS: a `TXT` record at `_authorship.subtract.ing` containing the key line
   - A third party you control: GitHub profile gist / keybase / a signed mastodon post
3. **Immediately submit the `.well-known/authorship.pub` URL and the DNS zone to `web.archive.org`** so the binding is preserved by someone other than you.
4. Create the verifier file you'll ship alongside content:
   ```
   echo "authorship@subtract.ing namespaces=\"file\" $(cut -d' ' -f1,2 ~/.ssh/subtracting_authorship.pub)" > allowed_signers
   ```
   Commit `allowed_signers` into the site repo. Consider adding `valid-after=...` so a future key rotation stays unambiguous.

## Authoring & signing (workstation)

```
$EDITOR posts/2026-05-10-essay.txt
ssh-keygen -Y sign -f ~/.ssh/subtracting_authorship -n file posts/2026-05-10-essay.txt
sha256sum posts/2026-05-10-essay.txt > posts/2026-05-10-essay.txt.sha256
ots stamp posts/2026-05-10-essay.txt
ots stamp posts/2026-05-10-essay.txt.asc 2>/dev/null || ots stamp posts/2026-05-10-essay.txt.sig
```
Produces `essay.txt`, `essay.txt.sig`, `essay.txt.sha256`, `essay.txt.ots`. Then record it in git with a signed commit:
```
git add posts/2026-05-10-essay.txt posts/2026-05-10-essay.txt.sig posts/2026-05-10-essay.txt.ots posts/2026-05-10-essay.txt.sha256
git commit -S -m "essay: <title>"
git tag -s essay-2026-05-10 -m "signed release"
```
A few hours/days later, complete the Bitcoin attestation and commit the upgraded proof:
```
ots upgrade posts/2026-05-10-essay.txt.ots
git add posts/2026-05-10-essay.txt.ots && git commit -S -m "ots: upgrade essay attestation"
```

## Which machine pushes, which does not

- **Workstation**: holds the signing key, does the signing, makes signed commits. It may also do the deploy push (`git push origin main`, or `rsync -avz --delete public/ deploy@subtract.ing:/var/www/subtract.ing/`).
- **CI / hosting build machine** (if subtract.ing builds on Cloudflare Pages/Netlify/Actions): receives only the already-signed static bytes from the repo. It has the deploy/build credential and nothing else. It does **not** have the signing key and never signs anything. If you'd rather not have CI at all, push the built site straight from the workstation via `rsync` and skip it.
- **Web server**: only ever serves bytes that were signed elsewhere.

## Authority boundaries

| Secret / authority | Lives on | Can do | Cannot do |
|---|---|---|---|
| Domain registrar + DNS account (2FA) | registrar; you | Prove/define control of subtract.ing; set the `_authorship` TXT anchor | Forge a signature |
| Signing private key | workstation only (FIDO2 token if possible); never in repo, CI, or server | Produce valid authorship signatures | — |
| Deploy credential (SSH deploy key or host API token) | the pushing machine (workstation or CI) | Replace files on the site / repo | Forge a signature under the published key |
| Git commit signing (can be the same key or a separate one) | workstation | Attest commit order & dates | — |

The point of the table: a full takeover of the web server or the CI pipeline lets an attacker swap the `.txt` — but the swapped file won't verify against the key published via DNS + the archived `.well-known` + the third-party anchor, and won't have a matching OpenTimestamps proof. Authorship survives a server compromise.

## How a verifier confirms it, a year later

1. Download `essay.txt`, `essay.txt.sig`, `essay.txt.ots` from subtract.ing (or from a Wayback snapshot if the site is gone).
2. Get the public key from anchors *other than the file itself* and check they agree:
   ```
   dig +short TXT _authorship.subtract.ing
   curl -s https://subtract.ing/.well-known/authorship.pub
   # plus the GitHub/keybase copy, and the web.archive.org snapshot of the .well-known URL
   ```
3. Build `allowed_signers` from that key and verify the bytes:
   ```
   ssh-keygen -Y verify -f allowed_signers -I authorship@subtract.ing -n file -s essay.txt.sig < essay.txt
   ```
   Expect `Good "file" signature`.
4. Verify the date independently of the website:
   ```
   ots verify essay.txt.ots
   ```
   This shows the file's hash was committed to the Bitcoin blockchain at a block whose timestamp is ~a year ago — no need to trust subtract.ing's clock or that it still exists.
5. (Optional, strengthens it) `git clone` the site repo and run `git log --show-signature` / `git tag -v essay-2026-05-10` to see the signed commit and tag with consistent dates.
6. Conclusion the stranger can stand behind: the file's bytes were signed by the holder of a key that was publicly bound to subtract.ing through multiple independent, archived channels, and a decentralized timestamp corroborates "around then." Tools needed: `ssh-keygen`, `dig`, `curl`, `ots`, a browser. No trust in me, in the host, or in the current state of the site.

## Caveats to decide up front

- **Identity vs. domain**: the above proves "controller of subtract.ing." To bind it to a named person, also `gpg --detach-sign` with a long-lived personal key that's in the OpenPGP strong set / on keybase, and ship that `.asc` too.
- **Key loss/rotation**: keep a pre-written, signed revocation statement; when rotating, publish the new key through the same anchors and add `valid-before` to the old entry in `allowed_signers` so historical files still verify.
- **Anchor rot**: re-submit the `.well-known` key URL and DNS to `web.archive.org` periodically; a binding nobody archived is a binding a server compromise can quietly rewrite.
