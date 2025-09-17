#!/usr/bin/env python3
"""
Script para verificar los datos más recientes en Redis y PostgreSQL
"""

import os
import redis
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_redis_data():
    """Verificar datos recientes en Redis"""
    print("🔴 === DATOS RECIENTES EN REDIS ===")
    
    redis_url = os.getenv("REDIS_PUBLIC_URL") or os.getenv("REDIS_URL") or os.getenv("Connection_redis")
    
    try:
        client = redis.from_url(redis_url, decode_responses=True)
        
        # Último número
        latest = client.get("roulette:latest")
        print(f"Último número: {latest}")
        
        # Últimos 10 números del historial
        history = client.lrange("roulette:history", 0, 9)
        print(f"Últimos 10 números: {history}")
        
        # Estadísticas de colores
        red_count = client.get("roulette:colors:red") or 0
        black_count = client.get("roulette:colors:black") or 0
        green_count = client.get("roulette:colors:green") or 0
        total_spins = client.get("roulette:total_spins") or 0
        
        print(f"Estadísticas:")
        print(f"  - Rojos: {red_count}")
        print(f"  - Negros: {black_count}")
        print(f"  - Verdes: {green_count}")
        print(f"  - Total spins: {total_spins}")
        
        # Stats hash
        stats = client.hgetall("roulette:stats")
        if stats:
            print(f"Stats generales:")
            for key, value in stats.items():
                print(f"  - {key}: {value}")
        
    except Exception as e:
        print(f"Error: {e}")

def check_postgres_data():
    """Verificar datos recientes en PostgreSQL"""
    print("\n🐘 === DATOS RECIENTES EN POSTGRESQL ===")
    
    db_url = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL")
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Últimos 10 números
        cursor.execute("""
            SELECT rni.number_value, rni.color, rni.created_at
            FROM roulette_numbers_individual rni
            ORDER BY rni.created_at DESC
            LIMIT 10;
        """)
        
        recent_numbers = cursor.fetchall()
        print(f"Últimos 10 números:")
        for num, color, created in recent_numbers:
            print(f"  - {num} ({color}) - {created}")
        
        # Estadísticas por color
        cursor.execute("""
            SELECT color, COUNT(*) as count
            FROM roulette_numbers_individual
            GROUP BY color
            ORDER BY count DESC;
        """)
        
        color_stats = cursor.fetchall()
        print(f"\nEstadísticas por color:")
        for color, count in color_stats:
            print(f"  - {color}: {count}")
        
        # Último registro de historia
        cursor.execute("""
            SELECT created_at, session_data
            FROM roulette_history
            ORDER BY created_at DESC
            LIMIT 1;
        """)
        
        last_session = cursor.fetchone()
        if last_session:
            print(f"\nÚltima sesión: {last_session[0]}")
            print(f"Datos: {last_session[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Función principal"""
    print("🔍 VERIFICACIÓN DE DATOS RECIENTES")
    print("=" * 50)
    
    check_redis_data()
    check_postgres_data()

if __name__ == "__main__":
    main() 