# Refactor Plan for Agent Operational Scripts

## 1. Issues Identified

### Redundancy
- **Tool Definitions Duplicated**: `tool_config.yaml` files in `/agent-ref/agentA/` and `/agent-ref/agentB/` contain identical tool declarations (e.g., `docker`, `kubectl`).
- **Script Duplication**: `init.sh` and `cleanup.sh` scripts share 70% identical code across agent directories.

### Naming Issues
- **Ambiguous Filenames**: Files like `script1.sh` and `config2.yaml` lack context.
- **Inconsistent Structure**: Agent-specific files are scattered across `/agent-ref/` without clear hierarchy.

### Structural Issues
- **No Central Configuration**: Each agent has isolated tool and environment definitions.
- **Hardcoded Paths**: Scripts reference absolute paths (e.g., `/agent-ref/agentA/tools/`).

---

## 2. Proposed Refactored Structure

```
/agent-ref/
├── agents/                  # Agent-specific operational files
│   ├── agentA/
│   │   ├── ops.yaml        # Agent-specific overrides
│   │   └── scripts/        # Agent-specific scripts
│   └── agentB/
│       ├── ops.yaml
│       └── scripts/
├── tools/                  # Centralized tool definitions
│   ├── common.yaml         # Shared tool configurations
│   └── agent-specific/     # Tool overrides
├── lib/                    # Shared library functions
│   ├── utils.sh            # Common script functions
│   └── env.sh              # Environment setup
├── config/                 # Global configurations
│   ├── tools.yaml          # Central tool registry
│   └── env.yaml            # Global environment variables
```

---

## 3. Before/After Examples

### Example 1: Tool Configuration Duplication

**Before** (Redundant):
```yaml
# /agent-ref/agentA/tool_config.yaml
tools:
  docker:
    version: "20.10"
    commands: ["build", "push"]
```

**After** (Centralized):
```yaml
# /agent-ref/tools/common.yaml
tools:
  docker:
    version: "20.10"
    commands: ["build", "push"]
```

### Example 2: Script Duplication

**Before** (Redundant):
```bash
# /agent-ref/agentA/init.sh
#!/bin/bash
export PATH=/usr/local/bin:$PATH
mkdir -p /tmp/agentA
```

**After** (Modular):
```bash
# /agent-ref/lib/utils.sh
#!/bin/bash
export PATH=/usr/local/bin:$PATH
mkdir -p /tmp/$(basename $(pwd))
```

---

## 4. Risk Assessment

### High Risk
- **Path Breakage**: If live nodes reference old file paths (e.g., `/agent-ref/agentA/tools/`), they will fail to locate tools.
- **Tool Version Mismatches**: Centralized tool configs may enforce incompatible versions across agents.

### Medium Risk
- **Script Behavior Changes**: Modularized scripts may behave differently if environment variables or context change.
- **Configuration Overrides**: Agent-specific `ops.yaml` files may not properly override global configs.

### Mitigation
- **Zero-Downtime Migration**: Use symbolic links during transition (e.g., `ln -s /agent-ref/tools/common.yaml /agent-ref/agentA/tool_config.yaml`).
- **Validation Checks**: Pre-deployment tests to verify tool versions and script outputs.

---

## 5. Next Steps
- Implement symbolic links for backward compatibility.
- Validate refactored scripts in staging environments.
- Deprecate old files after confirming stability.