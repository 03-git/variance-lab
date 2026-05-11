# Plan — publish a verifiable signed `.txt` to subtract.ing

Not executing. Steps, tools, boundaries below.

## 0. Preconditions — Rousseau, agent prepares
- `bash ~/scripts/audit-health.sh` — ground truth on subtract.ing DNS, the `subtract` service on `m1studio:8087`, drive/credential state. Don't proceed on a red.
- `loop.before`: verify the *current* canonical manifest signature before touching anything —
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I <principal> -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST`
  Surface any unsigned drift to the governor; he decides sign/continue/abort.

## 1. Draft — Rousseau, agent (Write/Edit are available)
- Author the file at the canonical web root, e.g. `~/subtract.ing/runtime/<name>.txt`. Confirm the actual webroot from audit-health output; don't assume the path.
- Freeze the content. Any post-signature byte change invalidates the signature — finalize first.

## 2. Sign — human gate, agent STOPS and hands off
This is `boundary` / `reflex.2` / `loop.before.3`. The agent does not hold the key and does not run these. Warn the governor first (popup/blocking-prompt courtesy), then he runs, on the machine holding the signing key:
- `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/runtime/<name>.txt`
  → emits `~/subtract.ing/runtime/<name>.txt.sig` (armored `SSH SIGNATURE` block). Namespace `file` is the convention — keep it consistent.
- Ensure the public half is in the canonical `~/subtract.ing/allowed_signers`:
  `<principal e.g. jnous@subtract.ing>  file  ssh-ed25519  AAAAC3Nza...`
  If this is a *new* signing key, admitting it to `allowed_signers` is itself a human decision (publishing the trust root), not an agent action.

## 3. Verify locally before publish — Rousseau, agent (it's a verifying read, reflex.4)
- `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I <principal> -n file -s ~/subtract.ing/runtime/<name>.txt.sig < ~/subtract.ing/runtime/<name>.txt`
- Expect: `Good "file" signature for <principal>`. Anything else → stop, report.

## 4. Update + re-sign the manifest — `loop.after`
- Append the new file and its hash to the canonical manifest (`MANIFEST` / `SHA256SUMS`): `sha256sum runtime/<name>.txt >> MANIFEST` (or the existing format).
- Governor re-signs: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST` → `MANIFEST.sig`. Human gate again — agent doesn't sign.

## 5. Publish — Rousseau pushes; agent may do this (pushing already-signed artifacts is infra, not a gate)
- Deploy the bundle together from **Rousseau (m1studio)** — the node serving the canonical `subtract` site on `:8087`: `<name>.txt`, `<name>.txt.sig`, updated `allowed_signers`, `MANIFEST`, `MANIFEST.sig`. Mechanism is whatever that service consumes (`rsync` to webroot, or `git push` to the deploy remote it serves) — ends up live at `https://subtract.ing/runtime/<name>.txt` and `…/<name>.txt.sig`.
- **Does not push:** Emile (`m2mini`) is compute-offload, not a publisher. Media (`acer1660ti`) is explicitly *not formation* — service infra + warm-backup tier, never canonical, never the publish point. A GitHub mirror, if any, is `mirror-only` (reflex.5) — fine to push, but it is not the authority for this claim.
- Post-deploy live-read (reflex.4, assertions count as actions): `curl -fsSL https://subtract.ing/runtime/<name>.txt`, `curl -fsSL https://subtract.ing/runtime/<name>.txt.sig`, re-run the `ssh-keygen -Y verify` from step 3 against the fetched copies.

## 6. How a stranger verifies, a year later
1. `curl -fsSLO https://subtract.ing/runtime/<name>.txt` and `…/<name>.txt.sig`
2. `curl -fsSLO https://subtract.ing/allowed_signers` — the trust root, fetched from the **signing key's own domain**. Per reflex.5 a git/GitHub copy would not be authoritative for this; subtract.ing is.
3. `ssh-keygen -Y verify -f allowed_signers -I <principal> -n file -s <name>.txt.sig < <name>.txt`
   → `Good "file" signature for <principal>` ⇒ authorship confirmed under `authority.signed`.
4. Cross-checks: `ssh-keygen -lf allowed_signers` fingerprint against any other channel the governor has published the key on; and `ssh-keygen -Y verify … -s MANIFEST.sig < MANIFEST` to confirm `<name>.txt`'s hash is in the signed canonical set (guards against a file slipped in unsigned).
- Time isn't a factor: an SSH signature carries no timestamp; verification is over the key, not the date, so "a year from now" verifies identically. If a date is ever needed, the manifest's signed history (mirror git commits, or a dated `MANIFEST` line) supplies it.

## Authority boundaries, condensed
- **Agent prepares:** draft, stage, local verify-reads, push already-signed artifacts from Rousseau, curl-verify the live copy.
- **Human signs — the only gate:** `ssh-keygen -Y sign` on the file *and* the manifest; admitting any new key to `allowed_signers`. The signature is what proves authorship; the agent never holds the key.
- **Machines:** Rousseau (m1studio) drafts and publishes. Emile = compute offload, never publishes. Media/acer = service infra + warm backup, never canonical. Git hosts = mirror-only.
