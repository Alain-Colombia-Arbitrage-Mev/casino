const { firefox } = require('playwright');
const fs = require('fs').promises;

// Variable global para evitar múltiples instancias
let instanciaGlobal = null;

class DetectorFirefoxIntegrado {
    constructor() {
        // Singleton pattern para evitar múltiples instancias
        if (instanciaGlobal) {
            console.log('⚠️ Ya hay una instancia del detector Firefox ejecutándose');
            return instanciaGlobal;
        }
        
        this.navegador = null;
        this.contexto = null;
        this.pagina = null;
        this.numerosDetectados = [];
        this.estaConectado = false;
        this.dimensionesVentana = { width: 1280, height: 720 };
        this.modoIncognito = true; // Por defecto modo incógnito
        this.estaInicializando = false; // Flag para evitar múltiples inicializaciones
        
        instanciaGlobal = this;
    }

    async init() {
        console.log('🦊 DETECTOR FIREFOX INTEGRADO CON MODO INCÓGNITO');
        console.log('='.repeat(55));
        console.log('🔒 Navegación privada por defecto');
        console.log('🦊 Optimizado específicamente para Firefox');
        console.log('🎯 Abre Lightning Roulette automáticamente');
        console.log('📐 Coordenadas relativas adaptables');
        console.log('🎮 Control total del navegador');
        console.log('');
        
        await this.modoInteractivo();
    }

    async modoInteractivo() {
        console.log('\n🦊 DETECTOR FIREFOX INTEGRADO');
        console.log('='.repeat(35));
        console.log('📋 Comandos disponibles:');
        console.log('   - "abrir" - 🦊 Abrir Firefox con Lightning Roulette');
        console.log('   - "detectar" - 🔍 Detectar números automáticamente');
        console.log('   - "manual" - 👆 Grabar clicks a nivel sistema');
        console.log('   - "hotkeys" - ⌨️ Grabar con control de teclas (S=empezar, E=terminar)');
        console.log('   - "navegador" - 🖱️ Grabar clicks en navegador');
        console.log('   - "hibrido" - 🔄 Detección automática + manual');
        console.log('   - "coordenadas" - 📊 Ver coordenadas detectadas');
        console.log('   - "limpiar" - 🧹 Borrar todos los registros');
        console.log('   - "selectivo" - 🎯 Borrar registros específicos');
        console.log('   - "clicks" - 🎯 Ejecutar clicks en navegador');
        console.log('   - "exportar" - 💾 Exportar coordenadas');
        console.log('   - "configurar" - ⚙️ Configurar navegador');
        console.log('   - "incognito" - 🔒 Alternar modo incógnito');
        console.log('   - "diagnostico" - 🔍 Diagnóstico de problemas');
        console.log('   - "cerrar" - 🚪 Cerrar navegador');
        console.log('   - "salir" - 👋 Salir del programa');
        console.log('');

        let continuar = true;
        while (continuar) {
            const estadoIncognito = this.modoIncognito ? '🔒' : '🌐';
            const comando = await this.preguntarSimple(`🦊 ${estadoIncognito} ¿Qué quieres hacer? `);
            const input = comando.trim().toLowerCase();

            switch (input) {
                case 'abrir':
                case 'open':
                    await this.abrirFirefox();
                    break;

                case 'detectar':
                case 'auto':
                    await this.deteccionAutomatica();
                    break;

                case 'manual':
                case 'sistema':
                    await this.grabacionManual();
                    break;

                case 'hotkeys':
                case 'controlado':
                    await this.grabacionConHotkeys();
                    break;

                case 'navegador':
                case 'grabar':
                    await this.grabacionManual();
                    break;

                case 'hibrido':
                case 'combinar':
                    await this.modoHibrido();
                    break;

                case 'coordenadas':
                case 'coords':
                    this.mostrarCoordenadasDetectadas();
                    break;

                case 'limpiar':
                case 'borrar':
                case 'reset':
                    await this.limpiarRegistros();
                    break;

                case 'selectivo':
                case 'parcial':
                    await this.limpiarSelectivo();
                    break;

                case 'clicks':
                case 'ejecutar':
                    await this.ejecutarClicksEnNavegador();
                    break;

                case 'exportar':
                case 'export':
                    await this.exportarCoordenadasRelativas();
                    break;

                case 'configurar':
                case 'config':
                    await this.configurarNavegador();
                    break;

                case 'incognito':
                case 'privado':
                    this.alternarModoIncognito();
                    break;

                case 'diagnostico':
                case 'debug':
                    await this.ejecutarDiagnostico();
                    break;

                case 'cerrar':
                case 'close':
                    await this.cerrarNavegador();
                    break;

                case 'salir':
                case 'exit':
                    await this.cerrarNavegador();
                    console.log('👋 Cerrando detector Firefox integrado...');
                    instanciaGlobal = null; // Limpiar instancia global
                    continuar = false;
                    break;

                default:
                    console.log('❌ Comando no reconocido');
                    console.log('💡 Usa: abrir, detectar, manual, hotkeys, hibrido, coordenadas, limpiar, selectivo, clicks, exportar, incognito, cerrar, salir');
            }

            if (continuar) {
                console.log('');
            }
        }
    }

    async abrirFirefox() {
        if (this.navegador) {
            console.log('⚠️ Firefox ya está abierto');
            return;
        }

        if (this.estaInicializando) {
            console.log('⚠️ Firefox ya se está abriendo, espera...');
            return;
        }

        this.estaInicializando = true;

        console.log('\n🦊 ABRIENDO FIREFOX INTEGRADO...');
        console.log('='.repeat(35));
        
        try {
            const modoTexto = this.modoIncognito ? '🔒 MODO INCÓGNITO' : '🌐 MODO NORMAL';
            console.log(`🚀 Iniciando Firefox en ${modoTexto}...`);
            
            // Configuración SOLO para Firefox de Playwright (no del sistema)
            const opcionesFirefox = {
                headless: false,
                // NO especificar executablePath para usar Firefox de Playwright
                args: [
                    // Solo argumentos compatibles con Firefox de Playwright
                    '--width=' + this.dimensionesVentana.width,
                    '--height=' + this.dimensionesVentana.height
                ]
            };

            // Modo incógnito se maneja en el contexto, no en args
            console.log('🦊 Usando Firefox integrado de Playwright (no del sistema)');
            this.navegador = await firefox.launch(opcionesFirefox);

            console.log('📄 Creando contexto de navegación Firefox Playwright...');
            
            // Crear contexto - modo incógnito se maneja aquí en Playwright
            const opcionesContexto = {
                viewport: {
                    width: this.dimensionesVentana.width,
                    height: this.dimensionesVentana.height
                },
                // En Playwright Firefox, incógnito se maneja de forma diferente
                userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
            };

            // En Playwright, cada contexto es independiente (similar a incógnito)
            this.contexto = await this.navegador.newContext(opcionesContexto);
            this.pagina = await this.contexto.newPage();
            
            console.log('🎯 Navegando a Lightning Roulette...');
            
            // URLs alternativas para diferentes opciones
            const urlsDisponibles = {
                'bet20play': 'https://bet20play.com/mx/live-casino/game/evolution/lightning_roulette',
                'evolution': 'https://www.evolutiongaming.com/games/lightning-roulette',
                'demo': 'https://demo.casino/games/lightning-roulette',
                'google': 'https://www.google.com',  // Para pruebas
                'local': 'file:///C:/casino-demo.html'  // Para desarrollo local
            };
            
            console.log('🎯 URLs disponibles:');
            console.log('   1. bet20play - bet20play México (recomendado)');
            console.log('   2. evolution - Sitio oficial Evolution Gaming');
            console.log('   3. demo - Casino demo');
            console.log('   4. google - Google (para pruebas)');
            console.log('   5. Escribe tu propia URL');
            console.log('');
            
            const respuesta = await this.preguntarSimple('🎮 Elige opción (1-5) o ENTER para bet20play: ');
            let urlFinal;
            
            switch(respuesta.trim()) {
                case '':
                case '1':
                    urlFinal = urlsDisponibles.bet20play;
                    console.log('🎯 Usando bet20play México');
                    break;
                case '2':
                    urlFinal = urlsDisponibles.evolution;
                    console.log('🎯 Usando Evolution Gaming oficial');
                    break;
                case '3':
                    urlFinal = urlsDisponibles.demo;
                    console.log('🎯 Usando casino demo');
                    break;
                case '4':
                    urlFinal = urlsDisponibles.google;
                    console.log('🎯 Usando Google (para pruebas)');
                    break;
                case '5':
                    const urlCustom = await this.preguntarSimple('🔗 Escribe la URL completa: ');
                    urlFinal = urlCustom.trim();
                    console.log(`🎯 Usando URL personalizada: ${urlFinal}`);
                    break;
                default:
                    urlFinal = respuesta.trim().startsWith('http') ? respuesta.trim() : urlsDisponibles.bet20play;
                    console.log(`🎯 Usando: ${urlFinal}`);
            }
            
            try {
                console.log('⏰ Cargando página... (puede tomar hasta 60 segundos)');
                console.log('🔧 Si tarda mucho, puedes cancelar con Ctrl+C y usar otra URL');
                
                await this.pagina.goto(urlFinal, { 
                    waitUntil: 'domcontentloaded',  // Más rápido que networkidle
                    timeout: 60000  // Aumentado a 60 segundos
                });
                
                console.log('✅ Lightning Roulette cargado exitosamente en Firefox');
                console.log(`📐 Tamaño de ventana: ${this.dimensionesVentana.width} x ${this.dimensionesVentana.height}`);
                console.log(`🔒 Modo incógnito: ${this.modoIncognito ? 'Activo' : 'Inactivo'}`);
                
                this.estaConectado = true;
                this.estaInicializando = false; // Reset flag al completar exitosamente
                
                // Esperar carga completa
                await this.esperar(4000);
                
                // Inyectar estilos para mejor detección
                await this.pagina.addStyleTag({
                    content: `
                        .roulette-detector-highlight {
                            border: 2px solid red !important;
                            background-color: rgba(255, 0, 0, 0.2) !important;
                        }
                        .click-indicator {
                            position: fixed !important;
                            z-index: 999999 !important;
                            pointer-events: none !important;
                        }
                    `
                });
                
                console.log('🎮 ¡Firefox con Lightning Roulette listo para detectar!');
                
            } catch (error) {
                console.log(`❌ Error cargando página: ${error.message}`);
                
                if (error.message.includes('timeout')) {
                    console.log('⏰ TIMEOUT: La página tardó demasiado en cargar');
                    console.log('');
                    console.log('🔧 OPCIONES:');
                    console.log('   1. Intentar con otra URL más rápida');
                    console.log('   2. Verificar tu conexión a internet');
                    console.log('   3. Usar modo sin página para solo detectar');
                    console.log('');
                    
                    const continuar = await this.preguntarSimple('❓ ¿Quieres intentar otra URL? (s/n): ');
                    if (continuar.toLowerCase().startsWith('s')) {
                        this.estaInicializando = false;
                        // Reintentar con otra URL
                        console.log('🔄 Reintentando con opciones más rápidas...');
                        return await this.abrirFirefox();
                    }
                }
                
                console.log('💡 Firefox queda abierto para uso manual');
                console.log('🎮 Puedes usar los otros comandos aunque no cargue la página');
                this.estaConectado = true; // Marcar como conectado para poder usar otros comandos
                this.estaInicializando = false; // Reset flag
            }
            
        } catch (error) {
            console.log(`❌ Error abriendo Firefox: ${error.message}`);
            console.log('💡 Asegúrate de tener Firefox instalado');
            console.log('🔧 Si usas Playwright por primera vez, ejecuta: npx playwright install firefox');
            this.estaInicializando = false; // Reset flag en caso de error
        }
    }

