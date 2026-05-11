## Goal, decomposed

"Verifiable authorship a year from now" is really three separate claims, each needing its own mechanism:

1. **Integrity** — "these exact bytes" → SHA-256.
2. **Authorship** — "the holder of key K produced these bytes" → detached cryptographic signature.
3. **Identity binding** — "key K is the person/entity behind subtract.ing" → key published over the domain (WKD / DNS / HTTPS), pinned out-of-band.
4. **Anti-backdating** — "this existed no later than T" → a trustless timestamp (OpenTimestamps on Bitcoin) and/or an RFC 3161 token.

A year from now, none of the verification should depend on trusting your word, a single still-running server, or the website still existing.

## Machines and authority boundaries

| Role | Machine | Holds | Touches network? | Pushes to subtract.ing? |
|---|---|---|---|---|
| **Signing host (A)** | air-gapped laptop / offline VM | the secret signing key (`ed25519`) | no | **no** |
| **Publishing host (B)** | normal workstation | git remote push rights, no secret key | yes | yes (`git push`) |
| **Deploy runner (C)** | CI (GitHub Actions / Netlify) | the deploy token / DNS for `*.subtract.ing` | yes | it *is* the deploy |
| **Registrar account** | browser session, anywhere | DNS control for `subtract.ing` (the `.ing` gTLD zone) | yes | used once, for key binding |

Boundary rules:
- The **authorship key never leaves A** and A never has deploy creds. If the key lived on B or C, anyone who pops the deploy box or steals the CI token can forge authorship — that defeats the whole exercise.
- B/C can publish, deface, or delete the site but **cannot forge a signature**.
- The registrar account is its own trust root (it can swap the published key), so the fingerprint also gets pinned somewhere the registrar doesn't control (git history on GitHub, keys.openpgp.org with verified email, inside the file itself).
- Transfer A→B is **USB only**, one direction in practice (the three output files out).

## One-time setup

On **Machine A** (offline):

```bash
# Option 1: minisign (small, no web-of-trust baggage)
minisign -G -p subtract.pub -s subtract.key
# Option 2: GnuPG
gpg --quick-generate-key 'subtract.ing <hello@subtract.ing>' ed25519 sign 2y
gpg --fingerprint hello@subtract.ing
gpg --armor --export hello@subtract.ing > subtract.pub.asc
gpg --armor --export-secret-keys hello@subtract.ing > /media/usb-encrypted/secret.asc   # backup
```

Back the secret key up to offline media (encrypted USB + a paper/metal copy of the key or its mnemonic). Write down the **fingerprint**; you'll publish it in several places.

Identity binding — done from a networked machine (B or the registrar browser), publishing the *public* half only:
- Serve it at a stable URL: `https://subtract.ing/pubkey.asc` (and ideally WKD: `https://subtract.ing/.well-known/openpgpkey/subtract.ing/hu/<wkd-hash>`).
- DNS TXT record in the `subtract.ing` zone, e.g. `_pubkey.subtract.ing. TXT "openpgp4fpr:ABCD…1234"`.
- `gpg --keyserver keys.openpgp.org --send-keys <FPR>` and complete the email-verification loop.
- Commit `pubkey.asc` to the site repo so it's in GitHub's history with timestamps.

## Publishing a post

On **Machine A** (offline):

```bash
# 1. author
$EDITOR 2026-05-10-hello.txt          # consider putting the key fingerprint in the file footer
sha256sum 2026-05-10-hello.txt        # note this hash

# 2. sign (detached, armored)
minisign -S -s subtract.key -m 2026-05-10-hello.txt -t "subtract.ing 2026-05-10"
#   -> 2026-05-10-hello.txt.minisig
# or:  gpg --armor --detach-sign --local-user <FPR> 2026-05-10-hello.txt
#   -> 2026-05-10-hello.txt.asc

# 3. timestamp (trustless; will need an `ots upgrade` later once the BTC block confirms)
ots stamp 2026-05-10-hello.txt
#   -> 2026-05-10-hello.txt.ots
```

(Optional, belt-and-suspenders, run from B since it needs the network — an RFC 3161 token from an independent TSA:)

