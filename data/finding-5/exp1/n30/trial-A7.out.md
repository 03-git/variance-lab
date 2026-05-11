## Plan: publish a verifiable `.txt` to subtract.ing

### Step 0 — reflexes before anything (gates, not steps I can skip)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, the m1studio:8087 listener that serves `subtract.ing`. Don't touch the web root if the audit shows drift.
- **reflex.2:** the signature format is already settled — OpenSSH signatures via `ssh-keygen -Y sign` / `-Y verify` against an `allowed_signers` file. Do not invent a manifest/signature scheme.
- **reflex.5:** `subtract.ing` (the HTTPS origin under the signing key's domain) is canonical. GitHub / any git remote is mirror-only and carries no authority.
- **boundary:** I prepare; the governor signs. Until a verifying `.sig` exists, the `.txt` is `authority.unsigned` → a draft, not publishable.

### Step 1 — draft and stage (Rousseau, agent may do this — reversible)
- Write the file into the `subtract.ing` staging tree on Rousseau (canonical content lives here, e.g. `~/subtract.ing/<name>.txt` — confirm the actual web-root path from the running server config, don't assume).
- Normalize: UTF-8, LF, trailing newline — signatures are over exact bytes; a later CRLF/whitespace fixup breaks verification "a year from now."
- Record the digest: `sha256sum <name>.txt`.

### Step 2 — pre-publish loop (loop.before.1–3)
- `ssh-keygen -Y verify` the **current** manifest signature on Rousseau's canonical tree. If it fails or the tree has unsigned drift, stop and surface it — don't stack a new file on an unverified base.
- Present to the governor: the new file, its sha256, the diff to the manifest. Human decides: sign / continue / abort.

### Step 3 — sign (governor only — this is the human gate, NOT the agent)
On the governor's machine, with the private key (`~/.ssh/id_ed25519` or whichever key's pubkey is in the published `allowed_signers`):
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file <name>.txt
```
→ produces `<name>.txt.sig` (an `SSH SIGNATURE` PEM block). Namespace `file` is the convention here; use whatever namespace the rest of `subtract.ing` already uses — check an existing `.sig`. The agent does not run this command and does not hold the key.

### Step 4 — update and re-sign the manifest (loop.after.1–2)
- Add `<name>.txt` + its sha256 to `subtract.ing`'s manifest (the file that lists every canonical artifact).
- Governor re-signs the manifest the same way: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file MANIFEST` → `MANIFEST.sig`.
- This is what lets a verifier confirm the file is *part of the canon*, not just a bytes-blob someone signed once.

### Step 5 — publish to the canonical origin (Rousseau pushes; nothing else does)
- Place `<name>.txt`, `<name>.txt.sig`, updated `MANIFEST`, `MANIFEST.sig` into the live `subtract.ing` web root on **Rousseau** (the node behind `subtract→m1studio:8087`). Reload/verify the server picks them up.
- Ensure `https://subtract.ing/allowed_signers` is current and contains the signing identity → pubkey line. This file is the trust anchor and is itself canonical under the domain — if the signer's key isn't already published there, that change goes through the same sign-the-manifest loop.
- **reflex.4:** immediately do a live read-back: `curl -fsSL https://subtract.ing/<name>.txt | sha256sum` and confirm it equals Step 1's digest.

### Step 6 — mirrors (no authority — do not confuse with publishing)
- Git remote (GitHub or similar): commit/push the same files. Mirror-only; if it ever disagrees with `subtract.ing`, the origin wins. Useful only as an independent timestamped copy.
- Emile (`ssh m2mini`) and Media (`ssh acer1660ti`) pull the tree on their next `discover.sh`/sync — warm copies, not push targets.
- Optional durability: add `<name>.txt` + manifest snapshot to the SDXC air-gap tier (per the SDXC refresh routine). Belt-and-suspenders for the "still verifiable in a year" requirement.

### Step 7 — how a stranger verifies it a year from now
```
curl -fsSLO https://subtract.ing/<name>.txt
curl -fsSLO https://subtract.ing/<name>.txt.sig
curl -fsSLO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers \
  -I <identity-string-from-allowed_signers> \
  -n file -s <name>.txt.sig < <name>.txt
```
Exit status `0` and `Good "file" signature for <identity>` ⇒ the file's bytes were signed by the key `subtract.ing` publishes for that identity. Then:
- Fetch `MANIFEST` + `MANIFEST.sig`, run the same `ssh-keygen -Y verify`, and check `<name>.txt`'s sha256 appears in it ⇒ the file is part of the canon, not a one-off.
- Cross-check the git mirror's commit date and the SDXC manifest for an independent timestamp.

Why it survives a year: the signature is over content bytes with no expiry; the only moving part is the `allowed_signers` mapping served over TLS from the signing domain — as long as that's intact (and it's covered by the signed manifest + air-gap snapshot), verification still passes. Key rotation would require keeping the old pubkey line in `allowed_signers`, so plan for append-not-replace there.

### Authority boundaries, condensed
- **Agent (me):** audit, draft, stage, hash, prepare manifest diff, run `-Y verify`, do the read-back, push files to the web root, push mirrors. All reversible / verification-only.
- **Governor (human):** every `ssh-keygen -Y sign` invocation, and the sign/continue/abort decision in Step 2. Non-delegable — `authority.unsigned → do not act`; `boundary: the agent prepares, the human signs`.
- **Pushes to canon:** Rousseau (m1studio) only. **Does not push:** Surface (terminal, no web root), Emile, Media — they mirror/pull. Git host mirrors, never authoritative.

One thing to confirm before doing this for real: the exact web-root path and the signature **namespace** already in use on `subtract.ing` — read an existing `.sig` rather than assuming `-n file`.
