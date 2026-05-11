# Plan: publish a verifiable-authorship `.txt` on subtract.ing

## Goal decomposed
Three independent facts a stranger must be able to check in May 2027:
1. **Integrity** — the bytes they download from subtract.ing are the bytes you signed.
2. **Identity** — the signing key belongs to whoever controls `subtract.ing` (that domain *is* the authorship claim).
3. **Anteriority** — the file existed at the claimed date and isn't a recent backdate.

This needs a signature (1), a key-to-domain binding via channels only the domain owner controls (2), and a trustless timestamp (3).

## Tools
- `minisign` (OpenBSD `signify`-style; single small pubkey string) — primary signer. GPG (`gpg`, Ed25519) is the alternative if you want WKD-based identity binding.
- `opentimestamps-client` (`ots`) — Bitcoin-anchored timestamp. Optionally `openssl ts` against a free RFC-3161 TSA (freeTSA) as a secondary.
- `sha256sum` / `shasum -a 256` — manifest.
- `rsync` + `ssh`, *or* the host's deploy CLI (`wrangler pages deploy`, `netlify deploy`, or `git push` to a Pages repo) — whichever fronts subtract.ing.
- `dig` / `curl` — used by the verifier, and by you to publish the DNS record via your registrar's API or web console.

## Machines and authority boundaries
- **Machine A — "signer".** Holds the minisign/GPG **secret key** (ideally on a YubiKey via `gpg --card-edit` or `age-plugin-yubikey`, or at least an offline-ish laptop). Has **no** credentials to subtract.ing's host and **no** DNS credentials. The secret key never leaves this machine.
- **Machine B — "publisher".** Holds the **deploy credential** (server SSH key, or Cloudflare/Netlify token, or GitHub Pages deploy key). Never sees the signing secret. If B is fully compromised, an attacker can serve a *different* file but cannot produce a valid signature — the verifier catches the mismatch.
- **DNS/registrar account** — a third boundary, used once, ideally from a different session with its own 2FA. Publishes the key fingerprint at the domain.
- **Data flow:** A → B carries only *public* artifacts (`.txt`, `.minisig`, `.ots`, `SHA256SUMS`) via USB or `scp A→B`. Nothing flows B → A. **Machine B is the only machine that pushes to the internet-facing host.** Machine A's only outbound act is publishing the *public* key to a keyserver, which is harmless.

## Steps (do not execute — plan)

### One-time, on Machine A: key setup
- `minisign -G -p subtracting.pub -s subtracting.sec` — generate the long-lived key.
  - (GPG variant: `gpg --quick-generate-key "subtract.ing <author@subtract.ing>" ed25519 sign 3y`.)
- Back up `subtracting.sec` (and its password) offline: two USB sticks + a paper copy, stored separately. Set expiry > 1 year or none.

### Authoring + signing, on Machine A
1. Create the file, e.g. `article.txt`. Freeze the bytes.
2. `sha256sum article.txt > SHA256SUMS`
3. `minisign -Sm article.txt -s subtracting.sec -c "subtract.ing article" -t "subtract.ing 2026-05-10 author=<your name/handle>; pubkey RWxxxxxxxx"`
   - produces `article.txt.minisig`; the **trusted comment** is itself signed, so the date/author string can't be edited.
   - (GPG variant: `gpg --armor --detach-sign -o article.txt.asc article.txt`.)
4. Timestamp: `ots stamp article.txt` → `article.txt.ots`. (Optionally also `openssl ts -query -data article.txt -sha256 -cert -out a.tsq` → POST to `https://freetsa.org/tsr` → `article.txt.tsr`.)
5. A few hours/days later, when the OTS calendar has the Bitcoin attestation: `ots upgrade article.txt.ots` so the `.ots` is self-contained.

### Transfer A → B
- Copy `article.txt`, `article.txt.minisig` (or `.asc`), `article.txt.ots`, `SHA256SUMS` to Machine B via USB or `scp ./out/* deploy@hostB:~/stage/`. The secret key does **not** move.

### Publish, on Machine B
- Lay out a directory and deploy with whatever fronts subtract.ing, e.g.:
  - `rsync -avz --checksum ./public/ deploy@subtract.ing:/var/www/subtract.ing/`, or
  - `wrangler pages deploy ./public`, or
  - `git add . && git commit -m "publish article.txt + sig" && git push` to the Pages repo.
- Result URLs: `https://subtract.ing/article.txt`, `…/article.txt.minisig`, `…/article.txt.ots`, `…/SHA256SUMS`.
- Also place the pubkey at `https://subtract.ing/.well-known/minisign.pub` (and, for the GPG variant, set up WKD so `gpg --locate-keys author@subtract.ing` works).

### Bind the key to the domain (the part that makes it *authorship*, not just *a signature*)
- Add a DNS TXT record on `subtract.ing` via the registrar: `subtract.ing. IN TXT "minisign-pubkey=RWxxxxxxxx"` (GPG: an `OPENPGPKEY` record / WKD). Only the domain controller can do this — that's the link.
- Cross-anchor the fingerprint where it gets archived: post the pubkey string + date in a signed git tag (`git tag -s`), a social post, and submit the page to `https://web.archive.org/save/`. This is your fallback if the domain ever lapses.
- (Optional, on Machine A) `gpg --send-keys <fpr>` to `keys.openpgp.org`, and/or set up a Keyoxide/Ariadne identity claim.

## How a stranger verifies in May 2027
1. Download: `curl -O https://subtract.ing/article.txt`, `curl -O https://subtract.ing/article.txt.minisig`, `curl -O https://subtract.ing/article.txt.ots`.
2. Get the claimed key *independently of the file*: `dig +short TXT subtract.ing` (or `curl https://subtract.ing/.well-known/minisign.pub`, or `gpg --locate-keys author@subtract.ing`). Compare that fingerprint against the year-old archived copy (`web.archive.org`) and the signed git tag — confirms the domain owner committed to this key back then, not retroactively.
3. Check integrity + authorship: `minisign -Vm article.txt -p subtracting.pub` → `Signature and comment signature verified` / `Trusted comment: subtract.ing 2026-05-10 author=…`. (GPG: `gpg --verify article.txt.asc article.txt`.) Optionally `sha256sum -c SHA256SUMS`.
4. Check anteriority: `ots verify article.txt.ots` → reports the Bitcoin block height/time attesting the hash existed by ~2026-05-10 (needs a Bitcoin node or uses a block explorer). Defeats backdating. (RFC-3161 fallback: `openssl ts -verify -data article.txt -in article.txt.tsr -CAfile freetsa_cacert.pem`.)
5. Conclusion the verifier can defend: *the bytes served by subtract.ing carry a valid signature from a key that the controller of subtract.ing published via DNS and `.well-known` (corroborated by an independent year-old archive), and the content provably existed at the stated date* — i.e. the party controlling subtract.ing authored it, and it's not a fresh forgery.

## Failure modes this survives, and the one weak link
- Machine B compromised → forged file fails `minisign -V`. ✔
- Backdating attempt → fails `ots verify`. ✔
- Keyserver lies / Keyoxide down → DNS + `.well-known` + archived git tag still bind the key. ✔
- **Weak link: the domain.** Authorship-by-domain evaporates if `subtract.ing` lapses or changes hands. Mitigations: long registration + auto-renew, and the cross-posted signed statement (git tag + archive.org) that ties *your* name to the fingerprint independently of the domain. Keep `subtracting.sec` backed up offline so you can re-sign/rotate if needed.
