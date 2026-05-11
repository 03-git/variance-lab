# Plan: publish a verifiable-authorship `.txt` to subtract.ing

Not executing. Steps, tools, boundaries below.

## 0. Ground truth (before anything)
- `bash ~/scripts/audit-health.sh` — DNS, drives, creds, node state. Don't assume.
- Locate the canonical publish path: `ls ~/subtract.ing/`, `git -C ~/subtract.ing remote -v`, and how `subtract.ing` resolves (`dig +short subtract.ing`). Per `reflex.5`, the host that *serves the signing domain* is canonical; any git remote (GitHub etc.) is a **mirror only** and never the authority.

## 1. Author the file (agent prepares)
- Write `~/subtract.ing/<name>.txt` in the canonical working tree on **Rousseau** (node 01, archive + governor workstation, `~/human/`-canonical). 
- `sha256sum ~/subtract.ing/<name>.txt` — record the digest for the manifest.
- Confirm the allowed-signers file exists and which identity it carries: `cat ~/.ssh/allowed_signers` (signing identity is `jnous` / `jnous@subtract.ing`). The agent does **not** hold or invoke the private key.

## 2. Verify the existing signature state (`loop.before.1`, `reflex.4`)
- `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous@subtract.ing -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST` — confirm the current manifest verifies before extending it. If it doesn't, stop and surface the drift.

## 3. Human gate — signing (`boundary`, `loop.before.3`)
This is the one step the agent cannot do. Warn the governor first (may prompt the ssh-agent / keychain). Governor runs:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt
```
→ produces `~/subtract.ing/<name>.txt.sig`. `ssh-keygen -Y sign` is the primitive (`reflex.2`); no invented format.

Then add the digest line to `~/subtract.ing/MANIFEST` and re-sign the manifest the same way:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST
```

## 4. Verify locally before publishing (`authority.signed`, `reflex.4`)
```
ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous@subtract.ing -n file \
  -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt
```
Exit 0 required. Only now is it "signed" — not before the verify passes (no ceremonial language).

## 5. Publish (agent executes — pushing already-signed artifacts is infra, not a gate)
- Push `<name>.txt`, `<name>.txt.sig`, updated `MANIFEST`, `MANIFEST.sig` to the host that serves `subtract.ing` directly (the canonical signing domain).
- Ensure `https://subtract.ing/allowed_signers` (or equivalent) publishes the **public** key `jnous@subtract.ing` under that same domain — the trust anchor must live where the claim lives (`reflex.5`).
- **Rousseau pushes.** Emile (`m2mini`) is execution-offload, not the canonical publisher. Surface is a terminal. **Media/`acer1660ti` does not push** — it's NAS/service tier, not formation, mirror-only. A git remote, if any, gets the same files but is explicitly a mirror.
- If the key is ever rotated within the year, keep the old public key in `allowed_signers` with a `valid-before="..."` / `valid-after="..."` window so the year-old signature still verifies.

## 6. How a stranger verifies, a year later
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file \
  -s <name>.txt.sig < <name>.txt
```
Exit 0 ⇒ the file was signed by the holder of `jnous@subtract.ing`'s key. Trust chain: the public key is published under the very domain making the authorship claim; a GitHub mirror agreeing is *not* independent confirmation (correlated copy, not a second source). Optional cross-check: pull `MANIFEST` + `MANIFEST.sig`, verify the manifest signature, confirm `sha256sum <name>.txt` matches its manifest line.

## Authority boundaries, summarized
- Agent: writes file, computes digests, drafts manifest entry, runs all `-Y verify` checks, pushes signed artifacts. 
- Human: runs `ssh-keygen -Y sign` — the only gate. New signing = human; redistribution of signed bytes = infra.
- Canonical = subtract.ing signing domain. Git hosts = mirror. Media node = never a publisher.
