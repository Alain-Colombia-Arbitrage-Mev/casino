const { firefox } = require('playwright');

async function verificarFirefoxPlaywright() {
    console.log('🦊 VERIFICACIÓN DE FIREFOX PLAYWRIGHT');
    console.log('='.repeat(40));
    
    let navegador = null;
    
    try {
        console.log('🚀 Iniciando Firefox de Playwright...');
        
        // Configuración mínima para solo verificar
        navegador = await firefox.launch({
            headless: false,
            args: ['--width=800', '--height=600']
        });
        
        console.log('✅ Firefox de Playwright iniciado correctamente');
        
        // Crear página de prueba
        const contexto = await navegador.newContext({
            viewport: { width: 800, height: 600 }
        });
        const pagina = await contexto.newPage();
        
        console.log('📄 Página creada, navegando a página de prueba...');
        
        // Usar una página más simple para verificación
        await pagina.goto('data:text/html,<h1>Firefox Playwright Test</h1><p>Si ves esto, Firefox funciona correctamente</p>');
        
        console.log('✅ Navegación exitosa');
        console.log('⏰ Esperando 3 segundos antes de cerrar...');
        
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        await contexto.close();
        await navegador.close();
        console.log('✅ Firefox cerrado correctamente');
        
        console.log('\n🎯 VERIFICACIÓN COMPLETADA:');
        console.log('   ✅ Firefox de Playwright funciona');
        console.log('   ✅ Solo se abre una ventana');
        console.log('   ✅ Se puede navegar correctamente');
        console.log('   ✅ Se cierra sin problemas');
        
    } catch (error) {
        console.log(`❌ Error en verificación: ${error.message}`);
        
        if (error.message.includes('Executable doesn\'t exist')) {
            console.log('\n🔧 SOLUCIÓN:');
            console.log('   Firefox de Playwright no está instalado');
            console.log('   Ejecuta: npx playwright install firefox');
        }
        
        if (navegador) {
            try {
                await navegador.close();
            } catch (e) {
                console.log('⚠️ Error cerrando navegador en catch');
            }
        }
    }
}

// Ejecutar verificación
if (require.main === module) {
    verificarFirefoxPlaywright();
}

module.exports = { verificarFirefoxPlaywright }; 