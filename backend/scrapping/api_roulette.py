#!/usr/bin/env python3
"""
API simple para consultar datos de la ruleta desde Redis y PostgreSQL
Útil para crear dashboards o consultar estadísticas
"""

import os
import json
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuración
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/roulette_db")
REDIS_PREFIX = "roulette:"

# Conexiones globales
redis_client = None
postgres_conn = None

def init_connections():
    """Inicializar conexiones a las bases de datos"""
    global redis_client, postgres_conn
    
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        print("✅ Redis conectado")
    except Exception as e:
        print(f"❌ Error Redis: {e}")
        redis_client = None
    
    try:
        postgres_conn = psycopg2.connect(DATABASE_URL)
        print("✅ PostgreSQL conectado")
    except Exception as e:
        print(f"❌ Error PostgreSQL: {e}")
        postgres_conn = None

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "redis_connected": redis_client is not None,
        "postgres_connected": postgres_conn is not None
    })

@app.route('/stats/redis')
def redis_stats():
    """Obtener estadísticas desde Redis"""
    if not redis_client:
        return jsonify({"error": "Redis no disponible"}), 500
    
    try:
        # Estadísticas generales
        stats = redis_client.hgetall(f"{REDIS_PREFIX}stats")
        
        # Contadores por color
        colors = {
            'red': redis_client.get(f"{REDIS_PREFIX}colors:red") or "0",
            'black': redis_client.get(f"{REDIS_PREFIX}colors:black") or "0",
            'green': redis_client.get(f"{REDIS_PREFIX}colors:green") or "0"
        }
        
        # Total de giros y último número
        total_spins = redis_client.get(f"{REDIS_PREFIX}total_spins") or "0"
        latest_number = redis_client.get(f"{REDIS_PREFIX}latest") or None
        
        # Historial (últimos 20)
        history = redis_client.lrange(f"{REDIS_PREFIX}history", 0, 19)
        
        return jsonify({
            "timestamp": datetime.now().isoformat(),
            "general_stats": stats,
            "colors": colors,
            "total_spins": int(total_spins),
            "latest_number": latest_number,
            "recent_history": history
        })
        
    except Exception as e:
        return jsonify({"error": f"Error obteniendo stats Redis: {str(e)}"}), 500

@app.route('/stats/postgres')
def postgres_stats():
    """Obtener estadísticas desde PostgreSQL"""
    if not postgres_conn:
        return jsonify({"error": "PostgreSQL no disponible"}), 500
    
    try:
        cursor = postgres_conn.cursor(cursor_factory=RealDictCursor)
        
        # Estadísticas por color
        cursor.execute("""
            SELECT stat_key, stat_value 
            FROM roulette_stats 
            WHERE stat_type = 'color'
            ORDER BY stat_key
        """)
        color_stats = {row['stat_key']: row['stat_value'] for row in cursor.fetchall()}
        
        # Total de giros
        cursor.execute("""
            SELECT stat_value 
            FROM roulette_stats 
            WHERE stat_type = 'general' AND stat_key = 'total_spins'
        """)
        total_result = cursor.fetchone()
        total_spins = total_result['stat_value'] if total_result else 0
        
        # Últimos números (últimos 20)
        cursor.execute("""
            SELECT number_value, color, created_at
            FROM roulette_numbers_individual
            ORDER BY created_at DESC
            LIMIT 20
        """)
        recent_numbers = [dict(row) for row in cursor.fetchall()]
        
        # Estadísticas por día (últimos 7 días)
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_numbers,
                COUNT(*) FILTER (WHERE color = 'red') as red_count,
                COUNT(*) FILTER (WHERE color = 'black') as black_count,
                COUNT(*) FILTER (WHERE color = 'green') as green_count
            FROM roulette_numbers_individual
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        daily_stats = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            "timestamp": datetime.now().isoformat(),
            "color_totals": color_stats,
            "total_spins": total_spins,
            "recent_numbers": recent_numbers,
            "daily_stats": daily_stats
        })
        
    except Exception as e:
        return jsonify({"error": f"Error obteniendo stats PostgreSQL: {str(e)}"}), 500

