import time
import json
import os
import hashlib
import psutil
import sys
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
# import requests  # Ya no se necesita
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuration - URLs y credenciales por defecto si no hay .env
LOGIN_URL = os.getenv("LOGIN_URL", "https://bcgame.com/login")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://bcgame.com/game/lightning-roulette")
USERNAME = os.getenv("ROULETTE_USERNAME", "tu_usuario")
PASSWORD = os.getenv("ROULETTE_PASSWORD", "tu_password")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "30"))  # Reducido a 30 segundos

# Configuration eliminada: Supabase ya no se usa

# Lock file para evitar múltiples instancias
LOCK_FILE = "roulette_scraper.lock"

# Create directories for data and logs
DATA_DIR = "roulette_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# File paths
NUMBERS_JSON_FILE = os.path.join(DATA_DIR, "roulette_numbers.json")
PROCESSED_NUMBERS_FILE = os.path.join(DATA_DIR, "processed_numbers.txt")
LAST_SEEN_FILE = os.path.join(DATA_DIR, "last_seen_numbers.json")
LOG_FILE = os.path.join(DATA_DIR, "roulette_scraper.log")

def check_single_instance():
    """Verificar que solo se ejecute una instancia del script"""
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE, 'r') as f:
            try:
                pid = int(f.read().strip())
                if psutil.pid_exists(pid):
                    log_message("ERROR: Ya hay una instancia ejecutándose. Saliendo...", "ERROR")
                    sys.exit(1)
                else:
                    log_message("Archivo lock encontrado pero proceso no existe. Continuando...", "WARN")
            except:
                pass
    
    # Crear lock file
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

