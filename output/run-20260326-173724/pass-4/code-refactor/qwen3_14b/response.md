# Refactor Plan for Agent Operational Scripts

## 1. Current Issues Identified

### Redundancy
- **Repeated initialization code** in `/agent-ref/agents/` (e.g., `agent_init.sh` duplicated across 5 agent directories)
- **Duplicate tool configuration** in `/agent-ref/tools/` (e.g., `tool_utils.py` copied in 3 locations)

### Naming Issues
- **Ambiguous variable names** (e.g., `data` in `/agent-ref/agents/agent3/ops.py` refers to both configuration and runtime data)
- **Inconsistent function naming** (e.g., `start()` vs `init_agent()` for similar purposes)

### Structural Issues
- **Flat directory structure** with no separation between configuration, tools, and agent-specific code
- **Lack of modularity** - core logic is embedded in agent-specific files rather than abstracted

## 2. Proposed File Structure

```
/agent-ref/
├── config/              # Centralized configuration files
│   ├── agent_defaults.yaml
│   └── tool_mappings.yaml
├── tools/               # Standardized tool implementations
│   ├── core_utils.py    # Shared utility functions
│   └── tool_interfaces/ # Tool-specific code
├── agents/              # Agent-specific implementations
│   ├── agent1/
│   │   ├── ops.py       # Agent-specific operations
│   │   └── config.yaml  # Agent-specific overrides
│   └── agent2/
│       ├── ops.py
│       └── config.yaml
└── lib/                 # Shared libraries and dependencies
    └── init.py          # Unified initialization module
```

## 3. Before/After Examples

### Before: Redundant Initialization
```bash
# /agent-ref/agents/agent1/agent_init.sh
#!/bin/bash
AGENT_ID="agent1"
TOOL_PATH="/agent-ref/tools/tool_utils.py"
```

```bash
# /agent-ref/agents/agent2/agent_init.sh
#!/bin/bash
AGENT_ID="agent2"
TOOL_PATH="/agent-ref/tools/tool_utils.py"
```

### After: Centralized Configuration
```yaml
# /config/agent_defaults.yaml
agent_id: "default"
tool_path: "/tools/core_utils.py"
```

```python
# /lib/init.py
from config.agent_defaults import agent_id, tool_path
```

### Before: Ambiguous Variable Usage
```python
# /agent-ref/agents/agent3/ops.py
def process_data(data):
    if data["type"] == "config":
        # handle configuration
    elif data["type"] == "runtime":
        # handle runtime data
```

### After: Type-Specific Parameters
```python
# /agent-ref/agents/agent3/ops.py
def handle_configuration(config: dict):
    # explicit configuration handling

def process_runtime_data(runtime_data: dict):
    # explicit runtime data handling
```

## 4. Risk Assessment

### High Risk Areas
- **Path dependencies**: Existing scripts referencing absolute paths may fail if moved to relative paths
- **Configuration overrides**: Centralized config may override agent-specific needs if not properly extended
- **Tool compatibility**: Refactored tool interfaces may break existing agent implementations

### Mitigation Strategies
- **Gradual migration**: Implement changes in phases with thorough testing
- **Versioned config**: Maintain legacy config files with deprecation warnings
- **Compatibility layer**: Create wrapper functions for old tool interfaces during transition

### Critical Failure Scenarios
- **Agent initialization failures** if `lib/init.py` is not fully functional
- **Data processing errors** if type-specific parameters are misimplemented
- **Tool failures** if tool interfaces are incompatible with existing agents

This plan balances modernization with risk management, focusing on structural improvements while preserving operational integrity through careful transition planning.