Planning only — not running `audit-health.sh` or anything else, per your "do not execute" instruction. In a real run that audit would gate step 0.

# Plan: publish a verifiable `.txt` to subtract.ing

## Authority boundaries (these constrain every step below)
- **The agent prepares; the human signs.** `governance: boundary` + `authority.source = the human`. I (Rousseau's session) write the file, stage it, draft the manifest entry and the `allowed_signers` line. I never hold or invoke the signing private key.
- **No subagents, no Emile, no Acer for the signing/publish path.** Emile is execution offload only; handing it `~/.ssh/id_ed25519` would breach the boundary. Acer is the NAS/mirror tier, not formation, not a canonical publish target.
- **Canonical = the signing key's domain.** `reflex.5`: the load-bearing copy lives at `https://subtract.ing/...`. GitHub or any git host is **mirror-only** — a verifier must not treat it as authoritative.
- **`reflex.2`: don't invent a signature format.** Use `ssh-keygen -Y sign` / `-Y verify`. It already does detached signatures with namespaces and an `allowed_signers` trust file. Nothing custom.
- **`loop.before`**: before publishing, verify the *current* manifest signature, surface any unsigned drift, human decides sign/continue/abort.

## Step 0 — ground truth (Rousseau)
- `bash ~/scripts/audit-health.sh` — confirm DNS for subtract.ing, deploy creds, drive state.
- On the canonical hosuni/runtime tree: `git log --oneline -5`, `git status`, and `wc -l` on anything I'm about to touch. State the timestamps/line counts observed.

## Step 1 — author the file (Rousseau, agent)
- Write `newdoc.txt` into the canonical working tree (the subtract.ing runtime/site source, e.g. `~/subtract.ing/...`), not `/tmp`.
- Record its hash for the manifest: `shasum -a 256 newdoc.txt`.

## Step 2 — verify last signature, surface drift (Rousseau, agent → human)
- `ssh-keygen -Y verify -f <allowed_signers> -I <governor-identity> -n manifest -s MANIFEST.sig < MANIFEST` — confirm the existing manifest is intact.
- `git status` / diff the tree against the last signed manifest; report any unsigned changes.
- **Human decides.** No publish proceeds on unsigned drift.

## Step 3 — sign the file (HUMAN, on the machine holding the key)
Run by the governor, interactively — not by me, not over SSH to Emile:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file newdoc.txt
```
Produces `newdoc.txt.sig` (armored `-----BEGIN SSH SIGNATURE-----`). Namespace `file` is the documented convention; keep it consistent with whatever subtract.ing already uses for published artifacts.

## Step 4 — make the trust root publishable (agent prepares, human confirms)
A stranger a year out needs to map identity → key. Maintain `allowed_signers.txt` at the canonical domain:
```
jns@subtract.ing namespaces="file,manifest" ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...
```
- Keep **old** keys in this file (don't delete on rotation) and use `valid-before=` / `valid-after=` options so signatures stay verifiable after a future rotation.
- This file should itself be signed (it's load-bearing) and ideally cross-anchored: a `TXT` record on `subtract.ing` carrying the key fingerprint, plus the file linked from a stable path. The trust claim is "this key is published, signed, at the domain the content claims to originate from."

## Step 5 — update and sign the manifest (agent prepares, HUMAN signs) — `loop.after.1/2`
- Add `newdoc.txt` + its SHA-256 to `MANIFEST`.
- Human: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n manifest MANIFEST` → `MANIFEST.sig`.

## Step 6 — publish to the canonical host (Rousseau pushes)
- Deploy `newdoc.txt`, `newdoc.txt.sig`, updated `allowed_signers.txt` (+ its `.sig`), `MANIFEST`, `MANIFEST.sig` to `https://subtract.ing/` via whatever the existing deploy path is (rsync/scp to the web host from Rousseau, or the site's publish script — confirmed in Step 0).
- **Surface** does not push (it's the governor terminal that authorizes). **Emile** does not push. **Acer** receives only the warm-backup mirror after the fact, and is explicitly non-canonical.
- Mirror to the git host if that's the convention — labeled mirror-only.

## Step 7 — self-verify from outside (Rousseau, agent)
Fetch over plain HTTPS as a stranger would and confirm before declaring done:
```
curl -sO https://subtract.ing/newdoc.txt
curl -sO https://subtract.ing/newdoc.txt.sig
curl -sO https://subtract.ing/allowed_signers.txt
ssh-keygen -Y verify -f allowed_signers.txt -I jns@subtract.ing -n file -s newdoc.txt.sig < newdoc.txt
```
Expect `Good "file" signature for jns@subtract.ing`. Report the literal output.

## How a stranger verifies, a year from now
1. `curl` the three files from `subtract.ing`: `newdoc.txt`, `newdoc.txt.sig`, `allowed_signers.txt`.
2. Independently corroborate the key in `allowed_signers.txt` — e.g. `dig +short TXT subtract.ing` against the published fingerprint, and check `allowed_signers.txt.sig`. (This is the only "trust" leap; everything downstream is math.)
3. `ssh-keygen -Y verify -f allowed_signers.txt -I jns@subtract.ing -n file -s newdoc.txt.sig < newdoc.txt`.
4. Optional: pull `MANIFEST` + `MANIFEST.sig`, verify with namespace `manifest`, and confirm `shasum -a 256 newdoc.txt` matches the manifest entry — ties the file into the signed set, not just a standalone blob.

The signature is over content bytes, so it survives mirroring, CDN caching, and re-hosting; what must not drift is the key↔identity binding at the domain — hence keeping retired keys in `allowed_signers.txt` with validity windows.

## What breaks if you skip pieces
- Skip `allowed_signers` publication → verifier has a signature but no trusted key; claim is unverifiable.
- Delete the old key on rotation → every previously published `.sig` fails `-Y verify`.
- Treat the GitHub mirror as canonical → violates `reflex.5`; an attacker who controls the mirror can swap content with no signature check.
- Let me (agent) or Emile run `ssh-keygen -Y sign` → violates `boundary`/`authority.source`; the signature no longer proves the human.
