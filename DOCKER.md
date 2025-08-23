# Docker Development & Deployment Workflow

This document explains how to use Docker for local development and deployment of the LinkedIn Ingestion Service.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Local Dev      │    │  Container       │    │  Production     │
│                 │    │  Registry        │    │                 │
│ docker build    │───▶│  ghcr.io        │───▶│  Railway        │
│ docker-compose  │    │  docker.io       │    │  Fly.io         │
│ Testing         │    │  ECR/ACR/GCR     │    │  Render         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Set up environment
```bash
# Copy template and fill in your values
cp .env.template .env
# Edit .env with your actual credentials
```

### 2. Build and run locally
```bash
# Build the Docker image
./scripts/build.sh

# Run with Docker Compose (recommended for development)
docker-compose up

# Or run directly
docker run -p 8000:8000 --env-file .env linkedin-ingestion:latest
```

### 3. Test the service
```bash
# Health check
curl http://localhost:8000/api/v1/health

# API documentation
open http://localhost:8000/docs
```

## 📦 Docker Commands

### Building Images
```bash
# Build latest
./scripts/build.sh

# Build with specific tag
./scripts/build.sh v1.2.3

# Build manually
docker build -t linkedin-ingestion:latest .
```

### Running Containers
```bash
# Development with live reload (docker-compose)
docker-compose up --build

# Production-like testing
docker-compose -f docker-compose.yml up

# Run single container
docker run -p 8000:8000 --env-file .env linkedin-ingestion:latest

# Run with custom environment
docker run -p 8000:8000 \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_ANON_KEY=your_key \
  linkedin-ingestion:latest
```

### Debugging
```bash
# View logs
docker-compose logs -f linkedin-ingestion

# Execute shell in running container
docker exec -it linkedin-ingestion_linkedin-ingestion_1 bash

# Check container health
docker ps
docker inspect linkedin-ingestion:latest
```

## 🚚 Deployment Workflow

### 1. GitHub Container Registry (Recommended)
```bash
# Set up GitHub token
export GITHUB_TOKEN=your_github_personal_access_token

# Build and push
./scripts/build.sh v1.2.3
./scripts/deploy.sh v1.2.3
```

### 2. Docker Hub
```bash
# Login to Docker Hub
docker login

# Build with Docker Hub registry
./scripts/build.sh v1.2.3 docker.io/yourusername

# Push to Docker Hub
./scripts/deploy.sh v1.2.3 docker.io/yourusername
```

### 3. Configure Railway
1. Go to Railway dashboard
2. Select your service
3. Navigate to Settings → Deploy
4. Change source from "GitHub Repo" to "Docker Image"
5. Set Image URL: `ghcr.io/bautrey/linkedin-ingestion:latest`
6. Click "Deploy"

**Benefits of Docker deployment on Railway:**
- ✅ Faster deployments (no build time)
- ✅ Consistent environments
- ✅ Better caching
- ✅ Version control of images
- ✅ Rollback capability

## 🔧 Configuration

### Environment Variables
All configuration is done through environment variables. See `.env.template` for the complete list.

Key variables:
- `SUPABASE_URL` & `SUPABASE_ANON_KEY`: Database connection
- `OPENAI_API_KEY`: For embeddings and LLM scoring
- `API_KEY`: Secure your API endpoints
- `CASSIDY_API_KEY`: LinkedIn data source

### Docker Compose Overrides
Create `docker-compose.override.yml` for local customizations:
```yaml
version: '3.8'
services:
  linkedin-ingestion:
    environment:
      - ENVIRONMENT=local-dev
    volumes:
      - ./app:/app/app:ro  # Live code reload
```

## 🧪 Testing & Development

### Local Testing
```bash
# Full stack with admin UI
docker-compose up

# API only
docker-compose up linkedin-ingestion

# With specific environment
ENVIRONMENT=testing docker-compose up
```

### Production Testing
```bash
# Remove development volume mounts
docker-compose -f docker-compose.yml up

# Test specific image version
docker run -p 8000:8000 --env-file .env linkedin-ingestion:v1.2.3
```

### Performance Testing
```bash
# Check image size
docker images linkedin-ingestion

# Analyze layers
docker history linkedin-ingestion:latest

# Check resource usage
docker stats
```

## 🔄 CI/CD Integration

### GitHub Actions (Example)
```yaml
name: Build and Deploy
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push
        run: |
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          ./scripts/build.sh ${{ github.ref_name }}
          ./scripts/deploy.sh ${{ github.ref_name }}
```

## 🐛 Troubleshooting

### Common Issues

**Build Failures:**
```bash
# Clear cache and rebuild
docker system prune -a
docker-compose build --no-cache
```

**Port Conflicts:**
```bash
# Check what's using port 8000
lsof -i :8000
# Kill the process or use different port
docker run -p 8001:8000 linkedin-ingestion:latest
```

**Environment Variables:**
```bash
# Check if .env is loaded
docker-compose config

# Debug environment in container
docker exec -it container_name env | grep SUPABASE
```

### Health Check Failures
- Ensure your Supabase credentials are correct
- Check if required services (OpenAI, Cassidy) are accessible
- Verify API_KEY is set properly

## 📊 Monitoring

### Container Metrics
```bash
# Resource usage
docker stats linkedin-ingestion

# Health status
docker inspect --format='{{.State.Health.Status}}' container_name

# Logs
docker logs -f --tail 100 container_name
```

### Application Metrics
- Health endpoint: `http://localhost:8000/api/v1/health`
- Detailed health: `http://localhost:8000/api/v1/health/detailed`
- API docs: `http://localhost:8000/docs`

## 🚀 Alternative Deployment Platforms

### Fly.io
```bash
# Install flyctl, then:
fly launch
fly deploy --image ghcr.io/bautrey/linkedin-ingestion:latest
```

### Render
1. Create new "Web Service"
2. Set "Docker Image" as source
3. Use image: `ghcr.io/bautrey/linkedin-ingestion:latest`
4. Set environment variables

### DigitalOcean App Platform
1. Create new app
2. Choose "Docker Hub" or "Container Registry"
3. Enter image URL: `ghcr.io/bautrey/linkedin-ingestion:latest`
4. Configure environment variables

## 💡 Best Practices

1. **Use multi-stage builds** for smaller images
2. **Pin base image versions** for consistency
3. **Use .dockerignore** to reduce build context
4. **Run as non-root user** for security
5. **Include health checks** for better orchestration
6. **Tag images with versions** for rollbacks
7. **Use environment variables** for configuration
8. **Monitor container metrics** in production

## 📚 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Railway Docker Deployments](https://docs.railway.app/deploy/deployments)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
