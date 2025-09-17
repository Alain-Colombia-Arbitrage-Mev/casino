# 🚀 GUÍA DE EJECUCIÓN - SISTEMA AI CASINO ULTRA OPTIMIZADO

## ⚡ EJECUCIÓN PASO A PASO

### **PASO 1: PREPARAR REDIS**
```bash
# Instalar Redis (Windows con Docker - RECOMENDADO)
docker run -d -p 6379:6379 --name redis-casino redis:alpine

# Verificar que Redis está corriendo
docker ps
# Debería mostrar: redis-casino running

# Test Redis
redis-cli ping
# Respuesta: PONG
```

### **PASO 2: PROBAR SISTEMA COMPLETO (RECOMENDADO)**
```bash
# 1. Ejecutar simulador para generar datos de prueba
python test_optimized_system.py

# Salida esperada:
# 🚀 INICIANDO SIMULACIÓN SCRAPER ULTRA OPTIMIZADO
# ✅ Redis conectado - Modo ULTRA OPTIMIZADO
# 🧹 Limpiando datos previos...
# 🎯 #1: 23 (red  ) Sector:4 - REDIS ULTRA OPTIMIZADO
# ...
# ✅ SIMULACIÓN COMPLETADA: 50 números guardados en Redis
```

### **PASO 3: BACKEND GO OPTIMIZADO**
```bash
# Ejecutar backend optimizado
cd backend
go run main_optimized.go

# Salida esperada:
# 🚀 AI Casino ULTRA OPTIMIZED Backend (Go + Redis Enriched)
# ✅ Redis conectado - Listo para datos ultra enriquecidos
# 🌐 Servidor ULTRA OPTIMIZADO corriendo en puerto 5002
```

### **PASO 4: VERIFICAR SISTEMA**
```bash
# Test ping
curl http://localhost:5002/ping
# Respuesta: {"message":"pong","status":"blazing_fast","version":"2.0_optimized"}

# Test estadísticas enriquecidas
curl http://localhost:5002/api/roulette/stats
# Respuesta: JSON con estadísticas completas

# Test features ML
curl http://localhost:5002/api/roulette/ml-features
# Respuesta: Features listos para Machine Learning
```

### **PASO 5: FRONTEND**
```bash
# Terminal separado
cd frontend
npm run dev

# Abrir navegador en: http://localhost:3000
```

### **PASO 6: SCRAPER REAL (PRODUCCIÓN)**
```bash
# Configurar .env con tus credenciales:
LOGIN_URL=https://tu-casino.com/login
ROULETTE_USERNAME=tu_usuario
ROULETTE_PASSWORD=tu_password
DASHBOARD_URL=https://tu-casino.com/roulette

# Ejecutar scraper real
python redis_scraper_optimized.py

# Salida esperada:
# 🚀 SCRAPER ULTRA RÁPIDO - SOLO REDIS OPTIMIZADO
# ✅ Sesión configurada - Modo Ultra Rápido
# 🆕 NUEVO NÚMERO: None → 17
# 🚀 Redis Ultra-Rápido: 17 (red) - Sector 2
```

## 🔄 ORDEN DE EJECUCIÓN RECOMENDADO

### **DESARROLLO/TESTING:**
1. `docker run redis` ← **Redis primero**
2. `python test_optimized_system.py` ← **Datos de prueba**
3. `go run main_optimized.go` ← **Backend Go**
4. `npm run dev` ← **Frontend**

### **PRODUCCIÓN:**
1. `docker run redis` ← **Redis primero**
2. `go run main_optimized.go` ← **Backend Go**
3. `python redis_scraper_optimized.py` ← **Scraper real**
4. `npm run dev` ← **Frontend**

## 🛠️ TROUBLESHOOTING

### **Error: Redis Connection Failed**
```bash
# Verificar Redis
docker ps | grep redis
redis-cli ping

# Si no responde, reiniciar:
docker restart redis-casino
```

