## Plan: publish a verifiable `.txt` to subtract.ing

### 0. Reflex checks before touching anything
- **reflex.5 (canonical → signing domain):** the file is load-bearing, so its canonical home is the subtract.ing origin under the signing key's control. Git hosts (GitHub mirror) are mirror-only and are *not* the authority. This decides the whole topology below.
- **reflex.2 (memory → signature):** the verifiable-authorship primitive is `ssh-keygen -Y sign` / `-Y verify`. Don't invent a format; use the OpenSSH signature format with namespace `file`.
- **boundary:** the agent prepares; the human signs. New signing is the one hard human gate. Pushing already-signed bytes between nodes is infra work.
- Session start per CLAUDE.md: `bash ~/scripts/audit-health.sh` — confirm DNS, the subtract.ing origin, and the signing key are healthy before proceeding.

### 1. Draft on Rousseau (01) — the only canonical node
Rousseau is the archive/governor workstation and holds the canonical `~/subtract.ing/` tree and canonical `~/human/`. All authoring happens here.

```
cd ~/subtract.ing
git log --oneline -5          # know the current head
git status                    # clean tree before adding
# write the new file
$EDITOR ~/subtract.ing/<name>.txt
wc -l ~/subtract.ing/<name>.txt
sha256sum ~/subtract.ing/<name>.txt
```

Claude may do all of the above (drafting, staging) — it's reversible local work.

### 2. Human signing gate (Claude stops here)
The human — not the agent — runs the sign command with the `jnous` key:

```
ssh-keygen -Y sign -f ~/.ssh/<jnous_key> -n file ~/subtract.ing/<name>.txt
# produces ~/subtract.ing/<name>.txt.sig
```

This is `loop.after.2`. Claude prepares the command and the file; the human executes it. Without this signature the file is a suggestion, not canonical (`authority.unsigned`).

### 3. Update + re-sign the manifest (`loop.after.1`)
The manifest is what lets a stranger enumerate what's canonical, so it must cover the new file and be itself signed.

```
# append: <name>.txt  <sha256>   to ~/subtract.ing/MANIFEST
$EDITOR ~/subtract.ing/MANIFEST
# human signs again:
ssh-keygen -Y sign -f ~/.ssh/<jnous_key> -n file ~/subtract.ing/MANIFEST
# produces ~/subtract.ing/MANIFEST.sig
```

Confirm `~/subtract.ing/allowed_signers` already contains the `jnous` line (`jnous ssh-ed25519 AAAA…`). If a verifier can't get the public key from the domain, nothing else matters — so this file must be served too.

### 4. Commit and publish — Rousseau pushes, nobody else
```
cd ~/subtract.ing
git add <name>.txt <name>.txt.sig MANIFEST MANIFEST.sig
git commit -m "publish <name>.txt (signed: jnous)"
```

Deploy to the subtract.ing origin (the node terminating its TLS — per reflex.5 *that* is canonical):
- if the origin is served from Rousseau via tunnel: the working tree *is* the deploy, reload the static server.
- if the origin is a separate host: `rsync -av ~/subtract.ing/ <origin>:/var/www/subtract.ing/` — and **only Rousseau is authorized to run this rsync**.

Then mirror (mirror-only, no authority): `git push github main`.

**Authority boundaries on the push side:**
- **Rousseau (01):** pushes canonical — origin deploy + git mirror. ✅
- **Emile (m2mini):** pull-mirror only. Never pushes canonical content. ❌
- **Surface:** pulls only; it's a governor terminal, not a publish point. ❌ (Moot after the 2026-05-22 reorg, but the rule predates it.)
- **Media/acer:** not formation, not in this path at all. ❌

### 5. How a verifier confirms it, a year from now
A stranger needs three files from the **subtract.ing domain itself** (not the GitHub mirror — the domain is the authority root):

```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers      # contains: jnous ssh-ed25519 AAAA…

ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```

Success output: `Good "file" signature for jnous` (exit 0). That is the authorship claim confirmed — the bytes of `<name>.txt` were signed by the holder of the `jnous` key, which subtract.ing publishes as its signing identity.

Cross-checks the verifier can add:
```
curl -O https://subtract.ing/MANIFEST
curl -O https://subtract.ing/MANIFEST.sig
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST
sha256sum <name>.txt        # must equal the line in MANIFEST
```
This proves the file is not just signed but *listed* as canonical, closing the "valid signature on an orphan file" gap.

### 6. Why this still holds in a year
- The OpenSSH signature is computed over the file's bytes and has no embedded expiry; verification is offline and deterministic given the three files.
- The Ed25519 `jnous` key is long-lived; as long as `allowed_signers` on subtract.ing still carries it, the binding "this key = subtract.ing" holds.
- If subtract.ing is down, the GitHub mirror still carries `<name>.txt`, `.sig`, `allowed_signers`, and the signature still verifies cryptographically — but the *authority* link is weaker off-domain (a mirror can be anyone's), so a careful verifier should treat the mirror as availability backup, not as the trust root. That asymmetry is exactly reflex.5.

### What Claude does vs. doesn't, in one line
Claude: audit, draft the `.txt`, edit the manifest, stage the git commit, run the origin deploy + mirror push from Rousseau. Human: the two `ssh-keygen -Y sign` invocations. No other machine pushes canonical.
