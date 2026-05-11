Ran `audit-health.sh`. Ground truth from it: the live `subtract.ing` artifact verifies — `Good "subtract.ing" signature for hodori@subtract.ing` (ED25519 SHA256:Aw1QLLpzaCc7ycWKwLBsG/2rfWagcs2OjBFdh6SA0s4). Note that identity (`hodori@subtract.ing`) does **not** match what formation memory says about the content-signing key (`jnous`) — see the open item at the bottom; I'm not going to bake either name into a published verify command without reading `~/.ssh/allowed_signers` first.

Plan only, nothing executed below.

---

## 0. Pre-flight — verify before acting (loop.before.1–3, reflex.4)
- `ssh-keygen -Y verify` the *current* canonical artifact and `MANIFEST` against `~/.ssh/allowed_signers` — confirm the chain you're extending is itself good.
- In `~/subtract.ing/runtime/...` (the real tree, not `/tmp`): `git log --oneline -5`, `git status`, `wc -l` on anything you'll touch. State timestamps/line counts before editing.
- Resolve the signer identity from `~/.ssh/allowed_signers` and the existing `.sig` files — do **not** proceed on a name carried in from memory or a prior session (that's `fail.confabulation`).
- reflex.1: the primitive here is "a file in the web root, served by the process already running" + `ssh-keygen` for the signature. No deploy framework, no new signing format (reflex.2 — `ssh-keygen -Y sign` is the format).

## 1. Draft the file — agent, on rousseau
- Author `newfile.txt` under `~/human/...` (canonical for formation human-authored work), then stage it into the `~/subtract.ing/` working tree at its serving path.
- This is preparation. The agent may do all of it. It produces no authority yet.

## 2. Sign — human only, on the node holding the key (boundary, authority.unsigned, loop.before.3)
- The governor runs: `ssh-keygen -Y sign -f ~/.ssh/<signing_key> -n file newfile.txt` → produces `newfile.txt.sig`.
- The agent never runs this. "The agent prepares, the human signs." An unsigned file is a suggestion, not canonical content.

## 3. Update + sign the manifest (loop.after.1, loop.after.2)
- Add `newfile.txt` and its `shasum -a 256` to `MANIFEST`.
- Governor: `ssh-keygen -Y sign -f ~/.ssh/<signing_key> -n file MANIFEST` → `MANIFEST.sig`.
- This puts the file in the *signed set*, so a verifier can confirm it belongs, not just that it's individually signed.

## 4. Verify the new artifacts before publishing (reflex.4, authority.signed)
- `ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I <identity> -n file -s newfile.txt.sig < newfile.txt`
- Same for `MANIFEST` / `MANIFEST.sig`.
- Only after both pass is the bundle actionable.

## 5. Publish — which machine pushes
- **Rousseau pushes.** It holds canonical `~/human/` and `~/subtract.ing`; reflex.5 puts canonical content under the signing key's domain (`subtract.ing`). Pushing an *already-signed* bundle is plain infra — the agent can do it (only *new* signing is a human gate).
- **Surface does not push.** Governor terminal; it pulls `~/human/` etc., it's not in the publish path.
- **Emile does not push.** It's the heavy-compute offload target (`ssh m2mini "claude -p"`), not a publish node.
- **Media / acer does not push.** Not formation — service infra (Jellyfin/*arr/Kiwix). Never in the signing or publish path.
- A git host, if mirrored to, is **mirror-only** and carries no authority (reflex.5). Canonical = `https://subtract.ing/...` only.
- Exact deploy command (rsync to a serving host vs. it's served off rousseau directly) — read it from `~/subtract.ing` + the audit output before running. I won't name an rsync target here that might be confabulated.

## 6. Confirm done with a live read (reflex.4)
```
curl -fsS https://subtract.ing/newfile.txt      -o /tmp/v.txt
curl -fsS https://subtract.ing/newfile.txt.sig  -o /tmp/v.txt.sig
curl -fsS https://subtract.ing/allowed_signers  -o /tmp/allowed_signers
ssh-keygen -Y verify -f /tmp/allowed_signers -I <identity> -n file -s /tmp/v.txt.sig < /tmp/v.txt
```
- Re-fetch + re-verify `MANIFEST` + `MANIFEST.sig`; `shasum -a 256 /tmp/v.txt` must match the manifest line. Any failure → not published.
- Then loop.after.1: note the new canonical artifact in formation memory / session log.

## 7. How a stranger verifies it a year from now
Needs only stock OpenSSH and `curl`. Verification is offline and key-based, so the year gap is irrelevant — no trust-on-first-use against a live service.
```
curl -O https://subtract.ing/newfile.txt
curl -O https://subtract.ing/newfile.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <identity> -n file -s newfile.txt.sig < newfile.txt
```
- `Good "file" signature for <identity>` → authorship confirmed. The **signature** proves it — not the TLS cert, not the host, not any git mirror.
- Optional chain check: `curl -O .../MANIFEST` + `.../MANIFEST.sig`, verify the same way, then `shasum -a 256 newfile.txt` and match the manifest entry — ties the file to the signed set.
- reflex.5: a verifier who finds the file on a git host should treat that as a mirror and re-fetch from `subtract.ing` (the signing key's domain) before trusting it.

## Authority boundaries, summarized
| Actor | May do | May not do |
|---|---|---|
| Claude / node automation | draft `newfile.txt`, edit `MANIFEST` delta, run `ssh-keygen -Y verify`, push the *signed* bundle from rousseau | produce a signature; declare it canonical before verify passes |
| Governor (human) | holds `<signing_key>`; runs `ssh-keygen -Y sign` for the file and the manifest | — (this is the only blocking step) |
| Verifier (stranger) | fetch the 3 public files, run `ssh-keygen -Y verify` | needs nothing else from the formation |
| Push node | rousseau only | Surface / Emile / Media must not push |

## Open item — do not paper over
Memory says the content-signing identity is `jnous`; today's `audit-health.sh` shows the live `subtract.ing` signature is by `hodori@subtract.ing`. Those may be two distinct keys (site/infra vs. governor-authored content) or memory may be stale. Before step 2, read `~/.ssh/allowed_signers` and an existing `.sig` to pin which identity governs human-authored `.txt` files, and use that exact `-I` value in the published verify instructions. Don't guess.
