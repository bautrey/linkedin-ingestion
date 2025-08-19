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

- ✅ **ALWAYS** use Memory Keeper during hibernation: `call_mcp_tool` with correct tool names
- 🔧 **Available Tools**: `create_entities`, `create_relations`, `add_observations`, `delete_entities`, `delete_observations`, `delete_relations`, `read_graph`, `search_nodes`, `open_nodes`
- 📝 **Correct Usage**: Use `entityName` parameter (not `entity_name`), create entities before adding observations
- 🎯 **Purpose**: Evaluate Memory Keeper as potential replacement for session files
- ⚠️ **Never Skip**: Memory Keeper integration is mandatory during hibernation - failure to use undermines process evaluation

*Memory Keeper MCP server visible in Warp terminal with `mcp-server-memory` command*

### Session File Location Rule
**CRITICAL HIBERNATION RULE** - Project owner explicitly requires centralized session management

- ✅ **ALWAYS** create session files in main project sessions folder: `/Users/burke/projects/linkedin-ingestion/sessions/`
- ❌ **NEVER** create session files in subdirectories: `admin-ui/sessions/`, `app/sessions/`, etc.
- 🎯 **Reason**: Sessions represent work on ENTIRE project, not just current working directory
- 📁 **Correct Pattern**: `[PROJECT_ROOT]/sessions/[project-name]-session-YYYY-MM-DD-HHMMSS.md`
- ⚠️ **User Correction**: 2025-08-18 - Whether working on backend or frontend, it's one unified project session

*Hibernation process must identify main project root, not current working directory*
