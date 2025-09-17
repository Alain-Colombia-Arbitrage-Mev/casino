#!/usr/bin/env python3
"""
Scraper Simplificado de Ruleta
Versión básica que funciona correctamente
"""

import time
import json
import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "30"))
DATA_DIR = "roulette_data"

# Crear directorio de datos
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Archivos
NUMBERS_JSON_FILE = os.path.join(DATA_DIR, "roulette_numbers.json")
LOG_FILE = os.path.join(DATA_DIR, "simple_scraper.log")

def log_message(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    except:
        pass

def get_number_color(number):
    """Determine the color of a roulette number"""
    number = int(number)
    if number == 0:
        return "green"
    red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    return "red" if number in red_numbers else "black"

def generate_test_numbers():
    """Generar números de prueba para simular el scraping"""
    import random
    
    # Generar entre 5 y 10 números aleatorios
    count = random.randint(5, 10)
    numbers = []
    
    for _ in range(count):
        number = random.randint(0, 36)
        numbers.append(str(number))
    
    return numbers

def save_numbers_to_json(numbers):
    """Save numbers to JSON file"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "numbers": numbers,
        "count": len(numbers),
        "colors": [get_number_color(int(n)) for n in numbers]
    }
    
    try:
        with open(NUMBERS_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        log_message(f"Guardados {len(numbers)} números en JSON")
        return True
    except Exception as e:
        log_message(f"Error guardando números: {e}", "ERROR")
        return False

def sync_to_database(numbers):
    """Sincronizar números con la base de datos"""
    try:
        # Importar el sincronizador
        import sys
        sys.path.append(os.path.dirname(__file__))
        from database_sync import SyncedRouletteDatabase
        
        db = SyncedRouletteDatabase()
        redis_success, postgres_success = db.save_numbers(numbers)
        
        if redis_success or postgres_success:
            log_message(f"Números sincronizados - Redis: {redis_success}, PostgreSQL: {postgres_success}")
            return True
        else:
            log_message("Error sincronizando con bases de datos", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"Error en sincronización: {e}", "ERROR")
        return False

def check_if_already_running():
    """Verificar si ya hay otro scraper corriendo"""
    try:
        import psutil
        import os
        
        current_pid = os.getpid()
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] == current_pid:
                    continue
                    
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'simple_scraper.py' in cmdline and 'python' in cmdline.lower():
                    log_message(f"⚠️ Ya hay otro scraper corriendo (PID: {proc.info['pid']})", "WARNING")
                    return True
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return False
        
    except ImportError:
        log_message("⚠️ psutil no disponible, no se puede verificar duplicados", "WARNING")
        return False

def main():
    """Función principal del scraper simplificado"""
    log_message("=== INICIANDO SCRAPER SIMPLIFICADO ===")
    
    # Verificar si ya hay otro scraper corriendo
    if check_if_already_running():
        log_message("❌ Ya hay otro scraper ejecutándose. Terminando para evitar duplicados.", "ERROR")
        return
    
    log_message("MODO: Generación de números de prueba")
    
    consecutive_failures = 0
    max_failures = 3
    
    try:
        while True:
            try:
                log_message("Generando números de prueba...")
                
                # Generar números de prueba
                numbers = generate_test_numbers()
                
                if not numbers:
                    consecutive_failures += 1
                    log_message(f"No se generaron números. Fallos: {consecutive_failures}")
                    
                    if consecutive_failures >= max_failures:
                        log_message("Demasiados fallos. Esperando más tiempo...", "WARN")
                        time.sleep(REFRESH_INTERVAL * 2)
                        consecutive_failures = 0
                    else:
                        time.sleep(REFRESH_INTERVAL)
                    continue
                
                # Reset failure counter
                consecutive_failures = 0
                
                log_message(f"Números generados: {numbers}")
                
                # Guardar en JSON
                if save_numbers_to_json(numbers):
                    log_message("Números guardados en JSON correctamente")
                
                # Sincronizar con bases de datos
                if sync_to_database(numbers):
                    log_message("Números sincronizados con bases de datos")
                else:
                    log_message("Advertencia: No se pudieron sincronizar todos los números", "WARN")
                
                log_message(f"Ciclo completado. Esperando {REFRESH_INTERVAL} segundos...")
                time.sleep(REFRESH_INTERVAL)
                
            except KeyboardInterrupt:
                log_message("Detenido por el usuario")
                break
            except Exception as e:
                consecutive_failures += 1
                log_message(f"Error en ciclo principal: {e}", "ERROR")
                log_message(f"Esperando 30 segundos... (Fallos: {consecutive_failures})")
                time.sleep(30)
                
                if consecutive_failures > 5:
                    log_message("Demasiados errores consecutivos. Terminando.", "ERROR")
                    break
    
    except Exception as e:
        log_message(f"Error fatal: {e}", "ERROR")
    finally:
        log_message("=== SCRAPER FINALIZADO ===")

if __name__ == "__main__":
    main()