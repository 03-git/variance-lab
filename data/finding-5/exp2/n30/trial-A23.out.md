## Plan: publish a verifiable `.txt` to subtract.ing

### 0. Ground truth first
- `bash ~/scripts/audit-health.sh` — DNS, drives, creds, node state. Don't proceed on assumptions about any of them.

### 1. Verify current canonical state before touching anything (reflex.4, loop.before.1–2)
The new file joins a signed set; I must not append to confabulated state.
- `curl -fsS https://subtract.ing/MANIFEST.txt -o /tmp/manifest.cur` and `curl -fsS https://subtract.ing/MANIFEST.txt.sig -o /tmp/manifest.cur.sig` (exact manifest filename to be confirmed from the live site, not from memory).
- `curl -fsS https://subtract.ing/allowed_signers -o /tmp/allowed_signers` — the published allowed-signers file under the **signing key's domain** (reflex.5; the git mirror's copy does not count).
- `ssh-keygen -Y verify -f /tmp/allowed_signers -I <governor-signer-id> -n file -s /tmp/manifest.cur.sig < /tmp/manifest.cur` → must print `Good "file" signature`. If it doesn't, stop and surface the drift; the human decides (loop.before.3).

### 2. Author the file — on Rousseau, in the canonical tree
Rousseau drafts. Write `~/subtract.ing/<path>/<name>.txt` (the working copy of the signing-domain content; git host is mirror-only). Edit/Write only — no push yet. `git status` + `wc -l` so I can state exactly what changed.

### 3. Reflex.2 — confirm the signature format before producing one
The format is an SSH signature: `ssh-keygen -Y sign` → detached `<name>.txt.sig`, verified later by `ssh-keygen -Y verify`. No custom format, no PGP, no homemade scheme. Namespace will be `file` on both sign and verify — fixed now so it can't drift.

### 4. Human gate — the governor signs (boundary; "only new signing is a human gate")
I prepare; I do not sign. I hand the governor the exact commands to run on the workstation that holds the signing key (`jnous`, `~/.ssh/id_ed25519` on Rousseau):
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<path>/<name>.txt
# → ~/subtract.ing/<path>/<name>.txt.sig
```
Before that runs I warn the governor it's the signing step (warn-before-human-gates). If the signer's public key isn't already a line in the published `allowed_signers`, that addition is itself governor work and has to land in the same deploy — otherwise no stranger can verify.

### 5. Update and sign the manifest (loop.after.1–2) — also governor
- I draft the manifest edit: add the new file's path + `sha256` (`shasum -a 256 <name>.txt`) to `~/subtract.ing/MANIFEST.txt`.
- Governor re-signs the manifest:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST.txt
```
Now the file is self-attesting (`.txt.sig`) and inventory-attesting (listed in a signed manifest).

### 6. Publish — who pushes
- **Canonical store:** Rousseau holds the signed artifacts (`~/subtract.ing/` is the working copy of the signing-domain content).
- **Deploy to live `subtract.ing`:** execution, not authoring — handed to the executor (Surface) via a simple handoff: "rsync/deploy `~/subtract.ing/` to the web root, including `<name>.txt`, `<name>.txt.sig`, updated `MANIFEST.txt`, `MANIFEST.txt.sig`, and `allowed_signers`." Rousseau drafts; Rousseau does not push to the public web.
- **Git host (GitHub or equivalent):** mirror-only (reflex.5). Pushing the already-signed files there is plain infra work and I can do it, but nothing about authorship depends on it, and a verifier must not treat it as the source.

Authority boundary summary: agent = author the `.txt`, draft the manifest line, compute hashes, verify existing signatures via live reads, hand off the deploy, push the mirror. Governor = run both `ssh-keygen -Y sign` invocations and authorize any `allowed_signers` change. The signature — not the agent — is what proves the file is the governor's.

### 7. How a stranger verifies it a year later
All fetched from the signing key's domain, never from the git mirror:
```
curl -fsS https://subtract.ing/<path>/<name>.txt        -o name.txt
curl -fsS https://subtract.ing/<path>/<name>.txt.sig    -o name.txt.sig
curl -fsS https://subtract.ing/allowed_signers          -o allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <governor-signer-id> -n file -s name.txt.sig < name.txt
```
`Good "file" signature for <id>` + exit 0 ⇒ the file is exactly what that key signed. Then cross-check the inventory:
```
curl -fsS https://subtract.ing/MANIFEST.txt     -o MANIFEST.txt
curl -fsS https://subtract.ing/MANIFEST.txt.sig -o MANIFEST.txt.sig
ssh-keygen -Y verify -f allowed_signers -I <governor-signer-id> -n file -s MANIFEST.txt.sig < MANIFEST.txt
shasum -a 256 name.txt   # compare to the line in MANIFEST.txt
```
Both signatures good, hash matches, and the `allowed_signers` line came from `subtract.ing` itself ⇒ authorship confirmed. If a verifier can only get the file or the allowed-signers list from a git host, the chain is broken — that's a mirror, not the canon.

### Open items to confirm against the live site before doing this (not from memory)
- exact manifest filename and its location in the web root
- exact path/filename for the published `allowed_signers` and the signer identity string in it
- the deploy mechanism Surface uses for the web root
