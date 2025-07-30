# Technical Specification

This is the technical specification for the spec detailed in @agent-os/specs/2025-07-30-v1.7-cassidy-canonical-adapter/spec.md

> Created: 2025-07-30
> Version: 1.0.0

## Technical Requirements

- The adapter must be a pure Python module with no external dependencies other than Pydantic.
- The adapter must expose a single function, `transform`, that accepts a Cassidy API response as a dictionary and returns a `CanonicalProfile` instance.
- The transformation logic must handle nested structures in the Cassidy response and map them to the corresponding nested Pydantic models in our canonical representation.
- A custom exception, `IncompleteDataError`, should be raised if essential fields required for core functionality are missing from the Cassidy response.

## Approach Options

**Option A:** Direct Mapping in a Single Function

- Create a single, large function that handles the entire transformation logic. This approach is simple to implement but may become difficult to maintain as the mapping logic grows more complex.

**Option B:** Class-Based Adapter with Helper Methods (Selected)

- Create a `CassidyAdapter` class with a public `transform` method and private helper methods for transforming specific sections of the response (e.g., `_transform_experience`, `_transform_education`). This approach is more modular, easier to test, and more extensible for future modifications.

**Rationale:** The class-based approach (Option B) provides better organization and testability, which is crucial for a core component like this adapter. It also aligns better with object-oriented principles and will be easier to extend if we support more data sources in the future.

## External Dependencies

- **None**: This adapter will only use built-in Python types and the existing Pydantic models from `app/models/canonical.py`.

