# AgentOS Session Management Overhaul - Implementation Plan

## ✅ **Phase 1: COMPLETED** - Current Project Reorganization

**Status**: ✅ **COMPLETE**  
**Date**: 2025-07-25

### Completed Tasks:
- [x] Created project-local `sessions/` directory with all archived sessions
- [x] Renamed all files to include project name prefix (`linkedin-ingestion-`)
- [x] Consolidated 7 historical sessions from multiple scattered locations
- [x] Created navigation hub `linkedin-ingestion-SESSION_HISTORY.md` 
- [x] Updated current session file with project identification
- [x] Removed deprecated global session storage directories
- [x] Committed all changes to git

### Files Reorganized:
```
linkedin-ingestion-SESSION_SUMMARY.md     # Current session (was: SESSION_SUMMARY.md)
linkedin-ingestion-SESSION_HISTORY.md     # Navigation hub (was: SESSION_HISTORY.md)
sessions/                                  # All archived sessions
├── linkedin-ingestion-session-2025-07-23-143000.md  (was: SESSION_SUMMARY_FINAL.md)
├── linkedin-ingestion-session-2025-07-24-003016.md  (was: ~/.agent-os/session-history/...)
├── linkedin-ingestion-session-2025-07-24-085332.md  (was: SESSION_SUMMARY_backup_...)
├── linkedin-ingestion-session-2025-07-24-090744.md  (was: .agent-os/sessions/...)
├── linkedin-ingestion-session-2025-07-24-134700.md  (was: SESSION_SUMMARY_2025-07-24T13-47.md)
├── linkedin-ingestion-session-2025-07-25-113132.md  (was: ~/.agent-os/session-history/...)
└── linkedin-ingestion-session-2025-07-25-165400.md  (current session archived)
```

---

## 🔄 **Phase 2: PARTIALLY COMPLETE** - Update Global AgentOS Standards

**Status**: 🟡 **IN PROGRESS**  
**Priority**: HIGH

### ✅ Completed:
- [x] Updated `~/.agent-os/instructions/session-hibernation.md` with project-specific naming
- [x] Added critical rule: NEVER create generic SESSION_SUMMARY.md files
- [x] Modified template to require project identification

### 🔄 Still Needed:
- [ ] Update `~/.agent-os/instructions/session-recovery.md` for new structure
- [ ] Update Burke's standards repository (`/Users/burke/projects/burke-agent-os-standards`)
- [ ] Sync changes to global standards using `sync-standards.sh push`
- [ ] Update Warp commands to use project-specific naming
- [ ] Test instructions work correctly with new structure

### Priority Files to Update:
```bash
# Global AgentOS Instructions
~/.agent-os/instructions/session-recovery.md
~/.agent-os/commands/session-hibernation.md
~/.agent-os/commands/session-recovery.md

# Burke's Standards Repository  
/Users/burke/projects/burke-agent-os-standards/instructions/session-hibernation.md
/Users/burke/projects/burke-agent-os-standards/sync-standards.sh

# Warp Integration
~/.agent-os/warp-commands.md
```

---

## 📋 **Phase 3: PLANNED** - Future Project Standardization

**Status**: ⏳ **PLANNED**  
**Priority**: MEDIUM

### Goal: Apply new session management to all existing projects

### Discovery Phase:
```bash
# Find all projects with session files
find /Users/burke/projects -name "SESSION_*" -type f

# Identify projects needing conversion
ls /Users/burke/projects/*/SESSION_SUMMARY.md
```

### Standardization Tasks:
- [ ] Create project assessment checklist
- [ ] Develop automated conversion script
- [ ] Apply to high-priority projects first
- [ ] Update each project's `.agent-os/product/` configuration
- [ ] Ensure all projects follow new naming convention

### Project Priority Order:
1. **Active Development Projects** (currently worked on)
2. **Recent Projects** (last 30 days activity)  
3. **Archived Projects** (older/stable projects)

---

## ⚠️ **Critical Rules Established**

### 🚫 **NEVER DO:**
- Create generic `SESSION_SUMMARY.md` files without project names
- Store session files in global `~/.agent-os/session-history/`
- Overwrite sessions without archiving to `./sessions/`
- Use scattered backup files in project root

### ✅ **ALWAYS DO:**
- Include project name in ALL session filenames (`[project]-SESSION_SUMMARY.md`)
- Archive sessions to project-local `./sessions/` directory
- Update navigation hub `[project]-SESSION_HISTORY.md` with timeline  
- Include **Project**: field in session content headers

---

## 🎯 **Next Session Priorities**

### Immediate (Next Session):
1. **Complete Phase 2**: Update remaining global AgentOS instructions
2. **Test New System**: Verify hibernation/recovery works correctly  
3. **Update Standards Repo**: Push changes to burke-agent-os-standards
4. **Document Process**: Create complete documentation for future use

### Medium Term:
1. **Project Discovery**: Identify all projects needing conversion
2. **Conversion Script**: Automate the session file reorganization process
3. **Rollout Plan**: Systematic approach to update existing projects

### Long Term:
1. **Standards Enforcement**: Ensure new projects automatically follow rules
2. **Monitoring**: Verify no generic session files are created
3. **Training**: Update any documentation/guides for new approach

---

## 🔍 **Testing Checklist**

Before declaring Phase 2 complete, verify:
- [ ] Session hibernation creates properly named files
- [ ] Session recovery finds and reads correct files
- [ ] Navigation hub updates correctly
- [ ] No generic SESSION_SUMMARY.md files created anywhere
- [ ] Warp commands work with new structure
- [ ] Burke's standards repo synchronized

---

## 📊 **Success Metrics**

**Phase 1**: ✅ 100% - LinkedIn Ingestion project reorganized
**Phase 2**: 🟡 60% - Global instructions partially updated
**Phase 3**: ⏳ 0% - Future project standardization not started

**Overall Progress**: 53% Complete

---

*This document tracks the comprehensive overhaul of AgentOS session management to eliminate generic filenames and ensure project-specific organization across all development work.*
