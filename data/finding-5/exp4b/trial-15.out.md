# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. This is the procedure, the boundaries, and the verifier's check.

## 0. Reflex checks (before touching anything)

- **reflex.2 — memory→signature:** the primitive is `ssh-keygen -Y sign` / `-Y verify` (OpenSSH signature format, namespace `file`). It already covers this case; do not invent a signing scheme or pull in a library.
- **reflex.5 — canonical→signing domain:** the authoritative copy lives at `https://subtract.ing/…`, served from the host the signing key's domain points at. Any GitHub copy is a mirror, not the artifact a verifier trusts.
- **reflex.4 — action→verification:** if the new file replaces or sits beside an existing canonical file, do a live read + `ssh-keygen -Y verify` of that file's current `.sig` *before* writing. Don't act on remembered state.
- **boundary:** agent prepares; human signs. The one command below run by the governor is the only step the agent never performs.

## 1. Draft + stage — Rousseau (01), agent

- Write the file into the canonical staging tree on Rousseau, e.g. `~/subtract.ing/<path>/<name>.txt` (or `~/human/…` if it's human-authored prose staged for publish). Rousseau holds canonical `~/human/` and `~/subtract.ing/runtime/`; staging writes here need no permission (reversible).
- Record the digest you intend to anchor: `sha256sum <name>.txt` — keep it for the manifest step.
- `git status` / `git log --oneline -5` on the staging repo so you know the base state you're adding onto.

## 2. Surface unsigned drift — agent → governor (loop.before)

Present to the governor: the new file path, its sha256, and that it is currently **unsigned** (so: suggestion only, not yet canonical — `authority.unsigned`). Governor decides: sign / continue / abort. Warn that step 3 will prompt for the key passphrase (human-gate popup).

## 3. Sign — governor, on the machine holding the private key

Run by the governor, not the agent:

```
ssh-keygen -Y sign -f ~/.ssh/<governor_signing_key> -n file ~/subtract.ing/<path>/<name>.txt
```

Produces `<name>.txt.sig` (an `-----BEGIN SSH SIGNATURE-----` armored blob). Identity in the signature is the key's comment / the entry used in `allowed_signers` (the governor's published signer id, e.g. `jnous`). `authority.source` = the human; this `.sig` is what makes the file canonical.

## 4. Update + re-sign the manifest (loop.after.1 / loop.after.2)

- Add a line for `<name>.txt` (path + sha256) to the canonical manifest in the staging tree.
- Governor re-signs the manifest the same way: `ssh-keygen -Y sign -f ~/.ssh/<key> -n file <manifest>` → refreshed `<manifest>.sig`.
- Confirm `allowed_signers` already contains the governor's identity → pubkey line:
  `jnous namespaces="file" ssh-ed25519 AAAA…` — if not, it gets added and the file is itself covered by the signed manifest. The verifier's trust anchor is this file *as served from subtract.ing's own domain*, nothing else.

## 5. Push to the canonical host

- The bundle to publish: `<name>.txt`, `<name>.txt.sig`, the updated manifest + `.sig`, and `allowed_signers` (if changed) — into the subtract.ing web root, under the same path the file is referenced by.
- **Which machine pushes:** the node holding deploy/write access to the subtract.ing web root (currently the Surface-side executor path; that role moves to Rousseau after the 2026-05-22 reorg). Whichever node it is, it pushes **only the already-signed bytes** — copying signed artifacts across nodes is plain infra work (`feedback: human gate scope`), no fresh approval needed.
- **Which machine does not push:** Media/acer — it's the warm-backup mirror tier, not the signing domain; it receives a copy, it does not publish canonical. A GitHub mirror, if one exists, is updated for convenience only and is explicitly *not* the artifact anyone verifies against (reflex.5).
- Rousseau's role ends at "staged + signed bundle ready"; it may also be the push node depending on reorg state, but it never originates the signature.

## 6. How a stranger verifies it, a year later

All fetched over HTTPS **from `subtract.ing` itself** (the signing key's domain — that's the whole point of reflex.5):

```
curl -O https://subtract.ing/<path>/<name>.txt
curl -O https://subtract.ing/<path>/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
```

Then:

```
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```

`Good "file" signature for jnous with ED25519 key …` + exit 0 ⇒ the file is byte-for-byte what the holder of the `jnous` key signed. To pin it against tampering of the signer list, also verify the manifest (`ssh-keygen -Y verify … -s <manifest>.sig < <manifest>`) and check `<name>.txt`'s sha256 appears there. No appeal to GitHub, to the agent, or to memory — the signature is the authority, the domain is the trust anchor, and `ssh-keygen -Y verify` is the entire check.

## Authority boundaries, condensed

| Step | Who | Why |
|---|---|---|
| draft, hash, stage, manifest edit | agent (Rousseau) | reversible staging writes |
| `ssh-keygen -Y sign` (file + manifest) | **governor only** | `boundary` — agent prepares, human signs; `authority.source` |
| push signed bundle to subtract.ing | deploy node (Surface→Rousseau post-reorg) | moving signed bytes = infra, not a gate |
| serve / mirror | subtract.ing host canonical; Media + any git host = mirror-only | reflex.5 |
| verify | anyone, anywhere | `authority.signed` — the signature, not the messenger |
