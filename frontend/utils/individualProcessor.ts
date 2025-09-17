// Función para procesar cada número individualmente 
import { processNumbersInput, getLastRouletteNumbers } from '~/utils/api';
import { generateNumberGroups, generateLocalStatisticalGroups, generateAIBasedGroups } from '~/utils/predictions';

export interface ProcessingResult {
  number: number;
  isWinning: boolean;
  message: string;
}

export const processIndividualNumbers = async (
  numbersString: string,
  checkGroupsFunction: (number: number) => any,
  getWinningMessage: (number: number, result: any) => string,
  getLosingMessage: (number: number, result: any) => string,
  fetchLastNumbers: () => Promise<void>,
  refreshAllGroups: () => Promise<boolean>,
  addMessage: (message: any) => void,
  emitter: any
) => {
  console.log(`🔄 Iniciando procesamiento individual de números: ${numbersString}`);
  
  // Extraer números de la cadena
  const numbersArray = numbersString
    .split(',')
    .map(num => num.trim())
    .filter(num => num !== '')
    .map(num => parseInt(num))
    .filter(num => !isNaN(num) && num >= 0 && num <= 36);

  if (numbersArray.length === 0) {
    addMessage({
      id: Date.now(),
      sender: 'bot',
      message: 'No se encontraron números válidos en el mensaje. Asegúrate de ingresar números del 0 al 36 separados por comas.',
      timestamp: new Date().toISOString()
    });
    return;
  }

  console.log(`📊 Números válidos a procesar: [${numbersArray.join(', ')}]`);
  
  let totalProcessed = 0;
  let victories = 0;
  let defeats = 0;
  const results: ProcessingResult[] = [];

  // Procesar cada número individualmente
  for (let i = 0; i < numbersArray.length; i++) {
    const number = numbersArray[i];
    console.log(`\n======= PROCESANDO NÚMERO ${i + 1}/${numbersArray.length}: ${number} =======`);
    
    try {
      // PASO 1: Verificar si el número está en los grupos ACTUALES (antes de procesarlo)
      const currentResult = checkGroupsFunction(number);
      
      // PASO 2: Procesar y guardar el número en la base de datos
      const processed = await processNumbersInput(number.toString());
      
      if (processed && processed.error && processed.isDuplicate) {
        console.log(`⚠️ Número ${number} duplicado, saltando...`);
        results.push({
          number,
          isWinning: false,
          message: `Número ${number}: Ya fue ingresado recientemente (duplicado)`
        });
        continue;
      }
      
      if (processed && processed.processedCount > 0) {
        totalProcessed++;
        
        // PASO 3: Actualizar datos después de cada número
        await fetchLastNumbers();
        
        // PASO 4: Determinar resultado
        let resultMessage = '';
        if (currentResult.isWinning) {
          victories++;
          resultMessage = `✅ Número ${number}: ¡VICTORIA! ${getWinningMessage(number, currentResult)}`;
        } else {
          defeats++;
          resultMessage = `❌ Número ${number}: DERROTA. ${getLosingMessage(number, currentResult)}`;
        }
        
        results.push({
          number,
          isWinning: currentResult.isWinning,
          message: resultMessage
        });
        
        // PASO 5: Regenerar grupos después de cada número para el siguiente
        await refreshAllGroups();
        
        // Emitir eventos
        if (emitter) {
          emitter.emit('number-registered', { number });
          emitter.emit('number-played', {
            number,
            isWinning: currentResult.isWinning
          });
        }
        
        // PASO 6: Mostrar resultado inmediatamente
        addMessage({
          id: Date.now() + i,
          sender: 'bot',
          message: resultMessage,
          timestamp: new Date().toISOString(),
          numbersGenerated: [number],
          isWinning: currentResult.isWinning
        });
        
        console.log(`✅ Número ${number} procesado: ${currentResult.isWinning ? 'VICTORIA' : 'DERROTA'}`);
        
        // Pausa pequeña entre números para mejor UX
        if (i < numbersArray.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 300));
        }
      } else {
        console.error(`❌ Error procesando número ${number}`);
        results.push({
          number,
          isWinning: false,
          message: `Número ${number}: Error al procesar`
        });
      }
    } catch (error) {
      console.error(`❌ Error procesando número ${number}:`, error);
      results.push({
        number,
        isWinning: false,
        message: `Número ${number}: Error al procesar - ${error}`
      });
    }
  }
  
  // RESUMEN FINAL
  console.log(`\n🎯 RESUMEN DEL PROCESAMIENTO:`);
  console.log(`Total números procesados: ${totalProcessed}`);
  console.log(`Victorias: ${victories}`);
  console.log(`Derrotas: ${defeats}`);
  console.log(`Eficacia: ${totalProcessed > 0 ? Math.round((victories / totalProcessed) * 100) : 0}%`);
  
  // Mostrar resumen en el chat
  if (totalProcessed > 0) {
    const efficiencyPercentage = Math.round((victories / totalProcessed) * 100);
    const summaryMessage = `📊 RESUMEN: Se procesaron ${totalProcessed} números individualmente.\n✅ Victorias: ${victories}\n❌ Derrotas: ${defeats}\n🎯 Eficacia: ${efficiencyPercentage}%`;
    
    addMessage({
      id: Date.now() + 1000,
      sender: 'bot',
      message: summaryMessage,
      timestamp: new Date().toISOString()
    });
  }
  
  // Emitir evento final
  if (emitter) {
    emitter.emit('numbers-updated');
    if (numbersArray.length > 0) {
      emitter.emit('last-number-played', numbersArray[numbersArray.length - 1]);
    }
  }
  
  return results;
}; 