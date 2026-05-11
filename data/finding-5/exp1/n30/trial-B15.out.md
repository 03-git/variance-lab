## Goal restated

"Authorship verifiable by a stranger in a year" ≠ "the file sits on subtract.ing." Domains lapse, hosts get compromised, TLS certs rotate. The durable claim has to rest on **a signature from a key you control** plus **an independent timestamp**, with the web server treated as an untrusted delivery channel. So the plan separates three roles: **signer** (holds the secret key, does not push), **publisher** (holds deploy credentials, pushes, never holds the secret key), **host** (serves bytes, holds neither).

---

## 1. Pick the trust anchor: a dedicated signing keypair

Use `minisign` (small, single-purpose, stable signature format; `ssh-keygen -Y sign` is an equivalent fallback).

On the **signer machine** (your laptop, ideally with the secret on a YubiKey or in an `age`-encrypted blob; this machine will *not* be the one running deploy commands):

```
minisign -G -p subtract-author.pub -s subtract-author.key
# record the fingerprint minisign prints (the 'untrusted comment' contains the key id)
```

- `subtract-author.key` — secret. Never leaves this machine; never copied to the host; never put in the website repo. Back it up offline (paper/HSM).
- `subtract-author.pub` — public. This is the thing strangers will need, so it must be discoverable from channels that outlive subtract.ing.

## 2. One-time: publish the public key in ≥3 independent places, then archive them

The verifier must be able to get the pubkey *without* trusting subtract.ing alone (otherwise whoever seizes the domain can swap key + file together).

- DNS TXT record at the registrar: `subtract-author._minisign.subtract.ing  TXT  "<base64 pubkey line>"`
- A GitHub gist (or repo) under your account containing `subtract-author.pub`.
- A Keyoxide / `keys.openpgp.org`-style identity page, or a signed message on an existing account (Mastodon bio, etc.).
- Then snapshot each: `curl "https://web.archive.org/save/https://gist.github.com/<you>/<id>"` and same for the DNS-over-HTTPS lookup URL. Now the "independent channel" is itself frozen in the Wayback Machine with a 2026 date.

Authority note: putting the key in DNS uses your **registrar account** — that's domain authority, not authorship authority. It's one of several corroborating copies, deliberately not the only one.

## 3. Per-file publish flow

### a. Author the file (signer machine)
Make it self-describing so it's legible even stripped of metadata:

```
2026-05-10.txt
---------------
Author: <name/handle>
Date (UTC): 2026-05-10
Signing key (minisign): RWQ<...>            <- fingerprint of subtract-author.pub
Verify: minisign -Vm 2026-05-10.txt -P <pubkey>; ots verify 2026-05-10.txt.ots
---------------
<body>
```

### b. Sign it (signer machine)
```
minisign -S -s subtract-author.key -m 2026-05-10.txt \
  -t "subtract.ing note; author <handle>; 2026-05-10T00:00:00Z"
```
This writes `2026-05-10.txt.minisig`. The `-t` "trusted comment" is *also* covered by the signature, so the asserted date/purpose can't be edited without breaking it.

### c. Independent timestamp (signer machine)
`pip install opentimestamps-client`, then:
```
ots stamp 2026-05-10.txt
```
Produces `2026-05-10.txt.ots`. Over the next hours it gets anchored into the Bitcoin blockchain — a non-custodial proof that *these exact bytes existed by this date*, which survives even if subtract.ing, GitHub, and your DNS all disappear. (If you also host the site from a GitHub Pages repo, additionally `git config gpg.format ssh` + `git commit -S` so the commit timestamp in GitHub's logs is a second anchor — but OTS is the one that doesn't depend on a company.)

### d. Hand off only public artifacts
Move `2026-05-10.txt`, `.minisig`, `.ots` to the **publisher machine** (or publisher role on the same box, but the secret key is not involved from here on). Re-run `ots upgrade 2026-05-10.txt.ots` a day later to embed the Bitcoin attestation, and re-publish the upgraded `.ots`.

### e. Push (publisher machine — the one with deploy creds)
Whatever subtract.ing actually is:
- static host / VPS: `rsync -av 2026-05-10.txt 2026-05-10.txt.minisig 2026-05-10.txt.ots user@subtract.ing:/var/www/notes/`
- Netlify/Cloudflare Pages: `netlify deploy --prod --dir=public`
- GitHub Pages: `git add notes/2026-05-10.txt* && git commit -S -m "note 2026-05-10" && git push`

