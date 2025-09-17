#!/usr/bin/env python3
"""
Scraper de Lightning Roulette con sesión persistente - SIN LOGIN REPETIDO
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Importar las clases sincronizadas
from database_sync import SyncedRouletteDatabase, log_message, get_number_color

# URLs y credenciales
LOGIN_URL = os.getenv("LOGIN_URL", "https://www.iamonstro.com.br/sistema/index.php")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://www.iamonstro.com.br/sistema/dashboard.php?mesa=Lightning%20Roulette")
USERNAME = os.getenv("ROULETTE_USERNAME", "tu_usuario")
PASSWORD = os.getenv("ROULETTE_PASSWORD", "tu_password")

# Cargar variables de entorno
load_dotenv()

REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "10"))

class PersistentRouletteScraper:
    """Scraper con sesión persistente para evitar logins repetidos"""
    
    def __init__(self):
        self.driver = None
        self.db_handler = SyncedRouletteDatabase()
        self.last_number = None
        self.consecutive_errors = 0
        self.login_attempts = 0
        
    def setup_session(self):
        """Configurar la sesión persistente una sola vez"""
        log_message("🔧 Configurando sesión persistente...")
        
        try:
            # Setup driver
            self.driver = self.setup_chrome_driver()
            
            # Login proceso
            self.driver.get(LOGIN_URL)
            time.sleep(2)
            
            # Login fields
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
            
            log_message("✅ Sesión persistente configurada exitosamente")
            return True
            
        except Exception as e:
            log_message(f"❌ Error configurando sesión: {e}", "ERROR")
            if self.driver:
                self.driver.quit()
                self.driver = None
            return False
    
    def extract_numbers_fast(self):
        """Extraer números usando la sesión persistente (SIN LOGIN)"""
        if not self.driver:
            return []
        
        try:
            # Solo refresh de la página actual
            self.driver.refresh()
            time.sleep(1.5)  # Tiempo mínimo
            
            # Extract numbers
            numbers = self.driver.execute_script("""
            var table = document.querySelector("table");
            if (!table) return [];
            
            var rows = table.querySelectorAll("tr");
            var numbers = [];
            
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll("td");
                if (cells.length > 0) {
                    var text = cells[0].textContent.trim();
                    if (text && !isNaN(text)) {
                        numbers.push(text);
                    }
                }
            }
            
            return numbers.reverse();  // Newest first
            """)
            
            if numbers and len(numbers) > 0:
                log_message(f"⚡ Extracción rápida: {len(numbers)} números. Más reciente: {numbers[0]}")
                return numbers
            else:
                log_message("⚠️ No se encontraron números en extracción rápida")
                return []
                
        except Exception as e:
            log_message(f"❌ Error en extracción rápida: {e}", "ERROR")
            return []
    
    def save_to_databases(self, numbers):
        """Guardar números en las bases de datos"""
        if not numbers:
            return False, False
        
        log_message("📤 Guardando en bases de datos...")
        
        # Redis
        redis_success = self.db_handler.save_to_redis(numbers)
        
        # PostgreSQL
        postgres_success = self.db_handler.save_to_postgres(numbers)
        
        return redis_success, postgres_success
    
    def run(self):
        """Ejecutar el scraper con sesión persistente"""
        log_message("🚀 SCRAPER CON SESIÓN PERSISTENTE")
        log_message("✨ Modo: Sin login repetido - Ultra rápido")
        
        try:
            # Setup inicial de sesión
            if not self.setup_session():
                log_message("❌ No se pudo configurar la sesión inicial")
                return
            
            # Main loop
            while True:
                try:
                    log_message("⚡ Extracción rápida (sin login)...")
                    
                    # Extraer números usando sesión persistente
                    numbers = self.extract_numbers_fast()
                    
                    if not numbers:
                        self.consecutive_errors += 1
                        log_message(f"❌ Sin números. Errores consecutivos: {self.consecutive_errors}")
                        
                        # Si hay muchos errores, reconfigurar sesión
                        if self.consecutive_errors >= 3:
                            log_message("🔄 Reconfiguración de sesión...")
                            if self.driver:
                                self.driver.quit()
                            if self.setup_session():
                                self.consecutive_errors = 0
                            else:
                                log_message("❌ Error reconfiguración. Pausa larga...")
                                time.sleep(30)
                        else:
                            time.sleep(REFRESH_INTERVAL)
                        continue
                    
                    self.consecutive_errors = 0  # Reset error count
                    
                    # Guardar en JSON
                    save_numbers_to_json(numbers)
                    
                    # Verificar números nuevos
                    current_number = numbers[0]
                    log_message(f"🔢 Número actual: {current_number}")
                    
                    if current_number == self.last_number:
                        log_message(f"⏸️ Mismo número ({current_number}). Esperando cambio...")
                        time.sleep(REFRESH_INTERVAL)
                        continue
                    
                    # ¡NÚMERO NUEVO!
                    log_message(f"🆕 ¡CAMBIO DETECTADO! {self.last_number} → {current_number}")
                    
                    # Determinar números a enviar
                    if self.last_number is None:
                        # Primera ejecución
                        numbers_to_send = numbers[:3]
                        log_message(f"🎯 Primera ejecución: {numbers_to_send}")
                    else:
                        # Solo el nuevo número
                        numbers_to_send = [current_number]
                        log_message(f"🎯 Enviando nuevo: {numbers_to_send}")
                    
                    # GUARDAR EN BASES DE DATOS
                    redis_success, postgres_success = self.save_to_databases(numbers_to_send)
                    
                    # Resultados
                    if redis_success or postgres_success:
                        log_message(f"✅ ¡GUARDADO EXITOSO! {len(numbers_to_send)} números")
                        log_message(f"   Redis: {'✅' if redis_success else '❌'}")
                        log_message(f"   PostgreSQL: {'✅' if postgres_success else '❌'}")
                    else:
                        log_message("❌ Error guardando en ambas bases de datos")
                    
                    # Actualizar último número
                    self.last_number = current_number
                    
                    # Pausa corta
                    log_message(f"⏰ Pausa de {REFRESH_INTERVAL}s...")
                    time.sleep(REFRESH_INTERVAL)
                    
                except KeyboardInterrupt:
                    log_message("🛑 Detenido por usuario")
                    break
                except Exception as e:
                    self.consecutive_errors += 1
                    log_message(f"❌ Error en bucle: {e}")
                    log_message(f"⏳ Pausa de 10s... (errores: {self.consecutive_errors})")
                    time.sleep(10)
        
        finally:
            if self.driver:
                self.driver.quit()
            self.db_handler.close_connections()
            log_message("🔌 Sesión cerrada")

def main():
    """Función principal"""
    scraper = PersistentRouletteScraper()
    scraper.run()

if __name__ == "__main__":
    main() 