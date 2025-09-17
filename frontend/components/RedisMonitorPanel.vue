<template>
  <div class="redis-monitor-panel bg-white rounded-lg shadow-lg p-6 mb-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-xl font-bold text-gray-800 flex items-center">
        <span class="mr-2">🔍</span>
        Monitor de Detección Automática
      </h3>
      <div class="flex items-center space-x-2">
        <div 
          :class="[
            'w-3 h-3 rounded-full',
            monitorStatus?.monitoring ? 'bg-green-500 animate-pulse' : 'bg-red-500'
          ]"
        ></div>
        <span 
          :class="[
            'text-sm font-medium',
            monitorStatus?.monitoring ? 'text-green-600' : 'text-red-600'
          ]"
        >
          {{ monitorStatus?.monitoring ? 'Activo' : 'Inactivo' }}
        </span>
      </div>
    </div>

    <!-- Estado del Monitor -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="bg-blue-50 rounded-lg p-4">
        <div class="text-sm text-blue-600 font-medium">Estado</div>
        <div class="text-lg font-bold text-blue-800">
          {{ monitorStatus?.monitoring ? '🟢 Monitoreando' : '🔴 Detenido' }}
        </div>
      </div>
      
      <div class="bg-purple-50 rounded-lg p-4">
        <div class="text-sm text-purple-600 font-medium">Longitud Actual</div>
        <div class="text-lg font-bold text-purple-800">
          {{ monitorStatus?.current_history_length || 0 }}
        </div>
      </div>
      
      <div class="bg-orange-50 rounded-lg p-4">
        <div class="text-sm text-orange-600 font-medium">Última Conocida</div>
        <div class="text-lg font-bold text-orange-800">
          {{ monitorStatus?.last_history_length || 0 }}
        </div>
      </div>
      
      <div class="bg-green-50 rounded-lg p-4">
        <div class="text-sm text-green-600 font-medium">Hilo Activo</div>
        <div class="text-lg font-bold text-green-800">
          {{ monitorStatus?.thread_alive ? '✅ Sí' : '❌ No' }}
        </div>
      </div>
    </div>

    <!-- Controles -->
    <div class="flex flex-wrap gap-3 mb-6">
      <button
        @click="startMonitoring"
        :disabled="loading || monitorStatus?.monitoring"
        class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
      >
        <span class="mr-2">▶️</span>
        {{ loading && actionType === 'start' ? 'Iniciando...' : 'Iniciar Monitor' }}
      </button>
      
      <button
        @click="stopMonitoring"
        :disabled="loading || !monitorStatus?.monitoring"
        class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
      >
        <span class="mr-2">⏹️</span>
        {{ loading && actionType === 'stop' ? 'Deteniendo...' : 'Detener Monitor' }}
      </button>
      
      <button
        @click="forceCheck"
        :disabled="loading"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
      >
        <span class="mr-2">🔄</span>
        {{ loading && actionType === 'check' ? 'Verificando...' : 'Verificación Manual' }}
      </button>
      
      <button
        @click="refreshStatus"
        :disabled="loading"
        class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
      >
        <span class="mr-2">🔄</span>
        {{ loading && actionType === 'refresh' ? 'Actualizando...' : 'Actualizar Estado' }}
      </button>
    </div>

    <!-- Información del Sistema -->
    <div class="bg-gray-50 rounded-lg p-4 mb-4">
      <h4 class="font-semibold text-gray-800 mb-2">ℹ️ Información del Sistema</h4>
      <div class="text-sm text-gray-600 space-y-1">
        <p><strong>Función:</strong> Detecta automáticamente nuevas inserciones en Redis y ejecuta verificaciones de predicciones</p>
        <p><strong>Frecuencia:</strong> Verifica cada 2 segundos</p>
        <p><strong>Acciones automáticas:</strong> Verificar predicciones pendientes, generar nuevas predicciones, actualizar estadísticas</p>
        <p><strong>Estado ideal:</strong> Monitor activo con hilo ejecutándose</p>
      </div>
    </div>

    <!-- Últimas Acciones -->
    <div v-if="lastActions.length > 0" class="bg-blue-50 rounded-lg p-4">
      <h4 class="font-semibold text-blue-800 mb-2">📋 Últimas Acciones</h4>
      <div class="space-y-2 max-h-32 overflow-y-auto">
        <div 
          v-for="(action, index) in lastActions" 
          :key="index"
          class="text-sm text-blue-700 bg-white rounded px-2 py-1"
        >
          <span class="font-medium">{{ action.timestamp }}</span> - {{ action.message }}
        </div>
      </div>
    </div>

    <!-- Resultados de Verificación Manual -->
    <div v-if="lastCheckResult" class="mt-4 bg-yellow-50 rounded-lg p-4">
      <h4 class="font-semibold text-yellow-800 mb-2">🔍 Resultado de Última Verificación</h4>
      <div class="text-sm text-yellow-700">
        <p><strong>Mensaje:</strong> {{ lastCheckResult.message }}</p>
        <div v-if="lastCheckResult.data && lastCheckResult.data.insertion_data" class="mt-2">
          <p><strong>Número detectado:</strong> {{ lastCheckResult.data.insertion_data.number }}</p>
          <p><strong>Timestamp:</strong> {{ formatTimestamp(lastCheckResult.data.insertion_data.timestamp) }}</p>
          <p><strong>Predicciones verificadas:</strong> {{ lastCheckResult.data.verification_results?.length || 0 }}</p>
          <p><strong>Nueva predicción:</strong> {{ lastCheckResult.data.new_prediction ? '✅ Generada' : '❌ No generada' }}</p>
        </div>
        <div v-else-if="lastCheckResult.data" class="mt-2">
          <p><strong>Longitud actual:</strong> {{ lastCheckResult.data.current_length }}</p>
          <p><strong>Última conocida:</strong> {{ lastCheckResult.data.last_known_length }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { getMonitorStatus, startMonitor, stopMonitor, forceMonitorCheck } from '../utils/api'

// Estado reactivo
const monitorStatus = ref(null)
const loading = ref(false)
const actionType = ref('')
const lastActions = ref([])
const lastCheckResult = ref(null)

// Intervalo para actualización automática
let statusInterval: NodeJS.Timeout | null = null

// Función para agregar acción al log
const addAction = (message: string) => {
  const timestamp = new Date().toLocaleTimeString()
  lastActions.value.unshift({ timestamp, message })
  
  // Mantener solo las últimas 5 acciones
  if (lastActions.value.length > 5) {
    lastActions.value = lastActions.value.slice(0, 5)
  }
}

// Función para formatear timestamp
const formatTimestamp = (isoString: string) => {
  try {
    return new Date(isoString).toLocaleString()
  } catch {
    return isoString
  }
}

// Obtener estado del monitor
const refreshStatus = async () => {
  if (loading.value) return
  
  try {
    loading.value = true
    actionType.value = 'refresh'
    
    const status = await getMonitorStatus()
    if (status) {
      monitorStatus.value = status
      addAction('Estado actualizado correctamente')
    } else {
      addAction('Error al obtener estado del monitor')
    }
  } catch (error) {
    console.error('Error refreshing status:', error)
    addAction(`Error: ${error.message}`)
  } finally {
    loading.value = false
    actionType.value = ''
  }
}

// Iniciar monitoreo
const startMonitoring = async () => {
  if (loading.value) return
  
  try {
    loading.value = true
    actionType.value = 'start'
    
    const result = await startMonitor()
    if (result) {
      monitorStatus.value = result
      addAction('Monitor iniciado exitosamente')
    } else {
      addAction('Error al iniciar monitor')
    }
  } catch (error) {
    console.error('Error starting monitor:', error)
    addAction(`Error iniciando: ${error.message}`)
  } finally {
    loading.value = false
    actionType.value = ''
  }
}

// Detener monitoreo
const stopMonitoring = async () => {
  if (loading.value) return
  
  try {
    loading.value = true
    actionType.value = 'stop'
    
    const result = await stopMonitor()
    if (result) {
      monitorStatus.value = result
      addAction('Monitor detenido exitosamente')
    } else {
      addAction('Error al detener monitor')
    }
  } catch (error) {
    console.error('Error stopping monitor:', error)
    addAction(`Error deteniendo: ${error.message}`)
  } finally {
    loading.value = false
    actionType.value = ''
  }
}

// Verificación manual
const forceCheck = async () => {
  if (loading.value) return
  
  try {
    loading.value = true
    actionType.value = 'check'
    
    const result = await forceMonitorCheck()
    if (result) {
      lastCheckResult.value = result
      addAction('Verificación manual completada')
    } else {
      addAction('Error en verificación manual')
    }
  } catch (error) {
    console.error('Error in force check:', error)
    addAction(`Error en verificación: ${error.message}`)
  } finally {
    loading.value = false
    actionType.value = ''
  }
}

// Ciclo de vida del componente
onMounted(async () => {
  // Obtener estado inicial
  await refreshStatus()
  
  // Configurar actualización automática cada 10 segundos
  statusInterval = setInterval(async () => {
    if (!loading.value) {
      await refreshStatus()
    }
  }, 10000)
  
  addAction('Panel de monitor inicializado')
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
})
</script>

<style scoped>
.redis-monitor-panel {
  font-family: 'Inter', sans-serif;
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: .5;
  }
}

/* Scrollbar personalizado para las acciones */
.overflow-y-auto::-webkit-scrollbar {
  width: 4px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 2px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>