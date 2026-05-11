# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. Steps, tools, boundaries below.

## 0. Ground truth first
- `bash ~/scripts/audit-health.sh` — confirm DNS, drives, the subtract.ing working tree, and key availability before touching anything.
- `git -C ~/subtract.ing log --oneline -5` and `git -C ~/subtract.ing status` — know the current head and whether the tree is dirty.

## 1. Honor reflex.2 before inventing anything
Don't guess the signature/manifest format. Inspect what's already canonical:
- `ls ~/subtract.ing` and find an existing pair, e.g. `governance.conf.universal.txt` + `governance.conf.universal.txt.sig`.
- `ssh-keygen -Y verify` that existing pair (see §6 form) to learn the **namespace** (`-n …`) and the **principal/identity** string used in `allowed_signers`. Match it exactly. If there's a `MANIFEST`/`manifest.txt` and an `allowed_signers` file in the tree, note their paths and formats.

## 2. Agent prepares (no human gate — reversible)
- Write the new file at its canonical path, e.g. `~/subtract.ing/newfile.txt`. Use `Write`/editor.
- `sha256sum ~/subtract.ing/newfile.txt` — record the digest for the manifest entry.
- Stage the manifest change: add `newfile.txt <sha256>` (matching the existing manifest's columns) to the manifest file. Leave it unsigned.
- This is all staging-area work — execute it without asking (per the reversible-ops rule). Do **not** sign, do **not** push yet.

## 3. Human gate — the only gate (boundary; loop.before.3)
Surface to the governor: "new file `newfile.txt` staged, manifest updated, here's the diff and the sha256 — sign or abort." The agent cannot cross this line; `ssh-keygen -Y sign` with the private key is the human's act and is what proves authorship.

Governor runs, on the machine that holds the private key `~/.ssh/jnousign` (the key never moves to another node):
```
ssh-keygen -Y sign -f ~/.ssh/jnousign -n <namespace-from-§1> ~/subtract.ing/newfile.txt
ssh-keygen -Y sign -f ~/.ssh/jnousign -n <namespace-from-§1> ~/subtract.ing/<manifest>
```
Produces `newfile.txt.sig` and a refreshed `<manifest>.sig`. (Sign the manifest too so the file's hash is itself covered — defense in depth if the standalone `.sig` is ever questioned.)

## 4. Which machine publishes
- **Rousseau (this M1 Studio)** is the canonical node — it holds `~/subtract.ing` and `~/human/` canonical. The commit and the push to the publishing remote originate **here**.
- `git -C ~/subtract.ing add newfile.txt newfile.txt.sig <manifest> <manifest>.sig`
- `git -C ~/subtract.ing commit -m "publish newfile.txt"` then `git push`
- Then run whatever deploys the served tree at `https://subtract.ing/` — also from rousseau. Per **reflex.5**, the GitHub remote is a *mirror*, not the authority; publication isn't done until the file is reachable at `https://subtract.ing/newfile.txt` under the signing key's domain. A green `git push` alone is not publication.
- **Emile (m2mini)** does not push canonical and does not sign — it's a pull-mirror / execution offload only.
- **Acer / "Media"** does not push canonical and does not sign — it's not formation, just a warm backup tier; it receives the mirrored copy, nothing more.
- Pushing the already-signed artifact between nodes afterward is plain infra work (per the human-gate-scope rule) — no further gate.

## 5. Close the loop (loop.after)
- Manifest already updated and signed in §2–3; confirm it's the version that landed in the published tree.
- Note the new head commit; if there's a session manifest in `~/human/sessions/`, record what was published and the sha256.

## 6. How a stranger verifies it, a year out
SSH signatures are over the file bytes and have no expiry (no `valid-after`/`valid-before` was set), so this holds indefinitely as long as the verifier can get the public key.

```
curl -fO https://subtract.ing/newfile.txt
curl -fO https://subtract.ing/newfile.txt.sig
curl -fO https://subtract.ing/allowed_signers      # principal -> pubkey map, published alongside
ssh-keygen -Y verify -f allowed_signers -I <principal-from-§1> -n <namespace-from-§1> \
  -s newfile.txt.sig < newfile.txt
```
- Exit 0 + "Good … signature" → the bytes were signed by the key bound to that principal.
- Cross-check: `sha256sum newfile.txt` must equal the entry in the (separately signed) `MANIFEST`; verify `MANIFEST.sig` the same way. Two independent confirmations of the same key.
- Trust root for the key: the verifier should pin `allowed_signers` out-of-band — it's referenced from the canonical `governance.conf.universal.txt` and the subtract.ing domain. If subtract.ing is down in a year, the GitHub mirror still carries `newfile.txt` + `.sig`, and verification still succeeds against the same pinned pubkey — the mirror is fine for *availability*, just not for *authority*.

## Authority boundaries, summarized
- **Agent (Claude on rousseau):** audit, inspect existing sig format, write the file, compute hashes, stage the manifest, and — after signing — commit/push/deploy/mirror. All reversible or already-signed; no permission needed.
- **Human (governor):** sole holder of `~/.ssh/jnousign`; the only actor who runs `ssh-keygen -Y sign`. New signing is the gate. The signature *is* the proof of authorship — not the commit author, not the agent's say-so.
- **reflexes in play:** 2 (don't invent a sig format — match the existing one), 4 (verify the last signature with a live read before acting), 5 (subtract.ing is canonical; git is mirror-only). **loop.before:** verify last sig → surface the unsigned new file → human signs/aborts. **loop.after:** manifest updated, signed.
