## Goal, restated precisely

A file at `https://subtract.ing/<name>.txt` such that in May 2027 a stranger can independently confirm: (a) it was authored by the holder of a specific key, and (b) it existed on or before May 2026 — **without trusting me, without trusting subtract.ing's server, and without any single host needing to still be online.**

## Authority model — three trust domains, three machines, data flows one direction

| Machine / account | Holds | Does | Must NOT have |
|---|---|---|---|
| **(1) Signing machine** — laptop, ideally an offline box | the *secret* signing key (`subtract.key`) | authors the .txt, signs it | web-host SSH key, deploy token, DNS login |
| **(2) Publishing machine** — workstation or CI runner | web-host / git-remote credentials | receives already-signed files, pushes them | the secret signing key (so it physically cannot forge) |
| **(3) Registrar/DNS account** — browser + 2FA | zone control | publishes the pubkey fingerprint in a DNSSEC-signed TXT record once | nothing to do with signing or pushing |

Why the split: a compromised web server can replace the file but can't produce a valid signature; a stolen deploy token can deface the site but can't impersonate the author; forging authorship requires the offline key, which never leaves machine 1. **Machine 2 is the only one that runs a command against the live site.** Artifacts only ever move 1 → 2, never back.

## Step 1 — author + sign (machine 1, offline)

- Write `manifesto.txt`.
- Key (reuse existing, or generate): `minisign -G -p subtract.pub -s subtract.key`
  - Alternative toolchain: `ssh-keygen -t ed25519 -f subtract_sign` and sign in the SSH signature namespace (`ssh-keygen -Y sign -f subtract_sign -n file manifesto.txt`). GPG (`gpg --armor --detach-sign`) also works but is the heaviest option.
- Sign: `minisign -S -m manifesto.txt -s subtract.key -t "subtract.ing/manifesto.txt v1, authored 2026-05-10"` → produces `manifesto.txt.minisig`.
- Note the public-key string `RWS...` and keep it; it goes into DNS in step 3.

## Step 2 — independent timestamp (hash only, so any machine; do it on 1)

- `pip install opentimestamps-client`
- `ots stamp manifesto.txt` → `manifesto.txt.ots` (submits SHA-256 of the file to calendar servers that aggregate into a Bitcoin transaction).
- A few hours later: `ots upgrade manifesto.txt.ots` to bake in the confirmed block header.
- Redundant independent anchors (cheap, do all):
  - `git commit -S manifesto.txt` into a repo you `git push` to a public GitHub mirror — the signed commit + GitHub's timestamp is a second anchor.
  - After step 4 goes live: `curl -s "https://web.archive.org/save/https://subtract.ing/manifesto.txt"` — a third-party copy with its own timestamp.

## Step 3 — publish key provenance (DNS account, machine 3)

- Add, on a **DNSSEC-enabled** zone: `_minisign.subtract.ing.  TXT  "minisign-pubkey=RWS..."`
- Also mirror it at `https://subtract.ing/.well-known/minisign.pub` and in a GitHub gist/profile for redundancy — but the DNSSEC TXT record is the one that lets a stranger root the key in something other than "a file on the same server that served the .txt".

## Step 4 — push (machine 2 only)

- Move `manifesto.txt`, `manifesto.txt.minisig`, `manifesto.txt.ots`, `minisign.pub` from machine 1 to machine 2 (USB, or `scp` *into* machine 2 — the secret key does not travel).
- Deploy with whatever subtract.ing actually uses, e.g. one of:
  - `rsync -av ./public/ deploy@subtract.ing:/var/www/subtract.ing/`
  - `git push pages main` (GitHub/GitLab Pages)
  - `npx wrangler pages deploy ./public` (Cloudflare Pages)
- Confirm fetchability over TLS: `curl -fsSIL https://subtract.ing/manifesto.txt` and likewise for `.minisig`, `.ots`, and `/.well-known/minisign.pub`.

## Step 5 — how a stranger verifies in May 2027 (public info only)

1. Fetch artifacts: `curl -O https://subtract.ing/manifesto.txt{,.minisig,.ots}`
2. Get the pubkey *independently of the web server*: `dig +dnssec TXT _minisign.subtract.ing` and check the `ad` flag / validate the chain (`delv TXT _minisign.subtract.ing` for an explicit "fully validated"). This is the step that makes authorship checkable by a stranger.
3. Verify authorship: `minisign -V -m manifesto.txt -P "RWS...<from DNS>"` → must print *"Signature and comment signature verified"*. (SSH-sig equivalent: `ssh-keygen -Y verify -I subtract.ing -n file -f allowed_signers -s manifesto.txt.minisig < manifesto.txt`.)
4. Verify it isn't backdated: `ots verify manifesto.txt.ots` → reports the Bitcoin block (and its date) attesting the file's hash existed by 2026-05-10. Cross-check `git log --show-signature` on the GitHub mirror and the Wayback capture date.
5. Conclusion the verifier can stand behind: *the holder of key `RWS…`, which subtract.ing's DNSSEC-signed zone vouches for, signed exactly this text, and it provably existed no later than May 2026.*

## Failure modes worth stating up front

- **Site goes dark:** the `.ots` proof, the signed Git commit on GitHub, and the Wayback copy each stand alone — verification doesn't depend on subtract.ing surviving.
- **Key later leaks:** publish a revocation in the same TXT record; the OpenTimestamps proof pins *when* the signature was made, so a future leak doesn't retroactively void the 2026 claim.
- **Anti-pattern that breaks everything:** signing on the publishing machine, or storing `subtract.key` in the repo / CI secrets — that merges domains 1 and 2 and a server compromise becomes an authorship forgery. Keep the secret key on machine 1 only.
