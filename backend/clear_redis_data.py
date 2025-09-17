#!/usr/bin/env python3
"""
Script para limpiar todos los datos de Redis y inicializar con estructura nueva
"""

import redis
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_and_initialize_redis():
    """Limpiar Redis y configurar estructura inicial"""

    # Conectar a Redis
    redis_url = (
        os.getenv('REDIS_PUBLIC_URL') or
        os.getenv('Connection_redis') or
        os.getenv('REDIS_URL') or
        'redis://default:kuBKgwJxPrMoMOWqpobsGZIcpgnOFwoW@ballast.proxy.rlwy.net:58381'
    )

    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        logger.info("✅ Conectado a Redis exitosamente")
    except Exception as e:
        logger.error(f"❌ Error conectando a Redis: {e}")
        return False

    # Limpiar todos los datos
    try:
        logger.info("🧹 Limpiando todos los datos de Redis...")
        client.flushall()
        logger.info("✅ Redis limpiado completamente")
    except Exception as e:
        logger.error(f"❌ Error limpiando Redis: {e}")
        return False

    # Inicializar estructura básica
    try:
        logger.info("🔧 Inicializando estructura básica...")

        # Inicializar contadores
        client.set('roulette:total_spins', 0)
        client.set('roulette:colors:red', 0)
        client.set('roulette:colors:black', 0)
        client.set('roulette:colors:green', 0)

        # Inicializar estadísticas de IA
        client.set('ai:total_predictions', 0)
        client.set('ai:total_wins', 0)
        client.set('ai:total_losses', 0)

        # Hash de configuración del sistema
        client.hset('system:config', mapping={
            'version': '2.0.0',
            'storage_type': 'redis_only',
            'max_history_size': '200',
            'initialized_at': '2024-12-15T12:00:00Z'
        })

        # Hash de estadísticas del sistema
        client.hset('system:stats', mapping={
            'last_update': '2024-12-15T12:00:00Z',
            'status': 'initialized',
            'data_source': 'redis_only'
        })

        logger.info("✅ Estructura básica inicializada")

        # Insertar algunos números de ejemplo para testing
        logger.info("📝 Insertando números de ejemplo...")
        example_numbers = [15, 22, 8, 0, 31, 17, 25, 10, 4, 36]

        for i, number in enumerate(example_numbers):
            # Agregar a historial
            client.lpush('roulette:history', str(number))

            # Actualizar último número
            client.set('roulette:latest', str(number))

            # Actualizar contadores de color
            if number == 0:
                client.incr('roulette:colors:green')
            elif number in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]:
                client.incr('roulette:colors:red')
            else:
                client.incr('roulette:colors:black')

            # Actualizar total spins
            client.incr('roulette:total_spins')

        # Mantener solo los últimos 200 números
        client.ltrim('roulette:history', 0, 199)

        logger.info(f"✅ Insertados {len(example_numbers)} números de ejemplo")

        # Verificar estructura
        history_length = client.llen('roulette:history')
        latest_number = client.get('roulette:latest')
        total_spins = client.get('roulette:total_spins')

        logger.info(f"📊 Estado final:")
        logger.info(f"   - Números en historial: {history_length}")
        logger.info(f"   - Último número: {latest_number}")
        logger.info(f"   - Total spins: {total_spins}")
        logger.info(f"   - Rojos: {client.get('roulette:colors:red')}")
        logger.info(f"   - Negros: {client.get('roulette:colors:black')}")
        logger.info(f"   - Verdes: {client.get('roulette:colors:green')}")

        return True

    except Exception as e:
        logger.error(f"❌ Error inicializando estructura: {e}")
        return False

if __name__ == '__main__':
    logger.info("🚀 Iniciando limpieza e inicialización de Redis...")
    success = clear_and_initialize_redis()

    if success:
        logger.info("🎉 Redis limpiado e inicializado exitosamente")
        logger.info("💡 El sistema ahora usa Redis únicamente para almacenamiento")
    else:
        logger.error("💥 Error en el proceso de inicialización")