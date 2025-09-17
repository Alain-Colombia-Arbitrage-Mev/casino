<template>
  <div class="bg-white p-4 rounded-lg shadow-md h-full overflow-auto">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold text-gray-800">Estadísticas de la Ruleta</h2>
      <div class="flex gap-2">
        <button 
          @click="fetchStats" 
          class="bg-blue-600 text-white px-3 py-1 rounded text-sm"
          :disabled="updateLoading"
        >
          {{ updateLoading ? 'Actualizando...' : 'Actualizar' }}
        </button>
        <button 
          @click="purgeAllStatistics" 
          class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
          title="Purga todas las estadísticas del sistema"
        >
          Purgar todo
        </button>
      </div>
    </div>
    
    <div class="text-xs text-gray-500 mb-4">
      Última actualización: {{ formattedLastUpdated }} |
      Total de números: {{ stats.totalSpins || 0 }} |
      Último número: {{ stats.lastNumber || 'N/A' }} ({{ stats.lastColor || 'N/A' }})
    </div>
    
    <!-- Actualizar estadísticas -->
    <div class="flex justify-end mb-4">
      <button 
        @click="fetchStats"
        class="bg-blue-600 text-white px-3 py-1 rounded text-sm"
      >
        Actualizar estadísticas
      </button>
    </div>
    
    <!-- Columnas y Docenas -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      <div>
        <h3 class="text-lg font-semibold mb-2 text-gray-700">Columnas</h3>
        <div class="bg-gray-100 p-3 rounded">
          <div class="flex items-center justify-between mb-2">
            <span>Columna 1:</span>
            <span class="font-bold">{{ stats.columns?.c1 || 0 }}</span>
          </div>
          <div class="w-full bg-gray-300 rounded-full h-2.5">
            <div 
              class="bg-blue-600 h-2.5 rounded-full" 
              :style="{ width: getPercentage(stats.columns?.c1, columnsTotal) + '%' }"
            ></div>
          </div>
          
          <div class="flex items-center justify-between mb-2 mt-3">
            <span>Columna 2:</span>
            <span class="font-bold">{{ stats.columns?.c2 || 0 }}</span>
          </div>
          <div class="w-full bg-gray-300 rounded-full h-2.5">
            <div 
              class="bg-green-600 h-2.5 rounded-full" 
              :style="{ width: getPercentage(stats.columns?.c2, columnsTotal) + '%' }"
            ></div>
          </div>
          
          <div class="flex items-center justify-between mb-2 mt-3">
            <span>Columna 3:</span>
            <span class="font-bold">{{ stats.columns?.c3 || 0 }}</span>
          </div>
          <div class="w-full bg-gray-300 rounded-full h-2.5">
            <div 
              class="bg-purple-600 h-2.5 rounded-full" 
              :style="{ width: getPercentage(stats.columns?.c3, columnsTotal) + '%' }"
            ></div>
          </div>
        </div>
      </div>
      
      <div>
        <h3 class="text-lg font-semibold mb-2 text-gray-700">Docenas</h3>
        <div class="bg-gray-100 p-3 rounded">
          <div class="flex items-center justify-between mb-2">
            <span>Docena 1 (1-12):</span>
            <span class="font-bold">{{ stats.dozens?.d1 || 0 }}</span>
          </div>
          <div class="w-full bg-gray-300 rounded-full h-2.5">
            <div 
              class="bg-red-600 h-2.5 rounded-full" 
              :style="{ width: getPercentage(stats.dozens?.d1, dozensTotal) + '%' }"
            ></div>
          </div>
          
          <div class="flex items-center justify-between mb-2 mt-3">
            <span>Docena 2 (13-24):</span>
            <span class="font-bold">{{ stats.dozens?.d2 || 0 }}</span>
          </div>
          <div class="w-full bg-gray-300 rounded-full h-2.5">
            <div 
              class="bg-yellow-600 h-2.5 rounded-full" 
              :style="{ width: getPercentage(stats.dozens?.d2, dozensTotal) + '%' }"
            ></div>
          </div>
          
          <div class="flex items-center justify-between mb-2 mt-3">
            <span>Docena 3 (25-36):</span>
            <span class="font-bold">{{ stats.dozens?.d3 || 0 }}</span>
          </div>
          <div class="w-full bg-gray-300 rounded-full h-2.5">
            <div 
              class="bg-indigo-600 h-2.5 rounded-full" 
              :style="{ width: getPercentage(stats.dozens?.d3, dozensTotal) + '%' }"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Par/Impar, Rojo/Negro -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      <div>
        <h3 class="text-lg font-semibold mb-2 text-gray-700">Par / Impar</h3>
        <div class="flex justify-between items-center bg-gray-100 p-4 rounded">
          <div class="text-center">
            <div class="text-xl font-bold">{{ stats.oddVsEven?.odd || 0 }}</div>
            <div>Impar</div>
          </div>
          <div class="text-center">
            <div class="text-xl font-bold">{{ stats.oddVsEven?.even || 0 }}</div>
            <div>Par</div>
          </div>
        </div>
      </div>
      
      <div>
        <h3 class="text-lg font-semibold mb-2 text-gray-700">Rojo / Negro</h3>
        <div class="flex justify-between items-center bg-gray-100 p-4 rounded">
          <div class="text-center">
            <div class="text-xl font-bold text-red-600">{{ stats.redVsBlack?.red || 0 }}</div>
            <div>Rojo</div>
          </div>
          <div class="text-center">
            <div class="text-xl font-bold">{{ stats.redVsBlack?.black || 0 }}</div>
            <div>Negro</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Números calientes y fríos -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      <div>
        <h3 class="text-lg font-semibold mb-2 text-gray-700">Números Calientes</h3>
        <div class="bg-gray-100 p-3 rounded">
          <div class="flex flex-wrap gap-2">
            <div 
              v-for="num in stats.hotNumbers" 
              :key="num"
              class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold bg-red-600"
            >
              {{ num }}
            </div>
          </div>
          <p class="text-sm mt-2 text-gray-600">Estos números aparecen con mayor frecuencia.</p>
        </div>
      </div>
      
      <div>
        <h3 class="text-lg font-semibold mb-2 text-gray-700">Números Fríos</h3>
        <div class="bg-gray-100 p-3 rounded">
          <div class="flex flex-wrap gap-2">
            <div 
              v-for="num in stats.coldNumbers" 
              :key="num"
              class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold bg-blue-600"
            >
              {{ num }}
            </div>
          </div>
          <p class="text-sm mt-2 text-gray-600">Estos números aparecen con menor frecuencia.</p>
        </div>
      </div>
    </div>
    
    <!-- Últimos números -->
    <div class="mb-6">
      <h3 class="text-lg font-semibold mb-2 text-gray-700">Últimos números</h3>
      <div class="bg-gray-100 p-3 rounded">
        <div class="flex flex-wrap gap-2">
          <div
            v-for="(numData, index) in stats.lastNumbers"
            :key="index"
            class="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold"
            :class="getNumberBackgroundClass(typeof numData === 'object' ? numData.number : numData)"
          >
            {{ typeof numData === 'object' ? numData.number : numData }}
          </div>
        </div>
        <p class="text-xs text-gray-500 mt-2">El número de la izquierda es el más reciente jugado</p>
      </div>
    </div>
    
    <!-- Análisis de patrones -->
    <div class="mb-6">
      <h3 class="text-lg font-semibold mb-2 text-gray-700">Análisis de Patrones</h3>
      <div class="bg-gray-100 p-3 rounded">
        <p class="text-sm">
          Los patrones de la ruleta son difíciles de predecir debido a su naturaleza aleatoria. Sin embargo, las estadísticas pueden ayudar a identificar tendencias temporales.
        </p>
        <div class="mt-3 grid grid-cols-2 gap-3">
          <button 
            @click="generateTiaLuAnalysis"
            class="bg-pink-600 text-white px-3 py-2 rounded text-sm"
          >
            Análisis Tía Lu
          </button>
          <button 
            @click="generatePuxaUltraAnalysis"
            class="bg-purple-600 text-white px-3 py-2 rounded text-sm"
          >
            Análisis Puxa Ultra
          </button>
        </div>
        <div v-if="patternAnalysis" class="mt-3 p-2 bg-white rounded">
          <p>{{ patternAnalysis }}</p>
        </div>
      </div>
    </div>
    
    <!-- Análisis de secuencias -->
    <div class="mb-6" v-if="sequences">
      <h3 class="text-lg font-semibold mb-2 text-gray-700">Análisis de Secuencias</h3>
      <div class="bg-gray-100 p-3 rounded">
        <h4 class="font-medium mb-2">Últimos 5 números</h4>
        <div class="flex flex-wrap gap-2 mb-3">
          <div 
            v-for="(num, index) in sequences.recentNumberSequence.slice(0, 5)" 
            :key="index"
            class="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold"
            :class="getNumberBackgroundClass(num)"
          >
            {{ num }}
          </div>
        </div>
        <p class="text-xs text-gray-500 mt-1 mb-3">El número de la izquierda es el más reciente jugado</p>
        
        <h4 class="font-medium mb-2">Ciclos de 5 números</h4>
        <div class="space-y-2">
          <div v-for="(cycle, index) in sequences.cycles.slice(-3).reverse()" :key="index" class="bg-white p-2 rounded shadow-sm">
            <div class="flex flex-wrap gap-1 mb-1">
              <div 
                v-for="(num, numIndex) in cycle.numbers" 
                :key="numIndex"
                class="w-7 h-7 rounded-full flex items-center justify-center text-white font-bold text-xs"
                :class="{ 
                  'bg-red-600': cycle.colors[numIndex] === 'red',
                  'bg-gray-800': cycle.colors[numIndex] === 'black',
                  'bg-green-600': cycle.colors[numIndex] === 'green'
                }"
              >
                {{ num }}
              </div>
            </div>
            <div class="text-xs text-gray-600">
              Suma: {{ cycle.sum }} | 
              Promedio: {{ (cycle.sum / 5).toFixed(1) }}
            </div>
          </div>
        </div>
        
        <div class="mt-3 grid grid-cols-2 gap-2">
          <div class="bg-white p-2 rounded">
            <h5 class="text-sm font-medium mb-1">Alternancia Par/Impar</h5>
            <div class="flex flex-wrap gap-1">
              <span 
                v-for="(parity, index) in sequences.paritySequences.slice(-10)" 
                :key="index"
                class="inline-block px-2 text-xs rounded"
                :class="{ 
                  'bg-blue-100': parity === 'even',
                  'bg-pink-100': parity === 'odd',
                  'bg-green-100': parity === 'zero'
                }"
              >
                {{ parity === 'even' ? 'Par' : parity === 'odd' ? 'Impar' : '0' }}
              </span>
            </div>
          </div>
          
          <div class="bg-white p-2 rounded">
            <h5 class="text-sm font-medium mb-1">Alternancia Color</h5>
            <div class="flex flex-wrap gap-1">
              <span 
                v-for="(color, index) in sequences.colorSequences.slice(-10)" 
                :key="index"
                class="inline-block w-4 h-4 rounded-full"
                :class="{ 
                  'bg-red-600': color === 'red',
                  'bg-gray-800': color === 'black',
                  'bg-green-600': color === 'green'
                }"
              ></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, inject } from 'vue';