Also drop `subtract-author.pub` at a stable path (`https://subtract.ing/subtract-author.pub`) for convenience — but remember step 2 means the verifier doesn't *have* to trust that copy.

TLS on subtract.ing (Let's Encrypt via the host's ACME client) matters only for integrity-in-transit at fetch time; it proves nothing about authorship a year out, so it's not part of the trust chain — just hygiene.

## 4. Authority boundaries

| Capability | Who holds it | What it can do | What it proves about authorship |
|---|---|---|---|
| `subtract-author.key` (minisign secret) | **signer machine only**, offline | produce valid signatures | **everything** — this *is* the identity |
| Registrar/DNS account | publisher/you | repoint subtract.ing, change the TXT copy of the pubkey | nothing — can serve a different file under the name, can't forge a signature |
| Host SSH key / Netlify token / Pages write | **publisher machine** | replace/delete files on subtract.ing | nothing — tampered file fails `minisign -V` |
| Let's Encrypt cert (on host) | host | terminate TLS | nothing about authorship over time |
| GitHub account, Keyoxide, Mastodon | you | host corroborating pubkey copies | corroboration only; collusion would need *all* of them + the Wayback snapshots |
| Bitcoin blockchain (OTS anchor) | nobody / everybody | attest the bytes existed by date D | the timestamp leg; immune to any single-party compromise |

The point of the table: a compromise of the **publisher machine or the host** lets an attacker take subtract.ing offline or post garbage, but cannot manufacture a file that verifies as yours. Only loss of `subtract-author.key` breaks the claim — so that key is the thing under the strictest boundary, on the machine that never runs a deploy command.

## 5. Which machine pushes, which doesn't

- **Signer machine** (laptop w/ YubiKey or air-gapped): generates the keypair, writes & signs the file, runs `ots stamp`. **Does not** hold hosting credentials, **does not** push.
- **Publisher machine**: receives only `*.txt`, `*.minisig`, `*.ots`. Runs `rsync` / `netlify deploy` / `git push`. **Never** sees `subtract-author.key`.
- **Host (subtract.ing web server / CDN)**: serves the four files over HTTPS. Holds no signing key; a full compromise is *detectable* by any verifier, which is the design intent.

## 6. How a stranger verifies, a year later

```
# 1. Fetch artifacts
curl -O https://subtract.ing/notes/2026-05-10.txt
curl -O https://subtract.ing/notes/2026-05-10.txt.minisig
curl -O https://subtract.ing/notes/2026-05-10.txt.ots

# 2. Get the public key from channels NOT controlled by whoever serves subtract.ing today,
#    and check they agree:
dig +short TXT subtract-author._minisign.subtract.ing
curl https://gist.githubusercontent.com/<handle>/<id>/raw/subtract-author.pub
#    (and/or the Keyoxide page; and/or the 2026 Wayback snapshots of the above)
#    -> confirm the same key line / fingerprint appears in at least two independent ones.

# 3. Verify the signature
minisign -Vm 2026-05-10.txt -P "<pubkey line>"
#    -> "Signature and comment signature verified"
#    -> read the trusted comment it prints: author + 2026-05-10T00:00:00Z

# 4. Verify the independent timestamp
pip install opentimestamps-client
ots verify 2026-05-10.txt.ots
#    -> "Success! Bitcoin block <N> attests existence as of 2026-05-1x"
#    (needs a Bitcoin node or uses public block explorers; either way no trust in subtract.ing)
```

Conclusion the verifier can soundly draw: *these exact bytes were signed by the holder of key RWQ..., and that key was publicly bound to this author identity in May 2026 (per multiple archived channels), and the bytes provably existed by May 2026 (per Bitcoin).* None of that depends on who owns subtract.ing or its server at verification time.

## 7. Why it still holds in a year

- subtract.ing lapses / changes hands → verifier pulls the file from the Wayback Machine; signature + OTS still check out.
- Host compromised, file swapped → `minisign -V` fails; tamper detected.
- Your GitHub deleted → DNS TXT and/or Keyoxide and/or Wayback snapshot still carry the pubkey.
- OpenTimestamps calendar servers gone → the `.ots` already contains the Bitcoin Merkle path; only a Bitcoin block explorer is needed.
- Only unrecoverable failure: `subtract-author.key` leaks or is lost — which is exactly why it lives only on the non-pushing signer machine and is backed up offline.

(Optional hardening: also commit the file to a Git repo and `git commit -S` with `gpg.format ssh` so GitHub's records are a third date anchor; publish a `SHA256SUMS` file alongside; rotate to a new note key per year and cross-sign old→new.)
