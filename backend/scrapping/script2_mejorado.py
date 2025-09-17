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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service

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
        self.driver = None
        self.target_position = None
        self.target_relative_position = None
        self.window_handle = None
        self.window_position = None
        self.is_running = False
        self.click_thread = None
        self.hotkey_active = False
        self.config_file = "casino_bot_config.json"
        self.game_profiles = {}
        self.current_profile = None
        self.positions_memory = {}
        self.use_speed_mode = False
        self.exit_requested = False
        self.click_patterns = []
        self.last_window_check = 0
        self.auto_open_firefox = True
        self.manual_firefox = False
        self.favorites_numbers = []
        self.turbo_mode = False  # Modo turbo para clicks ultra-rápidos
        
        # Configurar pyautogui para mayor naturalidad
        pyautogui.PAUSE = 0.01
        pyautogui.FAILSAFE = True
        
        # Cargar configuraciones y perfiles guardados
        self.load_config_safe()
        self.init_click_patterns()
        
        # Preguntar si desea abrir Firefox automáticamente o usar uno manual
        self.ask_firefox_startup()
        
        # Configurar Firefox según la elección del usuario
        if self.auto_open_firefox:
            self.setup_firefox()
        elif self.manual_firefox:
            self.setup_manual_firefox()

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
                        
                        # Cargar datos
                        self.game_profiles = data.get("game_profiles", {})
                        
                        # Compatibilidad con versiones anteriores
                        old_positions = data.get("positions", {})
                        if old_positions and not self.game_profiles:
                            self.game_profiles["Default"] = {"positions": old_positions}
                        
                        # Cargar último perfil usado
                        last_profile = data.get("last_profile", None)
                        if last_profile and last_profile in self.game_profiles:
                            self.current_profile = last_profile
                            self.positions_memory = self.game_profiles[last_profile].get("positions", {})
                            # Cargar números favoritos si existen
                            self.favorites_numbers = self.game_profiles[last_profile].get("favorites", [])
                        elif self.game_profiles:
                            self.current_profile = list(self.game_profiles.keys())[0]
                            self.positions_memory = self.game_profiles[self.current_profile].get("positions", {})
                            self.favorites_numbers = self.game_profiles[self.current_profile].get("favorites", [])
                        else:
                            self.current_profile = "Default"
                            self.game_profiles[self.current_profile] = {"positions": {}, "favorites": []}
                            self.positions_memory = {}
                            self.favorites_numbers = []
                        
                        logger.info(f"✅ Configuración cargada exitosamente: {len(self.game_profiles)} perfiles")
                        logger.info(f"📁 Perfil actual: {self.current_profile}")
                        logger.info(f"📍 Posiciones en perfil: {len(self.positions_memory)}")
                        return
                        
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
            self.game_profiles = {
                self.current_profile: {
                    "positions": {},
                    "favorites": []
                }
            }
            self.positions_memory = {}
            self.favorites_numbers = []
            
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
                if self.current_profile not in self.game_profiles:
                    self.game_profiles[self.current_profile] = {}
                self.game_profiles[self.current_profile]["positions"] = self.positions_memory
            
            data = {
                "game_profiles": self.game_profiles,
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
            
        if not self.window_handle:
            return False
        
        try:
            if not win32gui.IsWindow(self.window_handle):
                return False
            
            if not win32gui.IsWindowVisible(self.window_handle):
                return False
            
            title = win32gui.GetWindowText(self.window_handle)
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
        print("\n🦊 CONFIGURACIÓN DE FIREFOX")
        print("=" * 40)
        print("1. 🤖 Abrir Firefox automáticamente (puede ser detectado)")
        print("2. 👤 Usar Firefox abierto manualmente (más sigiloso)")
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
                    print("\n📋 INSTRUCCIONES:")
                    print("1. Abre Firefox manualmente ANTES de usar el bot")
                    print("2. Navega al sitio del casino")
                    print("3. Mantén la ventana de Firefox visible")
                    print("4. El bot detectará automáticamente la ventana")
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
        """Configura Firefox de forma más sigilosa"""
        try:
            firefox_options = Options()
            
            # ===== CONFIGURACIONES ANTI-DETECCIÓN AVANZADAS =====
            
            # Desactivar WebDriver
            firefox_options.set_preference("dom.webdriver.enabled", False)
            firefox_options.set_preference("useAutomationExtension", False)
            
            # Ocultar que es un navegador automatizado
            firefox_options.set_preference("marionette.enabled", False)
            
            # User Agent natural (simular navegador normal)
            firefox_options.set_preference("general.useragent.override", 
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0")
            
            # Desactivar logging de WebDriver
            firefox_options.add_argument("--log-level=3")
            firefox_options.set_preference("webdriver.log.level", "OFF")
            
            # Configuraciones de privacidad mejoradas
            firefox_options.set_preference("privacy.trackingprotection.enabled", True)
            firefox_options.set_preference("dom.disable_beforeunload", True)
            
            # Desactivar automatización detectables
            firefox_options.set_preference("dom.webnotifications.enabled", False)
            firefox_options.set_preference("media.navigator.enabled", False)
            
            # Configuraciones de ventana natural
            firefox_options.add_argument("--width=1366")
            firefox_options.add_argument("--height=768")
            
            # Perfil personalizado (más natural)
            firefox_options.set_preference("browser.startup.homepage", "about:blank")
            firefox_options.set_preference("startup.homepage_welcome_url", "")  
            firefox_options.set_preference("startup.homepage_welcome_url.additional", "")
            
            # JavaScript avanzado
            firefox_options.set_preference("javascript.enabled", True)
            firefox_options.set_preference("dom.webgl.disabled", False)
            
            # Plugins y extensiones
            firefox_options.set_preference("plugin.state.flash", 2)
            firefox_options.set_preference("permissions.default.microphone", 2)
            firefox_options.set_preference("permissions.default.camera", 2)
            
            # Crear driver con configuración sigilosa
            service = Service(log_output=os.devnull)  # Sin logs visibles
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            
            # Ejecutar scripts para mayor naturalidad
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("🦊 Firefox configurado en modo SIGILOSO")
            
            # Abrir página inicial
            self.driver.get("about:blank")
            time.sleep(2)
            
            # Maximizar después de cargar
            self.driver.maximize_window()
            
            print("\n🎯 FIREFOX LISTO")
            print("=" * 30)
            print("✅ Configuración anti-detección aplicada")
            print("✅ Navega manualmente al sitio del casino")
            print("✅ El bot estará listo para funcionar")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al configurar Firefox: {e}")
            print("\n💡 SUGERENCIA:")
            print("- Intenta usar la opción de Firefox manual")
                         print("- Verifica que Firefox esté instalado correctamente")
             return False

    def setup_manual_firefox(self):
        """Configura el bot para usar Firefox ya abierto manualmente"""
        try:
            print("\n👤 MODO FIREFOX MANUAL")
            print("=" * 40)
            print("✅ Configuración más sigilosa activada")
            print("✅ No se detectará automatización")
            print("✅ Firefox debe estar abierto manualmente")
            
            # Buscar ventana de Firefox existente
            if self.find_firefox_window():
                print("✅ Firefox detectado y listo")
                print("\n📋 RECORDATORIO:")
                print("- Mantén Firefox visible durante el uso")
                print("- Navega al sitio del casino manualmente")  
                print("- El bot hará clicks en las coordenadas configuradas")
                return True
            else:
                print("⚠️ No se detectó Firefox abierto")
                print("\n📋 INSTRUCCIONES:")
                print("1. Abre Firefox manualmente")
                print("2. Navega al sitio del casino")
                print("3. Reinicia el bot")
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
            self.window_handle = windows[0][0]
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
        """Realiza un click natural en las coordenadas especificadas"""
        try:
            if self.turbo_mode:
                # MODO TURBO: Delays mínimos para máxima velocidad
                # Mover cursor directamente sin variación
                pyautogui.moveTo(x, y, duration=0.01)
                
                # Click inmediato sin delays
                pyautogui.click()
                
                # Delay mínimo post-click
                time.sleep(0.05)
                
                logger.info(f"⚡ TURBO Click en ({x}, {y})")
                return True
            else:
                # Modo normal con naturalidad
                # Seleccionar patrón aleatorio
                pattern = random.choice(self.click_patterns)
                
                # Delay antes del click
                pre_delay = random.uniform(*pattern["pre_delay"])
                time.sleep(pre_delay)
                
                # Mover cursor con variación humana
                variation_x = random.randint(-2, 2)
                variation_y = random.randint(-2, 2)
                final_x = x + variation_x
                final_y = y + variation_y
                
                # Mover cursor de forma natural
                pyautogui.moveTo(final_x, final_y, duration=random.uniform(0.1, 0.3))
                
                # Hold time
                hold_time = random.uniform(*pattern["hold_time"])
                
                # Realizar click
                pyautogui.mouseDown()
                time.sleep(hold_time)
                pyautogui.mouseUp()
                
                # Delay después del click
                post_delay = random.uniform(*pattern["post_delay"])
                time.sleep(post_delay)
                
                logger.info(f"🎯 Click realizado en ({final_x}, {final_y})")
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
                        
                        # Delay entre clicks (1-3 segundos)
                        delay = random.uniform(1.0, 3.0)
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
            
            # Hotkeys para modo turbo
            keyboard.add_hotkey('ctrl+shift+t', self.toggle_turbo_mode)  # Activar/desactivar turbo
            keyboard.add_hotkey('ctrl+shift+q', lambda: self.turbo_bet_favorites())  # Apuesta turbo favoritos
            
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
            logger.info("   === MODO TURBO ===")
            logger.info("   Ctrl+Shift+T: Activar/desactivar modo turbo")
            logger.info("   Ctrl+Shift+Q: Apuesta turbo favoritos")
            logger.info("   === CAMBIO RÁPIDO ===")
            logger.info("   Ctrl+F1-F5: Cambio rápido a perfiles 1-5")
            
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
            print("🔧 MODO MANUAL: Selecciona coordenadas por nombre")
            print("=" * 50)
            
            try:
                positions_input = input("Ingresa los nombres de las coordenadas separados por comas: ").strip()
                
                if not positions_input:
                    logger.warning("❌ No se ingresaron nombres")
                    return False
                
                # Procesar nombres
                position_names = [name.strip() for name in positions_input.split(',')]
                valid_positions = []
                missing_positions = []
                
                for name in position_names:
                    if name in self.positions_memory:
                        valid_positions.append((name, self.positions_memory[name]))
                    else:
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
            logger.info("⚡ MODO TURBO ACTIVADO - Clicks ultra-rápidos")
            logger.info("🚀 Delays mínimos: 0.05-0.1 segundos entre clicks")
            logger.info("⚠️ Usa Ctrl+Shift+T para desactivar")
        else:
            logger.info("🎯 MODO NORMAL ACTIVADO - Clicks naturales")
            logger.info("🕐 Delays normales: 0.2-1.5 segundos entre clicks")
        
        return self.turbo_mode

    def turbo_bet_favorites(self):
        """Apuesta turbo a números favoritos - máxima velocidad"""
        if not hasattr(self, 'favorites_numbers') or not self.favorites_numbers:
            logger.warning("⚠️ No hay números favoritos configurados")
            logger.info("💡 Usa Ctrl+Shift+F para configurar favoritos")
            return False
        
        # Activar modo turbo temporalmente
        original_turbo = self.turbo_mode
        self.turbo_mode = True
        
        try:
            # Buscar posiciones de números favoritos
            valid_positions = []
            for num in self.favorites_numbers:
                name = f"Numero_{num:02d}"
                if name in self.positions_memory:
                    valid_positions.append((num, self.positions_memory[name]))
            
            if not valid_positions:
                logger.warning("⚠️ No se encontraron posiciones para números favoritos")
                return False
            
            # Realizar apuesta turbo
            logger.info(f"⚡ APUESTA TURBO FAVORITOS: {', '.join(map(str, self.favorites_numbers))}")
            
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
        
        if hasattr(self, 'favorites_numbers') and self.favorites_numbers:
            numbers_to_bet = self.favorites_numbers
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
                self.favorites_numbers = favorite_numbers
                
                # Guardar en configuración
                if self.current_profile not in self.game_profiles:
                    self.game_profiles[self.current_profile] = {}
                
                self.game_profiles[self.current_profile]["favorites"] = favorite_numbers
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
        print("🎰 CASINO BOT - MENÚ PRINCIPAL")
        print("="*60)
        print(f"📁 Perfil actual: {self.current_profile}")
        print(f"📍 Posiciones guardadas: {len(self.positions_memory)}")
        if hasattr(self, 'favorites_numbers') and self.favorites_numbers:
            print(f"⭐ Números favoritos: {', '.join(map(str, self.favorites_numbers))}")
        if self.target_position:
            print(f"🎯 Posición objetivo: {self.target_position}")
        
        # Mostrar estado del modo turbo
        if self.turbo_mode:
            print("⚡ MODO TURBO: ACTIVADO (clicks ultra-rápidos)")
        else:
            print("🎯 MODO NORMAL: ACTIVADO (clicks naturales)")
            
        print("="*60)

    def create_new_profile(self):
        """Crea un nuevo perfil de juego"""
        print("\n📁 CREAR NUEVO PERFIL")
        print("=" * 40)
        
        # Mostrar perfiles existentes
        if self.game_profiles:
            print("Perfiles existentes:")
            for i, profile_name in enumerate(self.game_profiles.keys(), 1):
                print(f"  {i}. {profile_name}")
            print()
        
        try:
            profile_name = input("Nombre del nuevo perfil: ").strip()
            
            if not profile_name:
                logger.warning("❌ El nombre no puede estar vacío")
                return False
            
            if profile_name in self.game_profiles:
                logger.warning(f"❌ El perfil '{profile_name}' ya existe")
                return False
            
            # Crear nuevo perfil
            self.game_profiles[profile_name] = {"positions": {}}
            
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
        if not self.game_profiles:
            logger.info("📁 No hay perfiles disponibles")
            return False
        
        print("\n📁 CAMBIAR PERFIL")
        print("=" * 40)
        
        profiles_list = list(self.game_profiles.keys())
        for i, profile_name in enumerate(profiles_list, 1):
            marker = "👉" if profile_name == self.current_profile else "  "
            positions_count = len(self.game_profiles[profile_name].get("positions", {}))
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
                self.positions_memory = self.game_profiles[selected_profile].get("positions", {})
                self.favorites_numbers = self.game_profiles[selected_profile].get("favorites", [])
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
        if not self.game_profiles:
            logger.info("📁 No hay perfiles disponibles")
            return False
        
        print("\n📝 RENOMBRAR PERFIL")
        print("=" * 40)
        
        profiles_list = list(self.game_profiles.keys())
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
                
                if new_name in self.game_profiles:
                    logger.warning(f"❌ El perfil '{new_name}' ya existe")
                    return False
                
                # Renombrar perfil
                self.game_profiles[new_name] = self.game_profiles.pop(old_name)
                
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
        if not self.game_profiles:
            logger.info("📁 No hay perfiles disponibles")
            return False
        
        if len(self.game_profiles) == 1:
            logger.warning("❌ No puedes eliminar el único perfil existente")
            return False
        
        print("\n🗑️ ELIMINAR PERFIL")
        print("=" * 40)
        
        profiles_list = list(self.game_profiles.keys())
        for i, profile_name in enumerate(profiles_list, 1):
            marker = "👉" if profile_name == self.current_profile else "  "
            positions_count = len(self.game_profiles[profile_name].get("positions", {}))
            print(f"{marker} {i}. {profile_name} ({positions_count} posiciones)")
        
        print("=" * 40)
        
        try:
            choice = input("Selecciona perfil a eliminar (número): ").strip()
            index = int(choice) - 1
            
            if 0 <= index < len(profiles_list):
                profile_to_delete = profiles_list[index]
                
                # Confirmar eliminación
                positions_count = len(self.game_profiles[profile_to_delete].get("positions", {}))
                print(f"⚠️ Vas a eliminar '{profile_to_delete}' con {positions_count} posiciones")
                confirm = input("¿Estás seguro? (s/N): ").strip().lower()
                
                if confirm != 's':
                    logger.info("❌ Eliminación cancelada")
                    return False
                
                # Eliminar perfil
                del self.game_profiles[profile_to_delete]
                
                # Si era el perfil actual, cambiar a otro
                if self.current_profile == profile_to_delete:
                    self.current_profile = list(self.game_profiles.keys())[0]
                    self.positions_memory = self.game_profiles[self.current_profile].get("positions", {})
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
        if not self.game_profiles:
            logger.info("📁 No hay perfiles disponibles")
            return
        
        print("\n📁 TODOS LOS PERFILES:")
        print("=" * 60)
        
        for profile_name, profile_data in self.game_profiles.items():
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
            profiles_list = list(self.game_profiles.keys())
            
            if 1 <= profile_number <= len(profiles_list):
                target_profile = profiles_list[profile_number - 1]
                
                if target_profile == self.current_profile:
                    logger.info(f"ℹ️ Ya estás en el perfil '{target_profile}'")
                    return
                
                # Cambiar perfil
                self.current_profile = target_profile
                self.positions_memory = self.game_profiles[target_profile].get("positions", {})
                self.favorites_numbers = self.game_profiles[target_profile].get("favorites", [])
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
            print("18. ⚡ Activar/desactivar modo turbo")
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
                    self.show_all_positions()
                elif choice == '14':
                    self.bet_multiple_numbers()
                elif choice == '15':
                    self.set_favorite_numbers()
                elif choice == '16':
                    self.map_coordinates_to_numbers()
                elif choice == '17':
                    self.continuous_betting_mode()
                elif choice == '18':
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
            logger.info("🎰 CASINO BOT INICIADO")
            logger.info("=" * 50)
            
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

if __name__ == "__main__":
    try:
        bot = CasinoBot()
        bot.run()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        input("Presiona Enter para salir...") 