import { getRouletteStats, getRouletteNumberSequences, purgeAllStatistics as apiPurgeAllStatistics } from '~/utils/api';
import { generateTiaLuPredictions, generatePuxaUltraPredictions } from '~/utils/predictions';
import type { RouletteStats } from '~/types';

// Evento de actualización para comunicación entre componentes
const emitter = inject('emitter') as any;

// Estado
const stats = ref<RouletteStats>({
  hotNumbers: [],
  coldNumbers: [],
  redVsBlack: { red: 0, black: 0 },
  oddVsEven: { odd: 0, even: 0 },
  columns: { c1: 0, c2: 0, c3: 0 },
  dozens: { d1: 0, d2: 0, d3: 0 },
  lastNumbers: []
});
const patternAnalysis = ref('');
const sequences = ref<any>(null);
const updateLoading = ref(false);
const lastUpdated = ref(new Date());

// Auto-actualización en tiempo real
let autoUpdateInterval: NodeJS.Timeout | null = null;

// Inicializar
onMounted(async () => {
  await fetchStats();
  await fetchSequences();

  // Iniciar auto-actualización cada 5 segundos
  autoUpdateInterval = setInterval(async () => {
    await fetchStats();
    await fetchSequences();
    lastUpdated.value = new Date();
  }, 5000);

  // Escuchar eventos para actualización manual
  if (emitter) {
    emitter.on('update-stats', async () => {
      updateLoading.value = true;
      await fetchStats();
      await fetchSequences();
      updateLoading.value = false;
      lastUpdated.value = new Date();
    });
  }
});

