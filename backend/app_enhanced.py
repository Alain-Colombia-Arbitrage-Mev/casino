#!/usr/bin/env python3
"""
AI Casino - Enhanced Roulette Application
Backend API con Redis Enhanced + XGBoost ML Predictions
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Imports del sistema enhanced
from database_redis_enhanced import enhanced_db_manager
from xgboost_predictor import XGBoostRoulettePredictor, get_xgboost_status

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
CORS(app)

# Configuración
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'enhanced-secret-key')

# Inicializar predictores
xgb_predictor = XGBoostRoulettePredictor(enhanced_db_manager.redis_client)

@app.route('/')
def index():
    """Página principal enhanced"""
    return jsonify({
        "message": "AI Casino - Enhanced Roulette API",
        "version": "3.0.0",
        "database": "Redis Enhanced + Analytics + ML",
        "status": "running",
        "storage_type": "redis_enhanced",
        "ml_features": ["XGBoost", "Feature Engineering", "Pattern Analytics"]
    })

@app.route('/health')
def health():
    """Endpoint de salud enhanced"""
    try:
        # Verificar estado del sistema enhanced
        db_status = enhanced_db_manager.get_database_status()

        # Estado de XGBoost
        xgb_status = get_xgboost_status(enhanced_db_manager.redis_client)

        # Verificar conexión Redis
        redis_status = False
        redis_info = {}
        try:
            if enhanced_db_manager.redis_client:
                enhanced_db_manager.redis_client.ping()
                redis_status = True
                info = enhanced_db_manager.redis_client.info()
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
            "storage_type": "redis_enhanced",
            "redis": {
                "connected": redis_status,
                "info": redis_info
            },
            "system_status": db_status,
            "ml_status": xgb_status
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/api/roulette/numbers', methods=['GET'])
def get_roulette_numbers():
    """Obtener números con enhanced analytics"""
    try:
        limit = request.args.get('limit', 20, type=int)
        numbers = enhanced_db_manager.get_enhanced_roulette_numbers(limit)

        return jsonify({
            "success": True,
            "data": numbers,
            "count": len(numbers),
            "analytics_available": True
        })
    except Exception as e:
        logger.error(f"Error obteniendo números: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/roulette/numbers', methods=['POST'])
def add_roulette_number_enhanced():
    """Agregar número con enhanced analytics y ML features"""
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
            if enhanced_db_manager.redis_client:
                pending_predictions = enhanced_db_manager.redis_client.lrange('ai:pending_predictions', 0, -1)

                for pred_id in pending_predictions:
                    result = verify_prediction_enhanced(pred_id, number)
                    if result:
                        pending_results.append(result)

                logger.info(f"Verificadas {len(pending_results)} predicciones pendientes para número {number}")

        except Exception as verify_error:
            logger.error(f"Error verificando predicciones: {verify_error}")

        # 2. Insertar número con enhanced analytics
        insert_result = enhanced_db_manager.insert_roulette_number_enhanced(number)

        if insert_result and insert_result.get('success'):
            # 3. Auto-entrenar XGBoost con estrategias optimizadas
            try:
                xgb_predictor.auto_train_with_strategies()
            except Exception as train_error:
                logger.warning(f"Auto-training with strategies error: {train_error}")
                # Fallback al entrenamiento tradicional
                try:
                    xgb_predictor.auto_train_if_needed()
                except Exception as fallback_error:
                    logger.warning(f"Fallback auto-training error: {fallback_error}")

            # 4. Generar nueva predicción XGBoost
            new_prediction = None
            try:
                new_prediction = xgb_predictor.make_advanced_prediction('xgboost')
                if new_prediction:
                    logger.info(f"Nueva predicción XGBoost generada: {new_prediction.prediction_id}")
            except Exception as pred_error:
                logger.error(f"Error generando predicción XGBoost: {pred_error}")

            # 5. Obtener analytics summary
            analytics_summary = enhanced_db_manager.get_analytics_summary()

            # 6. Preparar respuesta enhanced
            response_data = {
                "number_data": insert_result.get('data', {}),
                "verified_predictions": len(pending_results),
                "prediction_results": pending_results,
                "new_prediction_generated": new_prediction is not None,
                "analytics_summary": analytics_summary
            }

            if new_prediction:
                response_data["new_prediction"] = {
                    "prediction_id": new_prediction.prediction_id,
                    "prediction_groups": new_prediction.prediction_groups,
                    "confidence": new_prediction.confidence,
                    "reasoning": new_prediction.reasoning,
                    "model_used": new_prediction.model_used,
                    "probabilities": dict(list(new_prediction.probabilities.items())[:10])  # Top 10 prob
                }

            return jsonify({
                "success": True,
                "message": "Número agregado con enhanced analytics exitosamente",
                "data": response_data
            })
        else:
            error_msg = insert_result.get('error') if insert_result else "Error desconocido"
            return jsonify({
                "success": False,
                "error": error_msg
            }), 500

    except Exception as e:
        logger.error(f"Error agregando número enhanced: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def verify_prediction_enhanced(prediction_id, actual_number):
    """Función enhanced para verificar predicción"""
    try:
        if not enhanced_db_manager.redis_client:
            return None

        pred_data = enhanced_db_manager.redis_client.hgetall(f"prediction:{prediction_id}")

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

        # Actualizar estadísticas enhanced
        try:
            stats_key = "ai:game_stats"
            enhanced_db_manager.redis_client.hincrby(stats_key, "total_predictions", 1)

            if overall_winner:
                enhanced_db_manager.redis_client.hincrby(stats_key, "total_wins", 1)
            else:
                enhanced_db_manager.redis_client.hincrby(stats_key, "total_losses", 1)

            # Remover de predicciones pendientes
            enhanced_db_manager.redis_client.lrem('ai:pending_predictions', 0, prediction_id)

        except Exception as stats_error:
            logger.error(f"Error actualizando estadísticas: {stats_error}")

        return {
            "prediction_id": prediction_id,
            "actual_number": actual_number,
            "overall_winner": overall_winner,
            "group_results": group_results,
            "model_used": pred_data.get('model_used', 'unknown'),
            "analysis": {
                "total_groups": len(groups),
                "winning_groups": sum(1 for gr in group_results if gr["is_winner"]),
                "success_rate": f"{sum(1 for gr in group_results if gr['is_winner']) / len(groups) * 100:.1f}%" if groups else "0%"
            }
        }

    except Exception as e:
        logger.error(f"Error verificando predicción enhanced {prediction_id}: {e}")
        return None

@app.route('/api/ai/predict-xgboost', methods=['POST'])
def make_xgboost_prediction():
    """Crear predicción usando XGBoost"""
    try:
        data = request.get_json() or {}
        prediction_type = data.get('type', 'xgboost')

        # Hacer predicción XGBoost
        prediction = xgb_predictor.make_advanced_prediction(prediction_type)

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
                    "reasoning": prediction.reasoning,
                    "model_used": prediction.model_used,
                    "feature_importance": prediction.feature_importance,
                    "probabilities": dict(list(prediction.probabilities.items())[:15])  # Top 15
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo generar predicción XGBoost"
            }), 500

    except Exception as e:
        logger.error(f"Error en predicción XGBoost: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ml/train-xgboost', methods=['POST'])
def train_xgboost_model():
    """Entrenar modelo XGBoost manualmente"""
    try:
        data = request.get_json() or {}
        retrain = data.get('retrain', False)

        success = xgb_predictor.train_xgboost_model(retrain=retrain)

        if success:
            # Obtener metadata del modelo
            metadata = enhanced_db_manager.redis_client.hgetall('ml:models:metadata')

            return jsonify({
                "success": True,
                "message": "Modelo XGBoost entrenado exitosamente",
                "model_metadata": metadata
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo entrenar el modelo XGBoost"
            }), 500

    except Exception as e:
        logger.error(f"Error entrenando XGBoost: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ml/status', methods=['GET'])
def get_ml_status():
    """Obtener estado del sistema ML"""
    try:
        xgb_status = get_xgboost_status(enhanced_db_manager.redis_client)
        analytics_summary = enhanced_db_manager.get_analytics_summary()

        return jsonify({
            "success": True,
            "data": {
                "xgboost_status": xgb_status,
                "analytics_summary": analytics_summary,
                "feature_extraction_active": True
            }
        })

    except Exception as e:
        logger.error(f"Error obteniendo estado ML: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/analytics/summary', methods=['GET'])
def get_analytics_summary():
    """Obtener resumen completo de analytics"""
    try:
        summary = enhanced_db_manager.get_analytics_summary()

        return jsonify({
            "success": True,
            "data": summary
        })

    except Exception as e:
        logger.error(f"Error obteniendo analytics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ml/features', methods=['GET'])
def get_ml_features():
    """Obtener features de ML"""
    try:
        limit = request.args.get('limit', 50, type=int)
        features_history = enhanced_db_manager.get_ml_features_history(limit)

        return jsonify({
            "success": True,
            "data": {
                "features_history": features_history,
                "count": len(features_history)
            }
        })

    except Exception as e:
        logger.error(f"Error obteniendo features ML: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/database/status', methods=['GET'])
def database_status_enhanced():
    """Obtener estado enhanced de la base de datos"""
    try:
        status = enhanced_db_manager.get_database_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/predict-ensemble', methods=['POST'])
def make_ensemble_prediction():
    """Crear predicción usando ensemble de modelos optimizados"""
    try:
        data = request.get_json() or {}
        prediction_type = data.get('type', 'ensemble')

        # Hacer predicción ensemble
        prediction = xgb_predictor.make_ensemble_prediction(prediction_type)

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
                    "reasoning": prediction.reasoning,
                    "model_used": prediction.model_used,
                    "feature_importance": prediction.feature_importance,
                    "probabilities": dict(list(prediction.probabilities.items())[:15])  # Top 15
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo generar predicción ensemble"
            }), 500

    except Exception as e:
        logger.error(f"Error en predicción ensemble: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/strategy-optimization', methods=['POST'])
def trigger_strategy_optimization():
    """Trigger manual de optimización de estrategias"""
    try:
        data = request.get_json() or {}
        force = data.get('force', False)

        # Ejecutar optimización
        success = xgb_predictor.trigger_strategy_optimization(force=force)

        if success:
            return jsonify({
                "success": True,
                "message": "Optimización de estrategias ejecutada exitosamente"
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo ejecutar la optimización de estrategias"
            }), 500

    except Exception as e:
        logger.error(f"Error en optimización de estrategias: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/strategy-performance', methods=['GET'])
def get_strategy_performance():
    """Obtener resumen del rendimiento de estrategias"""
    try:
        performance_summary = xgb_predictor.get_strategy_performance_summary()

        return jsonify({
            "success": True,
            "data": performance_summary
        })

    except Exception as e:
        logger.error(f"Error obteniendo rendimiento de estrategias: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/auto-retrain', methods=['POST'])
def trigger_auto_retrain():
    """Trigger manual de auto-entrenamiento con estrategias"""
    try:
        data = request.get_json() or {}
        force = data.get('force', False)

        # Ejecutar auto-entrenamiento
        success = xgb_predictor.auto_train_with_strategies(force_retrain=force)

        if success:
            return jsonify({
                "success": True,
                "message": "Auto-entrenamiento con estrategias completado exitosamente"
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo completar el auto-entrenamiento"
            }), 500

    except Exception as e:
        logger.error(f"Error en auto-entrenamiento: {e}")
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
    # Verificar conexiones al iniciar (Enhanced Redis + ML)
    logger.info("Iniciando AI Casino - Enhanced Roulette API")

    try:
        # Verificar sistema Redis Enhanced
        db_status = enhanced_db_manager.get_database_status()
        if db_status['success']:
            logger.info("Sistema Redis Enhanced operativo")
            logger.info(f"Números en historial: {db_status['estado']['total_registros']['history']}")
            logger.info(f"Total spins: {db_status['estado']['total_spins']}")
            logger.info(f"Session ID: {db_status['estado']['session_id']}")

            # Analytics status
            analytics = db_status['estado'].get('analytics_status', {})
            if analytics:
                ml_status = analytics.get('ml_status', {})
                logger.info(f"ML Features disponibles: {ml_status.get('features_available', 0)}")
                logger.info(f"Listo para training: {ml_status.get('ready_for_training', False)}")
        else:
            logger.error(f"Error en sistema Redis Enhanced: {db_status.get('error', 'Unknown error')}")
    except Exception as e:
        logger.error(f"Error verificando sistema Redis Enhanced: {e}")

    try:
        # Verificar XGBoost
        xgb_status = get_xgboost_status(enhanced_db_manager.redis_client)
        logger.info(f"XGBoost disponible: {xgb_status.get('xgboost_available', False)}")
        logger.info(f"Modelo entrenado: {xgb_status.get('model_trained', False)}")
        logger.info(f"Listo para predicción: {xgb_status.get('ready_for_prediction', False)}")

        # Auto-entrenar si es necesario
        try:
            xgb_predictor.auto_train_if_needed()
        except Exception as train_error:
            logger.warning(f"Auto-training inicial falló: {train_error}")

    except Exception as e:
        logger.error(f"Error verificando XGBoost: {e}")

    # Configurar puerto
    port = int(os.getenv('PORT', 5001))  # Puerto diferente para enhanced
    debug = os.getenv('FLASK_ENV') == 'development'

    logger.info(f"Servidor Enhanced iniciando en puerto {port}")
    logger.info("Features: Redis Enhanced + XGBoost + Analytics + ML Pipeline")
    app.run(host='0.0.0.0', port=port, debug=debug)