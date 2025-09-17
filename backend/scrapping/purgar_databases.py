#!/usr/bin/env python3
"""
PURGAR AMBAS BASES DE DATOS - EMPEZAR DESDE CERO
Limpia Redis y PostgreSQL completamente
"""

import redis
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def log_message(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)

def purge_redis():
    """Limpiar Redis completamente"""
    redis_url = os.getenv("REDIS_PUBLIC_URL") or os.getenv("REDIS_URL") or os.getenv("Connection_redis")
    if not redis_url:
        log_message("❌ No hay URL de Redis configurada", "ERROR")
        return False
    
    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        
        # Obtener todas las claves relacionadas con roulette
        roulette_keys = client.keys("roulette:*")
        
        if roulette_keys:
            log_message(f"🔍 Encontradas {len(roulette_keys)} claves de roulette en Redis:")
            for key in roulette_keys:
                log_message(f"   - {key}")
            
            # Eliminar todas las claves de roulette
            deleted = client.delete(*roulette_keys)
            log_message(f"🗑️ Eliminadas {deleted} claves de Redis")
        else:
            log_message("📭 No se encontraron claves de roulette en Redis")
        
        # Verificar que estén eliminadas
        remaining = client.keys("roulette:*")
        if not remaining:
            log_message("✅ Redis limpio - Sin claves de roulette")
            return True
        else:
            log_message(f"⚠️ Quedan {len(remaining)} claves en Redis", "WARNING")
            return False
            
    except Exception as e:
        log_message(f"❌ Error limpiando Redis: {e}", "ERROR")
        return False

def purge_postgresql():
    """Limpiar PostgreSQL completamente"""
    db_url = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        log_message("❌ No hay URL de PostgreSQL configurada", "ERROR")
        return False
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Listar todas las tablas relacionadas con roulette
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%roulette%';
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        if tables:
            log_message(f"🔍 Encontradas {len(tables)} tablas de roulette en PostgreSQL:")
            for table in tables:
                log_message(f"   - {table}")
            
            # Eliminar cada tabla
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                log_message(f"🗑️ Tabla {table} eliminada")
                
        else:
            log_message("📭 No se encontraron tablas de roulette en PostgreSQL")
        
        # Verificar que estén eliminadas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%roulette%';
        """)
        
        remaining = cursor.fetchall()
        if not remaining:
            log_message("✅ PostgreSQL limpio - Sin tablas de roulette")
            return True
        else:
            log_message(f"⚠️ Quedan {len(remaining)} tablas en PostgreSQL", "WARNING")
            return False
            
        conn.close()
        
    except Exception as e:
        log_message(f"❌ Error limpiando PostgreSQL: {e}", "ERROR")
        return False

def create_fresh_schema():
    """Crear esquema fresco en PostgreSQL"""
    db_url = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        return False
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Crear tabla nueva y limpia
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roulette_numbers (
                id BIGSERIAL PRIMARY KEY,
                number_value INTEGER NOT NULL CHECK (number_value >= 0 AND number_value <= 36),
                color TEXT NOT NULL CHECK (color IN ('red', 'black', 'green')),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                session_info JSONB
            );
        """)
        
        # Índices optimizados
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_roulette_numbers_timestamp ON roulette_numbers(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_roulette_numbers_value ON roulette_numbers(number_value);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_roulette_numbers_color ON roulette_numbers(color);")
        
        log_message("✅ Esquema fresco creado en PostgreSQL")
        conn.close()
        return True
        
    except Exception as e:
        log_message(f"❌ Error creando esquema fresco: {e}", "ERROR")
        return False

def verify_clean_state():
    """Verificar que ambas bases estén completamente limpias"""
    log_message("🔍 VERIFICANDO ESTADO LIMPIO...")
    
    # Verificar Redis
    redis_url = os.getenv("REDIS_PUBLIC_URL") or os.getenv("REDIS_URL") or os.getenv("Connection_redis")
    redis_clean = False
    if redis_url:
        try:
            client = redis.from_url(redis_url, decode_responses=True)
            keys = client.keys("roulette:*")
            redis_clean = len(keys) == 0
            log_message(f"   Redis: {'✅ Limpio' if redis_clean else '❌ Tiene datos'}")
        except:
            log_message("   Redis: ❌ Error verificando")
    
    # Verificar PostgreSQL
    db_url = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL")
    postgres_clean = False
    if db_url:
        try:
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM roulette_numbers;")
            count = cursor.fetchone()[0]
            postgres_clean = count == 0
            log_message(f"   PostgreSQL: {'✅ Limpio (0 registros)' if postgres_clean else f'❌ Tiene {count} registros'}")
            conn.close()
        except:
            log_message("   PostgreSQL: ✅ Tabla no existe (limpio)")
            postgres_clean = True
    
    return redis_clean, postgres_clean

def main():
    """Función principal de purga"""
    log_message("🧹 PURGANDO AMBAS BASES DE DATOS")
    log_message("⚠️  ESTO ELIMINARÁ TODOS LOS DATOS DE ROULETTE")
    log_message("=" * 60)
    
    # Estado inicial
    log_message("📊 Estado inicial:")
    verify_clean_state()
    
    # Purgar Redis
    log_message("\n🗑️ LIMPIANDO REDIS...")
    redis_success = purge_redis()
    
    # Purgar PostgreSQL
    log_message("\n🗑️ LIMPIANDO POSTGRESQL...")
    postgres_success = purge_postgresql()
    
    # Crear esquema fresco
    log_message("\n🆕 CREANDO ESQUEMA FRESCO...")
    schema_success = create_fresh_schema()
    
    # Verificar estado final
    log_message("\n📊 Estado final:")
    redis_clean, postgres_clean = verify_clean_state()
    
    # Resultado
    log_message("\n" + "=" * 60)
    if redis_clean and postgres_clean:
        log_message("🎉 ¡BASES DE DATOS COMPLETAMENTE LIMPIAS!")
        log_message("✅ Redis: Sin claves de roulette")
        log_message("✅ PostgreSQL: Tabla fresca y vacía")
        log_message("\n🚀 Ahora puedes ejecutar: python scraper_final.py")
    else:
        log_message("⚠️ PURGA PARCIAL:")
        log_message(f"   Redis: {'✅' if redis_clean else '❌'}")
        log_message(f"   PostgreSQL: {'✅' if postgres_clean else '❌'}")
    
    log_message("=" * 60)

if __name__ == "__main__":
    # Confirmación de seguridad
    print("⚠️  ADVERTENCIA: Esto eliminará TODOS los datos de roulette")
    print("   en Redis y PostgreSQL permanentemente.")
    print("\n¿Estás seguro? (escribe 'SI' para confirmar)")
    
    confirmacion = input().strip().upper()
    if confirmacion == "SI":
        main()
    else:
        print("❌ Operación cancelada") 