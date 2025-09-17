#!/bin/bash

# AI Casino Docker Logs Management Script
# Easy log viewing and management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to show service logs
show_service_logs() {
    local service=$1
    local follow=$2

    if [[ "$follow" == "follow" ]]; then
        echo -e "${BLUE}📄 Following logs for $service (Press Ctrl+C to stop)...${NC}"
        docker-compose logs -f --tail=50 $service
    else
        echo -e "${BLUE}📄 Recent logs for $service:${NC}"
        docker-compose logs --tail=50 $service
    fi
}

# Function to show all logs
show_all_logs() {
    local follow=$1

    if [[ "$follow" == "follow" ]]; then
        echo -e "${BLUE}📄 Following all service logs (Press Ctrl+C to stop)...${NC}"
        docker-compose logs -f --tail=20
    else
        echo -e "${BLUE}📄 Recent logs for all services:${NC}"
        docker-compose logs --tail=20
    fi
}

# Function to show help
show_help() {
    echo -e "${BLUE}📖 AI Casino Docker Logs Script${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 [service] [options]"
    echo ""
    echo -e "${YELLOW}Services:${NC}"
    echo "  redis     - Redis database logs"
    echo "  backend   - Go backend service logs"
    echo "  scraper   - Python scraper logs"
    echo "  frontend  - Vue.js frontend logs"
    echo "  all       - All services logs (default)"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  -f, --follow  - Follow log output (live tail)"
    echo "  -h, --help    - Show this help"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0                    # Show recent logs for all services"
    echo "  $0 backend            # Show recent backend logs"
    echo "  $0 scraper -f         # Follow scraper logs"
    echo "  $0 all --follow       # Follow all logs"
}

# Function to check if services are running
check_services() {
    if ! docker-compose ps | grep -q "Up"; then
        echo -e "${RED}❌ No services are currently running${NC}"
        echo -e "${YELLOW}💡 Start services with: ./docker-start.sh${NC}"
        exit 1
    fi
}

# Main execution
main() {
    local service="all"
    local follow_mode="no"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            redis|backend|scraper|frontend|all)
                service="$1"
                shift
                ;;
            -f|--follow)
                follow_mode="follow"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done

    check_services

    # Show current service status
    echo -e "${BLUE}📊 Current Service Status:${NC}"
    docker-compose ps
    echo ""

    # Show logs based on service selection
    case $service in
        redis|backend|scraper|frontend)
            show_service_logs $service $follow_mode
            ;;
        all)
            show_all_logs $follow_mode
            ;;
        *)
            echo -e "${RED}❌ Invalid service: $service${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Handle script interruption
cleanup_on_exit() {
    echo -e "\n${YELLOW}🛑 Log viewing stopped${NC}"
    exit 0
}

trap cleanup_on_exit INT TERM

# Run main function
main "$@"