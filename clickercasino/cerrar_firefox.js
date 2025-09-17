const { spawn } = require('child_process');

class CerrarFirefox {
    async cerrarTodosLosProcesos() {
        console.log('🚪 CERRANDO TODOS LOS PROCESOS FIREFOX...');
        console.log('='.repeat(45));
        
        const comandos = [
            // Cerrar Firefox de Playwright específicamente
            'taskkill /f /im firefox.exe 2>nul',
            // Cerrar procesos Node.js específicos
            'taskkill /f /fi "IMAGENAME eq node.exe" 2>nul',
            // Usar PowerShell para procesos más específicos
            'powershell "Get-Process -Name firefox -ErrorAction SilentlyContinue | Stop-Process -Force"',
            'powershell "Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like \\"*firefox*\\"} | Stop-Process -Force"'
        ];
        
        for (const comando of comandos) {
            try {
                console.log(`🔧 Ejecutando: ${comando}`);
                const resultado = await this.ejecutarComando(comando);
                console.log(`✅ ${resultado.includes('SUCCESS') ? 'Procesos cerrados' : 'No había procesos'}`);
            } catch (error) {
                console.log(`⚠️ ${error.message}`);
            }
        }
        
        console.log('\n🧹 LIMPIEZA ADICIONAL...');
        
        // Limpiar archivos temporales
        try {
            const fs = require('fs').promises;
            
            const archivosTemp = [
                'detectar_ventana.ps1',
                'click_temp.ps1',
                'lightning_roulette_firefox_captura.png'
            ];
            
            for (const archivo of archivosTemp) {
                try {
                    await fs.unlink(archivo);
                    console.log(`🗑️ Archivo temporal eliminado: ${archivo}`);
                } catch {
                    // Archivo no existe, continuar
                }
            }
        } catch (error) {
            console.log(`⚠️ Error limpiando archivos: ${error.message}`);
        }
        
        console.log('\n✅ LIMPIEZA COMPLETADA');
        console.log('💡 Ahora puedes ejecutar npm run detector-firefox');
    }
    
    ejecutarComando(comando) {
        return new Promise((resolve, reject) => {
            const proceso = spawn('cmd', ['/c', comando], {
                windowsHide: true
            });
            
            let salida = '';
            let error = '';
            
            proceso.stdout.on('data', (data) => {
                salida += data.toString();
            });
            
            proceso.stderr.on('data', (data) => {
                error += data.toString();
            });
            
            proceso.on('close', (codigo) => {
                if (codigo === 0 || salida.includes('SUCCESS')) {
                    resolve(salida || 'SUCCESS');
                } else {
                    reject(new Error(error || `Código de salida: ${codigo}`));
                }
            });
            
            // Timeout para evitar que se cuelgue
            setTimeout(() => {
                proceso.kill();
                resolve('TIMEOUT - proceso terminado');
            }, 5000);
        });
    }
}

// Función principal
async function cerrarFirefox() {
    const cerrador = new CerrarFirefox();
    
    try {
        await cerrador.cerrarTodosLosProcesos();
    } catch (error) {
        console.error(`❌ Error: ${error.message}`);
    }
}

// Ejecutar si se llama directamente
if (require.main === module) {
    cerrarFirefox();
}

module.exports = { CerrarFirefox, cerrarFirefox }; 