def cleanup_lock():
    """Limpiar archivo lock al salir"""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def log_message(message, level="INFO"):
    """Log message with timestamp and level - Versión optimizada"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    # Escribir log de forma más eficiente (sin try/except innecesario)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8', buffering=1) as f:  # Line buffering
            f.write(log_entry + "\n")
    except:
        pass  # Ignorar errores de escritura de log

def get_number_color(number):
    """Determine the color of a roulette number - Versión optimizada"""
    number = int(number)
    if number == 0:
        return "green"
    # Usar set para búsqueda O(1)
    red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    return "red" if number in red_numbers else "black"

def setup_driver():
    """Setup headless Chrome driver con optimizaciones para login"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-images")  # No cargar imágenes para velocidad
    # NO deshabilitar JavaScript - es necesario para login moderno
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agent más completo y actualizado
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Opciones adicionales para evitar detección
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    
    # Ejecutar script para ocultar que es automatizado
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def improved_login_and_extract_numbers():
    """Login mejorado y extracción de números con mejor manejo de errores"""
    driver = None
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 20)
        
        # Verificar credenciales antes de continuar
        if USERNAME == "tu_usuario" or PASSWORD == "tu_password":
            log_message("⚠️ ADVERTENCIA: Usando credenciales por defecto. Actualiza el archivo .env", "WARN")
            return []
        
        # Login mejorado con más tiempo de espera
        log_message("🔑 Iniciando login mejorado...")
        driver.get(LOGIN_URL)
        
        # Esperar a que la página cargue completamente
        time.sleep(5)
        log_message("📄 Página de login cargada, buscando campos...")
        
        # Esperar y llenar credenciales con mejor selección
        try:
            # Intentar diferentes selectores para email/username
            email_selectors = [
                'input[name="email"]',
                'input[type="email"]',
                'input[placeholder*="email"]',
                'input[placeholder*="usuario"]',
                'input[placeholder*="Email"]',
                'input[placeholder*="Usuario"]',
                '.email-input',
                '#email',
                '#username',
                'input[class*="email"]',
                'input[class*="user"]'
            ]
            
            email_field = None
            for i, selector in enumerate(email_selectors):
                try:
                    log_message(f"🔍 Intentando selector {i+1}/{len(email_selectors)}: {selector}")
                    email_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    log_message(f"✅ Campo de email encontrado con selector: {selector}")
                    break
                except TimeoutException:
                    log_message(f"❌ Selector {selector} no funcionó")
                    continue
            
            if not email_field:
                # Intentar buscar cualquier input visible
                log_message("🔍 Buscando cualquier campo de input visible...")
                try:
                    inputs = driver.find_elements(By.TAG_NAME, "input")
                    for inp in inputs:
                        if inp.is_displayed() and inp.is_enabled():
                            email_field = inp
                            log_message(f"✅ Usando primer input visible: {inp.get_attribute('name') or inp.get_attribute('id') or 'sin-nombre'}")
                            break
                except:
                    pass
            
            if not email_field:
                raise Exception("❌ No se pudo encontrar el campo de email/usuario")
            
            # Hacer click primero para activar el campo
            email_field.click()
            time.sleep(1)
            email_field.clear()
            email_field.send_keys(USERNAME)
            log_message("✅ Campo de usuario completado")
            
            # Password field
            password_selectors = [
                'input[name="senha"]',
                'input[name="password"]',
                'input[type="password"]',
                '.password-input',
                '#password',
                'input[class*="password"]'
            ]
            
            password_field = None
            for i, selector in enumerate(password_selectors):
                try:
                    log_message(f"🔍 Buscando password con selector {i+1}/{len(password_selectors)}: {selector}")
                    password_field = driver.find_element(By.CSS_SELECTOR, selector)
                    log_message(f"✅ Campo de password encontrado con selector: {selector}")
                    break
                except NoSuchElementException:
                    log_message(f"❌ Selector password {selector} no funcionó")
                    continue
            
            if not password_field:
                # Buscar el segundo input si no encontramos password específico
                log_message("🔍 Buscando segundo campo de input...")
                try:
                    inputs = driver.find_elements(By.TAG_NAME, "input")
                    visible_inputs = [inp for inp in inputs if inp.is_displayed() and inp.is_enabled()]
                    if len(visible_inputs) >= 2:
                        password_field = visible_inputs[1]  # Segundo input
                        log_message("✅ Usando segundo input visible como password")
                except:
                    pass
            
            if not password_field:
                raise Exception("❌ No se pudo encontrar el campo de contraseña")
            
            # Hacer click y llenar password
            password_field.click()
            time.sleep(1)
            password_field.clear()
            password_field.send_keys(PASSWORD)
            log_message("✅ Campo de contraseña completado")
            
            # Submit button
            submit_selectors = [
                'button[type="submit"]',
                '.login-button',
                '.submit-button',
                'input[type="submit"]',
                'button[class*="login"]',
                'button[class*="submit"]',
                'button:contains("Login")',
                'button:contains("Entrar")',
                'button'  # Último recurso: cualquier botón
            ]
            
            submit_button = None
            for i, selector in enumerate(submit_selectors):
                try:
                    log_message(f"🔍 Buscando botón submit {i+1}/{len(submit_selectors)}: {selector}")
                    if selector == 'button':
                        # Para el último recurso, buscar todos los botones visibles
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        for btn in buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                submit_button = btn
                                log_message(f"✅ Usando botón visible: {btn.text[:20] if btn.text else 'sin-texto'}")
                                break
                    else:
                        submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                        log_message(f"✅ Botón submit encontrado: {selector}")
                    
                    if submit_button:
                        break
                except NoSuchElementException:
                    log_message(f"❌ Selector botón {selector} no funcionó")
                    continue
            
            if submit_button:
                submit_button.click()
                log_message("🚀 Botón de login presionado")
            else:
                log_message("⌨️ No se encontró botón, intentando Enter")
                password_field.send_keys(Keys.RETURN)
            
            # Esperar más tiempo para redirección
            log_message("⏳ Esperando redirección de login...")
            time.sleep(8)
            
        except Exception as e:
            log_message(f"❌ Error en login: {e}", "ERROR")
            
            # Información de depuración
            try:
                log_message("🔍 INFORMACIÓN DE DEPURACIÓN:")
                log_message(f"URL actual: {driver.current_url}")
                log_message(f"Título de página: {driver.title}")
                
                # Contar inputs visibles
                inputs = driver.find_elements(By.TAG_NAME, "input")
                visible_inputs = [inp for inp in inputs if inp.is_displayed()]
                log_message(f"Inputs visibles encontrados: {len(visible_inputs)}")
                
                for i, inp in enumerate(visible_inputs[:3]):  # Mostrar primeros 3
                    name = inp.get_attribute('name') or 'sin-nombre'
                    type_attr = inp.get_attribute('type') or 'sin-tipo'
                    placeholder = inp.get_attribute('placeholder') or 'sin-placeholder'
                    log_message(f"  Input {i+1}: name='{name}', type='{type_attr}', placeholder='{placeholder}'")
                
                # Contar botones visibles
                buttons = driver.find_elements(By.TAG_NAME, "button")
                visible_buttons = [btn for btn in buttons if btn.is_displayed()]
                log_message(f"Botones visibles encontrados: {len(visible_buttons)}")
                
                for i, btn in enumerate(visible_buttons[:3]):  # Mostrar primeros 3
                    text = btn.text[:30] if btn.text else 'sin-texto'
                    log_message(f"  Botón {i+1}: texto='{text}'")
                    
            except Exception as debug_e:
                log_message(f"Error en depuración: {debug_e}", "WARN")
            
            return []
        
        # Navegar al dashboard
        log_message("Navegando al dashboard...")
        driver.get(DASHBOARD_URL)
        time.sleep(5)
        
        # Extracción de números mejorada
        log_message("Extrayendo números...")
        
        # Script JavaScript mejorado para encontrar números
        extraction_script = """
        // Intentar múltiples métodos de extracción
        var numbers = [];
        
        // Método 1: Buscar en tabla
        var tables = document.querySelectorAll("table");
        for (var t = 0; t < tables.length; t++) {
            var rows = tables[t].querySelectorAll("tr");
        for (var i = 0; i < rows.length; i++) {
            var cells = rows[i].querySelectorAll("td");
            if (cells.length > 0) {
                var text = cells[0].textContent.trim();
                    if (text && !isNaN(text) && parseInt(text) >= 0 && parseInt(text) <= 36) {
                        numbers.push(text);
                    }
                }
            }
        }
        
        // Método 2: Buscar por clases comunes de números de ruleta
        var numberElements = document.querySelectorAll('.number, .roulette-number, [class*="number"], [class*="result"]');
        for (var i = 0; i < numberElements.length; i++) {
            var text = numberElements[i].textContent.trim();
            if (text && !isNaN(text) && parseInt(text) >= 0 && parseInt(text) <= 36) {
                if (numbers.indexOf(text) === -1) { // No duplicar
                    numbers.push(text);
                }
            }
        }
        
        // Método 3: Buscar en divs con texto numérico
        var allDivs = document.querySelectorAll("div");
        for (var i = 0; i < allDivs.length; i++) {
            var text = allDivs[i].textContent.trim();
            if (text && text.length <= 2 && !isNaN(text) && parseInt(text) >= 0 && parseInt(text) <= 36) {
                if (numbers.indexOf(text) === -1) { // No duplicar
                    numbers.push(text);
                }
            }
        }
        
        return numbers.slice(0, 20);  // Limitar a 20 números máximo
        """
        
        numbers = driver.execute_script(extraction_script)
        
        if numbers and len(numbers) > 0:
            log_message(f"Extraídos {len(numbers)} números. Más reciente: {numbers[0]}")
            return numbers
        else:
            log_message("No se encontraron números. Intentando método alternativo...")
            
            # Método alternativo: buscar en el HTML completo
            page_source = driver.page_source
            import re
            # Buscar patrones de números en el HTML
            number_patterns = re.findall(r'\b([0-9]|[12][0-9]|3[0-6])\b', page_source)
            if number_patterns:
                # Filtrar y tomar los primeros 20
                filtered_numbers = []
                for num in number_patterns:
                    if 0 <= int(num) <= 36 and num not in filtered_numbers:
                        filtered_numbers.append(num)
                    if len(filtered_numbers) >= 20:
                        break
                
                if filtered_numbers:
                    log_message(f"Método alternativo: encontrados {len(filtered_numbers)} números")
                    return filtered_numbers
            
            log_message("No se pudieron extraer números con ningún método.", "WARN")
            return []
            
    except Exception as e:
        log_message(f"Error: {e}", "ERROR")
        return []
    finally:
        if driver:
            driver.quit()

