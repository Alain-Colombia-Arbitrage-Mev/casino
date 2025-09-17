# Sistema Integrado de Sectores y Procesamiento de Números

## 📋 Descripción General

Este documento describe las mejoras implementadas en el sistema de análisis de ruleta para manejar correctamente las tablas de Supabase existentes y proporcionar funcionalidades avanzadas de gestión de sectores personalizados.

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────────┐
│                    SISTEMA INTEGRADO                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  NumberProcessor │  │  SectorManager  │  │ Victory Trainer │  │
│  │                 │  │                 │  │                 │  │
│  │ • Comas         │  │ • Sectores      │  │ • Entrenamiento │  │
│  │ • Validación    │  │ • Aciertos      │  │ • ML Avanzado   │  │
│  │ • Colores       │  │ • Estadísticas  │  │ • Victorias     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│           │                      │                      │       │
│           └──────────────────────┼──────────────────────┘       │
│                                  │                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  SUPABASE INTEGRATION                   │   │
│  │                                                          │   │
│  │ • roulette_history          • sectores_definiciones     │   │
│  │ • roulette_numbers_individual • sectores_conteos        │   │
│  │ • victory_training_data     • analyzer_state           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    REST API ENDPOINTS                   │   │
│  │                                                          │   │
│  │ • /sectores                 • /sectores/crear           │   │
│  │ • /sectores/estadisticas    • /sectores/eliminar        │   │
│  │ • /sectores/analizar-numero • /entrenar-con-victorias   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Componentes Detallados

### 1. NumberProcessor (`number_processor.py`)

#### Funcionalidades
- **Procesamiento de múltiples formatos**: Maneja números separados por comas, espacios, guiones
- **Validación automática**: Verifica rangos válidos (0-36)
- **Detección de colores**: Asigna automáticamente Rojo/Negro/Verde
- **Integración con Supabase**: Prepara datos para inserción en `roulette_numbers_individual`

#### Ejemplos de Uso

```python
from number_processor import create_number_processor

processor = create_number_processor()

# Procesar números con comas
resultado = processor.procesar_cadena_numeros("23, 14, 5, 32")
# resultado.numeros_validos = [NumeroProcessed(valor=23, color='Rojo'), ...]

# Función rápida
numeros = procesar_numeros_rapido("12, 25, 3")
# numeros = [12, 25, 3]
```

#### Formatos Soportados
- `"23, 14, 5, 32"` - Comas con espacios
- `"23,14,5,32"` - Comas sin espacios  
- `"23 14 5 32"` - Espacios
- `"23-14-5-32"` - Guiones
- `"23|14|5|32"` - Pipes
- `"salió el 23, después 14"` - Texto mixto

### 2. SectorManager (`sector_manager.py`)

#### Funcionalidades
- **Sectores predefinidos**: 12 sectores clásicos (Rojos, Negros, Docenas, etc.)
- **Sectores personalizados**: Creación dinámica de sectores
- **Seguimiento de aciertos**: Conteo automático por sector
- **Persistencia**: Almacenamiento en Supabase
- **Estadísticas**: Análisis de rendimiento por sector

#### Sectores Predefinidos

| Sector | Números | Descripción |
|--------|---------|-------------|
| `Rojos` | 1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36 | Números rojos |
| `Negros` | 2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35 | Números negros |
| `Primera_Docena` | 1-12 | Primera docena |
| `Segunda_Docena` | 13-24 | Segunda docena |
| `Tercera_Docena` | 25-36 | Tercera docena |
| `Vecinos_Cero` | 32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26 | Orden en la rueda |
| `Tier` | 5,8,10,11,13,16,23,24,27,30,33,36 | Sector Tier |
| `Orphelins` | 1,6,9,14,17,20,31,34 | Huérfanos |

#### Ejemplos de Uso

```python
from sector_manager import create_sector_manager

manager = create_sector_manager(supabase_client)

# Crear sector personalizado
manager.crear_sector("Mi_Sector", [1, 5, 9, 13, 17, 21])

# Verificar aciertos
sectores_acertados = manager.verificar_acierto_sectores(5)
# Retorna: ['Rojos', 'Impares', 'Mi_Sector']

# Obtener estadísticas
stats = manager.obtener_estadisticas_sectores()
```

### 3. Integración con Victory Trainer

El sistema se integra con el Victory Trainer existente para:
- **Registro de victorias por sector**: Detecta automáticamente aciertos en sectores
- **Entrenamiento especializado**: Usa datos de sectores exitosos
- **Métricas avanzadas**: Análisis de rendimiento por tipo de sector

## 📊 Estructura de Base de Datos

### Tablas Utilizadas

