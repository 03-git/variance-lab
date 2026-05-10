## Plan: publish a verifiable .txt to subtract.ing

### Authority boundaries (up front)
- **Agent prepares**: drafting, staging, computing what gets signed, pushing already-signed artifacts.
- **Human signs**: only the governor invokes `ssh-keygen -Y sign` with the `jnous` private key. New signing is the human gate.
- **Canonical domain = signing domain** (reflex.5): `subtract.ing` is canonical. Any git mirror is informational only and not what a verifier consults.

### Machines
- **Rousseau (this node)**: drafts under `~/human/`, stages under `~/subtract.ing/`, executes the push. Signing key lives here; human signs here.
- **Emile / Media**: not involved. No drafting, no signing, no push.

### Steps

**1. Draft (agent, rousseau)**
```
$EDITOR ~/human/drafts/<slug>.txt
```
Freeze content. No trailing-newline churn after this point — the byte stream is what gets signed.

**2. Stage into the canonical tree (agent, rousseau)**
```
cp ~/human/drafts/<slug>.txt ~/subtract.ing/<slug>.txt
cd ~/subtract.ing
sha256sum <slug>.txt        # record for the human before signing
```

**3. Confirm allowed_signers is published (agent, rousseau)**
The verifier needs a public key bound to an identity at the canonical domain. Check:
```
curl -fsS https://subtract.ing/allowed_signers
ssh-keygen -Y find-principals -s /dev/null -f <(curl -fsS https://subtract.ing/allowed_signers) 2>&1 | head
```
Expected line shape:
```
jnous@subtract.ing ssh-ed25519 AAAA...
```
If absent or stale, that file is the precondition — fix it (itself a signed artifact) before signing the new .txt.

**4. Human signs (governor, rousseau — human gate)**
Governor runs (agent does not):
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<slug>.txt
```
Produces `<slug>.txt.sig` (PEM-wrapped SSHSIG, namespace `file`).

**5. Local verify before push (agent, rousseau)**
```
ssh-keygen -Y verify \
  -f ~/subtract.ing/allowed_signers \
  -I jnous@subtract.ing \
  -n file \
  -s ~/subtract.ing/<slug>.txt.sig \
  < ~/subtract.ing/<slug>.txt
```
Must print `Good "file" signature for jnous@subtract.ing with ED25519 key SHA256:...`. If not, stop. Do not push.

**6. Push to canonical subtract.ing (agent, rousseau)**
Pushing already-signed artifacts is infra, not a human gate. Use whatever the deploy primitive is for the host (`rsync` over ssh to the subtract.ing webroot, e.g. `rsync -av <slug>.txt <slug>.txt.sig <host>:/var/www/subtract.ing/`). Do not rely on a git push to GitHub for canonicity — git hosts are mirrors.

**7. Post-push live read (agent)**
```
curl -fsS -o /tmp/v.txt  https://subtract.ing/<slug>.txt
curl -fsS -o /tmp/v.sig  https://subtract.ing/<slug>.txt.sig
curl -fsS -o /tmp/v.as   https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f /tmp/v.as -I jnous@subtract.ing -n file -s /tmp/v.sig < /tmp/v.txt
```
Round-trip must pass. This satisfies reflex.4 (verify with a live read after acting).

### How a stranger verifies a year from now
Given only the URL `https://subtract.ing/<slug>.txt`:

```
curl -fsSO https://subtract.ing/<slug>.txt
curl -fsSO https://subtract.ing/<slug>.txt.sig
curl -fsS  https://subtract.ing/allowed_signers -o allowed_signers

ssh-keygen -Y verify \
  -f allowed_signers \
  -I jnous@subtract.ing \
  -n file \
  -s <slug>.txt.sig \
  < <slug>.txt
```
A `Good "file" signature ...` line is the proof. The chain of trust is: verifier trusts the `subtract.ing` domain to publish the correct `allowed_signers` → that file binds `jnous@subtract.ing` to an ed25519 pubkey → SSHSIG over the .txt resolves under that key. No GitHub, no PGP keyserver, no third party in the loop.

### Notes / failure modes I'd watch
- Touching the file after signing (even a newline) breaks the signature. Treat the staged copy as frozen.
- `-n file` namespace must match on sign and verify; mismatched namespace is the most common verify failure.
- If `allowed_signers` is rotated within the year, the old signature still verifies *only* if the old pubkey line is retained (append, don't replace). That's a publishing-policy concern, not a per-file one.
