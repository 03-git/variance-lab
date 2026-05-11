# Plan: publish a verifiable‑authorship `.txt` to subtract.ing

Assumptions: `subtract.ing` is a static site you control (Git repo → CI/host such as GitHub Pages/Netlify, or a VPS with nginx). You have one trusted personal machine ("laptop"). Nothing below is executed; it's the procedure.

## 0. What "verifiable by a stranger in a year" requires
A future stranger must be able to, without trusting you: (a) fetch the file, (b) fetch a detached signature, (c) obtain your public key via a channel independently bound to your identity, (d) verify the signature, (e) confirm the file's hash existed at/around the claimed date. So: a non‑expiring signature, a multi‑channel published pubkey, and an independent timestamp.

## 1. One‑time key setup — laptop only
- Generate an Ed25519 keypair with **minisign**:
  `minisign -G -p ~/keys/subtract.ing.pub -s ~/keys/subtract.ing.key` (set a passphrase).
- Back the secret key up offline (encrypted USB / paper). It never leaves the laptop.
- Publish the **public** key through ≥2 identity‑bound channels:
  - In the site repo, served at `https://subtract.ing/.well-known/minisign.pub`
  - DNS TXT record at the registrar: `_minisign.subtract.ing` containing the `RW...` line (verify later with `dig +short TXT _minisign.subtract.ing`)
  - Optional third: post the key fingerprint from another account you own, or in a signed git tag.
- (Alternative tool, if you prefer SSH keys: `ssh-keygen -Y sign` / `ssh-keygen -Y verify` with an `allowed_signers` file published at `https://subtract.ing/.well-known/allowed_signers`. Pick one scheme and stick to it.)

**Authority boundary:** the secret key exists only on the laptop. Not in the repo, not in CI secrets, not on the web server.

## 2. Author the file — laptop
- Write `essays/2026-05-10-<slug>.txt`. Put a self‑describing header inside it: title, author name, date `2026-05-10`, and "signed with minisign key RW…<fingerprint>".

## 3. Sign — laptop
- `minisign -Sm essays/2026-05-10-<slug>.txt -s ~/keys/subtract.ing.key -t "subtract.ing essay; author: <name>; date: 2026-05-10"`
  → produces `essays/2026-05-10-<slug>.txt.minisig` (the trusted comment is itself signed).
- Self‑check: `minisign -Vm essays/2026-05-10-<slug>.txt -p ~/keys/subtract.ing.pub`
- Record the digest: `shasum -a 256 essays/2026-05-10-<slug>.txt`

## 4. Timestamp — laptop
- `pip install opentimestamps-client`
- `ots stamp essays/2026-05-10-<slug>.txt` → `…txt.ots` (anchors the hash into Bitcoin).
- A few hours/days later: `ots upgrade essays/2026-05-10-<slug>.txt.ots` to embed the block proof. Commit the upgraded `.ots`.

## 5. Push / publish — laptop pushes, nothing else does
- In the site repo on the laptop: `git add` the `.txt`, `.minisig`, `.ots`; commit with a signed commit: `git -c commit.gpgsign=true commit -S -m "essay 2026-05-10; sha256 …"`; `git push origin main`.
- CI/host (GitHub Pages, Netlify, or `rsync -av public/ deploy@subtract.ing:/var/www/subtract.ing/` run **from the laptop** for a VPS) copies the already‑signed bytes to the web root.

**Authority boundaries:**
- **Laptop** = authorship authority: holds the secret key, makes the signature + timestamp, makes the signed git commit, and is the only machine with push/write to the canonical repo and (if VPS) the only one running the deploy.
- **CI runner / build bot** = distribution only: reads the repo, writes the deployed artifact bucket; has no signing key and does not push back to the content repo (restrict any write‑back to non‑content paths).
- **Web server / CDN** = serves bytes; no write‑back, no key.
- **DNS/registrar account** = separate authority used once from the laptop browser; treat its compromise as a real risk — which is why the pubkey is multi‑channel + archived (next step), not trusted from the live site alone.
- Compromise of CI/host/CDN lets an attacker serve a *different* file, but not produce a valid minisign signature over it or a valid `.ots` proof for it.

## 6. Independent third‑party timestamp
- Once live, snapshot each artifact: `curl "https://web.archive.org/save/https://subtract.ing/essays/2026-05-10-<slug>.txt"` and the same for `…txt.minisig`, `…txt.ots`, and `https://subtract.ing/.well-known/minisign.pub`. Save the returned snapshot URLs. This pins "existed and key was published by May 2026" to an independent party.

## 7. Publish verifier instructions
Add `https://subtract.ing/VERIFY.md` describing exactly what a stranger runs a year later:
1. `curl -O https://subtract.ing/essays/2026-05-10-<slug>.txt`
2. `curl -O https://subtract.ing/essays/2026-05-10-<slug>.txt.minisig`
3. Obtain the pubkey two independent ways and confirm they're identical:
   `curl https://subtract.ing/.well-known/minisign.pub` ; `dig +short TXT _minisign.subtract.ing` ; and the 2026 Wayback snapshot of the pubkey URL (so a *future* site compromise can't swap the key).
4. `minisign -Vm 2026-05-10-<slug>.txt -p minisign.pub` — a valid check prints the signed trusted comment ("author: <name>; date: 2026-05-10").
5. `ots verify 2026-05-10-<slug>.txt.ots` (needs the `.txt`) — reports the Bitcoin block timestamp, proving the file's hash existed by then; cross‑check against the Wayback snapshot date.
6. If the repo is public: `git log --show-signature` on that commit for the additional commit‑signature layer.

## 8. Why it still holds in a year, and failure modes
- Ed25519/minisign signatures don't expire. (If you'd used GPG instead, set no expiry or a long one and keep a revocation certificate.)
- Trust root is "this pubkey appeared at subtract.ing **and** in DNS **and** in a 2026 web.archive.org snapshot" — not the server's current state.
- If the domain lapses or changes hands: the Wayback snapshots + the OpenTimestamps proof + the signed git commit/tag still stand alone.
- minisign has no revocation; for higher assurance either use GPG with a pre‑made revocation cert, or plan to publish a signed "key rotated on <date>" note. Keep the laptop secret key passphrase‑protected and backed up offline so you don't lose the ability to issue that note.
