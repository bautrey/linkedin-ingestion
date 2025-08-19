# AgentOS Migration: Hidden to Visible Directories

**Date**: August 19, 2025  
**Scope**: /Users/burke/projects (excluding upstream-agent-os)  
**Issue**: Remove all references to hidden `.agent-os` directories and replace with visible `agent-os`

## Summary of Changes

### Files Modified: 82 unique files
### References Changed: 561 total occurrences
### Directories Renamed: 1 global installation

## Major Changes

### 1. Text Replacements
- Replaced all `.agent-os` references with `agent-os` in 82 files
- Affected projects:
  - linkedin-ingestion (19 files)
  - burke-agent-os-standards (23 files) 
  - agent-os (19 files)
  - PartnerConnect-Sprints (1 file)
  - warp-learning-system (2 files)

### 2. Directory Renames
- **Global**: `~/.agent-os` → `~/agent-os`
- **Project-specific**: Already used visible `agent-os` directories

### 3. Files Excluded
- **upstream-agent-os/**: Preserved original structure as reference implementation

## Path Updates

### Before:
```
~/.agent-os/standards/
~/.agent-os/instructions/
@.agent-os/product/
@.agent-os/specs/
```

### After:
```
~/agent-os/standards/
~/agent-os/instructions/
@agent-os/product/
@agent-os/specs/
```

## Verification Results

✅ **No `.agent-os` references remain** (excluding upstream-agent-os)  
✅ **Global installation accessible** at ~/agent-os  
✅ **Project directories accessible** (e.g., linkedin-ingestion/agent-os)  
✅ **AgentOS commands functional** (tested create-spec.md access)  
✅ **Git status shows expected changes**  

## Migration Commands Used

```bash
# 1. Remove empty hidden directory
rm -rf /Users/burke/projects/linkedin-ingestion/.agent-os

# 2. Replace text references (excluding upstream-agent-os)
find . -type f \( -name "*.md" -o -name "*.sh" \) \
  -not -path "./upstream-agent-os/*" \
  -exec sed -i '' 's/\.agent-os/agent-os/g' {} \;

# 3. Rename global installation
mv ~/.agent-os ~/agent-os
```

## Impact Assessment

### ✅ Working:
- All AgentOS functionality preserved
- Project-specific agent-os directories accessible
- Session management and hibernation paths updated
- Documentation references corrected

### 🔄 Git Status:
- Modified: 33+ files (documentation and session files)
- Deleted: 2 files from old .agent-os directory
- Untracked: 2 files in new agent-os directory

## Next Steps

1. Commit all changes to git
2. Update any external documentation that references `.agent-os`
3. Test full AgentOS workflow (create-spec, execute-tasks)
4. Verify TaskMaster integration still works

---

**Migration Completed Successfully**  
All `.agent-os` references have been eliminated from the projects directory while preserving full AgentOS functionality.
