# Refactor Plan for Agent Operational Scripts

## 1. Current Issues Identified

### Redundancy
- Repeated initialization code in `agent_*.sh` scripts (e.g., environment setup, logging functions)
- Duplicated error handling patterns across 7 agent scripts
- Multiple tool configuration files with overlapping parameters

### Naming Issues
- Ambiguous function names like `do_work()` without context
- Inconsistent naming conventions (snake_case vs camelCase)
- Generic file names like `script_3.sh` with no functional indication

### Structural Issues
- Flat file structure with no logical grouping
- Missing separation between configuration, logic, and tools
- No clear hierarchy for agent-specific vs shared code

## 2. Proposed File Structure

```
/agent-ref
├── config/                # Centralized configuration
│   ├── env_vars.sh        # Shared environment variables
│   └── tool_configs/      # Tool-specific configurations
├── lib/                   # Shared functions
│   ├── logging.sh         # Standardized logging functions
│   └── utils.sh           # Common utility functions
├── agents/                # Agent-specific logic
│   ├── core/              # Base agent functionality
│   │   └── init.sh        # Standard initialization
│   ├── specialized/     # Role-specific agents
│   │   ├── data_agent.sh
│   │   └── control_agent.sh
│   └── tools/           # Agent-specific tool integrations
├── tools/                 # Tool definitions
│   ├── tool_a.sh
│   └── tool_b.sh
└── README.md              # Updated documentation
```

## 3. Before/After Examples

### Before: Redundant Initialization
```bash
# agent_1.sh
setup_env() {
  export LOG_LEVEL="INFO"
  export API_KEY="xyz123"
  # ... 20+ lines of similar setup
}
```

### After: Centralized Configuration
```bash
# config/env_vars.sh
export LOG_LEVEL="INFO"
export API_KEY="xyz123"

# lib/utils.sh
setup_env() {
  source config/env_vars.sh
}
```

### Before: Ambiguous Function
```bash
# agent_2.sh
process_data() {
  # 150 lines of data processing logic
}
```

### After: Structured Organization
```bash
# agents/specialized/data_agent.sh
source lib/utils.sh
source config/env_vars.sh

process_data() {
  # 150 lines of data processing logic with clear context
}
```

## 4. Risk Assessment

**High Risk Scenarios:**
- Breaking existing tool integrations if configuration parameters are moved without updating tool scripts
- Breaking agent initialization if environment variables are restructured
- Potential runtime failures if function signatures change without proper versioning

**Mitigation Strategies:**
- Implement gradual migration with conditional fallbacks
- Add versioning to configuration files
- Create detailed migration guide in README.md
- Maintain parallel old/new structures during transition

**Critical Dependency Warning:** 
The current formation node relies on specific file paths and variable names. Any refactoring must ensure backward compatibility through:
1. Symbolic links for legacy scripts
2. Environment variable compatibility layer
3. Gradual phase-out of old scripts

This plan balances modernization with operational stability, reducing technical debt while maintaining production readiness.