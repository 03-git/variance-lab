# Plan: publish `manifesto.txt` to subtract.ing with year-durable, stranger-verifiable authorship

The claim a stranger needs to check has three independent parts, and each maps to a different tool and a different authority:

1. **"This byte sequence is what was published"** → content hash.
2. **"This author signed it"** → detached cryptographic signature + a key bound to an identity.
3. **"It existed at least a year ago"** → trusted timestamp anchored in something the verifier doesn't have to trust me about (Bitcoin via OpenTimestamps, or an RFC 3161 TSA).

Authorship is only as good as the binding between the signing key and "the person/project behind subtract.ing." So the key must be anchored through a channel the verifier reaches independently of the file itself — DNSSEC-signed TXT record under the domain, plus a signed git history. I'd set the key up (or reuse an already-published one) *before* publishing.

## Machines and authority boundaries

| Role | Machine | Holds | Can it forge authorship? |
|---|---|---|---|
| **Signing / identity** | Workstation or air-gapped laptop; key ideally on a YubiKey / `gpg --card` | `~/.ssh/subtract_signing` (ed25519) **private** key | Yes — this is *the* authority. Never copied to the server or into CI secrets. |
| **Domain / DNS** | Registrar + DNS provider web console | Registrar login, DNSSEC keys | Sets the `_author` TXT record once; controls what "subtract.ing says about itself." Separate credential. |
| **Deploy / hosting** | Networked workstation *or* a GitHub Actions runner | Git remote push token / Netlify/Cloudflare deploy token / SSH deploy key | **No.** Can alter or remove the page; a verifier detects that via signature mismatch. |
| **TLS termination** | The host (Pages/Cloudflare/VPS) | Cert for `subtract.ing` | Proves hostname control at fetch time, not authorship. |

The line that matters: **the machine that pushes is not the machine that signs** — at minimum a different credential, ideally a different machine. The signing box produces `manifesto.txt.sig` and `manifesto.txt.ots`; those move to the deploy box by git commit or USB; the signing private key never makes that trip.

## Steps

### 1. Prepare content (signing machine)
- Write `manifesto.txt`. Freeze it.
- `shasum -a 256 manifesto.txt | tee manifesto.txt.sha256` — record the digest.

### 2. Establish the identity key (signing machine, ideally once, ahead of time)
- `ssh-keygen -t ed25519 -f ~/.ssh/subtract_signing -C "author@subtract.ing"` (or generate on a YubiKey: `ssh-keygen -t ed25519-sk`).
- Build the verifier-facing trust anchors:
  - **DNS:** add a DNSSEC-signed TXT record at `_author.subtract.ing`: `v=ssh-ed25519; ns=file; key=AAAAC3Nz...` (the contents of `subtract_signing.pub`). Confirm the zone is DNSSEC-signed (`dig +dnssec subtract.ing`).
  - **In-repo:** keep `allowed_signers` in the site repo: `author@subtract.ing namespaces="file" ssh-ed25519 AAAAC3Nz...`.
  - Optional extra anchors: a Keybase/Sigstore identity, or publish the pubkey at `https://subtract.ing/.well-known/author.pub` (weak alone — same origin as the file).
- (GPG variant if you prefer: `gpg --quick-generate-key 'Author <author@subtract.ing>' ed25519 sign 3y`, publish via an `OPENPGPKEY` DNS record and `keys.openpgp.org`.)

### 3. Sign (signing machine)
- `ssh-keygen -Y sign -f ~/.ssh/subtract_signing -n file manifesto.txt` → produces `manifesto.txt.sig`.
- Self-check: `ssh-keygen -Y verify -f allowed_signers -I author@subtract.ing -n file -s manifesto.txt.sig < manifesto.txt`.

