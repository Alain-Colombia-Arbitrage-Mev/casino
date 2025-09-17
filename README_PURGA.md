# Sistema de Purga Automática de Base de Datos

## 📋 Descripción
El sistema de purga automática mantiene la base de datos optimizada eliminando registros antiguos cada 48 horas, mientras preserva la integridad de los datos más recientes.

## 🚀 Características

### ✅ Purga Automática
- **Frecuencia**: Cada 48 horas automáticamente
- **Hilo independiente**: Se ejecuta en segundo plano sin afectar el rendimiento
- **Configuración inteligente**: Mantiene siempre un mínimo de registros funcionales

### ✅ Purga Manual
- **Control administrativo**: Ejecuta purgas bajo demanda desde la interfaz
- **Configuración personalizable**: Ajusta horas y registros mínimos a mantener
- **Vista previa**: Simula la purga antes de ejecutarla

### ✅ Monitoreo
- **Estado en tiempo real**: Consulta el estado actual de la base de datos
- **Métricas detalladas**: Registros totales, actividad reciente, antigüedad
- **Alertas automáticas**: Notifica cuando se necesita purga

## 🛠️ Configuración

### Backend
```python
# Configuración por defecto
MANTENER_HORAS = 48      # Eliminar registros > 48 horas
MANTENER_MINIMO = 50     # Siempre mantener mínimo 50 registros
FRECUENCIA_PURGA = 48    # Ejecutar cada 48 horas
```

### Tablas afectadas
- `roulette_numbers_individual`: Números individuales de la ruleta
- `roulette_history`: Historial de entradas agrupadas

## 📡 Endpoints API

### Estado de la Base de Datos
```http
GET /estado-db
```

**Respuesta:**
```json
{
  "success": true,
  "estado": {
    "total_registros": {
      "individual": 1250,
      "history": 320
    },
    "registro_mas_antiguo": "2024-01-15T10:30:00Z",
    "registro_mas_reciente": "2024-01-17T14:45:00Z",
    "registros_ultimas_48h": 180,
    "registros_ultimas_24h": 95,
    "horas_desde_mas_antiguo": 52.5,
    "necesita_purga": true
  }
}
```

### Purga Manual
```http
POST /purgar-db
Content-Type: application/json

{
  "mantener_horas": 48,
  "mantener_minimo": 50
}
```

**Respuesta:**
```json
{
  "success": true,
  "registros_eliminados": 350,
  "registros_antes": {
    "individual": 1250,
    "history": 320
  },
  "registros_despues": {
    "individual": 900,
    "history": 180
  },
  "fecha_limite": "2024-01-15T14:00:00Z"
}
```

## 🖥️ Interfaz de Usuario

### Acceso
1. Abrir la aplicación web
2. Hacer clic en "⚙️ Administración" en la barra superior
3. Ver el panel "Estado de la Base de Datos"

### Funciones disponibles
- **Actualizar Estado**: Consulta el estado actual de la DB
- **Vista Previa**: Simula una purga para ver qué se eliminaría
- **Ejecutar Purga**: Ejecuta purga manual con configuración personalizada
- **Monitoreo**: Ve registros totales, actividad reciente y fechas

### Indicadores de Estado
- 🟢 **Estado normal**: Registros < 36 horas de antigüedad
- 🟡 **Próxima purga pronto**: Registros entre 36-48 horas
- 🟠 **Necesita purga**: Registros > 48 horas de antigüedad

## ⚠️ Consideraciones de Seguridad

### Protecciones Implementadas
1. **Mínimo de registros**: Nunca elimina todos los registros
2. **Validación de parámetros**: Limita rangos de configuración
3. **Confirmación requerida**: Solicita confirmación antes de purgas manuales
4. **Logs detallados**: Registra todas las operaciones de purga

### Rangos Permitidos
- **Mantener horas**: 1-168 horas (1 hora a 1 semana)
- **Mantener mínimo**: 10-1000 registros

### Recomendaciones
- Mantener al menos 48 horas de datos para análisis de patrones
- Conservar mínimo 50 registros para funcionamiento de algoritmos
- Ejecutar purgas durante horarios de menor actividad
- Monitorear regularmente el estado de la base de datos

## 📊 Métricas y Monitoreo

### Información Mostrada
- **Total de registros**: Por tabla y total general
- **Actividad reciente**: Registros de últimas 24h y 48h
- **Fechas**: Registro más antiguo y más reciente
- **Porcentajes**: Distribución temporal de los datos

### Alertas
- Alerta naranja cuando se necesita purga (>48h)
- Indicador de estado del sistema automático
- Notificaciones de éxito/error en purgas manuales

## 🔧 Solución de Problemas

### Problemas Comunes

**P: La purga automática no se ejecuta**
- Verificar que el backend esté ejecutándose
- Revisar logs del servidor para errores
- Confirmar que el hilo de purga se inició correctamente

**P: Error al ejecutar purga manual**
- Verificar conexión a Supabase
- Revisar permisos de eliminación en la base de datos
- Comprobar que los parámetros estén en rangos válidos

**P: No se muestran datos en el panel**
- Verificar conexión a internet
- Confirmar que el backend esté accesible
- Revisar configuración de CORS

### Logs Importantes
```bash
# Inicio del sistema de purga
✅ Sistema de purga automática iniciado correctamente

# Purga automática programada
🔄 Sistema de purga automática iniciado
Próxima purga programada en 48 horas: 2024-01-19 14:30:00

# Ejecución de purga
========== INICIANDO PURGA DE BASE DE DATOS ==========
✓ Eliminados 350 registros antiguos de roulette_numbers_individual
✅ PURGA COMPLETADA
```

## 🚦 Estados del Sistema

### Normal (🟢)
- Registros más antiguos < 36 horas
- Sistema funcionando correctamente
- No requiere acción

### Advertencia (🟡)
- Registros más antiguos entre 36-48 horas
- Próxima purga automática pronto
- Monitoreo recomendado

### Acción Requerida (🟠)
- Registros más antiguos > 48 horas
- Se recomienda purga manual
- Sistema automático debería ejecutarse pronto

## 📞 Soporte

### Contacto
- Para problemas técnicos: Revisar logs del servidor
- Para configuración: Consultar este documento
- Para desarrollo: Revisar código fuente en `/backend/app.py`

### Archivos Relevantes
- Backend: `backend/app.py` (líneas 1946-2274)
- Frontend: `frontend/components/PurgaBaseDatos.vue`
- Utilidades: `frontend/utils/supabase.ts` (funciones de purga)
- Configuración: `frontend/app.vue` (panel de administración) 