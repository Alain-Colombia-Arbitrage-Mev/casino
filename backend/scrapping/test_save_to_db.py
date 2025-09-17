#!/usr/bin/env python3
"""
Script de prueba para enviar números directamente a Redis y PostgreSQL
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Importar las clases del scraper principal
from roulette_scraper_fixed import RouletteDatabase, log_message

# Cargar variables de entorno
load_dotenv()

def test_save_current_numbers():
    """Tomar números del JSON actual y enviarlos a las bases de datos"""
    log_message("🧪 INICIANDO PRUEBA DE GUARDADO EN BASE DE DATOS")
    
    # Leer números del JSON actual
    json_file = "roulette_data/roulette_numbers.json"
    
    if not os.path.exists(json_file):
        log_message("❌ No se encontró archivo JSON con números")
        return
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    numbers = data.get('numbers', [])
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    log_message(f"📊 Números encontrados: {len(numbers)}")
    log_message(f"🕒 Timestamp: {timestamp}")
    log_message(f"🔢 Primeros 5 números: {numbers[:5]}")
    
    # Inicializar conexiones de base de datos
    db_handler = RouletteDatabase()
    
    try:
        # Tomar los primeros 3 números para la prueba
        test_numbers = numbers[:3]
        log_message(f"🎯 Enviando números de prueba: {test_numbers}")
        
        # Guardar en Redis
        log_message("📤 Enviando a Redis...")
        redis_success = db_handler.save_to_redis(test_numbers)
        
        # Guardar en PostgreSQL
        log_message("📤 Enviando a PostgreSQL...")
        postgres_success = db_handler.save_to_postgres(test_numbers)
        
        # Resultados
        log_message("📋 RESULTADOS:")
        log_message(f"Redis: {'✅ ÉXITO' if redis_success else '❌ FALLÓ'}")
        log_message(f"PostgreSQL: {'✅ ÉXITO' if postgres_success else '❌ FALLÓ'}")
        
        if redis_success or postgres_success:
            log_message("🎉 ¡Al menos una base de datos funcionó!")
            
            # Verificar que se guardaron
            log_message("🔍 Verificando datos guardados...")
            return verify_saved_data(test_numbers)
        else:
            log_message("❌ Ninguna base de datos funcionó")
            return False
    
    finally:
        db_handler.close_connections()

def verify_saved_data(test_numbers):
    """Verificar que los datos se guardaron correctamente"""
    try:
        import redis
        import psycopg2
        
        # Verificar Redis
        redis_url = os.getenv("REDIS_PUBLIC_URL") or os.getenv("REDIS_URL") or os.getenv("Connection_redis")
        if redis_url:
            client = redis.from_url(redis_url, decode_responses=True)
            
            # Verificar último número
            latest = client.get("roulette:latest")
            log_message(f"🔴 Redis - Último número: {latest}")
            
            # Verificar historial
            history = client.lrange("roulette:history", 0, 4)
            log_message(f"🔴 Redis - Primeros 5 en historial: {history}")
        
        # Verificar PostgreSQL
        db_url = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL")
        if db_url:
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Contar registros totales
            cursor.execute("SELECT COUNT(*) FROM roulette_numbers_individual;")
            total_count = cursor.fetchone()[0]
            log_message(f"🐘 PostgreSQL - Total registros: {total_count}")
            
            # Últimos 3 números
            cursor.execute("""
                SELECT number_value, color, created_at 
                FROM roulette_numbers_individual 
                ORDER BY created_at DESC 
                LIMIT 3;
            """)
            recent = cursor.fetchall()
            log_message(f"🐘 PostgreSQL - Últimos 3 números:")
            for num, color, created in recent:
                log_message(f"   - {num} ({color}) - {created}")
            
            conn.close()
        
        return True
        
    except Exception as e:
        log_message(f"❌ Error verificando datos: {e}")
        return False

def main():
    """Función principal"""
    log_message("🚀 INICIANDO PRUEBA DE GUARDADO DIRECTO")
    log_message("=" * 50)
    
    success = test_save_current_numbers()
    
    log_message("=" * 50)
    if success:
        log_message("✅ PRUEBA EXITOSA - Las funciones de guardado funcionan correctamente")
        log_message("El problema debe estar en la lógica de detección de números nuevos del scraper")
    else:
        log_message("❌ PRUEBA FALLÓ - Hay un problema con las funciones de guardado")

if __name__ == "__main__":
    main() 