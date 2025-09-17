#!/usr/bin/env python3
"""
Scraper Redis Only - Lightning Roulette
Scraper optimizado que guarda datos únicamente en Redis para máxima velocidad
"""

import time
import json
import os
import redis
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
LOGIN_URL = os.getenv("LOGIN_URL", "https://www.iamonstro.com.br/sistema/index.php")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://www.iamonstro.com.br/sistema/dashboard.php?mesa=Lightning%20Roulette")
USERNAME = os.getenv("ROULETTE_USERNAME", "tu_usuario")
PASSWORD = os.getenv("ROULETTE_PASSWORD", "tu_password")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "8"))

# Configuración Redis
REDIS_URL = (
    os.getenv('REDIS_PUBLIC_URL') or
    os.getenv('Connection_redis') or
    os.getenv('REDIS_URL') or
    'redis://default:kuBKgwJxPrMoMOWqpobsGZIcpgnOFwoW@ballast.proxy.rlwy.net:58381'
)

def log_message(message, level="INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def get_color_for_number(number: int) -> str:
    """Determinar color para número de ruleta"""
    if number == 0:
        return 'green'

    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    return 'red' if number in red_numbers else 'black'

class RedisRouletteScraper:
    """Scraper optimizado que usa únicamente Redis"""

    def __init__(self):
        self.driver = None
        self.redis_client = None
        self.last_number = None
        self.consecutive_errors = 0

        # Inicializar Redis
        self.setup_redis()

    def setup_redis(self):
        """Configurar conexión Redis"""
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            log_message("✅ Conectado a Redis exitosamente")

            # Mostrar estado inicial
            current_count = self.redis_client.llen('roulette:history')
            latest = self.redis_client.get('roulette:latest')
            log_message(f"📊 Estado inicial Redis - Números en historial: {current_count}, Último: {latest}")

        except Exception as e:
            log_message(f"❌ Error conectando a Redis: {e}", "ERROR")
            self.redis_client = None

    def setup_chrome_driver(self):
        """Configurar Chrome driver optimizado"""
        options = Options()
        options.add_argument("--headless")
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

    def setup_session(self):
        """Configurar sesión persistente con login"""
        log_message("🔧 Configurando sesión...")

        try:
            self.driver = self.setup_chrome_driver()

            # Login
            self.driver.get(LOGIN_URL)
            time.sleep(2)

            wait = WebDriverWait(self.driver, 10)
            email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_field.clear()
            email_field.send_keys(USERNAME)

            password_field = self.driver.find_element(By.NAME, "senha")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            password_field.send_keys(Keys.RETURN)

            time.sleep(3)

            # Navigate to dashboard
            self.driver.get(DASHBOARD_URL)
            time.sleep(2)

            log_message("✅ Sesión configurada exitosamente")
            return True

        except Exception as e:
            log_message(f"❌ Error configurando sesión: {e}", "ERROR")
            if self.driver:
                self.driver.quit()
                self.driver = None
            return False

    def extract_numbers(self):
        """Extraer números de la tabla"""
        if not self.driver:
            return []

        try:
            self.driver.refresh()
            time.sleep(1.5)

            numbers = self.driver.execute_script("""
            var table = document.querySelector("table");
            if (!table) return [];

            var rows = table.querySelectorAll("tr");
            var numbers = [];

            // Leer desde ABAJO hacia ARRIBA (más reciente al más antiguo)
            for (var i = rows.length - 1; i >= 0; i--) {
                var cells = rows[i].querySelectorAll("td");
                if (cells.length > 0) {
                    var text = cells[0].textContent.trim();
                    if (text && !isNaN(text)) {
                        var num = parseInt(text);
                        if (num >= 0 && num <= 36) {
                            numbers.push(num);
                        }
                    }
                }
            }

            return numbers;
            """)

            if numbers and len(numbers) > 0:
                log_message(f"⚡ Extraídos {len(numbers)} números. Más reciente: {numbers[0]}")
                return numbers
            else:
                log_message("⚠️ No se encontraron números válidos")
                return []

        except Exception as e:
            log_message(f"❌ Error extrayendo números: {e}", "ERROR")
            return []

    def save_number_to_redis(self, number: int) -> bool:
        """Guardar número individual en Redis (optimizado)"""
        if not self.redis_client:
            log_message("❌ Redis no disponible", "ERROR")
            return False

        try:
            color = get_color_for_number(number)
            timestamp = datetime.utcnow().isoformat()

            # Usar pipeline para operaciones atómicas
            pipe = self.redis_client.pipeline()

            # 1. Añadir al historial (más reciente primero)
            pipe.lpush('roulette:history', str(number))

            # 2. Actualizar último número
            pipe.set('roulette:latest', str(number))

            # 3. Actualizar contadores de colores
            if color == 'red':
                pipe.incr('roulette:colors:red')
            elif color == 'black':
                pipe.incr('roulette:colors:black')
            else:  # green
                pipe.incr('roulette:colors:green')

            # 4. Actualizar total spins
            pipe.incr('roulette:total_spins')

            # 5. Mantener solo los últimos 200 números
            pipe.ltrim('roulette:history', 0, 199)

            # 6. Actualizar estadísticas
            pipe.hset('roulette:stats', mapping={
                'last_update': timestamp,
                'latest_number': str(number),
                'latest_color': color,
                'scraper_last_save': timestamp
            })

            # 7. Marcar en el log de scraper
            pipe.lpush('scraper:log', f"{timestamp}|{number}|{color}")
            pipe.ltrim('scraper:log', 0, 99)  # Mantener últimos 100 logs

            # Ejecutar todas las operaciones
            results = pipe.execute()

            log_message(f"💾 GUARDADO: {number} ({color}) en Redis ✅")

            # Obtener estadísticas actualizadas
            total_spins = self.redis_client.get('roulette:total_spins')
            history_count = self.redis_client.llen('roulette:history')
            red_count = self.redis_client.get('roulette:colors:red') or 0
            black_count = self.redis_client.get('roulette:colors:black') or 0
            green_count = self.redis_client.get('roulette:colors:green') or 0

            log_message(f"📊 Stats: Total:{total_spins} | Historial:{history_count} | R:{red_count} B:{black_count} G:{green_count}")

            return True

        except Exception as e:
            log_message(f"❌ Error guardando en Redis: {e}", "ERROR")
            return False

    def check_redis_health(self):
        """Verificar salud de Redis"""
        try:
            self.redis_client.ping()
            return True
        except:
            log_message("⚠️ Redis no responde, reintentando conexión...", "WARNING")
            try:
                self.setup_redis()
                return self.redis_client is not None
            except:
                return False

    def run(self):
        """Ejecutar el scraper principal"""
        log_message("🚀 SCRAPER REDIS-ONLY INICIADO")
        log_message("⚡ Modo: Ultra rápido - Solo Redis")

        if not self.redis_client:
            log_message("❌ No se puede continuar sin Redis", "ERROR")
            return

        try:
            # Configurar sesión inicial
            if not self.setup_session():
                log_message("❌ No se pudo configurar la sesión")
                return

            # Obtener número inicial para comparación
            initial_numbers = self.extract_numbers()
            if initial_numbers:
                self.last_number = initial_numbers[0]
                log_message(f"🎯 Número inicial detectado: {self.last_number}")

            # Loop principal
            iteration = 0
            while True:
                try:
                    iteration += 1
                    log_message(f"🔄 Iteración #{iteration} - Verificando nuevos números...")

                    # Verificar salud de Redis
                    if not self.check_redis_health():
                        log_message("❌ Redis no disponible", "ERROR")
                        time.sleep(30)
                        continue

                    # Extraer números
                    numbers = self.extract_numbers()

                    if not numbers:
                        self.consecutive_errors += 1
                        log_message(f"❌ Sin números. Errores consecutivos: {self.consecutive_errors}")

                        if self.consecutive_errors >= 3:
                            log_message("🔄 Reconfiguración de sesión por errores...")
                            if self.driver:
                                self.driver.quit()
                            if self.setup_session():
                                self.consecutive_errors = 0
                                log_message("✅ Sesión reconfigurada")
                            else:
                                log_message("❌ Error reconfiguración, pausa larga")
                                time.sleep(60)
                        else:
                            time.sleep(REFRESH_INTERVAL)
                        continue

                    # Reset errores consecutivos
                    self.consecutive_errors = 0

                    # Verificar cambios
                    current_number = numbers[0]

                    if current_number == self.last_number:
                        log_message(f"⏸️ Sin cambios (actual: {current_number})")
                        time.sleep(REFRESH_INTERVAL)
                        continue

                    # ¡NUEVO NÚMERO DETECTADO!
                    log_message(f"🆕 ¡CAMBIO DETECTADO! {self.last_number} → {current_number}")

                    # Guardar SOLO el número más reciente
                    save_success = self.save_number_to_redis(current_number)

                    if save_success:
                        self.last_number = current_number
                        log_message(f"✅ Número {current_number} procesado exitosamente")

                        # Llamar al endpoint del backend para generar predicción automática
                        try:
                            import requests
                            backend_url = "http://localhost:5000/api/roulette/numbers"
                            response = requests.post(backend_url,
                                                   json={"number": current_number},
                                                   timeout=5)
                            if response.status_code == 200:
                                log_message("🤖 Backend notificado - predicción automática generada")
                            else:
                                log_message(f"⚠️ Backend respondió: {response.status_code}")
                        except Exception as backend_error:
                            log_message(f"⚠️ No se pudo notificar al backend: {backend_error}")
                    else:
                        log_message(f"❌ Error guardando número {current_number}")

                    # Pausa
                    log_message(f"⏰ Pausa de {REFRESH_INTERVAL}s...")
                    time.sleep(REFRESH_INTERVAL)

                except KeyboardInterrupt:
                    log_message("🛑 Detenido por usuario")
                    break
                except Exception as e:
                    self.consecutive_errors += 1
                    log_message(f"❌ Error en iteración: {e}", "ERROR")
                    time.sleep(10)

        finally:
            if self.driver:
                self.driver.quit()
            if self.redis_client:
                # Marcar fin del scraper
                try:
                    self.redis_client.hset('scraper:status', mapping={
                        'last_run': datetime.utcnow().isoformat(),
                        'status': 'stopped',
                        'reason': 'normal_shutdown'
                    })
                except:
                    pass
            log_message("🔌 Scraper cerrado")

def main():
    """Función principal"""
    log_message("=" * 60)
    log_message("🚀 INICIANDO SCRAPER REDIS-ONLY")
    log_message("⚡ Velocidad máxima - Sin PostgreSQL")
    log_message("=" * 60)

    scraper = RedisRouletteScraper()
    scraper.run()

if __name__ == "__main__":
    main()