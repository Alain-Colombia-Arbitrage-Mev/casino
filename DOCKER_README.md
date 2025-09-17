# AI Casino Docker Setup

Complete containerized deployment of the AI Casino system with Redis, Go backend, Python scraper, and Vue.js frontend.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │     Backend     │    │     Scraper     │
│   (Vue.js)      │────│      (Go)       │────│    (Python)     │
│   Port: 3000    │    │   Port: 8080    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                      ┌─────────────────┐
                      │      Redis      │
                      │   (Database)    │
                      │   Port: 6379    │
                      └─────────────────┘
```

## 📦 Services

### 1. Redis Database
- **Image**: `redis:7.2-alpine`
- **Port**: `6379`
- **Purpose**: Primary data storage for roulette numbers and predictions
- **Features**: Persistence, memory optimization, health checks

### 2. Go Backend
- **Build**: Multi-stage optimized build
- **Port**: `8080`
- **Purpose**: API server with ML predictions
- **Features**: Fast startup, minimal footprint, health endpoints

### 3. Python Scraper
- **Build**: Chrome + Selenium optimized
- **Purpose**: Web scraping for roulette data
- **Features**: Headless browser, automatic restart, memory limits

### 4. Vue.js Frontend
- **Build**: Nuxt.js production build
- **Port**: `3000`
- **Purpose**: User interface for casino system
- **Features**: Server-side rendering, optimized assets

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space

### Option 1: Automated Start (Recommended)

**Linux/macOS:**
```bash
./docker-start.sh
```

**Windows:**
```cmd
docker-start.bat
```

### Option 2: Manual Start

```bash
# Build and start all services
docker-compose up -d

# Start services in sequence (recommended)
docker-compose up -d redis
docker-compose up -d backend
docker-compose up -d scraper frontend
```

## 🛠️ Management Scripts

### Start System
```bash
# Full startup with health checks
./docker-start.sh

# Quick start (no health checks)
docker-compose up -d
```

### Stop System
```bash
# Graceful shutdown with backup option
./docker-stop.sh

# Force stop
./docker-stop.sh --force
```

### View Logs
```bash
# All services
./docker-logs.sh

# Specific service
./docker-logs.sh backend

# Follow logs live
./docker-logs.sh scraper -f
```

## 📊 Monitoring & Health Checks

### Service Status
```bash
docker-compose ps
```

### Health Check Endpoints
- **Backend**: `http://localhost:8080/health`
- **Frontend**: `http://localhost:3000`
- **Redis**: `redis-cli ping`

### Resource Usage
```bash
docker stats
```

## 🔧 Configuration

### Environment Variables
Edit `.env.docker` for configuration:

```env
# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Backend
BACKEND_PORT=8080
API_BASE_URL=http://backend:8080

# Scraper
SCRAPER_INTERVAL=10
HEADLESS_MODE=true

# Frontend
FRONTEND_PORT=3000
NODE_ENV=production
```

### Redis Configuration
Edit `redis.conf` for Redis-specific settings:
- Memory limits
- Persistence options
- Security settings

## 🔐 Security Features

### Container Security
- Non-root users in all containers
- Read-only file systems where possible
- Resource limits and quotas
- Network isolation

### Data Protection
- Persistent volumes for Redis data
- Automatic backup capabilities
- Configuration secrets handling

## 📈 Performance Optimization

### Multi-stage Builds
- **Go Backend**: ~15MB final image
- **Frontend**: ~50MB final image
- **Scraper**: Optimized Chrome installation

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 512M
```

### Caching Strategy
- Docker layer caching
- Redis memory optimization
- Static asset optimization

## 🐛 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker daemon
docker --version

# Check logs
./docker-logs.sh

# Rebuild images
docker-compose build --no-cache
```

#### Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :3000
netstat -tulpn | grep :8080

# Change ports in docker-compose.yml
```

#### Memory Issues
```bash
# Check available memory
free -h

# Reduce container memory limits
# Edit docker-compose.yml deploy.resources
```

#### Redis Connection Issues
```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Redis logs
./docker-logs.sh redis
```

### Debug Mode
```bash
# Start with debug logging
COMPOSE_LOG_LEVEL=debug docker-compose up

# Enter container for debugging
docker-compose exec backend sh
docker-compose exec scraper bash
```

## 📁 File Structure

```
aicasino2/
├── docker-compose.yml          # Main orchestration
├── .env.docker                 # Environment config
├── redis.conf                  # Redis configuration
├── Dockerfile.backend          # Go backend image
├── Dockerfile.frontend         # Vue.js frontend image
├── Dockerfile.scraper          # Python scraper image
├── .dockerignore               # Global ignore rules
├── docker-start.sh             # Startup script (Linux/macOS)
├── docker-start.bat            # Startup script (Windows)
├── docker-stop.sh              # Stop script
├── docker-logs.sh              # Log management
├── scraper.requirements.txt    # Python dependencies
├── backend/
│   ├── .dockerignore          # Go-specific ignores
│   ├── go.mod                 # Go modules
│   └── *.go                   # Go source files
└── frontend/
    ├── .dockerignore          # Node-specific ignores
    ├── package.json           # Node dependencies
    └── (Vue.js source files)
```

## 🔄 Development Workflow

### 1. Code Changes
```bash
# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Rebuild all
docker-compose build --no-cache
```

### 2. Database Management
```bash
# Redis CLI access
docker-compose exec redis redis-cli

# Backup Redis data
docker-compose exec redis redis-cli BGSAVE

# View Redis data
docker-compose exec redis redis-cli KEYS "*"
```

### 3. Testing
```bash
# Test individual services
curl http://localhost:8080/health
curl http://localhost:3000

# Integration tests
docker-compose exec backend go test ./...
```

## 📊 Production Deployment

### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml aicasino
```

### Kubernetes
Convert using Kompose:
```bash
kompose convert -f docker-compose.yml
kubectl apply -f .
```

### Performance Tuning
- Use external Redis cluster
- Load balancer for multiple backend instances
- CDN for frontend assets
- Container orchestration platform

## 🔗 Useful Commands

```bash
# View service URLs
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8080"
echo "Redis: localhost:6379"

# Container shell access
docker-compose exec backend sh
docker-compose exec scraper bash
docker-compose exec frontend sh

# Resource monitoring
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Network inspection
docker network ls
docker network inspect aicasino2_aicasino-network

# Volume management
docker volume ls
docker volume inspect aicasino2_redis_data
```

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review service logs: `./docker-logs.sh`
3. Verify system requirements
4. Check Docker and Docker Compose versions

## 🎯 Next Steps

1. **Security**: Add SSL/TLS certificates
2. **Monitoring**: Integrate Prometheus/Grafana
3. **Scaling**: Implement horizontal scaling
4. **CI/CD**: Automated testing and deployment
5. **Backup**: Automated data backup strategy