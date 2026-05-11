Plan only — nothing executed.

## 0. Pre-flight (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, creds, drives before touching anything.
- Verify the *current* signed manifest before extending it: `ssh-keygen -Y verify -f ~/.subtract/allowed_signers -I jnous -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST`. If that fails, stop — the chain is broken and nothing new gets added on top of unverified state.
- Reflex.2: the signing primitive is `ssh-keygen -Y sign` / `-Y verify`. No bespoke format, no library wrapper.

## 1. Draft (agent, on Rousseau)
- Rousseau is canonical for `~/human/` and is the governor's workstation. Write the file there: `~/subtract.ing/<name>.txt` (working tree of the site repo) — *not* `/tmp`.
- Agent does the drafting/editing (`Edit`/`Write`). This is reversible staging work — no permission needed.

## 2. Sign (human gate — agent stops here)
- Authority boundary: `boundary` + `loop.before.3`. The agent prepares; the human signs. This is the *only* human gate in the sequence.
- Governor runs, on Rousseau (where the private key lives — `claude -p`/agents never touch it):
  ```
  ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt
  ```
  → produces `~/subtract.ing/<name>.txt.sig`. The principal in `~/.subtract/allowed_signers` is `jnous`.
- Warn the governor first (feedback: warn before human gates) — this is an interactive command they must run themselves.

## 3. Verify locally before publish (agent — reflex.4)
- Live read, not memory:
  ```
  ssh-keygen -Y verify -f ~/.subtract/allowed_signers -I jnous -n file -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt
  ```
  Expect exit 0 + `Good "file" signature`. If not, do not publish.

## 4. Update + sign the manifest (loop.after.1/2)
- Add `<name>.txt` and its sig to `~/subtract.ing/MANIFEST` (agent edits the draft).
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST` → `MANIFEST.sig`. Second (and last) human action.
- Confirm `~/subtract.ing/allowed_signers.txt` is present in the web tree and itself listed in the manifest — that's the published trust root the stranger will need.

## 5. Push (infra work — already-signed artifacts, no gate)
- The canonical publish is to the **subtract.ing signing domain** — the web host serving `https://subtract.ing/`. Per "Rousseau drafts, Surface executes," the deploy push runs from **Surface** (the node holding deploy creds): `git push` to the deploy remote / `rsync` of the `{<name>.txt, <name>.txt.sig, MANIFEST, MANIFEST.sig, allowed_signers.txt}` set to the host. Pushing signed artifacts across nodes is infra, not a gate (feedback: human gate scope).
- **Rousseau** drafts and is where signing happened; it does not run the deploy push.
- **GitHub / any git mirror**: push if you want, but reflex.5 — git hosts are mirror-only. A copy on GitHub is *not* the canonical artifact and does not establish authorship; only the file served under the signing domain does.
- **Media (acer1660ti)**: does not push. It's a warm backup tier, not formation, not canonical. It may *receive* a copy as backup; it never originates the published version.
- **Emile**: not in this path. Execution offload only; no canonical pushes.

## 6. Post-publish check (agent)
- `curl -fsS https://subtract.ing/<name>.txt | ssh-keygen -Y verify -f <(curl -fsS https://subtract.ing/allowed_signers.txt) -I jnous -n file -s <(curl -fsS https://subtract.ing/<name>.txt.sig)` — confirm the *served* bytes verify, not just the local ones.

## How a stranger verifies it a year from now
1. Fetch the artifact and its detached signature from the signing domain:
   ```
   curl -O https://subtract.ing/<name>.txt
   curl -O https://subtract.ing/<name>.txt.sig
   ```
2. Fetch the trust root from the *same* domain over HTTPS (this binding — key published under subtract.ing — is what makes it authorship and not just "some Ed25519 key"):
   ```
   curl -O https://subtract.ing/allowed_signers.txt
   ```
3. Verify:
   ```
   ssh-keygen -Y verify -f allowed_signers.txt -I jnous -n file -s <name>.txt.sig < <name>.txt
   ```
   Exit 0 + `Good "file" signature` → the holder of `jnous`'s key authored this file.
4. Optional corroboration: fetch `MANIFEST` + `MANIFEST.sig`, verify the same way, confirm `<name>.txt` is listed — ties the file into the signed canonical set rather than standing alone.

Why it still holds in a year: `ssh-keygen -Y` signs *content*, not a timestamp — the signature never "expires." The only requirement is that `allowed_signers.txt` served from subtract.ing still carries the same `jnous` public key. If the key is ever rotated, the old signature still verifies against the archived old key, and the manifest chain records the handoff. The git mirror's state is irrelevant to all of this.
