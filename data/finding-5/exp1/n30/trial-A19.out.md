Plan only — nothing executed.

## 0. Pre-flight (loop.before)

- `bash ~/scripts/audit-health.sh` — ground-truth on DNS, creds, drives before touching anything.
- Locate the canonical site source (the tree that publishes to `subtract.ing`, not a GitHub clone). On it: `git status`, `git log --oneline -5`, `wc -l` on the manifest.
- Verify the **current** manifest signature before editing it: `ssh-keygen -Y verify -f ./allowed_signers -I jnous -n file -s MANIFEST.sig < MANIFEST`. If that fails or there's unsigned drift, stop and surface it (loop.before.2/3). Do not stack a new file on an unverified base.

## 1. Author the file (agent does this)

- Write `foo.txt` into the canonical source tree on **Rousseau** (governor workstation + canonical node). Agent prepares content. Agent does **not** sign — `boundary`, `authority.unsigned: do not act`.
- Stage the manifest change: append `foo.txt` + `sha256` to `MANIFEST` (or `SHA256SUMS`). This is a *prepared diff*, still unsigned.

## 2. Human gate — signing (governor only)

Only new signing is the human gate. Warn first: these prompt for the key passphrase (blocking popup). Governor runs, on Rousseau:

```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file foo.txt        # -> foo.txt.sig
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file MANIFEST       # -> MANIFEST.sig  (loop.after.1/.2)
```

Namespace `file` is the convention; it must be identical on the verify side, so it's documented, not improvised (reflex.2 — `ssh-keygen -Y` *is* the format, nothing invented). Signer identity in `allowed_signers` is `jnous`.

The signature is over the file bytes, so it survives a year, CDN caching, and mirror copies untouched.

## 3. Trust root must be on the signing domain (reflex.5)

`allowed_signers` — one line, `jnous ssh-ed25519 AAAA...` — must be reachable at `https://subtract.ing/allowed_signers`. Load-bearing content (the file, its `.sig`, and the key that anchors it) is canonical **under the signing key's domain**. GitHub or any git host is mirror-only — a stranger is pointed at `subtract.ing` URLs, never the mirror, for the authority chain.

## 4. Publish — which machine pushes

- **Rousseau pushes.** It holds the canonical tree and the only deploy credential. `rsync -av --checksum foo.txt foo.txt.sig MANIFEST MANIFEST.sig <deploy-target-for-subtract.ing>`, then a mirror push to the git host if one exists.
- **Emile does not push.** Execution-offload node only; `ssh m2mini "claude -p"` is for reasoning/build work, not for being a publish origin.
- **Surface does not push.** Governor terminal, no deploy authority.
- **Media/acer1660ti does not push.** Service infra + warm backup tier, not formation publish.

Pushing already-signed artifacts across nodes/mirrors is plain infra — agent does it without asking. The asking happened at step 2 and nowhere else.

## 5. How a stranger verifies, a year later

Only OpenSSH required, no subtract.ing-specific tooling:

```
curl -O https://subtract.ing/foo.txt
curl -O https://subtract.ing/foo.txt.sig
curl -O https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s foo.txt.sig < foo.txt
```

`Good "file" signature for jnous` + exit 0 ⇒ authorship confirmed. If they pulled `foo.txt` from a GitHub mirror instead, they re-run the same `verify` against it — mirror trustworthiness is irrelevant, the signature is self-checking (reflex.4: verify with a live read, don't trust the carrier). Optional hardening for the verifier: cross-check the `allowed_signers` key fingerprint against an independent copy (web.archive.org snapshot of `subtract.ing/allowed_signers`, or a fingerprint published elsewhere) so the trust root doesn't rest solely on whoever controls the domain a year out.

## Authority boundaries, summarized

- Agent: writes `foo.txt`, stages the manifest diff, pushes signed artifacts, points verifiers at canonical URLs.
- Human: runs `ssh-keygen -Y sign` — the only gate, and the thing that confers authority. TLS / domain control is **not** the authority; the SSH signature is. An old signed file still verifies even if `subtract.ing` later changes hands.
- Canonical = `subtract.ing` (signing key's domain). Git hosts = mirror-only.
- Push origin = Rousseau. Emile / Surface / Media do not publish.
