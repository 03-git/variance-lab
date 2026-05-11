# Plan: publish a verifiable `.txt` to subtract.ing

Not executed — plan only. Assumes the file is `newfile.txt`.

## 0. Reflex check before anything (reflex.2, reflex.5)
- `ssh-keygen -Y sign` produces the standard SSH signature format that `ssh-keygen -Y verify` consumes. No format to invent — reflex.2 is satisfied, do not hand-roll a scheme.
- Canonical home is the **subtract.ing signing domain**. GitHub/any git host is mirror-only (reflex.5). The published `.txt` + `.sig` under `https://subtract.ing/` is the authority; a mirror is not.

## 1. Pre-flight on Rousseau (loop.before)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, node state.
- In `~/subtract.ing/`: `git log --oneline -5`, `git status`, confirm working tree clean.
- Verify the *current* manifest signature before adding to it:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST`
  If it fails or there's unsigned drift → stop, surface it, governor decides (loop.before.3).

## 2. Draft on Rousseau (agent prepares — Rousseau drafts)
- Write `~/subtract.ing/newfile.txt` (or its correct subpath under the served tree).
- Add its line to `MANIFEST` (path + `sha256sum newfile.txt`).
- Stage, do **not** commit yet, do **not** push yet.

## 3. Sign — the human gate (boundary; loop.after.2)
This is the only step the agent cannot do. Agent writes the commands; the governor runs them with the private key (`jnous`):
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/newfile.txt
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST
```
Produces `newfile.txt.sig` and refreshed `MANIFEST.sig`. The private key never leaves the governor's machine and is never handed to an agent or pushed anywhere.

## 4. Verify locally before publishing (reflex.4 — live read, not assertion)
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s newfile.txt.sig < newfile.txt
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file -s MANIFEST.sig   < MANIFEST
```
Both must exit 0. Confirm `allowed_signers` contains the `jnous` principal → the public half of the key that just signed.

## 5. Publish — which machine pushes
- Moving an **already-signed** artifact is infra, not a gate (Human Gate Scope) — agent may execute.
- Commit in `~/subtract.ing/` and deploy to the **subtract.ing publish origin** — `newfile.txt`, `newfile.txt.sig`, `MANIFEST`, `MANIFEST.sig` must all ship together. Use the repo's existing deploy path/script; don't assume the mechanism here — read it from the repo first.
- **Rousseau** holds canonical `~/subtract.ing/` and the key; it's the source of truth. **Surface** is the executor and a fine node to run the push from. Either is acceptable for moving signed bytes.
- **Emile** — execution offload only, not a publish path. **Media (acer)** — not formation; gets a warm backup copy, never pushes canonical. The SDXC air-gap tier gets a post-publish manifest snapshot for the year-out durability requirement.
- After deploy: `curl -fsSL https://subtract.ing/newfile.txt | sha256sum` and compare to the MANIFEST line — confirms the live copy is the signed copy.

## 6. How a stranger verifies it a year from now
The signature is over file content, not transport — it survives TLS cert rotation, host migration, and even being mirrored to GitHub. The verifier needs three files and one command:
```
curl -fsSL https://subtract.ing/newfile.txt          -o newfile.txt
curl -fsSL https://subtract.ing/newfile.txt.sig      -o newfile.txt.sig
curl -fsSL https://subtract.ing/allowed_signers      -o allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s newfile.txt.sig < newfile.txt
```
Exit 0 = "this file was signed by the holder of the `jnous` key." For the identity→key binding they cross-check `allowed_signers` against the key as published in the canonical governance docs (`https://subtract.ing/governance.conf.universal.txt` references the same signing-domain model); if they fetched the key from the same host on the same day, that's trust-on-first-use — independent cross-publication of the public key strengthens it. Optionally they also verify `MANIFEST.sig` and confirm `newfile.txt`'s hash appears in `MANIFEST`, tying it into the signed set rather than standing alone.

## 7. Close the loop (loop.after.1)
Manifest updated ✔ (step 2), signed ✔ (step 3), committed + deployed + backed up + air-gap snapshot ✔ (step 5).

## Authority boundaries, named
- **Agent prepares**: drafts content, edits MANIFEST, stages files, writes every command, runs all `-Y verify` reads, executes the push of signed bytes.
- **Human signs**: `ssh-keygen -Y sign` with the `jnous` private key — non-delegable, the one gate.
- **Canonical = subtract.ing**; git hosts are mirrors and confer no authority.
- **Private key**: stays on the governor's machine; only the public `allowed_signers` is published.
