#!/usr/bin/env python3
"""
Scraper Final de Lightning Roulette - COMPLETAMENTE FUNCIONAL
Con Redis y PostgreSQL sincronizados y sin login repetido
"""

import time
import json
import os
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

# Importar la clase de sincronización
from database_sync import SyncedRouletteDatabase, log_message

# Cargar variables de entorno
load_dotenv()

def clean_local_files():
    """Limpiar archivos locales de datos"""
    log_message("🗂️ Limpiando archivos locales...")

    files_to_clean = [
        "roulette_data/history_counter.txt",
        "roulette_data/last_seen_numbers.json",
        "roulette_data/pending_numbers.txt",
        "roulette_data/processed_numbers.txt",
        "roulette_data/roulette_numbers.json"
    ]

    cleaned_count = 0

    for file_path in files_to_clean:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                log_message(f"🗑️ Eliminado: {file_path}")
                cleaned_count += 1
            else:
                log_message(f"ℹ️ No existe: {file_path}")
        except Exception as e:
            log_message(f"❌ Error eliminando {file_path}: {e}", "ERROR")

    # Crear archivos básicos limpios
    try:
        os.makedirs("roulette_data", exist_ok=True)

        # Crear archivos con contenido inicial
        with open("roulette_data/history_counter.txt", "w") as f:
            f.write("0")

        with open("roulette_data/last_seen_numbers.json", "w") as f:
            f.write("[]")

        with open("roulette_data/processed_numbers.txt", "w") as f:
            f.write("")

        with open("roulette_data/pending_numbers.txt", "w") as f:
            f.write("")

        with open("roulette_data/roulette_numbers.json", "w") as f:
            f.write("[]")

        log_message("✅ Archivos locales reiniciados correctamente")
        return True

    except Exception as e:
        log_message(f"❌ Error reiniciando archivos: {e}", "ERROR")
        return False

def purge_all_databases_auto():
    """Función para limpiar completamente todas las bases de datos automáticamente"""

    log_message("=" * 60)
    log_message("🧹 DEPURACIÓN AUTOMÁTICA ANTES DE INICIAR SCRAPER")
    log_message("=" * 60)

    print("\n🧹 Depurando todas las bases de datos automáticamente...")
    print("   • Redis - Todas las claves de roulette")
    print("   • PostgreSQL - Tabla roulette_numbers completa")
    print("   • Archivos locales - Historial y contadores")

    log_message("🚀 Iniciando depuración automática...")

    # Inicializar base de datos
    db = SyncedRouletteDatabase()

    # Limpiar bases de datos
    redis_success, postgres_success = db.purge_all_data()

    # Limpiar archivos locales
    local_files_cleaned = clean_local_files()

    # Resultado final
    if redis_success and postgres_success and local_files_cleaned:
        log_message("🎉 ¡DEPURACIÓN AUTOMÁTICA EXITOSA!")
        log_message("✅ Redis: Limpio")
        log_message("✅ PostgreSQL: Limpio")
        log_message("✅ Archivos locales: Limpios")
        print("\n🚀 Sistema completamente limpio - Iniciando scraper...")
    else:
        log_message("⚠️ Depuración parcial:")
        log_message(f"   Redis: {'✅' if redis_success else '❌'}")
        log_message(f"   PostgreSQL: {'✅' if postgres_success else '❌'}")
        log_message(f"   Archivos locales: {'✅' if local_files_cleaned else '❌'}")
        print("\n⚠️ Algunas bases no se pudieron limpiar completamente")

    db.close_connections()
    log_message("=" * 60)
    return redis_success and postgres_success and local_files_cleaned

# Configuración
LOGIN_URL = os.getenv("LOGIN_URL", "https://www.iamonstro.com.br/sistema/index.php")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://www.iamonstro.com.br/sistema/dashboard.php?mesa=Lightning%20Roulette")
USERNAME = os.getenv("ROULETTE_USERNAME", "tu_usuario")
PASSWORD = os.getenv("ROULETTE_PASSWORD", "tu_password")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "10"))

