# Task Breakdown

> Spec: Simple Admin UI with Node.js + Express + Bootstrap 5
> Created: 2025-08-18
> Status: Planning

## Phase 1: Project Foundation (1-2 hours)

### Task 1.1: Project Setup
- Initialize Node.js project in `admin-ui/` directory
- Install core dependencies: Express, EJS, Bootstrap 5, Socket.io, Axios
- Configure basic Express server with static file serving
- Set up EJS templating engine
- Create basic project structure with routes, views, and public directories

### Task 1.2: Backend API Integration
- Configure Axios client for FastAPI backend communication
- Set up environment variables for API endpoints and configuration
- Create API service layer for backend interactions
- Implement error handling and response formatting
- Test basic connectivity to existing FastAPI endpoints

## Phase 2: Profile Management Interface (3-4 hours)

### Task 2.1: Profile Table Implementation
- Create comprehensive profile listing table with Bootstrap 5 styling
- Implement sortable columns (name, title, company, location, ingestion date, score)
- Add filtering capabilities with search inputs and dropdown filters
- Implement adjustable column widths with local storage persistence
- Add pagination for large profile datasets

### Task 2.2: Profile Detail View
- Design profile detail modal or dedicated page template
- Format LinkedIn profile data for readable display
- Include profile image, contact information, work experience, education, skills
- Add navigation between profiles from detail view
- Implement responsive design for different screen sizes

### Task 2.3: Profile Management Actions
- Add profile action buttons (score, re-score, view details, delete)
- Implement bulk selection for multi-profile operations
- Add profile status indicators (scored, processing, error states)
- Create confirmation dialogs for destructive actions

## Phase 3: Scoring System Integration (2-3 hours)

### Task 3.1: Scoring Interface
- Create scoring form with template selection dropdown
- Implement profile scoring request with progress indicators
- Display scoring results with detailed breakdown and scores
- Add re-scoring capability with different templates
- Show scoring history and timestamps

### Task 3.2: Scoring Results Display
- Design results display with clear score visualization
- Show detailed scoring criteria and explanations
- Implement results comparison between different template scores
- Add export functionality for scoring results
- Create scoring status tracking and error handling

## Phase 4: Template Management (2-3 hours)

### Task 4.1: Template CRUD Interface
- Create template listing table with search and filter capabilities
- Implement template creation form with validation
- Add template editing with version control
- Implement template deletion with safety checks
- Show template usage statistics and history

### Task 4.2: Template Versioning System
- Design template version comparison interface
- Implement version saving and restoration
- Add version history display with timestamps and changes
- Create template testing interface for validation
- Implement template activation and deactivation

## Phase 5: LinkedIn Ingestion Interface (2-3 hours)

### Task 5.1: Ingestion Form
- Create LinkedIn URL input form with validation
- Implement URL format checking and sanitization
- Add batch URL ingestion capability
- Create ingestion job queue display
- Implement progress monitoring with real-time updates

### Task 5.2: Ingestion Monitoring
- Display active and completed ingestion jobs
- Show ingestion progress with detailed status updates
- Implement error handling for failed ingestions
- Add retry functionality for failed jobs
- Create ingestion history and statistics

## Phase 6: Dashboard and Real-time Features (1-2 hours)

### Task 6.1: Dashboard Implementation
- Create system overview dashboard with key statistics
- Display recent activity feed with profile ingestions and scoring
- Show system health indicators and performance metrics
- Implement quick access to common actions
- Add system configuration display

### Task 6.2: Real-time Updates
- Set up Socket.io for real-time communications
- Implement live updates for job progress and completions
- Add real-time notifications for system events
- Update dashboard statistics in real-time
- Implement WebSocket connection management and reconnection

## Phase 7: UI Polish and Testing (1-2 hours)

### Task 7.1: User Experience Enhancement
- Implement responsive design improvements
- Add loading states and skeleton screens
- Create consistent error messaging and user feedback
- Implement keyboard shortcuts for power users
- Add tooltips and help text for complex features

### Task 7.2: Testing and Validation
- Test all CRUD operations with backend API
- Validate form inputs and error handling
- Test real-time features and WebSocket connections
- Perform cross-browser testing and responsive design validation
- Load test with larger datasets for performance optimization

## Phase 8: Deployment and Integration (1 hour)

### Task 8.1: Production Deployment
- Configure production environment variables
- Set up process management (PM2 or similar)
- Configure reverse proxy for admin UI alongside FastAPI
- Implement health checks and monitoring
- Create deployment documentation and procedures

### Task 8.2: Final Integration Testing
- Test full integration with existing FastAPI backend
- Validate all API endpoints and data flows
- Perform user acceptance testing with sample workflows
- Document admin UI usage and maintenance procedures
- Create backup and recovery procedures

## Total Estimated Time: 12-18 hours

This task breakdown prioritizes core functionality first (profile management and scoring) followed by template management, ingestion features, and finally polish and deployment. Each task is designed to be completable independently while building toward the full admin UI functionality.
