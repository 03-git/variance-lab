# Plan: publish a verifiably-authored `.txt` to subtract.ing

Not executing anything — this is the plan only. Two things have to be true at the end: (1) the file is live at `https://subtract.ing/<name>.txt`, and (2) a stranger in May 2027 can independently tie that file's bytes to *you*.

## 0. Authority boundaries (decide this first)

- **This sandbox (`/private/tmp`, ephemeral, non-git):** may be used to *draft* the `.txt`, compute hashes, and write out command scripts. It must **never** hold your signing private key, your SSH deploy key, or your `gh`/hosting credentials, and it must **not** run the push. Treat anything here as disposable and world-readable.
- **Your personal machine (the one with your GPG/SSH keys in `~/.gnupg` / `~/.ssh` and your password manager):** this is the only machine that signs and the only machine that pushes/deploys. Call this the *trusted machine*.
- **Outward-facing, hard-to-reverse:** publishing to a live domain and pushing a signature to public keyservers are both effectively permanent (CDNs, archives, keyserver replication). I'd confirm with you before any of those steps even on the trusted machine; approval to draft is not approval to publish.
- **Key custody:** authorship proof rests on a key that already exists and that strangers can already associate with you, *or* on one you create now and publish through several independent channels. A brand-new key with no prior public footprint proves "whoever holds this key wrote it," not "you wrote it" — so the binding step (3 and 6) matters as much as the signature.

## 1. Draft the file (sandbox OK)

- Write the content to `subtract-ing-<slug>.txt` here. Decide on a fixed final filename, e.g. `2026-05-10-<slug>.txt`. UTF-8, LF newlines, final newline — pin the bytes now because the signature covers exact bytes.
- Inside the file, include a self-identifying header line so the artifact is meaningful out of context, e.g.:
  ```
  Author: <Your Name> <key fingerprint EB1A 2F... >
  Date:   2026-05-10
  Canonical URL: https://subtract.ing/2026-05-10-<slug>.txt
  ```
- Record the digest: `shasum -a 256 2026-05-10-<slug>.txt` (or `sha256sum`). Note it down — you'll re-check it on the trusted machine before signing.

## 2. Move the file to the trusted machine

- `scp` / `rsync` the `.txt` from sandbox to your machine, or just paste it — then `shasum -a 256` again there and confirm it equals the digest from step 1. Everything after this happens on the trusted machine.

## 3. Establish the identity key (trusted machine)

Pick one signing mechanism and stick with it. Options, best-supported first:

- **GPG (most widely verifiable):** use an existing key if you have one with a public history. Otherwise `gpg --full-generate-key` (Ed25519, set a real expiry, e.g. 2 years). Then publish the public key through *independent* channels so the binding isn't single-sourced:
  - `gpg --send-keys <FPR>` to `hkps://keys.openpgp.org` (and do the email-verification step so the UID is searchable).
  - Commit `pubkey.asc` into a repo you control with a long history (see step 5).
  - Add a `https://subtract.ing/.well-known/openpgpkey/...` WKD entry, or at minimum a DNS `TXT`/a published fingerprint on a page you already control (your existing site, GitHub profile, Mastodon bio). Three places > one.
- **minisign / signify:** `minisign -G` → publish `minisign.pub` the same multi-channel way. Simpler, but fewer strangers have the tool.
- **SSH signature (`ssh-keygen -Y sign`):** convenient if your SSH key is already on your GitHub profile (`https://github.com/<you>.keys`) — that URL *is* a pre-existing public binding. Use namespace `file`.

## 4. Sign the file (trusted machine)

- GPG: `gpg --armor --detach-sign --output 2026-05-10-<slug>.txt.asc 2026-05-10-<slug>.txt`
- or minisign: `minisign -Sm 2026-05-10-<slug>.txt` → produces `.minisig`
- or SSH: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file 2026-05-10-<slug>.txt` → produces `.sig`
- Verify your own signature locally before going further (`gpg --verify ...`, `minisign -Vm ...`, or `ssh-keygen -Y verify`).

## 5. Independent timestamp (so "a year from now" is anchored, trusted machine)

A signature says *who*, not *when*. Add at least one of:

- **OpenTimestamps:** `ots stamp 2026-05-10-<slug>.txt` → `2026-05-10-<slug>.txt.ots`. Wait for Bitcoin confirmation, then `ots upgrade`. This is the strongest "existed by this date" proof and needs no trusted third party to verify later.
- **Signed git tag** in the deploy repo (step 6): `git tag -s 2026-05-10-<slug> -m "publish <slug>.txt"` — the tag object carries a GPG-signed, dated commitment.
- **archive.org:** after publishing, submit the live URL to `https://web.archive.org/save/https://subtract.ing/2026-05-10-<slug>.txt`. Independent third-party dated copy.

