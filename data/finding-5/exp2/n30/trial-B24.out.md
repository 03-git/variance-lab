I'm not running `audit-health.sh` or anything else here — the task is explicitly plan-only ("Do not execute"). Flagging that, since session-start normally requires it; this is a deliberate skip for a non-acting request.

# Plan: publish a signed `.txt` to subtract.ing, verifiable by a stranger in a year

## 0. Pre-flight (governance loop.before)
- `loop.before.1` / `reflex.4`: verify the last manifest signature on the subtract.ing runtime repo with `ssh-keygen -Y verify` against the existing `allowed_signers` before touching anything. If it fails, stop.
- `loop.before.2`: `git status` in `~/subtract.ing/` — surface any unsigned drift before adding to it.
- `reflex.2`: the signature format is **not invented** — it's `ssh-keygen -Y sign` / `-Y verify` (SSH signatures, `SSHSIG` armor). Confirmed primitive, no wrapper.

## 1. Author the file — Rousseau (this workstation)
- Write the content to e.g. `~/subtract.ing/www/<name>.txt` (the web-root tree for the domain, wherever it actually lives — confirm path from system state, not memory).
- Plain UTF-8, LF endings, no BOM. The bytes are what gets signed, so freeze them now.

## 2. Sign it — the governor, not the agent (`boundary`, `authority.source`)
- The agent prepares; **the human runs the signing command** with the human's private key. `authority.unsigned → do not act`; the agent never holds or invokes the signing key on its own initiative.
- Command (governor runs):
  ```
  ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/www/<name>.txt
  ```
  → produces `~/subtract.ing/www/<name>.txt.sig` (the detached `SSHSIG`).
- `-n file` is the namespace; the verifier must use the same one. Standardize on `file`.

## 3. Publish the identity → key binding at the signing domain (`reflex.5`)
- Maintain `allowed_signers` (ssh `AllowedSigners` format), one line:
  ```
  jns@subtract.ing namespaces="file" ssh-ed25519 AAAA...   # the governor's signing pubkey
  ```
  Optionally add `valid-after="YYYYMMDD"` so the binding has a provenance window.
- This file must be served from **subtract.ing itself** — e.g. `https://subtract.ing/allowed_signers` (or `.ssh/allowed_signers`). Canonical content lives under the signing key's domain. GitHub copy, if any, is **mirror-only** and is not authoritative for verification.

## 4. Deploy — which machine pushes
- **Rousseau pushes.** It's the governor's main workstation and (per the formation layout) the node with deploy authority to the subtract.ing origin. Commit in `~/subtract.ing/` (`git add <name>.txt <name>.txt.sig allowed_signers`), then deploy to the live web root for the domain (rsync/scp/`git push` to the origin host that *serves* subtract.ing — the canonical surface, not a git host).
- **Emile does not push.** Emile is an offload target for reasoning/execution via `ssh m2mini "claude -p"`; it has no deploy authority to the domain.
- **Surface does not push.** Governor terminal only.
- A push to GitHub (if the repo mirrors there) is allowed but is explicitly a *mirror* — it does not constitute publication for verification purposes (`reflex.5`).

## 5. Close the loop (`loop.after`)
- Update the runtime manifest to include `<name>.txt` + its `.sig`.
- Re-sign the manifest (`ssh-keygen -Y sign`) and deploy that too. Now the file is covered both by its own detached sig and by the signed manifest.

## 6. How a stranger verifies, a year later
1. Fetch three files over HTTPS **from subtract.ing** (not the git mirror):
   - `https://subtract.ing/<name>.txt`
   - `https://subtract.ing/<name>.txt.sig`
   - `https://subtract.ing/allowed_signers`
2. Run:
   ```
   ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s <name>.txt.sig < <name>.txt
   ```
   Expected: `Good "file" signature for jns@subtract.ing`.
3. What this proves: the holder of the published key signed *exactly these bytes*. It's offline, has no CA or expiry, and doesn't depend on TLS or on GitHub — so it still holds in a year as long as subtract.ing still publishes `allowed_signers` and the key hasn't been rotated out without a forwarding entry.
4. Trust root for the *identity*: the key is canonical because it's served from the signing key's own domain. A verifier who wants a second anchor can cross-check the same pubkey against the signed manifest history in the repo, or any prior signed release — consistency over time is the corroboration.

## Key-rotation note (so it survives a year)
- If the signing key changes within the year: keep the old pubkey in `allowed_signers` with `valid-before="YYYYMMDD"` and add the new one with `valid-after`. Never silently drop a key that has signed published content — that breaks every existing verification. If a key is *compromised*, publish a revocation alongside, don't just delete the line.

## Authority boundaries, summarized
- Agent: authors the file, prepares the commit, runs the verification (a live read — allowed under `reflex.4`), drafts the manifest update.
- Governor (human): runs `ssh-keygen -Y sign`, holds the private key, makes the `loop.before.3` call (sign / continue / abort), authorizes the deploy.
- Machines: Rousseau authors + pushes to the canonical origin; Emile and Surface do neither; GitHub is mirror-only and never the verification source.
