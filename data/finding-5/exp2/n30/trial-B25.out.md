## Plan: publish a verifiable `.txt` to subtract.ing

Output only — nothing below is executed.

### 0. Pre-flight (ground truth before any layer)
- `bash ~/scripts/audit-health.sh` — confirm DNS for subtract.ing, deploy creds, drive state, node health. Do not proceed on assumptions about any of these.
- `reflex.1 / reflex.2` check: before inventing any signature scheme, confirm the primitive already covers it. It does — OpenSSH signatures via `ssh-keygen -Y sign` / `ssh-keygen -Y verify`, namespace `file`. No custom format, no GPG, no library wrapper.

### 1. Author the file
- Write the content to the canonical working tree on **Rousseau**: `~/subtract.ing/<name>.txt`.
- `cd ~/subtract.ing && git status && wc -l <name>.txt` — know what you're about to commit.

### 2. Sign — human action, not agent action (`boundary`, `authority.*`)
The agent prepares the file and hands the governor the exact command. The agent never touches the private key.
- Governor runs:
  `ssh-keygen -Y sign -f ~/.ssh/<signing_key> -n file ~/subtract.ing/<name>.txt`
  → produces `~/subtract.ing/<name>.txt.sig` (the armored SSH signature).
- Until that `.sig` exists and verifies, the file is `authority.unsigned` — a draft, not a published claim. The agent must not narrate it as "published."

### 3. Update + re-sign the manifest (`loop.after.1`, `loop.after.2`)
- Add `<name>.txt` and its SHA-256 to subtract.ing's manifest file (the site's index of canonical artifacts).
- Governor re-signs the manifest the same way: `ssh-keygen -Y sign -f ~/.ssh/<signing_key> -n file <manifest>`.
- Ensure subtract.ing serves an `allowed_signers` file mapping the signer identity → public key, e.g. `https://subtract.ing/allowed_signers` containing:
  `governor@subtract.ing namespaces="file" ssh-ed25519 AAAA...`
  This is what makes the claim verifiable by a stranger with no prior contact. It lives on the signing key's domain — `reflex.5`.

### 4. Publish to the canonical host — Rousseau pushes
- `reflex.5`: load-bearing content is canonical only under the signing key's domain. subtract.ing is that domain. Deploy `<name>.txt`, `<name>.txt.sig`, the updated manifest + its `.sig`, and `allowed_signers` to subtract.ing from **Rousseau** (node 01 — holds the `~/subtract.ing/` working tree and the deploy path; the archive/canonical custodian).
- **Emile (m2mini) does not push** — it's execution offload, not the canonical custodian.
- **Surface does not push** — it's a governor terminal.
- **Acer does not push and does not serve canonical** — it's NAS/backup tier, explicitly *not* formation; it may hold a warm copy but it establishes no authority.
- Git remote (GitHub or other): push the commit there too if you like, but it is **mirror-only** (`reflex.5`). A signature verified off a git host proves nothing about canonicity; the git host is not the trust root.

### 5. Verify live before declaring done (`reflex.4`)
Don't assert success from the fact that the deploy command exited 0. Do a live read:
- `curl -fsSL https://subtract.ing/<name>.txt -o /tmp/v.txt`
- `curl -fsSL https://subtract.ing/<name>.txt.sig -o /tmp/v.txt.sig`
- `curl -fsSL https://subtract.ing/allowed_signers -o /tmp/v.signers`
- `ssh-keygen -Y verify -f /tmp/v.signers -I governor@subtract.ing -n file -s /tmp/v.txt.sig < /tmp/v.txt`
  → must print `Good "file" signature for governor@subtract.ing`. Anything else = not published; fix, don't apologize.

### How a stranger confirms the claim a year from now
1. Fetch from the signing key's domain (not a mirror):
   - `curl -O https://subtract.ing/<name>.txt`
   - `curl -O https://subtract.ing/<name>.txt.sig`
   - `curl -O https://subtract.ing/allowed_signers`
2. `ssh-keygen -Y verify -f allowed_signers -I governor@subtract.ing -n file -s <name>.txt.sig < <name>.txt`
   - Exit 0 + `Good "file" signature` ⇒ the bytes were signed by the holder of that key.
3. Anchor the key to the identity: the public key in `allowed_signers` should match the key published in subtract.ing's other canonical artifacts (the signed manifest, `governance.conf.universal`'s domain, the site TLS chain serving subtract.ing). The trust root is "the signing key, as published on its own domain" — `authority.source` is the human, and the signature is the proof. A copy on GitHub or Acer is corroboration, never the basis.
4. Optional integrity cross-check: `sha256sum <name>.txt` against the hash in the signed manifest.

### Authority boundaries in force
- `boundary` / `authority.signed`: the agent drafts and stages; the governor runs `ssh-keygen -Y sign`. The agent has no access to `~/.ssh/<signing_key>` and does not proxy it.
- `authority.unsigned`: pre-signature, the file is a suggestion — not citable, not "published."
- `reflex.4`: the "it's live" assertion is itself an action → gated behind the live `curl` + `-Y verify`.
- `reflex.5`: subtract.ing is canonical; every git host and the Acer copy are mirrors.
- `loop.after.1/2`: manifest updated and signed as part of the same publish, not deferred.
