# 🎰 AI CASINO - Sistema Ultra Optimizado

## 🚀 EJECUCIÓN RÁPIDA

### **Opción 1: Inicio Automático (Recomendado)**
```bash
python start_ai_casino.py
```

### **Opción 2: Docker Compose**
```bash
docker-compose up -d
```

### **Opción 3: Manual**
```bash
# 1. Redis
docker run -d -p 6379:6379 --name redis-casino redis:alpine

# 2. Backend
cd backend
go run main_optimized.go adaptive_ml.go

# 3. Frontend
cd frontend
npm run dev
```

## 🧠 CARACTERÍSTICAS

- **ML Adaptativo**: Aprende nuevas estrategias automáticamente
- **Redis Ultra-Optimizado**: Datos ricos para predicciones
- **Go Backend**: API ultra-rápida con ML paralelo
- **Sistema Dockerizado**: Despliegue en contenedores

## 🔧 UTILIDADES

### **Purgar Redis**
```bash
# Ver datos actuales
python redis_purge.py --action summary

# Backup
python redis_purge.py --action backup

# Purgar todo
python redis_purge.py --action purge-all --confirm
```

## 📡 ENDPOINTS

- **Frontend**: http://localhost:3000
- **API**: http://localhost:5002/api/roulette/stats
- **ML Adaptativo**: http://localhost:5002/api/ai/predict-adaptive

## 📁 ESTRUCTURA

```
aicasino2/
├── redis_scraper_optimized.py     # Scraper ultra-rápido
├── backend/
│   ├── main_optimized.go          # API Go optimizada
│   └── adaptive_ml.go             # ML que aprende
├── frontend/                       # Vue.js frontend
├── clickercasino/                  # (Preservado)
├── docker-compose.yml             # Orquestación Docker
├── redis_purge.py                 # Limpieza Redis
└── start_ai_casino.py             # Inicio automático
```

**🎯 Sistema listo para dominar la ruleta con IA adaptativa!**