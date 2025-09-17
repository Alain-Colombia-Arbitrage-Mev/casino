#!/bin/bash
# ==========================================
# AI CASINO - SCRIPT DE BACKUP AUTOMATIZADO
# ==========================================

set -e

# Configuración
PROJECT_DIR="/opt/aicasino"
BACKUP_DIR="/opt/backups/aicasino"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/aicasino-backup.log"
RETENTION_DAYS=7
MAX_BACKUP_SIZE="5G"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Función de logging
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> $LOG_FILE

    case $level in
        "ERROR")   echo -e "${RED}[$level]${NC} $message" ;;
        "WARNING") echo -e "${YELLOW}[$level]${NC} $message" ;;
        "INFO")    echo -e "${GREEN}[$level]${NC} $message" ;;
        *)         echo "[$level] $message" ;;
    esac
}

# Verificar espacio disponible
check_disk_space() {
    log "INFO" "Verificando espacio en disco..."

    local available_space=$(df $BACKUP_DIR 2>/dev/null | awk 'NR==2 {print $4}' || echo "0")
    local required_space=5242880  # 5GB en KB

    if [[ $available_space -lt $required_space ]]; then
        log "ERROR" "Espacio insuficiente en $BACKUP_DIR. Disponible: ${available_space}KB, Requerido: ${required_space}KB"
        return 1
    fi

    log "INFO" "Espacio disponible: ${available_space}KB"
    return 0
}

# Crear directorio de backup
setup_backup_dir() {
    log "INFO" "Configurando directorio de backup..."

    mkdir -p $BACKUP_DIR/{redis,config,logs,ml_models}

    if [[ ! -w $BACKUP_DIR ]]; then
        log "ERROR" "No se puede escribir en $BACKUP_DIR"
        return 1
    fi

    log "INFO" "Directorio de backup listo: $BACKUP_DIR"
}

# Backup de Redis
backup_redis() {
    log "INFO" "Iniciando backup de Redis..."

    if ! docker exec aicasino-redis redis-cli ping >/dev/null 2>&1; then
        log "ERROR" "Redis no está disponible"
        return 1
    fi

    # Crear snapshot RDB
    if docker exec aicasino-redis redis-cli bgsave >/dev/null 2>&1; then
        log "INFO" "Background save iniciado"

        # Esperar a que termine el backup
        while docker exec aicasino-redis redis-cli lastsave 2>/dev/null | grep -q "$(docker exec aicasino-redis redis-cli lastsave 2>/dev/null)"; do
            sleep 2
        done

        # Copiar el archivo RDB
        docker cp aicasino-redis:/data/dump.rdb $BACKUP_DIR/redis/redis_$DATE.rdb

        # Comprimir
        gzip $BACKUP_DIR/redis/redis_$DATE.rdb

        log "INFO" "✅ Backup de Redis completado: redis_$DATE.rdb.gz"
    else
        log "ERROR" "No se pudo crear backup de Redis"
        return 1
    fi

    # Backup adicional de claves específicas
    docker exec aicasino-redis redis-cli --rdb /data/backup_keys_$DATE.rdb >/dev/null 2>&1 || true
    docker cp aicasino-redis:/data/backup_keys_$DATE.rdb $BACKUP_DIR/redis/keys_$DATE.rdb 2>/dev/null || true
}

# Backup de configuración
backup_config() {
    log "INFO" "Iniciando backup de configuración..."

    cd $PROJECT_DIR

    # Archivos de configuración críticos
    tar -czf $BACKUP_DIR/config/config_$DATE.tar.gz \
        .env.production \
        docker-compose.production.yml \
        nginx/ \
        scripts/ \
        --exclude='*.log' \
        --exclude='logs/' 2>/dev/null || {
        log "WARNING" "Algunos archivos de configuración no se pudieron respaldar"
    }

    log "INFO" "✅ Backup de configuración completado: config_$DATE.tar.gz"
}

