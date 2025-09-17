#!/bin/bash

# AI Casino Docker Startup Script
# Sequential startup with health checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎰 Starting AI Casino System with Docker...${NC}"

# Function to wait for service health
wait_for_service() {
    local service_name=$1
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}⏳ Waiting for $service_name to be healthy...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service_name | grep -q "healthy"; then
            echo -e "${GREEN}✅ $service_name is healthy!${NC}"
            return 0
        fi

        echo -e "${YELLOW}   Attempt $attempt/$max_attempts - $service_name not ready yet...${NC}"
        sleep 10
        attempt=$((attempt + 1))
    done

    echo -e "${RED}❌ $service_name failed to become healthy after $max_attempts attempts${NC}"
    return 1
}

# Function to check if Docker is running
check_docker() {
    if ! docker --version &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed or not running${NC}"
        exit 1
    fi

    if ! docker-compose --version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Docker and Docker Compose are available${NC}"
}

# Function to cleanup previous containers
cleanup_containers() {
    echo -e "${YELLOW}🧹 Cleaning up previous containers...${NC}"
    docker-compose down --remove-orphans 2>/dev/null || true
    docker system prune -f --volumes 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Function to build images
build_images() {
    echo -e "${YELLOW}🔨 Building Docker images...${NC}"
    docker-compose build --no-cache --parallel
    echo -e "${GREEN}✅ Images built successfully${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}📋 Pre-flight checks...${NC}"
    check_docker

    echo -e "${BLUE}🧹 Preparation phase...${NC}"
    cleanup_containers

    echo -e "${BLUE}🔨 Build phase...${NC}"
    build_images

    echo -e "${BLUE}🚀 Starting services in sequence...${NC}"

    # Step 1: Start Redis
    echo -e "${YELLOW}1️⃣ Starting Redis database...${NC}"
    docker-compose up -d redis
    wait_for_service "redis"

    # Step 2: Start Backend
    echo -e "${YELLOW}2️⃣ Starting Go backend service...${NC}"
    docker-compose up -d backend
    wait_for_service "backend"

    # Step 3: Start Scraper and Frontend in parallel
    echo -e "${YELLOW}3️⃣ Starting scraper and frontend services...${NC}"
    docker-compose up -d scraper frontend
    wait_for_service "frontend"

    echo -e "${GREEN}🎉 All services are running successfully!${NC}"
    echo ""
    echo -e "${BLUE}📊 Service Status:${NC}"
    docker-compose ps

    echo ""
    echo -e "${BLUE}🌐 Access URLs:${NC}"
    echo -e "${GREEN}  Frontend: http://localhost:3000${NC}"
    echo -e "${GREEN}  Backend API: http://localhost:8080${NC}"
    echo -e "${GREEN}  Redis: localhost:6379${NC}"

    echo ""
    echo -e "${BLUE}📝 Useful Commands:${NC}"
    echo -e "${YELLOW}  View logs: docker-compose logs -f [service_name]${NC}"
    echo -e "${YELLOW}  Stop all: docker-compose down${NC}"
    echo -e "${YELLOW}  Restart service: docker-compose restart [service_name]${NC}"
    echo -e "${YELLOW}  View status: docker-compose ps${NC}"
}

# Handle script interruption
cleanup_on_exit() {
    echo -e "\n${YELLOW}🛑 Received interrupt signal. Stopping services...${NC}"
    docker-compose down
    exit 1
}

trap cleanup_on_exit INT TERM

# Run main function
main "$@"