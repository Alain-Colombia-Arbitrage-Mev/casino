import { getLastRouletteNumbers, getRouletteStats, getRouletteNumberSequences } from './api';

// Función para generar números aleatorios en un rango
export const generateRandomNumbers = (count: number, min = 0, max = 36) => {
  const numbers = [];
  for (let i = 0; i < count; i++) {
    numbers.push(Math.floor(Math.random() * (max - min + 1)) + min);
  }
  return numbers;
};

// Función para generar predicciones básicas basadas en estadísticas recientes
export const generateStatPredictions = async (count = 5) => {
  const lastNumbers = await getLastRouletteNumbers(100);
  
  if (!lastNumbers.length) {
    return generateRandomNumbers(count);
  }
  
  // Contar las frecuencias de los números
  const freqMap = new Map<number, number>();
  
  lastNumbers.forEach(entry => {
    const num = entry.number;
    freqMap.set(num, (freqMap.get(num) || 0) + 1);
  });
  
  // Ordenar por frecuencia
  const sortedFreq = Array.from(freqMap.entries())
    .sort((a, b) => b[1] - a[1]);
  
  // Tomar los primeros 'count' números más frecuentes
  return sortedFreq.slice(0, count).map(entry => entry[0]);
};

// Predicciones basadas en "Tía Lu" (números desencadenantes)
export const generateTiaLuPredictions = async () => {
  const lastNumbers = await getLastRouletteNumbers(10);
  
  if (!lastNumbers.length) {
    return generateRandomNumbers(5);
  }
  
  // Último número que salió
  const lastNumber = lastNumbers[0].number;
  
  // Mapa de números desencadenantes a posibles siguientes números
  const triggerMap: Record<number, number[]> = {
    0: [3, 12, 26, 32, 35],
    1: [5, 9, 16, 20, 24],
    2: [4, 11, 17, 25, 31],
    3: [0, 6, 14, 26, 34],
    4: [2, 15, 19, 21, 33],
    5: [1, 8, 13, 23, 30],
    6: [3, 17, 24, 27, 34],
    7: [11, 18, 20, 29, 36],
    8: [5, 10, 19, 28, 31],
    9: [1, 14, 22, 27, 36],
    10: [8, 13, 25, 29, 35],
    11: [2, 7, 20, 30, 33],
    12: [0, 16, 23, 28, 35],
    13: [5, 10, 17, 24, 31],
    14: [3, 9, 18, 26, 32],
    15: [4, 19, 22, 29, 34],
    16: [1, 12, 23, 27, 30],
    17: [2, 6, 13, 24, 32],
    18: [7, 14, 22, 28, 36],
    19: [4, 8, 15, 21, 33],
    20: [1, 7, 11, 25, 34],
    21: [4, 19, 26, 30, 36],
    22: [9, 15, 18, 27, 31],
    23: [5, 12, 16, 32, 35],
    24: [1, 6, 13, 29, 33],
    25: [2, 10, 20, 28, 34],
    26: [0, 3, 14, 21, 35],
    27: [6, 9, 16, 22, 31],
    28: [10, 12, 18, 25, 36],
    29: [7, 10, 15, 24, 33],
    30: [5, 11, 16, 21, 32],
    31: [2, 8, 13, 22, 27],
    32: [0, 14, 17, 23, 30],
    33: [4, 11, 19, 24, 29],
    34: [3, 6, 15, 20, 25],
    35: [0, 10, 12, 23, 26],
    36: [7, 9, 18, 21, 28]
  };
  
  // Devolver los números asociados con el último
  return triggerMap[lastNumber] || generateRandomNumbers(5);
};

// Predicciones "Puxa Ultra"
export const generatePuxaUltraPredictions = async () => {
  const lastNumbers = await getLastRouletteNumbers(5);
  
  if (lastNumbers.length < 3) {
    return generateRandomNumbers(5);
  }
  
  // Análisis de patrones en los últimos 3 números
  const last3 = lastNumbers.slice(0, 3).map(entry => entry.number);
  
  // Sumar los últimos 3 números para determinar un patrón
  const sum = last3.reduce((acc, num) => acc + num, 0);
  
  // Dependiendo de la suma, generamos diferentes grupos
  if (sum <= 30) {
    return [1, 5, 9, 12, 14, 23, 27, 30];
  } else if (sum <= 60) {
    return [2, 8, 13, 17, 24, 28, 31, 36];
  } else if (sum <= 90) {
    return [3, 6, 11, 19, 22, 25, 32, 35];
  } else {
    return [0, 4, 7, 10, 15, 18, 20, 26, 29, 33, 34];
  }
};

