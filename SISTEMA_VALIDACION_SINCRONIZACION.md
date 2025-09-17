# Sistema de Validación y Sincronización AI Casino

## 🎯 Arquitectura del Sistema

### Flujo de Datos Correcto:
```
SCRAPER (Python) → REDIS → BACKEND (Go) → FRONTEND (Vue.js)
    ⬇️                ⬇️         ⬇️           ⬇️
 1. Genera datos   2. Almacena  3. Procesa   4. Muestra
 2. Valida datos   3. Notifica  4. Predice   5. Tiempo real
 3. Envía heartbeat 4. Eventos  5. Aprende   6. Interactivo
```

## 🔒 Sistema de Validación Implementado

### 1. Validación en el Scraper (Python)

#### Funciones de Validación:
- **`validate_data_integrity(number_data)`**: Valida datos antes de enviar a Redis
- **`send_heartbeat()`**: Envía señal de vida cada 5 segundos
- **`notify_backend_new_data()`**: Notifica al backend sobre nuevos datos

#### Validaciones Realizadas:
- ✅ Número válido (0-36)
- ✅ Color consistente con el número
- ✅ Timestamp presente y válido
- ✅ No duplicados recientes (< 5 segundos)
- ✅ Contador de errores consecutivos

#### Variables de Entorno:
```env
DATA_VALIDATION=true
SCRAPER_INTERVAL=10
REDIS_HOST=redis
REDIS_PORT=6379
```

### 2. Validación en el Backend (Go)

#### Nuevas Rutas Implementadas:
- **`GET /api/system/scraper-status`**: Estado del scraper
- **`POST /api/system/validate-data`**: Validar datos recibidos
- **`GET /api/system/sync-status`**: Estado de sincronización

#### Listener de Eventos Redis:
- **`StartRedisEventListener()`**: Escucha canal `roulette:events`
- **`processNewNumber()`**: Procesa nuevos números automáticamente
- Ejecuta predicciones ML al recibir nuevos datos

#### Validaciones del Backend:
- ✅ Número válido (0-36)
- ✅ Color consistente
- ✅ Timestamp válido
- ✅ No duplicados
- ✅ Consistencia con Redis

## 🔄 Sistema de Sincronización

### 1. Heartbeat del Scraper
```json
{
  "scraper_status": "active",
  "timestamp": "2025-09-16T21:45:00Z",
  "session_start": "2025-09-16T21:30:00Z",
  "consecutive_errors": 0,
  "last_update": 1726522500
}
```

### 2. Notificaciones de Eventos
```json
{
  "event": "new_roulette_number",
  "number": 17,
  "timestamp": "2025-09-16T21:45:00Z",
  "trigger_prediction": true,
  "data_key": "roulette:current_number"
}
```

### 3. Flags de Sincronización
```json
{
  "has_new_data": true,
  "last_number": 17,
  "timestamp": 1726522500
}
```

## 🐳 Orden de Dependencias Docker

### Docker Compose Actualizado:
```yaml
services:
  redis:      # 🥇 PRIMERO: Base de datos
  scraper:    # 🥈 SEGUNDO: Genera datos (depende de Redis)
  backend:    # 🥉 TERCERO: Procesa datos (depende de Redis + Scraper)
  frontend:   # 🏆 CUARTO: Muestra datos (depende de Backend + Scraper)
```

### Variables de Entorno por Servicio:

#### Scraper:
```env
REDIS_HOST=redis
DATA_VALIDATION=true
SCRAPER_INTERVAL=10
HEADLESS_MODE=true
```

#### Backend:
```env
REDIS_HOST=redis
SCRAPER_VALIDATION=true
GIN_MODE=release
PORT=8080
```

#### Frontend:
```env
API_BASE_URL=http://backend:8080
REAL_TIME_UPDATES=true
NODE_ENV=production
```

## 📊 Monitoreo del Sistema

### Monitor Automático:
```bash
python monitor_system.py
```

#### Verificaciones Realizadas:
- ✅ Conexión Redis
- ✅ Estado del Scraper (heartbeat)
- ✅ Estado del Backend (APIs)
- ✅ Estado del Frontend (accesibilidad)
- ✅ Consistencia de datos
- ✅ Sincronización entre componentes

### Endpoints de Monitoreo:

#### Estado del Scraper:
```bash
curl http://localhost:8080/api/system/scraper-status
```

#### Validar Datos:
```bash
curl -X POST http://localhost:8080/api/system/validate-data \
  -H "Content-Type: application/json" \
  -d '{"number": 17, "color": "red", "timestamp": "2025-09-16T21:45:00Z"}'
```

#### Estado de Sincronización:
```bash
curl http://localhost:8080/api/system/sync-status
```

## 🚀 Comandos de Ejecución

### Iniciar Sistema Completo:
```bash
# 1. Construir y iniciar todos los servicios
docker-compose up --build -d

# 2. Verificar estado
docker-compose ps

# 3. Ver logs en tiempo real
docker-compose logs -f scraper backend frontend

# 4. Monitorear sistema
python monitor_system.py
```

### Orden de Inicio (Automático):
1. **Redis** se inicia primero
2. **Scraper** espera Redis healthy → inicia y genera datos
3. **Backend** espera Scraper started → inicia y procesa datos
4. **Frontend** espera Backend healthy → inicia y muestra datos

## 🔧 Resolución de Problemas

### Problemas Comunes:

#### 1. Scraper Offline:
```bash
# Verificar logs
docker-compose logs scraper

# Reiniciar scraper
docker-compose restart scraper
```

#### 2. Datos Inconsistentes:
```bash
# Verificar sincronización
curl http://localhost:8080/api/system/sync-status

# Limpiar y reiniciar
docker-compose down
docker-compose up --build -d
```

#### 3. Backend No Recibe Eventos:
```bash
# Verificar listener Redis
docker-compose logs backend | grep "🔔"

# Verificar notificaciones del scraper
docker-compose logs scraper | grep "🔔"
```

## 📈 Beneficios del Sistema

### 1. **Validación Robusta**:
- Datos consistentes entre componentes
- Detección automática de errores
- Prevención de datos corruptos

### 2. **Sincronización en Tiempo Real**:
- Notificaciones instantáneas
- Predicciones automáticas
- Estado del sistema monitoreado

### 3. **Orden de Dependencias**:
- Inicio secuencial correcto
- Datos fluyen en la dirección correcta
- Cada componente espera sus dependencias

### 4. **Monitoreo Automático**:
- Estado de todos los componentes
- Detección proactiva de problemas
- Recomendaciones automáticas

## 🎯 Resultado Final

El sistema ahora garantiza:

✅ **Scraper** genera datos validados y notifica al backend
✅ **Backend** recibe notificaciones y ejecuta predicciones automáticamente
✅ **Frontend** muestra datos en tiempo real y consistentes
✅ **Validación** completa en cada paso del flujo de datos
✅ **Sincronización** automática entre todos los componentes
✅ **Monitoreo** continuo del estado del sistema

### Flujo Completo Funcional:
```
🎰 Casino → 🕷️ Scraper → ✅ Validación → 💾 Redis → 🔔 Evento → 🧠 Backend → 🤖 ML → 📱 Frontend
```

**¡El sistema está completamente validado y sincronizado para funcionar como una unidad coherente!**