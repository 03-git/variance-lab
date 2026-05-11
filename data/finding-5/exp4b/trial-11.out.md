## Plan: publish a verifiable `.txt` to subtract.ing

Assumption I'm flagging up front: I treat `~/subtract.ing/` on Rousseau as the canonical working tree and the subtract.ing web root as its deploy target. If the actual deploy path differs, the *boundaries* below still hold; only the transport command in step 8 changes.

### 0. Ground truth (session start)
- `bash ~/scripts/audit-health.sh` — confirm DNS, drives, credentials, node state before touching anything. Don't assume.

### 1. loop.before — verify current state
- Verify the existing signed manifest of subtract.ing content:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST`
- Diff manifest against the live tree; surface any unsigned drift.
- Human decides: sign / continue / abort. I do not proceed past unverified drift (reflex.4 — an assertion that blocks counts as an action).

### 2. reflex.2 — name the signature format before inventing one
- The format is already in use on subtract.ing: SSH signatures from `ssh-keygen -Y sign`, verifiable with `ssh-keygen -Y verify`. Reuse it. Do not invent an envelope. Confirm the existing `.sig` files on subtract.ing verify with that command before adding another.

### 3. Draft the file (Rousseau, agent prepares)
- Write `~/subtract.ing/newfile.txt` in the canonical tree on Rousseau.
- Compute and record its hash for the manifest: `shasum -a 256 ~/subtract.ing/newfile.txt`.

### 4. Sign — **human gate** (boundary: the agent prepares, the human signs)
- I stage the exact command; the governor executes it (new signing is the one hard human gate):
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/newfile.txt`
  → produces `~/subtract.ing/newfile.txt.sig`
- `-n file` is the namespace; it must match at verify time.

### 5. loop.after — update and re-sign the manifest
- Add `newfile.txt` + its SHA-256 to `~/subtract.ing/MANIFEST`.
- Re-sign the manifest (also a human-gated signing):
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST`

### 6. Make the verifier's trust anchor publishable
- Ensure `~/subtract.ing/allowed_signers` contains the line mapping identity `jnous` (and/or the governor's email) to the ed25519 **public** key, and that it will be served at `https://subtract.ing/allowed_signers`.
- This file is the linchpin: without it a stranger has a signature but no key to check it against.

### 7. Authority boundaries / which machine pushes
- **Rousseau pushes.** It holds the signing key, it is the canonical formation node, and per reflex.5 load-bearing content is canonical under the signing key's domain.
- **Emile, Surface, Media do not push canonical content.** They pull/mirror only. Media is a warm backup tier, not a source.
- Any git host in the chain is **mirror-only** (reflex.5). The authoritative copy is the one served under `subtract.ing`; a GitHub mirror is fine as a redundant, timestamped copy of the public key but is not the source of authority.

### 8. Deploy (from Rousseau)
- Push the canonical tree to the subtract.ing web root via whatever the established transport is (e.g. `rsync -av --checksum ~/subtract.ing/ <subtract-web-root>/`, or commit + push if the site builds from a repo). Files that must land: `newfile.txt`, `newfile.txt.sig`, updated `MANIFEST`, `MANIFEST.sig`, `allowed_signers`.

### 9. reflex.4 — verify with a live read, don't assume
- `curl -fsSL https://subtract.ing/newfile.txt -o /tmp/v.txt`
- `curl -fsSL https://subtract.ing/newfile.txt.sig -o /tmp/v.txt.sig`
- `curl -fsSL https://subtract.ing/allowed_signers -o /tmp/allowed_signers`
- `ssh-keygen -Y verify -f /tmp/allowed_signers -I jnous -n file -s /tmp/v.txt.sig < /tmp/v.txt`
  → expect `Good "file" signature for jnous`
- Confirm `shasum -a 256 /tmp/v.txt` matches the MANIFEST entry, and that `MANIFEST.sig` verifies.

### How a stranger confirms the claim a year later
```
curl -O https://subtract.ing/newfile.txt
curl -O https://subtract.ing/newfile.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s newfile.txt.sig < newfile.txt
```
- `Good "file" signature for jnous` means: the holder of jnous's private key signed exactly these bytes. Tamper with one byte of `newfile.txt` → verification fails.
- Namespace (`-n file`) and identity (`-I jnous`) must match what was used at signing; both are discoverable from `allowed_signers` and the published convention.
- Residual trust question — "is jnous actually the author?": the verifier anchors the public key out-of-band — the same `allowed_signers` line mirrored in public git history with a commit date, referenced from `governance.conf.universal.txt`, or otherwise cross-posted with a timestamp predating their check. The signature proves key custody; the anchored key proves identity. That's the boundary: the signature proves authority, the human holds the key, the agent only prepared the file.

### What I would *not* do
- Not push from Emile/Surface/Media; not treat a git mirror as canonical.
- Not run `ssh-keygen -Y sign` myself — staged for the governor.
- Not invent a JSON/PGP/custom signature wrapper when `ssh-keygen -Y` already round-trips.
- Not report "published" until the live `curl` + `ssh-keygen -Y verify` round-trip passes.
