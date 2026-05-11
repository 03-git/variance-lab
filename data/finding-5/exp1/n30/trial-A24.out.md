# Plan: publish a signed `.txt` to subtract.ing

## 0. Reflex gate (before touching anything)
- `reflex.2` — the signature format is **not** invented: it's `ssh-keygen -Y sign` / `ssh-keygen -Y verify` (OpenSSH ≥ 8.2). Confirm `ssh-keygen -Y verify` can consume the output before producing it.
- `reflex.5` — canonical home is the **signing key's domain (subtract.ing)**. GitHub or any git host is mirror-only and never the authority a verifier is pointed at.
- `reflex.4` / `loop.before.1` — before editing the runtime tree, `cd ~/subtract.ing && git log --oneline -5 && git status`, and `ssh-keygen -Y verify` the existing `SHA256SUMS.sig` (or equivalent) so you're not building on drifted state.
- `boundary` — the agent **prepares**; the human **signs**. New signing is the one hard human gate (`authority.signed`, `feedback_human_gate_scope`). Everything downstream of an existing signature is just infra.

## 1. Pre-flight (rousseau)
- `bash ~/scripts/audit-health.sh` — ground truth on DNS, drives, creds.
- Confirm the signing identity in `~/.ssh/allowed_signers` (principal `jnous`, namespace `file`) and that the private key is present (`ssh-keygen -Y sign` will need it / agent).

## 2. Draft (rousseau — Rousseau drafts, Surface executes)
- Author the file at its canonical path in the runtime tree, e.g. `~/subtract.ing/<path>/<name>.txt`. Plain UTF-8, LF, final newline.
- This is reversible staging work — no permission needed.

## 3. Sign — the human gate
Prepare, do **not** run, and hand to the governor:
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file ~/subtract.ing/<path>/<name>.txt
# -> produces <name>.txt.sig  (SSHSIG armored)
```
- Namespace **must** be `file` and must match what the verifier will pass to `-n`.
- Warn first: this touches the agent (`ssh-add`) or prompts for a passphrase — a blocking prompt (`feedback_warn_human_gates`).
- Also (re)generate and have the governor sign the directory manifest so the file is covered by the chain of trust:
  ```
  cd ~/subtract.ing && sha256sum <path>/<name>.txt >> SHA256SUMS
  ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n file SHA256SUMS   # -> SHA256SUMS.sig
  ```

## 4. Publish — which machine pushes
- **Rousseau pushes.** Rousseau is canonical for `~/human/` and the subtract.ing runtime tree; it is the node that writes to the subtract.ing origin (the signing key's domain). The push set: `<name>.txt`, `<name>.txt.sig`, updated `SHA256SUMS` + `SHA256SUMS.sig`, and `allowed_signers` (the public side — see step 5).
- **Surface does not push.** It's the governor terminal; it pulls. (Moot after the 2026-05-22 reorg, but true today.)
- **Emile does not push** canonical. It's a pull-mirror of rousseau's scripts; offload *execution* there, not authority.
- **Acer/Media does not push.** Not formation — service infra only.
- Any GitHub mirror update is downstream and explicitly **not** where the verifier is sent (`reflex.5`).

## 5. Make the public key fetchable
Publish an `allowed_signers` line at a stable subtract.ing URL alongside the file (or in `governance`/keys dir):
```
jnous namespaces="file" ssh-ed25519 AAAA...<the public key>...
```
A stranger needs *some* trust root for the key; binding it to the subtract.ing domain (HTTPS, same origin as the canonical text) is that root. The git mirror is not.

## 6. loop.after
- `loop.after.1` — update the manifest (done in step 3 if SHA256SUMS is the manifest; otherwise update whatever `MANIFEST`/index lists published artifacts).
- `loop.after.2` — sign it (`ssh-keygen -Y sign -n file MANIFEST`).
- Commit in the runtime repo with a plain message; that commit is a mirror record, not the authority.

## 7. How a verifier (stranger, +1 year) confirms authorship
From the subtract.ing domain only:
```
curl -O https://subtract.ing/<path>/<name>.txt
curl -O https://subtract.ing/<path>/<name>.txt.sig
curl -O https://subtract.ing/<keys>/allowed_signers

ssh-keygen -Y verify -f allowed_signers -I jnous -n file \
  -s <name>.txt.sig < <name>.txt
# "Good \"file\" signature for jnous ..."  + exit 0  => authorship confirmed
```
Optional integrity cross-check via the signed manifest:
```
curl -O https://subtract.ing/SHA256SUMS
curl -O https://subtract.ing/SHA256SUMS.sig
ssh-keygen -Y verify -f allowed_signers -I jnous -n file -s SHA256SUMS.sig < SHA256SUMS
sha256sum -c SHA256SUMS --ignore-missing
```
What makes it durable: SSHSIG is detached and self-contained; the only external dependency is the `jnous` public key, served from the signing key's own domain. No timestamp service, no CA, no git host required. If `ssh-keygen -Y verify` exits non-zero a year from now, the claim is false or the file drifted — that's the whole point of the gate.

## Authority boundaries, summarized
| Action | Who | Gate |
|---|---|---|
| Draft `.txt`, stage, edit | agent (rousseau) | none — reversible |
| `ssh-keygen -Y sign` | **governor only** | human gate; agent prepares the command |
| Push signed bundle to subtract.ing | rousseau | infra — already signed, execute |
| Mirror to GitHub | rousseau | infra — explicitly non-authoritative |
| Verify | anyone, anywhere | none — that's the design |

Not executing — plan only.