@app.route('/numbers/recent')
def recent_numbers():
    """Obtener números recientes desde Redis (más rápido)"""
    if not redis_client:
        return jsonify({"error": "Redis no disponible"}), 500
    
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 100)  # Máximo 100
        
        numbers = redis_client.lrange(f"{REDIS_PREFIX}history", 0, limit-1)
        
        return jsonify({
            "timestamp": datetime.now().isoformat(),
            "count": len(numbers),
            "numbers": numbers
        })
        
    except Exception as e:
        return jsonify({"error": f"Error obteniendo números: {str(e)}"}), 500

@app.route('/numbers/search')
def search_numbers():
    """Buscar números con filtros en PostgreSQL"""
    if not postgres_conn:
        return jsonify({"error": "PostgreSQL no disponible"}), 500
    
    try:
        # Parámetros de búsqueda
        color = request.args.get('color')  # red, black, green
        number = request.args.get('number', type=int)  # número específico
        start_date = request.args.get('start_date')  # YYYY-MM-DD
        end_date = request.args.get('end_date')  # YYYY-MM-DD
        limit = request.args.get('limit', 100, type=int)
        
        cursor = postgres_conn.cursor(cursor_factory=RealDictCursor)
        
        # Construir query dinámicamente
        conditions = []
        params = []
        
        if color:
            conditions.append("color = %s")
            params.append(color)
        
        if number is not None:
            conditions.append("number_value = %s")
            params.append(number)
        
        if start_date:
            conditions.append("DATE(created_at) >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("DATE(created_at) <= %s")
            params.append(end_date)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT number_value, color, created_at
            FROM roulette_numbers_individual
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s
        """
        params.append(limit)
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            "timestamp": datetime.now().isoformat(),
            "filters": {
                "color": color,
                "number": number,
                "start_date": start_date,
                "end_date": end_date
            },
            "count": len(results),
            "numbers": results
        })
        
    except Exception as e:
        return jsonify({"error": f"Error en búsqueda: {str(e)}"}), 500

@app.route('/stats/summary')
def stats_summary():
    """Resumen completo de estadísticas"""
    redis_data = {}
    postgres_data = {}
    
    # Intentar obtener datos de Redis
    if redis_client:
        try:
            redis_data = {
                "latest": redis_client.get(f"{REDIS_PREFIX}latest"),
                "total_spins": redis_client.get(f"{REDIS_PREFIX}total_spins") or "0",
                "colors": {
                    'red': redis_client.get(f"{REDIS_PREFIX}colors:red") or "0",
                    'black': redis_client.get(f"{REDIS_PREFIX}colors:black") or "0",
                    'green': redis_client.get(f"{REDIS_PREFIX}colors:green") or "0"
                }
            }
        except:
            pass
    
    # Intentar obtener datos de PostgreSQL
    if postgres_conn:
        try:
            cursor = postgres_conn.cursor(cursor_factory=RealDictCursor)
            
            # Total de números en la base
            cursor.execute("SELECT COUNT(*) as total FROM roulette_numbers_individual")
            total_db = cursor.fetchone()['total']
            
            # Distribución por color en la base
            cursor.execute("""
                SELECT color, COUNT(*) as count 
                FROM roulette_numbers_individual 
                GROUP BY color
            """)
            color_distribution = {row['color']: row['count'] for row in cursor.fetchall()}
            
            postgres_data = {
                "total_in_db": total_db,
                "color_distribution": color_distribution
            }
        except:
            pass
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "redis_data": redis_data,
        "postgres_data": postgres_data,
        "data_sources": {
            "redis_available": redis_client is not None,
            "postgres_available": postgres_conn is not None
        }
    })

if __name__ == '__main__':
    init_connections()
    
    # Configurar puerto para Railway
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 