import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuration
LOGIN_URL = os.getenv("LOGIN_URL", "https://bcgame.com/login")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://bcgame.com/game/lightning-roulette")
USERNAME = os.getenv("ROULETTE_USERNAME", "tu_usuario")
PASSWORD = os.getenv("ROULETTE_PASSWORD", "tu_password")

def log_message(message, level="INFO"):
    """Log message with timestamp and level"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)

def setup_debug_driver():
    """Setup Chrome driver VISIBLE para debug"""
    options = Options()
    # NO headless para poder ver qué pasa
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-images")  # Velocidad
    
    # User agent actualizado
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Anti-detección
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    
    # Script anti-detección
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def debug_login():
    """Función de debug para el login"""
    driver = None
    try:
        driver = setup_debug_driver()
        wait = WebDriverWait(driver, 20)
        
        log_message("🔑 === MODO DEBUG - LOGIN VISIBLE ===")
        log_message(f"🌐 Navegando a: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        
        # Esperar carga
        time.sleep(5)
        log_message(f"📄 Página cargada. URL actual: {driver.current_url}")
        log_message(f"📄 Título: {driver.title}")
        
        # Analizar la página
        log_message("🔍 ANALIZANDO ELEMENTOS DE LA PÁGINA...")
        
        # Buscar todos los inputs
        inputs = driver.find_elements(By.TAG_NAME, "input")
        log_message(f"📝 Total de inputs encontrados: {len(inputs)}")
        
        visible_inputs = []
        for i, inp in enumerate(inputs):
            try:
                if inp.is_displayed():
                    visible_inputs.append(inp)
                    name = inp.get_attribute('name') or 'sin-nombre'
                    type_attr = inp.get_attribute('type') or 'text'
                    placeholder = inp.get_attribute('placeholder') or 'sin-placeholder'
                    class_attr = inp.get_attribute('class') or 'sin-clase'
                    id_attr = inp.get_attribute('id') or 'sin-id'
                    
                    log_message(f"  📝 Input {i+1} (VISIBLE):")
                    log_message(f"      name='{name}'")
                    log_message(f"      type='{type_attr}'")
                    log_message(f"      placeholder='{placeholder}'")
                    log_message(f"      class='{class_attr}'")
                    log_message(f"      id='{id_attr}'")
            except Exception as e:
                log_message(f"  ❌ Error analizando input {i+1}: {e}")
        
        log_message(f"✅ Inputs visibles: {len(visible_inputs)}")
        
        # Buscar botones
        buttons = driver.find_elements(By.TAG_NAME, "button")
        log_message(f"🔘 Total de botones encontrados: {len(buttons)}")
        
        visible_buttons = []
        for i, btn in enumerate(buttons):
            try:
                if btn.is_displayed():
                    visible_buttons.append(btn)
                    text = btn.text.strip() if btn.text else 'sin-texto'
                    class_attr = btn.get_attribute('class') or 'sin-clase'
                    type_attr = btn.get_attribute('type') or 'sin-tipo'
                    
                    log_message(f"  🔘 Botón {i+1} (VISIBLE):")
                    log_message(f"      texto='{text}'")
                    log_message(f"      class='{class_attr}'")
                    log_message(f"      type='{type_attr}'")
            except Exception as e:
                log_message(f"  ❌ Error analizando botón {i+1}: {e}")
        
        log_message(f"✅ Botones visibles: {len(visible_buttons)}")
        
        # Intentar login automático si hay campos
        if len(visible_inputs) >= 2:
            log_message("🤖 INTENTANDO LOGIN AUTOMÁTICO...")
            
            try:
                # Primer campo (usuario/email)
                email_field = visible_inputs[0]
                email_field.click()
                time.sleep(1)
                email_field.clear()
                email_field.send_keys(USERNAME)
                log_message("✅ Usuario ingresado en primer campo")
                
                # Segundo campo (password)
                password_field = visible_inputs[1]
                password_field.click()
                time.sleep(1)
                password_field.clear()
                password_field.send_keys(PASSWORD)
                log_message("✅ Password ingresado en segundo campo")
                
                # Buscar botón de submit
                if visible_buttons:
                    submit_button = visible_buttons[0]  # Primer botón visible
                    log_message(f"🚀 Presionando botón: {submit_button.text}")
                    submit_button.click()
                else:
                    log_message("⌨️ No hay botones, usando Enter")
                    password_field.send_keys(Keys.RETURN)
                
                log_message("⏳ Esperando redirección...")
                time.sleep(10)
                
                log_message(f"🌐 URL después de login: {driver.current_url}")
                log_message(f"📄 Título después de login: {driver.title}")
                
                # Intentar navegar al dashboard
                log_message(f"🎰 Navegando al dashboard: {DASHBOARD_URL}")
                driver.get(DASHBOARD_URL)
                time.sleep(5)
                
                log_message(f"🌐 URL del dashboard: {driver.current_url}")
                log_message(f"📄 Título del dashboard: {driver.title}")
                
            except Exception as login_e:
                log_message(f"❌ Error en login automático: {login_e}", "ERROR")
        
        # Mantener ventana abierta para inspección manual
        log_message("👁️ VENTANA ABIERTA PARA INSPECCIÓN MANUAL")
        log_message("🔍 Puedes hacer login manualmente y revisar los elementos")
        log_message("⌨️ Presiona Enter en la consola para continuar...")
        input("Presiona Enter para cerrar el navegador...")
        
    except Exception as e:
        log_message(f"❌ Error general: {e}", "ERROR")
    finally:
        if driver:
            driver.quit()
        log_message("🏁 Debug terminado")

if __name__ == "__main__":
    debug_login() 