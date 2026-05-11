## Goal restated

Put `post.txt` on `subtract.ing` such that a stranger, a year from now, can confirm *I* authored it — without trusting the website, its TLS cert, or its host at verification time. That means: a detached cryptographic signature, a public key distributed through channels independent of the site, and a timestamp anchored to something that can't be backdated.

HTTPS on `subtract.ing` is explicitly *not* part of the authorship proof — it only attests "whoever controls the server right now," which is the wrong claim and the wrong time.

---

## Authority boundaries (decide these before touching anything)

- **Signing machine** holds the private key. Ideally the key lives on a hardware token (YubiKey, `gpg --card-edit`) or at minimum a passphrase-protected keyring on the user's workstation. The private key is never copied, never put in the repo, never transmitted, never shown to me. I (the agent) operate only in the working dir and run local commands; I do not exfiltrate key material.
- **Publishing machine** holds the `subtract.ing` write credential (deploy SSH key, CI token, or rsync target). This is a *separate credential scope* from the signing key even if it's physically the same laptop. The agent does **not** hold the deploy credential — the push is run by the user, or by CI triggered by the user.
- **Outward-facing actions that need explicit user approval before I do them** (each is hard to unring): publishing the public key to a keyserver, creating DNS records, pushing to the site/repo, submitting the URL to archive.org, writing to a public transparency log. I prepare these; the user authorizes and executes the ones that leave the machine.
- The working dir here is `/private/tmp` and not a git repo — so any git-based step starts with an explicit `git init` in a directory the user designates, not here.

---

## Step 1 — Author the file locally (signing machine)

```
mkdir -p ~/subtracting-post && cd ~/subtracting-post
$EDITOR post.txt          # write the content; finalize it — any later byte change breaks the signature
sha256sum post.txt        # record the digest for your own notes
```

## Step 2 — Establish (or reuse) a signing identity

If no long-term key exists:

```
gpg --full-generate-key      # choose ECC (ed25519), set a real expiry (e.g. 3y), strong passphrase
gpg --list-secret-keys --keyid-format=long      # note the full 40-hex fingerprint FPR
gpg --armor --export $FPR > pubkey.asc
```

The fingerprint `FPR` is the thing the world has to know is "mine." Its value comes from being published in multiple independent places *now*, so a forger a year from now can't retroactively control all of them.

## Step 3 — Sign the file

```
gpg --armor --detach-sign --output post.txt.asc post.txt
gpg --verify post.txt.asc post.txt          # sanity check: "Good signature"
```

(Equivalent alternatives, pick one and stay consistent: `minisign -Sm post.txt` with a published `minisign.pub`; or `cosign sign-blob --bundle post.txt.bundle post.txt` which also writes to the Rekor public transparency log and gives you a timestamp for free.)

## Step 4 — Anchor a tamper-evident timestamp (so "a year ago" is provable)

Belt and suspenders, because each anchor has different failure modes:

- **OpenTimestamps** (anchors a hash into the Bitcoin chain):
  ```
  pip install opentimestamps-client
  ots stamp post.txt          # -> post.txt.ots
  # ~a few hours later, once it's in a block:
  ots upgrade post.txt.ots
  ots verify post.txt.ots      # confirms existence before a dated block
  ```
- **Signed git tag** in a public repo (GitHub/Codeberg), which also corroborates the date via the host's own logs:
  ```
  git init && git add post.txt post.txt.asc post.txt.ots pubkey.asc
  git commit -S -m "post.txt for subtract.ing"
  git tag -s subtracting-post -m "signed release"
  # push step is Step 6's authority class — user runs it
  ```
- **archive.org snapshot** of the eventual live URL (third-party-attested date) — submitted after Step 5, via `https://web.archive.org/save/https://subtract.ing/post.txt`.

## Step 5 — Publish the key through site-independent channels (user authorizes)

So the verifier can get `FPR` *without* trusting `subtract.ing`:

- Upload to `https://keys.openpgp.org` (verified-email distribution), or `gpg --keyserver keys.openpgp.org --send-keys $FPR`.
- WKD: serve `pubkey.asc` at `https://<your-domain>/.well-known/openpgpkey/...` if you control another domain.
- A DNSSEC-signed `TXT` record on a domain you control containing `FPR`.
- Post `FPR` somewhere with its own timestamping: a tweet/Mastodon post, a Keybase proof, a Git commit. Three independent places is plenty.

Also put `FPR` (not just the file) into `post.txt` itself or a sibling `SIGNED-BY.txt` — convenient, but it does *not* count as an independent channel.

## Step 6 — Push to subtract.ing (publishing machine / CI — not the agent)

Whatever `subtract.ing`'s pipeline is, the upload runs from the credentialed machine, by the user:

- static-site-in-git: `git push` to the deploy remote → CI (`Cloudflare Pages` / `Netlify` / `GitHub Pages` / a `Caddy`/`nginx` box) publishes.
- or direct: `rsync -av post.txt post.txt.asc post.txt.ots pubkey.asc deploy@subtract.ing:/var/www/subtract.ing/`

Publish all four artifacts at stable URLs:
`/post.txt`, `/post.txt.asc`, `/post.txt.ots`, `/pubkey.asc`.

Then submit the live `/post.txt` URL to `web.archive.org/save/`.

---

## How a stranger verifies, a year from now

1. Download `https://subtract.ing/post.txt` and `https://subtract.ing/post.txt.asc`.
2. Get the public key from a channel *not* controlled by subtract.ing — `gpg --keyserver keys.openpgp.org --recv-keys $FPR` (or WKD, or the DNSSEC TXT record). Confirm the key's fingerprint equals the `FPR` that was published in those several independent places (and check those publications are themselves a year old: tweet date, git history, `keys.openpgp.org` first-seen, DNS history).
3. `gpg --verify post.txt.asc post.txt` → expect **"Good signature from <identity>"** and that the signing key's creation date precedes the post.
4. Establish the date independently of the server's claims:
   - `ots verify post.txt.ots` → "success! Bitcoin block <N> attests existence as of <date ~1yr ago>"; and/or
   - the signed, dated git tag in the public repo (`git tag -v subtracting-post`), corroborated by GitHub's commit timestamps; and/or
   - the archive.org snapshot timestamp on the live URL.
5. Conclusion the stranger can defend: the bytes of `post.txt` existed by date *D*, were signed by the holder of key `FPR`, and `FPR` was publicly claimed by me across multiple channels before *D*. Forging that requires breaking ed25519 *or* having compromised several independent publication channels a year ago and waited — which is the bar we wanted.

**What this deliberately does not depend on:** subtract.ing being up, its TLS cert, its DNS, its host, or me being reachable in a year. The file could be re-served from anywhere and still verify.

---

## What I'd need from you to actually do it

- Confirmation to perform the outward-facing steps (keyserver upload, DNS, repo push, archive.org) — and which of those you want.
- The real publish mechanism for `subtract.ing` (git remote? rsync target? CMS?) and which machine holds that credential.
- Whether a signing key already exists or I should walk you through generating one (you run the `gpg` keygen so the passphrase/private key never reach me).
