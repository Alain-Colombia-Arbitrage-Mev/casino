<template>
  <div class="bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-6 rounded-xl shadow-xl h-full flex flex-col border border-blue-200/50 backdrop-blur-sm">
    <!-- Header con controles del sistema -->
    <div class="flex justify-between items-center mb-4">
      <div>
        <h2 class="text-xl font-bold text-gray-800">Sistema Automático de Ruleta</h2>
        <p class="text-sm text-gray-600">Lightning Roulette - Evolution Gaming</p>
      </div>
      <div class="flex items-center gap-2">
        <div class="text-sm font-medium px-3 py-1 rounded-lg" :class="systemStatusClass">
          {{ systemStatusText }}
        </div>
        <button 
          @click="toggleAutoService"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="serviceRunning ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-green-500 hover:bg-green-600 text-white'"
          :disabled="loading"
        >
          {{ loading ? 'Procesando...' : (serviceRunning ? 'Detener Sistema' : 'Iniciar Sistema') }}
        </button>
      </div>
    </div>

    <!-- Panel principal de información -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
      <!-- Último número detectado -->
      <div class="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border-2 border-blue-200">
        <h3 class="text-lg font-semibold text-blue-700 mb-3 text-center">Último Número Detectado</h3>
        <div class="flex flex-col items-center">
          <div v-if="latestNumber" class="text-center">
            <div class="inline-block w-20 h-20 rounded-full bg-gray-800 text-white flex items-center justify-center text-3xl font-bold mb-2 shadow-lg">
              {{ latestNumber.number }}
            </div>
            <div class="text-sm text-blue-600 font-medium">
              {{ formatTime(latestNumber.timestamp) }}
            </div>
            <div class="text-xs text-blue-500 mt-1">
              Color: {{ getNumberColor(latestNumber.number) }}
            </div>
          </div>
          <div v-else class="text-gray-500 text-center py-4">
            <div class="animate-pulse">
              <div class="w-20 h-20 bg-gray-300 rounded-full mx-auto mb-2"></div>
              <div class="text-sm">Esperando números...</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Estadísticas del sistema -->
      <div class="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border-2 border-green-200">
        <h3 class="text-lg font-semibold text-green-700 mb-3 text-center">Estadísticas de Predicciones</h3>
        <div class="grid grid-cols-2 gap-3">
          <div class="text-center bg-white p-3 rounded-lg">
            <div class="text-2xl font-bold text-green-600">{{ stats.wins }}</div>
            <div class="text-xs text-green-700 font-medium">Aciertos</div>
          </div>
          <div class="text-center bg-white p-3 rounded-lg">
            <div class="text-2xl font-bold text-red-600">{{ stats.losses }}</div>
            <div class="text-xs text-red-700 font-medium">Fallos</div>
          </div>
          <div class="text-center bg-white p-3 rounded-lg col-span-2">
            <div class="text-2xl font-bold text-blue-600">{{ winRate }}%</div>
            <div class="text-xs text-blue-700 font-medium">Tasa de Éxito</div>
          </div>
        </div>
      </div>

      <!-- Estado del sistema -->
      <div class="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border-2 border-purple-200">
        <h3 class="text-lg font-semibold text-purple-700 mb-3 text-center">Estado del Sistema</h3>
        <div class="space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-purple-600">Servicio:</span>
            <span class="font-medium" :class="serviceRunning ? 'text-green-600' : 'text-red-600'">
              {{ serviceRunning ? 'Activo' : 'Inactivo' }}
            </span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-purple-600">Predicciones activas:</span>
            <span class="font-medium text-purple-800">{{ activePredictions.length }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-purple-600">Números procesados:</span>
            <span class="font-medium text-purple-800">{{ stats.total_predictions }}</span>
          </div>
          <div class="text-xs text-purple-500 text-center mt-2">
            Última actualización: {{ formatTime(lastUpdate) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Predicciones activas -->
    <div class="flex-1 mb-4">
      <div class="flex justify-between items-center mb-3">
        <h3 class="text-lg font-semibold text-purple-700">Predicciones Automáticas Activas</h3>
        <div class="text-sm text-purple-600">
          {{ activePredictions.length }} predicción{{ activePredictions.length !== 1 ? 'es' : '' }}
        </div>
      </div>
      
      <div class="bg-purple-50 rounded-lg p-4 max-h-80 overflow-y-auto">
        <div v-if="activePredictions.length === 0" class="text-center text-gray-500 py-8">
          <div class="text-4xl mb-2">🎯</div>
          <div class="font-medium">No hay predicciones activas</div>
          <div class="text-sm">El sistema generará predicciones automáticamente</div>
        </div>
        
        <div v-else class="space-y-3">
          <div 
            v-for="prediction in activePredictions" 
            :key="prediction.id"
            class="bg-white p-4 rounded-lg border border-purple-200 shadow-sm"
          >
            <div class="flex justify-between items-start mb-3">
              <div>
                <div class="font-semibold text-purple-700">{{ prediction.method || 'Predicción IA' }}</div>
                <div class="text-sm text-purple-600">ID: {{ prediction.id.slice(-8) }}</div>
              </div>
              <div class="text-right">
                <div class="text-sm text-purple-600">{{ formatTime(prediction.timestamp) }}</div>
                <div class="text-xs text-purple-500">
                  Confianza: {{ Math.round((prediction.confidence || 0) * 100) }}%
                </div>
              </div>
            </div>
            
            <!-- Números predichos -->
            <div class="mb-3">
              <div class="text-sm font-medium text-gray-700 mb-2">Números Predichos:</div>
              <div class="flex flex-wrap gap-1">
                <span 
                  v-for="num in prediction.predicted_numbers.slice(0, 15)" 
                  :key="prediction.id + '-' + num"
                  class="inline-block w-7 h-7 rounded-full text-white flex items-center justify-center text-xs font-bold"
                  :class="getNumberColorClass(num)"
                >
                  {{ num }}
                </span>
                <span v-if="prediction.predicted_numbers.length > 15" class="text-xs text-purple-500 flex items-center px-2">
                  +{{ prediction.predicted_numbers.length - 15 }} más
                </span>
              </div>
            </div>
            
            <!-- Descripción de la predicción -->
            <div v-if="prediction.description" class="text-sm text-gray-600 bg-gray-50 p-2 rounded">
              {{ prediction.description }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Historial de resultados -->
    <div class="bg-gray-50 rounded-lg p-4">
      <div class="flex justify-between items-center mb-3">
        <h3 class="text-lg font-semibold text-gray-700">Historial de Resultados</h3>
        <button 
          @click="clearHistory"
          class="text-xs bg-gray-200 hover:bg-gray-300 text-gray-600 px-3 py-1 rounded"
        >
          Limpiar Historial
        </button>
      </div>
      
      <div class="max-h-32 overflow-y-auto">
        <div v-if="recentResults.length === 0" class="text-center text-gray-500 py-4">
          No hay resultados recientes
        </div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          <div 
            v-for="result in recentResults.slice(0, 12)" 
            :key="result.id"
            class="flex items-center gap-2 bg-white p-2 rounded border text-sm"
          >
            <div class="w-8 h-8 rounded-full text-white flex items-center justify-center text-sm font-bold"
                 :class="getNumberColorClass(result.number)">
              {{ result.number }}
            </div>
            <div class="flex-1">
              <div class="font-medium" :class="result.isWin ? 'text-green-600' : 'text-red-600'">
                {{ result.isWin ? '✓ WIN' : '✗ LOSS' }}
              </div>
              <div class="text-xs text-gray-500">{{ formatTime(result.timestamp) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Controles adicionales -->
    <div class="mt-4 flex justify-between items-center pt-3 border-t border-gray-200">
      <div class="text-sm text-gray-600">
        <span class="font-medium">Sistema:</span> 
        <span :class="serviceRunning ? 'text-green-600' : 'text-red-600'">
          {{ serviceRunning ? 'Funcionando automáticamente' : 'Detenido' }}
        </span>
      </div>
      <div class="flex gap-2">
        <button 
          @click="refreshData"
          class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm transition-colors"
          :disabled="loading"
        >
          Actualizar Datos
        </button>
        <button 
          @click="showSystemInfo = !showSystemInfo"
          class="px-3 py-1 bg-gray-500 hover:bg-gray-600 text-white rounded text-sm transition-colors"
        >
          {{ showSystemInfo ? 'Ocultar Info' : 'Info Sistema' }}
        </button>
      </div>
    </div>

    <!-- Información del sistema (expandible) -->
    <div v-if="showSystemInfo" class="mt-4 bg-gray-100 p-3 rounded-lg text-sm">
      <div class="font-medium text-gray-700 mb-2">Información del Sistema:</div>
      <div class="grid grid-cols-2 gap-2 text-xs">
        <div><strong>Estado Redis:</strong> {{ systemStatus }}</div>
        <div><strong>Componentes:</strong> Activos</div>
        <div><strong>Modo:</strong> Automático</div>
        <div><strong>Versión:</strong> 2.0</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getRouletteStats, getLatestNumber, makePrediction, getAIStats, getMonitorStatus, startMonitor, stopMonitor } from '~/utils/api'

// Estado del sistema
const serviceRunning = ref(false)
const loading = ref(false)
const systemStatus = ref('unknown')
const systemMessage = ref('')
const showSystemInfo = ref(false)

// Datos del juego
const latestNumber = ref(null)
const stats = ref({ wins: 0, losses: 0, total_predictions: 0 })
const activePredictions = ref([])
const recentResults = ref([])
const lastUpdate = ref(new Date().toISOString())

// Intervalos de actualización
let updateInterval = null
let statusInterval = null

// Computed properties
const winRate = computed(() => {
  if (stats.value.total_predictions === 0) return 0
  return Math.round((stats.value.wins / stats.value.total_predictions) * 100)
})

const systemStatusClass = computed(() => {
  switch (systemStatus.value) {
    case 'running': return 'bg-green-100 text-green-800 border border-green-300'
    case 'stopped': return 'bg-red-100 text-red-800 border border-red-300'
    case 'error': return 'bg-red-100 text-red-800 border border-red-300'
    default: return 'bg-gray-100 text-gray-800 border border-gray-300'
  }
})

const systemStatusText = computed(() => {
  switch (systemStatus.value) {
    case 'running': return 'Sistema Operativo'
    case 'stopped': return 'Sistema Pausado'
    case 'error': return 'Error del Sistema'
    default: return 'Estado Desconocido'
  }
})

// Métodos principales
const toggleAutoService = async () => {
  loading.value = true
  try {
    const endpoint = serviceRunning.value ? '/automatic-service/stop' : '/automatic-service/start'
    const response = serviceRunning.value ? await stopMonitor() : await startMonitor()
    
    if (response) {
      serviceRunning.value = !serviceRunning.value
      await refreshData()
    } else {
      console.error('Error toggling service')
      alert('Error al cambiar estado del servicio')
    }
  } catch (error) {
    console.error('Error toggling service:', error)
    alert('Error de conexión con el servidor')
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  try {
    await Promise.all([
      getServiceStatus(),
      getLatestNumberData(),
      getPredictions()
    ])
    lastUpdate.value = new Date().toISOString()
  } catch (error) {
    console.error('Error refreshing data:', error)
  }
}

const getServiceStatus = async () => {
  try {
    const monitorStatus = await getMonitorStatus()
    const aiStats = await getAIStats()

    if (monitorStatus) {
      serviceRunning.value = monitorStatus.monitor_active || false
      systemStatus.value = monitorStatus.redis_connected ? 'running' : 'error'
      systemMessage.value = monitorStatus.status_message || ''
    }

    if (aiStats) {
      stats.value = {
        wins: aiStats.total_wins || 0,
        losses: aiStats.total_losses || 0,
        total_predictions: aiStats.total_predictions || 0
      }
    }
  } catch (error) {
    console.error('Error getting service status:', error)
    systemStatus.value = 'error'
  }
}

const getLatestNumberData = async () => {
  try {
    const response = await getLatestNumber()

    if (response && response.number !== undefined) {
      const newNumber = response

      if (!latestNumber.value || latestNumber.value.number !== newNumber.number) {
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
    // Simular predicciones activas mientras implementamos la nueva API
    const aiStats = await getAIStats()

    if (aiStats && aiStats.pending_predictions > 0) {
      // Generar predicción de ejemplo
      const prediction = await makePrediction('groups')
      if (prediction) {
        activePredictions.value = [{
          id: prediction.id || Date.now().toString(),
          method: 'Predicción IA Automática',
          timestamp: new Date().toISOString(),
          confidence: prediction.confidence || 0.75,
          predicted_numbers: prediction.predicted_numbers || [],
          description: prediction.reasoning || 'Predicción generada automáticamente'
        }]
      }
    } else {
      activePredictions.value = []
    }
  } catch (error) {
    console.error('Error getting predictions:', error)
  }
}

const evaluatePredictions = (resultNumber) => {
  activePredictions.value.forEach(prediction => {
    const isWin = prediction.predicted_numbers.includes(resultNumber)
    
    recentResults.value.unshift({
      id: Date.now() + Math.random(),
      number: resultNumber,
      isWin: isWin,
      timestamp: new Date().toISOString(),
      predictionId: prediction.id
    })
    
    if (recentResults.value.length > 50) {
      recentResults.value.pop()
    }
  })
}

// Métodos auxiliares
const getNumberColor = (number) => {
  if (number === 0) return 'Verde'
  const reds = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
  return reds.includes(number) ? 'Rojo' : 'Negro'
}

const getNumberColorClass = (number) => {
  if (number === 0) return 'bg-green-600'
  const reds = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
  return reds.includes(number) ? 'bg-red-600' : 'bg-gray-800'
}

const clearHistory = () => {
  recentResults.value = []
  if (confirm('¿Resetear también las estadísticas?')) {
    stats.value = { wins: 0, losses: 0, total_predictions: 0 }
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Lifecycle hooks
onMounted(() => {
  refreshData()
  
  // Actualizar datos cada 3 segundos
  updateInterval = setInterval(refreshData, 3000)
  
  // Actualizar estado del servicio cada 30 segundos
  statusInterval = setInterval(getServiceStatus, 30000)
})

onUnmounted(() => {
  if (updateInterval) clearInterval(updateInterval)
  if (statusInterval) clearInterval(statusInterval)
})
</script>

<style scoped>
/* Animaciones */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.animate-pulse {
  animation: pulse 2s infinite;
}

/* Transiciones */
.transition-colors {
  transition: background-color 0.2s ease-in-out, color 0.2s ease-in-out;
}

/* Scrollbar personalizado */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style> 