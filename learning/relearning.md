# Learning and Relearning

> Last Updated: 2025-07-30
> Version: 1.0.0

## Critical Process Requirements

### AgentOS Spec Creation Process

**ALWAYS use the AgentOS spec creation process for ALL specs and test plans.**

- **Source of Truth**: @/Users/burke/projects/burke-agent-os-standards/instructions/create-spec.md
- **Never** create specs manually without following the AgentOS process
- **Always** follow the 16-step process including:
  1. Location validation (CRITICAL - ensure in project directory, not standards directory)
  2. Spec initiation (with user approval)
  3. Context gathering (read product docs)
  4. Requirements clarification
  5. Date determination (use file system timestamp)
  6. Spec folder creation (YYYY-MM-DD-spec-name format)
  7. Create spec.md (with all required sections)
  8. Create technical-spec.md in sub-specs/
  9. Create database-schema.md (if needed)
  10. Create api-spec.md (if needed)
  11. Create tests.md in sub-specs/
  12. User review and approval
  13. Create tasks.md with TDD approach
  14. Update cross-references
  15. Decision documentation (if strategic impact)
  16. Execution readiness check

### Required Spec Structure

```
agent-os/specs/YYYY-MM-DD-spec-name/
├── spec.md (main spec with all required sections)
├── tasks.md (task breakdown)
└── sub-specs/
    ├── technical-spec.md (always required)
    ├── tests.md (always required)
    ├── database-schema.md (conditional)
    └── api-spec.md (conditional)
```

### Key Requirements

- **Location Validation**: NEVER create specs in burke-agent-os-standards or agent-os directories
- **User Approval**: Always get user approval before proceeding to task creation
- **Complete Structure**: Always create all required files and sub-specs
- **Cross-References**: Always add spec documentation references to spec.md
- **Date Accuracy**: Use file system timestamp for accurate folder naming

## Project-Specific Learnings

### LinkedIn Ingestion Service

- All Pydantic models must be V2 compliant
- Use `datetime.now(timezone.utc)` instead of `datetime.utcnow()`
- Use `.model_dump()` instead of `.dict()`
- Zero deprecation warnings policy enforced
- Test suite must pass without warnings

## Recovery Process Integration

This learning must be integrated into session recovery to ensure:
1. Any agent resuming work follows AgentOS process
2. Spec creation is never done ad-hoc
3. All specs maintain proper structure and documentation
4. User approval is always obtained before implementation
