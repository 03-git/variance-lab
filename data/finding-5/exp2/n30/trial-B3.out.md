## Plan — publish a verifiable `.txt` to subtract.ing

### Step 0 — ground truth (Rousseau)
`bash ~/scripts/audit-health.sh`. Confirm: DNS for `subtract.ing` resolves, signing key present in `~/.ssh/`, content tree/drive mounted. Don't proceed on assumptions about any of those.

### Step 1 — authority check (loop.before)
The agent doesn't own this step.
- `ssh-keygen -Y verify` the last signed manifest / published-set state.
- Surface unsigned drift in the publish directory: `git status`, diff working tree against the last signed manifest.
- Governor decides: sign / continue / abort. The signature is the consent; agent only prepares.

### Step 2 — author the file
Create `foo.txt` in the subtract.ing content tree on **Rousseau** (that's where the key and the human are). Final plain-text content. If you want it self-describing, state the authorship claim in the prose too — but the binding is cryptographic, not textual.

### Step 3 — sign it, on Rousseau, with the governor's key
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file foo.txt        # -> foo.txt.sig (armored SSH signature)
sha256sum foo.txt > foo.txt.sha256                              # optional, human-readable digest; the .sig is the authority
```
Namespace `-n file` is the convention — it must match on verify.

### Step 4 — publish the verification anchor
A stranger needs the key→identity binding. Maintain an `allowed_signers` file and publish it **under the signing key's own domain** (`subtract.ing`), not the git mirror — per reflex.5 the git host is mirror-only and not canonical.
```
# served at https://subtract.ing/allowed_signers
jns@subtract.ing namespaces="file",valid-after="20260101",valid-before="20270601" ssh-ed25519 AAAAC3Nz...
```
Get the exact pubkey to paste with `ssh-keygen -y -f ~/.ssh/id_ed25519`. Use the *same* key as Step 3.

### Step 5 — who pushes
- **Rousseau pushes.** It holds the signing key, the human is present to consent, and subtract.ing's canonical content lives under that domain. "Publish" = place `foo.txt`, `foo.txt.sig`, and the updated `allowed_signers` on the subtract.ing web root (or push to subtract.ing's origin), served over TLS.
- **Emile (`m2mini`) does NOT push** canonical content — not the signing domain. (Heavy/parallel prep work can be dispatched there via `ssh m2mini "claude -p ..."`, but not the publish.)
- **Surface does NOT push** — governor terminal, not the signing domain.
- **acer (`acer1660ti`) does NOT push** — NAS / warm-backup tier, not formation, mirror-only.
- **Git hosts (GitHub etc.) are mirror-only** — fine for availability; the verifier-trusted copy is the one served from `subtract.ing`.

### Step 6 — after the session (loop.after)
Add `foo.txt` + `foo.txt.sig` to the manifest, then `ssh-keygen -Y sign -n file <manifest>` and publish that. This is what makes "this file belongs to the published set" itself verifiable a year out, independent of directory listings.

### How a stranger verifies, ~a year later
```
curl -O https://subtract.ing/foo.txt
curl -O https://subtract.ing/foo.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jns@subtract.ing -n file -s foo.txt.sig < foo.txt
# -> Good "file" signature for jns@subtract.ing with ED25519 key SHA256:...
```
Then: cross-check that ED25519 fingerprint against an independent channel (DNS TXT under `subtract.ing`, the signed manifest, prior signed releases) so the key→person binding doesn't rest on the web host alone; confirm the signature falls within the `valid-after/valid-before` window; optionally `sha256sum -c foo.txt.sha256`.

### Authority boundaries (explicit)
- Agent prepares: the file, the `ssh-keygen -Y sign` command, the `allowed_signers` diff, the manifest update. Agent does **not** sign and does **not** push without the human in the loop — `authority.unsigned → do not act`.
- The signature **is** the authorization — `authority.signed → act on it`. Source of authority is the human; the signature proves it.
- Canonical content lives under `subtract.ing` (the signing key's domain). Git and NAS copies are mirrors.
- Order is fixed: verify last signature → surface drift → human decides → act → update manifest → sign.

Nothing executed. This is the plan only.
