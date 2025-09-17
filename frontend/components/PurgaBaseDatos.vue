<template>
  <div class="bg-white p-4 rounded-lg shadow-md">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold text-gray-800">Estado de la Base de Datos</h2>
      <div class="flex gap-2">
        <button 
          @click="actualizarEstado"
          class="bg-blue-600 text-white px-3 py-1 rounded text-sm"
          :disabled="cargandoEstado"
        >
          <span v-if="cargandoEstado" class="animate-spin">⟳</span>
          <span v-else>🔄</span>
          Actualizar
        </button>
      </div>
    </div>
    
    <!-- Estado actual -->
    <div v-if="estadoFormateado" class="mb-6">
      <div class="flex items-center mb-3">
        <span class="text-lg font-semibold mr-2">Estado:</span>
        <span :class="['font-bold', estadoFormateado.color]">
          {{ estadoFormateado.estadoGeneral }}
        </span>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <!-- Resumen de registros -->
        <div class="bg-gray-50 p-3 rounded">
          <h3 class="font-medium text-gray-700 mb-2">Total de Registros</h3>
          <div class="space-y-1 text-sm">
            <div class="flex justify-between">
              <span>Números individuales:</span>
              <span class="font-medium">{{ estadoFormateado.totalRegistros.individual.toLocaleString() }}</span>
            </div>
            <div class="flex justify-between">
              <span>Historial:</span>
              <span class="font-medium">{{ estadoFormateado.totalRegistros.history.toLocaleString() }}</span>
            </div>
            <div class="flex justify-between border-t pt-1 font-semibold">
              <span>Total:</span>
              <span>{{ estadoFormateado.totalRegistros.total.toLocaleString() }}</span>
            </div>
          </div>
        </div>
        
        <!-- Actividad reciente -->
        <div class="bg-gray-50 p-3 rounded">
          <h3 class="font-medium text-gray-700 mb-2">Actividad Reciente</h3>
          <div class="space-y-1 text-sm">
            <div class="flex justify-between">
              <span>Últimas 24h:</span>
              <span class="font-medium">
                {{ estadoFormateado.registrosRecientes.ultimas24h }} 
                ({{ estadoFormateado.registrosRecientes.porcentaje24h }}%)
              </span>
            </div>
            <div class="flex justify-between">
              <span>Últimas 48h:</span>
              <span class="font-medium">
                {{ estadoFormateado.registrosRecientes.ultimas48h }} 
                ({{ estadoFormateado.registrosRecientes.porcentaje48h }}%)
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Información de fechas -->
      <div class="bg-blue-50 p-3 rounded mb-4">
        <h3 class="font-medium text-blue-700 mb-2">Información Temporal</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div>
            <span class="text-blue-600 font-medium">Registro más antiguo:</span>
            <p class="text-gray-700">{{ estadoFormateado.antiguedad.fechaMasAntigua }}</p>
            <p class="text-xs text-gray-500">
              ({{ estadoFormateado.antiguedad.horas }} horas atrás)
            </p>
          </div>
          <div>
            <span class="text-blue-600 font-medium">Registro más reciente:</span>
            <p class="text-gray-700">{{ estadoFormateado.antiguedad.fechaMasReciente }}</p>
          </div>
        </div>
      </div>
      
      <!-- Mensaje descriptivo -->
      <div class="bg-gray-100 p-3 rounded">
        <p class="text-sm text-gray-700">{{ estadoFormateado.mensaje }}</p>
      </div>
    </div>
    
    <!-- Sección de purga -->
    <div class="border-t pt-4">
      <h3 class="text-lg font-semibold mb-4 text-gray-700">Control de Purga</h3>
      
      <!-- Alertas -->
      <div v-if="estadoFormateado?.necesitaPurga" class="bg-orange-100 border border-orange-300 p-3 rounded mb-4">
        <div class="flex items-center">
          <span class="text-orange-600 text-xl mr-2">⚠️</span>
          <div>
            <p class="font-medium text-orange-800">La base de datos necesita purga</p>
            <p class="text-sm text-orange-700">
              Los registros más antiguos tienen más de 48 horas. Se recomienda ejecutar una purga.
            </p>
          </div>
        </div>
      </div>
      
      <!-- Configuración de purga -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Mantener últimas (horas)
          </label>
          <input
            v-model.number="configuracionPurga.mantenerHoras"
            type="number"
            min="1"
            max="168"
            class="w-full border rounded px-3 py-2 text-sm"
          />
          <p class="text-xs text-gray-500 mt-1">
            Eliminar registros anteriores a estas horas (1-168)
          </p>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Mantener mínimo (registros)
          </label>
          <input
            v-model.number="configuracionPurga.mantenerMinimo"
            type="number"
            min="10"
            max="1000"
            class="w-full border rounded px-3 py-2 text-sm"
          />
          <p class="text-xs text-gray-500 mt-1">
            Siempre mantener estos registros más recientes (10-1000)
          </p>
        </div>
      </div>
      
      <!-- Botones de acción -->
      <div class="flex gap-3">
        <button 
          @click="ejecutarPurga"
          class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded flex items-center"
          :disabled="ejecutandoPurga"
        >
          <span v-if="ejecutandoPurga" class="animate-spin mr-2">⟳</span>
          <span v-else class="mr-2">🗑️</span>
          {{ ejecutandoPurga ? 'Ejecutando purga...' : 'Ejecutar Purga Manual' }}
        </button>
        
        <button 
          @click="simularPurga"
          class="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded flex items-center"
          :disabled="ejecutandoPurga"
        >
          <span class="mr-2">🔍</span>
          Vista Previa
        </button>
      </div>
      
      <!-- Información de sistema automático -->
      <div class="mt-4 bg-green-50 border border-green-200 p-3 rounded">
        <div class="flex items-center">
          <span class="text-green-600 text-xl mr-2">🤖</span>
          <div>
            <p class="font-medium text-green-800">Sistema de Purga Automática Activo</p>
            <p class="text-sm text-green-700">
              El sistema ejecuta automáticamente una purga cada 48 horas para mantener la base de datos optimizada.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Sección de reinicio completo -->
    <div class="border-t pt-6 mt-6">
      <h3 class="text-lg font-semibold mb-4 text-gray-700">Reinicio Completo de Estadísticas</h3>

      <!-- Advertencia -->
      <div class="bg-red-50 border border-red-300 p-4 rounded mb-4">
        <div class="flex items-start">
          <span class="text-red-600 text-xl mr-3">⚠️</span>
          <div>
            <p class="font-medium text-red-800 mb-2">¡ACCIÓN DESTRUCTIVA!</p>
            <p class="text-sm text-red-700">
              Esta acción eliminará TODAS las estadísticas, números históricos, predicciones y análisis.
              También limpiará la cache de Redis y reiniciará todos los cálculos desde cero.
            </p>
          </div>
        </div>
      </div>

      <!-- Información de lo que se eliminará -->
      <div class="bg-orange-50 border border-orange-200 p-3 rounded mb-4">
        <h4 class="font-medium text-orange-800 mb-2">Se eliminarán:</h4>
        <ul class="text-sm text-orange-700 space-y-1 ml-4">
          <li>• Todos los números de la base de datos</li>
          <li>• Todo el historial de ruleta</li>
          <li>• Cache de números en Redis</li>
          <li>• Estadísticas de grupos y análisis</li>
          <li>• Predicciones de IA almacenadas</li>
          <li>• Análisis de estrategias (TIA LU, Ultra PUX)</li>
        </ul>
      </div>

      <!-- Confirmación -->
      <div class="mb-4">
        <label class="flex items-center space-x-3">
          <input
            v-model="confirmacionReinicio"
            type="checkbox"
            class="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
          />
          <span class="text-sm font-medium text-gray-700">
            Confirmo que entiendo que esta acción es irreversible y eliminará todas las estadísticas
          </span>
        </label>
      </div>

      <!-- Botón de reinicio -->
      <button
        @click="ejecutarReinicioCompleto"
        class="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded flex items-center font-semibold"
        :disabled="ejecutandoReinicio || !confirmacionReinicio"
      >
        <span v-if="ejecutandoReinicio" class="animate-spin mr-2">⟳</span>
        <span v-else class="mr-2">🔄</span>
        {{ ejecutandoReinicio ? 'Reiniciando sistema...' : 'REINICIAR TODO EL SISTEMA' }}
      </button>
    </div>
    
    <!-- Resultados de la última purga -->
    <div v-if="ultimoResultadoPurga" class="mt-6 border-t pt-4">
      <h3 class="text-lg font-semibold mb-4 text-gray-700">Último Resultado de Purga</h3>
      
      <div v-if="ultimoResultadoPurga.success" class="bg-green-50 border border-green-200 p-4 rounded">
        <div class="flex items-start">
          <span class="text-green-600 text-xl mr-3">✅</span>
          <div class="flex-1">
            <p class="font-medium text-green-800 mb-2">Purga ejecutada exitosamente</p>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p class="font-medium text-green-700">Registros antes:</p>
                <ul class="text-green-600 ml-4">
                  <li>• Individual: {{ ultimoResultadoPurga.registros_antes.individual.toLocaleString() }}</li>
                  <li>• Historial: {{ ultimoResultadoPurga.registros_antes.history.toLocaleString() }}</li>
                </ul>
              </div>
              
              <div>
                <p class="font-medium text-green-700">Registros después:</p>
                <ul class="text-green-600 ml-4">
                  <li>• Individual: {{ ultimoResultadoPurga.registros_despues.individual.toLocaleString() }}</li>
                  <li>• Historial: {{ ultimoResultadoPurga.registros_despues.history.toLocaleString() }}</li>
                </ul>
              </div>
            </div>
            
            <div class="mt-3 p-2 bg-green-100 rounded">
              <p class="font-semibold text-green-800">
                Total eliminado: {{ ultimoResultadoPurga.registros_eliminados.toLocaleString() }} registros
              </p>
              <p class="text-xs text-green-600 mt-1">
                Fecha límite: {{ new Date(ultimoResultadoPurga.fecha_limite).toLocaleString('es-ES') }}
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else class="bg-red-50 border border-red-200 p-4 rounded">
        <div class="flex items-start">
          <span class="text-red-600 text-xl mr-3">❌</span>
          <div>
            <p class="font-medium text-red-800 mb-2">Error en la purga</p>
            <p class="text-sm text-red-600">{{ ultimoResultadoPurga.error }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Mensajes de estado -->
    <div v-if="mensaje" class="mt-4">
      <div :class="[
        'p-3 rounded border',
        mensaje.tipo === 'success' ? 'bg-green-50 border-green-200 text-green-800' :
        mensaje.tipo === 'error' ? 'bg-red-50 border-red-200 text-red-800' :
        'bg-blue-50 border-blue-200 text-blue-800'
      ]">
        {{ mensaje.texto }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { obtenerEstadoBaseDatos, ejecutarPurgaManual, formatearEstadoDb } from '~/utils/api';

// Estado del componente
const estadoFormateado = ref<any>(null);
const cargandoEstado = ref(false);
const ejecutandoPurga = ref(false);
const ultimoResultadoPurga = ref<any>(null);
const mensaje = ref<{ tipo: string; texto: string } | null>(null);

// Estado del reinicio completo
const confirmacionReinicio = ref(false);
const ejecutandoReinicio = ref(false);

// Configuración de purga
const configuracionPurga = ref({
  mantenerHoras: 48,
  mantenerMinimo: 50
});

// Cargar estado inicial
onMounted(async () => {
  await actualizarEstado();
});

// Actualizar estado de la base de datos
const actualizarEstado = async () => {
  cargandoEstado.value = true;
  mensaje.value = null;
  
  try {
    const estadoRaw = await obtenerEstadoBaseDatos();
    estadoFormateado.value = formatearEstadoDb(estadoRaw);
    
    if (!estadoRaw.success) {
      mostrarMensaje('error', `Error al obtener estado: ${estadoRaw.error}`);
    }
  } catch (error) {
    console.error('Error al actualizar estado:', error);
    mostrarMensaje('error', 'Error al conectar con el servidor');
  } finally {
    cargandoEstado.value = false;
  }
};

// Ejecutar purga manual
const ejecutarPurga = async () => {
  if (!confirm('¿Estás seguro de que quieres ejecutar la purga? Esta acción eliminará registros antiguos de manera permanente.')) {
    return;
  }
  
  ejecutandoPurga.value = true;
  mensaje.value = null;
  
  try {
    mostrarMensaje('info', 'Ejecutando purga... Esto puede tomar algunos segundos.');
    
    const resultado = await ejecutarPurgaManual(
      configuracionPurga.value.mantenerHoras,
      configuracionPurga.value.mantenerMinimo
    );
    
    ultimoResultadoPurga.value = resultado;
    
    if (resultado.success) {
      mostrarMensaje('success', `Purga completada exitosamente. Se eliminaron ${resultado.registros_eliminados} registros.`);
      // Actualizar estado después de la purga
      setTimeout(actualizarEstado, 1000);
    } else {
      mostrarMensaje('error', `Error en la purga: ${resultado.error}`);
    }
  } catch (error) {
    console.error('Error al ejecutar purga:', error);
    mostrarMensaje('error', 'Error al ejecutar la purga');
  } finally {
    ejecutandoPurga.value = false;
  }
};

// Simular purga (vista previa)
const simularPurga = async () => {
  if (!estadoFormateado.value) {
    mostrarMensaje('error', 'Primero actualiza el estado de la base de datos');
    return;
  }
  
  const { antiguedad, totalRegistros } = estadoFormateado.value;
  const horasConfig = configuracionPurga.value.mantenerHoras;
  
  let registrosAEliminar = 0;
  
  if (antiguedad.horas > horasConfig) {
    // Estimar cuántos registros se eliminarían
    const porcentajeAntiguo = Math.max(0, (antiguedad.horas - horasConfig) / antiguedad.horas);
    registrosAEliminar = Math.round(totalRegistros.individual * porcentajeAntiguo);
    
    // Asegurar que no eliminamos más del mínimo permitido
    const mantenerMinimo = configuracionPurga.value.mantenerMinimo;
    const registrosAMantener = totalRegistros.individual - registrosAEliminar;
    
    if (registrosAMantener < mantenerMinimo) {
      registrosAEliminar = Math.max(0, totalRegistros.individual - mantenerMinimo);
    }
  }
  
  const registrosRestantes = totalRegistros.individual - registrosAEliminar;
  
  mostrarMensaje('info', 
    `Vista previa: Se eliminarían aproximadamente ${registrosAEliminar.toLocaleString()} registros. ` +
    `Quedarían ${registrosRestantes.toLocaleString()} registros en la base de datos.`
  );
};

// Mostrar mensaje temporal
const mostrarMensaje = (tipo: string, texto: string) => {
  mensaje.value = { tipo, texto };

  // Limpiar mensaje después de cierto tiempo
  if (tipo === 'success' || tipo === 'info') {
    setTimeout(() => {
      mensaje.value = null;
    }, 5000);
  }
};

// Ejecutar reinicio completo del sistema
const ejecutarReinicioCompleto = async () => {
  if (!confirmacionReinicio.value) {
    mostrarMensaje('error', 'Debes confirmar que entiendes las consecuencias de esta acción');
    return;
  }

  const confirmacion = confirm(
    '¿ESTÁS ABSOLUTAMENTE SEGURO?\n\n' +
    'Esta acción eliminará:\n' +
    '• Todos los números de la base de datos\n' +
    '• Todo el historial de ruleta\n' +
    '• Cache de Redis\n' +
    '• Todas las estadísticas y análisis\n' +
    '• Predicciones de IA\n\n' +
    'Esta acción es IRREVERSIBLE.\n\n' +
    'Escribe "CONFIRMO" en el siguiente cuadro para continuar:'
  );

  if (!confirmacion) return;

  const confirmacionTexto = prompt('Escribe "CONFIRMO" para proceder con el reinicio completo:');
  if (confirmacionTexto !== 'CONFIRMO') {
    mostrarMensaje('error', 'Reinicio cancelado. No se escribió la confirmación correcta.');
    return;
  }

  ejecutandoReinicio.value = true;
  mensaje.value = null;

  try {
    mostrarMensaje('info', 'Iniciando reinicio completo del sistema... Esto puede tomar varios minutos.');

    // Llamar al endpoint de reinicio completo
    const response = await fetch('/api/system/reset-complete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        confirmed: true,
        timestamp: new Date().toISOString()
      })
    });

    const resultado = await response.json();

    if (resultado.success) {
      mostrarMensaje('success',
        `Sistema reiniciado completamente. Se eliminaron ${resultado.deleted_numbers || 0} números ` +
        `y ${resultado.deleted_history || 0} registros de historial. Redis limpiado.`
      );

      // Resetear el checkbox
      confirmacionReinicio.value = false;

      // Actualizar estado después del reinicio
      setTimeout(actualizarEstado, 2000);

      // Recargar la página después de unos segundos para limpiar todo el estado
      setTimeout(() => {
        window.location.reload();
      }, 5000);

    } else {
      mostrarMensaje('error', `Error en el reinicio: ${resultado.error || 'Error desconocido'}`);
    }

  } catch (error) {
    console.error('Error al ejecutar reinicio completo:', error);
    mostrarMensaje('error', 'Error al conectar con el servidor para el reinicio completo');
  } finally {
    ejecutandoReinicio.value = false;
  }
};
</script> 