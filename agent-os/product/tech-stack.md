# Technical Stack

> Last Updated: 2025-01-23
> Version: 1.0.0

## Application Framework

**FastAPI** (Latest stable)
- Modern Python web framework optimized for API development
- Automatic OpenAPI documentation generation
- Native async support for concurrent LinkedIn data fetching
- Pydantic integration for data validation

## Database System

**Supabase (PostgreSQL-based)**
- Primary database for metadata and relationship storage
- **Vector Database:** Supabase pgvector for LinkedIn profile and company embeddings
- Real-time capabilities for ingestion status updates
- Row Level Security for data access control

## Admin UI Framework

**Node.js + Express** (Simple admin interface)
- Lightweight Express server for admin UI
- Server-side rendering with EJS templates
- Static file serving for Bootstrap assets
- WebSocket support for real-time updates

## Frontend Framework

**Vanilla JavaScript + Bootstrap 5**
- Bootstrap 5 for responsive UI components
- Vanilla JavaScript for interactivity
- No complex build processes or frameworks
- Fast development and easy maintenance

## CSS Framework

**Bootstrap 5**
- Responsive grid system and components
- Built-in dark mode support
- Professional admin interface styling
- Minimal custom CSS requirements

## UI Component Library

**Bootstrap 5 Components**
- Tables, forms, modals, alerts
- Navigation and breadcrumb components
- Cards and badges for data display
- Icons via Bootstrap Icons

## Icon Library

**Bootstrap Icons**
- Consistent with Bootstrap styling
- Lightweight SVG icons
- Admin interface appropriate icons

## Application Hosting

**Railway**
- Automatic deployment from Git repository
- Environment variable management for API keys
- Horizontal scaling for high ingestion loads

## Database Hosting

**Supabase Cloud**
- Managed PostgreSQL with pgvector extension
- Automatic backups and scaling
- Real-time subscriptions for status updates

## Asset Hosting

**Express Static Files**
- Bootstrap CSS/JS served from node_modules
- Custom CSS and JavaScript assets
- Profile images and company logos (if applicable)

## Deployment Solution

**Railway + GitHub Integration**
- Automatic deployment on git push
- Environment-based configuration
- Health check monitoring

## Code Repository URL

*To be configured during setup*

## Additional Technical Components

### LinkedIn Data Processing
- **HTTP Client:** httpx for async LinkedIn API calls
- **Data Parsing:** Beautiful Soup 4 for HTML parsing (if needed)
- **Rate Limiting:** slowapi for LinkedIn API rate limit compliance

### Vector Operations
- **Embeddings:** OpenAI text-embedding-ada-002 for profile vectorization
- **Vector Storage:** Supabase pgvector for similarity search
- **Vector Queries:** Supabase Vector client libraries

### API Standards
- **Validation:** Pydantic models for request/response validation
- **Documentation:** Automatic Swagger/OpenAPI generation
- **Authentication:** API key-based authentication for internal services
- **CORS:** Configured for internal Fortium service domains

### Testing Framework
- **Unit Tests:** pytest with async support
- **API Testing:** httpx for endpoint testing
- **Mocking:** pytest-mock for LinkedIn API mocking
- **Coverage:** pytest-cov for test coverage reporting

#### MANDATORY Test Execution Standards
🚨 **NEVER HIDE TEST OUTPUT** - Project owner requires full test visibility

**Required Commands:**
- ✅ `source venv/bin/activate && pytest` (shows full dots format)
- ✅ `pytest` (if venv already active)
- ❌ **NEVER** `pytest | tail -X` (hides test execution)
- ❌ **NEVER** `pytest | head -X` (truncates output)
- ❌ **NEVER** use any pipe that hides test results

**Rationale:** Project owner has explicitly requested full test execution visibility.
Any agent working on this project must show complete pytest output.

### Monitoring & Logging
- **Structured Logging:** Python logging with JSON formatting
- **Health Checks:** FastAPI health endpoint
- **Metrics:** Basic performance and usage metrics
- **Error Tracking:** Comprehensive error logging for debugging

### Development Environment
- **Local Development:** FastAPI with uvicorn --reload
- **Database:** Supabase cloud (no local setup required)
- **Environment Management:** python-dotenv for local development
- **Dependencies:** requirements.txt for reproducible builds
