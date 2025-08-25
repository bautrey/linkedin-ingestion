# Product Backlog

> **Last Updated:** 2025-08-24  
> **Priority Scale:** P0 (Critical) → P1 (High) → P2 (Medium) → P3 (Low)  
> **Size Scale:** XS (1-2 hours) → S (1 day) → M (2-3 days) → L (1 week) → XL (2+ weeks)

## 🔥 High Priority Items

### P1-001: Enforce Single Active Template Per Role
**Priority:** P1 (High) | **Size:** S (1 day) | **Status:** Ready  

**User Story:**
As an admin managing scoring templates, I want the system to prevent multiple active templates for the same role so that scoring results are predictable and consistent.

**Description:**
Currently, users can accidentally create multiple "active" templates for the same role (e.g., CTO), causing the system to pick the "most recent" one unpredictably. This leads to:
- Inconsistent scoring results depending on which template gets selected
- Workflow failures when old "junk" templates lack required JSON structure
- Brittle system behavior that's hard to debug

**Acceptance Criteria:**
- [ ] API validation prevents saving/activating a template when another active template exists for the same role
- [ ] Clear error message: "Cannot create/activate template. An active template already exists for role {ROLE}."
- [ ] Error response includes details about the existing conflicting template
- [ ] User must explicitly delete or deactivate the existing template before proceeding
- [ ] UI displays appropriate error handling for this conflict scenario

**Technical Notes:**
- Implement validation in template save/update API endpoints
- Return HTTP 409 (Conflict) with structured error response
- No automatic deactivation - force user to make intentional decision
- Separate UI logic to handle the error gracefully

**Definition of Done:**
- [ ] API endpoint validation implemented and tested
- [ ] Error response format documented
- [ ] Manual testing confirms enforcement works
- [ ] UI properly handles and displays the error

---

### P1-002: Enhance Template Management UI with Proper Type Separation
**Priority:** P1 (High) | **Size:** M (2-3 days) | **Status:** Ready  

**User Story:**
As an admin managing templates, I want clear separation between compatibility check templates and scoring templates in the UI, and I want to manage all template content through the database rather than config files, so that I can efficiently configure the system without technical deployment requirements.

**Description:**
Currently, the admin UI template section doesn't clearly distinguish between two different template types:
1. **Role Compatibility Templates** - Used for Stage 3 role compatibility checks (single template, no versioning needed)
2. **Scoring Templates** - Used for detailed profile scoring (multiple templates per role, version management needed)

Additionally, the role compatibility template is currently stored in config files rather than the database, making it impossible to modify through the admin UI in production environments.

**Current Issues:**
- No visual distinction between compatibility vs scoring templates in UI
- Role compatibility template stored in `settings.ROLE_COMPATIBILITY_SYSTEM_MESSAGE` and `settings.ROLE_COMPATIBILITY_USER_MESSAGE` (config files)
- Admins cannot modify compatibility templates without code deployment
- UI doesn't reflect the different management patterns (single vs multiple active templates)

**Acceptance Criteria:**
- [ ] UI clearly separates "Role Compatibility Template" and "Scoring Templates" sections
- [ ] Role compatibility template moved from config to database storage
- [ ] Single role compatibility template with simple save/edit interface (no versioning)
- [ ] Scoring templates section supports multiple templates per role with active/inactive states
- [ ] Role compatibility template editable through admin UI without deployment
- [ ] Clear labeling: "Role Compatibility (Stage 3)" vs "Detailed Scoring (Stage 4)"
- [ ] Migration script to move existing config-based compatibility template to database
- [ ] Backward compatibility during transition period

**Technical Notes:**
- Create new template type enum: `ROLE_COMPATIBILITY` vs `SCORING`
- Role compatibility templates don't need role-specific categories (applies to all roles)
- Database schema may need template_type field to distinguish types
- UI should show different management interfaces for each template type
- Consider single "Role Compatibility Template" page vs "Scoring Templates" page

**Definition of Done:**
- [ ] Database schema updated to support template types
- [ ] Role compatibility template migrated from config to database
- [ ] UI redesigned with clear template type separation
- [ ] Admin can edit role compatibility template through UI
- [ ] Scoring templates section maintains existing functionality
- [ ] Migration tested with existing production data
- [ ] Config-based template gracefully deprecated

