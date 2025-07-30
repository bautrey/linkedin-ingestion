# v1.6 Canonical Profile Models

**Goal**: Create clean, Pydantic V2-compliant internal data models for LinkedIn profiles and companies to serve as a stable, internal data contract, decoupling the application from any specific external data provider's format.

**Justification**: The current models are tightly coupled to the Cassidy API's response structure, including its quirks and inconsistencies. This creates a brittle foundation where any change in the external API requires widespread changes in our application. By creating a canonical internal model and an adapter layer, we can build all future features on a stable, predictable data structure that we control.

This spec will cover:
- Creating `CanonicalProfile` and `CanonicalCompany` Pydantic V2 models
- Defining a clean, consistent, and well-documented data schema
- Ensuring all fields use proper data types with strict validation
- Removing all Pydantic V1 deprecation warnings
- Preparing the foundation for the Cassidy-to-Canonical adapter in v1.7

