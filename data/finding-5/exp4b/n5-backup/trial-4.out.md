# Plan: publish a verifiable .txt to subtract.ing

## 0. Pre-flight (reflex.4, loop.before.1–3)
- Run `bash ~/scripts/audit-health.sh` to confirm rousseau ground truth.
- `ls ~/subtract.ing/` to confirm the canonical tree exists locally.
- `git -C ~/subtract.ing log --oneline -5` and `git -C ~/subtract.ing status` to confirm working tree is clean before adding new content.
- Confirm signing key fingerprint: `ssh-keygen -lf ~/.ssh/id_ed25519.pub` should match the `jnous` identity used elsewhere.
- Confirm an `allowed_signers` file already exists on subtract.ing at a stable URL (e.g. `https://subtract.ing/allowed_signers` or `.well-known/...`); `curl -sI` to verify. If not, the plan must include publishing it once — see §5.

## 1. Draft (agent prepares)
- Write the file at the canonical path: `~/subtract.ing/runtime/<name>.txt` (or whatever subtree fits the document's domain). Per `reflex.5`, the file is canonical under the signing key's domain, not under a git host.
- No agent action beyond drafting until the human reviews.

## 2. Human review and signature (authority boundary)
This step the agent cannot perform. `boundary`: the signature proves authority. `authority.unsigned`: do not act on a draft.

Human runs, on rousseau:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/runtime/<name>.txt
```
This produces `~/subtract.ing/runtime/<name>.txt.sig` (an SSH signature with namespace `file`). The `-n file` namespace is the same one ssh-keygen recommends for arbitrary file signing and is what the verifier will pass.

## 3. Local verify before publishing (reflex.4)
Before pushing anything, verify the signature locally with the same tool a stranger will use:
```
ssh-keygen -Y verify \
  -f ~/subtract.ing/allowed_signers \
  -I jnous \
  -n file \
  -s ~/subtract.ing/runtime/<name>.txt.sig \
  < ~/subtract.ing/runtime/<name>.txt
```
Expect: `Good "file" signature for jnous with ED25519 key SHA256:...`. If this fails, stop — do not publish.

## 4. Publish (agent may execute; signed artifact, not new signing)
Per `feedback_human_gate_scope`, pushing an already-signed artifact is infra work, not a human gate.

- Rousseau pushes. Rousseau is governor's main workstation and host of `~/subtract.ing/`. Emile and the acer media node do not push to the signing domain — they're mirrors.
- Commit and push the canonical tree:
  ```
  git -C ~/subtract.ing add runtime/<name>.txt runtime/<name>.txt.sig
  git -C ~/subtract.ing commit -m "publish <name>.txt"
  git -C ~/subtract.ing push
  ```
- Then whatever deploy step subtract.ing uses to materialize files at `https://subtract.ing/runtime/<name>.txt` and `https://subtract.ing/runtime/<name>.txt.sig`. (If publishing is via a static-site/CDN deploy hook on push, no further action; if a manual rsync/deploy is involved, run that here. Confirm the exact mechanism from `~/subtract.ing/` tooling before this step — do not assume.)
- Post-publish: `curl -sI https://subtract.ing/runtime/<name>.txt` and `…/<name>.txt.sig` should both 200. Re-run the §3 `ssh-keygen -Y verify` against the curled bytes, not the local files, to prove what's on the wire verifies.

## 5. Allowed-signers durability (so verification works in a year)
The verifier needs an `allowed_signers` line mapping the identity `jnous` to the ed25519 public key. Format:
```
jnous ssh-ed25519 AAAAC3Nz...
```
- Publish `allowed_signers` at a stable URL on subtract.ing (e.g. `https://subtract.ing/allowed_signers`) and reference it from a human-readable page so a stranger can find it.
- Do not rotate the key without leaving the old key in `allowed_signers` with a `valid-before` option, or future verifications of past artifacts break.

## 6. How a stranger verifies, a year from now
With only `ssh-keygen` (OpenSSH ≥ 8.1) and curl:
```
curl -O https://subtract.ing/runtime/<name>.txt
curl -O https://subtract.ing/runtime/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file \
  -s <name>.txt.sig < <name>.txt
```
A `Good "file" signature for jnous` line is the proof. No GitHub, no PGP keyserver, no third party — `reflex.5` holds: authority lives at the signing domain, git is a mirror.

## Authority boundaries summary
- Agent: drafts (§1), runs local verify (§3), pushes already-signed artifacts (§4), curls/checks (§4 tail).
- Human: signs (§2). Only new signing is a human gate.
- Machines: rousseau is the only pusher to subtract.ing. Emile and acer are mirror/consumers and must not be on the publish path.
