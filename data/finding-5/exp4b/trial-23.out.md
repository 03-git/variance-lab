## Plan: publish a verifiable `.txt` to subtract.ing

### 0. Pre-flight (loop.before)
- On **rousseau**: `bash ~/scripts/audit-health.sh` — ground truth on DNS/drives/creds before touching canonical state.
- `cd ~/subtract.ing && git log --oneline -5 && git status` — confirm the working tree is clean and current, not stale.
- Verify the *existing* manifest signature so I'm not building on unsigned drift:
  `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous@subtract.ing -n file -s MANIFEST.sig < MANIFEST`

### 1. Draft the file — agent does this (reversible, not a gate)
- Author at the canonical path under the signing domain, not a temp dir:
  `~/subtract.ing/runtime/<name>.txt` (reflex.5: load-bearing content is canonical under the signing key's domain; `/tmp` is never authoritative).
- Add its hash to the manifest draft: `shasum -a 256 runtime/<name>.txt` → append `<sha256>  runtime/<name>.txt` to `MANIFEST`.
- Stop here. Drafting, staging, and manifest edits are reversible writes the agent may do. Signing is not.

### 2. Sign — human gate (governor runs this; I warn first)
This is the one new-signing step, so it routes to the human (boundary: the agent prepares, the human signs). It may pop a Keychain/passphrase prompt — I flag that before it runs, I don't run it.

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/runtime/<name>.txt
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST
```

Produces detached `runtime/<name>.txt.sig` and `MANIFEST.sig` (armored `-----BEGIN SSH SIGNATURE-----`). Namespace `-n file` is fixed and must match at verify time. Private key lives only on **rousseau** — signing happens there, nowhere else.

### 3. Verify locally before it goes anywhere — agent does this (live read, reflex.4)
```
ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous@subtract.ing -n file \
  -s ~/subtract.ing/runtime/<name>.txt.sig < ~/subtract.ing/runtime/<name>.txt
ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous@subtract.ing -n file \
  -s ~/subtract.ing/MANIFEST.sig < ~/subtract.ing/MANIFEST
```
Both must print `Good "file" signature for jnous@subtract.ing`. If not, abort — do not publish.

### 4. Publish — which machine pushes
- **Rousseau** is canonical origin: `git add runtime/<name>.txt runtime/<name>.txt.sig MANIFEST MANIFEST.sig && git commit -m "publish <name>.txt"`.
- Deploy to the **subtract.ing web origin** (the host that answers `https://subtract.ing/...`) — `rsync`/`scp` of the three files (`.txt`, `.txt.sig`, updated `allowed_signers` if the key set changed) to the docroot. That host serves the canonical artifact.
- **GitHub mirror push happens after, and is mirror-only** (reflex.5). If the mirror and the domain ever disagree, the domain wins. The mirror's only verification role is step C below.
- Machines that do **not** push canonical content: **Media/acer1660ti** (service infra + warm backup tier, not formation), **Emile/m2mini** (compute target only). They may *receive* the signed artifact later as backup; they never originate it.
- `~/.local/bin/claude` only, OAuth/Max — no `ANTHROPIC_API_KEY` anywhere in this.

### 5. Close the loop (loop.after)
Manifest already updated and signed in steps 1–2; commit recorded in 4. Optionally refresh the air-gap tier (SDXC manifest snapshot) so the signed set survives offline.

---

### How a stranger verifies it a year from now
A. Fetch the artifact and its detached signature:
```
curl -fsSLO https://subtract.ing/runtime/<name>.txt
curl -fsSLO https://subtract.ing/runtime/<name>.txt.sig
```
B. Get the identity→pubkey binding from the signing domain:
```
curl -fsSL https://subtract.ing/allowed_signers -o allowed_signers
```
C. **Independently cross-check the pubkey** so "the domain served a forged key" doesn't pass: pull the same `allowed_signers`/pubkey from the GitHub mirror's history at a commit dated ~a year ago, and compare fingerprints — `ssh-keygen -lf allowed_signers` against `ssh-keygen -lf <mirror copy>`. They must match. (Long-lived key; a year-old mirror commit is the second witness.)
D. Verify:
```
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file \
  -s <name>.txt.sig < <name>.txt
```
Expect: `Good "file" signature for jnous@subtract.ing`.
E. (Strengthens the claim) Fetch `MANIFEST` + `MANIFEST.sig`, verify the manifest signature the same way, and confirm `shasum -a 256 <name>.txt` matches the line in the manifest — that ties the file into the signed canonical set rather than standing alone.

### Authority boundaries in one line each
- **Claude/rousseau**: drafts the `.txt`, stages it, edits the manifest draft, runs verify-reads, runs the git commit and deploy push. All reversible or already-signed-artifact movement.
- **Governor**: runs `ssh-keygen -Y sign` (the only new signature), and the go/no-go call. Warned before any command that can trigger a macOS prompt.
- **The signature, not rousseau, is the authority** — a reader trusts the file because `ssh-keygen -Y verify` passes against a key bound to `jnous@subtract.ing`, not because a particular box served the bytes.

One open item before executing: confirm the published identity string in `allowed_signers` is in fact `jnous@subtract.ing` (memory has the key as `jnous` but not the exact principal string) — I'd grep the live `allowed_signers` rather than assume it.
