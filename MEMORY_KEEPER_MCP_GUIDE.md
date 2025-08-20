# Memory Keeper MCP - Complete Usage Guide

> **CRITICAL**: This documentation is stored locally because if Memory Keeper MCP isn't working, you can't retrieve usage information from Memory Keeper itself.

## Overview
Memory Keeper MCP is a Model Context Protocol server that provides persistent knowledge graph storage for maintaining context across development sessions. It's visible in Warp Terminal as a running service with green status indicator.

## Available Tools

Based on project documentation and CLAUDE.md references, Memory Keeper MCP provides these tools:

### Core Entity Management
- `create_entities` - Create new entities in the knowledge graph
- `create_relations` - Create relationships between entities  
- `add_observations` - Add new observations to existing entities
- `delete_entities` - Remove entities from the knowledge graph
- `delete_observations` - Remove specific observations
- `delete_relations` - Remove relationships between entities

### Query and Retrieval
- `search_nodes` - Search for entities by query terms
- `read_graph` - Read the entire knowledge graph structure
- `open_nodes` - Access detailed information about specific entities

## Tool Usage Patterns

### 1. Creating Entities

**CORRECT Syntax (Researched and Tested):**
```javascript
call_mcp_tool("create_entities", {
  "entities": [{
    "entityType": "critical_learning",
    "name": "Entity_Name_With_Underscores",
    "observations": [
      "First observation about this entity",
      "Second observation with more details",
      "Additional context and information"
    ]
  }]
})
```

**Key Parameter Rules:**
- Use `entities` array (REQUIRED)
- Each entity needs `entityType`, `name`, `observations`
- Use `name` (not `entityName`) inside entities array
- Use `observations` array for entity creation
- Entity names should use underscores for spaces

**Entity Types Examples:**
- `project` - Project-wide information
- `issue` - Problems and bugs encountered
- `solution` - Fixes and resolutions
- `learning` - Important lessons learned
- `critical_learning` - High-priority lessons to remember
- `debugging_pattern` - Systematic approaches to common problems
- `api_pattern` - API usage and integration patterns
- `project_status` - Current state and progress tracking

### 2. Adding Observations to Existing Entities

**CORRECT Syntax (Researched and Tested):**
```javascript
call_mcp_tool("add_observations", {
  "observations": [{
    "entityName": "LinkedIn Ingestion Service",
    "contents": [
      "V1.9 Database Migration completed successfully", 
      "Enhanced schema with 13 new columns deployed",
      "All 28 repository tests passing"
    ]
  }]
})
```

**Key Parameter Rules:**
- Use `observations` array containing objects (REQUIRED)
- Each object needs `entityName` and `contents`
- Use `contents` (not `observations`) for the actual observation data
- Entity name must match exactly (case-sensitive)

### 3. Creating Relationships

```javascript
call_mcp_tool("create_relations", {
  "relations": [{
    "from": "LinkedIn_Ingestion_Service",
    "to": "Supabase_Database_Schema",
    "relationType": "uses"
  }, {
    "from": "CompanyRepository", 
    "to": "CanonicalCompany_Model",
    "relationType": "manages"
  }]
})
```

### 4. Searching for Information

```javascript
// Search for specific topics
call_mcp_tool("search_nodes", {
  "query": "supabase migration"
})

// Search for entities by type
call_mcp_tool("search_nodes", {
  "query": "debugging API connection"
})

// Search for solutions to problems
call_mcp_tool("search_nodes", {
  "query": "token waste prevention"
})
```

### 5. Reading Graph Structure

```javascript
// Get overview of all entities and relationships
call_mcp_tool("read_graph", {})

// Open specific entities for detailed information
call_mcp_tool("open_nodes", {
  "nodeIds": ["LinkedIn_Ingestion_Service", "Supabase_CLI_Patterns"]
})
```

## Best Practices

### 1. Entity Naming Conventions
- Use descriptive, unique names: `Supabase_CLI_Critical_Patterns`
- Include project context: `LinkedIn_Ingestion_Database_Migration`
- Use underscores for multi-word names: `Token_Waste_Prevention_Rules`

### 2. Observation Structure
- Start with summary/context
- Include specific details and examples
- Add implementation steps or commands
- Note impact and lessons learned