// Limpiar intervalo al desmontar
onUnmounted(() => {
  if (autoUpdateInterval) {
    clearInterval(autoUpdateInterval);
  }
});

// Obtener estadísticas
const fetchStats = async () => {
  try {
    const data = await getRouletteStats();
    if (data) {
      stats.value = data;
    }
  } catch (error) {
    console.error('Error fetching stats:', error);
  }
};

// Obtener secuencias
const fetchSequences = async () => {
  try {
    const data = await getRouletteNumberSequences(50);
    if (data) {
      sequences.value = data;
    }
  } catch (error) {
    console.error('Error fetching sequences:', error);
  }
};

// Análisis de Tía Lu
const generateTiaLuAnalysis = async () => {
  try {
    const numbers = await generateTiaLuPredictions();
    patternAnalysis.value = `Según el análisis "Tía Lu", hay una mayor probabilidad de que salgan los siguientes números: ${numbers.join(', ')}. Este método se basa en patrones de números desencadenantes.`;
  } catch (error) {
    console.error('Error generating analysis:', error);
    patternAnalysis.value = 'No se pudo generar el análisis en este momento.';
  }
};

// Análisis de Puxa Ultra
const generatePuxaUltraAnalysis = async () => {
  try {
    const numbers = await generatePuxaUltraPredictions();
    patternAnalysis.value = `De acuerdo al método "Puxa Ultra", los números recomendados son: ${numbers.join(', ')}. Este método analiza la suma de los últimos 3 números para predecir patrones.`;
  } catch (error) {
    console.error('Error generating analysis:', error);
    patternAnalysis.value = 'No se pudo generar el análisis en este momento.';
  }
};

