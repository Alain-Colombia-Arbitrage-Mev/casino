<template>
  <div class="automation-panel bg-white rounded-lg shadow-lg p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-800 flex items-center">
        <svg class="w-8 h-8 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
        </svg>
        Sistema de Automatización
      </h2>
      
      <!-- Estado general -->
      <div class="flex items-center space-x-3">
        <div class="flex items-center">
          <div :class="[
            'w-3 h-3 rounded-full mr-2',
            status?.is_running ? 'bg-green-500 animate-pulse' : 'bg-red-500'
          ]"></div>
          <span :class="[
            'text-sm font-medium',
            status?.is_running ? 'text-green-600' : 'text-red-600'
          ]">
            {{ status?.is_running ? 'ACTIVO' : 'INACTIVO' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Controles principales -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <!-- Control del servicio -->
      <div class="bg-gray-50 rounded-lg p-4">
        <h3 class="text-lg font-semibold text-gray-700 mb-3">Control del Servicio</h3>
        <div class="space-y-3">
          <button
            @click="startAutomation"
            :disabled="loading || status?.is_running"
            class="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            <svg v-if="loading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ loading ? 'Iniciando...' : 'Iniciar Automatización' }}
          </button>
          
          <button
            @click="stopAutomation"
            :disabled="loading || !status?.is_running"
            class="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            {{ loading ? 'Deteniendo...' : 'Detener Automatización' }}
          </button>
        </div>
      </div>

      <!-- Estado del Scraper -->
      <div class="bg-gray-50 rounded-lg p-4">
        <h3 class="text-lg font-semibold text-gray-700 mb-3">Estado del Scraper</h3>
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">Estado:</span>
            <span :class="[
              'text-sm font-medium px-2 py-1 rounded',
              status?.scraper_status === 'running' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            ]">
              {{ status?.scraper_status === 'running' ? 'Ejecutándose' : 'Detenido' }}
            </span>
          </div>
          
          <div v-if="status?.scraper_pid" class="flex items-center justify-between">
            <span class="text-sm text-gray-600">PID:</span>
            <span class="text-sm font-mono">{{ status.scraper_pid }}</span>
          </div>
          
          <button
            @click="restartScraper"
            :disabled="loading || !status?.is_running"
            class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            Reiniciar Scraper
          </button>
        </div>
      </div>
    </div>

    <!-- Estadísticas -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-blue-50 rounded-lg p-4 text-center">
        <div class="text-2xl font-bold text-blue-600">{{ status?.stats?.total_numbers_processed || '0' }}</div>
        <div class="text-sm text-blue-800">Números Procesados</div>
      </div>
      
      <div class="bg-green-50 rounded-lg p-4 text-center">
        <div class="text-2xl font-bold text-green-600">{{ status?.stats?.predictions_verified || '0' }}</div>
        <div class="text-sm text-green-800">Predicciones Verificadas</div>
      </div>
      
      <div class="bg-purple-50 rounded-lg p-4 text-center">
        <div class="text-2xl font-bold text-purple-600">{{ status?.last_known_number || '-' }}</div>
        <div class="text-sm text-purple-800">Último Número</div>
      </div>
      
      <div class="bg-orange-50 rounded-lg p-4 text-center">
        <div class="text-2xl font-bold text-orange-600">{{ status?.check_interval || '0' }}s</div>
        <div class="text-sm text-orange-800">Intervalo</div>
      </div>
    </div>

    <!-- Configuración -->
    <div class="bg-gray-50 rounded-lg p-4 mb-6">
      <h3 class="text-lg font-semibold text-gray-700 mb-3">Configuración</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600">Scraper Habilitado:</span>
          <span :class="[
            'text-sm font-medium',
            status?.scraper_enabled ? 'text-green-600' : 'text-red-600'
          ]">
            {{ status?.scraper_enabled ? '✅' : '❌' }}
          </span>
        </div>
        
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600">Predicciones Auto:</span>
          <span :class="[
            'text-sm font-medium',
            status?.auto_predict ? 'text-green-600' : 'text-red-600'
          ]">
            {{ status?.auto_predict ? '✅' : '❌' }}
          </span>
        </div>
        
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600">Monitoreo Activo:</span>
          <span :class="[
            'text-sm font-medium',
            status?.monitoring_active ? 'text-green-600' : 'text-red-600'
          ]">
            {{ status?.monitoring_active ? '✅' : '❌' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Logs en tiempo real -->
    <div class="bg-gray-50 rounded-lg p-4">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-lg font-semibold text-gray-700">Logs del Sistema</h3>
        <button
          @click="refreshLogs"
          class="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          Actualizar
        </button>
      </div>
      
      <div class="bg-black rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm">
        <div
          v-for="(log, index) in logs"
          :key="index"
          :class="[
            'mb-1',
            log.includes('[ERROR]') ? 'text-red-400' :
            log.includes('[WARNING]') ? 'text-yellow-400' :
            log.includes('✅') ? 'text-green-400' :
            log.includes('🆕') ? 'text-blue-400' :
            'text-gray-300'
          ]"
        >
          {{ log }}
        </div>
        
        <div v-if="logs.length === 0" class="text-gray-500 text-center py-8">
          No hay logs disponibles
        </div>
      </div>
    </div>

    <!-- Notificaciones recientes -->
    <div v-if="notifications.length > 0" class="mt-6 bg-gray-50 rounded-lg p-4">
      <h3 class="text-lg font-semibold text-gray-700 mb-3">Eventos Recientes</h3>
      <div class="space-y-2 max-h-32 overflow-y-auto">
        <div
          v-for="(notification, index) in notifications.slice(0, 5)"
          :key="index"
          class="bg-white rounded p-3 border-l-4 border-blue-500"
        >
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-800">
              {{ getNotificationMessage(notification) }}
            </span>
            <span class="text-xs text-gray-500">
              {{ formatTime(notification.timestamp) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// Estado reactivo
const status = ref(null)
const logs = ref([])
const notifications = ref([])
const loading = ref(false)

// Intervalo para actualización automática
let statusInterval = null
let logsInterval = null

// Funciones de API
const fetchStatus = async () => {
  try {
    const response = await fetch('/api/automation/status')
    const data = await response.json()
    
    if (data.success) {
      status.value = data.data
    }
  } catch (error) {
    console.error('Error obteniendo estado:', error)
  }
}

const fetchLogs = async () => {
  try {
    const response = await fetch('/api/automation/logs')
    const data = await response.json()
    
    if (data.success) {
      logs.value = data.data.logs.reverse() // Mostrar más recientes primero
    }
  } catch (error) {
    console.error('Error obteniendo logs:', error)
  }
}

const fetchNotifications = async () => {
  try {
    const response = await fetch('/api/automation/notifications')
    const data = await response.json()
    
    if (data.success) {
      notifications.value = data.data.notifications
    }
  } catch (error) {
    console.error('Error obteniendo notificaciones:', error)
  }
}

// Acciones
const startAutomation = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/automation/start', {
      method: 'POST'
    })
    const data = await response.json()
    
    if (data.success) {
      await fetchStatus()
      showNotification('Automatización iniciada exitosamente', 'success')
    } else {
      showNotification(data.error || 'Error iniciando automatización', 'error')
    }
  } catch (error) {
    showNotification('Error de conexión', 'error')
  } finally {
    loading.value = false
  }
}

