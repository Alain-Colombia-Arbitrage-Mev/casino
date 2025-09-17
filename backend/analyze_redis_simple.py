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
        print("Conectado a Redis exitosamente")
        print("=" * 60)

        # Obtener todas las claves
        all_keys = client.keys("*")
        print(f"Total de claves en Redis: {len(all_keys)}")
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
                print(f"{category.upper()} ({len(keys)} claves):")
                for key in sorted(keys):
                    key_type = client.type(key)
                    size = get_key_size(client, key, key_type)
                    print(f"  - {key} ({key_type}) - {size}")
                print()

        print("=" * 60)
        print("ANALISIS DETALLADO DE DATOS:")
        print("=" * 60)

        # Análisis específico de datos de ruleta
        analyze_roulette_data(client)

        # Análisis de predicciones
        analyze_predictions_data(client)

        # Análisis de rendimiento
        analyze_performance(client)

        # Propuestas de mejora
        print_improvement_suggestions()

        # Generar estructura recomendada
        generate_improved_structure(client)

    except Exception as e:
        print(f"Error analizando Redis: {e}")

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
    print("DATOS DE RULETA:")

    # Historial
    if client.exists('roulette:history'):
        history_length = client.llen('roulette:history')
        recent_numbers = client.lrange('roulette:history', 0, 9)
        print(f"  Historial: {history_length} numeros")
        print(f"  Ultimos 10: {recent_numbers}")

    # Estadísticas
    total_spins = client.get('roulette:total_spins') or 0
    latest_number = client.get('roulette:latest') or 'N/A'

    red_count = client.get('roulette:colors:red') or 0
    black_count = client.get('roulette:colors:black') or 0
    green_count = client.get('roulette:colors:green') or 0

    print(f"  Total spins: {total_spins}")
    print(f"  Ultimo numero: {latest_number}")
    print(f"  Rojos: {red_count} | Negros: {black_count} | Verdes: {green_count}")

    # Stats hash
    if client.exists('roulette:stats'):
        stats = client.hgetall('roulette:stats')
        print(f"  Stats adicionales: {len(stats)} campos")
        for key, value in stats.items():
            print(f"    {key}: {value}")

    print()

def analyze_predictions_data(client):
    """Analizar datos de predicciones"""
    print("DATOS DE IA Y PREDICCIONES:")

    # Predicciones pendientes
    if client.exists('ai:pending_predictions'):
        pending_count = client.llen('ai:pending_predictions')
        pending_list = client.lrange('ai:pending_predictions', 0, -1)
        print(f"  Predicciones pendientes: {pending_count}")
        for pred_id in pending_list[:3]:  # Mostrar solo las primeras 3
            if client.exists(f'prediction:{pred_id}'):
                pred_data = client.hgetall(f'prediction:{pred_id}')
                confidence = pred_data.get('confidence', 'N/A')
                timestamp = pred_data.get('timestamp', 'N/A')
                pred_type = pred_data.get('prediction_type', 'N/A')
                print(f"    - {pred_id}: tipo={pred_type}, confianza={confidence}")

    # Estadísticas de IA
    if client.exists('ai:game_stats'):
        ai_stats = client.hgetall('ai:game_stats')
        print(f"  Estadisticas IA: {len(ai_stats)} campos")
        for key, value in ai_stats.items():
            print(f"    {key}: {value}")

    print()

def analyze_performance(client):
    """Analizar rendimiento de Redis"""
    print("ANALISIS DE RENDIMIENTO:")

    # Información del servidor
    info = client.info()

    memory_used = info.get('used_memory_human', 'N/A')
    memory_peak = info.get('used_memory_peak_human', 'N/A')
    connected_clients = info.get('connected_clients', 0)
    total_commands = info.get('total_commands_processed', 0)

    print(f"  Memoria usada: {memory_used}")
    print(f"  Pico de memoria: {memory_peak}")
    print(f"  Clientes conectados: {connected_clients}")
    print(f"  Comandos procesados: {total_commands}")

    # Keyspace info
    if 'db0' in info:
        db_info = info['db0']
        print(f"  Base de datos: {db_info}")

    print()

def print_improvement_suggestions():
    """Imprimir sugerencias de mejora"""
    print("SUGERENCIAS DE MEJORA:")
    print("=" * 60)

    improvements = [
        "ESTRUCTURA DE DATOS:",
        "  - Agregar timestamps estructurados para cada numero",
        "  - Implementar indices para busquedas rapidas por fecha/rango",
        "  - Crear agregaciones por minutos/horas para analisis temporal",
        "",
        "MACHINE LEARNING:",
        "  - Almacenar features engineered para XGBoost",
        "  - Crear cache de modelos entrenados",
        "  - Implementar pipeline de feature extraction",
        "",
        "ANALYTICS:",
        "  - Agregar metricas de patrones (rachas, gaps, frecuencias)",
        "  - Implementar rolling statistics (ventanas moviles)",
        "  - Crear indices de sectores y posiciones de la rueda",
        "",
        "PERFORMANCE:",
        "  - Usar pipelines para operaciones batch",
        "  - Implementar compression para datos historicos",
        "  - Agregar TTL para limpeza automatica",
    ]

    for suggestion in improvements:
        print(suggestion)

    print("\n" + "=" * 60)

