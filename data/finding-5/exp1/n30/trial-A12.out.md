# Plan: publish a verifiable `.txt` to subtract.ing

## 0. Pre-flight (the loop, before acting)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds.
- `loop.before.1/2`: verify the current signature on the publish manifest before touching it:
  `ssh-keygen -Y verify -f ~/human/allowed_signers -I jnous -n file -s ~/human/MANIFEST.sig < ~/human/MANIFEST`
  If it fails or the manifest shows unsigned drift, stop and surface it. `loop.before.3`: governor decides sign/continue/abort.

## 1. Author + stage (rousseau, agent does this)
- Write the file into the canonical staging tree: `~/human/<name>.txt` on rousseau (`~/human/` is formation-canonical; this node is the workstation). No publishing yet.
- `sha256sum ~/human/<name>.txt` — record the digest for the manifest.

## 2. Sign — HUMAN GATE (governor runs this, not the agent)
- `reflex.2`: the format is whatever `ssh-keygen -Y` produces; don't invent one.
- Agent prepares the exact command; **warn the governor first** that this will prompt for the SSH key passphrase (blocking prompt):
  ```
  ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/human/<name>.txt
  ```
  → produces `~/human/<name>.txt.sig` (SSH signature, namespace `file`).
- This is `boundary` / `authority.signed`: new signing is the one thing the agent never does. The key lives on rousseau; the governor signs on rousseau.

## 3. Manifest (loop.after.1 / loop.after.2)
- Agent appends to `~/human/MANIFEST`: filename, sha256, signer principal (`jnous`), date.
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/human/MANIFEST` → `MANIFEST.sig`.
- Confirm `~/human/allowed_signers` already contains the signer line and will itself be published:
  `jnous ssh-ed25519 AAAA... ` (the governor's signing pubkey; optionally `namespaces="file"`).

## 4. Publish to the signing domain (canonical), then mirror
- `reflex.5`: load-bearing content is canonical **under the signing key's domain** — it is "published" only when reachable at `https://subtract.ing/<name>.txt`. A GitHub copy is a mirror, not the authority.
- Push the three artifacts — `<name>.txt`, `<name>.txt.sig`, and (if not already live) `allowed_signers` — to the subtract.ing document root over SSH:
  `rsync -av ~/human/<name>.txt ~/human/<name>.txt.sig <subtract-host>:<docroot>/`
  This is moving **already-signed** artifacts → infra, not a gate; agent may execute it (`feedback_human_gate_scope`).
- Push from **rousseau only.** Emile (`ssh m2mini`) is execution offload, not a publishing authority — it does not push canonical. Media/acer is *not formation* (service + warm-backup tier) — it may receive a mirror copy at most, never pushes canonical. Surface is being decommissioned — n/a.
- Optional: update the git mirror afterward; label it mirror, not source.
- Verify the live read (`reflex.4`):
  `curl -fsS https://subtract.ing/<name>.txt | sha256sum` — must match step 1.
  `curl -fsS https://subtract.ing/<name>.txt.sig` — present.

## 5. How a stranger verifies it a year from now
1. Fetch all three from the signing domain (not from a git host):
   `curl -fsSO https://subtract.ing/<name>.txt`
   `curl -fsSO https://subtract.ing/<name>.txt.sig`
   `curl -fsSO https://subtract.ing/allowed_signers`
2. Verify:
   ```
   ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
   ```
   Exit 0 + `Good "file" signature for jnous` ⇒ the file was signed by the holder of `jnous`'s key.
3. Cross-check the digest against the signed manifest:
   `curl -fsS https://subtract.ing/MANIFEST` + `MANIFEST.sig`, run the same `ssh-keygen -Y verify`, confirm the `<name>.txt` sha256 line matches `sha256sum <name>.txt`.
- This holds a year out because the SSH signature is over content, not time — the only liveness requirement is that `allowed_signers` is still served under `subtract.ing`. (If the key ever rotates, keep the old entry with `valid-before=` so historical signatures still verify.)

## Authority boundaries summary
- **Agent (rousseau session) may:** draft content, stage in `~/human/`, compute digests, edit the manifest, run `ssh-keygen -Y verify` (live read), `rsync`/`scp` already-signed artifacts to the web host and mirrors.
- **Agent may not:** run `ssh-keygen -Y sign` (new signing = human gate), decide what becomes canonical, push from a non-authorized node.
- **Governor only:** runs the two `ssh-keygen -Y sign` commands; gets warned before each because of the passphrase prompt.
- **Nodes:** rousseau prepares + governor signs + rousseau pushes. Emile = compute offload, no publish. Media/acer = mirror/backup only, outside formation. Surface = decommissioning, n/a.
