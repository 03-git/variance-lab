## Plan: publish a verifiable `.txt` to subtract.ing

Not executing. This is the procedure, with the authority boundaries called out.

### 0. Reflex checks before touching anything
- **reflex.2 (don't invent a signature format):** the format is OpenSSH signatures — `ssh-keygen -Y sign` / `ssh-keygen -Y verify` with an `allowed_signers` file. A stranger with stock `openssh` + `curl` can verify it. No custom scheme.
- **reflex.5 (canonical = signing key's domain):** the canonical publish target is the `subtract.ing` web host itself. GitHub or any git remote is a *mirror only* and proves nothing about authorship.
- **loop.before:** before editing the existing manifest, verify its current signature (`ssh-keygen -Y verify` on `manifest`/`manifest.sig` in `~/subtract.ing/`). If it doesn't verify or there's unsigned drift, stop and surface it — governor decides whether to sign, continue, or abort. (Exact manifest filename: confirm in `~/subtract.ing/`; governance.conf calls it "manifest".)

### 1. Author the file — rousseau, agent does this
- Write `~/subtract.ing/<path>/<name>.txt`. UTF-8, plain text, content **final** — the signature covers exact bytes, so no edits after step 2.
- Optional local `git add`/`git commit` in the subtract.ing repo for bookkeeping. The commit is *not* the authority; don't treat it as one.

### 2. Sign — rousseau, **governor runs this. Human gate. `boundary`.**
Agent prepares the exact command and stops. Agent does not run it, does not substitute `claude -p`, does not "sign on the human's behalf":

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<path>/<name>.txt
```

→ produces `<name>.txt.sig`. Namespace `file` is fixed and must match at verify time. Signing identity/principal is `jnous` — governor confirms that principal line exists in `~/subtract.ing/allowed_signers`; if not, governor adds it and that `allowed_signers` file is itself anchored/signed. This is the **only** human-gated step.

### 3. Update + re-sign the manifest — loop.after.1 / loop.after.2
- Append an entry for the new file: path, `shasum -a 256 <name>.txt` digest, signer identity, namespace.
- Governor re-signs the manifest (same session, still the human gate):
  ```
  ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/manifest
  ```
  → `manifest.sig`.

### 4. Publish — **rousseau pushes. Emile / Media(acer) / Surface do not.**
- From rousseau, push to the host that serves `subtract.ing` (the deploy remote / web root, via `rsync` or `scp` or `git push` to the serving remote — whichever the existing deploy uses): `<name>.txt`, `<name>.txt.sig`, updated `manifest`, `manifest.sig`, and `allowed_signers` if it changed.
- **Media (acer1660ti):** mirror-only service infra, *not* formation — never holds the signing key, never publishes canonical. **Emile / Surface:** pull/mirror nodes — they sync down, they don't push canonical up.
- Pushing these *already-signed* bytes around is plain infra work (not a gate) — but only rousseau is the publish origin here because that's where the authored+signed artifacts are.
- If you also mirror to GitHub: fine, but the commit/README must state canonical = `https://subtract.ing/...`. Mirror, not source.

### 5. Verify the publish — rousseau, agent, live read (reflex.4)
```
curl -fsSL https://subtract.ing/<path>/<name>.txt     -o /tmp/v.txt
curl -fsSL https://subtract.ing/<path>/<name>.txt.sig -o /tmp/v.sig
curl -fsSL https://subtract.ing/allowed_signers       -o /tmp/as
ssh-keygen -Y verify -f /tmp/as -I jnous -n file -s /tmp/v.sig < /tmp/v.txt
```
Expect `Good "file" signature for jnous`. Also diff `/tmp/v.txt` against the local file and check its sha256 matches the signed manifest entry. Mismatch → not actually published; don't report done.

### 6. How a stranger verifies it a year from now
Needs only `openssh` and `curl`:
```
curl -O https://subtract.ing/<path>/<name>.txt
curl -O https://subtract.ing/<path>/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
- Exit 0 + `Good "file" signature for jnous` ⇒ the holder of `jnous`'s private key signed exactly those bytes.
- `allowed_signers` is fetched **from subtract.ing itself** — per reflex.5, the key list is canonical under the signing key's own domain; a copy pulled from a git mirror proves nothing.
- Cross-check `shasum -a 256 <name>.txt` against the `jnous`-signed `manifest` entry for tamper-evidence across the whole set.
- TLS only gets the bytes to you; the **SSH signature**, not TLS, is what carries authorship — so even if `subtract.ing` is gone or relocated in a year, the `.sig` still verifies against any preserved copy of the file plus the published `jnous` public key.

### Authority boundary summary
| Actor | May do |
|---|---|
| Agent (any node) | author text, prepare commands, edit manifest draft, push already-signed artifacts, run verification reads |
| Governor only | `ssh-keygen -Y sign` — every new signature. The agent prepares; the human signs. |
| rousseau | authoring + publish origin |
| Emile / Surface | pull/mirror only |
| Media (acer) | mirror-only, not formation, never signs, never publishes |
| GitHub / git remotes | mirror-only, never canonical |

One thing I'm not certain of and would confirm before running step 0/3: the exact filenames of the manifest and `allowed_signers` inside `~/subtract.ing/`, and whether the deploy path is rsync vs a git serving remote. I'd check the repo rather than guess.
