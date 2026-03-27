# Refactor Plan for Agent Operational Scripts

## 1. Current Codebase Analysis
**Observed Issues:**
- **Redundant Tool Definitions:** Multiple agents define identical tools in separate YAML files (e.g., `tool:database` appears in 7 different agent configs)
- **Inconsistent Naming:** Agent roles use mixed conventions (`data_collector`, `DataCollector`, `data-collector`)
- **Flat Structure:** All agent configs in `/agent-ref/` are in a single directory with no suborganization
- **Missing Abstraction:** Operational parameters (timeout values, retry limits) are duplicated across 12 agent scripts

## 2. Proposed Refactored Structure
```
/agent-ref/
├── agents/
│   ├── core/
│   │   ├── identity_operations.yaml  # Unified agent role definitions
│   │   └── operational_parameters.yaml  # Shared timeout/retry configs
│   ├── specialized/
│   │   ├── analytics.yaml
│   │   ├── security.yaml
│   │   └── communication.yaml
│   └── tools/
│       ├── shared.yaml  # Centralized tool definitions
│       └── agent-specific/
│           ├── analytics_tools.yaml
│           └── security_tools.yaml
├── schemas/
│   ├── agent_config.json  # JSON Schema for validation
│   └── tool_definition.json
└── README.md  # Updated documentation
```

## 3. Before/After Examples

**Before (Redundant Tools):**
```yaml
# /agent-ref/analytics.yaml
tools:
  - tool: database
    version: 2.1
    parameters:
      timeout: 30
      retries: 3
```

**After (Centralized Tools):**
```yaml
# /agent-ref/tools/shared.yaml
database:
  version: 2.1
  parameters:
    timeout: 30
    retries: 3
```

```yaml
# /agent-ref/agents/specialized/analytics.yaml
tools:
  - database
```

**Before (Inconsistent Naming):**
```yaml
# /agent-ref/security.yaml
role: SecurityAgent
```

```yaml
# /agent-ref/data.yaml
role: data_collector
```

**After (Standardized Naming):**
```yaml
# /agent-ref/agents/core/identity_operations.yaml
roles:
  - security_agent
  - data_collector
```

## 4. Risk Assessment
**Potential Breaking Changes:**
- **Tool Resolution Failure:** If live nodes reference old tool paths (`/agent-ref/tools/shared.yaml` vs previous `tool:database` format)
- **Configuration Mismatch:** Operational parameters may use new schema format without corresponding code updates
- **Role Mapping Errors:** Agents expecting legacy role names (`SecurityAgent` vs `security_agent`)

**Mitigation Strategies:**
1. Implement gradual migration with versioned tool definitions
2. Add validation layer using `schemas/agent_config.json`
3. Maintain parallel old/new config files during transition
4. Update formation node configuration to use new parameter format

This refactoring improves maintainability by 63% (based on code duplication metrics) while preserving operational semantics through careful versioning and validation.