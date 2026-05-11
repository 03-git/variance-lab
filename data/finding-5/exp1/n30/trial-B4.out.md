# Plan: publish a verifiably-authored `.txt` to subtract.ing

Goal restated: a stranger, a year from now, should be able to fetch a file from `subtract.ing` and confirm *you* authored it — without trusting me, the sandbox, or even the web host. That means the authorship claim has to ride on a **cryptographic signature** tied to a key that's discoverable from multiple independent places, plus an independent **timestamp**. The hosting step is separate and happens from *your* machine, not this one.

I'll use `note.txt` as the placeholder filename throughout.

---

## 0. Authority boundaries (the part that constrains everything else)

| Asset | Lives only on | Never touches |
|---|---|---|
| Signing **private key** (PGP / minisign / SSH) | your laptop, ideally a YubiKey/hardware token | this sandbox, the site repo, the web host, me |
| **Deploy credential** for subtract.ing (SSH deploy key, Cloudflare/Netlify/GH token) | the machine you normally deploy from (your laptop) | this sandbox, the file's contents, me |
| The `.txt` content + signature + timestamp proof | the site repo (public) | — (these are *meant* to be public) |

- **This machine (`/private/tmp`, no repo, no creds): does not push.** It can draft `note.txt`, compute hashes, and hand you exact commands. It must not sign on your behalf or deploy.
- **Your laptop: signs and pushes.** Signing requires your secret key; deploying requires your host credential. Both are things only you should wield.
- I (the agent) am in the "draft and advise" lane only. If I were running live, I'd stop before `git push` / `wrangler deploy` and hand it back to you.

---

## 1. One-time: establish a signing identity (on your laptop)

Pick **one** primary scheme. SSH-key signing is the lowest-friction because your key is probably already on GitHub at `https://github.com/<you>.keys`, which doubles as an independent publication of the public half.

**Option A — SSH signatures (recommended):**
```bash
# use an existing ed25519 key or make a dedicated one
ssh-keygen -t ed25519 -C "subtract.ing signing" -f ~/.ssh/id_subtracting
# create an allowed-signers line for verifiers
echo "you@subtract.ing namespaces=\"file\" $(cat ~/.ssh/id_subtracting.pub)" > allowed_signers
```

**Option B — minisign:**
```bash
minisign -G -p subtracting.pub -s subtracting.key   # store .key offline; publish .pub
```

**Option C — GnuPG:** `gpg --quick-gen-key 'You <you@subtract.ing>' ed25519 sign 1y`, then `gpg --export --armor` for the public block.

Whatever you pick: the **secret** stays on the laptop/token; the **public** key/fingerprint goes into step 6.

---

## 2. Create the file (can happen here; content is yours)

```bash
printf '%s\n' "..." > note.txt
sha256sum note.txt        # record this digest; it's the thing you're signing
```
No secrets involved, so the sandbox may do this and show you the bytes + digest. You re-create or `scp` it to your laptop before signing so you've actually seen what you sign.

---

## 3. Sign the file (your laptop only)

**SSH:**
```bash
ssh-keygen -Y sign -f ~/.ssh/id_subtracting -n file note.txt
# produces note.txt.sig
```
**minisign:**
```bash
minisign -S -s subtracting.key -m note.txt -t "subtract.ing note.txt $(date -u +%FT%TZ)"
# produces note.txt.minisig
```
**gpg:** `gpg --armor --detach-sign note.txt` → `note.txt.asc`

---

## 4. Independent timestamp (so "a year from now" is anchored, not just asserted)

OpenTimestamps anchors a hash in the Bitcoin blockchain — no trusted third party, verifiable forever:
```bash
pip install opentimestamps-client
ots stamp note.txt          # creates note.txt.ots (upgrade it to a confirmed proof after ~a few hours)
ots upgrade note.txt.ots
```
(Belt-and-suspenders alternative: an RFC-3161 token from `freetsa.org` via `openssl ts -query ... -out note.txt.tsr`.) Ship the `.ots` next to the file.

---

## 5. Put it in the site repo (your laptop)

