#!/bin/bash

# Build script for LinkedIn Ingestion Service
# Usage: ./scripts/build.sh [tag]

set -e

# Default values
TAG=${1:-latest}
IMAGE_NAME="linkedin-ingestion"
REGISTRY_URL="ghcr.io/bautrey"  # GitHub Container Registry - change as needed

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🐳 Building LinkedIn Ingestion Service...${NC}"

# Build the image
echo -e "${YELLOW}Building Docker image: ${REGISTRY_URL}/${IMAGE_NAME}:${TAG}${NC}"
docker build -t ${IMAGE_NAME}:${TAG} -t ${IMAGE_NAME}:latest .

# Tag for registry
docker tag ${IMAGE_NAME}:${TAG} ${REGISTRY_URL}/${IMAGE_NAME}:${TAG}
docker tag ${IMAGE_NAME}:latest ${REGISTRY_URL}/${IMAGE_NAME}:latest

echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo -e "${GREEN}Local image: ${IMAGE_NAME}:${TAG}${NC}"
echo -e "${GREEN}Registry image: ${REGISTRY_URL}/${IMAGE_NAME}:${TAG}${NC}"

# Show image size
echo -e "${YELLOW}📊 Image size:${NC}"
docker images ${IMAGE_NAME}:${TAG} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo -e "${YELLOW}🚀 To run locally:${NC}"
echo -e "  docker run -p 8000:8000 --env-file .env ${IMAGE_NAME}:${TAG}"
echo -e "${YELLOW}🚀 To run with docker-compose:${NC}"
echo -e "  docker-compose up"
echo -e "${YELLOW}📤 To push to registry:${NC}"
echo -e "  docker push ${REGISTRY_URL}/${IMAGE_NAME}:${TAG}"
