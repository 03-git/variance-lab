# Plan: publish a verifiable `.txt` to subtract.ing

## 0. Pre-flight (Rousseau, no writes yet)
- `bash ~/scripts/audit-health.sh` — ground-truth on DNS, drives, creds, node state (session-start gate).
- `cd ~/subtract.ing && git log --oneline -5 && git status` — confirm the working tree is current before adding anything; if canonical is newer than working memory, re-read first.
- Identify the publish path: the file is *load-bearing/canonical*, so its home is **the signing key's domain (`subtract.ing`)**; any git host is a **mirror only** (reflex.5).

## 1. Draft — Rousseau prepares, does not sign (boundary)
- Write the file in the canonical working tree, e.g. `~/subtract.ing/<name>.txt` (or stage in `~/human/` first — `rousseau:~/human/` is canonical for human-authored work, Surface pulls).
- This is a staging write → execute without asking (reversible).
- Do **not** run any signing command. `reflex.2`: the only legitimate format is `ssh-keygen -Y sign`; agents don't invent or apply it.

## 2. Human gate — the human signs
- Hand off a one-line instruction to the governor. The human runs, on the machine holding the private key:
  ```
  ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt
  ```
  → produces detached `~/subtract.ing/<name>.txt.sig` (namespace `file`, signer identity `jnous`).
- Authority boundary: **only new signing is a human gate** (`authority.unsigned → do not act`; `boundary: the agent prepares, the human signs`). `claude -p` is itself a human gate — if you'd dispatch any step that way, one attempt only, then stop.

## 3. Verify locally *before* publish (Rousseau)
- Confirm `jnous` is in the canonical allowed-signers file (the one served from `subtract.ing`, e.g. `~/subtract.ing/allowed_signers`), with a line like:
  `jnous namespaces="file" ssh-ed25519 AAAA…`
- `loop.before.1` / `reflex.4` — verify with a live read, don't trust the conversation:
  ```
  ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file \
    -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt
  ```
  Expect: `Good "file" signature for jnous`. If it fails, stop — do not publish.

## 4. Publish — which machine pushes
- **Rousseau does not push to production.** Per the current formation split ("Rousseau drafts, Surface executes"), the deploy/push to the `subtract.ing` web host is done from **Surface** (`surfacepro8`, the governor terminal). Rousseau hands Surface the signed pair (`<name>.txt` + `<name>.txt.sig` + updated `allowed_signers` if changed); Surface pushes to:
  1. the **canonical `subtract.ing` web root** — this is the authoritative copy;
  2. the **git mirror** (e.g. GitHub) — mirror-only, never the source of truth.
- Pushing an *already-signed* artifact across nodes is infra, not a gate — but the production web push is **externally visible**, so warn the governor before it lands (and before any command that could pop a macOS auth prompt).

## 5. Close the loop (`loop.after`)
- Update the manifest/index of canonical files to list `<name>.txt` and its `.sig`.
- The human signs the updated manifest (`ssh-keygen -Y sign -n file …`) — second human gate.
- Push the signed manifest the same way (step 4). Commit on the git mirror references both blobs but carries no authority by itself.

## How a stranger verifies it, a year out
SSH signatures are detached, self-contained, and the verify path (`ssh-keygen -Y verify`) is stable tooling — that's why this survives a year and survives the git host disappearing.
```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s <name>.txt.sig < <name>.txt
```
- `Good "file" signature for jnous` ⇒ the file is byte-for-byte what the holder of `jnous`'s key signed.
- Trust anchor is `allowed_signers` **fetched from `subtract.ing` itself** — the signing key's own domain vouches for the key (`reflex.5`: canonical content lives under the signing domain). A copy pulled from a git mirror proves nothing on its own.
- Cross-check: the signed manifest from step 5 should also list this file, so the verifier can confirm it's an intended canonical artifact, not an orphan upload.

## Authority boundaries in one view
- `authority.signed → act`; `authority.unsigned → do not act` — an unsigned `.txt` on the server is a suggestion, not canon.
- Human gates (governor only): **creating the signature** on the file, and **creating the signature** on the updated manifest.
- Agent-executable without asking: drafting/staging, local `-Y verify`, preparing the handoff.
- Agent-executable but warn first (externally visible): the production push to `subtract.ing` and the mirror push.
- Machine roles: **Rousseau** = draft + verify + handoff (canonical for `~/human/`); **Surface** = push to web host + git mirror; the **private key never leaves the governor's signing machine**.
