# Plan: publish verifiable .txt to subtract.ing

## 0. Preconditions to confirm before drafting
- `bash ~/scripts/audit-health.sh` — ground truth on rousseau state.
- `ls ~/.ssh/` — confirm the `jnous` signing key is present (priv + pub).
- `curl -sI https://subtract.ing/allowed_signers` — confirm the allowed_signers file is already canonical and reachable (it is what makes a stranger's verify work). If absent, that has to ship first, separately, before anything else can be verified.

## 1. Draft (agent, rousseau)
- Author the file at the canonical path under the signing-key domain on rousseau, e.g. `~/subtract.ing/<area>/<name>.txt`. Never `/tmp/`.
- After the last edit, freeze: `wc -c ~/subtract.ing/<area>/<name>.txt` and `shasum -a 256` the file. Quote both back to the governor. No edits after this point — any byte change invalidates the signature.

## 2. Sign (human gate, rousseau)
This is the only step the agent does not perform. Per `authority.signed` and `boundary`: the agent prepares, the human signs.

Command for the governor to run:
```
ssh-keygen -Y sign \
  -f ~/.ssh/jnous \
  -n subtract.ing \
  ~/subtract.ing/<area>/<name>.txt
```
Produces `<name>.txt.sig` next to the file. Namespace `subtract.ing` is the verification domain; a verifier must pass the same `-n`.

## 3. Verify locally before publishing (agent, rousseau)
Dry-run the exact check a stranger will run, against the local allowed_signers:
```
ssh-keygen -Y verify \
  -f ~/subtract.ing/allowed_signers \
  -I <identity-string-in-allowed_signers> \
  -n subtract.ing \
  -s ~/subtract.ing/<area>/<name>.txt.sig \
  < ~/subtract.ing/<area>/<name>.txt
```
Must print `Good "subtract.ing" signature ...`. If not, stop — do not publish a sig that won't verify a year from now.

## 4. Publish to canonical (agent, rousseau pushes)
- Rousseau is canonical for `~/subtract.ing/`, so the deploy originates here.
- Push both `<name>.txt` and `<name>.txt.sig` to the subtract.ing webroot via whatever existing deploy path the site uses (rsync over ssh to the host serving subtract.ing, or the existing publish script in `~/subtract.ing/`). This is reversible/standard infra — no human gate (per "Human Gate Scope": only new signing is a gate; pushing signed artifacts is infra).
- Confirm post-push: `curl -sSf https://subtract.ing/<path>/<name>.txt -o /tmp/check.txt` and `curl -sSf https://subtract.ing/<path>/<name>.txt.sig -o /tmp/check.sig`, then re-run the `ssh-keygen -Y verify` from §3 against `/tmp/check.txt` and `/tmp/check.sig`. This proves the bytes the public sees verify, not just the local copy.

## 5. What does NOT push
- No git host. Per `reflex.5`: "load-bearing content is canonical under the signing key's domain; git hosts are mirror-only." If the file ends up in a GitHub mirror later, that's incidental — verification authority is `https://subtract.ing/`, not `github.com/...`.
- Emile / Media / Surface do not push. Only rousseau touches the canonical webroot.

## 6. How a stranger verifies a year from now
Given only the URL of the .txt, a verifier on any machine with OpenSSH ≥ 8.2 runs:

```
curl -O https://subtract.ing/<path>/<name>.txt
curl -O https://subtract.ing/<path>/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers

ssh-keygen -Y verify \
  -f allowed_signers \
  -I <identity-string> \
  -n subtract.ing \
  -s <name>.txt.sig \
  < <name>.txt
```
A `Good "subtract.ing" signature for <identity> with ED25519 key ...` line is the proof. The chain is: file bytes → signature → public key in allowed_signers → same domain serving all three. No third party, no agent, no git host involved.

## 7. Authority boundaries summary
- Agent: drafts, freezes, dry-run verifies, deploys already-signed artifacts, post-publish re-verifies. No editing after sign.
- Human (governor): runs `ssh-keygen -Y sign` with the `jnous` key. That signature *is* the authority.
- Canonical surface: `subtract.ing` (signing-key domain). Everything else is a mirror.