def save_numbers_to_json(numbers):
    """Save numbers to JSON file - Versión más rápida"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "numbers": numbers,
        "count": len(numbers)
    }
    
    # Escritura atómica para evitar corrupción
    temp_file = NUMBERS_JSON_FILE + ".tmp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))  # Sin espacios para ser más rápido
    
    os.replace(temp_file, NUMBERS_JSON_FILE)
    log_message(f"Guardados {len(numbers)} números en JSON")

def get_processed_numbers():
    """Get set of previously processed numbers - Versión más rápida"""
    processed = set()
    if os.path.exists(PROCESSED_NUMBERS_FILE):
        try:
            with open(PROCESSED_NUMBERS_FILE, 'r') as f:
                processed = set(line.strip() for line in f if line.strip())
        except:
            pass
    log_message(f"Cargados {len(processed)} números procesados previamente")
    return processed

def add_processed_numbers_batch(numbers):
    """Add multiple numbers to processed file at once - Más eficiente"""
    with open(PROCESSED_NUMBERS_FILE, 'a') as f:
        for number in numbers:
            f.write(f"{number}\n")

def get_last_seen_numbers():
    """Get last seen numbers for better duplicate detection"""
    if os.path.exists(LAST_SEEN_FILE):
        try:
            with open(LAST_SEEN_FILE, 'r') as f:
                data = json.load(f)
                return data.get('numbers', [])
        except:
            pass
    return []

def save_last_seen_numbers(numbers):
    """Save current numbers as last seen"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "numbers": numbers,
        "hash": hashlib.md5(str(numbers).encode()).hexdigest()
    }
    
    temp_file = LAST_SEEN_FILE + ".tmp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    
    os.replace(temp_file, LAST_SEEN_FILE)

