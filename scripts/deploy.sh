#!/bin/bash

# Deploy script for LinkedIn Ingestion Service
# Usage: ./scripts/deploy.sh [tag] [registry]

set -e

# Default values
TAG=${1:-latest}
REGISTRY_URL=${2:-"ghcr.io/bautrey"}  # Default to GitHub Container Registry
IMAGE_NAME="linkedin-ingestion"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Deploying LinkedIn Ingestion Service...${NC}"

# Check if image exists locally
if ! docker images --format 'table {{.Repository}}:{{.Tag}}' | grep -q "${IMAGE_NAME}:${TAG}"; then
    echo -e "${RED}❌ Image ${IMAGE_NAME}:${TAG} not found locally. Build it first with:${NC}"
    echo -e "  ./scripts/build.sh ${TAG}"
    exit 1
fi

# Login to registry (GitHub Container Registry example)
echo -e "${YELLOW}🔐 Logging in to ${REGISTRY_URL}...${NC}"
if [[ ${REGISTRY_URL} == *"ghcr.io"* ]]; then
    echo -e "${YELLOW}GitHub Container Registry detected. Make sure you have GITHUB_TOKEN set.${NC}"
    echo $GITHUB_TOKEN | docker login ghcr.io -u $(git config user.name) --password-stdin
elif [[ ${REGISTRY_URL} == *"docker.io"* ]]; then
    echo -e "${YELLOW}Docker Hub detected. Make sure you have DOCKER_TOKEN set.${NC}"
    echo $DOCKER_TOKEN | docker login -u $(docker config ls | grep userName | awk '{print $2}') --password-stdin
else
    echo -e "${YELLOW}Custom registry detected. Ensure you're logged in.${NC}"
fi

# Push the images
echo -e "${YELLOW}📤 Pushing to registry...${NC}"
docker push ${REGISTRY_URL}/${IMAGE_NAME}:${TAG}
docker push ${REGISTRY_URL}/${IMAGE_NAME}:latest

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}Registry URL: ${REGISTRY_URL}/${IMAGE_NAME}:${TAG}${NC}"

# Generate Railway deployment command
echo -e "${YELLOW}🚂 Railway deployment:${NC}"
echo -e "  1. Go to Railway dashboard"
echo -e "  2. Select your service"
echo -e "  3. Go to Settings > Deploy"
echo -e "  4. Set Source to 'Docker Image'"
echo -e "  5. Set Image URL to: ${REGISTRY_URL}/${IMAGE_NAME}:${TAG}"
echo -e "  6. Click 'Deploy'"

echo -e "${YELLOW}🐳 Alternative providers:${NC}"
echo -e "  Fly.io: fly deploy --image ${REGISTRY_URL}/${IMAGE_NAME}:${TAG}"
echo -e "  Render: Set Docker image to ${REGISTRY_URL}/${IMAGE_NAME}:${TAG}"
echo -e "  DigitalOcean App Platform: Use ${REGISTRY_URL}/${IMAGE_NAME}:${TAG}"
