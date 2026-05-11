# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. Below is the sequence, the boundaries, and the verifier path.

## 0. Ground truth first (loop.before)
- `bash ~/scripts/audit-health.sh` — DNS, drives, creds, node state. Don't assume the deploy path; read it.
- Identify the real publish mechanism instead of guessing: `git -C ~/subtract.ing remote -v`, `ls ~/scripts | grep -i 'deploy\|publish\|subtract'`, and check whether subtract.ing is served from rousseau (`subtract→m1studio:8087` per the hosuni config) or pushed to an external host. reflex.4: verify with a live read before acting.
- Verify the current canonical manifest's signature before touching anything:
  `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST`
  If that fails or the manifest is stale → stop, surface drift, governor decides (loop.before.3).

## 1. reflex.2 check (before inventing anything)
The signature format is not invented: `ssh-keygen -Y sign` / `-Y verify` with namespace `file` is the format. A stranger reproduces it with stock OpenSSH. No custom scheme.

## 2. Agent prepares the file (no signing here)
On **rousseau** (canonical archive node, governor's workstation), in the site's canonical source tree (`~/subtract.ing/...` — the dir confirmed in step 0, *not* `/tmp`):
- `Write` the new `newfile.txt`.
- Draft the manifest update: append `newfile.txt  <sha256>` (`shasum -a 256 newfile.txt`) to `~/subtract.ing/MANIFEST`.
- Stop. The agent does not sign and does not push unsigned load-bearing content. boundary: the agent prepares, the human signs.

## 3. Human gate — governor signs (the one gate)
Only the holder of the `jnous` private key, the governor, runs this. Not Claude, not a subagent, not any other node:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file newfile.txt        # -> newfile.txt.sig
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file MANIFEST           # -> MANIFEST.sig  (loop.after.2)
```
New signing is the human gate (per the human-gate-scope rule). Everything before is prep; everything after is infra.

## 4. Which machine pushes
- **Rousseau pushes.** It's node 01, the archive/canonical node and the governor's workstation. The signed `newfile.txt`, `newfile.txt.sig`, updated `MANIFEST`, `MANIFEST.sig` go to the canonical web root via whatever step 0 identified (deploy script / rsync to the serving host / commit+push if subtract.ing serves from a repo on rousseau itself).
- **Emile does not push.** Pull-mirror only (`discover.sh` pulls from rousseau).
- **Surface does not push.** Governor terminal; it pulls `~/human/` and friends, it is not in the publish path.
- **Media / acer does not push.** Not formation — service infra (Jellyfin/*arr/Kiwix), never in the signing or publish path.
- Pushing the *already-signed* bundle from rousseau to the serving host is plain infra; the agent can do it. Re-signing or first-signing is not.

## 5. reflex.4 — confirm with a live read before declaring done
- `curl -fsS https://subtract.ing/newfile.txt -o /tmp/v.txt`
- `curl -fsS https://subtract.ing/newfile.txt.sig -o /tmp/v.txt.sig`
- `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous -n file -s /tmp/v.txt.sig < /tmp/v.txt`
- Re-fetch and re-verify `MANIFEST` + `MANIFEST.sig`; confirm `newfile.txt`'s sha256 matches the manifest line. If any check fails, the publish is not done.
- Update formation memory / session log noting the new canonical artifact (loop.after.1).

## 6. How a stranger verifies it a year later
Needs only OpenSSH and `curl`. reflex.5: trust the copy under the signing domain; treat any GitHub mirror as non-authoritative.
```
curl -O https://subtract.ing/newfile.txt
curl -O https://subtract.ing/newfile.txt.sig
curl -O https://subtract.ing/allowed_signers          # the published allowed-signers file under the signing domain
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s newfile.txt.sig < newfile.txt
```
- `Good "file" signature for jnous` → authorship confirmed. The signature proves authority; the host, the TLS cert, and any git mirror do not.
- Optional chain check: fetch `MANIFEST` + `MANIFEST.sig`, verify the manifest signature the same way, then `shasum -a 256 newfile.txt` and confirm it matches the manifest entry — ties the file into the signed set, not just signed in isolation.
- The identity `jnous` is pinned by the allowed-signers file served from subtract.ing itself; the year gap doesn't matter because the verification is offline and key-based, not trust-on-first-use against a live service.

## Authority boundaries, summarized
- **Claude / any node automation:** prepare `newfile.txt`, draft the manifest delta, push *signed* artifacts from rousseau, run verification. Never produces a signature.
- **Governor (human):** sole holder of `jnous` key; runs `ssh-keygen -Y sign` for the file and the manifest. The only blocking step.
- **Verifier (stranger):** needs nothing from the formation but the three public files and stock `ssh-keygen -Y verify`.
- **Canonical vs mirror:** `https://subtract.ing/...` under the signing key's domain is canonical; a git host, if used, is a mirror and carries no authority.

One open item I would not paper over: the exact deploy command in step 4 depends on what `audit-health.sh` and `~/subtract.ing` actually show. I'd read that before running anything, rather than name an rsync target here that might be confabulated.
