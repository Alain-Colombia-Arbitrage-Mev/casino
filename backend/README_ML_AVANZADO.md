# Sistema ML Avanzado para Predicción de Ruleta

## 🚀 Descripción General

El Sistema ML Avanzado es una implementación sofisticada que combina múltiples enfoques de aprendizaje automático para generar predicciones inteligentes de números de ruleta. Este sistema va más allá de las predicciones básicas al integrar:

- **Machine Learning Ensemble**: Múltiples algoritmos trabajando en conjunto
- **Análisis de Sectores**: Patrones basados en la rueda europea
- **Análisis de Estrategias**: Detección de patrones como Tía Lu, Fibonacci, etc.
- **Análisis Temporal**: Predicciones basadas en patrones de tiempo
- **Sistema Híbrido**: Combinación ponderada de todos los métodos

## 🧠 Arquitectura del Sistema

### Componentes Principales

#### 1. AdvancedMLPredictor
**Clase principal que coordina todo el sistema**

```python
from advanced_ml_predictor import AdvancedMLPredictor

predictor = AdvancedMLPredictor()
predictor.train_models(historial_numeros)
predicciones = predictor.predict_advanced(nuevos_datos)
```

**Características:**
- Entrenamiento automático con múltiples algoritmos
- Sistema de ensemble con pesos adaptativos
- Predicciones híbridas combinando todos los métodos
- Sistema de respaldo inteligente

#### 2. SectorAnalyzer
**Analiza patrones basados en sectores de la rueda europea**

```python
sector_analyzer = SectorAnalyzer()
predicciones_sectores = sector_analyzer.predict_sectors(historial)
```

**Sectores incluidos:**
- Vecinos del Cero (0, 32, 26, 3, 35, 12, 28, 7, 29, 18, 22, 9, 31, 14, 20, 1)
- Tercios del Cilindro (33, 16, 24, 5, 10, 23, 8, 30, 11, 36, 13, 27)
- Orphelins (17, 34, 6, 1, 20, 14, 31, 9)
- **Nuevos sectores dinámicos:**
  - Vecinos 5 del 7, 27, 31, 34
  - Vecinos 9 del 0 y 2

#### 3. StrategyAnalyzer
**Detecta y analiza estrategias de ruleta**

```python
strategy_analyzer = StrategyAnalyzer()
predicciones_estrategias = strategy_analyzer.predict_strategies(historial)
```

**Estrategias implementadas:**
- **Tía Lu**: Activación con números 33, 22, 11
- **Fibonacci**: Números de la secuencia (1, 1, 2, 3, 5, 8, 13, 21, 34)
- **Compensación**: Números fríos que no han salido recientemente

#### 4. TemporalAnalyzer
**Analiza patrones basados en tiempo**

```python
temporal_analyzer = TemporalAnalyzer()
predicciones_temporales = temporal_analyzer.predict_temporal(historial)
```

**Características temporales:**
- Hora del día (mañana, tarde, noche, madrugada)
- Día de la semana
- Patrones cíclicos usando funciones trigonométricas

## 🔧 Algoritmos de Machine Learning

### Modelos Implementados

1. **Random Forest Classifier**
   - 100 estimadores
   - Profundidad máxima: 10
   - Balanceo de clases automático

2. **Gradient Boosting Classifier**
   - 100 estimadores
   - Tasa de aprendizaje: 0.1
   - Profundidad máxima: 6

3. **Support Vector Machine (SVM)**
   - Kernel RBF
   - Probabilidades habilitadas
   - Balanceo de clases

4. **Red Neuronal (MLP)**
   - Capas ocultas: (100, 50, 25)
   - Activación ReLU
   - Optimizador Adam

### Sistema Ensemble
Los modelos se combinan usando votación ponderada basada en rendimiento histórico:

```python
# Pesos calculados dinámicamente
ensemble_weights = {
    'random_forest': 0.3,
    'gradient_boost': 0.25,
    'svm': 0.2,
    'neural_network': 0.25
}
```

## 📊 Ingeniería de Características

### Características Extraídas

1. **Características Básicas**
   - Últimos 10 números
   - Media y desviación estándar
   - Números únicos en ventana

2. **Características de Frecuencia**
   - Frecuencia de cada número (0-36) en últimos 20 giros
   - Patrones de diferencias entre números consecutivos

3. **Características de Sectores**
   - Conteo de apariciones por sector
   - Porcentaje de actividad por sector
   - Posición de última aparición

4. **Características Temporales**
   - Hora normalizada (0-1)
   - Día de la semana normalizado
   - Componentes cíclicos (sin/cos)

5. **Características de Estrategias**
   - Contadores de activación de Tía Lu
   - Presencia de números Fibonacci
   - Análisis par/impar, rojo/negro
   - Distribución por docenas y columnas

## 🎯 Sistema de Predicciones

### Tipos de Predicciones Generadas

1. **Predicción Individual**: Número único más probable
2. **Grupos de Predicción**:
   - Grupo de 5 números
   - Grupo de 10 números
   - Grupo de 15 números
   - Grupo de 20 números

### Algoritmo Híbrido

El sistema combina las predicciones usando pesos específicos:

