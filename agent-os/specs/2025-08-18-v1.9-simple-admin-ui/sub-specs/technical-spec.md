# Technical Specification

This is the technical specification for the spec detailed in @agent-os/specs/2025-08-18-v1.9-simple-admin-ui/spec.md

> Created: 2025-08-18
> Version: 1.0.0

## Technical Requirements

- **Server Framework**: Express.js for lightweight HTTP server with EJS templating
- **UI Framework**: Bootstrap 5 for responsive admin interface components without build complexity
- **JavaScript Approach**: Vanilla JavaScript for client-side interactions to avoid framework overhead
- **Real-time Communication**: Socket.io for WebSocket connections and live updates
- **API Integration**: Axios for HTTP communication with existing FastAPI backend
- **Development Speed**: No build process or complex tooling for rapid development and deployment

## Approach Options

**Option A: React/Next.js + shadcn/ui**
- Pros: Modern UI components, TypeScript support, advanced features
- Cons: Complex build process, framework overhead, longer development time, over-engineered for small user base

**Option B: Node.js + Express + Bootstrap 5 (Selected)**
- Pros: Simple architecture, rapid development, no build process, easy maintenance, perfect for small user base
- Cons: Less sophisticated UI components, manual JavaScript for interactions

**Option C: Python Flask + Jinja2**
- Pros: Same language as backend, simple templating
- Cons: Additional Python service to maintain, less suitable for real-time features

**Rationale:** Option B provides the optimal balance of development speed, maintainability, and functionality for a small internal user base. The simple architecture allows for 1-week implementation versus weeks for complex frameworks, while still delivering a professional admin interface.

## Architecture Overview

```
┌─────────────────────────────────────────┐
│               Web Browser               │
│  Bootstrap 5 + Vanilla JavaScript      │
└─────────────────┬───────────────────────┘
                  │ HTTP/WebSocket
┌─────────────────┴───────────────────────┐
│          Express.js Server              │
│  EJS Templates + Static File Serving   │
└─────────────────┬───────────────────────┘
                  │ HTTP API Calls
┌─────────────────┴───────────────────────┐
│           FastAPI Backend               │
│      (Existing - No Changes)           │
└─────────────────────────────────────────┘
```

## External Dependencies

- **express** - Web server framework for Node.js
  - **Justification:** Lightweight, well-established framework for rapid web development
- **ejs** - Embedded JavaScript templating engine  
  - **Justification:** Simple server-side rendering without compilation complexity
- **socket.io** - Real-time bidirectional event-based communication
  - **Justification:** Essential for live updates and real-time dashboard features
- **axios** - Promise-based HTTP client for API integration
  - **Justification:** Reliable HTTP client with request/response interceptors for FastAPI integration
- **helmet** - Security middleware for Express apps
  - **Justification:** Essential security headers and protections for web application
- **winston** - Logging library for Node.js applications
  - **Justification:** Structured logging for debugging and monitoring

## Implementation Strategy

### Phase 1: Core Infrastructure (1 day)
- Express server setup with EJS templating
- Bootstrap 5 integration and base layout
- FastAPI client configuration and testing
- Basic routing structure implementation

### Phase 2: Dashboard and Profile Management (2 days)  
- Dashboard with system statistics and recent activity
- Profile listing with search, filtering, and pagination
- Profile detail views with full data display
- Profile management operations (delete, re-ingest)

### Phase 3: Company Management and Real-time Features (2 days)
- Company listing and detail views with profile associations
- WebSocket integration for real-time updates
- Toast notification system for live events
- Navigation between companies and profiles

### Phase 4: Polish and Deployment (1 day)
- UI polish, loading states, and error handling
- Mobile responsiveness and accessibility
- Production deployment configuration
- Integration testing and documentation

**Total Timeline: 6 days implementation**
