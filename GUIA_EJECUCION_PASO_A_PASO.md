# 🚀 Guía de Ejecución Paso a Paso - AI Casino Roulette

Esta guía te llevará a través de la secuencia correcta para ejecutar el sistema completo de automatización.

## 📋 Pre-requisitos

Antes de comenzar, asegúrate de tener instalado:
- **Python 3.8+**
- **PostgreSQL 12+** 
- **Redis 6+**
- **Git** (opcional)

## 🔧 PASO 1: Verificación Inicial del Sistema

Primero, verifica que todos los archivos estén en su lugar:

```bash
# Ejecutar verificación completa
python verify_system.py
```

**Resultado esperado:** 
- ✅ Tasa de éxito > 90%
- ⚠️ Algunas advertencias son normales (se corregirán automáticamente)
- ❌ Si hay errores críticos, revisa la estructura de archivos

## 🗄️ PASO 2: Configuración de Base de Datos PostgreSQL

### 2.1 Crear Base de Datos
```bash
# Conectar a PostgreSQL como superusuario
psql -U postgres

# Crear base de datos
CREATE DATABASE aicasino;

# Crear usuario (opcional)
CREATE USER aicasino_user WITH PASSWORD 'tu_password_aqui';
GRANT ALL PRIVILEGES ON DATABASE aicasino TO aicasino_user;

# Salir de psql
\q
```

### 2.2 Ejecutar Migraciones
```bash
# Ir al directorio backend
cd backend

# Ejecutar script de migración
python migrate.py
```

**Resultado esperado:**
- ✅ Tablas creadas exitosamente
- ✅ Índices creados
- ✅ Conexión a base de datos verificada

## 🔴 PASO 3: Configuración de Redis

### 3.1 Iniciar Redis Server

**En Windows:**
```bash
# Si Redis está instalado como servicio
net start redis

# O ejecutar manualmente
redis-server
```

**En Linux/Mac:**
```bash
# Iniciar Redis
redis-server

# O como servicio
sudo systemctl start redis
```

### 3.2 Verificar Redis
```bash
# Probar conexión
redis-cli ping
# Debe responder: PONG
```

## ⚙️ PASO 4: Configuración de Variables de Entorno

### 4.1 Configurar archivo .env
```bash
# Ir al directorio backend
cd backend

# Crear archivo .env (si no existe)
cp .env.example .env

# O crear manualmente
nano .env
```

### 4.2 Contenido del archivo .env
```bash
# Configuración de base de datos
DATABASE_URL=postgresql://username:password@localhost:5432/aicasino

# Configuración de Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Configuración de Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=tu-clave-secreta-muy-segura-aqui

# Configuración de automatización
AUTO_START_SCRAPER=true
AUTO_PREDICT=true
SCRAPER_INTERVAL=30

# Configuración de IA
AI_MODEL_PATH=models/
PREDICTION_CONFIDENCE_THRESHOLD=0.7
```

**⚠️ IMPORTANTE:** Reemplaza los valores con tus credenciales reales.

## 📦 PASO 5: Instalación de Dependencias

```bash
# Asegúrate de estar en el directorio backend
cd backend

# Instalar dependencias de Python
pip install -r requirements.txt
```

**Resultado esperado:**
- ✅ Todas las dependencias instaladas sin errores
- ⚠️ Si hay conflictos, usa un entorno virtual

### 5.1 Crear Entorno Virtual (Recomendado)
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🧪 PASO 6: Pruebas de Conectividad

### 6.1 Probar Conexión a PostgreSQL
```bash
cd backend
python -c "
import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    print('✅ PostgreSQL: Conexión exitosa')
    conn.close()
except Exception as e:
    print(f'❌ PostgreSQL: Error - {e}')
"
```

### 6.2 Probar Conexión a Redis
```bash
cd backend
python -c "
import redis
import os
from dotenv import load_dotenv
load_dotenv()
try:
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=int(os.getenv('REDIS_PORT', 6379)))
    r.ping()
    print('✅ Redis: Conexión exitosa')
except Exception as e:
    print(f'❌ Redis: Error - {e}')
"
```

## 🚀 PASO 7: Iniciar el Sistema (SECUENCIA CRÍTICA)

### 7.1 OPCIÓN A: Inicio Automático (Recomendado)
```bash
# Desde el directorio raíz del proyecto
python quick_start.py
```

**Esto iniciará automáticamente:**
1. ✅ Verificaciones del sistema
2. ✅ Configuración de entorno
3. ✅ Servidor backend (Puerto 5000)
4. ✅ Servicio de automatización
5. ✅ Monitoreo en tiempo real

### 7.2 OPCIÓN B: Inicio Manual (Paso a Paso)

**Terminal 1 - Backend API:**
```bash
cd backend
python app.py
```
**Esperar hasta ver:** `* Running on http://127.0.0.1:5000`

**Terminal 2 - Servicio de Automatización:**
```bash
cd backend
python automation_service.py
```
**Esperar hasta ver:** `Automation service started`

**Terminal 3 - Scraper (Opcional para testing):**
```bash
cd backend/scrapping
python scraper_final.py
```

## 🌐 PASO 8: Verificar el Frontend

