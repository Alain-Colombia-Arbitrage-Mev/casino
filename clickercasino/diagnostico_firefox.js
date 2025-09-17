const { firefox } = require('playwright');
const fs = require('fs').promises;
const { spawn } = require('child_process');

class DiagnosticoFirefox {
    constructor() {
        this.navegador = null;
        this.pagina = null;
        this.resultados = [];
    }

    async ejecutarDiagnostico() {
        console.log('🔍 DIAGNÓSTICO COMPLETO DE FIREFOX');
        console.log('='.repeat(40));
        console.log('📋 Verificando todos los componentes necesarios para detectar clicks...');
        console.log('');

        await this.verificarPlaywright();
        await this.verificarPowerShell();
        await this.verificarPermisos();
        await this.verificarFirefoxProceso();
        await this.verificarFirefoxPlaywright();
        await this.verificarSelectores();
        await this.verificarHooks();
        
        console.log('\n📊 RESUMEN DEL DIAGNÓSTICO:');
        console.log('='.repeat(30));
        
        this.resultados.forEach((resultado, i) => {
            const estado = resultado.estado ? '✅' : '❌';
            console.log(`${estado} ${resultado.nombre}: ${resultado.mensaje}`);
        });

        // Sugerir soluciones
        const problemasEncontrados = this.resultados.filter(r => !r.estado);
        
        if (problemasEncontrados.length > 0) {
            console.log('\n🔧 SOLUCIONES RECOMENDADAS:');
            console.log('='.repeat(30));
            
            problemasEncontrados.forEach((problema, i) => {
                console.log(`${i + 1}. ${problema.nombre}:`);
                console.log(`   💡 ${problema.solucion}`);
                console.log('');
            });
        } else {
            console.log('\n🎉 ¡TODOS LOS COMPONENTES ESTÁN FUNCIONANDO CORRECTAMENTE!');
            console.log('💡 Si sigues teniendo problemas, puede ser específico del sitio web.');
        }
    }

    async verificarPlaywright() {
        console.log('🔍 Verificando instalación de Playwright...');
        
        try {
            const packageJson = JSON.parse(await fs.readFile('package.json', 'utf8'));
            const tienePlaywright = packageJson.dependencies?.playwright || packageJson.devDependencies?.playwright;
            
            if (tienePlaywright) {
                this.resultados.push({
                    nombre: 'Playwright Instalado',
                    estado: true,
                    mensaje: `Versión ${tienePlaywright} encontrada`,
                    solucion: null
                });
                console.log('✅ Playwright está instalado');
            } else {
                this.resultados.push({
                    nombre: 'Playwright Instalado',
                    estado: false,
                    mensaje: 'No encontrado en package.json',
                    solucion: 'Ejecuta: npm install playwright'
                });
                console.log('❌ Playwright no encontrado');
            }
        } catch (error) {
            this.resultados.push({
                nombre: 'Playwright Instalado',
                estado: false,
                mensaje: 'Error verificando package.json',
                solucion: 'Verifica que estés en el directorio correcto del proyecto'
            });
            console.log('❌ Error verificando Playwright');
        }
    }

    async verificarPowerShell() {
        console.log('🔍 Verificando PowerShell...');
        
        try {
            const resultado = await this.ejecutarComando('powershell', ['-Command', 'Get-Host | Select-Object Version']);
            
            if (resultado.includes('Version')) {
                this.resultados.push({
                    nombre: 'PowerShell Disponible',
                    estado: true,
                    mensaje: 'PowerShell funciona correctamente',
                    solucion: null
                });
                console.log('✅ PowerShell disponible');
            } else {
                throw new Error('PowerShell no responde correctamente');
            }
        } catch (error) {
            this.resultados.push({
                nombre: 'PowerShell Disponible',
                estado: false,
                mensaje: 'PowerShell no funciona',
                solucion: 'Instala PowerShell o verifica la ruta del sistema'
            });
            console.log('❌ PowerShell no disponible');
        }
    }

