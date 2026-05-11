# Plan: publish a verifiable-authorship `.txt` to subtract.ing

Goal restated: a stranger, ~12 months from now, can fetch a file from `https://subtract.ing/`, and independently confirm (a) who authored it and (b) that the claim isn't back-dated — without trusting me, the web host, or the CA.

The load-bearing idea: **TLS proves "this came from whoever controls the domain today." It does not prove authorship.** Authorship needs a detached cryptographic signature from a key whose binding to my identity is published over multiple independent channels, plus a blockchain timestamp so the date can't be forged.

## 0. Authority boundaries (decide these first)

| Authority | What it can do | Where it lives | Where it must NOT live |
|---|---|---|---|
| **Signing key** (private) | Assert authorship | Trusted local machine, ideally a YubiKey/hardware token | CI runners, the web host, the registrar |
| **Git push credential** (SSH key / PAT) | Write to the source repo | Same trusted local machine | — |
| **Deploy token** (Netlify/Cloudflare/host API key) | Replace the bytes served at subtract.ing | CI runner *or* host's git integration | Anywhere that also holds the signing key |
| **Registrar + DNS account** | Repoint subtract.ing, get a TLS cert for it | Separate account, MFA | — |

Consequence to internalize: a compromise of the deploy token, the host, or DNS lets an attacker serve *different bytes over a perfectly valid HTTPS cert*. That's the whole reason the detached signature and the offline key exist. The **trusted local machine signs and pushes; the CI/host machine only deploys and never signs.**

## 1. One-time identity setup (trusted local machine)

Pick one signing scheme. I'd use GPG (best tooling/keyserver ecosystem); minisign is a fine lighter alternative.

```bash
# GPG, ed25519, on the trusted machine (or generate on-card with a YubiKey)
gpg --quick-generate-key 'Your Name <you@subtract.ing>' ed25519 sign 2y
gpg --fingerprint you@subtract.ing          # note the full fingerprint
gpg --armor --export you@subtract.ing > publickey.asc
```

Publish the public key / fingerprint over **independent channels** so the key→human binding doesn't rest on subtract.ing alone:
- Commit `publickey.asc` into the site repo, and serve it at `https://subtract.ing/.well-known/openpgpkey/...` (WKD layout via `gpg --list-options show-only-fpr-mbox`) or at a stable `https://subtract.ing/pubkey.asc`.
- `gpg --send-keys <FPR>` to `keys.openpgp.org`.
- Put the fingerprint in a DNS `TXT` record on subtract.ing, in social profiles, in a signed git tag — anywhere with a different trust root.
- Snapshot the key page in the Wayback Machine *now* (step 5) so "the key was already published in 2026" is itself provable.

(Alternative: SSH-based signing — `ssh-keygen -t ed25519`, `git config gpg.format ssh`, sign files with `ssh-keygen -Y sign -n file -f key file.txt`, verify with `ssh-keygen -Y verify`. Or minisign: `minisign -G`, sign with `minisign -Sm file.txt`. Same boundary rules apply.)

## 2. Create and sign the file (trusted local machine)

```bash
cd ~/src/subtract.ing            # local clone of the site repo
$EDITOR content/notes/the-thing.txt

sha256sum content/notes/the-thing.txt > the-thing.txt.sha256
gpg --armor --detach-sign --local-user you@subtract.ing content/notes/the-thing.txt
# -> content/notes/the-thing.txt.asc
```

Optionally also write a short human-readable claim ("I, Your Name, authored the-thing.txt on 2026-05-10, sha256 …") and **clearsign** it (`gpg --clearsign claim.txt`) so the assertion itself is signed, not just the bytes.

## 3. Timestamp it so the date can't be forged (trusted local machine)

```bash
pip install opentimestamps-client
ots stamp content/notes/the-thing.txt          # -> the-thing.txt.ots (anchors into Bitcoin)
# also stamp the .asc if you like:
ots stamp content/notes/the-thing.txt.asc
```

The `.ots` proof, once upgraded (a few hours later: `ots upgrade the-thing.txt.ots`), pins the file's existence to a Bitcoin block — no one, including me, can later claim it existed earlier or later. Commit the `.ots` file alongside.

## 4. Commit, sign the commit, push (trusted local machine — *this* machine pushes)

```bash
git add content/notes/the-thing.txt content/notes/the-thing.txt.asc \
        content/notes/the-thing.txt.ots content/notes/the-thing.txt.sha256
git commit -S -m "Add the-thing.txt (signed + timestamped)"
git tag -s the-thing-2026-05-10 -m "the-thing.txt"
git push origin main
git push origin the-thing-2026-05-10
```

