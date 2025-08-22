#!/bin/bash
# LinkedIn Ingestion Admin UI - Docker Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CONTAINER_NAME="linkedin-admin-ui"

show_help() {
    echo -e "${BLUE}LinkedIn Ingestion Admin UI - Docker Management${NC}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start    - Start the admin UI service"
    echo "  stop     - Stop the admin UI service"
    echo "  restart  - Restart the admin UI service"
    echo "  status   - Show service status"
    echo "  logs     - Show service logs"
    echo "  build    - Build the Docker image"
    echo "  clean    - Remove container and image"
    echo "  shell    - Open shell inside container"
    echo "  health   - Check service health"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start the service in background"
    echo "  $0 logs     # View real-time logs"
    echo "  $0 status   # Check if service is running"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed or not in PATH${NC}"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker daemon is not running${NC}"
        exit 1
    fi
}

build_image() {
    echo -e "${BLUE}🔨 Building Docker image...${NC}"
    docker compose build
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
}

start_service() {
    echo -e "${BLUE}🚀 Starting LinkedIn Admin UI...${NC}"
    
    # Check if container is already running
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        echo -e "${YELLOW}⚠️  Service is already running${NC}"
        show_status
        return 0
    fi
    
    # Start the service
    docker compose up -d
    
    echo -e "${GREEN}✅ Admin UI started successfully${NC}"
    echo -e "${BLUE}📡 Service available at: http://localhost:3003${NC}"
    
    # Wait a moment and show status
    sleep 3
    show_status
}

stop_service() {
    echo -e "${BLUE}🛑 Stopping LinkedIn Admin UI...${NC}"
    docker compose down
    echo -e "${GREEN}✅ Admin UI stopped${NC}"
}

restart_service() {
    echo -e "${BLUE}🔄 Restarting LinkedIn Admin UI...${NC}"
    docker compose restart
    echo -e "${GREEN}✅ Admin UI restarted${NC}"
    show_status
}

show_status() {
    echo -e "${BLUE}📊 Service Status:${NC}"
    
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        echo -e "${GREEN}✅ Container is running${NC}"
        
        # Show container details
        docker ps --filter name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        # Show health status
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "unknown")
        case $HEALTH in
            "healthy")
                echo -e "${GREEN}💚 Health Status: Healthy${NC}"
                ;;
            "unhealthy")
                echo -e "${RED}💔 Health Status: Unhealthy${NC}"
                ;;
            "starting")
                echo -e "${YELLOW}💛 Health Status: Starting${NC}"
                ;;
            *)
                echo -e "${YELLOW}💛 Health Status: Unknown${NC}"
                ;;
        esac
        
        echo -e "${BLUE}🌐 Access URL: http://localhost:3003${NC}"
    else
        echo -e "${RED}❌ Container is not running${NC}"
    fi
}

show_logs() {
    echo -e "${BLUE}📋 Showing logs (Ctrl+C to exit):${NC}"
    docker compose logs -f
}

clean_up() {
    echo -e "${BLUE}🧹 Cleaning up Docker resources...${NC}"
    docker compose down --rmi all --volumes
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

open_shell() {
    if ! docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        echo -e "${RED}❌ Container is not running. Start it first with: $0 start${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}🐚 Opening shell in container...${NC}"
    docker exec -it $CONTAINER_NAME /bin/sh
}

check_health() {
    echo -e "${BLUE}🏥 Checking service health...${NC}"
    
    if ! docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        echo -e "${RED}❌ Container is not running${NC}"
        exit 1
    fi
    
    # Check HTTP endpoint
    if curl -f -s http://localhost:3003/ > /dev/null; then
        echo -e "${GREEN}✅ HTTP Health Check: Passed${NC}"
    else
        echo -e "${RED}❌ HTTP Health Check: Failed${NC}"
    fi
    
    # Show Docker health status
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "unknown")
    echo -e "${BLUE}🔍 Docker Health Status: $HEALTH${NC}"
    
    # Show resource usage
    echo -e "${BLUE}📊 Resource Usage:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $CONTAINER_NAME
}

# Main script logic
case "${1:-}" in
    "start")
        check_docker
        start_service
        ;;
    "stop")
        check_docker
        stop_service
        ;;
    "restart")
        check_docker
        restart_service
        ;;
    "status")
        check_docker
        show_status
        ;;
    "logs")
        check_docker
        show_logs
        ;;
    "build")
        check_docker
        build_image
        ;;
    "clean")
        check_docker
        clean_up
        ;;
    "shell")
        check_docker
        open_shell
        ;;
    "health")
        check_docker
        check_health
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    "")
        echo -e "${RED}❌ No command specified${NC}"
        echo ""
        show_help
        exit 1
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