// Calcular totales para porcentajes
const columnsTotal = computed(() => {
  const c = stats.value.columns;
  return (c?.c1 || 0) + (c?.c2 || 0) + (c?.c3 || 0);
});

const dozensTotal = computed(() => {
  const d = stats.value.dozens;
  return (d?.d1 || 0) + (d?.d2 || 0) + (d?.d3 || 0);
});

// Calcular porcentaje
const getPercentage = (value?: number, total?: number) => {
  if (!value || !total) return 0;
  return Math.round((value / total) * 100);
};

// Obtener clase de color para un número
const getNumberBackgroundClass = (num: number) => {
  // Determinar el color del número
  const redNumbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36];
  
  if (num === 0) {
    return 'bg-green-600';
  } else if (redNumbers.includes(num)) {
    return 'bg-red-600';
  } else {
    return 'bg-gray-800';
  }
};

// Formatear la fecha de última actualización
const formattedLastUpdated = computed(() => {
  return lastUpdated.value.toLocaleTimeString();
});

// Función para purgar todas las estadísticas
const purgeAllStatistics = async () => {
  if (!confirm('¿Estás seguro de que quieres purgar TODAS las estadísticas del sistema? Esta acción eliminará:\n\n• Todos los números de la base de datos\n• Estadísticas de columnas y docenas\n• Números calientes y fríos\n• Contadores par/impar y rojo/negro\n• Historial completo\n\nEsta acción NO se puede deshacer.')) {
    return;
  }

  try {
    updateLoading.value = true;

    // Llamar a la función de purga de la API
    const result = await apiPurgeAllStatistics();

    // Resetear estadísticas locales
    stats.value = {
      hotNumbers: [],
      coldNumbers: [],
      redVsBlack: { red: 0, black: 0 },
      oddVsEven: { odd: 0, even: 0 },
      columns: { c1: 0, c2: 0, c3: 0 },
      dozens: { d1: 0, d2: 0, d3: 0 },
      lastNumbers: []
    };

    sequences.value = null;
    patternAnalysis.value = '';
    lastUpdated.value = new Date();

    // Emitir evento para que otros componentes se actualicen
    if (emitter) {
      emitter.emit('statistics-purged');
      emitter.emit('update-stats');
    }

    alert(`✅ ${result.message}${result.deleted_keys ? ` (${result.deleted_keys} keys eliminadas)` : ''}`);
  } catch (error) {
    console.error('Error al purgar estadísticas:', error);
    alert(`❌ Error al purgar estadísticas: ${error.message || 'Error desconocido'}`);
  } finally {
    updateLoading.value = false;
  }
};
</script> 