### 3. Relationship Types
- `uses` - Component dependencies
- `implements` - Feature relationships  
- `solves` - Solution to problem relationships
- `causes` - Problem causation
- `enhances` - Improvement relationships

### 4. Session Management Integration

**At Session Start:**
```javascript
// Query for project context
call_mcp_tool("search_nodes", {
  "query": "LinkedIn Ingestion current status"
})
```

**During Development:**
```javascript
// Store critical findings immediately
call_mcp_tool("create_entities", {
  "entityName": "Database_Migration_Issue_2025_01_20",
  "entityType": "issue",
  "observations": [
    "Problem: Migration failed due to policy conflicts",
    "Root cause: Duplicate policies on template_version_history",
    "Solution: Created focused migration with only companies table",
    "Command used: supabase db push -p 'dvm2rjq6ngk@GZN-wth'"
  ]
})
```

**At Session End:**
```javascript
// Update project status
call_mcp_tool("add_observations", {
  "entityName": "LinkedIn_Ingestion_Service", 
  "observations": [
    "Session 2025-01-20: Database migration completed successfully",
    "CompanyRepository with 28 tests implemented and passing",
    "Enhanced schema deployed to production Supabase",
    "Ready for next development phase"
  ]
})
```

## Troubleshooting Memory Keeper MCP

### Common Error: "MCP server tool not found"
This indicates the Memory Keeper MCP server is not running or not properly connected.

**Check Server Status:**
1. Look for Memory Keeper MCP server in Warp Terminal
2. Should show green "Running" indicator
3. May be listed as `mcp-server-memory` in terminal

**Server Not Running:**
- Memory Keeper MCP may need to be restarted
- Check Warp MCP configuration
- Verify server installation and setup

### Common Error: "Cannot read properties of undefined (reading 'filter')"
This indicates incorrect parameter structure - specifically missing required array wrappers.

**Root Cause (RESEARCHED):**
The Memory Keeper MCP expects specific parameter structures that differ from documentation examples.

**CORRECT vs INCORRECT Formats:**
```javascript
// ✅ CORRECT - create_entities
call_mcp_tool("create_entities", {
  "entities": [{
    "entityType": "learning",
    "name": "My_Entity", 
    "observations": ["First observation"]
  }]
})

// ❌ INCORRECT - missing entities array wrapper
call_mcp_tool("create_entities", {
  "entityName": "My_Entity",
  "entityType": "learning",
  "observations": ["First observation"]
})

// ✅ CORRECT - add_observations
call_mcp_tool("add_observations", {
  "observations": [{
    "entityName": "My_Entity",
    "contents": ["New observation"]
  }]
})

// ❌ INCORRECT - wrong parameter names
call_mcp_tool("add_observations", {
  "entityName": "My_Entity",
  "observations": ["New observation"]
})
```

### Common Error: "Entity with name undefined not found"
This indicates the entity name is not being passed correctly or doesn't exist.

**Solutions:**
1. Use exact entity name from search_nodes results
2. Ensure proper parameter structure with required arrays
3. Create entity first if it doesn't exist

## Integration with Project Workflow

### 1. Hibernation Protocol
- Store session accomplishments in Memory Keeper
- Document current state and next steps
- Create relationships between completed and pending work

### 2. Recovery Protocol  
- Query Memory Keeper for project context before starting work
- Search for related issues and solutions
- Update entities with new progress and findings

### 3. Learning Retention
- Store critical mistakes and prevention measures
- Document successful patterns and approaches
- Create searchable knowledge base for future sessions

## linkedin-ingestion Project Entities

### Essential Entities to Maintain
1. **LinkedIn_Ingestion_Service** - Main project status and progress
2. **Supabase_CLI_Critical_Patterns** - Database operation procedures
3. **Token_Waste_Prevention_Rules** - Efficiency guidelines
4. **CompanyRepository_Implementation** - Repository layer details
5. **Database_Migration_Patterns** - Schema change procedures

### Critical Relationships
- LinkedIn_Ingestion_Service → uses → Supabase_Database
- CompanyRepository → implements → CanonicalCompany_Model
- Token_Waste_Prevention → prevents → CLI_Inefficiencies
- Database_Migration → requires → Service_Role_Password

This documentation ensures Memory Keeper MCP usage information is available even when the MCP server itself is not accessible.
