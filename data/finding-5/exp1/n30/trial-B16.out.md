# Plan: publish a verifiable `.txt` to subtract.ing

Goal restated: a file at `https://subtract.ing/<name>.txt` such that an unrelated person in May 2027 can confirm (a) it was authored by the claimed identity and (b) it existed on the claimed date. The mechanism is cryptographic signing + independent key-binding channels + a blockchain timestamp — not "trust the web server."

## 0. Identity anchor — decide once, before touching files

Pick the keypair that *is* the identity. Use a dedicated signing key, generated and stored on the user's own hardware (laptop keychain or, better, a YubiKey), passphrase-protected, **never copied to a shell sandbox or CI**:

- minisign (simplest for files): `minisign -G -p subtract.ing.pub -s subtract.ing.sec`
- and/or SSH signature key: `ssh-keygen -t ed25519 -C "subtract.ing signing" -f ~/.ssh/id_ed25519_subtracting`
- GPG is a fine alternative (`gpg --quick-generate-key`), but minisign/SSH have less footgun surface for a stranger to verify.

The public key gets published in **at least three independent channels** so a year from now no single outage breaks verification:
1. `https://subtract.ing/.well-known/minisign.pub` (and `/.well-known/allowed_signers` for the SSH key)
2. DNS: a `TXT` record, e.g. `_minisign.subtract.ing` containing the pubkey line
3. A Keyoxide / `keys.openpgp.org` profile or a Keybase identity proof tying the key to the domain
4. (free bonus) the key file is in the public git repo history under a signed commit

## 1. Prepare the file — agent sandbox is allowed here

On the working machine (this ephemeral `/private/tmp` sandbox is fine — it only drafts content, holds no secrets, and pushes nothing):

```
git clone <repo-url> subtracting && cd subtracting
# write content
$EDITOR 2026-05-10-statement.txt
sha256sum 2026-05-10-statement.txt > 2026-05-10-statement.txt.sha256
```

Agent may: read the repo, draft the text, run non-mutating commands, show the diff. Agent stops here.

## 2. Sign + timestamp — user's machine with the key

These steps run on the machine that holds the secret key (the user's, behind passphrase/touch). Detached signatures:

```
minisign -Sm 2026-05-10-statement.txt -s subtract.ing.sec \
  -t "subtract.ing — statement 2026-05-10" -x 2026-05-10-statement.txt.minisig
# or SSH:
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_subtracting -n file 2026-05-10-statement.txt
```

Independent timestamp (proves *existence by date*, defeats backdating, no authority to trust, doesn't expire):

```
pip install opentimestamps-client
ots stamp 2026-05-10-statement.txt          # -> 2026-05-10-statement.txt.ots
# (run `ots upgrade 2026-05-10-statement.txt.ots` a day later once it's in a Bitcoin block)
```

Commit and tag, signed:

```
git config gpg.format ssh
git config user.signingkey ~/.ssh/id_ed25519_subtracting.pub
git add 2026-05-10-statement.txt 2026-05-10-statement.txt.minisig 2026-05-10-statement.txt.ots .well-known/
git commit -S -m "Publish statement 2026-05-10"
git tag -s v2026.05.10 -m "statement 2026-05-10"
```

## 3. Push / deploy — explicitly NOT the agent

Who pushes: the **user's own machine**, which has (a) the deploy credential and (b) was where signing happened. After the user reviews:

```
git push origin main && git push origin v2026.05.10
git push codeberg main          # second mirror, so the signed history is independently retrievable
netlify deploy --prod           # or `rsync -av ./ user@host:/var/www/subtract.ing/`, whatever the host is
```

Who does **not** push: this agent sandbox — it has no deploy token, no DNS API key, no signing key, and "publish to the public internet" is outward-facing and effectively irreversible (Wayback/CT will capture it), so it requires a human at the controls. Creating the DNS `TXT` record is likewise a human action in the registrar/DNS console.

### Authority boundaries, explicitly
- **Agent, no confirmation needed:** read repo, draft `.txt`, compute hashes, explain.
- **Agent, only with per-action human confirmation:** running `git push`, deploy commands. Even then, it's cleaner to hand these to the user, because —
- **Never the agent, ever:** generating or holding the signing secret key, touching DNS records, posting identity proofs. The whole claim's strength comes from a key the agent has never possessed; if the agent could sign, a stranger couldn't distinguish the author from the tool.
- If the secret key is ever exposed: publish a revocation (`minisign` → rotate and announce on all channels; GPG → `gpg --gen-revoke`), and re-sign with a new key.

## 4. How a stranger verifies, May 2027

```
# 1. fetch artifacts
curl -O https://subtract.ing/2026-05-10-statement.txt
curl -O https://subtract.ing/2026-05-10-statement.txt.minisig
curl -O https://subtract.ing/2026-05-10-statement.txt.ots

# 2. obtain the claimed pubkey from MULTIPLE channels and check they match
curl https://subtract.ing/.well-known/minisign.pub
dig +short TXT _minisign.subtract.ing
#   ...plus the Keyoxide/Keybase proof, plus the key file in the git repo
#   ...plus a Wayback snapshot from ~publish time, to defeat "site was changed last week":
#   http://web.archive.org/web/2026*/https://subtract.ing/.well-known/minisign.pub

# 3. verify the file against that key
minisign -Vm 2026-05-10-statement.txt -p minisign.pub
#   -> "Signature and comment signature verified"
#   (SSH variant: ssh-keygen -Y verify -f allowed_signers -I <id> -n file -s file.sig < file)

# 4. verify the commit/tag history independently
git clone <repo-or-mirror> && git verify-tag v2026.05.10 && git verify-commit <hash>

# 5. verify the date, trustlessly
ots verify 2026-05-10-statement.txt.ots
#   -> attests the file's SHA256 was embedded in a Bitcoin block dated ~2026-05-10
```

Conclusion the verifier can draw: the bytes they downloaded are exactly what was signed; the signing key is the one bound to `subtract.ing` across DNS + the site + a third-party identity proof + the git history (so a single compromised channel isn't enough); and OpenTimestamps shows the content isn't backdated. The authorship claim is then as strong as the *weakest* of those independent key-binding channels — which is the point of using several.

## Why this still works in a year
- minisig/`.asc`/`.ots` files and the pubkey are static — nothing to renew.
- OpenTimestamps anchors to Bitcoin and never expires; no timestamping company to outlive.
- The repo is mirrored (GitHub + Codeberg), and the site + DNS state are passively archived by the Wayback Machine, so even if subtract.ing goes dark the verification path survives.
- No reliance on a single GPG keyserver or a single host.

I haven't run anything — this is the plan only. If you want, I can next draft the actual `.txt` content and the `.well-known/` files in the sandbox for you to review before any signing or pushing happens on your machine.
