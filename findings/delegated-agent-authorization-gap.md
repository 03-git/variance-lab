---
title: Delegated Agent Authorization Gap
date: 2026-03-28
source: production empirical
domain:
  - agent-authorization
  - oauth
  - credential-delegation
  - agentic-access
  - identity
  - financial-api
  - communication-protocol
keywords:
  - delegated agent authorization
  - OAuth agent access
  - agentic credential
  - RFC 8628 device flow
  - GNAP RFC 9635
  - CIBA OpenID
  - SPIFFE machine identity
  - FDX open banking
  - Section 1033 CFPB
  - PSD2 PISP
  - 3D Secure agent
  - bot detection authorized agent
  - Privacy Pass RFC 9577
related_findings:
  - "variance-lab finding 5: instruction-based constraints do not override capability"
  - "variance-lab finding 6: cost inversion - dumber model + capability subtraction beats smarter model + instruction"
methodology: parallel research across domain verticals
finding_class: survey/taxonomy
---

# Delegated Agent Authorization Gap

## Core Finding

Every human-first service uses human-presence signals as a proxy for authorization. The single infrastructure primitive missing across all domains is a **delegated agent authorization credential**: user-signed, time-bounded, scope-limited, with revocation and audit trail.

When a valid machine-readable authorization exists, the human-presence check is redundant. The fix is always the same structural subtraction: **remove the human-presence verification when bearer authorization already proves delegation.**

This was derived empirically from a production KEYMASTER implementation where SSH credential subtraction outperformed instruction-based constraints on identical cross-node dispatch tasks.

> **Unsourced figures struck:** Earlier revisions cited "$0.02/call" (capability subtraction) and "$0.30-0.55/call" (instruction-based) as the comparative cost. No artifact path, sample size, date range, or measurement methodology exists in this repo to ground those figures. Treat the *direction* of the comparison as the load-bearing claim; treat the numeric magnitudes as unsourced operator anecdote pending a reproducible measurement artifact.

## Per-Domain Findings

### Communications (IMAP/SMTP/CalDAV/Messaging)

| Service | Current Barrier | What Works Today | Infrastructure Fix |
|---------|----------------|------------------|-------------------|
| Gmail | OAuth2 consent requires browser; 7-day token in Testing mode | Service accounts with domain-wide delegation (Workspace only) | Long-lived app passwords scoped to IMAP/SMTP; RFC 8628 device flow with non-expiring refresh |
| Microsoft 365 | No application-level IMAP scope; Graph API only | Graph API with admin consent | Application-permission IMAP scope |
| ProtonMail | No IMAP without Bridge GUI daemon | None headless | Headless Bridge with token auth |
| Fastmail | App-specific passwords + IMAP/CalDAV | **Fully agentic today** | None needed |
| iMessage | No API, no protocol docs, Apple-device-only | osascript on local Mac (requires GUI session) | None possible without Apple |
| Signal | signal-cli works headless after registration | Yes, post phone verification | Bot account type without phone verification |
| Discord | Bot token, fully programmatic | **Fully agentic today** | None needed |
| Slack | Bot tokens with granular scopes | **Fully agentic today** (after admin install) | None needed |
| Matrix | Access token via login endpoint | **Fully agentic today** | None needed |

**Pattern:** Services designed for machines (Slack, Discord, Matrix) work. Services designed for humans (Gmail, iMessage) do not. The protocol capability exists (IMAP is programmatic); the auth layer blocks it.

### Identity and Authentication

| Layer | Human-Presence Signal | Subtraction When Authorized |
|-------|----------------------|---------------------------|
| Bot detection (reCAPTCHA, Turnstile, Akamai) | Behavioral scoring, JS challenges, fingerprinting | Remove challenges for requests carrying valid bearer token with agent scope |
| OAuth consent | Interactive browser click | RFC 8628 device flow as first-class grant; prompt=none for pre-authorized agents |
| MFA (push/SMS/biometric) | Physical device interaction | Bypass push/SMS for sessions established via pre-authorized agent credential |
| Session management | Device binding, IP pinning, UA validation | Remove binding for token-authenticated sessions |
| WebAuthn/FIDO2 | Physical presence attestation (UP flag) | Delegated attestation type - authenticator signs delegation cert for agent key pair |
| TLS fingerprinting | JA3/JA4 browser identification | Remove fingerprint checks for authenticated API requests |

**Pattern:** Every check conflates "not human" with "not authorized." The missing designation: **authorized agent acting on behalf of authenticated user.**

### Financial Services and Commerce

