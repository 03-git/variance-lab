# Refactor Plan for Agent Operational Scripts

## 1. Identified Issues in Current Codebase

### Redundancy
- Repeated initialization code across `agent-ops-*.sh` scripts (e.g., `setup_env()` and `validate_config()` functions)
- Duplicated error handling patterns in `task-executor.py` and `monitor-agent.sh`

### Naming Issues
- Ambiguous variable names like `tmp_data` and `cfg` without context
- Inconsistent function naming (e.g., `start_task()` vs `initiate_process()`)

### Structural Issues
- Monolithic `identity-agent.js` file with 1,200+ lines of mixed configuration and logic
- No clear separation between agent identity definitions and operational logic

## 2. Proposed Refactored Structure

```
/agent-ref/
├── core/                  # Shared operational logic
│   ├── utils.sh           # Common shell functions
│   ├── error-handling.py  # Standardized error patterns
│   └── config-parser.js   # Identity configuration loader
├── agents/                # Agent-specific implementations
│   ├── agent-1/
│   │   ├── ops.sh         # Agent-specific operational scripts
│   │   └── identity.json  # Cleaned-up identity definitions
│   └── agent-2/
│       ├── ops.sh
│       └── identity.json
├── tools/                 # Tool-specific implementations
│   ├── communication/   # Standardized messaging patterns
│   └── validation/      # Shared validation logic
└── config/                # Centralized configuration files
    └── environment-vars.json
```

## 3. Before/After Examples

### Before: Redundant Initialization (agent-ops-1.sh)
```bash
# agent-ops-1.sh (original)
setup_env() {
    export AGENT_HOME="/agent-ref/agent-1"
    export LOG_LEVEL="INFO"
    # ... 40+ lines of similar setup code ...
}
```

### After: Modularized Initialization
```bash
# core/utils.sh (new)
setup_env() {
    local agent_id=$1
    export AGENT_HOME="/agent-ref/${agent_id}"
    export LOG_LEVEL="INFO"
    # Standardized setup logic
}
```

### Before: Ambiguous Variables (task-executor.py)
```python
# task-executor.py (original)
def execute_task(tmp_data):
    cfg = load_config()
    # ... 200+ lines with unclear variable usage ...
```

### After: Explicit Naming
```python
# tools/validation/task-validator.py (new)
def execute_task(agent_data, config):
    validate_inputs(agent_data, config)
    # ... clear variable names with contextual meaning ...
```

## 4. Risk Assessment

### High Risk Areas
- **File Path Dependencies**: Existing scripts may reference old file paths (e.g., `/agent-ref/agent-1/ops.sh` vs new structure)
- **Configuration Loading**: Centralized config parsing may break if existing agents use non-standard configuration formats
- **Tool Dependencies**: Refactored tool modules may require updates to `require()`/`import` statements in JavaScript/Python files

### Mitigation Strategies
1. Implement gradual migration with symlink aliases during transition
2. Add validation checks in `config-parser.js` for backward compatibility
3. Create versioned tool interfaces to maintain compatibility with existing agents

This refactoring preserves all operational functionality while improving maintainability through modularization, standardized interfaces, and clearer naming conventions.