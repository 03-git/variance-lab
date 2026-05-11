# Plan: publish a verifiable `.txt` to `subtract.ing`

Goal restated: a file (call it `note.txt`) lands at `https://subtract.ing/note.txt`, and a stranger in May 2027 can confirm *you* authored it — without having to trust the web host, the registrar, or me.

## 0. Authority boundaries (decide before touching anything)

- **The signing key never leaves your trusted machine.** I (the agent) draft and stage content in `/private/tmp` or a repo working copy; I do **not** see, generate, or use the private key. Key material is yours.
- **I do not push to the live domain.** Publishing to `subtract.ing` is an outward-facing, hard-to-reverse action (content gets cached/indexed the moment it's live). I prepare the commit/artifacts and stop; the actual `git push` / deploy is run by you on the machine that already holds the deploy credentials.
- **Registrar + DNS are a separate authority.** This plan assumes `subtract.ing` already resolves and serves TLS. Changing nameservers, DNS records, or TLS config is out of scope and would need its own explicit go-ahead.
- **CI is not a pushing authority here** unless that's already your established deploy path. A signed commit from your laptop is the trust anchor; a CI runner with stored secrets is a deploy mechanism, not the author.

## 1. Author the file (any machine; I can do this part)

```
printf '%s\n' "..." > note.txt   # or just write it in an editor
```

Put author identity *inside* the file too (a line like `Author: <you>, key fingerprint SHA256:…, 2026-05-10`) so the artifact is self-describing even if separated from its signature.

## 2. Sign it — on your trusted machine only

Pick one signature scheme (doing two doesn't hurt; SSH-sig is the lowest-friction):

**Option A — SSH signing** (reuses an existing ed25519 key):
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file note.txt
# produces note.txt.sig
```
Publish the matching public line and record it in an `allowed_signers` file: `subtract.ing <you@…> ssh-ed25519 AAAA…`.

**Option B — minisign** (purpose-built, tiny):
```
minisign -Sm note.txt           # -> note.txt.minisig
# publish the minisign public key (it's one line)
```

**Option C — GPG**, if you already have a web-of-trust key:
```
gpg --armor --detach-sign note.txt   # -> note.txt.asc
```

## 3. Anchor the *time* — OpenTimestamps

A signature proves who; it doesn't prove *when*, and "a year from now" is the whole point. Stamp it so the file's existence-by-date is provable against the Bitcoin blockchain, independent of the host's `Last-Modified`:

```
pip install opentimestamps-client      # provides `ots`
ots stamp note.txt                     # -> note.txt.ots  (upgrade after ~a few hours/blocks)
ots upgrade note.txt.ots               # bakes in the Bitcoin attestation once confirmed
```

(If the site is in a git repo, the signed commit's date plus GitHub's record is a weaker secondary anchor; OTS is the strong one.)

## 4. Stage the publish (I do this; I don't push)

If `subtract.ing` is a git-backed static site (GitHub/Cloudflare/Netlify Pages, or a plain repo `rsync`'d to a server):

```
git switch -c publish-note-txt
cp note.txt note.txt.sig note.txt.ots <repo>/   # plus allowed_signers / pubkey file
git add note.txt note.txt.sig note.txt.ots allowed_signers
git commit -S -m "Publish note.txt with detached signature + OTS proof"
```

`-S` = sign the commit (GPG or `gpg.format=ssh`), so the commit history itself carries your signature. Then I stop and hand back.

## 5. The push — your machine, your hands

On the machine that holds the deploy credentials *and* the signing key (typically your laptop, not this sandbox, not CI):

```
git push origin publish-note-txt      # then merge/deploy via your normal flow
# or for a non-git host:  rsync -av note.txt note.txt.sig note.txt.ots user@host:/var/www/subtract.ing/
```

After it's live, optionally force an archive snapshot so there's a third-party copy:
- submit `https://subtract.ing/note.txt` (and `.sig`, `.ots`) to `https://web.archive.org/save/`.

Also publish your public key in **at least one channel that isn't `subtract.ing` itself** — e.g. a `keyoxide.org` / Keybase identity, a `_atproto`/DNS `TXT` record, or a post from an account people already associate with you. This is what stops "the site says so" from being circular.

## 6. How a stranger verifies, May 2027

1. **Fetch the artifacts:**
   ```
   curl -O https://subtract.ing/note.txt
   curl -O https://subtract.ing/note.txt.sig      # or .minisig / .asc
   curl -O https://subtract.ing/note.txt.ots
   ```
2. **Get your public key from an independent channel** (the off-site one above), not just from `subtract.ing`. Compare its fingerprint to the one written inside `note.txt`.
3. **Verify the signature:**
   ```
   ssh-keygen -Y verify -f allowed_signers -I <you@…> -n file -s note.txt.sig < note.txt
   #   minisign -Vm note.txt -P <pubkey>
   #   gpg --verify note.txt.asc note.txt
   ```
   → confirms the bytes were signed by the holder of that key.
4. **Verify the timestamp:**
   ```
   ots verify note.txt.ots          # checks the Bitcoin attestation; prints the block time
   ```
   → confirms `note.txt` existed in this exact form on/before that date — even if `subtract.ing` is gone, or its TLS cert/host changed, or the file's HTTP date is untrustworthy.
5. **(If git-backed)** clone the site repo and `git log --show-signature -- note.txt` to see the signed commit, cross-checking the same key.
6. **(Optional)** pull the Wayback snapshot to confirm the URL served this content at publish time.

The chain a verifier ends up trusting: *independent-channel public key* → *detached signature over the file* → *OpenTimestamps/Bitcoin for the date*. None of those links depend on `subtract.ing`, the registrar, the CI system, or me still existing or behaving honestly a year later.