    async verificarPermisos() {
        console.log('🔍 Verificando permisos de PowerShell...');
        
        try {
            const resultado = await this.ejecutarComando('powershell', ['-Command', 'Get-ExecutionPolicy']);
            
            const politica = resultado.trim();
            const permitido = ['RemoteSigned', 'Unrestricted', 'Bypass'].includes(politica);
            
            if (permitido) {
                this.resultados.push({
                    nombre: 'Permisos PowerShell',
                    estado: true,
                    mensaje: `Política actual: ${politica}`,
                    solucion: null
                });
                console.log(`✅ Permisos OK: ${politica}`);
            } else {
                this.resultados.push({
                    nombre: 'Permisos PowerShell',
                    estado: false,
                    mensaje: `Política restrictiva: ${politica}`,
                    solucion: 'Ejecuta como administrador: Set-ExecutionPolicy RemoteSigned'
                });
                console.log(`❌ Permisos restrictivos: ${politica}`);
            }
        } catch (error) {
            this.resultados.push({
                nombre: 'Permisos PowerShell',
                estado: false,
                mensaje: 'Error verificando permisos',
                solucion: 'Ejecuta PowerShell como administrador'
            });
            console.log('❌ Error verificando permisos');
        }
    }

    async verificarFirefoxProceso() {
        console.log('🔍 Verificando proceso de Firefox...');
        
        try {
            const resultado = await this.ejecutarComando('powershell', [
                '-Command', 
                'Get-Process | Where-Object { $_.ProcessName -like "*firefox*" -and $_.MainWindowTitle -ne "" } | Select-Object ProcessName, MainWindowTitle'
            ]);
            
            if (resultado.includes('firefox') || resultado.includes('Firefox')) {
                this.resultados.push({
                    nombre: 'Firefox Ejecutándose',
                    estado: true,
                    mensaje: 'Firefox detectado en el sistema',
                    solucion: null
                });
                console.log('✅ Firefox está ejecutándose');
            } else {
                this.resultados.push({
                    nombre: 'Firefox Ejecutándose',
                    estado: false,
                    mensaje: 'No se detectó Firefox ejecutándose',
                    solucion: 'Abre Firefox manualmente o usa el comando "abrir" del detector'
                });
                console.log('❌ Firefox no está ejecutándose');
            }
        } catch (error) {
            this.resultados.push({
                nombre: 'Firefox Ejecutándose',
                estado: false,
                mensaje: 'Error verificando procesos',
                solucion: 'Verifica que Firefox esté instalado'
            });
            console.log('❌ Error verificando Firefox');
        }
    }

    async verificarFirefoxPlaywright() {
        console.log('🔍 Verificando Firefox de Playwright...');
        
        try {
            this.navegador = await firefox.launch({
                headless: false,
                args: ['--width=800', '--height=600']
            });
            
            const contexto = await this.navegador.newContext();
            this.pagina = await contexto.newPage();
            
            await this.pagina.goto('data:text/html,<h1>Test Firefox Playwright</h1><button id="testBtn">Click Me</button>');
            await this.pagina.waitForSelector('#testBtn', { timeout: 5000 });
            
            this.resultados.push({
                nombre: 'Firefox Playwright',
                estado: true,
                mensaje: 'Firefox de Playwright funciona correctamente',
                solucion: null
            });
            console.log('✅ Firefox Playwright OK');
            
            await this.navegador.close();
            this.navegador = null;
            
        } catch (error) {
            this.resultados.push({
                nombre: 'Firefox Playwright',
                estado: false,
                mensaje: `Error: ${error.message}`,
                solucion: 'Ejecuta: npx playwright install firefox'
            });
            console.log(`❌ Firefox Playwright falla: ${error.message}`);
            
            if (this.navegador) {
                try {
                    await this.navegador.close();
                } catch (e) { /* ignorar */ }
            }
        }
    }

