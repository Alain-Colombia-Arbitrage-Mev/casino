# Sistema de Automatización Completo - AI Casino

## 🎯 Descripción General

Este sistema integra completamente el scraper, backend, predicciones de IA y frontend para crear un flujo automático de detección, análisis y predicción de números de ruleta.

## 🔄 Flujo de Automatización

```
1. SCRAPER (scraper_final.py)
   ↓ Detecta números nuevos
   ↓ Guarda en Redis + PostgreSQL
   
2. SERVICIO DE AUTOMATIZACIÓN (automation_service.py)
   ↓ Monitorea Redis cada 5 segundos
   ↓ Detecta cambios en números
   ↓ Verifica predicciones pendientes
   ↓ Genera nuevas predicciones automáticamente
   
3. BACKEND (app.py)
   ↓ Proporciona APIs para el frontend
   ↓ Maneja estadísticas y resultados
   
4. FRONTEND (AutomationPanel.vue)
   ↓ Muestra estado en tiempo real
   ↓ Permite control manual del sistema
   ↓ Visualiza logs y estadísticas
```

## 🚀 Inicio Rápido

### Opción 1: Script de Inicio Automático
```bash
# Iniciar sistema completo (backend + automatización)
python start_automation.py

# Iniciar con frontend incluido
python start_automation.py --frontend

# Solo backend para pruebas
python start_automation.py --backend-only
```

### Opción 2: Inicio Manual
```bash
# Terminal 1: Backend
cd backend
python app.py

# Terminal 2: Servicio de Automatización
cd backend
python automation_service.py

# Terminal 3: Frontend (opcional)
cd frontend
npm run dev
```

## 🔧 Configuración

### Variables de Entorno (.env)
```env
# Configuración del Scraper
LOGIN_URL=https://www.iamonstro.com.br/sistema/index.php
DASHBOARD_URL=https://www.iamonstro.com.br/sistema/dashboard.php?mesa=Lightning%20Roulette
ROULETTE_USERNAME=tu_usuario
ROULETTE_PASSWORD=tu_password
REFRESH_INTERVAL=10

# Configuración de Automatización
AUTOMATION_CHECK_INTERVAL=5
AUTO_PREDICT=true
SCRAPER_ENABLED=true

# Base de Datos
DATABASE_PUBLIC_URL=postgresql://...
REDIS_PUBLIC_URL=redis://...
```

## 📊 Componentes del Sistema

### 1. Scraper Final (`backend/scrapping/scraper_final.py`)
- **Función**: Detecta números nuevos de la ruleta
- **Características**:
  - Login único sin repetición
  - Sincronización Redis + PostgreSQL
  - Limpieza automática de datos antiguos
  - Detección de cambios en tiempo real

### 2. Servicio de Automatización (`backend/automation_service.py`)
- **Función**: Coordina todo el flujo automático
- **Características**:
  - Monitoreo continuo de Redis
  - Verificación automática de predicciones
  - Generación automática de nuevas predicciones
  - Gestión del proceso del scraper
  - Logs detallados para debugging

### 3. Backend API (`backend/app.py`)
- **Función**: API REST para el frontend
- **Endpoints nuevos**:
  - `GET /api/automation/status` - Estado del sistema
  - `POST /api/automation/start` - Iniciar automatización
  - `POST /api/automation/stop` - Detener automatización
  - `GET /api/automation/logs` - Logs del sistema
  - `GET /api/automation/notifications` - Eventos recientes
  - `POST /api/automation/scraper/restart` - Reiniciar scraper

### 4. Panel de Automatización (`frontend/components/AutomationPanel.vue`)
- **Función**: Interfaz de control y monitoreo
- **Características**:
  - Control de inicio/parada del sistema
  - Monitoreo en tiempo real del estado
  - Visualización de logs en tiempo real
  - Estadísticas de procesamiento
  - Notificaciones de eventos importantes

## 🎮 Uso del Sistema

### 1. Acceso al Panel de Automatización
1. Abrir el frontend: `http://localhost:3000`
2. Ir a la pestaña "🤖 Automatización"
3. Ver el estado actual del sistema

