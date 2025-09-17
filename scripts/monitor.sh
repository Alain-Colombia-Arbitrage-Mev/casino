#!/bin/bash
# ==========================================
# AI CASINO - SCRIPT DE MONITOREO CONTINUO
# ==========================================

# Configuración
PROJECT_DIR="/opt/aicasino"
LOG_FILE="/var/log/aicasino-monitor.log"
ALERT_EMAIL="tu-email@dominio.com"
WEBHOOK_URL=""  # Slack webhook URL (opcional)

# Umbrales de alerta
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=85
RESPONSE_TIME_THRESHOLD=5000  # milliseconds

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Función para enviar alertas
send_alert() {
    local subject=$1
    local message=$2

    # Log de la alerta
    log "ALERT" "$subject: $message"

    # Enviar por email (si está configurado)
    if command -v mail >/dev/null 2>&1 && [[ -n "$ALERT_EMAIL" ]]; then
        echo "$message" | mail -s "AI Casino Alert: $subject" "$ALERT_EMAIL"
    fi

    # Enviar por webhook (si está configurado)
    if [[ -n "$WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"🚨 AI Casino Alert: '"$subject"'\n'"$message"'"}' \
            "$WEBHOOK_URL" >/dev/null 2>&1
    fi
}

# Verificar servicios Docker
check_services() {
    log "INFO" "Verificando estado de servicios Docker..."

    cd $PROJECT_DIR 2>/dev/null || {
        log "ERROR" "No se puede acceder al directorio del proyecto: $PROJECT_DIR"
        return 1
    }

    local services=("redis" "scraper" "backend" "python-ml" "frontend" "nginx")
    local failed_services=()

    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.production.yml ps | grep -q "${service}.*Up"; then
            log "INFO" "✅ Servicio $service está corriendo"
        else
            failed_services+=("$service")
            log "ERROR" "❌ Servicio $service NO está corriendo"

            # Intentar reiniciar el servicio
            log "INFO" "Intentando reiniciar servicio $service..."
            if docker-compose -f docker-compose.production.yml restart "$service"; then
                log "INFO" "Servicio $service reiniciado exitosamente"
                send_alert "Servicio Reiniciado" "El servicio $service fue reiniciado automáticamente"
            else
                log "ERROR" "No se pudo reiniciar el servicio $service"
                send_alert "Servicio Fallido" "El servicio $service no está corriendo y no se pudo reiniciar"
            fi
        fi
    done

    # Verificar salud de servicios
    check_service_health
}

# Verificar salud específica de servicios
check_service_health() {
    log "INFO" "Verificando salud de servicios..."

    # Backend Go
    if ! curl -f -s --max-time 10 "http://localhost:8080/health" >/dev/null; then
        log "WARNING" "Backend Go no responde correctamente"
        send_alert "Backend No Responde" "El backend Go no está respondiendo en puerto 8080"
    fi

    # Python ML
    if ! curl -f -s --max-time 15 "http://localhost:5001/health" >/dev/null; then
        log "WARNING" "Python ML no responde correctamente"
        send_alert "Python ML No Responde" "El backend Python ML no está respondiendo en puerto 5001"
    fi

    # Frontend
    if ! curl -f -s --max-time 10 "http://localhost:3000" >/dev/null; then
        log "WARNING" "Frontend no responde correctamente"
        send_alert "Frontend No Responde" "El frontend no está respondiendo en puerto 3000"
    fi

    # Redis
    if ! docker exec aicasino-redis redis-cli ping >/dev/null 2>&1; then
        log "ERROR" "Redis no responde a ping"
        send_alert "Redis No Responde" "Redis no está respondiendo a comandos ping"
    fi
}

# Verificar uso de recursos del sistema
check_system_resources() {
    log "INFO" "Verificando recursos del sistema..."

    # CPU Usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d',' -f1)
    cpu_usage=${cpu_usage%.*}  # Remove decimal part

    if [[ -n "$cpu_usage" ]] && [[ $cpu_usage -gt $CPU_THRESHOLD ]]; then
        log "WARNING" "Uso de CPU alto: ${cpu_usage}%"
        send_alert "CPU Alta" "Uso de CPU: ${cpu_usage}% (Umbral: ${CPU_THRESHOLD}%)"
    else
        log "INFO" "Uso de CPU: ${cpu_usage}%"
    fi

    # Memory Usage
    local mem_info=$(free | grep Mem)
    local mem_total=$(echo $mem_info | awk '{print $2}')
    local mem_used=$(echo $mem_info | awk '{print $3}')
    local mem_usage=$((mem_used * 100 / mem_total))

    if [[ $mem_usage -gt $MEMORY_THRESHOLD ]]; then
        log "WARNING" "Uso de memoria alto: ${mem_usage}%"
        send_alert "Memoria Alta" "Uso de memoria: ${mem_usage}% (Umbral: ${MEMORY_THRESHOLD}%)"
    else
        log "INFO" "Uso de memoria: ${mem_usage}%"
    fi

    # Disk Usage
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | cut -d'%' -f1)

    if [[ $disk_usage -gt $DISK_THRESHOLD ]]; then
        log "WARNING" "Uso de disco alto: ${disk_usage}%"
        send_alert "Disco Lleno" "Uso de disco: ${disk_usage}% (Umbral: ${DISK_THRESHOLD}%)"
    else
        log "INFO" "Uso de disco: ${disk_usage}%"
    fi

    # Verificar espacio en logs
    local log_size=$(du -sm /opt/aicasino/logs 2>/dev/null | awk '{print $1}' || echo "0")
    if [[ $log_size -gt 1000 ]]; then  # 1GB
        log "WARNING" "Logs ocupan ${log_size}MB"
        # Opcional: Limpiar logs antiguos automáticamente
        find /opt/aicasino/logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
    fi
}

# Verificar conectividad de Redis y datos
check_redis_data() {
    log "INFO" "Verificando datos en Redis..."

    local redis_keys=$(docker exec aicasino-redis redis-cli keys "*" 2>/dev/null | wc -l || echo "0")
    log "INFO" "Claves en Redis: $redis_keys"

    if [[ $redis_keys -eq 0 ]]; then
        log "WARNING" "Redis no tiene datos"
        send_alert "Redis Sin Datos" "Redis no contiene ninguna clave de datos"
    fi

    # Verificar números recientes
    local recent_numbers=$(docker exec aicasino-redis redis-cli llen "roulette:history" 2>/dev/null || echo "0")
    log "INFO" "Números en historial: $recent_numbers"

    if [[ $recent_numbers -lt 10 ]]; then
        log "WARNING" "Pocos números en el historial: $recent_numbers"
    fi
}

# Verificar logs por errores
check_logs_for_errors() {
    log "INFO" "Verificando logs por errores recientes..."

    # Verificar errores en logs de Docker de la última hora
    local errors=$(docker-compose -f /opt/aicasino/docker-compose.production.yml logs --since=1h 2>/dev/null | grep -i error | wc -l)

    if [[ $errors -gt 10 ]]; then
        log "WARNING" "Muchos errores en logs: $errors errores en la última hora"
        send_alert "Errores en Logs" "Se detectaron $errors errores en los logs de la última hora"
    fi
}

# Verificar tiempo de respuesta
check_response_times() {
    log "INFO" "Verificando tiempos de respuesta..."

    # Backend
    local backend_time=$(curl -o /dev/null -s -w "%{time_total}" --max-time 10 "http://localhost:8080/health" | awk '{print $1*1000}')
    if [[ ${backend_time%.*} -gt $RESPONSE_TIME_THRESHOLD ]]; then
        log "WARNING" "Backend lento: ${backend_time}ms"
    fi

    # Frontend
    local frontend_time=$(curl -o /dev/null -s -w "%{time_total}" --max-time 10 "http://localhost:3000" | awk '{print $1*1000}')
    if [[ ${frontend_time%.*} -gt $RESPONSE_TIME_THRESHOLD ]]; then
        log "WARNING" "Frontend lento: ${frontend_time}ms"
    fi
}

# Generar reporte de estado
generate_status_report() {
    local report_file="/tmp/aicasino-status-$(date +%Y%m%d_%H%M%S).txt"

    {
        echo "AI CASINO - REPORTE DE ESTADO"
        echo "=============================="
        echo "Fecha: $(date)"
        echo ""

        echo "SERVICIOS DOCKER:"
        docker-compose -f /opt/aicasino/docker-compose.production.yml ps
        echo ""

        echo "RECURSOS DEL SISTEMA:"
        echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')"
        echo "Memoria: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
        echo "Disco: $(df -h / | awk 'NR==2 {print $5 " usado de " $2}')"
        echo ""

        echo "DATOS REDIS:"
        echo "Claves totales: $(docker exec aicasino-redis redis-cli dbsize 2>/dev/null || echo "Error")"
        echo "Números en historial: $(docker exec aicasino-redis redis-cli llen "roulette:history" 2>/dev/null || echo "Error")"
        echo ""

        echo "ÚLTIMOS LOGS (10 líneas):"
        tail -10 $LOG_FILE

    } > $report_file

    log "INFO" "Reporte generado: $report_file"
}

# Función principal
main() {
    log "INFO" "=== INICIANDO VERIFICACIÓN DE MONITOREO ==="

    # Verificar que el script se ejecute desde el directorio correcto
    if [[ ! -d "$PROJECT_DIR" ]]; then
        log "ERROR" "Directorio del proyecto no encontrado: $PROJECT_DIR"
        exit 1
    fi

    # Ejecutar todas las verificaciones
    check_services
    check_system_resources
    check_redis_data
    check_logs_for_errors
    check_response_times

    # Generar reporte si se solicita
    if [[ "$1" == "--report" ]]; then
        generate_status_report
    fi

    log "INFO" "=== VERIFICACIÓN COMPLETADA ==="
}

# Ejecutar función principal
main "$@"