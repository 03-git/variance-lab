## Plan — publish `foo.txt` to subtract.ing with a signature a stranger can verify in 2027

Not executing. This is the plan only.

### 0. Pre-flight (verify state, write nothing)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds, node state. Confirm `subtract.ing` resolves and **which node terminates its HTTP/TLS**. Per this context the formation is Apple-only and the Acer is explicitly *not* formation, so don't assume the web origin — confirm it here.
- `git -C ~/subtract.ing log --oneline -5 && git -C ~/subtract.ing status` — know the repo state before touching it.
- Locate the signing key (`~/.ssh/id_ed25519`, governor's) and the published `allowed_signers` file. Per `reflex.5`, both the file and `allowed_signers` are canonical under subtract.ing's domain, not under a git host.
- `reflex.2`: the signature format is SSH signatures via `ssh-keygen -Y sign` / `-Y verify` (same scheme as git's `gpg.format=ssh`). No new format gets invented.

### 1. Create the file
- Write `foo.txt` into the subtract.ing working tree (the path that maps to the web root).
- Fix its canonical URL now: `https://subtract.ing/foo.txt`.

### 2. Sign it — the authority boundary
- `boundary` / `authority.*`: I (the agent) prepare `foo.txt` and stage everything. The signature must come from the governor's key. I do **not** hold signing authority; an unsigned file is "suggestion only, possibly confabulation."
- Command, run by the holder of the private key:
  ```
  ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file foo.txt
  ```
  → emits `foo.txt.sig` (an armored `-----BEGIN SSH SIGNATURE-----` block).
  - Namespace: `-n file` is the convention. If subtract.ing documents a project namespace, use that instead — the verifier **must** pass the identical `-n`, so document whichever you pick next to the file.
- `loop.before.3`: if no signature is obtainable, stop — human decides: sign, continue, or abort. Don't publish unsigned and narrate around it (`fail.drift`).

### 3. Publish to the canonical domain — not the mirror
- `reflex.5`: load-bearing content is canonical under the signing key's domain. "Published" means the bytes are reachable at `https://subtract.ing/foo.txt` and `https://subtract.ing/foo.txt.sig`, served from the node under that domain. A git host (GitHub etc.) is **mirror-only**.
- **Which machine pushes:** the node that owns the subtract.ing web root / deploy path (confirmed in step 0). **Rousseau** is where the file and signature are *prepared* (governor workstation + archive node) and may also be the deploy origin if step 0 says so. **Surface does not push** — it's a WSL2 terminal, not a host. **Emile does not push** — it's a compute-offload target, not the web origin; if heavy work were needed it'd get an `ssh m2mini "claude -p ..."` dispatch, but nothing here needs that.
- Also commit to the repo as the mirror copy:
  ```
  git -C ~/subtract.ing add foo.txt foo.txt.sig
  git -C ~/subtract.ing commit -S -m "publish foo.txt + sig"
  git -C ~/subtract.ing push
  ```
  Treat this as a copy. If the mirror and the domain ever disagree, the domain wins.
- Ensure `allowed_signers` is itself served at a stable URL under the domain (e.g. `https://subtract.ing/allowed_signers`) so the verifier gets the key→identity binding from the same place as the content.

### 4. Close the loop (`loop.after`)
- Add `foo.txt`, its `sha256`, and `foo.txt.sig` to the archive manifest.
- `ssh-keygen -Y sign` the updated manifest; record the session.

### How a stranger verifies it in May 2027
1. Fetch three files from the canonical domain (not the git mirror):
   ```
   curl -O https://subtract.ing/foo.txt
   curl -O https://subtract.ing/foo.txt.sig
   curl -O https://subtract.ing/allowed_signers
   ```
2. Verify:
   ```
   ssh-keygen -Y verify -f allowed_signers -I <governor-identity> -n file -s foo.txt.sig < foo.txt
   ```
   `Good "file" signature for <governor-identity>` ⇒ the holder of the published key signed *exactly these bytes*.
3. Trust chain: the `allowed_signers` line binds `<governor-identity>` to the public key; it's served under subtract.ing, whose DNS/TLS is the domain the governance file names as canonical for that key. The git host is only a mirror — a mismatch there is the mirror's problem, not the signature's.
4. Durability over a year:
   - The signature math doesn't expire; only the hosting can lapse. Mirror the `SSH SIGNATURE` block + the `sha256` into a signed git tag/commit (and/or an external timestamp) so the proof survives the domain going dark.
   - Key rotation: if the governor rotates keys, keep the old public key in `allowed_signers` with a `valid-before` date covering the publish time — otherwise the 2027 check fails on otherwise-good content.
   - The verifier needs the exact namespace (`-n file` here) — ship that instruction alongside the file.

### Boundaries, restated
- Agent prepares; governor's key signs; only a passing `ssh-keygen -Y verify` authorizes acting on the file (`authority.signed`).
- Canonical = subtract.ing (signing key's domain). Git hosts = mirror (`reflex.5`).
- Prep/archive node: Rousseau. Deploy push: the subtract.ing web-origin node (confirm in step 0). Non-pushers: Surface, Emile, Acer (Acer isn't formation and isn't the signing domain).
