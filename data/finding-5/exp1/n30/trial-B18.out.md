# Plan: publish a verifiable-authorship `.txt` to subtract.ing

## 0. Threat model / what "verifiable" will mean
A stranger in May 2027 should be able to establish three independent links:
1. **bytes ⇄ key**: the file was signed by a specific keypair (digital signature);
2. **key ⇄ domain**: that key was published under `subtract.ing` before the claim date (DNS + HTTPS, archived);
3. **bytes ⇄ time**: the file's hash existed no later than some date, attested by a party that isn't me and isn't the web host (blockchain timestamp).

Identity ⇄ human is explicitly *out of scope* unless I additionally cross-sign from an already-established identity (noted at the end).

## 1. Author the content (trusted workstation)
- Write `article.txt`. Freeze it — any later byte change invalidates everything below.
- `sha256sum article.txt > SHA256SUMS`

## 2. Create the long-term signing key (trusted workstation, ideally hardware-backed)
- `minisign -G -p subtract.pub -s subtract.sec`
  - Keep `subtract.sec` on this machine only — better, generate/keep it on a YubiKey or an offline box. This is the **signing authority**. It will never be copied to a server, a CI runner, or the registrar account.
- (Optional, for web-of-trust folks) also generate a GPG key and `gpg --export --armor` it.

## 3. Sign
- `minisign -S -s subtract.sec -m article.txt -x article.txt.minisig -c "subtract.ing article — <YYYY-MM-DD>" -t "signed <YYYY-MM-DD> by subtract.ing key RWQ..."`
  - The *trusted comment* is itself signed, so the asserted date is tamper-evident.
- Also sign the manifest: `minisign -S -s subtract.sec -m SHA256SUMS -x SHA256SUMS.minisig`
- (Optional GPG) `gpg --armor --detach-sign article.txt` → `article.txt.asc`

## 4. Independent timestamp (don't trust my clock or the server's)
- Install client: `pipx install opentimestamps-client`
- `ots stamp article.txt` → produces `article.txt.ots` (commits the SHA-256 into the Bitcoin blockchain via calendar servers).
- Wait for confirmation (hours), then `ots upgrade article.txt.ots` to embed the block header path. Keep the upgraded `.ots`.
- (Belt and suspenders) also get an RFC 3161 token: `openssl ts -query -data article.txt -sha256 -cert -out article.tsq` → POST to a free TSA (e.g. `curl -H 'Content-Type: application/timestamp-query' --data-binary @article.tsq https://freetsa.org/tsr -o article.tsr`).

## 5. Publish the public key under the domain (registrar/DNS authority — a *different* authority than the signing key)
- DNS TXT record, e.g. `_minisign.subtract.ing. TXT "minisign-pubkey=RWQ...<base64>"`. Do this in the registrar/DNS-provider console, protected with its own 2FA. **Enable DNSSEC** on the zone so the record is provable later.
- Also serve `https://subtract.ing/.well-known/minisign.pub` (and `…/minisign.pub.asc` if GPG). HTTPS cert via Let's Encrypt/ACME on the web host — yet another, separate authority (ACME account key lives on the web server, not the workstation).
- Cross-posting the key fingerprint somewhere append-only (a git host profile, a signed git tag, a social post) strengthens link #2; not required.

## 6. Deploy the artifacts (deploy authority — NOT the signing machine's privileges)
Two acceptable shapes; pick one:

- **Direct push from workstation:** `rsync -av --chmod=F644 article.txt article.txt.minisig article.txt.ots SHA256SUMS SHA256SUMS.minisig deploy@subtract.ing:/var/www/subtract.ing/`
  - The SSH key used here is a *deploy-only* key: in the server's `~/.ssh/authorized_keys` it's pinned with `command="rrsync /var/www/subtract.ing",restrict`. It can write the web root and nothing else. It cannot sign anything.
- **Via CI (GitHub Actions, etc.):** commit the *already-signed* files to a repo; CI rsyncs/`scp`s them on push. The CI runner gets only the scoped deploy secret. **The signing private key is never added as a CI secret** — CI ships bytes I already signed, it does not sign on my behalf. Optionally `git commit -S` / `git tag -s` for an extra signed record.

**Authority boundary summary**
| Authority | Lives on | Can do | Cannot do |
|---|---|---|---|
| `subtract.sec` (minisign) | trusted workstation / hardware token | sign files | reach the server, DNS, or CI |
| deploy SSH key | workstation *or* CI runner | write `/var/www/subtract.ing` (forced-command) | sign, shell access, touch DNS |
| registrar/DNS account | browser + 2FA | publish pubkey TXT, enable DNSSEC | sign files |
| ACME account key | web server | issue/renew TLS cert | sign files, edit DNS (unless DNS-01 — then scope it) |

The machine that **pushes**: the workstation (or CI runner) using the scoped deploy key. The machine that **does not push**: anything holding `subtract.sec` if it's a separate offline box/token — it only emits a `.minisig` that someone carries to the deploy step.

## 7. Make link #2 durable
- Submit to the Wayback Machine now: `curl "https://web.archive.org/save/https://subtract.ing/.well-known/minisign.pub"`, same for `https://subtract.ing/article.txt` and the `.minisig`/`.ots`. This freezes "the key was here, serving this file, in May 2026."
- Note that `dnshistory`/`SecurityTrails`-type services will also retain the TXT record; DNSSEC makes a fetched-later copy self-verifying.

## 8. How a stranger verifies in May 2027
1. Download `article.txt`, `article.txt.minisig`, `article.txt.ots` from `https://subtract.ing/…`.
2. **Get the key independently of the file:** `dig +dnssec TXT _minisign.subtract.ing` and confirm the resolver sets the **AD flag** (DNSSEC-validated); also `curl https://subtract.ing/.well-known/minisign.pub`; confirm both match each other. Then check the **Wayback Machine** snapshot from 2026 shows the same `minisign.pub` — so the key predates the claim and wasn't swapped in later.
3. **bytes ⇄ key:** `minisign -V -p minisign.pub -m article.txt -x article.txt.minisig` → must print "Signature and comment signature verified", and the trusted comment shows the asserted date.
4. **bytes ⇄ time:** `ots verify article.txt.ots` (after `ots upgrade` if needed) → "Success! Bitcoin block <N> attests existence as of <date>". Optionally `openssl ts -verify -data article.txt -in article.tsr -CAfile freetsa_cacert.pem`.
5. Conclusion the verifier can defend: *the holder of minisign key `RWQ…`, which was published under `subtract.ing` (DNSSEC-signed, Wayback-archived) by May 2026, authored these exact bytes, and those bytes demonstrably existed by the Bitcoin-attested block time.* If I also linked the key from a pre-existing identity (step 5/6 options), the human attribution follows too; otherwise it stops at "whoever controlled that key and that domain."

## Notes / failure modes to disclose
- If `subtract.sec` leaks, post a `revocation.txt` signed by it (or by a pre-published backup key) and update the DNS TXT — verifiers checking dates still hold for items timestamped before the leak.
- Don't rotate the file in place; publish `article-v2.txt` with its own `.minisig`/`.ots` so old links keep verifying.
- OpenTimestamps proves *not-later-than*; the signed trusted comment provides the *not-earlier-than* claim. Neither alone proves an exact authorship instant — together they bracket it.
