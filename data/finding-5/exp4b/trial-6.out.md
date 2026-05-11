Plan only — nothing executed.

## 0. Ground truth first
- `bash ~/scripts/audit-health.sh` — confirm DNS resolves `subtract.ing`, the deploy path/creds are intact, and the signing key is present. Don't proceed on assumptions about any of those.

## 1. Authoring (rousseau drafts)
- Write the file into the canonical working tree: `~/subtract.ing/<path>/newfile.txt`.
- `git -C ~/subtract.ing status` and `wc -l ~/subtract.ing/<path>/newfile.txt` — state what you observe before touching anything signed (same discipline as hosuni.c).
- At this point the file is **unsigned → authority.unsigned → it's a suggestion, not canonical.** Nothing downstream acts on it yet.

## 2. Pre-sign prep (agent prepares, does not sign)
- reflex.2 check: the format is OpenSSH signatures via `ssh-keygen -Y sign` / `-Y verify` — no new format to invent, the primitive already round-trips. Good.
- Fix the **namespace** now and record it (the verifier must pass the exact same `-n`): use `subtract.ing`. Don't improvise a per-file namespace.
- Confirm the signing identity is published: `grep jnous ~/.ssh/allowed_signers` — principal is `jnous`, key is `jnous`'s ed25519.
- Stage the exact signing command for the human (below). The agent stops here — **boundary: the agent prepares, the human signs.**

## 3. Signing — human gate (only the human, only on the box holding the private key)
Warn the governor first: this may pop a passphrase dialog. One attempt; if it fails, flag and stop — don't spiral on retries.
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n subtract.ing ~/subtract.ing/<path>/newfile.txt
```
→ produces `newfile.txt.sig` (the detached SSH signature).

## 4. Local verify before anything ships (reflex.4 — verify with a live read before acting)
```
ssh-keygen -Y verify -f ~/.ssh/allowed_signers -I jnous -n subtract.ing -s newfile.txt.sig < newfile.txt
```
Must print `Good "jnous" signature`. If not: do not publish, do not push, surface it.

## 5. Manifest (loop.after.1 / loop.after.2)
- Append to the subtract.ing manifest: filename, `sha256`, signer `jnous`, namespace `subtract.ing`.
- Re-sign the manifest the same way as step 3 (another human-gate signing — batch it with step 3 if doing both in one sitting):
  `ssh-keygen -Y sign -f ~/.ssh/id_ed25519_jnous -n subtract.ing ~/subtract.ing/MANIFEST`
- Re-verify the manifest with `-Y verify` as in step 4.

## 6. Publish — rousseau pushes, others do not
Rousseau owns the canonical `~/subtract.ing/` tree and the deploy path; it is the only node that pushes to the subtract.ing origin. Pushing **already-signed** artifacts is plain infra work — no further human gate.
- Deploy via the existing mechanism (rsync-over-ssh to the web host, or `git push` to the pages remote that the host pulls) these objects:
  - `newfile.txt`
  - `newfile.txt.sig`
  - updated `MANIFEST` + `MANIFEST.sig`
  - `allowed_signers` served at a stable URL, e.g. `https://subtract.ing/allowed_signers` (the key→identity map — without it a stranger can't anchor the principal).
- **Does not push:** Emile and Media are pull-mirrors, not publishers. Surface does not push (and is mid-decommission). GitHub / any git remote may carry the same bytes but is **mirror-only — reflex.5**; it is not the authority and the verifier should not treat it as one.

## 7. Post-publish live check (reflex.4 again, from outside)
```
curl -fsSL https://subtract.ing/<path>/newfile.txt      -o /tmp/v.txt
curl -fsSL https://subtract.ing/<path>/newfile.txt.sig  -o /tmp/v.txt.sig
curl -fsSL https://subtract.ing/allowed_signers         -o /tmp/as
ssh-keygen -Y verify -f /tmp/as -I jnous -n subtract.ing -s /tmp/v.txt.sig < /tmp/v.txt
```
Expect `Good "jnous" signature`. Done.

## How a stranger confirms it a year later
1. Fetch from `subtract.ing`: `newfile.txt`, `newfile.txt.sig`, and `allowed_signers`. (Optionally also `MANIFEST` + `MANIFEST.sig` to cross-check the file's sha256 against a signed list.)
2. Run:
   ```
   ssh-keygen -Y verify -f allowed_signers -I jnous -n subtract.ing -s newfile.txt.sig < newfile.txt
   ```
   `Good "jnous" signature` + the principal resolving in `allowed_signers` = authorship established. The signature is self-contained and offline-verifiable; it doesn't expire.
3. Authority boundary the verifier is relying on: **the signature proves authorship; the identity→key binding is anchored by the signing key's own domain** (`subtract.ing` serving `allowed_signers` under the same name as the principal — reflex.5). Git hosts mirroring the file prove nothing.
4. Weak point to harden: that domain-as-anchor assumption. Strengthen the binding with an out-of-band copy of the key fingerprint — a DNS `TXT` record on `subtract.ing`, and/or a signed git tag — so a year-later verifier who distrusts the live web host still has a second path to the same key. The `.sig` itself needs no maintenance; only the identity anchor does.