#### `roulette_history`
```sql
CREATE TABLE roulette_history (
    id SERIAL PRIMARY KEY,
    numbers_string TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `roulette_numbers_individual`
```sql
CREATE TABLE roulette_numbers_individual (
    id SERIAL PRIMARY KEY,
    history_entry_id INTEGER REFERENCES roulette_history(id),
    number_value INTEGER CHECK (number_value >= 0 AND number_value <= 36),
    color TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `sectores_definiciones` *(Nueva)*
```sql
CREATE TABLE sectores_definiciones (
    id SERIAL PRIMARY KEY,
    nombre_sector TEXT NOT NULL UNIQUE,
    numeros TEXT NOT NULL, -- CSV: "1,2,3,4,5"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `sectores_conteos` *(Nueva)*
```sql
CREATE TABLE sectores_conteos (
    id SERIAL PRIMARY KEY,
    id_estado_analizador INTEGER DEFAULT 1,
    id_sector_definicion INTEGER REFERENCES sectores_definiciones(id),
    conteo INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🌐 API Endpoints

### Gestión de Sectores

#### `GET /sectores`
Obtiene todos los sectores disponibles con estadísticas.

**Respuesta:**
```json
{
  "success": true,
  "sectores": {
    "Rojos": {
      "id": 1,
      "nombre": "Rojos",
      "numeros": [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36],
      "cantidad_numeros": 18
    }
  },
  "estadisticas": {
    "Rojos": {
      "aciertos_totales": 15,
      "probabilidad_teorica": 0.486
    }
  }
}
```

#### `POST /sectores/crear`
Crea un nuevo sector personalizado.

**Request:**
```json
{
  "nombre": "Mi_Sector_Especial",
  "numeros": [1, 5, 9, 13, 17, 21, 25, 29, 33]
}
```

**Soporte para comas:**
```json
{
  "nombre": "Sector_Comas",
  "numeros": ["1, 5, 9, 13, 17, 21"]
}
```

#### `DELETE /sectores/eliminar/{nombre}`
Elimina un sector personalizado.

#### `GET /sectores/estadisticas`
Obtiene estadísticas detalladas de todos los sectores.

**Respuesta:**
```json
{
  "success": true,
  "estadisticas_por_sector": {
    "Rojos": {
      "aciertos_totales": 15,
      "cantidad_numeros": 18,
      "probabilidad_teorica": 0.486
    }
  },
  "resumen": {
    "total_sectores": 12,
    "total_aciertos": 87,
    "mejores_sectores": [
      {"nombre": "Rojos", "aciertos": 15},
      {"nombre": "Primera_Docena", "aciertos": 12}
    ]
  }
}
```

#### `GET /sectores/analizar-numero/{numero}`
Analiza en qué sectores se encuentra un número específico.

**Ejemplo: `/sectores/analizar-numero/5`**
```json
{
  "success": true,
  "numero": 5,
  "color": "Rojo",
  "sectores_que_contienen": [
    {
      "nombre": "Rojos",
      "cantidad_numeros": 18,
      "aciertos_totales": 15,
      "probabilidad_teorica": 0.486
    },
    {
      "nombre": "Impares",
      "cantidad_numeros": 18,
      "aciertos_totales": 14,
      "probabilidad_teorica": 0.486
    }
  ]
}
```

#### `POST /sectores/resetear-conteos`
Resetea todos los conteos de sectores a 0.

**Request:**
```json
{
  "confirmar": true
}
```

## 🔄 Flujo de Procesamiento

### 1. Ingreso de Números
```
Usuario ingresa: "23, 14, 5, 32"
         ↓
NumberProcessor.procesar_cadena_numeros()
         ↓
Resultado: [
  NumeroProcessed(valor=23, color='Rojo'),
  NumeroProcessed(valor=14, color='Negro'),
  NumeroProcessed(valor=5, color='Rojo'),
  NumeroProcessed(valor=32, color='Rojo')
]
```

### 2. Guardado en Supabase
```
save_history_to_supabase("23, 14, 5, 32")
         ↓
INSERT INTO roulette_history (numbers_string)
         ↓
save_individual_numbers_to_supabase(id, "23, 14, 5, 32")
         ↓
INSERT INTO roulette_numbers_individual 
  (history_entry_id, number_value, color)
VALUES 
  (123, 23, 'Rojo'),
  (123, 14, 'Negro'),
  (123, 5, 'Rojo'),
  (123, 32, 'Rojo')
```

### 3. Análisis de Sectores
```
Para cada número insertado:
sector_manager.verificar_acierto_sectores(numero)
         ↓
- Número 23 → Sectores: ['Rojos', 'Impares', 'Segunda_Docena']
- Número 14 → Sectores: ['Negros', 'Pares', 'Segunda_Docena']
         ↓
Actualizar conteos en sectores_conteos
```

### 4. Victory Trainer Integration
```
Si Victory Trainer está activo:
victory_trainer.record_victory(prediction_data, actual_number, context)
         ↓
Incluye información de sectores acertados
         ↓
Entrenamiento ML considera sectores exitosos
```

## 🧪 Testing

### Ejecutar Pruebas Completas
```bash
cd backend
python test_integrated_system.py
```

### Pruebas Incluidas
1. **NumberProcessor**: Formatos, validación, colores
2. **SectorManager**: CRUD, aciertos, estadísticas  
3. **API Endpoints**: Crear, obtener, eliminar sectores
4. **Integración**: Análisis completo con sectores

### Ejemplo de Salida
```
🚀 INICIANDO PRUEBAS DEL SISTEMA INTEGRADO
Fecha: 2024-01-15 14:30:22

==================================================
🔍 PRUEBA 1: NUMBER PROCESSOR
==================================================

Caso 1: '23, 14, 5, 32'
  Formato detectado: comas
  Números válidos: [23, 14, 5, 32]
  Colores: ['Rojo', 'Negro', 'Rojo', 'Rojo']
  ✅ Procesado correctamente

📊 Resultado: 11/11 pruebas exitosas

==================================================
🎯 PRUEBA 2: SECTOR MANAGER  
==================================================

📋 Listando sectores predefinidos...
  Sectores encontrados: 12
  ✅ Sectores predefinidos cargados correctamente

📊 Resultado: 5/5 pruebas exitosas

============================================================
📋 RESUMEN FINAL DE PRUEBAS
============================================================

  NumberProcessor      ✅ EXITOSA
  SectorManager        ✅ EXITOSA  
  Endpoints API        ✅ EXITOSA
  Integración Completa ✅ EXITOSA

📊 RESULTADO GENERAL: 4/4 pruebas exitosas
🎉 SISTEMA FUNCIONANDO CORRECTAMENTE (100.0%)
✅ El sistema integrado está listo para producción
```

## 🚀 Instalación y Configuración

### 1. Verificar Dependencias
```bash
pip install supabase python-dotenv flask flask-cors requests
```

### 2. Configurar Variables de Entorno
```bash
# .env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 3. Ejecutar Migraciones de Tablas
Las tablas `sectores_definiciones` y `sectores_conteos` se crean automáticamente según el esquema en `create_tables.sql`.

### 4. Iniciar el Sistema
```bash
cd backend
python app.py
```

### 5. Verificar Funcionamiento
```bash
curl http://localhost:5000/sectores
```

## 📈 Métricas y Monitoreo

### Métricas Disponibles
- **Total de sectores**: Número de sectores configurados
- **Aciertos por sector**: Conteo de números que caen en cada sector
- **Tasa de acierto**: Aciertos vs probabilidad teórica
- **Mejores sectores**: Ranking por número de aciertos
- **Distribución de colores**: Análisis de balanceamiento

### Logging
El sistema registra automáticamente:
- Números procesados y su formato
- Sectores acertados por cada número
- Errores de procesamiento
- Estadísticas de uso

## 🔮 Funcionalidades Avanzadas

### 1. Análisis Predictivo con Sectores
El sistema puede usar los datos de sectores para:
- Identificar patrones de aciertos por sector
- Entrenar modelos ML específicos por sector
- Generar predicciones basadas en rendimiento histórico

### 2. Alertas de Desbalance
Detecta automáticamente cuando:
- Un sector tiene demasiados aciertos consecutivos
- La distribución se desvía significativamente de lo esperado
- Hay patrones anómalos en los datos

### 3. Exportación de Datos
```python
# Exportar estadísticas de sectores
stats = sector_manager.obtener_estadisticas_sectores()
with open('sector_stats.json', 'w') as f:
    json.dump(stats, f, indent=2)
```

## 🤝 Integración con Sistemas Existentes

### Victory Trainer
- Los aciertos en sectores se registran automáticamente como victorias
- El entrenamiento ML puede usar datos específicos de sectores exitosos
- Las métricas de Victory Trainer incluyen análisis por sector

### Advanced ML Predictor
- Entrenamiento enriquecido con datos de sectores
- Predicciones que consideran tendencias por sector
- Modelos especializados para diferentes tipos de sectores

### Análisis de Ruleta Existente
- Integración transparente con `AnalizadorRuleta`
- Enriquecimiento de análisis con información de sectores
- Mantenimiento de compatibilidad con todas las funciones existentes

## 📝 Changelog

### v1.0.0 - Sistema Integrado Inicial
- ✅ NumberProcessor para manejo de comas
- ✅ SectorManager con sectores predefinidos  
- ✅ Integración con tablas Supabase existentes
- ✅ 6 endpoints API nuevos
- ✅ Suite de pruebas completa
- ✅ Documentación exhaustiva
- ✅ Compatibilidad con Victory Trainer

### Próximas Versiones
- 🔄 Análisis temporal de sectores
- 🔄 Machine Learning específico por sector  
- 🔄 Dashboard web para gestión de sectores
- 🔄 Exportación/importación de configuraciones
- 🔄 API de webhooks para eventos de sectores

---

**Desarrollado para el Sistema ML Avanzado de Predicción de Ruleta**

*Optimizando el análisis a través de sectores inteligentes* 🎯 