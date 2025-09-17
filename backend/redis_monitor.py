#!/usr/bin/env python3
"""
Redis Monitor - Sistema de detección automática de nuevas inserciones
Monitorea cambios en Redis y ejecuta verificaciones automáticas
"""

import redis
import json
import time
import threading
import logging
from datetime import datetime
from typing import Callable, Optional
from database import db_manager
from ai_predictor import RouletteAIPredictor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisMonitor:
    def __init__(self, redis_client, ai_predictor):
        self.redis_client = redis_client
        self.ai_predictor = ai_predictor
        self.monitoring = False
        self.monitor_thread = None
        self.last_history_length = 0
        self.callbacks = []
        
    def add_callback(self, callback: Callable):
        """Agregar callback para ejecutar cuando se detecte una nueva inserción"""
        self.callbacks.append(callback)
    
    def get_current_history_length(self) -> int:
        """Obtener la longitud actual del historial"""
        try:
            return self.redis_client.llen('roulette:history') or 0
        except Exception as e:
            logger.error(f"Error obteniendo longitud del historial: {e}")
            return 0
    
    def get_latest_number(self) -> Optional[int]:
        """Obtener el último número insertado"""
        try:
            latest = self.redis_client.lindex('roulette:history', 0)
            if latest:
                return int(latest)
            return None
        except Exception as e:
            logger.error(f"Error obteniendo último número: {e}")
            return None
    
    def detect_new_insertion(self) -> Optional[dict]:
        """Detectar si hay una nueva inserción comparando la longitud del historial"""
        current_length = self.get_current_history_length()
        
        if current_length > self.last_history_length:
            # Nueva inserción detectada
            latest_number = self.get_latest_number()
            
            if latest_number is not None:
                insertion_data = {
                    'number': latest_number,
                    'timestamp': datetime.now().isoformat(),
                    'previous_length': self.last_history_length,
                    'current_length': current_length,
                    'new_insertions': current_length - self.last_history_length
                }
                
                # Actualizar la longitud conocida
                self.last_history_length = current_length
                
                logger.info(f"🔔 Nueva inserción detectada: {latest_number} (longitud: {self.last_history_length} -> {current_length})")
                return insertion_data
        
        return None
    
    def verify_pending_predictions(self, number: int) -> list:
        """Verificar predicciones pendientes contra un número"""
        try:
            if not self.redis_client:
                return []
            
            # Obtener predicciones pendientes
            pending_predictions = self.redis_client.lrange('ai:pending_predictions', 0, -1)
            results = []
            
            for pred_id_bytes in pending_predictions:
                pred_id = pred_id_bytes.decode('utf-8') if isinstance(pred_id_bytes, bytes) else str(pred_id_bytes)
                
                # Verificar cada predicción pendiente
                result = self.verify_prediction_against_number(pred_id, number)
                if result:
                    results.append(result)
            
            logger.info(f"✅ Verificadas {len(results)} predicciones pendientes automáticamente para número {number}")
            return results
            
        except Exception as e:
            logger.error(f"Error verificando predicciones pendientes: {e}")
            return []
    
    def verify_prediction_against_number(self, prediction_id: str, actual_number: int):
        """Verificar una predicción específica contra un número"""
        try:
            if not self.redis_client:
                return None
                
            pred_data = self.redis_client.hgetall(f"prediction:{prediction_id}")
            
            if not pred_data:
                return None
            
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
                self.redis_client.hincrby(stats_key, "total_predictions", 1)
                
                if overall_winner:
                    self.redis_client.hincrby(stats_key, "total_wins", 1)
                else:
                    self.redis_client.hincrby(stats_key, "total_losses", 1)
                
                # Actualizar estadísticas por grupo
                for group_result in group_results:
                    group_key = f"ai:group_stats:{group_result['group_name']}"
                    self.redis_client.hincrby(group_key, "total", 1)
                    
                    if group_result['is_winner']:
                        self.redis_client.hincrby(group_key, "wins", 1)
                    else:
                        self.redis_client.hincrby(group_key, "losses", 1)
                
                # Guardar resultado específico
                result_key = f"result:{prediction_id}"
                result_data = {
                    'prediction_id': prediction_id,
                    'actual_number': str(actual_number),
                    'is_winner': '1' if overall_winner else '0',
                    'winning_groups': str(sum(1 for gr in group_results if gr["is_winner"])),
                    'total_groups': str(len(groups)),
                    'timestamp': datetime.now().isoformat(),
                    'verified': '1',
                    'auto_detected': '1'  # Marcar como detectado automáticamente
                }
                
                self.redis_client.hset(result_key, mapping=result_data)
                self.redis_client.expire(result_key, 86400 * 7)  # 7 días
                
                # Remover de predicciones pendientes
                self.redis_client.lrem('ai:pending_predictions', 0, prediction_id)
                
                logger.info(f"✅ Estadísticas actualizadas automáticamente para {prediction_id}: {sum(1 for gr in group_results if gr['is_winner'])}/{len(groups)} grupos ganadores")
                
            except Exception as stats_error:
                logger.error(f"Error actualizando estadísticas automáticamente: {stats_error}")
            
            return {
                "prediction_id": prediction_id,
                "actual_number": actual_number,
                "overall_winner": overall_winner,
                "group_results": group_results,
                "analysis": {
                    "total_groups": len(groups),
                    "winning_groups": sum(1 for gr in group_results if gr["is_winner"]),
                    "success_rate": f"{sum(1 for gr in group_results if gr['is_winner']) / len(groups) * 100:.1f}%" if groups else "0%"
                },
                "auto_detected": True
            }
            
        except Exception as e:
            logger.error(f"Error verificando predicción automáticamente {prediction_id}: {e}")
            return None
    
    def generate_new_prediction(self) -> Optional[dict]:
        """Generar una nueva predicción automáticamente"""
        try:
            prediction = self.ai_predictor.make_prediction('groups')
            if prediction:
                logger.info(f"✅ Nueva predicción generada automáticamente: {prediction.prediction_id}")
                return {
                    "prediction_id": prediction.prediction_id,
                    "prediction_groups": prediction.prediction_groups,
                    "confidence": prediction.confidence,
                    "reasoning": prediction.reasoning
                }
            return None
        except Exception as e:
            logger.error(f"Error generando nueva predicción automáticamente: {e}")
            return None
    
    def process_new_insertion(self, insertion_data: dict):
        """Procesar una nueva inserción detectada"""
        number = insertion_data['number']
        timestamp = insertion_data['timestamp']
        
        logger.info(f"🔄 Procesando nueva inserción automática: {number} a las {timestamp}")
        
        # 1. Verificar predicciones pendientes
        verification_results = self.verify_pending_predictions(number)
        
        # 2. Generar nueva predicción
        new_prediction = self.generate_new_prediction()
        
        # 3. Ejecutar callbacks personalizados
        for callback in self.callbacks:
            try:
                callback(insertion_data, verification_results, new_prediction)
            except Exception as e:
                logger.error(f"Error ejecutando callback: {e}")
        
        # 4. Log del resumen
        logger.info(f"📊 Procesamiento automático completado:")
        logger.info(f"   - Número: {number}")
        logger.info(f"   - Predicciones verificadas: {len(verification_results)}")
        logger.info(f"   - Nueva predicción: {'✅' if new_prediction else '❌'}")
        
        return {
            'insertion_data': insertion_data,
            'verification_results': verification_results,
            'new_prediction': new_prediction,
            'processed_at': datetime.now().isoformat()
        }
    
    def monitor_loop(self):
        """Loop principal de monitoreo"""
        logger.info("🔍 Iniciando monitoreo automático de Redis...")
        
        # Inicializar la longitud actual
        self.last_history_length = self.get_current_history_length()
        logger.info(f"📊 Longitud inicial del historial: {self.last_history_length}")
        
        while self.monitoring:
            try:
                # Detectar nuevas inserciones
                insertion_data = self.detect_new_insertion()
                
                if insertion_data:
                    # Procesar la nueva inserción
                    self.process_new_insertion(insertion_data)
                
                # Esperar antes de la siguiente verificación
                time.sleep(2)  # Verificar cada 2 segundos
                
            except Exception as e:
                logger.error(f"Error en el loop de monitoreo: {e}")
                time.sleep(5)  # Esperar más tiempo en caso de error
    
    def start_monitoring(self):
        """Iniciar el monitoreo en un hilo separado"""
        if self.monitoring:
            logger.warning("⚠️ El monitoreo ya está activo")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🚀 Monitoreo automático iniciado")
    
    def stop_monitoring(self):
        """Detener el monitoreo"""
        if not self.monitoring:
            logger.warning("⚠️ El monitoreo no está activo")
            return
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 Monitoreo automático detenido")
    
    def get_status(self) -> dict:
        """Obtener el estado actual del monitor"""
        return {
            'monitoring': self.monitoring,
            'last_history_length': self.last_history_length,
            'current_history_length': self.get_current_history_length(),
            'callbacks_count': len(self.callbacks),
            'thread_alive': self.monitor_thread.is_alive() if self.monitor_thread else False
        }

# Instancia global del monitor
redis_monitor = None

def initialize_monitor():
    """Inicializar el monitor global"""
    global redis_monitor
    if redis_monitor is None and db_manager.redis_client:
        ai_predictor = RouletteAIPredictor(db_manager.redis_client)
        redis_monitor = RedisMonitor(db_manager.redis_client, ai_predictor)
        logger.info("✅ Monitor de Redis inicializado")
    return redis_monitor

def get_monitor():
    """Obtener la instancia del monitor"""
    global redis_monitor
    if redis_monitor is None:
        return initialize_monitor()
    return redis_monitor