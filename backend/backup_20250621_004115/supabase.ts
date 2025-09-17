// Nueva implementación que reemplaza Supabase con llamadas directas a la API
// Mantiene la misma interfaz para compatibilidad con el código existente

// Caché en memoria para reducir consultas
let cachedNumbers: any[] = [];
let lastFetchTimestamp = 0;
const CACHE_LIFETIME = 10000; // 10 segundos de vida para la caché

// Configuración de la API
const getApiBaseUrl = () => {
  if (process.server) {
    return 'http://localhost:5000'; // Server-side
  }
  
  // Client-side
  if (typeof window !== 'undefined') {
    return window.location.origin.includes('localhost') 
      ? 'http://localhost:5000' 
      : window.location.origin;
  }
  
  return 'http://localhost:5000';
};

// Función auxiliar para hacer peticiones HTTP
const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };
  
  try {
    const response = await fetch(url, defaultOptions);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API request failed for ${endpoint}:`, error);
    throw error;
  }
};

// ============================================================================
// FUNCIONES PRINCIPALES (COMPATIBLES CON SUPABASE.TS)
// ============================================================================

// Obtener los últimos números de la ruleta
export const getLastRouletteNumbers = async (limit = 20) => {
  // Verificar si podemos usar la caché
  const now = Date.now();
  if (cachedNumbers.length > 0 && (now - lastFetchTimestamp) < CACHE_LIFETIME) {
    return cachedNumbers.slice(0, limit);
  }
  
  try {
    const response = await apiRequest(`/api/numeros-recientes?limit=${limit}`);
    
    if (!response.success) {
      console.error('Error fetching roulette numbers:', response.error);
      return cachedNumbers.length ? cachedNumbers.slice(0, limit) : [];
    }
    
    // Los datos ya vienen en el formato correcto desde la nueva API
    const transformedData = response.data.map((item: any) => ({
      id: item.id,
      history_entry_id: item.history_entry_id,
      number: item.number, // La nueva API ya usa 'number'
      color: item.color,
      created_at: item.created_at,
      timestamp: item.timestamp || item.created_at
    }));
    
    // Actualizar la caché
    cachedNumbers = transformedData;
    lastFetchTimestamp = now;
    
    return transformedData;
    
  } catch (error) {
    console.error('Error inesperado al obtener números:', error);
    return cachedNumbers.length ? cachedNumbers.slice(0, limit) : [];
  }
};

// Insertar un nuevo número de ruleta
export const insertRouletteNumber = async (number: number, customTimestamp?: string) => {
  // Validar que el número sea válido en la ruleta (0-36)
  if (number < 0 || number > 36 || isNaN(number)) {
    console.error(`Número inválido: ${number}. Debe estar entre 0 y 36.`);
    return null;
  }
  
  try {
    const response = await apiRequest('/api/insertar-numero', {
      method: 'POST',
      body: JSON.stringify({
        number: number,
        custom_timestamp: customTimestamp
      })
    });
    
    if (!response.success) {
      // Manejar errores de duplicados
      if (response.error === 'duplicate_detected') {
        console.error(`Duplicado detectado para número ${number}:`, response.message);
        return {
          error: true,
          message: response.message,
          isDuplicate: true,
          duplicateNumber: number,
          allowOverride: response.allow_override
        };
      }
      
      console.error('Error al insertar número:', response.error);
      return null;
    }
    
    // Invalidar la caché
    cachedNumbers = [];
    lastFetchTimestamp = 0;
    
    console.log(`Número ${number} insertado correctamente`);
    return response.data;
    
  } catch (error) {
    console.error(`Error al insertar número ${number}:`, error);
    return null;
  }
};

// Función para verificar duplicados consecutivos de forma inteligente
const checkConsecutiveDuplicate = (number: number, recentNumbers: number[]) => {
  // VALIDACIÓN REFORZADA para evitar duplicados accidentales
  if (recentNumbers.length === 0) {
    return { isDuplicate: false, message: '' };
  }
  
  // VALIDACIÓN 1: Duplicado inmediato (último número igual)
  if (recentNumbers[0] === number) {
    return {
      isDuplicate: true,
      message: `El número ${number} se repite inmediatamente después del último número. ¿Está seguro de que es correcto? Esto es inusual en ruleta.`
    };
  }
  
  // VALIDACIÓN 2: Número aparece en los últimos 3 números
  if (recentNumbers.length >= 2) {
    const lastThree = recentNumbers.slice(0, 3);
    if (lastThree.includes(number)) {
      const position = lastThree.indexOf(number) + 1;
      return {
        isDuplicate: true,
        message: `El número ${number} ya apareció recientemente en los últimos números (posición: ${position}). ¿Está seguro?`
      };
    }
  }
  
  // VALIDACIÓN 3: Detectar patrones sospechosos (mismo número aparece frecuentemente)
  if (recentNumbers.length >= 4) {
    const lastFive = recentNumbers.slice(0, 5);
    const countInRecent = lastFive.filter(n => n === number).length;
    if (countInRecent >= 2) {
      return {
        isDuplicate: true,
        message: `El número ${number} ya apareció ${countInRecent} veces en los últimos ${lastFive.length} números. Esto es estadísticamente inusual.`
      };
    }
  }
  
  return { isDuplicate: false, message: '' };
};

// Función para procesar una entrada de texto con números separados por comas
export const processNumbersInput = async (numbersText: string) => {
  // Comprobar si la entrada es válida
  if (!numbersText || numbersText.trim() === '') {
    console.error('Entrada vacía');
    return null;
  }
  
  console.log(`Procesando entrada: "${numbersText}"`);
  
  // NUEVO: Obtener los últimos números para validar duplicados consecutivos
  const recentNumbers = await getLastRouletteNumbers(5);
  const recentNumberValues = recentNumbers.map(item => item.number);
  
  // Manejo especial para entrada de voz (solo un número)
  if (/^\d+$/.test(numbersText.trim())) {
    const singleNumber = parseInt(numbersText.trim());
    
    // Validar el número para ruleta
    if (singleNumber < 0 || singleNumber > 36 || isNaN(singleNumber)) {
      console.error(`Número inválido: ${singleNumber}. Debe estar entre 0 y 36.`);
      return null;
    }
    
    // MEJORADO: Verificar duplicados consecutivos más inteligentemente
    const isDuplicateConsecutive = checkConsecutiveDuplicate(singleNumber, recentNumberValues);
    if (isDuplicateConsecutive.isDuplicate) {
      console.error(`El número ${singleNumber} se detectó como duplicado consecutivo.`);
      return {
        error: true,
        message: isDuplicateConsecutive.message,
        isDuplicate: true,
        duplicateNumber: singleNumber,
        allowOverride: true
      };
    }
    
    console.log(`Procesando número único del reconocimiento de voz: ${singleNumber}`);
    
    // Insertar el número directamente
    try {
      const result = await insertRouletteNumber(singleNumber);
      
      if (!result) {
        console.error(`No se pudo insertar el número ${singleNumber}`);
        return null;
      }
      
      // Si hay error de duplicado, retornarlo
      if (result.error && result.isDuplicate) {
        return result;
      }
      
      console.log(`Número ${singleNumber} procesado correctamente`);
      
      return {
        processedCount: 1,
        totalInput: 1,
        numbers: [singleNumber],
        lastPlayed: singleNumber,
        individualEntries: [result],
      };
    } catch (error) {
      console.error(`Error al procesar número único ${singleNumber}:`, error);
      return null;
    }
  }
  
  // Para múltiples números, usar la nueva API
  try {
    const response = await apiRequest('/api/insertar-numeros', {
      method: 'POST',
      body: JSON.stringify({
        numbers: numbersText,
        force: false
      })
    });
    
    if (!response.success) {
      // Manejar errores de duplicados
      if (response.error === 'duplicates_detected') {
        console.error('Duplicados detectados:', response.message);
        return {
          error: true,
          message: response.message,
          isDuplicate: true,
          duplicateNumbers: response.duplicate_numbers?.map((d: any) => d.number) || [],
          allowOverride: true
        };
      }
      
      console.error('Error procesando múltiples números:', response.error);
      return null;
    }
    
    // Invalidar la caché
    cachedNumbers = [];
    lastFetchTimestamp = 0;
    
    console.log(`Procesamiento completado: ${response.data.processed_count} números procesados`);
    
    return {
      processedCount: response.data.processed_count,
      totalInput: response.data.total_input,
      numbers: response.data.numbers,
      lastPlayed: response.data.last_played,
      individualEntries: response.data.individual_entries,
    };
    
  } catch (error) {
    console.error('Error procesando entrada de números:', error);
    return null;
  }
};

// Obtener estadísticas de los números
export const getRouletteStats = async () => {
  try {
    const response = await apiRequest('/api/estadisticas');
    
    if (!response.success) {
      console.error('Error fetching stats:', response.error);
      return null;
    }
    
    return response.data;
    
  } catch (error) {
    console.error('Error obteniendo estadísticas:', error);
    return null;
  }
};

// Nueva función para obtener secuencias de números desde la API
export const getRouletteNumberSequences = async (limit = 100) => {
  try {
    const response = await apiRequest(`/api/secuencias?limit=${limit}`);
    
    if (!response.success) {
      console.error('Error fetching sequences:', response.error);
      return null;
    }
    
    return response.data;
    
  } catch (error) {
    console.error('Error obteniendo secuencias:', error);
    return null;
  }
};

// ============================================================================
// FUNCIONES DE PURGA DE BASE DE DATOS
// ============================================================================

// Obtener estado actual de la base de datos
export const obtenerEstadoBaseDatos = async () => {
  try {
    const response = await apiRequest('/estado-db');
    return response;
  } catch (error) {
    console.error('Error al obtener estado de la base de datos:', error);
    return {
      success: false,
      error: error.message || 'Error desconocido'
    };
  }
};

// Ejecutar purga manual de la base de datos
export const ejecutarPurgaManual = async (mantenerHoras = 48, mantenerMinimo = 50) => {
  try {
    const response = await apiRequest('/purgar-db', {
      method: 'POST',
      body: JSON.stringify({
        mantener_horas: mantenerHoras,
        mantener_minimo: mantenerMinimo
      })
    });
    
    return response;
  } catch (error) {
    console.error('Error al ejecutar purga manual:', error);
    return {
      success: false,
      error: error.message || 'Error desconocido'
    };
  }
};

// Verificar si la base de datos necesita purga
export const verificarNecesidadPurga = async () => {
  try {
    const estado = await obtenerEstadoBaseDatos();
    
    if (!estado.success) {
      return {
        necesita: false,
        error: estado.error
      };
    }
    
    const { estado: estadoDb } = estado;
    
    return {
      necesita: estadoDb.necesita_purga,
      horasDesdeAntiguo: estadoDb.horas_desde_mas_antiguo,
      totalRegistros: estadoDb.total_registros,
      registrosRecientes: {
        ultimas24h: estadoDb.registros_ultimas_24h,
        ultimas48h: estadoDb.registros_ultimas_48h
      },
      fechaAntigua: estadoDb.registro_mas_antiguo,
      fechaReciente: estadoDb.registro_mas_reciente
    };
  } catch (error) {
    console.error('Error al verificar necesidad de purga:', error);
    return {
      necesita: false,
      error: error.message || 'Error desconocido'
    };
  }
};

// Función para mostrar información legible sobre el estado de la DB
export const formatearEstadoDb = (estadoRaw: any) => {
  if (!estadoRaw || !estadoRaw.success) {
    return {
      mensaje: 'Error al obtener estado de la base de datos',
      detalles: estadoRaw?.error || 'Error desconocido'
    };
  }
  
  const estado = estadoRaw.estado;
  
  // Formatear fechas
  const formatearFecha = (isoString: string) => {
    try {
      const fecha = new Date(isoString);
      return fecha.toLocaleString('es-ES');
    } catch {
      return 'Fecha inválida';
    }
  };
  
  // Determinar el estado general
  let estadoGeneral = '';
  let color = '';
  
  if (estado.necesita_purga) {
    estadoGeneral = '⚠️ Necesita purga';
    color = 'text-orange-600';
  } else if (estado.horas_desde_mas_antiguo > 36) {
    estadoGeneral = '⏳ Próxima purga pronto';
    color = 'text-yellow-600';
  } else {
    estadoGeneral = '✅ Estado normal';
    color = 'text-green-600';
  }
  
  return {
    estadoGeneral,
    color,
    totalRegistros: {
      individual: estado.total_registros.individual,
      history: estado.total_registros.history,
      total: estado.total_registros.individual + estado.total_registros.history
    },
    antiguedad: {
      horas: Math.round(estado.horas_desde_mas_antiguo * 100) / 100,
      fechaMasAntigua: estado.registro_mas_antiguo ? formatearFecha(estado.registro_mas_antiguo) : 'N/A',
      fechaMasReciente: estado.registro_mas_reciente ? formatearFecha(estado.registro_mas_reciente) : 'N/A'
    },
    registrosRecientes: {
      ultimas24h: estado.registros_ultimas_24h,
      ultimas48h: estado.registros_ultimas_48h,
      porcentaje24h: estado.total_registros.individual > 0 ? 
        Math.round((estado.registros_ultimas_24h / estado.total_registros.individual) * 100) : 0,
      porcentaje48h: estado.total_registros.individual > 0 ? 
        Math.round((estado.registros_ultimas_48h / estado.total_registros.individual) * 100) : 0
    },
    necesitaPurga: estado.necesita_purga,
    mensaje: `Base de datos con ${estado.total_registros.individual + estado.total_registros.history} registros. El más antiguo tiene ${Math.round(estado.horas_desde_mas_antiguo)} horas.`
  };
};

// Función para insertar un número forzosamente, ignorando validaciones de duplicados
export const forceInsertNumber = async (number: number) => {
  console.log(`🔥 FORZANDO inserción del número ${number} (ignorando validaciones)`);
  
  // Validar que el número sea válido en la ruleta (0-36)
  if (number < 0 || number > 36 || isNaN(number)) {
    console.error(`Número inválido: ${number}. Debe estar entre 0 y 36.`);
    return null;
  }
  
  try {
    const response = await apiRequest('/api/insertar-numero', {
      method: 'POST',
      body: JSON.stringify({
        number: number,
        force: true
      })
    });
    
    if (!response.success) {
      console.error(`No se pudo forzar la inserción del número ${number}:`, response.error);
      return null;
    }
    
    // Invalidar la caché
    cachedNumbers = [];
    lastFetchTimestamp = 0;
    
    console.log(`✅ Número ${number} FORZADO correctamente`);
    
    return {
      processedCount: 1,
      totalInput: 1,
      numbers: [number],
      lastPlayed: number,
      individualEntries: [response.data],
      forced: true
    };
  } catch (error) {
    console.error(`Error al forzar inserción del número ${number}:`, error);
    return null;
  }
};

// Función para procesar múltiples números forzosamente con orden cronológico correcto
export const forceInsertMultipleNumbers = async (numbersText: string) => {
  console.log(`🔥 FORZANDO inserción de múltiples números: ${numbersText}`);
  
  try {
    const response = await apiRequest('/reconocer-voz', {
      method: 'POST',
      body: JSON.stringify({
        text: numbersText,
        force_insert: true
      })
    });
    
    if (!response.success) {
      console.error('Error en inserción forzada múltiple:', response.error);
      throw new Error(response.error);
    }
    
    // Invalidar caché
    cachedNumbers = [];
    lastFetchTimestamp = 0;
    
    console.log('✅ Inserción forzada exitosa:', response);
    
    return {
      processedCount: response.processed_count,
      totalInput: response.total_input,
      numbers: response.numbers,
      lastPlayed: response.last_played,
      individualEntries: response.individual_entries,
      forced: true,
      method: 'api_direct'
    };
    
  } catch (error) {
    console.error('Error en inserción forzada múltiple:', error);
    throw error;
  }
};

// ============================================================================
// FUNCIONES DE COMPATIBILIDAD ADICIONALES
// ============================================================================

// Función para obtener el estado del analizador
export const getAnalyzerState = async () => {
  try {
    const response = await apiRequest('/api/estado-analizador');
    
    if (!response.success) {
      console.error('Error getting analyzer state:', response.error);
      return null;
    }
    
    return response.data;
  } catch (error) {
    console.error('Error obteniendo estado del analizador:', error);
    return null;
  }
};

// Función para actualizar el estado del analizador
export const updateAnalyzerState = async (updates: any) => {
  try {
    const response = await apiRequest('/api/actualizar-analizador', {
      method: 'POST',
      body: JSON.stringify(updates)
    });
    
    if (!response.success) {
      console.error('Error updating analyzer state:', response.error);
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Error actualizando estado del analizador:', error);
    return false;
  }
};

// Función para verificar el estado de salud de la API
export const checkApiHealth = async () => {
  try {
    const response = await apiRequest('/health');
    return response;
  } catch (error) {
    console.error('Error checking API health:', error);
    return {
      status: 'unhealthy',
      error: error.message || 'Connection failed'
    };
  }
};