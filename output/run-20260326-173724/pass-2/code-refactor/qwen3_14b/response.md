# Refactor Plan for Agent Operational Scripts

## 1. Current Issues Identified

### Redundancy
- **Tool Definitions Duplicated**: Multiple agent scripts contain identical tool configuration blocks (e.g., `tool: "data-validator"` with same parameters in 5+ files)
- **Agent Initialization Repeats**: `initialize_agent()` function signatures are duplicated across `agent-ops/*.py`

### Naming Issues
- **Ambiguous File Names**: Files named `agent-3.py`, `agent-4.py` without clear role indication
- **Inconsistent Variables**: Variables like `tmp_data` vs `temp_data` across different scripts

### Structural Problems
- **Mixed Concerns**: Single files handle both agent logic and tool configuration
- **Lack of Central Configuration**: No centralized place for shared parameters or tool definitions

## 2. Proposed Refactored Structure

```
/agent-ref/
├── configs/
│   ├── agent-roles.yaml      # Centralized agent role definitions
│   ├── tool-definitions.yaml # Shared tool configurations
│   └── parameters.yaml       # Global parameters for all agents
├── tools/
│   ├── data-validator.py     # Tool implementation files
│   └── encryption.py
├── agents/
│   ├── analytics-agent.py    # Agent-specific logic files
│   ├── compliance-agent.py
│   └── __init__.py           # Central import hub
└── utils/
    └── helpers.py            # Shared utility functions
```

## 3. Before/After Examples

### Before (Redundant Tool Configuration)
```python
# agent-ops/agent-3.py
def initialize_agent():
    return {
        'tools': [
            {'type': 'data-validator', 'params': {'threshold': 0.8}},
            {'type': 'encryption', 'params': {'key': 'secret'}}
        ]
    }
```

### After (Centralized Configuration)
```python
# agents/analytics-agent.py
from configs.tool-definitions import TOOL_DEFINITIONS

def initialize_agent():
    return {
        'tools': TOOL_DEFINITIONS['analytics']
    }
```

```yaml
# configs/tool-definitions.yaml
analytics:
  - type: data-validator
    params: {threshold: 0.8}
  - type: encryption
    params: {key: "secret"}
```

## 4. Risk Assessment

**High Risk Areas:**
- **Path Dependency**: Existing code may reference old file locations (e.g., `from agent-ops import *`)
- **Tool Versioning**: Centralized tool definitions may break agents expecting specific tool versions
- **Initialization Order**: Reliance on global parameters.yaml may fail if file loading order changes

**Mitigation Strategies:**
1. Implement gradual migration with versioned config files
2. Add validation checks for config file integrity
3. Create compatibility layer for old file paths during transition

**Critical Warning**: Live formation nodes must not be updated without:
- Full testing in staging environment
- Backup of current configuration
- Gradual rollout over 48 hours with rollback plan

This plan preserves all operational functionality while improving maintainability through separation of concerns and centralized configuration management.