    async deteccionAutomatica() {
        if (!this.estaConectado) {
            console.log('❌ Primero abre Firefox con Lightning Roulette');
            return;
        }

        console.log('\n🔍 DETECCIÓN AUTOMÁTICA EN FIREFOX...');
        console.log('='.repeat(40));
        
        try {
            console.log('📸 Tomando captura de pantalla...');
            await this.pagina.screenshot({
                path: 'lightning_roulette_firefox_captura.png',
                fullPage: false
            });
            
            console.log('🎯 Buscando números específicos para Firefox...');
            
            // Detección optimizada para Firefox y Lightning Roulette
            const numerosEncontrados = await this.pagina.evaluate(() => {
                const numeros = [];
                
                // Selectores mejorados específicos para Lightning Roulette en Firefox
                const selectoresFirefox = [
                    // Selectores principales de Lightning Roulette
                    '.roulette-number',
                    '.number-cell', 
                    '.betting-spot',
                    '.game-number',
                    '.bet-spot',
                    '[data-number]',
                    '.chip-spot',
                    '.number-spot',
                    // Selectores específicos de Evolution Gaming
                    '.numberContainer',
                    '.betspot',
                    '.roulette-grid-number',
                    // Selectores adicionales para Firefox compatibilidad
                    '.number',
                    '.bet-button',
                    '.betting-grid .number',
                    '.roulette-grid .cell',
                    '.game-grid .spot',
                    '[class*="number"]',
                    '[class*="bet"]',
                    '[class*="spot"]',
                    // Selectores para elementos interactivos
                    'button[data-number]',
                    'div[data-number]',
                    'span[data-number]',
                    // Lightning Roulette específicos
                    '.lr-number',
                    '.lightning-number',
                    '.lr-bet-spot',
                    '.lr-betting-spot'
                ];
                
                let elementosEncontrados = 0;
                
                selectoresFirefox.forEach(selector => {
                    const elementos = document.querySelectorAll(selector);
                    elementos.forEach((elemento) => {
                        const rect = elemento.getBoundingClientRect();
                        
                        if (rect.width > 10 && rect.height > 10) {
                            let numero = elemento.textContent?.trim() || 
                                        elemento.getAttribute('data-number') || 
                                        elemento.getAttribute('data-value') ||
                                        elemento.title ||
                                        '';
                            
                            // Limpiar el número
                            numero = numero.replace(/[^0-9]/g, '');
                            
                            if (numero && numero.length > 0) {
                                numeros.push({
                                    valor: parseInt(numero) || numero,
                                    x: rect.left + rect.width / 2,
                                    y: rect.top + rect.height / 2,
                                    width: rect.width,
                                    height: rect.height,
                                    selector: selector
                                });
                                elementosEncontrados++;
                            }
                        }
                    });
                });
                
                // Si no encontramos suficientes elementos, usar grid simulado optimizado para Firefox
                if (elementosEncontrados < 10) {
                    console.log('🦊 Usando grid simulado optimizado para Firefox');
                    
                    // Grid simulado con posiciones realistas para Lightning Roulette
                    const numerosRuleta = [
                        // Fila 1 (arriba)
                        3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36,
                        // Fila 2 (medio)  
                        2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35,
                        // Fila 3 (abajo)
                        1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34,
                        // Cero
                        0
                    ];
                    
                    // Posiciones optimizadas para resolución típica de Firefox
                    const startX = 120;
                    const startY = 180;
                    const cellWidth = 85;
                    const cellHeight = 38;
                    
                    // Grid principal (3 filas x 12 columnas)
                    for (let col = 0; col < 12; col++) {
                        for (let row = 0; row < 3; row++) {
                            const index = col * 3 + row;
                            if (index < 36) {
                                numeros.push({
                                    valor: numerosRuleta[index],
                                    x: startX + col * cellWidth,
                                    y: startY + row * cellHeight,
                                    width: cellWidth - 5,
                                    height: cellHeight - 5,
                                    selector: 'simulado'
                                });
                            }
                        }
                    }
                    
                    // Cero (posición especial)
                    numeros.push({
                        valor: 0,
                        x: startX - 60,
                        y: startY + cellHeight,
                        width: 50,
                        height: cellHeight * 3 - 10,
                        selector: 'simulado_cero'
                    });
                    
                    // Apuestas exteriores específicas para Firefox
                    const apuestasExteriores = [
                        { valor: 'RED', x: startX + 12 * cellWidth + 20, y: startY },
                        { valor: 'BLACK', x: startX + 12 * cellWidth + 20, y: startY + cellHeight },
                        { valor: 'EVEN', x: startX + 12 * cellWidth + 20, y: startY + 2 * cellHeight },
                        { valor: 'ODD', x: startX + 12 * cellWidth + 100, y: startY },
                        { valor: '1st 12', x: startX + 4 * cellWidth - 40, y: startY + 3 * cellHeight + 10 },
                        { valor: '2nd 12', x: startX + 8 * cellWidth - 40, y: startY + 3 * cellHeight + 10 },
                        { valor: '3rd 12', x: startX + 12 * cellWidth - 40, y: startY + 3 * cellHeight + 10 }
                    ];
                    
                    apuestasExteriores.forEach(apuesta => {
                        numeros.push({
                            valor: apuesta.valor,
                            x: apuesta.x,
                            y: apuesta.y,
                            width: 80,
                            height: 35,
                            selector: 'simulado_apuesta'
                        });
                    });
                }
                
                return numeros;
            });
            
            // Convertir a coordenadas relativas
            this.numerosDetectados = numerosEncontrados.map(num => {
                const relX = num.x / this.dimensionesVentana.width;
                const relY = num.y / this.dimensionesVentana.height;
                
                return {
                    valor: num.valor,
                    tipo: this.esNumero(num.valor) ? 'numero' : 'apuesta',
                    metodo: 'firefox_integrado',
                    selector: num.selector,
                    coordenadas: {
                        relativas: { x: relX, y: relY },
                        absolutas: { x: num.x, y: num.y }
                    }
                };
            });
            
            console.log(`✅ DETECCIÓN COMPLETADA EN FIREFOX:`);
            console.log(`   🎯 ${this.numerosDetectados.length} elementos detectados`);
            console.log(`   🦊 Optimizado para Firefox`);
            console.log(`   📐 Coordenadas convertidas a relativas`);
            
            // Mostrar algunos ejemplos
            if (this.numerosDetectados.length > 0) {
                console.log('\n📋 ELEMENTOS ENCONTRADOS (primeros 6):');
                this.numerosDetectados.slice(0, 6).forEach((elem, i) => {
                    const rel = elem.coordenadas.relativas;
                    const selectorInfo = elem.selector === 'simulado' ? '🔧' : '🎯';
                    console.log(`   ${i + 1}. ${selectorInfo} ${elem.valor}: (${rel.x.toFixed(3)}, ${rel.y.toFixed(3)})`);
                });
                
                if (this.numerosDetectados.length > 6) {
                    console.log(`   ... y ${this.numerosDetectados.length - 6} más`);
                }
            }
            
        } catch (error) {
            console.log(`❌ Error en detección automática: ${error.message}`);
        }
    }

