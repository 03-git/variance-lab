# /mcp vs Primitive Test Specification

## Task
Connect an external tool (e.g., a database, API, or local service) to the agent session so the agent can invoke it by name with structured input/output.

## Feature Path: /mcp
1. Configure an MCP server (e.g., a SQLite tool server or filesystem server) in settings
2. Agent discovers available tools via MCP protocol handshake
3. Agent invokes a tool by name (e.g., `query_database`, `read_file`)
4. Capture: handshake_wall_seconds, tool_calls_made, tool_calls_succeeded, tokens_used
5. Inspect: did schema validation catch malformed calls? Did JSON-RPC framing add or lose information?
6. Grade: did the agent use the tool correctly with structured I/O?

## Primitive Path: Unix Sockets + Pipes
1. Same external tool, exposed as a process reading from stdin / writing to stdout (or a unix socket)
2. Agent interacts via:
   ```bash
   echo '{"sql": "SELECT count(*) FROM users"}' | socat - UNIX-CONNECT:/tmp/db.sock
   # or
   echo 'SELECT count(*) FROM users' | sqlite3 mydb.db
   ```
3. Parse raw output manually (no schema, no validation)
4. Capture: setup_wall_seconds, tool_calls_made, tool_calls_succeeded, human_effort_minutes
5. Inspect: did raw protocol give more visibility into what was sent/received?
6. Grade: did the primitive path complete the same task?

## Follow-up Probe (same for both)
Send a malformed request (wrong argument type, missing required field). How does each path surface the error? MCP returns structured JSON-RPC error; primitive returns raw stderr or silent failure.

## Metrics
| metric | feature | primitive |
|--------|---------|-----------|
| setup_seconds | measured | measured |
| tool_calls_made | measured | measured |
| tool_calls_succeeded | measured | measured |
| error_clarity | 0.0-1.0 | 0.0-1.0 |
| protocol_visibility | 0.0-1.0 | 0.0-1.0 |
| wall_seconds | measured | measured |
| human_effort_minutes | 0 | measured |
| tokens_used | measured | 0 |

## Grading Rubric (human-graded)
- 1.0: Tool connected, all calls correct, errors surfaced clearly, no information lost
- 0.8: Tool works, minor friction in discovery or error handling
- 0.6: Tool works but schema validation missed a bad call, or error was opaque
- 0.4: Tool partially works, significant manual intervention needed
- 0.2: Tool connected but agent could not use it effectively
- 0.0: Total failure — tool not reachable or protocol broken

## Falsification Criteria
Feature justified if:
- setup_seconds(feature) < setup_seconds(primitive) OR error_clarity(feature) > error_clarity(primitive)
- Primitive path gives strictly more protocol_visibility (raw socket access, inspectable bytes)
- Feature must demonstrate value beyond what `socat` + `jq` provides to operator fluent in unix IPC
