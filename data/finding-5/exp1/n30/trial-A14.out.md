## Plan: publish a verifiable `.txt` to subtract.ing

### 0. Ground truth (before anything)
`bash ~/scripts/audit-health.sh` — confirm DNS for subtract.ing, the signing key is present, LEDGER/canonical drive mounted, node state sane. Don't proceed on assumptions.

### 1. Pre-act loop (`loop.before`)
- `git -C ~/subtract.ing log --oneline -5` and `git -C ~/subtract.ing status` — see what's already there, surface uncommitted drift.
- `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I <identity> -n file -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST` — confirm the current manifest signature is good before extending it. If it fails, stop and surface it.
- Governor decides: sign / continue / abort.

### 2. Draft (rousseau; agent does this)
- Write the file into the canonical working tree on rousseau: `~/subtract.ing/<name>.txt`. Rousseau holds canonical; this is a reversible staging write, no gate.
- Compute `shasum -a 256 ~/subtract.ing/<name>.txt` and keep the digest for the manifest.
- Agent prepares the exact `ssh-keygen -Y sign` command but does **not** run it.

### 3. Sign — human gate (`boundary`, `authority.source`)
Governor runs, on rousseau:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file ~/subtract.ing/<name>.txt
```
→ produces `~/subtract.ing/<name>.txt.sig`. New signing is the one hard human gate — the agent never does this. (`-n file` namespace must match what verifiers use.)

Confirm the `jnous` public key + its identity line are present in `~/subtract.ing/allowed_signers`, which must itself be served from the subtract.ing domain so a stranger can fetch it.

### 4. Manifest update + re-sign (`loop.after.1/2`)
- Append `<name>.txt  <sha256>` to `~/subtract.ing/MANIFEST`.
- Governor re-signs: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file ~/subtract.ing/MANIFEST` → `MANIFEST.sig`.

### 5. Publish — which machine pushes
- **Rousseau pushes.** It's the canonical holder. Deploy to the subtract.ing web root: `<name>.txt`, `<name>.txt.sig`, updated `MANIFEST`, `MANIFEST.sig`, and verify `allowed_signers` is reachable (e.g. `https://subtract.ing/allowed_signers`). Moving already-signed artifacts is plain infra, not a gate.
- Git host (GitHub etc.): mirror push is fine but **mirror-only** (`reflex.5`) — never cite it as the authority.
- **Surface does not push** — pull-only consumer of `~/human/`, not a canonical writer.
- **Emile does not push** — pull-mirror of `~/scripts` only.
- **Media/acer does not push** — service infra / warm backup tier, not canonical.

### 6. How a stranger verifies (a year later)
Fetch from the **signing key's domain**, not a git mirror:
```
curl -fsSLO https://subtract.ing/<name>.txt
curl -fsSLO https://subtract.ing/<name>.txt.sig
curl -fsSLO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <identity> -n file -s <name>.txt.sig < <name>.txt
```
Expect: `Good "file" signature for <identity> with ED25519 key SHA256:...`. Then cross-check:
```
curl -fsSLO https://subtract.ing/MANIFEST
curl -fsSLO https://subtract.ing/MANIFEST.sig
ssh-keygen -Y verify -f allowed_signers -I <identity> -n file -s MANIFEST.sig < MANIFEST
shasum -a 256 <name>.txt   # must equal the line in MANIFEST
```
Trust chain: `allowed_signers` (served under subtract.ing) binds the ed25519 key to the identity → the `.sig` proves that key signed exactly these bytes → the signed `MANIFEST` proves the file belongs to the published set. If they pulled the file from a git mirror, that proves nothing on its own — re-fetch from the canonical domain and re-run verify.

### Authority boundaries summary
- Agent may: run `audit-health.sh`, verify existing signatures, draft `<name>.txt`, stage the manifest line, push *already-signed* artifacts from rousseau, mirror to git.
- Agent may not: run `ssh-keygen -Y sign` (new signing = human gate); treat any unsigned/un-verified state as authoritative; treat the git mirror as canonical.