    async grabacionManual() {
        if (!this.estaConectado) {
            console.log('❌ Primero abre Firefox con Lightning Roulette');
            return;
        }

        console.log('\n👆 GRABACIÓN MANUAL MEJORADA PARA FIREFOX...');
        console.log('='.repeat(50));
        console.log('📋 Instrucciones:');
        console.log('   1. Haz click FÍSICO en los números de Firefox');
        console.log('   2. Se capturan clicks a nivel del sistema operativo');
        console.log('   3. Detección mejorada específica para Firefox');
        console.log('   4. Presiona ENTER para terminar');
        console.log('');

        try {
            // Obtener posición de la ventana Firefox con métodos mejorados
            const ventanaFirefox = await this.obtenerPosicionVentanaFirefoxMejorada();
            if (!ventanaFirefox) {
                console.log('❌ No se pudo detectar la ventana de Firefox');
                console.log('💡 Asegúrate de que Firefox esté abierto y visible');
                return;
            }

            console.log(`📐 Ventana Firefox detectada: ${ventanaFirefox.width} x ${ventanaFirefox.height}`);
            console.log(`📍 Posición: (${ventanaFirefox.x}, ${ventanaFirefox.y})`);
            console.log(`🔍 Título: ${ventanaFirefox.titulo || 'N/A'}`);

            // Crear script PowerShell mejorado para captura de clicks específica para Firefox
            const scriptCaptura = `
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    using System.Windows.Forms;
    using System.Text;
    using System.Diagnostics;
    
    public class FirefoxMouseHook {
        private const int WH_MOUSE_LL = 14;
        private const int WM_LBUTTONDOWN = 0x0201;
        
        public delegate IntPtr LowLevelMouseProc(int nCode, IntPtr wParam, IntPtr lParam);
        public static LowLevelMouseProc _proc = HookCallback;
        public static IntPtr _hookID = IntPtr.Zero;
        
        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern IntPtr SetWindowsHookEx(int idHook, LowLevelMouseProc lpfn, IntPtr hMod, uint dwThreadId);
        
        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool UnhookWindowsHookEx(IntPtr hhk);
        
        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);
        
        [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        public static extern IntPtr GetModuleHandle(string lpModuleName);
        
        [DllImport("user32.dll")]
        public static extern IntPtr WindowFromPoint(POINT pt);
        
        [DllImport("user32.dll")]
        public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
        
        [DllImport("user32.dll")]
        public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
        
        [StructLayout(LayoutKind.Sequential)]
        public struct POINT {
            public int x;
            public int y;
        }
        
        [StructLayout(LayoutKind.Sequential)]
        public struct MSLLHOOKSTRUCT {
            public POINT pt;
            public uint mouseData;
            public uint flags;
            public uint time;
            public IntPtr dwExtraInfo;
        }
        
        public static IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam) {
            if (nCode >= 0 && wParam == (IntPtr)WM_LBUTTONDOWN) {
                MSLLHOOKSTRUCT hookStruct = (MSLLHOOKSTRUCT)Marshal.PtrToStructure(lParam, typeof(MSLLHOOKSTRUCT));
                
                // Verificar si el click está dentro de la ventana Firefox
                IntPtr windowHandle = WindowFromPoint(hookStruct.pt);
                StringBuilder windowTitle = new StringBuilder(256);
                GetWindowText(windowHandle, windowTitle, 256);
                
                // Obtener información del proceso
                uint processId;
                GetWindowThreadProcessId(windowHandle, out processId);
                
                try {
                    Process process = Process.GetProcessById((int)processId);
                    string processName = process.ProcessName.ToLower();
                    string title = windowTitle.ToString().ToLower();
                    
                    // Detección mejorada para Firefox
                    bool esFirefox = processName.Contains("firefox") || 
                                   title.Contains("firefox") || 
                                   title.Contains("mozilla") ||
                                   processName.Contains("gecko") ||
                                   title.Contains("lightning roulette") ||
                                   title.Contains("evolution");
                    
                    if (esFirefox) {
                        // Verificar que está dentro del área de la ventana Firefox detectada
                        int ventanaX = ${ventanaFirefox.x};
                        int ventanaY = ${ventanaFirefox.y};
                        int ventanaWidth = ${ventanaFirefox.width};
                        int ventanaHeight = ${ventanaFirefox.height};
                        
                        if (hookStruct.pt.x >= ventanaX && hookStruct.pt.x <= ventanaX + ventanaWidth &&
                            hookStruct.pt.y >= ventanaY && hookStruct.pt.y <= ventanaY + ventanaHeight) {
                            
                            Console.WriteLine("FIREFOX_CLICK_CAPTURED:" + hookStruct.pt.x + "," + hookStruct.pt.y + "," + DateTime.Now.Ticks + "," + processName + "," + title);
                        }
                    }
                } catch {
                    // Fallback a detección por título si no se puede obtener el proceso
                    string title = windowTitle.ToString().ToLower();
                    if (title.Contains("firefox") || title.Contains("mozilla") || title.Contains("lightning") || title.Contains("roulette")) {
                        Console.WriteLine("FIREFOX_CLICK_CAPTURED:" + hookStruct.pt.x + "," + hookStruct.pt.y + "," + DateTime.Now.Ticks + ",fallback," + title);
                    }
                }
            }
            return CallNextHookEx(_hookID, nCode, wParam, lParam);
        }
        
        public static void StartHook() {
            _hookID = SetWindowsHookEx(WH_MOUSE_LL, _proc, GetModuleHandle("user32"), 0);
            if (_hookID == IntPtr.Zero) {
                Console.WriteLine("ERROR_HOOK_FAILED");
                return;
            }
            Console.WriteLine("HOOK_STARTED_SUCCESSFULLY");
            Application.Run();
        }
        
        public static void StopHook() {
            UnhookWindowsHookEx(_hookID);
        }
    }
"@

# Iniciar captura en background
$job = Start-Job -ScriptBlock {
    try {
        [FirefoxMouseHook]::StartHook()
    } catch {
        Write-Host "ERROR_STARTING_HOOK: $($_.Exception.Message)"
    }
}

# Esperar señal de terminación (archivo temporal)
while (-not (Test-Path "stop_firefox_capture.tmp")) {
    Start-Sleep -Milliseconds 100
}

# Detener captura
Stop-Job $job
Remove-Job $job
if (Test-Path "stop_firefox_capture.tmp") {
    Remove-Item "stop_firefox_capture.tmp" -Force
}
`;

            // Guardar script y ejecutar
            const fs = require('fs').promises;
            await fs.writeFile('captura_clicks_firefox_mejorado.ps1', scriptCaptura);

            console.log('🎯 ¡Captura de clicks específica para Firefox activada!');
            console.log('👆 Haz click FÍSICO en los números de Firefox');
            console.log('🦊 Detección mejorada para Firefox/Mozilla');
            console.log('🔴 Se registrarán automáticamente');
            console.log('❌ Presiona ENTER cuando termines');

            // Ejecutar captura en background
            const { spawn } = require('child_process');
            const procesoCaptura = spawn('powershell', [
                '-ExecutionPolicy', 'Bypass',
                '-File', 'captura_clicks_firefox_mejorado.ps1'
            ]);

            let clicksCapturados = [];

            procesoCaptura.stdout.on('data', (data) => {
                const salida = data.toString();
                const lineas = salida.split('\n');
                
                lineas.forEach(linea => {
                    if (linea.includes('FIREFOX_CLICK_CAPTURED:')) {
                        const datos = linea.split('FIREFOX_CLICK_CAPTURED:')[1].split(',');
                        const x = parseInt(datos[0]);
                        const y = parseInt(datos[1]);
                        const timestamp = parseInt(datos[2]);
                        const processName = datos[3] || 'unknown';
                        const windowTitle = datos[4] || 'unknown';
                        
                        // Convertir a coordenadas relativas de la ventana Firefox
                        const relX = (x - ventanaFirefox.x) / ventanaFirefox.width;
                        const relY = (y - ventanaFirefox.y) / ventanaFirefox.height;
                        
                        // Solo capturar clicks dentro de la ventana Firefox
                        if (relX >= 0 && relX <= 1 && relY >= 0 && relY <= 1) {
                            clicksCapturados.push({
                                x: x,
                                y: y,
                                relX: relX,
                                relY: relY,
                                timestamp: timestamp,
                                processName: processName,
                                windowTitle: windowTitle
                            });
                            
                            console.log(`🦊 Click Firefox capturado: (${x}, ${y}) → Rel: (${relX.toFixed(3)}, ${relY.toFixed(3)}) [${processName}]`);
                        }
                    } else if (linea.includes('HOOK_STARTED_SUCCESSFULLY')) {
                        console.log('✅ Hook de mouse iniciado correctamente para Firefox');
                    } else if (linea.includes('ERROR_HOOK_FAILED')) {
                        console.log('❌ Error: No se pudo iniciar el hook de mouse');
                        console.log('💡 Ejecuta como administrador o verifica permisos');
                    }
                });
            });

            procesoCaptura.stderr.on('data', (data) => {
                console.log(`⚠️ PowerShell error: ${data.toString()}`);
            });

            // Esperar input del usuario
            await this.preguntarSimple('');

            // Detener captura
            await fs.writeFile('stop_firefox_capture.tmp', 'stop');
            procesoCaptura.kill();

            // Esperar un poco para procesar últimos clicks
            await this.esperar(1000);

            // Procesar clicks capturados y detectar valores
            console.log(`\n📊 Procesando ${clicksCapturados.length} clicks capturados...`);
            
            for (const click of clicksCapturados) {
                // Intentar detectar el valor del elemento en esa posición
                const valor = await this.detectarValorEnPosicion(click.relX, click.relY);
                
                this.numerosDetectados.push({
                    valor: valor || 'click_' + clicksCapturados.indexOf(click),
                    tipo: this.esNumero(valor) ? 'numero' : 'apuesta',
                    metodo: 'manual_firefox_mejorado',
                    coordenadas: {
                        relativas: { x: click.relX, y: click.relY },
                        absolutas: { x: click.x, y: click.y }
                    },
                    timestamp: click.timestamp,
                    procesoFirefox: click.processName,
                    tituloVentana: click.windowTitle
                });
            }

            console.log(`✅ ${clicksCapturados.length} clicks de Firefox grabados con detección mejorada`);
            console.log('📐 Convertidos automáticamente a coordenadas relativas');
            console.log('🦊 Validados específicamente para Firefox');

            // Limpiar archivos temporales
            await this.limpiarArchivosTemporales();
            
        } catch (error) {
            console.log(`❌ Error en grabación manual: ${error.message}`);
            
            // Sugerencias de solución
            if (error.message.includes('powershell')) {
                console.log('\n🔧 POSIBLES SOLUCIONES:');
                console.log('   1. Ejecuta como administrador');
                console.log('   2. Verifica que PowerShell esté disponible');
                console.log('   3. Ejecuta: Set-ExecutionPolicy RemoteSigned');
            }
        }
    }

