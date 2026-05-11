# Plan: publish `manifesto.txt` to subtract.ing with year-durable authorship proof

Goal restated: a stranger in May 2027, trusting **neither me, nor the web host, nor the TLS CA**, can confirm (a) these exact bytes, (b) signed by the key that represents "the author of subtract.ing", (c) no later than the claimed date. That requires three independent legs — a **signature** (who), a **trustless timestamp** (when), and an **identity binding** anchored outside the web server (so a future host swap can't forge it).

---

## Machines & roles (authority boundaries)

| Machine / authority | Holds | Does | Must NOT have |
|---|---|---|---|
| **Signing box** (my laptop, or air-gapped box; ideally key on a YubiKey) | long-term `minisign` secret key + git signing key | writes the file, signs it, OpenTimestamps it, makes the signed git commit/tag | no deploy tokens, no DNS creds |
| **Publishing machine** (CI runner *or* laptop in a different shell profile) | Netlify/GitHub token, or an SSH **deploy** key to the web server | pulls the signed commit, builds `public/`, pushes bytes to subtract.ing | never sees the signing secret key |
| **Registrar / DNS console** (separate web login + its own MFA) | control of the `subtract.ing` zone | publishes/maintains a DNSSEC-signed TXT provenance record | not scriptable from the publishing machine |
| **Bitcoin network** (via OpenTimestamps calendars) | nothing of mine | provides the timestamp; no operator to trust | — |
| **TLS CA + web host** | cert, bytes | serve HTTPS | irrelevant to authorship — the proof must survive them being hostile |

The key boundary: **the machine that proves authorship is not the machine that publishes.** Compromise of the deploy token swaps the file but can't produce a valid signature; compromise of DNS redirects the site but can't forge the DNSSEC-signed record or the blockchain anchor.

---

## One-time setup (signing box)

```
# identity key — passphrase-protected, or better: on hardware
minisign -G -p ~/.minisign/subtract.pub -s ~/.minisign/subtract.key
# git signing via the same class of key
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
pip install --user opentimestamps-client     # provides `ots`
```

Record the `minisign` public key string and its short ID somewhere durable; it is the root of the whole claim.

---

## Publish (all on the signing box, before anything goes live)

1. **Write the file** `public/manifesto.txt`. Freeze the bytes.
2. **Hash it** for the manifest: `sha256sum public/manifesto.txt`.
3. **Sign it** with a meaningful trusted comment (the comment is itself signed by minisign):
   ```
   minisign -S -s ~/.minisign/subtract.key -m public/manifesto.txt \
     -t "subtract.ing/manifesto.txt — author key RWxxxx — 2026-05-10"
   # -> public/manifesto.txt.minisig
   ```
   *(Equivalent with SSH keys: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file public/manifesto.txt` → `.sig`, verified later against an `allowed_signers` line.)*
4. **Timestamp it trustlessly:**
   ```
   ots stamp public/manifesto.txt          # -> public/manifesto.txt.ots (pending)
   ```
   Hours later, once it's in a Bitcoin block: `ots upgrade public/manifesto.txt.ots`, then `ots info public/manifesto.txt.ots` to confirm a block height/merkle path is embedded. Commit the upgraded `.ots`.
5. **Write `public/.well-known/provenance.txt`** (or `PROVENANCE.md`): filename, sha256, minisign public key string, "verify with: `minisign -Vm manifesto.txt -p subtract.pub` and `ots verify manifesto.txt.ots`". Also drop `public/subtract.pub`.
6. **Commit, signed:**
   ```
   git add public/manifesto.txt public/manifesto.txt.minisig public/manifesto.txt.ots \
           public/subtract.pub public/.well-known/provenance.txt
   git commit -S -m "publish manifesto.txt + signature + OTS stamp"
   git tag -s manifesto-2026-05-10 -m "manifesto.txt, signed + timestamped"
   git push origin main --tags        # to GitHub/your forge — signed history is now public
   ```

## Deploy (publishing machine — no signing key present)

Pick one; in all cases it only moves already-signed bytes:
- **GitHub Pages:** the push above triggers the Pages build; `subtract.ing` is set as the custom domain (`public/CNAME`), DNS points there.
- **Netlify:** `NETLIFY_AUTH_TOKEN=… netlify deploy --prod --dir=public`.
- **Own server:** `rsync -avz --delete public/ deploy@web.subtract.ing:/var/www/subtract.ing/`.

Confirm live: `curl -fsS https://subtract.ing/manifesto.txt | sha256sum` matches step 2; `curl -fsSI https://subtract.ing/manifesto.txt.minisig` is 200.

## Out-of-band identity binding (registrar/DNS console)

Add a DNSSEC-signed TXT record so the author↔key link doesn't live only on the swappable web server:
```
_provenance.subtract.ing.  TXT  "minisign=RWxxxx…; sha256=<hash of manifesto.txt>"
```
Ensure the zone is DNSSEC-signed (DS record at the registrar). Optionally also add `rel="me"` links from a Mastodon/other profile to subtract.ing so the identity has more than one anchor.

## Third-party snapshot (anyone's machine)

Force Internet Archive captures of the file and its sidecars, so a neutral party attests "this content was at this URL on 2026-05-10":
```
curl -sI "https://web.archive.org/save/https://subtract.ing/manifesto.txt"
curl -sI "https://web.archive.org/save/https://subtract.ing/manifesto.txt.minisig"
curl -sI "https://web.archive.org/save/https://subtract.ing/manifesto.txt.ots"
curl -sI "https://web.archive.org/save/https://subtract.ing/subtract.pub"
```

---

## What a stranger does in May 2027

```
# 1. Get the artifacts (live site, or Wayback if the site changed)
curl -O https://subtract.ing/manifesto.txt
curl -O https://subtract.ing/manifesto.txt.minisig
curl -O https://subtract.ing/manifesto.txt.ots
curl -O https://subtract.ing/subtract.pub

# 2. Corroborate the key is "the author's" from independent sources — agreement is the trust:
dig +dnssec TXT _provenance.subtract.ing      # AD flag set, key string matches subtract.pub
git clone <forge>/subtract.ing && git -C subtract.ing verify-tag manifesto-2026-05-10
#   + Wayback snapshot of subtract.pub dated 2026-05-10 shows the same key
#   + rel=me cross-links, if used

# 3. Signature: do the bytes belong to that key?
minisign -Vm manifesto.txt -p subtract.pub          # "Signature and comment signature verified"

# 4. Time: was it really no later than the claim, not backdated?
ots verify manifesto.txt.ots        # confirms manifesto.txt's hash is in a Bitcoin block from ~2026-05
                                    # (uses public block explorers or `-b` against their own bitcoind)

# 5. (optional) git log --show-signature  — signed commit chain corroborates the date
```

If steps 3 and 4 pass and step 2 shows the key was already associated with subtract.ing at publication time (via the DNSSEC record and/or the 2026 Wayback capture and/or signed git tags), the claim holds — and it holds even if, a year later, the domain has been sold, the host serves something else, or the original CA is distrusted. Each leg fails independently and visibly: a forged file breaks `minisign -V`; a backdated file has no pre-existing Bitcoin anchor; a hijacked domain can't reproduce the DNSSEC signature or the archived/git history.

### Caveats worth stating up front
- The timestamp must be created **at publish time** — you cannot retro-timestamp later.
- `.ots` proofs need `ots upgrade` after Bitcoin confirmation; do that within a day and re-commit.
- The signing secret key's secrecy is the whole ballgame — hardware-backed (YubiKey) or air-gapped, never on the publishing/CI machine, never in CI secrets.
- DNSSEC must actually be enabled at the registrar (DS record), or the TXT leg is worthless.
