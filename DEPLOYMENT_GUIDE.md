# 🚀 Guía de Deployment en Producción - AI Casino Roulette System

## 📋 Tabla de Contenido

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Requisitos de Infraestructura](#requisitos-de-infraestructura)
3. [Deployment en VPS/Cloud](#deployment-en-vpscloud)
4. [Configuración de Docker en Producción](#configuración-de-docker-en-producción)
5. [Configuración de Dominio y SSL](#configuración-de-dominio-y-ssl)
6. [Monitoreo y Logs](#monitoreo-y-logs)
7. [Mantenimiento y Updates](#mantenimiento-y-updates)
8. [Troubleshooting](#troubleshooting)

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐     ┌─────────────────┐
│   FRONTEND      │     │   SCRAPER       │
│   (Nuxt.js)     │     │   (Python)      │
│   Port: 3000    │     │   Auto-detect   │
└─────────────────┘     └─────────────────┘
         │                       │
         │              ┌─────────────────┐
         │              │     REDIS       │
         │              │   (Database)    │
         │              │   Port: 6379    │
         │              └─────────────────┘
         │                       │
┌─────────────────┐     ┌─────────────────┐
│   BACKEND GO    │────▶│  BACKEND PYTHON │
│   (Statistics)  │     │   (ML/XGBoost)  │
│   Port: 8080    │     │   Port: 5001    │
└─────────────────┘     └─────────────────┘
```

---

## 🖥️ Requisitos de Infraestructura

### Mínimos Recomendados:
- **CPU:** 2 vCPUs
- **RAM:** 4GB RAM
- **Storage:** 20GB SSD
- **Bandwidth:** 100GB/mes
- **OS:** Ubuntu 20.04+ / CentOS 8+ / Debian 11+

### Recomendado para Producción:
- **CPU:** 4 vCPUs
- **RAM:** 8GB RAM
- **Storage:** 50GB SSD
- **Bandwidth:** 500GB/mes
- **OS:** Ubuntu 22.04 LTS

### Proveedores Recomendados:
- **DigitalOcean:** Droplet $40/mes (4GB RAM, 2 vCPU)
- **AWS:** t3.medium $30-50/mes
- **Linode:** Shared CPU $20-40/mes
- **Vultr:** Regular Performance $20-40/mes
- **Hetzner:** Cloud CPX21 €8.21/mes (más económico)

---

## 🌐 Deployment en VPS/Cloud

### 1. Preparación del Servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias básicas
sudo apt install -y curl wget git vim ufw fail2ban

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Reiniciar para aplicar permisos
sudo reboot
```

### 2. Configuración de Seguridad

```bash
# Configurar firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Configurar fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Clonar y Configurar el Proyecto

```bash
# Clonar repositorio
git clone <tu-repositorio> /opt/aicasino
cd /opt/aicasino

# Crear variables de entorno para producción
cp .env.example .env.production

# Editar configuración
nano .env.production
```

### 4. Configuración de Variables de Entorno

```bash
# .env.production
NODE_ENV=production
REDIS_URL=redis://redis:6379
BACKEND_URL=http://backend:8080
PYTHON_ML_URL=http://python-ml:5001
DOMAIN=tu-dominio.com
SSL_EMAIL=tu-email@dominio.com

# Configuración Redis
REDIS_PASSWORD=tu_password_seguro_aqui
REDIS_MAXMEMORY=1gb
REDIS_MAXMEMORY_POLICY=allkeys-lru

# Configuración de logs
LOG_LEVEL=info
LOG_RETENTION_DAYS=30
```

---

## 🐳 Configuración de Docker en Producción

### 1. Docker Compose para Producción

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  redis:
    image: redis:7.2-alpine
    container_name: aicasino-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory ${REDIS_MAXMEMORY} --maxmemory-policy ${REDIS_MAXMEMORY_POLICY}
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    networks:
      - aicasino-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  scraper:
    build:
      context: ./scraper
      dockerfile: Dockerfile.production
    container_name: aicasino-scraper
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - ./logs:/app/logs
    networks:
      - aicasino-network
    healthcheck:
      test: ["CMD", "python", "-c", "import redis; r=redis.Redis(host='redis', password='${REDIS_PASSWORD}'); r.ping()"]
      interval: 60s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.production
    container_name: aicasino-backend
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - PORT=8080
      - GIN_MODE=release
    volumes:
      - ./logs:/app/logs
    networks:
      - aicasino-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  python-ml:
    build:
      context: ./backend
      dockerfile: Dockerfile.python
    container_name: aicasino-python-ml
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - PORT=5001
      - FLASK_ENV=production
    volumes:
      - ./ml_models:/app/models
      - ./logs:/app/logs
    networks:
      - aicasino-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.production
    container_name: aicasino-frontend
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_healthy
    environment:
      - NODE_ENV=production
      - NUXT_PUBLIC_API_BASE_URL=https://${DOMAIN}/api
      - NUXT_PUBLIC_PYTHON_ML_URL=https://${DOMAIN}/ml-api
    volumes:
      - ./logs:/app/logs
    networks:
      - aicasino-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: aicasino-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/sites-available:/etc/nginx/sites-available
      - ./ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - frontend
      - backend
      - python-ml
    networks:
      - aicasino-network

volumes:
  redis_data:
  ssl_certs:

networks:
  aicasino-network:
    driver: bridge
```

### 2. Configuración de Nginx

```nginx
# nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Include site configurations
    include /etc/nginx/sites-available/*.conf;
}
```

```nginx
# nginx/sites-available/aicasino.conf
upstream frontend {
    server frontend:3000;
}

upstream backend {
    server backend:8080;
}

upstream python_ml {
    server python-ml:5001;
}

server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Frontend (Nuxt.js)
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Backend API (Go)
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://backend/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }

    # Python ML API
    location /ml-api/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://python_ml/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /_nuxt/hmr {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 🔒 Configuración de Dominio y SSL

### 1. Configurar DNS

```bash
# Configurar registros DNS en tu proveedor:
# A record: tu-dominio.com → IP_DEL_SERVIDOR
# CNAME: www.tu-dominio.com → tu-dominio.com
```

### 2. Instalar SSL con Let's Encrypt

```bash
# Instalar Certbot
sudo apt install snapd
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot

# Crear certificado SSL
sudo certbot certonly --standalone -d tu-dominio.com -d www.tu-dominio.com

# Copiar certificados para Docker
sudo mkdir -p /opt/aicasino/ssl
sudo cp /etc/letsencrypt/live/tu-dominio.com/fullchain.pem /opt/aicasino/ssl/
sudo cp /etc/letsencrypt/live/tu-dominio.com/privkey.pem /opt/aicasino/ssl/
sudo chown -R $USER:$USER /opt/aicasino/ssl

# Configurar renovación automática
sudo crontab -e
# Agregar: 0 12 * * * /usr/bin/certbot renew --quiet && docker-compose -f /opt/aicasino/docker-compose.production.yml restart nginx
```

---

## 🚀 Scripts de Deployment

### 1. Script de Deployment Inicial

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Iniciando deployment de AI Casino..."

# Variables
PROJECT_DIR="/opt/aicasino"
BACKUP_DIR="/opt/backups/aicasino"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear backup
echo "📦 Creando backup..."
mkdir -p $BACKUP_DIR
docker-compose -f $PROJECT_DIR/docker-compose.production.yml exec redis redis-cli --rdb /data/backup_$DATE.rdb

# Actualizar código
echo "📥 Actualizando código..."
cd $PROJECT_DIR
git pull origin main

# Construir imágenes
echo "🔨 Construyendo imágenes..."
docker-compose -f docker-compose.production.yml build --no-cache

# Parar servicios (excepto Redis para mantener datos)
echo "⏹️ Parando servicios..."
docker-compose -f docker-compose.production.yml stop frontend backend python-ml scraper nginx

# Iniciar servicios
echo "▶️ Iniciando servicios..."
docker-compose -f docker-compose.production.yml up -d

# Verificar salud
echo "🏥 Verificando estado de servicios..."
sleep 30
docker-compose -f docker-compose.production.yml ps

echo "✅ Deployment completado!"
```

### 2. Script de Monitoreo

```bash
#!/bin/bash
# monitor.sh

PROJECT_DIR="/opt/aicasino"
LOG_FILE="/var/log/aicasino-monitor.log"

# Función de log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

# Verificar servicios
check_services() {
    cd $PROJECT_DIR

    services=("redis" "scraper" "backend" "python-ml" "frontend" "nginx")

    for service in "${services[@]}"; do
        if ! docker-compose -f docker-compose.production.yml ps | grep -q "${service}.*Up"; then
            log "ERROR: Servicio $service no está corriendo"
            # Restart service
            docker-compose -f docker-compose.production.yml restart $service
            log "INFO: Servicio $service reiniciado"
        else
            log "OK: Servicio $service funcionando correctamente"
        fi
    done
}

# Verificar recursos
check_resources() {
    # CPU
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        log "WARNING: Uso de CPU alto: ${cpu_usage}%"
    fi

    # Memoria
    mem_usage=$(free | grep Mem | awk '{printf("%.2f", $3/$2 * 100.0)}')
    if (( $(echo "$mem_usage > 85" | bc -l) )); then
        log "WARNING: Uso de memoria alto: ${mem_usage}%"
    fi

    # Disco
    disk_usage=$(df / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
    if [[ $disk_usage -gt 85 ]]; then
        log "WARNING: Uso de disco alto: ${disk_usage}%"
    fi
}

# Ejecutar verificaciones
log "INFO: Iniciando verificación de sistema"
check_services
check_resources
log "INFO: Verificación completada"
```

### 3. Automatización con Cron

```bash
# Configurar cron jobs
sudo crontab -e

# Monitoreo cada 5 minutos
*/5 * * * * /opt/aicasino/scripts/monitor.sh

# Backup diario a las 2 AM
0 2 * * * /opt/aicasino/scripts/backup.sh

# Limpieza de logs semanalmente
0 0 * * 0 /opt/aicasino/scripts/cleanup.sh

# Reinicio semanal (domingo 3 AM)
0 3 * * 0 /opt/aicasino/scripts/restart.sh
```

---

## 📊 Monitoreo y Logs

### 1. Configuración de Logs

```bash
# Crear estructura de logs
mkdir -p /opt/aicasino/logs/{nginx,backend,frontend,scraper,python-ml}

# Configurar rotación de logs
sudo nano /etc/logrotate.d/aicasino
```

```bash
# /etc/logrotate.d/aicasino
/opt/aicasino/logs/*/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        docker-compose -f /opt/aicasino/docker-compose.production.yml restart nginx
    endscript
}
```

### 2. Script de Monitoreo Avanzado

```bash
#!/bin/bash
# health_check.sh

check_url() {
    local url=$1
    local expected_status=$2
    local timeout=${3:-10}

    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time $timeout "$url")

    if [[ "$status" == "$expected_status" ]]; then
        echo "✅ $url - Status: $status"
        return 0
    else
        echo "❌ $url - Status: $status (Expected: $expected_status)"
        return 1
    fi
}

echo "🏥 Health Check - $(date)"
echo "=================================="

# Verificar endpoints
check_url "https://tu-dominio.com" "200"
check_url "https://tu-dominio.com/api/health" "200"
check_url "https://tu-dominio.com/ml-api/health" "200"

# Verificar Redis
if docker exec aicasino-redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis - PONG"
else
    echo "❌ Redis - No response"
fi

# Verificar uso de recursos
echo ""
echo "📊 Recursos del Sistema:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')"
echo "Memoria: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "Disco: $(df -h / | awk 'NR==2 {print $5 " usado de " $2}')"
```

---

## 🔧 Mantenimiento y Updates

### 1. Script de Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/aicasino"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/opt/aicasino"

mkdir -p $BACKUP_DIR

echo "📦 Iniciando backup..."

# Backup Redis
docker exec aicasino-redis redis-cli --rdb /data/backup_$DATE.rdb
docker cp aicasino-redis:/data/backup_$DATE.rdb $BACKUP_DIR/

# Backup configuraciones
tar -czf $BACKUP_DIR/config_$DATE.tar.gz -C $PROJECT_DIR \
    .env.production \
    nginx/ \
    docker-compose.production.yml

# Backup logs importantes
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz -C $PROJECT_DIR logs/

# Limpiar backups antiguos (mantener últimos 7 días)
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup completado: $DATE"
```

### 2. Script de Update

```bash
#!/bin/bash
# update.sh

PROJECT_DIR="/opt/aicasino"
cd $PROJECT_DIR

echo "🔄 Actualizando AI Casino..."

# Crear backup antes de actualizar
./scripts/backup.sh

# Actualizar código
git fetch origin
git pull origin main

# Verificar si hay cambios en Docker
if git diff HEAD~1 HEAD --name-only | grep -E "(Dockerfile|docker-compose)" > /dev/null; then
    echo "🔨 Detectados cambios en Docker, reconstruyendo..."
    docker-compose -f docker-compose.production.yml build --no-cache
fi

# Restart servicios
docker-compose -f docker-compose.production.yml restart

echo "✅ Update completado"
```

---

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. Servicios no inician
```bash
# Verificar logs
docker-compose -f docker-compose.production.yml logs [servicio]

# Verificar recursos
htop
df -h

# Reiniciar servicio específico
docker-compose -f docker-compose.production.yml restart [servicio]
```

#### 2. Error de conexión Redis
```bash
# Verificar estado de Redis
docker exec aicasino-redis redis-cli ping

# Verificar configuración
docker exec aicasino-redis cat /usr/local/etc/redis/redis.conf

# Verificar logs
docker logs aicasino-redis
```

#### 3. SSL no funciona
```bash
# Verificar certificados
sudo certbot certificates

# Renovar certificados
sudo certbot renew

# Verificar configuración nginx
docker exec aicasino-nginx nginx -t
```

#### 4. Performance lenta
```bash
# Verificar recursos
htop
iotop
docker stats

# Optimizar Redis
docker exec aicasino-redis redis-cli info memory

# Revisar logs de aplicación
docker-compose logs --tail=100 [servicio]
```

### Comandos Útiles

```bash
# Verificar estado general
docker-compose -f docker-compose.production.yml ps

# Ver logs en tiempo real
docker-compose -f docker-compose.production.yml logs -f

# Acceso a contenedor
docker exec -it aicasino-backend /bin/bash

# Verificar uso de recursos
docker stats

# Limpiar recursos no utilizados
docker system prune -a

# Reinicio completo del sistema
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

---

## 📞 Soporte y Contacto

Para soporte técnico o consultas sobre el deployment:

- **Issues:** GitHub Issues del proyecto
- **Documentación:** README.md del proyecto
- **Logs:** Revisar `/opt/aicasino/logs/`

---

## 📝 Checklist de Deployment

- [ ] Servidor configurado con requisitos mínimos
- [ ] Docker y Docker Compose instalados
- [ ] Firewall configurado
- [ ] DNS configurado
- [ ] SSL certificado instalado
- [ ] Variables de entorno configuradas
- [ ] Docker Compose production configurado
- [ ] Nginx configurado
- [ ] Scripts de monitoreo configurados
- [ ] Backups automatizados configurados
- [ ] Health checks funcionando
- [ ] Logs configurados
- [ ] Documentación del sistema actualizada

¡Tu sistema AI Casino Roulette está listo para producción! 🎰✨