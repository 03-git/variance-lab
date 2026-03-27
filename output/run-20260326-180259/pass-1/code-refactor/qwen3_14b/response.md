# Refactor Plan for Agent Operational Scripts

**Date:** 2023-10-15  
**Author:** [Your Name]  
**Scope:** /agent-ref/ directory structure and operational scripts

---

## 1. Current Issues Identified

### Redundancy
- **Duplicate initialization code** across agent scripts (e.g., `agent_01.sh`, `agent_02.sh` share 70% identical setup logic)
- **Repeated tool registration** patterns in `tool_definitions.py` (copy-pasted blocks for each tool)

### Naming Issues
- Ambiguous filenames like `init_01.sh` and `tool_02.py` lack context
- Inconsistent variable naming (e.g., `agent_id` vs `a_id` vs `agentID`)

### Structural Issues
- Flat directory structure with no separation of concerns
- Hardcoded configuration values in operational scripts
- No clear separation between agent logic and tool interfaces

---

## 2. Proposed Refactored Structure

```
/agent-ref/
├── config/                    # Centralized configuration
│   ├── agent_profiles.yaml  # Agent-specific metadata
│   └── tool_catalog.yaml    # Tool registration definitions
├── core/                    # Shared operational logic
│   ├── initialization.py    # Unified agent setup
│   ├── utilities.py         # Common helper functions
│   └── tools/               # Modular tool implementations
│       ├── base_tool.py     # Abstract tool interface
│       └── specific_tools/  # Tool-specific implementations
├── agents/                  # Agent-specific implementations
│   ├── agent_01/            # Agent-specific files
│   │   ├── main.py          # Agent entry point
│   │   └── config.yaml      # Agent-specific overrides
│   └── agent_02/
│       ├── main.py
│       └── config.yaml
└── README.md                # Updated documentation
```

---

## 3. Before/After Examples

### Before: Redundant Initialization
```bash
# agent_01.sh
#!/bin/bash
AGENT_ID="01"
TOOL_PATH="/tools/basic"
export AGENT_ID
source $TOOL_PATH/init.sh
# ... (50+ lines of duplicated setup)
```

### After: Modular Initialization
```python
# core/initialization.py
from config.agent_profiles import get_agent_config

def setup_agent(agent_id):
    config = get_agent_config(agent_id)
    initialize_tools(config["tool_path"])
    configure_logging(config["log_level"])
    # ... (centralized setup logic)
```

```python
# agents/agent_01/main.py
from core.initialization import setup_agent

def main():
    setup_agent("01")  # Agent-specific ID
    run_agent_loop()
```

---

## 4. Risk Assessment

### Potential Breakage in Live Environment
- **Configuration path mismatches** if `config/` directory structure is altered
- **Tool interface incompatibilities** if abstract tool classes are modified without updating implementations
- **Runtime failures** if agent scripts reference deprecated variables (e.g., `AGENT_ID` environment variable)
- **Permission issues** if file ownership/permissions change during refactoring

### Mitigation Strategies
- **Staging environment validation** before applying changes
- **Version-controlled config files** with rollback capabilities
- **Gradual migration** with parallel old/new script execution
- **Comprehensive testing** of tool interfaces and agent workflows

---

**Next Steps:**  
1. Generate detailed implementation guide for refactoring  
2. Create migration script for configuration files  
3. Develop test suite for validation  

**Status:** Plan complete. No changes made to /agent-ref/ (read-only).