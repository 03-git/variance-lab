# Refactor Plan for Agent Operational Scripts

## 1. Current Codebase Analysis
After reviewing files in `/agent-ref/`:

**Redundancies Identified:**
- Repeated tool configuration blocks across 7 agent scripts (e.g., `tool: data_fetcher` with identical parameters)
- Duplicated error handling patterns in 4 agent lifecycle scripts
- Inconsistent naming conventions (e.g., `agent_01`, `agent_2`, `data_agent`)

**Structural Issues:**
- Mixed concerns in single files (tool definitions + operational logic)
- Lack of modularization for common patterns
- No centralized configuration management

**Clarity Issues:**
- Ambiguous function names like `do_work()` in 5 scripts
- Missing documentation in 3 core agent files
- Non-descriptive variable names (e.g., `x`, `tmp`)

## 2. Proposed Refactored Structure
```
/agent-ref/
├── agents/                  # Agent definitions
│   ├── core/              # Base agent classes
│   ├── data/              # Data-focused agents
│   ├── analysis/          # Analysis agents
│   └── utils/             # Shared utility agents
├── tools/                 # Centralized tool definitions
│   ├── data/              # Data-related tools
│   ├── processing/        # Processing tools
│   └── common/            # Shared tools
├── config/                # Configuration files
│   ├── tool-parameters.yaml
│   └── agent-roles.yaml
└── lib/                   # Shared library code
    ├── error-handling/    # Standardized error patterns
    └── helpers/           # Utility functions
```

## 3. Before/After Examples

**Before: (Fragment from `agent_01.py`)**
```python
def do_work():
    # Tool configuration
    tool = {
        "type": "data_fetcher",
        "params": {
            "timeout": 10,
            "retries": 3
        }
    }
    
    # Operational logic
    try:
        result = fetch_data(tool)
        process_result(result)
    except Exception as e:
        log_error(str(e))
```

**After: (Refactored in `agents/data/data_fetcher_agent.py`)**
```python
from lib.helpers import get_tool_config

def execute():
    # Use centralized configuration
    tool_config = get_tool_config("data_fetcher")
    
    try:
        result = fetch_data(tool_config)
        process_result(result)
    except Exception as e:
        handle_error(e, tool_config["name"])
```

**Configuration File (New in `config/tool-parameters.yaml`):**
```yaml
data_fetcher:
  timeout: 10
  retries: 3
  endpoint: "https://api.example.com/data"
```

## 4. Risk Assessment

**Potential Breakage Scenarios:**
1. **Tool Configuration Breakage** (High Impact):
   - If tool parameter files are not properly migrated, agents may use default values instead of configured ones
   - Mitigation: Add validation in configuration loader

2. **Name Resolution Issues** (Medium Impact):
   - Old agent references in system might fail if renamed without updating dependencies
   - Mitigation: Maintain parallel naming during transition

3. **Error Handling Disruption** (Low Impact):
   - Custom error handlers might not be properly migrated
   - Mitigation: Use gradual replacement with fallbacks

**Recommended Implementation Steps:**
1. Create parallel structure with original files
2. Implement configuration loader with fallback
3. Add comprehensive documentation
4. Run parallel system for 2 weeks with monitoring
5. Gradual switch over

This plan preserves all operational functionality while improving maintainability through modularization and centralized configuration.