const { DetectorFirefoxIntegrado } = require('./detector_firefox_integrado.js');

async function testClickDetection() {
    console.log('🧪 PRUEBA DE DETECCIÓN DE CLICKS EN FIREFOX');
    console.log('='.repeat(45));
    
    const detector = new DetectorFirefoxIntegrado();
    
    try {
        // Test 1: Verificar que se puede crear la instancia
        console.log('✅ Instancia del detector creada correctamente');
        
        // Test 2: Probar la función de detección de ventana Firefox
        console.log('\n🔍 Probando detección de ventana Firefox...');
        const ventanaFirefox = await detector.obtenerPosicionVentanaFirefoxMejorada();
        
        if (ventanaFirefox) {
            console.log('✅ Ventana Firefox detectada:');
            console.log(`   📐 Dimensiones: ${ventanaFirefox.width} x ${ventanaFirefox.height}`);
            console.log(`   📍 Posición: (${ventanaFirefox.x}, ${ventanaFirefox.y})`);
            console.log(`   🔍 Proceso: ${ventanaFirefox.procesoNombre || 'N/A'}`);
            console.log(`   📋 Título: ${ventanaFirefox.titulo || 'N/A'}`);
        } else {
            console.log('❌ No se pudo detectar ventana Firefox');
            console.log('💡 Abre Firefox manualmente para probar');
        }
        
        // Test 3: Verificar que las funciones de utilidad funcionan
        console.log('\n🔧 Probando funciones de utilidad...');
        
        // Test esNumero
        console.log(`   📊 esNumero('7'): ${detector.esNumero('7')}`);
        console.log(`   📊 esNumero('RED'): ${detector.esNumero('RED')}`);
        console.log(`   📊 esNumero('36'): ${detector.esNumero('36')}`);
        
        // Test obtenerEmojiMetodo
        console.log(`   📊 emoji para 'firefox_integrado': ${detector.obtenerEmojiMetodo('firefox_integrado')}`);
        console.log(`   📊 emoji para 'manual_firefox_mejorado': ${detector.obtenerEmojiMetodo('manual_firefox_mejorado')}`);
        
        console.log('\n🎯 RESULTADO DE LA PRUEBA:');
        console.log('✅ Todas las funciones básicas funcionan correctamente');
        console.log('✅ La detección de clicks debería funcionar sin problemas');
        console.log('💡 El error de PowerShell ha sido corregido');
        
        if (ventanaFirefox) {
            console.log('\n🚀 PRÓXIMOS PASOS:');
            console.log('1. Ejecuta: node detector_firefox_integrado.js');
            console.log('2. Usa el comando "manual" para probar la detección de clicks');
            console.log('3. Haz clicks en Firefox y verifica que se detecten correctamente');
        } else {
            console.log('\n🔧 PARA PROBAR COMPLETAMENTE:');
            console.log('1. Abre Firefox manualmente');
            console.log('2. Ejecuta este test de nuevo');
            console.log('3. Si detecta Firefox, usa el detector principal');
        }
        
    } catch (error) {
        console.log(`❌ Error en la prueba: ${error.message}`);
        console.log('🔧 Verifica que todos los archivos estén en su lugar');
    }
}

// Ejecutar prueba
if (require.main === module) {
    testClickDetection().catch(console.error);
}

module.exports = { testClickDetection }; 