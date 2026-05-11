# Plan: publish a verifiably-authored `.txt` to subtract.ing

Goal: a stranger in May 2027 can confirm "the holder of identity X authored this file and it existed by May 2026" without trusting the website's own claims. The backbone is a **cryptographic signature** over the file plus an **independent timestamp anchor**; the website is just a delivery channel.

## 1. Choose the identity & signing mechanism
Use one of (I'd pick SSH signatures for simplicity, or GPG if you want keyserver/WKD distribution):

- **SSH signatures** (`ssh-keygen -Y sign`) — minimal, no keyring.
- **GPG detached signature** — wider tooling, distributable via keyservers/WKD.

Either way, generate a *dedicated* key, not your login/auth key:
```
ssh-keygen -t ed25519 -f ~/.ssh/subtracting_authorship -C "authorship@subtract.ing"
# or
gpg --quick-generate-key "authorship <you@subtract.ing>" ed25519 sign 2y
```

## 2. Authority boundaries — which machine does what
- **Signing machine** (ideally a hardware token — YubiKey via `gpg --card-edit` / `ssh-keygen -t ed25519-sk` — or an offline laptop): holds the *private signing key*. It runs only the `sign` command. It has **no deploy credentials and never pushes**.
- **Deploy machine**: holds the credentials that can mutate subtract.ing (rsync/SSH deploy key, or Cloudflare Pages / Netlify / GitHub Pages token). It pushes the file + signature + timestamp proof. It **never holds the signing key**.
- **DNS/registrar control**: a third authority — adds a TXT record binding the key to the domain. Separate from both above.
- **This agent (me)**: would author the file, compute hashes, and prepare the signature *request*, but would **not** push to the live site, publish a key to a keyserver, or change DNS without your explicit go-ahead — those are outward-facing and effectively irreversible (keyservers are append-only; a published page may be cached/archived). I'd hand you the exact commands and let the signing/deploy/DNS holders run them.

## 3. Create and sign the file (signing machine)
```
# author the file (name encodes the date for humans; the crypto is what counts)
$EDITOR post-2026-05-10.txt

# SSH-signature path:
ssh-keygen -Y sign -f ~/.ssh/subtracting_authorship -n file post-2026-05-10.txt
# -> post-2026-05-10.txt.sig

# OR GPG path:
gpg --armor --detach-sign --output post-2026-05-10.txt.asc post-2026-05-10.txt

# content manifest for good measure
sha256sum post-2026-05-10.txt > SHA256SUMS
```

## 4. Anchor the date independently (so it doesn't rely on the site)
OpenTimestamps writes a commitment into the Bitcoin blockchain:
```
pip install opentimestamps-client
ots stamp post-2026-05-10.txt.sig      # stamping the sig also commits to the file's hash
# (re-run `ots upgrade post-2026-05-10.txt.sig.ots` a few hours later once confirmed)
```
Also submit the live URL to the Wayback Machine the day you publish (`https://web.archive.org/save/https://subtract.ing/post-2026-05-10.txt`) as corroboration.

## 5. Publish the key→domain binding
- **GPG**: publish via Web Key Directory at `https://subtract.ing/.well-known/openpgpkey/...` (`gpg --list-keys`, then use `wkd` tooling) and/or `gpg --keyserver keys.openpgp.org --send-keys <FPR>`.
- **SSH**: publish an `allowed_signers` line at `https://subtract.ing/.well-known/allowed_signers`:
  ```
  authorship@subtract.ing namespaces="file" ssh-ed25519 AAAA...   # contents of the .pub
  ```
- **DNS** (the domain-bound anchor): add `TXT _authorship.subtract.ing  "ssh-ed25519 AAAA..."` or the GPG fingerprint. (DNS is mutable, so it's corroborating, not dispositive — the signature + OTS is the part that survives a year regardless.)

## 6. Push (deploy machine only)
Upload `post-2026-05-10.txt`, `.sig`/`.asc`, `.sig.ots`, `SHA256SUMS`, and the `.well-known/` files via whatever the site's pipeline is, e.g.:
```
rsync -av post-2026-05-10.txt post-2026-05-10.txt.sig post-2026-05-10.txt.sig.ots SHA256SUMS \
      deploy@subtract.ing:/var/www/subtract.ing/
# or: git commit -S … && git push   (signed commit, if the site is a git-deployed repo)
```
If git-deployed, also `git tag -s post-2026-05-10 -m "publish"` — a second, independent signature over the same content.

## 7. How a verifier confirms it (May 2027, from scratch)
```
# 1. fetch artifacts
curl -O https://subtract.ing/post-2026-05-10.txt
curl -O https://subtract.ing/post-2026-05-10.txt.sig          # or .asc
curl -O https://subtract.ing/post-2026-05-10.txt.sig.ots
curl -O https://subtract.ing/.well-known/allowed_signers       # or fetch the GPG key via WKD

# 2. confirm the key is the one the domain claims
dig +short TXT _authorship.subtract.ing            # matches the pubkey in allowed_signers?

# 3. verify the signature
ssh-keygen -Y verify -f allowed_signers -I authorship@subtract.ing -n file \
           -s post-2026-05-10.txt.sig < post-2026-05-10.txt
#   -> "Good "file" signature for authorship@subtract.ing"
# (GPG path: gpg --locate-keys you@subtract.ing && gpg --verify post-2026-05-10.txt.asc post-2026-05-10.txt)

# 4. verify the file existed by the claimed date, independent of the site
ots verify post-2026-05-10.txt.sig.ots
#   -> "Bitcoin block <N> attests existence as of 2026-05-10..."

# 5. corroborate: Wayback snapshot from May 2026; signed git tag if the repo is public
```
Chain of reasoning the verifier ends up with: the DNS record + `.well-known` say *this* key speaks for subtract.ing; the signature says the key's holder vouched for these exact bytes; OpenTimestamps says those bytes existed by 2026-05-10; the Wayback snapshot independently shows the page live then. No need to trust the web server's mutable state in 2027.

## Failure modes handled
- Site goes down / page edited → signature + `.ots` + keyserver copy still verify offline; Wayback corroborates.
- Key later compromised/rotated → the OTS anchor proves the signature predates any later compromise.
- Someone re-hosts a forged file → fails signature verification.
- DNS record changed → the cryptographic signature is unaffected; only the convenience binding is, and the keyserver/WKD/archived `.well-known` still pin it.

One residual gap to accept or close: the binding "this key = this person/domain" rests on whoever controlled DNS + the web root in May 2026. To harden it, also have the key cross-signed by an already-known identity of yours (existing GPG key, Keybase, a signed tweet) at publish time.
