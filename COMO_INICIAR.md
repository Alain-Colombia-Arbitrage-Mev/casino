# 🚀 Cómo Iniciar el Sistema de Ruleta

## Script Principal

**Usa solo este comando para iniciar todo el sistema:**

```bash
python start_complete_system.py
```

## ¿Qué hace este script?

Inicia todos los componentes en el orden correcto:

1. **🔌 Verificación de conexiones** - Redis y PostgreSQL
2. **🕷️ Backend del Scraper** - Obtiene números de ruleta
3. **🧠 Backend Principal** - API y sistema de predicciones  
4. **🤖 Servicio Automático** - Procesa números y genera predicciones
5. **🌐 Frontend Web** - Interfaz de usuario (puerto 3002)
6. **🌐 Navegador** - Se abre automáticamente

## URLs de Acceso

- **Frontend:** http://localhost:3002
- **Backend API:** http://localhost:5000
- **Health Check:** http://localhost:5000/health

## Otros Scripts Útiles

- `start_backend_only.py` - Solo el backend principal
- `test_connections.py` - Probar conexiones a bases de datos
- `diagnose_redis.py` - Diagnosticar estado de Redis
- `test_system_order.py` - Verificar que todo funcione correctamente

## Detener el Sistema

Presiona **Ctrl+C** en la ventana del script principal para detener todos los servicios.

---

**¡Eso es todo!** Un solo comando inicia todo el sistema completo.