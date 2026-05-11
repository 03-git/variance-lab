Plan only — nothing executed.

## 0. Ground truth first
- `bash ~/scripts/audit-health.sh` — confirm DNS, drives, and that `~/subtract.ing/` is intact and the working tree is clean (`cd ~/subtract.ing && git status`, `git log --oneline -5`).
- Confirm where the `subtract.ing` origin is actually served from before assuming (reflex.4 — verify with a live read, don't narrate). It's served off Rousseau; the canonical store and the served docroot are the same tree, so "publish" = land the signed bytes in `~/subtract.ing/` on Rousseau.

## 1. Reflex check on the format (reflex.2)
Don't invent a signing scheme. The primitive is `ssh-keygen -Y sign` / `ssh-keygen -Y verify` against an `allowed_signers` roster — stock OpenSSH, so a stranger with a default macOS/Linux box can verify it in a year with no extra software. Match the namespace and roster format already used by the existing signed artifacts in the repo (e.g. `governance.conf.universal.txt.sig`); below I assume namespace `file` and signer identity `jnous` — confirm against the repo, don't guess.

## 2. Author the file (Rousseau, agent does this)
- Write `~/subtract.ing/<path>/newfile.txt` (Write/Edit).
- `cd ~/subtract.ing && git add <path>/newfile.txt`
- This is staging-tier work — no permission needed (reversible).

## 3. Human gate — signing (governor runs this, not the agent)
The agent does **not** hold or use the private key. Warn the governor first that this prompts (and may pop a macOS passphrase dialog). Governor runs:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<path>/newfile.txt
```
→ produces `~/subtract.ing/<path>/newfile.txt.sig`. This is the only step that is a human gate (boundary: the agent prepares, the human signs; authority.source = the human).

## 4. Verify locally before acting (loop.before / reflex.4)
Agent verifies with a live read against the in-repo roster:
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file \
  -s ~/subtract.ing/<path>/newfile.txt.sig < ~/subtract.ing/<path>/newfile.txt
```
Expect `Good "file" signature for jnous`. If it doesn't verify, stop and surface it — do not publish.

## 5. Update + re-sign the manifest (loop.after.1 / loop.after.2)
- `sha256sum <path>/newfile.txt` appended to `~/subtract.ing/MANIFEST` (or whatever the repo's manifest file is named).
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST` → `MANIFEST.sig`.
- Agent re-verifies `MANIFEST.sig` the same way.
- `git add <path>/newfile.txt <path>/newfile.txt.sig MANIFEST MANIFEST.sig && git commit -m "publish <newfile>"`

## 6. Publish — which machine pushes
- **Rousseau (01) pushes.** It is the canonical archive node, holds `~/subtract.ing/`, and serves the `subtract.ing` origin. Landing the committed, signed bytes in that tree on Rousseau *is* the publish. If the docroot is a separate path, `rsync -a --checksum ~/subtract.ing/<path>/newfile.txt newfile.txt.sig <docroot>/`. Pushing already-signed artifacts is plain infra work — execute, don't ask.
- **Emile, Media (acer), Surface do not push canonical.** Emile and Media are pull-mirrors / backup tier; Surface is a governor terminal that pulls. They sync *from* Rousseau and never originate canonical content.
- **Git host (GitHub) push is mirror-only** (reflex.5): `git push <mirror-remote> main`. It is not the source of truth and the verifier must not be pointed at a `raw.githubusercontent.com` URL.

## 7. Make sure the trust anchor stays reachable for a year
- `~/subtract.ing/allowed_signers` must remain published at `https://subtract.ing/allowed_signers` with `jnous`'s public key. If the key might rotate, keep the old key entry with `valid-before="..."` / `valid-after="..."` so old signatures still verify.
- SSH signatures don't expire; durability depends only on the file, its `.sig`, and the roster all staying served under the `subtract.ing` domain.

## 8. How a stranger verifies, a year from now
```
curl -O https://subtract.ing/<path>/newfile.txt
curl -O https://subtract.ing/<path>/newfile.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file \
  -s newfile.txt.sig < newfile.txt
```
A `Good "file" signature for jnous` line is the confirmation. Optionally cross-check `sha256sum newfile.txt` against `MANIFEST` and verify `MANIFEST.sig` the same way. Crucially: `allowed_signers` is fetched from `subtract.ing` itself — the signing key's domain is canonical (reflex.5); a copy on a git mirror would prove nothing.

## Authority boundaries, summarized
- **Agent may, without asking:** draft the `.txt`, stage/commit, run all `ssh-keygen -Y verify` reads, rsync already-signed bytes, push the git mirror.
- **Human gate (governor only):** every `ssh-keygen -Y sign` invocation — new signing is the one thing the agent never does. The agent must not possess the private key.
- **Before publishing:** verify the new `.sig` and the manifest `.sig` with live reads; if anything is unsigned or fails, surface it and let the governor decide (loop.before.1–3).
- **Warn before the sign step** — it triggers an interactive/macOS prompt.