---

## 🔧 Technical Debt

### P2-001: Centralize OpenAI Client Management
**Priority:** P2 (Medium) | **Size:** M (2-3 days) | **Status:** Identified  

**User Story:**
As a developer, I want centralized OpenAI client initialization and error handling so that AI service failures are handled consistently across all features.

**Description:**
Currently, OpenAI client validation and error handling is duplicated across multiple services:
- `LLMScoringService` - for detailed profile scoring
- `AIRoleCompatibilityService` - for role compatibility checks
- Each service has its own client initialization and error handling patterns
- Validation logic is duplicated (checking for API key, client initialization, etc.)

**Proposed Solution:**
Create a `BaseAIService` or `OpenAIClientService` class that:
- Handles centralized client initialization
- Provides standardized error handling and logging
- Validates API key and client setup consistently
- Can be inherited/injected into other AI services

**Acceptance Criteria:**
- [ ] Single source of truth for OpenAI client management
- [ ] Consistent error handling across all AI services  
- [ ] Standardized logging for AI service failures
- [ ] Existing services refactored to use centralized approach
- [ ] No regression in current functionality

---

### P2-002: Separate JSON Schema from Prompt Templates
**Priority:** P2 (Medium) | **Size:** L (1 week) | **Status:** Identified  

**User Story:**
As a template administrator, I want JSON response schemas separated from prompt content so that I can modify prompts without breaking downstream workflow parsing.

**Description:**
Currently, the exact JSON structure for AI responses is embedded within the prompt text itself. This creates brittleness:
- Any prompt modification can break JSON parsing
- Downstream Make.com workflows depend on exact field structure
- No validation that prompts include required JSON schema
- Schema changes require coordinated prompt updates

**Proposed Solution:**
- Separate `response_schema` field in template model
- Template validation ensures schema is present and valid
- AI response validation against expected schema
- Prompt can reference schema but doesn't need to embed full structure

**Acceptance Criteria:**
- [ ] Template model includes separate `response_schema` field
- [ ] Template validation checks for valid JSON schema
- [ ] AI responses validated against expected schema before processing
- [ ] Migration plan for existing templates
- [ ] Backward compatibility during transition

---

## 📋 Future Enhancements

### P3-001: Template Versioning System
**Priority:** P3 (Low) | **Size:** XL (2+ weeks) | **Status:** Idea  

**User Story:**
As a template administrator, I want proper versioning of templates so that I can safely experiment with changes and roll back if needed.

**Description:**
Implement proper template versioning with:
- Version history tracking
- Ability to promote/demote versions
- A/B testing capabilities
- Safe rollback mechanisms

**Acceptance Criteria:**
- [ ] Template version tracking
- [ ] Version comparison interface
- [ ] Safe rollback functionality
- [ ] A/B testing framework

---

### P3-002: Enhanced Template Analytics
**Priority:** P3 (Low) | **Size:** M (2-3 days) | **Status:** Idea  

**User Story:**
As a system administrator, I want analytics on template performance so that I can optimize scoring accuracy and cost.

**Description:**
Track template usage metrics:
- Success/failure rates by template
- Average response times
- Token usage and costs
- Score distribution analysis

**Acceptance Criteria:**
- [ ] Template performance metrics
- [ ] Usage analytics dashboard
- [ ] Cost tracking per template
- [ ] Performance optimization recommendations

---

## 🗃️ Completed Items

*Items moved here when completed for historical reference*

---

## 📝 Notes

**How to Add Items:**
1. Use the next available ID in the appropriate priority section
2. Include User Story, Description, Acceptance Criteria
3. Estimate Priority (P0-P3) and Size (XS-XL)
4. Set Status (Idea → Ready → In Progress → Done)

**Priority Guidelines:**
- **P0 (Critical):** Production issues, security vulnerabilities
- **P1 (High):** User-blocking issues, core functionality problems  
- **P2 (Medium):** Technical debt, performance improvements
- **P3 (Low):** Nice-to-have features, optimizations

**Status Values:**
- **Idea:** Initial concept, needs refinement
- **Ready:** Fully defined, ready for development
- **In Progress:** Currently being worked on
- **Done:** Completed, moved to completed section
