## Plan: publish a verifiable `.txt` to subtract.ing

Not executing — this is the sequence, the boundaries, and the verifier's side.

### 0. Pre-flight (the loop, before acting)
- `bash ~/scripts/audit-health.sh` on Rousseau — ground truth for DNS, drives, node state. Don't proceed on assumptions.
- Confirm the canonical working tree and which node is the subtract.ing **origin** (the host that answers `https://subtract.ing/`). reflex.5: the file is canonical under the signing key's domain; GitHub or any git host is **mirror-only** and does not count as published.
- `git -C ~/subtract.ing log --oneline -5` and `git -C ~/subtract.ing status` — know the current head before adding to it.
- Verify the *existing* signature chain is intact before extending it: `ssh-keygen -Y verify` against the current manifest/`.sig` (loop.before.1, loop.before.2). If current state doesn't verify, stop and surface that — don't stack a new artifact on unverified state.

### 1. Draft (Rousseau, agent does this)
- Write the new file into the canonical tree, e.g. `~/subtract.ing/<path>/newfile.txt`. Plain UTF-8, final newline. Rousseau drafts; this is reversible staging work, no gate.

### 2. Sign — **human gate**
- New signing is the one hard gate (`boundary`: the agent prepares, the human signs; "Human Gate Scope": only *new* signing is a human gate). The agent does **not** run this; it hands the governor the exact command:
  ```
  ssh-keygen -Y sign -n file -f ~/.ssh/id_ed25519 ~/subtract.ing/<path>/newfile.txt
  ```
  → produces `newfile.txt.sig` (armored SSH signature, namespace `file`). Key is `jnous` — the formation's existing signing identity, not a new format (reflex.2: `ssh-keygen -Y` is the primitive already in use; don't invent anything).
- Warn the governor first if the key touch triggers an agent/passphrase prompt (feedback: warn before human gates).

### 3. Verify locally before it goes anywhere (action → verification, reflex.4)
- Ensure an `allowed_signers` line exists for the identity, e.g.:
  ```
  jnous@subtract.ing ssh-ed25519 AAAA...<pubkey>...
  ```
- Live read, not memory:
  ```
  ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file \
    -s ~/subtract.ing/<path>/newfile.txt.sig < ~/subtract.ing/<path>/newfile.txt
  ```
  Expect `Good "file" signature for jnous@subtract.ing`. If it doesn't print that, the publish does not happen.

### 4. Update and re-sign the manifest (loop.after.1, loop.after.2)
- Add `newfile.txt` + its hash to the canonical manifest in the tree.
- Governor re-signs the manifest the same way (`ssh-keygen -Y sign -n file -f ~/.ssh/id_ed25519 MANIFEST`). Re-verify it with `ssh-keygen -Y verify`. The manifest chain is what lets a stranger trust *which* files are canonical, not just that one blob has a good signature.

### 5. Publish (which machine pushes)
- The triplet must all be reachable under `https://subtract.ing/`: `newfile.txt`, `newfile.txt.sig`, and the public key / `allowed_signers` (or an `allowed_signers` published at a stable subtract.ing URL). A signature is worthless to a stranger if the pubkey isn't anchored at the domain.
- **Pushes:** the subtract.ing origin node (confirmed in step 0). Per the formation split, Rousseau drafts and the deploy node executes the publish; pushing *already-signed* artifacts across nodes is infra work, not a gate ("Human Gate Scope"). If the origin is served from Rousseau itself, Rousseau pushes; if it's fronted elsewhere (e.g. via the deploy path), the artifacts go there.
- **Does not push:** any git host (GitHub etc.) as the *canonical* location — mirror only (reflex.5). Mirroring there afterward is fine but is not "published."
- After deploy, fetch it back over HTTPS and re-run the `ssh-keygen -Y verify` against the *live* URL content, not the local copy (reflex.4 again — verify with a live read).

### 6. How a stranger verifies it a year from now
1. `curl -O https://subtract.ing/<path>/newfile.txt`
2. `curl -O https://subtract.ing/<path>/newfile.txt.sig`
3. Get the signing pubkey from the same domain (it's canonical under the signing key's domain, by design): `curl https://subtract.ing/<allowed_signers path>` → build an `allowed_signers` line for `jnous@subtract.ing`.
4. ```
   ssh-keygen -Y verify -f allowed_signers -I jnous@subtract.ing -n file \
     -s newfile.txt.sig < newfile.txt
   ```
   `Good "file" signature` ⇒ the file is byte-for-byte what the holder of the `jnous` key signed.
5. Cross-check the pubkey fingerprint against the other places the governor has anchored it (the signed MANIFEST chain, prior `.sig`-bearing releases). That's what closes the loop: the domain says "this key is mine," the prior signed history corroborates the key, and the signature binds the key to this file. Time doesn't enter the math — the verification holds as long as the pubkey stays published, which is why step 5's anchoring matters more than any timestamp.

### Authority boundaries, summarized
- Agent (Claude/Rousseau): draft, stage, run all `-Y verify` reads, update manifest text, push already-signed artifacts, mirror to git.
- Human only: every `ssh-keygen -Y sign` invocation (the file and the manifest). That's the authority — the signature is what makes the claim, and only the human produces it.
- Unsigned anything (including this plan, including resumed session context) is suggestion only — nothing acts on the file until step 3's verify passes.
