# Plan: publish a verifiable `.txt` to subtract.ing

## 0. Pre-flight — reflex checks before touching anything

- **reflex.2 / don't invent a format.** The format is SSHSIG via `ssh-keygen -Y sign`. Don't design one. Confirm the existing canonical artifact verifies and learn its exact namespace:
  ```
  curl -s https://subtract.ing/governance.conf.universal.txt        -o /tmp/gov.txt
  curl -s https://subtract.ing/governance.conf.universal.txt.sig    -o /tmp/gov.sig
  curl -s https://subtract.ing/allowed_signers                      -o /tmp/allowed_signers
  ssh-keygen -Y verify -f /tmp/allowed_signers -I <governor-identity> -n <namespace> -s /tmp/gov.sig < /tmp/gov.txt
  ```
  Whatever `-n` namespace and which key-id makes that return `Good "<namespace>" signature` — reuse *exactly* that for the new file. (`jnous` is the expected signing key.)
- **loop.before.** Verify the last signature on the canonical tree, surface any unsigned drift in `~/human/`, and stop — the governor decides whether to proceed before any new signing happens.
- **reflex.5.** Canonical home for this file is the signing key's domain: `subtract.ing`. Any git remote is a mirror, not the source of truth.

## 1. Draft — agent (Claude on Rousseau)

- Rousseau is node 01 and canonical for `~/human/`. Author the file there, e.g. `~/human/<name>.txt`. Agent may freely create, edit, stage. This is reversible work — no permission gate.
- No `.sig` yet. An unsigned file is a suggestion (`authority.unsigned`), so it is not yet publishable as canonical.

## 2. Sign — human gate (governor only)

- The agent does **not** run this and does not touch the private key. `claude -p`/agent-initiated signing is out of scope; new signing is the one hard human gate (`boundary`, `authority.source`).
- Governor runs, on Rousseau:
  ```
  ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n <namespace> ~/human/<name>.txt
  ```
  → produces `~/human/<name>.txt.sig` (SSHSIG, ASCII-armored).
- If the governor's pubkey is not already a line in the published `allowed_signers`, that line gets added now: `<identity> namespaces="<namespace>" ssh-ed25519 AAAA...`. That file itself should be signed/stable since it is the trust root.

## 3. Publish — Rousseau pushes; nothing else does

- **Rousseau** holds the canonical `~/human/` tree and the deploy credential for `subtract.ing`; the push originates here. Deploy the *pair* (and updated `allowed_signers` if changed) so both are reachable at predictable URLs:
  ```
  https://subtract.ing/<name>.txt
  https://subtract.ing/<name>.txt.sig
  https://subtract.ing/allowed_signers
  ```
  Use whatever the existing deploy mechanism is for `governance.conf.universal.txt` (same host, same path convention) — don't introduce a new channel.
- **Emile (m2mini)** does *not* push. It's an execution-offload target (`ssh m2mini "claude -p"`), not a publishing authority.
- **Acer / "Media" (acer1660ti)** does *not* push and never hosts canonical content — it's NAS/service infrastructure outside the formation, warm-backup tier only.
- **Surface** is a governor terminal, not a publish origin.
- Pushing this *already-signed* bundle is infra, not a gate (`feedback: human gate scope`) — agent may do it once step 2 is done.

## 4. Mirror — optional, explicitly mirror-only

- If mirrored to a git host, the commit/README must not present the git copy as authoritative. `reflex.5`: load-bearing content is canonical under `subtract.ing`; the git host is a convenience replica.

## 5. Post-session — loop.after

- Update the archive manifest on Rousseau to list `<name>.txt` + its `.sig` + the SHA256 of each.
- Governor signs the updated manifest (`ssh-keygen -Y sign ... manifest`). Refresh the SDXC/FROZEN air-gap snapshot on the next discover.sh run so the signed pair lands in the cold tier too.

## 6. How a stranger verifies it, a year later

With nothing but a browser/curl and OpenSSH:

```
curl -sO https://subtract.ing/<name>.txt
curl -sO https://subtract.ing/<name>.txt.sig
curl -sO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <governor-identity> -n <namespace> -s <name>.txt.sig < <name>.txt
```

- Exit status `0` and `Good "<namespace>" signature for <identity>` → the file is byte-for-byte what the holder of key `jnous` signed. Any edit to the `.txt` breaks it.
- **Trust root:** `allowed_signers` is served over TLS from `subtract.ing` — the signing key's own domain. Domain control + cert is the binding between the human and the public key (`reflex.5`, `authority.source`).
- **Continuity cross-check:** the same `ssh-ed25519 AAAA...` pubkey verifies `governance.conf.universal.txt.sig` and other long-standing canonical artifacts. A verifier can confirm the key didn't appear out of nowhere — it's the same one that's been signing the corpus. If the key ever rotated, the old `allowed_signers` line stays valid for old signatures (SSHSIG carries no expiry; revocation would be published as a separate signed notice).
- Git mirrors, caches, or reposts prove nothing on their own — only the `ssh-keygen -Y verify` pass against the domain-served `allowed_signers` does.

## Authority boundaries, summarized

| Action | Who | Gate? |
|---|---|---|
| Draft / edit / stage `<name>.txt` | agent on Rousseau | no — reversible |
| `ssh-keygen -Y sign` (private key) | governor only | **yes — the human gate** |
| Add line to `allowed_signers` | governor | yes — part of signing trust root |
| Push signed pair to `subtract.ing` | Rousseau (agent ok) | no — infra |
| Mirror to git host | Rousseau (agent ok) | no — but must be labeled mirror-only |
| Update + sign manifest | agent updates, governor signs | sign step is a gate |
| Publish from Emile / Acer / Surface | — | never |

No step here requires inventing a signature scheme, a new endpoint, or a new key. If any of the pre-flight `ssh-keygen -Y verify` checks fail, stop and surface it — don't publish on top of unverified state.