### 2. Control del Sistema
- **Iniciar**: Botón "Iniciar Automatización"
- **Detener**: Botón "Detener Automatización"
- **Reiniciar Scraper**: Botón "Reiniciar Scraper"

### 3. Monitoreo
- **Estado en Tiempo Real**: Indicadores visuales
- **Logs**: Consola en tiempo real con eventos
- **Estadísticas**: Números procesados, predicciones verificadas
- **Notificaciones**: Eventos importantes del sistema

## 📈 Estadísticas y Métricas

### Métricas del Sistema
- **Números Procesados**: Total de números detectados
- **Predicciones Verificadas**: Predicciones evaluadas automáticamente
- **Último Número**: Número más reciente detectado
- **Intervalo**: Frecuencia de verificación

### Métricas de Rendimiento
- **Estado del Scraper**: Running/Stopped
- **PID del Scraper**: Identificador del proceso
- **Monitoreo Activo**: Estado del loop de monitoreo
- **Predicciones Automáticas**: Habilitado/Deshabilitado

## 🔍 Debugging y Logs

### Tipos de Logs
- **INFO**: Eventos normales del sistema
- **WARNING**: Advertencias no críticas
- **ERROR**: Errores que requieren atención

### Códigos de Estado
- **🆕**: Nuevo número detectado
- **✅**: Operación exitosa
- **❌**: Error en operación
- **🔄**: Proceso de reinicio
- **🎯**: Nueva predicción generada

## 🛠️ Solución de Problemas

### Problema: Scraper no inicia
**Solución**:
1. Verificar credenciales en `.env`
2. Comprobar conectividad a internet
3. Revisar logs del sistema
4. Reiniciar el scraper manualmente

### Problema: No se detectan números nuevos
**Solución**:
1. Verificar conexión a Redis
2. Comprobar que el scraper esté ejecutándose
3. Revisar logs para errores
4. Verificar la URL del dashboard

### Problema: Predicciones no se generan
**Solución**:
1. Verificar `AUTO_PREDICT=true` en configuración
2. Comprobar que hay suficientes números históricos
3. Revisar logs del predictor de IA
4. Verificar conexión a base de datos

## 📋 Checklist de Verificación

### Antes de Iniciar
- [ ] Variables de entorno configuradas
- [ ] Redis funcionando
- [ ] PostgreSQL funcionando
- [ ] Credenciales de scraper válidas
- [ ] Dependencias instaladas

### Durante la Operación
- [ ] Scraper en estado "Running"
- [ ] Números siendo detectados
- [ ] Predicciones generándose automáticamente
- [ ] Logs sin errores críticos
- [ ] Frontend mostrando datos actualizados

### Mantenimiento Regular
- [ ] Revisar logs semanalmente
- [ ] Limpiar datos antiguos si es necesario
- [ ] Verificar rendimiento del sistema
- [ ] Actualizar credenciales si expiran

## 🔮 Próximas Mejoras

### Funcionalidades Planificadas
- [ ] Alertas por email/SMS
- [ ] Dashboard de métricas avanzadas
- [ ] Backup automático de datos
- [ ] API webhooks para integraciones
- [ ] Modo de simulación/testing

### Optimizaciones
- [ ] Reducir latencia de detección
- [ ] Mejorar precisión de predicciones
- [ ] Optimizar uso de memoria
- [ ] Implementar cache inteligente

## 📞 Soporte

### Logs Importantes
- **Automation Service**: `automation:logs` en Redis
- **Scraper**: `backend/scrapping/roulette_data/roulette_scraper.log`
- **Backend**: Consola del servidor Flask

### Comandos de Diagnóstico
```bash
# Verificar estado de Redis
redis-cli ping

# Verificar conexión a PostgreSQL
python -c "from backend.database import db_manager; print(db_manager.get_database_status())"

# Ver logs del scraper
tail -f backend/scrapping/roulette_data/roulette_scraper.log
```

---

## 🎉 ¡Sistema Listo!

El sistema de automatización está completamente integrado y listo para usar. El flujo automático detectará números, verificará predicciones y generará nuevas predicciones sin intervención manual.

**¡Disfruta del poder de la automatización inteligente!** 🚀