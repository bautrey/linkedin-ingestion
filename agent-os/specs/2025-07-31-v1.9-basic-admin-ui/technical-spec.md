# V1.9 Basic Admin UI - Technical Specification

e **Feature**: Basic Admin UI Interface Development
e **Version**: 1.9.0
e **Created**: 2025-07-31
e **Status**: 🚧 DRAFT - Technical Spec In Progress

## Overview

The technical specification for the V1.9 Basic Admin UI feature outlines the necessary architectural components, integrations, data models, and interfaces required to implement a functioning administrative interface for LinkedIn Ingestion Service management, leveraging the shadcn/ui framework.

### Key Architecture Decisions
- **Framework**: Next.js 14 utilized for its performance efficiency and comprehensive feature set, including the App Router and server-client hybrid model.
- **UI Components**: Utilization of shadcn/ui for leveraging Radix UI components combined with Tailwind CSS for a cohesive design approach.
- **State Management**: Use of React Query for server-side state synchronization and Zustand for client-side state management.

## System Architecture

### Frontend Architecture
- **Next.js App Router**: Facilitates page-based routing for enhanced navigability and includes configurations for serverless functions.
- **UI Component Strategy**: A modular component design allowing reusable widgets.
- **Styling**: Tailwind CSS integration with shadcn/ui theme to maintain styling consistency.
- **State Management**:
  - *Server-side*: React Query for data-fetching and caching logic.
  - *Client-side*: Zustand, offering a lightweight store for ephemeral UI state manipulation.

### Backend Integration
- **API Communication**:
  - Utilizing Axios for manageable and simplified HTTP request logic, including error handling and authentication processing.
- **Data Handling**:
  - JSON data interchange format using Pydantic models to define response schemas.
  - API endpoints designed within FastAPI, ensuring compatibility with anticipated frontend requirements.

### Data Models
- **Profile Model**:
  - Fields: `id`, `name`, `position`, `company`, `experience`, etc.
  - Relationships: Direct association fields for company mapping.
- **Company Model**:
  - Fields: `id`, `name`, `industry`, `location`, `size`, etc.
  - Association: Method to relate employee profiles.

## Interfaces 6 Components

### Navigation Components
- **Primary Navigation**: Sidebar for primary connections (Dashboard, Profiles, Companies).
- **Sign-On/Registration**: Utilizes OAuth integration offered by FastAPI backend.

### Profile Management
- **Search Area**:
  - Debounced search inputs with filtering criteria.
  - Integration to provide search result highlights.

### Detail View Components
- **Profile View**:
  - Displays all known data fields and relationships.
  - Action buttons to edit, re-ingest, or delete existence.

### Company Management
- **Company Overview**:
  - Detailed view enabling insights into companies and linked profiles.
  - Sorting by various metrics like age, size, etc.

## API Endpoint Specification

- **Profile API**:
  - `GET /api/v1/profiles`: Retrieves the list of profiles with optional query params for sorting and filtering.
  - `POST /api/v1/profiles/{id}`: Edits profile data.
  - `DELETE /api/v1/profiles/{id}`: Removes specified profile.

- **Company API**:
  - `GET /api/v1/companies`: Returns all companies for selection criteria.
  - `GET /api/v1/companies/{id}/profiles`: Returns all profiles associated with a particular company.

## Security Considerations
- **Authentication**: API key-based with Secure Headers implementation to safeguard data flow.
- **Data Privacy**: GDPR compliance through data minimization and access control.
- **Rate Limiting**: Logical throttle for preventing abuse and DDoS attacks.

## Testing Approach
- **Unit Testing**: Vast unification to cover UI components and utility functions.
- **Integration Testing**: Ensuring that communication with the backend performs as expected.
- **End-to-End Testing**: Playwright tests across major user journeys to validate real-world usage.

### Key Test Cases
- Successful API Authentication.
- Profile CRUD operations including edge cases.
- Company data validity across all sorts and filters.

## Deployment Strategy
- **Development and Production**: Standard Railway deployment using robust containerization strategies.
- **Environment Configuration**: Utilize `.env` files for variable consistency and security adherence.

## Maintenance and Documentation
- **Versioning**: Utilize semver for feature delivery and manage version track with change logs.
- **Continuous Integration**: Automated build verification using GitHub workflows.

## Conclusion

This technical spec addresses critical areas for implementing a responsive and user-friendly Admin UI within the LinkedIn Ingestion Service's infrastructure. Attention to architectural detail and comprehensive planning ensures the delivery of a robust and maintainable UI component set, aligned with product and business objectives. Feedback loops and iterative development will secure feature integrity and quality through the lifecycle.

