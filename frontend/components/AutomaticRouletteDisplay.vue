<template>
  <div class="bg-white p-4 rounded-lg shadow-md h-full flex flex-col">
    <!-- Header con estado del sistema -->
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold text-gray-800">Sistema Automático de Ruleta</h2>
      <div class="flex items-center gap-2">
        <div class="text-sm font-medium px-2 py-1 rounded" :class="systemStatusClass">
          {{ systemStatusText }}
        </div>
        <button 
          @click="toggleAutoService"
          class="px-3 py-1 rounded text-sm font-medium"
          :class="serviceRunning ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-green-500 hover:bg-green-600 text-white'"
          :disabled="loading"
        >
          {{ serviceRunning ? 'Detener' : 'Iniciar' }}
        </button>
      </div>
    </div>

    <!-- Panel de información actual -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <!-- Último número detectado -->
      <div class="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
        <h3 class="text-lg font-semibold text-blue-700 mb-2">Último Número</h3>
        <div class="flex items-center justify-center">
          <div v-if="latestNumber" class="text-center">
            <div class="inline-block w-16 h-16 rounded-full bg-gray-800 text-white flex items-center justify-center text-2xl font-bold mb-2">
              {{ latestNumber.number }}
            </div>
            <div class="text-sm text-blue-600">
              {{ formatTime(latestNumber.timestamp) }}
            </div>
          </div>
          <div v-else class="text-gray-500">
            Esperando números...
          </div>
        </div>
      </div>

      <!-- Estadísticas de predicciones -->
      <div class="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
        <h3 class="text-lg font-semibold text-green-700 mb-2">Estadísticas</h3>
        <div class="grid grid-cols-3 gap-2 text-center">
          <div>
            <div class="text-lg font-bold text-green-600">{{ stats.wins }}</div>
            <div class="text-xs text-green-700">Aciertos</div>
          </div>
          <div>
            <div class="text-lg font-bold text-red-600">{{ stats.losses }}</div>
            <div class="text-xs text-red-700">Fallos</div>
          </div>
          <div>
            <div class="text-lg font-bold text-blue-600">{{ winRate }}%</div>
            <div class="text-xs text-blue-700">Efectividad</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Predicciones activas -->
    <div class="flex-1 mb-4">
      <h3 class="text-lg font-semibold text-purple-700 mb-3">Predicciones Activas</h3>
      <div class="overflow-y-auto max-h-64">
        <div v-if="activePredictions.length === 0" class="text-center text-gray-500 py-8">
          No hay predicciones activas
        </div>
        <div v-else class="space-y-3">
          <div 
            v-for="prediction in activePredictions" 
            :key="prediction.id"
            class="bg-purple-50 p-3 rounded-lg border border-purple-200"
          >
            <div class="flex justify-between items-start mb-2">
              <div class="font-medium text-purple-700">{{ prediction.method || 'Predicción' }}</div>
              <div class="text-sm text-purple-600">{{ formatTime(prediction.timestamp) }}</div>
            </div>
            
            <!-- Números predichos -->
            <div class="flex flex-wrap gap-1 mb-2">
              <span 
                v-for="num in prediction.predicted_numbers.slice(0, 12)" 
                :key="prediction.id + '-' + num"
                class="inline-block w-6 h-6 rounded-full bg-purple-600 text-white flex items-center justify-center text-xs font-bold"
              >
                {{ num }}
              </span>
              <span v-if="prediction.predicted_numbers.length > 12" class="text-xs text-purple-500 flex items-center">
                +{{ prediction.predicted_numbers.length - 12 }} más
              </span>
            </div>
            
            <!-- Información adicional -->
            <div class="text-xs text-purple-600">
              Confianza: {{ Math.round((prediction.confidence || 0) * 100) }}%
              <span v-if="prediction.description" class="ml-2">
                • {{ prediction.description }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Historial de resultados recientes -->
    <div class="bg-gray-50 p-4 rounded-lg">
      <h3 class="text-lg font-semibold text-gray-700 mb-3">Resultados Recientes</h3>
      <div class="flex flex-wrap gap-2 max-h-24 overflow-y-auto">
        <div 
          v-for="result in recentResults" 
          :key="result.id"
          class="flex items-center gap-2 bg-white p-2 rounded border text-sm"
        >
          <div class="w-6 h-6 rounded-full bg-gray-800 text-white flex items-center justify-center text-xs font-bold">
            {{ result.number }}
          </div>
          <span class="px-2 py-1 rounded text-xs font-medium" :class="result.isWin ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'">
            {{ result.isWin ? 'WIN' : 'LOSS' }}
          </span>
          <span class="text-xs text-gray-500">{{ formatTime(result.timestamp) }}</span>
        </div>
      </div>
    </div>

    <!-- Controles del sistema -->
    <div class="mt-4 flex justify-between items-center pt-3 border-t">
      <div class="text-sm text-gray-600">
        Última actualización: {{ formatTime(lastUpdate) }}
      </div>
      <div class="flex gap-2">
        <button 
          @click="refreshData"
          class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm"
          :disabled="loading"
        >
          Actualizar
        </button>
        <button 
          @click="clearHistory"
          class="px-3 py-1 bg-gray-500 hover:bg-gray-600 text-white rounded text-sm"
        >
          Limpiar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

// Estado del sistema
const serviceRunning = ref(false)
const loading = ref(false)
const systemStatus = ref('unknown')
const systemMessage = ref('')

// Datos del juego
const latestNumber = ref(null)
const stats = ref({ wins: 0, losses: 0, total_predictions: 0 })
const activePredictions = ref([])
const recentResults = ref([])
const lastUpdate = ref(new Date().toISOString())

// Intervalo de actualización
let updateInterval = null
let statusInterval = null

// Computed properties
const winRate = computed(() => {
  if (stats.value.total_predictions === 0) return 0
  return Math.round((stats.value.wins / stats.value.total_predictions) * 100)
})

const systemStatusClass = computed(() => {
  switch (systemStatus.value) {
    case 'running': return 'bg-green-100 text-green-800'
    case 'stopped': return 'bg-red-100 text-red-800'
    case 'error': return 'bg-red-100 text-red-800'
    default: return 'bg-gray-100 text-gray-800'
  }
})

const systemStatusText = computed(() => {
  switch (systemStatus.value) {
    case 'running': return 'Sistema Activo'
    case 'stopped': return 'Sistema Detenido'
    case 'error': return 'Error del Sistema'
    default: return 'Estado Desconocido'
  }
})

// Métodos
const toggleAutoService = async () => {
  loading.value = true
  try {
    const endpoint = serviceRunning.value ? '/automatic-service/stop' : '/automatic-service/start'
    const response = await fetch(`http://localhost:5000${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    
    const data = await response.json()
    
    if (data.status === 'success') {
      serviceRunning.value = !serviceRunning.value
      await refreshData()
    } else {
      console.error('Error toggling service:', data.message)
    }
  } catch (error) {
    console.error('Error toggling service:', error)
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  try {
    // Obtener estado del servicio
    await getServiceStatus()
    
    // Obtener último número
    await getLatestNumber()
    
    // Obtener predicciones activas
    await getPredictions()
    
    lastUpdate.value = new Date().toISOString()
  } catch (error) {
    console.error('Error refreshing data:', error)
  }
}

const getServiceStatus = async () => {
  try {
    const response = await fetch('http://localhost:5000/automatic-service/status')
    const data = await response.json()
    
    if (data.status === 'success' && data.data) {
      serviceRunning.value = data.data.service_running || false
      systemStatus.value = data.data.redis_status?.status || 'unknown'
      systemMessage.value = data.data.redis_status?.message || ''
      
      // Actualizar estadísticas locales
      if (data.data.local_statistics) {
        stats.value = data.data.local_statistics
      }
    }
  } catch (error) {
    console.error('Error getting service status:', error)
    systemStatus.value = 'error'
  }
}

const getLatestNumber = async () => {
  try {
    const response = await fetch('http://localhost:5000/redis/latest-number')
    const data = await response.json()
    
    if (data.status === 'success' && data.data) {
      const newNumber = data.data
      
      // Si es un número nuevo, procesarlo
      if (!latestNumber.value || latestNumber.value.number !== newNumber.number) {
        // Evaluar predicciones activas
        if (latestNumber.value && activePredictions.value.length > 0) {
          evaluatePredictions(newNumber.number)
        }
        
        latestNumber.value = newNumber
      }
    }
  } catch (error) {
    console.error('Error getting latest number:', error)
  }
}

const getPredictions = async () => {
  try {
    const response = await fetch('http://localhost:5000/redis/predictions')
    const data = await response.json()
    
    if (data.status === 'success' && data.data) {
      activePredictions.value = data.data.active_predictions || []
      
      // Actualizar estadísticas de Redis
      if (data.data.statistics) {
        const redisStats = data.data.statistics
        stats.value = {
          wins: redisStats.wins || 0,
          losses: redisStats.losses || 0,
          total_predictions: redisStats.total_predictions || 0
        }
      }
    }
  } catch (error) {
    console.error('Error getting predictions:', error)
  }
}

const evaluatePredictions = (resultNumber) => {
  // Evaluar predicciones activas contra el número resultado
  activePredictions.value.forEach(prediction => {
    const isWin = prediction.predicted_numbers.includes(resultNumber)
    
    // Agregar al historial de resultados
    recentResults.value.unshift({
      id: Date.now() + Math.random(),
      number: resultNumber,
      isWin: isWin,
      timestamp: new Date().toISOString(),
      predictionId: prediction.id
    })
    
    // Mantener solo los últimos 20 resultados
    if (recentResults.value.length > 20) {
      recentResults.value.pop()
    }
  })
}

const clearHistory = () => {
  recentResults.value = []
  stats.value = { wins: 0, losses: 0, total_predictions: 0 }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  // Actualización inicial
  refreshData()
  
  // Actualizar datos cada 5 segundos
  updateInterval = setInterval(refreshData, 5000)
  
  // Actualizar estado del servicio cada 30 segundos
  statusInterval = setInterval(getServiceStatus, 30000)
})

onUnmounted(() => {
  if (updateInterval) clearInterval(updateInterval)
  if (statusInterval) clearInterval(statusInterval)
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style> 