<template>
  <div class="prediction-stats-container">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
          📊 Estadísticas de Predicciones
          <span v-if="loading" class="ml-2 text-sm text-blue-500">Cargando...</span>
        </h2>
        <div class="flex space-x-2">
          <select 
            v-model="daysPeriod" 
            @change="cargarEstadisticas"
            class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
          >
            <option value="7">Últimos 7 días</option>
            <option value="14">Últimos 14 días</option>
            <option value="30">Últimos 30 días</option>
          </select>
          <button 
            @click="cargarEstadisticas" 
            :disabled="loading"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 text-sm"
          >
            {{ loading ? 'Cargando...' : 'Actualizar' }}
          </button>
          <button 
            @click="resetearEstadisticas" 
            :disabled="loading"
            class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 text-sm"
          >
            Resetear
          </button>
        </div>
      </div>

      <!-- Estado de carga -->
      <div v-if="loading" class="flex items-center justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="ml-2 text-gray-600 dark:text-gray-400">Cargando estadísticas...</span>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
        <p class="text-red-700 dark:text-red-300">{{ error }}</p>
      </div>

      <!-- Estadísticas -->
      <div v-else-if="estadisticas">
        <!-- Resumen General -->
        <div class="grid md:grid-cols-4 gap-4 mb-8">
          <div class="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-4 text-white">
            <h3 class="text-sm font-semibold mb-1">🎯 Predicción Individual</h3>
            <div class="text-2xl font-bold">{{ formatearPorcentaje(estadisticas.group_statistics.individual?.porcentaje) }}%</div>
            <p class="text-xs opacity-90">{{ estadisticas.group_statistics.individual?.aciertos || 0 }}/{{ estadisticas.group_statistics.individual?.total || 0 }}</p>
          </div>

          <div class="bg-gradient-to-r from-green-500 to-teal-600 rounded-lg p-4 text-white">
            <h3 class="text-sm font-semibold mb-1">🎲 Grupo 20</h3>
            <div class="text-2xl font-bold">{{ formatearPorcentaje(estadisticas.group_statistics.grupo_20?.porcentaje) }}%</div>
            <p class="text-xs opacity-90">{{ estadisticas.group_statistics.grupo_20?.aciertos || 0 }}/{{ estadisticas.group_statistics.grupo_20?.total || 0 }}</p>
          </div>

          <div class="bg-gradient-to-r from-orange-500 to-red-600 rounded-lg p-4 text-white">
            <h3 class="text-sm font-semibold mb-1">🎯 Grupo 12</h3>
            <div class="text-2xl font-bold">{{ formatearPorcentaje(estadisticas.group_statistics.grupo_12?.porcentaje) }}%</div>
            <p class="text-xs opacity-90">{{ estadisticas.group_statistics.grupo_12?.aciertos || 0 }}/{{ estadisticas.group_statistics.grupo_12?.total || 0 }}</p>
          </div>

          <div class="bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg p-4 text-white">
            <h3 class="text-sm font-semibold mb-1">🔥 Grupo 10</h3>
            <div class="text-2xl font-bold">{{ formatearPorcentaje(estadisticas.group_statistics.grupo_10?.porcentaje) }}%</div>
            <p class="text-xs opacity-90">{{ estadisticas.group_statistics.grupo_10?.aciertos || 0 }}/{{ estadisticas.group_statistics.grupo_10?.total || 0 }}</p>
          </div>
        </div>

        <!-- Estadísticas Detalladas por Grupo -->
        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 mb-8">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">📈 Rendimiento por Grupo</h3>
          <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="(stats, groupName) in estadisticas.group_statistics" :key="groupName" 
                 class="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
              <div class="flex items-center justify-between mb-2">
                <h4 class="font-medium text-gray-900 dark:text-white capitalize">
                  {{ String(groupName).replace('_', ' ') }}
                </h4>
                <span :class="getPerformanceClass(stats.porcentaje)"
                      class="px-2 py-1 rounded text-xs font-medium">
                  {{ formatearPorcentaje(stats.porcentaje) }}%
                </span>
              </div>
              <div class="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                <div class="flex justify-between">
                  <span>Aciertos:</span>
                  <span class="text-green-600 dark:text-green-400 font-medium">{{ stats.aciertos || 0 }}</span>
                </div>
                <div class="flex justify-between">
                  <span>Total:</span>
                  <span>{{ stats.total || 0 }}</span>
                </div>
                <div class="flex justify-between">
                  <span>Fallos:</span>
                  <span class="text-red-600 dark:text-red-400 font-medium">{{ (stats.total || 0) - (stats.aciertos || 0) }}</span>
                </div>
              </div>
              <!-- Barra de progreso -->
              <div class="mt-3">
                <div class="bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                  <div :class="getProgressBarClass(stats.porcentaje)"
                       :style="{ width: `${Math.min(stats.porcentaje || 0, 100)}%` }"
                       class="h-2 rounded-full transition-all duration-300">
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Análisis de Rendimiento Reciente -->
        <div v-if="estadisticas.recent_performance && !estadisticas.recent_performance.error" 
             class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 mb-8">
          <h3 class="text-lg font-semibold text-blue-900 dark:text-blue-300 mb-4">
            🔍 Análisis de Rendimiento ({{ daysPeriod }} días)
          </h3>
          
          <div class="grid md:grid-cols-2 gap-6">
            <!-- Mejores Grupos -->
            <div>
              <h4 class="font-medium text-gray-900 dark:text-white mb-3">🏆 Mejores Grupos</h4>
              <div class="space-y-2">
                <div v-for="[groupName, rate] in estadisticas.recent_performance.best_groups" :key="groupName"
                     class="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border border-green-200 dark:border-green-800">
                  <span class="font-medium text-gray-900 dark:text-white capitalize">
                    {{ String(groupName).replace('_', ' ') }}
                  </span>
                  <span class="text-green-600 dark:text-green-400 font-bold">{{ formatearPorcentaje(rate) }}%</span>
                </div>
              </div>
            </div>

            <!-- Peores Grupos -->
            <div>
              <h4 class="font-medium text-gray-900 dark:text-white mb-3">⚠️ Grupos que Necesitan Mejora</h4>
              <div class="space-y-2">
                <div v-for="[groupName, rate] in estadisticas.recent_performance.worst_groups" :key="groupName"
                     class="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border border-red-200 dark:border-red-800">
                  <span class="font-medium text-gray-900 dark:text-white capitalize">
                    {{ String(groupName).replace('_', ' ') }}
                  </span>
                  <span class="text-red-600 dark:text-red-400 font-bold">{{ formatearPorcentaje(rate) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recomendaciones -->
        <div v-if="estadisticas.recent_performance?.recommendations?.length > 0" 
             class="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-6">
          <h3 class="text-lg font-semibold text-yellow-900 dark:text-yellow-300 mb-4">
            💡 Recomendaciones Basadas en Estadísticas
          </h3>
          <div class="space-y-3">
            <div v-for="rec in estadisticas.recent_performance.recommendations" :key="rec.tipo"
                 class="p-4 bg-white dark:bg-gray-800 rounded-lg border border-yellow-200 dark:border-yellow-800">
              <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                  <span class="text-lg">{{ getRecommendationIcon(rec.tipo) }}</span>
                </div>
                <div class="flex-1">
                  <h4 class="font-medium text-gray-900 dark:text-white">{{ rec.mensaje }}</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">{{ rec.accion }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Información de Exportación -->
        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mt-6">
          <div class="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
            <span>Total de evaluaciones: {{ estadisticas.export_data?.evaluation_count || 0 }}</span>
            <span>Última actualización: {{ formatearFecha(estadisticas.export_data?.last_updated) }}</span>
          </div>
        </div>
      </div>

      <!-- Estado inicial -->
      <div v-else class="text-center py-8">
        <p class="text-gray-500 dark:text-gray-400 mb-4">
          Haz clic en "Actualizar" para cargar las estadísticas de predicciones
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface GroupStats {
  aciertos: number
  total: number
  porcentaje: number
}

interface RecentPerformance {
  total_evaluations: number
  best_groups: [string, number][]
  worst_groups: [string, number][]
  recommendations: Array<{
    tipo: string
    mensaje: string
    accion: string
  }>
  error?: string
}

interface Estadisticas {
  group_statistics: { [key: string]: GroupStats }
  recent_performance: RecentPerformance
  analysis_period_days: number
  export_data: {
    evaluation_count: number
    last_updated: string
  }
}

const estadisticas = ref<Estadisticas | null>(null)
const loading = ref(false)
const error = ref('')
const daysPeriod = ref(7)

const cargarEstadisticas = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const apiBaseUrl = window.location.origin.includes('localhost') ? 'http://localhost:5001' : window.location.origin
    
    const response = await fetch(`${apiBaseUrl}/estadisticas-evaluacion?days=${daysPeriod.value}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    const data = await response.json()
    
    if (response.ok && data.status === 'success') {
      estadisticas.value = data
      console.log('✅ Estadísticas cargadas:', data)
    } else {
      error.value = data.message || 'Error al cargar estadísticas'
      console.error('❌ Error en estadísticas:', data)
    }
  } catch (err) {
    error.value = 'Error de conexión con el servidor'
    console.error('❌ Error de conexión:', err)
  } finally {
    loading.value = false
  }
}

const resetearEstadisticas = async () => {
  if (!confirm('¿Está seguro de que desea resetear todas las estadísticas de predicciones? Esta acción no se puede deshacer.')) {
    return
  }
  
  loading.value = true
  
  try {
    const apiBaseUrl = window.location.origin.includes('localhost') ? 'http://localhost:5001' : window.location.origin
    
    const response = await fetch(`${apiBaseUrl}/resetear-estadisticas`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    const data = await response.json()
    
    if (response.ok && data.status === 'success') {
      console.log('✅ Estadísticas reseteadas')
      // Recargar estadísticas
      await cargarEstadisticas()
    } else {
      error.value = data.message || 'Error al resetear estadísticas'
      console.error('❌ Error al resetear:', data)
    }
  } catch (err) {
    error.value = 'Error de conexión con el servidor'
    console.error('❌ Error de conexión:', err)
  } finally {
    loading.value = false
  }
}

const formatearPorcentaje = (porcentaje: number | undefined): string => {
  if (porcentaje === undefined || porcentaje === null) return '0.0'
  return porcentaje.toFixed(1)
}

const formatearFecha = (fecha: string | undefined): string => {
  if (!fecha) return 'N/A'
  try {
    return new Date(fecha).toLocaleString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return 'N/A'
  }
}

const getPerformanceClass = (porcentaje: number | undefined): string => {
  const value = porcentaje || 0
  if (value >= 50) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
  if (value >= 30) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
  return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
}

const getProgressBarClass = (porcentaje: number | undefined): string => {
  const value = porcentaje || 0
  if (value >= 50) return 'bg-green-500'
  if (value >= 30) return 'bg-yellow-500'
  return 'bg-red-500'
}

const getRecommendationIcon = (tipo: string): string => {
  switch (tipo) {
    case 'grupo_recomendado': return '🎯'
    case 'modelo_ml_recomendado': return '🤖'
    case 'estrategias_activas': return '⚡'
    default: return '💡'
  }
}

onMounted(() => {
  cargarEstadisticas()
})
</script>

<style scoped>
.prediction-stats-container {
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