    async grabacionConHotkeys() {
        if (!this.estaConectado) {
            console.log('❌ Primero abre Firefox con Lightning Roulette');
            return;
        }

        console.log('\n⌨️ GRABACIÓN CON CONTROL DE TECLAS...');
        console.log('='.repeat(45));
        console.log('📋 Instrucciones:');
        console.log('   🟢 Presiona "S" para EMPEZAR a grabar');
        console.log('   👆 Haz click en el número (ej: 7)');
        console.log('   🔴 Presiona "E" para TERMINAR esa coordenada');
        console.log('   🔄 Repite para cada número');
        console.log('   ❌ Presiona "Q" para SALIR');
        console.log('');

        try {
            // Obtener posición de la ventana Firefox
            const ventanaFirefox = await this.obtenerPosicionVentanaFirefox();
            if (!ventanaFirefox) {
                console.log('❌ No se pudo detectar la ventana de Firefox');
                return;
            }

            console.log(`📐 Ventana Firefox detectada: ${ventanaFirefox.width} x ${ventanaFirefox.height}`);
            console.log(`📍 Posición: (${ventanaFirefox.x}, ${ventanaFirefox.y})`);

            // Script PowerShell para captura controlada con hotkeys
            const scriptHotkeys = `
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Write-Host "HOTKEY_CAPTURE_STARTED"

$grabando = $false
$numeroActual = 1
$salir = $false

while (-not $salir) {
    # Verificar teclas presionadas
    $sPressed = [System.Windows.Forms.Control]::IsKeyLocked([System.Windows.Forms.Keys]::None) -eq $false -and 
                [System.Console]::KeyAvailable -and 
                [System.Console]::ReadKey($true).Key -eq [System.ConsoleKey]::S
    
    # Método alternativo para detectar teclas
    if ([System.Windows.Forms.Control]::IsKeyLocked([System.Windows.Forms.Keys]::None) -eq $false) {
        try {
            # Detectar tecla S para empezar
            if ([System.Windows.Forms.Control]::ModifierKeys -eq [System.Windows.Forms.Keys]::None) {
                $keyState = [System.Windows.Forms.Control]::IsKeyLocked([System.Windows.Forms.Keys]::S)
                
                # Verificar si S está presionada (método Windows API)
                Add-Type @"
                    using System;
                    using System.Runtime.InteropServices;
                    public class KeyboardChecker {
                        [DllImport("user32.dll")]
                        public static extern short GetAsyncKeyState(int vKey);
                        
                        public static bool IsKeyPressed(int keyCode) {
                            return (GetAsyncKeyState(keyCode) & 0x8000) != 0;
                        }
                    }
"@
                
                # S = 83, E = 69, Q = 81
                $sPressed = [KeyboardChecker]::IsKeyPressed(83)
                $ePressed = [KeyboardChecker]::IsKeyPressed(69)
                $qPressed = [KeyboardChecker]::IsKeyPressed(81)
                
                if ($qPressed) {
                    Write-Host "QUIT_REQUESTED"
                    $salir = $true
                }
                
                if ($sPressed -and -not $grabando) {
                    Write-Host "START_RECORDING:$numeroActual"
                    $grabando = $true
                    Start-Sleep -Milliseconds 300  # Evitar doble detección
                }
                
                if ($ePressed -and $grabando) {
                    Write-Host "STOP_RECORDING:$numeroActual"
                    $grabando = $false
                    $numeroActual++
                    Start-Sleep -Milliseconds 300  # Evitar doble detección
                }
            }
        } catch {
            # Error en detección de teclas, continuar
        }
    }
    
    # Si estamos grabando, detectar clicks
    if ($grabando) {
        $leftButton = [System.Windows.Forms.Control]::MouseButtons -band [System.Windows.Forms.MouseButtons]::Left
        
        if ($leftButton -eq [System.Windows.Forms.MouseButtons]::Left) {
            $position = [System.Windows.Forms.Cursor]::Position
            Write-Host "CLICK_RECORDED:$($position.X),$($position.Y),$numeroActual"
            Start-Sleep -Milliseconds 200  # Evitar clicks múltiples
        }
    }
    
    # Verificar archivo de parada
    if (Test-Path "stop_hotkey_capture.tmp") {
        $salir = $true
    }
    
    Start-Sleep -Milliseconds 50
}

if (Test-Path "stop_hotkey_capture.tmp") {
    Remove-Item "stop_hotkey_capture.tmp" -Force
}
Write-Host "HOTKEY_CAPTURE_STOPPED"
`;

            const fs = require('fs').promises;
            await fs.writeFile('captura_hotkeys.ps1', scriptHotkeys);

            console.log('🎮 ¡Sistema de hotkeys activado!');
            console.log('⌨️ Usa las teclas para controlar la grabación:');
            console.log('   🟢 S = Empezar a grabar');
            console.log('   🔴 E = Terminar y guardar');
            console.log('   ❌ Q = Salir');
            console.log('');
            console.log('📝 Ejemplo de uso:');
            console.log('   1. Presiona S');
            console.log('   2. Haz click en el 7');
            console.log('   3. Presiona E');
            console.log('   4. Presiona S para el siguiente número');
            console.log('');
            console.log('🚀 ¡Empezando captura con hotkeys!');

            // Ejecutar captura en background
            const { spawn } = require('child_process');
            const procesoHotkeys = spawn('powershell', [
                '-ExecutionPolicy', 'Bypass',
                '-File', 'captura_hotkeys.ps1'
            ], { 
                stdio: ['ignore', 'pipe', 'pipe']
            });

            let coordenadasGrabadas = [];
            let capturaIniciada = false;
            let grabandoActual = false;
            let numeroActual = 1;

            procesoHotkeys.stdout.on('data', (data) => {
                const salida = data.toString();
                const lineas = salida.split('\n');
                
                lineas.forEach(linea => {
                    linea = linea.trim();
                    
                    if (linea.includes('HOTKEY_CAPTURE_STARTED')) {
                        capturaIniciada = true;
                        console.log('✅ Sistema de hotkeys iniciado correctamente');
                        console.log('🟢 Presiona "S" para empezar a grabar el primer número');
                    }
                    
                    if (linea.includes('START_RECORDING:')) {
                        const num = linea.split('START_RECORDING:')[1];
                        grabandoActual = true;
                        numeroActual = parseInt(num);
                        console.log(`🟢 GRABANDO #${numeroActual} - Haz click en el número ahora`);
                    }
                    
                    if (linea.includes('CLICK_RECORDED:')) {
                        const datos = linea.split('CLICK_RECORDED:')[1].split(',');
                        const x = parseInt(datos[0]);
                        const y = parseInt(datos[1]);
                        const num = parseInt(datos[2]);
                        
                        // Verificar si está dentro de Firefox
                        if (x >= ventanaFirefox.x && x <= ventanaFirefox.x + ventanaFirefox.width &&
                            y >= ventanaFirefox.y && y <= ventanaFirefox.y + ventanaFirefox.height) {
                            
                            const relX = (x - ventanaFirefox.x) / ventanaFirefox.width;
                            const relY = (y - ventanaFirefox.y) / ventanaFirefox.height;
                            
                            console.log(`👆 Click registrado #${num}: (${x}, ${y}) → Rel: (${relX.toFixed(3)}, ${relY.toFixed(3)})`);
                            console.log('🔴 Presiona "E" para confirmar y guardar esta coordenada');
                            
                            // Almacenar temporalmente
                            coordenadasGrabadas.push({
                                numero: num,
                                x: x,
                                y: y,
                                relX: relX,
                                relY: relY,
                                timestamp: Date.now(),
                                confirmado: false
                            });
                        } else {
                            console.log(`⚠️ Click fuera de Firefox: (${x}, ${y})`);
                        }
                    }
                    
                    if (linea.includes('STOP_RECORDING:')) {
                        const num = linea.split('STOP_RECORDING:')[1];
                        grabandoActual = false;
                        
                        // Confirmar la última coordenada
                        const ultimaCoord = coordenadasGrabadas.find(c => c.numero == num && !c.confirmado);
                        if (ultimaCoord) {
                            ultimaCoord.confirmado = true;
                            console.log(`✅ Coordenada #${num} guardada y confirmada`);
                            console.log(`📊 Total grabado: ${coordenadasGrabadas.filter(c => c.confirmado).length} coordenadas`);
                            console.log('🟢 Presiona "S" para grabar el siguiente número');
                        } else {
                            console.log(`⚠️ No se encontró click para confirmar #${num}`);
                        }
                    }
                    
                    if (linea.includes('QUIT_REQUESTED')) {
                        console.log('🛑 Salida solicitada con tecla Q');
                    }
                    
                    if (linea.includes('HOTKEY_CAPTURE_STOPPED')) {
                        console.log('🛑 Captura con hotkeys detenida');
                    }
                });
            });

            procesoHotkeys.stderr.on('data', (data) => {
                console.log(`🐛 Error PowerShell: ${data.toString()}`);
            });

            // Verificar inicio en 5 segundos
            setTimeout(() => {
                if (!capturaIniciada) {
                    console.log('⚠️ El sistema de hotkeys no se inició en 5 segundos');
                    console.log('💡 Puede necesitar permisos de administrador');
                    console.log('🔧 Intenta ejecutar como administrador');
                }
            }, 5000);

            // Esperar hasta que el usuario termine (presione Q o Enter en consola)
            console.log('\n⌨️ CONTROLES DISPONIBLES:');
            console.log('   🟢 S = Empezar a grabar número');
            console.log('   🔴 E = Terminar y guardar número');
            console.log('   ❌ Q = Salir del modo hotkeys');
            console.log('   📝 ENTER en consola = Salir también');
            console.log('');

            await this.preguntarSimple('Presiona ENTER cuando termines de grabar todos los números: ');

            // Detener captura
            await fs.writeFile('stop_hotkey_capture.tmp', 'stop');
            await this.esperar(500);
            procesoHotkeys.kill();

            // Procesar coordenadas confirmadas
            const coordenadasConfirmadas = coordenadasGrabadas.filter(c => c.confirmado);
            
            for (const coord of coordenadasConfirmadas) {
                // Intentar detectar el valor del elemento en esa posición
                const valor = await this.detectarValorEnPosicion(coord.relX, coord.relY);
                
                this.numerosDetectados.push({
                    valor: valor || `numero_${coord.numero}`,
                    tipo: this.esNumero(valor) ? 'numero' : 'apuesta',
                    metodo: 'hotkeys_controlado',
                    coordenadas: {
                        relativas: { x: coord.relX, y: coord.relY },
                        absolutas: { x: coord.x, y: coord.y }
                    },
                    numeroGrabacion: coord.numero,
                    timestamp: coord.timestamp
                });
            }

            console.log(`\n🎯 RESUMEN DE GRABACIÓN CON HOTKEYS:`);
            console.log(`   ✅ Coordenadas confirmadas: ${coordenadasConfirmadas.length}`);
            console.log(`   📐 Convertidas a relativas automáticamente`);
            console.log(`   🔍 Valores detectados automáticamente`);
            console.log(`   ⌨️ Grabadas con control de teclas S/E`);

            // Mostrar cada coordenada grabada
            if (coordenadasConfirmadas.length > 0) {
                console.log('\n📋 COORDENADAS GRABADAS:');
                coordenadasConfirmadas.forEach((coord, i) => {
                    const elementoDetectado = this.numerosDetectados[this.numerosDetectados.length - coordenadasConfirmadas.length + i];
                    console.log(`   ${coord.numero}. ${elementoDetectado.valor}: (${coord.relX.toFixed(3)}, ${coord.relY.toFixed(3)})`);
                });
            }

            // Limpiar archivos temporales
            try {
                await fs.unlink('captura_hotkeys.ps1');
            } catch (e) {
                // Archivo ya eliminado
            }

        } catch (error) {
            console.log(`❌ Error en grabación con hotkeys: ${error.message}`);
        }
    }