| System | API Status | Read | Write | Agent-Ready |
|--------|-----------|------|-------|-------------|
| Major US banks (Chase, WF, BofA, Citi) | Portal-only | Via Plaid/Finicity (bilateral OAuth) | ACH only via Plaid Transfer | Low |
| Schwab (post-TD) | OAuth 2.0 + PKCE | Yes | Yes (trading) | Low - 7-day browser re-auth |
| Interactive Brokers | TWS API + Client Portal | Yes | Yes (trading + FIX) | Medium - IB Gateway Docker workaround |
| Fidelity / Vanguard | None | No | No | None |
| Alpaca | API key auth | Yes | Yes | **High - fully agentic** |
| Tradier | OAuth non-expiring tokens | Yes | Yes | **High - fully agentic** |
| PayPal | REST API OAuth 2.0 | Yes | Yes (payments) | Medium - initial consent interactive |
| Apple Pay / Google Pay | Secure Element biometric | No | No | None - non-extractable |
| Zelle / Venmo | No public API | No | No | None |

**Pattern:** Only brokers built for algorithmic trading (Alpaca, Tradier, IBKR) are agent-accessible. Every consumer financial service assumes the authenticated entity IS the human.

## Missing Standard: Delegated Agent Authorization Credential

No standard exists. Closest building blocks:

| Standard | Status | Gap |
|----------|--------|-----|
| OAuth 2.0 RAR (RFC 9396) | Final 2023 | No agent identity or liability framework |
| GNAP (RFC 9635) | Final 2024 | Near-zero adoption |
| OpenID CIBA | Final | Agent initiates, human approves on separate channel. Closest existing fit |
| Privacy Pass (RFC 9577) | Published 2023 | Apple-only attestation. Could support agent attestation |
| SPIFFE/SPIRE | CNCF Incubating | Machine identity via x509 SVIDs. Maps to agent identity |
| FDX 6.0 | Production | Explicitly excludes payment initiation |
| W3C Verifiable Credentials | Rec 2022 | No payment system accepts VCs |
| eIDAS 2.0 / EUDIW | EU mandate 2026 | Agent delegation not in ARF 1.4 spec |

### What the complete standard requires:

1. **Agent identity attestation** - model, operator, version, distinct from user identity
2. **Delegation credential** - user-signed, time-bounded, scope-limited (amount, merchant, time window)
3. **Liability framework** - loss allocation when agent acts within/outside scope
4. **Real-time revocation** - OCSP-like for agent credentials
5. **Cryptographic audit trail** - proof that specific agent took specific action under specific delegation

## Timeline Estimate

- **2025-2026:** PayPal-style OAuth scoped tokens for existing APIs. Section 1033 read APIs (if rule survives)
- **2027-2028:** CFPB 1033 expansion to payment initiation (requires new rulemaking). FDX write APIs. EU PSD3/PSR with agent-compatible SCA exemptions
- **2029+:** Cross-industry delegated agent authorization standard, possibly under OpenID Foundation

## Infrastructure Implication

Every enterprise deploying agents needs a credential authority under their control. Not a vendor sandbox. Not a cloud guardrail. A KEYMASTER that issues delegation credentials, enforces TTL, and provides physical revocation. The infrastructure where that authority runs is the sovereignty surface.

## Methodology

This finding is a **landscape survey / taxonomy**, not a gated experiment. The per-domain tables are the product of secondary research (vendor documentation, RFCs, public API references) compiled by a single researcher against published sources as of 2026-03-28. The KEYMASTER cost comparison is the only empirical claim in the document, and it is not independently reproduced in this repo.

Gates from the variance-lab handler methodology do not apply uniformly:
- *Pre-committed rubric* — inapplicable: this is a survey, not a scored comparison.
- *Deliberative pass across lineage-distinct reviewers* — not executed for the survey portion.
- *Artifact path for empirical claim* — **missing** for the KEYMASTER cost comparison (see struck figures above); this is a gate miss, not a gate inapplicability.

## Limitations

- Single researcher; single production deployment informing the empirical anchor.
- No controlled experiment: the KEYMASTER comparison is production observation, not an A/B with randomized trial structure.
- No cross-operator replication of either the survey results or the cost comparison.
- API-status claims in domain tables are time-dependent; each row reflects status as of 2026-03-28 and will decay. Timestamps per row were not captured at compile time.
- Reviewer deliberation across lineage-distinct auditors not executed; verdicts in tables are the author's reading of primary-source documentation.
- The KEYMASTER cost claim and the domain taxonomy are epistemically distinct — the former is (unreproduced) measurement, the latter is secondary research. A single "verified" label does not cover both; readers should treat them separately.