    async verificarSelectores() {
        console.log('🔍 Verificando selectores de Lightning Roulette...');
        
        const selectoresTest = [
            '.roulette-number',
            '.betting-spot',
            '[data-number]',
            '.number-cell',
            'button[data-number]'
        ];
        
        // Simular una página básica con elementos de ruleta
        const htmlTest = `
        <html>
        <body>
            <div class="roulette-number" data-number="1">1</div>
            <div class="roulette-number" data-number="2">2</div>
            <button class="betting-spot" data-number="3">3</button>
            <div class="number-cell">4</div>
        </body>
        </html>
        `;
        
        try {
            this.navegador = await firefox.launch({ headless: true });
            const contexto = await this.navegador.newContext();
            this.pagina = await contexto.newPage();
            
            await this.pagina.setContent(htmlTest);
            
            let selectoresEncontrados = 0;
            
            for (const selector of selectoresTest) {
                try {
                    const elementos = await this.pagina.$$(selector);
                    if (elementos.length > 0) {
                        selectoresEncontrados++;
                    }
                } catch (e) {
                    // Selector no válido
                }
            }
            
            await this.navegador.close();
            
            const porcentaje = Math.round((selectoresEncontrados / selectoresTest.length) * 100);
            
            if (porcentaje >= 60) {
                this.resultados.push({
                    nombre: 'Selectores CSS',
                    estado: true,
                    mensaje: `${selectoresEncontrados}/${selectoresTest.length} selectores funcionan (${porcentaje}%)`,
                    solucion: null
                });
                console.log(`✅ Selectores CSS: ${porcentaje}% funcionan`);
            } else {
                this.resultados.push({
                    nombre: 'Selectores CSS',
                    estado: false,
                    mensaje: `Solo ${selectoresEncontrados}/${selectoresTest.length} selectores funcionan (${porcentaje}%)`,
                    solucion: 'Los selectores pueden necesitar actualización para el sitio específico'
                });
                console.log(`❌ Selectores CSS: solo ${porcentaje}% funcionan`);
            }
            
        } catch (error) {
            this.resultados.push({
                nombre: 'Selectores CSS',
                estado: false,
                mensaje: 'Error verificando selectores',
                solucion: 'Problema con el navegador de prueba'
            });
            console.log('❌ Error verificando selectores');
        }
    }

    async verificarHooks() {
        console.log('🔍 Verificando capacidad de hooks de mouse...');
        
        const scriptTest = `
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    
    public class HookTest {
        [DllImport("user32.dll")]
        public static extern IntPtr GetForegroundWindow();
        
        [DllImport("user32.dll")]
        public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
        
        [StructLayout(LayoutKind.Sequential)]
        public struct RECT {
            public int Left; public int Top; public int Right; public int Bottom;
        }
    }
"@

try {
    $window = [HookTest]::GetForegroundWindow()
    $rect = New-Object HookTest+RECT
    $result = [HookTest]::GetWindowRect($window, [ref]$rect)
    
    if ($result) {
        Write-Host "HOOK_TEST_SUCCESS"
    } else {
        Write-Host "HOOK_TEST_FAILED"
    }
} catch {
    Write-Host "HOOK_TEST_ERROR: $($_.Exception.Message)"
}
`;

        try {
            await fs.writeFile('test_hooks.ps1', scriptTest);
            const resultado = await this.ejecutarComando('powershell', ['-ExecutionPolicy', 'Bypass', '-File', 'test_hooks.ps1']);
            
            if (resultado.includes('HOOK_TEST_SUCCESS')) {
                this.resultados.push({
                    nombre: 'Hooks de Mouse',
                    estado: true,
                    mensaje: 'Hooks de sistema funcionan correctamente',
                    solucion: null
                });
                console.log('✅ Hooks de mouse OK');
            } else {
                this.resultados.push({
                    nombre: 'Hooks de Mouse',
                    estado: false,
                    mensaje: 'Hooks de sistema no funcionan',
                    solucion: 'Ejecuta como administrador o verifica permisos de seguridad'
                });
                console.log('❌ Hooks de mouse fallan');
            }
            
            await fs.unlink('test_hooks.ps1');
            
        } catch (error) {
            this.resultados.push({
                nombre: 'Hooks de Mouse',
                estado: false,
                mensaje: 'Error probando hooks',
                solucion: 'Problema con permisos del sistema o antivirus'
            });
            console.log('❌ Error probando hooks');
        }
    }

    async ejecutarComando(comando, args) {
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
                if (codigo === 0) {
                    resolve(salida);
                } else {
                    reject(new Error(error || `Código de salida: ${codigo}`));
                }
            });

            setTimeout(() => {
                proceso.kill();
                reject(new Error('Timeout'));
            }, 10000);
        });
    }
}

// Función principal
async function ejecutarDiagnostico() {
    const diagnostico = new DiagnosticoFirefox();
    await diagnostico.ejecutarDiagnostico();
}

// Ejecutar si se llama directamente
if (require.main === module) {
    ejecutarDiagnostico().catch(console.error);
}

module.exports = { DiagnosticoFirefox, ejecutarDiagnostico }; 