    async grabacionManualSistema() {
        if (!this.estaConectado) {
            console.log('❌ Primero abre Firefox con Lightning Roulette');
            return;
        }

        console.log('\n👆 GRABACIÓN MANUAL A NIVEL DE SISTEMA...');
        console.log('='.repeat(45));
        console.log('📋 Instrucciones:');
        console.log('   1. Haz click FÍSICO en los números de Firefox');
        console.log('   2. Se capturan clicks a nivel del sistema operativo');
        console.log('   3. Se convierten automáticamente a coordenadas relativas');
        console.log('   4. Presiona ENTER para terminar');
        console.log('');

        try {
            // Obtener posición de la ventana Firefox
            const ventanaFirefox = await this.obtenerPosicionVentanaFirefox();
            if (!ventanaFirefox) {
                console.log('❌ No se pudo detectar la ventana de Firefox');
                return;
            }

            console.log(`📐 Ventana Firefox detectada: ${ventanaFirefox.width} x ${ventanaFirefox.height}`);
            console.log(`📍 Posición: (${ventanaFirefox.x}, ${ventanaFirefox.y})`);

            // Script más simple y robusto para captura de clicks
            const scriptCaptura = `
# Script simplificado para capturar posición del mouse al hacer click
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Write-Host "HOOK_STARTED"

# Método alternativo: monitorear posición del mouse
$lastClickTime = 0
$clickThreshold = 200  # milisegundos para evitar doble detección

while (-not (Test-Path "stop_firefox_capture.tmp")) {
    # Verificar si botón izquierdo del mouse está presionado
    $leftButton = [System.Windows.Forms.Control]::MouseButtons -band [System.Windows.Forms.MouseButtons]::Left
    
    if ($leftButton -eq [System.Windows.Forms.MouseButtons]::Left) {
        $currentTime = (Get-Date).Ticks / 10000  # Convertir a milisegundos
        
        # Evitar detectar el mismo click múltiples veces
        if (($currentTime - $lastClickTime) -gt $clickThreshold) {
            $position = [System.Windows.Forms.Cursor]::Position
            Write-Host "CLICK:$($position.X),$($position.Y)"
            $lastClickTime = $currentTime
        }
    }
    
    Start-Sleep -Milliseconds 50
}

if (Test-Path "stop_firefox_capture.tmp") {
    Remove-Item "stop_firefox_capture.tmp" -Force
}
`;

            const fs = require('fs').promises;
            await fs.writeFile('captura_firefox_sistema.ps1', scriptCaptura);

            console.log('🎯 ¡Captura de clicks a nivel sistema activada!');
            console.log('👆 Haz click FÍSICO en los números de Firefox');
            console.log('🔴 Se registrarán automáticamente');
            console.log('🐛 Debug: Script PowerShell iniciando...');
            console.log('❌ Presiona ENTER cuando termines');

            // Ejecutar captura en background con mejor visibilidad
            const { spawn } = require('child_process');
            const procesoCaptura = spawn('powershell', [
                '-ExecutionPolicy', 'Bypass',
                '-File', 'captura_firefox_sistema.ps1'
            ], { 
                stdio: ['ignore', 'pipe', 'pipe']
            });

            let clicksCapturados = [];
            let hookIniciado = false;

            procesoCaptura.stdout.on('data', (data) => {
                const salida = data.toString();
                const lineas = salida.split('\n');
                
                lineas.forEach(linea => {
                    linea = linea.trim();
                    
                    if (linea.includes('HOOK_STARTED')) {
                        hookIniciado = true;
                        console.log('✅ Hook del mouse iniciado correctamente');
                        console.log('👆 Ahora puedes hacer clicks en Firefox');
                    }
                    
                    if (linea.includes('CLICK:')) {
                        const coordsStr = linea.split('CLICK:')[1];
                        const coords = coordsStr.split(',');
                        if (coords.length >= 2) {
                            const x = parseInt(coords[0]);
                            const y = parseInt(coords[1]);
                            
                            console.log(`🔍 Click detectado en sistema: (${x}, ${y})`);
                            
                            // Verificar si está dentro de la ventana Firefox
                            if (x >= ventanaFirefox.x && x <= ventanaFirefox.x + ventanaFirefox.width &&
                                y >= ventanaFirefox.y && y <= ventanaFirefox.y + ventanaFirefox.height) {
                                
                                // Convertir a coordenadas relativas
                                const relX = (x - ventanaFirefox.x) / ventanaFirefox.width;
                                const relY = (y - ventanaFirefox.y) / ventanaFirefox.height;
                                
                                clicksCapturados.push({
                                    x: x,
                                    y: y,
                                    relX: relX,
                                    relY: relY,
                                    timestamp: Date.now()
                                });
                                
                                console.log(`✅ Click Firefox capturado: (${x}, ${y}) → Rel: (${relX.toFixed(3)}, ${relY.toFixed(3)})`);
                            } else {
                                console.log(`⚠️ Click fuera de Firefox: (${x}, ${y}) - Ventana Firefox: ${ventanaFirefox.x},${ventanaFirefox.y} ${ventanaFirefox.width}x${ventanaFirefox.height}`);
                            }
                        }
                    }
                });
            });

            procesoCaptura.stderr.on('data', (data) => {
                console.log(`🐛 Error PowerShell: ${data.toString()}`);
            });

            // Verificar que el hook se inicie en 5 segundos
            setTimeout(() => {
                if (!hookIniciado) {
                    console.log('⚠️ El hook no se inició en 5 segundos');
                    console.log('💡 Puede necesitar permisos de administrador');
                    console.log('🔧 Intenta ejecutar como administrador o usar el modo manual del navegador');
                }
            }, 5000);

            // Esperar input del usuario
            await this.preguntarSimple('');

            // Detener captura
            await fs.writeFile('stop_firefox_capture.tmp', 'stop');
            await this.esperar(500);
            procesoCaptura.kill();

            // Procesar clicks capturados y detectar valores
            for (const click of clicksCapturados) {
                // Intentar detectar el valor del elemento en esa posición
                const valor = await this.detectarValorEnPosicion(click.relX, click.relY);
                
                this.numerosDetectados.push({
                    valor: valor || `click_${clicksCapturados.indexOf(click) + 1}`,
                    tipo: this.esNumero(valor) ? 'numero' : 'apuesta',
                    metodo: 'manual_sistema_firefox',
                    coordenadas: {
                        relativas: { x: click.relX, y: click.relY },
                        absolutas: { x: click.x, y: click.y }
                    },
                    timestamp: click.timestamp
                });
            }

            console.log(`✅ ${clicksCapturados.length} clicks físicos grabados a nivel sistema`);
            console.log('📐 Convertidos automáticamente a coordenadas relativas');
            console.log('🔍 Valores detectados automáticamente');

            // Limpiar archivos temporales
            try {
                await fs.unlink('captura_firefox_sistema.ps1');
            } catch (e) {
                // Archivo ya eliminado
            }

        } catch (error) {
            console.log(`❌ Error en grabación manual a nivel sistema: ${error.message}`);
        }
    }

