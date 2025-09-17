import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

LOGIN_URL = os.getenv("LOGIN_URL", "https://bcgame.com/login")
USERNAME = os.getenv("ROULETTE_USERNAME", "tu_usuario")
PASSWORD = os.getenv("ROULETTE_PASSWORD", "tu_password")

def setup_debug_driver():
    """Setup Chrome driver SIN headless para ver la página"""
    options = Options()
    # NO HEADLESS para debug visual
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def debug_login_page():
    """Debug de la página de login para ver elementos disponibles"""
    driver = None
    try:
        driver = setup_debug_driver()
        
        print("🔍 Navegando a la página de login...")
        driver.get(LOGIN_URL)
        time.sleep(5)  # Tiempo para que cargue completamente
        
        print(f"📍 URL actual: {driver.current_url}")
        print(f"📄 Título de la página: {driver.title}")
        
        # Buscar todos los inputs
        print("\n🔎 BUSCANDO TODOS LOS INPUTS:")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"   Total de inputs encontrados: {len(inputs)}")
        
        for i, inp in enumerate(inputs):
            try:
                name = inp.get_attribute('name') or 'sin-name'
                type_attr = inp.get_attribute('type') or 'sin-type'
                placeholder = inp.get_attribute('placeholder') or 'sin-placeholder'
                id_attr = inp.get_attribute('id') or 'sin-id'
                class_attr = inp.get_attribute('class') or 'sin-class'
                visible = inp.is_displayed()
                enabled = inp.is_enabled()
                
                print(f"   Input {i+1}:")
                print(f"     - name: '{name}'")
                print(f"     - type: '{type_attr}'")
                print(f"     - placeholder: '{placeholder}'")
                print(f"     - id: '{id_attr}'")
                print(f"     - class: '{class_attr}'")
                print(f"     - visible: {visible}")
                print(f"     - enabled: {enabled}")
                print()
            except Exception as e:
                print(f"   Error obteniendo info del input {i+1}: {e}")
        
        # Buscar todos los botones
        print("\n🔎 BUSCANDO TODOS LOS BOTONES:")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"   Total de botones encontrados: {len(buttons)}")
        
        for i, btn in enumerate(buttons):
            try:
                text = btn.text[:50] if btn.text else 'sin-texto'
                type_attr = btn.get_attribute('type') or 'sin-type'
                class_attr = btn.get_attribute('class') or 'sin-class'
                visible = btn.is_displayed()
                enabled = btn.is_enabled()
                
                print(f"   Botón {i+1}:")
                print(f"     - texto: '{text}'")
                print(f"     - type: '{type_attr}'")
                print(f"     - class: '{class_attr}'")
                print(f"     - visible: {visible}")
                print(f"     - enabled: {enabled}")
                print()
            except Exception as e:
                print(f"   Error obteniendo info del botón {i+1}: {e}")
        
        # Buscar forms
        print("\n🔎 BUSCANDO FORMULARIOS:")
        forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"   Total de formularios encontrados: {len(forms)}")
        
        for i, form in enumerate(forms):
            try:
                action = form.get_attribute('action') or 'sin-action'
                method = form.get_attribute('method') or 'sin-method'
                class_attr = form.get_attribute('class') or 'sin-class'
                
                print(f"   Form {i+1}:")
                print(f"     - action: '{action}'")
                print(f"     - method: '{method}'")
                print(f"     - class: '{class_attr}'")
                print()
            except Exception as e:
                print(f"   Error obteniendo info del form {i+1}: {e}")
        
        # Buscar elementos por selectores comunes de login
        print("\n🔎 PROBANDO SELECTORES COMUNES DE LOGIN:")
        
        selectors_email = [
            'input[name="email"]',
            'input[type="email"]',
            'input[placeholder*="email"]',
            'input[placeholder*="Email"]',
            'input[class*="email"]',
            '#email',
            '.email-input',
            'input[name="username"]',
            'input[name="user"]',
            'input[autocomplete="email"]',
            'input[autocomplete="username"]'
        ]
        
        for selector in selectors_email:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   ✅ Encontrado con '{selector}': {len(elements)} elemento(s)")
                    for j, elem in enumerate(elements):
                        visible = elem.is_displayed()
                        enabled = elem.is_enabled()
                        print(f"      Elemento {j+1}: visible={visible}, enabled={enabled}")
                else:
                    print(f"   ❌ No encontrado: '{selector}'")
            except Exception as e:
                print(f"   ❌ Error con '{selector}': {e}")
        
        print("\n⏳ Esperando 30 segundos para inspección manual...")
        print("   Puedes inspeccionar la página manualmente en el navegador que se abrió.")
        time.sleep(30)
        
    except Exception as e:
        print(f"❌ Error general: {e}")
    finally:
        if driver:
            print("🔒 Cerrando navegador...")
            driver.quit()

if __name__ == "__main__":
    debug_login_page() 