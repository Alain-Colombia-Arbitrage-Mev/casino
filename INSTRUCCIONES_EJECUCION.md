# 🚀 Instrucciones de Ejecución - Frontend y Backend

## 🎯 Método Más Fácil (Recomendado)

### ⚡ Ejecutar Todo con Un Solo Comando

```bash
# 1. Migrar (solo la primera vez)
npm run migrate

# 2. Ejecutar frontend y backend juntos
npm run start:all
```

**¡Eso es todo!** El comando `start:all` ejecutará automáticamente:
- Backend en `http://localhost:5000`
- Frontend en `http://localhost:3000`

---

## 📋 Método Paso a Paso (Alternativo)

### 1️⃣ Ejecutar la Migración (Solo la primera vez)

```bash
# Opción A: Usar npm script
npm run migrate

# Opción B: Manual
cd backend && python migrate.py
```

### 2️⃣ Instalar Dependencias (Solo la primera vez)

```bash
# Instalar todo de una vez
npm run install:all
```

### 3️⃣ Ejecutar Backend y Frontend

#### **Opción A: Un Solo Comando (Recomendado)**
```bash
npm run start:all
```

#### **Opción B: Por Separado**
```bash
# Terminal 1 - Backend
npm run start:backend

# Terminal 2 - Frontend
npm run start:frontend
```

#### **Opción C: Manual**
```bash
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## 🔧 Comandos Específicos por Tecnología

### Si el Frontend es Nuxt 3:
```bash
cd frontend
npm run dev
```

### Si el Frontend es Next.js:
```bash
cd frontend
npm run dev
```

### Si el Frontend es Vue CLI:
```bash
cd frontend
npm run serve
```

### Si el Frontend es Vite:
```bash
cd frontend
npm run dev
```

## 📱 Verificar que Todo Funciona

### 1. Verificar Backend
```bash
# En una terminal, probar la API
curl http://localhost:5000/health

# Debería responder algo como:
# {"status": "healthy", "database": "connected", "redis": "connected"}
```

### 2. Verificar Frontend
- Abrir navegador en `http://localhost:3000` (o el puerto que muestre)
- Verificar que la aplicación carga correctamente
- Probar insertar un número de ruleta
- Verificar que las estadísticas se muestran

## 🐛 Solución de Problemas Comunes

### Error: "Port 5000 already in use"
```bash
# Encontrar qué proceso usa el puerto
lsof -i :5000

# Matar el proceso (reemplaza PID con el número real)
kill -9 PID

# O usar otro puerto
PORT=5001 python app.py
```

### Error: "Module not found" en Backend
```bash
cd backend
pip install -r requirements.txt
```

### Error: "Command not found: npm" en Frontend
```bash
# Instalar Node.js desde https://nodejs.org/
# O usar el gestor de paquetes de tu sistema:

# Ubuntu/Debian:
sudo apt install nodejs npm

# macOS:
brew install node

# Windows: Descargar desde nodejs.org
```

### Error: "Redis connection failed"
- Redis es opcional, la aplicación funcionará sin él
- Verificar que las credenciales en `.env` son correctas
- El sistema continuará funcionando solo con PostgreSQL

### Error: "PostgreSQL connection failed"
```bash
# Verificar las credenciales en backend/.env
cat backend/.env

# Asegurarse de que Railway PostgreSQL está activo
# Verificar conectividad de red
```

## 📂 Estructura de Directorios

```
tu-proyecto/
├── backend/
│   ├── app.py              # ← Servidor Flask (puerto 5000)
│   ├── database.py         # ← Gestor de base de datos
│   ├── requirements.txt    # ← Dependencias Python
│   └── .env               # ← Variables de entorno
├── frontend/
│   ├── package.json       # ← Dependencias Node.js
│   ├── nuxt.config.ts     # ← Configuración (si es Nuxt)
│   └── utils/
│       └── supabase.ts    # ← Nueva implementación API
└── INSTRUCCIONES_EJECUCION.md
```

## 🔄 Flujo de Desarrollo Típico

### Desarrollo Diario:
```bash
# Método más fácil - Un solo comando
npm run start:all

# O por separado si prefieres:
# Terminal 1 - Backend
npm run start:backend

# Terminal 2 - Frontend
npm run start:frontend

# Terminal 3 - Pruebas (opcional)
npm run test
```

### Después de Cambios en Backend:
```bash
# Reiniciar servidor backend
Ctrl+C  # Detener servidor
python app.py  # Reiniciar
```

### Después de Cambios en Frontend:
- El servidor de desarrollo se recarga automáticamente
- Si no, reiniciar con `Ctrl+C` y `npm run dev`

## 🌐 URLs de Acceso

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Frontend | http://localhost:3000 | Interfaz de usuario |
| Backend API | http://localhost:5000 | API REST |
| Health Check | http://localhost:5000/health | Estado del sistema |
| API Docs | http://localhost:5000 | Documentación de endpoints |

## 📊 Monitoreo en Tiempo Real

### Ver Logs del Backend:
```bash
cd backend
python app.py
# Los logs aparecerán en la terminal
```

### Ver Logs del Frontend:
```bash
cd frontend
npm run dev
# Los logs aparecerán en la terminal
# También revisar la consola del navegador (F12)
```

## 🔧 Variables de Entorno Importantes

### Backend (.env):
```env
DATABASE_URL=postgresql://postgres:JqPnbywtvvZyINvBFikSRYdKqGmtTFFj@postgres.railway.internal:5432/railway
REDIS_URL=redis://default:kuBKgwJxPrMoMOWqpobsGZIcpgnOFwoW@redis.railway.internal:6379
FLASK_ENV=development
PORT=5000
```

### Frontend (si aplica):
```env
NUXT_PUBLIC_API_BASE=http://localhost:5000
```

## 🚀 Comandos Rápidos

### Inicio Rápido (2 comandos):
```bash
# Terminal 1
cd backend && python app.py

# Terminal 2  
cd frontend && npm run dev
```

### Reinicio Completo:
```bash
# Detener ambos servidores (Ctrl+C en cada terminal)
# Luego ejecutar inicio rápido de nuevo
```

### Verificación Rápida:
```bash
curl http://localhost:5000/health && echo "Backend OK"
curl http://localhost:3000 && echo "Frontend OK"
```

---

## 🎯 ¡Listo para Usar!

Después de seguir estos pasos tendrás:
- ✅ Backend corriendo en puerto 5000
- ✅ Frontend corriendo en puerto 3000  
- ✅ Base de datos PostgreSQL conectada
- ✅ Redis cache funcionando (opcional)
- ✅ Sistema completo operativo

**¡Tu aplicación de roulette analyzer estará lista para usar!** 🎰