### 8.1 Abrir Interfaz Web
```bash
# Abrir en navegador
start frontend/index.html
# O en Linux/Mac:
open frontend/index.html
```

### 8.2 Verificar Funcionalidad
1. **Dashboard Principal** - Debe mostrar estadísticas
2. **Pestaña Automatización** - Estado de servicios
3. **Pestaña Predicciones IA** - Panel de predicciones
4. **Pestaña Análisis** - Gráficos y estadísticas

## 🧪 PASO 9: Ejecutar Pruebas del Sistema

```bash
# Prueba completa del sistema
python test_automation_system.py

# Prueba con reporte detallado
python test_automation_system.py --save-report
```

**Resultado esperado:**
- ✅ Todas las pruebas pasan (100% éxito)
- ⚠️ Si hay fallos, revisar logs y configuración

## 📊 PASO 10: Monitoreo y Verificación

### 10.1 Verificar APIs
```bash
# Probar endpoint de salud
curl http://localhost:5000/health

# Probar estado de automatización
curl http://localhost:5000/api/automation/status

# Probar números de ruleta
curl http://localhost:5000/api/roulette/numbers?limit=5
```

### 10.2 Verificar Logs
```bash
# Ver logs del backend
tail -f backend/logs/app.log

# Ver logs de automatización
tail -f backend/logs/automation.log

# Ver logs del scraper
tail -f backend/logs/scraper.log
```

## 🔄 PASO 11: Flujo de Automatización Completo

Una vez que todo esté funcionando, el flujo será:

1. **🕷️ Scraper** detecta nuevo número → guarda en Redis/PostgreSQL
2. **🤖 Automation Service** detecta cambio → verifica predicciones → genera nuevas
3. **📊 Frontend** actualiza dashboard en tiempo real
4. **🧠 AI Predictor** analiza patrones → mejora predicciones

### 11.1 Probar Flujo Manual
```bash
# Insertar número de prueba
curl -X POST http://localhost:5000/api/roulette/add-number \
  -H "Content-Type: application/json" \
  -d '{"number": 17}'

# Verificar que se procesó
curl http://localhost:5000/api/automation/logs
```

## 🚨 Solución de Problemas Comunes

### Error: "Puerto 5000 en uso"
```bash
# Encontrar proceso usando el puerto
netstat -ano | findstr :5000
# Terminar proceso
taskkill /PID <PID> /F
```

### Error: "No se puede conectar a PostgreSQL"
```bash
# Verificar que PostgreSQL esté ejecutándose
pg_isready -h localhost -p 5432

# Verificar credenciales en .env
cat backend/.env | grep DATABASE_URL
```

### Error: "Redis no disponible"
```bash
# Verificar Redis
redis-cli ping

# Reiniciar Redis
redis-server --daemonize yes
```

### Error: "Módulo no encontrado"
```bash
# Reinstalar dependencias
cd backend
pip install -r requirements.txt --force-reinstall
```

## 📈 Monitoreo Continuo

### Métricas Clave a Monitorear:
- **Uptime de servicios** (Backend, Automatización, Scraper)
- **Números procesados por minuto**
- **Precisión de predicciones**
- **Tiempo de respuesta de API**
- **Uso de memoria y CPU**

### Comandos de Monitoreo:
```bash
# Estado general
curl http://localhost:5000/api/automation/status

# Estadísticas de rendimiento
curl http://localhost:5000/api/system/stats

# Logs en tiempo real
tail -f backend/logs/*.log
```

## 🔄 Reinicio del Sistema

### Reinicio Completo:
```bash
# Detener todos los servicios (Ctrl+C en cada terminal)

# Reiniciar con script automático
python quick_start.py

# O reiniciar manualmente siguiendo PASO 7.2
```

### Reinicio Solo de Automatización:
```bash
curl -X POST http://localhost:5000/api/automation/restart
```

## 📞 Soporte y Debugging

### Archivos de Log Importantes:
- `backend/logs/app.log` - Backend principal
- `backend/logs/automation.log` - Servicio de automatización
- `backend/logs/scraper.log` - Scraper de números
- `backend/logs/ai.log` - Predicciones de IA

### Comandos de Debugging:
```bash
# Verificar estado completo
python verify_system.py

# Probar sistema completo
python test_automation_system.py

# Limpiar datos de prueba
python -c "
import redis
r = redis.Redis(decode_responses=True)
r.flushdb()
print('Redis limpiado')
"
```

---

## ✅ Lista de Verificación Final

Antes de considerar el sistema completamente operativo:

- [ ] PostgreSQL ejecutándose y accesible
- [ ] Redis ejecutándose y accesible  
- [ ] Variables de entorno configuradas correctamente
- [ ] Dependencias de Python instaladas
- [ ] Backend API respondiendo en puerto 5000
- [ ] Servicio de automatización ejecutándose
- [ ] Frontend accesible y funcional
- [ ] Pruebas del sistema pasando (>90% éxito)
- [ ] Logs mostrando actividad normal
- [ ] Flujo de automatización funcionando

**🎉 ¡Una vez completada esta lista, tu sistema AI Casino Roulette estará completamente operativo!**

---

*Para soporte adicional, consulta los archivos de documentación técnica o revisa los logs del sistema.*