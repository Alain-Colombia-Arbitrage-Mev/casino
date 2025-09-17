#!/usr/bin/env python3
"""
Script para limpiar predicciones con valores booleanos en Redis
"""

import redis
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def clear_redis_predictions():
    """Limpiar todas las predicciones y resultados de Redis"""
    try:
        # Conectar a Redis
        redis_url = os.getenv('REDIS_PUBLIC_URL', os.getenv('Connection_redis', 'redis://localhost:6379'))
        redis_client = redis.from_url(redis_url, decode_responses=True)
        
        print("🧹 Limpiando predicciones y resultados de Redis...")
        
        # Obtener todas las claves de predicciones
        prediction_keys = redis_client.keys('prediction:*')
        result_keys = redis_client.keys('result:*')
        
        # Eliminar predicciones
        if prediction_keys:
            for key in prediction_keys:
                redis_client.delete(key)
            print(f"✅ Eliminadas {len(prediction_keys)} predicciones")
        
        # Eliminar resultados
        if result_keys:
            for key in result_keys:
                redis_client.delete(key)
            print(f"✅ Eliminados {len(result_keys)} resultados")
        
        # Limpiar listas
        redis_client.delete('predictions:pending')
        redis_client.delete('game:results')
        
        # Limpiar estadísticas de IA
        stats_keys = redis_client.keys('stats:*')
        if stats_keys:
            for key in stats_keys:
                redis_client.delete(key)
            print(f"✅ Eliminadas {len(stats_keys)} estadísticas de IA")
        
        print("🎉 Limpieza completada. Redis está listo para nuevas predicciones.")
        
    except Exception as e:
        print(f"❌ Error limpiando Redis: {e}")

if __name__ == '__main__':
    clear_redis_predictions()