### **Error: Go Build Failed**
```bash
# Instalar dependencias Go
cd backend
go mod init aicasino
go mod tidy
go get github.com/gin-gonic/gin
go get github.com/go-redis/redis/v8
```

### **Error: Puerto 5002 ocupado**
```bash
# Verificar qué usa el puerto
netstat -ano | findstr :5002

# Matar proceso si es necesario
taskkill /PID [numero_pid] /F
```

## 📊 VERIFICACIÓN DEL SISTEMA

### **1. Check Redis Data**
```bash
redis-cli keys "roulette:*" | head -10
# Debería mostrar keys como:
# roulette:latest
# roulette:history
# roulette:colors:red
# etc.
```

### **2. Check API Endpoints**
```bash
# Ping test
curl http://localhost:5002/ping

# Stats completas
curl -s http://localhost:5002/api/roulette/stats | jq .

# ML Features
curl -s http://localhost:5002/api/roulette/ml-features | jq .

# Health check
curl http://localhost:5002/api/system/health
```

### **3. Check Frontend**
- Abrir: `http://localhost:3000`
- Verificar que los números se muestran
- Verificar estadísticas en tiempo real
- Verificar que no hay números negativos

## 🔧 CONFIGURACIÓN AVANZADA

### **Optimizar Redis**
```bash
# En redis.conf o comando Docker:
docker run -d -p 6379:6379 \
  --name redis-casino \
  redis:alpine redis-server \
  --maxmemory 256mb \
  --maxmemory-policy allkeys-lru
```

### **Optimizar Go Backend**
```bash
# Compilar para producción
cd backend
go build -o casino-backend main_optimized.go

# Ejecutar binario optimizado
./casino-backend
```

### **Variables de Entorno (.env)**
```env
# Redis
REDIS_URL=redis://localhost:6379

# Scraper
LOGIN_URL=https://www.iamonstro.com.br/sistema/index.php
DASHBOARD_URL=https://www.iamonstro.com.br/sistema/dashboard.php?mesa=Lightning%20Roulette
ROULETTE_USERNAME=tu_usuario
ROULETTE_PASSWORD=tu_password
REFRESH_INTERVAL=8

# Performance
CACHE_TTL=180
WORKER_POOL_SIZE=6
PORT=5002
```

## 🚨 LOGS Y MONITOREO

### **Monitorear Redis en tiempo real**
```bash
# Ver todos los comandos
redis-cli monitor

# Ver memoria usage
redis-cli info memory

# Ver stats
redis-cli info stats
```

### **Logs del Backend Go**
El backend muestra logs en consola:
```
🚀 AI Casino ULTRA OPTIMIZED Backend
✅ Redis conectado
🌐 Servidor corriendo en puerto 5002
```

### **Logs del Scraper**
```
🚀 SCRAPER ULTRA RÁPIDO
✅ Sesión configurada
🆕 NUEVO NÚMERO: 23 → 17
📊 Total spins: 1847
```

## 💡 TIPS DE RENDIMIENTO

### **Para máximo rendimiento:**
1. **Redis**: Usar SSD para persistencia
2. **Go**: Compilar con `go build -ldflags="-s -w"`
3. **Frontend**: Usar `npm run build` para producción
4. **Scraper**: Ajustar `REFRESH_INTERVAL` según velocidad del casino

### **Monitoreo continuo:**
```bash
# Script de monitoreo
while true; do
  echo "=== $(date) ==="
  curl -s http://localhost:5002/api/system/health | jq .
  redis-cli get roulette:total_spins
  sleep 30
done
```

---

## ✅ **CHECKLIST DE EJECUCIÓN**

- [ ] Redis corriendo (`docker ps`)
- [ ] Test con `python test_optimized_system.py`
- [ ] Backend Go corriendo (`curl localhost:5002/ping`)
- [ ] Frontend accesible (`http://localhost:3000`)
- [ ] Scraper conectado y enviando datos
- [ ] No hay errores en consolas
- [ ] Datos aparecen en frontend en tiempo real

**¡Sistema listo para dominar la ruleta! 🎯🚀**