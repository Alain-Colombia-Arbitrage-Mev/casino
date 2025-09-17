#!/usr/bin/env python3
"""
Analizar estructura actual de Redis y proponer mejoras
"""

import redis
import json
import os
from datetime import datetime

# Configuración Redis
REDIS_URL = (
    os.getenv('REDIS_PUBLIC_URL') or
    os.getenv('Connection_redis') or
    os.getenv('REDIS_URL') or
    'redis://default:kuBKgwJxPrMoMOWqpobsGZIcpgnOFwoW@ballast.proxy.rlwy.net:58381'
)

def analyze_redis_structure():
    """Analizar estructura actual de Redis"""

    try:
        # Conectar a Redis
        client = redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()
        print("✅ Conectado a Redis exitosamente")
        print("=" * 60)

        # Obtener todas las claves
        all_keys = client.keys("*")
        print(f"📊 Total de claves en Redis: {len(all_keys)}")
        print()

        # Categorizar claves
        categories = {
            'roulette': [],
            'ai': [],
            'prediction': [],
            'scraper': [],
            'stats': [],
            'system': [],
            'other': []
        }

        for key in all_keys:
            if key.startswith('roulette:'):
                categories['roulette'].append(key)
            elif key.startswith('ai:'):
                categories['ai'].append(key)
            elif key.startswith('prediction:'):
                categories['prediction'].append(key)
            elif key.startswith('scraper:'):
                categories['scraper'].append(key)
            elif key.startswith('stats:'):
                categories['stats'].append(key)
            elif key.startswith('system:'):
                categories['system'].append(key)
            else:
                categories['other'].append(key)

        # Mostrar análisis por categoría
        for category, keys in categories.items():
            if keys:
                print(f"🔍 {category.upper()} ({len(keys)} claves):")
                for key in sorted(keys):
                    key_type = client.type(key)
                    size = get_key_size(client, key, key_type)
                    print(f"  • {key} ({key_type}) - {size}")
                print()

        print("=" * 60)
        print("📈 ANÁLISIS DETALLADO DE DATOS:")
        print("=" * 60)

        # Análisis específico de datos de ruleta
        analyze_roulette_data(client)

        # Análisis de predicciones
        analyze_predictions_data(client)

        # Análisis de rendimiento
        analyze_performance(client)

        # Propuestas de mejora
        print_improvement_suggestions()

    except Exception as e:
        print(f"❌ Error analizando Redis: {e}")

def get_key_size(client, key, key_type):
    """Obtener tamaño de la clave según su tipo"""
    try:
        if key_type == 'string':
            value = client.get(key)
            return f"{len(str(value))} chars"
        elif key_type == 'list':
            length = client.llen(key)
            return f"{length} items"
        elif key_type == 'hash':
            length = client.hlen(key)
            return f"{length} fields"
        elif key_type == 'set':
            length = client.scard(key)
            return f"{length} members"
        elif key_type == 'zset':
            length = client.zcard(key)
            return f"{length} members"
        else:
            return "unknown"
    except:
        return "error"

def analyze_roulette_data(client):
    """Análizar datos específicos de ruleta"""
    print("🎰 DATOS DE RULETA:")

    # Historial
    if client.exists('roulette:history'):
        history_length = client.llen('roulette:history')
        recent_numbers = client.lrange('roulette:history', 0, 9)
        print(f"  📜 Historial: {history_length} números")
        print(f"      Últimos 10: {recent_numbers}")

    # Estadísticas
    total_spins = client.get('roulette:total_spins') or 0
    latest_number = client.get('roulette:latest') or 'N/A'

    red_count = client.get('roulette:colors:red') or 0
    black_count = client.get('roulette:colors:black') or 0
    green_count = client.get('roulette:colors:green') or 0

    print(f"  📊 Total spins: {total_spins}")
    print(f"  🎯 Último número: {latest_number}")
    print(f"  🔴 Rojos: {red_count} | ⚫ Negros: {black_count} | 🟢 Verdes: {green_count}")

    # Stats hash
    if client.exists('roulette:stats'):
        stats = client.hgetall('roulette:stats')
        print(f"  📈 Stats adicionales: {len(stats)} campos")
        for key, value in stats.items():
            print(f"      {key}: {value}")

    print()

