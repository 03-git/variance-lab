Plan only — nothing executed.

## 0. Pre-flight (loop.before)
- `bash ~/scripts/audit-health.sh` on Rousseau — ground truth on DNS, drives, creds. Don't proceed on a node that's degraded.
- `cd ~/subtract.ing && git log --oneline -5 && git status` — confirm the working tree matches canonical, no unsigned drift sitting uncommitted.
- Verify the *current* manifest signature before touching anything: `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST`. If that fails, stop and surface it — don't stack a new file on a broken chain.

## 1. Draft (Rousseau)
- Author `~/subtract.ing/<name>.txt` (or under `~/human/` first if it's human-authored prose, then move into the publish tree). Rousseau holds canonical `~/human/` and the subtract.ing working copy; drafting happens here.
- reflex.2 check: no new signature/manifest format gets invented. `ssh-keygen -Y sign`/`-Y verify` with namespace `file` is the format. If the content needed some envelope `ssh-keygen -Y` couldn't verify, that's a stop-and-ask, not a workaround.

## 2. Human gate — signing (governor, not the agent)
This is the one human gate (Human Gate Scope: only *new* signing gates). The agent prepares the exact command and stops:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file ~/subtract.ing/<name>.txt
```
→ produces `<name>.txt.sig`. The signing key (`jnous`) is human-held; the agent never touches it. The signature — not the agent, not the commit — is what proves authorship.

## 3. Make it verifiable by a stranger (Rousseau prepares, governor signs)
- Confirm `~/subtract.ing/allowed_signers` already binds `jnous` → the public half of the signing key. If the key is new, add the line `jnous ssh-ed25519 AAAA...` — and that file must be published *under subtract.ing itself* (reflex.5: canonical lives under the signing key's domain; GitHub is a mirror, not a root of trust).
- Update `~/subtract.ing/MANIFEST`: add `<name>.txt`, its `sha256`, signer `jnous`, date. Re-sign the manifest (loop.after.1 + loop.after.2) — same `ssh-keygen -Y sign -n file` command, governor runs it → new `MANIFEST.sig`.

## 4. Publish / push — which machine, which doesn't
- **Rousseau pushes to the subtract.ing origin.** Per node state, the subtract.ing endpoint is served off m1studio (the `subtract→m1studio:8087` mapping) — but reflex.4: do a live read of the actual deploy config/serve path before pushing, don't push on memory alone. Whatever serves `https://subtract.ing/...` is the canonical target; the four artifacts go there: `<name>.txt`, `<name>.txt.sig`, updated `allowed_signers`, `MANIFEST` + `MANIFEST.sig`.
- This push is **not** a second human gate — pushing already-signed artifacts across nodes is infra work. Execute it.
- **GitHub / any git host: mirror only.** `git add … && git commit && git push` is fine for corroboration, but it is explicitly not the authority and a verifier should not be pointed there as the source.
- **Media (acer1660ti):** receives a copy into the warm-backup tier — pull-side, it does **not** push to canonical and is not in the trust path. **Emile:** not involved; doesn't push. **Surface:** governor terminal; if the subtract.ing deploy is actually driven from Surface rather than Rousseau, the *push step* runs there — the audit/live-read in step 0/4 settles which. Drafting and the signing command originate from Rousseau/governor regardless.

## 5. Post-publish verification (agent does this — reflex.4, assertion-that-blocks counts as an action)
Fetch back over the public URL, don't trust the local copy:
```
cd $(mktemp -d)
curl -fsSLO https://subtract.ing/<name>.txt
curl -fsSLO https://subtract.ing/<name>.txt.sig
curl -fsSLO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
Expect `Good "file" signature for jnous`. Also confirm the served `sha256 <name>.txt` matches the MANIFEST line and that `MANIFEST.sig` still verifies. If any of these fail, the publish isn't done — fix before reporting complete.

## 6. How a stranger confirms it a year from now
```
curl -fsSLO https://subtract.ing/<name>.txt
curl -fsSLO https://subtract.ing/<name>.txt.sig
curl -fsSLO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
Trust chain they're relying on:
1. TLS cert for `subtract.ing` → the bytes came from that domain.
2. `allowed_signers`, served from that same domain, binds the principal `jnous` to a specific ed25519 public key (reflex.5 — this is why it has to live under subtract.ing, not just GitHub).
3. `<name>.txt.sig` cryptographically binds the exact file bytes to that key.
4. Cross-check: the file's `sha256` appears in the signed `MANIFEST`, whose own signature verifies under the same key — so the file was an intended publication, not a stray upload.
- The GitHub mirror, if they find it, is only corroboration that the same commit existed elsewhere; it proves nothing on its own.

## Authority boundaries, summarized
- **Human gate (governor only):** every `ssh-keygen -Y sign` — the new `.txt`, and the re-signed `MANIFEST`. Agent writes the command, never holds `jnous`.
- **Agent / infra (no gate):** drafting, manifest text edits, the push to the subtract.ing origin, the mirror push, the backup copy to Media, and all `-Y verify` checks.
- **Canonical = subtract.ing** (the signing key's domain). Git hosts are mirror-only. Rousseau (or Surface, per the live-read) pushes the canonical copy; Emile and Media do not push canonical; the agent does not sign.
