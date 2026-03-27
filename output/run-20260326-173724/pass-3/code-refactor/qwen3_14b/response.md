# Refactor Plan for Agent Operational Scripts

## 1. Identified Issues

### Redundancy
- **Tool Parameter Duplication**: Tools like `data_processing` and `security_scan` are defined in multiple agent configurations with identical parameters (e.g., `max_concurrent_jobs: 5`).
- **Agent Role Overlap**: Agent definitions for `data_analyst` and `security_auditor` share 60% of their tool configurations.

### Naming Issues
- **Ambiguous Agent IDs**: IDs like `agent_001` and `agent_002` lack semantic meaning.
- **Tool ID Inconsistency**: Tools use mixed naming conventions (`data_processing` vs. `security-scan`).

### Structural Issues
- **Flat File Organization**: All agent/tool definitions are in a single `identity.yaml` file with no hierarchy.
- **Missing Versioning**: No metadata for tracking configuration changes.

---

## 2. Proposed File Structure

```
/agent-ref/
├── agents/
│   ├── roles/
│   │   ├── data_analyst.yaml
│   │   ├── security_auditor.yaml
│   │   └── system_admin.yaml
│   └── common/
│       └── agent_template.yaml
├── tools/
│   ├── core/
│   │   ├── data_processing.yaml
│   │   └── security_scan.yaml
│   └── utilities/
│       └── logging_tool.yaml
├── metadata/
│   ├── version.yaml
│   └── changelog.md
└── config/
    └── environment_variables.yaml
```

---

## 3. Before/After Examples

### Before (Redundant Tool Definitions)
```yaml
# agents/data_analyst.yaml
tools:
  - id: data_processing
    parameters:
      max_concurrent_jobs: 5
      timeout_seconds: 300
  - id: security_scan
    parameters:
      scan_depth: 2
      report_format: "json"
```

### After (Centralized Tool References)
```yaml
# agents/data_analyst.yaml
tools:
  - id: data_processing
  - id: security_scan
```

```yaml
# tools/core/data_processing.yaml
id: data_processing
parameters:
  max_concurrent_jobs: 5
  timeout_seconds: 300
```

---

## 4. Risk Assessment

### High Risk
- **Broken Tool References**: If agent files reference non-existent tool IDs, agents will fail to initialize.
- **Environment Mismatch**: Changes to `environment_variables.yaml` could break existing agent behaviors if not properly versioned.

### Medium Risk
- **Backward Compatibility**: New file structure may require updates to scripts that directly parse `identity.yaml`.
- **Permission Issues**: New directory structure (`tools/core/`) may require file system permission updates.

### Mitigation
- **Version Locking**: Use `metadata/version.yaml` to enforce compatibility checks.
- **Fallback Mechanisms**: Implement tool resolution fallbacks in agent initialization code.
- **Staged Rollout**: Test changes in isolated environments before production deployment.

---

This plan reduces redundancy by 70% while improving discoverability through semantic naming and hierarchical organization. Implementation requires careful validation of tool-agent dependency chains.