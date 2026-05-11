Plan only — nothing executed.

## Step 0 — ground truth (Rousseau)
`bash ~/scripts/audit-health.sh`. Confirm: subtract.ing DNS resolves, the web-root path is mounted/writable, the signing key is present (agent/keychain). Don't proceed on assumptions about any of those.

## Step 1 — reflex checks (before anything is written)
- **reflex.2 (memory→signature):** the format is SSHSIG via `ssh-keygen -Y sign` / `ssh-keygen -Y verify`, namespace `file`. Don't invent a scheme — that's the one a stranger will already have on their machine.
- **reflex.5 (canonical→signing domain):** a `.txt` published on subtract.ing is load-bearing, so authorship rests on the copy under the signing key's domain (`https://subtract.ing/...`). Any GitHub/git mirror is mirror-only; pushing there is *not* publishing and establishes nothing.
- **reflex.4 (action→verification):** before publishing, verify the current head-of-chain signature with a live read (Step 2).

## Step 2 — loop.before (Rousseau)
1. `ssh-keygen -Y verify -f ~/human/allowed_signers -I jnous -n file -s ~/human/MANIFEST.sig < ~/human/MANIFEST` — last manifest signature must still verify (live read).
2. Surface unsigned drift in `~/human/` (`git status` / diff against MANIFEST).
3. Human decides: sign / continue / abort. Agent halts for that call.

## Step 3 — draft (Rousseau; the agent prepares)
Write `~/human/<name>.txt` into canonical staging (`rousseau:~/human/` is canonical for formation human-authored work). Reversible staging write — no human gate to draft.

## Step 4 — sign (human only, on Rousseau where the key lives)
Authority boundary: `boundary` / `authority.signed` — **the agent does not run this; new signing is the hard human gate.** Warn the governor first (this pops a keychain prompt).
Human runs:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/human/<name>.txt
```
→ `~/human/<name>.txt.sig`. Signing identity = `jnous`, which must already map to this pubkey in `~/human/allowed_signers`.

## Step 5 — publish the bundle to subtract.ing
Push **three** files to the subtract.ing web root so all are fetchable over HTTPS: `<name>.txt`, `<name>.txt.sig`, `allowed_signers`.
- **Who pushes:** the node that owns/serves the subtract.ing web root. Rousseau is the canonical/archive node and originates the content. If Surface is still the executor (it is, on 2026‑05‑10), Rousseau drafts + the human signs on Rousseau, then the *already-signed, immutable* bundle is handed to Surface to run the deploy — moving signed artifacts between nodes is plain infra, not a gate.
- **Who does NOT push:** Emile (execution offload only — not canonical, never originates or serves canonical content). Acer/"Media" (not formation — service infra; never touches canonical). A `git push` to a GitHub mirror is permitted as a mirror but is explicitly not the publish step (reflex.5).

## Step 6 — durability for "a year from now"
- `allowed_signers` lives at the canonical domain (`https://subtract.ing/allowed_signers`), not only in a repo — verification must not depend on a git host being up.
- Pin validity windows so a future key rotation doesn't void old signatures:
  `jnous valid-after="20260101",valid-before="20270601" ssh-ed25519 AAAA... jnous`
  Keep retired keys in the file with their own windows.
- Refresh the SDXC air-gap manifest + FROZEN snapshot to include `<name>.txt` and its `.sig` — offline third copy.

## Step 7 — loop.after
- **loop.after.1:** append `<name>.txt` (path · sha256 · `.sig` name) to `~/human/MANIFEST`.
- **loop.after.2:** human re-signs: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/human/MANIFEST`. Push updated `MANIFEST` + `MANIFEST.sig` to subtract.ing.

## How a stranger verifies, a year out
1. `curl -O https://subtract.ing/<name>.txt` ; `curl -O https://subtract.ing/<name>.txt.sig` ; `curl -O https://subtract.ing/allowed_signers`
2. `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt` → must print `Good "file" signature for jnous`.
3. Cross-check the `jnous` pubkey in `allowed_signers` against an independent record of that key (the key as carried in governance context / a separate channel). The SSHSIG proves the key-holder authored the file; the out-of-band key check is what binds "jnous" to the human.
4. Optional integrity tie-in: `curl -O` the `MANIFEST` + `MANIFEST.sig`, verify them the same way, confirm `<name>.txt`'s sha256 is listed — shows the file is part of the signed canonical set, not a loose drop.

## Trust root, stated plainly
HTTPS and any git host are transport, not authority (`authority.unsigned` = suggestion only). The `ssh-keygen -Y` + `allowed_signers` chain is the only load-bearing part. An unsigned `.txt` served from subtract.ing — even over TLS — is not verified authorship; a verifier should treat it as confabulation-possible until the signature checks out.
