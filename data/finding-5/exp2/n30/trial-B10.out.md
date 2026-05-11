Plan only — nothing executed below. (Per session protocol I'd normally open with `bash ~/scripts/audit-health.sh`; that's step 0 of execution, not run here.)

## Authority boundaries (settled before any keystroke)

- `authority.signed` → act; `authority.unsigned` → suggestion only. A `.txt` on subtract.ing with no valid `.sig` is confabulation-equivalent and carries no authorship claim.
- `boundary`: the agent prepares, the human signs. I may stage the file, draft the exact commands, and run read-only verification. The `ssh-keygen -Y sign` invocation is a governor action — the signing key is governor-controlled and its use is a governor decision, not mine.
- `reflex.5`: the file is canonical **under the signing key's domain — subtract.ing**. GitHub or any git remote is mirror-only; if a mirror disagrees with subtract.ing, subtract.ing wins. The verifier's trust root is the domain, not the repo host.
- `reflex.2`: signing format is `ssh-keygen -Y sign` / `-Y verify`. Don't invent a wrapper or a new envelope.

## Which machine does what

- **Rousseau (this node, 01):** holds the canonical `~/subtract.ing` tree, is the governor's workstation, and is where the file is authored, signed, and deployed to the domain. This is the only machine that pushes canonical.
- **Emile (m2mini):** does not push. Compute/offload only — irrelevant to this task.
- **Surface (surfacepro8):** does not push. Governor terminal, no deploy authority.
- **acer1660ti:** NOT formation, NOT authoritative. May hold a warm backup copy of the published artifacts; never serves canonical.

## Steps

**0. Ground truth.** `bash ~/scripts/audit-health.sh` — confirm DNS for subtract.ing, deploy path health, and that the signing key + `allowed_signers` are present and unrotated. Don't proceed on a layer whose foundation is unresolved.

**1. Verify current signing state (loop.before.1–2, reflex.4).**
- `git -C ~/subtract.ing log --oneline -5` and `git -C ~/subtract.ing status` — clean tree, known head.
- Inspect the allowed-signers file (e.g. `~/.ssh/allowed_signers` or the in-repo `subtract.ing/allowed_signers`): confirm the identity line and the `ssh-ed25519 AAAA…` pubkey that subtract.ing publishes.
- Re-verify the existing manifest's signature with `ssh-keygen -Y verify` so the chain you're extending is sound. Surface any unsigned drift to the governor before continuing (loop.before.3).

**2. Write the file.** Create `~/subtract.ing/<path>/<name>.txt` with the final content. Freeze it — no edits after signing.

**3. Sign (governor action).**
```
ssh-keygen -Y sign -f ~/.ssh/<subtract-signing-key> -n file ~/subtract.ing/<path>/<name>.txt
```
Produces `<name>.txt.sig` (an `SSH SIGNATURE` armored blob). Namespace `file` must be the same string the published verify instructions tell strangers to use — pick it once, document it, never vary it.

**4. Publish to the canonical domain.** Deploy via whatever mechanism currently serves subtract.ing (confirmed in step 0 — likely a commit to `~/subtract.ing` + the site's publish step) so that these resolve over TLS:
- `https://subtract.ing/<path>/<name>.txt`
- `https://subtract.ing/<path>/<name>.txt.sig`
- `https://subtract.ing/allowed_signers` — the identity + pubkey, reachable under the same domain. This is the load-bearing part: a stranger gets the key from the signing domain, not from a README or a git host.

   In `allowed_signers`, pin a validity window so the claim survives key rotation:
   `jns@subtract.ing valid-after="20260510",valid-before="20280101" ssh-ed25519 AAAA…`
   If the key ever rotates, the retired key stays listed with its closed window — old signatures keep verifying.

**5. Mirror (optional, explicitly non-authoritative).** `git push` to GitHub/etc. if desired. Label it mirror-only in the repo. It proves nothing about authorship on its own.

**6. Independent timestamp (belt-and-suspenders for "a year from now").** Submit `https://subtract.ing/<path>/<name>.txt` to `web.archive.org/save/` so an external party corroborates existence-at-date, independent of subtract.ing's own history.

**7. Close the loop (loop.after).** Add `<name>.txt` (and its sig) to the subtract.ing manifest; re-sign the manifest with `ssh-keygen -Y sign`; deploy the updated manifest + manifest sig the same way as step 4.

## How a stranger verifies, one year later

1. Fetch over HTTPS: `<name>.txt`, `<name>.txt.sig`, and `allowed_signers` — all from `subtract.ing`.
2. Read the identity principal from `allowed_signers` (e.g. `jns@subtract.ing`).
3. Run:
   ```
   ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s <name>.txt.sig < <name>.txt
   ```
4. Exit 0 + `Good "file" signature for jns@subtract.ing` ⇒ the file is authentic and unmodified, authored by the holder of the subtract.ing signing key. Any byte change to the `.txt`, wrong namespace, or a key not in `allowed_signers` ⇒ non-zero exit, claim fails.
5. Trust chain: TLS proves the bytes came from `subtract.ing`; `subtract.ing` serving the `allowed_signers` *is* the authority binding (the signing key's domain, per `reflex.5`); the SSH signature binds the file to that key. The GitHub mirror and the Wayback snapshot are corroboration, not the root — a verifier who only had the git copy and no `allowed_signers` from the domain has a suggestion, not a verified claim.

One open item I'd resolve in step 0 before doing any of this for real: the exact deploy path that publishes `subtract.ing` (static host? rsync? CI from the repo?), because that determines whether step 4 is a `git push` or a separate publish command — and that's the only place this plan currently says "whatever mechanism."
