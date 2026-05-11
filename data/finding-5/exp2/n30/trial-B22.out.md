I'd normally run `bash ~/scripts/audit-health.sh` before anything — but you've said plan-only, so I'm not executing it. It's step 0 below.

# Plan: publish a verifiable `.txt` to subtract.ing

## 0. Ground truth (before touching anything)
- `bash ~/scripts/audit-health.sh` — read DNS/creds/drive/node state. Don't proceed on assumptions.
- `cd ~/subtract.ing && git log --oneline -5 && git status` — confirm the canonical working tree is clean and current. If my working memory of it is stale, re-read before patching (same discipline as hosuni.c).

## 1. Prepare the artifact (agent does this)
- Write `~/subtract.ing/<name>.txt` in the working copy on **Rousseau**. This is preparation only — an unsigned file is `authority.unsigned`: suggestion, possibly confabulation. Not citable yet.
- `shasum -a 256 ~/subtract.ing/<name>.txt` — record the digest for the manifest.

## 2. Sign (human only — this is the authority boundary)
- `boundary`: the agent prepares, the human signs. I do not hold or invoke the private signing key. The governor runs:
  - `ssh-keygen -Y sign -f <governor signing key> -n <namespace> ~/subtract.ing/<name>.txt`
  - → produces `~/subtract.ing/<name>.txt.sig` (SSHSIG, armored `-----BEGIN SSH SIGNATURE-----`).
- `-n <namespace>`: reflex.2 — do **not** invent it. Read an existing `*.sig` in `~/subtract.ing/` and reuse whatever namespace subtract.ing artifacts already use (e.g. `file` or `subtract.ing`). Confirm `ssh-keygen -Y verify` accepts that format before relying on it.
- Confirm the signing key's public half is already an entry in `~/subtract.ing/allowed_signers` (identity = governor's stable identifier, ideally with a `valid-after`/`valid-before` window). If not, that entry is added and that change is itself signed.

## 3. Verify locally before publishing (reflex.4)
- `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I <governor-identity> -n <namespace> -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt`
- Exit 0 required. Until this passes, nothing downstream happens.

## 4. Update + re-sign the manifest (loop.after.1, loop.after.2)
- Add the new file's path + sha256 to `~/subtract.ing/`'s manifest.
- Re-sign the manifest with the same `ssh-keygen -Y sign` invocation. The manifest is the formation's own record that this `.txt` is a canonical artifact — it survives even if the web origin doesn't.

## 5. Commit and publish — which machine, which doesn't
- **Rousseau** (this node, archive + governor workstation): stages and commits — `git add <name>.txt <name>.txt.sig <manifest> <manifest>.sig && git commit`.
- **Canonical publish** = deploying these files under the signing key's domain, i.e. the HTTPS origin serving `subtract.ing/` (where `governance.conf.universal.txt` lives). reflex.5: that domain is canonical; **GitHub / any git host is mirror-only** — pushing there does not make the file authoritative. The push to the canonical web root is done from whichever node is the subtract.ing deploy origin (verify in audit-health output / ssh config; if that's Rousseau, Rousseau pushes).
- **Emile (m2mini): does not push.** It's execution offload only.
- **Surface: does not push.** Governor terminal.
- After deploy: `curl -sS https://subtract.ing/<name>.txt | shasum -a 256` and re-run the `ssh-keygen -Y verify` against the *fetched* copies — a live read confirming the claim, not a memory of having done it.

## 6. How a stranger verifies, a year from now
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <governor-identity> -n <namespace> -s <name>.txt.sig < <name>.txt
echo $?    # 0 == authentic, signed by the key bound to <governor-identity>
```
- The trust root is the **signature**, not the URL and not me. `authority.source` is the human; the signature proves it. If subtract.ing is offline in a year, the `.sig` plus the public key (from the manifest, a pinned commit, a web-archive snapshot, or any mirror) still verifies — that's why this is SSHSIG and not "trust the host."
- The verifier should also: (a) check the `allowed_signers` validity window covers the file's claimed date, (b) cross-check that the same pubkey appears in at least one independent place (the signed manifest, prior signed artifacts), so a swapped `allowed_signers` on a compromised host doesn't fool them.

## Authority boundaries in one place
- Agent: writes the `.txt`, edits the manifest, stages commits, runs `-Y verify` reads, curls the published copy. Never signs.
- Human: holds the signing key, runs `ssh-keygen -Y sign`, decides to publish.
- Unsigned = not authoritative (`authority.unsigned`). Signed-and-verified = act on it (`authority.signed`).
- Canonical = subtract.ing domain. Git host = mirror. Don't cite the mirror as the source.
