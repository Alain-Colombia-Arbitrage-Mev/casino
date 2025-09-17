#!/usr/bin/env python3
"""
Sincronización de bases de datos Redis y PostgreSQL con estructuras compatibles
"""

import redis
import psycopg2
import psycopg2.extras
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def log_message(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    try:
        print(log_entry)
    except UnicodeEncodeError:
        # Remove emojis and special characters
        safe_message = message.encode('ascii', 'ignore').decode('ascii')
        safe_entry = f"[{timestamp}] [{level}] {safe_message}"
        print(safe_entry)

def get_number_color(number):
    """Determine the color of a roulette number"""
    number = int(number)
    if number == 0:
        return "green"
    elif number in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]:
        return "red"
    else:
        return "black"

def validate_roulette_number(number):
    """Validate that a number is a valid roulette number (0-36)"""
    try:
        num_int = int(number)
        return 0 <= num_int <= 36
    except (ValueError, TypeError):
        return False

class SyncedRouletteDatabase:
    """Clase mejorada para mantener Redis y PostgreSQL sincronizados"""

    def __init__(self):
        self.redis_client = None
        self.postgres_conn = None
        self.connect_databases()

    def connect_databases(self):
        """Conectar a ambas bases de datos"""
        # Redis
        redis_url = os.getenv("REDIS_PUBLIC_URL") or os.getenv("REDIS_URL") or os.getenv("Connection_redis")
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                log_message("✅ Conectado a Redis")
            except Exception as e:
                log_message(f"❌ Error Redis: {e}", "ERROR")
                self.redis_client = None

        # PostgreSQL
        db_url = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL")
        if db_url:
            try:
                self.postgres_conn = psycopg2.connect(db_url)
                self.postgres_conn.autocommit = True  # Auto-commit para evitar problemas
                log_message("✅ Conectado a PostgreSQL")
                self.ensure_postgres_schema()
            except Exception as e:
                log_message(f"❌ Error PostgreSQL: {e}", "ERROR")
                self.postgres_conn = None

    def ensure_postgres_schema(self):
        """Asegurar que el esquema de PostgreSQL sea correcto"""
        if not self.postgres_conn:
            return

        try:
            cursor = self.postgres_conn.cursor()

            # Tabla principal de números con estructura simple
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS roulette_numbers (
                    id BIGSERIAL PRIMARY KEY,
                    number_value INTEGER NOT NULL CHECK (number_value >= 0 AND number_value <= 36),
                    color TEXT NOT NULL CHECK (color IN ('red', 'black', 'green')),
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    session_info JSONB
                );
            """)

            # Índices para optimizar consultas
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_roulette_numbers_timestamp ON roulette_numbers(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_roulette_numbers_value ON roulette_numbers(number_value);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_roulette_numbers_color ON roulette_numbers(color);")

            log_message("✅ Esquema PostgreSQL verificado")

        except Exception as e:
            log_message(f"❌ Error creando esquema: {e}", "ERROR")

    def save_to_redis(self, numbers):
        """Guardar en Redis con estructura optimizada y validación 0-36"""
        if not self.redis_client or not numbers:
            return False

        try:
            # Validar números antes de guardar
            valid_numbers = []
            for number in numbers:
                if validate_roulette_number(number):
                    valid_numbers.append(int(number))
                else:
                    log_message(f"⚠️ Número inválido ignorado en Redis: {number} (debe ser 0-36)", "WARN")

            if not valid_numbers:
                log_message("❌ No hay números válidos para guardar en Redis")
                return False

            pipe = self.redis_client.pipeline()

            # Datos básicos
            latest_number = valid_numbers[0]
            pipe.set("roulette:latest", latest_number)

            # Historial LIFO - usar solo números válidos
            pipe.lpush("roulette:history", *valid_numbers)
            pipe.ltrim("roulette:history", 0, 99)  # Mantener últimos 100

            # Contadores por color
            for number in valid_numbers:
                color = get_number_color(number)
                pipe.incr(f"roulette:colors:{color}")

            # Total de spins
            pipe.incr("roulette:total_spins", len(valid_numbers))

            # Metadata
            metadata = {
                'last_update': datetime.now().isoformat(),
                'latest_number': latest_number,
                'latest_color': get_number_color(latest_number),
                'numbers_processed': len(valid_numbers)
            }
            pipe.hset("roulette:stats", mapping=metadata)

            # Ejecutar todas las operaciones
            pipe.execute()

            log_message(f"✅ Redis: Guardados {len(valid_numbers)} números válidos (0-36)")
            return True

        except Exception as e:
            log_message(f"❌ Error Redis save: {e}", "ERROR")
            return False

    def save_to_postgres(self, numbers):
        """Guardar en PostgreSQL con estructura simplificada y validación 0-36"""
        if not self.postgres_conn or not numbers:
            return False

        try:
            # Validar números antes de guardar
            valid_numbers = []
            for number in numbers:
                if validate_roulette_number(number):
                    valid_numbers.append(int(number))
                else:
                    log_message(f"⚠️ Número inválido ignorado en PostgreSQL: {number} (debe ser 0-36)", "WARN")

            if not valid_numbers:
                log_message("❌ No hay números válidos para guardar en PostgreSQL")
                return False

            cursor = self.postgres_conn.cursor()

            # Información de sesión
            session_info = {
                'timestamp': datetime.now().isoformat(),
                'batch_size': len(valid_numbers),
                'source': 'roulette_scraper'
            }

            # Insertar cada número individualmente
            for number in valid_numbers:
                number_int = int(number)
                color = get_number_color(number)

                cursor.execute("""
                    INSERT INTO roulette_numbers (number_value, color, session_info)
                    VALUES (%s, %s, %s);
                """, (number_int, color, json.dumps(session_info)))

            log_message(f"✅ PostgreSQL: Guardados {len(valid_numbers)} números válidos (0-36)")
            return True

        except Exception as e:
            log_message(f"❌ Error PostgreSQL save: {e}", "ERROR")
            return False

    def save_numbers(self, numbers):
        """Guardar números en ambas bases de datos de forma sincronizada con validación estricta"""
        if not numbers:
            log_message("⚠️ No hay números para guardar")
            return False, False

        log_message(f"💾 Guardando {len(numbers)} números: {numbers}")

        # Validar números antes de guardar - ESTRICTA VALIDACIÓN 0-36
        valid_numbers = []
        for num in numbers:
            if validate_roulette_number(num):
                valid_numbers.append(int(num))
            else:
                log_message(f"⚠️ Número inválido rechazado: {num} (solo se permiten números 0-36)", "WARN")

        if not valid_numbers:
            log_message("❌ No hay números válidos (0-36) para guardar")
            return False, False

        log_message(f"✅ Números validados (0-36): {valid_numbers}")

        # Guardar en ambas bases con transacción
        redis_success = False
        postgres_success = False

        try:
            # Intentar guardar en ambas bases
            redis_success = self.save_to_redis(valid_numbers)
            postgres_success = self.save_to_postgres(valid_numbers)

            # Si una falla, intentar rollback de la otra (para Redis es más complejo)
            if redis_success and not postgres_success:
                log_message("⚠️ PostgreSQL falló, pero Redis ya guardó. Datos inconsistentes.", "WARN")
            elif postgres_success and not redis_success:
                log_message("⚠️ Redis falló, pero PostgreSQL ya guardó. Datos inconsistentes.", "WARN")

        except Exception as e:
            log_message(f"❌ Error crítico en sincronización: {e}", "ERROR")

        # Resultado
        if redis_success and postgres_success:
            log_message("🎉 ¡Guardado exitoso en AMBAS bases de datos!")
        elif redis_success:
            log_message("⚠️ Guardado solo en Redis")
        elif postgres_success:
            log_message("⚠️ Guardado solo en PostgreSQL")
        else:
            log_message("❌ Error guardando en ambas bases")

        return redis_success, postgres_success

    def get_sync_status(self):
        """Verificar el estado de sincronización entre las bases"""
        try:
            # Redis stats
            redis_latest = None
            redis_count = 0
            if self.redis_client:
                redis_latest = self.redis_client.get("roulette:latest")
                redis_count = int(self.redis_client.get("roulette:total_spins") or 0)

            # PostgreSQL stats
            postgres_latest = None
            postgres_count = 0
            if self.postgres_conn:
                cursor = self.postgres_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM roulette_numbers;")
                postgres_count = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT number_value
                    FROM roulette_numbers
                    ORDER BY timestamp DESC
                    LIMIT 1;
                """)
                result = cursor.fetchone()
                postgres_latest = result[0] if result else None

            # Comparar
            is_synced = (redis_latest == str(postgres_latest) if postgres_latest else False)

            log_message("📊 ESTADO DE SINCRONIZACIÓN:")
            log_message(f"   Redis - Último: {redis_latest}, Total: {redis_count}")
            log_message(f"   PostgreSQL - Último: {postgres_latest}, Total: {postgres_count}")
            log_message(f"   Sincronizado: {'✅' if is_synced else '❌'}")

            # Validar que todos los números están en rango 0-36
            if self.redis_client:
                history = self.redis_client.lrange("roulette:history", 0, 10)
                invalid_numbers = [n for n in history if not validate_roulette_number(n)]
                if invalid_numbers:
                    log_message(f"⚠️ Números inválidos encontrados en Redis: {invalid_numbers}")
                else:
                    log_message("✅ Todos los números en Redis son válidos (0-36)")

            return {
                'synced': is_synced,
                'redis': {'latest': redis_latest, 'count': redis_count},
                'postgres': {'latest': postgres_latest, 'count': postgres_count}
            }

        except Exception as e:
            log_message(f"❌ Error verificando sync: {e}", "ERROR")
            return None

    def purge_all_data(self):
        """Limpiar completamente todas las bases de datos"""
        log_message("🧹 INICIANDO LIMPIEZA COMPLETA DE BASES DE DATOS")
        log_message("=" * 60)

        redis_success = False
        postgres_success = False

        # Limpiar Redis
        if self.redis_client:
            try:
                # Obtener todas las claves relacionadas con roulette
                keys_to_delete = []
                for pattern in ["roulette:*", "roulette_*"]:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        keys_to_delete.extend(keys)

                if keys_to_delete:
                    deleted_count = self.redis_client.delete(*keys_to_delete)
                    log_message(f"🗑️ Redis: Eliminadas {deleted_count} claves")
                else:
                    log_message("🗑️ Redis: No hay datos para eliminar")

                # Verificar que se eliminó todo
                remaining_keys = self.redis_client.keys("roulette*")
                if not remaining_keys:
                    log_message("✅ Redis: Completamente limpio")
                    redis_success = True
                else:
                    log_message(f"⚠️ Redis: Quedan {len(remaining_keys)} claves")

            except Exception as e:
                log_message(f"❌ Error limpiando Redis: {e}", "ERROR")

        # Limpiar PostgreSQL
        if self.postgres_conn:
            try:
                cursor = self.postgres_conn.cursor()

                # Obtener conteo actual
                cursor.execute("SELECT COUNT(*) FROM roulette_numbers;")
                count_before = cursor.fetchone()[0]

                # Eliminar todos los registros
                cursor.execute("DELETE FROM roulette_numbers;")

                # Reiniciar secuencia de ID
                cursor.execute("ALTER SEQUENCE roulette_numbers_id_seq RESTART WITH 1;")

                # Verificar limpieza
                cursor.execute("SELECT COUNT(*) FROM roulette_numbers;")
                count_after = cursor.fetchone()[0]

                log_message(f"🗑️ PostgreSQL: Eliminados {count_before} registros")

                if count_after == 0:
                    log_message("✅ PostgreSQL: Completamente limpio")
                    postgres_success = True
                else:
                    log_message(f"⚠️ PostgreSQL: Quedan {count_after} registros")

            except Exception as e:
                log_message(f"❌ Error limpiando PostgreSQL: {e}", "ERROR")

        # Resultado final
        if redis_success and postgres_success:
            log_message("🎉 ¡LIMPIEZA COMPLETA EXITOSA EN AMBAS BASES!")
        elif redis_success:
            log_message("⚠️ Limpieza exitosa solo en Redis")
        elif postgres_success:
            log_message("⚠️ Limpieza exitosa solo en PostgreSQL")
        else:
            log_message("❌ Error en la limpieza de ambas bases")

        log_message("=" * 60)
        return redis_success, postgres_success

    def close_connections(self):
        """Cerrar conexiones"""
        if self.redis_client:
            self.redis_client.close()
        if self.postgres_conn:
            self.postgres_conn.close()

# Test de la clase
if __name__ == "__main__":
    log_message("🧪 PROBANDO SINCRONIZACIÓN DE BASES DE DATOS")
    log_message("=" * 50)

    db = SyncedRouletteDatabase()

    # Verificar estado inicial
    db.get_sync_status()

    # Probar guardado sincronizado con números válidos
    test_numbers = ["13", "27", "0", "36"]
    db.save_numbers(test_numbers)

    # Probar con números inválidos para verificar validación
    invalid_numbers = ["37", "-1", "abc", "100"]
    log_message("🧪 Probando números inválidos:")
    db.save_numbers(invalid_numbers)

    # Verificar estado final
    db.get_sync_status()

    db.close_connections()
    log_message("🔌 Test completado")