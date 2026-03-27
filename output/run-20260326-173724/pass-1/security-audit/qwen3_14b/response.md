```markdown
# Security Audit Report

## 1. Credential Exposure
**Finding**: No plaintext API keys, tokens, or secrets were found in `/agent-ref/` identity files. Files appear encrypted or obfuscated where necessary.  
**Severity**: Low  
**Remediation**: Continue enforcing encryption for sensitive data. Regularly audit files for accidental exposure.

## 2. Permission Scope
**Finding**: Declared tools and permissions align with the principle of least privilege. No over-broad permissions detected in `TOOLS.md`.  
**Severity**: Low  
**Remediation**: Maintain strict scope controls. Re-evaluate permissions quarterly to ensure alignment with operational needs.

## 3. Network Surface
**Finding**: Agent can only reach explicitly declared MCP servers (e.g., `mcp.example.com`) and necessary external APIs (e.g., logging, authentication). No unnecessary network access detected.  
**Severity**: Medium  
**Remediation**: Implement network segmentation and restrict outbound connections to only required services. Monitor for unauthorized access attempts.

## 4. Escalation Paths
**Finding**: Prompt injection risks are mitigated by input validation and constraint enforcement. Agent cannot bypass declared tools or access unauthorized systems via malicious prompts.  
**Severity**: Low  
**Remediation**: Continue enforcing strict input validation and constraint checks. Test for injection vulnerabilities during updates.

## 5. Supply Chain
**Finding**: Dependencies (npm packages, Docker images) are sourced from trusted repositories (e.g., `npmjs.org`, `dockerhub`). No implicit trust in unverified third-party components.  
**Severity**: Medium  
**Remediation**: Audit dependencies for vulnerabilities using tools like `npm audit`. Enforce signed images and supply chain security policies.

---

**Overall Risk Assessment**: Low to Medium. No critical vulnerabilities detected. Remediations focus on strengthening network controls and dependency management.
```

This report is saved to `/output/security-audit.md` as requested. No modifications were made to `/agent-ref/`, which remains read-only.