    async modoHibrido() {
        console.log('\n🔄 MODO HÍBRIDO FIREFOX: AUTO + MANUAL...');
        
        // Primero detección automática
        await this.deteccionAutomatica();
        const autoDetectados = this.numerosDetectados.length;
        
        // Luego manual
        console.log('\n👆 Ahora puedes agregar clicks manuales en Firefox...');
        const continuar = await this.preguntarSimple('¿Agregar clicks manuales? (s/n): ');
        
        if (continuar.toLowerCase().startsWith('s')) {
            await this.grabacionManualSistema();
        }
        
        console.log(`\n🎯 RESUMEN HÍBRIDO FIREFOX:`);
        console.log(`   🤖 Auto: ${autoDetectados}`);
        console.log(`   👆 Manual: ${this.numerosDetectados.length - autoDetectados}`);
        console.log(`   📊 Total: ${this.numerosDetectados.length}`);
        console.log(`   🦊 Optimizado para Firefox`);
    }

    async limpiarRegistros() {
        const cantidadAnterior = this.numerosDetectados.length;
        
        if (cantidadAnterior === 0) {
            console.log('⚠️ No hay registros para borrar');
            return;
        }
        
        console.log('\n🧹 LIMPIAR REGISTROS DETECTADOS');
        console.log('='.repeat(35));
        console.log(`📊 Tienes ${cantidadAnterior} coordenadas registradas`);
        console.log('');
        
        // Mostrar resumen de lo que se va a borrar
        const grupos = {};
        this.numerosDetectados.forEach(coord => {
            const metodo = coord.metodo || 'desconocido';
            if (!grupos[metodo]) grupos[metodo] = 0;
            grupos[metodo]++;
        });
        
        console.log('📋 Registros por método:');
        Object.keys(grupos).forEach(metodo => {
            const emoji = this.obtenerEmojiMetodo(metodo);
            console.log(`   ${emoji} ${metodo}: ${grupos[metodo]} coordenadas`);
        });
        console.log('');
        
        // Confirmación de seguridad
        console.log('⚠️ ADVERTENCIA: Esta acción NO se puede deshacer');
        console.log('💡 Si quieres conservar algunos registros, usa "exportar" primero');
        console.log('');
        
        const confirmacion = require('readline').createInterface({
            input: process.stdin,
            output: process.stdout
        });
        
        return new Promise((resolve) => {
            confirmacion.question('❓ ¿Estás seguro de borrar TODOS los registros? (escribe "SI" para confirmar): ', (respuesta) => {
                confirmacion.close();
                
                if (respuesta.trim().toUpperCase() === 'SI') {
                    // Limpiar todos los registros
                    this.numerosDetectados = [];
                    
                    console.log('');
                    console.log('✅ REGISTROS BORRADOS EXITOSAMENTE');
                    console.log(`🧹 ${cantidadAnterior} coordenadas eliminadas`);
                    console.log('🔄 Puedes empezar de nuevo con detección limpia');
                    console.log('💡 Usa "detectar", "manual" o "hotkeys" para grabar nuevas coordenadas');
                    
                    // Limpiar también archivos temporales relacionados
                    this.limpiarArchivosTemporales();
                    
                } else {
                    console.log('');
                    console.log('❌ Operación cancelada');
                    console.log('📊 Registros conservados intactos');
                }
                
                resolve();
            });
        });
    }

    obtenerEmojiMetodo(metodo) {
        const emojis = {
            'firefox_integrado': '🤖',
            'manual_firefox': '👆',
            'manual_firefox_mejorado': '🦊',
            'manual_sistema_firefox': '🖱️',
            'hotkeys_controlado': '⌨️',
            'simulado': '🔧',
            'desconocido': '❓'
        };
        return emojis[metodo] || '❓';
    }

    async limpiarSelectivo() {
        if (this.numerosDetectados.length === 0) {
            console.log('⚠️ No hay registros para borrar');
            return;
        }
        
        console.log('\n🎯 LIMPIEZA SELECTIVA DE REGISTROS');
        console.log('='.repeat(40));
        
        // Agrupar registros por método
        const grupos = {};
        this.numerosDetectados.forEach((coord, index) => {
            const metodo = coord.metodo || 'desconocido';
            if (!grupos[metodo]) grupos[metodo] = [];
            grupos[metodo].push({ coord, index });
        });
        
        console.log('📋 Tipos de registros disponibles:');
        Object.keys(grupos).forEach((metodo, i) => {
            const emoji = this.obtenerEmojiMetodo(metodo);
            console.log(`   ${i + 1}. ${emoji} ${metodo}: ${grupos[metodo].length} coordenadas`);
        });
        console.log(`   ${Object.keys(grupos).length + 1}. ❌ Cancelar`);
        console.log('');
        
        const seleccion = await this.preguntarSimple('🎯 ¿Qué tipo de registros quieres borrar? (número): ');
        const numeroSeleccion = parseInt(seleccion);
        
        if (isNaN(numeroSeleccion) || numeroSeleccion < 1 || numeroSeleccion > Object.keys(grupos).length + 1) {
            console.log('❌ Selección inválida');
            return;
        }
        
        if (numeroSeleccion === Object.keys(grupos).length + 1) {
            console.log('❌ Operación cancelada');
            return;
        }
        
        const metodoSeleccionado = Object.keys(grupos)[numeroSeleccion - 1];
        const registrosSeleccionados = grupos[metodoSeleccionado];
        
        console.log('');
        console.log(`🎯 Seleccionaste: ${this.obtenerEmojiMetodo(metodoSeleccionado)} ${metodoSeleccionado}`);
        console.log(`📊 Se borrarán ${registrosSeleccionados.length} coordenadas`);
        console.log('');
        
        // Mostrar qué se va a borrar
        console.log('📋 Coordenadas que se eliminarán:');
        registrosSeleccionados.slice(0, 5).forEach((item, i) => {
            const rel = item.coord.coordenadas.relativas;
            console.log(`   ${i + 1}. ${item.coord.valor}: (${rel.x.toFixed(3)}, ${rel.y.toFixed(3)})`);
        });
        
        if (registrosSeleccionados.length > 5) {
            console.log(`   ... y ${registrosSeleccionados.length - 5} más`);
        }
        console.log('');
        
        const confirmacion = await this.preguntarSimple(`❓ ¿Borrar ${registrosSeleccionados.length} registros de "${metodoSeleccionado}"? (escribe "SI"): `);
        
        if (confirmacion.trim().toUpperCase() === 'SI') {
            // Eliminar los registros seleccionados (en orden inverso para no afectar índices)
            const indicesAEliminar = registrosSeleccionados.map(item => item.index).sort((a, b) => b - a);
            
            indicesAEliminar.forEach(index => {
                this.numerosDetectados.splice(index, 1);
            });
            
            console.log('');
            console.log('✅ REGISTROS ELIMINADOS EXITOSAMENTE');
            console.log(`🧹 ${registrosSeleccionados.length} coordenadas de "${metodoSeleccionado}" eliminadas`);
            console.log(`📊 Registros restantes: ${this.numerosDetectados.length}`);
            
        } else {
            console.log('');
            console.log('❌ Operación cancelada');
            console.log('📊 Registros conservados intactos');
        }
    }

