# Plan: publish a verifiable `.txt` to subtract.ing

Not executing — this is the plan only.

## 0. Reflex check before touching anything (reflex.2, reflex.4)

- **reflex.2 (memory→signature):** the format is already decided — don't invent one. SSH signatures via `ssh-keygen -Y sign` / `-Y verify`, namespace `file`, trust anchored by an `allowed_signers` file. `ssh-keygen -Y verify` can confirm this format, so it's the format we use.
- **reflex.4 / loop.before.1:** before building on current state, do a live read. On Rousseau, in the canonical tree (`~/subtract.ing/`), verify the existing manifest:
  ```
  ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file \
    -s ~/subtract.ing/MANIFEST.sha256.sig < ~/subtract.ing/MANIFEST.sha256
  ```
  If that fails or there's unsigned drift in the tree (`git -C ~/subtract.ing status`), stop and surface it (loop.before.2) — don't publish on top of an unverified base.

## 1. Agent prepares (boundary: "the agent prepares, the human signs")

On **Rousseau** (governor's workstation, holds the private key, where the human is):

1. Write the file into the canonical web root tree, not `/tmp`:
   `~/subtract.ing/<name>.txt`
2. Normalize and record its hash:
   ```
   shasum -a 256 ~/subtract.ing/<name>.txt
   ```
3. Draft the manifest update — append the filename + sha256 line to `~/subtract.ing/MANIFEST.sha256`. (Don't sign it yet.)
4. Stage everything and show the governor the diff. Agent stops here. Running `ssh-keygen -Y sign` is **not** an agent action — authority.unsigned says agent output is suggestion only; the signature is what confers authority, and only the human produces it (loop.before.3).

## 2. Human gate — the governor signs (loop.before.3, loop.after.2)

Governor, on Rousseau, with the `jnous` private key:

```
# sign the new file
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<name>.txt
#   -> produces ~/subtract.ing/<name>.txt.sig   (self-contained: embeds the pubkey)

# sign the updated manifest (loop.after.1 already did the edit; .2 signs it)
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/MANIFEST.sha256
#   -> ~/subtract.ing/MANIFEST.sha256.sig
```

Sanity-check locally before publishing:
```
ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I jnous -n file \
  -s ~/subtract.ing/<name>.txt.sig < ~/subtract.ing/<name>.txt
```

Confirm `~/subtract.ing/allowed_signers` already contains the line:
```
jnous ssh-ed25519 AAAA...   # the public half of the signing key
```
If for some reason it doesn't, that line is itself a human-gated addition — add and re-sign the manifest. The `allowed_signers` file is the trust root; it must live at the signing domain.

## 3. Publish — which machine pushes, which does not

- **Rousseau pushes.** It is the canonical origin under the signing key's domain (reflex.5). The bundle that goes out: `<name>.txt`, `<name>.txt.sig`, updated `MANIFEST.sha256`, `MANIFEST.sha256.sig`, and `allowed_signers` if it changed. Deploy is `rsync`/`scp` to the subtract.ing document root (or `git push` to the subtract.ing-controlled origin the webserver pulls).
- **Emile does not push and does not sign.** Emile is the execution-offload node; signing is a human gate and canonical publication isn't delegated to it.
- **Media (acer1660ti) does not push.** It's the NAS / warm-backup tier, not formation — it can hold a copy as backup, never as the authoritative source.
- **GitHub / any git host: mirror only (reflex.5).** Update it *after* the canonical push if you want; it carries no authority. A verifier who only has the GitHub copy is still fine *because the signature travels with the file* — but the canonical URL is the subtract.ing one.
- Publishing is an externally-visible mutation — governor already authorized it at step 2's gate, so the push proceeds; no second prompt needed, but it's the human's decision that licensed it, not the agent's.

## 4. How a stranger verifies it a year from now

The signature is over `(file bytes, namespace, public key)` — no timestamp, no dependency on subtract.ing still being up. A verifier needs three artifacts and one trust decision:

```
curl -O https://subtract.ing/<name>.txt
curl -O https://subtract.ing/<name>.txt.sig
curl -O https://subtract.ing/allowed_signers      # binds the key to the name "jnous"

ssh-keygen -Y verify -f allowed_signers -I jnous -n file \
  -s <name>.txt.sig < <name>.txt
# -> "Good "file" signature for jnous with ED25519 key SHA256:..."
```

Why it still holds in a year:
- **Integrity/authenticity:** the math is self-contained. Even if subtract.ing is gone, an archived copy (Wayback, the git mirror, the Media backup) of `file + .sig + allowed_signers` verifies identically.
- **Binding key→author:** the `allowed_signers` line maps the keyprint to `jnous`. The verifier corroborates that keyprint isn't a forgery by cross-checking it against (a) the signed `MANIFEST.sha256` published the same place, (b) every prior subtract.ing artifact signed by the same key (a long-lived key chained across many signed files is hard to retro-fake), and (c) `https://subtract.ing/governance.conf.universal.txt` and other canonical docs naming the same principal. That's the "canonical under the signing key's domain" guarantee — the domain and the key reinforce each other.
- **Manifest cross-check:** `shasum -a 256 <name>.txt` must equal the line in the signed `MANIFEST.sha256`, so the file is also pinned by an independently-signed inventory, not just its own detached sig.

## Authority boundaries, summarized

| Step | Who | Why |
|---|---|---|
| draft file, edit manifest, run `-Y verify`, stage | agent (Rousseau) | preparation; reversible; `-Y verify` is a read |
| `ssh-keygen -Y sign` (file + manifest) | **human only** | boundary: signature = authority; reflex.2; loop.before.3 |
| add/modify `allowed_signers` | **human only** | it's the trust root; new trust is a human gate |
| push signed bundle to subtract.ing | agent (Rousseau), under the human's go-ahead from the signing step | "pushing already-signed artifacts is infra work" — but it's externally visible, so it rides on the human's decision |
| mirror to GitHub | agent (Rousseau) | mirror-only, no authority (reflex.5) |
| anything on Emile / Media | n/a | not the signing host, not canonical origin |

Order matters: verify current signed state → prepare → human signs → push canonical → mirror → done.
