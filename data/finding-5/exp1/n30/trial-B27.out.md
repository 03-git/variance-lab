# Plan: publish a verifiably-authored `.txt` to subtract.ing

## Trust model first (what "authorship" actually means here)

"Authorship verifiable by a stranger" = the stranger can check that the bytes of the file were signed by a private key that is *publicly and durably bound to your identity*, and that the signature is not backdated. So the plan has three independent pieces: a **signature over the file**, **durable publication of the matching public key through paths the website host doesn't control**, and a **timestamp anchor**. The website itself is treated as untrusted for authorship — it only ships bytes.

## Tools

- `ssh-keygen -Y sign` / `-Y verify` — detached SSH signatures (Ed25519). Chosen because the public key is *independently* re-discoverable at `https://github.com/<user>.keys` and inside your signed git commits, not only on subtract.ing. (`minisign`/`signify` is a fine alternative but its key has fewer independent anchors.)
- A hardware key (YubiKey etc.) holding an `sk-ssh-ed25519` resident key — so the signing key cannot be exfiltrated from the workstation, CI, or the server.
- `git` + the static host for subtract.ing (assume GitHub Pages or Cloudflare Pages from a git repo).
- `ots` (OpenTimestamps client) — Bitcoin-anchored timestamp proving the signature existed by a certain date.
- `dig`, `curl`, `openssl dgst -sha256` — anchoring and self-check.
- `web.archive.org/save/` — third-party snapshots of the file and the key sources.

## Authority boundaries

| Secret / capability | Lives on | Never on | If compromised |
|---|---|---|---|
| Signing key (`sk-ssh-ed25519`, resident on hardware token) | Your workstation only, touch-to-sign | CI, the web host, any server, any backup | Authorship forgeable — this is the one that matters; hence hardware-backed |
| Repo-scoped deploy key / push token for subtract.ing's repo | Your workstation (optionally a CI deploy job) | — | Attacker can change/replace bytes, **cannot** produce a valid signature; verifiers get "bad signature" |
| TLS cert / CA for subtract.ing, DNS provider creds | the host / registrar | — | Not in the authorship trust path at all; DNS is only *one* of several key anchors |

Key rule: **signing authority is local and offline-ish; push authority is local; the server and CI have neither the signing key.** If CI builds the site, it only deploys an artifact that was *already signed on the workstation* — no "bot signs on deploy."

## One-time setup

1. Generate the signing key:
   `ssh-keygen -t ed25519-sk -O resident -O application=ssh:subtract.ing -C "author@subtract.ing" -f ~/.ssh/id_subtract`
2. Publish the public key (`~/.ssh/id_subtract.pub`) through ≥3 independent channels:
   - commit an `allowed_signers` file to the site repo: `author@subtract.ing namespaces="file" ssh-ed25519 AAAA... ` and serve it at `https://subtract.ing/allowed_signers`;
   - add it as an account SSH key so it appears at `https://github.com/<you>.keys`;
   - `dig`-able DNS TXT record, e.g. `_authorship.subtract.ing TXT "ssh-ed25519 AAAA... author@subtract.ing"`.
3. Enable signed git commits with the same key: `git config gpg.format ssh; git config user.signingkey ~/.ssh/id_subtract.pub; git config commit.gpgsign true`.

## Publishing the file (all on the workstation)

1. Write `article.txt`.
2. Sign it: `ssh-keygen -Y sign -f ~/.ssh/id_subtract -n file article.txt` → `article.txt.sig` (touch the token).
3. Timestamp the signature: `ots stamp article.txt.sig` → `article.txt.sig.ots`. (Run `ots upgrade article.txt.sig.ots` a day later once it's confirmed in a Bitcoin block.)
4. Optional content hash for humans: `openssl dgst -sha256 article.txt`.
5. Commit and push **from the workstation only**:
   - `git add article.txt article.txt.sig article.txt.sig.ots allowed_signers`
   - `git commit -S -m "Publish article.txt"`
   - `git push origin main` — using the repo-scoped deploy key. This workstation is the only machine that pushes. The web host builds and serves; **the host pushes nothing**.
6. After it's live, snapshot for durability: submit `https://subtract.ing/article.txt`, `https://subtract.ing/article.txt.sig`, `https://subtract.ing/allowed_signers`, and `https://github.com/<you>.keys` to `https://web.archive.org/save/`. The public git history (with the signed commit) is itself a durable anchor.
7. Self-verify from a clean machine using the steps below before considering it done.

## How a stranger verifies it, a year later

1. Fetch the artifacts:
   `curl -fO https://subtract.ing/article.txt` and `curl -fO https://subtract.ing/article.txt.sig`
2. Get the claimed author's public key **without trusting subtract.ing** — at least two of: `curl https://github.com/<you>.keys`, `dig +short TXT _authorship.subtract.ing`, the `allowed_signers` blob in the repo's history, or the archive.org snapshots. Confirm they're the same key.
3. Build a local `allowed_signers` line from that key:
   `printf 'author@subtract.ing namespaces="file" %s\n' "$(curl -s https://github.com/<you>.keys | grep ed25519)" > allowed_signers`
4. Verify the signature:
   `ssh-keygen -Y verify -f allowed_signers -I author@subtract.ing -n file -s article.txt.sig < article.txt`
   → expect `Good "file" signature for author@subtract.ing`.
5. Check it isn't backdated: `ots verify article.txt.sig.ots` → reports the Bitcoin block time; confirms the signature existed at/before that date (≈ publication).
6. Cross-check the git commit: `git clone … && git log --show-signature -- article.txt` → same key signed the commit around the same date.
7. What the verifier can then assert: *the bytes of `article.txt` were signed by the holder of key `SHA256:…`; that key is publicly bound to `<identity>` via `github.com/<you>.keys` and DNS and was so bound a year ago (archive.org); OpenTimestamps shows the signature predates `<date>`.* The claim holds unless that private key was compromised — which is why it's on a hardware token and never touched CI or the server.

## Failure modes this resists

- Web host / CDN compromise: attacker can swap `article.txt`, but `ssh-keygen -Y verify` then fails — tamper is detectable, not deniable.
- Stolen deploy key: same — bytes change, signature breaks.
- DNS hijack: only one of several key anchors; the others (github.com keys, signed commits, archive snapshots) disagree.
- Backdating: blocked by the OTS Bitcoin anchor.
- Not resisted: theft of the signing key itself (hence hardware-backed, touch-required) — and note this proves *key control*, not legal authorship.
