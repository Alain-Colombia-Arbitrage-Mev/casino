<template>
  <div class="ai-prediction-panel bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 rounded-xl p-6 shadow-2xl min-h-[800px]">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
          <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
          </svg>
        </div>
        <div>
          <h2 class="text-xl font-bold text-white">Sistema de Predicción IA</h2>
          <p class="text-purple-200 text-sm">Análisis inteligente de patrones</p>
        </div>
      </div>
      
      <div class="flex space-x-2">
        <button
          @click="makePredictionHandler"
          :disabled="isLoading"
          class="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 transition-all duration-200 flex items-center space-x-2"
        >
          <svg v-if="isLoading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>{{ isLoading ? 'Analizando...' : 'Nueva Predicción' }}</span>
        </button>
        
        <button 
          @click="refreshStats"
          class="px-3 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- Última Predicción -->
    <div v-if="currentPrediction" class="mb-6 bg-black/30 rounded-lg p-4 border border-purple-500/30">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-lg font-semibold text-white">Predicción Actual</h3>
        <div class="flex items-center space-x-2">
          <span class="text-sm text-purple-200">Confianza:</span>
          <div class="bg-gradient-to-r from-yellow-400 to-orange-500 text-black px-2 py-1 rounded text-sm font-bold">
            {{ Math.round(currentPrediction.confidence * 100) }}%
          </div>
        </div>
      </div>
      
      <!-- Grupos de Predicción -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
        <div v-for="(numbers, groupName) in currentPrediction.prediction_groups" :key="groupName" 
             class="bg-gradient-to-br from-indigo-800/50 to-purple-800/50 rounded-lg p-3 border border-indigo-400/30">
          <h4 class="text-sm font-semibold text-indigo-200 mb-2 capitalize">
            {{ formatGroupName(groupName) }}
          </h4>
          <div class="flex flex-wrap gap-1">
            <span v-for="number in numbers" :key="number" 
                  :class="getNumberColorClass(number)"
                  class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shadow-lg">
              {{ number }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- Razonamiento -->
      <div class="bg-gray-800/50 rounded-lg p-3">
        <h4 class="text-sm font-semibold text-gray-300 mb-2">Análisis:</h4>
        <p class="text-sm text-gray-400">{{ currentPrediction.reasoning }}</p>
      </div>
    </div>

    <!-- Estadísticas de IA Mejoradas -->
    <div v-if="aiStats" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-gradient-to-br from-green-800/60 to-emerald-800/60 rounded-xl p-4 text-center border border-green-400/30 backdrop-blur-sm transform hover:scale-105 transition-all duration-300 animate-fadeInUp">
        <div class="flex items-center justify-center mb-2">
          <div class="w-8 h-8 bg-green-500/20 rounded-lg flex items-center justify-center">
            <svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
        </div>
        <div class="text-2xl font-bold text-green-400 animate-pulse">{{ aiStats.total_wins || 0 }}</div>
        <div class="text-sm text-green-200">Victorias</div>
      </div>

      <div class="bg-gradient-to-br from-red-800/60 to-pink-800/60 rounded-xl p-4 text-center border border-red-400/30 backdrop-blur-sm transform hover:scale-105 transition-all duration-300 animate-fadeInUp" style="animation-delay: 0.1s">
        <div class="flex items-center justify-center mb-2">
          <div class="w-8 h-8 bg-red-500/20 rounded-lg flex items-center justify-center">
            <svg class="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </div>
        </div>
        <div class="text-2xl font-bold text-red-400">{{ aiStats.total_losses || 0 }}</div>
        <div class="text-sm text-red-200">Derrotas</div>
      </div>

      <div class="bg-gradient-to-br from-blue-800/60 to-cyan-800/60 rounded-xl p-4 text-center border border-blue-400/30 backdrop-blur-sm transform hover:scale-105 transition-all duration-300 animate-fadeInUp" style="animation-delay: 0.2s">
        <div class="flex items-center justify-center mb-2">
          <div class="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
            <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
          </div>
        </div>
        <div class="text-2xl font-bold text-blue-400">{{ aiStats.total_predictions || 0 }}</div>
        <div class="text-sm text-blue-200">Total Predicciones</div>
      </div>

      <div class="bg-gradient-to-br from-yellow-800/60 to-orange-800/60 rounded-xl p-4 text-center border border-yellow-400/30 backdrop-blur-sm transform hover:scale-105 transition-all duration-300 animate-fadeInUp" style="animation-delay: 0.3s">
        <div class="flex items-center justify-center mb-2">
          <div class="w-8 h-8 bg-yellow-500/20 rounded-lg flex items-center justify-center">
            <svg class="w-4 h-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7a4 4 0 11-8 0 4 4 0 018 0zM9 14a6 6 0 00-6 6v1h12v-1a6 6 0 00-6-6zM21 12h-6m3-3v6"></path>
            </svg>
          </div>
        </div>
        <div class="text-2xl font-bold text-yellow-400">{{ aiStats.overall_win_rate || 0 }}%</div>
        <div class="text-sm text-yellow-200">Tasa Éxito</div>
      </div>
    </div>

    <!-- Estadísticas por Grupo -->
    <div v-if="aiStats && aiStats.group_stats" class="bg-black/30 rounded-lg p-4 border border-purple-500/30 mb-6">
      <h3 class="text-lg font-semibold text-white mb-4">Rendimiento por Grupo</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
        <div v-for="(stats, groupName) in aiStats.group_stats" :key="groupName"
             class="bg-gradient-to-br from-indigo-800/50 to-purple-800/50 rounded-lg p-3 border border-indigo-400/30">
          <h4 class="text-sm font-semibold text-indigo-200 mb-2 capitalize">
            {{ formatGroupName(groupName) }}
          </h4>
          <div class="space-y-1">
            <div class="flex justify-between text-xs">
              <span class="text-green-400">Victorias:</span>
              <span class="text-white font-bold">{{ stats.wins || 0 }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-red-400">Derrotas:</span>
              <span class="text-white font-bold">{{ stats.losses || 0 }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-blue-400">Total:</span>
              <span class="text-white font-bold">{{ stats.total || 0 }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-yellow-400">Éxito:</span>
              <span class="text-white font-bold">{{ stats.win_rate || 0 }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Estadísticas Detalladas: Columnas, Docenas, Par/Impar, Rojo/Negro -->
    <div v-if="aiStats && aiStats.detailed_stats" class="bg-black/30 rounded-lg p-4 border border-purple-500/30 mb-6">
      <h3 class="text-lg font-semibold text-white mb-4">Estadísticas Detalladas</h3>
      
      <!-- Columnas -->
      <div class="mb-4">
        <h4 class="text-md font-semibold text-purple-200 mb-2">Columnas</h4>
        <div class="grid grid-cols-3 gap-3">
          <div v-for="(stats, index) in aiStats.detailed_stats.columns" :key="`col-${index}`"
               class="bg-gradient-to-br from-blue-800/50 to-cyan-800/50 rounded-lg p-3 border border-blue-400/30">
            <h5 class="text-sm font-semibold text-blue-200 mb-2">Columna {{ index + 1 }}</h5>
            <div class="space-y-1">
              <div class="flex justify-between text-xs">
                <span class="text-green-400">Victorias:</span>
                <span class="text-white font-bold">{{ stats.wins || 0 }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-red-400">Derrotas:</span>
                <span class="text-white font-bold">{{ stats.losses || 0 }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-yellow-400">Éxito:</span>
                <span class="text-white font-bold">{{ stats.win_rate || 0 }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Docenas -->
      <div class="mb-4">
        <h4 class="text-md font-semibold text-purple-200 mb-2">Docenas</h4>
        <div class="grid grid-cols-3 gap-3">
          <div v-for="(stats, index) in aiStats.detailed_stats.dozens" :key="`dozen-${index}`"
               class="bg-gradient-to-br from-indigo-800/50 to-purple-800/50 rounded-lg p-3 border border-indigo-400/30">
            <h5 class="text-sm font-semibold text-indigo-200 mb-2">{{ getDozenName(index) }}</h5>
            <div class="space-y-1">
              <div class="flex justify-between text-xs">
                <span class="text-green-400">Victorias:</span>
                <span class="text-white font-bold">{{ stats.wins || 0 }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-red-400">Derrotas:</span>
                <span class="text-white font-bold">{{ stats.losses || 0 }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-yellow-400">Éxito:</span>
                <span class="text-white font-bold">{{ stats.win_rate || 0 }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Par/Impar y Rojo/Negro -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <!-- Par -->
        <div v-if="aiStats.detailed_stats.even"
             class="bg-gradient-to-br from-gray-800/50 to-slate-800/50 rounded-lg p-3 border border-gray-400/30">
          <h5 class="text-sm font-semibold text-gray-200 mb-2">Par</h5>
          <div class="space-y-1">
            <div class="flex justify-between text-xs">
              <span class="text-green-400">Victorias:</span>
              <span class="text-white font-bold">{{ aiStats.detailed_stats.even.wins || 0 }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-red-400">Derrotas:</span>
              <span class="text-white font-bold">{{ aiStats.detailed_stats.even.losses || 0 }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-yellow-400">Éxito:</span>
              <span class="text-white font-bold">{{ aiStats.detailed_stats.even.win_rate || 0 }}%</span>
            </div>
          </div>
        </div>

        <!-- Impar -->
        <div v-if="aiStats.detailed_stats.odd"
             class="bg-gradient-to-br from-gray-700/50 to-slate-700/50 rounded-lg p-3 border border-gray-500/30">
          <h5 class="text-sm font-semibold text-gray-200 mb-2">Impar</h5>
          <div class="space-y-1">
            <div class="flex justify-between text-xs">
              <span class="text-green-400">Victorias:</span>
              <span class="text-white font-bold">{{ aiStats.detailed_stats.odd.wins || 0 }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-red-400">Derrotas:</span>
              <span class="text-white font-bold">{{ aiStats.detailed_stats.odd.losses || 0 }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-yellow-400">Éxito:</span>
              <span class="text-white font-bold">{{ aiStats.detailed_stats.odd.win_rate || 0 }}%</span>
            </div>
          </div>
        </div>

        <!-- Rojo -->
        <div v-if="aiStats.detailed_stats.red"
             class="bg-gradient-to-br from-red-800/50 to-rose-800/50 rounded-lg p-3 border border-red-400/30">
          <h5 class="text-sm font-semibold text-red-200 mb-2">Rojo</h5>
          <div class="space-y-1">
            <div class="flex justify-between text-xs">
              <span class="text-green-400">Victorias:</span>
              <span class="text-white font-bold">{{ aiStats.detailed_stats.red.wins || 0 }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-red-400">Derrotas:</span>
              <span class="text-white font-bold">{{ aiStats.detailed_stats.red.losses || 0 }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-yellow-400">Éxito:</span>
              <span class="text-white font-bold">{{ aiStats.detailed_stats.red.win_rate || 0 }}%</span>
            </div>
          </div>
        </div>

        <!-- Negro -->
        <div v-if="aiStats.detailed_stats.black"
             class="bg-gradient-to-br from-gray-900/50 to-black/50 rounded-lg p-3 border border-gray-600/30">
          <h5 class="text-sm font-semibold text-gray-200 mb-2">Negro</h5>
          <div class="space-y-1">
            <div class="flex justify-between text-xs">
              <span class="text-green-400">Victorias:</span>
              <span class="text-white font-bold">{{ aiStats.detailed_stats.black.wins || 0 }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-red-400">Derrotas:</span>
              <span class="text-white font-bold">{{ aiStats.detailed_stats.black.losses || 0 }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-yellow-400">Éxito:</span>
              <span class="text-white font-bold">{{ aiStats.detailed_stats.black.win_rate || 0 }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Predicciones Pendientes -->
    <div v-if="aiStats && aiStats.pending_predictions > 0" class="bg-orange-800/30 rounded-lg p-4 border border-orange-500/30 mb-6">
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
          <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        <div>
          <h3 class="text-lg font-semibold text-orange-200">Predicciones Pendientes</h3>
          <p class="text-sm text-orange-300">
            Hay <span class="font-bold">{{ aiStats.pending_predictions }}</span> predicción(es) esperando verificación
          </p>
        </div>
      </div>
    </div>

    <!-- Historial de Resultados -->
    <div v-if="gameResults.length > 0" class="bg-black/30 rounded-lg p-4 border border-purple-500/30">
      <h3 class="text-lg font-semibold text-white mb-3">Últimos Resultados</h3>
      <div class="space-y-2 max-h-40 overflow-y-auto">
        <div v-for="result in gameResults.slice(0, 5)" :key="result.prediction_id" 
             class="flex items-center justify-between p-2 rounded bg-gray-800/50">
          <div class="flex items-center space-x-3">
            <div :class="result.is_winner ? 'bg-green-500' : 'bg-red-500'" 
                 class="w-3 h-3 rounded-full"></div>
            <span class="text-sm text-gray-300">
              Número: <span class="font-bold text-white">{{ result.actual_number }}</span>
            </span>
          </div>
          <div class="flex items-center space-x-2">
            <span class="text-xs text-gray-400">{{ formatTime(result.timestamp) }}</span>
            <span :class="result.is_winner ? 'text-green-400' : 'text-red-400'" 
                  class="text-sm font-semibold">
              {{ result.is_winner ? 'GANÓ' : 'PERDIÓ' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Mensaje de Estado -->
    <div v-if="statusMessage" class="mt-4 p-3 rounded-lg" 
         :class="statusMessage.type === 'success' ? 'bg-green-800/50 border border-green-400/30' : 'bg-red-800/50 border border-red-400/30'">
      <p :class="statusMessage.type === 'success' ? 'text-green-200' : 'text-red-200'" class="text-sm">
        {{ statusMessage.text }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { makePrediction, getAIStats, autoProcessPrediction, getPendingPredictions } from '~/utils/api'

// Props
const props = defineProps<{
  latestNumber?: number
}>()

// Reactive data
const isLoading = ref(false)
const currentPrediction = ref(null)
const aiStats = ref(null)
const gameResults = ref([])
const statusMessage = ref(null)
let statsInterval: NodeJS.Timeout | null = null

// Métodos
const makePredictionHandler = async () => {
  isLoading.value = true
  statusMessage.value = null
  
  try {
    const prediction = await makePrediction('groups')
    
    if (prediction) {
      currentPrediction.value = prediction
      statusMessage.value = {
        type: 'success',
        text: `Nueva predicción generada con ${Object.keys(prediction.prediction_groups).length} grupos de números`
      }
    } else {
      statusMessage.value = {
        type: 'error',
        text: 'Error al generar predicción'
      }
    }
  } catch (error) {
    console.error('Error making prediction:', error)
    statusMessage.value = {
      type: 'error',
      text: 'Error de conexión al generar predicción'
    }
  } finally {
    isLoading.value = false
  }
}

const refreshStats = async () => {
  try {
    const response = await getAIStats()
    if (response) {
      // El API devuelve los datos dentro de response.data
      const stats = response.data || response
      aiStats.value = stats
      console.log('📊 Estadísticas actualizadas:', {
        total_wins: stats.total_wins,
        total_losses: stats.total_losses,
        total_predictions: stats.total_predictions,
        overall_win_rate: stats.overall_win_rate,
        pending_predictions: stats.pending_predictions,
        group_stats: Object.keys(stats.group_stats || {}).length
      })
    }
  } catch (error) {
    console.error('Error refreshing stats:', error)
    // Reintentar en caso de error de conexión
    setTimeout(() => refreshStats(), 5000)
  }
}

const processNewNumber = async (number: number) => {
  if (!number || number < 0 || number > 36) return
  
  try {
    const result = await autoProcessPrediction(number, 'groups')
    
    if (result) {
      // Actualizar predicción actual
      if (result.new_prediction) {
        currentPrediction.value = result.new_prediction
      }
      
      // Agregar resultados anteriores al historial
      if (result.previous_results && result.previous_results.length > 0) {
        gameResults.value.unshift(...result.previous_results)
        gameResults.value = gameResults.value.slice(0, 10) // Mantener solo los últimos 10
      }
      
      // Actualizar estadísticas
      await refreshStats()
      
      statusMessage.value = {
        type: 'success',
        text: `Número ${number} procesado. ${result.previous_results?.length || 0} predicciones verificadas.`
      }
    }
  } catch (error) {
    console.error('Error processing new number:', error)
    statusMessage.value = {
      type: 'error',
      text: `Error al procesar número ${number}`
    }
  }
}

// Utilidades
const formatGroupName = (groupName: string) => {
  return groupName.replace('group_', 'Grupo ').replace('_', ' ')
}

const getNumberColorClass = (number: number) => {
  if (number === 0) return 'bg-green-600'
  
  const redNumbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
  return redNumbers.includes(number) ? 'bg-red-600' : 'bg-gray-800'
}

const formatTime = (timestamp: string) => {
  try {
    return new Date(timestamp).toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return ''
  }
}

const getDozenName = (index: number) => {
  const dozenNames = ['1ª Docena (1-12)', '2ª Docena (13-24)', '3ª Docena (25-36)']
  return dozenNames[index] || `Docena ${index + 1}`
}

// Watchers
watch(() => props.latestNumber, (newNumber) => {
  if (newNumber !== undefined) {
    processNewNumber(newNumber)
  }
})

// Lifecycle
onMounted(async () => {
  await refreshStats()
  await makePredictionHandler()
  
  // Configurar intervalo para actualizar estadísticas cada 30 segundos
  statsInterval = setInterval(async () => {
    await refreshStats()
  }, 30000)
})

onUnmounted(() => {
  if (statsInterval) {
    clearInterval(statsInterval)
    statsInterval = null
  }
})

// Expose methods
defineExpose({
  makePrediction: makePredictionHandler,
  refreshStats,
  processNewNumber
})
</script>

<style scoped>
.ai-prediction-panel {
  min-height: 400px;
}

/* Animaciones mejoradas */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes bounce {
  0%, 20%, 53%, 80%, 100% {
    transform: translate3d(0, 0, 0);
  }
  40%, 43% {
    transform: translate3d(0, -8px, 0);
  }
  70% {
    transform: translate3d(0, -4px, 0);
  }
  90% {
    transform: translate3d(0, -2px, 0);
  }
}

.animate-fadeInUp {
  animation: fadeInUp 0.6s ease-out;
}

.animate-slideInRight {
  animation: slideInRight 0.6s ease-out;
}

.animate-bounce {
  animation: bounce 2s infinite;
}

/* Transiciones suaves */
.transition-all {
  transition: all 0.3s ease;
}

/* Efectos hover mejorados */
.transform:hover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

/* Gradientes animados */
@keyframes gradientShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.bg-gradient-animate {
  background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
}

/* Scrollbar personalizado */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(147, 51, 234, 0.5);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(147, 51, 234, 0.7);
}

/* Efectos de cristal */
.backdrop-blur-sm {
  backdrop-filter: blur(8px);
}

/* Pulso suave para números importantes */
@keyframes softPulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

.animate-pulse {
  animation: softPulse 2s ease-in-out infinite;
}
</style>