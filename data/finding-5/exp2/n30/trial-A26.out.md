# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. Steps, commands, and boundaries below.

## 0. Pre-flight (Rousseau, before touching anything)

- `bash ~/scripts/audit-health.sh` — ground truth on DNS/creds/drives. Don't proceed if it's unhappy.
- `loop.before.1/2`: verify the last signed state of the subtract.ing tree and surface any unsigned drift before adding to it:
  - `cd ~/subtract.ing && git status && git log --oneline -5`
  - For the file(s) you're about to sit next to: `ssh-keygen -Y verify -f <allowed_signers> -I jnous -n <ns> -s <existing>.txt.sig < <existing>.txt` — confirm the *existing* canon verifies before extending it.
- `reflex.2` — do not invent the signature format. Inspect an existing pair to read the namespace convention actually in use:
  - `head -3 ~/subtract.ing/.../governance.conf.universal.txt.sig` (it's `-----BEGIN SSH SIGNATURE-----` armored; the namespace isn't in the armor, so check the signing wrapper script if there is one, or the repo's README/Makefile). Whatever string the existing `.sig` files were produced with — reuse it. Call it `<ns>` below. If nothing documents it, that's a question for the governor, not a guess.
- Confirm the trust root is already published: `curl -fsS https://subtract.ing/allowed_signers` and check it contains a `jnous <keytype> <pubkey>` line matching `~/.ssh/id_ed25519.pub` on Rousseau. If that file doesn't exist or is stale, publishing *it* is a prerequisite and is itself human-gated (same flow as below).

## 1. Author — Rousseau (drafts)

- Write the file into the canonical working tree: `~/subtract.ing/<path>/newfile.txt`. Rousseau is where formation/canonical authoring happens; `reflex.5` — this content is canonical under the signing key's domain (subtract.ing), the git host is a mirror only.
- No CRLF, final newline, UTF-8 — the bytes you sign are the bytes the verifier hashes.

## 2. Sign — human gate, on Rousseau

This is the only step the agent cannot do. `boundary` / `authority.source`: the agent prepares the exact command, the governor runs it (key + passphrase are the human's).

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n <ns> ~/subtract.ing/<path>/newfile.txt
```

Produces `newfile.txt.sig` (armored, detached). Identity in `allowed_signers` is `jnous`.

Then re-verify locally before anything moves:
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n <ns> \
  -s ~/subtract.ing/<path>/newfile.txt.sig < ~/subtract.ing/<path>/newfile.txt
```
Expect exit 0 and `Good "<ns>" signature for jnous`. If it doesn't, stop — the artifact is not publishable.

## 3. Manifest — `loop.after.1` / `loop.after.2`

- Add `newfile.txt` (and `.sig`) to whatever manifest covers that tree (the FROZEN / SDXC-style manifest), then re-sign the manifest with the same `ssh-keygen -Y sign` invocation. A new canonical file that isn't in a signed manifest is drift.

## 4. Push — Surface executes; Rousseau and the mirrors do not

- Authority boundary: **signing happens before the push; no machine downstream of the signature ever re-signs or edits.** The `.sig` travels with the file unchanged.
- **Surface** does the publish to the subtract.ing web origin (the "Surface executes" split). It moves an already-signed pair across nodes — `Human Gate Scope`: that's infra work, not a gate. `git push` to the mirror and/or `rsync` to the serving host, whatever the existing deploy path is — Surface runs it, doesn't touch contents.
- **Rousseau** does not push to the public origin; it's the author/keyholder. **Emile** is a pull-mirror. **Media (acer1660ti)** is a warm backup tier, never canonical, never signs, no inference. None of them re-sign.
- If subtract.ing is fronted by a git-hosted page: `reflex.5` — that host is a mirror. The canonical artifact is the signed file; the URL is just where strangers fetch it.

## 5. How a stranger verifies, a year from now

They need three URLs and `ssh-keygen` (OpenSSH ≥ 8.0):

```
curl -fsSO https://subtract.ing/<path>/newfile.txt
curl -fsSO https://subtract.ing/<path>/newfile.txt.sig
curl -fsS  https://subtract.ing/allowed_signers -o allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n <ns> -s newfile.txt.sig < newfile.txt
```

Pass condition: exit status 0 and `Good "<ns>" signature for jnous`. Any byte change to `newfile.txt`, wrong namespace, or a key not in `allowed_signers` → non-zero, fail.

Trust chain the verifier is relying on:
1. The signature itself — Ed25519 over the file's hash. No expiry baked in (we didn't pass a timestamp/validity window), so it verifies indefinitely.
2. `jnous` → public key binding — comes from `allowed_signers`, served over HTTPS from `subtract.ing`, i.e. the signing key's *own* domain (`reflex.5`: canonical lives under the signing key's domain, not a git mirror). For belt-and-suspenders, the same pubkey line also appears in the already-published, separately-signed `governance.conf.universal.txt` lineage, so a stranger can cross-check it against an artifact that predates this one.
3. Domain control — TLS cert for `subtract.ing` plus the fact that the canonical txt files have been served from there over time.

A verifier who only trusts (1)+(2) needs nothing from us a year out except that the three files still resolve — which is the mirrors' job, not the signature's.

## Boundary summary

- **Human, on Rousseau:** runs `ssh-keygen -Y sign` (file + manifest). Only gated step.
- **Agent, on Rousseau:** authors the file, prepares the exact sign command, verifies locally, updates the manifest text.
- **Surface:** publishes the signed pair to the subtract.ing origin. No content changes, no signing.
- **Emile / Media:** mirrors and backup only. Never canonical, never sign.
- **Git host (if any):** mirror only — not the canonical location.