def generate_improved_structure(client):
    """Generar propuesta de estructura mejorada"""
    print("PROPUESTA DE ESTRUCTURA MEJORADA:")
    print("=" * 60)

    # Obtener datos actuales para el análisis
    history = client.lrange('roulette:history', 0, -1)

    structure = {
        "DATOS BASICOS": [
            "roulette:history                 # Lista principal (actual)",
            "roulette:latest                  # Ultimo numero (actual)",
            "roulette:total_spins            # Contador total (actual)"
        ],
        "TIMESTAMPS Y METADATOS": [
            "roulette:timeline               # Sorted set: timestamp -> numero",
            "roulette:metadata:{id}          # Hash por numero con timestamp, session_id, etc",
            "roulette:sessions:current       # ID de sesion actual",
            "roulette:sessions:{id}          # Datos de cada sesion"
        ],
        "ANALYTICS AVANZADO": [
            "analytics:patterns:streaks      # Rachas de colores",
            "analytics:patterns:gaps         # Gaps entre repeticiones",
            "analytics:patterns:sectors      # Frecuencia por sectores",
            "analytics:rolling:1min          # Stats ventana 1 minuto",
            "analytics:rolling:5min          # Stats ventana 5 minutos",
            "analytics:rolling:15min         # Stats ventana 15 minutos"
        ],
        "MACHINE LEARNING": [
            "ml:features:current             # Features actuales para ML",
            "ml:features:history             # Historial de features",
            "ml:models:xgboost:v1           # Modelo XGBoost serializado",
            "ml:models:metadata             # Metadata de modelos (accuracy, version, etc)",
            "ml:predictions:queue           # Cola de predicciones a procesar"
        ],
        "OPTIMIZACIONES": [
            "cache:stats:5min               # Cache de stats (TTL 5min)",
            "cache:predictions:latest       # Cache de ultima prediccion",
            "performance:metrics            # Metricas de rendimiento",
            "system:health                  # Estado del sistema"
        ]
    }

    for category, keys in structure.items():
        print(f"\n{category}:")
        for key_desc in keys:
            print(f"  {key_desc}")

    print("\n" + "=" * 60)

    # Calcular estadísticas para demostrar valor
    if history:
        print("ESTADISTICAS PARA NUEVA ESTRUCTURA:")
        print(f"  Numeros disponibles: {len(history)}")

        # Análisis de patrones
        colors = []
        for num_str in history:
            num = int(num_str)
            if num == 0:
                colors.append('G')
            elif num in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]:
                colors.append('R')
            else:
                colors.append('B')

        # Calcular rachas
        streaks = calculate_streaks(colors)
        print(f"  Rachas detectadas: {len(streaks)}")
        print(f"  Racha mas larga: {max([s['length'] for s in streaks]) if streaks else 0}")

        # Calcular gaps
        gaps = calculate_gaps(history)
        print(f"  Gaps calculados: {len(gaps)} numeros con repeticiones")

        print("\n")

def calculate_streaks(colors):
    """Calcular rachas de colores"""
    streaks = []
    if not colors:
        return streaks

    current_color = colors[0]
    current_length = 1

    for i in range(1, len(colors)):
        if colors[i] == current_color:
            current_length += 1
        else:
            if current_length >= 2:  # Solo contar rachas de 2+
                streaks.append({
                    'color': current_color,
                    'length': current_length,
                    'end_position': i - 1
                })
            current_color = colors[i]
            current_length = 1

    # Agregar última racha si es válida
    if current_length >= 2:
        streaks.append({
            'color': current_color,
            'length': current_length,
            'end_position': len(colors) - 1
        })

    return streaks

def calculate_gaps(history):
    """Calcular gaps entre repeticiones de números"""
    gaps = {}
    number_positions = {}

    # Mapear posiciones de cada número
    for i, num_str in enumerate(history):
        num = int(num_str)
        if num not in number_positions:
            number_positions[num] = []
        number_positions[num].append(i)

    # Calcular gaps para números que aparecen más de una vez
    for num, positions in number_positions.items():
        if len(positions) > 1:
            gaps[num] = []
            for i in range(1, len(positions)):
                gap = positions[i-1] - positions[i]  # Distancia entre apariciones
                gaps[num].append(gap)

    return gaps

if __name__ == "__main__":
    print("ANALISIS DE ESTRUCTURA DE REDIS")
    print("=" * 60)
    analyze_redis_structure()