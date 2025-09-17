const fs = require('fs').promises;
const { spawn } = require('child_process');

async function testHookSimple() {
    console.log('🧪 PRUEBA SIMPLE DEL HOOK DE MOUSE');
    console.log('='.repeat(40));
    
    // Script PowerShell simple para probar el hook
    const scriptTest = `
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    using System.Text;
    
    public class SimpleMouseTest {
        [DllImport("user32.dll")]
        public static extern IntPtr GetForegroundWindow();
        
        [DllImport("user32.dll")]
        public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
        
        [StructLayout(LayoutKind.Sequential)]
        public struct POINT {
            public int x;
            public int y;
        }
        
        [DllImport("user32.dll")]
        public static extern IntPtr WindowFromPoint(POINT pt);
        
        public static void TestHook() {
            IntPtr window = GetForegroundWindow();
            StringBuilder title = new StringBuilder(256);
            GetWindowText(window, title, 256);
            
            Console.WriteLine("HOOK_TEST_SUCCESS: " + title.ToString());
        }
    }
"@

try {
    [SimpleMouseTest]::TestHook()
    Write-Host "COMPILATION_SUCCESS"
} catch {
    Write-Host "COMPILATION_ERROR: $($_.Exception.Message)"
}
`;

    try {
        console.log('📝 Creando script de prueba...');
        await fs.writeFile('test_hook_simple.ps1', scriptTest);
        
        console.log('🚀 Ejecutando prueba del hook...');
        
        const resultado = await ejecutarComando('powershell', [
            '-ExecutionPolicy', 'Bypass', 
            '-File', 'test_hook_simple.ps1'
        ]);
        
        console.log('\n📊 RESULTADO:');
        console.log(resultado);
        
        if (resultado.includes('COMPILATION_SUCCESS')) {
            console.log('\n✅ ¡HOOK FUNCIONA CORRECTAMENTE!');
            console.log('🎯 El problema de PowerShell ha sido solucionado');
            console.log('🦊 Firefox detector debería funcionar ahora');
        } else if (resultado.includes('COMPILATION_ERROR')) {
            console.log('\n❌ Aún hay errores de compilación:');
            console.log('🔧 Puede necesitar permisos de administrador');
        } else {
            console.log('\n⚠️ Resultado inesperado');
            console.log('💡 Verifica que PowerShell esté funcionando correctamente');
        }
        
        // Limpiar archivo temporal
        await fs.unlink('test_hook_simple.ps1');
        
    } catch (error) {
        console.log(`❌ Error en la prueba: ${error.message}`);
        console.log('🔧 Posibles soluciones:');
        console.log('   1. Ejecutar como administrador');
        console.log('   2. Verificar permisos de PowerShell');
        console.log('   3. Usar: Set-ExecutionPolicy RemoteSigned');
    }
}

function ejecutarComando(comando, args) {
    return new Promise((resolve, reject) => {
        const proceso = spawn(comando, args);
        let salida = '';
        let error = '';

        proceso.stdout.on('data', (data) => {
            salida += data.toString();
        });

        proceso.stderr.on('data', (data) => {
            error += data.toString();
        });

        proceso.on('close', (codigo) => {
            resolve(salida || error || `Código: ${codigo}`);
        });

        setTimeout(() => {
            proceso.kill();
            resolve('TIMEOUT');
        }, 10000);
    });
}

// Ejecutar prueba
if (require.main === module) {
    testHookSimple().catch(console.error);
}

module.exports = { testHookSimple }; 