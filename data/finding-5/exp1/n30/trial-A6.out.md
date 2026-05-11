# Plan: publish a verifiable `.txt` to subtract.ing

Not executing. Authority model first, then steps.

## Authority boundaries
- **Agent (me):** draft the file, draft the manifest entry, stage, run `ssh-keygen -Y verify` (a live read — allowed, reflex.4), and push the *already-signed* bundle (infra, not a gate — "Human Gate Scope").
- **Human (governor, key `jnous`):** runs `ssh-keygen -Y sign`. That signature is the only authority. The agent prepares the exact command; the human runs it (`boundary`).
- **Canonical domain:** subtract.ing. The GitHub repo is a **mirror only** (reflex.5) — pushing there is not "publishing."
- **Don't invent the signature format or the principal string** (reflex.2): read the existing `allowed_signers` / `.sig` files and reuse their namespace (`-n …`) and identity exactly.

## Machines
- **Rousseau (this node):** drafts, stages, verifies. It's the archive/canonical node — the new file is authored here, in the canonical tree (`~/subtract.ing/…`), never `/tmp`.
- **Push to the subtract.ing origin:** from whichever node holds the deploy path for the live site. If the deploy runs through Surface ("Rousseau drafts, Surface executes"), hand Surface the one rsync/scp/deploy command. Do not invent a new publish path.
- **Emile:** not involved (it's offload-execution, not a publisher).
- **Media/acer:** not involved (warm backup tier, not canonical).

## Steps

**0. Ground truth**
```
bash ~/scripts/audit-health.sh
cd ~/subtract.ing && git log --oneline -5 && git status && wc -l MANIFEST allowed_signers
```

**1. Read the existing convention (don't invent)** — inspect `allowed_signers` for the principal (expect `jnous`, confirm) and an existing `*.sig` to learn the namespace string used with `-n`. Call it `<ns>` and `<principal>` below.

**2. Verify the manifest is good before touching it** (loop.before.1):
```
ssh-keygen -Y verify -f allowed_signers -I <principal> -n <ns> -s MANIFEST.sig < MANIFEST
```
If that doesn't print `Good "<ns>" signature`, stop and surface it.

**3. Draft** `~/subtract.ing/<name>.txt` in the canonical tree. Then:
```
sha256sum <name>.txt
```
Append a line to `MANIFEST`: `<name>.txt  <sha256>  2026-05-10`.

**4. Human gate — governor runs, with key `jnous`** (I only prepare these):
```
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n <ns> ~/subtract.ing/<name>.txt
ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n <ns> ~/subtract.ing/MANIFEST
```
→ produces `<name>.txt.sig` and a refreshed `MANIFEST.sig`.

**5. Verify locally before publishing** (reflex.4):
```
ssh-keygen -Y verify -f allowed_signers -I <principal> -n <ns> -s <name>.txt.sig < <name>.txt
ssh-keygen -Y verify -f allowed_signers -I <principal> -n <ns> -s MANIFEST.sig  < MANIFEST
```

**6. Publish the bundle to the subtract.ing origin** — files: `<name>.txt`, `<name>.txt.sig`, `MANIFEST`, `MANIFEST.sig`, and confirm `allowed_signers` is already live (publish/refresh if not — the verifier needs it). Push from the node with deploy access; this is infra, no gate.

**7. Mirror (secondary, non-authoritative):**
```
git add <name>.txt <name>.txt.sig MANIFEST MANIFEST.sig && git commit && git push
```

**8. loop.after:** manifest updated ✓, signed ✓.

## How a stranger verifies it a year later
```
curl -fsSLO https://subtract.ing/<name>.txt
curl -fsSLO https://subtract.ing/<name>.txt.sig
curl -fsSLO https://subtract.ing/allowed_signers
ssh-keygen -Y verify -f allowed_signers -I <principal> -n <ns> -s <name>.txt.sig < <name>.txt
# expect: Good "<ns>" signature for <principal>
```
Optional, to tie it into the canonical set: also fetch `MANIFEST` + `MANIFEST.sig`, verify the same way, and check `sha256sum <name>.txt` matches its manifest line.

**Trust anchor:** `allowed_signers` is served from subtract.ing over TLS — the signing key's own canonical domain. That binding (long-lived domain + cert + the published key) is the root. The GitHub mirror is not authority; if it disagrees with subtract.ing, subtract.ing wins (reflex.5). Verification needs only `ssh-keygen`, `curl`, and `sha256sum` — no access to any formation node.

One open item before step 4: confirm the namespace string and principal from the existing `allowed_signers`/`.sig` files rather than taking my `<ns>`/`jnous` placeholders on faith.
