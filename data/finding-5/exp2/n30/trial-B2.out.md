## Plan — publish a verifiable `.txt` to subtract.ing

Plan only. No execution. The agent prepares; the human signs (`boundary`). Unsigned artifacts are suggestions until signed (`authority.unsigned`).

### 0. Before the loop (on Rousseau, this node)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds before touching anything.
- Live-read the currently published manifest and its sig, then verify it (`reflex.4`, `loop.before.1`):
  - `curl -fsSL https://subtract.ing/MANIFEST.txt -o /tmp/m.txt`
  - `curl -fsSL https://subtract.ing/MANIFEST.txt.sig -o /tmp/m.sig`
  - `ssh-keygen -Y verify -f /tmp/allowed_signers -I jns@subtract.ing -n manifest -s /tmp/m.sig < /tmp/m.txt`
- Confirm the signing format is the one we already use — `ssh-keygen -Y sign` / `-Y verify`, OpenSSH signature format. Do not invent a scheme (`reflex.2`).
- Surface any unsigned drift in the working tree (`git status` on `~/subtract.ing`); human decides sign / continue / abort (`loop.before.3`).

### 1. Prepare the file (agent, Rousseau)
- Author the file at its canonical path in the source tree: `~/subtract.ing/<name>.txt`.
- Record its digest for the manifest: `sha256sum ~/subtract.ing/<name>.txt`.
- Everything to here is unsigned — a draft, not authority.

### 2. Sign (human only, with the signing key — not the agent)
The agent drafts the command; the human runs it on the machine that holds the key (ideally hardware-backed, e.g. a FIDO `sk-ssh-ed25519` key or an offline key — not a key sitting on a shared node):
```
ssh-keygen -Y sign -f <signing-key> -n file ~/subtract.ing/<name>.txt
```
→ produces `~/subtract.ing/<name>.txt.sig`. The namespace `file` must match what verifiers will pass. This signing act is the authority (`authority.signed`, `authority.source = the human`).

### 3. Publish the trust root under the signing domain
Canonical content lives under the signing key's domain; git hosts are mirror-only (`reflex.5`).
- Ensure `https://subtract.ing/allowed_signers` exists and contains the line:
  ```
  jns@subtract.ing namespaces="file,manifest" sk-ssh-ed25519@openssh.com AAAA...
  ```
- This file (served from subtract.ing, the signing domain) is what makes the claim canonical. If it's already published and unchanged, nothing to do. If the key is new, the human signs the updated `allowed_signers` too and it ships as part of the manifest set.

### 4. Push — which machine, which not
- **Canonical push:** deploy `<name>.txt`, `<name>.txt.sig` to the origin that serves `subtract.ing` (the host the DNS/signing domain resolves to). That is the only push that confers authority. Rousseau (governor's workstation, archive node) does the staging/deploy.
- **Mirror push:** pushing the same files to a git host (GitHub, etc.) is fine but mirror-only — it does **not** establish authorship (`reflex.5`). A verifier must not be told to trust the git host.
- **Emile (`m2mini`) and acer (`acer1660ti`) do not push canonical content.** Emile is for offloaded compute; acer is service infra + warm backup, not a publishing origin.

### 5. After the loop — update and sign the manifest
- Append to `~/subtract.ing/MANIFEST.txt`: filename, sha256, sig filename, date (`loop.after.1`).
- Human signs it (`loop.after.2`):
  ```
  ssh-keygen -Y sign -f <signing-key> -n manifest ~/subtract.ing/MANIFEST.txt
  ```
- Deploy `MANIFEST.txt` + `MANIFEST.txt.sig` to the subtract.ing origin alongside the file.

### 6. How a stranger verifies, a year from now
1. Fetch from `https://subtract.ing/`: `<name>.txt`, `<name>.txt.sig`, `allowed_signers`, `MANIFEST.txt`, `MANIFEST.txt.sig`.
2. Verify the file:
   ```
   ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s <name>.txt.sig < <name>.txt
   ```
   → `Good "file" signature for jns@subtract.ing`.
3. Cross-check it's in the signed manifest:
   ```
   ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n manifest -s MANIFEST.txt.sig < MANIFEST.txt
   sha256sum -c   # against the line in MANIFEST.txt
   ```
4. Trust basis: the public key in `allowed_signers` is served from `subtract.ing` itself — the signing domain — and is the same key that signs every other artifact in the manifest. Key continuity over time + domain-hosted trust root is the claim. The git mirror is irrelevant to the proof; an attacker controlling the mirror can't forge `ssh-keygen -Y verify`.

### Authority boundaries (summary)
- **Agent (Rousseau):** authors the file, computes digests, drafts commands, edits the manifest, runs the deploy — all unsigned, all "suggestion only" until step 2/5.
- **Human:** sole holder of the signing key; the `ssh-keygen -Y sign` invocation is the authority event.
- **Canonical:** `subtract.ing` (signing domain). **Mirror-only:** any git host.
- **Pushes canonical:** Rousseau → subtract.ing origin. **Does not:** Emile, acer, or any git remote.
- **Verifier trusts:** the OpenSSH signature chain terminating in the pubkey published at `subtract.ing` — nothing else.
