<template>
  <div class="advanced-predictions-container">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
          🧠 Predicciones Avanzadas
          <span v-if="loading" class="ml-2 text-sm text-blue-500">Analizando...</span>
        </h2>
        <button 
          @click="obtenerPredicciones" 
          :disabled="loading"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
        >
          {{ loading ? 'Analizando...' : 'Actualizar' }}
        </button>
      </div>

      <!-- Estado de carga -->
      <div v-if="loading" class="flex items-center justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="ml-2 text-gray-600 dark:text-gray-400">Procesando análisis avanzado...</span>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
        <p class="text-red-700 dark:text-red-300">{{ error }}</p>
      </div>

      <!-- Predicciones -->
      <div v-else-if="predicciones">
        <!-- Predicción Principal -->
        <div class="grid md:grid-cols-3 gap-6 mb-8">
          <div class="bg-gradient-to-r from-purple-500 to-blue-600 rounded-lg p-6 text-white">
            <h3 class="text-lg font-semibold mb-2">🎯 Predicción Principal</h3>
            <div class="text-4xl font-bold">{{ predicciones.prediccion_individual }}</div>
            <p class="text-sm opacity-90 mt-2">Análisis híbrido ML + Estrategias</p>
          </div>

          <div class="bg-gradient-to-r from-green-500 to-teal-600 rounded-lg p-6 text-white">
            <h3 class="text-lg font-semibold mb-2">📊 Números Analizados</h3>
            <div class="text-3xl font-bold">{{ predicciones.cantidad_numeros_analizados }}</div>
            <p class="text-sm opacity-90 mt-2">Registros en el análisis</p>
          </div>

          <div class="bg-gradient-to-r from-orange-500 to-red-600 rounded-lg p-6 text-white">
            <h3 class="text-lg font-semibold mb-2">🔥 Confianza ML</h3>
            <div class="text-3xl font-bold">{{ getMaxConfidence() }}%</div>
            <p class="text-sm opacity-90 mt-2">Modelo más confiable</p>
          </div>
        </div>

                <!-- Grupos de Predicción -->        <div class="mb-8">          <div class="flex items-center justify-between mb-4">            <h3 class="text-xl font-semibold text-gray-900 dark:text-white">🎲 Grupos de Predicción</h3>            <div class="flex items-center text-sm text-green-600 dark:text-green-400">              <span class="bg-green-500 text-white px-2 py-1 rounded mr-2">0</span>              <span>Número de protección incluido</span>            </div>          </div>          <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-4">            <div v-for="(grupo, key) in predicciones.grupos_prediccion" :key="key"                  class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">              <h4 class="font-semibold text-gray-900 dark:text-white mb-2 capitalize flex items-center">                {{ String(key).replace('_', ' ') }}                <span v-if="grupo.includes(0)" class="ml-2 text-xs bg-green-500 text-white px-1 py-0.5 rounded">                  +0                </span>              </h4>              <div class="flex flex-wrap gap-1">                <span v-for="(num, index) in grupo" :key="num"                       :class="getNumberClass(num)"                      class="px-2 py-1 rounded text-white text-sm font-medium relative">                  {{ num }}                  <span v-if="num === 0" class="absolute -top-1 -right-1 text-xs">🛡️</span>                </span>              </div>              <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">                {{ grupo.length }} números • {{ (grupo.length / 37 * 100).toFixed(1) }}% cobertura              </div>            </div>          </div>        </div>

        <!-- Análisis por Método -->
        <div class="grid lg:grid-cols-2 gap-6 mb-8">
          <!-- Análisis ML -->
          <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
            <h3 class="text-lg font-semibold text-blue-900 dark:text-blue-300 mb-4">
              🤖 Modelos de Machine Learning
            </h3>
            <div class="space-y-3">
              <div v-for="(pred, model) in predicciones.analisis_ml" :key="model" 
                   class="flex items-center justify-between">
                                 <span class="font-medium text-gray-700 dark:text-gray-300 capitalize">                   {{ String(model).replace('_', ' ') }}                 </span>
                <div class="flex items-center space-x-2">
                  <span :class="getNumberClass(pred)" 
                        class="px-3 py-1 rounded text-white font-bold">
                    {{ pred }}
                  </span>
                  <span class="text-sm text-gray-500">
                    {{ (predicciones.confianza[model] * 100).toFixed(1) }}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Análisis de Estrategias -->
          <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-6">
            <h3 class="text-lg font-semibold text-green-900 dark:text-green-300 mb-4">
              🎯 Estrategias Activas
            </h3>
            <div v-if="Object.keys(predicciones.analisis_estrategias).length > 0" class="space-y-3">
              <div v-for="(numeros, estrategia) in predicciones.analisis_estrategias" :key="estrategia">
                                 <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2 capitalize">                   {{ String(estrategia).replace('_', ' ') }}                 </h4>
                <div class="flex flex-wrap gap-1">
                  <span v-for="num in numeros.slice(0, 6)" :key="num" 
                        :class="getNumberClass(num)"
                        class="px-2 py-1 rounded text-white text-xs font-medium">
                    {{ num }}
                  </span>
                </div>
              </div>
            </div>
            <p v-else class="text-gray-500 dark:text-gray-400 italic">
              No hay estrategias activas en este momento
            </p>
          </div>
        </div>

        <!-- Análisis de Sectores -->
        <div class="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-6 mb-8">
          <h3 class="text-lg font-semibold text-purple-900 dark:text-purple-300 mb-4">
            🎡 Análisis de Sectores
          </h3>
          <div v-if="Object.keys(predicciones.analisis_sectores).length > 0" 
               class="grid md:grid-cols-2 gap-4">
            <div v-for="(numeros, sector) in predicciones.analisis_sectores" :key="sector">
                             <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2 capitalize">                 {{ String(sector).replace('_', ' ') }}               </h4>
              <div class="flex flex-wrap gap-1">
                <span v-for="num in numeros.slice(0, 8)" :key="num" 
                      :class="getNumberClass(num)"
                      class="px-2 py-1 rounded text-white text-xs font-medium">
                  {{ num }}
                </span>
              </div>
            </div>
          </div>
          <p v-else class="text-gray-500 dark:text-gray-400 italic">
            No hay sectores destacados detectados
          </p>
        </div>

        <!-- Recomendaciones -->
        <div v-if="predicciones.recomendaciones && predicciones.recomendaciones.length > 0" 
             class="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-6">
          <h3 class="text-lg font-semibold text-yellow-900 dark:text-yellow-300 mb-4">
            💡 Recomendaciones Estratégicas
          </h3>
          <div class="space-y-4">
            <div v-for="rec in predicciones.recomendaciones" :key="rec.nombre" 
                 class="border border-yellow-200 dark:border-yellow-800 rounded p-4">
              <div class="flex items-center justify-between mb-2">
                <h4 class="font-semibold text-gray-900 dark:text-white">{{ rec.nombre }}</h4>
                <span :class="getPriorityClass(rec.prioridad)" 
                      class="px-2 py-1 rounded text-xs font-medium">
                  {{ rec.prioridad }}
                </span>
              </div>
              <p class="text-gray-700 dark:text-gray-300 text-sm mb-2">{{ rec.descripcion }}</p>
              <div v-if="rec.numeros" class="flex flex-wrap gap-1">
                <span v-for="num in rec.numeros.slice(0, 8)" :key="num" 
                      :class="getNumberClass(num)"
                      class="px-2 py-1 rounded text-white text-xs font-medium">
                  {{ num }}
                </span>
              </div>
              <div v-if="rec.numero" class="mt-2">
                <span :class="getNumberClass(rec.numero)"
                      class="px-3 py-1 rounded text-white font-bold">
                  {{ rec.numero }}
                </span>
                <span v-if="rec.confianza" class="ml-2 text-sm text-gray-500">
                  Confianza: {{ (rec.confianza * 100).toFixed(1) }}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Últimos números -->
        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mt-6">
          <h4 class="font-semibold text-gray-900 dark:text-white mb-2">📈 Últimos números analizados</h4>
          <div class="flex flex-wrap gap-1">
            <span v-for="num in predicciones.ultimos_numeros" :key="num" 
                  :class="getNumberClass(num)"
                  class="px-2 py-1 rounded text-white text-sm font-medium">
              {{ num }}
            </span>
          </div>
        </div>
      </div>

      <!-- Estado inicial -->
      <div v-else class="text-center py-8">
        <p class="text-gray-500 dark:text-gray-400 mb-4">
          Haz clic en "Actualizar" para obtener predicciones avanzadas
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Predicciones {
  prediccion_individual: number
  cantidad_numeros_analizados: number
  ultimos_numeros: number[]
  grupos_prediccion: {
    grupo_5: number[]
    grupo_10: number[]
    grupo_15: number[]
    grupo_20: number[]
  }
  analisis_ml: { [key: string]: number }
  analisis_sectores: { [key: string]: number[] }
  analisis_estrategias: { [key: string]: number[] }
  analisis_temporal: { [key: string]: any }
  confianza: { [key: string]: number }
  pesos_hibridos: { [key: string]: number }
  recomendaciones: Array<{
    tipo: string
    nombre: string
    descripcion: string
    numeros?: number[]
    numero?: number
    confianza?: number
    prioridad: string
  }>
}

