# Plan: publish `essay.txt` to subtract.ing with year-durable authorship proof

## What "verifiable by a stranger" decomposes into
- **Integrity** — the bytes haven't changed → content hash + detached signature
- **Authenticity** — a key bound to a persistent identity made that signature → public key published through independent, durable channels
- **Timeliness** — it existed ~now → an independent timestamp anchored to something that will still resolve in 2027 (Bitcoin via OpenTimestamps, or a transparency log)
- **Trust boundary** — none of the above may depend on trusting subtract.ing itself; it's just a byte host

## Machines and authority boundaries
1. **Signing machine** — holds the private signing key (ideally on a hardware token / YubiKey; key file never leaves it). Does: hash, sign, timestamp. Has *no* subtract.ing credentials. **Does not push.**
2. **Publishing machine** — holds subtract.ing upload credentials/session. Receives only the finished artifacts over a one-way transfer. Never sees the private key. **This is the one that pushes.**
3. **subtract.ing servers** — untrusted relay. Verification must not require trusting them.
4. **Identity-anchor accounts** (GitHub, your DNS zone, your personal domain) — touched once to publish the *public* key. Compromise of subtract.ing doesn't reach these.

## Tools
`ssh-keygen -Y sign/verify` (SSH signatures — chosen because people already associate your SSH keys with your GitHub) — alt: `minisign` or `gpg --detach-sign`. `shasum -a 256` for the digest. `opentimestamps-client` (`ots stamp/upgrade/verify`) for a Bitcoin-anchored timestamp — alt: `cosign sign-blob` + Rekor, or `openssl ts` against an RFC 3161 TSA. `git` (signed commit + signed tag) as a secondary anchor. `curl` for the upload. `web.archive.org/save` + `archive.today` for snapshot durability.

## Phase 0 — one-time identity setup (signing machine)
1. Dedicated signing key (not your login key — limits blast radius):
   `ssh-keygen -t ed25519 -C "authorship-key-2026" -f ~/.ssh/authorship_ed25519`
   (or hardware-backed: `ssh-keygen -t ed25519-sk -f ~/.ssh/authorship_sk`)
2. Record the fingerprint: `ssh-keygen -lf ~/.ssh/authorship_ed25519.pub`
3. Publish the **public** key through ≥2 independent durable channels: add it to GitHub (served at `https://github.com/<user>.keys`); a `TXT` record in your DNS zone; a note at `https://yourdomain/.well-known/authorship.txt`; optionally Keybase. Keep ≥2 so a lapsed domain doesn't sink the claim.
4. Build the verifier's allow-list line and publish it too:
   `echo "you@example.com namespaces=\"file\" $(cat ~/.ssh/authorship_ed25519.pub)" > allowed_signers`

## Phase 1 — author, sign, timestamp (signing machine, offline is fine)
5. Write `essay.txt`. Freeze it — no further edits.
6. `shasum -a 256 essay.txt | tee essay.txt.sha256`
7. Detached signature: `ssh-keygen -Y sign -f ~/.ssh/authorship_ed25519 -n file essay.txt` → `essay.txt.sig`
   (minisign alt: `minisign -Sm essay.txt` → `essay.txt.minisig`)
8. Timestamp: `ots stamp essay.txt` and `ots stamp essay.txt.sig` → `.ots` files. (Sigstore alt: `cosign sign-blob --bundle essay.txt.bundle essay.txt` — logs hash+time to Rekor.)
9. Secondary anchor (optional): in a public repo, `git add essay.txt essay.txt.sig essay.txt.ots`, `git commit -S -m "publish essay"`, `git tag -s essay-2026-05-10 -m "..."`, `git push` — GitHub records the commit/tag time.

## Phase 2 — cross the authority boundary (one-way)
10. Move **only** `essay.txt`, `essay.txt.sig`, `essay.txt.ots`, `essay.txt.sha256` to the publishing machine via USB or an `scp` *pull* initiated from the publishing side. The private key file does not cross. subtract.ing credentials do not flow back to the signing machine.

## Phase 3 — publish (publishing machine)
11. Upload the artifacts to subtract.ing via its mechanism (e.g. `curl -T essay.txt https://subtract.ing/<path>` plus the `.sig` and `.ots`). If subtract.ing hosts only a lone `.txt`, append the SHA-256 and a URL to the `.sig`/`.ots` inside the file, or paste the SSH-sig block at the end of the text. Note the public URL.
12. Durability snapshot: `curl -s https://web.archive.org/save/https://subtract.ing/<path>` and submit the same URL to archive.today.
13. Next day, back on the signing machine once Bitcoin has confirmed: `ots upgrade essay.txt.ots` (makes the proof self-contained), then re-upload the upgraded `.ots` to subtract.ing.

## Phase 4 — how a stranger verifies in May 2027
1. Fetch `essay.txt`, `essay.txt.sig`, `essay.txt.ots` from the subtract.ing URL.
2. Fetch the claimed public key from an **independent** source — `https://github.com/<user>.keys`, the DNS `TXT` record, the `/.well-known/` file — *not* from subtract.ing; confirm the fingerprint agrees across them.
3. Verify the signature against a locally rebuilt allow-list:
   `ssh-keygen -Y verify -f allowed_signers -I you@example.com -n file -s essay.txt.sig < essay.txt` → `Good signature`
   (minisign: `minisign -Vm essay.txt -P <pubkey>`)
4. Verify the timestamp: `ots verify essay.txt.ots` → reports the Bitcoin block/date showing the content existed by ~May 2026. (Sigstore path: `cosign verify-blob --bundle essay.txt.bundle essay.txt`.)
5. Corroborate (optional): the GitHub signed tag's date, the Wayback snapshot date.
6. Stranger's defensible conclusion: *the bytes of `essay.txt` were signed by key `SHA256:…`; that key has been publicly claimed by `<identity>` via GitHub/DNS/their own domain since before May 2026; an independent timestamp shows the content existed by May 2026; subtract.ing was only a host and did not have to be trusted.*

## Caveats worth stating in the published file
- This proves *the key* signed it and *the key maps to an identity* — not that the human wasn't coerced.
- OpenTimestamps proves "existed no later than" (the useful direction for a priority claim), not "no earlier than."
- If the key is ever compromised, publish a revocation through the same identity channels; a 2027 verifier should check the key wasn't revoked *before* the timestamp.
- Renew the domain. Keep ≥2 key-distribution channels alive so one expiring doesn't break verification.

I won't execute any of this — plan only, as requested.
