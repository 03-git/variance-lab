## Plan: publish a verifiable `.txt` to subtract.ing

### Authority boundaries (settle these first)
- **Agent prepares, human signs.** Drafting the file, staging it, preparing the manifest diff, and *pushing already-signed bytes* are infra work I can do. **New signing is a human gate** — only the governor runs `ssh-keygen -Y sign`. (`boundary`, `authority.unsigned`, Human-Gate-Scope memory.)
- **reflex.2 before inventing anything:** the signature format is OpenSSH's own — armored `-----BEGIN SSH SIGNATURE-----`, namespace `file`. `ssh-keygen -Y sign`/`-Y verify` round-trips it. No custom format.
- **reflex.5:** canonical content lives under the signing key's domain (`subtract.ing`). Git hosts are mirror-only, never the authority.
- **reflex.4 / loop.before:** before touching the existing manifest, `ssh-keygen -Y verify` it first — don't act on assumed state.
- Don't trust this conversation or memory for the key path; read the actual `~/.ssh` key + `allowed_signers` on disk before the governor signs (`fail.confabulation`).

### Steps

1. **Draft** `foo.txt` in Rousseau's canonical staging — `~/human/...` (rousseau:`~/human/` is canonical for formation human-authored work; this machine, not Surface, not acer).

2. **Verify current manifest** before editing it:
   `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST`

3. **Human gate — governor signs** on the machine holding `jnous`'s private key (warn first that it'll prompt for the passphrase):
   `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/human/.../foo.txt`
   → produces `foo.txt.sig`.

4. **Update + re-sign the manifest** (`loop.after.1`, `loop.after.2`): append `foo.txt`, its `sha256sum`, and a note; then governor runs
   `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file MANIFEST` → `MANIFEST.sig`.

5. **Publish to subtract.ing** (the canonical serve, reflex.5). Push `foo.txt`, `foo.txt.sig`, updated `MANIFEST`, `MANIFEST.sig`, and `allowed_signers` (so a verifier gets the key→principal binding) to whatever fronts `https://subtract.ing/`, rsync'd from Rousseau's canonical dir. **Rousseau is the push origin.** Mirror to git hosts *after*, flagged mirror-only. **acer/Media does not push canonical** — it's service infra + warm-backup tier, never a signing domain; a backup copy there is fine.

6. **Optional air-gap:** add `foo.txt` + `.sig` to the SDXC manifest snapshot, same pattern as the last SDXC refresh.

### How a stranger verifies, a year later
1. Fetch from the **canonical domain**, not a git mirror: `https://subtract.ing/foo.txt`, `…/foo.txt.sig`, `…/allowed_signers`.
2. `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s foo.txt.sig < foo.txt`
   Exit 0 + `Good "file" signature for jnous` ⇒ the holder of `jnous`'s key signed exactly those bytes.
3. Pin/cross-check the pubkey in `allowed_signers` against an independent publication of that fingerprint (the signature only proves "same key as in this file"; *which* key is `jnous` is out-of-band trust — reflex.5: that binding is canonical under subtract.ing).
4. Optionally confirm `sha256sum foo.txt` matches the entry in the signed `MANIFEST`.

The signature — not DNS, TLS, or the git mirror — is the authority; any of those can be compromised and `-Y verify` still tells the truth (`authority.source`: the human; the signature proves it).
