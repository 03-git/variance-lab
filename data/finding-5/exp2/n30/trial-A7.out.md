# Plan: publish a verifiable `.txt` to subtract.ing

## 0. Reflex checks before touching anything
- **reflex.2 (memory→signature):** don't invent a signing scheme. The authority primitive in this formation is already `ssh-keygen -Y sign` / `-Y verify`. Inspect an existing artifact pair in `~/subtract.ing/` (e.g. `ls ~/subtract.ing/**/*.sig`, then `head -1 some.txt.sig`) to read off the namespace and principal in use — `feedback_verify_signatures_before_editing` says the signing identity is `jnous`. Match that. Don't pick a new `-n` namespace.
- **loop.before.1–3:** before staging, verify the current canonical manifest: `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n <ns> -s MANIFEST.sig < MANIFEST`. Run `git -C ~/subtract.ing status` and `git -C ~/subtract.ing log --oneline -5`. Surface any unsigned drift. Governor decides sign / continue / abort. An agent that can't verify the last signature does not proceed.

## 1. Draft (Rousseau — node 01, archive/draft node)
- Write the file in the canonical working tree: `~/subtract.ing/<path>/<name>.txt`. Rousseau holds the canonical tree (`infra_human_canonical`); other nodes pull.
- Agent may write content, compute `shasum -a 256 <name>.txt`, and prepare everything up to the signature. Agent does **not** sign — `boundary`: the agent prepares, the human signs.

## 2. Sign (human gate — governor only)
- This is the one real human gate (`feedback_human_gate_scope`: only *new* signing gates). Warn first if it'll prompt for a passphrase (`feedback_warn_human_gates`).
- Governor runs, with the private key that maps to principal `jnous`:
  ```
  ssh-keygen -Y sign -f ~/.ssh/<jnous_key> -n <ns> ~/subtract.ing/<path>/<name>.txt
  ```
  → produces `<name>.txt.sig` (SSH signature format, verifiable offline by anyone).
- If `jnous` isn't already in the published `~/subtract.ing/allowed_signers`, governor adds the line (`jnous ssh-ed25519 AAAA...`) — that mapping is what a stranger needs and it must live under the subtract.ing domain.

## 3. Update + re-sign the manifest (loop.after.1–2)
- Append `<name>.txt` + its sha256 to `~/subtract.ing/MANIFEST` (or whatever the existing manifest file is called).
- Governor re-signs the manifest: `ssh-keygen -Y sign -f ~/.ssh/<jnous_key> -n <ns> ~/subtract.ing/MANIFEST` → `MANIFEST.sig`.

## 4. Publish (Rousseau pushes; mirrors don't count)
- **reflex.5:** load-bearing content is canonical *under the signing key's domain*. The authorship claim is established by `https://subtract.ing/<path>/<name>.txt` + `.txt.sig` + `allowed_signers` being reachable on the subtract.ing origin. Push the deploy from Rousseau (the canonical node) — this is pushing already-signed artifacts, so it's plain infra work, no gate (`feedback_human_gate_scope`).
- Git host (GitHub or wherever): push as a mirror only. `git -C ~/subtract.ing add … && git commit && git push`. A commit on a git host proves nothing about authorship — it's a mirror, not the signing domain. Don't let the git push masquerade as the canonical act.
- **Which machines do NOT push canonical:** Emile (m2mini) and Surface are pull/mirror nodes; Media (acer1660ti) is not formation at all, just a warm backup tier. None of them establish the subtract.ing copy. (Heavy compute would offload to Emile per CLAUDE.md, but nothing here is heavy.)

## 5. Verify (no execution now — this is the standing recipe a stranger uses a year out)
A verifier with only `ssh-keygen` and `curl`:
```
curl -O https://subtract.ing/<path>/<name>.txt
curl -O https://subtract.ing/<path>/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n <ns> -s <name>.txt.sig < <name>.txt
```
- Exit 0 + `Good "<ns>" signature for jnous` ⇒ authorship confirmed.
- Optional integrity cross-check: fetch `MANIFEST` + `MANIFEST.sig`, `ssh-keygen -Y verify … < MANIFEST`, then confirm `shasum -a 256 <name>.txt` matches the manifest line.
- Why it still holds in a year: the SSH signature binds content↔key; verification is offline and time-independent. The only freshness requirement is that the `allowed_signers` principal→key mapping served from the subtract.ing domain is intact. Git mirror state, node reorgs (M5 Max migration, Surface decommission) are irrelevant to the check.

## Authority boundaries summary
- **Agent (Rousseau Claude):** drafts content, computes hashes, updates manifest text, writes the exact `ssh-keygen -Y sign` commands, runs all `-Y verify` pre-checks, pushes already-signed artifacts to origin + mirror. Never runs `-Y sign`, never declares content canonical on its own authority.
- **Governor:** holds the `jnous` private key, runs the signing commands. The signature *is* the consent (`authority.source`: the human; `authority.signed`: act on it).
- **Verifier (stranger):** trusts nothing but `ssh-keygen -Y verify` against the domain-served `allowed_signers`.
