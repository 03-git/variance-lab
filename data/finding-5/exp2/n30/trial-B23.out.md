# Plan — publish a verifiable `.txt` to subtract.ing

Output only. Nothing below is executed.

## 0. Pre-flight (loop.before — runs before any action)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds, node state. Do not proceed if it flags drift on the subtract.ing endpoint or the signing path.
- Verify the last signature in the publishing manifest before adding to it:
  `ssh-keygen -Y verify -f ~/subtract.ing/allowed_signers -I <governor-identity> -n file -s <last-published>.txt.sig < <last-published>.txt`
- Surface any unsigned drift in `~/subtract.ing/` (`git status`, compare manifest to what's actually served). Human decides: sign / continue / abort. The agent does not decide this.

## 1. Prepare the artifact (agent does this)
- Write the file at the canonical path under the signing key's domain — `~/subtract.ing/<name>.txt`. Per reflex.5, the copy served from subtract.ing is canonical; a GitHub copy would be mirror-only and carries no authority.
- Freeze the bytes. No trailing-whitespace normalization, no CRLF surprises — the signature covers exact bytes. `wc -c ~/subtract.ing/<name>.txt` and note it.
- Confirm the verification format *before* relying on it (reflex.2): the signature must be one `ssh-keygen -Y verify` can check — i.e. an SSH signature with namespace `file`, not a hand-rolled scheme.

## 2. Sign — **authority boundary** (the human, not the agent)
- The agent prepares the exact command; the governor runs it with the private key. The agent never touches the private key, and "Rousseau can push" is not "Rousseau can sign."
- Command the governor runs (on whichever machine holds the key — not necessarily Rousseau, never Emile):
  `ssh-keygen -Y sign -f ~/.ssh/<signing_key> -n file ~/subtract.ing/<name>.txt`
  → produces `~/subtract.ing/<name>.txt.sig` (armored `-----BEGIN SSH SIGNATURE-----`).
- The signature is what makes the claim real (authority.signed). Until it exists, the `.txt` is a suggestion.

## 3. Make the verifier resolvable a year out
- Ensure the signing key's public half is published as an `allowed_signers` line at a stable URL under subtract.ing, e.g. `subtract.ing/allowed_signers.txt`, format:
  `<governor-identity> namespaces="file" <keytype> <base64-pubkey>`
- This is the thing a stranger needs in 12 months. If the key isn't already pinned there, that line gets added, and it too should be covered by the manifest signature. Don't rotate the signing key without leaving the old pubkey discoverable.

## 4. Publish (which machine pushes)
- **Rousseau pushes.** It's the archive node and the governor's workstation, and it holds the canonical `~/subtract.ing/` tree. Deploy `<name>.txt` + `<name>.txt.sig` to the subtract.ing web endpoint by the existing publish path (rsync/deploy script in `~/subtract.ing/`, or `git push` to the host that *serves* subtract.ing — the origin that backs the domain, not a mirror).
- **Emile does not push.** It's execution offload only; publishing authority doesn't live there.
- **Surface does not push.** Governor terminal, not the canonical tree.
- A push to GitHub (if any) is mirror-only (reflex.5) — fine for redundancy, irrelevant to authorship.
- Confirm the live endpoint serves both files: a plain `curl -sI https://subtract.ing/<name>.txt` and `curl -s https://subtract.ing/<name>.txt.sig` — a live read, not an assumption (reflex.4).

## 5. Close the loop (loop.after)
- Update the publishing manifest in `~/subtract.ing/` to list `<name>.txt` and its `.sig` (and byte count / date 2026-05-10).
- The governor re-signs the manifest:
  `ssh-keygen -Y sign -f ~/.ssh/<signing_key> -n file ~/subtract.ing/MANIFEST`
- Commit on the canonical host.

## How a stranger verifies, a year from now
1. Fetch all three: `curl -sO https://subtract.ing/<name>.txt`, `curl -sO https://subtract.ing/<name>.txt.sig`, `curl -s https://subtract.ing/allowed_signers.txt -o allowed_signers`.
2. Run:
   `ssh-keygen -Y verify -f allowed_signers -I <governor-identity> -n file -s <name>.txt.sig < <name>.txt`
   → `Good "file" signature for <governor-identity>` means the bytes are exactly what the holder of the subtract.ing signing key signed.
3. Cross-check the `<name>.txt` line against the signed `MANIFEST` (same `ssh-keygen -Y verify` dance) to confirm it's a deliberate publication, not a stray file.
4. Trust chain: the file is canonical because it's served under the signing key's own domain; the key is identified by the `allowed_signers` entry at that same domain; the signature ties the two together. No git host, no CA, no third party is load-bearing.

## Authority boundaries, summarized
- Agent (Rousseau's Claude): writes the `.txt`, drafts commands, runs the publish/deploy, updates the manifest, does the live-read checks. Prepares only.
- Governor (human): runs `ssh-keygen -Y sign` for both the file and the manifest. The signature is the authority; the human is its source.
- Rousseau: the machine that pushes to the canonical endpoint.
- Emile / Surface / GitHub: do not push canonical content; mirrors and offload only.

One open question before step 2, for the governor: is the subtract.ing signing key already published in an `allowed_signers` file at a stable subtract.ing URL with `namespaces="file"`? If not, that's a prerequisite, not a step.
