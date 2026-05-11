Plan only — nothing executed.

## 0. Ground the assumptions first
- `bash ~/scripts/audit-health.sh` — DNS/creds/drive state is ground truth, per session-start rule.
- Look at how an existing canonical file is laid out before inventing anything (reflex.1 — mirror the existing primitive, don't add a new flow): on Rousseau, inspect `~/subtract.ing/` for `governance.conf.universal.txt`, its `.sig`, the `allowed_signers` file, and the manifest. Whatever `-n <namespace>` and identity those used is what this file must use. (Memory: signing identity is `jnous`; confirm against the actual `.sig`.)

## 1. Draft + stage on Rousseau (this M1 Studio)
Rousseau is the archive/canonical node and the governor's workstation, so the file originates here.
- Write `~/subtract.ing/<name>.txt` (Write/Edit tool, or `$EDITOR`).
- `cd ~/subtract.ing && git log --oneline -5 && git status && wc -l <name>.txt` — state what you see before proceeding.
- Agent's job stops at "file staged + manifest diff prepared." It does **not** sign.

## 2. Pre-act loop (loop.before.1–3)
- Verify the current head of trust still verifies — e.g.:
  `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST`
- `git status --porcelain` — surface any unsigned drift in the tree.
- Human decides: sign / continue / abort. Do not proceed past this on conversation momentum.

## 3. Human gate — signing (governor, on the box holding the signing key)
This is the authority boundary: `boundary` — the agent prepared, the human signs.
- File: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt` → produces `<name>.txt.sig`.
- `-n` namespace and key path must match the existing `.sig` files exactly, or strangers' verify commands won't line up. Warn before running — `ssh-keygen` may prompt for a key passphrase (macOS popup).

## 4. Update + sign the manifest (loop.after.1–2)
- Add `<name>.txt`, its `sha256sum`, and signer identity to the canonical `MANIFEST` in the format already in use.
- Re-sign: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST` → new `MANIFEST.sig`. This chains the new file into the archive's signed history rather than leaving it as a lone artifact.

## 5. Publish — canonical vs mirror (reflex.5)
- Canonical publish = the HTTPS origin under the signing key's domain: `https://subtract.ing/<name>.txt`, `…/<name>.txt.sig`, updated `MANIFEST` + `MANIFEST.sig`, and `allowed_signers` must be reachable at `https://subtract.ing/allowed_signers`. Push via whatever node holds deploy creds to the subtract.ing origin (confirm in step 0); that push is "infra work on already-signed artifacts," not a human gate.
- A `git push` to GitHub or any git host is a **mirror only** — it does not establish authorship and is not where a verifier should fetch the trust anchor.

**Machine roles:**
- **Rousseau (M1 Studio):** drafts the file, holds the canonical `~/subtract.ing` tree, runs pre/post verification reads; the governor's `ssh-keygen -Y sign` happens here if the signing key lives here.
- **Emile (M2 mini):** execution offload only; can carry the deploy push if it holds creds, but never signs and is not canonical.
- **Media (acer1660ti):** not formation — no inference, no signing, no publish, never in this path.
- **Surface:** governor terminal; pulls, never originates canonical content.
- **Git host:** mirror push only; never authoritative.

## 6. Self-verify before asserting "done" (reflex.4 — an assertion that blocks is an action)
```
curl -fsSL https://subtract.ing/<name>.txt      -o /tmp/v.txt
curl -fsSL https://subtract.ing/<name>.txt.sig  -o /tmp/v.txt.sig
curl -fsSL https://subtract.ing/allowed_signers -o /tmp/allowed_signers
ssh-keygen -Y verify -f /tmp/allowed_signers -I jnous -n file -s /tmp/v.txt.sig < /tmp/v.txt
```
Only report it published/verifiable if this prints `Good "file" signature for jnous`. Until then it's a suggestion, not a fact (authority.unsigned, and the "verify before presenting as fact" rule).

## 7. How a stranger confirms the claim a year from now
1. `curl -O https://subtract.ing/<name>.txt` and `curl -O https://subtract.ing/<name>.txt.sig`.
2. Fetch the trust anchor from the **same TLS domain**: `curl -O https://subtract.ing/allowed_signers` — a GitHub copy is a mirror, not the authority.
3. `ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt` → expect `Good "file" signature for jnous`.
4. Optional but stronger: `curl -O https://subtract.ing/MANIFEST{,.sig}`, verify `MANIFEST.sig` the same way, and confirm `<name>.txt`'s sha256 appears in it — ties the file into the archive's signed lineage.

## 8. Longevity caveat (build the durability in now, not later)
The verification only holds as long as that ed25519 signing key isn't rotated or revoked. So the plan must include: either the key outlives the claim, or any rotation is itself recorded as a signed old→new entry in the `MANIFEST`, and `allowed_signers` keeps the old identity entry so historical signatures still verify. Without that, "verifiable a year from now" isn't guaranteed.
