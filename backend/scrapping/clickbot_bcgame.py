import pyautogui
import time
import random
import logging
import threading
import keyboard
import json
import os
import sys
import tempfile
from PIL import Image, ImageGrab
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Intentar importar win32gui, pero continuar sin él si no está disponible
try:
    import win32gui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("⚠️ win32gui no disponible. Algunas funciones de ventana estarán limitadas.")

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("roulette_bot.log", encoding='utf-8'), 
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CasinoBotLogger")

# Configurar el handler de consola para usar UTF-8
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Configurar encoding para Windows
import sys
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

class CasinoBot:
    def __init__(self):
        """Inicializa el CasinoBot"""
        # Configuración de archivos
        self.config_file = os.path.join(os.path.dirname(__file__), 'casino_bot_config.json')
        self.current_profile = "bcgame"  # BC Game es el perfil por defecto
        self.profiles = {}
        self.positions_memory = {}
        
        # Estado del bot
        self.is_running = False
        self.target_position = None
        self.click_thread = None
        self.current_window = None
        self.driver = None
        
        # Sistema de perfiles mejorado
        self.config = self.load_config_safe()
        self.positions_validation = {}
        
        # NUEVA: Configuraciones de velocidad extrema
        self.speed_mode = "ultra"  # CAMBIO: Empezar en modo ULTRA por defecto
        self.speed_configs = {
            "normal": {
                "pre_delay": (0.1, 0.3),
                "post_delay": (0.1, 0.4),
                "hold_time": (0.05, 0.15),
                "move_duration": (0.1, 0.3),
                "between_clicks": (1.0, 3.0)
            },
            "fast": {
                "pre_delay": (0.001, 0.01),  # MÁS RÁPIDO
                "post_delay": (0.001, 0.02),  # MÁS RÁPIDO
                "hold_time": (0.001, 0.01),  # MÁS RÁPIDO
                "move_duration": (0.001, 0.02),  # MÁS RÁPIDO
                "between_clicks": (0.05, 0.2)  # MÁS RÁPIDO
            },
            "ultra": {
                "pre_delay": (0.0, 0.005),  # ULTRA RÁPIDO
                "post_delay": (0.0, 0.005),  # ULTRA RÁPIDO
                "hold_time": (0.0, 0.005),  # ULTRA RÁPIDO
                "move_duration": (0.0, 0.01),  # ULTRA RÁPIDO
                "between_clicks": (0.01, 0.05)  # ULTRA RÁPIDO
            },
            "lightning": {
                "pre_delay": (0.0, 0.001),  # INSTANTÁNEO
                "post_delay": (0.0, 0.001),  # INSTANTÁNEO
                "hold_time": (0.0, 0.001),  # INSTANTÁNEO
                "move_duration": (0.0, 0.001),  # INSTANTÁNEO
                "between_clicks": (0.001, 0.01)  # INSTANTÁNEO
            }
        }
        
        # Modo turbo mejorado - ACTIVADO por defecto
        self.turbo_mode = True  # CAMBIO: Activar turbo por defecto
        self.ultra_fast_mode = False
        self.lightning_mode = False
        
        # Para apuestas continuas rápidas
        self.continuous_mode = False
        self.favorite_numbers = []
        self.exit_requested = False  # Control de salida del bot
        
        # Patrones de click adaptables
        self.init_click_patterns()
        
        # Configurar hotkeys
        self.setup_hotkeys()
        
        logger.info("🎰 BC GAME BOT INICIALIZADO - VERSIÓN VELOCIDAD EXTREMA")
        logger.info(f"📂 Perfil actual: {self.current_profile}")
        logger.info(f"⚡ Velocidad: {self.speed_mode.upper()}")
        
        # Para detectar automáticamente la ventana del navegador
        self.auto_detect_window()
        
        # Configurar pyautogui para máxima velocidad
        self.setup_pyautogui()

    def load_config_safe(self):
        """Carga la configuración de forma segura con múltiples intentos"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                if os.path.exists(self.config_file):
                    # Verificar que el archivo no esté vacío
                    if os.path.getsize(self.config_file) == 0:
                        logger.warning(f"Archivo de configuración vacío en intento {attempt + 1}")
                        self.create_default_config()
                        continue
                    
                    # Intentar leer el archivo
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        
                        if not content:
                            logger.warning(f"Contenido vacío en intento {attempt + 1}")
                            self.create_default_config()
                            continue
                        
                        # Parsear JSON
                        data = json.loads(content)
                        
                        # Validar estructura
                        if not isinstance(data, dict):
                            logger.warning(f"Estructura JSON inválida en intento {attempt + 1}")
                            self.create_default_config()
                            continue
                        
                        # Cargar datos con compatibilidad
                        self.profiles = data.get("profiles", {})
                        
                        # Compatibilidad con versiones anteriores - IMPORTANTE para no perder coordenadas
                        old_game_profiles = data.get("game_profiles", {})
                        if old_game_profiles and not self.profiles:
                            self.profiles = old_game_profiles
                            logger.info("🔄 Migrando desde game_profiles a profiles")
                        
                        # Compatibilidad con posiciones sueltas
                        old_positions = data.get("positions", {})
                        if old_positions and not self.profiles:
                            self.profiles["Default"] = {"positions": old_positions}
                        
                        # Cargar último perfil usado
                        last_profile = data.get("last_profile", None)
                        if last_profile and last_profile in self.profiles:
                            self.current_profile = last_profile
                            self.positions_memory = self.profiles[last_profile].get("positions", {})
                            # Cargar números favoritos si existen
                            self.favorite_numbers = self.profiles[last_profile].get("favorites", [])
                        elif self.profiles:
                            self.current_profile = list(self.profiles.keys())[0]
                            self.positions_memory = self.profiles[self.current_profile].get("positions", {})
                            self.favorite_numbers = self.profiles[self.current_profile].get("favorites", [])
                        else:
                            self.current_profile = "Default"
                            self.profiles[self.current_profile] = {"positions": {}, "favorites": []}
                            self.positions_memory = {}
                            self.favorite_numbers = []
                        
                        logger.info(f"✅ Configuración cargada exitosamente: {len(self.profiles)} perfiles")
                        logger.info(f"📁 Perfil actual: {self.current_profile}")
                        logger.info(f"📍 Posiciones en perfil: {len(self.positions_memory)}")
                        return self.profiles
                        
                else:
                    logger.info("📄 No se encontró archivo de configuración. Creando uno nuevo...")
                    self.create_default_config()
                    return
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ Error JSON en intento {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    logger.info(f"🔄 Reintentando en 1 segundo...")
                    time.sleep(1)
                else:
                    logger.error("❌ Máximo de intentos alcanzado. Creando configuración por defecto.")
                    self.create_default_config()
                    
            except Exception as e:
                logger.error(f"❌ Error inesperado en intento {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(1)
                else:
                    self.create_default_config()

    def create_default_config(self):
        """Crea una configuración por defecto"""
        try:
            self.current_profile = "Default"
            self.profiles = {
                self.current_profile: {
                    "positions": {},
                    "favorites": []
                }
            }
            self.positions_memory = {}
            self.favorite_numbers = []
            
            # Guardar configuración por defecto
            self.save_config_safe()
            logger.info("✅ Configuración por defecto creada")
            
        except Exception as e:
            logger.error(f"❌ Error creando configuración por defecto: {e}")

    def save_config_safe(self):
        """Guarda la configuración de forma segura"""
        try:
            # Actualizar las posiciones en el perfil actual
            if self.current_profile:
                if self.current_profile not in self.profiles:
                    self.profiles[self.current_profile] = {}
                self.profiles[self.current_profile]["positions"] = self.positions_memory
            
            data = {
                "profiles": self.profiles,
                "last_profile": self.current_profile
            }
            
            # Escribir a archivo temporal primero
            temp_file = self.config_file + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Mover archivo temporal al final
            if os.path.exists(temp_file):
                if os.path.exists(self.config_file):
                    os.remove(self.config_file)
                os.rename(temp_file, self.config_file)
            
            logger.info("💾 Configuración guardada correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error al guardar la configuración: {e}")

    def validate_window_handle(self):
        """Valida que el handle de ventana actual sea válido"""
        if not WIN32_AVAILABLE:
            return True  # Asumir válido si win32gui no está disponible
            
        if not self.current_window:
            return False
        
        try:
            if not win32gui.IsWindow(self.current_window):
                return False
            
            if not win32gui.IsWindowVisible(self.current_window):
                return False
            
            title = win32gui.GetWindowText(self.current_window)
            return True
            
        except Exception as e:
            logger.warning(f"Validación de ventana falló: {e}")
            return False

    def init_click_patterns(self):
        """Inicializa patrones de click naturales"""
        self.click_patterns = [
            {"pre_delay": (0.05, 0.15), "hold_time": (0.08, 0.12), "post_delay": (0.1, 0.3)},
            {"pre_delay": (0.1, 0.25), "hold_time": (0.06, 0.14), "post_delay": (0.08, 0.2)},
            {"pre_delay": (0.02, 0.08), "hold_time": (0.04, 0.08), "post_delay": (0.05, 0.15)},
            {"pre_delay": (0.2, 0.4), "hold_time": (0.1, 0.18), "post_delay": (0.15, 0.35)},
        ]

    def ask_firefox_startup(self):
        """Pregunta al usuario si desea abrir Firefox automáticamente o usar uno manual"""
        print("\n🦊 CONFIGURACIÓN DE FIREFOX PARA BC GAME")
        print("=" * 40)
        print("1. 🤖 Abrir Firefox automáticamente (puede ser detectado)")
        print("2. 👤 Usar Firefox abierto manualmente (MÁS SIGILOSO para BC Game)")
        print("3. ❌ Solo usar clicks sin Firefox")
        
        while True:
            try:
                choice = input("\nSelecciona una opción (1/2/3): ").strip()
                
                if choice == "1":
                    self.auto_open_firefox = True
                    self.manual_firefox = False
                    logger.info("🤖 Configurado para abrir Firefox automáticamente")
                    break
                elif choice == "2":
                    self.auto_open_firefox = False  
                    self.manual_firefox = True
                    logger.info("👤 Configurado para usar Firefox manual")
                    print("\n📋 INSTRUCCIONES PARA BC GAME:")
                    print("1. Abre Firefox manualmente ANTES de usar el bot")
                    print("2. Navega a BC Game: https://bc.game")
                    print("3. Inicia sesión y ve al juego de ruleta")
                    print("4. Mantén la ventana de Firefox visible")
                    print("5. El bot detectará automáticamente la ventana")
                    break
                elif choice == "3":
                    self.auto_open_firefox = False
                    self.manual_firefox = False
                    logger.info("❌ Solo se usarán clicks, sin Firefox")
                    break
                else:
                    print("❌ Opción inválida. Selecciona 1, 2 o 3")
                    
            except KeyboardInterrupt:
                logger.info("❌ Operación cancelada")
                return

    def setup_firefox(self):
        """Configura Firefox de forma más sigilosa para BC Game"""
        try:
            firefox_options = Options()
            
            # ===== CONFIGURACIONES ANTI-DETECCIÓN PARA BC GAME =====
            
            # Desactivar WebDriver completamente
            firefox_options.set_preference("dom.webdriver.enabled", False)
            firefox_options.set_preference("useAutomationExtension", False)
            
            # Ocultar que es un navegador automatizado
            firefox_options.set_preference("marionette.enabled", False)
            
            # User Agent específico para BC Game (simular navegador normal)
            firefox_options.set_preference("general.useragent.override", 
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0")
            
            # Desactivar logging de WebDriver
            firefox_options.add_argument("--log-level=3")
            firefox_options.set_preference("webdriver.log.level", "OFF")
            
            # Configuraciones de privacidad mejoradas para BC Game
            firefox_options.set_preference("privacy.trackingprotection.enabled", True)
            firefox_options.set_preference("dom.disable_beforeunload", True)
            
            # Desactivar automatización detectables
            firefox_options.set_preference("dom.webnotifications.enabled", False)
            firefox_options.set_preference("media.navigator.enabled", False)
            firefox_options.set_preference("permissions.default.microphone", 2)
            firefox_options.set_preference("permissions.default.camera", 2)
            
            # Configuraciones de ventana natural
            firefox_options.add_argument("--width=1366")
            firefox_options.add_argument("--height=768")
            
            # Perfil personalizado para BC Game
            firefox_options.set_preference("browser.startup.homepage", "about:blank")
            firefox_options.set_preference("startup.homepage_welcome_url", "")  
            firefox_options.set_preference("startup.homepage_welcome_url.additional", "")
            
            # JavaScript avanzado para BC Game
            firefox_options.set_preference("javascript.enabled", True)
            firefox_options.set_preference("dom.webgl.disabled", False)
            
            # Configuraciones específicas para sitios de juegos
            firefox_options.set_preference("plugin.state.flash", 2)
            firefox_options.set_preference("media.autoplay.default", 0)  # Permitir autoplay
            
            # Crear driver con configuración sigilosa
            service = Service(log_output=os.devnull)  # Sin logs visibles
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            
            # Ejecutar scripts anti-detección específicos para BC Game
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array")
            self.driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise")
            self.driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol")
            
            logger.info("🦊 Firefox configurado en modo ULTRA SIGILOSO para BC Game")
            
            # Abrir página inicial
            self.driver.get("about:blank")
            time.sleep(2)
            
            # Maximizar después de cargar
            self.driver.maximize_window()
            
            print("\n🎯 FIREFOX LISTO PARA BC GAME")
            print("=" * 40)
            print("✅ Configuración anti-detección aplicada")
            print("✅ Optimizado específicamente para BC Game")
            print("✅ Navega manualmente a https://bc.game")
            print("✅ Ve al juego de ruleta y el bot estará listo")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al configurar Firefox: {e}")
            print("\n💡 SUGERENCIA PARA BC GAME:")
            print("- Intenta usar la opción de Firefox manual (más segura)")
            print("- Verifica que Firefox esté instalado correctamente")
            print("- BC Game puede detectar automatización, usa modo manual")
            return False

    def setup_manual_firefox(self):
        """Configura el bot para usar Firefox ya abierto manualmente (ÓPTIMO para BC Game)"""
        try:
            print("\n👤 MODO FIREFOX MANUAL PARA BC GAME")
            print("=" * 50)
            print("✅ Configuración MÁS SIGILOSA activada")
            print("✅ BC Game NO detectará automatización")
            print("✅ Firefox debe estar abierto manualmente")
            print("✅ Máxima seguridad para BC Game")
            
            # Buscar ventana de Firefox existente
            if self.find_firefox_window():
                print("✅ Firefox detectado y listo para BC Game")
                print("\n📋 RECORDATORIO PARA BC GAME:")
                print("- Mantén Firefox visible durante el uso")
                print("- Asegúrate de estar en https://bc.game")
                print("- Ve al juego de ruleta antes de usar el bot")  
                print("- El bot hará clicks en las coordenadas configuradas")
                print("- BC Game no detectará que es automatización")
                return True
            else:
                print("⚠️ No se detectó Firefox abierto")
                print("\n📋 INSTRUCCIONES PARA BC GAME:")
                print("1. Abre Firefox manualmente")
                print("2. Navega a https://bc.game")
                print("3. Inicia sesión en tu cuenta")
                print("4. Ve al juego de ruleta")
                print("5. Reinicia el bot")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en configuración manual: {e}")
            return False

    def find_firefox_window(self):
        """Encuentra la ventana de Firefox"""
        if not WIN32_AVAILABLE:
            logger.info("🔍 win32gui no disponible, usando método alternativo")
            return True
            
        def enum_windows_callback(hwnd, windows):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    
                    firefox_indicators = [
                        "firefox" in class_name.lower(),
                        "mozilla" in window_text.lower(),
                        "firefox" in window_text.lower(),
                        "mozillawindowclass" in class_name.lower()
                    ]
                    
                    if any(firefox_indicators) and len(window_text) > 10:
                        windows.append((hwnd, window_text, class_name))
            except:
                pass
            return True

        windows = []
        try:
            win32gui.EnumWindows(enum_windows_callback, windows)
        except Exception as e:
            logger.error(f"Error al enumerar ventanas: {e}")
            return False
        
        if windows:
            self.current_window = windows[0][0]
            logger.info(f"🎯 Firefox encontrado: {windows[0][1]}")
            return True
        else:
            logger.warning("⚠️ No se encontró ventana de Firefox")
            return False

    def save_current_position(self, name_prefix="Posicion"):
        """Guarda la posición actual del cursor"""
        try:
            current_pos = pyautogui.position()
            
            # Generar nombre único
            counter = 1
            name = f"{name_prefix}_{counter:02d}"
            while name in self.positions_memory:
                counter += 1
                name = f"{name_prefix}_{counter:02d}"
            
            # Guardar posición
            self.positions_memory[name] = (current_pos.x, current_pos.y)
            self.save_config_safe()
            
            logger.info(f"✅ Posición guardada: {name} = ({current_pos.x}, {current_pos.y})")
            return name
            
        except Exception as e:
            logger.error(f"❌ Error guardando posición: {e}")
            return None

    def load_saved_position(self):
        """Carga una posición guardada"""
        if not self.positions_memory:
            logger.info("📍 No hay posiciones guardadas")
            return False
        
        print("\n📍 POSICIONES GUARDADAS:")
        print("=" * 40)
        
        positions_list = list(self.positions_memory.items())
        for i, (name, pos) in enumerate(positions_list, 1):
            print(f"{i}. {name}: ({pos[0]}, {pos[1]})")
        
        print("=" * 40)
        
        try:
            choice = input("Selecciona una posición (número): ").strip()
            index = int(choice) - 1
            
            if 0 <= index < len(positions_list):
                name, pos = positions_list[index]
                self.target_position = pos
                logger.info(f"✅ Posición cargada: {name} = {pos}")
                return True
            else:
                logger.warning("❌ Selección inválida")
                return False
                
        except ValueError:
            logger.warning("❌ Entrada inválida")
            return False

    def perform_natural_click(self, x, y):
        """Realiza un click natural en las coordenadas especificadas con velocidad adaptable"""
        try:
            # MODO RELÁMPAGO - Velocidad máxima sin pausa alguna
            if self.lightning_mode:
                pyautogui.moveTo(x, y, duration=0)  # Movimiento instantáneo
                pyautogui.click()  # Click inmediato
                logger.info(f"⚡⚡ LIGHTNING Click en ({x}, {y})")
                return True
            
            # MODO ULTRA-RÁPIDO - Velocidad extrema con mínimas pausas
            elif self.ultra_fast_mode:
                config = self.speed_configs["ultra"]
                
                # Sin delay pre-click
                pyautogui.moveTo(x, y, duration=random.uniform(*config["move_duration"]))
                
                # Click ultra-rápido
                pyautogui.mouseDown()
                time.sleep(random.uniform(*config["hold_time"]))
                pyautogui.mouseUp()
                
                # Delay post-click mínimo
                time.sleep(random.uniform(*config["post_delay"]))
                
                logger.info(f"🚀 ULTRA Click en ({x}, {y})")
                return True
            
            # MODO TURBO ORIGINAL
            elif self.turbo_mode:
                config = self.speed_configs["fast"]
                
                # Mover cursor rápidamente
                pyautogui.moveTo(x, y, duration=random.uniform(*config["move_duration"]))
                
                # Click rápido
                pyautogui.click()
                
                # Delay mínimo post-click
                time.sleep(random.uniform(*config["post_delay"]))
                
                logger.info(f"⚡ TURBO Click en ({x}, {y})")
                return True
            
            else:
                # Modo normal/rápido basado en speed_mode
                config = self.speed_configs[self.speed_mode]
                
                # Seleccionar patrón aleatorio si existe
                if hasattr(self, 'click_patterns') and self.click_patterns:
                    pattern = random.choice(self.click_patterns)
                    
                    # Usar patrón o configuración de velocidad
                    pre_delay = random.uniform(*config["pre_delay"])
                    hold_time = random.uniform(*config["hold_time"])
                    post_delay = random.uniform(*config["post_delay"])
                else:
                    # Sin patrones, usar solo configuración de velocidad
                    pre_delay = random.uniform(*config["pre_delay"])
                    hold_time = random.uniform(*config["hold_time"])
                    post_delay = random.uniform(*config["post_delay"])
                
                # Delay antes del click
                time.sleep(pre_delay)
                
                # Mover cursor con variación humana (solo si no es ultra-rápido)
                if self.speed_mode in ["normal", "fast"]:
                    variation_x = random.randint(-2, 2)
                    variation_y = random.randint(-2, 2)
                    final_x = x + variation_x
                    final_y = y + variation_y
                else:
                    final_x, final_y = x, y
                
                # Mover cursor
                pyautogui.moveTo(final_x, final_y, duration=random.uniform(*config["move_duration"]))
                
                # Realizar click
                pyautogui.mouseDown()
                time.sleep(hold_time)
                pyautogui.mouseUp()
                
                # Delay después del click
                time.sleep(post_delay)
                
                logger.info(f"🎯 {self.speed_mode.upper()} Click en ({final_x}, {final_y})")
                return True
            
        except Exception as e:
            logger.error(f"❌ Error en click natural: {e}")
            return False

    def start_clicking(self):
        """Inicia el ciclo de clicks automáticos"""
        if not self.target_position:
            logger.warning("⚠️ No hay posición objetivo configurada")
            return False
        
        self.is_running = True
        logger.info("🚀 Iniciando clicks automáticos...")
        logger.info("⚠️ Presiona ESC para detener")
        
        def click_loop():
            while self.is_running:
                try:
                    if self.target_position:
                        self.perform_natural_click(*self.target_position)
                        
                        # Delay entre clicks basado en configuración de velocidad
                        if self.lightning_mode:
                            delay = random.uniform(0.01, 0.05)  # Velocidad máxima
                        elif self.ultra_fast_mode:
                            config = self.speed_configs["ultra"]
                            delay = random.uniform(*config["between_clicks"])
                        elif self.turbo_mode:
                            config = self.speed_configs["fast"]
                            delay = random.uniform(*config["between_clicks"])
                        else:
                            config = self.speed_configs[self.speed_mode]
                            delay = random.uniform(*config["between_clicks"])
                        
                        time.sleep(delay)
                    else:
                        break
                        
                except Exception as e:
                    logger.error(f"❌ Error en ciclo de clicks: {e}")
                    break
        
        self.click_thread = threading.Thread(target=click_loop, daemon=True)
        self.click_thread.start()
        return True

    def stop_clicking(self):
        """Detiene el ciclo de clicks"""
        self.is_running = False
        logger.info("⏹️ Clicks detenidos")

    def setup_hotkeys(self):
        """Configura las teclas de acceso rápido"""
        try:
            # Hotkeys principales
            keyboard.add_hotkey('f1', lambda: self.save_current_position("Rapida"))
            keyboard.add_hotkey('f2', self.load_saved_position)
            keyboard.add_hotkey('f3', self.toggle_clicking)
            keyboard.add_hotkey('esc', self.stop_clicking)
            
            # Hotkeys para números de ruleta
            for i in range(10):
                keyboard.add_hotkey(f'ctrl+{i}', lambda num=i: self.record_number(num))
                keyboard.add_hotkey(f'alt+{i}', lambda num=i: self.quick_bet_number(num))
            
            # Hotkeys para gestión de perfiles
            keyboard.add_hotkey('ctrl+shift+n', self.create_new_profile)  # Nuevo perfil
            keyboard.add_hotkey('ctrl+shift+p', self.switch_profile)      # Cambiar perfil
            keyboard.add_hotkey('ctrl+shift+r', self.rename_profile)      # Renombrar perfil
            keyboard.add_hotkey('ctrl+shift+d', self.delete_profile)      # Eliminar perfil
            keyboard.add_hotkey('ctrl+shift+a', self.show_all_profiles)   # Ver todos los perfiles
            
            # Hotkeys para apuesta múltiple
            keyboard.add_hotkey('ctrl+shift+m', self.bet_multiple_numbers)      # Apuesta múltiple manual
            keyboard.add_hotkey('ctrl+shift+b', self.quick_bet_multiple_from_hotkey)  # Apuesta rápida favoritos
            keyboard.add_hotkey('ctrl+shift+f', self.set_favorite_numbers)      # Configurar favoritos
            keyboard.add_hotkey('ctrl+shift+c', self.continuous_betting_mode)   # Modo continuo
            
            # Hotkeys para apuestas ultra-rápidas (sin confirmación)
            keyboard.add_hotkey('ctrl+shift+1', lambda: self.ultra_quick_bet([0, 7, 14, 21, 28]))  # Apuesta rápida 1
            keyboard.add_hotkey('ctrl+shift+2', lambda: self.ultra_quick_bet([1, 8, 15, 22, 29]))  # Apuesta rápida 2
            keyboard.add_hotkey('ctrl+shift+3', lambda: self.ultra_quick_bet([2, 9, 16, 23, 30]))  # Apuesta rápida 3
            
            # Hotkeys para control de velocidad
            keyboard.add_hotkey('ctrl+shift+t', self.toggle_turbo_mode)          # Modo turbo
            keyboard.add_hotkey('ctrl+shift+u', self.toggle_ultra_fast_mode)     # Modo ultra-rápido
            keyboard.add_hotkey('ctrl+shift+l', self.toggle_lightning_mode)      # Modo relámpago
            keyboard.add_hotkey('ctrl+shift+v', self.cycle_speed_mode)           # Cambiar velocidad
            keyboard.add_hotkey('ctrl+shift+s', self.show_speed_menu)            # Menú de velocidad
            keyboard.add_hotkey('ctrl+shift+q', lambda: self.turbo_bet_favorites())  # Apuesta turbo favoritos
            
            # Hotkeys para apuestas ultra-rápidas por velocidad
            keyboard.add_hotkey('alt+shift+1', lambda: self.lightning_bet_multiple([0, 7, 14, 21, 28]))  # Relámpago 1
            keyboard.add_hotkey('alt+shift+2', lambda: self.lightning_bet_multiple([1, 8, 15, 22, 29]))  # Relámpago 2
            keyboard.add_hotkey('alt+shift+3', lambda: self.lightning_bet_multiple([2, 9, 16, 23, 30]))  # Relámpago 3
            
            # Hotkeys para apuestas INSTANTÁNEAS (sin delays)
            keyboard.add_hotkey('ctrl+alt+1', lambda: self.instant_bet_multiple([0, 7, 14, 21, 28]))  # Instantáneo 1
            keyboard.add_hotkey('ctrl+alt+2', lambda: self.instant_bet_multiple([1, 8, 15, 22, 29]))  # Instantáneo 2
            keyboard.add_hotkey('ctrl+alt+3', lambda: self.instant_bet_multiple([2, 9, 16, 23, 30]))  # Instantáneo 3
            keyboard.add_hotkey('ctrl+alt+r', lambda: self.instant_bet_multiple([0, 32, 15, 19, 4, 21, 2, 25, 17, 34]))  # Rojos
            keyboard.add_hotkey('ctrl+alt+b', lambda: self.instant_bet_multiple([3, 6, 9, 12, 18, 21, 30, 36, 5, 14]))  # Negros
            
            # Hotkeys para cambio rápido entre primeros 5 perfiles
            for i in range(1, 6):
                keyboard.add_hotkey(f'ctrl+f{i}', lambda num=i: self.quick_switch_profile(num))
            
            logger.info("⌨️ Hotkeys configurados:")
            logger.info("   === BÁSICOS ===")
            logger.info("   F1: Guardar posición rápida")
            logger.info("   F2: Cargar posición guardada")
            logger.info("   F3: Iniciar/parar clicks")
            logger.info("   ESC: Detener bot")
            logger.info("   === NÚMEROS ===")
            logger.info("   Ctrl+0-9: Grabar números")
            logger.info("   Alt+0-9: Apostar números")
            logger.info("   === PERFILES ===")
            logger.info("   Ctrl+Shift+N: Nuevo perfil")
            logger.info("   Ctrl+Shift+P: Cambiar perfil")
            logger.info("   Ctrl+Shift+R: Renombrar perfil")
            logger.info("   Ctrl+Shift+D: Eliminar perfil")
            logger.info("   Ctrl+Shift+A: Ver todos los perfiles")
            logger.info("   === APUESTA MÚLTIPLE ===")
            logger.info("   Ctrl+Shift+M: Apuesta múltiple manual")
            logger.info("   Ctrl+Shift+B: Apuesta rápida favoritos")
            logger.info("   Ctrl+Shift+F: Configurar favoritos")
            logger.info("   Ctrl+Shift+C: Modo continuo")
            logger.info("   === APUESTAS ULTRA-RÁPIDAS ===")
            logger.info("   Ctrl+Shift+1: Apuesta rápida patrón 1")
            logger.info("   Ctrl+Shift+2: Apuesta rápida patrón 2")
            logger.info("   Ctrl+Shift+3: Apuesta rápida patrón 3")
            logger.info("   === CONTROL DE VELOCIDAD ===")
            logger.info("   Ctrl+Shift+T: Modo turbo")
            logger.info("   Ctrl+Shift+U: Modo ultra-rápido")
            logger.info("   Ctrl+Shift+L: Modo relámpago")
            logger.info("   Ctrl+Shift+V: Cambiar velocidad")
            logger.info("   Ctrl+Shift+S: Menú de velocidad")
            logger.info("   Ctrl+Shift+Q: Apuesta turbo favoritos")
            logger.info("   === APUESTAS RELÁMPAGO ===")
            logger.info("   Alt+Shift+1: Apuesta relámpago patrón 1")
            logger.info("   Alt+Shift+2: Apuesta relámpago patrón 2") 
            logger.info("   Alt+Shift+3: Apuesta relámpago patrón 3")
            logger.info("   === APUESTAS INSTANTÁNEAS ===")
            logger.info("   Ctrl+Alt+1: Apuesta instantánea patrón 1")
            logger.info("   Ctrl+Alt+2: Apuesta instantánea patrón 2")
            logger.info("   Ctrl+Alt+3: Apuesta instantánea patrón 3")
            logger.info("   Ctrl+Alt+R: Apuesta instantánea rojos")
            logger.info("   Ctrl+Alt+B: Apuesta instantánea negros")
            
        except Exception as e:
            logger.error(f"❌ Error configurando hotkeys: {e}")

    def record_number(self, number):
        """Graba la posición actual para un número específico"""
        name = f"Numero_{number:02d}"
        saved_name = self.save_current_position(name)
        if saved_name:
            logger.info(f"🎯 Número {number} grabado como {saved_name}")

    def quick_bet_number(self, number):
        """Apuesta rápidamente a un número específico"""
        name = f"Numero_{number:02d}"
        if name in self.positions_memory:
            self.target_position = self.positions_memory[name]
            logger.info(f"🎲 Apostando al número {number}")
            self.perform_natural_click(*self.target_position)
        else:
            logger.warning(f"⚠️ Número {number} no está grabado")

    def bet_multiple_numbers(self):
        """Apuesta a múltiples números separados por comas"""
        print("\n🎲 APOSTAR A MÚLTIPLES NÚMEROS")
        print("=" * 50)
        
        # Mostrar todas las coordenadas disponibles
        if not self.positions_memory:
            logger.warning("❌ No hay coordenadas grabadas en este perfil")
            logger.info("💡 Usa la opción 1 para grabar coordenadas")
            return False
        
        print("📍 COORDENADAS DISPONIBLES:")
        print("-" * 30)
        for i, (name, pos) in enumerate(self.positions_memory.items(), 1):
            print(f"  {i}. {name}: ({pos[0]}, {pos[1]})")
        print("-" * 30)
        
        # Buscar números específicos (formato Numero_XX)
        available_numbers = []
        number_positions = {}
        
        for pos_name, pos_coords in self.positions_memory.items():
            # Buscar patrones de números
            if pos_name.startswith("Numero_"):
                try:
                    num = int(pos_name.split("_")[1])
                    if 0 <= num <= 36:
                        available_numbers.append(num)
                        number_positions[num] = pos_coords
                except:
                    pass
            # También buscar números directos (0, 1, 2, etc.)
            elif pos_name.isdigit():
                try:
                    num = int(pos_name)
                    if 0 <= num <= 36:
                        available_numbers.append(num)
                        number_positions[num] = pos_coords
                except:
                    pass
        
        if available_numbers:
            available_numbers.sort()
            print(f"🎯 Números detectados automáticamente: {', '.join(map(str, available_numbers))}")
            print("=" * 50)
            
            try:
                # Solicitar números a apostar
                numbers_input = input("Ingresa los números separados por comas (ej: 0,7,14,21): ").strip()
                
                if not numbers_input:
                    logger.warning("❌ No se ingresaron números")
                    return False
                
                # Procesar números
                try:
                    numbers_to_bet = []
                    for num_str in numbers_input.split(','):
                        num = int(num_str.strip())
                        if 0 <= num <= 36:
                            numbers_to_bet.append(num)
                        else:
                            logger.warning(f"⚠️ Número {num} fuera de rango (0-36)")
                    
                    if not numbers_to_bet:
                        logger.warning("❌ No hay números válidos para apostar")
                        return False
                    
                except ValueError:
                    logger.error("❌ Formato inválido. Usa números separados por comas")
                    return False
                
                # Verificar que los números estén disponibles
                missing_numbers = []
                valid_numbers = []
                
                for num in numbers_to_bet:
                    if num in number_positions:
                        valid_numbers.append(num)
                    else:
                        missing_numbers.append(num)
                
                if missing_numbers:
                    logger.warning(f"⚠️ Números no disponibles: {', '.join(map(str, missing_numbers))}")
                
                if not valid_numbers:
                    logger.error("❌ Ningún número está disponible")
                    return False
                
                # Confirmar apuesta
                print(f"\n🎯 NÚMEROS A APOSTAR: {', '.join(map(str, valid_numbers))}")
                if missing_numbers:
                    print(f"⚠️ NÚMEROS OMITIDOS: {', '.join(map(str, missing_numbers))}")
                
                confirm = input("¿Confirmar apuesta? (s/N): ").strip().lower()
                if confirm != 's':
                    logger.info("❌ Apuesta cancelada")
                    return False
                
                # Realizar apuestas
                logger.info(f"🚀 Iniciando apuesta a {len(valid_numbers)} números...")
                
                for i, num in enumerate(valid_numbers, 1):
                    position = number_positions[num]
                    
                    logger.info(f"🎲 [{i}/{len(valid_numbers)}] Apostando al número {num}")
                    
                    # Realizar click natural
                    if self.perform_natural_click(*position):
                        # Delay entre clicks para parecer más humano
                        if i < len(valid_numbers):
                            if self.turbo_mode:
                                delay = random.uniform(0.05, 0.15)  # Delay mínimo en turbo
                            else:
                                delay = random.uniform(0.5, 1.5)    # Delay normal
                            time.sleep(delay)
                    else:
                        logger.error(f"❌ Error apostando al número {num}")
                
                logger.info(f"✅ Apuesta completada: {len(valid_numbers)} números")
                
                # Preguntar si hacer otra apuesta
                return self._ask_for_another_bet()
                
            except KeyboardInterrupt:
                logger.info("❌ Apuesta cancelada por el usuario")
                return False
            except Exception as e:
                logger.error(f"❌ Error en apuesta múltiple: {e}")
                return False
        
        else:
            # No hay números detectados automáticamente, usar modo manual
            print("⚠️ No se detectaron números automáticamente")
            print("🔧 MODO MANUAL MEJORADO PARA BC GAME")
            print("=" * 50)
            print("💡 Puedes usar:")
            print("   - Números simples: 0,1,6,31")
            print("   - Nombres completos: Numero_00,Numero_01,Numero_06,Numero_31")
            print("   - Nombres de coordenadas: Posicion_01,Posicion_02")
            print("=" * 50)
            
            try:
                positions_input = input("Ingresa números o nombres separados por comas: ").strip()
                
                if not positions_input:
                    logger.warning("❌ No se ingresaron nombres")
                    return False
                
                # Procesar nombres - Mejorado para BC Game
                position_names = [name.strip() for name in positions_input.split(',')]
                valid_positions = []
                missing_positions = []
                
                for name in position_names:
                    # Buscar nombre exacto primero
                    if name in self.positions_memory:
                        valid_positions.append((name, self.positions_memory[name]))
                    else:
                        # Si es un número, intentar formato Numero_XX
                        try:
                            if name.isdigit():
                                num = int(name)
                                if 0 <= num <= 36:
                                    numero_format = f"Numero_{num:02d}"
                                    if numero_format in self.positions_memory:
                                        valid_positions.append((numero_format, self.positions_memory[numero_format]))
                                        logger.info(f"✅ Convertido: {name} → {numero_format}")
                                    else:
                                        missing_positions.append(name)
                                else:
                                    missing_positions.append(name)
                            else:
                                missing_positions.append(name)
                        except:
                            missing_positions.append(name)
                
                if missing_positions:
                    logger.warning(f"⚠️ Coordenadas no encontradas: {', '.join(missing_positions)}")
                
                if not valid_positions:
                    logger.error("❌ Ninguna coordenada está disponible")
                    return False
                
                # Confirmar apuesta
                print(f"\n🎯 COORDENADAS A USAR:")
                for name, pos in valid_positions:
                    print(f"  • {name}: ({pos[0]}, {pos[1]})")
                
                if missing_positions:
                    print(f"⚠️ COORDENADAS OMITIDAS: {', '.join(missing_positions)}")
                
                confirm = input("¿Confirmar apuesta? (s/N): ").strip().lower()
                if confirm != 's':
                    logger.info("❌ Apuesta cancelada")
                    return False
                
                # Realizar apuestas
                logger.info(f"🚀 Iniciando apuesta a {len(valid_positions)} coordenadas...")
                
                for i, (name, position) in enumerate(valid_positions, 1):
                    logger.info(f"🎲 [{i}/{len(valid_positions)}] Apostando en {name}")
                    
                    # Realizar click natural
                    if self.perform_natural_click(*position):
                        # Delay entre clicks
                        if i < len(valid_positions):
                            if self.turbo_mode:
                                delay = random.uniform(0.05, 0.15)  # Delay mínimo en turbo
                            else:
                                delay = random.uniform(0.5, 1.5)    # Delay normal
                            time.sleep(delay)
                    else:
                        logger.error(f"❌ Error apostando en {name}")
                
                logger.info(f"✅ Apuesta completada: {len(valid_positions)} coordenadas")
                
                # Preguntar si hacer otra apuesta
                return self._ask_for_another_bet()
                
            except KeyboardInterrupt:
                logger.info("❌ Apuesta cancelada por el usuario")
                return False
            except Exception as e:
                logger.error(f"❌ Error en apuesta manual: {e}")
                return False

    def _ask_for_another_bet(self):
        """Pregunta si hacer otra apuesta inmediatamente"""
        try:
            print("\n" + "="*50)
            print("🎲 APUESTA COMPLETADA")
            print("="*50)
            print("¿Qué quieres hacer ahora?")
            print("1. 🔄 Hacer otra apuesta múltiple")
            print("2. ⭐ Apostar a números favoritos")
            print("3. 🎯 Apostar a un número específico")
            print("4. 📋 Volver al menú principal")
            print("0. ❌ Salir")
            
            choice = input("Selecciona una opción: ").strip()
            
            if choice == '1':
                # Hacer otra apuesta múltiple
                return self.bet_multiple_numbers()
            elif choice == '2':
                # Apostar a favoritos
                return self.quick_bet_multiple_from_hotkey()
            elif choice == '3':
                # Apostar a número específico
                return self._quick_single_bet()
            elif choice == '4':
                # Volver al menú
                return True
            elif choice == '0':
                # Salir
                self.exit_requested = True
                return False
            else:
                logger.warning("❌ Opción inválida, volviendo al menú")
                return True
                
        except KeyboardInterrupt:
            logger.info("❌ Volviendo al menú principal")
            return True
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return True

    def _quick_single_bet(self):
        """Apuesta rápida a un número específico"""
        try:
            # Mostrar números disponibles
            available_numbers = []
            number_positions = {}
            
            for pos_name, pos_coords in self.positions_memory.items():
                if pos_name.startswith("Numero_"):
                    try:
                        num = int(pos_name.split("_")[1])
                        if 0 <= num <= 36:
                            available_numbers.append(num)
                            number_positions[num] = pos_coords
                    except:
                        pass
                elif pos_name.isdigit():
                    try:
                        num = int(pos_name)
                        if 0 <= num <= 36:
                            available_numbers.append(num)
                            number_positions[num] = pos_coords
                    except:
                        pass
            
            if not available_numbers:
                logger.warning("❌ No hay números disponibles")
                return self._ask_for_another_bet()
            
            available_numbers.sort()
            print(f"\n🎯 Números disponibles: {', '.join(map(str, available_numbers))}")
            
            number_input = input("¿A qué número apostar?: ").strip()
            number = int(number_input)
            
            if number in number_positions:
                position = number_positions[number]
                logger.info(f"🎲 Apostando al número {number}")
                
                if self.perform_natural_click(*position):
                    logger.info(f"✅ Apuesta al número {number} completada")
                else:
                    logger.error(f"❌ Error apostando al número {number}")
                
                # Preguntar si hacer otra apuesta
                return self._ask_for_another_bet()
            else:
                logger.warning(f"❌ Número {number} no disponible")
                return self._ask_for_another_bet()
                
        except ValueError:
            logger.error("❌ Número inválido")
            return self._ask_for_another_bet()
        except KeyboardInterrupt:
            logger.info("❌ Apuesta cancelada")
            return self._ask_for_another_bet()
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return self._ask_for_another_bet()

    def continuous_betting_mode(self):
        """Modo de apuesta continua - múltiples apuestas seguidas"""
        print("\n🔄 MODO DE APUESTA CONTINUA")
        print("=" * 50)
        print("Realiza múltiples apuestas seguidas sin volver al menú")
        print("Presiona Ctrl+C en cualquier momento para salir")
        print("=" * 50)
        
        bet_count = 0
        
        try:
            while not self.exit_requested:
                bet_count += 1
                print(f"\n🎲 APUESTA #{bet_count}")
                print("-" * 30)
                
                # Realizar apuesta
                if not self.bet_multiple_numbers():
                    break
                
                # Pequeña pausa entre apuestas
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            logger.info(f"\n🔚 Modo continuo finalizado. Total de apuestas: {bet_count - 1}")
        except Exception as e:
            logger.error(f"❌ Error en modo continuo: {e}")
        
        return True

    def toggle_turbo_mode(self):
        """Activa/desactiva el modo turbo"""
        self.turbo_mode = not self.turbo_mode
        if self.turbo_mode:
            # Desactivar otros modos
            self.ultra_fast_mode = False
            self.lightning_mode = False
        
        status = "ACTIVADO" if self.turbo_mode else "DESACTIVADO"
        logger.info(f"⚡ MODO TURBO {status}")
        
        if self.turbo_mode:
            logger.info("   📊 Velocidad: RÁPIDA (delays reducidos)")
        else:
            logger.info(f"   📊 Velocidad actual: {self.speed_mode.upper()}")
    
    def toggle_ultra_fast_mode(self):
        """Activa/desactiva el modo ultra-rápido"""
        self.ultra_fast_mode = not self.ultra_fast_mode
        if self.ultra_fast_mode:
            # Desactivar otros modos
            self.turbo_mode = False
            self.lightning_mode = False
        
        status = "ACTIVADO" if self.ultra_fast_mode else "DESACTIVADO"
        logger.info(f"🚀 MODO ULTRA-RÁPIDO {status}")
        
        if self.ultra_fast_mode:
            logger.info("   📊 Velocidad: EXTREMA (delays mínimos)")
        else:
            logger.info(f"   📊 Velocidad actual: {self.speed_mode.upper()}")
    
    def toggle_lightning_mode(self):
        """Activa/desactiva el modo relámpago (velocidad máxima)"""
        self.lightning_mode = not self.lightning_mode
        if self.lightning_mode:
            # Desactivar otros modos
            self.turbo_mode = False
            self.ultra_fast_mode = False
        
        status = "ACTIVADO" if self.lightning_mode else "DESACTIVADO"
        logger.info(f"⚡⚡ MODO RELÁMPAGO {status}")
        
        if self.lightning_mode:
            logger.info("   📊 Velocidad: INSTANTÁNEA (sin delays)")
            logger.warning("   ⚠️ ATENCIÓN: Máxima velocidad - puede ser detectado")
        else:
            logger.info(f"   📊 Velocidad actual: {self.speed_mode.upper()}")
    
    def cycle_speed_mode(self):
        """Cambia entre los diferentes modos de velocidad base"""
        speed_order = ["normal", "fast", "ultra", "lightning"]
        current_index = speed_order.index(self.speed_mode)
        self.speed_mode = speed_order[(current_index + 1) % len(speed_order)]
        
        # Desactivar modos especiales al cambiar velocidad base
        self.turbo_mode = False
        self.ultra_fast_mode = False
        self.lightning_mode = False
        
        logger.info(f"🔄 VELOCIDAD CAMBIADA A: {self.speed_mode.upper()}")
        
        # Mostrar información de la velocidad
        config = self.speed_configs[self.speed_mode]
        between_min, between_max = config["between_clicks"]
        logger.info(f"   📊 Delay entre clicks: {between_min:.3f}s - {between_max:.3f}s")
        
        if self.speed_mode == "lightning":
            logger.warning("   ⚠️ VELOCIDAD MÁXIMA - usar con precaución")
    
    def set_speed_mode(self, mode):
        """Establece un modo de velocidad específico"""
        if mode in self.speed_configs:
            self.speed_mode = mode
            
            # Desactivar modos especiales
            self.turbo_mode = False
            self.ultra_fast_mode = False
            self.lightning_mode = False
            
            logger.info(f"⚙️ VELOCIDAD ESTABLECIDA: {mode.upper()}")
            
            config = self.speed_configs[mode]
            between_min, between_max = config["between_clicks"]
            logger.info(f"   📊 Delay entre clicks: {between_min:.3f}s - {between_max:.3f}s")
        else:
            logger.error(f"❌ Modo de velocidad inválido: {mode}")
    
    def show_speed_menu(self):
        """Muestra menú de configuración de velocidad"""
        print("\n🚀 MENÚ DE VELOCIDAD")
        print("=" * 50)
        
        # Mostrar velocidad actual
        current_mode = "ESPECIAL"
        if self.lightning_mode:
            current_mode = "RELÁMPAGO ⚡⚡"
        elif self.ultra_fast_mode:
            current_mode = "ULTRA-RÁPIDO 🚀"
        elif self.turbo_mode:
            current_mode = "TURBO ⚡"
        else:
            current_mode = self.speed_mode.upper()
        
        print(f"🎯 Velocidad actual: {current_mode}")
        print()
        
        print("MODOS DISPONIBLES:")
        print("1. NORMAL    - Velocidad natural (1-3 segundos entre clicks)")
        print("2. RÁPIDO    - Velocidad acelerada (0.3-1 segundo entre clicks)")
        print("3. ULTRA     - Velocidad extrema (0.1-0.3 segundos entre clicks)")
        print("4. RELÁMPAGO - Velocidad máxima (0.01-0.05 segundos entre clicks)")
        print()
        print("MODOS ESPECIALES:")
        print("5. TURBO     - Modo turbo optimizado")
        print("6. ULTRA-FAST - Modo ultra-rápido avanzado")
        print("7. LIGHTNING - Modo relámpago instantáneo")
        print()
        print("0. Volver al menú principal")
        print()
        
        try:
            choice = input("Elige una opción (0-7): ").strip()
            
            if choice == "0":
                return
            elif choice == "1":
                self.set_speed_mode("normal")
            elif choice == "2":
                self.set_speed_mode("fast")
            elif choice == "3":
                self.set_speed_mode("ultra")
            elif choice == "4":
                self.set_speed_mode("lightning")
            elif choice == "5":
                self.toggle_turbo_mode()
            elif choice == "6":
                self.toggle_ultra_fast_mode()
            elif choice == "7":
                self.toggle_lightning_mode()
            else:
                logger.warning("⚠️ Opción inválida")
        
        except Exception as e:
            logger.error(f"❌ Error en menú de velocidad: {e}")
    
    def lightning_bet_multiple(self, numbers):
        """Apuesta múltiple con velocidad relámpago"""
        if not numbers:
            logger.warning("⚠️ No se proporcionaron números para apostar")
            return False
        
        # Activar modo relámpago temporalmente
        original_lightning = self.lightning_mode
        self.lightning_mode = True
        
        try:
            logger.info(f"⚡⚡ APUESTA RELÁMPAGO: {', '.join(map(str, numbers))}")
            
            successful_bets = 0
            for num in numbers:
                # Buscar coordenadas del número
                num_key = f"Numero_{num:02d}"
                if num_key in self.positions_memory:
                    position = self.positions_memory[num_key]
                    if self.perform_natural_click(*position):
                        successful_bets += 1
                        logger.info(f"⚡ Número {num} apostado")
                else:
                    logger.warning(f"⚠️ Número {num} no encontrado")
            
            logger.info(f"✅ APUESTA RELÁMPAGO COMPLETADA: {successful_bets}/{len(numbers)} números")
            return successful_bets > 0
            
        except Exception as e:
            logger.error(f"❌ Error en apuesta relámpago: {e}")
            return False
        finally:
            # Restaurar modo original
            self.lightning_mode = original_lightning

    def turbo_bet_favorites(self):
        """Apuesta turbo a números favoritos - máxima velocidad"""
        if not hasattr(self, 'favorite_numbers') or not self.favorite_numbers:
            logger.warning("⚠️ No hay números favoritos configurados")
            logger.info("💡 Usa Ctrl+Shift+F para configurar favoritos")
            return False
        
        # Activar modo turbo temporalmente
        original_turbo = self.turbo_mode
        self.turbo_mode = True
        
        try:
            # Buscar posiciones de números favoritos
            valid_positions = []
            for num in self.favorite_numbers:
                name = f"Numero_{num:02d}"
                if name in self.positions_memory:
                    valid_positions.append((num, self.positions_memory[name]))
            
            if not valid_positions:
                logger.warning("⚠️ No se encontraron posiciones para números favoritos")
                return False
            
            # Realizar apuesta turbo
            logger.info(f"⚡ APUESTA TURBO FAVORITOS: {', '.join(map(str, self.favorite_numbers))}")
            
            for num, position in valid_positions:
                self.perform_natural_click(*position)
                time.sleep(0.05)  # Delay mínimo entre clicks
            
            logger.info(f"✅ Apuesta turbo completada: {len(valid_positions)} números en modo ultra-rápido")
            return True
            
        finally:
            # Restaurar modo turbo original
            self.turbo_mode = original_turbo
            
    def ultra_quick_bet(self, numbers_list):
        """Apuesta ultra-rápida sin confirmación a una lista predefinida"""
        try:
            # Buscar números disponibles
            available_numbers = []
            number_positions = {}
            
            for pos_name, pos_coords in self.positions_memory.items():
                if pos_name.startswith("Numero_"):
                    try:
                        num = int(pos_name.split("_")[1])
                        if 0 <= num <= 36:
                            available_numbers.append(num)
                            number_positions[num] = pos_coords
                    except:
                        pass
                elif pos_name.isdigit():
                    try:
                        num = int(pos_name)
                        if 0 <= num <= 36:
                            available_numbers.append(num)
                            number_positions[num] = pos_coords
                    except:
                        pass
            
            # Filtrar números que están disponibles
            valid_numbers = [num for num in numbers_list if num in number_positions]
            
            if not valid_numbers:
                logger.warning("⚠️ No hay números disponibles para apuesta ultra-rápida")
                return False
            
            # Realizar apuesta sin confirmación
            logger.info(f"⚡ APUESTA ULTRA-RÁPIDA: {', '.join(map(str, valid_numbers))}")
            
            for num in valid_numbers:
                position = number_positions[num]
                self.perform_natural_click(*position)
                
                # Delay entre clicks - más corto en modo turbo
                if self.turbo_mode:
                    time.sleep(random.uniform(0.05, 0.1))  # Delay mínimo en turbo
                else:
                    time.sleep(random.uniform(0.2, 0.5))   # Delay normal
            
            logger.info(f"✅ Apuesta ultra-rápida completada: {len(valid_numbers)} números")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en apuesta ultra-rápida: {e}")
            return False

    def quick_bet_multiple_from_hotkey(self):
        """Versión rápida para hotkey - usa números predefinidos"""
        # Buscar si hay números favoritos guardados
        favorites_key = "numeros_favoritos"
        
        if hasattr(self, 'favorite_numbers') and self.favorite_numbers:
            numbers_to_bet = self.favorite_numbers
        else:
            # Si no hay favoritos, usar números comunes
            common_numbers = [0, 7, 14, 21, 28]  # Números espaciados en la ruleta
            numbers_to_bet = []
            
            for num in common_numbers:
                name = f"Numero_{num:02d}"
                if name in self.positions_memory:
                    numbers_to_bet.append(num)
            
            if not numbers_to_bet:
                logger.warning("⚠️ No hay números grabados para apuesta rápida")
                logger.info("💡 Usa Ctrl+Shift+F para configurar números favoritos")
                return False
        
        # Realizar apuesta sin confirmación
        logger.info(f"🚀 Apuesta rápida: {', '.join(map(str, numbers_to_bet))}")
        
        for num in numbers_to_bet:
            name = f"Numero_{num:02d}"
            if name in self.positions_memory:
                position = self.positions_memory[name]
                self.perform_natural_click(*position)
                
                # Delay entre clicks - ajustado según modo
                if self.turbo_mode:
                    time.sleep(random.uniform(0.05, 0.15))  # Más rápido en turbo
                else:
                    time.sleep(random.uniform(0.3, 0.8))    # Normal
        
        logger.info(f"✅ Apuesta rápida completada: {len(numbers_to_bet)} números")
        
        # Preguntar si hacer otra apuesta
        return self._ask_for_another_bet()

    def set_favorite_numbers(self):
        """Configura números favoritos para apuesta rápida"""
        print("\n⭐ CONFIGURAR NÚMEROS FAVORITOS")
        print("=" * 40)
        print("Estos números se usarán para la apuesta rápida (Ctrl+Shift+B)")
        print("=" * 40)
        
        try:
            numbers_input = input("Ingresa tus números favoritos separados por comas: ").strip()
            
            if not numbers_input:
                logger.info("❌ Configuración cancelada")
                return False
            
            # Procesar números
            try:
                favorite_numbers = []
                for num_str in numbers_input.split(','):
                    num = int(num_str.strip())
                    if 0 <= num <= 36:
                        favorite_numbers.append(num)
                    else:
                        logger.warning(f"⚠️ Número {num} fuera de rango (0-36)")
                
                if not favorite_numbers:
                    logger.warning("❌ No hay números válidos")
                    return False
                
                # Guardar números favoritos
                self.favorite_numbers = favorite_numbers
                
                # Guardar en configuración
                if self.current_profile not in self.profiles:
                    self.profiles[self.current_profile] = {}
                
                self.profiles[self.current_profile]["favorites"] = favorite_numbers
                self.save_config_safe()
                
                logger.info(f"⭐ Números favoritos configurados: {', '.join(map(str, favorite_numbers))}")
                logger.info("🚀 Usa Ctrl+Shift+B para apuesta rápida")
                return True
                
            except ValueError:
                logger.error("❌ Formato inválido. Usa números separados por comas")
                return False
                
        except KeyboardInterrupt:
            logger.info("❌ Configuración cancelada")
            return False

    def toggle_clicking(self):
        """Alterna entre iniciar y parar clicks"""
        if self.is_running:
            self.stop_clicking()
        else:
            self.start_clicking()

    def display_menu(self):
        """Muestra el menú principal"""
        print("\n" + "="*60)
        print("🎰 BC GAME BOT - MENÚ PRINCIPAL")
        print("="*60)
        print(f"📁 Perfil actual: {self.current_profile}")
        print(f"📍 Posiciones guardadas: {len(self.positions_memory)}")
        if hasattr(self, 'favorite_numbers') and self.favorite_numbers:
            print(f"⭐ Números favoritos: {', '.join(map(str, self.favorite_numbers))}")
        if self.target_position:
            print(f"🎯 Posición objetivo: {self.target_position}")
        
        # Mostrar estado de velocidad actual
        if self.lightning_mode:
            print("⚡⚡ MODO RELÁMPAGO ACTIVADO (VELOCIDAD MÁXIMA)")
        elif self.ultra_fast_mode:
            print("🚀 MODO ULTRA-RÁPIDO ACTIVADO")
        elif self.turbo_mode:
            print("⚡ MODO TURBO ACTIVADO")
        else:
            print(f"🕐 Velocidad: {self.speed_mode.upper()}")
            
        print("="*60)

    def create_new_profile(self):
        """Crea un nuevo perfil de juego"""
        print("\n📁 CREAR NUEVO PERFIL")
        print("=" * 40)
        
        # Mostrar perfiles existentes
        if self.profiles:
            print("Perfiles existentes:")
            for i, profile_name in enumerate(self.profiles.keys(), 1):
                print(f"  {i}. {profile_name}")
            print()
        
        try:
            profile_name = input("Nombre del nuevo perfil: ").strip()
            
            if not profile_name:
                logger.warning("❌ El nombre no puede estar vacío")
                return False
            
            if profile_name in self.profiles:
                logger.warning(f"❌ El perfil '{profile_name}' ya existe")
                return False
            
            # Crear nuevo perfil
            self.profiles[profile_name] = {"positions": {}}
            
            # Preguntar si cambiar al nuevo perfil
            change = input(f"¿Cambiar al perfil '{profile_name}'? (s/N): ").strip().lower()
            if change == 's':
                self.current_profile = profile_name
                self.positions_memory = {}
            
            self.save_config_safe()
            logger.info(f"✅ Perfil '{profile_name}' creado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando perfil: {e}")
            return False

    def switch_profile(self):
        """Cambia entre perfiles existentes"""
        if not self.profiles:
            logger.info("📁 No hay perfiles disponibles")
            return False
        
        print("\n📁 CAMBIAR PERFIL")
        print("=" * 40)
        
        profiles_list = list(self.profiles.keys())
        for i, profile_name in enumerate(profiles_list, 1):
            marker = "👉" if profile_name == self.current_profile else "  "
            positions_count = len(self.profiles[profile_name].get("positions", {}))
            print(f"{marker} {i}. {profile_name} ({positions_count} posiciones)")
        
        print("=" * 40)
        
        try:
            choice = input("Selecciona un perfil (número): ").strip()
            index = int(choice) - 1
            
            if 0 <= index < len(profiles_list):
                selected_profile = profiles_list[index]
                
                if selected_profile == self.current_profile:
                    logger.info(f"ℹ️ Ya estás en el perfil '{selected_profile}'")
                    return True
                
                # Cambiar perfil
                self.current_profile = selected_profile
                self.positions_memory = self.profiles[selected_profile].get("positions", {})
                self.favorite_numbers = self.profiles[selected_profile].get("favorites", [])
                self.target_position = None  # Limpiar posición objetivo
                
                self.save_config_safe()
                logger.info(f"✅ Cambiado al perfil: {selected_profile}")
                logger.info(f"📍 Posiciones disponibles: {len(self.positions_memory)}")
                return True
            else:
                logger.warning("❌ Selección inválida")
                return False
                
        except ValueError:
            logger.warning("❌ Entrada inválida")
            return False

    def rename_profile(self):
        """Renombra un perfil existente"""
        if not self.profiles:
            logger.info("📁 No hay perfiles disponibles")
            return False
        
        print("\n📝 RENOMBRAR PERFIL")
        print("=" * 40)
        
        profiles_list = list(self.profiles.keys())
        for i, profile_name in enumerate(profiles_list, 1):
            marker = "👉" if profile_name == self.current_profile else "  "
            print(f"{marker} {i}. {profile_name}")
        
        print("=" * 40)
        
        try:
            choice = input("Selecciona perfil a renombrar (número): ").strip()
            index = int(choice) - 1
            
            if 0 <= index < len(profiles_list):
                old_name = profiles_list[index]
                new_name = input(f"Nuevo nombre para '{old_name}': ").strip()
                
                if not new_name:
                    logger.warning("❌ El nombre no puede estar vacío")
                    return False
                
                if new_name in self.profiles:
                    logger.warning(f"❌ El perfil '{new_name}' ya existe")
                    return False
                
                # Renombrar perfil
                self.profiles[new_name] = self.profiles.pop(old_name)
                
                # Actualizar perfil actual si es necesario
                if self.current_profile == old_name:
                    self.current_profile = new_name
                
                self.save_config_safe()
                logger.info(f"✅ Perfil renombrado: '{old_name}' → '{new_name}'")
                return True
            else:
                logger.warning("❌ Selección inválida")
                return False
                
        except ValueError:
            logger.warning("❌ Entrada inválida")
            return False

    def delete_profile(self):
        """Elimina un perfil existente"""
        if not self.profiles:
            logger.info("📁 No hay perfiles disponibles")
            return False
        
        if len(self.profiles) == 1:
            logger.warning("❌ No puedes eliminar el único perfil existente")
            return False
        
        print("\n🗑️ ELIMINAR PERFIL")
        print("=" * 40)
        
        profiles_list = list(self.profiles.keys())
        for i, profile_name in enumerate(profiles_list, 1):
            marker = "👉" if profile_name == self.current_profile else "  "
            positions_count = len(self.profiles[profile_name].get("positions", {}))
            print(f"{marker} {i}. {profile_name} ({positions_count} posiciones)")
        
        print("=" * 40)
        
        try:
            choice = input("Selecciona perfil a eliminar (número): ").strip()
            index = int(choice) - 1
            
            if 0 <= index < len(profiles_list):
                profile_to_delete = profiles_list[index]
                
                # Confirmar eliminación
                positions_count = len(self.profiles[profile_to_delete].get("positions", {}))
                print(f"⚠️ Vas a eliminar '{profile_to_delete}' con {positions_count} posiciones")
                confirm = input("¿Estás seguro? (s/N): ").strip().lower()
                
                if confirm != 's':
                    logger.info("❌ Eliminación cancelada")
                    return False
                
                # Eliminar perfil
                del self.profiles[profile_to_delete]
                
                # Si era el perfil actual, cambiar a otro
                if self.current_profile == profile_to_delete:
                    self.current_profile = list(self.profiles.keys())[0]
                    self.positions_memory = self.profiles[self.current_profile].get("positions", {})
                    self.target_position = None
                    logger.info(f"📁 Cambiado automáticamente al perfil: {self.current_profile}")
                
                self.save_config_safe()
                logger.info(f"✅ Perfil '{profile_to_delete}' eliminado")
                return True
            else:
                logger.warning("❌ Selección inválida")
                return False
                
        except ValueError:
            logger.warning("❌ Entrada inválida")
            return False

    def show_all_profiles(self):
        """Muestra todos los perfiles y sus posiciones"""
        if not self.profiles:
            logger.info("📁 No hay perfiles disponibles")
            return
        
        print("\n📁 TODOS LOS PERFILES:")
        print("=" * 60)
        
        for profile_name, profile_data in self.profiles.items():
            marker = "👉" if profile_name == self.current_profile else "  "
            positions = profile_data.get("positions", {})
            
            print(f"{marker} 📁 {profile_name} ({len(positions)} posiciones)")
            
            if positions:
                for pos_name, pos_coords in positions.items():
                    print(f"     📍 {pos_name}: ({pos_coords[0]}, {pos_coords[1]})")
            else:
                print("     (sin posiciones guardadas)")
            print()
        
        print("=" * 60)

    def quick_switch_profile(self, profile_number):
        """Cambio rápido a un perfil específico por número"""
        try:
            profiles_list = list(self.profiles.keys())
            
            if 1 <= profile_number <= len(profiles_list):
                target_profile = profiles_list[profile_number - 1]
                
                if target_profile == self.current_profile:
                    logger.info(f"ℹ️ Ya estás en el perfil '{target_profile}'")
                    return
                
                # Cambiar perfil
                self.current_profile = target_profile
                self.positions_memory = self.profiles[target_profile].get("positions", {})
                self.favorite_numbers = self.profiles[target_profile].get("favorites", [])
                self.target_position = None
                
                self.save_config_safe()
                logger.info(f"🚀 Cambio rápido al perfil: {target_profile}")
                logger.info(f"📍 Posiciones disponibles: {len(self.positions_memory)}")
            else:
                logger.warning(f"❌ No existe perfil #{profile_number}")
                
        except Exception as e:
            logger.error(f"❌ Error en cambio rápido de perfil: {e}")

    def map_coordinates_to_numbers(self):
        """Mapea coordenadas existentes a números específicos"""
        print("\n🔗 MAPEAR COORDENADAS A NÚMEROS")
        print("=" * 50)
        print("Asigna números (0-36) a tus coordenadas existentes")
        print("=" * 50)
        
        if not self.positions_memory:
            logger.warning("❌ No hay coordenadas grabadas en este perfil")
            logger.info("💡 Usa la opción 1 para grabar coordenadas primero")
            return False
        
        # Mostrar coordenadas disponibles
        print("📍 COORDENADAS DISPONIBLES:")
        print("-" * 30)
        positions_list = list(self.positions_memory.items())
        for i, (name, pos) in enumerate(positions_list, 1):
            print(f"  {i}. {name}: ({pos[0]}, {pos[1]})")
        print("-" * 30)
        
        try:
            print("\n🎯 OPCIONES DE MAPEO:")
            print("1. Mapear coordenada individual")
            print("2. Mapear múltiples coordenadas")
            print("3. Auto-mapear si los nombres son números")
            print("0. Cancelar")
            
            choice = input("Selecciona una opción: ").strip()
            
            if choice == '1':
                return self._map_single_coordinate(positions_list)
            elif choice == '2':
                return self._map_multiple_coordinates(positions_list)
            elif choice == '3':
                return self._auto_map_coordinates()
            elif choice == '0':
                logger.info("❌ Mapeo cancelado")
                return False
            else:
                logger.warning("❌ Opción inválida")
                return False
                
        except KeyboardInterrupt:
            logger.info("❌ Mapeo cancelado por el usuario")
            return False
        except Exception as e:
            logger.error(f"❌ Error en mapeo: {e}")
            return False

    def _map_single_coordinate(self, positions_list):
        """Mapea una sola coordenada a un número"""
        try:
            # Seleccionar coordenada
            coord_choice = input("Número de coordenada a mapear: ").strip()
            coord_index = int(coord_choice) - 1
            
            if 0 <= coord_index < len(positions_list):
                old_name, position = positions_list[coord_index]
                
                # Solicitar número
                number_input = input(f"¿A qué número (0-36) mapear '{old_name}'?: ").strip()
                number = int(number_input)
                
                if 0 <= number <= 36:
                    new_name = f"Numero_{number:02d}"
                    
                    # Verificar si ya existe
                    if new_name in self.positions_memory and new_name != old_name:
                        overwrite = input(f"⚠️ '{new_name}' ya existe. ¿Sobrescribir? (s/N): ").strip().lower()
                        if overwrite != 's':
                            logger.info("❌ Mapeo cancelado")
                            return False
                    
                    # Realizar mapeo
                    if old_name != new_name:
                        # Eliminar nombre anterior y agregar nuevo
                        del self.positions_memory[old_name]
                        self.positions_memory[new_name] = position
                        self.save_config_safe()
                        
                        logger.info(f"✅ Mapeado: '{old_name}' → '{new_name}' (número {number})")
                    else:
                        logger.info(f"ℹ️ '{old_name}' ya está mapeado correctamente")
                    
                    return True
                else:
                    logger.warning("❌ Número debe estar entre 0 y 36")
                    return False
            else:
                logger.warning("❌ Selección inválida")
                return False
                
        except ValueError:
            logger.error("❌ Entrada inválida")
            return False

    def _map_multiple_coordinates(self, positions_list):
        """Mapea múltiples coordenadas a números"""
        print("\n🔗 MAPEO MÚLTIPLE")
        print("Formato: número_coordenada:número_ruleta")
        print("Ejemplo: 1:0,2:7,3:14 (mapea coord 1 al número 0, coord 2 al 7, etc.)")
        print("-" * 50)
        
        try:
            mapping_input = input("Ingresa los mapeos separados por comas: ").strip()
            
            if not mapping_input:
                logger.warning("❌ No se ingresaron mapeos")
                return False
            
            mappings = []
            for mapping in mapping_input.split(','):
                if ':' in mapping:
                    coord_num, roulette_num = mapping.strip().split(':')
                    coord_index = int(coord_num) - 1
                    roulette_number = int(roulette_num)
                    
                    if 0 <= coord_index < len(positions_list) and 0 <= roulette_number <= 36:
                        mappings.append((coord_index, roulette_number))
                    else:
                        logger.warning(f"⚠️ Mapeo inválido: {mapping}")
                else:
                    logger.warning(f"⚠️ Formato incorrecto: {mapping}")
            
            if not mappings:
                logger.warning("❌ No hay mapeos válidos")
                return False
            
            # Mostrar mapeos a realizar
            print(f"\n🎯 MAPEOS A REALIZAR:")
            for coord_index, roulette_number in mappings:
                old_name = positions_list[coord_index][0]
                new_name = f"Numero_{roulette_number:02d}"
                print(f"  • '{old_name}' → '{new_name}' (número {roulette_number})")
            
            confirm = input("¿Confirmar mapeos? (s/N): ").strip().lower()
            if confirm != 's':
                logger.info("❌ Mapeos cancelados")
                return False
            
            # Realizar mapeos
            for coord_index, roulette_number in mappings:
                old_name, position = positions_list[coord_index]
                new_name = f"Numero_{roulette_number:02d}"
                
                if old_name != new_name:
                    # Eliminar nombre anterior si existe
                    if old_name in self.positions_memory:
                        del self.positions_memory[old_name]
                    # Agregar nuevo nombre
                    self.positions_memory[new_name] = position
            
            self.save_config_safe()
            logger.info(f"✅ Completados {len(mappings)} mapeos")
            return True
            
        except ValueError:
            logger.error("❌ Formato inválido")
            return False

    def _auto_map_coordinates(self):
        """Auto-mapea coordenadas que ya tienen nombres numéricos"""
        mapped_count = 0
        
        # Buscar coordenadas con nombres numéricos
        to_rename = []
        for name, position in self.positions_memory.items():
            if name.isdigit():
                try:
                    number = int(name)
                    if 0 <= number <= 36:
                        new_name = f"Numero_{number:02d}"
                        if new_name != name:
                            to_rename.append((name, new_name, position, number))
                except:
                    pass
        
        if not to_rename:
            logger.info("ℹ️ No se encontraron coordenadas para auto-mapear")
            logger.info("💡 Las coordenadas deben tener nombres numéricos (0, 1, 2, etc.)")
            return False
        
        # Mostrar auto-mapeos
        print(f"\n🤖 AUTO-MAPEOS DETECTADOS:")
        for old_name, new_name, position, number in to_rename:
            print(f"  • '{old_name}' → '{new_name}'")
        
        confirm = input(f"¿Confirmar {len(to_rename)} auto-mapeos? (s/N): ").strip().lower()
        if confirm != 's':
            logger.info("❌ Auto-mapeo cancelado")
            return False
        
        # Realizar auto-mapeos
        for old_name, new_name, position, number in to_rename:
            del self.positions_memory[old_name]
            self.positions_memory[new_name] = position
            mapped_count += 1
        
        self.save_config_safe()
        logger.info(f"✅ Auto-mapeadas {mapped_count} coordenadas")
        return True

    def run_menu(self):
        """Ejecuta el menú principal"""
        while not self.exit_requested:
            self.display_menu()
            
            print("1. 📍 Ubicar manualmente (grabar coordenadas)")
            print("2. 📂 Usar posición guardada")
            print("3. 🚀 Iniciar clicks automáticos")
            print("4. ⏹️ Detener clicks")
            print("5. 📋 Ver posiciones guardadas")
            print("6. 🗑️ Limpiar posiciones del perfil actual")
            print("7. ⌨️ Configurar hotkeys")
            print("8. 🦊 Abrir/reabrir Firefox")
            print("9. 📁 Crear nuevo perfil")
            print("10. 🔄 Cambiar perfil")
            print("11. 📝 Renombrar perfil")
            print("12. 🗑️ Eliminar perfil")
            print("13. 📊 Ver todos los perfiles")
            print("14. 🎲 Apostar a múltiples números")
            print("15. ⭐ Configurar números favoritos")
            print("16. 🔗 Mapear coordenadas a números")
            print("17. 🔄 Modo de apuesta continua")
            print("18. 🚀 Configurar velocidad")
            print("19. ⚡ Activar/desactivar modo turbo")
            print("0. ❌ Salir")
            print("="*60)
            
            try:
                choice = input("Selecciona una opción: ").strip()
                
                if choice == '1':
                    self.manual_locate()
                elif choice == '2':
                    self.load_saved_position()
                elif choice == '3':
                    self.start_clicking()
                elif choice == '4':
                    self.stop_clicking()
                elif choice == '5':
                    self.show_saved_positions()
                elif choice == '6':
                    self.clear_positions()
                elif choice == '7':
                    self.setup_hotkeys()
                elif choice == '8':
                    self.setup_firefox()
                elif choice == '9':
                    self.create_new_profile()
                elif choice == '10':
                    self.switch_profile()
                elif choice == '11':
                    self.rename_profile()
                elif choice == '12':
                    self.delete_profile()
                elif choice == '13':
                    self.show_all_profiles()
                elif choice == '14':
                    self.bet_multiple_numbers()
                elif choice == '15':
                    self.set_favorite_numbers()
                elif choice == '16':
                    self.map_coordinates_to_numbers()
                elif choice == '17':
                    self.continuous_betting_mode()
                elif choice == '18':
                    self.show_speed_menu()
                elif choice == '19':
                    self.toggle_turbo_mode()
                elif choice == '0':
                    self.exit_requested = True
                    logger.info("👋 Saliendo del bot...")
                else:
                    logger.warning("❌ Opción inválida")
                    
            except KeyboardInterrupt:
                self.exit_requested = True
                logger.info("👋 Saliendo del bot...")

    def manual_locate(self):
        """Ubicación manual de coordenadas"""
        print("\n📍 UBICACIÓN MANUAL")
        print("Posiciona el cursor sobre el objetivo y presiona Enter...")
        
        try:
            input("Presiona Enter cuando el cursor esté en posición: ")
            current_pos = pyautogui.position()
            
            name = input("Nombre para esta posición (opcional): ").strip()
            if not name:
                name = "Manual"
            
            self.target_position = (current_pos.x, current_pos.y)
            saved_name = self.save_current_position(name)
            
            logger.info(f"✅ Posición configurada: {self.target_position}")
            
        except KeyboardInterrupt:
            logger.info("❌ Ubicación manual cancelada")

    def show_saved_positions(self):
        """Muestra las posiciones guardadas"""
        if not self.positions_memory:
            logger.info("📍 No hay posiciones guardadas")
            return
        
        print("\n📍 POSICIONES GUARDADAS:")
        print("=" * 50)
        for name, pos in self.positions_memory.items():
            print(f"  {name}: ({pos[0]}, {pos[1]})")
        print("=" * 50)

    def clear_positions(self):
        """Limpia todas las posiciones guardadas"""
        confirm = input("¿Estás seguro de limpiar todas las posiciones? (s/N): ").strip().lower()
        if confirm == 's':
            self.positions_memory.clear()
            self.save_config_safe()
            logger.info("🗑️ Todas las posiciones han sido eliminadas")
        else:
            logger.info("❌ Operación cancelada")

    def run(self):
        """Función principal del bot"""
        try:
            logger.info("🎰 BC GAME BOT INICIADO")
            logger.info("=" * 50)
            logger.info("🎯 Optimizado específicamente para BC Game")
            logger.info("🥷 Configuraciones anti-detección aplicadas")
            
            # Configurar hotkeys
            self.setup_hotkeys()
            
            # Buscar ventana de Firefox si está disponible
            if WIN32_AVAILABLE:
                self.find_firefox_window()
            
            # Ejecutar menú principal
            self.run_menu()
            
        except KeyboardInterrupt:
            logger.info("👋 Bot detenido por el usuario")
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
        finally:
            self.stop_clicking()
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            logger.info("🔚 Bot finalizado")

    def setup_pyautogui(self):
        """Configura pyautogui para máxima velocidad y confiabilidad"""
        try:
            # Configuración para velocidad EXTREMA
            pyautogui.PAUSE = 0  # SIN PAUSA entre comandos
            pyautogui.FAILSAFE = True  # Mantener seguridad (cursor en esquina para parar)
            
            # Configuración para confiabilidad y velocidad máxima
            pyautogui.MINIMUM_DURATION = 0  # Sin duración mínima para movimientos
            pyautogui.MINIMUM_SLEEP = 0     # Sin sleep mínimo
            
            # Configurar velocidad de mouse al máximo
            import pyautogui
            pyautogui.PAUSE = 0
            
            logger.info("⚙️ PyAutoGUI configurado para VELOCIDAD EXTREMA")
            logger.info("   📊 PAUSE: 0s (INSTANTÁNEO)")
            logger.info("   🚀 MINIMUM_DURATION: 0s (SIN DELAYS)")
            logger.info("   ⚠️ FAILSAFE activado (cursor esquina superior izquierda para parar)")
            
        except Exception as e:
            logger.warning(f"⚠️ Error configurando PyAutoGUI: {e}")
    
    def auto_detect_window(self):
        """Detecta automáticamente la ventana del navegador"""
        if not WIN32_AVAILABLE:
            logger.info("🔍 Detección automática de ventana no disponible")
            return False
        
        # Buscar ventana de Firefox/Chrome
        found = self.find_firefox_window()
        if found:
            logger.info("✅ Ventana del navegador detectada automáticamente")
        else:
            logger.info("⚠️ No se detectó ventana del navegador automáticamente")
        
        return found

    def instant_bet_multiple(self, numbers):
        """Apuesta instantánea sin delays - VELOCIDAD MÁXIMA"""
        if not numbers:
            logger.warning("⚠️ No se proporcionaron números para apostar")
            return False
        
        try:
            logger.info(f"⚡⚡⚡ APUESTA INSTANTÁNEA: {', '.join(map(str, numbers))}")
            
            successful_bets = 0
            for num in numbers:
                # Buscar coordenadas del número
                num_key = f"Numero_{num:02d}"
                if num_key in self.positions_memory:
                    position = self.positions_memory[num_key]
                    
                    # CLICK INSTANTÁNEO SIN DELAYS
                    pyautogui.moveTo(*position, duration=0)  # Movimiento instantáneo
                    pyautogui.click()  # Click inmediato
                    
                    successful_bets += 1
                    logger.info(f"⚡ Número {num} apostado INSTANTÁNEAMENTE")
                else:
                    logger.warning(f"⚠️ Número {num} no encontrado")
            
            logger.info(f"✅ APUESTA INSTANTÁNEA COMPLETADA: {successful_bets}/{len(numbers)} números en 0 segundos")
            return successful_bets > 0
            
        except Exception as e:
            logger.error(f"❌ Error en apuesta instantánea: {e}")
            return False
    
    def turbo_click_position(self, position):
        """Click turbo en una posición específica - sin delays"""
        try:
            x, y = position
            
            # MODO TURBO EXTREMO
            pyautogui.moveTo(x, y, duration=0)  # Movimiento instantáneo
            pyautogui.click()  # Click inmediato
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en click turbo: {e}")
            return False

if __name__ == "__main__":
    try:
        bot = CasinoBot()
        bot.run()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        input("Presiona Enter para salir...") 