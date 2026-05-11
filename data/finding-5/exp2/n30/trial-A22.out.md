# Plan: publish a verifiable `.txt` to subtract.ing

Nothing below is executed. The signing step is the governor's; everything else Claude-on-Rousseau prepares.

## 0. Ground truth (before acting — `loop.before`)
- `bash ~/scripts/audit-health.sh` — read DNS, creds, drive, node state. Do not assume.
- Verify the *current* canonical manifest still carries a good signature before touching anything (`reflex.4`, "assertions-that-block count as actions"):
  - `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST`
  - Expect `Good file signature for jnous`. If it fails or there's unsigned drift in `~/subtract.ing/`, stop and surface it — the governor decides (sign / continue / abort).

## 1. Draft (Rousseau — canonical workstation, drafts but does not push outward)
- Write the new file into the canonical working tree: `~/subtract.ing/<name>.txt`. `subtract.ing` is the signing domain, so this is the canonical copy; git hosts are mirror-only (`reflex.5`).
- Freeze the exact bytes *now*, because the bytes are what gets signed and any later transform breaks the signature:
  - `printf` a trailing newline if missing; `file ~/subtract.ing/<name>.txt` to confirm UTF-8 / no CRLF; `LC_ALL=C` sanity check.
  - `shasum -a 256 ~/subtract.ing/<name>.txt` — record this hash.
- Do **not** invent a signature scheme (`reflex.2`): the format is an OpenSSH signature from `ssh-keygen -Y sign` with namespace `file`, verifiable by `ssh-keygen -Y verify`. That's the whole mechanism.

## 2. Sign — the human gate (`boundary`: the agent prepares, the human signs)
- Claude prepares the exact command and hands it over. Warn first that this touches `~/.ssh/id_ed25519` and will prompt for the key passphrase (a blocking prompt — `feedback.warn_human_gates`).
- Governor runs, on Rousseau:
  - `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt` → produces `~/subtract.ing/<name>.txt.sig`
- Claude never holds the private key and never runs `-Y sign`. New signing is the only step that is a human gate (`feedback.human_gate_scope`).

## 3. Update + re-sign the manifest (`loop.after.1`, `loop.after.2`)
- Add a line to `~/subtract.ing/MANIFEST`: `<name>.txt  <sha256 from step 1>` (match the file's existing format).
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST` → `MANIFEST.sig`.
- This puts the new file under the manifest chain, not just its own detached sig.
- If `~/subtract.ing/allowed_signers` does not already contain the `jnous` line (`jnous ssh-ed25519 AAAA...`), it must — that's the file a stranger needs. It should itself be served from subtract.ing.

## 4. Verify locally before anything leaves the box
- `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt` → must print `Good file signature for jnous`.
- Same for `MANIFEST.sig`. If either fails, stop — do not publish.

## 5. Publish (externally-visible mutation → governor confirms; executor pushes)
- Pushing already-signed bytes is infra, not a human gate — *but* publishing to the public domain is an externally-visible mutation, so confirm with the governor before the push (`feedback.stop_asking_on_reversible` carves out exactly this case).
- The outward push is done from **Surface** (the executor terminal), not Rousseau — Rousseau drafts and verifies, Surface executes (`feedback.draft_rousseau_execute_surface`). Emile is for heavy compute, not relevant here.
- Use the *existing* deploy path in `~/subtract.ing/` (look for `deploy.sh` / `Makefile` / publish target) — do not invent a new one (`fail.additive`). Whatever it is, it ships `<name>.txt`, `<name>.txt.sig`, `MANIFEST`, `MANIFEST.sig`, and `allowed_signers` to the host that answers `https://subtract.ing`. If it's `rsync -av --checksum ~/subtract.ing/ <web-host>:<webroot>/` over ssh, that's the primitive.
- Git host: push the mirror *after* the canonical host is live. Mirror-only (`reflex.5`).

## 6. Verify from the outside, as a stranger would (`reflex.4` — live read after acting)
- `curl -fsSL https://subtract.ing/<name>.txt -o /tmp/v.txt`
- `curl -fsSL https://subtract.ing/<name>.txt.sig -o /tmp/v.txt.sig`
- `curl -fsSL https://subtract.ing/allowed_signers -o /tmp/as`
- `ssh-keygen -Y verify -f /tmp/as -I jnous -n file -s /tmp/v.txt.sig < /tmp/v.txt` → `Good file signature for jnous`
- `shasum -a 256 /tmp/v.txt` matches the line in `https://subtract.ing/MANIFEST`, and `MANIFEST.sig` verifies.
- Record the result in `~/human/sessions/2026-05-10-*.md` (`loop.after`).

## How a verifier confirms the claim (one year later, stranger)
1. Fetch over HTTPS from `subtract.ing`: `<name>.txt`, `<name>.txt.sig`, `allowed_signers` (and `MANIFEST` + `MANIFEST.sig`). TLS roots the trust in the domain — and the domain *is* the signing key's canonical domain, which is the point of `reflex.5`.
2. Run `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt`. `Good file signature for jnous` means: the holder of the `jnous` Ed25519 key signed *exactly those bytes*, namespace `file`.
3. Cross-check `shasum -a 256 <name>.txt` against the signed `MANIFEST` line — the file is covered by the manifest chain too, not just a loose detached sig.
4. Optionally pin the `jnous` public key from a second channel (the git mirror's copy, a prior archived fetch) to confirm `allowed_signers` wasn't swapped along with the file.

## Authority boundaries in play
- `authority.source` = the human; the signature proves it. The agent is not the authority (`boundary`) — it prepares the file and the exact `ssh-keygen -Y sign` invocation; the governor signs.
- Private key `~/.ssh/id_ed25519` is never read, copied, or used by Claude. Identity in `allowed_signers` is `jnous`.
- Canonical = `subtract.ing` (signing domain). Git hosts = mirror-only, pushed after.
- Machine roles: **Rousseau** drafts, signs-input-prep, verifies; **Surface** does the outward push; **Emile** not involved. Rousseau does not push outward.
- Human gates: (a) signing the new file and re-signing the manifest; (b) confirmation before the public publish. Warn before the sign step — it pops a passphrase prompt.
- Moving the signed bundle node-to-node = ordinary infra, no permission needed.

## One caveat to flag to the governor
An OpenSSH signature proves *authorship*, not *date* — it carries no trusted timestamp. "Verifiable a year from now" works for "jnous wrote this"; if "and wrote it on 2026-05-10" must also be provable, anchor it: a dated line inside the signed `MANIFEST`, the git mirror commit timestamp, or an RFC3161 timestamp over `<name>.txt.sig`. Worth deciding before publishing, not after.
