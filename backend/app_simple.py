#!/usr/bin/env python3
"""
AI Casino - Roulette Application
Backend API con Redis únicamente (alta velocidad) - Version Simple
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from database_redis_only import db_manager
from ai_predictor_redis import RouletteAIPredictor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
CORS(app)

# Configuración
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Inicializar predictor de IA
ai_predictor = RouletteAIPredictor(db_manager.redis_client)

@app.route('/')
def index():
    """Página principal"""
    return jsonify({
        "message": "AI Casino - Roulette API",
        "version": "2.0.0",
        "database": "Redis Only (High Speed)",
        "status": "running",
        "storage_type": "redis_only"
    })

@app.route('/health')
def health():
    """Endpoint de salud (Redis only)"""
    try:
        # Verificar estado del sistema Redis
        db_status = db_manager.get_database_status()

        # Verificar conexión Redis
        redis_status = False
        redis_info = {}
        try:
            if db_manager.redis_client:
                db_manager.redis_client.ping()
                redis_status = True
                # Información adicional de Redis
                info = db_manager.redis_client.info()
                redis_info = {
                    "memory_used": info.get('used_memory_human', 'N/A'),
                    "connected_clients": info.get('connected_clients', 0),
                    "total_commands_processed": info.get('total_commands_processed', 0)
                }
        except Exception as redis_error:
            logger.warning(f"Redis health check failed: {redis_error}")

        return jsonify({
            "status": "healthy" if redis_status else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "storage_type": "redis_only",
            "redis": {
                "connected": redis_status,
                "info": redis_info
            },
            "system_status": db_status
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/api/roulette/numbers', methods=['GET'])
def get_roulette_numbers():
    """Obtener los últimos números de la ruleta"""
    try:
        limit = request.args.get('limit', 20, type=int)
        numbers = db_manager.get_last_roulette_numbers(limit)

        return jsonify({
            "success": True,
            "data": numbers,
            "count": len(numbers)
        })
    except Exception as e:
        logger.error(f"Error obteniendo números: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/roulette/numbers', methods=['POST'])
def add_roulette_number():
    """Agregar un nuevo número de ruleta y generar predicción automáticamente"""
    try:
        data = request.get_json()

        if not data or 'number' not in data:
            return jsonify({
                "success": False,
                "error": "Número requerido"
            }), 400

        number = data['number']

        # Validar número
        if not isinstance(number, int) or number < 0 or number > 36:
            return jsonify({
                "success": False,
                "error": "Número debe estar entre 0 y 36"
            }), 400

        # 1. Verificar predicciones pendientes ANTES de insertar
        pending_results = []
        try:
            if db_manager.redis_client:
                pending_predictions = db_manager.redis_client.lrange('ai:pending_predictions', 0, -1)

                for pred_id in pending_predictions:
                    if isinstance(pred_id, bytes):
                        pred_id = pred_id.decode('utf-8')

                    result = verify_prediction_simple(pred_id, number)
                    if result:
                        pending_results.append(result)

                logger.info(f"Verificadas {len(pending_results)} predicciones pendientes para número {number}")

        except Exception as verify_error:
            logger.error(f"Error verificando predicciones: {verify_error}")

        # 2. Insertar el nuevo número
        insert_result = db_manager.insert_roulette_number(number)

        if insert_result and insert_result.get('success'):
            # 3. Generar nueva predicción automáticamente
            new_prediction = None
            try:
                new_prediction = ai_predictor.make_prediction('groups')
                if new_prediction:
                    logger.info(f"Nueva predicción generada: {new_prediction.prediction_id}")
            except Exception as pred_error:
                logger.error(f"Error generando predicción: {pred_error}")

            # 4. Preparar respuesta
            response_data = {
                "number_data": insert_result.get('data', {}),
                "verified_predictions": len(pending_results),
                "prediction_results": pending_results,
                "new_prediction_generated": new_prediction is not None
            }

            if new_prediction:
                response_data["new_prediction"] = {
                    "prediction_id": new_prediction.prediction_id,
                    "prediction_groups": new_prediction.prediction_groups,
                    "confidence": new_prediction.confidence,
                    "reasoning": new_prediction.reasoning
                }

            return jsonify({
                "success": True,
                "message": "Número agregado y predicciones verificadas exitosamente",
                "data": response_data
            })
        else:
            error_msg = insert_result.get('error') if insert_result else "Error desconocido"
            return jsonify({
                "success": False,
                "error": error_msg
            }), 500

    except Exception as e:
        logger.error(f"Error agregando número: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def verify_prediction_simple(prediction_id, actual_number):
    """Función simple para verificar predicción"""
    try:
        if not db_manager.redis_client:
            return None

        pred_data = db_manager.redis_client.hgetall(f"prediction:{prediction_id}")

        if not pred_data:
            return None

        # Obtener grupos predichos
        groups_str = pred_data.get('prediction_groups', '{}')
        try:
            groups = json.loads(groups_str)
        except json.JSONDecodeError:
            return None

        # Verificar resultado para cada grupo
        group_results = []
        overall_winner = False

        for group_name, group_numbers in groups.items():
            is_group_winner = actual_number in group_numbers
            if is_group_winner:
                overall_winner = True

            group_results.append({
                "group_name": group_name,
                "predicted_numbers": group_numbers,
                "is_winner": is_group_winner,
                "group_size": len(group_numbers)
            })

        # Actualizar estadísticas
        try:
            stats_key = "ai:game_stats"
            db_manager.redis_client.hincrby(stats_key, "total_predictions", 1)

            if overall_winner:
                db_manager.redis_client.hincrby(stats_key, "total_wins", 1)
            else:
                db_manager.redis_client.hincrby(stats_key, "total_losses", 1)

            # Remover de predicciones pendientes
            db_manager.redis_client.lrem('ai:pending_predictions', 0, prediction_id)

        except Exception as stats_error:
            logger.error(f"Error actualizando estadísticas: {stats_error}")

        return {
            "prediction_id": prediction_id,
            "actual_number": actual_number,
            "overall_winner": overall_winner,
            "group_results": group_results,
            "analysis": {
                "total_groups": len(groups),
                "winning_groups": sum(1 for gr in group_results if gr["is_winner"]),
                "success_rate": f"{sum(1 for gr in group_results if gr['is_winner']) / len(groups) * 100:.1f}%" if groups else "0%"
            }
        }

    except Exception as e:
        logger.error(f"Error verificando predicción {prediction_id}: {e}")
        return None

@app.route('/api/ai/predict', methods=['POST'])
def make_prediction():
    """Crear una nueva predicción con IA"""
    try:
        data = request.get_json() or {}
        prediction_type = data.get('type', 'groups')

        if prediction_type not in ['individual', 'groups', 'sector', 'color']:
            return jsonify({
                "success": False,
                "error": "Tipo de predicción inválido"
            }), 400

        # Hacer predicción
        prediction = ai_predictor.make_prediction(prediction_type)

        if prediction:
            return jsonify({
                "success": True,
                "data": {
                    "prediction_id": prediction.prediction_id,
                    "timestamp": prediction.timestamp,
                    "last_number": prediction.last_number,
                    "predicted_numbers": prediction.predicted_numbers,
                    "prediction_groups": prediction.prediction_groups,
                    "prediction_type": prediction.prediction_type,
                    "confidence": prediction.confidence,
                    "reasoning": prediction.reasoning
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo generar predicción"
            }), 500

    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/stats', methods=['GET'])
def get_ai_stats():
    """Obtener estadísticas de IA"""
    try:
        if not db_manager.redis_client:
            return jsonify({
                "success": False,
                "error": "Redis no disponible"
            }), 500

        # Obtener estadísticas globales
        global_stats = db_manager.redis_client.hgetall("ai:game_stats")

        total_predictions = int(global_stats.get('total_predictions', 0))
        total_wins = int(global_stats.get('total_wins', 0))
        total_losses = int(global_stats.get('total_losses', 0))

        win_rate = (total_wins / total_predictions * 100) if total_predictions > 0 else 0

        # Predicciones pendientes
        pending_count = db_manager.redis_client.llen('ai:pending_predictions') or 0

        stats_data = {
            'total_predictions': total_predictions,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'overall_win_rate': round(win_rate, 1),
            'pending_predictions': pending_count,
            'last_updated': datetime.now().isoformat()
        }

        return jsonify({
            "success": True,
            "data": stats_data
        })

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/database/status', methods=['GET'])
def database_status():
    """Obtener estado de la base de datos"""
    try:
        status = db_manager.get_database_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint no encontrado"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Error interno del servidor"
    }), 500

if __name__ == '__main__':
    # Verificar conexiones al iniciar (Redis only)
    logger.info("Iniciando AI Casino - Roulette API (Redis Only)")

    try:
        # Verificar sistema Redis
        db_status = db_manager.get_database_status()
        if db_status['success']:
            logger.info("Sistema Redis operativo")
            logger.info(f"Números en historial: {db_status['estado']['total_registros']['history']}")
            logger.info(f"Total spins: {db_status['estado']['total_spins']}")
        else:
            logger.error(f"Error en sistema Redis: {db_status.get('error', 'Unknown error')}")
    except Exception as e:
        logger.error(f"Error verificando sistema Redis: {e}")

    try:
        # Verificar Redis connection
        if db_manager.redis_client:
            db_manager.redis_client.ping()
            logger.info("Conexión a Redis exitosa")
        else:
            logger.error("Redis no disponible - Sistema no puede funcionar")
    except Exception as e:
        logger.error(f"Redis no disponible: {e}")

    # Configurar puerto
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'

    logger.info(f"Servidor iniciando en puerto {port} (Storage: Redis Only)")
    app.run(host='0.0.0.0', port=port, debug=debug)