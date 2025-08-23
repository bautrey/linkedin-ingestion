## Agent OS Documentation

### Product Context
- **Mission & Vision:** @agent-os/product/mission.md
- **Technical Architecture:** @agent-os/product/tech-stack.md
- **Development Roadmap:** @agent-os/product/roadmap.md
- **Decision History:** @agent-os/product/decisions.md

### Development Standards
- **Code Style:** @~/agent-os/standards/code-style.md
- **Best Practices:** @~/agent-os/standards/best-practices.md

### Project Management
- **Active Specs:** @agent-os/specs/
- **Spec Planning:** Use `@~/agent-os/instructions/create-spec.md`
- **Tasks Execution:** Use `@~/agent-os/instructions/execute-tasks.md`

## Workflow Instructions

When asked to work on this codebase:

1. **First**, check @agent-os/product/roadmap.md for current priorities
2. **Then**, follow the appropriate instruction file:
   - For new features: @agent-os/instructions/create-spec.md
   - For tasks execution: @agent-os/instructions/execute-tasks.md
3. **Always**, adhere to the standards in the files listed above

## Important Notes

- Product-specific files in `agent-os/product/` override any global standards
- User's specific instructions override (or amend) instructions found in `agent-os/specs/...`
- Always adhere to established patterns, code style, and best practices documented above.

## 🚨 MANDATORY PROJECT RULES

### Test Execution Visibility
**NEVER HIDE TEST OUTPUT** - Project owner explicitly requires full test visibility

- ✅ **ALWAYS** run: `source venv/bin/activate && pytest` (shows full dots format)
- ❌ **NEVER** run: `pytest | tail-X` (hides test execution)
- ❌ **NEVER** use any pipe that truncates or hides pytest output

*This rule is also documented in `agent-os/product/tech-stack.md` Testing Framework section*

### Memory Keeper MCP Integration
**CRITICAL SESSION MANAGEMENT** - Memory Keeper MCP is essential for hibernation protocol

- ✅ **ALWAYS** use Memory Keeper during hibernation: `call_mcp_tool` with correct parameter formats
- 🔧 **Available Tools**: `create_entities`, `create_relations`, `add_observations`, `delete_entities`, `delete_observations`, `delete_relations`, `read_graph`, `search_nodes`, `open_nodes`
- 📝 **CORRECT USAGE PATTERNS (RESEARCHED 2025-01-20)**:
  - `create_entities`: Use `{"entities":[{"name":"Entity_Name","entityType":"type","observations":["obs1"]}]}`
  - `add_observations`: Use `{"observations":[{"entityName":"Entity Name","contents":["obs1"]}]}`
  - `search_nodes`: Use `{"query":"search terms"}`
- ⚠️ **CRITICAL**: See `MEMORY_KEEPER_MCP_GUIDE.md` for complete usage documentation
- 🎯 **Purpose**: Evaluate Memory Keeper as potential replacement for session files
- ⚠️ **Never Skip**: Memory Keeper integration is mandatory during hibernation - failure to use undermines process evaluation

*Memory Keeper MCP server visible in Warp terminal with green "Running" indicator*

### Session File Location Rule
**CRITICAL HIBERNATION RULE** - Project owner explicitly requires centralized session management

- ✅ **ALWAYS** create session files in main project sessions folder: `/Users/burke/projects/linkedin-ingestion/sessions/`
- ❌ **NEVER** create session files in subdirectories: `admin-ui/sessions/`, `app/sessions/`, etc.
- 🎯 **Reason**: Sessions represent work on ENTIRE project, not just current working directory
- 📁 **Correct Pattern**: `[PROJECT_ROOT]/sessions/[project-name]-session-YYYY-MM-DD-HHMMSS.md`
- ⚠️ **User Correction**: 2025-08-18 - Whether working on backend or frontend, it's one unified project session

*Hibernation process must identify main project root, not current working directory*

## Debugging & Troubleshooting

### Memory Server Usage
**Essential for debugging and knowledge retention across sessions**

- 🟢 **Status Check**: Memory server shows as "Running" with green indicator in Warp terminal
- 📚 **CRITICAL REFERENCE**: See `MEMORY_KEEPER_MCP_GUIDE.md` for complete usage documentation
- 🔧 **Available Tools with CORRECT Formats**: 
  - `create_entities`: `{"entities":[{"name":"Name","entityType":"type","observations":["obs"]}]}`
  - `add_observations`: `{"observations":[{"entityName":"Name","contents":["obs"]}]}`
  - `search_nodes`: `{"query":"search terms"}` 
  - `create_relations`: `{"relations":[{"from":"Entity1","to":"Entity2","relationType":"uses"}]}`
- 📋 **Usage Pattern**: Document key learnings, API patterns, debugging solutions
- 💡 **Best Practice**: Store troubleshooting patterns to avoid repeating same mistakes
- ⚡ **Quick Access**: Use search_nodes to find previously stored solutions
- 🚨 **CRITICAL ENTITIES STORED**: 
  - `LinkedIn Ingestion Service` - Project status and progress
  - `Supabase_CLI_Token_Waste_Prevention` - Database operation patterns

### Railway/GitHub Auto-Deployment Behavior
**CRITICAL UNDERSTANDING** - Railway only rebuilds when production code changes

- ✅ **Triggers rebuild**: Changes to `app/`, `main.py`, `requirements.txt`, `Dockerfile`, etc.
- ❌ **Does NOT trigger rebuild**: Changes to `docs/`, `tests/`, `sessions/`, `*.md` files, `__pycache__/`, etc.
- 🔍 **Version comparison**: If local commit ahead of deployed commit, check if commits contain actual production code changes
- 🚨 **Don't assume failure**: Railway deployment isn't "broken" just because commit hashes differ
- 📋 **Example**: 5 commits of only test updates = Railway still runs same version until code changes

### Common Issues & Solutions
**Recently resolved patterns (stored in memory server)**

- **UI showing "No data found"**: Check API connectivity, verify production endpoints, debug with temporary logging
- **Profile names missing**: Enrich data with additional API calls rather than assuming nested response structure
- **Environment variables**: Fix typos in .env files (e.g., `FASAPI_BASE_URL` → `FASTAPI_BASE_URL`)
- **API testing**: Always test against production Railway deployment, not localhost assumptions
- **Deployment version mismatch**: Check if recent commits actually changed production code vs just docs/tests