const predicciones = ref<Predicciones | null>(null)
const loading = ref(false)
const error = ref('')

const obtenerPredicciones = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const apiBaseUrl = window.location.origin.includes('localhost') ? 'http://localhost:5000' : window.location.origin
    
    const response = await fetch(`${apiBaseUrl}/predicciones-avanzadas`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    const data = await response.json()
    
    if (response.ok && data.status === 'success') {
      predicciones.value = data
      console.log('✅ Predicciones avanzadas obtenidas:', data)
    } else {
      error.value = data.message || 'Error al obtener predicciones avanzadas'
      console.error('❌ Error en predicciones:', data)
    }
  } catch (err) {
    error.value = 'Error de conexión con el servidor'
    console.error('❌ Error de conexión:', err)
  } finally {
    loading.value = false
  }
}

const getNumberClass = (number: number) => {
  if (number === 0) return 'bg-green-500'
  const redNumbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
  return redNumbers.includes(number) ? 'bg-red-500' : 'bg-gray-800'
}

const getPriorityClass = (priority: string) => {
  switch (priority) {
    case 'alta': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
    case 'media': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
    case 'baja': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
    default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
  }
}

const getMaxConfidence = () => {
  if (!predicciones.value?.confianza) return 0
  const maxConf = Math.max(...Object.values(predicciones.value.confianza))
  return (maxConf * 100).toFixed(0)
}

onMounted(() => {
  // Obtener predicciones al cargar el componente
  // obtenerPredicciones()
})
</script>

<style scoped>
.advanced-predictions-container {
  max-width: 1400px;
  margin: 0 auto;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style> 