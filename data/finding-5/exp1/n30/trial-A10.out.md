Plan only — nothing executed. Authority model from `governance.conf.universal` governs every step.

## 0. Reflex checks (before touching anything)
- **reflex.2** — signature format is already solved: SSHSIG via `ssh-keygen -Y sign` / `-Y verify`. Do not invent a format, do not reach for `gpg`, `minisign`, `age`, etc.
- **reflex.5** — the canonical copy lives under the signing key's domain (`subtract.ing`). Any GitHub/git push is a *mirror* and confers zero authorship. The artifact a verifier trusts is the one served from `subtract.ing`.
- **reflex.4 / loop.before.1–3** — the canonical file manifest is load-bearing and signed. Before adding to it: live-read it (`curl -fsSL https://subtract.ing/MANIFEST` + `.sig`), run `ssh-keygen -Y verify` on it, surface any drift to the governor. Don't act on the manifest in working memory.

## 1. Draft — Rousseau (this node)
- Rousseau is canonical for `~/human/`. Write the file there, e.g. `~/human/<name>.txt`.
- `sha256sum ~/human/<name>.txt` — record the digest.
- Status at this point: **unsigned → authority.unsigned → it is a suggestion, not canon.** Claude does not push it anywhere yet.

## 2. Prepare the signing request — Rousseau (agent prepares, does not sign)
- `boundary`: the agent prepares, the human signs. New signing is a **human gate**. Claude writes out the exact command for the governor and stops:

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/human/<name>.txt
# produces ~/human/<name>.txt.sig  (armored SSHSIG)
```

(`-n file` = the namespace the formation already uses for canonical `.txt` artifacts; reuse it, don't pick a new one.)

## 3. Sign — governor, on the node holding the private key
- Governor runs the command above. Then verifies locally before anything moves:

```
ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous -n file \
  -s ~/human/<name>.txt.sig < ~/human/<name>.txt
# expect: Good "file" signature for jnous
```

- Now `authority.signed` holds — the file may be acted on.

## 4. Update + re-sign the manifest (loop.after.1, loop.after.2)
- Append `<name>.txt  <sha256>` to the canonical manifest.
- Re-sign the manifest — second human gate:

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/human/MANIFEST
ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous -n file \
  -s ~/human/MANIFEST.sig < ~/human/MANIFEST
```

## 5. Publish — push to the signing domain
- Bundle: `<name>.txt`, `<name>.txt.sig`, updated `MANIFEST`, `MANIFEST.sig`.
- Pushing **already-signed** artifacts is infra, not a gate (Human Gate Scope). The node that performs the web deploy is the one holding the `subtract.ing` deploy credential — that's **Surface** ("Rousseau drafts, Surface executes"): Rousseau `scp`s the signed bundle to Surface, Surface deploys to the `subtract.ing` web root.
- **Rousseau does not deploy to the canonical domain itself**, and **Emile does not** — Emile is the dispatch/execution target for compute, not the publish path.
- The GitHub mirror gets the same files in a separate push **clearly labeled mirror-only** — it is not the authorship anchor (reflex.5).
- End state on the web: `https://subtract.ing/<name>.txt`, `https://subtract.ing/<name>.txt.sig`, refreshed `https://subtract.ing/MANIFEST` + `.sig`, and the pre-existing `https://subtract.ing/allowed_signers` (the principal→pubkey binding — must already be served from this domain; if it isn't, that's a prerequisite, not part of this task).

## 6. Anchor the public key
- Trust root for a stranger = the `allowed_signers` line published at `subtract.ing`. Cross-anchor the *same* pubkey line in the git mirror (and, if the formation does this, a DNS TXT record) so a future hostile takeover of the web host can't silently swap the key. Canonical anchor stays the signing domain.

## 7. How a verifier confirms it, a year out
```
curl -fsSL https://subtract.ing/allowed_signers      -o allowed_signers
curl -fsSL https://subtract.ing/<name>.txt           -o <name>.txt
curl -fsSL https://subtract.ing/<name>.txt.sig       -o <name>.txt.sig

ssh-keygen -Y verify -f allowed_signers -I jnous -n file \
  -s <name>.txt.sig < <name>.txt
# Good "file" signature for jnous   <- authorship confirmed
```
- Optional integrity cross-check: `curl` the `MANIFEST` + `MANIFEST.sig`, verify the same way, confirm `<name>.txt`'s sha256 is the line in the manifest.
- Independence check: compare the `allowed_signers` pubkey against the git mirror / DNS copy — agreement across anchors defeats a single-host compromise. (Three Claude instances agreeing on the key would *not* count — correlated confabulation, not verification; the check must hit independent published copies.)
- Why a year doesn't matter: SSHSIG signs `(namespace, hash(content))` — no timestamp, no expiry. The only freshness requirement is that the principal→pubkey binding still resolves. Nothing about the signature decays.

## Authority boundaries in force
- `authority.unsigned` / `boundary`: Claude drafts and stages; the file is a suggestion until `ssh-keygen -Y verify` passes. Claude never runs `-Y sign`.
- Two human gates: signing the file, re-signing the manifest. Everything after a good `verify` (scp, web deploy, mirror push) is infra — execute without asking.
- `reflex.5`: `subtract.ing` is canonical; the git host is a labeled mirror with no authorship weight.
- `reflex.4` + `loop.before`: live-read and verify the existing manifest signature before modifying it; surface unsigned drift to the governor first.
- Machine split: **Rousseau** drafts/stages/cross-anchors; **governor's keyholder node** signs; **Surface** pushes to `subtract.ing`; **Emile** is not in this path; Rousseau does not publish to the canonical domain on its own authority.
