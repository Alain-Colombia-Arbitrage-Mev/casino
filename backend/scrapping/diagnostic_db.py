#!/usr/bin/env python3
"""
Diagnóstico de conexiones a Redis y PostgreSQL
"""

import os
import redis
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_redis_connection():
    """Probar conexión a Redis"""
    print("🔴 === DIAGNÓSTICO REDIS ===")
    
    # Mostrar variables de entorno
    redis_public_url = os.getenv("REDIS_PUBLIC_URL")
    redis_url = os.getenv("REDIS_URL")
    connection_redis = os.getenv("Connection_redis")
    
    print(f"REDIS_PUBLIC_URL: {redis_public_url[:50] + '...' if redis_public_url else 'No definida'}")
    print(f"REDIS_URL: {redis_url[:50] + '...' if redis_url else 'No definida'}")
    print(f"Connection_redis: {connection_redis[:50] + '...' if connection_redis else 'No definida'}")
    
    # Determinar URL a usar
    final_redis_url = redis_public_url or redis_url or connection_redis
    
    if not final_redis_url:
        print("❌ No hay URL de Redis configurada")
        return False
    
    print(f"\n🔗 Intentando conectar con: {final_redis_url[:50]}...")
    
    try:
        # Conectar a Redis
        client = redis.from_url(
            final_redis_url,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10
        )
        
        # Test de conexión
        client.ping()
        print("✅ Conexión a Redis exitosa")
        
        # Probar operaciones básicas
        test_key = "test_roulette_connection"
        client.set(test_key, "test_value", ex=60)
        value = client.get(test_key)
        
        if value == "test_value":
            print("✅ Operaciones Redis funcionando correctamente")
            
            # Limpiar
            client.delete(test_key)
            
            # Mostrar claves existentes con prefijo roulette
            keys = client.keys("roulette:*")
            if keys:
                print(f"\n📊 Claves existentes con prefijo 'roulette:': {len(keys)}")
                for key in keys[:10]:  # Mostrar máximo 10
                    print(f"   - {key}")
                if len(keys) > 10:
                    print(f"   ... y {len(keys) - 10} más")
            else:
                print("\n📊 No se encontraron claves con prefijo 'roulette:'")
            
            return True
        else:
            print("❌ Error en operaciones Redis")
            return False
            
    except redis.RedisError as e:
        print(f"❌ Error de Redis: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_postgres_connection():
    """Probar conexión a PostgreSQL"""
    print("\n🐘 === DIAGNÓSTICO POSTGRESQL ===")
    
    # Mostrar variables de entorno
    database_public_url = os.getenv("DATABASE_PUBLIC_URL")
    database_url = os.getenv("DATABASE_URL")
    
    print(f"DATABASE_PUBLIC_URL: {database_public_url[:50] + '...' if database_public_url else 'No definida'}")
    print(f"DATABASE_URL: {database_url[:50] + '...' if database_url else 'No definida'}")
    
    # Determinar URL a usar
    final_db_url = database_public_url or database_url
    
    if not final_db_url:
        print("❌ No hay URL de PostgreSQL configurada")
        return False
    
    print(f"\n🔗 Intentando conectar con: {final_db_url[:50]}...")
    
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(final_db_url)
        cursor = conn.cursor()
        
        # Test de conexión
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Conexión a PostgreSQL exitosa")
        print(f"📄 Versión: {version}")
        
        # Verificar si existen las tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%roulette%'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\n📊 Tablas de roulette encontradas: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
            
            # Contar registros en cada tabla
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
                count = cursor.fetchone()[0]
                print(f"     Registros: {count}")
            except Exception as e:
                print(f"     Error contando: {e}")
        
        # Test de inserción
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id SERIAL PRIMARY KEY,
                test_data TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        cursor.execute("""
            INSERT INTO test_connection (test_data) VALUES ('test_value') RETURNING id;
        """)
        
        test_id = cursor.fetchone()[0]
        print(f"✅ Test de inserción exitoso (ID: {test_id})")
        
        # Limpiar test
        cursor.execute("DROP TABLE IF EXISTS test_connection;")
        
        conn.commit()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 DIAGNÓSTICO DE CONEXIONES DE BASE DE DATOS")
    print("=" * 50)
    
    # Test Redis
    redis_ok = test_redis_connection()
    
    # Test PostgreSQL
    postgres_ok = test_postgres_connection()
    
    # Resumen
    print("\n" + "=" * 50)
    print("📋 RESUMEN:")
    print(f"Redis: {'✅ OK' if redis_ok else '❌ FALLA'}")
    print(f"PostgreSQL: {'✅ OK' if postgres_ok else '❌ FALLA'}")
    
    if redis_ok and postgres_ok:
        print("\n🎉 Todas las conexiones funcionan correctamente!")
        print("Si el scraper no está guardando datos, revisa los logs para otros errores.")
    else:
        print("\n⚠️ Hay problemas de conexión. Revisa las variables de entorno.")
        print("\nVariables necesarias:")
        print("- REDIS_PUBLIC_URL o REDIS_URL")
        print("- DATABASE_PUBLIC_URL o DATABASE_URL")

if __name__ == "__main__":
    main() 