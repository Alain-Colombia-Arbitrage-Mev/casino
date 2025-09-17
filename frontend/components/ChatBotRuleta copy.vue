<template>
  <div class="bg-white p-4 rounded-lg shadow-md h-full flex flex-col">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold text-gray-800">Chat en Vivo</h2>
      <div class="text-sm font-medium bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
        Lightning Roulette - Evolution
      </div>
    </div>
    
    <!-- Área de chat -->
    <div class="flex-1 overflow-y-auto mb-4 border rounded-lg p-3">
      <div class="flex justify-end mb-2">
        <button 
          @click="clearLastMessages(5)" 
          class="text-xs bg-gray-200 hover:bg-gray-300 text-gray-600 px-2 py-1 rounded flex items-center"
          v-if="chatMessages.length > 6"
        >
          <span>Limpiar 5 últimos mensajes</span>
        </button>
      </div>
      <div 
        v-for="(message, index) in chatMessages" 
        :key="'msg-' + message.id"
        class="mb-3 p-2 rounded-lg"
        :class="message.sender === 'user' ? 'bg-blue-100 ml-8' : 'bg-gray-100 mr-8'"
      >
        <div v-if="message.sender === 'bot' && message.numbersGenerated" class="mb-2">
          <div class="font-medium mb-1" v-once>Números generados:</div>
          <div class="flex flex-wrap gap-1 mb-2">
            <span 
              v-for="num in [...message.numbersGenerated].sort((a, b) => a - b)" 
              :key="message.id + '-' + num"
              class="inline-block w-7 h-7 rounded-full bg-gray-800 text-white flex items-center justify-center text-xs font-bold"
            >
              {{ num }}
            </span>
          </div>
          <div v-if="message.isWinning !== undefined" class="mt-1">
            <span 
              class="px-2 py-1 rounded text-xs font-bold"
              :class="message.isWinning ? 'bg-green-500 text-white' : 'bg-red-500 text-white'"
            >
              {{ message.isWinning ? '¡Victoria!' : 'Derrota' }}
            </span>
          </div>
        </div>
        <p>{{ message.message }}</p>
        <div class="text-xs text-gray-500 mt-1">{{ formatTime(message.timestamp) }}</div>
      </div>
    </div>
    
    <!-- Información del último número ganador -->
    <div v-if="lastWinningResult && lastWinningResult.isWinning" class="mb-4 bg-green-50 p-3 rounded-lg border border-green-200">
      <h3 class="text-lg font-semibold text-green-700 mb-2">¡Último Resultado Ganador!</h3>
      <div class="flex items-center mb-2">
        <span class="font-bold text-xl mr-2">Número:</span>
        <span class="inline-block w-8 h-8 rounded-full bg-gray-800 text-white flex items-center justify-center font-bold">
          {{ lastWinningResult.number }}
        </span>
      </div>
      <div class="text-sm mb-2">
        <p class="font-semibold">Grupos donde apareció:</p>
        <ul class="pl-4 list-disc">
          <li v-for="(group, index) in lastWinningResult.matchingGroups" :key="index">
            {{ group }}
          </li>
        </ul>
      </div>
      <div v-if="lastWinningResult.rouletteSector" class="text-sm mb-2 bg-blue-50 p-2 rounded">
        <p class="font-semibold text-blue-700">
          Sector de la ruleta: <span class="text-blue-900">{{ lastWinningResult.rouletteSector }}</span>
        </p>
        <p class="text-xs text-blue-600 mt-1">
          Los sectores son importantes para estrategias avanzadas en Lightning Roulette.
        </p>
      </div>
      <div class="text-xs text-yellow-600 font-medium">
        ⚡ Lightning Roulette de Evolution: Verifica si el número tuvo multiplicador especial.
      </div>
    </div>
    
    <!-- Contador de victorias y derrotas -->
    <div class="mb-4 bg-gray-100 p-3 rounded-lg">
      <div class="flex justify-between mb-2">
        <div class="text-center flex-1">
          <div class="text-sm font-medium text-gray-700">Victorias</div>
          <div class="text-xl font-bold text-green-600">{{ winCount }}</div>
        </div>
        <div class="text-center flex-1">
          <div class="text-sm font-medium text-gray-700">Derrotas</div>
          <div class="text-xl font-bold text-red-600">{{ loseCount }}</div>
        </div>
        <div class="text-center flex-1">
          <div class="text-sm font-medium text-gray-700">Efectividad</div>
          <div class="text-xl font-bold" :class="getEfficiencyColor">
            {{ calculateEfficiency }}%
          </div>
        </div>
      </div>
      <div class="flex justify-center">
        <button 
          @click="resetCounters" 
          class="text-xs bg-gray-200 hover:bg-gray-300 text-gray-700 px-2 py-1 rounded"
        >
          Reiniciar contadores
        </button>
      </div>
    </div>
    
    <!-- Estadísticas detalladas de victorias por grupo -->
    <div class="mb-4 bg-indigo-50 p-4 rounded-lg border border-indigo-200">
      <div class="flex justify-between items-center mb-3">
        <h3 class="text-lg font-semibold text-indigo-700">Análisis de Victorias por Grupo</h3>
        <div class="flex gap-2">
          <button 
            @click="statsViewMode = 'details'" 
            class="text-xs px-2 py-1 rounded"
            :class="statsViewMode === 'details' ? 'bg-indigo-600 text-white' : 'bg-indigo-100 text-indigo-700'"
          >
            Detalles
          </button>
          <button 
            @click="statsViewMode = 'chart'" 
            class="text-xs px-2 py-1 rounded"
            :class="statsViewMode === 'chart' ? 'bg-indigo-600 text-white' : 'bg-indigo-100 text-indigo-700'"
          >
            Gráfico
          </button>
          <button 
            @click="showStatsDetails = !showStatsDetails" 
            class="text-xs bg-indigo-100 hover:bg-indigo-200 text-indigo-700 px-2 py-1 rounded flex items-center"
            v-if="statsViewMode === 'details'"
          >
            <span v-if="showStatsDetails">Ocultar</span>
            <span v-else>Ver Detalles</span>
            <span class="ml-1">{{ showStatsDetails ? '▲' : '▼' }}</span>
          </button>
        </div>
      </div>

      <!-- Vista de detalles -->
      <div v-if="statsViewMode === 'details'">
        <transition name="fade">
          <div v-if="showStatsDetails" class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Grupos estándar -->
            <div class="bg-white p-3 rounded shadow-sm">
              <h4 class="font-medium text-gray-700 mb-2">Grupos Estándar</h4>
              <ul class="space-y-1">
                <li v-for="(groupName, index) in ['group20', 'group12', 'group8', 'group6', 'group4']" :key="index" class="flex justify-between items-center">
                  <span class="text-sm">{{ getGroupLabel(groupName) }}</span>
                  <span class="font-medium text-indigo-600 bg-indigo-50 px-2 py-1 rounded-lg text-sm">
                    {{ groupWinStats[groupName] || 0 }} victorias
                  </span>
                </li>
              </ul>
            </div>

            <!-- Grupos estadísticos -->
            <div class="bg-white p-3 rounded shadow-sm">
              <h4 class="font-medium text-gray-700 mb-2">Grupos Estadísticos</h4>
              <ul class="space-y-1">
                <li v-for="(groupName, index) in ['groupTerminals', 'groupParity', 'groupColumns', 'groupDozens', 'groupRecent']" :key="index" class="flex justify-between items-center">
                  <span class="text-sm">{{ getLocalStatGroupLabel(groupName) }}</span>
                  <span class="font-medium text-green-600 bg-green-50 px-2 py-1 rounded-lg text-sm">
                    {{ groupWinStats[groupName] || 0 }} victorias
                  </span>
                </li>
              </ul>
            </div>

            <!-- Grupos IA -->
            <div class="bg-white p-3 rounded shadow-sm">
              <h4 class="font-medium text-gray-700 mb-2">Grupos IA</h4>
              <ul class="space-y-1">
                <li v-for="(groupName, index) in ['groupCycles', 'groupNeighbors', 'groupSection', 'groupAlternate', 'groupRecentAI', 'groupSectors', 'groupVecinos']" :key="index" class="flex justify-between items-center">
                  <span class="text-sm">{{ getAIGroupLabel(groupName) }}</span>
                  <span class="font-medium text-purple-600 bg-purple-50 px-2 py-1 rounded-lg text-sm">
                    {{ groupWinStats[groupName] || 0 }} victorias
                  </span>
                </li>
              </ul>
            </div>

            <!-- Sectores de ruleta -->
            <div class="bg-white p-3 rounded shadow-sm">
              <h4 class="font-medium text-gray-700 mb-2">Sectores de Ruleta</h4>
              <ul class="space-y-1">
                <li v-for="(groupName, displayName) in { 'voisinsDeZero': 'Vecinos del Cero', 'tiers': 'Tercios del Cilindro', 'orphelins': 'Huérfanos', 'jeuZero': 'Juego del Cero' }" :key="groupName" class="flex justify-between items-center">
                  <span class="text-sm">{{ displayName }}</span>
                  <span class="font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-lg text-sm">
                    {{ groupWinStats[groupName] || 0 }} victorias
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </transition>

        <div v-if="!showStatsDetails" class="text-center text-sm text-indigo-500 mt-2">
          Haz clic en "Ver Detalles" para mostrar el análisis completo de victorias por grupo
        </div>
      </div>
      
      <!-- Vista de gráfico -->
      <div v-if="statsViewMode === 'chart'" class="bg-white p-3 rounded shadow-sm">
        <h4 class="font-medium text-gray-700 mb-2 text-center">Número de Victorias por Grupo</h4>
        
        <!-- Filtros para el gráfico -->
        <div class="flex justify-center gap-2 mb-4">
          <button 
            v-for="category in ['standard', 'statistical', 'ai', 'sectors']" 
            :key="category"
            @click="chartCategory = category"
            class="text-xs px-2 py-1 rounded-full"
            :class="chartCategory === category ? 
              (category === 'standard' ? 'bg-indigo-600 text-white' : 
              category === 'statistical' ? 'bg-green-600 text-white' : 
              category === 'ai' ? 'bg-purple-600 text-white' : 
              'bg-blue-600 text-white') : 'bg-gray-100 text-gray-700'"
          >
            {{ 
              category === 'standard' ? 'Estándar' : 
              category === 'statistical' ? 'Estadístico' : 
              category === 'ai' ? 'IA' : 'Sectores' 
            }}
          </button>
        </div>
        
        <!-- Gráfico de barras simple -->
        <div class="h-60 flex items-end justify-around border-b border-l border-gray-300 relative">
          <!-- Eje Y - Etiquetas -->
          <div class="absolute -left-6 top-0 h-full flex flex-col justify-between text-xs text-gray-500">
            <span>{{ Math.max(...getChartData.values) }}</span>
            <span>{{ Math.max(...getChartData.values) / 2 }}</span>
            <span>0</span>
          </div>
          
          <!-- Barras -->
          <div 
            v-for="(value, index) in getChartData.values" 
            :key="index"
            class="w-8 mx-1 flex flex-col items-center justify-end"
          >
            <div 
              class="w-full rounded-t transition-all duration-500"
              :class="
                chartCategory === 'standard' ? 'bg-indigo-500' : 
                chartCategory === 'statistical' ? 'bg-green-500' : 
                chartCategory === 'ai' ? 'bg-purple-500' : 
                'bg-blue-500'
              "
              :style="{
                height: value > 0 ? `${(value / Math.max(...getChartData.values, 1)) * 100}%` : '2px',
                minHeight: '2px'
              }"
            ></div>
            <span class="text-xs mt-1 text-gray-600 whitespace-nowrap overflow-hidden text-ellipsis" style="max-width: 60px; text-align: center;">
              {{ getChartData.labels[index] }}
            </span>
            <span class="text-xs font-bold" :class="
              chartCategory === 'standard' ? 'text-indigo-700' : 
              chartCategory === 'statistical' ? 'text-green-700' : 
              chartCategory === 'ai' ? 'text-purple-700' : 
              'text-blue-700'
            ">{{ value }}</span>
          </div>
        </div>
      </div>

      <div class="flex justify-center mt-3">
        <button 
          @click="resetGroupStats" 
          class="text-xs bg-indigo-100 hover:bg-indigo-200 text-indigo-700 px-2 py-1 rounded"
        >
          Reiniciar estadísticas de grupos
        </button>
      </div>
    </div>
    
    <!-- Controles para generar números -->
    <div class="mb-4 grid grid-cols-3 gap-3">
      <button 
        @click="generateRandomPrediction"
        class="bg-purple-600 text-white px-3 py-2 rounded text-sm"
      >
        Generar Aleatorio
      </button>
      <button 
        @click="generateStatPrediction"
        class="bg-green-600 text-white px-3 py-2 rounded text-sm"
      >
        Usar Estadísticas
      </button>
      <button 
        @click="generateTiaLuPrediction"
        class="bg-pink-600 text-white px-3 py-2 rounded text-sm"
      >
        Tía Lu
      </button>
      <button 
        @click="generatePuxaUltraPrediction"
        class="bg-blue-600 text-white px-3 py-2 rounded text-sm"
      >
        Puxa Ultra
      </button>
      <button 
        @click="checkLastNumberResult"
        class="bg-amber-600 text-white px-3 py-2 rounded text-sm col-span-2"
      >
        Verificar último número
      </button>
    </div>
    
    <!-- Generación de grupos de números -->
    <div class="mb-4">
      <div class="flex justify-between items-center mb-2">
        <h3 class="text-lg font-semibold text-gray-700">Grupos de números</h3>
        <div class="flex gap-2">
          <button 
            @click="refreshAllGroups"
            class="bg-blue-600 text-white px-2 py-1 rounded text-xs"
            title="Actualizar todos los grupos"
          >
            <span>↻</span>
          </button>
        </div>
      </div>
      
      <div class="flex items-center mb-2">
        <div class="text-sm font-medium mr-2">Mostrar:</div>
        <div class="flex gap-2">
          <button 
            @click="activeGroupSet = 'standard'"
            class="px-2 py-1 rounded text-xs"
            :class="activeGroupSet === 'standard' ? 'bg-blue-600 text-white' : 'bg-gray-200'"
          >
            Estándar
          </button>
          <button 
            @click="activeGroupSet = 'statistical'"
            class="px-2 py-1 rounded text-xs"
            :class="activeGroupSet === 'statistical' ? 'bg-green-600 text-white' : 'bg-gray-200'"
          >
            Estadístico
          </button>
          <button 
            @click="activeGroupSet = 'ai'"
            class="px-2 py-1 rounded text-xs"
            :class="activeGroupSet === 'ai' ? 'bg-purple-600 text-white' : 'bg-gray-200'"
          >
            IA
          </button>
        </div>
      </div>
      
      <!-- Grupos estándar -->
      <div v-if="activeGroupSet === 'standard'" class="space-y-3">
        <div v-for="(group, groupName) in numberGroups" :key="groupName" class="bg-gray-100 p-2 rounded">
          <div class="flex justify-between mb-1">
            <span class="font-medium">{{ getGroupLabel(groupName) }}</span>
            <span v-if="lastWinningResult?.details && lastWinningResult.details[groupName]" class="text-green-600 font-bold">
              ✓
            </span>
          </div>
          <div class="flex flex-wrap gap-1">
            <span 
              v-for="num in [...group].sort((a, b) => a - b)" 
              :key="num"
              class="inline-block w-6 h-6 rounded-full bg-gray-700 text-white flex items-center justify-center text-xs font-bold"
            >
              {{ num }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- Grupos estadísticos locales -->
      <div v-if="activeGroupSet === 'statistical'" class="space-y-3">
        <div v-for="(group, groupName) in localStatGroups" :key="groupName" class="bg-green-50 p-2 rounded">
          <div class="flex justify-between mb-1">
            <span class="font-medium">{{ getLocalStatGroupLabel(groupName) }}</span>
            <span v-if="isNumberInGroup(lastWinningResult?.number, group)" class="text-green-600 font-bold">
              ✓
            </span>
          </div>
          <div class="flex flex-wrap gap-1">
            <span 
              v-for="num in [...group].sort((a, b) => a - b)" 
              :key="num"
              class="inline-block w-6 h-6 rounded-full bg-green-700 text-white flex items-center justify-center text-xs font-bold"
            >
              {{ num }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- Grupos IA -->
      <div v-if="activeGroupSet === 'ai'" class="space-y-3">
        <div v-for="(group, groupName) in aiGroups" :key="groupName" class="bg-purple-50 p-2 rounded">
          <div class="flex justify-between mb-1">
            <span class="font-medium">{{ getAIGroupLabel(groupName) }}</span>
            <span v-if="isNumberInGroup(lastWinningResult?.number, group)" class="text-green-600 font-bold">
              ✓
            </span>
          </div>
          <div class="flex flex-wrap gap-1">
            <span 
              v-for="num in [...group].sort((a, b) => a - b)" 
              :key="num"
              class="inline-block w-6 h-6 rounded-full bg-purple-700 text-white flex items-center justify-center text-xs font-bold"
            >
              {{ num }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Input del usuario -->
    <div class="mt-auto">
      <form @submit.prevent="sendMessage" class="flex gap-2">
        <input
          v-model="userInput"
          type="text"
          placeholder="Escribe un mensaje o ingresa un número..."
          class="flex-1 border rounded px-3 py-2"
        />
        <button 
          type="submit"
          class="bg-blue-600 text-white px-4 py-2 rounded"
        >
          Enviar
        </button>
        <button 
          type="button"
          @click="toggleVoiceRecognition"
          class="text-white px-4 py-2 rounded relative"
          :class="getVoiceButtonClass"
          :title="getVoiceButtonTitle"
        >
          <span v-if="isListening">Escuchando...</span>
          <span v-else-if="voiceError && voiceError.includes('Error de red')">Reintentar 🔄</span>
          <span v-else-if="voiceError">Error 🔄</span>
          <span v-else>🎤</span>
          
          <!-- Indicador de estado -->
          <span v-if="voiceStatus !== 'idle'" class="absolute -top-2 -right-2 w-3 h-3 rounded-full"
            :class="voiceStatusClass"></span>
        </button>
      </form>
      <div v-if="voiceError" class="text-red-500 text-sm mt-1 flex items-center flex-wrap">
        <span>{{ voiceError }}</span>
        <button 
          v-if="voiceError.includes('Error de red') || voiceError.includes('conexión') || voiceError.includes('reconect')" 
          @click="retryVoiceRecognition" 
          class="ml-2 bg-yellow-500 text-white px-2 py-1 rounded text-xs mb-1"
        >
          Reintentar reconocimiento
        </button>
        <button 
          v-if="voiceError" 
          @click="switchToManualInput" 
          class="ml-2 bg-blue-500 text-white px-2 py-1 rounded text-xs mb-1"
        >
          Usar teclado
        </button>
      </div>
      
      <!-- Estado del reconocimiento de voz -->
      <div v-if="showVoiceStatus" class="text-xs mt-1 flex items-center">
        <span class="w-2 h-2 rounded-full mr-1" :class="voiceStatusClass"></span>
        <span :class="voiceStatusTextClass">{{ voiceStatusText }}</span>
        <button
          v-if="voiceStatus === 'error'"
          @click="showVoiceHelp"
          class="ml-1 text-blue-500 underline"
        >
          Ayuda
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, inject, computed } from 'vue';
import { processNumbersInput, getLastRouletteNumbers } from '~/utils/api';
import { 
  generateRandomNumbers, 
  generateStatPredictions, 
  generateTiaLuPredictions,
  generatePuxaUltraPredictions,
  generateNumberGroups,
  generateLocalStatisticalGroups,
  generateAIBasedGroups,
  checkWinningNumber
} from '~/utils/predictions';
import { AudioRecorder, recognizeSpeech } from '~/utils/speech';
import type { ChatMessage } from '~/types';
import { ROULETTE_WHEEL_SECTORS, getRouletteSectors } from '~/utils/predictions';

// Evento de actualización para comunicación entre componentes
const emitter = inject('emitter') as any;

// Variables reactivas
const userInput = ref('');
const chatMessages = ref<ChatMessage[]>([]);
const apiBaseUrl = ref(process.server ? '' : window.location.origin.includes('localhost') ? 'http://localhost:5000' : window.location.origin);
const recentNumbers = ref<number[]>([]);
const isProcessingVoice = ref(false);
const voiceError = ref('');
const voiceStatus = ref<'idle' | 'listening' | 'processing' | 'error' | 'success'>('idle');
const showVoiceStatus = ref(false);
const autoRetryEnabled = ref(true);
const manualInputPreferred = ref(false);

// Variables para seguimiento de sectores frecuentes
const sectorCounts = ref<Record<string, number>>({
  'voisinsDeZero': 0,
  'tiers': 0,
  'orphelins': 0,
  'jeuZero': 0,
  'redSector': 0,
  'blackSector': 0
});
const sectorHistory = ref<{sector: string, number: number}[]>([]);
const SECTOR_THRESHOLD = 3; // Número de repeticiones para considerar un sector "caliente"

// Variables para grupos de números
const numberGroups = ref<Record<string, number[]>>({
  group20: [],
  group12: [],
  group8: [],
  group6: [],
  group4: []
});
const localStatGroups = ref<Record<string, number[]>>({});
const aiGroups = ref<Record<string, number[]>>({});
const activeGroupSet = ref('standard');
const lastWinningResult = ref<any>(null);
const isListening = ref(false);

// Variables para conteo de victorias y derrotas
const winCount = ref(0);
const loseCount = ref(0);

// Variables para análisis de victorias por grupo
const groupWinStats = ref<Record<string, number>>({
  // Grupos estándar
  group20: 0,
  group12: 0,
  group8: 0,
  group6: 0,
  group4: 0,
  // Grupos estadísticos
  groupTerminals: 0,
  groupParity: 0,
  groupColumns: 0,
  groupDozens: 0,
  groupRecent: 0,
  // Grupos IA
  groupCycles: 0,
  groupNeighbors: 0,
  groupSection: 0,
  groupAlternate: 0,
  groupRecentAI: 0,
  groupSectors: 0,
  groupVecinos: 0,
  // Sectores de ruleta
  voisinsDeZero: 0,
  tiers: 0,
  orphelins: 0,
  jeuZero: 0,
  redSector: 0,
  blackSector: 0
});

// Variables para reconocimiento de voz
let recognition: any = null;
// Nuevo sistema de reconocimiento con Google Speech
const audioRecorder = ref<AudioRecorder | null>(null);

// Definición de tipo para el resultado de checkGroupsForNumber
type GroupCheckResult = {
  found: boolean;
  isWinning: boolean;
  groupName: string;
  predictedNumbers: number[];
  matchingGroups: string[];
  rouletteSector: string;
};

// Función para generar mensaje de victoria con detalles de grupos
const getWinningMessage = (number: number, result: GroupCheckResult): string => {
  let message = '';
  
  // Comprobar explícitamente en qué grupos principales se encontró el número
  const inGroup20 = numberGroups.value.group20?.includes(number) || false;
  const inGroup12 = numberGroups.value.group12?.includes(number) || false;
  
  // Construir el mensaje base según dónde se encontró
  if (inGroup20 && inGroup12) {
    message = `¡El número ${number} es una VICTORIA! Se encontró en ambos grupos principales: Grupo 20 y Grupo 12.`;
  } else if (inGroup20) {
    message = `¡El número ${number} es una VICTORIA! Se encontró en el Grupo 20.`;
  } else if (inGroup12) {
    message = `¡El número ${number} es una VICTORIA! Se encontró en el Grupo 12.`;
  } else {
    // Esta condición no debería ocurrir con la nueva lógica, pero la mantenemos por seguridad
    message = `¡El número ${number} es una VICTORIA! Se encontró en alguno de los grupos principales.`;
    console.warn("Advertencia: Victoria detectada pero no se encontró el número en ningún grupo principal. Revisar lógica.");
  }
  
  // Añadir verificación explícita para claridad
  message += `\n\nVerificación explícita:`;
  message += `\n• Grupo 20: ${inGroup20 ? '✓' : '✗'}`;
  message += `\n• Grupo 12: ${inGroup12 ? '✓' : '✗'}`;
  
  // Añadir información sobre otros grupos coincidentes
  if (result.matchingGroups && result.matchingGroups.length > 0) {
    message += `\n\nTambién coincide con: ${result.matchingGroups.join(', ')}.`;
  }
  
  // Añadir información del sector de la ruleta
  if (result.rouletteSector) {
    message += `\n\nEl número pertenece al sector: ${result.rouletteSector}.`;
  }
  
  return message;
};

// Generar mensaje para derrota
const getLosingMessage = (number: number, result: GroupCheckResult): string => {
  let message = `El número ${number} es una DERROTA. No se encontró ni en el Grupo 20 ni en el Grupo 12.`;
  
  // Añadir detalles sobre los grupos principales para claridad
  const group20 = numberGroups.value.group20 || [];
  const group12 = numberGroups.value.group12 || [];
  
  message += `\n\nVerificación explícita:`;
  message += `\n• Grupo 20: ${group20.includes(number) ? '✓' : '✗'}`;
  message += `\n• Grupo 12: ${group12.includes(number) ? '✓' : '✗'}`;
  
  // Mostrar los contenidos de los grupos para verificación
  const group20Sorted = [...group20].sort((a, b) => a - b);
  const group12Sorted = [...group12].sort((a, b) => a - b);
  
  message += `\n\nContenido de los grupos de predicción:`;
  message += `\n• Grupo 20: [${group20Sorted.join(', ')}]`;
  message += `\n• Grupo 12: [${group12Sorted.join(', ')}]`;
  
  // Añadir información del sector si existe
  if (result.rouletteSector) {
    message += `\n\nEl número ${number} pertenece al sector: ${result.rouletteSector}`;
  }
  
  // Sugerir grupos donde sí apareció, si hay alguno
  if (result.matchingGroups && result.matchingGroups.length > 0) {
    message += `\n\nSin embargo, sí apareció en los siguientes grupos secundarios (que no cuentan para victoria): ${result.matchingGroups.join(', ')}.`;
  }
  
  return message;
}

// Obtener últimos números de la ruleta
const fetchLastNumbers = async () => {
  try {
    // Asegurarse de obtener datos frescos 
    console.log("Obteniendo últimos números...");
    
    // Intentar hasta 3 veces
    let attempts = 0;
    const maxAttempts = 3;
    let success = false;
    
    while (attempts < maxAttempts && !success) {
      attempts++;
      try {
        // Esperamos un momento para dar tiempo a que se actualice la base de datos
        if (attempts > 1) {
          await new Promise(resolve => setTimeout(resolve, 500 * attempts));
        }
        
        const numbers = await getLastRouletteNumbers(20);
        if (numbers && numbers.length > 0) {
          recentNumbers.value = numbers.map(item => item.number);
          success = true;
          console.log(`Últimos números obtenidos: ${recentNumbers.value.join(', ')}`);
        } else {
          console.warn(`Intento ${attempts}: No se obtuvieron números`);
        }
      } catch (error) {
        console.error(`Error en intento ${attempts} al obtener últimos números:`, error);
      }
    }
    
    if (!success) {
      console.error("No se pudieron obtener los últimos números después de múltiples intentos");
    }
    
  } catch (error) {
    console.error('Error al obtener últimos números:', error);
  }
};

// Inicializar
onMounted(async () => {
  // Cargar contadores de localStorage si existen
  if (process.client) {
    const savedWins = localStorage.getItem('roulette_wins');
    const savedLosses = localStorage.getItem('roulette_losses');
    
    if (savedWins) winCount.value = parseInt(savedWins);
    if (savedLosses) loseCount.value = parseInt(savedLosses);
    
    // Cargar estadísticas de victorias por grupo
    const savedGroupStats = localStorage.getItem('roulette_group_stats');
    if (savedGroupStats) {
      try {
        groupWinStats.value = JSON.parse(savedGroupStats);
      } catch (e) {
        console.error('Error parsing group stats:', e);
      }
    }
    
    // Cargar historial de sectores
    const savedSectorHistory = localStorage.getItem('roulette_sector_history');
    if (savedSectorHistory) {
      try {
        sectorHistory.value = JSON.parse(savedSectorHistory);
      } catch (e) {
        console.error('Error parsing sector history:', e);
      }
    }
    
    // Cargar contadores de sectores
    const savedSectorCounts = localStorage.getItem('roulette_sector_counts');
    if (savedSectorCounts) {
      try {
        sectorCounts.value = JSON.parse(savedSectorCounts);
      } catch (e) {
        console.error('Error parsing sector counts:', e);
      }
    }
  }
  
  await fetchLastNumbers();
  await refreshAllGroups();
  
  // Mensaje de bienvenida
  chatMessages.value.push({
    id: Date.now(),
    sender: 'bot',
    message: '¡Bienvenido al asistente de Ruleta! Puedes ingresar números o pedir predicciones.',
    timestamp: new Date().toISOString()
  });
  
  // Inicializar reconocimiento de voz si está disponible
  initVoiceRecognition();
  
  // Escuchar eventos para actualización solo cuando se ingresan números nuevos
  if (emitter) {
    // Actualizar grupos cuando los números se actualizan explícitamente
    emitter.on('number-registered', async (data) => {
      await fetchLastNumbers();
      await refreshAllGroups();
    });
    
    // Escuchar solicitudes específicas de generación de predicciones
    emitter.on('request-predictions-update', async (data: { lastNumber: number; allNumbers: number[] }) => {
      // Esperamos a que se actualicen los grupos
      await fetchLastNumbers();
      await refreshAllGroups();
      
      // Verificar si se proporcionó un último número jugado
      if (data && data.lastNumber) {
        // Generar predicciones automáticas
        generateAutomaticPredictions(data.lastNumber);
      }
    });
  }
});

// Observar cambios en los contadores para guardarlos en localStorage
watch([winCount, loseCount, groupWinStats, sectorHistory, sectorCounts], ([newWins, newLosses, newGroupStats, newSectorHistory, newSectorCounts]) => {
  if (process.client) {
    localStorage.setItem('roulette_wins', newWins.toString());
    localStorage.setItem('roulette_losses', newLosses.toString());
    localStorage.setItem('roulette_group_stats', JSON.stringify(newGroupStats));
    localStorage.setItem('roulette_sector_history', JSON.stringify(newSectorHistory));
    localStorage.setItem('roulette_sector_counts', JSON.stringify(newSectorCounts));
  }
});

// Limpiar al desmontar
onBeforeUnmount(() => {
  if (recognition) {
    recognition.stop();
  }
});

// Refrescar todos los grupos de números
const refreshAllGroups = async () => {
  try {
    console.log('========== INICIANDO ACTUALIZACIÓN DE GRUPOS ==========');
    console.log(`Hora de actualización: ${new Date().toLocaleTimeString()}`);
    
    // Actualizar grupos estándar
    const groups = await generateNumberGroups();
    numberGroups.value = groups;
    
    // Actualizar grupos estadísticos locales
    const localGroups = await generateLocalStatisticalGroups();
    localStatGroups.value = localGroups;
    
    // Actualizar grupos basados en IA
    const aiBasedGroups = await generateAIBasedGroups();
    aiGroups.value = aiBasedGroups;

    // DEBUG: Mostrar los grupos generados en la consola
    console.log('======= GRUPOS REGENERADOS COMPLETAMENTE =======');
    console.log('Grupo 20:', [...numberGroups.value.group20].sort((a, b) => a - b));
    console.log('Grupo 12:', [...numberGroups.value.group12].sort((a, b) => a - b));
    console.log('Grupo 8:', [...numberGroups.value.group8].sort((a, b) => a - b));
    console.log('Grupo 6:', [...numberGroups.value.group6].sort((a, b) => a - b));
    console.log('Grupo 4:', [...numberGroups.value.group4].sort((a, b) => a - b));
    console.log('===============================================');
    
    return true; // Indicar que la actualización fue exitosa
  } catch (error) {
    console.error('Error generating number groups:', error);
    return false; // Indicar que hubo un error
  }
};

// Verificar si un número está en un grupo
const isNumberInGroup = (number: number | undefined, group: number[] | undefined) => {
  if (!number || !group) return false;
  return group.includes(number);
};

// Inicializar reconocimiento de voz
const initVoiceRecognition = () => {
  // Si el usuario prefiere entrada manual, no inicializar reconocimiento
  if (manualInputPreferred.value) {
    console.log('Reconocimiento de voz desactivado por preferencia del usuario');
    return;
  }

  // Verificar si el navegador soporta la API de reconocimiento de voz
  if (process.client) {
    try {
      // Actualizar estado
      voiceStatus.value = 'idle';
      showVoiceStatus.value = true;
      
      // Primero verificar si está disponible SpeechRecognition nativa
      if ('SpeechRecognition' in window) {
        recognition = new window.SpeechRecognition();
      } 
      // O la versión con prefijo webkit (Chrome, Safari, etc.)
      else if ('webkitSpeechRecognition' in window) {
        // @ts-ignore - webkitSpeechRecognition existe pero TypeScript no lo reconoce
        recognition = new window.webkitSpeechRecognition();
      } 
      else {
        voiceError.value = 'Tu navegador no soporta reconocimiento de voz.';
        return;
      }
      
      // Configurar reconocimiento
      recognition.lang = 'es-ES';
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.maxAlternatives = 3; // Obtener hasta 3 alternativas de reconocimiento
      
      // Sistema de reintentos automáticos para problemas de red
      let retryCount = 0;
      const MAX_AUTO_RETRIES = 3;
      
      // Modificar el manejador de resultados
      recognition.onresult = (event: any) => {
        try {
          // Actualizar estado
          voiceStatus.value = 'success';
          
          // Resetear contador de reintentos automáticos
          retryCount = 0;
          
          // Tomar el resultado con mayor confianza
          const transcript = event.results[0][0].transcript;
          console.log(`Texto reconocido: "${transcript}". Confianza: ${event.results[0][0].confidence}`);
          
          // También registrar alternativas para diagnóstico
          if (event.results[0].length > 1) {
            for (let i = 1; i < event.results[0].length; i++) {
              console.log(`Alternativa ${i}: "${event.results[0][i].transcript}". Confianza: ${event.results[0][i].confidence}`);
            }
          }
          
          userInput.value = transcript;
          // Usar setTimeout para desacoplar de posibles errores de WebSocket
          setTimeout(() => {
            sendMessage();
          }, 0);
          
          // Limpiar cualquier mensaje de error previo
          voiceError.value = '';
        } catch (error) {
          console.error('Error al procesar resultado de voz:', error);
          voiceError.value = 'Error al procesar la voz. Inténtalo de nuevo.';
          voiceStatus.value = 'error';
        }
      };
      
      // Modificar manejador de fin de reconocimiento
      recognition.onend = () => {
        isListening.value = false;
        
        // Si no hubo éxito ni error, cambiar estado a idle
        if (voiceStatus.value !== 'success' && voiceStatus.value !== 'error') {
          voiceStatus.value = 'idle';
        }
        
        // Si hubo un error de red y los reintentos automáticos están habilitados, reintentar
        if (voiceError.value.includes('Error de red') && autoRetryEnabled.value && retryCount < MAX_AUTO_RETRIES) {
          retryCount++;
          console.log(`Reintento automático ${retryCount}/${MAX_AUTO_RETRIES} por error de red...`);
          
          // Mostrar mensaje de reintento
          voiceError.value = `Error de red. Reintentando automáticamente (${retryCount}/${MAX_AUTO_RETRIES})...`;
          voiceStatus.value = 'processing';
          
          // Esperar un momento antes de reintentar
          setTimeout(() => {
            try {
              recognition.start();
              isListening.value = true;
              console.log('Reconocimiento reiniciado automáticamente');
            } catch (e) {
              console.error('Error al reiniciar automáticamente:', e);
              
              // Si falla el reintento automático, permitir al usuario reintentar manualmente
              if (retryCount >= MAX_AUTO_RETRIES) {
                voiceError.value = 'No se pudo reconectar automáticamente. Haz clic en el micrófono para reintentar.';
                voiceStatus.value = 'error';
              }
            }
          }, 1000);
        }
        
        // Después de 5 segundos, ocultar el indicador de estado si fue exitoso
        if (voiceStatus.value === 'success') {
          setTimeout(() => {
            if (voiceStatus.value === 'success') {
              showVoiceStatus.value = false;
            }
          }, 5000);
        }
      };
      
      // Modificar manejador de errores
      recognition.onerror = (event: any) => {
        isListening.value = false;
        voiceStatus.value = 'error';
        
        // Registrar detalles adicionales para diagnóstico
        console.error('Error detallado de reconocimiento de voz:', {
          error: event.error,
          message: event.message,
          timestamp: new Date().toISOString(),
          navigator: {
            onLine: navigator.onLine,
            userAgent: navigator.userAgent
          }
        });
        
        // Manejar específicamente errores de red
        if (event.error === 'network') {
          // Mensaje más detallado para errores de red
          voiceError.value = 'Error de conexión a los servidores de reconocimiento de voz. Verificando alternativas...';
          console.error('Error de red en el reconocimiento de voz:', event);
          
          // Intentar verificar conexión a internet
          if (!navigator.onLine) {
            voiceError.value = 'No hay conexión a internet. El reconocimiento de voz requiere conexión.';
          } else {
            // Si hay conexión pero falla el servidor de reconocimiento
            voiceError.value = 'Hay conexión a internet, pero no se puede conectar a los servidores de reconocimiento de voz.';
            
            // Sugerir alternativas (entrada manual)
            setTimeout(() => {
              chatMessages.value.push({
                id: Date.now(),
                sender: 'bot',
                message: 'El reconocimiento de voz está fallando. Puedes usar el teclado para ingresar números directamente.',
                timestamp: new Date().toISOString()
              });
            }, 500);
          }
          
          // No hace falta un setTimeout aquí ya que lo manejaremos con el reintento automático
          // en el evento onend
        } else if (event.error === 'no-speech') {
          voiceError.value = 'No se detectó ninguna voz. Intenta hablar más cerca del micrófono.';
        } else if (event.error === 'aborted') {
          voiceError.value = 'Reconocimiento de voz cancelado.';
        } else if (event.error === 'audio-capture') {
          voiceError.value = 'No se pudo capturar audio. Verifica que tu micrófono esté conectado y funcionando.';
        } else if (event.error === 'not-allowed') {
          voiceError.value = 'Permiso de micrófono denegado. Debes permitir el acceso al micrófono.';
        } else {
          voiceError.value = `Error de reconocimiento: ${event.error}`;
        }
        
        console.error('Error de reconocimiento de voz:', event);
      };

      console.log('Reconocimiento de voz inicializado correctamente');
    } catch (error) {
      console.error('Error al inicializar el reconocimiento de voz:', error);
      voiceError.value = 'Error al inicializar el reconocimiento de voz. Tu navegador puede no ser compatible.';
      voiceStatus.value = 'error';
    }
  }
};

// Modificar método toggleVoiceRecognition
const toggleVoiceRecognition = async () => {
  try {
    // Verificar conexión a internet
    if (!navigator.onLine) {
      voiceError.value = 'No hay conexión a internet. El reconocimiento de voz requiere conexión.';
      // Sugerir alternativas
      chatMessages.value.push({
        id: Date.now(),
        sender: 'bot',
        message: 'No hay conexión a internet. Por favor, ingresa los números manualmente usando el teclado.',
        timestamp: new Date().toISOString()
      });
      return;
    }
    
    // Si está escuchando, detener la grabación
    if (isListening.value) {
      if (audioRecorder.value && audioRecorder.value.getIsRecording()) {
        try {
          // Actualizar estado
          voiceStatus.value = 'processing';
          isListening.value = false;
        
          // Detener grabación y procesar
          const audioBlob = await audioRecorder.value.stopRecording();
          const transcript = await recognizeSpeech(audioBlob);
          
          if (transcript) {
            userInput.value = transcript;
            voiceStatus.value = 'success';
            
            // Pequeña pausa para actualizar UI
            setTimeout(() => {
              sendMessage();
            }, 100);
          } else {
            voiceError.value = 'No se detectó ningún texto. Intenta hablar más claro.';
            voiceStatus.value = 'error';
          }
        } catch (error) {
          console.error('Error al procesar la grabación:', error);
          voiceError.value = `Error al procesar la grabación: ${error.message || 'Error desconocido'}`;
          voiceStatus.value = 'error';
        }
      } else {
        // Si Web Speech API está activa, detenerla
        if (recognition) {
          try {
            recognition.stop();
          } catch (e) {
            console.log('Error al detener Web Speech API:', e);
          }
        }
        
        isListening.value = false;
        voiceStatus.value = 'idle';
      }
    } else {
      // Iniciar grabación con Google Speech
      voiceError.value = '';
      voiceStatus.value = 'processing';
      
      // Intentar usar Google Speech primero
      const googleSpeechSuccess = await useGoogleSpeechRecognition();
      
      // Si falla Google Speech, intentar con Web Speech como fallback
      if (!googleSpeechSuccess && navigator.mediaDevices.getUserMedia === undefined) {
        console.log('Fallback a Web Speech API');
        
        // Intentar inicializar Web Speech si no está inicializado
        if (!recognition) {
          initVoiceRecognition();
          
          if (!recognition) {
            console.error('No se pudo inicializar ningún sistema de reconocimiento de voz');
            voiceError.value = 'No se pudo inicializar el reconocimiento de voz. Intenta con otro navegador.';
            return;
          }
        }
        
        // Usar Web Speech como fallback
        try {
          recognition.start();
          isListening.value = true;
          voiceStatus.value = 'listening';
          console.log('Comenzando escucha de voz con Web Speech API (fallback)');
        } catch (startError) {
          console.error('Error al iniciar Web Speech API:', startError);
          voiceStatus.value = 'error';
          isListening.value = false;
          voiceError.value = 'Error al iniciar el reconocimiento. Inténtalo de nuevo o usa el teclado.';
        }
      }
    }
  } catch (error) {
    console.error('Error al alternar el reconocimiento de voz:', error);
    voiceError.value = 'Error en el sistema de reconocimiento de voz. Por favor, usa el teclado.';
    isListening.value = false;
    voiceStatus.value = 'error';
    
    // Sugerir alternativa de entrada manual
    chatMessages.value.push({
      id: Date.now(),
      sender: 'bot',
      message: 'Estamos teniendo problemas con el reconocimiento de voz. Por favor, usa el teclado para ingresar números.',
      timestamp: new Date().toISOString()
    });
  }
};

// Modificar método retryVoiceRecognition
const retryVoiceRecognition = async () => {
  voiceError.value = 'Reiniciando sistema de reconocimiento de voz...';
  voiceStatus.value = 'processing';
  
  // Detener cualquier grabación activa
  if (audioRecorder.value && audioRecorder.value.getIsRecording()) {
    try {
      await audioRecorder.value.stopRecording();
    } catch (e) {
      console.log('Error al detener grabación para reintentar:', e);
    }
  }
  
  // Detener cualquier instancia de Web Speech existente
  if (recognition) {
    try {
      recognition.stop();
    } catch (e) {
      console.log('Error al detener Web Speech para reintentar:', e);
    }
  }
  
  // Restablecer variables
  isListening.value = false;
  audioRecorder.value = null;
  
  // Verificar conexión a internet
  if (!navigator.onLine) {
    voiceError.value = 'No hay conexión a internet. El reconocimiento de voz requiere conexión.';
    voiceStatus.value = 'error';
    return;
  }
  
  // Pequeña pausa antes de reiniciar
  setTimeout(async () => {
    try {
      // Iniciar con Google Speech primero
      await useGoogleSpeechRecognition();
    } catch (error) {
      console.error('Error al reiniciar el reconocimiento de voz:', error);
      voiceError.value = 'Error al reiniciar. Por favor, usa el teclado o refresca la página.';
      voiceStatus.value = 'error';
      
      // Sugerir alternativa de entrada manual
      chatMessages.value.push({
        id: Date.now(),
        sender: 'bot',
        message: 'Seguimos teniendo problemas con el reconocimiento de voz. Puedes ingresar los números directamente usando el teclado.',
        timestamp: new Date().toISOString()
      });
    }
  }, 300);
};

// Enviar mensaje del usuario
const sendMessage = async () => {
  const message = userInput.value.trim();
  if (!message) return;
  
  // Agregar mensaje del usuario al chat
  chatMessages.value.push({
    id: Date.now(),
    sender: 'user',
    message: message,
    timestamp: new Date().toISOString()
  });
  
  // Limpiar el input después de enviar
  userInput.value = '';
  
  // Verificar si el mensaje contiene números (con comas, espacios o ambos)
  // Patrones posibles: "1,2,3", "1, 2, 3", "1 2 3", números mezclados con texto
  const containsMultipleNumbers = /\d+[,\s]+\d+/.test(message);
  const isJustOneNumber = /^\d+$/.test(message);
  
  // Verificar si es una petición para comprobar victoria
  const isCheckingWin = /gané|perdí|victoria|resultado|ganó|comparar|comprobar/i.test(message);
  
  // Nueva verificación para detectar diversas frases donde se menciona un número
  const patrones = [
    // Patrón "salió el X"
    /sal[ií][oó]\s+(?:el\s+)?(?:n[úu]mero\s+)?(\d{1,2})/i,
    // Patrón "el número X"
    /(?:el\s+)?n[úu]mero\s+(\d{1,2})/i,
    // Patrón "cayó el X"
    /cay[oó]\s+(?:el\s+)?(?:n[úu]mero\s+)?(\d{1,2})/i,
    // Patrón "tocó el X"
    /toc[oó]\s+(?:el\s+)?(?:n[úu]mero\s+)?(\d{1,2})/i,
    // Patrón "apareció el X"
    /apareci[oó]\s+(?:el\s+)?(?:n[úu]mero\s+)?(\d{1,2})/i,
    // Número solo (con verificación de que sea un número exacto)
    /^(\d{1,2})$/
  ];
  
  // Verificar cada patrón uno por uno
  let numberToAdd = null;
  for (const patron of patrones) {
    const match = message.match(patron);
    if (match && match[1]) {
      numberToAdd = parseInt(match[1]);
      console.log(`Reconocido número ${numberToAdd} por voz con patrón: ${patron}`);
      break;
    }
  }
  
  if (numberToAdd !== null) {
    // Validar que el número está en el rango válido de la ruleta (0-36)
    if (isNaN(numberToAdd) || numberToAdd < 0 || numberToAdd > 36) {
      chatMessages.value.push({
        id: Date.now(),
        sender: 'bot',
        message: `El número reconocido (${numberToAdd}) no es válido para la ruleta. Por favor, usa números entre 0 y 36.`,
        timestamp: new Date().toISOString()
      });
      return;
    }
    
    // Procesar directamente como un número individual
    try {
      // IMPORTANTE: Primero verificamos si el número está en los grupos ACTUALES
      // antes de procesar el número y regenerar grupos
      const currentResult = checkGroupsForNumber(numberToAdd);
      
      // Ahora procesamos el número y lo insertamos en la base de datos
      const processed = await processNumbersInput(numberToAdd.toString());
      
      if (processed && processed.processedCount > 0) {
        // Después de insertar el número, actualizamos la lista de números recientes
        await fetchLastNumbers();
        
        // Emitir evento para que otros componentes se actualicen con el número registrado
        if (emitter) {
          emitter.emit('number-registered', {
            number: numberToAdd
          });
          emitter.emit('numbers-updated');
          emitter.emit('last-number-played', numberToAdd);
          
          // Emitir el evento de resultado de la apuesta para actualizar contadores
          emitter.emit('number-played', {
            number: numberToAdd,
            isWinning: currentResult.isWinning
          });
        }
        
        // Preparar mensaje según el resultado que ya fue calculado con los grupos anteriores
        let resultMessage = "";
        if (currentResult.isWinning) {
          // Mensaje de victoria con información específica sobre el grupo ganador
          const inGroup20 = numberGroups.value.group20?.includes(numberToAdd) || false;
          const inGroup12 = numberGroups.value.group12?.includes(numberToAdd) || false;
          
          resultMessage = `¡El número ${numberToAdd} es una VICTORIA! `;
          
          if (inGroup20 && inGroup12) {
            resultMessage += `Se encontró en ambos grupos: Grupo 20 y Grupo 12.`;
          } else if (inGroup20) {
            resultMessage += `Se encontró en el Grupo 20.`;
          } else if (inGroup12) {
            resultMessage += `Se encontró en el Grupo 12.`;
          }
          
          // Añadir información sobre otros grupos coincidentes
          if (currentResult.matchingGroups && currentResult.matchingGroups.length > 0) {
            resultMessage += `\nTambién aparece en: ${currentResult.matchingGroups.join(', ')}`;
          }
        } else {
          // Mensaje de derrota con información específica sobre la falta en los grupos principales
          resultMessage = `El número ${numberToAdd} es una DERROTA. No se encontró ni en el Grupo 20 ni en el Grupo 12.`;
          
          // Mostrar a qué sector pertenece si está disponible
          if (currentResult.rouletteSector) {
            resultMessage += `\nEl número pertenece al sector: ${currentResult.rouletteSector}`;
          }
        }
        
        // Mensaje de confirmación con información de victoria/derrota
        chatMessages.value.push({
          id: Date.now(),
          sender: 'bot',
          message: resultMessage,
          timestamp: new Date().toISOString(),
          numbersGenerated: [numberToAdd],
          isWinning: currentResult.isWinning
        });
        
        // Guardar el resultado en el historial de resultados
        lastWinningResult.value = {
          number: numberToAdd,
          isWinning: currentResult.isWinning,
          groupName: currentResult.groupName,
          matchingGroups: currentResult.matchingGroups,
          rouletteSector: currentResult.rouletteSector,
          timestamp: new Date()
        };
        
        // IMPORTANTE: SOLO DESPUÉS de verificar y mostrar el resultado, regeneramos los grupos
        // para predicciones futuras
        await refreshAllGroups();
        
        // Generar automáticamente nuevos grupos de predicción
        setTimeout(async () => {
          try {
            // Generar predicción estadística
            const statNumbers = await generateStatPredictions(6);
            chatMessages.value.push({
              id: Date.now() + 1,
              sender: 'bot',
              message: `Basado en estadísticas, te recomiendo estos números para la próxima jugada:`,
              timestamp: new Date().toISOString(),
              numbersGenerated: statNumbers
            });
          } catch (e) {
            console.error("Error generando predicciones estadísticas:", e);
          }
        }, 500);
      } else {
        chatMessages.value.push({
          id: Date.now() + 1,
          sender: 'bot',
          message: `Hubo un error al procesar el número ${numberToAdd}.`,
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error('Error processing number from voice:', error);
      chatMessages.value.push({
        id: Date.now() + 1,
        sender: 'bot',
        message: `Error al procesar el número ${numberToAdd}.`,
        timestamp: new Date().toISOString()
      });
    }
    return;
  }
  
  // Si está verificando victoria con un número específico
  if (isCheckingWin && (isJustOneNumber || message.includes('número'))) {
    let numberToCheck = null;
    
    // Extraer el número de la consulta si está presente
    if (isJustOneNumber) {
      numberToCheck = parseInt(message);
    } else {
      // Buscar un número en el mensaje
      const numberMatch = message.match(/\d+/);
      if (numberMatch) {
        numberToCheck = parseInt(numberMatch[0]);
      }
    }
    
    if (numberToCheck !== null) {
      // Verificar si el número está en los grupos generados y determinar si ganó
      const result = checkGroupsForNumber(numberToCheck);
      
      // Mostrar resultado de la apuesta
      chatMessages.value.push({
        id: Date.now() + 1,
        sender: 'bot',
        message: result.isWinning ? 
          getWinningMessage(numberToCheck, result) : 
          getLosingMessage(numberToCheck, result),
        timestamp: new Date().toISOString(),
        isWinning: result.isWinning,
        numbersGenerated: result.predictedNumbers
      });
      
      // Emitir evento de resultado de apuesta
      if (emitter) {
        emitter.emit('number-played', {
          number: numberToCheck,
          isWinning: result.isWinning
        });
      }
      
      return;
    }
  }
  
  // Procesar múltiples números o un mensaje que podría contener números
  if (containsMultipleNumbers || message.includes(',')) {
    try {
      const processed = await processNumbersInput(message);
      
      if (processed && processed.processedCount > 0) {
        // El último número es el primero de la lista (el más a la izquierda)
        const lastNumber = processed.lastPlayed;
        
        // Verificar si el último número estaba en nuestras predicciones anteriores
        let winResult = false;
        let winMessage = '';
        
        // Solo verificar si no es el primer conjunto de números que se ingresa
        if (recentNumbers.value.length > 1) {
          const result = checkGroupsForNumber(lastNumber);
          winResult = result.isWinning;
          
          winMessage = result.isWinning ? 
            ` ${getWinningMessage(lastNumber, result)}` : 
            ` El número ${lastNumber} no estaba en nuestras predicciones activas.`;
          
          // Emitir evento de resultado de la apuesta
          if (emitter) {
            emitter.emit('number-played', {
              number: lastNumber,
              isWinning: result.isWinning
            });
          }
        }
        
        // Mostrar mensaje de confirmación destacando el último número jugado
        chatMessages.value.push({
          id: Date.now(),
          sender: 'bot',
          message: `He procesado ${processed.processedCount} números correctamente. El último número jugado registrado es ${lastNumber}.${winMessage}`,
          timestamp: new Date().toISOString(),
          numbersGenerated: [lastNumber], // Mostrar solo el último número jugado para claridad
          isWinning: recentNumbers.value.length > 1 ? winResult : undefined
        });
        
        // Actualizar todos los grupos
        await refreshAllGroups();
        await fetchLastNumbers();
        
        // GENERAR AUTOMÁTICAMENTE NUEVAS PREDICCIONES Y MOSTRARLAS
        // Esperamos un momento para que se actualicen los grupos
        setTimeout(async () => {
          try {
            // Mostrar los grupos recomendados
            const activeGroup = 
              activeGroupSet.value === 'standard' ? numberGroups.value.group8 :
              activeGroupSet.value === 'statistical' ? Object.values(localStatGroups.value)[0] :
              Object.values(aiGroups.value)[0];
            
            chatMessages.value.push({
              id: Date.now() + 1,
              sender: 'bot',
              message: `Basado en el análisis de los números ingresados, te recomiendo estos para la próxima jugada:`,
              timestamp: new Date().toISOString(),
              numbersGenerated: activeGroup
            });
            
            // También mostrar otra predicción con retraso
            setTimeout(async () => {
              const puxa = await generatePuxaUltraPredictions();
              chatMessages.value.push({
                id: Date.now() + 2,
                sender: 'bot',
                message: `El método Puxa Ultra también recomienda:`,
                timestamp: new Date().toISOString(),
                numbersGenerated: puxa
              });
            }, 800);
          } catch (e) {
            console.error("Error generando predicciones automáticas:", e);
          }
        }, 500);
        
        // Emitir evento para que otros componentes se actualicen
        if (emitter) {
          emitter.emit('numbers-updated');
          // Emitir evento específico para el último número jugado
          emitter.emit('last-number-played', lastNumber);
        }
      } else {
        console.error("No se pudieron procesar números del mensaje:", message);
        chatMessages.value.push({
          id: Date.now() + 1,
          sender: 'bot',
          message: 'No pude identificar números válidos en tu mensaje. Asegúrate de ingresar números del 0 al 36 separados por comas.',
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error('Error processing multiple numbers:', error);
      chatMessages.value.push({
        id: Date.now() + 1,
        sender: 'bot',
        message: 'Hubo un error al procesar los números. Por favor, inténtalo de nuevo.',
        timestamp: new Date().toISOString()
      });
    }
  } 
  // Verificar si el mensaje contiene un único número
  else if (isJustOneNumber) {
    const number = parseInt(message);
    
    // Guardar el número en la base de datos
    try {
      // Mostrar información de diagnóstico en la consola
      console.log(`---------- VERIFICACIÓN DE NÚMERO ÚNICO: ${number} ----------`);
      console.log(`Grupos estándar antes de procesar:`);
      Object.entries(numberGroups.value).forEach(([name, nums]) => {
        if (nums && nums.length > 0) {
          const includesNumber = nums.includes(number);
          const sortedNumbers = [...nums].sort((a, b) => a - b);
          console.log(`${name}: [${sortedNumbers.join(', ')}] - ${includesNumber ? '✓ CONTIENE' : '✗ NO CONTIENE'} el número ${number}`);
        }
      });
      
      const processed = await processNumbersInput(message);
      if (processed && processed.processedCount > 0) {
        // Actualizar todos los grupos tras ingresar un nuevo número
        await fetchLastNumbers();
        await refreshAllGroups();
        
        // Emitir evento para que otros componentes se actualicen inmediatamente
        if (emitter) {
          emitter.emit('number-registered', {
            number
          });
          emitter.emit('numbers-updated');
        }
        
        // Verificar automáticamente si el número estaba en nuestras predicciones anteriores
        let resultMessage = "";
        let winResult = false;
        
        // Solo verificar si hay predicciones existentes
        if (recentNumbers.value.length > 1) {
          // Verificar si el número está en cualquiera de nuestros grupos de predicción
          const result = checkGroupsForNumber(number);
          winResult = result.isWinning;
          
          // Mensaje según resultado
          if (winResult) {
            resultMessage = getWinningMessage(number, result);
          } else {
            // Usar la nueva función para mensajes de derrota
            resultMessage = getLosingMessage(number, result);
          }
          
          // Emitir evento de resultado de la apuesta
          if (emitter) {
            emitter.emit('number-played', {
              number,
              isWinning: result.isWinning
            });
          }
        } else {
          // Si es el primer número, solo confirmar el registro
          resultMessage = `He registrado el número ${number}.`;
        }
        
        // Mensaje de resultado
        chatMessages.value.push({
          id: Date.now(),
          sender: 'bot',
          message: resultMessage,
          timestamp: new Date().toISOString(),
          numbersGenerated: [number],
          isWinning: recentNumbers.value.length > 1 ? winResult : undefined
        });
        
        // Generar automáticamente nuevos grupos de predicción para la próxima jugada
        await refreshAllGroups();
        
        // GENERAR AUTOMÁTICAMENTE NUEVAS PREDICCIONES Y MOSTRARLAS
        // Esperamos un momento para que se actualicen los grupos
        setTimeout(async () => {
          // 1. Generar predicción estadística
          try {
            const statNumbers = await generateStatPredictions(6);
            const statMsg = `Basado en estadísticas, te recomiendo estos números para la próxima jugada:`;
            
            chatMessages.value.push({
              id: Date.now() + 1,
              sender: 'bot',
              message: statMsg,
              timestamp: new Date().toISOString(),
              numbersGenerated: statNumbers
            });
          } catch (e) {
            console.error("Error generando predicciones estadísticas:", e);
          }
          
          // 2. Generar predicción Tía Lu
          try {
            const tiaLuNumbers = await generateTiaLuPredictions();
            const tiaLuMsg = `Con el método "Tía Lu", estos son los números recomendados:`;
            
            setTimeout(() => {
              chatMessages.value.push({
                id: Date.now() + 2,
                sender: 'bot',
                message: tiaLuMsg,
                timestamp: new Date().toISOString(),
                numbersGenerated: tiaLuNumbers
              });
            }, 600);
          } catch (e) {
            console.error("Error generando predicciones Tía Lu:", e);
          }
        }, 500);
        
        // Emitir evento para que otros componentes se actualicen
        if (emitter) {
          emitter.emit('numbers-updated');
          emitter.emit('number-registered', {
            number
          });
        }
      } else {
        chatMessages.value.push({
          id: Date.now() + 2,
          sender: 'bot',
          message: 'Hubo un error al procesar el número.',
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error('Error processing number:', error);
      chatMessages.value.push({
        id: Date.now() + 2,
        sender: 'bot',
        message: 'Hubo un error al procesar el número.',
        timestamp: new Date().toISOString()
      });
    }
  } else {
    console.log("Procesando como mensaje de texto normal");
    // Para mensajes que no son números, enviar al backend
    try {
      const response = await fetch(`${apiBaseUrl.value}/consulta`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          mensaje: message,
          historial: recentNumbers.value || []
        })
      });
      
      if (!response.ok) {
        throw new Error(`Error en la respuesta: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Agregar respuesta del bot
      chatMessages.value.push({
        id: Date.now() + 3,
        sender: 'bot',
        message: data.respuesta || 'Lo siento, no pude procesar tu consulta.',
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('Error al enviar mensaje:', error);
      
      // Mensaje de error
      chatMessages.value.push({
        id: Date.now() + 4,
        sender: 'bot',
        message: 'Lo siento, hubo un error al procesar tu mensaje. Inténtalo de nuevo.',
        timestamp: new Date().toISOString()
      });
    }
  }
};

// Verificar si un número está en los grupos de predicción
const checkGroupsForNumber = (number: number): GroupCheckResult => {
  // Inicializar resultado con valores por defecto
  const result: GroupCheckResult = {
    found: false,
    isWinning: false,
    groupName: '',
    predictedNumbers: [] as number[],
    matchingGroups: [] as string[],
    rouletteSector: ''
  };
  
  // Guardamos todos los números utilizados en predicciones activas 
  // para mostrarlos en caso de derrota
  let allPredictedNumbers: number[] = [];
  
  // ========== PASO 1: VERIFICAR EXPLÍCITAMENTE SI HAY DERROTA ==========
  console.log(`\n========== VERIFICACIÓN DE NÚMERO ${number} ==========`);
  
  // Asegurarnos de usar los grupos ACTUALES después de refreshAllGroups
  // Hacer una referencia local explícita para evitar problemas de sincronización
  const currentGroup20 = [...(numberGroups.value.group20 || [])];
  const currentGroup12 = [...(numberGroups.value.group12 || [])];
  
  // Comprobar si el número está en los grupos principales
  const isInGroup20 = currentGroup20.includes(number);
  const isInGroup12 = currentGroup12.includes(number);
  
  // Mostrar el contenido de los grupos principales para debugging
  console.log(`Grupo 20: [${currentGroup20.sort((a, b) => a - b).join(', ')}]`);
  console.log(`¿Número ${number} en Grupo 20?: ${isInGroup20 ? 'SÍ' : 'NO'}`);
  
  console.log(`Grupo 12: [${currentGroup12.sort((a, b) => a - b).join(', ')}]`);
  console.log(`¿Número ${number} en Grupo 12?: ${isInGroup12 ? 'SÍ' : 'NO'}`);
  
  // REGLA PRINCIPAL: Si no está en ninguno de los dos grupos principales, es DERROTA
  if (!isInGroup20 && !isInGroup12) {
    // DERROTA CONFIRMADA - No está en ninguno de los grupos principales
    result.isWinning = false;
    result.found = false;
    
    console.log(`❌ DERROTA CONFIRMADA: Número ${number} NO está ni en grupo20 NI en grupo12.`);
    
    // Agregamos los números de los grupos estándar para referencia
    Object.entries(numberGroups.value).forEach(([groupName, numbers]) => {
      if (numbers && numbers.length > 0) {
        allPredictedNumbers = [...allPredictedNumbers, ...numbers];
        console.log(`Grupo ${groupName}: [${numbers.sort((a, b) => a - b).join(', ')}]`);
      }
    });
    
    // Eliminar duplicados y ordenar para referencia
    result.predictedNumbers = [...new Set(allPredictedNumbers)].sort((a, b) => a - b);
    
    // Incrementar contador de derrotas
    loseCount.value++;
  } 
  // ========== PASO 2: SI NO HAY DERROTA, VERIFICAR VICTORIA ==========
  else {
    // Si llegamos aquí, es porque NO hubo derrota (está en al menos uno de los grupos principales)
    // Por lo tanto, ya sabemos que es VICTORIA
    result.isWinning = true;
    result.found = true;
    
    console.log(`✅ VICTORIA CONFIRMADA: Número ${number} está en al menos uno de los grupos principales.`);
    
    // Registramos en qué grupos se encuentra para estadísticas y detalles
    if (isInGroup20) {
      result.matchingGroups.push(`estándar: ${getGroupLabel('group20')}`);
      groupWinStats.value['group20']++;
      console.log(`✓ Número ${number} encontrado en grupo20`);
    }
    
    if (isInGroup12) {
      result.matchingGroups.push(`estándar: ${getGroupLabel('group12')}`);
      groupWinStats.value['group12']++;
      console.log(`✓ Número ${number} encontrado en grupo12`);
    }
    
    // Determinar el mensaje según dónde se encontró
    if (isInGroup20 && isInGroup12) {
      // Bonus por estar en ambos grupos
      result.groupName = 'group20_and_group12';
      result.predictedNumbers = [...new Set([...currentGroup20, ...currentGroup12])];
      console.log(`💰 Número ${number} encontrado en AMBOS grupos (grupo20 y grupo12). ¡VICTORIA DOBLE!`);
    } else if (isInGroup20) {
      result.groupName = 'group20';
      result.predictedNumbers = [...currentGroup20];
      console.log(`✓ Número ${number} encontrado en grupo20. VICTORIA.`);
    } else {
      result.groupName = 'group12';
      result.predictedNumbers = [...currentGroup12];
      console.log(`✓ Número ${number} encontrado en grupo12. VICTORIA.`);
    }
    
    // Incrementar contador de victorias
    winCount.value++;
  }
  
  // ========== PASO 3: VERIFICAR GRUPOS ADICIONALES PARA ESTADÍSTICAS ==========
  
  // Verificar resto de grupos estándar
  Object.entries(numberGroups.value).forEach(([groupName, numbers]) => {
    if (groupName !== 'group20' && groupName !== 'group12' && numbers && numbers.includes(number)) {
      result.matchingGroups.push(`estándar: ${getGroupLabel(groupName)}`);
      // Incrementar contador específico
      if (groupWinStats.value[groupName] !== undefined) {
        groupWinStats.value[groupName]++;
      }
    }
  });

  // Verificar grupos estadísticos locales
  Object.entries(localStatGroups.value).forEach(([groupName, numbers]) => {
    if (numbers && numbers.includes(number)) {
      result.matchingGroups.push(`estadístico: ${getLocalStatGroupLabel(groupName)}`);
      // Incrementar contador específico
      if (groupWinStats.value[groupName] !== undefined) {
        groupWinStats.value[groupName]++;
      }
    }
  });

  // Verificar grupos IA
  Object.entries(aiGroups.value).forEach(([groupName, numbers]) => {
    if (numbers && numbers.includes(number)) {
      result.matchingGroups.push(`IA: ${getAIGroupLabel(groupName)}`);
      // Incrementar contador específico
      if (groupWinStats.value[groupName] !== undefined) {
        groupWinStats.value[groupName]++;
      }
    }
  });
  
  // Verificar en qué sector de la ruleta está el número
  try {
    // Verificar en qué sector conocido está el número
    let currentSector = '';
    
    if (ROULETTE_WHEEL_SECTORS.voisinsDeZero.includes(number)) {
      result.rouletteSector = 'Vecinos del Cero';
      groupWinStats.value['voisinsDeZero']++;
      currentSector = 'voisinsDeZero';
    } else if (ROULETTE_WHEEL_SECTORS.tiers.includes(number)) {
      result.rouletteSector = 'Tercios del Cilindro';
      groupWinStats.value['tiers']++;
      currentSector = 'tiers';
    } else if (ROULETTE_WHEEL_SECTORS.orphelinsPlein.includes(number)) {
      result.rouletteSector = 'Huérfanos';
      groupWinStats.value['orphelins']++;
      currentSector = 'orphelins';
    } else if (ROULETTE_WHEEL_SECTORS.jeuZero.includes(number)) {
      result.rouletteSector = 'Juego del Cero';
      groupWinStats.value['jeuZero']++;
      currentSector = 'jeuZero';
    } else if (ROULETTE_WHEEL_SECTORS.redSector.includes(number)) {
      result.rouletteSector = 'Sector Rojo';
      groupWinStats.value['redSector']++;
      currentSector = 'redSector';
    } else if (ROULETTE_WHEEL_SECTORS.blackSector.includes(number)) {
      result.rouletteSector = 'Sector Negro';
      groupWinStats.value['blackSector']++;
      currentSector = 'blackSector';
    }
    
    // Si identificamos un sector, añadirlo a los grupos coincidentes y actualizar contadores
    if (result.rouletteSector && currentSector) {
      result.matchingGroups.push(`Sector: ${result.rouletteSector}`);
      
      // Actualizar historial y contadores de sectores
      sectorCounts.value[currentSector]++;
      sectorHistory.value.push({sector: currentSector, number: number});
      
      // Mantener solo los últimos 20 sectores en el historial
      if (sectorHistory.value.length > 20) {
        sectorHistory.value.shift();
      }
    }
  } catch (error) {
    console.error('Error verificando sectores de ruleta:', error);
  }
  
  console.log(`RESULTADO FINAL para número ${number}: ${result.isWinning ? 'VICTORIA' : 'DERROTA'}`);
  console.log(`===========================================\n`);
  
  // Detalles específicos para referencia en la UI
  const group20Details = {
    group20: isInGroup20,
    group12: isInGroup12
  };
  
  // Guardar el resultado en el historial con detalles específicos
  lastWinningResult.value = {
    number,
    isWinning: result.isWinning,
    groupName: result.groupName,
    matchingGroups: result.matchingGroups,
    rouletteSector: result.rouletteSector,
    details: group20Details,
    timestamp: new Date()
  };
  
  return result;
};

// Obtener los números activos en el conjunto de grupos actual
const getActiveGroupNumbers = (): number[] => {
  let allNumbers: number[] = [];
  
  if (activeGroupSet.value === 'standard') {
    Object.values(numberGroups.value).forEach(group => {
      allNumbers = [...allNumbers, ...group];
    });
  } else if (activeGroupSet.value === 'statistical') {
    Object.values(localStatGroups.value).forEach(group => {
      allNumbers = [...allNumbers, ...group];
    });
  } else if (activeGroupSet.value === 'ai') {
    Object.values(aiGroups.value).forEach(group => {
      allNumbers = [...allNumbers, ...group];
    });
  }
  
  // Eliminar duplicados y ordenar
  return [...new Set(allNumbers)].sort((a, b) => a - b);
};

// Generar predicción aleatoria
const generateRandomPrediction = () => {
  const numbers = generateRandomNumbers(5).sort((a, b) => a - b);
  chatMessages.value.push({
    id: Date.now(),
    sender: 'bot',
    message: 'He generado estos números aleatorios para ti:',
    timestamp: new Date().toISOString(),
    numbersGenerated: numbers
  });
};

// Generar predicción basada en estadísticas
const generateStatPrediction = async () => {
  try {
    const numbers = (await generateStatPredictions(5)).sort((a, b) => a - b);
    chatMessages.value.push({
      id: Date.now(),
      sender: 'bot',
      message: 'Basado en las estadísticas recientes, estos son los números más probables:',
      timestamp: new Date().toISOString(),
      numbersGenerated: numbers
    });
  } catch (error) {
    console.error('Error generating prediction:', error);
    chatMessages.value.push({
      id: Date.now(),
      sender: 'bot',
      message: 'No pude generar una predicción estadística en este momento.',
      timestamp: new Date().toISOString()
    });
  }
};

// Generar predicción "Tía Lu"
const generateTiaLuPrediction = async () => {
  try {
    const numbers = (await generateTiaLuPredictions()).sort((a, b) => a - b);
    chatMessages.value.push({
      id: Date.now(),
      sender: 'bot',
      message: 'Según el método "Tía Lu", estos son los números recomendados:',
      timestamp: new Date().toISOString(),
      numbersGenerated: numbers
    });
  } catch (error) {
    console.error('Error generating prediction:', error);
    chatMessages.value.push({
      id: Date.now(),
      sender: 'bot',
      message: 'No pude generar una predicción "Tía Lu" en este momento.',
      timestamp: new Date().toISOString()
    });
  }
};

// Generar predicción "Puxa Ultra"
const generatePuxaUltraPrediction = async () => {
  try {
    const numbers = (await generatePuxaUltraPredictions()).sort((a, b) => a - b);
    chatMessages.value.push({
      id: Date.now(),
      sender: 'bot',
      message: 'Aplicando el método "Puxa Ultra", estos son los números recomendados:',
      timestamp: new Date().toISOString(),
      numbersGenerated: numbers
    });
  } catch (error) {
    console.error('Error generating prediction:', error);
    chatMessages.value.push({
      id: Date.now(),
      sender: 'bot',
      message: 'No pude generar una predicción "Puxa Ultra" en este momento.',
      timestamp: new Date().toISOString()
    });
  }
};

// Obtener etiqueta para el grupo
const getGroupLabel = (groupName: string) => {
  switch (groupName) {
    case 'group20': return 'Grupo 20 números';
    case 'group12': return 'Grupo 12 números';
    case 'group8': return 'Grupo 8 números';
    case 'group6': return 'Grupo 6 números';
    case 'group4': return 'Grupo 4 números';
    default: return groupName;
  }
};

// Obtener etiqueta para grupo estadístico local
const getLocalStatGroupLabel = (groupName: string) => {
  switch (groupName) {
    case 'groupTerminals': return 'Terminales frecuentes';
    case 'groupParity': return 'Tendencia par/impar';
    case 'groupColumns': return 'Columna frecuente';
    case 'groupDozens': return 'Docena frecuente';
    case 'groupRecent': return 'Números recientes';
    default: return groupName;
  }
};

// Obtener etiqueta para grupo IA
const getAIGroupLabel = (groupName: string) => {
  switch (groupName) {
    case 'groupCycles': return 'Ciclos avanzados';
    case 'groupNeighbors': return 'Vecinos físicos';
    case 'groupSection': return 'Sector caliente';
    case 'groupAlternate': return 'Patrón de alternancia';
    case 'groupRecentAI': return 'IA avanzada';
    case 'groupSectors': return 'Sectores de ruleta';
    case 'groupVecinos': return 'Vecinos del último número';
    default: return groupName;
  }
};

// Calcular porcentaje de eficacia
const calculateEfficiency = computed(() => {
  const total = winCount.value + loseCount.value;
  if (total === 0) return 0;
  return Math.round((winCount.value / total) * 100);
});

// Obtener color según la eficacia
const getEfficiencyColor = computed(() => {
  const efficiency = calculateEfficiency.value;
  if (efficiency >= 70) return 'text-green-600';
  if (efficiency >= 50) return 'text-amber-600';
  return 'text-red-600';
});

// Formatear hora
const formatTime = (timestamp: string) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString();
};

// Verificar último número ingresado
const checkLastNumberResult = () => {
  if (!recentNumbers.value.length) {
    chatMessages.value.push({
      id: Date.now(),
      sender: 'bot',
      message: 'No hay números recientes para verificar.',
      timestamp: new Date().toISOString()
    });
    return;
  }
  
  // El último número jugado es el primero en el array (el más reciente)
  const lastNumber = recentNumbers.value[0];
  
  // Mostrar información de diagnóstico en la consola
  console.log(`---------- VERIFICACIÓN DEL NÚMERO ${lastNumber} ----------`);
  console.log(`Grupos estándar actuales:`);
  Object.entries(numberGroups.value).forEach(([name, numbers]) => {
    if (numbers && numbers.length > 0) {
      const includesNumber = numbers.includes(lastNumber);
      const sortedNumbers = [...numbers].sort((a, b) => a - b);
      console.log(`${name}: [${sortedNumbers.join(', ')}] - ${includesNumber ? '✓ CONTIENE' : '✗ NO CONTIENE'} el número ${lastNumber}`);
    }
  });
  
  // Ejecutar la verificación
  const result = checkGroupsForNumber(lastNumber);
  
  // Verificar si hay sectores calientes y agregar recomendación
  const hotSectorRecommendation = getHotSectorRecommendation();
  let sectorRecommendationMsg = '';
  let recommendedSectorNumbers: number[] = [];
  
  if (hotSectorRecommendation) {
    // Ordenar los números del sector recomendado
    recommendedSectorNumbers = [...hotSectorRecommendation.numbers].sort((a, b) => a - b);
    const numbersStr = recommendedSectorNumbers.slice(0, 8).join(', '); // Mostrar máximo 8 números
    
    sectorRecommendationMsg = `\n\n📊 Recomendación: El sector "${hotSectorRecommendation.name}" está repitiendo mucho (${hotSectorRecommendation.count} veces).\nNúmeros recomendados de este sector: ${numbersStr}`;
  }
  
  // Construir mensaje según resultado
  let baseMessage = '';
  if (result.isWinning) {
    baseMessage = getWinningMessage(lastNumber, result);
  } else {
    // Usar la nueva función para mensajes de derrota
    baseMessage = getLosingMessage(lastNumber, result);
  }
  
  chatMessages.value.push({
    id: Date.now(),
    sender: 'bot',
    message: baseMessage + sectorRecommendationMsg,
    timestamp: new Date().toISOString(),
    isWinning: result.isWinning,
    numbersGenerated: result.isWinning ? result.predictedNumbers : 
                   recommendedSectorNumbers.length > 0 ? recommendedSectorNumbers : result.predictedNumbers
  });
  
  // Emitir evento de resultado de apuesta
  if (emitter) {
    emitter.emit('number-played', {
      number: lastNumber,
      isWinning: result.isWinning
    });
  }
  
  // Generar nuevas predicciones después de verificar el resultado
  setTimeout(async () => {
    // Actualizar todos los grupos con el último número
    await refreshAllGroups();
    
    // Generar diferentes tipos de predicciones
    try {
      // Método estadístico
      const statNumbers = (await generateStatPredictions(5)).sort((a, b) => a - b);
      
      chatMessages.value.push({
        id: Date.now() + 1,
        sender: 'bot',
        message: `Nuevas predicciones para el próximo número:`,
        timestamp: new Date().toISOString(),
        numbersGenerated: statNumbers
      });
      
      // Método Tía Lu
      setTimeout(async () => {
        const tialuNumbers = (await generateTiaLuPredictions()).sort((a, b) => a - b);
        chatMessages.value.push({
          id: Date.now() + 2,
          sender: 'bot',
          message: `También podrías considerar estos números del método Tía Lu:`,
          timestamp: new Date().toISOString(),
          numbersGenerated: tialuNumbers
        });
      }, 700);
    } catch (e) {
      console.error("Error generando predicciones:", e);
    }
  }, 1000);
};

// Función para obtener recomendación de sector caliente
const getHotSectorRecommendation = () => {
  // Analizar sectores recientes para encontrar tendencias
  const recentSectorCounts: Record<string, number> = {};
  
  // Contar ocurrencias de cada sector en los últimos números
  sectorHistory.value.forEach(item => {
    if (!recentSectorCounts[item.sector]) {
      recentSectorCounts[item.sector] = 0;
    }
    recentSectorCounts[item.sector]++;
  });
  
  // Encontrar el sector más frecuente
  let hotSector = '';
  let maxCount = 0;
  
  for (const [sector, count] of Object.entries(recentSectorCounts)) {
    if (count > maxCount) {
      maxCount = count;
      hotSector = sector;
    }
  }
  
  // Solo recomendar si supera el umbral
  if (maxCount >= SECTOR_THRESHOLD) {
    const sectorNames: Record<string, string> = {
      'voisinsDeZero': 'Vecinos del Cero',
      'tiers': 'Tercios del Cilindro',
      'orphelins': 'Huérfanos',
      'jeuZero': 'Juego del Cero',
      'redSector': 'Sector Rojo',
      'blackSector': 'Sector Negro'
    };
    
    return {
      id: hotSector,
      name: sectorNames[hotSector] || hotSector,
      count: maxCount,
      numbers: ROULETTE_WHEEL_SECTORS[hotSector as keyof typeof ROULETTE_WHEEL_SECTORS] || []
    };
  }
  
  return null;
};

// Función para generar predicciones automáticas
const generateAutomaticPredictions = async (lastNumber: number) => {
  try {
    // Mostrar el número registrado
    chatMessages.value.push({
      id: Date.now(),
      sender: 'bot',
      message: `Número ${lastNumber} registrado desde el historial. Generando predicciones...`,
      timestamp: new Date().toISOString(),
      numbersGenerated: [lastNumber]
    });
    
    // Esperar un momento antes de mostrar las predicciones
    setTimeout(async () => {
      try {
        // Método estadístico
        const statNumbers = (await generateStatPredictions(6)).sort((a, b) => a - b);
        chatMessages.value.push({
          id: Date.now() + 1,
          sender: 'bot',
          message: `Predicciones estadísticas para el próximo número:`,
          timestamp: new Date().toISOString(),
          numbersGenerated: statNumbers
        });
        
        // Método Tía Lu con un pequeño retraso
        setTimeout(async () => {
          const tiaLuNumbers = (await generateTiaLuPredictions()).sort((a, b) => a - b);
          chatMessages.value.push({
            id: Date.now() + 2,
            sender: 'bot',
            message: `También puedes considerar estos números del método Tía Lu:`,
            timestamp: new Date().toISOString(),
            numbersGenerated: tiaLuNumbers
          });
        }, 600);
      } catch (e) {
        console.error("Error generando predicciones automáticas:", e);
      }
    }, 800);
  } catch (error) {
    console.error('Error al generar predicciones automáticas:', error);
  }
};

// Reiniciar contadores
const resetCounters = () => {
  winCount.value = 0;
  loseCount.value = 0;
  // También reiniciar contadores de sectores
  sectorCounts.value = {
    'voisinsDeZero': 0,
    'tiers': 0,
    'orphelins': 0,
    'jeuZero': 0,
    'redSector': 0,
    'blackSector': 0
  };
  sectorHistory.value = [];
};

// Variables para mostrar estadísticas detalladas
const showStatsDetails = ref(false);

// Reiniciar estadísticas de grupos
const resetGroupStats = () => {
  groupWinStats.value = {
    group20: 0,
    group12: 0,
    group8: 0,
    group6: 0,
    group4: 0,
    groupTerminals: 0,
    groupParity: 0,
    groupColumns: 0,
    groupDozens: 0,
    groupRecent: 0,
    groupCycles: 0,
    groupNeighbors: 0,
    groupSection: 0,
    groupAlternate: 0,
    groupRecentAI: 0,
    groupSectors: 0,
    groupVecinos: 0,
    voisinsDeZero: 0,
    tiers: 0,
    orphelins: 0,
    jeuZero: 0,
    redSector: 0,
    blackSector: 0
  };
};

// Variables para mostrar estadísticas detalladas
const statsViewMode = ref('details');

// Variables para el gráfico
const chartCategory = ref('standard');

// Obtener datos para el gráfico según la categoría seleccionada
const getChartData = computed(() => {
  let groupKeys: string[] = [];
  let getLabel: (key: string) => string = key => key;
  
  // Determinar qué grupos y etiquetas mostrar según la categoría
  if (chartCategory.value === 'standard') {
    groupKeys = ['group20', 'group12', 'group8', 'group6', 'group4'];
    getLabel = getGroupLabel;
  } else if (chartCategory.value === 'statistical') {
    groupKeys = ['groupTerminals', 'groupParity', 'groupColumns', 'groupDozens', 'groupRecent'];
    getLabel = getLocalStatGroupLabel;
  } else if (chartCategory.value === 'ai') {
    groupKeys = ['groupCycles', 'groupNeighbors', 'groupSection', 'groupAlternate', 'groupRecentAI', 'groupSectors', 'groupVecinos'];
    getLabel = getAIGroupLabel;
  } else if (chartCategory.value === 'sectors') {
    groupKeys = ['voisinsDeZero', 'tiers', 'orphelins', 'jeuZero'];
    getLabel = (key) => {
      const sectorNames: Record<string, string> = {
        'voisinsDeZero': 'Vecinos del Cero',
        'tiers': 'Tercios del Cilindro',
        'orphelins': 'Huérfanos',
        'jeuZero': 'Juego del Cero'
      };
      return sectorNames[key] || key;
    };
  }
  
  // Extraer valores y etiquetas
  const values = groupKeys.map(key => groupWinStats.value[key] || 0);
  const labels = groupKeys.map(getLabel);
  
  return { labels, values };
});

// Añadir la función para limpiar los últimos mensajes
const clearLastMessages = (count: number) => {
  if (chatMessages.value.length <= count) {
    return; // No hacer nada si no hay suficientes mensajes
  }
  
  // Eliminar los últimos 'count' mensajes
  chatMessages.value = chatMessages.value.slice(0, -count);
  
  // Añadir un mensaje de sistema para indicar que se limpiaron mensajes
  chatMessages.value.push({
    id: Date.now(),
    sender: 'bot',
    message: `Se han eliminado los últimos ${count} mensajes para mantener el chat más limpio.`,
    timestamp: new Date().toISOString()
  });
};

// Métodos computados para estados de voz
const voiceStatusClass = computed(() => {
  switch (voiceStatus.value) {
    case 'listening': return 'bg-blue-500';
    case 'processing': return 'bg-yellow-500';
    case 'error': return 'bg-red-500';
    case 'success': return 'bg-green-500';
    default: return 'bg-gray-500';
  }
});

const voiceStatusText = computed(() => {
  switch (voiceStatus.value) {
    case 'listening': return 'Escuchando...';
    case 'processing': return 'Procesando...';
    case 'error': return 'Error de reconocimiento';
    case 'success': return 'Reconocimiento exitoso';
    default: return 'Inactivo';
  }
});

const voiceStatusTextClass = computed(() => {
  switch (voiceStatus.value) {
    case 'listening': return 'text-blue-500';
    case 'processing': return 'text-yellow-500';
    case 'error': return 'text-red-500';
    case 'success': return 'text-green-500';
    default: return 'text-gray-500';
  }
});

const getVoiceButtonClass = computed(() => {
  if (isListening.value) {
    return 'bg-red-800'; // Escuchando activamente
  } else if (voiceError.value && voiceError.value.includes('Error de red')) {
    return 'bg-yellow-600'; // Error de red - reintento
  } else if (voiceError.value) {
    return 'bg-orange-600'; // Otro tipo de error
  } else if (voiceStatus.value === 'success') {
    return 'bg-green-600'; // Último reconocimiento exitoso
  } else {
    return 'bg-red-600'; // Estado normal
  }
});

const getVoiceButtonTitle = computed(() => {
  if (isListening.value) {
    return 'Escuchando... Haz clic para detener';
  } else if (voiceError.value && voiceError.value.includes('Error de red')) {
    return 'Error de red. Haz clic para reintentar';
  } else if (voiceError.value) {
    return `Error: ${voiceError.value}. Haz clic para reintentar`;
  } else {
    return 'Haz clic para hablar';
  }
});

// Función para mostrar ayuda sobre reconocimiento de voz
const showVoiceHelp = () => {
  chatMessages.value.push({
    id: Date.now(),
    sender: 'bot',
    message: `Problemas con el reconocimiento de voz:
    
1. Asegúrate de tener una conexión estable a internet
2. Verifica que tu navegador tiene permiso para usar el micrófono
3. Habla claramente y cerca del micrófono
4. Si sigues teniendo problemas, puedes:
   - Usar el teclado para ingresar números directamente
   - Refrescar la página
   - Probar en otro navegador (Chrome suele funcionar mejor)
   - Verificar que tu micrófono funciona en otras aplicaciones`,
    timestamp: new Date().toISOString()
  });
};

// Función para cambiar a entrada manual
const switchToManualInput = () => {
  manualInputPreferred.value = true;
  voiceError.value = '';
  chatMessages.value.push({
    id: Date.now(),
    sender: 'bot',
    message: 'Has cambiado a entrada manual. Puedes ingresar números directamente usando el teclado.',
    timestamp: new Date().toISOString()
  });
};

// Función para usar Google Speech API en lugar de Web Speech API
const useGoogleSpeechRecognition = async () => {
  try {
    // Verificar si tenemos el grabador de audio inicializado
    if (!audioRecorder.value) {
      audioRecorder.value = new AudioRecorder();
    }
    
    // Actualizar estado
    voiceStatus.value = 'listening';
    isListening.value = true;
    voiceError.value = '';
    
    // Iniciar grabación
    await audioRecorder.value.startRecording();
    console.log('Grabación iniciada con Google Speech API');
    
    // Esperamos a que el usuario termine de hablar
    setTimeout(async () => {
      if (isListening.value) {
        try {
          // Actualizar estado
          voiceStatus.value = 'processing';
          isListening.value = false;
          
          // Detener grabación y obtener audio
          const audioBlob = await audioRecorder.value!.stopRecording();
          
          // Enviar a backend para reconocimiento
          const transcript = await recognizeSpeech(audioBlob);
          
          if (transcript) {
            // Actualizar campo de entrada
            userInput.value = transcript;
            voiceStatus.value = 'success';
            
            // Pequeña pausa para actualizar UI
            setTimeout(() => {
              // Procesar el mensaje
              sendMessage();
            }, 100);
          } else {
            voiceError.value = 'No se detectó ningún texto. Intenta hablar más claro.';
            voiceStatus.value = 'error';
          }
        } catch (error) {
          console.error('Error en el reconocimiento con Google Speech:', error);
          voiceError.value = `Error en el reconocimiento: ${error.message || 'Error desconocido'}`;
          voiceStatus.value = 'error';
        }
      }
    }, 3000); // 3 segundos de grabación
    
    return true;
  } catch (error) {
    console.error('Error al iniciar Google Speech Recognition:', error);
    voiceError.value = `Error al iniciar reconocimiento: ${error.message || 'Error desconocido'}`;
    voiceStatus.value = 'error';
    isListening.value = false;
    return false;
  }
};

// Manejar un número reconocido
const handleRecognizedNumber = async (numberToAdd: number) => {
  // Validar que el número está en el rango válido de la ruleta (0-36)
  if (isNaN(numberToAdd) || numberToAdd < 0 || numberToAdd > 36) {
    chatMessages.value.push({
      id: Date.now(),
      sender: 'bot',
      message: `El número reconocido (${numberToAdd}) no es válido para la ruleta. Por favor, usa números entre 0 y 36.`,
      timestamp: new Date().toISOString()
    });
    return;
  }
  
  // PASO 1: Procesar el número (guardarlo en la base de datos)
  console.log(`\n========== PROCESANDO NUEVO NÚMERO: ${numberToAdd} ==========`);
  try {
    const processed = await processNumbersInput(numberToAdd.toString());
    if (!processed || processed.processedCount === 0) {
      console.error(`Error al procesar el número ${numberToAdd}`);
      return;
    }
    
    // PASO 2: Actualizar la lista de números recientes
    console.log(`Número ${numberToAdd} procesado. Actualizando lista de números...`);
    await fetchLastNumbers();
    
    // PASO 3: Regenerar completamente los grupos de predicción
    console.log(`Lista de números actualizada. Regenerando grupos de predicción...`);
    const groupsUpdated = await refreshAllGroups();
    if (!groupsUpdated) {
      console.error('Error al actualizar los grupos de predicción');
      // Continuar de todos modos, podríamos tener grupos anteriores válidos
    }
    
    // PASO 4: Verificar si el número está en nuestras predicciones (grupos actuales)
    console.log(`Grupos regenerados. Verificando si ${numberToAdd} es victoria o derrota...`);
    const result = checkGroupsForNumber(numberToAdd);
    
    // Emitir eventos para que otros componentes se actualicen
    if (emitter) {
      emitter.emit('number-registered', { number: numberToAdd });
      emitter.emit('numbers-updated');
      emitter.emit('last-number-played', numberToAdd);
      
      // Emitir el evento de resultado de la apuesta para actualizar contadores
      emitter.emit('number-played', {
        number: numberToAdd,
        isWinning: result.isWinning
      });
    }
    
    // Preparar mensaje según el resultado
    let resultMessage = "";
    
    if (result.isWinning) {
      // Mensaje de victoria detallado
      resultMessage = getWinningMessage(numberToAdd, result);
    } else {
      // Mensaje de derrota detallado
      resultMessage = getLosingMessage(numberToAdd, result);
    }
    
    // Mensaje de confirmación con información de victoria/derrota
    chatMessages.value.push({
      id: Date.now(),
      sender: 'bot',
      message: resultMessage,
      timestamp: new Date().toISOString(),
      numbersGenerated: [numberToAdd],
      isWinning: result.isWinning
    });
    
    // Guardar el resultado en el historial
    if (process.client) {
      const historyEntry = {
        number: numberToAdd,
        result: result.isWinning ? 'victoria' : 'derrota',
        timestamp: new Date().toISOString()
      };
      
      // Obtener historial existente o crear uno nuevo
      const existingHistory = localStorage.getItem('roulette_results_history');
      const history = existingHistory ? JSON.parse(existingHistory) : [];
      
      // Añadir la nueva entrada y limitar a 50 resultados
      history.unshift(historyEntry);
      if (history.length > 50) history.length = 50;
      
      // Guardar historial actualizado
      localStorage.setItem('roulette_results_history', JSON.stringify(history));
    }
    
    // Reiniciar reconocimiento de voz si estaba activado
    if (isListening.value) {
      toggleVoiceRecognition();
    }
  } catch (error) {
    console.error('Error al procesar número reconocido:', error);
    chatMessages.value.push({
      id: Date.now(),
      sender: 'bot',
      message: `Ha ocurrido un error al procesar el número. Por favor, intenta de nuevo.`,
      timestamp: new Date().toISOString()
    });
  }
};
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style> 