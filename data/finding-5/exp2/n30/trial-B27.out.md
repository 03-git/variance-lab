# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. Plan only. Note up front (reflex.2): the format is OpenSSH's SSHSIG via `ssh-keygen -Y sign` / `-Y verify` — a stranger needs only `openssh` to check it, no bespoke tooling. Not inventing a format.

## Authority boundaries (settle these first)
- **Agent (me):** authors the `.txt`, computes hashes, stages the commit, drafts the verifier command, updates the manifest draft. Prepares — does not sign, does not publish. (`boundary`: the agent prepares, the human signs.)
- **Governor (human):** holds `~/.ssh/id_ed25519`, runs `ssh-keygen -Y sign`, authorizes the deploy push. `authority.source` = the human; the signature is what proves it.
- **Canonical domain:** subtract.ing. Load-bearing content is canonical only under the signing key's domain (reflex.5). GitHub/any git host = mirror-only; pushing there does not make it canonical.

## Machines
- **Rousseau (01, this box):** carries the subtract.ing deploy path and the governor's signing key. This is where authoring, signing, and the publish push happen.
- **Emile (m2mini):** execution/offload node. No publish authority. Does not push.
- **Surface:** governor terminal, not a publish origin.
- **acer1660ti:** explicitly NOT formation — warm backup/mirror tier. Receives a copy at most; never the canonical push.

## Steps

**1. Author**
Write the file inside the subtract.ing content working tree, e.g. `~/subtract.ing/<path>/foo.txt`.

**2. Pre-sign inspection (loop.before)**
```
git -C ~/subtract.ing log --oneline -5
git -C ~/subtract.ing status
wc -l ~/subtract.ing/<path>/foo.txt
shasum -a 256 ~/subtract.ing/<path>/foo.txt   # macOS; sha256sum on Debian
```
Surface any unsigned drift; governor decides sign / continue / abort before anything publishes.

**3. Sign — governor only, not me**
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<path>/foo.txt
```
Produces `foo.txt.sig` (SSHSIG, namespace `file`). The signature covers the file *bytes* — independent of URL, host, or timestamp.

**4. Ensure the identity→key map is published**
`~/subtract.ing/allowed_signers` must contain the public half:
```
governor@subtract.ing ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...
```
This file is itself canonical under subtract.ing. (If it's already deployed and unchanged, nothing to do.)

**5. Publish to the canonical domain**
Commit `foo.txt` + `foo.txt.sig` (+ `allowed_signers` if changed) and deploy to whatever serves https://subtract.ing/ — using the deploy credential held on Rousseau. Result:
- `https://subtract.ing/<path>/foo.txt`
- `https://subtract.ing/<path>/foo.txt.sig`
- `https://subtract.ing/allowed_signers`

Git-host mirrors may receive the same commit afterward; they are not the source of authority.

**6. Manifest (loop.after)**
Add `foo.txt` and its `.sig` to the subtract.ing manifest; governor re-signs the manifest. Session close.

## How a stranger verifies, a year later
```
curl -sO https://subtract.ing/<path>/foo.txt
curl -sO https://subtract.ing/<path>/foo.txt.sig
curl -sO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I governor@subtract.ing -n file -s foo.txt.sig < foo.txt
```
Expected:
```
Good "file" signature for governor@subtract.ing with ED25519 key SHA256:<fingerprint>
```

Why it still holds in a year:
- The signature is over file content, so any copy from any mirror verifies — even if subtract.ing is down at check time.
- ed25519 signatures don't expire; no CA, no revocation clock.
- The `allowed_signers` identity binding is served from the same domain the verifier already trusts (DNS+TLS) to fetch the content — the trust root is the domain, and the domain is the signing key's domain (reflex.5). A stranger who trusts they reached subtract.ing transitively trusts the key listed there.
- Tamper on the file, the `.sig`, or substitution of a different key → `ssh-keygen -Y verify` fails closed.

Residual trust assumptions worth stating to any verifier: control of the subtract.ing domain and the integrity of the published `allowed_signers` at fetch time. Pinning the key fingerprint out-of-band (or cross-posting it where the governor is already known) closes that gap.
