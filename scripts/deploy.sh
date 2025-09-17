#!/bin/bash
# =================================================
# AI CASINO - SCRIPT DE DEPLOYMENT EN PRODUCCIÓN
# =================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PROJECT_DIR="/opt/aicasino"
BACKUP_DIR="/opt/backups/aicasino"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/aicasino-deploy.log"

# Función de logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[ERROR] $1" >> $LOG_FILE
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[SUCCESS] $1" >> $LOG_FILE
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[WARNING] $1" >> $LOG_FILE
}

# Verificar que estamos en el directorio correcto
if [[ ! -f "docker-compose.production.yml" ]]; then
    error "docker-compose.production.yml no encontrado. Ejecutar desde el directorio del proyecto."
fi

log "🚀 Iniciando deployment de AI Casino..."

# Crear directorio de backup si no existe
mkdir -p $BACKUP_DIR

# 1. Crear backup de Redis
log "📦 Creando backup de Redis..."
if docker-compose -f docker-compose.production.yml ps | grep -q "aicasino-redis.*Up"; then
    docker-compose -f docker-compose.production.yml exec -T redis redis-cli --rdb /data/backup_$DATE.rdb || warning "No se pudo crear backup de Redis"
    docker cp aicasino-redis:/data/backup_$DATE.rdb $BACKUP_DIR/ 2>/dev/null || warning "No se pudo copiar backup de Redis"
    success "Backup de Redis creado"
else
    warning "Redis no está corriendo, omitiendo backup"
fi

# 2. Backup de configuración
log "📦 Creando backup de configuración..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    .env.production \
    nginx/ \
    docker-compose.production.yml \
    scripts/ 2>/dev/null || warning "Error en backup de configuración"

# 3. Actualizar código fuente
log "📥 Actualizando código fuente..."
git fetch origin
if git pull origin main; then
    success "Código actualizado desde Git"
else
    error "Error al actualizar código desde Git"
fi

# 4. Verificar si necesita rebuild
NEED_REBUILD=false
if git diff HEAD~1 HEAD --name-only | grep -E "(Dockerfile|package\.json|go\.mod|requirements\.txt)" > /dev/null; then
    NEED_REBUILD=true
    log "🔨 Detectados cambios que requieren rebuild..."
fi

# 5. Construir imágenes si es necesario
if [[ "$NEED_REBUILD" == "true" ]] || [[ "$1" == "--rebuild" ]]; then
    log "🔨 Construyendo imágenes Docker..."
    if docker-compose -f docker-compose.production.yml build --no-cache; then
        success "Imágenes construidas exitosamente"
    else
        error "Error al construir imágenes Docker"
    fi
fi

# 6. Verificar configuración
log "🔧 Verificando configuración..."
if [[ ! -f ".env.production" ]]; then
    warning "Archivo .env.production no encontrado, copiando desde ejemplo..."
    cp .env.production.example .env.production
    warning "IMPORTANTE: Editar .env.production con valores reales antes de continuar"
fi

# 7. Parar servicios (excepto Redis para mantener datos)
log "⏹️ Parando servicios para actualización..."
docker-compose -f docker-compose.production.yml stop frontend backend python-ml scraper nginx || warning "Error al parar algunos servicios"

# 8. Actualizar servicios dependientes primero
log "🔄 Actualizando Redis..."
docker-compose -f docker-compose.production.yml up -d redis
sleep 10

# 9. Iniciar servicios backend
log "▶️ Iniciando servicios backend..."
docker-compose -f docker-compose.production.yml up -d scraper backend python-ml
sleep 20

# 10. Verificar que backends estén healthy
log "🏥 Verificando salud de servicios backend..."
for i in {1..6}; do
    if docker-compose -f docker-compose.production.yml ps | grep -E "(backend|python-ml).*healthy" > /dev/null; then
        success "Servicios backend están healthy"
        break
    fi
    if [[ $i -eq 6 ]]; then
        error "Servicios backend no están healthy después de 60 segundos"
    fi
    log "Esperando que servicios backend estén healthy... ($i/6)"
    sleep 10
done

# 11. Iniciar frontend y nginx
log "▶️ Iniciando frontend y nginx..."
docker-compose -f docker-compose.production.yml up -d frontend nginx

# 12. Verificar que todos los servicios estén running
log "🏥 Verificación final de servicios..."
sleep 30

# Verificar cada servicio
services=("redis" "scraper" "backend" "python-ml" "frontend" "nginx")
failed_services=()

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.production.yml ps | grep "${service}.*Up" > /dev/null; then
        success "✅ $service está corriendo"
    else
        failed_services+=($service)
        error "❌ $service NO está corriendo"
    fi
done

# 13. Verificar endpoints
log "🌐 Verificando endpoints..."
sleep 10

# Función para verificar URL
check_url() {
    local url=$1
    local expected_status=$2
    local timeout=${3:-10}

    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time $timeout "$url" 2>/dev/null || echo "000")

    if [[ "$status" == "$expected_status" ]]; then
        success "✅ $url - Status: $status"
        return 0
    else
        warning "❌ $url - Status: $status (Expected: $expected_status)"
        return 1
    fi
}

# Verificar endpoints locales
check_url "http://localhost:8080/health" "200"
check_url "http://localhost:5001/health" "200"
check_url "http://localhost:3000" "200"

# 14. Limpiar recursos no utilizados
log "🧹 Limpiando recursos Docker no utilizados..."
docker system prune -f > /dev/null 2>&1 || true

# 15. Limpiar backups antiguos (mantener últimos 7 días)
log "🧹 Limpiando backups antiguos..."
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete 2>/dev/null || true
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true

# 16. Resultado final
if [[ ${#failed_services[@]} -eq 0 ]]; then
    success "🎉 ¡Deployment completado exitosamente!"
    success "📊 Estado del sistema:"
    docker-compose -f docker-compose.production.yml ps

    success "📝 URLs del sistema:"
    success "   Frontend: http://localhost:3000"
    success "   Backend API: http://localhost:8080"
    success "   Python ML API: http://localhost:5001"

    success "📂 Logs disponibles en:"
    success "   Deployment: $LOG_FILE"
    success "   Aplicación: $(pwd)/logs/"

else
    error "❌ Deployment completado con errores en: ${failed_services[*]}"
    error "Revisar logs: docker-compose -f docker-compose.production.yml logs [servicio]"
    exit 1
fi

log "✅ Deployment completado en $(date)"