# Spec Tasks

These are the tasks to be completed for the spec detailed in @agent-os/specs/2025-07-30-v1.6-canonical-profile-models/spec.md

> Created: 2025-07-30
> Status: Ready for Implementation

## Tasks

- [x] 1. **Create Canonical Models**
  - [x] 1.1 Create `app/models/canonical.py` with `CanonicalProfile` and `CanonicalCompany` models
  - [x] 1.2 Implement all fields with Pydantic V2 types and validation
  - [x] 1.3 Add nested models for education, experience, etc.
  - [x] 1.4 Ensure all models are Pydantic V2 compliant with no deprecation warnings

- [x] 2. **Update Codebase**
  - [x] 2.1 Replace all `datetime.utcnow()` calls with `datetime.now(timezone.utc)`
  - [x] 2.2 Replace all `.dict()` calls with `.model_dump()`
  - [x] 2.3 Run full test suite and fix any failures
  - [x] 2.4 Verify no Pydantic V1 or other deprecation warnings in test suite

- [x] 3. **Finalize Spec**
  - [x] 3.1 Create `spec.md`, `technical-spec.md`, and `tests.md`
  - [x] 3.2 Create `tasks.md` to document completed work
  - [x] 3.3 Update `spec.md` with cross-references

