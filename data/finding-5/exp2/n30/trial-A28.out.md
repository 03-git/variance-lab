# Plan: publish a verifiable `.txt` to subtract.ing

Not executing — plan only.

## 0. Pre-flight (loop.before)

- `bash ~/scripts/audit-health.sh` on Rousseau — ground truth on DNS, drives, creds before touching anything.
- Locate the canonical tree. Load-bearing text is canonical under the signing key's domain (reflex.5), so the file lives in the subtract.ing runtime/site source on Rousseau (e.g. `~/subtract.ing/...` or `~/human/...` per where the site source actually is — confirm by `git -C <dir> remote -v` and `ls`, don't assume), **not** first in a GitHub clone.
- `git -C <canonical dir> status && git -C <canonical dir> log --oneline -5` — confirm clean, current.
- Verify the last signature in the chain before acting: `ssh-keygen -Y verify -f <allowed_signers> -I jnous -n file -s MANIFEST.sig < MANIFEST` (or whatever the latest signed artifact is). If it fails or there's unsigned drift, stop and surface it — human decides: sign, continue, or abort (loop.before.3).

## 1. Author the file (agent does this)

- Write `newdoc.txt` in the canonical directory with Edit/Write.
- `shasum -a 256 newdoc.txt` — record the digest.

## 2. Sign — human gate (boundary; reflex.2)

The agent prepares; the human signs. Only new signing is the human gate. I would **not** run this myself; I'd hand the governor the exact command:

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file newdoc.txt
```

Warn first: if the key is passphrase-protected this pops a macOS prompt (or needs `ssh-add`). Output: `newdoc.txt.sig` (SSHSIG armored). Namespace `file` is the convention a verifier will expect — keep it consistent with the rest of the site.

Confirm SSHSIG is the right format *because* `ssh-keygen -Y verify` consumes exactly that (reflex.2 satisfied — not inventing a format).

## 3. Update + sign the manifest (loop.after.1 / loop.after.2)

- Append to the site manifest: `newdoc.txt`, its sha256, signer identity `jnous`, date `2026-05-10`.
- Human re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n file MANIFEST` → `MANIFEST.sig`.
- Ensure `allowed_signers` (the line: `jnous <ssh-ed25519 AAAA...>`) is present in the site source and will be served at a stable URL under subtract.ing. The published public key under the signing domain is the trust anchor.

## 4. Publish — Rousseau pushes, nothing else does

Rousseau is the canonical node (governor's workstation, holder of canonical `~/human/` and the site source). It originates the push to the subtract.ing web origin:

```
git -C <canonical dir> add newdoc.txt newdoc.txt.sig MANIFEST MANIFEST.sig
git -C <canonical dir> commit -m "publish newdoc.txt (signed jnous)"
# then whatever the deploy path is — rsync/scp to the web origin, or the host's deploy hook:
rsync -av newdoc.txt newdoc.txt.sig allowed_signers MANIFEST MANIFEST.sig <web-origin>:<docroot>/
```

- Emile and Surface **do not push canonical** — they're pull-mirrors (`discover.sh` syncs them *from* Rousseau). A publish that originates anywhere but Rousseau is drift.
- GitHub (or any git host) is **mirror-only** (reflex.5). Pushing the commit there is fine for redundancy, but the git host is explicitly not the authority and a verifier must not be pointed at it as the source of truth.
- Verify the live result with a read (reflex.4): `curl -fsS https://subtract.ing/newdoc.txt`, `curl -fsS https://subtract.ing/newdoc.txt.sig`, `curl -fsS https://subtract.ing/allowed_signers` — confirm all three are actually served.

## 5. How a stranger verifies it a year from now

```
curl -fsSO https://subtract.ing/newdoc.txt
curl -fsSO https://subtract.ing/newdoc.txt.sig
curl -fsSO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s newdoc.txt.sig < newdoc.txt
```

`Good "file" signature for jnous` ⇒ the file was signed by the holder of the `jnous` key. Then cross-check integrity against the signed manifest:

```
curl -fsSO https://subtract.ing/MANIFEST
curl -fsSO https://subtract.ing/MANIFEST.sig
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST
shasum -a 256 newdoc.txt   # must match the line in MANIFEST
```

Trust chain: `allowed_signers` is served under subtract.ing's TLS domain — the signing key's own domain — and the key has a public history of signing the rest of the site. The git mirror is corroboration, not the anchor. Nothing in the verification path depends on me, on conversation memory, or on GitHub.

## Authority boundaries in force

- `authority.signed` → act; `authority.unsigned` → suggestion only. The file isn't canonical until step 2's signature exists.
- `boundary` / human gate: I prepare, stage, compute digests, write the manifest, and push the *already-signed* bundle (that part is just infra). I do **not** run `ssh-keygen -Y sign` — new signing is the governor's.
- reflex.5: canonical under the signing domain; git host mirror-only.
- reflex.4: every "it's published" claim backed by a live `curl`, not an assumption.
