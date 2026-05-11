## Plan: publish a verifiable `.txt` to subtract.ing

### 0. Reflex checks before anything (antecedent gates)

- **reflex.2 — don't invent a signature format.** `ssh-keygen -Y sign` / `-Y verify` (SSH signature, namespace `file`) already does this. Use it. No detached-GPG, no homemade scheme.
- **reflex.5 — canonical lives under the signing key's domain.** The authoritative copy is the one served from `https://subtract.ing/…`. GitHub or any other host is **mirror-only** and gets flagged as such.
- **reflex.4 — no assertion without a live read.** I don't get to say "it's published and verifiable" until I've `curl`'d it back and run `-Y verify` against it post-deploy.
- **loop.before.1–3** — before I touch the canonical tree: `ssh-keygen -Y verify` the current `MANIFEST.sig`, surface any unsigned drift, governor decides sign/continue/abort.

### 1. Prepare — rousseau, agent does this (reversible, no gate)

On rousseau (`~/subtract.ing/`, the canonical working copy):

```
cd ~/subtract.ing
git log --oneline -5        # ground truth, like the hosuni.c discipline
git status
# author the file
$EDITOR newfile.txt
wc -l newfile.txt
# fold it into the manifest the rest of the tree is signed under
$EDITOR MANIFEST            # add path + sha256 of newfile.txt
sha256sum newfile.txt       # the value that goes in MANIFEST
```

This is staging-tier work — write the file, edit the manifest text. Per *Human Gate Scope* and *Stop Asking on Reversible Ops*, I don't ask permission for this part.

### 2. Sign — governor only (HUMAN GATE: `boundary`, `authority`, loop.before.3)

New signing is the one hard gate. The agent prepares; the human signs. The private key (`jnous` identity) lives in the governor's control — signing happens on whatever machine holds it; if that isn't rousseau, the resulting `.sig` is copied to rousseau afterward, and *that copy step is plain infra*, not a gate.

Governor runs:

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file newfile.txt   # -> newfile.txt.sig
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file MANIFEST      # -> MANIFEST.sig (re-sign, manifest changed)
```

I warn the governor first (*Warn Before Human Gates*) that these two commands are the only thing needed from them.

### 3. Verify locally before publishing — agent (read-only, reversible)

```
ssh-keygen -Y verify -f allowed_signers -I <governor-principal> -n file -s newfile.txt.sig < newfile.txt
ssh-keygen -Y verify -f allowed_signers -I <governor-principal> -n file -s MANIFEST.sig    < MANIFEST
```

Both must print `Good "file" signature` / exit 0. `allowed_signers` is the line `<principal> ssh-ed25519 AAAA…` for the signing key — and it must itself be one of the files published to subtract.ing, or a stranger has nothing to verify against.

### 4. Publish — which machine pushes, which does not

- **rousseau (01, M1 Studio) pushes.** It's the formation's canonical node (`~/human/` and `~/subtract.ing/` canonical, governor's workstation). It pushes to the subtract.ing origin the site is served from (`rsync`/`git push` to that origin — same mechanism already in use for `governance.conf.universal.txt`). Payload: `newfile.txt`, `newfile.txt.sig`, updated `MANIFEST`, `MANIFEST.sig`, `allowed_signers`.
- **emile (m2mini) does not push and does not sign.** Compute-offload node only. If step 1 needed heavy grunt work I'd `ssh m2mini "claude -p …"`, but it touches nothing canonical.
- **acer / "Media" does not push and is never authoritative.** Out-of-formation NAS / warm-backup tier. It may receive a copy of the signed bundle into backup, but per reflex.5 it's a mirror — a verifier pointed there is being pointed at a mirror.
- **GitHub / any git host: mirror-only.** Update it for convenience, but the canonical claim is "served from subtract.ing under the signing key's domain."

### 5. loop.after — close the session

- `loop.after.1` — manifest already updated in step 1.
- `loop.after.2` — manifest already re-signed in step 2.
- Housekeeping: fold `newfile.txt` + `.sig` + new `MANIFEST`/`.sig` into the SDXC air-gap snapshot on the next `discover.sh`/refresh cycle (same as the 2026-04-15 refresh). Optional, not load-bearing for verifiability.
- Then: `curl https://subtract.ing/newfile.txt`, `curl https://subtract.ing/newfile.txt.sig`, re-run the `-Y verify` from step 3 against the *live fetched* copies (reflex.4). Only now do I report "published and verifiable."

### 6. How a stranger verifies it a year from now

```
curl -O https://subtract.ing/newfile.txt
curl -O https://subtract.ing/newfile.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <governor-principal> -n file -s newfile.txt.sig < newfile.txt
```

`Good "file" signature` + exit 0 ⇒ the file was signed by the key published under the signing domain. Strength comes from three things, not just the one command:

1. The `allowed_signers` key is fetched **from subtract.ing itself** — the signing key's own domain — not from a git mirror that a third party could rewrite (reflex.5).
2. The **same key** signs `MANIFEST.sig` and every other canonical artifact in the tree, so the file isn't a one-off — it's part of a continuous signed ledger.
3. Anyone holding an **older** signed manifest (from before this file existed) sees the identical key, giving trust-on-first-use continuity across the year.

If the verifier only has a GitHub mirror, they can check the signature math but must treat provenance as unconfirmed until they reach `subtract.ing` — that's the reflex.5 boundary, stated to them explicitly in the manifest header.

### Authority boundaries, summarized

| Action | Who | Why |
|---|---|---|
| Write `newfile.txt`, edit `MANIFEST` text | agent (rousseau) | reversible staging-tier work |
| `ssh-keygen -Y sign` (file + manifest) | **governor only** | `boundary` — the signature is the authority; new signing is the human gate |
| Copy resulting `.sig` onto rousseau | agent | already-signed artifact movement = infra, not a gate |
| `ssh-keygen -Y verify` (pre- and post-publish) | agent | read-only; required by reflex.4 |
| Push to subtract.ing origin | agent (rousseau) | rousseau is the canonical formation node |
| Update GitHub / acer copies | agent | mirror-only, explicitly non-authoritative |
| Decide sign / continue / abort on any unsigned drift found in the tree | governor | loop.before.3 |

No subagents at any step (per CLAUDE.md); any parallel work goes to emile via `ssh m2mini "claude -p"`.
