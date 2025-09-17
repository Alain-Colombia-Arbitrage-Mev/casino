# 🎰 AI Casino Roulette - Sistema de Automatización

Sistema completo de automatización para predicción de números de ruleta usando inteligencia artificial, con detección automática de números, análisis de patrones y predicciones en tiempo real.

## 🚀 Características Principales

- **🤖 Automatización Completa**: Detección automática de números jugados y generación de predicciones
- **🧠 Inteligencia Artificial**: Predicciones basadas en análisis de patrones y machine learning
- **📊 Dashboard en Tiempo Real**: Interfaz web con estadísticas, gráficos y monitoreo en vivo
- **🔄 Sincronización Multi-Base**: Redis para velocidad, PostgreSQL para persistencia
- **📈 Análisis Avanzado**: Estadísticas detalladas, patrones de frecuencia y tendencias
- **🎯 Predicciones por Grupos**: Números altos/bajos, pares/impares, rojos/negros, docenas y columnas

## 📋 Requisitos del Sistema

### Software Requerido
- **Python 3.8+**
- **PostgreSQL 12+**
- **Redis 6+**
- **Node.js 16+** (opcional, para desarrollo frontend)

### Dependencias Python
```bash
pip install -r backend/requirements.txt
```

Principales dependencias:
- Flask (API web)
- SQLAlchemy (ORM)
- Redis (cache y comunicación)
- Pandas (análisis de datos)
- NumPy (cálculos numéricos)
- Scikit-learn (machine learning)
- Requests (HTTP client)
- Psycopg2 (PostgreSQL driver)

## 🛠️ Instalación Rápida

### Opción 1: Inicio Automático (Recomendado)
```bash
# Clonar o descargar el proyecto
cd aicasino2

# Ejecutar script de inicio rápido
python quick_start.py
```

### Opción 2: Instalación Manual

1. **Configurar Base de Datos**
```bash
# Crear base de datos PostgreSQL
createdb aicasino

# Ejecutar migraciones
cd backend
python migrate.py
```

2. **Configurar Redis**
```bash
# Iniciar Redis (Linux/Mac)
redis-server

# Windows: descargar e instalar Redis
```

3. **Configurar Variables de Entorno**
```bash
# Copiar archivo de configuración
cp backend/.env.example backend/.env

# Editar configuración según tu entorno
nano backend/.env
```

4. **Instalar Dependencias**
```bash
cd backend
pip install -r requirements.txt
```

5. **Iniciar Servicios**
```bash
# Terminal 1: Backend
cd backend
python app.py

# Terminal 2: Automatización
cd backend
python automation_service.py

# Terminal 3: Frontend (opcional)
cd frontend
# Abrir index.html en navegador
```

## 🎮 Uso del Sistema

### 1. Acceso Web
- **Backend API**: http://localhost:5000
- **Frontend**: Abrir `frontend/index.html` en navegador
- **Panel de Automatización**: Pestaña "🤖 Automatización"

### 2. Endpoints Principales

#### Estado del Sistema
```bash
GET /health                    # Estado general
GET /api/automation/status     # Estado de automatización
GET /api/automation/logs       # Logs del sistema
```

#### Datos de Ruleta
```bash
GET /api/roulette/numbers      # Números jugados
GET /api/roulette/stats        # Estadísticas generales
GET /api/roulette/patterns     # Análisis de patrones
```

#### Predicciones de IA
```bash
POST /api/ai/predict           # Generar predicción
GET /api/ai/predictions        # Historial de predicciones
GET /api/ai/accuracy           # Precisión del modelo
```

#### Control de Automatización
```bash
POST /api/automation/start     # Iniciar automatización
POST /api/automation/stop      # Detener automatización
POST /api/automation/restart   # Reiniciar servicios
```

### 3. Panel de Control Web

El frontend incluye:
- **📊 Dashboard Principal**: Estadísticas y números recientes
- **🤖 Panel de Automatización**: Control y monitoreo en tiempo real
- **🧠 Predicciones de IA**: Visualización de predicciones y precisión
- **📈 Análisis Avanzado**: Gráficos de tendencias y patrones
- **⚙️ Configuración**: Ajustes del sistema

## 🔧 Configuración Avanzada

### Variables de Entorno (.env)
```bash
# Base de datos
DATABASE_URL=postgresql://user:pass@localhost:5432/aicasino
REDIS_HOST=localhost
REDIS_PORT=6379

# Automatización
AUTO_START_SCRAPER=true
AUTO_PREDICT=true
SCRAPER_INTERVAL=30

# IA y Predicciones
AI_MODEL_PATH=models/
PREDICTION_CONFIDENCE_THRESHOLD=0.7
MAX_PREDICTION_HISTORY=1000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/system.log
```

### Configuración del Scraper
```python
# backend/scrapping/scraper_config.py
SCRAPER_CONFIG = {
    "url": "https://casino-url.com/roulette",
    "interval": 30,  # segundos
    "timeout": 10,
    "max_retries": 3,
    "user_agent": "Mozilla/5.0...",
}
```

### Configuración de IA
```python
# backend/ai_config.py
AI_CONFIG = {
    "model_type": "ensemble",
    "features": ["number", "color", "parity", "range"],
    "lookback_window": 100,
    "prediction_groups": ["high_low", "even_odd", "red_black"],
    "confidence_threshold": 0.7
}
```

## 🧪 Pruebas y Validación

### Ejecutar Pruebas Completas
```bash
# Prueba completa del sistema
python test_automation_system.py

# Prueba con reporte detallado
python test_automation_system.py --save-report

# Prueba de componente específico
python test_automation_system.py --url http://localhost:5000
```