def analyze_predictions_data(client):
    """Analizar datos de predicciones"""
    print("🤖 DATOS DE IA Y PREDICCIONES:")

    # Predicciones pendientes
    if client.exists('ai:pending_predictions'):
        pending_count = client.llen('ai:pending_predictions')
        pending_list = client.lrange('ai:pending_predictions', 0, -1)
        print(f"  ⏳ Predicciones pendientes: {pending_count}")
        for pred_id in pending_list[:5]:  # Mostrar solo las primeras 5
            if client.exists(f'prediction:{pred_id}'):
                pred_data = client.hgetall(f'prediction:{pred_id}')
                confidence = pred_data.get('confidence', 'N/A')
                timestamp = pred_data.get('timestamp', 'N/A')
                print(f"      • {pred_id}: confianza={confidence}, timestamp={timestamp}")

    # Estadísticas de IA
    if client.exists('ai:game_stats'):
        ai_stats = client.hgetall('ai:game_stats')
        print(f"  📊 Estadísticas IA: {len(ai_stats)} campos")
        for key, value in ai_stats.items():
            print(f"      {key}: {value}")

    print()

def analyze_performance(client):
    """Analizar rendimiento de Redis"""
    print("⚡ ANÁLISIS DE RENDIMIENTO:")

    # Información del servidor
    info = client.info()

    memory_used = info.get('used_memory_human', 'N/A')
    memory_peak = info.get('used_memory_peak_human', 'N/A')
    connected_clients = info.get('connected_clients', 0)
    total_commands = info.get('total_commands_processed', 0)

    print(f"  💾 Memoria usada: {memory_used}")
    print(f"  📈 Pico de memoria: {memory_peak}")
    print(f"  👥 Clientes conectados: {connected_clients}")
    print(f"  ⚙️ Comandos procesados: {total_commands}")

    # Keyspace info
    if 'db0' in info:
        db_info = info['db0']
        print(f"  🗃️ Base de datos: {db_info}")

    print()

def print_improvement_suggestions():
    """Imprimir sugerencias de mejora"""
    print("💡 SUGERENCIAS DE MEJORA:")
    print("=" * 60)

    improvements = [
        "🔧 ESTRUCTURA DE DATOS:",
        "  • Agregar timestamps estructurados para cada número",
        "  • Implementar índices para búsquedas rápidas por fecha/rango",
        "  • Crear agregaciones por minutos/horas para análisis temporal",
        "",
        "🤖 MACHINE LEARNING:",
        "  • Almacenar features engineered para XGBoost",
        "  • Crear cache de modelos entrenados",
        "  • Implementar pipeline de feature extraction",
        "",
        "📊 ANALYTICS:",
        "  • Agregar métricas de patrones (rachas, gaps, frecuencias)",
        "  • Implementar rolling statistics (ventanas móviles)",
        "  • Crear índices de sectores y posiciones de la rueda",
        "",
        "🚀 PERFORMANCE:",
        "  • Usar pipelines para operaciones batch",
        "  • Implementar compression para datos históricos",
        "  • Agregar TTL para limpeza automática",
        "",
        "🔍 MONITORING:",
        "  • Métricas de performance del sistema",
        "  • Logs estructurados de predicciones",
        "  • Dashboard de salud del sistema"
    ]

    for suggestion in improvements:
        print(suggestion)

    print("\n" + "=" * 60)

if __name__ == "__main__":
    print("🔍 ANÁLISIS DE ESTRUCTURA DE REDIS")
    print("=" * 60)
    analyze_redis_structure()