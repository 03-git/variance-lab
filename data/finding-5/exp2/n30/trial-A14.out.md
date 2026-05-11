# Plan: publish a verifiable `.txt` to subtract.ing

Not executed — plan only. Tool/command names are exact.

## 0. Ground truth (before anything)
- `bash ~/scripts/audit-health.sh` — read DNS, drives, credential state. Don't assume.
- On the canonical working tree (Rousseau, `~/subtract.ing/`): `git log --oneline -5`, `git status`, `ls -la` the target dir. State timestamps/line counts before touching anything (reflex.4 — verify with a live read, not memory).
- Verify the *current* manifest signature still passes: `ssh-keygen -Y verify -f allowed_signers -I <principal> -n file -s MANIFEST.sig < MANIFEST`. If it fails or there's unsigned drift, surface that and stop (loop.before.1–3).

## 1. Draft (Rousseau — agent prepares)
- Rousseau is canonical for formation human-authored work; write the new file there: `~/subtract.ing/<path>/newfile.txt`.
- This is the agent's job: content, formatting, and computing the hash. Nothing here is load-bearing yet.

## 2. Stage the manifest entry (Rousseau — agent prepares)
- `sha256sum newfile.txt` → append the line to the repo `MANIFEST` (or `SHA256SUMS`).
- Confirm `allowed_signers` already contains the governor's signing principal → pubkey mapping. If a stranger can't get the pubkey from the signing domain, the rest is theater — this file ships alongside the artifact.

## 3. Sign — THE HUMAN GATE (governor, not the agent)
- Only new signing is a human gate (the agent never holds or invokes the signing key). The governor runs, on the machine holding the private key:
  - `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file newfile.txt` → `newfile.txt.sig`
  - `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file MANIFEST` → `MANIFEST.sig`
- Namespace is `file` on both sign and verify — must match or verification fails.
- loop.before.3: governor decides — sign, continue, or abort. Agent waits.

## 4. Publish to the canonical origin (Surface executes)
- Authority boundary: pushing *already-signed* artifacts is infra, not a gate — but per formation discipline Rousseau drafts and hands off; **Surface** (governor terminal) runs the deploy to the subtract.ing web origin. Rousseau does not push to the public origin itself; Emile is for heavy compute (not this); **Media/acer is mirror-only backup tier and never publishes canonical**.
- Deploy bundle: `newfile.txt`, `newfile.txt.sig`, updated `MANIFEST` + `MANIFEST.sig`, `allowed_signers`.
- reflex.5: the web origin under the signing key's domain (`https://subtract.ing/...`) is canonical. A `git push` to GitHub or any git host is a **mirror only** — fine to do for redundancy, but it is not the authoritative copy and the verifier should not be pointed there.
- loop.after: manifest updated and signed — done in steps 2–3, confirm it landed.

## 5. How a stranger verifies, one year out
From the canonical domain only (not a git mirror):
```
curl -O https://subtract.ing/<path>/newfile.txt
curl -O https://subtract.ing/<path>/newfile.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <principal> -n file -s newfile.txt.sig < newfile.txt
```
- `Good "file" signature for <principal>` → authorship confirmed.
- Optional integrity cross-check: fetch `MANIFEST` + `MANIFEST.sig`, `ssh-keygen -Y verify ... -n file -s MANIFEST.sig < MANIFEST`, then `sha256sum -c MANIFEST` to confirm `newfile.txt`'s hash is the one the governor signed into the manifest.
- Trust anchor: the verifier trusts the pubkey because `allowed_signers` is served from the signing key's own domain (reflex.5), ideally corroborated out-of-band (DNS TXT / a second self-hosted location). GitHub having the same key proves nothing on its own — mirror, not authority.

## Authority boundaries, summarized
- **Agent (Claude/Rousseau):** draft content, compute hashes, stage `MANIFEST`, verify existing signatures, prepare the deploy bundle. Never touches the private key.
- **Human (governor):** the only gate — runs `ssh-keygen -Y sign`. The signature is what proves authorship; the agent prepares, the human signs.
- **Surface:** executes the publish to the canonical origin.
- **Rousseau:** canonical drafting/source tree; does not push the public origin.
- **Emile:** not involved (no heavy compute here).
- **Media/acer:** warm-backup mirror only — never canonical, never publishes.
- **Git hosts:** mirror-only, never cited to the verifier as authoritative.