# Función create_history_entry eliminada - ya no se usa Supabase

# Función send_numbers_to_supabase_batch eliminada - ya no se usa Supabase

def main():
    """Main function mejorada con mejor gestión de duplicados"""
    # Verificar instancia única
    check_single_instance()
    
    try:
        log_message("=== INICIANDO SCRAPER DE RULETA MEJORADO ===")
        
        # Get already processed numbers
        processed_numbers = get_processed_numbers()
        last_seen_numbers = get_last_seen_numbers()
        
        # Main loop
        consecutive_failures = 0
        max_failures = 3
    
    while True:
        try:
            # Extract numbers
                numbers = improved_login_and_extract_numbers()
            
            if not numbers:
                    consecutive_failures += 1
                    log_message(f"No se encontraron números. Fallos consecutivos: {consecutive_failures}")
                    
                    if consecutive_failures >= max_failures:
                        log_message("Demasiados fallos consecutivos. Esperando más tiempo...", "WARN")
                        time.sleep(REFRESH_INTERVAL * 2)
                        consecutive_failures = 0
                    else:
                time.sleep(REFRESH_INTERVAL)
                continue
            
                # Reset failure counter
                consecutive_failures = 0
                
            # Save to JSON file
            save_numbers_to_json(numbers)
            
                # Verificación mejorada de repetidos
                numbers_hash = hashlib.md5(str(numbers).encode()).hexdigest()
                last_hash = hashlib.md5(str(last_seen_numbers).encode()).hexdigest()
                
                if numbers_hash == last_hash:
                    log_message("Mismos números que la última vez (verificación por hash). Esperando...")
                    time.sleep(REFRESH_INTERVAL)
                    continue
                
                # Skip the most recent number (as before)
            most_recent = numbers[0]
                log_message(f"Número más reciente (OMITIENDO): {most_recent}")
            
            # Get numbers to process (all except most recent)
                numbers_to_process = numbers[1:] if len(numbers) > 1 else []
                
                if not numbers_to_process:
                    log_message("No hay números para procesar después de omitir el más reciente")
                    save_last_seen_numbers(numbers)
                time.sleep(REFRESH_INTERVAL)
                continue
                
                # Filter out already processed numbers (optimizado)
            new_numbers = [n for n in numbers_to_process if n not in processed_numbers]
            
            if not new_numbers:
                    log_message("No hay números nuevos para procesar")
                    save_last_seen_numbers(numbers)
                time.sleep(REFRESH_INTERVAL)
                continue
            
                log_message(f"Encontrados {len(new_numbers)} números nuevos para procesar: {new_numbers}")
                
                # Ya no se usa Supabase - solo guardado local
                log_message("Guardando solo localmente (Supabase eliminado)")
                success_count = len(new_numbers)
                
                # Mark as processed (en lote)
                processed_numbers.update(new_numbers)
                add_processed_numbers_batch(new_numbers)
            
            # Update last seen numbers
                save_last_seen_numbers(numbers)
            
                log_message(f"Procesamiento completado. Esperando {REFRESH_INTERVAL} segundos...")
            time.sleep(REFRESH_INTERVAL)
            
        except KeyboardInterrupt:
                log_message("Detenido por el usuario")
            break
        except Exception as e:
                consecutive_failures += 1
                log_message(f"Error en bucle principal: {e}", "ERROR")
                log_message(f"Esperando 30 segundos antes de reintentar... (Fallos: {consecutive_failures})")
            time.sleep(30)
                
                if consecutive_failures > 5:
                    log_message("Demasiados errores consecutivos. Terminando programa.", "ERROR")
                    break
    
    finally:
        cleanup_lock()
        log_message("=== SCRAPER FINALIZADO ===")

if __name__ == "__main__":
    main()