### 4. Timestamp (signing machine, network-connected for this step only)
- `pip install opentimestamps-client`
- `ots stamp manifesto.txt` → `manifesto.txt.ots` (calendar commitment; not yet Bitcoin-confirmed).
- Hours later: `ots upgrade manifesto.txt.ots` then `ots verify manifesto.txt.ots` — now it carries a Bitcoin block attestation. Re-commit the upgraded `.ots`.
- (Belt-and-suspenders: also get an RFC 3161 token — `openssl ts -query -data manifesto.txt -sha256 -cert -out req.tsr` then submit to a public TSA like freetsa.org — for verifiers who'd rather trust a CA than Bitcoin.)

### 5. Publish (deploy machine — the one with the push/deploy credential)
Assuming the site is a git-backed static host (GitHub Pages / Cloudflare Pages / Netlify):
- `git add manifesto.txt manifesto.txt.sig manifesto.txt.ots manifesto.txt.sha256 allowed_signers`
- `git -c gpg.format=ssh -c user.signingkey=~/.ssh/subtract_signing.pub commit -S -m "Publish manifesto.txt"` — a signed commit gives a second, git-native authorship record with its own timestamp chain.
- `git push origin main` — this push uses the **deploy token**, not the signing key.
- CI (e.g. `.github/workflows/pages.yml`) builds and deploys. CI secrets contain only the deploy/Pages token. If you deploy by hand instead: `rsync -av ./public/ deploy@subtract.ing:/var/www/` or `npx netlify deploy --prod` or `npx wrangler pages deploy ./public` — same boundary, the deploy host never sees the signing key.
- Verify the live URLs return the exact bytes: `curl -fsSL https://subtract.ing/manifesto.txt | shasum -a 256` matches step 1.

### 6. (Optional, strengthens the year-later claim) external mirrors
- `gh release create manifesto-v1 manifesto.txt manifesto.txt.sig manifesto.txt.ots` on a public repo, and/or submit `https://subtract.ing/manifesto.txt` to the Wayback Machine. These are corroborating, not load-bearing — the OTS proof is the real time anchor.

## How a stranger verifies it, a year later

```
# 1. Get the artifacts from the site
curl -fsSLO https://subtract.ing/manifesto.txt
curl -fsSLO https://subtract.ing/manifesto.txt.sig
curl -fsSLO https://subtract.ing/manifesto.txt.ots

# 2. Get the author's public key from an INDEPENDENT channel (not just the site)
dig +dnssec +short TXT _author.subtract.ing      # DNSSEC-validated; extract the key=...
#   build allowed_signers from that:  author@subtract.ing namespaces="file" ssh-ed25519 AAAAC3Nz...

# 3. Verify the signature binds key -> file
ssh-keygen -Y verify -f allowed_signers -I author@subtract.ing -n file \
  -s manifesto.txt.sig < manifesto.txt
#   => "Good "file" signature for author@subtract.ing"

# 4. Verify the file existed >= ~1 year ago, independent of any server clock
pip install opentimestamps-client
ots verify manifesto.txt.ots
#   => "Bitcoin block <N> attests existence as of <date>"   (date is ~publication time)

# 5. (Optional) cross-check the signed git commit / GitHub release / Wayback snapshot
git verify-commit <hash>      # in a clone of the site repo
```

If all four succeed: the bytes are intact (3), a key that DNSSEC says belongs to `subtract.ing` signed those exact bytes (2,3), and Bitcoin's chain — not my say-so — puts that file in existence a year back (4). A compromised web host or expired TLS cert in the meantime breaks none of those proofs; only theft of the offline/hardware signing key would, which is why that key is the one thing that never touches the deploy path.

## What I would *not* rely on
- TLS/HTTPS as proof of authorship — it's transport, and certs rotate.
- The hosting platform's "last modified" date or git committer date alone — server-controlled, not trustworthy to a stranger.
- The pubkey served only from `subtract.ing` itself — circular; DNSSEC TXT + an external mirror break the circle.
- Putting the signing key in CI/GitHub secrets "for convenience" — that collapses the deploy boundary into the identity boundary.
