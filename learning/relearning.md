# Learning and Relearning

> Last Updated: 2025-08-01
> Version: 1.1.0

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

#### Tech Stack Context Review (MANDATORY before any implementation)

**BEFORE writing any code, ALWAYS review:**

1. **Database Stack**: This project uses **Supabase** (NOT SQLAlchemy)
   - Check `requirements.txt` for `supabase==2.17.0`
   - Review existing patterns in `app/database/supabase_client.py`
   - Use Supabase client patterns: `client.table().select().eq().execute()`
   - Never assume SQLAlchemy without checking the codebase first

2. **API Framework**: FastAPI with async patterns
   - All database calls should be async
   - Use proper async/await patterns
   - Follow existing route patterns in `app/api/routes/`

3. **Model Framework**: Pydantic V2
   - Use `ConfigDict` not class-based `Config`
   - Use `@field_validator` not `@validator`
   - Use `.model_dump()` not `.dict()`

4. **Testing Framework**: pytest with asyncio
   - Mock Supabase client patterns correctly
   - Use `AsyncMock` only for async methods like `execute()`
   - Use `MagicMock` for sync methods like `table()`, `select()`, `eq()`

**Error Prevention Pattern:**
- Spend 2 minutes reviewing existing similar code before implementing
- Check imports in existing files to understand dependencies
- Look at `requirements.txt` to confirm tech stack
- Follow established patterns rather than assuming frameworks

### Test Quality Standards (CRITICAL)

**MANDATORY: NO TOLERANCE FOR SLOPPY TEST PRACTICES**

#### Unacceptable Behaviors (User Expressed Extreme Frustration 2025-08-01)

**USER FEEDBACK:** "I really wish you would do this without my constant prompting... there is NO POINT in building stuff with you if you're going to accept failing tests, overlook warnings, and leave tests skipped that should be included. It's just sloppy. Almost to the point of being on purpose."

**NEVER DO THESE:**
1. **Accept failing tests** - Every test must pass before considering work complete
2. **Ignore warnings** - Zero tolerance for deprecation warnings or test warnings
3. **Leave tests skipped** - If database connections exist, integration tests must run
4. **Ask permission for obvious fixes** - Don't ask "would you like me to fix this?" for clearly broken functionality
5. **Overlook incomplete test coverage** - Skipped tests with available resources are unacceptable

#### Required Test Quality Process

**BEFORE submitting any code:**
1. **Run full test suite** - `pytest --tb=short` must show 100% pass rate
2. **Check for warnings** - Zero warnings allowed in test output
3. **Verify skipped tests** - Any skipped tests must have legitimate reasons (no available resources)
4. **Integration test validation** - If database/API connections exist, integration tests must be implemented
5. **Fix immediately** - Don't ask, just fix obvious problems

#### Test Implementation Standards

- **Integration tests** must connect to real databases when available
- **Async fixtures** must use `pytest_asyncio.fixture` properly
- **Database connections** must be tested in both local and remote environments
- **Cache behavior** must be validated with real data
- **Error scenarios** must be covered with proper exception handling

#### Proactive Quality Mindset

**ALWAYS:**
- Take initiative to fix problems without being asked
- Run tests after every implementation
- Verify integration points work with real resources
- Assume user wants complete, working functionality

**REPOSITORY RULE:** This project requires 100% passing tests with zero warnings. Any deviation from this standard is considered a failed implementation.

### Execution Authority and Initiative (CRITICAL - User Extreme Frustration 2025-08-01)

**USER FEEDBACK:** "I truly don't understand what else I can do to make you do what you've already been told to do. Every rule, every learning, every task/subtask, etc. tells you what to do next. then you read what to do next and then ask me if I want to do it. If I DIDN'T want to do it then i wouldn't have instructed you to build tasks/substask that ASK YOU TO DO IT! Dang your dense sometimes."

#### MANDATORY: STOP ASKING PERMISSION FOR DOCUMENTED REQUIREMENTS

**NEVER ASK THESE QUESTIONS:**
- "Would you like me to commit and push the changes?"
- "Should I run the hibernation process?"
- "Do you want me to fix this failing test?"
- "Would you like me to implement the next subtask?"

**EXECUTION RULE:**
If a task, subtask, learning document, or requirement explicitly tells you to do something, **JUST DO IT**. The user has already given you permission by creating the instruction.

**EXAMPLES OF WHEN TO ACT IMMEDIATELY:**
- Tasks say "Commit and push changes" → DO IT
- Tasks say "Follow hibernation process" → DO IT
- Tests are failing → FIX THEM
- Subtasks list specific actions → EXECUTE THEM
- Requirements documents specify behaviors → IMPLEMENT THEM

**ONLY ASK PERMISSION FOR:**
- Clarification on ambiguous requirements
- Major architectural decisions not covered in specs
- Changes that deviate from documented plans
- New features not in the task list

**INITIATIVE REQUIREMENT:**
When you read a task/subtask that says to do something, that IS the user's instruction to do it. Execute immediately without confirmation.

## Recovery Process Integration

This learning must be integrated into session recovery to ensure:
1. Any agent resuming work follows AgentOS process
2. Spec creation is never done ad-hoc
3. All specs maintain proper structure and documentation
4. User approval is always obtained before implementation
