#!/usr/bin/env python3
"""
Script de diagnóstico para Railway
Identifica problemas de conexión y configuración
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def log_message(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)

def test_redis_connection():
    """Probar conexión a Redis con diferentes métodos"""
    log_message("🔍 === DIAGNÓSTICO REDIS ===")
    
    # Recopilar todas las variables Redis
    redis_vars = {
        'REDIS_URL': os.getenv("REDIS_URL"),
        'REDIS_PUBLIC_URL': os.getenv("REDIS_PUBLIC_URL"),
        'Connection_redis': os.getenv("Connection_redis"),
        'REDIS_PASSWORD': os.getenv("REDIS_PASSWORD"),
        'REDISPASSWORD': os.getenv("REDISPASSWORD"),
        'REDIS_PORT': os.getenv("REDIS_PORT", "6379"),
        'REDISUSER': os.getenv("REDISUSER"),
        'PGHOST': os.getenv("PGHOST")  # Para construir URL alternativa
    }
    
    # Mostrar variables disponibles
    log_message("📋 Variables Redis encontradas:")
    for name, value in redis_vars.items():
        if value:
            display_value = value if 'PASSWORD' not in name else '***'
            log_message(f"   ✅ {name}: {display_value}")
        else:
            log_message(f"   ❌ {name}: NO ENCONTRADA")
    
    # Intentar importar redis
    try:
        import redis
        log_message("✅ Módulo redis importado correctamente")
    except ImportError as e:
        log_message(f"❌ Error importando redis: {e}", "ERROR")
        log_message("💡 Instala redis con: pip install redis", "INFO")
        return False
    
    # URLs a probar
    urls_to_test = []
    
    # URL principal
    if redis_vars['REDIS_URL']:
        urls_to_test.append(('REDIS_URL', redis_vars['REDIS_URL']))
    
    # URL pública
    if redis_vars['REDIS_PUBLIC_URL']:
        urls_to_test.append(('REDIS_PUBLIC_URL', redis_vars['REDIS_PUBLIC_URL']))
    
    # Connection_redis
    if redis_vars['Connection_redis']:
        urls_to_test.append(('Connection_redis', redis_vars['Connection_redis']))
    
    # Construir URL desde componentes
    if redis_vars['PGHOST']:
        password = redis_vars['REDIS_PASSWORD'] or redis_vars['REDISPASSWORD']
        user = redis_vars['REDISUSER']
        port = redis_vars['REDIS_PORT']
        
        if password and user:
            constructed_url = f"redis://{user}:{password}@{redis_vars['PGHOST']}:{port}"
        elif password:
            constructed_url = f"redis://:{password}@{redis_vars['PGHOST']}:{port}"
        else:
            constructed_url = f"redis://{redis_vars['PGHOST']}:{port}"
        
        urls_to_test.append(('CONSTRUCTED', constructed_url))
    
    if not urls_to_test:
        log_message("❌ No hay URLs de Redis para probar", "ERROR")
        return False
    
    # Probar cada URL
    log_message("🔗 Probando conexiones Redis...")
    
    for name, url in urls_to_test:
        log_message(f"🔍 Probando {name}: {url[:50]}...")
        
        try:
            # Crear cliente con timeouts cortos para diagnóstico rápido
            client = redis.from_url(
                url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Probar conexión
            result = client.ping()
            if result:
                log_message(f"✅ {name}: CONEXIÓN EXITOSA")
                
                # Probar operaciones básicas
                try:
                    client.set("test_key", "test_value", ex=10)
                    value = client.get("test_key")
                    if value == "test_value":
                        log_message(f"✅ {name}: OPERACIONES READ/WRITE OK")
                        client.delete("test_key")
                        return True
                    else:
                        log_message(f"⚠️ {name}: Problema con operaciones READ/WRITE", "WARN")
                except Exception as op_e:
                    log_message(f"⚠️ {name}: Error en operaciones: {op_e}", "WARN")
            else:
                log_message(f"❌ {name}: PING falló")
                
        except redis.ConnectionError as e:
            log_message(f"❌ {name}: Error de conexión - {e}")
        except redis.TimeoutError as e:
            log_message(f"❌ {name}: Timeout - {e}")
        except Exception as e:
            log_message(f"❌ {name}: Error inesperado - {e}")
    
    return False

def test_postgres_connection():
    """Probar conexión a PostgreSQL"""
    log_message("🔍 === DIAGNÓSTICO POSTGRESQL ===")
    
    # Recopilar variables PostgreSQL
    postgres_vars = {
        'DATABASE_URL': os.getenv("DATABASE_URL"),
        'DATABASE_PUBLIC_URL': os.getenv("DATABASE_PUBLIC_URL"),
        'PGHOST': os.getenv("PGHOST"),
        'PGPORT': os.getenv("PGPORT", "5432"),
        'PGUSER': os.getenv("PGUSER"),
        'POSTGRES_USER': os.getenv("POSTGRES_USER"),
        'POSTGRES_DB': os.getenv("POSTGRES_DB"),
        'POSTGRES_PASSWORD': os.getenv("POSTGRES_PASSWORD")
    }
    
    # Mostrar variables disponibles
    log_message("📋 Variables PostgreSQL encontradas:")
    for name, value in postgres_vars.items():
        if value:
            display_value = value if 'PASSWORD' not in name else '***'
            if 'URL' in name and len(display_value) > 50:
                display_value = display_value[:50] + '...'
            log_message(f"   ✅ {name}: {display_value}")
        else:
            log_message(f"   ❌ {name}: NO ENCONTRADA")
    
    # Intentar importar psycopg2
    try:
        import psycopg2
        log_message("✅ Módulo psycopg2 importado correctamente")
    except ImportError as e:
        log_message(f"❌ Error importando psycopg2: {e}", "ERROR")
        log_message("💡 Instala psycopg2 con: pip install psycopg2-binary", "INFO")
        return False
    
    # URLs a probar
    urls_to_test = []
    
    if postgres_vars['DATABASE_URL']:
        urls_to_test.append(('DATABASE_URL', postgres_vars['DATABASE_URL']))
    
    if postgres_vars['DATABASE_PUBLIC_URL']:
        urls_to_test.append(('DATABASE_PUBLIC_URL', postgres_vars['DATABASE_PUBLIC_URL']))
    
    # Construir URL desde componentes
    if all([postgres_vars['PGHOST'], postgres_vars['PGUSER'], postgres_vars['POSTGRES_PASSWORD'], postgres_vars['POSTGRES_DB']]):
        constructed_url = f"postgresql://{postgres_vars['PGUSER']}:{postgres_vars['POSTGRES_PASSWORD']}@{postgres_vars['PGHOST']}:{postgres_vars['PGPORT']}/{postgres_vars['POSTGRES_DB']}"
        urls_to_test.append(('CONSTRUCTED', constructed_url))
    
    if not urls_to_test:
        log_message("❌ No hay URLs de PostgreSQL para probar", "ERROR")
        return False
    
    # Probar cada URL
    log_message("🔗 Probando conexiones PostgreSQL...")
    
    for name, url in urls_to_test:
        log_message(f"🔍 Probando {name}: {url[:50]}...")
        
        try:
            # Crear conexión con timeout
            conn = psycopg2.connect(url, connect_timeout=10)
            cursor = conn.cursor()
            
            # Probar consulta básica
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            log_message(f"✅ {name}: CONEXIÓN EXITOSA")
            log_message(f"   PostgreSQL version: {version[:50]}...")
            
            # Probar creación de tabla temporal
            try:
                cursor.execute("CREATE TEMP TABLE test_table (id INTEGER);")
                cursor.execute("INSERT INTO test_table VALUES (1);")
                cursor.execute("SELECT * FROM test_table;")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    log_message(f"✅ {name}: OPERACIONES DDL/DML OK")
                    conn.commit()
                    cursor.close()
                    conn.close()
                    return True
            except Exception as op_e:
                log_message(f"⚠️ {name}: Error en operaciones: {op_e}", "WARN")
            
            cursor.close()
            conn.close()
            
        except psycopg2.OperationalError as e:
            log_message(f"❌ {name}: Error operacional - {e}")
        except Exception as e:
            log_message(f"❌ {name}: Error inesperado - {e}")
    
    return False

def check_network_connectivity():
    """Verificar conectividad de red básica"""
    log_message("🔍 === DIAGNÓSTICO DE RED ===")
    
    import socket
    
    # Probar resolución DNS
    hosts_to_test = [
        "google.com",
        "railway.app",
        "redis.railway.internal" if os.getenv("PGHOST") == "redis.railway.internal" else None
    ]
    
    for host in hosts_to_test:
        if host:
            try:
                ip = socket.gethostbyname(host)
                log_message(f"✅ DNS {host}: {ip}")
            except socket.gaierror as e:
                log_message(f"❌ DNS {host}: {e}")

def main():
    """Función principal de diagnóstico"""
    log_message("🚀 === DIAGNÓSTICO RAILWAY INICIADO ===")
    
    # Información del sistema
    log_message(f"🐍 Python version: {sys.version}")
    log_message(f"💻 Platform: {sys.platform}")
    
    # Variables de entorno Railway
    railway_vars = ['RAILWAY_RUN_AS_ROOT', 'RAILWAY_RUN_UID']
    log_message("🚂 Variables Railway del sistema:")
    for var in railway_vars:
        value = os.getenv(var)
        if value:
            log_message(f"   ✅ {var}: {value}")
        else:
            log_message(f"   ❌ {var}: NO ENCONTRADA")
    
    # Verificar conectividad de red
    check_network_connectivity()
    
    # Probar Redis
    redis_ok = test_redis_connection()
    
    # Probar PostgreSQL
    postgres_ok = test_postgres_connection()
    
    # Resumen final
    log_message("📊 === RESUMEN FINAL ===")
    log_message(f"Redis: {'✅ OK' if redis_ok else '❌ FALLO'}")
    log_message(f"PostgreSQL: {'✅ OK' if postgres_ok else '❌ FALLO'}")
    
    if redis_ok or postgres_ok:
        log_message("✅ Al menos una base de datos está funcionando")
        log_message("💡 El scraper puede ejecutarse con funcionalidad limitada")
    else:
        log_message("❌ Ninguna base de datos está funcionando", "ERROR")
        log_message("💡 Revisa la configuración de los plugins en Railway", "ERROR")
    
    log_message("🏁 Diagnóstico completado")

if __name__ == "__main__":
    main() 