class FinalRouletteScraper:
    """Scraper final con todas las correcciones aplicadas"""

    def __init__(self):
        self.driver = None
        self.db_handler = SyncedRouletteDatabase()
        self.last_number = None
        self.consecutive_errors = 0

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

    def save_numbers_to_json(self, numbers):
        """Guardar números en archivo JSON local"""
        # Validate numbers are between 0-36
        valid_numbers = []
        for num in numbers:
            try:
                num_int = int(num)
                if 0 <= num_int <= 36:
                    valid_numbers.append(num_int)
                else:
                    log_message(f"⚠️ Número inválido ignorado en JSON: {num} (debe ser 0-36)", "WARN")
            except (ValueError, TypeError):
                log_message(f"⚠️ Número no numérico ignorado en JSON: {num}", "WARN")

        data = {
            "timestamp": datetime.now().isoformat(),
            "numbers": valid_numbers
        }

        data_dir = "roulette_data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        json_file = os.path.join(data_dir, "roulette_numbers.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def setup_session(self):
        """Configurar sesión persistente con login una sola vez"""
        log_message("🔧 Configurando sesión persistente...")

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

            log_message("✅ Sesión persistente configurada")
            return True

        except Exception as e:
            log_message(f"❌ Error configurando sesión: {e}", "ERROR")
            if self.driver:
                self.driver.quit()
                self.driver = None
            return False

    def extract_numbers_fast(self):
        """Extraer números rápidamente sin login"""
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
                        // Validar que el número esté en rango 0-36
                        if (num >= 0 && num <= 36) {
                            numbers.push(num);
                        }
                    }
                }
            }

            // NO reverse - ya están en orden correcto (más reciente primero)
            return numbers;
            """)

            if numbers and len(numbers) > 0:
                log_message(f"⚡ Extraídos {len(numbers)} números válidos (0-36). Más reciente: {numbers[0]}")
                return numbers
            else:
                log_message("⚠️ No se encontraron números válidos")
                return []

        except Exception as e:
            log_message(f"❌ Error extrayendo números: {e}", "ERROR")
            return []

    def run(self):
        """Ejecutar el scraper principal"""
        log_message("🚀 SCRAPER FINAL - REDIS + POSTGRESQL SINCRONIZADOS")
        log_message("✨ Características: Sin login repetido, bases sincronizadas, ultra rápido, números 0-36")

        try:
            # 🧹 DEPURACIÓN AUTOMÁTICA ANTES DE INICIAR
            log_message("🧹 Ejecutando depuración automática antes de iniciar...")
            purge_success = purge_all_databases_auto()

            if not purge_success:
                log_message("⚠️ Advertencia: La depuración no fue completamente exitosa")
                log_message("🔄 Continuando con el scraper de todos modos...")

            # Reinicializar conexión de base de datos después de la limpieza
            if self.db_handler:
                self.db_handler.close_connections()
            self.db_handler = SyncedRouletteDatabase()

            # Mostrar estado inicial (después de limpieza)
            log_message("📊 Estado después de la depuración:")
            self.db_handler.get_sync_status()

            # Configurar sesión inicial
            if not self.setup_session():
                log_message("❌ No se pudo configurar la sesión")
                return

            # Main loop
            while True:
                try:
                    log_message("⚡ Extracción rápida...")

                    numbers = self.extract_numbers_fast()

                    if not numbers:
                        self.consecutive_errors += 1
                        log_message(f"❌ Sin números. Errores: {self.consecutive_errors}")

                        if self.consecutive_errors >= 3:
                            log_message("🔄 Reconfiguración de sesión...")
                            if self.driver:
                                self.driver.quit()
                            if self.setup_session():
                                self.consecutive_errors = 0
                            else:
                                time.sleep(30)
                        else:
                            time.sleep(REFRESH_INTERVAL)
                        continue

                    self.consecutive_errors = 0

                    # Guardar en JSON local
                    self.save_numbers_to_json(numbers)

                    # Verificar cambios
                    current_number = numbers[0]
                    log_message(f"🔢 Número actual: {current_number} (válido 0-36)")

                    if current_number == self.last_number:
                        log_message(f"⏸️ Sin cambios ({current_number}). Esperando...")
                        time.sleep(REFRESH_INTERVAL)
                        continue

                    # ¡CAMBIO DETECTADO!
                    log_message(f"🆕 ¡NUEVO NÚMERO! {self.last_number} → {current_number}")

                    # SOLO guardar EL número más reciente (uno por vez)
                    numbers_to_save = [current_number]
                    log_message(f"🎯 Guardando SOLO el más reciente: {current_number}")

                    # GUARDAR EN AMBAS BASES DE DATOS
                    redis_success, postgres_success = self.db_handler.save_numbers(numbers_to_save)

                    # Actualizar último número
                    self.last_number = current_number

                    # Mostrar estado de sincronización
                    self.db_handler.get_sync_status()

                    # Pausa
                    log_message(f"⏰ Pausa de {REFRESH_INTERVAL}s...")
                    time.sleep(REFRESH_INTERVAL)

                except KeyboardInterrupt:
                    log_message("🛑 Detenido por usuario")
                    break
                except Exception as e:
                    self.consecutive_errors += 1
                    log_message(f"❌ Error: {e}")
                    time.sleep(10)

        finally:
            if self.driver:
                self.driver.quit()
            self.db_handler.close_connections()
            log_message("🔌 Scraper cerrado")

def main():
    """Función principal"""
    scraper = FinalRouletteScraper()
    scraper.run()

if __name__ == "__main__":
    main()