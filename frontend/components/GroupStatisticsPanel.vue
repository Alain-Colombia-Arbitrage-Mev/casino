<template>
  <div class="card bg-base-100 shadow-xl border border-base-300">
    <div class="card-header bg-gradient-to-r from-orange-500 to-red-600 text-white p-4 rounded-t-xl">
      <h2 class="card-title flex items-center gap-2">
        <Icon name="heroicons:chart-bar-20-solid" class="w-6 h-6" />
        📊 Análisis de Grupos de Números
      </h2>
      <p class="text-orange-100 text-sm mt-1">
        Estadísticas detalladas por grupos y sectores de la ruleta
      </p>
    </div>

    <div class="card-body p-6">
      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center py-8">
        <span class="loading loading-spinner loading-lg text-primary"></span>
        <span class="ml-3 text-base-content">Analizando grupos de números...</span>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="alert alert-error">
        <Icon name="heroicons:exclamation-triangle-20-solid" class="w-6 h-6" />
        <span>{{ error }}</span>
        <button @click="fetchGroupStatistics" class="btn btn-sm btn-outline btn-error">
          Reintentar
        </button>
      </div>

      <!-- Main Content -->
      <div v-else class="space-y-6">
        <!-- Quick Stats -->
        <div class="stats stats-vertical lg:stats-horizontal shadow w-full">
          <div class="stat">
            <div class="stat-figure text-primary">
              <Icon name="heroicons:fire-20-solid" class="w-8 h-8" />
            </div>
            <div class="stat-title">Grupo Más Caliente</div>
            <div class="stat-value text-primary">{{ bestPerformingGroup?.name || 'N/A' }}</div>
            <div class="stat-desc">
              {{ bestPerformingGroup?.winRate || 0 }}% de aciertos
            </div>
          </div>

          <div class="stat">
            <div class="stat-figure text-secondary">
              <Icon name="heroicons:snowflake-20-solid" class="w-8 h-8" />
            </div>
            <div class="stat-title">Grupo Más Frío</div>
            <div class="stat-value text-secondary">{{ coldestGroup?.name || 'N/A' }}</div>
            <div class="stat-desc">
              {{ coldestGroup?.winRate || 0 }}% de aciertos
            </div>
          </div>

          <div class="stat">
            <div class="stat-figure text-accent">
              <Icon name="heroicons:chart-pie-20-solid" class="w-8 h-8" />
            </div>
            <div class="stat-title">Total Grupos</div>
            <div class="stat-value text-accent">{{ groupStats.length }}</div>
            <div class="stat-desc">Analizados</div>
          </div>
        </div>

        <!-- Groups Analysis -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Traditional Groups -->
          <div class="card bg-base-200 shadow">
            <div class="card-header bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4">
              <h3 class="text-lg font-bold">🎯 Grupos Tradicionales</h3>
            </div>
            <div class="card-body p-4">
              <div class="space-y-3">
                <div v-for="group in traditionalGroups" :key="group.id" class="group-item">
                  <div class="flex justify-between items-center p-3 rounded-lg"
                       :class="getGroupColor(group.winRate)">
                    <div>
                      <h4 class="font-semibold">{{ group.name }}</h4>
                      <p class="text-sm opacity-75">{{ group.numbers.join(', ') }}</p>
                    </div>
                    <div class="text-right">
                      <div class="text-lg font-bold">{{ group.winRate }}%</div>
                      <div class="text-xs">{{ group.hits }}/{{ group.total }} hits</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Sector Analysis -->
          <div class="card bg-base-200 shadow">
            <div class="card-header bg-gradient-to-r from-green-500 to-teal-600 text-white p-4">
              <h3 class="text-lg font-bold">🎡 Análisis por Sectores</h3>
            </div>
            <div class="card-body p-4">
              <div class="space-y-3">
                <div v-for="sector in sectorGroups" :key="sector.id" class="group-item">
                  <div class="flex justify-between items-center p-3 rounded-lg"
                       :class="getGroupColor(sector.winRate)">
                    <div>
                      <h4 class="font-semibold">{{ sector.name }}</h4>
                      <p class="text-sm opacity-75">{{ sector.description }}</p>
                    </div>
                    <div class="text-right">
                      <div class="text-lg font-bold">{{ sector.winRate }}%</div>
                      <div class="text-xs">{{ sector.hits }}/{{ sector.total }} hits</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Advanced Analysis -->
        <div class="card bg-base-200 shadow">
          <div class="card-header bg-gradient-to-r from-purple-500 to-pink-600 text-white p-4">
            <h3 class="text-lg font-bold">🧠 Análisis Avanzado de Tendencias</h3>
          </div>
          <div class="card-body p-4">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <!-- Trend Analysis -->
              <div class="stat-group">
                <h4 class="font-semibold mb-2">📈 Tendencias Actuales</h4>
                <div class="space-y-2">
                  <div v-for="trend in currentTrends" :key="trend.type"
                       class="flex justify-between items-center p-2 rounded"
                       :class="trend.strength > 70 ? 'bg-success bg-opacity-20' :
                               trend.strength > 40 ? 'bg-warning bg-opacity-20' : 'bg-error bg-opacity-20'">
                    <span class="text-sm">{{ trend.type }}</span>
                    <span class="font-bold">{{ trend.strength }}%</span>
                  </div>
                </div>
              </div>

              <!-- Hot Streak -->
              <div class="stat-group">
                <h4 class="font-semibold mb-2">🔥 Rachas Calientes</h4>
                <div class="space-y-2">
                  <div v-for="streak in hotStreaks" :key="streak.group"
                       class="flex justify-between items-center p-2 rounded bg-error bg-opacity-20">
                    <span class="text-sm">{{ streak.group }}</span>
                    <span class="font-bold">{{ streak.count }} hits</span>
                  </div>
                </div>
              </div>

              <!-- Predictions -->
              <div class="stat-group">
                <h4 class="font-semibold mb-2">🎯 Predicciones</h4>
                <div class="space-y-2">
                  <div v-for="prediction in groupPredictions" :key="prediction.group"
                       class="flex justify-between items-center p-2 rounded bg-info bg-opacity-20">
                    <span class="text-sm">{{ prediction.group }}</span>
                    <span class="font-bold">{{ prediction.probability }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Real-time Updates -->
        <div class="alert alert-info">
          <Icon name="heroicons:clock-20-solid" class="w-6 h-6" />
          <div>
            <div class="font-bold">Actualización en tiempo real</div>
            <div class="text-sm">
              Última actualización: {{ lastUpdate }} |
              Próxima en: {{ nextUpdateCountdown }}s
            </div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="card-actions justify-end mt-6">
        <button @click="exportGroupData" class="btn btn-outline btn-primary">
          <Icon name="heroicons:arrow-down-tray-20-solid" class="w-4 h-4" />
          Exportar Datos
        </button>
        <button @click="fetchGroupStatistics" class="btn btn-primary">
          <Icon name="heroicons:arrow-path-20-solid" class="w-4 h-4" />
          Actualizar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'

// Reactive state
const loading = ref(true)
const error = ref('')
const groupStats = ref([])
const lastUpdate = ref('')
const nextUpdateCountdown = ref(30)
const updateInterval = ref(null)
const countdownInterval = ref(null)

// Group definitions
const groupDefinitions = {
  traditional: [
    { id: 'rojo', name: 'Números Rojos', numbers: [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36], color: 'red' },
    { id: 'negro', name: 'Números Negros', numbers: [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35], color: 'black' },
    { id: 'par', name: 'Números Pares', numbers: [2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36] },
    { id: 'impar', name: 'Números Impares', numbers: [1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35] },
    { id: 'bajo', name: 'Manque (1-18)', numbers: Array.from({length: 18}, (_, i) => i + 1) },
    { id: 'alto', name: 'Passe (19-36)', numbers: Array.from({length: 18}, (_, i) => i + 19) },
    { id: 'primera_docena', name: 'Primera Docena (1-12)', numbers: Array.from({length: 12}, (_, i) => i + 1) },
    { id: 'segunda_docena', name: 'Segunda Docena (13-24)', numbers: Array.from({length: 12}, (_, i) => i + 13) },
    { id: 'tercera_docena', name: 'Tercera Docena (25-36)', numbers: Array.from({length: 12}, (_, i) => i + 25) }
  ],
  sectors: [
    { id: 'voisins', name: 'Voisins du Zéro', numbers: [22,18,29,7,28,12,35,3,26,0,32,15,19,4,21,2,25], description: 'Vecinos del cero' },
    { id: 'tiers', name: 'Tiers du Cylindre', numbers: [27,13,36,11,30,8,23,10,5,24,16,33], description: 'Tercio del cilindro' },
    { id: 'orphelins', name: 'Orphelins', numbers: [1,20,14,31,9,17,34,6], description: 'Huérfanos' },
    { id: 'zero_game', name: 'Zero Spiel', numbers: [12,35,3,26,0,32,15], description: 'Juego del cero' }
  ]
}

// Computed properties
const traditionalGroups = computed(() =>
  groupStats.value.filter(group => groupDefinitions.traditional.some(def => def.id === group.id))
)

const sectorGroups = computed(() =>
  groupStats.value.filter(group => groupDefinitions.sectors.some(def => def.id === group.id))
)

const bestPerformingGroup = computed(() =>
  groupStats.value.reduce((best, group) =>
    !best || group.winRate > best.winRate ? group : best, null)
)

const coldestGroup = computed(() =>
  groupStats.value.reduce((coldest, group) =>
    !coldest || group.winRate < coldest.winRate ? group : coldest, null)
)

const currentTrends = ref([
  { type: 'Tendencia Rojo/Negro', strength: 65 },
  { type: 'Secuencia Par/Impar', strength: 78 },
  { type: 'Patrón Docenas', strength: 45 }
])

const hotStreaks = ref([
  { group: 'Primera Docena', count: 4 },
  { group: 'Números Rojos', count: 3 }
])

const groupPredictions = ref([
  { group: 'Segunda Docena', probability: 73 },
  { group: 'Números Negros', probability: 68 },
  { group: 'Passe (19-36)', probability: 61 }
])

// Methods
const fetchGroupStatistics = async () => {
  try {
    loading.value = true
    error.value = ''

    // Fetch group statistics from backend
    const response = await fetch('http://localhost:8080/api/roulette/group-stats')
    if (!response.ok) throw new Error('Error al obtener estadísticas de grupos')

    const data = await response.json()

    // Combine traditional and sector groups
    const allStats = []

    if (data.traditional_groups) {
      data.traditional_groups.forEach(group => {
        allStats.push({
          id: group.id,
          name: group.name,
          numbers: group.numbers,
          hits: group.hits,
          total: group.total,
          winRate: Math.round(group.win_rate),
          type: 'traditional'
        })
      })
    }

    if (data.sector_groups) {
      data.sector_groups.forEach(group => {
        allStats.push({
          id: group.id,
          name: group.name,
          numbers: group.numbers,
          description: group.description,
          hits: group.hits,
          total: group.total,
          winRate: Math.round(group.win_rate),
          type: 'sector'
        })
      })
    }

    groupStats.value = allStats

    // Update trends if available
    if (data.trends) {
      currentTrends.value = data.trends.map(trend => ({
        type: trend.type,
        strength: Math.round(trend.strength)
      }))
    }

    lastUpdate.value = data.last_update || new Date().toLocaleTimeString()

  } catch (err) {
    error.value = `Error al cargar estadísticas de grupos: ${err.message}`
    console.error('Error fetching group statistics:', err)
  } finally {
    loading.value = false
  }
}

const getGroupColor = (winRate) => {
  if (winRate >= 60) return 'bg-success bg-opacity-20 border border-success'
  if (winRate >= 40) return 'bg-warning bg-opacity-20 border border-warning'
  return 'bg-error bg-opacity-20 border border-error'
}

const exportGroupData = () => {
  const dataToExport = {
    timestamp: new Date().toISOString(),
    groupStatistics: groupStats.value,
    trends: currentTrends.value,
    hotStreaks: hotStreaks.value,
    predictions: groupPredictions.value
  }

  const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const a = document.createElement('a')
  a.href = url
  a.download = `group-statistics-${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const startCountdown = () => {
  countdownInterval.value = setInterval(() => {
    nextUpdateCountdown.value--
    if (nextUpdateCountdown.value <= 0) {
      nextUpdateCountdown.value = 30
    }
  }, 1000)
}

// Lifecycle
onMounted(() => {
  fetchGroupStatistics()

  // Auto-refresh every 30 seconds
  updateInterval.value = setInterval(() => {
    fetchGroupStatistics()
    nextUpdateCountdown.value = 30
  }, 30000)

  startCountdown()
})

onUnmounted(() => {
  if (updateInterval.value) {
    clearInterval(updateInterval.value)
  }
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value)
  }
})
</script>

<style scoped>
.group-item {
  transition: all 0.3s ease;
}

.group-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-group h4 {
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 8px;
}

@media (max-width: 768px) {
  .stats {
    grid-template-columns: 1fr;
  }

  .grid-cols-1.md\\:grid-cols-3 {
    grid-template-columns: 1fr;
  }
}
</style>