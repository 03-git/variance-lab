# Plan: publish a verifiably-authored .txt to subtract.ing

## 0. Preconditions (verify, don't assume)
- `bash ~/scripts/audit-health.sh` — ground truth on rousseau before touching anything.
- `cd ~/subtract.ing && git status && git log --oneline -5` — confirm working tree clean and you're on the canonical mirror.
- `ssh-add -L | grep jnous` — confirm the `jnous` signing key is loaded in the agent (the key the existing `allowed_signers` already trusts).
- `cat ~/subtract.ing/allowed_signers` — confirm the public key fingerprint that a stranger will use to verify is the one currently published.

## 1. Draft (rousseau, agent does this)
- Author the file at `~/subtract.ing/<path>/<name>.txt`. UTF-8, LF line endings, no trailing whitespace drift.
- Decide the canonical URL up front: `https://subtract.ing/<path>/<name>.txt`. Per reflex.5, this URL is the canonical address; any GitHub mirror is non-authoritative.
- If the site uses a manifest (e.g. an index/catalog file), stage the manifest entry in the same commit so the file is reachable, not orphaned.

## 2. Sign (HUMAN GATE — agent stops here)
This is loop.before.3. The agent does not run `ssh-keygen -Y sign`. The governor does.

Command the human runs:
```
ssh-keygen -Y sign -f ~/.ssh/jnous -n subtract.ing \
  ~/subtract.ing/<path>/<name>.txt
```
Produces `<name>.txt.sig` next to it. Namespace `subtract.ing` is the verifier's domain pin — it must match what verifiers will pass to `-n`.

Notes:
- Per `feedback_verify_signatures_before_editing`: if the file already has a `.sig`, run `ssh-keygen -Y verify` on the existing one before overwriting. Not relevant for a brand-new file, but the reflex applies if iterating.
- Per `boundary` in governance.conf: the signature *is* the authority. The agent prepares, the human signs.

## 3. Commit + push (rousseau is canonical, agent can do this once .sig exists)
- `git add <path>/<name>.txt <path>/<name>.txt.sig <manifest-if-any>`
- `git commit -m "<name>.txt: <one-line description>"`
- `git push` — to whichever remote actually serves `subtract.ing` (the live web origin, not the github mirror). Confirm with `git remote -v` before push; the github remote is mirror-only per reflex.5.
- After web propagation: `curl -fsS https://subtract.ing/<path>/<name>.txt | sha256sum` and compare to local `sha256sum` — confirms the canonical URL serves the signed bytes, not a stale CDN copy.

Rousseau pushes. Emile and Media do not — they are not the canonical origin for subtract.ing content. (Acer is NAS, not formation.)

## 4. Update post-session state (loop.after)
- If subtract.ing has a top-level manifest of signed artifacts, append `<name>.txt` with its sha256 and signing date.
- Sign the manifest with the same `ssh-keygen -Y sign -n subtract.ing` invocation (human gate again).
- Commit + push the manifest update.

## 5. How a stranger verifies (a year from now)
The stranger needs three things, all reachable from `subtract.ing`:
1. `curl -O https://subtract.ing/<path>/<name>.txt`
2. `curl -O https://subtract.ing/<path>/<name>.txt.sig`
3. `curl -O https://subtract.ing/allowed_signers` — this is the trust root. It binds an identity (e.g. `jnous@subtract.ing`) to the ssh public key.

Then:
```
ssh-keygen -Y verify \
  -f allowed_signers \
  -I jnous@subtract.ing \
  -n subtract.ing \
  -s <name>.txt.sig \
  < <name>.txt
```
Exit 0 + `Good "subtract.ing" signature for jnous@subtract.ing` = authorship verified. The verifier trusts subtract.ing's TLS for the `allowed_signers` fetch (that's the chain-of-custody for the pubkey); everything downstream is cryptographic.

## Authority boundaries summary
- **Agent (rousseau):** drafts, stages, commits, pushes, verifies the live URL serves the right bytes.
- **Human (governor):** runs `ssh-keygen -Y sign`. Only the human holds `~/.ssh/jnous`. New signatures are a human gate per `feedback_human_gate_scope`.
- **Canonical push origin:** rousseau → subtract.ing web origin only. GitHub mirror gets the push as a side effect but is not load-bearing.
- **Not involved:** Emile, Media, Acer. None of them sign, none of them push canonical.

## Failure modes to avoid
- Committing the `.txt` without the `.sig` and "fixing it later" — the canonical URL would briefly serve unsigned, load-bearing content (reflex.5 violation).
- Running `ssh-keygen -Y sign` from the agent (boundary violation).
- Pushing only to github and assuming subtract.ing updates (reflex.5: github is mirror-only).
- Forgetting `-n subtract.ing` on either side — signature verifies cryptographically but is unbound from the domain claim.
