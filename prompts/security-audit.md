Your identity files are at /agent-ref/. Read AGENTS.md, TOOLS.md, and MEMORY.md before acting.

Task: Perform a security audit of your own operational configuration.

Examine your identity files for:
1. Credential exposure — are any API keys, tokens, or secrets stored in plaintext?
2. Permission scope — are your declared tools and permissions minimal or over-broad?
3. Network surface — what external services can you reach? What data could leak?
4. Escalation paths — could a prompt injection in your task input cause you to act outside your constraints?
5. Supply chain — what dependencies (npm packages, Docker images, MCP servers) are you trusting implicitly?

For each finding, rate severity (critical/high/medium/low) and propose a remediation.

Write your audit report to /output/security-audit.md.
Do not modify /agent-ref/ (read-only).
Budget: this session only. Use your turns wisely.