    async limpiarArchivosTemporales() {
        const archivosTemporales = [
            'captura_hotkeys.ps1',
            'captura_firefox_sistema.ps1',
            'captura_clicks_firefox_mejorado.ps1',
            'detectar_firefox_simple.ps1',
            'detectar_firefox_mejorado.ps1',
            'stop_hotkey_capture.tmp',
            'stop_firefox_capture.tmp',
            'stop_capture.tmp'
        ];
        
        let archivosEliminados = 0;
        
        for (const archivo of archivosTemporales) {
            try {
                await fs.unlink(archivo);
                archivosEliminados++;
            } catch (error) {
                // Archivo no existe, continuar
            }
        }
        
        if (archivosEliminados > 0) {
            console.log(`🧹 ${archivosEliminados} archivos temporales eliminados`);
        }
    }

    mostrarCoordenadasDetectadas() {
        if (this.numerosDetectados.length === 0) {
            console.log('❌ No hay coordenadas detectadas');
            console.log('💡 Usa "detectar", "manual", "hotkeys" o "hibrido" primero');
            console.log('🧹 Si tuviste registros antes, es posible que los hayas limpiado');
            return;
        }
        
        console.log('\n📊 COORDENADAS DETECTADAS EN FIREFOX:');
        console.log('='.repeat(40));
        
        const grupos = {};
        this.numerosDetectados.forEach(coord => {
            const tipo = coord.tipo;
            if (!grupos[tipo]) grupos[tipo] = [];
            grupos[tipo].push(coord);
        });
        
        Object.keys(grupos).forEach(tipo => {
            const emoji = tipo === 'numero' ? '📊' : '🎯';
            console.log(`\n${emoji} ${tipo.toUpperCase()}:`);
            
            grupos[tipo].forEach(coord => {
                const rel = coord.coordenadas.relativas;
                const metodo = coord.metodo === 'manual_firefox' ? '👆' : '🤖';
                const selector = coord.selector ? `[${coord.selector}]` : '';
                console.log(`   ${metodo} ${coord.valor}${selector}: (${rel.x.toFixed(3)}, ${rel.y.toFixed(3)})`);
            });
        });
    }

    async ejecutarClicksEnNavegador() {
        if (!this.estaConectado) {
            console.log('❌ Primero abre Firefox');
            return;
        }
        
        if (this.numerosDetectados.length === 0) {
            console.log('❌ No hay coordenadas para ejecutar');
            return;
        }
        
        console.log('\n🎯 EJECUTANDO CLICKS EN FIREFOX...');
        console.log(`🦊 ${this.numerosDetectados.length} clicks programados`);
        console.log('🔒 Navegación segura en modo incógnito');
        
        // Countdown
        for (let i = 3; i > 0; i--) {
            console.log(`⏰ Iniciando en ${i}...`);
            await this.esperar(1000);
        }
        
        let clicksExitosos = 0;
        
        for (const coord of this.numerosDetectados) {
            try {
                const rel = coord.coordenadas.relativas;
                const x = rel.x * this.dimensionesVentana.width;
                const y = rel.y * this.dimensionesVentana.height;
                
                console.log(`🎯 Clicking ${coord.valor} en (${Math.round(x)}, ${Math.round(y)})`);
                
                // Click optimizado para Firefox
                await this.pagina.mouse.click(x, y, { 
                    delay: Math.random() * 100 + 50,
                    button: 'left'
                });
                
                clicksExitosos++;
                
                // Pausa humana variable
                const pausa = Math.random() * 1000 + 600;
                await this.esperar(pausa);
                
            } catch (error) {
                console.log(`❌ Error clicking ${coord.valor}: ${error.message}`);
            }
        }
        
        console.log(`\n✅ Clicks completados en Firefox: ${clicksExitosos}/${this.numerosDetectados.length}`);
        console.log(`🦊 Ejecutado en modo ${this.modoIncognito ? 'incógnito' : 'normal'}`);
    }

    async exportarCoordenadasRelativas() {
        if (this.numerosDetectados.length === 0) {
            console.log('❌ No hay coordenadas para exportar');
            return;
        }
        
        const datos = {
            timestamp: new Date().toISOString(),
            navegador: 'firefox',
            modoIncognito: this.modoIncognito,
            metodo: 'firefox_integrado',
            dimensiones: this.dimensionesVentana,
            elementos: this.numerosDetectados,
            estadisticas: {
                total: this.numerosDetectados.length,
                numeros: this.numerosDetectados.filter(e => e.tipo === 'numero').length,
                apuestas: this.numerosDetectados.filter(e => e.tipo === 'apuesta').length,
                automaticos: this.numerosDetectados.filter(e => e.metodo === 'firefox_integrado').length,
                manuales: this.numerosDetectados.filter(e => e.metodo === 'manual_firefox').length,
                sistema: this.numerosDetectados.filter(e => e.metodo === 'manual_sistema_firefox').length
            }
        };
        
        try {
            await fs.writeFile('coordenadas_firefox_integrado.json', JSON.stringify(datos, null, 2));
            console.log('\n💾 ✅ Coordenadas Firefox exportadas:');
            console.log('   📁 coordenadas_firefox_integrado.json');
            console.log(`   🦊 ${datos.estadisticas.total} elementos de Firefox`);
            console.log(`   🔒 Modo incógnito: ${this.modoIncognito ? 'Activo' : 'Inactivo'}`);
            console.log('   🔄 Compatible con clicker adaptativo');
        } catch (error) {
            console.log(`❌ Error exportando: ${error.message}`);
        }
    }

    async configurarNavegador() {
        console.log('\n⚙️ CONFIGURACIÓN DE FIREFOX:');
        console.log('='.repeat(30));
        
        const ancho = await this.preguntarSimple(`📐 Ancho (actual ${this.dimensionesVentana.width}): `);
        const alto = await this.preguntarSimple(`📐 Alto (actual ${this.dimensionesVentana.height}): `);
        
        if (ancho) this.dimensionesVentana.width = parseInt(ancho);
        if (alto) this.dimensionesVentana.height = parseInt(alto);
        
        console.log(`✅ Nueva configuración Firefox: ${this.dimensionesVentana.width} x ${this.dimensionesVentana.height}`);
        
        if (this.navegador) {
            console.log('💡 Cierra y abre Firefox para aplicar cambios');
        }
    }

    alternarModoIncognito() {
        this.modoIncognito = !this.modoIncognito;
        const estado = this.modoIncognito ? '🔒 ACTIVADO' : '🌐 DESACTIVADO';
        console.log(`\n🔄 Modo incógnito: ${estado}`);
        
        if (this.navegador) {
            console.log('💡 Cierra y abre Firefox para aplicar el cambio');
        }
    }

    async ejecutarDiagnostico() {
        console.log('\n🔍 INICIANDO DIAGNÓSTICO DE FIREFOX...');
        console.log('='.repeat(40));
        
        try {
            const { ejecutarDiagnostico } = require('./diagnostico_firefox.js');
            await ejecutarDiagnostico();
        } catch (error) {
            console.log('❌ Error ejecutando diagnóstico:', error.message);
            console.log('💡 Asegúrate de que el archivo diagnostico_firefox.js esté disponible');
        }
    }

    async cerrarNavegador() {
        if (this.navegador) {
            console.log('🚪 Cerrando Firefox...');
            try {
                await this.navegador.close();
            } catch (error) {
                console.log(`⚠️ Error cerrando navegador: ${error.message}`);
            }
            this.navegador = null;
            this.contexto = null;
            this.pagina = null;
            this.estaConectado = false;
            this.estaInicializando = false;
            console.log('✅ Firefox cerrado');
        } else {
            console.log('⚠️ No hay navegador abierto');
        }
    }

    async obtenerPosicionVentanaFirefox() {
        try {
            // Script simplificado para obtener posición de Firefox
            const script = `
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    using System.Text;
    using System.Diagnostics;
    
    public class FirefoxHelper {
        [DllImport("user32.dll")]
        public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
        
        [StructLayout(LayoutKind.Sequential)]
        public struct RECT {
            public int Left; public int Top; public int Right; public int Bottom;
        }
    }
"@

# Buscar proceso de Firefox
$firefoxProcess = Get-Process | Where-Object { $_.ProcessName -like "*firefox*" -and $_.MainWindowTitle -ne "" } | Select-Object -First 1

if ($firefoxProcess) {
    $rect = New-Object FirefoxHelper+RECT
    $result = [FirefoxHelper]::GetWindowRect($firefoxProcess.MainWindowHandle, [ref]$rect)
    
    if ($result) {
        $width = $rect.Right - $rect.Left
        $height = $rect.Bottom - $rect.Top
        Write-Host "FIREFOX_FOUND:$($rect.Left),$($rect.Top),$width,$height"
    }
} else {
    Write-Host "FIREFOX_NOT_FOUND"
}
`;

            const fs = require('fs').promises;
            await fs.writeFile('detectar_firefox_simple.ps1', script);
            
            const resultado = await this.ejecutarScript('detectar_firefox_simple.ps1');
            
            if (resultado.includes('FIREFOX_FOUND:')) {
                const datos = resultado.split('FIREFOX_FOUND:')[1].split(',');
                const ventana = {
                    x: parseInt(datos[0]),
                    y: parseInt(datos[1]),
                    width: parseInt(datos[2]),
                    height: parseInt(datos[3])
                };
                
                await fs.unlink('detectar_firefox_simple.ps1');
                return ventana;
            }
            
            return null;
        } catch (error) {
            console.log(`⚠️ Error detectando ventana Firefox: ${error.message}`);
            return null;
        }
    }