# Backup de logs importantes
backup_logs() {
    log "INFO" "Iniciando backup de logs..."

    if [[ -d "$PROJECT_DIR/logs" ]]; then
        # Solo respaldar logs de los últimos 7 días
        find $PROJECT_DIR/logs -name "*.log" -mtime -7 -type f | \
        tar -czf $BACKUP_DIR/logs/logs_$DATE.tar.gz -T - 2>/dev/null || {
            log "WARNING" "No se encontraron logs recientes para respaldar"
        }
    else
        log "WARNING" "Directorio de logs no encontrado: $PROJECT_DIR/logs"
    fi

    log "INFO" "✅ Backup de logs completado: logs_$DATE.tar.gz"
}

# Backup de modelos ML
backup_ml_models() {
    log "INFO" "Iniciando backup de modelos ML..."

    if [[ -d "$PROJECT_DIR/ml_models" ]]; then
        tar -czf $BACKUP_DIR/ml_models/ml_models_$DATE.tar.gz \
            -C $PROJECT_DIR ml_models/ 2>/dev/null || {
            log "WARNING" "No se pudieron respaldar todos los modelos ML"
        }
        log "INFO" "✅ Backup de modelos ML completado: ml_models_$DATE.tar.gz"
    else
        log "WARNING" "Directorio de modelos ML no encontrado"
    fi
}

# Verificar integridad de backups
verify_backups() {
    log "INFO" "Verificando integridad de backups..."

    local errors=0

    # Verificar archivos de backup
    for file in $BACKUP_DIR/redis/redis_$DATE.rdb.gz \
                $BACKUP_DIR/config/config_$DATE.tar.gz \
                $BACKUP_DIR/logs/logs_$DATE.tar.gz; do

        if [[ -f "$file" ]]; then
            if [[ "$file" == *.gz ]]; then
                if gzip -t "$file" 2>/dev/null; then
                    log "INFO" "✅ $file - OK"
                else
                    log "ERROR" "❌ $file - Corrupto"
                    errors=$((errors + 1))
                fi
            elif [[ "$file" == *.tar.gz ]]; then
                if tar -tzf "$file" >/dev/null 2>&1; then
                    log "INFO" "✅ $file - OK"
                else
                    log "ERROR" "❌ $file - Corrupto"
                    errors=$((errors + 1))
                fi
            fi
        else
            log "WARNING" "Archivo no encontrado: $file"
        fi
    done

    if [[ $errors -eq 0 ]]; then
        log "INFO" "✅ Todos los backups verificados correctamente"
        return 0
    else
        log "ERROR" "❌ Se encontraron $errors errores en la verificación"
        return 1
    fi
}

# Limpiar backups antiguos
cleanup_old_backups() {
    log "INFO" "Limpiando backups antiguos (>$RETENTION_DAYS días)..."

    local deleted_count=0

    # Limpiar por tipo de backup
    for backup_type in redis config logs ml_models; do
        if [[ -d "$BACKUP_DIR/$backup_type" ]]; then
            while IFS= read -r -d '' file; do
                rm -f "$file"
                deleted_count=$((deleted_count + 1))
                log "INFO" "Eliminado: $(basename "$file")"
            done < <(find "$BACKUP_DIR/$backup_type" -name "*" -mtime +$RETENTION_DAYS -type f -print0 2>/dev/null)
        fi
    done

    log "INFO" "✅ Limpieza completada. Archivos eliminados: $deleted_count"
}

