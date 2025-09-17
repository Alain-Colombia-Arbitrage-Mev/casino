const { spawn } = require('child_process');
const fs = require('fs').promises;

class ClickerAdaptativo {
    constructor() {
        this.ventanaJuego = null;
        this.coordenadasRelativas = [];
        this.configuracion = {
            precision: 0.95,
            recalibrarAutomatico: true,
            verificarVentana: true
        };
    }

    async init() {
        console.log('🎯 CLICKER ADAPTATIVO CON COORDENADAS RELATIVAS');
        console.log('='.repeat(55));
        console.log('📐 Se ajusta automáticamente al tamaño de ventana');
        console.log('🔄 Recalibra cuando detecta cambios');
        console.log('🎯 Compatible con grabador físico');
        console.log('');
        
        await this.cargarCoordenadasExistentes();
        await this.modoInteractivo();
    }

    async cargarCoordenadasExistentes() {
        try {
            // Intentar cargar coordenadas de Firefox integrado primero
            const datos = await fs.readFile('coordenadas_firefox_integrado.json', 'utf8');
            const coordenadas = JSON.parse(datos);
            
            // Convertir formato de Firefox integrado
            this.ventanaJuego = {
                x: 0,
                y: 0,
                width: coordenadas.dimensiones.width,
                height: coordenadas.dimensiones.height,
                navegador: 'firefox_integrado',
                modoIncognito: coordenadas.modoIncognito
            };
            this.coordenadasRelativas = coordenadas.elementos;
            
            console.log('📁 ✅ Coordenadas de Firefox integrado cargadas');
            console.log(`   🦊 ${this.coordenadasRelativas.length} elementos cargados`);
            console.log(`   📐 Dimensiones: ${coordenadas.dimensiones.width} x ${coordenadas.dimensiones.height}`);
            console.log(`   🔒 Modo incógnito: ${coordenadas.modoIncognito ? 'Activo' : 'Inactivo'}`);
            
                            // Mostrar estadísticas por método
                const auto = this.coordenadasRelativas.filter(e => e.metodo === 'firefox_integrado').length;
                const manual = this.coordenadasRelativas.filter(e => e.metodo === 'manual_firefox').length;
                if (auto > 0 || manual > 0) {
                    console.log(`   🤖 Firefox auto: ${auto} | 👆 Firefox manual: ${manual}`);
                }
            } catch {
                try {
                    // Intentar cargar coordenadas del navegador integrado (Chromium)
                    const datos = await fs.readFile('coordenadas_navegador_integrado.json', 'utf8');
                    const coordenadas = JSON.parse(datos);
                    
                    // Convertir formato de navegador integrado
                    this.ventanaJuego = {
                        x: 0,
                        y: 0,
                        width: coordenadas.dimensiones.width,
                        height: coordenadas.dimensiones.height,
                        navegador: 'chromium_integrado'
                    };
                    this.coordenadasRelativas = coordenadas.elementos;
                    
                    console.log('📁 ✅ Coordenadas del navegador integrado (Chromium) cargadas');
                    console.log(`   🎯 ${this.coordenadasRelativas.length} elementos cargados`);
                    console.log(`   📐 Dimensiones: ${coordenadas.dimensiones.width} x ${coordenadas.dimensiones.height}`);
                    
                    // Mostrar estadísticas por método
                    const auto = this.coordenadasRelativas.filter(e => e.metodo === 'navegador_integrado').length;
                    const manual = this.coordenadasRelativas.filter(e => e.metodo === 'manual_navegador').length;
                    if (auto > 0 || manual > 0) {
                        console.log(`   🤖 Navegador auto: ${auto} | 👆 Navegador manual: ${manual}`);
                    }
                } catch {
            try {
                // Intentar cargar coordenadas híbridas
                const datos = await fs.readFile('coordenadas_hibridas.json', 'utf8');
                const coordenadas = JSON.parse(datos);
                
                this.ventanaJuego = coordenadas.ventana;
                this.coordenadasRelativas = coordenadas.elementos;
                
                console.log('📁 ✅ Coordenadas híbridas cargadas (auto + manual)');
                console.log(`   🎯 ${this.coordenadasRelativas.length} elementos cargados`);
                
                // Mostrar estadísticas por método
                const auto = this.coordenadasRelativas.filter(e => e.metodo === 'ocr').length;
                const manual = this.coordenadasRelativas.filter(e => e.metodo === 'manual').length;
                if (auto > 0 || manual > 0) {
                    console.log(`   🤖 Automático: ${auto} | 👆 Manual: ${manual}`);
                }
            } catch {
                try {
                    // Intentar cargar coordenadas del detector automático
                    const datos = await fs.readFile('coordenadas_relativas.json', 'utf8');
                    const coordenadas = JSON.parse(datos);
                    
                    this.ventanaJuego = coordenadas.ventana;
                    this.coordenadasRelativas = coordenadas.elementos;
                    
                    console.log('📁 ✅ Coordenadas relativas cargadas desde detector automático');
                    console.log(`   🎯 ${this.coordenadasRelativas.length} elementos cargados`);
                } catch {
                    try {
                        // Intentar cargar desde grabador físico y convertir
                        const datos = await fs.readFile('clicks_fisicos.json', 'utf8');
                        const clicks = JSON.parse(datos);
                        
                        console.log('📁 ⚠️ Coordenadas absolutas encontradas, convirtiendo...');
                        await this.convertirCoordenadasAbsolutas(clicks.clicks);
                    } catch {
                        console.log('📁 ⚠️ No se encontraron coordenadas existentes');
                        console.log('💡 Usa detector híbrido, automático o grabador físico primero');
                    }
                }
            }
        }
    }

    async convertirCoordenadasAbsolutas(clicks) {
        console.log('\n🔄 CONVIRTIENDO COORDENADAS ABSOLUTAS A RELATIVAS...');
        
        // Detectar ventana actual para convertir
        await this.detectarVentanaActual();
        
        if (!this.ventanaJuego) {
            console.log('❌ No se pudo detectar ventana para conversión');
            return;
        }
        
        this.coordenadasRelativas = clicks.map(click => ({
            tipo: click.tipo || 'numero',
            valor: click.numero || click.valor || click.nombre,
            coordenadas: {
                relativas: {
                    x: (click.x - this.ventanaJuego.x) / this.ventanaJuego.width,
                    y: (click.y - this.ventanaJuego.y) / this.ventanaJuego.height
                },
                absolutas: { x: click.x, y: click.y }
            }
        }));
        
        console.log(`✅ ${this.coordenadasRelativas.length} coordenadas convertidas a relativas`);
        await this.guardarCoordenadasRelativas();
    }

    async detectarVentanaActual() {
        console.log('🔍 Detectando ventana del navegador...');
        
        const script = `
Add-Type -AssemblyName System.Windows.Forms

$browsers = @("chrome", "firefox", "msedge", "opera")
$ventanaEncontrada = $false

foreach ($browser in $browsers) {
    try {
        $process = Get-Process -Name $browser -ErrorAction Stop | Select-Object -First 1
        
        Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            public class Win32Window {
                [DllImport("user32.dll")]
                public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
                
                [StructLayout(LayoutKind.Sequential)]
                public struct RECT {
                    public int Left; public int Top; public int Right; public int Bottom;
                }
            }
"@
        
        $rect = New-Object Win32Window+RECT
        $result = [Win32Window]::GetWindowRect($process.MainWindowHandle, [ref]$rect)
        
        if ($result) {
            Write-Host "WINDOW_FOUND: $browser,$($rect.Left),$($rect.Top),$($rect.Right - $rect.Left),$($rect.Bottom - $rect.Top)"
            $ventanaEncontrada = $true
            break
        }
    } catch {
        # Continuar con siguiente navegador
    }
}

if (-not $ventanaEncontrada) {
    Write-Host "WINDOW_ERROR: No se encontró navegador"
}
`;

        try {
            await fs.writeFile('detectar_ventana.ps1', script);
            const resultado = await this.ejecutarScript('detectar_ventana.ps1');
            
            const lineas = resultado.split('\n');
            for (const linea of lineas) {
                if (linea.includes('WINDOW_FOUND:')) {
                    const datos = linea.split('WINDOW_FOUND: ')[1].split(',');
                    this.ventanaJuego = {
                        navegador: datos[0],
                        x: parseInt(datos[1]),
                        y: parseInt(datos[2]),
                        width: parseInt(datos[3]),
                        height: parseInt(datos[4])
                    };
                    
                    console.log(`✅ Ventana detectada: ${this.ventanaJuego.navegador}`);
                    console.log(`   📐 ${this.ventanaJuego.width} x ${this.ventanaJuego.height}`);
                    return;
                }
            }
            
            console.log('❌ No se pudo detectar ventana del navegador');
        } catch (error) {
            console.log(`❌ Error detectando ventana: ${error.message}`);
        }
    }

    async modoInteractivo() {
        console.log('\n🎯 CLICKER ADAPTATIVO INICIADO');
        console.log('='.repeat(35));
        console.log('📋 Comandos disponibles:');
        console.log('   - "estado" - 📊 Ver coordenadas cargadas');
        console.log('   - "calibrar" - 🔄 Recalibrar ventana actual');
        console.log('   - "click" - 🎯 Ejecutar clicks adaptativos');
        console.log('   - "verificar" - 🔍 Verificar coordenadas actuales');
        console.log('   - "exportar" - 💾 Exportar clicks para grabador físico');
        console.log('   - "ayuda" - ❓ Mostrar ayuda detallada');
        console.log('   - "salir" - 👋 Cerrar clicker');
        console.log('');

        let continuar = true;
        while (continuar) {
            const comando = await this.preguntarSimple('🎯 ¿Qué quieres hacer? ');
            const input = comando.trim().toLowerCase();

            switch (input) {
                case 'estado':
                case 'status':
                    this.mostrarEstado();
                    break;

                case 'calibrar':
                case 'recalibrar':
                    await this.recalibrarVentana();
                    break;

                case 'click':
                case 'ejecutar':
                    await this.ejecutarClicksAdaptativos();
                    break;

                case 'verificar':
                case 'check':
                    await this.verificarCoordenadas();
                    break;

                case 'exportar':
                case 'export':
                    await this.exportarClicksFisicos();
                    break;

                case 'ayuda':
                case 'help':
                    this.mostrarAyuda();
                    break;

                case 'salir':
                case 'exit':
                    console.log('👋 Cerrando clicker adaptativo...');
                    continuar = false;
                    break;

                default:
                    console.log('❌ Comando no reconocido');
                    console.log('💡 Escribe "ayuda" para ver todos los comandos');
            }

            if (continuar) {
                console.log('');
            }
        }
    }

    mostrarEstado() {
        console.log('\n📊 ESTADO DEL CLICKER ADAPTATIVO:');
        console.log('='.repeat(45));
        
        if (this.ventanaJuego) {
            console.log('🖥️ VENTANA ACTUAL:');
            console.log(`   🌐 Navegador: ${this.ventanaJuego.navegador || 'Detectado'}`);
            console.log(`   📍 Posición: (${this.ventanaJuego.x}, ${this.ventanaJuego.y})`);
            console.log(`   📐 Tamaño: ${this.ventanaJuego.width} x ${this.ventanaJuego.height}`);
        } else {
            console.log('❌ No hay ventana detectada');
        }
        
        console.log(`\n🎯 COORDENADAS CARGADAS: ${this.coordenadasRelativas.length}`);
        
        if (this.coordenadasRelativas.length > 0) {
            // Agrupar por tipo
            const grupos = {};
            this.coordenadasRelativas.forEach(coord => {
                const tipo = coord.tipo || 'numero';
                if (!grupos[tipo]) grupos[tipo] = [];
                grupos[tipo].push(coord);
            });
            
            Object.keys(grupos).forEach(tipo => {
                const emoji = {
                    numero: '📊',
                    rango: '🎯',
                    color: '🎨',
                    columna: '📋',
                    docena: '📦'
                }[tipo] || '📍';
                
                console.log(`   ${emoji} ${tipo}: ${grupos[tipo].length} elemento${grupos[tipo].length > 1 ? 's' : ''}`);
                
                // Mostrar algunos ejemplos
                grupos[tipo].slice(0, 3).forEach(coord => {
                    const valor = coord.valor || coord.texto;
                    const rel = coord.coordenadas.relativas;
                    console.log(`      - ${valor}: (${rel.x.toFixed(3)}, ${rel.y.toFixed(3)})`);
                });
                
                if (grupos[tipo].length > 3) {
                    console.log(`      ... y ${grupos[tipo].length - 3} más`);
                }
            });
        }
    }

    async recalibrarVentana() {
        console.log('\n🔄 RECALIBRANDO VENTANA...');
        console.log('='.repeat(30));
        
        const ventanaAnterior = this.ventanaJuego ? { ...this.ventanaJuego } : null;
        
        await this.detectarVentanaActual();
        
        if (!this.ventanaJuego) {
            console.log('❌ No se pudo detectar ventana para recalibrar');
            return;
        }
        
        if (ventanaAnterior) {
            console.log('\n📊 COMPARACIÓN DE VENTANAS:');
            console.log(`   📐 Anterior: ${ventanaAnterior.width} x ${ventanaAnterior.height}`);
            console.log(`   📐 Actual: ${this.ventanaJuego.width} x ${this.ventanaJuego.height}`);
            
            const cambioTamaño = (
                ventanaAnterior.width !== this.ventanaJuego.width ||
                ventanaAnterior.height !== this.ventanaJuego.height
            );
            
            const cambioPosicion = (
                ventanaAnterior.x !== this.ventanaJuego.x ||
                ventanaAnterior.y !== this.ventanaJuego.y
            );
            
            if (cambioTamaño) {
                console.log('🔄 ✅ Cambio de tamaño detectado - Coordenadas se adaptarán automáticamente');
            }
            
            if (cambioPosicion) {
                console.log('📍 ✅ Cambio de posición detectado - Coordenadas se adaptarán automáticamente');
            }
            
            if (!cambioTamaño && !cambioPosicion) {
                console.log('✅ No se detectaron cambios significativos');
            }
        }
        
        await this.guardarCoordenadasRelativas();
        console.log('💾 Configuración actualizada');
    }

    async ejecutarClicksAdaptativos() {
        if (this.coordenadasRelativas.length === 0) {
            console.log('❌ No hay coordenadas cargadas');
            console.log('💡 Usa detector automático o carga coordenadas existentes');
            return;
        }
        
        // Verificar ventana actual
        await this.detectarVentanaActual();
        
        if (!this.ventanaJuego) {
            console.log('❌ No se pudo detectar ventana del navegador');
            return;
        }
        
        console.log('\n🚀 EJECUTANDO CLICKS ADAPTATIVOS...');
        console.log('='.repeat(40));
        console.log(`🎯 ${this.coordenadasRelativas.length} clicks programados`);
        console.log('📐 Coordenadas se calculan automáticamente');
        console.log('⚠️ NO MUEVAS EL MOUSE durante la ejecución');
        console.log('');
        
        // Countdown
        for (let i = 3; i > 0; i--) {
            console.log(`⏰ Iniciando en ${i}...`);
            await this.esperar(1000);
        }
        
        let clicksExitosos = 0;
        const tiempoInicio = Date.now();
        
        for (const coordenada of this.coordenadasRelativas) {
            try {
                // Calcular coordenadas absolutas actuales
                const rel = coordenada.coordenadas.relativas;
                const x = Math.round(this.ventanaJuego.x + (rel.x * this.ventanaJuego.width));
                const y = Math.round(this.ventanaJuego.y + (rel.y * this.ventanaJuego.height));
                
                const valor = coordenada.valor || coordenada.texto;
                console.log(`🎯 Clicking ${valor} en (${x}, ${y}) [Rel: ${rel.x.toFixed(3)}, ${rel.y.toFixed(3)}]`);
                
                await this.ejecutarClickFisico(x, y);
                clicksExitosos++;
                
                // Pausa humana variable
                const pausa = Math.random() * 800 + 500;
                console.log(`⏳ Esperando ${Math.round(pausa)}ms...`);
                await this.esperar(pausa);
                
            } catch (error) {
                const valor = coordenada.valor || coordenada.texto;
                console.log(`❌ Error en click ${valor}: ${error.message}`);
            }
        }
        
        const tiempoTotal = Date.now() - tiempoInicio;
        
        console.log('\n📊 RESUMEN DE EJECUCIÓN ADAPTATIVA:');
        console.log('='.repeat(45));
        console.log(`✅ Clicks exitosos: ${clicksExitosos}`);
        console.log(`❌ Clicks fallidos: ${this.coordenadasRelativas.length - clicksExitosos}`);
        console.log(`⏱️ Tiempo total: ${(tiempoTotal / 1000).toFixed(1)}s`);
        console.log(`🎯 Método: Coordenadas relativas adaptativas`);
        console.log(`📐 Ventana: ${this.ventanaJuego.width} x ${this.ventanaJuego.height}`);
    }

    async verificarCoordenadas() {
        if (this.coordenadasRelativas.length === 0) {
            console.log('❌ No hay coordenadas para verificar');
            return;
        }
        
        await this.detectarVentanaActual();
        
        if (!this.ventanaJuego) {
            console.log('❌ No se pudo detectar ventana para verificación');
            return;
        }
        
        console.log('\n🔍 VERIFICANDO COORDENADAS ACTUALES...');
        console.log('='.repeat(40));
        
        console.log('📐 COORDENADAS CONVERTIDAS A ABSOLUTAS:');
        this.coordenadasRelativas.forEach((coord, i) => {
            const rel = coord.coordenadas.relativas;
            const x = Math.round(this.ventanaJuego.x + (rel.x * this.ventanaJuego.width));
            const y = Math.round(this.ventanaJuego.y + (rel.y * this.ventanaJuego.height));
            
            const valor = coord.valor || coord.texto;
            console.log(`   ${i + 1}. ${valor}: (${x}, ${y}) <- Rel: (${rel.x.toFixed(3)}, ${rel.y.toFixed(3)})`);
        });
    }

    async exportarClicksFisicos() {
        if (this.coordenadasRelativas.length === 0) {
            console.log('❌ No hay coordenadas para exportar');
            return;
        }
        
        await this.detectarVentanaActual();
        
        if (!this.ventanaJuego) {
            console.log('❌ No se pudo detectar ventana para exportar');
            return;
        }
        
        // Convertir a formato de grabador físico
        const clicksFisicos = this.coordenadasRelativas.map(coord => {
            const rel = coord.coordenadas.relativas;
            const x = Math.round(this.ventanaJuego.x + (rel.x * this.ventanaJuego.width));
            const y = Math.round(this.ventanaJuego.y + (rel.y * this.ventanaJuego.height));
            
            return {
                id: coord.tipo === 'numero' ? `num_${coord.valor}` : `bet_${coord.valor}`,
                tipo: coord.tipo,
                nombre: coord.valor?.toString() || coord.texto,
                valor: coord.valor,
                x: x,
                y: y,
                timestamp: Date.now(),
                metodo: 'adaptativo_exportado',
                coordenadasOriginales: coord.coordenadas
            };
        });
        
        const datos = {
            clicks: clicksFisicos,
            metadata: {
                fechaCreacion: new Date().toISOString(),
                totalClicks: clicksFisicos.length,
                metodo: 'adaptativo_exportado',
                ventana: this.ventanaJuego,
                sistema: process.platform,
                version: '1.0_adaptativo'
            }
        };
        
        try {
            await fs.writeFile('clicks_fisicos_adaptativo.json', JSON.stringify(datos, null, 2));
            console.log('\n💾 ✅ Clicks exportados para grabador físico:');
            console.log('   📁 clicks_fisicos_adaptativo.json');
            console.log(`   🎯 ${clicksFisicos.length} clicks listos para usar`);
            console.log('');
            console.log('💡 Puedes cargar estos clicks en el grabador físico');
        } catch (error) {
            console.log(`❌ Error exportando: ${error.message}`);
        }
    }

    async ejecutarClickFisico(x, y) {
        const script = `
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    public class MouseClick {
        [DllImport("user32.dll")]
        public static extern bool SetCursorPos(int x, int y);
        
        [DllImport("user32.dll")]
        public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
        
        public const uint MOUSEEVENTF_LEFTDOWN = 0x02;
        public const uint MOUSEEVENTF_LEFTUP = 0x04;
    }
"@

try {
    [MouseClick]::SetCursorPos(${x}, ${y})
    Start-Sleep -Milliseconds 50
    [MouseClick]::mouse_event([MouseClick]::MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    Start-Sleep -Milliseconds 100
    [MouseClick]::mouse_event([MouseClick]::MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    Write-Host "CLICK_SUCCESS: ${x},${y}"
} catch {
    Write-Host "CLICK_ERROR: $($_.Exception.Message)"
}
`;

        await fs.writeFile('click_temp.ps1', script);
        return this.ejecutarScript('click_temp.ps1');
    }

    async guardarCoordenadasRelativas() {
        const datos = {
            timestamp: new Date().toISOString(),
            ventana: this.ventanaJuego,
            elementos: this.coordenadasRelativas
        };
        
        try {
            await fs.writeFile('coordenadas_adaptativas.json', JSON.stringify(datos, null, 2));
        } catch (error) {
            console.log(`⚠️ Error guardando configuración: ${error.message}`);
        }
    }

    mostrarAyuda() {
        console.log('\n❓ AYUDA - CLICKER ADAPTATIVO');
        console.log('='.repeat(40));
        console.log('');
        console.log('🎯 CARACTERÍSTICAS:');
        console.log('   - Usa coordenadas relativas que se adaptan al tamaño');
        console.log('   - Se recalibra automáticamente cuando cambia la ventana');
        console.log('   - Compatible con detector automático y grabador físico');
        console.log('');
        console.log('📐 COORDENADAS RELATIVAS:');
        console.log('   - 0.0 = Borde izquierdo/superior de la ventana');
        console.log('   - 1.0 = Borde derecho/inferior de la ventana');
        console.log('   - 0.5 = Centro de la ventana');
        console.log('   - Se mantienen válidas aunque cambies el tamaño');
        console.log('');
        console.log('🔄 FLUJO DE USO:');
        console.log('   1. Usa "detector automático" para encontrar números');
        console.log('   2. O usa "grabador físico" para grabar manualmente');
        console.log('   3. Carga este clicker adaptativo');
        console.log('   4. Los clicks se ajustan automáticamente');
        console.log('');
        console.log('💡 VENTAJAS:');
        console.log('   - Funciona aunque cambies tamaño de navegador');
        console.log('   - Se adapta a diferentes resoluciones');
        console.log('   - Coordenadas más precisas y confiables');
    }

    async ejecutarScript(nombreScript) {
        return new Promise((resolve, reject) => {
            const proceso = spawn('powershell', ['-ExecutionPolicy', 'Bypass', '-File', nombreScript]);
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

    esperar(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    preguntarSimple(pregunta) {
        return new Promise((resolve) => {
            const readline = require('readline');
            const rl = readline.createInterface({
                input: process.stdin,
                output: process.stdout
            });
            
            rl.question(pregunta, (respuesta) => {
                rl.close();
                resolve(respuesta);
            });
        });
    }
}

// Función principal
async function iniciarClickerAdaptativo() {
    const clicker = new ClickerAdaptativo();
    
    try {
        await clicker.init();
    } catch (error) {
        console.error(`❌ Error: ${error.message}`);
    }
}

// Ejecutar si se llama directamente
if (require.main === module) {
    iniciarClickerAdaptativo();
}

module.exports = { ClickerAdaptativo, iniciarClickerAdaptativo }; 