const stopAutomation = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/automation/stop', {
      method: 'POST'
    })
    const data = await response.json()
    
    if (data.success) {
      await fetchStatus()
      showNotification('Automatización detenida exitosamente', 'success')
    } else {
      showNotification(data.error || 'Error deteniendo automatización', 'error')
    }
  } catch (error) {
    showNotification('Error de conexión', 'error')
  } finally {
    loading.value = false
  }
}

const restartScraper = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/automation/scraper/restart', {
      method: 'POST'
    })
    const data = await response.json()
    
    if (data.success) {
      await fetchStatus()
      showNotification('Scraper reiniciado exitosamente', 'success')
    } else {
      showNotification(data.error || 'Error reiniciando scraper', 'error')
    }
  } catch (error) {
    showNotification('Error de conexión', 'error')
  } finally {
    loading.value = false
  }
}

const refreshLogs = async () => {
  await fetchLogs()
}

// Utilidades
const getNotificationMessage = (notification) => {
  const data = notification.data
  if (data.type === 'new_number') {
    return `Nuevo número detectado: ${data.number} | Predicciones verificadas: ${data.verified_predictions}`
  }
  return 'Evento del sistema'
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

const showNotification = (message, type) => {
  // Implementar sistema de notificaciones toast
  console.log(`${type.toUpperCase()}: ${message}`)
}

// Ciclo de vida
onMounted(async () => {
  // Cargar datos iniciales
  await fetchStatus()
  await fetchLogs()
  await fetchNotifications()
  
  // Configurar actualizaciones automáticas
  statusInterval = setInterval(fetchStatus, 5000) // Cada 5 segundos
  logsInterval = setInterval(() => {
    fetchLogs()
    fetchNotifications()
  }, 10000) // Cada 10 segundos
})

onUnmounted(() => {
  if (statusInterval) clearInterval(statusInterval)
  if (logsInterval) clearInterval(logsInterval)
})
</script>

<style scoped>
.automation-panel {
  max-width: 1200px;
  margin: 0 auto;
}

/* Animación para el indicador de estado */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Scrollbar personalizado para logs */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #374151;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #6B7280;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #9CA3AF;
}
</style>