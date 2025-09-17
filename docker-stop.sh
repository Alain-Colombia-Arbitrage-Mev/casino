#!/bin/bash

# AI Casino Docker Stop Script
# Graceful shutdown with data preservation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping AI Casino System...${NC}"

# Function to stop service gracefully
stop_service() {
    local service_name=$1
    echo -e "${YELLOW}⏹️  Stopping $service_name...${NC}"

    if docker-compose ps -q $service_name | grep -q .; then
        docker-compose stop $service_name
        echo -e "${GREEN}✅ $service_name stopped successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  $service_name was not running${NC}"
    fi
}

# Function to backup Redis data
backup_redis_data() {
    if docker-compose ps -q redis | grep -q .; then
        echo -e "${YELLOW}💾 Creating Redis backup...${NC}"
        local backup_dir="./backups"
        local backup_file="redis_backup_$(date +%Y%m%d_%H%M%S).rdb"

        mkdir -p $backup_dir
        docker-compose exec -T redis redis-cli BGSAVE
        sleep 5
        docker cp $(docker-compose ps -q redis):/data/dump.rdb "$backup_dir/$backup_file"
        echo -e "${GREEN}✅ Redis backup saved to $backup_dir/$backup_file${NC}"
    fi
}

# Function to show final status
show_final_status() {
    echo ""
    echo -e "${BLUE}📊 Final Status:${NC}"
    docker-compose ps

    echo ""
    echo -e "${BLUE}💾 Persistent Data:${NC}"
    echo -e "${GREEN}  Redis data volume: preserved${NC}"
    echo -e "${GREEN}  Backups: ./backups/${NC}"

    echo ""
    echo -e "${BLUE}🔄 Restart Commands:${NC}"
    echo -e "${YELLOW}  Full restart: ./docker-start.sh${NC}"
    echo -e "${YELLOW}  Quick restart: docker-compose up -d${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}📋 Checking running services...${NC}"

    if ! docker-compose ps | grep -q "Up"; then
        echo -e "${YELLOW}⚠️  No services are currently running${NC}"
        exit 0
    fi

    # Optional: Create backup before stopping
    read -p "Create Redis backup before stopping? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        backup_redis_data
    fi

    echo -e "${BLUE}🛑 Stopping services in reverse order...${NC}"

    # Stop frontend and scraper first
    stop_service "frontend"
    stop_service "scraper"

    # Stop backend
    stop_service "backend"

    # Stop Redis last
    stop_service "redis"

    echo -e "${GREEN}🎉 All services stopped successfully!${NC}"
    show_final_status
}

# Handle script interruption
cleanup_on_exit() {
    echo -e "\n${YELLOW}🛑 Received interrupt signal. Force stopping...${NC}"
    docker-compose down
    exit 1
}

trap cleanup_on_exit INT TERM

# Check if force stop is requested
if [[ "$1" == "--force" ]] || [[ "$1" == "-f" ]]; then
    echo -e "${RED}⚡ Force stopping all services...${NC}"
    docker-compose down
    exit 0
fi

# Run main function
main "$@"