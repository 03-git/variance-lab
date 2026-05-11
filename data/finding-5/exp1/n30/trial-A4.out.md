## Plan: publish a verifiable `.txt` to subtract.ing

Nothing below is executed. Paths marked *(confirm)* are placeholders the governor pins before I draft the literal command. The new‑signing step is the only human gate; everything else I run.

### 0. Pre‑flight (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS/drives/node state.
- `git -C ~/subtract.ing status` and `git -C ~/subtract.ing log --oneline -5` — confirm the working tree is clean and matches the mirror.
- Verify the current head‑of‑chain signature so I'm not building on unsigned drift:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n subtract.ing -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST`
- If anything fails to verify or the tree has unexplained changes, stop and surface it to the governor (loop.before.2/3). Do not proceed past unresolved foundation.

### 1. Draft (agent, no gate)
- Write `~/subtract.ing/<name>.txt` on **Rousseau** — Rousseau is canonical for formation human‑authored work; subtract.ing is served from this node (m1studio). Pure preparation, no permission needed (the agent prepares).

### 2. Ensure the verifier's anchor exists
- `~/subtract.ing/allowed_signers` must contain the governor's signing identity, one line:
  `jnous namespaces="subtract.ing" ssh-ed25519 AAAA…`
- This file is the key→person binding. It has to live **under the signing key's domain** (https://subtract.ing/allowed_signers), not only in the git mirror (reflex.5). If it's already published and unchanged, reuse it.

### 3. Sign — HUMAN GATE (governor runs this, not the agent)
- I prepare the exact command; the governor executes it:
  `ssh-keygen -Y sign -f ~/.ssh/jnous`*(confirm key path)*` -n subtract.ing ~/subtract.ing/<name>.txt`
  → produces `~/subtract.ing/<name>.txt.sig` (armored SSH signature blob).
- `-n subtract.ing` pins the signature to this namespace so it can't be replayed as authority in another domain.
- Authority boundary: `authority.source = the human`; the signature is what proves it. I do not hold or use the signing key. (reflex.2: use `ssh-keygen -Y sign/verify` — do not invent a signature format.)

### 4. Verify locally before publishing (reflex.4 — the publish is the action)
- `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n subtract.ing -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt`
- Must print `Good "subtract.ing" signature for jnous`. If not, abort — do not publish.

### 5. Manifest update (loop.after) — second human gate
- Append `<name>.txt` + its `sha256sum` to `~/subtract.ing/MANIFEST` *(confirm manifest filename)*.
- Governor re‑signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/jnous -n subtract.ing ~/subtract.ing/MANIFEST` → new `MANIFEST.sig`.
- I verify it (`ssh-keygen -Y verify …` as in step 4).

### 6. Publish (agent — infra, not a gate: pushing already‑signed artifacts is just infra)
- **Canonical, from Rousseau only:** deploy `<name>.txt`, `<name>.txt.sig`, `allowed_signers`, `MANIFEST`, `MANIFEST.sig` into the docroot served at https://subtract.ing/ (rsync/cp into the served path *(confirm)*, reload the server). Rousseau (01) is the signing key's domain host — it publishes canonical.
- **Mirror, from Rousseau:** `git -C ~/subtract.ing add …; git commit -m "publish <name>.txt"; git push` to the GitHub mirror. Mirror‑only: if the git host ever disagrees with subtract.ing, subtract.ing wins (reflex.5).
- **Who does not push canonical:** Emile (pull‑mirror of scripts/, no canonical push), Media/acer1660ti (warm backup tier, not formation), Surface (governor terminal). They may receive the signed bundle as backups; they don't originate the publish.

### 7. How a stranger confirms authorship a year later
1. Fetch `https://subtract.ing/<name>.txt`, `…/<name>.txt.sig`, `…/allowed_signers` (and optionally `MANIFEST` + `MANIFEST.sig`).
2. Corroborate that the public key in `allowed_signers` is genuinely the author's, from **more than one channel the key owner controls** — e.g. a DNS TXT/SSHFP record under `subtract.ing`, the same key present in git history from over a year prior, or any other independent self‑disclosure. The signature alone proves "the holder of this key signed these exact bytes"; the key→person binding is the trust root and must not rest on a single source (correlated assertions aren't verification).
3. Run, with OpenSSH ≥ 8.0:
   `ssh-keygen -Y verify -f allowed_signers -I jnous -n subtract.ing -s <name>.txt.sig < <name>.txt`
   `Good "subtract.ing" signature for jnous` ⇒ the file is byte‑for‑byte what jnous signed; any later edit breaks it.
4. (Optional, for "is this part of the canonical set") verify `MANIFEST.sig` the same way and check `<name>.txt`'s sha256 is listed.

### Caveat to flag to the governor
SSH signatures carry no trusted timestamp. "Authored by jnous" is fully covered by step 7; "authored *on date X*" is only weakly anchored by the git mirror commit date and the signed manifest. If the date needs to be provable, add an OpenTimestamps proof on the file hash at publish time — additive, optional, not required for the authorship claim.

### Authority boundaries, condensed
- **Agent:** drafts the file, drafts the manifest entry, prepares the exact `sign` commands, runs every `ssh-keygen -Y verify`, runs every deploy/push of already‑signed artifacts.
- **Governor (human gate):** runs `ssh-keygen -Y sign` for the new `.txt` and for the updated `MANIFEST`. That's it. The agent prepares; the human signs.
- **Canonical push origin:** Rousseau. Mirror push: Rousseau. Emile / Media / Surface: not canonical publishers.