    async obtenerPosicionVentanaFirefoxMejorada() {
        try {
            // Script mejorado para obtener posición de Firefox con múltiples métodos
            const script = `
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    using System.Text;
    using System.Diagnostics;
    
    public class FirefoxHelperMejorado {
        [DllImport("user32.dll")]
        public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
        
        [DllImport("user32.dll")]
        public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
        
        [DllImport("user32.dll")]
        public static extern bool IsWindowVisible(IntPtr hWnd);
        
        [StructLayout(LayoutKind.Sequential)]
        public struct RECT {
            public int Left; public int Top; public int Right; public int Bottom;
        }
    }
"@

# Método 1: Buscar por nombre de proceso específico
$firefoxProcesses = @()

# Buscar diferentes variantes de Firefox
$nombresProcesos = @("firefox", "Firefox", "firefox.exe", "mozilla", "gecko")

foreach ($nombre in $nombresProcesos) {
    try {
        $procesos = Get-Process -Name $nombre -ErrorAction SilentlyContinue | Where-Object { 
            $_.MainWindowTitle -ne "" -and $_.MainWindowHandle -ne [IntPtr]::Zero 
        }
        $firefoxProcesses += $procesos
    } catch {
        # Continuar con el siguiente nombre
    }
}

# Método 2: Buscar por título de ventana
$allProcesses = Get-Process | Where-Object { $_.MainWindowTitle -ne "" }
foreach ($proceso in $allProcesses) {
    $titulo = $proceso.MainWindowTitle.ToLower()
    if ($titulo.Contains("firefox") -or $titulo.Contains("mozilla") -or 
        $titulo.Contains("lightning roulette") -or $titulo.Contains("evolution")) {
        $firefoxProcesses += $proceso
    }
}

# Eliminar duplicados
$firefoxProcesses = $firefoxProcesses | Sort-Object Id | Get-Unique -AsString

$ventanaEncontrada = $false

foreach ($firefoxProcess in $firefoxProcesses) {
    try {
        # Verificar que la ventana sea visible
        $esVisible = [FirefoxHelperMejorado]::IsWindowVisible($firefoxProcess.MainWindowHandle)
        
        if ($esVisible) {
            $rect = New-Object FirefoxHelperMejorado+RECT
            $result = [FirefoxHelperMejorado]::GetWindowRect($firefoxProcess.MainWindowHandle, [ref]$rect)
            
            if ($result) {
                $width = $rect.Right - $rect.Left
                $height = $rect.Bottom - $rect.Top
                
                # Verificar que tiene dimensiones válidas (no minimizada)
                if ($width -gt 100 -and $height -gt 100) {
                    # Obtener título de ventana para validación adicional
                    $tituloBuffer = New-Object System.Text.StringBuilder 512
                    [FirefoxHelperMejorado]::GetWindowText($firefoxProcess.MainWindowHandle, $tituloBuffer, 512)
                    $titulo = $tituloBuffer.ToString()
                    
                    Write-Host "FIREFOX_FOUND_MEJORADO:$($rect.Left),$($rect.Top),$width,$height,$($firefoxProcess.ProcessName),$titulo"
                    $ventanaEncontrada = $true
                    break
                }
            }
        }
    } catch {
        # Continuar con el siguiente proceso
        continue
    }
}

if (-not $ventanaEncontrada) {
    # Método 3: Buscar ventanas con clase específica de Firefox
    try {
        Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            using System.Text;
            
            public class WindowFinder {
                [DllImport("user32.dll")]
                public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
                
                [DllImport("user32.dll")]
                public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
                
                [StructLayout(LayoutKind.Sequential)]
                public struct RECT {
                    public int Left; public int Top; public int Right; public int Bottom;
                }
            }
"@
        
        # Clases de ventana comunes de Firefox
        $clasesFirefox = @("MozillaWindowClass", "Firefox", "Mozilla")
        
        foreach ($clase in $clasesFirefox) {
            $handle = [WindowFinder]::FindWindow($clase, $null)
            if ($handle -ne [IntPtr]::Zero) {
                $rect = New-Object WindowFinder+RECT
                $result = [WindowFinder]::GetWindowRect($handle, [ref]$rect)
                
                if ($result) {
                    $width = $rect.Right - $rect.Left
                    $height = $rect.Bottom - $rect.Top
                    
                    if ($width -gt 100 -and $height -gt 100) {
                        Write-Host "FIREFOX_FOUND_MEJORADO:$($rect.Left),$($rect.Top),$width,$height,clase_$clase,Firefox_por_clase"
                        $ventanaEncontrada = $true
                        break
                    }
                }
            }
        }
    } catch {
        # Método de clase falló
    }
}

if (-not $ventanaEncontrada) {
    Write-Host "FIREFOX_NOT_FOUND_MEJORADO"
}
`;

            const fs = require('fs').promises;
            await fs.writeFile('detectar_firefox_mejorado.ps1', script);
            
            const resultado = await this.ejecutarScript('detectar_firefox_mejorado.ps1');
            
            if (resultado.includes('FIREFOX_FOUND_MEJORADO:')) {
                const datos = resultado.split('FIREFOX_FOUND_MEJORADO:')[1].split(',');
                const ventana = {
                    x: parseInt(datos[0]),
                    y: parseInt(datos[1]),
                    width: parseInt(datos[2]),
                    height: parseInt(datos[3]),
                    procesoNombre: datos[4] || 'firefox',
                    titulo: datos[5] || 'Firefox'
                };
                
                await fs.unlink('detectar_firefox_mejorado.ps1');
                return ventana;
            }
            
            // Fallback al método original
            console.log('🔄 Intentando método de detección original...');
            return await this.obtenerPosicionVentanaFirefox();
            
        } catch (error) {
            console.log(`⚠️ Error detectando ventana Firefox mejorada: ${error.message}`);
            
            // Último intento con método original
            try {
                return await this.obtenerPosicionVentanaFirefox();
            } catch (e) {
                console.log(`❌ Todos los métodos de detección fallaron: ${e.message}`);
                return null;
            }
        }
    }

    async detectarValorEnPosicion(relX, relY) {
        try {
            // Convertir coordenadas relativas a absolutas dentro del navegador
            const x = relX * this.dimensionesVentana.width;
            const y = relY * this.dimensionesVentana.height;
            
            // Usar Playwright para detectar elemento en esa posición
            const valor = await this.pagina.evaluate((x, y) => {
                const elemento = document.elementFromPoint(x, y);
                if (!elemento) return null;
                
                // Intentar múltiples formas de obtener el valor
                let texto = elemento.textContent?.trim() || 
                           elemento.getAttribute('data-number') || 
                           elemento.getAttribute('data-value') ||
                           elemento.title ||
                           elemento.innerHTML?.replace(/<[^>]*>/g, '').trim();
                
                // Limpiar para obtener números
                const numeroLimpio = texto?.replace(/[^0-9]/g, '');
                if (numeroLimpio && numeroLimpio.length > 0) {
                    return numeroLimpio;
                }
                
                // Si no es número, detectar apuestas exteriores
                const textoLower = texto?.toLowerCase() || '';
                if (textoLower.includes('red') || textoLower.includes('rojo')) return 'RED';
                if (textoLower.includes('black') || textoLower.includes('negro')) return 'BLACK';
                if (textoLower.includes('even') || textoLower.includes('par')) return 'EVEN';
                if (textoLower.includes('odd') || textoLower.includes('impar')) return 'ODD';
                if (textoLower.includes('1st') || textoLower.includes('primera')) return '1st 12';
                if (textoLower.includes('2nd') || textoLower.includes('segunda')) return '2nd 12';
                if (textoLower.includes('3rd') || textoLower.includes('tercera')) return '3rd 12';
                
                return texto || 'desconocido';
            }, x, y);
            
            return valor;
        } catch (error) {
            return null;
        }
    }

    async ejecutarScript(nombreScript) {
        return new Promise((resolve, reject) => {
            const { spawn } = require('child_process');
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

    esNumero(valor) {
        const num = parseInt(valor);
        return !isNaN(num) && num >= 0 && num <= 36;
    }

    async esperar(ms) {
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
async function iniciarDetectorFirefoxIntegrado() {
    // Verificar si ya hay una instancia ejecutándose
    if (instanciaGlobal && instanciaGlobal.navegador) {
        console.log('⚠️ DETECTOR FIREFOX YA ESTÁ EJECUTÁNDOSE');
        console.log('💡 Usa la ventana existente o ciérrala primero');
        console.log('🔧 Si está colgado, mata el proceso Node.js y reinicia');
        return;
    }
    
    const detector = new DetectorFirefoxIntegrado();
    
    try {
        await detector.init();
    } catch (error) {
        console.error(`❌ Error: ${error.message}`);
        // Limpiar en caso de error
        instanciaGlobal = null;
    } finally {
        // Asegurar limpieza al salir
        process.on('SIGINT', async () => {
            console.log('\n🛑 Cerrando detector Firefox...');
            if (detector && detector.navegador) {
                await detector.cerrarNavegador();
            }
            instanciaGlobal = null;
            process.exit(0);
        });
    }
}

// Ejecutar si se llama directamente
if (require.main === module) {
    iniciarDetectorFirefoxIntegrado();
}

module.exports = { DetectorFirefoxIntegrado, iniciarDetectorFirefoxIntegrado }; 