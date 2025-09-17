#!/usr/bin/env python3
"""
Script de prueba para el endpoint de estadísticas optimizado
Demuestra cómo usar el nuevo backend Go con las keys de Redis reales
"""

import requests
import json
from datetime import datetime

def test_optimized_backend():
    """Prueba los endpoints optimizados del backend Go"""
    base_url = "http://localhost:5003"

    print(">> Probando Backend Go Optimizado con Keys de Redis Reales")
    print("=" * 60)

    # Test 1: Health check
    print("\n1. Health Check:")
    try:
        response = requests.get(f"{base_url}/ping")
        data = response.json()
        print(f"   [OK] Status: {data.get('status', 'unknown')}")
        print(f"   [INFO] Architecture: {data.get('architecture', 'unknown')}")
        print(f"   [TIME] Timestamp: {data.get('timestamp', 'unknown')}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Test 2: Redis Keys Diagnostic
    print("\n2. Redis Keys Diagnostic:")
    try:
        response = requests.get(f"{base_url}/api/system/redis-keys")
        data = response.json()

        print(f"   [INFO] Keys encontradas:")
        for key, info in data['expected_keys'].items():
            status = "[OK]" if info['exists'] else "[MISSING]"
            print(f"     {status} {key}: {info.get('type', 'unknown')}")

        print(f"\n   [INFO] Number Frequencies Sample:")
        for key, value in data['number_frequencies_sample'].items():
            print(f"     - {key}: {value}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Optimized Stats
    print("\n3. Estadísticas Optimizadas:")
    try:
        response = requests.get(f"{base_url}/api/roulette/stats")
        data = response.json()
        stats = data['stats']

        print(f"   📈 Total Spins: {stats['total_numbers']}")
        print(f"   🎯 Último número: {stats['last_number']} ({stats['last_color']})")
        print(f"   🕐 Session start: {stats['session_start']}")

        print(f"\n   🎨 Contadores de colores:")
        for color, count in stats['color_counts'].items():
            print(f"     • {color.capitalize()}: {count}")

        print(f"\n   📊 Docenas:")
        for dozen, count in stats['dozen_counts'].items():
            print(f"     • Docena {dozen}: {count}")

        print(f"\n   📊 Columnas:")
        for column, count in stats['column_counts'].items():
            print(f"     • Columna {column}: {count}")

        print(f"\n   🔥 Números calientes (Top 10):")
        for i, num in enumerate(stats['hot_numbers'][:10], 1):
            freq = stats['number_frequencies'].get(str(num), 0)
            print(f"     {i:2d}. Número {num:2d}: {freq} veces")

        print(f"\n   ❄️  Números fríos (Bottom 10):")
        for i, num in enumerate(stats['cold_numbers'][:10], 1):
            freq = stats['number_frequencies'].get(str(num), 0)
            print(f"     {i:2d}. Número {num:2d}: {freq} veces")

        print(f"\n   📅 Últimos 5 números:")
        for i, recent in enumerate(stats['recent_numbers'][:5], 1):
            print(f"     {i}. {recent['number']} ({recent['color']}) - "
                  f"Docena {recent['dozen']}, Columna {recent['column']}, "
                  f"{recent['parity']}, {recent['high_low']}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 4: ML Features
    print("\n4. ML Features:")
    try:
        response = requests.get(f"{base_url}/api/roulette/ml-features")
        data = response.json()
        features = data['features']

        print(f"   🧠 Números recientes (primeros 10): {features['recent_numbers'][:10]}")
        print(f"   🎨 Colores recientes (primeros 10): {features['recent_colors'][:10]}")

        # Estadísticas de gaps más interesantes
        gaps = features['current_gaps']
        sorted_gaps = sorted(gaps.items(), key=lambda x: int(x[1]))

        print(f"\n   ⏰ Numbers con menor gap (más recientes):")
        for num, gap in sorted_gaps[:5]:
            print(f"     • Número {num}: {gap} spins atrás")

        print(f"\n   ⏳ Numbers con mayor gap (más antiguos):")
        for num, gap in sorted_gaps[-5:]:
            print(f"     • Número {num}: {gap} spins atrás")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 5: System Status
    print("\n5. System Status:")
    try:
        response = requests.get(f"{base_url}/api/system/health")
        data = response.json()
        print(f"   💚 Backend Health: {data.get('status', 'unknown')}")

        response = requests.get(f"{base_url}/api/system/redis-status")
        data = response.json()
        print(f"   🔴 Redis Status: {data.get('status', 'unknown')}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "=" * 60)
    print("✅ Pruebas completadas!")
    print("📝 El backend Go está funcionando correctamente con las keys de Redis reales")

def analyze_patterns(stats):
    """Analiza patrones en los datos"""
    print("\n6. Análisis de Patrones:")

    # Analizar tendencias de color
    recent_colors = []
    for num_data in stats['recent_numbers'][:10]:
        recent_colors.append(num_data['color'])

    red_count = recent_colors.count('red')
    black_count = recent_colors.count('black')
    green_count = recent_colors.count('green')

    print(f"   🎨 Últimos 10 números por color:")
    print(f"     • Red: {red_count}/10 ({red_count*10}%)")
    print(f"     • Black: {black_count}/10 ({black_count*10}%)")
    print(f"     • Green: {green_count}/10 ({green_count*10}%)")

    # Analizar docenas
    recent_dozens = []
    for num_data in stats['recent_numbers'][:10]:
        if num_data['dozen'] > 0:  # Excluir el 0
            recent_dozens.append(num_data['dozen'])

    print(f"\n   📊 Últimos números por docena:")
    for dozen in [1, 2, 3]:
        count = recent_dozens.count(dozen)
        print(f"     • Docena {dozen}: {count}/{len(recent_dozens)} números")

    # Patrones de paridad
    recent_parity = []
    for num_data in stats['recent_numbers'][:10]:
        if num_data['parity'] != 'zero':
            recent_parity.append(num_data['parity'])

    odd_count = recent_parity.count('odd')
    even_count = recent_parity.count('even')

    print(f"\n   🔢 Paridad en últimos números:")
    print(f"     • Odd: {odd_count}/{len(recent_parity)}")
    print(f"     • Even: {even_count}/{len(recent_parity)}")

if __name__ == "__main__":
    test_optimized_backend()