### Pruebas Individuales
```bash
# Probar conexión a base de datos
cd backend
python test_database.py

# Probar Redis
python test_redis_connection.py

# Probar scraper
python scrapping/test_scraper.py

# Probar predicciones de IA
python test_ai_predictions.py
```

## 📁 Estructura del Proyecto

```
aicasino2/
├── 📁 backend/                 # Servidor backend
│   ├── 📄 app.py              # API principal Flask
│   ├── 📄 automation_service.py # Servicio de automatización
│   ├── 📄 ai_predictor.py     # Motor de IA
│   ├── 📄 database.py         # Conexiones de BD
│   ├── 📁 scrapping/          # Módulos de scraping
│   ├── 📁 models/             # Modelos de datos
│   └── 📁 utils/              # Utilidades
├── 📁 frontend/               # Interfaz web
│   ├── 📄 index.html          # Página principal
│   ├── 📄 app.vue             # Aplicación Vue.js
│   ├── 📁 components/         # Componentes Vue
│   └── 📁 utils/              # Utilidades frontend
├── 📁 docs/                   # Documentación
├── 📄 quick_start.py          # Script de inicio rápido
├── 📄 test_automation_system.py # Pruebas del sistema
├── 📄 start_automation.py     # Iniciador de servicios
└── 📄 README.md               # Este archivo
```

## 🔄 Flujo de Automatización

1. **🕷️ Scraper** detecta nuevo número en el casino
2. **💾 Redis** almacena el número para comunicación rápida
3. **🗄️ PostgreSQL** persiste el número para análisis histórico
4. **🤖 Automation Service** detecta el cambio en Redis
5. **🧠 AI Predictor** analiza patrones y genera predicciones
6. **📊 Frontend** actualiza dashboard en tiempo real
7. **🔔 Notifications** alertas de nuevas predicciones

## 📊 Tipos de Predicciones

### Grupos de Números
- **Alto/Bajo**: 1-18 vs 19-36
- **Par/Impar**: Números pares vs impares
- **Rojo/Negro**: Colores de la ruleta
- **Docenas**: 1-12, 13-24, 25-36
- **Columnas**: Primera, segunda, tercera columna

### Métricas de Precisión
- **Accuracy**: Porcentaje de predicciones correctas
- **Confidence**: Nivel de confianza del modelo
- **Trend Analysis**: Análisis de tendencias temporales
- **Pattern Recognition**: Detección de patrones recurrentes

## 🚨 Solución de Problemas

### Problemas Comunes

#### Backend no inicia
```bash
# Verificar dependencias
pip install -r backend/requirements.txt

# Verificar base de datos
python backend/test_database.py

# Verificar logs
tail -f backend/logs/app.log
```

#### Redis no conecta
```bash
# Verificar servicio Redis
redis-cli ping

# Verificar configuración
cat backend/.env | grep REDIS
```

#### Scraper no funciona
```bash
# Probar scraper manualmente
cd backend/scrapping
python scraper_final.py --test

# Verificar logs del scraper
tail -f logs/scraper.log
```

#### Predicciones no se generan
```bash
# Verificar servicio de automatización
curl http://localhost:5000/api/automation/status

# Probar predicción manual
curl -X POST http://localhost:5000/api/ai/predict
```

### Logs del Sistema
```bash
# Logs principales
tail -f backend/logs/app.log          # Backend
tail -f backend/logs/automation.log   # Automatización
tail -f backend/logs/scraper.log      # Scraper
tail -f backend/logs/ai.log           # IA
```

## 🔒 Seguridad

### Configuración de Producción
- Cambiar `SECRET_KEY` en `.env`
- Usar HTTPS para conexiones web
- Configurar firewall para puertos específicos
- Implementar autenticación para API endpoints
- Usar variables de entorno para credenciales

### Backup y Recuperación
```bash
# Backup de base de datos
pg_dump aicasino > backup_$(date +%Y%m%d).sql

# Backup de configuración Redis
redis-cli --rdb backup_redis.rdb

# Restaurar base de datos
psql aicasino < backup_20231222.sql
```

## 📈 Monitoreo y Métricas

### Métricas del Sistema
- **Uptime**: Tiempo de actividad de servicios
- **Response Time**: Tiempo de respuesta de API
- **Prediction Accuracy**: Precisión de predicciones
- **Data Processing Rate**: Números procesados por minuto

### Alertas Configurables
- Caída de servicios
- Baja precisión de predicciones
- Errores de conexión a base de datos
- Memoria o CPU alta

## 🤝 Contribución

### Desarrollo
1. Fork del repositorio
2. Crear rama de feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

### Reportar Bugs
- Usar GitHub Issues
- Incluir logs relevantes
- Describir pasos para reproducir
- Especificar entorno (OS, Python version, etc.)

## 📞 Soporte

### Documentación Adicional
- `SISTEMA_AUTOMATIZACION_COMPLETO.md` - Guía técnica detallada
- `MIGRATION_GUIDE.md` - Guía de migración de datos
- `API_DOCUMENTATION.md` - Documentación completa de API

### Contacto
- **Issues**: GitHub Issues para bugs y features
- **Discusiones**: GitHub Discussions para preguntas generales
- **Email**: soporte@aicasino.com (si aplica)

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 🎯 Inicio Rápido - Resumen

```bash
# 1. Clonar proyecto
git clone <repository-url>
cd aicasino2

# 2. Ejecutar inicio automático
python quick_start.py

# 3. Acceder al sistema
# Backend: http://localhost:5000
# Frontend: Abrir frontend/index.html

# 4. Probar sistema
python test_automation_system.py
```

¡El sistema estará listo para usar en minutos! 🚀

---

*Desarrollado con ❤️ para automatización inteligente de predicciones de ruleta*