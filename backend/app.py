#!/usr/bin/env python3
"""
AI Casino - Roulette Application
Backend API con Redis únicamente (alta velocidad)
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, make_response
from flask_cors import CORS
from database_redis_only import db_manager
from ai_predictor_redis import RouletteAIPredictor
# Importaciones opcionales
try:
    from data_exporter import data_exporter
    data_exporter_available = True
except ImportError:
    data_exporter_available = False
    print("⚠️ Data exporter no disponible")

try:
    from redis_monitor import initialize_monitor, get_monitor
    redis_monitor_available = True
except ImportError:
    redis_monitor_available = False
    print("⚠️ Redis monitor no disponible")

try:
    from automation_service import get_automation_service, initialize_automation
    automation_available = True
except ImportError:
    automation_available = False
    print("⚠️ Automation service no disponible")
from flask_cors import cross_origin

# Nuevas importaciones para Redis y servicio automático
try:
    from redis_manager import get_redis_manager
    redis_available = True
    print("✅ Redis Manager disponible")
except ImportError as e:
    redis_available = False
    print(f"⚠️ Redis no disponible: {e}")

try:
    from automatic_service import start_automatic_service, stop_automatic_service, get_service_status
    automatic_service_available = True
    print("✅ Servicio Automático disponible")
except ImportError as e:
    automatic_service_available = False
    print(f"⚠️ Servicio Automático no disponible: {e}")

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

# Inicializar monitor de Redis
redis_monitor = None

# Inicializar Redis Manager si está disponible
redis_manager = None
if redis_available:
    try:
        redis_manager = get_redis_manager()
        print("🔌 Redis Manager inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando Redis Manager: {e}")
        redis_manager = None

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
        limit = request.args.get('limit', 10, type=int)
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
    """Agregar un nuevo número de ruleta y verificar predicciones pendientes automáticamente"""
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
        
        # 1. Verificar predicciones pendientes ANTES de insertar el número
        pending_results = []
        try:
            if db_manager.redis_client:
                # Obtener predicciones pendientes
                pending_predictions = db_manager.redis_client.lrange('ai:pending_predictions', 0, -1)
                
                for pred_id_bytes in pending_predictions:
                    pred_id = pred_id_bytes.decode('utf-8') if isinstance(pred_id_bytes, bytes) else str(pred_id_bytes)
                    
                    # Verificar cada predicción pendiente
                    result = verify_prediction_against_number(pred_id, number)
                    if result:
                        pending_results.append(result)
                        
                logger.info(f"✅ Verificadas {len(pending_results)} predicciones pendientes para número {number}")
                        
        except Exception as verify_error:
            logger.error(f"Error verificando predicciones pendientes: {verify_error}")
        
        # 2. Insertar el nuevo número
        insert_result = db_manager.insert_roulette_number(number)
        
        if insert_result and insert_result.get('success'):
            # 3. Generar nueva predicción automáticamente
            new_prediction = None
            try:
                new_prediction = ai_predictor.make_prediction('groups')
                if new_prediction:
                    logger.info(f"✅ Nueva predicción generada automáticamente: {new_prediction.prediction_id}")
            except Exception as pred_error:
                logger.error(f"Error generando nueva predicción: {pred_error}")
            
            # 4. Preparar respuesta completa
            response_data = {
                "number_data": insert_result.get('data', {
                    "number": number,
                    "timestamp": datetime.now().isoformat()
                }),
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

def verify_prediction_against_number(prediction_id, actual_number):
    """Función helper para verificar una predicción contra un número real"""
    try:
        if not db_manager.redis_client:
            return None
            
        pred_data = db_manager.redis_client.hgetall(f"prediction:{prediction_id}")
        
        if not pred_data:
            return None
        
        import json
        
        # Función helper para obtener valores de Redis de forma segura
        def safe_get_redis_value(data, key, default=''):
            try:
                value = data.get(key, default)
                if isinstance(value, bytes):
                    return value.decode('utf-8')
                return str(value) if value is not None else default
            except Exception:
                return default
        
        # Obtener grupos de números predichos
        groups_str = safe_get_redis_value(pred_data, 'prediction_groups', '{}')
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
        
        # Guardar estadísticas en Redis
        try:
            # Actualizar estadísticas globales
            stats_key = "ai:game_stats"
            db_manager.redis_client.hincrby(stats_key, "total_predictions", 1)
            
            if overall_winner:
                db_manager.redis_client.hincrby(stats_key, "total_wins", 1)
            else:
                db_manager.redis_client.hincrby(stats_key, "total_losses", 1)
            
            # Actualizar estadísticas por grupo
            for group_result in group_results:
                group_key = f"ai:group_stats:{group_result['group_name']}"
                db_manager.redis_client.hincrby(group_key, "total", 1)
                
                if group_result['is_winner']:
                    db_manager.redis_client.hincrby(group_key, "wins", 1)
                else:
                    db_manager.redis_client.hincrby(group_key, "losses", 1)
            
            # Guardar resultado específico
            result_key = f"result:{prediction_id}"
            result_data = {
                'prediction_id': prediction_id,
                'actual_number': str(actual_number),
                'is_winner': '1' if overall_winner else '0',
                'winning_groups': str(sum(1 for gr in group_results if gr["is_winner"])),
                'total_groups': str(len(groups)),
                'timestamp': datetime.now().isoformat(),
                'verified': '1'
            }
            
            db_manager.redis_client.hset(result_key, mapping=result_data)
            db_manager.redis_client.expire(result_key, 86400 * 7)  # 7 días
            
            # Remover de predicciones pendientes
            db_manager.redis_client.lrem('ai:pending_predictions', 0, prediction_id)
            
            logger.info(f"✅ Estadísticas actualizadas para {prediction_id}: {sum(1 for gr in group_results if gr['is_winner'])}/{len(groups)} grupos ganadores")
            
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

@app.route('/api/roulette/latest', methods=['GET'])
def get_latest_number():
    """Obtener el último número de la ruleta"""
    try:
        numbers = db_manager.get_last_roulette_numbers(1)
        
        if numbers:
            return jsonify({
                "success": True,
                "data": numbers[0]
            })
        else:
            return jsonify({
                "success": True,
                "data": None,
                "message": "No hay números registrados"
            })
            
    except Exception as e:
        logger.error(f"Error obteniendo último número: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/roulette/stats', methods=['GET'])
def get_roulette_stats():
    """Obtener estadísticas de la ruleta"""
    try:
        # Inicializar estadísticas por defecto
        stats = {
            'total_spins': 0,
            'red_count': 0,
            'black_count': 0,
            'green_count': 0
        }
        
        # Intentar obtener desde Redis primero
        if db_manager.redis_client:
            try:
                # Obtener contadores de colores de forma segura
                red_count_str = db_manager.redis_client.get('roulette:colors:red')
                black_count_str = db_manager.redis_client.get('roulette:colors:black')
                green_count_str = db_manager.redis_client.get('roulette:colors:green')
                total_spins_str = db_manager.redis_client.get('roulette:total_spins')
                
                # Convertir a enteros de forma segura
                if red_count_str is not None:
                    stats['red_count'] = int(str(red_count_str))
                if black_count_str is not None:
                    stats['black_count'] = int(str(black_count_str))
                if green_count_str is not None:
                    stats['green_count'] = int(str(green_count_str))
                if total_spins_str is not None:
                    stats['total_spins'] = int(str(total_spins_str))
                
                # Si tenemos datos de Redis, usarlos
                if any(stats.values()):
                    logger.info("✅ Estadísticas obtenidas desde Redis")
                    return jsonify({
                        "success": True,
                        "data": stats
                    })
                    
            except Exception as redis_error:
                logger.warning(f"Error obteniendo stats de Redis: {redis_error}")
        
        # Si no hay stats en Redis, calcular desde los números
        numbers = db_manager.get_last_roulette_numbers(100)  # Últimos 100
        
        if numbers:
            red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
            black_numbers = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
            
            red_count = sum(1 for n in numbers if n['number'] in red_numbers)
            black_count = sum(1 for n in numbers if n['number'] in black_numbers)
            green_count = sum(1 for n in numbers if n['number'] == 0)
            
            stats = {
                'total_spins': len(numbers),
                'red_count': red_count,
                'black_count': black_count,
                'green_count': green_count
            }
            
            logger.info("✅ Estadísticas calculadas desde números históricos")
        
        return jsonify({
            "success": True,
            "data": stats
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/roulette/history', methods=['GET'])
def get_roulette_history():
    """Obtener historial completo de la ruleta"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Por ahora, usar el método existente
        numbers = db_manager.get_last_roulette_numbers(limit + offset)
        
        # Aplicar offset
        if offset > 0:
            numbers = numbers[offset:]
        else:
            numbers = numbers[:limit]
        
        return jsonify({
            "success": True,
            "data": numbers,
            "count": len(numbers),
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
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

# ============================================================================
# AI PREDICTION ENDPOINTS
# ============================================================================

@app.route('/api/ai/predict', methods=['POST'])
def make_prediction():
    """Crear una nueva predicción con IA"""
    try:
        data = request.get_json() or {}
        prediction_type = data.get('type', 'individual')  # individual, sector, color
        
        # Validar tipo de predicción
        if prediction_type not in ['individual', 'groups', 'sector', 'color']:
            return jsonify({
                "success": False,
                "error": "Tipo de predicción inválido. Use: individual, groups, sector, color"
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

@app.route('/api/ai/check-result', methods=['POST'])
def check_prediction_result():
    """Verificar resultado de una predicción - Análisis de victorias por grupos"""
    try:
        data = request.get_json()
        
        if not data or 'prediction_id' not in data or 'actual_number' not in data:
            return jsonify({
                "success": False,
                "error": "prediction_id y actual_number son requeridos"
            }), 400
        
        prediction_id = data['prediction_id']
        actual_number = data['actual_number']
        
        # Validar número
        if not isinstance(actual_number, int) or actual_number < 0 or actual_number > 36:
            return jsonify({
                "success": False,
                "error": "Número debe estar entre 0 y 36"
            }), 400
        
        # Obtener la predicción directamente desde Redis (SIN usar ai_predictor)
        try:
            if not db_manager.redis_client:
                return jsonify({
                    "success": False,
                    "error": "Redis no disponible"
                }), 500
            
            pred_data = db_manager.redis_client.hgetall(f"prediction:{prediction_id}")
            
            if not pred_data:
                return jsonify({
                    "success": False,
                    "error": f"Predicción {prediction_id} no encontrada"
                }), 404
            
            # Decodificar datos de la predicción
            import json
            
            # Función helper para obtener valores de Redis de forma segura
            def safe_get_redis_value(data, key, default=''):
                try:
                    value = data.get(key, default)
                    if isinstance(value, bytes):
                        return value.decode('utf-8')
                    return str(value) if value is not None else default
                except Exception as e:
                    logger.warning(f"Error obteniendo {key}: {e}")
                    return default
            
            # Obtener grupos de números predichos
            groups_str = safe_get_redis_value(pred_data, 'prediction_groups', '{}')
            try:
                groups = json.loads(groups_str)
            except json.JSONDecodeError:
                logger.error(f"Error decodificando grupos JSON: {groups_str}")
                groups = {}
            
            # Obtener otros datos de la predicción
            predicted_numbers_str = safe_get_redis_value(pred_data, 'predicted_numbers', '[]')
            try:
                predicted_numbers = json.loads(predicted_numbers_str)
            except json.JSONDecodeError:
                predicted_numbers = []
            
            prediction_type = safe_get_redis_value(pred_data, 'prediction_type', 'individual')
            
            try:
                confidence = float(safe_get_redis_value(pred_data, 'confidence', '0.0'))
            except ValueError:
                confidence = 0.0
            
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
            
            # Verificar también la predicción principal
            main_prediction_winner = actual_number in predicted_numbers
            
            # Preparar respuesta completa
            response_data = {
                "prediction_id": prediction_id,
                "actual_number": actual_number,
                "predicted_numbers": predicted_numbers,
                "prediction_type": prediction_type,
                "is_winner": main_prediction_winner,
                "overall_group_winner": overall_winner,
                "timestamp": datetime.now().isoformat(),
                "confidence": confidence,
                "group_results": group_results,
                "analysis": {
                    "total_groups": len(groups),
                    "winning_groups": sum(1 for gr in group_results if gr["is_winner"]),
                    "success_rate": f"{sum(1 for gr in group_results if gr['is_winner']) / len(groups) * 100:.1f}%" if groups else "0%"
                }
            }
            
            # Guardar el resultado en Redis para estadísticas (SIN usar ai_predictor)
            try:
                result_key = f"result:{prediction_id}"
                result_data = {
                    'prediction_id': prediction_id,
                    'actual_number': str(actual_number),
                    'is_winner': '1' if overall_winner else '0',
                    'main_prediction_winner': '1' if main_prediction_winner else '0',
                    'winning_groups': str(sum(1 for gr in group_results if gr["is_winner"])),
                    'total_groups': str(len(groups)),
                    'timestamp': datetime.now().isoformat(),
                    'verified': '1'
                }
                
                db_manager.redis_client.hset(result_key, mapping=result_data)
                db_manager.redis_client.expire(result_key, 86400 * 7)  # 7 días
                
                # Remover de predicciones pendientes
                db_manager.redis_client.lrem('ai:pending_predictions', 0, prediction_id)
                
                logger.info(f"✅ Resultado verificado para {prediction_id}: {sum(1 for gr in group_results if gr['is_winner'])}/{len(groups)} grupos ganadores")
                
            except Exception as save_error:
                logger.error(f"Error guardando resultado: {save_error}")
                # No fallar si no se puede guardar, solo continuar
            
            return jsonify({
                "success": True,
                "data": response_data
            })
            
        except Exception as e:
            logger.error(f"Error verificando resultado: {e}")
            return jsonify({
                "success": False,
                "error": f"Error procesando predicción: {str(e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error general verificando resultado: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/pending-predictions', methods=['GET'])
def get_pending_predictions():
    """Obtener predicciones pendientes"""
    try:
        pending_ids = ai_predictor.get_pending_predictions()
        
        return jsonify({
            "success": True,
            "data": {
                "pending_count": len(pending_ids),
                "pending_ids": pending_ids
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo predicciones pendientes: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/stats', methods=['GET'])
def get_ai_stats():
    """Obtener estadísticas de IA desde Redis con estadísticas detalladas"""
    try:
        if not db_manager.redis_client:
            return jsonify({
                "success": False,
                "error": "Redis no disponible"
            }), 500
        
        # Obtener estadísticas globales
        global_stats = db_manager.redis_client.hgetall("ai:game_stats")
        
        # Convertir a enteros de forma segura
        def safe_int(value, default=0):
            try:
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                return int(value) if value else default
            except (ValueError, AttributeError):
                return default
        
        total_predictions = safe_int(global_stats.get('total_predictions', 0))
        total_wins = safe_int(global_stats.get('total_wins', 0))
        total_losses = safe_int(global_stats.get('total_losses', 0))
        
        # Calcular porcentaje de éxito
        win_rate = (total_wins / total_predictions * 100) if total_predictions > 0 else 0
        
        # Obtener estadísticas por grupo
        group_names = ['group_4', 'group_6', 'group_8', 'group_9', 'group_12', 'group_15', 'group_20']
        group_stats = {}
        
        for group_name in group_names:
            group_key = f"ai:group_stats:{group_name}"
            group_data = db_manager.redis_client.hgetall(group_key)
            
            group_total = safe_int(group_data.get('total', 0))
            group_wins = safe_int(group_data.get('wins', 0))
            group_losses = safe_int(group_data.get('losses', 0))
            group_win_rate = (group_wins / group_total * 100) if group_total > 0 else 0
            
            group_stats[group_name] = {
                'total': group_total,
                'wins': group_wins,
                'losses': group_losses,
                'win_rate': round(group_win_rate, 1)
            }
        
        # Obtener predicciones pendientes
        pending_count = 0
        try:
            pending_predictions = db_manager.redis_client.llen('ai:pending_predictions')
            pending_count = pending_predictions if pending_predictions else 0
        except:
            pending_count = 0
        
        # Calcular estadísticas detalladas para columnas, docenas, par/impar, rojo/negro
        detailed_stats = calculate_detailed_stats()
        
        stats_data = {
            'total_predictions': total_predictions,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'overall_win_rate': round(win_rate, 1),
            'pending_predictions': pending_count,
            'group_stats': group_stats,
            'detailed_stats': detailed_stats,
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "data": stats_data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de IA: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def calculate_detailed_stats():
    """Calcular estadísticas detalladas para columnas, docenas, par/impar, rojo/negro"""
    try:
        if not db_manager.redis_client:
            return {}
        
        # Obtener números recientes para análisis
        recent_numbers = db_manager.get_last_roulette_numbers(100)
        
        if not recent_numbers:
            return {
                'columns': [{}, {}, {}],
                'dozens': [{}, {}, {}],
                'even': {},
                'odd': {},
                'red': {},
                'black': {}
            }
        
        # Definir números rojos
        red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        
        # Inicializar contadores
        column_stats = [{'wins': 0, 'losses': 0} for _ in range(3)]
        dozen_stats = [{'wins': 0, 'losses': 0} for _ in range(3)]
        even_stats = {'wins': 0, 'losses': 0}
        odd_stats = {'wins': 0, 'losses': 0}
        red_stats = {'wins': 0, 'losses': 0}
        black_stats = {'wins': 0, 'losses': 0}
        
        # Simular estadísticas basadas en frecuencia de aparición
        # (En un sistema real, esto vendría de predicciones verificadas)
        for number_entry in recent_numbers:
            number = number_entry['number']
            
            if number == 0:
                continue  # Ignorar el cero para estas estadísticas
            
            # Columnas (1-34: col 0, 2-35: col 1, 3-36: col 2)
            column = (number - 1) % 3
            # Simular win/loss basado en frecuencia
            if len(recent_numbers) > 0:
                column_stats[column]['wins'] += 1
            
            # Docenas
            if 1 <= number <= 12:
                dozen = 0
            elif 13 <= number <= 24:
                dozen = 1
            else:
                dozen = 2
            dozen_stats[dozen]['wins'] += 1
            
            # Par/Impar
            if number % 2 == 0:
                even_stats['wins'] += 1
            else:
                odd_stats['wins'] += 1
            
            # Rojo/Negro
            if number in red_numbers:
                red_stats['wins'] += 1
            else:
                black_stats['wins'] += 1
        
        # Calcular losses como el complemento (simulado)
        total_non_zero = len([n for n in recent_numbers if n['number'] != 0])
        
        for i in range(3):
            column_stats[i]['losses'] = max(0, total_non_zero // 3 - column_stats[i]['wins'])
            column_stats[i]['win_rate'] = round(
                (column_stats[i]['wins'] / (column_stats[i]['wins'] + column_stats[i]['losses']) * 100)
                if (column_stats[i]['wins'] + column_stats[i]['losses']) > 0 else 0, 1
            )
            
            dozen_stats[i]['losses'] = max(0, total_non_zero // 3 - dozen_stats[i]['wins'])
            dozen_stats[i]['win_rate'] = round(
                (dozen_stats[i]['wins'] / (dozen_stats[i]['wins'] + dozen_stats[i]['losses']) * 100)
                if (dozen_stats[i]['wins'] + dozen_stats[i]['losses']) > 0 else 0, 1
            )
        
        # Par/Impar
        even_stats['losses'] = max(0, total_non_zero // 2 - even_stats['wins'])
        even_stats['win_rate'] = round(
            (even_stats['wins'] / (even_stats['wins'] + even_stats['losses']) * 100)
            if (even_stats['wins'] + even_stats['losses']) > 0 else 0, 1
        )
        
        odd_stats['losses'] = max(0, total_non_zero // 2 - odd_stats['wins'])
        odd_stats['win_rate'] = round(
            (odd_stats['wins'] / (odd_stats['wins'] + odd_stats['losses']) * 100)
            if (odd_stats['wins'] + odd_stats['losses']) > 0 else 0, 1
        )
        
        # Rojo/Negro
        red_stats['losses'] = max(0, total_non_zero // 2 - red_stats['wins'])
        red_stats['win_rate'] = round(
            (red_stats['wins'] / (red_stats['wins'] + red_stats['losses']) * 100)
            if (red_stats['wins'] + red_stats['losses']) > 0 else 0, 1
        )
        
        black_stats['losses'] = max(0, total_non_zero // 2 - black_stats['wins'])
        black_stats['win_rate'] = round(
            (black_stats['wins'] / (black_stats['wins'] + black_stats['losses']) * 100)
            if (black_stats['wins'] + black_stats['losses']) > 0 else 0, 1
        )
        
        return {
            'columns': column_stats,
            'dozens': dozen_stats,
            'even': even_stats,
            'odd': odd_stats,
            'red': red_stats,
            'black': black_stats
        }
        
    except Exception as e:
        logger.error(f"Error calculando estadísticas detalladas: {e}")
        return {
            'columns': [{}, {}, {}],
            'dozens': [{}, {}, {}],
            'even': {},
            'odd': {},
            'red': {},
            'black': {}
        }

@app.route('/api/ai/auto-process', methods=['POST'])
def auto_process_prediction():
    """Procesar automáticamente: predicción -> nuevo número -> resultado"""
    try:
        data = request.get_json() or {}
        prediction_type = data.get('type', 'individual')
        new_number = data.get('number')
        
        # Validar número
        if new_number is None or not isinstance(new_number, int) or new_number < 0 or new_number > 36:
            return jsonify({
                "success": False,
                "error": "Número válido requerido (0-36)"
            }), 400
        
        # 1. Verificar predicciones pendientes antes del nuevo número
        pending_predictions = ai_predictor.get_pending_predictions()
        results = []
        
        for pred_id in pending_predictions:
            result = ai_predictor.check_prediction_result(pred_id, new_number)
            if result:
                results.append({
                    "prediction_id": result.prediction_id,
                    "is_winner": result.is_winner,
                    "predicted_numbers": result.predicted_numbers,
                    "prediction_type": result.prediction_type,
                    "confidence": result.confidence
                })
        
        # 2. Insertar el nuevo número en Redis
        insert_result = db_manager.insert_roulette_number(new_number)
        
        # 3. Hacer nueva predicción basada en el número recién insertado
        new_prediction = ai_predictor.make_prediction(prediction_type)
        
        response_data = {
            "new_number": new_number,
            "number_inserted": insert_result.get('success', False) if insert_result else False,
            "previous_results": results,
            "new_prediction": None
        }
        
        if new_prediction:
            response_data["new_prediction"] = {
                "prediction_id": new_prediction.prediction_id,
                "predicted_numbers": new_prediction.predicted_numbers,
                "prediction_groups": new_prediction.prediction_groups,
                "prediction_type": new_prediction.prediction_type,
                "confidence": new_prediction.confidence,
                "reasoning": new_prediction.reasoning
            }
        
        return jsonify({
            "success": True,
            "data": response_data
        })
        
    except Exception as e:
        logger.error(f"Error en procesamiento automático: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/predictions-csv', methods=['GET'])
def get_predictions_csv():
    """Endpoint para obtener predicciones en formato CSV (separadas por comas) para copiar fácilmente"""
    try:
        # Obtener tipo de predicción del parámetro
        prediction_type = request.args.get('type', 'groups')
        
        # Generar nueva predicción
        prediction = ai_predictor.make_prediction(prediction_type)
        
        if not prediction:
            return jsonify({
                'success': False,
                'error': 'No se pudo generar predicción'
            }), 500
        
        # Convertir cada grupo a formato CSV
        csv_predictions = {}
        compact_groups = []
        
        # Procesar grupos de predicción
        if hasattr(prediction, 'prediction_groups') and prediction.prediction_groups:
            for group_name, numbers in prediction.prediction_groups.items():
                if isinstance(numbers, list) and numbers:
                    # Ordenar números y convertir a string separado por comas
                    sorted_numbers = sorted(numbers)
                    csv_string = ','.join(map(str, sorted_numbers))
                    csv_predictions[group_name] = csv_string
                    csv_predictions[f"{group_name}_count"] = len(numbers)
                    
                    # Formato compacto para copiar
                    compact_groups.append(f"{group_name.upper()}({len(numbers)}): {csv_string}")
        
        # Procesar números principales si existen
        if hasattr(prediction, 'predicted_numbers') and prediction.predicted_numbers:
            sorted_main = sorted(prediction.predicted_numbers)
            csv_predictions['main_prediction'] = ','.join(map(str, sorted_main))
            csv_predictions['main_prediction_count'] = len(prediction.predicted_numbers)
            compact_groups.append(f"MAIN({len(prediction.predicted_numbers)}): {csv_predictions['main_prediction']}")
        
        # Crear formato de texto completo para copiar
        all_groups_text = '\n'.join(compact_groups)
        
        # Formato ultra compacto (solo números separados por |)
        compact_format = ' | '.join([
            csv_predictions.get(key, '')
            for key in csv_predictions.keys()
            if not key.endswith('_count') and csv_predictions.get(key)
        ])
        
        return jsonify({
            'success': True,
            'prediction_id': prediction.prediction_id,
            'csv_predictions': csv_predictions,
            'all_groups_text': all_groups_text,
            'compact_format': compact_format,
            'copy_ready': {
                'groups_detailed': all_groups_text,
                'numbers_only': compact_format,
                'single_line': all_groups_text.replace('\n', ' | ')
            },
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting CSV predictions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# DATA EXPORT ENDPOINTS
# ============================================================================

@app.route('/api/export/history', methods=['GET'])
def export_history():
    """Exportar historial de números a JSON"""
    try:
        limit = request.args.get('limit', 100, type=int)
        numbers = db_manager.get_last_roulette_numbers(limit)
        
        filepath = data_exporter.export_roulette_history(numbers)
        
        if filepath:
            return jsonify({
                "success": True,
                "data": {
                    "filepath": filepath,
                    "total_numbers": len(numbers),
                    "export_timestamp": datetime.now().isoformat()
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "Error exportando historial"
            }), 500
            
    except Exception as e:
        logger.error(f"Error exportando historial: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/export/stats', methods=['GET'])
def export_stats():
    """Exportar estadísticas completas a JSON"""
    try:
        # Obtener estadísticas de ruleta
        roulette_stats = {}
        if db_manager.redis_client:
            try:
                red_count = db_manager.redis_client.get('roulette:colors:red')
                black_count = db_manager.redis_client.get('roulette:colors:black')
                green_count = db_manager.redis_client.get('roulette:colors:green')
                total_spins = db_manager.redis_client.get('roulette:total_spins')
                
                roulette_stats = {
                    'colors': {
                        'red': int(str(red_count)) if red_count else 0,
                        'black': int(str(black_count)) if black_count else 0,
                        'green': int(str(green_count)) if green_count else 0
                    },
                    'total_spins': int(str(total_spins)) if total_spins else 0
                }
            except Exception as redis_error:
                logger.warning(f"Error obteniendo stats de Redis: {redis_error}")
        
        # Obtener estadísticas de IA
        ai_stats = ai_predictor.get_game_stats()
        
        # Obtener números recientes para análisis
        recent_numbers = db_manager.get_last_roulette_numbers(50)
        
        # Análisis de sectores
        sectors = {
            'voisins_zero': [22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25],
            'tiers': [27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33],
            'orphelins': [17, 34, 6, 1, 20, 14, 31, 9]
        }
        
        sector_stats = {}
        for sector_name, sector_nums in sectors.items():
            count = sum(1 for n in recent_numbers if n['number'] in sector_nums)
            sector_stats[sector_name] = {
                'count': count,
                'percentage': (count / len(recent_numbers) * 100) if recent_numbers else 0
            }
        
        # Análisis de pares/impares
        even_count = sum(1 for n in recent_numbers if n['number'] != 0 and n['number'] % 2 == 0)
        odd_count = sum(1 for n in recent_numbers if n['number'] != 0 and n['number'] % 2 == 1)
        
        complete_stats = {
            'export_timestamp': datetime.now().isoformat(),
            'roulette_stats': roulette_stats,
            'ai_stats': ai_stats,
            'recent_analysis': {
                'total_numbers_analyzed': len(recent_numbers),
                'sectors': sector_stats,
                'even_odd': {
                    'even': even_count,
                    'odd': odd_count,
                    'zero': sum(1 for n in recent_numbers if n['number'] == 0)
                }
            }
        }
        
        filepath = data_exporter.export_statistics(complete_stats)
        
        if filepath:
            return jsonify({
                "success": True,
                "data": {
                    "filepath": filepath,
                    "stats": complete_stats,
                    "export_timestamp": datetime.now().isoformat()
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "Error exportando estadísticas"
            }), 500
            
    except Exception as e:
        logger.error(f"Error exportando estadísticas: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/export/auto-save', methods=['POST'])
def auto_save_data():
    """Guardar automáticamente todos los datos importantes"""
    try:
        # Obtener datos
        numbers = db_manager.get_last_roulette_numbers(100)
        ai_stats = ai_predictor.get_game_stats()
        
        # Exportar historial
        history_file = data_exporter.export_roulette_history(numbers)
        
        # Exportar estadísticas
        stats_data = {
            'ai_performance': ai_stats,
            'numbers_count': len(numbers),
            'timestamp': datetime.now().isoformat()
        }
        stats_file = data_exporter.export_statistics(stats_data)
        
        # Limpiar archivos antiguos
        data_exporter.cleanup_old_exports(keep_count=20)
        
        return jsonify({
            "success": True,
            "data": {
                "history_file": history_file,
                "stats_file": stats_file,
                "auto_save_timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error en auto-guardado: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================================================
# REDIS MONITOR ENDPOINTS
# ============================================================================

@app.route('/api/monitor/status', methods=['GET'])
def get_monitor_status():
    """Obtener estado del monitor de Redis"""
    try:
        monitor = get_monitor()
        if monitor:
            status = monitor.get_status()
            return jsonify({
                "success": True,
                "data": status
            })
        else:
            return jsonify({
                "success": False,
                "error": "Monitor no inicializado"
            }), 500
    except Exception as e:
        logger.error(f"Error obteniendo estado del monitor: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/monitor/start', methods=['POST'])
def start_monitor():
    """Iniciar el monitor de Redis"""
    try:
        monitor = get_monitor()
        if monitor:
            monitor.start_monitoring()
            return jsonify({
                "success": True,
                "message": "Monitor iniciado exitosamente",
                "data": monitor.get_status()
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo inicializar el monitor"
            }), 500
    except Exception as e:
        logger.error(f"Error iniciando monitor: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/monitor/stop', methods=['POST'])
def stop_monitor():
    """Detener el monitor de Redis"""
    try:
        monitor = get_monitor()
        if monitor:
            monitor.stop_monitoring()
            return jsonify({
                "success": True,
                "message": "Monitor detenido exitosamente",
                "data": monitor.get_status()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Monitor no encontrado"
            }), 404
    except Exception as e:
        logger.error(f"Error deteniendo monitor: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/monitor/force-check', methods=['POST'])
def force_monitor_check():
    """Forzar una verificación manual del monitor"""
    try:
        monitor = get_monitor()
        if monitor:
            # Simular una detección manual
            insertion_data = monitor.detect_new_insertion()
            if insertion_data:
                result = monitor.process_new_insertion(insertion_data)
                return jsonify({
                    "success": True,
                    "message": "Verificación manual completada - Nueva inserción detectada",
                    "data": result
                })
            else:
                return jsonify({
                    "success": True,
                    "message": "Verificación manual completada - No hay nuevas inserciones",
                    "data": {
                        "current_length": monitor.get_current_history_length(),
                        "last_known_length": monitor.last_history_length
                    }
                })
        else:
            return jsonify({
                "success": False,
                "error": "Monitor no disponible"
            }), 500
    except Exception as e:
        logger.error(f"Error en verificación manual: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================================================
# AUTOMATION SERVICE ENDPOINTS
# ============================================================================

@app.route('/api/automation/status', methods=['GET'])
def get_automation_status():
    """Obtener estado del servicio de automatización"""
    try:
        service = get_automation_service()
        status = service.get_status()
        
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        logger.error(f"Error obteniendo estado de automatización: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/automation/start', methods=['POST'])
def start_automation():
    """Iniciar el servicio de automatización"""
    try:
        service = get_automation_service()
        
        if service.is_running:
            return jsonify({
                "success": False,
                "error": "El servicio de automatización ya está ejecutándose"
            }), 400
        
        service.start()
        
        return jsonify({
            "success": True,
            "message": "Servicio de automatización iniciado exitosamente",
            "data": service.get_status()
        })
    except Exception as e:
        logger.error(f"Error iniciando automatización: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/automation/stop', methods=['POST'])
def stop_automation():
    """Detener el servicio de automatización"""
    try:
        service = get_automation_service()
        
        if not service.is_running:
            return jsonify({
                "success": False,
                "error": "El servicio de automatización no está ejecutándose"
            }), 400
        
        service.stop()
        
        return jsonify({
            "success": True,
            "message": "Servicio de automatización detenido exitosamente",
            "data": service.get_status()
        })
    except Exception as e:
        logger.error(f"Error deteniendo automatización: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/automation/logs', methods=['GET'])
def get_automation_logs():
    """Obtener logs del servicio de automatización"""
    try:
        if not db_manager.redis_client:
            return jsonify({
                "success": False,
                "error": "Redis no disponible"
            }), 500
        
        # Obtener logs de Redis
        logs = db_manager.redis_client.lrange("automation:logs", 0, -1)
        
        # Convertir bytes a string si es necesario
        formatted_logs = []
        for log_entry in logs:
            if isinstance(log_entry, bytes):
                formatted_logs.append(log_entry.decode('utf-8'))
            else:
                formatted_logs.append(str(log_entry))
        
        return jsonify({
            "success": True,
            "data": {
                "logs": formatted_logs,
                "count": len(formatted_logs),
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Error obteniendo logs de automatización: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/automation/notifications', methods=['GET'])
def get_automation_notifications():
    """Obtener notificaciones del servicio de automatización"""
    try:
        if not db_manager.redis_client:
            return jsonify({
                "success": False,
                "error": "Redis no disponible"
            }), 500
        
        # Obtener notificaciones de Redis
        notifications_raw = db_manager.redis_client.lrange("automation:notifications", 0, -1)
        
        notifications = []
        for notif_raw in notifications_raw:
            try:
                if isinstance(notif_raw, bytes):
                    notif_str = notif_raw.decode('utf-8')
                else:
                    notif_str = str(notif_raw)
                
                notification = json.loads(notif_str)
                notifications.append(notification)
            except json.JSONDecodeError:
                continue
        
        return jsonify({
            "success": True,
            "data": {
                "notifications": notifications,
                "count": len(notifications),
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Error obteniendo notificaciones de automatización: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/automation/scraper/restart', methods=['POST'])
def restart_scraper():
    """Reiniciar solo el scraper"""
    try:
        service = get_automation_service()
        
        # Detener scraper actual
        service.stop_scraper()
        import time
        time.sleep(2)
        
        # Iniciar nuevo scraper
        success = service.start_scraper()
        
        return jsonify({
            "success": success,
            "message": "Scraper reiniciado" if success else "Error reiniciando scraper",
            "data": {
                "scraper_status": "running" if success else "stopped",
                "scraper_pid": service.scraper_process.pid if service.scraper_process else None
            }
        })
    except Exception as e:
        logger.error(f"Error reiniciando scraper: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Nuevos endpoints para el sistema automático
@app.route('/automatic-service/start', methods=['POST', 'OPTIONS'])
@cross_origin()
def start_auto_service():
    """Iniciar el servicio automático"""
    if request.method == "OPTIONS":
        return make_response()
    
    try:
        if not automatic_service_available:
            return jsonify({
                "status": "error",
                "message": "Servicio automático no disponible"
            }), 503
        
        start_automatic_service()
        
        return jsonify({
            "status": "success",
            "message": "Servicio automático iniciado correctamente"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error iniciando servicio automático: {str(e)}"
        }), 500

@app.route('/automatic-service/stop', methods=['POST', 'OPTIONS'])
@cross_origin()
def stop_auto_service():
    """Detener el servicio automático"""
    if request.method == "OPTIONS":
        return make_response()
    
    try:
        if not automatic_service_available:
            return jsonify({
                "status": "error",
                "message": "Servicio automático no disponible"
            }), 503
        
        stop_automatic_service()
        
        return jsonify({
            "status": "success",
            "message": "Servicio automático detenido correctamente"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error deteniendo servicio automático: {str(e)}"
        }), 500

@app.route('/automatic-service/status', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_auto_service_status():
    """Obtener estado del servicio automático"""
    if request.method == "OPTIONS":
        return make_response()
    
    try:
        if not automatic_service_available:
            return jsonify({
                "status": "unavailable",
                "message": "Servicio automático no disponible"
            }), 200
        
        status = get_service_status()
        
        return jsonify({
            "status": "success",
            "data": status
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error obteniendo estado: {str(e)}"
        }), 500

@app.route('/redis/latest-number', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_latest_number_redis():
    """Obtener el último número desde Redis"""
    if request.method == "OPTIONS":
        return make_response()
    
    try:
        if not redis_manager:
            return jsonify({
                "status": "error",
                "message": "Redis no disponible"
            }), 503
        
        latest_number = redis_manager.get_latest_number()
        
        if latest_number:
            return jsonify({
                "status": "success",
                "data": latest_number
            }), 200
        else:
            return jsonify({
                "status": "warning",
                "message": "No hay números disponibles en Redis"
            }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error obteniendo número de Redis: {str(e)}"
        }), 500

@app.route('/redis/predictions', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_redis_predictions():
    """Obtener predicciones activas desde Redis"""
    if request.method == "OPTIONS":
        return make_response()
    
    try:
        if not redis_manager:
            return jsonify({
                "status": "error",
                "message": "Redis no disponible"
            }), 503
        
        active_predictions = redis_manager.get_active_predictions()
        stats = redis_manager.get_stats()
        
        return jsonify({
            "status": "success",
            "data": {
                "active_predictions": active_predictions,
                "statistics": stats
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error obteniendo predicciones de Redis: {str(e)}"
        }), 500

@app.route('/redis/system-status', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_redis_system_status():
    """Obtener estado del sistema desde Redis"""
    if request.method == "OPTIONS":
        return make_response()
    
    try:
        if not redis_manager:
            return jsonify({
                "status": "error", 
                "message": "Redis no disponible"
            }), 503
        
        system_status = redis_manager.get_system_status()
        
        return jsonify({
            "status": "success",
            "data": system_status
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error obteniendo estado del sistema: {str(e)}"
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
    logger.info("🚀 Iniciando AI Casino - Roulette API (Redis Only)")

    try:
        # Verificar sistema Redis
        db_status = db_manager.get_database_status()
        if db_status['success']:
            logger.info("✅ Sistema Redis operativo")
            logger.info(f"📊 Números en historial: {db_status['estado']['total_registros']['history']}")
            logger.info(f"🎰 Total spins: {db_status['estado']['total_spins']}")
            logger.info(f"💾 Memoria Redis: {db_status['estado'].get('memory_usage', {}).get('used', 'N/A')}")
        else:
            logger.error(f"❌ Error en sistema Redis: {db_status.get('error', 'Unknown error')}")
    except Exception as e:
        logger.error(f"❌ Error verificando sistema Redis: {e}")

    try:
        # Verificar Redis connection
        if db_manager.redis_client:
            db_manager.redis_client.ping()
            logger.info("✅ Conexión a Redis exitosa")

            # Inicializar y arrancar el monitor automáticamente
            try:
                redis_monitor = initialize_monitor()
                if redis_monitor:
                    redis_monitor.start_monitoring()
                    logger.info("🔍 Monitor de Redis iniciado automáticamente")
                else:
                    logger.warning("⚠️ No se pudo inicializar el monitor de Redis")
            except Exception as monitor_error:
                logger.error(f"❌ Error iniciando monitor de Redis: {monitor_error}")
        else:
            logger.error("❌ Redis no disponible - Sistema no puede funcionar")
    except Exception as e:
        logger.error(f"❌ Redis no disponible: {e}")

    # Configurar puerto
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'

    logger.info(f"🌐 Servidor iniciando en puerto {port} (Storage: Redis Only)")
    app.run(host='0.0.0.0', port=port, debug=debug)