`-S` / `-s` produce a GPG-signed commit and tag. GitHub will show "Verified" once `publickey.asc` is registered to the account, giving a *second*, forge-hosted attestation with its own timestamp. `gh browse` to eyeball it.

## 5. Deploy — done by a *different* machine, with no signing power

Preferred: the push in step 4 triggers CI (`.github/workflows/deploy.yml` running the static generator — Hugo/Eleventy/Jekyll/whatever subtract.ing uses) which publishes to the host (`netlify deploy --prod`, `wrangler pages deploy`, `rsync`, etc.) using a **deploy token scoped to the site only**. That runner never sees the GPG key; it only copies the already-signed `.txt`, `.asc`, `.ots`, `.sha256` through verbatim. If subtract.ing isn't on CI, run the deploy command manually from the local machine — but keep the deploy token in a separate credential store from the signing key, and understand you've merged two authorities if you do.

Make sure the host serves `.txt`/`.asc`/`.ots` as `text/plain`/octet-stream and doesn't rewrite line endings.

## 6. Make it durable and independently dated (any machine)

```bash
curl -sS "https://web.archive.org/save/https://subtract.ing/notes/the-thing.txt"
curl -sS "https://web.archive.org/save/https://subtract.ing/notes/the-thing.txt.asc"
curl -sS "https://web.archive.org/save/https://subtract.ing/pubkey.asc"
```

Also archive.today. Now even if subtract.ing changes hosts or vanishes, the 2026 snapshots persist with the Wayback's own timestamps, corroborating the OTS proof.

## 7. How a stranger verifies, a year later

1. **Fetch the artifacts** over HTTPS: `the-thing.txt`, `the-thing.txt.asc`, `the-thing.txt.ots` from subtract.ing (or from a 2026 Wayback snapshot if the live site changed).
2. **Get the public key** from a channel that *isn't* the live site: `keys.openpgp.org` (`gpg --recv-keys <FPR>`), the git repo, the DNS TXT record, the 2026 Wayback snapshot of `pubkey.asc`. Confirm the fingerprint is the same across ≥2 of these.
3. **Verify the signature:**
   ```bash
   gpg --verify the-thing.txt.asc the-thing.txt
   # expect: Good signature from "Your Name <you@subtract.ing>"
   ```
4. **Verify the timestamp:**
   ```bash
   ots verify the-thing.txt.ots        # confirms the bytes existed by <Bitcoin block date>, ~May 2026
   ```
   This is what defeats back-dating — neither I nor a site-compromiser can move that date.
5. **Cross-check the forge:** open the signed commit/tag on GitHub ("Verified" badge), or `git verify-commit <sha>` / `git verify-tag the-thing-2026-05-10` against the same key.
6. **Cross-check time-in-place:** the May 2026 Wayback snapshots show the file was actually live then under that domain.
7. **Trust reasoning the verifier walks through:** TLS → "the domain owner served this today." Signature → "the holder of key `<FPR>` authored these exact bytes." Multi-channel key publication (keyserver + DNS + repo + 2026 archive) → "key `<FPR>` belongs to Your Name." OTS + Wayback → "this was true in 2026, not retrofitted." The web host, the CA, the CI runner, and the registrar are all *outside* that chain — none of them can forge a `gpg --verify` pass.

### Failure modes the plan deliberately covers
- Host or deploy-token compromise → attacker serves altered bytes over valid TLS, but `gpg --verify` fails. �so detected.
- DNS/registrar takeover → same; plus 2026 Wayback copies remain.
- Me trying to back-date later → OTS Bitcoin anchor and the forge commit timestamp contradict it.
- subtract.ing disappears → Wayback/archive.today snapshots of file + sig + key survive.
- Key compromise (the real residual risk) → mitigated by hardware-backed key (YubiKey), 2-year expiry, and being ready to publish a signed revocation; nothing software-only fully solves this.

### Tools referenced
`gpg` (or `ssh-keygen -Y` / `minisign`), `sha256sum`, `opentimestamps-client` (`ots`), `git` (`commit -S`, `tag -s`, `verify-commit`), `gh`, the site's static generator, CI (`GitHub Actions`), a scoped deploy CLI (`netlify` / `wrangler` / `rsync`), `curl` for Wayback Save-Page-Now.
