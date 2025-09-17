#!/usr/bin/env python3
"""
Redis Manager para el sistema de ruleta automático
Maneja la comunicación entre el scraper y el backend
"""

import redis
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisRouletteManager:
    """Gestor de Redis para el sistema de ruleta"""
    
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        """Inicializar conexión a Redis"""
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Probar conexión
            self.redis_client.ping()
            logger.info("✅ Conexión a Redis establecida correctamente")
            
        except redis.ConnectionError as e:
            logger.error(f"❌ Error conectando a Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error inesperado con Redis: {e}")
            raise
    
    def get_latest_number(self) -> Optional[Dict]:
        """Obtener el número más reciente desde Redis"""
        try:
            # Intentar obtener el número más reciente (clave usada por el scraper)
            latest_number = self.redis_client.get("roulette:latest")
            
            if latest_number:
                # Obtener metadatos adicionales
                stats = self.redis_client.hgetall("roulette:stats")
                
                # Construir respuesta compatible
                data = {
                    'number': int(latest_number),
                    'color': stats.get('latest_color', 'unknown'),
                    'timestamp': stats.get('last_update', datetime.now().isoformat())
                }
                
                logger.info(f"📥 Número obtenido de Redis: {data['number']}")
                return data
            
            logger.warning("⚠️ No hay números en Redis")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo número de Redis: {e}")
            return None
    
    def get_number_history(self, limit: int = 50) -> List[Dict]:
        """Obtener historial de números desde Redis"""
        try:
            # Obtener lista de números ordenada por tiempo
            numbers_data = self.redis_client.lrange("roulette:history", 0, limit - 1)
            
            history = []
            for number_json in numbers_data:
                try:
                    number_data = json.loads(number_json)
                    history.append(number_data)
                except json.JSONDecodeError:
                    continue
            
            logger.info(f"📋 Historial obtenido: {len(history)} números")
            return history
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo historial de Redis: {e}")
            return []
    
    def wait_for_new_number(self, timeout: int = 30) -> Optional[Dict]:
        """Esperar por un nuevo número usando pub/sub"""
        try:
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe("roulette:new_number")
            
            logger.info(f"👂 Esperando nuevo número (timeout: {timeout}s)...")
            
            # Esperar por mensajes
            message = pubsub.get_message(timeout=timeout)
            
            if message and message['type'] == 'message':
                data = json.loads(message['data'])
                logger.info(f"🆕 Nuevo número recibido: {data['number']}")
                pubsub.close()
                return data
            
            logger.warning("⏰ Timeout esperando nuevo número")
            pubsub.close()
            return None
            
        except Exception as e:
            logger.error(f"❌ Error esperando nuevo número: {e}")
            return None
    
    def store_prediction(self, prediction_data: Dict) -> bool:
        """Almacenar predicción en Redis"""
        try:
            # Generar ID único para la predicción
            prediction_id = f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Agregar timestamp y ID
            prediction_data['id'] = prediction_id
            prediction_data['timestamp'] = datetime.now().isoformat()
            prediction_data['status'] = 'pending'  # pending, win, lose
            
            # Guardar predicción
            self.redis_client.setex(
                f"roulette:prediction:{prediction_id}",
                timedelta(hours=1),  # Expira en 1 hora
                json.dumps(prediction_data)
            )
            
            # Agregar a lista de predicciones activas
            self.redis_client.lpush("roulette:active_predictions", prediction_id)
            
            logger.info(f"💾 Predicción almacenada: {prediction_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error almacenando predicción: {e}")
            return False
    
    def get_active_predictions(self) -> List[Dict]:
        """Obtener predicciones activas"""
        try:
            # Buscar predicciones pendientes (clave usada por el sistema de IA)
            prediction_ids = self.redis_client.lrange("ai:pending_predictions", 0, -1)
            predictions = []
            
            for pred_id in prediction_ids:
                # Buscar en la clave correcta usada por el sistema
                pred_data = self.redis_client.hgetall(f"prediction:{pred_id}")
                if pred_data:
                    # Convertir datos de Redis a formato JSON
                    prediction = {}
                    for key, value in pred_data.items():
                        if isinstance(value, bytes):
                            value = value.decode('utf-8')
                        
                        # Intentar parsear JSON para campos complejos
                        if key in ['prediction_groups', 'predicted_numbers']:
                            try:
                                prediction[key] = json.loads(value)
                            except:
                                prediction[key] = value
                        else:
                            prediction[key] = value
                    
                    predictions.append(prediction)
            
            logger.info(f"📋 Predicciones activas obtenidas: {len(predictions)}")
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo predicciones activas: {e}")
            return []
    
    def update_prediction_result(self, prediction_id: str, result_number: int, is_win: bool) -> bool:
        """Actualizar resultado de predicción"""
        try:
            pred_key = f"roulette:prediction:{prediction_id}"
            pred_data = self.redis_client.get(pred_key)
            
            if pred_data:
                prediction = json.loads(pred_data)
                prediction['result_number'] = result_number
                prediction['status'] = 'win' if is_win else 'lose'
                prediction['result_timestamp'] = datetime.now().isoformat()
                
                # Actualizar en Redis
                self.redis_client.setex(pred_key, timedelta(hours=24), json.dumps(prediction))
                
                # Remover de predicciones activas
                self.redis_client.lrem("roulette:active_predictions", 1, prediction_id)
                
                # Agregar a estadísticas
                self._update_stats(is_win)
                
                logger.info(f"📊 Predicción {prediction_id} actualizada: {'WIN' if is_win else 'LOSE'}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error actualizando predicción: {e}")
            return False
    
    def _update_stats(self, is_win: bool):
        """Actualizar estadísticas de predicciones"""
        try:
            if is_win:
                self.redis_client.incr("roulette:stats:wins")
            else:
                self.redis_client.incr("roulette:stats:losses")
            
            self.redis_client.incr("roulette:stats:total_predictions")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando estadísticas: {e}")
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas de predicciones"""
        try:
            # Obtener estadísticas del sistema de IA
            ai_stats = self.redis_client.hgetall("ai:game_stats")
            
            # Convertir valores de forma segura
            def safe_int(value, default=0):
                try:
                    if isinstance(value, bytes):
                        value = value.decode('utf-8')
                    return int(value) if value else default
                except (ValueError, AttributeError):
                    return default
            
            total_predictions = safe_int(ai_stats.get('total_predictions', 0))
            total_wins = safe_int(ai_stats.get('total_wins', 0))
            total_losses = safe_int(ai_stats.get('total_losses', 0))
            
            # Obtener estadísticas de ruleta también
            roulette_stats = self.redis_client.hgetall("roulette:stats")
            
            stats = {
                'wins': total_wins,
                'losses': total_losses,
                'total_predictions': total_predictions,
                'win_rate': (total_wins / total_predictions * 100) if total_predictions > 0 else 0,
                'latest_number': roulette_stats.get('latest_number', 'N/A'),
                'latest_color': roulette_stats.get('latest_color', 'N/A'),
                'total_spins': safe_int(self.redis_client.get("roulette:total_spins"), 0),
                'last_update': roulette_stats.get('last_update', 'N/A')
            }
            
            logger.info(f"📊 Estadísticas obtenidas: {stats['total_predictions']} predicciones, {stats['wins']} aciertos")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {
                'wins': 0, 
                'losses': 0, 
                'total_predictions': 0, 
                'win_rate': 0,
                'latest_number': 'N/A',
                'latest_color': 'N/A',
                'total_spins': 0,
                'last_update': 'N/A'
            }
    
    def set_system_status(self, status: str, message: str = ""):
        """Establecer estado del sistema"""
        try:
            status_data = {
                'status': status,  # 'running', 'stopped', 'error'
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            self.redis_client.setex(
                "roulette:system_status",
                timedelta(minutes=5),
                json.dumps(status_data)
            )
            
            logger.info(f"📡 Estado del sistema: {status}")
            
        except Exception as e:
            logger.error(f"❌ Error estableciendo estado del sistema: {e}")
    
    def get_system_status(self) -> Dict:
        """Obtener estado del sistema"""
        try:
            status_data = self.redis_client.get("roulette:system_status")
            if status_data:
                return json.loads(status_data)
            
            return {
                'status': 'unknown',
                'message': 'Estado no disponible',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado del sistema: {e}")
            return {
                'status': 'error',
                'message': f'Error de conexión: {e}',
                'timestamp': datetime.now().isoformat()
            }
    
    def close(self):
        """Cerrar conexión a Redis"""
        try:
            self.redis_client.close()
            logger.info("🔌 Conexión a Redis cerrada")
        except Exception as e:
            logger.error(f"❌ Error cerrando conexión a Redis: {e}")


# Instancia global para ser usada por el backend
redis_manager = None

def get_redis_manager() -> RedisRouletteManager:
    """Obtener instancia global de Redis Manager"""
    global redis_manager
    
    if redis_manager is None:
        try:
            # Intentar usar URL completa de Redis primero
            redis_url = (
                os.getenv('REDIS_PUBLIC_URL') or
                os.getenv('Connection_redis') or
                os.getenv('REDIS_URL') or
                'redis://default:kuBKgwJxPrMoMOWqpobsGZIcpgnOFwoW@ballast.proxy.rlwy.net:58381'
            )
            
            # Crear cliente Redis desde URL
            redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Crear instancia personalizada del manager
            redis_manager = RedisRouletteManager.__new__(RedisRouletteManager)
            redis_manager.redis_client = redis_client
            
            # Probar conexión
            redis_manager.redis_client.ping()
            logger.info("✅ Redis Manager inicializado con URL completa")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Redis Manager: {e}")
            raise
    
    return redis_manager 