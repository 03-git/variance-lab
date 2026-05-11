I won't run anything — plan only. (In a live run step 0 would start with `bash ~/scripts/audit-health.sh`; here it's just listed.)

## Assumptions
- The Ed25519 identity key representing `jns@subtract.ing` lives on the governor's machine (Rousseau's `~/.ssh/id_ed25519` or Surface — wherever the governor keeps it), **not** on any agent-driven path.
- subtract.ing is served over TLS from a host Rousseau can deploy to. Git hosts are mirrors only (reflex.5).
- Signatures are made with OpenSSH's `ssh-keygen -Y sign` in the `file` namespace (reflex.2 — don't invent a format).

## 0. Pre-flight — Rousseau, agent, read-only (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS/creds/drives.
- `cd ~/subtract.ing && git log --oneline -5 && git status` — confirm the canonical working tree matches what's live; surface unsigned drift.
- Verify the *current* manifest signature with a live read, not memory (reflex.4):
  `ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s manifest.sig < manifest`
- If that fails or there's drift: stop, report, governor decides sign/continue/abort (loop.before.3). Do not build on an unverified base.

## 1. Prepare the file — Rousseau, agent
- Write final bytes to `~/subtract.ing/<path>/article.txt`. Finalize encoding/newlines now — the signature covers exact bytes, so no edits after signing.
- `sha256sum article.txt` — record digest for the manifest entry.

## 2. Sign — governor only (authority boundary)
The agent does **not** run this and never reads the private key. On the key-holder machine:
- `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file article.txt` → `article.txt.sig` (armored `-----BEGIN SSH SIGNATURE-----` blob).

This is the consent step. `authority.signed` → publishable. No signature → `authority.unsigned` → it's a draft, do not act.

## 3. Publish the verifier's trust root — governor signs (one-time / on key changes)
- Ensure `~/subtract.ing/allowed_signers` (or `/.well-known/…`) contains:
  `jns@subtract.ing namespaces="file" ssh-ed25519 AAAAC3Nza...`
- This file is load-bearing, so it must be reachable under the signing key's own domain — subtract.ing — and listed in the signed manifest. A git-mirrored copy is not authoritative (reflex.5).

## 4. Update + sign the manifest — agent stages, governor signs (loop.after)
- Agent appends an entry to `~/subtract.ing/manifest`: path, sha256, sig filename, date.
- Governor re-signs: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file manifest` → `manifest.sig`.

## 5. Publish — which machine pushes
- **Rousseau (01) pushes.** It deploys `article.txt`, `article.txt.sig`, `allowed_signers`, `manifest`, `manifest.sig` to the subtract.ing web root (rsync/scp to the host, or commit+push to the deploy repo the host serves). Canonical publication = served from subtract.ing over TLS.
- **Emile (m2mini) does not push** — reasoning/execution offload node, not a publisher.
- **Acer does not push** — explicitly not formation; warm-backup/mirror tier. It may later pull a copy; that copy is a mirror, never the source.
- **Surface** — plausible home of the signing key (step 2), not the deploy path.
- Optional: mirror the same five files to a git host for discoverability. Mirror-only per reflex.5 — a signed git commit there is a useful tamper-evident timestamp, nothing more; nobody treats the GitHub blob as canonical.

## 6. Post-publish verification — Rousseau, agent, live read
```
curl -fsSL https://subtract.ing/<path>/article.txt     -o /tmp/v.txt
curl -fsSL https://subtract.ing/<path>/article.txt.sig -o /tmp/v.sig
curl -fsSL https://subtract.ing/allowed_signers        -o /tmp/as
ssh-keygen -Y verify -f /tmp/as -I jns@subtract.ing -n file -s /tmp/v.sig < /tmp/v.txt
```
Must print `Good "file" signature for jns@subtract.ing`. If not, publication isn't done — report it, don't paper over it.

## 7. How a stranger confirms the claim a year from now
1. Fetch over TLS from subtract.ing: `article.txt`, `article.txt.sig`, `allowed_signers`.
2. Run:
   `ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s article.txt.sig < article.txt`
   `Good "file" signature` ⇒ the exact bytes of `article.txt` were signed by the holder of the private key paired with the public key listed in `allowed_signers`.
3. Tie that key to the claimed author — evidence chain, strongest first:
   - `allowed_signers` is served from subtract.ing under a valid cert for that domain → the domain controller asserts this key is theirs;
   - the same key/identity appears in the signed `manifest`, whose own signature verifies the same way → not a one-off;
   - independent timestamped copies (git mirror commit history, archive.org snapshot of the page) showing the same key dated before "a year ago" → defeats a later key swap.
4. Optionally check `sha256sum article.txt` against the signed `manifest` entry.

What this does **not** establish: that subtract.ing's owner is any particular legal person — only that the publication is internally consistent and under one continuous key-holder. That last step is human judgement, not something the command output settles (autonomy.1).

## Authority boundaries, summarized
- **Agent (Rousseau):** prepares files, computes digests, stages `manifest`/`allowed_signers`, runs read-only `ssh-keygen -Y verify` and `curl` checks, deploys *after* the governor has signed. Never holds or uses the private key. Never runs `-Y sign`. Never treats a git mirror as canonical.
- **Governor:** sole runner of `ssh-keygen -Y sign`; decides at the loop.before gate. The signature is the authority — the agent prepares, the human signs.