## 6. Publish to subtract.ing — which machine pushes

The push happens **only from the trusted machine**, using your real credentials. Mechanism depends on how subtract.ing is hosted:

- **If it's a static site in a Git repo (GitHub Pages / Netlify / Cloudflare Pages):**
  - `git clone` the site repo on the trusted machine (or use your existing local clone).
  - Add `2026-05-10-<slug>.txt`, the signature file (`.asc`/`.minisig`/`.sig`), the `.ots`, and `pubkey.asc` (or a link to it) into the published tree.
  - `git add` → `git commit -S -m "Publish 2026-05-10-<slug>.txt with detached signature"` (signed commit) → `git tag -s ...` → `git push origin main --follow-tags`.
  - Use `gh auth status` to confirm you're pushing as yourself; `gh repo view` to confirm the remote. The CI/host deploys to the domain.
- **If it's a server you control (e.g. nginx):** `rsync -av 2026-05-10-<slug>.txt 2026-05-10-<slug>.txt.asc 2026-05-10-<slug>.txt.ots user@subtract.ing:/var/www/subtract.ing/` over your SSH key — again, only from the trusted machine.
- Either way, make sure the server returns `Content-Type: text/plain; charset=utf-8` for the `.txt` and that the signature file is reachable at a predictable path, e.g. `https://subtract.ing/2026-05-10-<slug>.txt.asc`.
- After it's live: `curl -fsSL https://subtract.ing/2026-05-10-<slug>.txt | shasum -a 256` and confirm the digest still matches step 1. Then fire the archive.org save (step 5).

## 7. Leave a verification breadcrumb

On the page or in a `SIGNATURES.md` / the file's own header, state plainly: the signing key fingerprint, where the public key lives (keys.openpgp.org link, `github.com/<you>.keys`, WKD), the signature file URL, and the `.ots` file URL. A stranger shouldn't have to guess the scheme.

## 8. How a verifier (a stranger, May 2027) confirms the claim

1. `curl -O https://subtract.ing/2026-05-10-<slug>.txt` and `curl -O https://subtract.ing/2026-05-10-<slug>.txt.asc`.
2. Fetch the public key from a channel that isn't subtract.ing — `gpg --locate-keys <your-email>` (hits keys.openpgp.org/WKD), or `curl https://github.com/<you>.keys`, or Keybase. Cross-check the fingerprint against the one printed in the file header and on your other properties. Independent agreement across channels is what makes it *your* key.
3. `gpg --verify 2026-05-10-<slug>.txt.asc 2026-05-10-<slug>.txt` → expects "Good signature from <Your Name>" with that fingerprint. (Or `minisign -Vm ... -P <pubkey>`, or `ssh-keygen -Y verify -f allowed_signers -I <your-email> -n file -s ...sig`.)
4. Timestamp: `ots verify 2026-05-10-<slug>.txt.ots` → confirms the bytes existed and were committed to the Bitcoin chain on/around 2026-05-10, i.e. not backdated. And/or check the web.archive.org snapshot date, and/or `git verify-tag 2026-05-10-<slug>` in the public repo.
5. Conclusion the stranger can stand behind: *these exact bytes were signed by the holder of key `<FPR>`, that key is bound to <Your Name> via multiple independent sources, and the content demonstrably existed by 2026-05-10.* That's verifiable authorship a year out, and it doesn't depend on subtract.ing still being up or on trusting me or this sandbox.

## What I would *not* do

- Not generate or store the signing key in this sandbox, not run `git push`/`rsync`/`gpg --send-keys` from here, not handle your `gh` token or SSH deploy key here.
- Not publish until you confirm the final filename, content bytes, and that you want it live — domain publication and keyserver upload don't un-happen.
