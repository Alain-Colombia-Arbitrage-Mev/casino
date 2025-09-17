<template>
  <div class="strategy-analysis-panel bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 rounded-xl p-6 shadow-2xl">
    <!-- Header con animación -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-4">
        <div class="relative">
          <div class="w-12 h-12 bg-gradient-to-r from-purple-500 via-pink-500 to-red-500 rounded-xl flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform duration-300">
            <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
          </div>
          <div v-if="isAnalyzing" class="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-pulse"></div>
        </div>
        <div>
          <h2 class="text-2xl font-bold text-white">Análisis de Estrategias IA</h2>
          <p class="text-purple-200 text-sm">Rendimiento en tiempo real y descubrimiento automático</p>
        </div>
      </div>

      <div class="flex space-x-2">
        <button
          @click="triggerDiscovery"
          :disabled="isAnalyzing"
          class="px-4 py-2 bg-gradient-to-r from-orange-500 to-red-600 text-white rounded-lg hover:from-orange-600 hover:to-red-700 disabled:opacity-50 transition-all duration-200 flex items-center space-x-2"
        >
          <svg v-if="isAnalyzing" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
          </svg>
          <span>{{ isAnalyzing ? 'Analizando...' : 'Descubrir Estrategias' }}</span>
        </button>

        <button
          @click="refreshData"
          class="px-3 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- Estadísticas globales mejoradas -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-gradient-to-br from-emerald-800/60 to-green-900/60 rounded-xl p-4 border border-emerald-500/30 backdrop-blur-sm">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-2xl font-bold text-emerald-400">{{ bestStrategy?.success_rate || 0 }}%</div>
            <div class="text-sm text-emerald-200">Mejor Estrategia</div>
            <div class="text-xs text-emerald-300 mt-1">{{ bestStrategy?.name || 'N/A' }}</div>
          </div>
          <div class="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>
            </svg>
          </div>
        </div>
      </div>

      <div class="bg-gradient-to-br from-blue-800/60 to-indigo-900/60 rounded-xl p-4 border border-blue-500/30 backdrop-blur-sm">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-2xl font-bold text-blue-400">{{ totalPredictions }}</div>
            <div class="text-sm text-blue-200">Total Predicciones</div>
            <div class="text-xs text-blue-300 mt-1">Todas las estrategias</div>
          </div>
          <div class="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
          </div>
        </div>
      </div>

      <div class="bg-gradient-to-br from-purple-800/60 to-pink-900/60 rounded-xl p-4 border border-purple-500/30 backdrop-blur-sm">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-2xl font-bold text-purple-400">{{ strategies.length }}</div>
            <div class="text-sm text-purple-200">Estrategias Activas</div>
            <div class="text-xs text-purple-300 mt-1">{{ newStrategiesCount }} nuevas</div>
          </div>
          <div class="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>
            </svg>
          </div>
        </div>
      </div>

      <div class="bg-gradient-to-br from-amber-800/60 to-yellow-900/60 rounded-xl p-4 border border-amber-500/30 backdrop-blur-sm">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-2xl font-bold text-amber-400">{{ averageSuccessRate }}%</div>
            <div class="text-sm text-amber-200">Promedio General</div>
            <div class="text-xs text-amber-300 mt-1">Todas las estrategias</div>
          </div>
          <div class="w-12 h-12 bg-amber-500/20 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7a4 4 0 11-8 0 4 4 0 018 0zM9 14a6 6 0 00-6 6v1h12v-1a6 6 0 00-6-6zM21 12h-6m3-3v6"></path>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Lista de estrategias mejorada -->
    <div class="bg-black/20 rounded-xl p-6 border border-purple-500/30 backdrop-blur-sm">
      <h3 class="text-xl font-semibold text-white mb-4 flex items-center">
        <svg class="w-5 h-5 mr-2 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        Rendimiento por Estrategia
      </h3>

      <div class="space-y-4">
        <div v-for="strategy in sortedStrategies" :key="strategy.id"
             class="bg-gradient-to-r from-gray-800/50 to-gray-900/50 rounded-lg p-4 border border-gray-600/30 hover:border-purple-500/50 transition-all duration-300 transform hover:scale-[1.02]">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center space-x-3">
              <div :class="getStrategyIconClass(strategy.type)" class="w-10 h-10 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getStrategyIcon(strategy.type)"></path>
                </svg>
              </div>
              <div>
                <h4 class="text-lg font-semibold text-white">{{ strategy.name }}</h4>
                <p class="text-sm text-gray-400 capitalize">{{ strategy.type.replace('_', ' ') }}</p>
              </div>
            </div>

            <div class="flex items-center space-x-4">
              <!-- Badge de rendimiento -->
              <div :class="getPerformanceBadgeClass(strategy.success_rate)"
                   class="px-3 py-1 rounded-full text-sm font-bold">
                {{ strategy.success_rate || 0 }}%
              </div>

              <!-- Confianza -->
              <div class="text-center">
                <div class="text-sm text-gray-400">Confianza</div>
                <div class="text-white font-bold">{{ Math.round((strategy.confidence || 0) * 100) }}%</div>
              </div>

              <!-- Total predicciones -->
              <div class="text-center">
                <div class="text-sm text-gray-400">Predicciones</div>
                <div class="text-white font-bold">{{ strategy.total_predictions || 0 }}</div>
              </div>
            </div>
          </div>

          <!-- Barra de progreso de rendimiento -->
          <div class="w-full bg-gray-700 rounded-full h-2 mb-2">
            <div
              :class="getProgressBarClass(strategy.success_rate)"
              class="h-2 rounded-full transition-all duration-500 ease-out"
              :style="{ width: Math.min((strategy.success_rate || 0), 100) + '%' }"
            ></div>
          </div>

          <!-- Información adicional -->
          <div class="flex justify-between text-xs text-gray-400">
            <span>Creada: {{ formatDate(strategy.created) }}</span>
            <span>Última actualización: {{ formatDate(strategy.last_updated) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Análisis de grupos de números -->
    <div v-if="groupAnalysis" class="mt-6 bg-black/20 rounded-xl p-6 border border-indigo-500/30 backdrop-blur-sm">
      <h3 class="text-xl font-semibold text-white mb-4 flex items-center">
        <svg class="w-5 h-5 mr-2 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
        </svg>
        Análisis por Grupos de Números
      </h3>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Docenas -->
        <div class="bg-gradient-to-br from-blue-900/40 to-cyan-900/40 rounded-lg p-4 border border-blue-500/30">
          <h4 class="text-lg font-semibold text-blue-300 mb-3">Docenas</h4>
          <div class="space-y-2">
            <div v-for="(dozen, index) in groupAnalysis.dozens" :key="index" class="flex items-center justify-between">
              <span class="text-blue-200">{{ getDozenName(index) }}</span>
              <div class="flex items-center space-x-2">
                <div class="w-16 bg-blue-800 rounded-full h-2">
                  <div class="bg-blue-400 h-2 rounded-full transition-all duration-500"
                       :style="{ width: (dozen.win_rate || 0) + '%' }"></div>
                </div>
                <span class="text-blue-400 font-bold text-sm">{{ dozen.win_rate || 0 }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Columnas -->
        <div class="bg-gradient-to-br from-purple-900/40 to-pink-900/40 rounded-lg p-4 border border-purple-500/30">
          <h4 class="text-lg font-semibold text-purple-300 mb-3">Columnas</h4>
          <div class="space-y-2">
            <div v-for="(column, index) in groupAnalysis.columns" :key="index" class="flex items-center justify-between">
              <span class="text-purple-200">Columna {{ index + 1 }}</span>
              <div class="flex items-center space-x-2">
                <div class="w-16 bg-purple-800 rounded-full h-2">
                  <div class="bg-purple-400 h-2 rounded-full transition-all duration-500"
                       :style="{ width: (column.win_rate || 0) + '%' }"></div>
                </div>
                <span class="text-purple-400 font-bold text-sm">{{ column.win_rate || 0 }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Par/Impar y Color -->
        <div class="bg-gradient-to-br from-emerald-900/40 to-teal-900/40 rounded-lg p-4 border border-emerald-500/30">
          <h4 class="text-lg font-semibold text-emerald-300 mb-3">Características</h4>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-emerald-200">Par</span>
              <span class="text-emerald-400 font-bold">{{ groupAnalysis.even?.win_rate || 0 }}%</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-emerald-200">Impar</span>
              <span class="text-emerald-400 font-bold">{{ groupAnalysis.odd?.win_rate || 0 }}%</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-red-200">Rojo</span>
              <span class="text-red-400 font-bold">{{ groupAnalysis.red?.win_rate || 0 }}%</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-200">Negro</span>
              <span class="text-gray-400 font-bold">{{ groupAnalysis.black?.win_rate || 0 }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mensaje de estado -->
    <div v-if="statusMessage" class="mt-4 p-4 rounded-lg border"
         :class="statusMessage.type === 'success' ? 'bg-green-900/50 border-green-500/50 text-green-200' : 'bg-red-900/50 border-red-500/50 text-red-200'">
      <p class="text-sm">{{ statusMessage.text }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { getAIStrategies, getStrategyPerformance, triggerStrategyDiscovery, getAIStats } from '~/utils/api'

// Estado reactivo
const strategies = ref([])
const performance = ref(null)
const groupAnalysis = ref(null)
const isAnalyzing = ref(false)
const statusMessage = ref(null)
const newStrategiesCount = ref(0)
let refreshInterval: NodeJS.Timeout | null = null

// Computed properties
const sortedStrategies = computed(() => {
  return [...strategies.value].sort((a, b) => (b.success_rate || 0) - (a.success_rate || 0))
})

const bestStrategy = computed(() => {
  return sortedStrategies.value[0] || null
})

const totalPredictions = computed(() => {
  return strategies.value.reduce((sum, strategy) => sum + (strategy.total_predictions || 0), 0)
})

const averageSuccessRate = computed(() => {
  const activeStrategies = strategies.value.filter(s => s.total_predictions > 0)
  if (activeStrategies.length === 0) return 0

  const sum = activeStrategies.reduce((sum, strategy) => sum + (strategy.success_rate || 0), 0)
  return Math.round(sum / activeStrategies.length)
})

// Métodos
const refreshData = async () => {
  try {
    const [strategiesData, performanceData, aiStats] = await Promise.all([
      getAIStrategies(),
      getStrategyPerformance(),
      getAIStats()
    ])

    if (strategiesData) {
      const oldCount = strategies.value.length
      strategies.value = strategiesData
      newStrategiesCount.value = Math.max(0, strategiesData.length - oldCount)
    }

    if (performanceData) {
      performance.value = performanceData
    }

    if (aiStats && aiStats.detailed_stats) {
      groupAnalysis.value = aiStats.detailed_stats
    }
  } catch (error) {
    console.error('Error refreshing strategy data:', error)
    statusMessage.value = {
      type: 'error',
      text: 'Error al actualizar datos de estrategias'
    }
  }
}

const triggerDiscovery = async () => {
  isAnalyzing.value = true
  statusMessage.value = null

  try {
    const result = await triggerStrategyDiscovery()

    if (result) {
      statusMessage.value = {
        type: 'success',
        text: 'Descubrimiento de estrategias iniciado. Los resultados aparecerán en breve.'
      }

      // Actualizar datos después de un delay
      setTimeout(async () => {
        await refreshData()
        isAnalyzing.value = false
      }, 3000)
    } else {
      statusMessage.value = {
        type: 'error',
        text: 'Error al iniciar descubrimiento de estrategias'
      }
      isAnalyzing.value = false
    }
  } catch (error) {
    console.error('Error triggering discovery:', error)
    statusMessage.value = {
      type: 'error',
      text: 'Error de conexión al activar descubrimiento'
    }
    isAnalyzing.value = false
  }
}

// Métodos de utilidad
const getStrategyIconClass = (type: string) => {
  const classes = {
    'gap_analysis': 'bg-gradient-to-r from-blue-600 to-cyan-600',
    'contrarian_analysis': 'bg-gradient-to-r from-red-600 to-pink-600',
    'pattern_analysis': 'bg-gradient-to-r from-purple-600 to-indigo-600',
    'spatial_analysis': 'bg-gradient-to-r from-green-600 to-emerald-600',
    'frequency_analysis': 'bg-gradient-to-r from-yellow-600 to-orange-600'
  }
  return classes[type] || 'bg-gradient-to-r from-gray-600 to-slate-600'
}

const getStrategyIcon = (type: string) => {
  const icons = {
    'gap_analysis': 'M13 10V3L4 14h7v7l9-11h-7z',
    'contrarian_analysis': 'M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4',
    'pattern_analysis': 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    'spatial_analysis': 'M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z',
    'frequency_analysis': 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
  }
  return icons[type] || 'M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z'
}

const getPerformanceBadgeClass = (successRate: number) => {
  if (successRate >= 70) return 'bg-gradient-to-r from-emerald-500 to-green-600 text-white'
  if (successRate >= 50) return 'bg-gradient-to-r from-yellow-500 to-orange-600 text-white'
  if (successRate >= 30) return 'bg-gradient-to-r from-orange-500 to-red-600 text-white'
  return 'bg-gradient-to-r from-red-500 to-pink-600 text-white'
}

const getProgressBarClass = (successRate: number) => {
  if (successRate >= 70) return 'bg-gradient-to-r from-emerald-500 to-green-500'
  if (successRate >= 50) return 'bg-gradient-to-r from-yellow-500 to-orange-500'
  if (successRate >= 30) return 'bg-gradient-to-r from-orange-500 to-red-500'
  return 'bg-gradient-to-r from-red-500 to-pink-500'
}

const formatDate = (dateString: string) => {
  try {
    return new Date(dateString).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return 'N/A'
  }
}

const getDozenName = (index: number) => {
  const names = ['1ª (1-12)', '2ª (13-24)', '3ª (25-36)']
  return names[index] || `Docena ${index + 1}`
}

// Lifecycle
onMounted(async () => {
  await refreshData()

  // Auto-refresh cada 30 segundos
  refreshInterval = setInterval(refreshData, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
})

// Limpiar mensaje de estado después de 5 segundos
watch(() => statusMessage.value, (newMessage) => {
  if (newMessage) {
    setTimeout(() => {
      statusMessage.value = null
    }, 5000)
  }
})
</script>

<style scoped>
.strategy-analysis-panel {
  min-height: 600px;
}

/* Animaciones personalizadas */
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.strategy-card {
  animation: slideInUp 0.5s ease-out;
}

/* Efectos de hover mejorados */
.strategy-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
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
</style>