# Crear manifiesto del backup
create_manifest() {
    log "INFO" "Creando manifiesto del backup..."

    local manifest_file="$BACKUP_DIR/manifest_$DATE.json"

    cat > "$manifest_file" << EOF
{
    "backup_date": "$(date -Iseconds)",
    "backup_id": "$DATE",
    "project_version": "$(cd $PROJECT_DIR && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "files": {
        "redis": "$(ls -la $BACKUP_DIR/redis/*$DATE* 2>/dev/null | wc -l) archivos",
        "config": "$(ls -la $BACKUP_DIR/config/*$DATE* 2>/dev/null | wc -l) archivos",
        "logs": "$(ls -la $BACKUP_DIR/logs/*$DATE* 2>/dev/null | wc -l) archivos",
        "ml_models": "$(ls -la $BACKUP_DIR/ml_models/*$DATE* 2>/dev/null | wc -l) archivos"
    },
    "total_size": "$(du -sh $BACKUP_DIR 2>/dev/null | cut -f1 || echo 'unknown')",
    "system_info": {
        "hostname": "$(hostname)",
        "docker_version": "$(docker --version 2>/dev/null || echo 'unknown')",
        "disk_usage": "$(df -h $BACKUP_DIR 2>/dev/null | awk 'NR==2 {print $5}' || echo 'unknown')"
    }
}
EOF

    log "INFO" "✅ Manifiesto creado: manifest_$DATE.json"
}

# Enviar notificación de backup
send_notification() {
    local status=$1
    local message=$2

    # Webhook de Slack (si está configurado)
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local emoji="✅"
        local color="good"

        if [[ "$status" != "success" ]]; then
            emoji="❌"
            color="danger"
        fi

        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$emoji AI Casino Backup: $message\", \"color\":\"$color\"}" \
            "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi

    # Email (si está configurado)
    if command -v mail >/dev/null 2>&1 && [[ -n "${BACKUP_EMAIL:-}" ]]; then
        echo "$message" | mail -s "AI Casino Backup - $status" "$BACKUP_EMAIL" || true
    fi
}

# Función principal
main() {
    log "INFO" "=== INICIANDO BACKUP AUTOMATIZADO ==="
    log "INFO" "Fecha: $(date)"
    log "INFO" "Backup ID: $DATE"

    local start_time=$(date +%s)
    local success=true

    # Verificaciones previas
    if ! check_disk_space; then
        log "ERROR" "Backup cancelado por falta de espacio"
        send_notification "failed" "Backup cancelado por falta de espacio en disco"
        exit 1
    fi

    if ! setup_backup_dir; then
        log "ERROR" "No se pudo configurar directorio de backup"
        exit 1
    fi

    # Ejecutar backups
    if ! backup_redis; then
        success=false
        log "ERROR" "Error en backup de Redis"
    fi

    if ! backup_config; then
        success=false
        log "ERROR" "Error en backup de configuración"
    fi

    backup_logs  # No crítico
    backup_ml_models  # No crítico

    # Verificaciones post-backup
    if ! verify_backups; then
        success=false
        log "ERROR" "Error en verificación de backups"
    fi

    # Mantenimiento
    cleanup_old_backups
    create_manifest

    # Calcular tiempo total
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [[ "$success" == "true" ]]; then
        log "INFO" "🎉 ¡Backup completado exitosamente!"
        log "INFO" "Duración: ${duration} segundos"
        log "INFO" "Ubicación: $BACKUP_DIR"

        send_notification "success" "Backup completado exitosamente en ${duration}s. ID: $DATE"
    else
        log "ERROR" "❌ Backup completado con errores"
        log "ERROR" "Duración: ${duration} segundos"

        send_notification "failed" "Backup completado con errores en ${duration}s. Revisar logs."
        exit 1
    fi

    log "INFO" "=== BACKUP FINALIZADO ==="
}

# Verificar argumentos
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  --help, -h     Mostrar esta ayuda"
    echo "  --verify       Solo verificar backups existentes"
    echo "  --cleanup      Solo limpiar backups antiguos"
    echo ""
    echo "Variables de entorno:"
    echo "  SLACK_WEBHOOK_URL   URL del webhook de Slack para notificaciones"
    echo "  BACKUP_EMAIL        Email para notificaciones"
    echo "  RETENTION_DAYS      Días de retención (default: 7)"
    exit 0
fi

if [[ "$1" == "--verify" ]]; then
    verify_backups
    exit $?
fi

if [[ "$1" == "--cleanup" ]]; then
    cleanup_old_backups
    exit 0
fi

# Ejecutar backup completo
main "$@"