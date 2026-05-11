# Plan: publish a verifiable .txt to subtract.ing

Not executing. This is the procedure, the boundaries, and the verifier's side.

## 0. Ground truth first
- `bash ~/scripts/audit-health.sh` — confirm DNS, the subtract.ing deploy path, and that `~/subtract.ing/` on Rousseau is clean (`git status`, `git log --oneline -5`). Do not proceed on assumptions about node state.

## 1. reflex.2 — don't invent a signature format
- The format is `ssh-keygen -Y sign` (SSH signatures, RFC-style armored `-----BEGIN SSH SIGNATURE-----`). It is verifiable by `ssh-keygen -Y verify`. No custom scheme. Confirm `ssh-keygen` is present (`ssh-keygen -Y sign 2>&1 | head` to see the usage stub).
- Pick a fixed namespace now and never change it. Use `subtract.ing` as the `-n` namespace so the domain is bound into the signature.

## 2. Draft the file — agent does this, no gate (reversible)
- Write the content to canonical staging on **Rousseau**: `~/human/<name>.txt` (then it lands in `~/subtract.ing/` at the published path). Rousseau:~/human/ and ~/subtract.ing/ are canonical; this is just a staging write — execute without asking.
- Freeze the bytes. Any later edit invalidates the signature, so the file is final before step 3.

## 3. Sign — this is the human gate (loop.before.3, boundary)
The agent prepares the exact command; the **governor runs it**. It will trigger a passphrase prompt — warn before handing it over.

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n subtract.ing ~/subtract.ing/<path>/<name>.txt
```

→ produces `<name>.txt.sig` next to the file. Signing identity is `jnous` (the formation signing key). The agent does not hold this authority; only new signing is the gate.

## 4. Publish the public key alongside — so a stranger needs nothing private
- Maintain an `allowed_signers` file at a stable URL under the signing domain, e.g. `https://subtract.ing/allowed_signers`:
  ```
  jnous ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... 
  ```
  (the pubkey from `ssh-keygen -y -f ~/.ssh/id_ed25519`).
- Because trust-on-first-use against subtract.ing alone is weak, also pin the same key fingerprint somewhere independent of the web host: `https://github.com/<gov>.keys`, an SSHFP/TXT DNS record, and the signed session manifest in `~/human/`. A verifier a year out cross-checks at least two.

## 5. Which machine pushes
- **Rousseau pushes.** Node 01 is the governor's workstation and holds canonical `~/subtract.ing/`. It runs the deploy to the subtract.ing web origin (`git push` to the deploy remote / rsync to the host — whatever audit-health confirms is the live path).
- **Emile does not push.** It's a pull-mirror of Rousseau (`discover.sh`).
- **Media (acer1660ti) does not push.** It's the warm-backup/mirror tier, never an origin. No inference, no canonical authority there.
- reflex.5: the GitHub repo (if the deploy goes through one) is **mirror-only**. The authoritative artifact is `https://subtract.ing/<path>/<name>.txt` served under the signing key's domain — not the git commit, not the commit author field.

## 6. loop.after — close the session
- `loop.after.1`: update the manifest in `~/human/` (or `~/subtract.ing/MANIFEST`) to list `<name>.txt` + its sha256 + the `.sig`.
- `loop.after.2`: governor signs the updated manifest the same way (`ssh-keygen -Y sign -n subtract.ing MANIFEST`). Pushing that signed manifest across nodes afterward is just infra — agent can do it.

## 7. How a verifier confirms it, one year later
No accounts, no trust in the agent, only `ssh-keygen` (preinstalled on every Mac/Linux):

```
curl -O https://subtract.ing/<path>/<name>.txt
curl -O https://subtract.ing/<path>/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers

ssh-keygen -Y verify -f allowed_signers -I jnous -n subtract.ing \
  -s <name>.txt.sig < <name>.txt
```

- Exit 0 + `Good "subtract.ing" signature for jnous` ⇒ the bytes are exactly what the holder of the `jnous` key signed.
- Then independent-source check: `ssh-keygen -lf allowed_signers` fingerprint must equal the fingerprint at `github.com/<gov>.keys` (or the DNS SSHFP record). This defeats a future subtract.ing compromise swapping in a forged key + forged signature.
- Optional belt-and-suspenders: the file's sha256 appears in the signed `MANIFEST`, which itself verifies against the same key.

## Authority boundaries, summarized
- **Agent (any node, Rousseau here):** drafts the .txt, freezes it, prepares the precise sign command, updates the manifest draft, runs the deploy *after* signing, propagates signed artifacts to mirrors.
- **Governor (human, holds `jnous` private key):** runs `ssh-keygen -Y sign` for the file and the manifest. This is the only step the agent cannot do. Agent warns first because it blocks on a passphrase prompt.
- **Authoritative location:** `https://subtract.ing/...` under the signing key's domain. Git hosts and Emile/Media copies are mirrors and can never be cited as the source of authorship — the SSH signature is, and that's what the verifier checks.