```bash
openssl ts -query -data 2026-05-10-hello.txt -sha256 -cert -out post.tsq
curl -H 'Content-Type: application/timestamp-query' --data-binary @post.tsq \
     https://freetsa.org/tsr > 2026-05-10-hello.txt.tsr
```

Move `2026-05-10-hello.txt`, its `.minisig`/`.asc`, and `.ots` (and `.tsr`) to **Machine B** via USB. The secret key stays on A.

On **Machine B** (networked, has push rights, no secret key):

```bash
git switch -c post/2026-05-10-hello
cp /media/usb/2026-05-10-hello.txt*  posts/
git add posts/2026-05-10-hello.txt posts/2026-05-10-hello.txt.minisig posts/2026-05-10-hello.txt.ots
git commit -m "post: 2026-05-10 hello"        # optionally -S with a *separate* commit-signing key on B
git push origin post/2026-05-10-hello
# merge -> CI (Machine C) deploys to subtract.ing
```

Confirm it's live and unmangled:

```bash
curl -fsSL https://subtract.ing/posts/2026-05-10-hello.txt | sha256sum   # == the hash from step 1
```

A few hours/days later (anyone, anywhere — needs network, not the key):

```bash
ots upgrade 2026-05-10-hello.txt.ots          # folds in the confirmed Bitcoin block
```

then commit the upgraded `.ots` back. Now the timestamp is self-contained.

## How a stranger verifies, a year from now

```bash
# 1. fetch artifacts
curl -O https://subtract.ing/posts/2026-05-10-hello.txt
curl -O https://subtract.ing/posts/2026-05-10-hello.txt.minisig   # or .asc
curl -O https://subtract.ing/posts/2026-05-10-hello.txt.ots

# 2. obtain the claimed public key the canonical way, and cross-check it
curl -O https://subtract.ing/pubkey.asc
dig +short TXT _pubkey.subtract.ing                 # fingerprint must match pubkey.asc
gpg --locate-keys hello@subtract.ing                # WKD path, must match
#   also: keys.openpgp.org lookup; the fingerprint in the file footer; git history of pubkey.asc

# 3. authorship: signature over exactly these bytes by key K
minisign -V -p subtract.pub -m 2026-05-10-hello.txt
#   or: gpg --verify 2026-05-10-hello.txt.asc 2026-05-10-hello.txt   -> "Good signature ... <FPR>"

# 4. anti-backdating: bytes existed before block N's time
ots verify 2026-05-10-hello.txt.ots                 # uses a Bitcoin node or public calendar/explorer
#   (and/or)  openssl ts -verify -data 2026-05-10-hello.txt -in 2026-05-10-hello.txt.tsr -CAfile freetsa-cacert.pem
```

The stranger's conclusion: key **K**, which the `subtract.ing` zone + WKD + keyserver all attest belongs to whoever runs that domain, signed *these exact bytes*, and an independent chain/TSA shows those bytes existed by mid-May 2026. Every step is checkable with public tooling; none requires the website still being up (the `.ots`/`.tsr` make the timestamp portable), the author's cooperation, or trusting a single server still alive a year on.

## Things that bite you in a year — handle now

- **Key expiry:** set it ≥ 2 years (or be ready to extend before it lapses). An expired key still verifies a historical signature *if* the verifier has the timestamp proving the sig predates expiry — but don't rely on that; just don't let it expire inside the verification horizon. Never `--gen-revoke`/publish a revocation unless the key is actually compromised.
- **Registrar/DNS hijack** would let an attacker replace the published key. Mitigation: the fingerprint is also pinned in GitHub commit history, keys.openpgp.org (email-verified), and the file's own footer — a verifier who checks more than one of these survives a single compromised root.
- **HTTPS cert / host churn:** fine — the durable proof is the signature + `.ots`, not "still reachable at this URL." Keep the three files together (repo, releases, IPFS, wherever).
- **`ots upgrade` must actually be run** after the Bitcoin confirmation, or the timestamp is still "pending" and weaker. Do it and re-commit.
- **Don't sign on the deploy box.** If you ever find the secret key on B or C, rotate it: generate a fresh key on A, re-publish the binding, and from then on the old key only vouches for posts whose timestamps predate the exposure.
