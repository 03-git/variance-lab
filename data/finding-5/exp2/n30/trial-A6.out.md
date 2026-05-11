## Plan: publish a verifiable `.txt` to subtract.ing

### 0. Reflex checks before touching anything
- **reflex.2** — signature format is not invented: `ssh-keygen -Y sign` / `ssh-keygen -Y verify` (SSH signatures + `allowed_signers`) is the format. Confirm the *namespace* by reading an existing artifact rather than guessing — `ssh-keygen -Y check-novalidate -n <ns> -s some-existing.txt.sig < some-existing.txt` against a current `.sig` in `~/subtract.ing/`. Match whatever that uses (documented default is `file`).
- **reflex.5** — the canonical copy lives under the subtract.ing HTTPS origin. The GitHub remote is a **mirror only**; pushing there is not "publishing."
- **reflex.4** — before asserting current state (e.g. "the live `allowed_signers` contains key X"), do a live read: `curl -fsS https://subtract.ing/allowed_signers`. Don't act on memory of it.
- **loop.before** — verify the last signature in the working tree, surface any unsigned drift, then the governor decides: sign / continue / abort.

### 1. Draft (Rousseau / node 01 — this machine)
- Write the file into the canonical working tree: `~/subtract.ing/<name>.txt`.
- This is a reversible staging write — done without asking.
- Prepare, but do **not** run, the exact signing command for the governor (next step). Agent prepares; the human signs (`boundary`).

### 2. Sign — human gate (governor, on the machine holding the private key)
- This is the one step that is a human gate (new signing). **Warn first**: `ssh-keygen -Y sign` will prompt for the key passphrase (macOS dialog / terminal prompt).
- Governor runs, from `~/subtract.ing/`:
  ```
  ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file <name>.txt
  ```
  → produces `<name>.txt.sig`. The signing identity is the governor's key as listed in `allowed_signers` (principal `jnous`).
- Agent does not substitute, retry, or script around this. If it fails: flag and stop.

### 3. Update + sign the manifest (loop.after)
- Add `<name>.txt` (and its hash) to the subtract.ing manifest.
- Re-sign the manifest the same way: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file <manifest>`.

### 4. Publish — which machine pushes
- **Push to the subtract.ing HTTPS origin** the three artifacts: `<name>.txt`, `<name>.txt.sig`, and (if not already current) `allowed_signers`. That origin host is the only "publish." If I'm not certain which node backs the origin, I verify with a live read before assuming — I don't push canonical content to a box on a hunch.
- **Rousseau** drafts and stages; it pushes to the canonical origin only if it *is* the origin host or holds deploy access to it.
- **Surface** (governor terminal) executes the deploy if that's the path — Rousseau drafts, Surface executes.
- **Emile** does **not** push canonical content — it's a pull-mirror.
- **Media (acer1660ti)** does **not** push canonical content — it's service infra / warm-backup tier, not formation.
- The GitHub remote may receive a mirror push afterward; that's corroboration, not the source of truth (reflex.5).
- Optional, air-gap tier: refresh the SDXC / FROZEN snapshots with the new artifact + updated manifest.

### 5. How a stranger verifies, a year out
1. Fetch over HTTPS from the canonical domain:
   ```
   curl -fsSO https://subtract.ing/<name>.txt
   curl -fsSO https://subtract.ing/<name>.txt.sig
   curl -fsSO https://subtract.ing/allowed_signers
   ```
2. Verify:
   ```
   ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
   ```
   → `Good "file" signature for jnous` means the file was signed by the key that subtract.ing publishes as the governor's. Authorship confirmed.
3. Trust anchor: the `allowed_signers` served **under the subtract.ing domain** — that domain binding is what makes the principal meaningful (reflex.5). The GitHub mirror's copy of the `.sig` should byte-match; if it doesn't, the domain copy wins.
4. Why it still works in a year: SSH signatures are offline-verifiable and don't expire. The only requirement is that the public key in the published `allowed_signers` is still the governor's signing key. If the key is ever rotated, the old `allowed_signers` (or a `valid-before` entry) must remain published so historical signatures stay verifiable.

### Authority boundaries in force
- `authority.signed` → a verifier (or this agent) acts on the file only after `ssh-keygen -Y verify` passes; until then it's a draft, not canon.
- `boundary` / human-gate scope → the agent writes the file and the command; the governor runs the signing. Pushing already-signed artifacts between nodes afterward is plain infra work — no gate.
- Use plain language ("the signature verifies / it doesn't") — the ceremony words apply only because `ssh-keygen -Y verify` is genuinely in this loop.
