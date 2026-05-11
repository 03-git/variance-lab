# Plan: publish a verifiable `.txt` to subtract.ing

Not executing — this is the procedure, the boundaries, and the verifier's check.

## 0. Ground truth before anything (`loop.before`, `reflex.4`)

- `bash ~/scripts/audit-health.sh` — DNS, drives, node state.
- Verify the *current* canonical manifest before touching it; resumed/assumed state is unsigned:
  - `curl -fsSL https://subtract.ing/MANIFEST -o /tmp/MANIFEST.cur`
  - `curl -fsSL https://subtract.ing/MANIFEST.sig -o /tmp/MANIFEST.cur.sig`
  - `curl -fsSL https://subtract.ing/allowed_signers -o /tmp/allowed_signers`
  - `ssh-keygen -Y verify -f /tmp/allowed_signers -I jnous@subtract.ing -n file -s /tmp/MANIFEST.cur.sig < /tmp/MANIFEST.cur`
- If that fails or the live manifest diverges from what's in `~/subtract.ing/`, stop and surface the drift. Don't build on an unverified base.

## 1. Draft the file — Rousseau (01)

Rousseau drafts; this is local, reversible, no gate.
- Write content to the canonical working tree, not `/tmp`: `~/subtract.ing/<path>/newfile.txt`.
- `git -C ~/subtract.ing log --oneline -5` and `git -C ~/subtract.ing status` first so you're patching current state.
- Normalize line endings / trailing newline now — the bytes you hash are the bytes you sign are the bytes you serve. Any later reflow breaks the signature.

## 2. Prepare the manifest delta — Rousseau (prepared, not authorized)

- `shasum -a 256 ~/subtract.ing/<path>/newfile.txt` → record the digest.
- Add the line to `~/subtract.ing/MANIFEST` (path + sha256, matching existing rows' format).
- Leave it staged. The agent prepares; it does not sign. (`boundary`)

## 3. Human gate — signing (`reflex.2`, `authority.*`, `boundary`)

Only new signing is a human gate. The agent hands the governor the exact commands; the governor runs them on the machine holding the private half of `jnous` (his `~/.ssh/` or token — the plan does not assume which node, and the key never moves to do this):

```
# detached SSH signatures, namespace "file" — the established primitive, not a new format
ssh-keygen -Y sign -f ~/.ssh/<jnous_key> -n file ~/subtract.ing/<path>/newfile.txt
ssh-keygen -Y sign -f ~/.ssh/<jnous_key> -n file ~/subtract.ing/MANIFEST
```

Produces `newfile.txt.sig` and `MANIFEST.sig`. `allowed_signers` already pins `jnous@subtract.ing namespaces="file" ssh-ed25519 AAAA…`; only touch it if the key rotated, and that's its own signed change.

Nothing downstream proceeds until these `.sig` files exist. The signature *is* the authority — `authority.source` is the human, not the agent's say-so.

## 4. Push — canonical vs mirror (`reflex.5`)

Pushing an *already-signed* bundle is infra, not a gate — agent executes (current formation: Surface runs the push pre-2026‑05‑22 reorg; after that, Rousseau).

- **Canonical:** the bundle — `newfile.txt`, `newfile.txt.sig`, updated `MANIFEST`, `MANIFEST.sig` — goes to the host serving `https://subtract.ing/` (the signing key's domain). `rsync -av --checksum` over ssh to that origin. This is the only copy that counts.
- **Mirror:** `git -C ~/subtract.ing add … && git commit && git push` to GitHub/etc. is fine for distribution but is **mirror-only** — never the root of trust. A verifier who only has the GitHub copy has not verified anything; they still need the `.sig` and `allowed_signers` resolved under `subtract.ing`.
- Confirm live: `curl -fsSL https://subtract.ing/<path>/newfile.txt | shasum -a 256` matches step 2's digest.

## 5. Close the loop (`loop.after`)

- Manifest already updated and signed in step 3 — confirm the live `MANIFEST` is the signed one.
- Note the addition in the session record under `~/human/sessions/`.

## 6. How a stranger verifies it, a year out

Everything resolved from `subtract.ing` — the signing key's domain — not from any git host:

```
curl -fsSL https://subtract.ing/<path>/newfile.txt      -o newfile.txt
curl -fsSL https://subtract.ing/<path>/newfile.txt.sig  -o newfile.txt.sig
curl -fsSL https://subtract.ing/allowed_signers         -o allowed_signers

# 1. authorship of the file itself
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file \
  -s newfile.txt.sig < newfile.txt          # -> "Good \"file\" signature for jnous@subtract.ing"

# 2. corroborate via the signed manifest
curl -fsSL https://subtract.ing/MANIFEST     -o MANIFEST
curl -fsSL https://subtract.ing/MANIFEST.sig -o MANIFEST.sig
ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file \
  -s MANIFEST.sig < MANIFEST
shasum -a 256 newfile.txt                    # digest must appear verbatim in MANIFEST
```

Both checks must pass. The namespace (`file`) and principal (`jnous@subtract.ing`) must match what was used at signing — a mismatch there is a fail, not a warning. `ssh-keygen -Y verify` returning success is the whole claim: `authority.signed → act on it`. If the file is reachable but unsigned, or only present on a git mirror, it's a suggestion, not an authored artifact.

## Authority boundaries, condensed

| Step | Who | Why |
|---|---|---|
| draft, hash, stage manifest, write the signing commands | agent (Rousseau) | reversible, local — no gate |
| `ssh-keygen -Y sign` with the `jnous` key | **human only** | `boundary` — the signature confers authority; agent never holds/uses the private key |
| push the signed bundle to `subtract.ing` origin | agent (Surface now / Rousseau post-reorg) | already-signed artifact movement is infra (`Human Gate Scope`) |
| push to GitHub/git mirrors | agent | distribution only — `reflex.5`, never the verification root |
| verify | anyone, forever | `ssh-keygen -Y verify` + `allowed_signers` from `subtract.ing` |

One thing I'd need from you before this is real: confirm the exact `jnous` key path/filename and the canonical origin host for `subtract.ing` — I've left both as placeholders rather than guess.