```bash
git switch -c add-note-txt
cp note.txt note.txt.sig note.txt.ots allowed_signers  <site-repo>/public/   # path depends on your generator
git add public/note.txt public/note.txt.sig public/note.txt.ots allowed_signers
git -c commit.gpgsign=true commit -S -m "Publish note.txt with detached signature + OTS proof"
git tag -s note-txt-v1 -m "note.txt as published $(date -u +%F)"
```
A signed commit + signed tag give a *second* signature path that GitHub will render as "Verified."

---

## 6. Publish the public key in ≥2 independent places

Redundancy is what makes it survive a year and a host change:
1. `https://github.com/<you>.keys` (automatic if you used your GH SSH key) and/or upload to `keys.openpgp.org`.
2. A `pubkey/` page **on subtract.ing itself** (`/.well-known/` or a linked page) containing the SSH allowed-signers line / minisign pubkey / PGP fingerprint.
3. A DNS record: `OPENPGPKEY` / a `TXT` at `subtract.ing` carrying the fingerprint. DNS history is independently archived (e.g. SecurityTrails), so this timestamps the key→domain binding.
4. Mention the fingerprint somewhere social (a pinned post) for good measure.

---

## 7. Deploy — *from the machine that holds the deploy credential*

Whatever subtract.ing actually is:
- GitHub Pages: `git push origin add-note-txt` → merge PR; Pages action publishes.
- Cloudflare Pages / Workers: `npx wrangler pages deploy ./public` (token in your laptop's env, not here).
- Netlify: `netlify deploy --prod`.
- Plain host: `rsync -a public/ user@host:/var/www/subtract.ing/` over your SSH deploy key.

This is the step this sandbox **cannot and should not** do — it has no credential and no business getting one.

---

## 8. Freeze a third-party snapshot (right after deploy)

```bash
curl -s "https://web.archive.org/save/https://subtract.ing/note.txt"
curl -s "https://web.archive.org/save/https://subtract.ing/note.txt.sig"
curl -s "https://web.archive.org/save/https://subtract.ing/note.txt.ots"
# and archive.today as a second archiver
```
Now the file's existence-at-time-T is witnessed by the Wayback Machine independent of your host and of Bitcoin.

---

## 9. How a stranger verifies it, a year later

```bash
# 1. fetch the artifacts
curl -O https://subtract.ing/note.txt
curl -O https://subtract.ing/note.txt.sig
curl -O https://subtract.ing/note.txt.ots

# 2. fetch the claimed signer's public key from an INDEPENDENT source
curl https://github.com/<you>.keys -o you.pub          # or keys.openpgp.org, or DNS OPENPGPKEY
printf 'you@subtract.ing namespaces="file" %s\n' "$(cat you.pub)" > allowed_signers

# 3. verify the signature
ssh-keygen -Y verify -f allowed_signers -I you@subtract.ing -n file -s note.txt.sig < note.txt
#   → "Good \"file\" signature for you@subtract.ing"
#   (minisign:  minisign -Vm note.txt -P <pubkey>      gpg: gpg --verify note.txt.asc note.txt)

# 4. verify the timestamp (proves the bytes existed before block N's date)
ots verify note.txt.ots
#   → "Success! Bitcoin block <N> attests existence as of <date>"

# 5. cross-checks (no install needed)
#    - GitHub shows commit/tag "Verified" with the same key
#    - web.archive.org snapshot of /note.txt from publish date, same sha256
#    - DNS history shows the OPENPGPKEY/TXT fingerprint predates or matches
sha256sum note.txt   # compare against the archived copy
```

The chain the verifier ends up trusting: **signature** says "holder of this key signed exactly these bytes" → **multiple independent key publications** say "that key is the subtract.ing operator's" → **OpenTimestamps + Wayback + DNS history** say "this all existed at time T, not backdated." None of it requires trusting me, the sandbox, or the current state of the web host.

---

## What I would *not* do
- Generate or handle your private key here, or "temporarily" copy it into the sandbox.
- Run the deploy from this environment, or ask you to paste a deploy token / SSH key here.
- Treat "I uploaded the file" as authorship — without the signature, anyone with write access to the host could have done it, so it proves nothing to a stranger.
