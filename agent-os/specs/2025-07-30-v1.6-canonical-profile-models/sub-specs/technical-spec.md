# Technical Specification

This is the technical specification for the spec detailed in @agent-os/specs/2025-07-30-v1.6-canonical-profile-models/spec.md

> Created: 2025-07-30
> Version: 1.0.0

## Technical Requirements

- **Pydantic V2 Compliance**: All models must use Pydantic V2 syntax with `@field_validator` decorators
- **Type Safety**: Use appropriate Python types with Pydantic validation for all fields
- **URL Validation**: LinkedIn URLs must use Pydantic's `AnyUrl` type for automatic validation
- **Date Handling**: Use Python `datetime` objects for all date fields
- **Optional Fields**: Clearly distinguish required vs optional fields with proper defaults
- **Import Statements**: Use `from pydantic import BaseModel, field_validator, AnyUrl` imports

## Approach Options

**Option A:** Create models in existing `app/cassidy/models.py` file
- Pros: Keeps all models in one location
- Cons: Mixes external API models with canonical models

**Option B:** Create new `app/models/canonical.py` file (Selected)
- Pros: Clean separation between external and internal models
- Cons: Adds new module to project structure

**Rationale:** Option B provides better separation of concerns and prepares for the adapter pattern in v1.7.

## Data Model Design

### CanonicalProfile Fields

- `id`: Optional[str] - Internal system ID
- `full_name`: str - Required full name
- `linkedin_url`: AnyUrl - Validated LinkedIn URL
- `headline`: Optional[str] - Professional headline
- `summary`: Optional[str] - Profile summary
- `location`: Optional[str] - Current location
- `work_history`: List[CanonicalCompany] - Employment history
- `created_at`: datetime - Record creation timestamp
- `updated_at`: datetime - Last update timestamp

### CanonicalCompany Fields

- `id`: Optional[str] - Internal system ID
- `name`: str - Required company name
- `linkedin_url`: Optional[AnyUrl] - Company LinkedIn URL
- `description`: Optional[str] - Company description
- `industry`: Optional[str] - Industry classification
- `size`: Optional[str] - Company size range
- `location`: Optional[str] - Company headquarters location
- `website`: Optional[str] - Company website
- `job_title`: Optional[str] - User's role at this company
- `start_date`: Optional[datetime] - Employment start date
- `end_date`: Optional[datetime] - Employment end date
- `created_at`: datetime - Record creation timestamp
- `updated_at`: datetime - Last update timestamp

## External Dependencies

No new external dependencies are required. The implementation uses existing Pydantic V2 installation.

## Validation Rules

- All URLs must be valid HTTP/HTTPS URLs
- Dates must be valid datetime objects
- Required fields cannot be None or empty strings
- List fields default to empty lists if not provided
- Timestamps are automatically set on model creation/updates