// Generar grupos de números de diferentes tamaños con AI y protección del cero
export const generateNumberGroups = async () => {
  const lastNumbers = await getLastRouletteNumbers(30);
  
  // 🛡️ PROTECCIÓN DEL CERO MEJORADA: Detectar patrones del cero
  const recentZeroAppeared = lastNumbers.slice(0, 10).some(entry => entry.number === 0);
  const zeroFrequency = lastNumbers.slice(0, 20).filter(entry => entry.number === 0).length;
  const shouldAddZeroProtection = recentZeroAppeared || zeroFrequency >= 2;
  
  console.log(`🛡️ PROTECCIÓN DEL CERO: ${shouldAddZeroProtection ? 'ACTIVADA' : 'INACTIVA'} (Cero reciente: ${recentZeroAppeared}, Frecuencia: ${zeroFrequency}/20)`);
  
  // Análisis probabilístico mejorado
  const freqMap = new Map<number, number>();
  lastNumbers.forEach(entry => {
    const num = entry.number;
    freqMap.set(num, (freqMap.get(num) || 0) + 1);
  });
  
  // Calcular probabilidades inversas (números menos frecuentes tienen mayor probabilidad)
  const totalNumbers = lastNumbers.length;
  const probabilityMap = new Map<number, number>();
  
  for (let i = 0; i <= 36; i++) {
    const frequency = freqMap.get(i) || 0;
    const inverseProbability = 1.0 - (frequency / totalNumbers);
    probabilityMap.set(i, inverseProbability);
  }
  
  // Función helper para añadir protección del cero
  const addZeroProtection = (groupSet: Set<number>, groupName: string) => {
    if (shouldAddZeroProtection && !groupSet.has(0)) {
      // Si el grupo está lleno, reemplazar un número aleatorio
      if (groupSet.size > 0) {
        const groupArray = Array.from(groupSet);
        const randomIndex = Math.floor(Math.random() * groupArray.length);
        groupSet.delete(groupArray[randomIndex]);
      }
      groupSet.add(0);
      console.log(`🛡️ Cero añadido a ${groupName} como protección`);
    }
    return groupSet;
  };
  
  // Función para seleccionar números con probabilidades ponderadas
  const selectWithProbability = (candidates: number[], count: number, minProbability = 0.3) => {
    const selected = [];
    const shuffled = [...candidates].sort(() => Math.random() - 0.5);
    
    for (const num of shuffled) {
      if (selected.length >= count) break;
      const probability = probabilityMap.get(num) || 0.5;
      if (Math.random() < Math.max(probability, minProbability)) {
        selected.push(num);
      }
    }
    
    // Si no tenemos suficientes, añadir los restantes
    while (selected.length < count && shuffled.length > selected.length) {
      const remaining = shuffled.filter(n => !selected.includes(n));
      if (remaining.length > 0) {
        selected.push(remaining[Math.floor(Math.random() * remaining.length)]);
      } else {
        break;
      }
    }
    
    return selected;
  };
  
  // Grupo de 20 números - Estrategia AI balanceada
  const group20Set = new Set<number>();
  
  // Añadir números calientes con probabilidad ponderada
  const hotNumbers = Array.from(freqMap.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12)
    .map(entry => entry[0]);
  
  const selectedHot = selectWithProbability(hotNumbers, 8, 0.7);
  selectedHot.forEach(num => group20Set.add(num));
  
  // Añadir números fríos con probabilidad menor
  const coldNumbers = Array.from(freqMap.entries())
    .sort((a, b) => a[1] - b[1])
    .slice(0, 10)
    .map(entry => entry[0]);
  
  const selectedCold = selectWithProbability(coldNumbers, 4, 0.4);
  selectedCold.forEach(num => group20Set.add(num));
  
  // Completar con números aleatorios ponderados por probabilidad
  const allNumbers = Array.from({length: 37}, (_, i) => i);
  const remaining = allNumbers.filter(n => !group20Set.has(n));
  const selectedRemaining = selectWithProbability(remaining, 19 - group20Set.size, 0.3);
  selectedRemaining.forEach(num => group20Set.add(num));
  
  // 🛡️ Aplicar protección del cero
  addZeroProtection(group20Set, "Grupo 20");
  
  const group20 = Array.from(group20Set).slice(0, 20);
  
  // Grupo de 12 números - AI enfocado en docenas y columnas con protección del cero
  const group12Set = new Set<number>();
  
  // Calculamos frecuencias por docenas y columnas con análisis probabilístico
  let dozenFreq = [0, 0, 0]; // d1, d2, d3
  let colFreq = [0, 0, 0];   // c1, c2, c3
  
  lastNumbers.forEach(entry => {
    const num = entry.number;
    if (num >= 1 && num <= 12) dozenFreq[0]++;
    else if (num >= 13 && num <= 24) dozenFreq[1]++;
    else if (num >= 25 && num <= 36) dozenFreq[2]++;
    
    if (num !== 0) {
      if (num % 3 === 1) colFreq[0]++;
      else if (num % 3 === 2) colFreq[1]++;
      else colFreq[2]++;
    }
  });
  
  // Añadir números calientes con alta probabilidad
  const topHot = Array.from(freqMap.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(entry => entry[0]);
  
  const selectedHot12 = selectWithProbability(topHot, 5, 0.8);
  selectedHot12.forEach(num => group12Set.add(num));
  
  // Usar probabilidad inversa para docenas (apostar a la menos frecuente)
  const totalSpins = lastNumbers.length;
  const dozenProbabilities = dozenFreq.map(freq => 1.0 - (freq / totalSpins));
  const bestDozenIndex = dozenProbabilities.indexOf(Math.max(...dozenProbabilities));
  const dozenStart = bestDozenIndex * 12 + 1;
  const dozenEnd = dozenStart + 11;
  
  // Añadir números de la docena menos frecuente
  const dozenNumbers = [];
  for (let i = dozenStart; i <= dozenEnd; i++) {
    if (!group12Set.has(i)) {
      dozenNumbers.push(i);
    }
  }
  
  const selectedDozen = selectWithProbability(dozenNumbers, 4, 0.6);
  selectedDozen.forEach(num => group12Set.add(num));
  
  // Añadir números de la columna menos frecuente
  const colProbabilities = colFreq.map(freq => 1.0 - (freq / totalSpins));
  const bestColIndex = colProbabilities.indexOf(Math.max(...colProbabilities));
  
  const columnNumbers = [];
  for (let i = 1; i <= 36; i++) {
    if ((i - 1) % 3 === bestColIndex && !group12Set.has(i)) {
      columnNumbers.push(i);
    }
  }
  
  const selectedColumn = selectWithProbability(columnNumbers, 2, 0.5);
  selectedColumn.forEach(num => group12Set.add(num));
  
  // Completar con números aleatorios ponderados
  const remaining12 = allNumbers.filter(n => !group12Set.has(n));
  const selectedRemaining12 = selectWithProbability(remaining12, 11 - group12Set.size, 0.3);
  selectedRemaining12.forEach(num => group12Set.add(num));
  
  // 🛡️ Aplicar protección del cero
  addZeroProtection(group12Set, "Grupo 12");
  
  const group12 = Array.from(group12Set).slice(0, 12);
  
  // Grupo de 15 números - AI combinación inteligente de estrategias múltiples
  const group15Set = new Set<number>();
  
  // 1. Añadir números calientes con alta probabilidad
  const topHot15 = Array.from(freqMap.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(entry => entry[0]);
  
  const selectedHot15 = selectWithProbability(topHot15, 6, 0.8);
  selectedHot15.forEach(num => group15Set.add(num));
  
  // 2. Añadir números de la docena menos frecuente (probabilidad inversa)
  const dozenProbabilities15 = dozenFreq.map(freq => 1.0 - (freq / totalSpins));
  const bestDozenIndex15 = dozenProbabilities15.indexOf(Math.max(...dozenProbabilities15));
  const dozenStart15 = bestDozenIndex15 * 12 + 1;
  const dozenEnd15 = dozenStart15 + 11;
  
  const dozenNumbers15 = [];
  for (let i = dozenStart15; i <= dozenEnd15; i++) {
    if (!group15Set.has(i)) {
      dozenNumbers15.push(i);
    }
  }
  
  const selectedDozen15 = selectWithProbability(dozenNumbers15, 4, 0.6);
  selectedDozen15.forEach(num => group15Set.add(num));
  
  // 3. Añadir números de la columna menos frecuente
  const colProbabilities15 = colFreq.map(freq => 1.0 - (freq / totalSpins));
  const bestColIndex15 = colProbabilities15.indexOf(Math.max(...colProbabilities15));
  
  const columnNumbers15 = [];
  for (let i = 1; i <= 36; i++) {
    if ((i - 1) % 3 === bestColIndex15 && !group15Set.has(i)) {
      columnNumbers15.push(i);
    }
  }
  
  const selectedColumn15 = selectWithProbability(columnNumbers15, 3, 0.5);
  selectedColumn15.forEach(num => group15Set.add(num));
  
  // 4. Completar con números aleatorios ponderados
  const remaining15 = allNumbers.filter(n => !group15Set.has(n));
  const selectedRemaining15 = selectWithProbability(remaining15, 14 - group15Set.size, 0.3);
  selectedRemaining15.forEach(num => group15Set.add(num));
  
  // 🛡️ Aplicar protección del cero
  addZeroProtection(group15Set, "Grupo 15");
  
  const group15 = Array.from(group15Set).slice(0, 15);
  
  // Grupo de 9 números - AI estrategia mixta avanzada con sectores
  const group9Set = new Set<number>();
  
  // 1. Añadir números ultra calientes
  const ultraHot = Array.from(freqMap.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(entry => entry[0]);
  
  const selectedUltraHot = selectWithProbability(ultraHot, 4, 0.9);
  selectedUltraHot.forEach(num => group9Set.add(num));
  
  // 2. Añadir números de sector de vecinos del cero con probabilidad
  const voisinsNumbers = [0, 2, 3, 4, 7, 12, 15, 18, 19, 21, 22, 25, 26, 28, 29, 32, 35];
  const voisinsFiltered = voisinsNumbers.filter(n => !group9Set.has(n));
  const selectedVoisins = selectWithProbability(voisinsFiltered, 3, 0.6);
  selectedVoisins.forEach(num => group9Set.add(num));
  
  // 3. Completar con números aleatorios ponderados
  const remaining9 = allNumbers.filter(n => !group9Set.has(n));
  const selectedRemaining9 = selectWithProbability(remaining9, 8 - group9Set.size, 0.4);
  selectedRemaining9.forEach(num => group9Set.add(num));
  
  // 🛡️ Aplicar protección del cero
  addZeroProtection(group9Set, "Grupo 9");
  
  const group9 = Array.from(group9Set).slice(0, 9);
  
  // Grupo de 8 números - AI basado en paridad con probabilidades inversas
  const group8Set = new Set<number>();
  
  // Calcular probabilidades inversas para paridad
  let evenCount = 0;
  let oddCount = 0;
  
  lastNumbers.forEach(entry => {
    const num = entry.number;
    if (num !== 0) {
      if (num % 2 === 0) evenCount++;
      else oddCount++;
    }
  });
  
  // Usar probabilidad inversa (apostar al menos frecuente)
  const evenProbability = 1.0 - (evenCount / (evenCount + oddCount));
  const oddProbability = 1.0 - (oddCount / (evenCount + oddCount));
  
  // Seleccionar números calientes primero
  const hotFor8 = Array.from(freqMap.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(entry => entry[0]);
  
  const selectedHot8 = selectWithProbability(hotFor8, 4, 0.8);
  selectedHot8.forEach(num => group8Set.add(num));
  
  // Añadir números según paridad menos frecuente
  if (evenProbability > oddProbability) {
    // Añadir números pares
    const evenNumbers = [];
    for (let i = 2; i <= 36; i += 2) {
      if (!group8Set.has(i)) {
        evenNumbers.push(i);
      }
    }
    const selectedEven = selectWithProbability(evenNumbers, 3, 0.6);
    selectedEven.forEach(num => group8Set.add(num));
  } else {
    // Añadir números impares
    const oddNumbers = [];
    for (let i = 1; i <= 35; i += 2) {
      if (!group8Set.has(i)) {
        oddNumbers.push(i);
      }
    }
    const selectedOdd = selectWithProbability(oddNumbers, 3, 0.6);
    selectedOdd.forEach(num => group8Set.add(num));
  }
  
  // Completar hasta 8
  const remaining8 = allNumbers.filter(n => !group8Set.has(n));
  const selectedRemaining8 = selectWithProbability(remaining8, 7 - group8Set.size, 0.3);
  selectedRemaining8.forEach(num => group8Set.add(num));
  
  // 🛡️ Aplicar protección del cero
  addZeroProtection(group8Set, "Grupo 8");
  
  const group8 = Array.from(group8Set).slice(0, 8);
  
  // Grupo de 6 números - AI columna menos frecuente con protección del cero
  const group6Set = new Set<number>();
  
  // Usar probabilidad inversa para columnas
  const colProbabilities6 = colFreq.map(freq => 1.0 - (freq / totalSpins));
  const bestColIndex6 = colProbabilities6.indexOf(Math.max(...colProbabilities6));
  
  // Añadir números de la columna menos frecuente
  const columnNumbers6 = [];
  for (let i = 1; i <= 36; i++) {
    if ((i - 1) % 3 === bestColIndex6) {
      columnNumbers6.push(i);
    }
  }
  
  const selectedColumn6 = selectWithProbability(columnNumbers6, 5, 0.7);
  selectedColumn6.forEach(num => group6Set.add(num));
  
  // Completar hasta 6
  const remaining6 = allNumbers.filter(n => !group6Set.has(n));
  const selectedRemaining6 = selectWithProbability(remaining6, 5 - group6Set.size, 0.4);
  selectedRemaining6.forEach(num => group6Set.add(num));
  
  // 🛡️ Aplicar protección del cero
  addZeroProtection(group6Set, "Grupo 6");
  
  const group6 = Array.from(group6Set).slice(0, 6);
  
  // Grupo de 4 números - AI máxima precisión con protección del cero
  const group4Set = new Set<number>();
  
  // Solo los números más calientes con máxima probabilidad
  const topHot4 = Array.from(freqMap.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(entry => entry[0]);
  
  const selectedHot4 = selectWithProbability(topHot4, 3, 0.95);
  selectedHot4.forEach(num => group4Set.add(num));
  
  // Completar hasta 4
  const remaining4 = allNumbers.filter(n => !group4Set.has(n));
  const selectedRemaining4 = selectWithProbability(remaining4, 4 - group4Set.size, 0.5);
  selectedRemaining4.forEach(num => group4Set.add(num));
  
  // 🛡️ Aplicar protección del cero
  addZeroProtection(group4Set, "Grupo 4");
  
  const group4 = Array.from(group4Set).slice(0, 4);
  
  // Registrar en consola para depuración
  console.log(`=== GRUPOS GENERADOS DINÁMICAMENTE ===`);
  console.log(`🛡️ PROTECCIÓN DEL CERO: ${shouldAddZeroProtection ? 'ACTIVADA' : 'INACTIVA'}`);
  console.log(`Grupo 20: [${Array.from(group20).sort((a, b) => a - b).join(', ')}] ${group20.includes(0) ? '🛡️' : ''}`);
  console.log(`Grupo 15: [${Array.from(group15).sort((a, b) => a - b).join(', ')}] ${group15.includes(0) ? '🛡️' : ''}`);
  console.log(`Grupo 12: [${Array.from(group12).sort((a, b) => a - b).join(', ')}] ${group12.includes(0) ? '🛡️' : ''}`);
  console.log(`Grupo 9: [${Array.from(group9).sort((a, b) => a - b).join(', ')}] ${group9.includes(0) ? '🛡️' : ''}`);
  console.log(`Última fecha de generación: ${new Date().toLocaleTimeString()}`);
  console.log(`==========================================`);
  
  return {
    group20,
    group15,
    group12,
    group8,
    group9,
    group6,
    group4
  };
};

// Función para generar grupos con modo estándar vs AI avanzada
export const generateNumberGroupsWithMode = async (mode: 'standard' | 'ai_advanced' = 'ai_advanced') => {
  if (mode === 'standard') {
    return generateStandardGroups();
  } else {
    return generateNumberGroups(); // Ya implementada con AI
  }
};

// Generación estándar (sin AI, basada en estadísticas simples)
export const generateStandardGroups = async () => {
  const lastNumbers = await getLastRouletteNumbers(20);
  
  if (!lastNumbers || lastNumbers.length < 5) {
    return {
      group20: generateRandomNumbers(20),
      group15: generateRandomNumbers(15),
      group12: generateRandomNumbers(12),
      group8: generateRandomNumbers(8),
      group9: generateRandomNumbers(9),
      group6: generateRandomNumbers(6),
      group4: generateRandomNumbers(4)
    };
  }
  
  // Análisis básico de frecuencias
  const freqMap = new Map<number, number>();
  lastNumbers.forEach(entry => {
    const num = entry.number;
    freqMap.set(num, (freqMap.get(num) || 0) + 1);
  });
  
  // Números más frecuentes
  const hotNumbers = Array.from(freqMap.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15)
    .map(entry => entry[0]);
  
  // Números menos frecuentes
  const allNumbers = Array.from({length: 37}, (_, i) => i);
  const coldNumbers = allNumbers.filter(n => !hotNumbers.includes(n));
  
  // Sectores de ruleta estándar
  const voisinsNumbers = [0, 2, 3, 4, 7, 12, 15, 18, 19, 21, 22, 25, 26, 28, 29, 32, 35];
  const tiersNumbers = [27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33];
  const orphelinsNumbers = [1, 20, 14, 31, 9, 17, 34, 6];
  
  // Vecinos del último número
  const lastNumber = lastNumbers[0]?.number || 0;
  const neighbors = getRouletteNeighborsImproved(lastNumber, 2);
  
  console.log(`=== GRUPOS GENERADOS MODO ESTÁNDAR ===`);
  console.log(`Números calientes: [${hotNumbers.join(', ')}]`);
  console.log(`Último número: ${lastNumber}, Vecinos: [${neighbors.join(', ')}]`);
  console.log(`==========================================`);
  
  return {
    group20: [...hotNumbers.slice(0, 10), ...coldNumbers.slice(0, 10)].slice(0, 20),
    group15: [...hotNumbers.slice(0, 8), ...voisinsNumbers.slice(0, 7)].slice(0, 15),
    group12: [...hotNumbers.slice(0, 6), ...tiersNumbers.slice(0, 6)].slice(0, 12),
    group9: [...hotNumbers.slice(0, 4), ...orphelinsNumbers.slice(0, 5)].slice(0, 9),
    group8: [...hotNumbers.slice(0, 4), ...neighbors.slice(0, 4)].slice(0, 8),
    group6: hotNumbers.slice(0, 6),
    group4: hotNumbers.slice(0, 4)
  };
};

// Función para generar grupos basados en sectores específicos de la ruleta
export const generateSectorBasedGroups = async () => {
  const lastNumbers = await getLastRouletteNumbers(15);
  
  if (!lastNumbers || lastNumbers.length < 3) {
    return {
      groupVoisins: ROULETTE_WHEEL_SECTORS.voisinsDeZero.slice(0, 8),
      groupTiers: ROULETTE_WHEEL_SECTORS.tiers.slice(0, 8),
      groupOrphelins: ROULETTE_WHEEL_SECTORS.orphelinsPlein,
      groupJeuZero: ROULETTE_WHEEL_SECTORS.jeuZero,
      groupNeighbors: getRouletteNeighborsImproved(0, 3)
    };
  }
  
  const lastNumber = lastNumbers[0]?.number || 0;
  const neighbors = getRouletteNeighborsImproved(lastNumber, 3);
  
  // Analizar qué sector ha sido más activo
  const sectorActivity = {
    voisins: 0,
    tiers: 0,
    orphelins: 0,
    jeuZero: 0
  };
  
  lastNumbers.forEach(entry => {
    const num = entry.number;
    if (ROULETTE_WHEEL_SECTORS.voisinsDeZero.includes(num)) sectorActivity.voisins++;
    if (ROULETTE_WHEEL_SECTORS.tiers.includes(num)) sectorActivity.tiers++;
    if (ROULETTE_WHEEL_SECTORS.orphelinsPlein.includes(num)) sectorActivity.orphelins++;
    if (ROULETTE_WHEEL_SECTORS.jeuZero.includes(num)) sectorActivity.jeuZero++;
  });
  
  console.log(`=== ANÁLISIS DE SECTORES ===`);
  console.log(`Último número: ${lastNumber}`);
  console.log(`Actividad Voisins: ${sectorActivity.voisins}`);
  console.log(`Actividad Tiers: ${sectorActivity.tiers}`);
  console.log(`Actividad Orphelins: ${sectorActivity.orphelins}`);
  console.log(`Actividad Jeu Zero: ${sectorActivity.jeuZero}`);
  console.log(`Vecinos: [${neighbors.join(', ')}]`);
  console.log(`============================`);
  
  return {
    groupVoisins: ROULETTE_WHEEL_SECTORS.voisinsDeZero.slice(0, 8),
    groupTiers: ROULETTE_WHEEL_SECTORS.tiers.slice(0, 8),
    groupOrphelins: ROULETTE_WHEEL_SECTORS.orphelinsPlein,
    groupJeuZero: ROULETTE_WHEEL_SECTORS.jeuZero,
    groupNeighbors: neighbors.slice(0, 8)
  };
};

// Función para verificar si un número ganó dentro de un grupo
export const checkWinningNumber = (number: number, groups: any) => {
  const results = {
    group20: groups.group20.includes(number),
    group15: groups.group15.includes(number),
    group12: groups.group12.includes(number),
    group8: groups.group8.includes(number),
    group9: groups.group9.includes(number),
    group6: groups.group6.includes(number),
    group4: groups.group4.includes(number)
  };
  
  // Determinar el resultado general (ganó en algún grupo)
  const isWinner = Object.values(results).some(value => value === true);
  
  return {
    isWinner,
    details: results
  };
};

// Generar grupos basados en análisis estadístico local
export const generateLocalStatisticalGroups = async (): Promise<Record<string, number[]>> => {
  try {
    const stats = await getRouletteStats();
    const sequences = await getRouletteNumberSequences(50);
    
    // Primero generar los grupos estándar de diferentes tamaños
    const standardGroups = await generateNumberGroups();
    
    // Si no hay datos, generar grupos con números aleatorios pero lógicos
    if (!stats || !sequences) {
      console.log('⚠️ No hay datos estadísticos disponibles, generando grupos con lógica básica');
      return {
        // Grupos estándar de diferentes tamaños
        group20: standardGroups.group20 || generateRandomNumbers(20),
        group15: standardGroups.group15 || generateRandomNumbers(15),
        group12: standardGroups.group12 || generateRandomNumbers(12),
        group9: standardGroups.group9 || generateRandomNumbers(9),
        group8: standardGroups.group8 || generateRandomNumbers(8),
        group6: standardGroups.group6 || generateRandomNumbers(6),
        group4: standardGroups.group4 || generateRandomNumbers(4),
        // Grupos estadísticos específicos
        groupTerminals: [0, 1, 2, 3, 10, 11, 12, 13, 20, 21, 22, 23], // Terminales 0,1,2,3
        groupParity: [2, 4, 6, 8, 10, 12, 14, 16], // Números pares
        groupColumns: [1, 4, 7, 10, 13, 16], // Primera columna
        groupDozens: [1, 2, 3, 4, 5, 6], // Primera docena
        groupRecent: generateRandomNumbers(6) // Números aleatorios
      };
    }
  
    // Hacemos copia profunda de los datos para evitar modificaciones no deseadas
    const statsClone = JSON.parse(JSON.stringify(stats));
    
    // Grupo basado en terminales calientes
    const terminalGroup = [];
    if (statsClone.terminals && statsClone.terminals.hot) {
      for (const terminal of statsClone.terminals.hot) {
        for (let i = 0; i <= 36; i++) {
          if (i % 10 === terminal) {
            terminalGroup.push(i);
          }
        }
      }
    }
    
    // Si no hay terminales calientes, usar terminales básicos
    if (terminalGroup.length === 0) {
      terminalGroup.push(...[0, 1, 2, 3, 10, 11, 12, 13, 20, 21, 22, 23]);
    }
    
    // Grupo basado en la tendencia de paridad
    const parityGroup = [];
    if (statsClone.oddVsEven && statsClone.oddVsEven.odd && statsClone.oddVsEven.even) {
      const evenOddRatio = statsClone.oddVsEven.odd / (statsClone.oddVsEven.odd + statsClone.oddVsEven.even);
      for (let i = 1; i <= 36; i++) {
        if (evenOddRatio > 0.52) { // Tendencia a impares
          if (i % 2 === 1) parityGroup.push(i);
        } else if (evenOddRatio < 0.48) { // Tendencia a pares
          if (i % 2 === 0) parityGroup.push(i);
        } else {
          // Sin tendencia clara, usar números calientes si están disponibles
          if (statsClone.hotNumbers && statsClone.hotNumbers.length > 0) {
            parityGroup.push(...statsClone.hotNumbers);
            break;
          } else {
            // Fallback a números pares
            if (i % 2 === 0) parityGroup.push(i);
          }
        }
      }
    } else {
      // Fallback: usar números pares
      parityGroup.push(...[2, 4, 6, 8, 10, 12, 14, 16]);
    }
    
    // Grupo basado en columnas/docenas más frecuentes
    const columnGroup = [];
    const dozenGroup = [];
    
    // Determinar columna más frecuente
    if (statsClone.columns && statsClone.columns.c1 !== undefined) {
      const columnsValues = [statsClone.columns.c1, statsClone.columns.c2, statsClone.columns.c3];
      const mostFreqColumnIndex = columnsValues.indexOf(Math.max(...columnsValues));
      for (let i = 1; i <= 36; i++) {
        if ((i - 1) % 3 === mostFreqColumnIndex) {
          columnGroup.push(i);
        }
      }
    } else {
      // Fallback: primera columna
      columnGroup.push(...[1, 4, 7, 10, 13, 16]);
    }
    
    // Determinar docena más frecuente
    if (statsClone.dozens && statsClone.dozens.d1 !== undefined) {
      const dozensValues = [statsClone.dozens.d1, statsClone.dozens.d2, statsClone.dozens.d3];
      const mostFreqDozenIndex = dozensValues.indexOf(Math.max(...dozensValues));
      const dozenStart = mostFreqDozenIndex * 12 + 1;
      for (let i = 0; i < 12; i++) {
        dozenGroup.push(dozenStart + i);
      }
    } else {
      // Fallback: primera docena
      dozenGroup.push(...[1, 2, 3, 4, 5, 6]);
    }
    
    // Grupo basado en números recientes (últimos 10 + hot numbers)
    let recentGroup = [];
    if (statsClone.lastNumbers && statsClone.lastNumbers.length > 0) {
      const lastNumbers = statsClone.lastNumbers.slice(0, 10);
      const hotNumbers = statsClone.hotNumbers || [];
      recentGroup = Array.from(new Set([...lastNumbers, ...hotNumbers])).slice(0, 12);
    } else {
      // Fallback: números aleatorios
      recentGroup = generateRandomNumbers(6);
    }
    
    console.log('✅ Grupos estadísticos generados exitosamente');
    
    return {
      // Grupos estándar de diferentes tamaños basados en estadísticas
      group20: standardGroups.group20 || generateRandomNumbers(20),
      group15: standardGroups.group15 || generateRandomNumbers(15),
      group12: standardGroups.group12 || generateRandomNumbers(12),
      group9: standardGroups.group9 || generateRandomNumbers(9),
      group8: standardGroups.group8 || generateRandomNumbers(8),
      group6: standardGroups.group6 || generateRandomNumbers(6),
      group4: standardGroups.group4 || generateRandomNumbers(4),
      // Grupos estadísticos específicos
      groupTerminals: terminalGroup.slice(0, 12), // Basado en terminales (dígitos finales)
      groupParity: parityGroup.slice(0, 8),       // Basado en tendencia par/impar
      groupColumns: columnGroup.slice(0, 6),      // Basado en columna más frecuente
      groupDozens: dozenGroup.slice(0, 6),        // Basado en docena más frecuente
      groupRecent: recentGroup.slice(0, 6)        // Basado en números recientes
    };
  } catch (error) {
    console.error('Error en generateLocalStatisticalGroups:', error);
    // Fallback completo con números lógicos
    const fallbackGroups = await generateNumberGroups();
    return {
      // Grupos estándar de diferentes tamaños
      group20: fallbackGroups.group20 || generateRandomNumbers(20),
      group15: fallbackGroups.group15 || generateRandomNumbers(15),
      group12: fallbackGroups.group12 || generateRandomNumbers(12),
      group9: fallbackGroups.group9 || generateRandomNumbers(9),
      group8: fallbackGroups.group8 || generateRandomNumbers(8),
      group6: fallbackGroups.group6 || generateRandomNumbers(6),
      group4: fallbackGroups.group4 || generateRandomNumbers(4),
      // Grupos estadísticos específicos
      groupTerminals: [0, 1, 2, 3, 10, 11, 12, 13, 20, 21, 22, 23],
      groupParity: [2, 4, 6, 8, 10, 12, 14, 16],
      groupColumns: [1, 4, 7, 10, 13, 16],
      groupDozens: [1, 2, 3, 4, 5, 6],
      groupRecent: generateRandomNumbers(6)
    };
  }
};

// Generar grupos basados en IA
export const generateAIBasedGroups = async (): Promise<Record<string, number[]>> => {
  try {
    const recentNumbers = await getLastRouletteNumbers(30);
    
    // Primero generar los grupos estándar de diferentes tamaños con IA
    const standardGroups = await generateNumberGroups();
    
    // Fallback robusto si no hay datos suficientes
    if (!recentNumbers || recentNumbers.length < 5) {
      console.log('⚠️ No hay suficientes números recientes para IA, usando fallbacks lógicos');
      return {
        // Grupos estándar de diferentes tamaños con IA
        group20: standardGroups.group20 || generateRandomNumbers(20),
        group15: standardGroups.group15 || generateRandomNumbers(15),
        group12: standardGroups.group12 || generateRandomNumbers(12),
        group9: standardGroups.group9 || generateRandomNumbers(9),
        group8: standardGroups.group8 || generateRandomNumbers(8),
        group6: standardGroups.group6 || generateRandomNumbers(6),
        group4: standardGroups.group4 || generateRandomNumbers(4),
        // Grupos IA específicos
        groupCycles: [1, 5, 9, 13, 17, 21], // Números con patrón de 4
        groupNeighbors: [0, 32, 15, 19, 4, 21], // Vecinos del 0
        groupSection: [1, 2, 3, 4, 5, 6], // Primera docena
        groupAlternate: [2, 4, 6, 8, 10, 12], // Números pares
        groupRecentAI: [7, 14, 21, 28, 35, 36], // Múltiplos de 7
        groupSectors: [22, 18, 29, 7, 28, 12, 35, 3], // Voisins del cero
        groupVecinos: [0, 32, 15, 19, 4, 21, 2, 25] // Vecinos del 0 extendidos
      };
    }
    
    const numbers = recentNumbers.map(n => n.number);
    
    // Grupo 1: Ciclos avanzados
    let cycleNumbers = [];
    const recentSum = numbers.slice(0, 5).reduce((sum, num) => sum + num, 0);
    const recentAvg = recentSum / 5;
    
    // Predicción basada en ciclos y repeticiones
    for (let i = 1; i <= 36; i++) {
      if (Math.abs(i - recentAvg) < 6) {
        cycleNumbers.push(i);
      }
    }
    
    // Fallback si no hay suficientes números en ciclos
    if (cycleNumbers.length < 6) {
      cycleNumbers = [1, 5, 9, 13, 17, 21, 25, 29];
    }
    
    // Grupo 2: Vecinos en la rueda física
    const lastNumber = numbers[0] || 0;
    let neighborNumbers = getRouletteNeighborsImproved(lastNumber, 2);
    
    // Asegurar que tenemos suficientes vecinos
    if (neighborNumbers.length < 6) {
      neighborNumbers = [0, 32, 15, 19, 4, 21, 2, 25];
    }
    
    // Grupo 3: Sector caliente basado en los últimos números
    const sectorCounts = {
      voisinsZero: 0,
      tiers: 0,
      orphelins: 0,
      jeuZero: 0
    };
    
    // Contar cuántos de los últimos 10 números están en cada sector
    numbers.slice(0, 10).forEach(num => {
      if (ROULETTE_WHEEL_SECTORS.voisinsDeZero.includes(num)) sectorCounts.voisinsZero++;
      if (ROULETTE_WHEEL_SECTORS.tiers.includes(num)) sectorCounts.tiers++;
      if (ROULETTE_WHEEL_SECTORS.orphelinsPlein.includes(num)) sectorCounts.orphelins++;
      if (ROULETTE_WHEEL_SECTORS.jeuZero.includes(num)) sectorCounts.jeuZero++;
    });
    
    // Seleccionar el sector con más ocurrencias
    let hotSector = 'voisinsZero';
    let maxCount = sectorCounts.voisinsZero;
    
    if (sectorCounts.tiers > maxCount) {
      hotSector = 'tiers';
      maxCount = sectorCounts.tiers;
    }
    if (sectorCounts.orphelins > maxCount) {
      hotSector = 'orphelins';
      maxCount = sectorCounts.orphelins;
    }
    if (sectorCounts.jeuZero > maxCount) {
      hotSector = 'jeuZero';
      maxCount = sectorCounts.jeuZero;
    }
    
    // Obtener números del sector caliente
    let sectionNumbers = [];
    if (hotSector === 'voisinsZero') sectionNumbers = ROULETTE_WHEEL_SECTORS.voisinsDeZero.slice(0, 8);
    else if (hotSector === 'tiers') sectionNumbers = ROULETTE_WHEEL_SECTORS.tiers.slice(0, 8);
    else if (hotSector === 'orphelins') sectionNumbers = ROULETTE_WHEEL_SECTORS.orphelinsPlein;
    else sectionNumbers = ROULETTE_WHEEL_SECTORS.jeuZero;
    
    // Asegurar que tenemos números en la sección
    if (sectionNumbers.length === 0) {
      sectionNumbers = ROULETTE_WHEEL_SECTORS.voisinsDeZero.slice(0, 8);
    }
    
    // Grupo 4: Patrón de alternancia detectado
    let alternateNumbers = [];
    let hasAlternatingPattern = false;
    
    // Verificar si hay alternancia de paridad en los últimos 4 números
    if (numbers.length >= 4) {
      const parities = numbers.slice(0, 4).map(n => n % 2);
      if (
        (parities[0] === 0 && parities[1] === 1 && parities[2] === 0 && parities[3] === 1) ||
        (parities[0] === 1 && parities[1] === 0 && parities[2] === 1 && parities[3] === 0)
      ) {
        hasAlternatingPattern = true;
        // Si existe alternancia, predecir continuando el patrón
        const nextParity = parities[0] === 0 ? 1 : 0;
        for (let i = 1; i <= 36; i++) {
          if (i % 2 === nextParity) alternateNumbers.push(i);
        }
      }
    }
    
    if (!hasAlternatingPattern || alternateNumbers.length === 0) {
      // Fallback: usar números pares
      alternateNumbers = [2, 4, 6, 8, 10, 12, 14, 16];
    }
    
    // Grupo 5: Correlación con IA simulada
    let recentAI = [];
    try {
      recentAI = await simulateAIPrediction(numbers.slice(0, 10));
    } catch (error) {
      console.error('Error en simulateAIPrediction:', error);
      recentAI = [3, 7, 11, 15, 19, 23, 27, 31]; // Fallback
    }
    
    // Asegurar que tenemos números en recentAI
    if (recentAI.length === 0) {
      recentAI = [3, 7, 11, 15, 19, 23, 27, 31];
    }
    
    console.log('✅ Grupos IA generados exitosamente');
    
    // Limitamos cada grupo a 8 números y aseguramos que todos tengan contenido
    return {
      // Grupos estándar de diferentes tamaños con IA
      group20: standardGroups.group20 || generateRandomNumbers(20),
      group15: standardGroups.group15 || generateRandomNumbers(15),
      group12: standardGroups.group12 || generateRandomNumbers(12),
      group9: standardGroups.group9 || generateRandomNumbers(9),
      group8: standardGroups.group8 || generateRandomNumbers(8),
      group6: standardGroups.group6 || generateRandomNumbers(6),
      group4: standardGroups.group4 || generateRandomNumbers(4),
      // Grupos IA específicos
      groupCycles: cycleNumbers.slice(0, 8),
      groupNeighbors: [...new Set(neighborNumbers)].slice(0, 8),
      groupSection: sectionNumbers.slice(0, 8),
      groupAlternate: alternateNumbers.slice(0, 8),
      groupRecentAI: recentAI.slice(0, 8),
      groupSectors: ROULETTE_WHEEL_SECTORS.voisinsDeZero.slice(0, 8),
      groupVecinos: getRouletteNeighborsImproved(lastNumber, 3).slice(0, 8)
    };
  } catch (error) {
    console.error('Error in generateAIBasedGroups:', error);
    // Generar grupos estándar como fallback
    const fallbackGroups = await generateNumberGroups().catch(() => ({
      group20: generateRandomNumbers(20),
      group15: generateRandomNumbers(15),
      group12: generateRandomNumbers(12),
      group9: generateRandomNumbers(9),
      group8: generateRandomNumbers(8),
      group6: generateRandomNumbers(6),
      group4: generateRandomNumbers(4)
    }));
    
    return {
      // Grupos estándar de diferentes tamaños
      group20: fallbackGroups.group20 || generateRandomNumbers(20),
      group15: fallbackGroups.group15 || generateRandomNumbers(15),
      group12: fallbackGroups.group12 || generateRandomNumbers(12),
      group9: fallbackGroups.group9 || generateRandomNumbers(9),
      group8: fallbackGroups.group8 || generateRandomNumbers(8),
      group6: fallbackGroups.group6 || generateRandomNumbers(6),
      group4: fallbackGroups.group4 || generateRandomNumbers(4),
      // Grupos IA específicos con fallbacks
      groupCycles: generateRandomNumbers(6),
      groupNeighbors: generateRandomNumbers(6),
      groupSection: generateRandomNumbers(6),
      groupAlternate: generateRandomNumbers(6),
      groupRecentAI: generateRandomNumbers(6),
      groupSectors: ROULETTE_WHEEL_SECTORS.voisinsDeZero.slice(0, 8),
      groupVecinos: getRouletteNeighborsImproved(0, 3).slice(0, 8)
    };
  }
};

// Obtener vecinos de un número en la rueda de ruleta
function getRouletteNeighbors(number: number): number[] {
  // Disposición de números en la ruleta europea (0, 32, 15, 19, ...)
  const rouletteOrder = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
  ];
  
  const index = rouletteOrder.indexOf(number);
  if (index === -1) return [];
  
  // Obtener 2 vecinos en cada dirección
  const neighbors = [];
  for (let i = 1; i <= 2; i++) {
    const leftIndex = (index - i + rouletteOrder.length) % rouletteOrder.length;
    const rightIndex = (index + i) % rouletteOrder.length;
    neighbors.push(rouletteOrder[leftIndex], rouletteOrder[rightIndex]);
  }
  
  return neighbors;
}

// Obtener los vecinos de un número en la ruleta (versión mejorada)
export const getRouletteNeighborsImproved = (number: number, radius = 2) => {
  // Orden de los números en la ruleta europea (0, 32, 15, 19, etc.)
  const wheelOrder = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34,
    6, 27, 13, 36, 11, 30, 8, 23, 10, 5,
    24, 16, 33, 1, 20, 14, 31, 9, 22, 18,
    29, 7, 28, 12, 35, 3, 26
  ];
  
  const position = wheelOrder.indexOf(number);
  if (position === -1) return [];
  
  const neighbors = [];
  const totalNumbers = wheelOrder.length;
  
  // Obtener vecinos en ambas direcciones
  for (let i = -radius; i <= radius; i++) {
    if (i === 0) continue; // Saltar el número mismo
    
    // Cálculo de posición con manejo de desbordamiento circular
    const neighborPos = (position + i + totalNumbers) % totalNumbers;
    neighbors.push(wheelOrder[neighborPos]);
  }
  
  return neighbors;
};

// Analizar secciones de la ruleta
function analyzeRouletteSection(numbers: number[]): { section: string, numbers: number[] } {
  // Dividir la ruleta en 3 secciones
  const section1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]; // 1-12
  const section2 = [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]; // 13-24
  const section3 = [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36]; // 25-36
  
  // Contar ocurrencias en cada sección
  let count1 = 0, count2 = 0, count3 = 0;
  
  numbers.forEach(num => {
    if (section1.includes(num)) count1++;
    else if (section2.includes(num)) count2++;
    else if (section3.includes(num)) count3++;
  });
  
  // Determinar sección más frecuente
  if (count1 >= count2 && count1 >= count3) {
    return { section: 'section1', numbers: section1 };
  } else if (count2 >= count1 && count2 >= count3) {
    return { section: 'section2', numbers: section2 };
  } else {
    return { section: 'section3', numbers: section3 };
  }
}

// Detectar patrones de alternancia
function detectAlternatePatterns(sequence: string[]): string | null {
  if (sequence.length < 4) return null;
  
  const lastFour = sequence.slice(-4);
  
  // Verificar patrón par-impar-par-impar o similar
  if (lastFour[0] === 'even' && lastFour[1] === 'odd' && lastFour[2] === 'even' && lastFour[3] === 'odd') {
    return 'even'; // El siguiente sería par
  } else if (lastFour[0] === 'odd' && lastFour[1] === 'even' && lastFour[2] === 'odd' && lastFour[3] === 'even') {
    return 'odd'; // El siguiente sería impar
  }
  
  // Verificar patrón rojo-negro-rojo-negro o similar
  if (lastFour[0] === 'red' && lastFour[1] === 'black' && lastFour[2] === 'red' && lastFour[3] === 'black') {
    return 'red'; // El siguiente sería rojo
  } else if (lastFour[0] === 'black' && lastFour[1] === 'red' && lastFour[2] === 'black' && lastFour[3] === 'red') {
    return 'black'; // El siguiente sería negro
  }
  
  return null; // No se detectó patrón
}

// Simular correlación entre números (para el grupo basado en IA)
function getCorrelatedNumbers(numbers: number[]): number[] {
  const correlated = [];
  
  for (const num of numbers) {
    // "Correlación" simple: sumar/restar dígitos
    const digits = num.toString().split('').map(Number);
    if (digits.length === 2) {
      const sum = digits[0] + digits[1];
      const diff = Math.abs(digits[0] - digits[1]);
      
      if (sum <= 36) correlated.push(sum);
      if (diff > 0 && diff <= 36) correlated.push(diff);
      
      // También añadir "espejo" (ej: 23 -> 32)
      const mirror = parseInt(digits.reverse().join(''));
      if (mirror <= 36) correlated.push(mirror);
    } else {
      // Para 0-9, añadir múltiplos
      correlated.push((num * 2) % 37);
      correlated.push((num * 3) % 37);
    }
  }
  
  return correlated.filter(n => n > 0 && n <= 36);
}

// Función para simular predicción de IA basada en patrones de números
export const simulateAIPrediction = async (numbers: number[]): Promise<number[]> => {
  if (!numbers || numbers.length === 0) {
    return generateRandomNumbers(8);
  }
  
  try {
    // Conjunto para almacenar números únicos
    const predictedSet = new Set<number>();
    
    // 1. Usar correlación entre números
    const correlatedNumbers = getCorrelatedNumbers(numbers.slice(0, 8));
    correlatedNumbers.slice(0, 5).forEach(num => predictedSet.add(num));
    
    // 2. Buscar patrones de repetición en los últimos 20 números
    const lastFive = numbers.slice(0, 5);
    for (let i = 0; i < lastFive.length; i++) {
      // Añadir números cercanos al conjunto (+1, -1, +2, -2)
      const num = lastFive[i];
      if (num > 1) predictedSet.add(num - 1);
      if (num < 36) predictedSet.add(num + 1);
      if (num > 2) predictedSet.add(num - 2);
      if (num < 35) predictedSet.add(num + 2);
    }
    
    // 3. Usar vecinos físicos en la ruleta
    const lastNumber = numbers[0];
    const neighbors = getRouletteNeighborsImproved(lastNumber, 2);
    neighbors.forEach(num => predictedSet.add(num));
    
    // 4. Verificar docenas y columnas
    const groupDozenColumn = (num: number) => {
      // Calcular docena (1-12, 13-24, 25-36)
      const dozen = Math.ceil(num / 12);
      // Calcular columna (1,4,7... = 1; 2,5,8... = 2; 3,6,9... = 3)
      const column = ((num - 1) % 3) + 1;
      return { dozen, column };
    };
    
    // Contar frecuencias
    const dozenCounts = [0, 0, 0, 0]; // Índice 0 no se usa
    const columnCounts = [0, 0, 0, 0]; // Índice 0 no se usa
    
    numbers.slice(0, 10).forEach(num => {
      if (num === 0) return;
      const { dozen, column } = groupDozenColumn(num);
      dozenCounts[dozen]++;
      columnCounts[column]++;
    });
    
    // Encontrar docena y columna más frecuentes
    const maxDozen = dozenCounts.indexOf(Math.max(...dozenCounts));
    const maxColumn = columnCounts.indexOf(Math.max(...columnCounts));
    
    // Añadir algunos números de la docena y columna más frecuentes
    for (let i = 1; i <= 36; i++) {
      const { dozen, column } = groupDozenColumn(i);
      if (dozen === maxDozen || column === maxColumn) {
        // Solo añadir algunos para no sobrecargar
        if (Math.random() < 0.3) predictedSet.add(i);
      }
    }
    
    // Convertir a array y limitar a 8-12 números
    let predicted = Array.from(predictedSet);
    
    // Si tenemos pocos números, complementar con aleatorios
    if (predicted.length < 8) {
      const additional = generateRandomNumbers(8 - predicted.length);
      predicted = [...predicted, ...additional];
    }
    
    // Si tenemos demasiados, seleccionar aleatoriamente
    if (predicted.length > 12) {
      predicted = predicted.sort(() => Math.random() - 0.5).slice(0, 12);
    }
    
    return predicted;
  } catch (error) {
    console.error('Error en simulateAIPrediction:', error);
    return generateRandomNumbers(8);
  }
};

// Definición de sectores de la ruleta europea
export const ROULETTE_WHEEL_SECTORS = {
  // Sectores tradicionales
  tierDuZero: [22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15], // Tier du zero (Vecinos del cero)
  tierDuCylindre: [27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33], // Tier du cylindre
  orphelins: [1, 20, 14, 31, 9, 17, 34, 6], // Orphelins (Huérfanos)
  
  // Sectores populares
  jeuZero: [0, 3, 12, 15, 26, 32, 35], // Jeu Zero
  tiers: [33, 16, 24, 5, 10, 23, 8, 30, 11, 36, 13, 27], // Tiers
  voisinsDeZero: [22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15], // Voisins du Zéro
  orphelinsPlein: [1, 20, 14, 31, 9, 17, 34, 6], // Orphelins Plein
  
  // Otros sectores
  redSector: [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36],
  blackSector: [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35],
  greenSector: [0],
  
  // Sectores por posición en la rueda
  segment1: [0, 32, 15, 19, 4, 21, 2], // Segmento 1
  segment2: [25, 17, 34, 6, 27, 13, 36], // Segmento 2
  segment3: [11, 30, 8, 23, 10, 5, 24], // Segmento 3
  segment4: [16, 33, 1, 20, 14, 31, 9], // Segmento 4
  segment5: [22, 18, 29, 7, 28, 12, 35], // Segmento 5
  segment6: [3, 26, 0, 32, 15, 19, 4], // Segmento 6
};

// Obtener sectores específicos de la ruleta
export const getRouletteSectors = () => {
  return {
    voisinsDeZero: ROULETTE_WHEEL_SECTORS.voisinsDeZero,
    tiers: ROULETTE_WHEEL_SECTORS.tiers,
    orphelins: ROULETTE_WHEEL_SECTORS.orphelinsPlein,
    jeuZero: ROULETTE_WHEEL_SECTORS.jeuZero,
    segments: [
      ROULETTE_WHEEL_SECTORS.segment1,
      ROULETTE_WHEEL_SECTORS.segment2,
      ROULETTE_WHEEL_SECTORS.segment3,
      ROULETTE_WHEEL_SECTORS.segment4,
      ROULETTE_WHEEL_SECTORS.segment5
    ]
  };
}; 