```python
# Ponderación híbrida
final_prediction = (
    ML_predictions * 0.40 +        # 40% Machine Learning
    sector_predictions * 0.30 +    # 30% Análisis de sectores
    strategy_predictions * 0.20 +  # 20% Estrategias
    temporal_predictions * 0.10    # 10% Patrones temporales
)
```

### Protección del 0
Todos los grupos incluyen automáticamente el número 0 como protección, ya que es estadísticamente significativo en la ruleta europea.

## 🔄 Entrenamiento y Rendimiento

### Proceso de Entrenamiento

1. **Preparación de Datos**
   - Ventana deslizante de 15 números
   - Extracción de características avanzadas
   - Normalización con StandardScaler

2. **Entrenamiento de Modelos**
   - División 80/20 para entrenamiento/validación
   - Validación cruzada para evaluación
   - Cálculo de pesos del ensemble basado en rendimiento

3. **Evaluación**
   - Métricas de precisión por modelo
   - Historial de rendimiento almacenado
   - Ajuste automático de pesos

### Métricas de Rendimiento

```python
performance_stats = {
    "random_forest": {
        "latest_accuracy": 0.156,
        "average_accuracy": 0.148,
        "best_accuracy": 0.178,
        "evaluations_count": 5
    }
    # ... otros modelos
}
```

## 🚀 Uso del Sistema

### Instalación de Dependencias

```bash
pip install numpy pandas scikit-learn tensorflow
```

### Uso Básico

```python
from advanced_ml_predictor import AdvancedMLPredictor

# Inicializar
predictor = AdvancedMLPredictor()

# Entrenar con historial
historial = [1, 15, 32, 0, 26, 3, 35, ...]  # Lista de números
success = predictor.train_models(historial)

if success:
    # Generar predicciones
    predicciones = predictor.predict_advanced(historial[-30:])
    
    print(f"Predicción individual: {predicciones['individual']}")
    print(f"Grupo de 5: {predicciones['grupo_5']}")
    print(f"Confianza: {predicciones['confidence_scores']}")
```

### Endpoints API

1. **`/predicciones-avanzadas`** - Predicciones usando sistema completo
2. **`/entrenar-ml-avanzado`** - Entrenamiento manual
3. **`/estado-ml-avanzado`** - Estado del sistema
4. **`/analisis-detallado-ml`** - Análisis detallado por componente

## 📈 Optimizaciones Implementadas

### Sistema de Cache
- Cache de predicciones con expiración (5 minutos)
- Limpieza automática de cache antiguo
- Claves basadas en últimos números del historial

### Entrenamiento Automático
- Entrenamiento en background al inicio
- Re-entrenamiento automático cada 6 horas
- Entrenamiento bajo demanda si no está disponible

### Manejo de Errores
- Predicciones de respaldo inteligentes
- Validación de datos de entrada
- Logs detallados para debugging

## 🔍 Análisis Detallado

### Importancia de Características

El sistema puede mostrar qué características son más importantes para las predicciones:

```python
feature_importance = predictor.get_feature_importance()
# Retorna top 10 características más importantes
```

### Análisis de Tendencias

```python
detailed_analysis = predictor.get_detailed_analysis(historial)
# Incluye:
# - Análisis de sectores con estados (frío/caliente)
# - Efectividad de estrategias
# - Patrones temporales
# - Importancia de características
```

## 🧪 Testing

Ejecutar el script de prueba:

```bash
cd backend
python test_advanced_ml.py
```

El script realiza:
- Generación de datos de prueba con patrones
- Entrenamiento del sistema completo
- Verificación de predicciones
- Prueba de componentes individuales
- Análisis de rendimiento

## 📋 Requisitos del Sistema

### Mínimos
- Python 3.8+
- 8GB RAM
- Historial mínimo: 30 números

### Recomendados
- Python 3.9+
- 16GB RAM
- Historial recomendado: 100+ números
- CPU multi-core para entrenamiento rápido

## 🔮 Características Futuras

1. **Análisis de Correlaciones Avanzadas**
   - Detección automática de nuevos patrones
   - Análisis de dependencias complejas

2. **Optimización de Hiperparámetros**
   - Auto-tuning de parámetros del modelo
   - Búsqueda de grilla automática

3. **Integración con Datos Externos**
   - APIs de casinos en tiempo real
   - Análisis de múltiples mesas simultáneamente

4. **Visualizaciones Avanzadas**
   - Gráficos de tendencias de sectores
   - Mapas de calor de predicciones
   - Análisis de flujo de números

## ⚠️ Limitaciones y Consideraciones

1. **Naturaleza Aleatoria de la Ruleta**
   - Los resultados pasados no garantizan resultados futuros
   - El sistema mejora las probabilidades pero no las garantiza

2. **Requisitos de Datos**
   - Necesita historial suficiente para entrenamiento efectivo
   - La calidad de predicciones mejora con más datos

3. **Rendimiento Computacional**
   - El entrenamiento puede tomar tiempo con historiales grandes
   - Se recomienda usar en servidores con recursos adecuados

## 📞 Soporte

Para soporte técnico o preguntas sobre la implementación, consulte:
- Logs del sistema para debugging
- Script de prueba para verificar funcionamiento
- Endpoints de estado para monitoreo en tiempo real

---

**Desarrollado con ❤️ para análisis inteligente de ruleta** 