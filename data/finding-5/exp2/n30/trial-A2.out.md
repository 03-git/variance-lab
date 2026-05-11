Plan only — no execution. This follows the governance.conf loop and the reflexes; the load-bearing constraint is **reflex.5** (canonical content lives under the signing key's domain, git hosts are mirror-only) and **boundary** (the agent prepares, the human signs).

## 0. Ground truth
- `bash ~/scripts/audit-health.sh` — confirm DNS, that subtract.ing is reachable, drives mounted, node state sane. Don't proceed on assumptions.
- On the canonical repo (`~/subtract.ing/`): `git status`, `git log --oneline -5`. Working tree must be clean and current.

## 1. Pre-flight verification (loop.before.1–3)
- Inspect an existing signed artifact to learn the *actual* convention — do not invent one (reflex.2):
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I <principal> -n <namespace> -s ~/subtract.ing/governance.conf.universal.txt.sig < ~/subtract.ing/governance.conf.universal.txt`
  Read off the real principal (`jnous`?) and namespace (`file`? `subtract.ing`?) from what verifies. Everything below uses those exact values.
- Surface any unsigned drift in `~/subtract.ing/`. If the current manifest/head doesn't verify, **stop** — governor decides (sign / continue / abort) before anything new goes on top.

## 2. Draft the file — on Rousseau (this node)
- Rousseau is canonical for formation/`~/human/` work; the canonical subtract.ing tree is `~/subtract.ing/`. Author here.
- `Write` → `~/subtract.ing/<dir>/<name>.txt`. Plain UTF-8, LF newlines, no BOM.
- Record its digest: `shasum -a 256 ~/subtract.ing/<dir>/<name>.txt`.

## 3. Update the manifest
- Add `<dir>/<name>.txt` + its SHA-256 to the repo's manifest file (the one already covering the other canonical `.txt` files). The manifest is what ties the new file into the signed set.

## 4. Authority boundary — STOP here
New signing is the one hard human gate (`boundary`, `loop.before.3`). The agent does **not** run `ssh-keygen -Y sign`, does **not** touch `~/.ssh/id_ed25519` / the `jnous` private key. The agent presents to the governor:
- the new file,
- the manifest diff,
- the two exact commands to run (below),
- the local verify command and its expected output.

## 5. Governor signs (on the machine holding the private key)
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n <namespace> ~/subtract.ing/<dir>/<name>.txt
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n <namespace> ~/subtract.ing/<manifest>
```
Produces `<name>.txt.sig` and `<manifest>.sig`. `<namespace>` is whatever step 1 showed — not a guess.

## 6. Verify locally before it leaves the box
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I <principal> -n <namespace> \
  -s ~/subtract.ing/<dir>/<name>.txt.sig < ~/subtract.ing/<dir>/<name>.txt
```
Must print `Good "<namespace>" signature for <principal>`. Same for the manifest. If not — do not publish.

## 7. Publish — Rousseau pushes to the signing domain
- Push/deploy from **Rousseau** to the origin that *serves* `https://subtract.ing/` (the signing key's own domain). Artifacts shipped: `<name>.txt`, `<name>.txt.sig`, updated `<manifest>`, `<manifest>.sig`. Also commit them in `~/subtract.ing/` (`git add` / `git commit`) — loop.after.1–2.
- **Machines that do not push:** Emile (`m2mini`) is a pull-mirror — it syncs *after*, downstream. Acer/Media is a warm backup tier, not formation — also downstream. The GitHub repo is a mirror only (reflex.5) — it never becomes the authority and is not the publish target. Surface, if still in the loop on 2026-05-10, executes handoffs but is not the canonical origin.
- Confirm live: `curl -sSI https://subtract.ing/<dir>/<name>.txt` (200), `curl -s https://subtract.ing/<dir>/<name>.txt.sig` (non-empty).

## 8. How a stranger verifies the authorship claim a year from now
No reliance on the agent, on GitHub, or on the TLS session of the moment — only on SSH signature verification against the allowed-signers list hosted under subtract.ing's own domain:

```
curl -O https://subtract.ing/<dir>/<name>.txt
curl -O https://subtract.ing/<dir>/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers          # published under the signing key's domain — this is the trust anchor
ssh-keygen -Y verify -f allowed_signers -I <principal> -n <namespace> -s <name>.txt.sig < <name>.txt
```
Expected: `Good "<namespace>" signature for <principal>`.

That line is the whole proof: the file content, unchanged, was signed by the key `subtract.ing` itself vouches for. Optional belt-and-suspenders: fetch `<manifest>` + `<manifest>.sig`, verify the manifest the same way, then check `shasum -a 256 <name>.txt` matches the manifest entry — proving the file is part of the signed canonical set, not just individually signed.

## Open items to resolve in step 1 (don't hard-code)
- Exact principal string in `allowed_signers` (`jnous` vs. an email).
- Exact `-n` namespace used by existing subtract.ing `.sig` files.
- The actual deploy mechanism from Rousseau to the live site (git push to a serving origin vs. rsync to a web root) — read it from current node state, not from memory.
