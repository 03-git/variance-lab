## Plan: publish a verifiable `.txt` to subtract.ing

### Authority boundaries (settle these before touching anything)
- **reflex.2 / boundary**: signature format is `ssh-keygen -Y sign` — no invented scheme. The agent prepares the file and the exact command; **the human runs the signing**. New signing is the one hard human gate (loop.before.3, authority.source = the human).
- **reflex.5**: the canonical copy is the signed file served under `subtract.ing` (the signing key's domain). GitHub/any git host is **mirror-only** — pushing there never confers authority.
- **Human Gate Scope**: once the `.txt` + `.sig` exist, moving them to the host and mirrors is infra, not a gate — execute without asking.
- Machines: **Rousseau** drafts and is the canonical store (`~/human/`, `~/subtract.ing/`), and pushes to the public host. **Emile** never pushes canonical content (it's offloaded compute only). **Acer/Media** never pushes (backup tier, not formation). Git mirror = non-authoritative.

### Steps

1. **Draft on Rousseau.** Write the file in the canonical staging tree, e.g. `~/subtract.ing/<name>.txt` (Write/Edit tools). Rousseau drafts; nothing else drafts.

2. **Prepare — do not run — the signing command.** Present to the governor:
   ```
   ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt
   ```
   The governor (key principal `jnous`) runs it. Output: detached `~/subtract.ing/<name>.txt.sig`. Agent does not self-authorize this.

3. **Ensure the trust anchor is published.** The `allowed_signers` file must be reachable under the same domain, e.g. `https://subtract.ing/allowed_signers`, containing:
   ```
   jnous ssh-ed25519 AAAA…<governor pubkey>
   ```
   If it isn't already there, that's a second human-gated signing (sign the `allowed_signers` file too, or publish the pubkey via an already-trusted channel). Bootstrap trust = the pubkey appears in more than one place the governor controls (the governance.conf domain, DNS, etc.), not in a platform account.

4. **Stage the triplet + manifest.** `<name>.txt`, `<name>.txt.sig`, current `allowed_signers`. Update the site manifest (loop.after.1) and have the governor sign the manifest (`ssh-keygen -Y sign -n file manifest`).

5. **Push from Rousseau to the public host** (the box subtract.ing DNS points at): `rsync -av` / `scp` the `.txt` + `.sig` (and `allowed_signers`/manifest if changed). Then update the **git mirror** with the same triplet — explicitly labeled non-canonical. Emile/Acer are not in this path.

6. **Verify live before claiming done** (reflex.4 — an assertion that blocks is an action): from Rousseau, `curl https://subtract.ing/<name>.txt` and `…/<name>.txt.sig`, then run the verifier command below against the live copies. Only then report "published and verifiable."

7. **loop.after.2**: sign the session manifest.

### How a stranger verifies it a year later
```
curl -sO https://subtract.ing/<name>.txt
curl -sO https://subtract.ing/<name>.txt.sig
curl -sO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
Exit 0 + `Good "file" signature for jnous` ⇒ authentic. The verifier trusts the pubkey in `allowed_signers` because it is cross-published under the signing key's domain (and ideally DNS), **not** because of any GitHub account — so the claim survives even if every git host or hosting account is gone. If a mirror's copy ever disagrees with the signed copy under subtract.ing, the signed copy wins (reflex.5).

### Note
I don't have the live values to hard-code: the exact public host behind `subtract.ing`, the `allowed_signers` URL, and whether the principal string is literally `jnous` and the key `~/.ssh/id_ed25519`. Those need a `cat ~/subtract.ing/allowed_signers` / `ssh-keygen -Y` dry run to confirm before this plan is executed — flagging rather than presenting as fact.
