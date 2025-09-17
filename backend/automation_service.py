#!/usr/bin/env python3
"""
Servicio de Automatización para AI Casino
Coordina el scraper, detección de números, predicciones y frontend
"""

import os
import sys
import time
import json
import threading
import subprocess
import logging
from datetime import datetime, timedelta
from database import db_manager
from ai_predictor import RouletteAIPredictor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomationService:
    """Servicio principal de automatización"""
    
    def __init__(self):
        self.redis_client = db_manager.redis_client
        self.ai_predictor = RouletteAIPredictor(self.redis_client)
        self.scraper_process = None
        self.monitoring_thread = None
        self.is_running = False
        self.last_known_number = None
        self.last_check_time = datetime.now()
        
        # Cargar configuración específica de automatización
        self.load_automation_config()
        
        # Configuración
        self.check_interval = int(os.getenv('AUTOMATION_CHECK_INTERVAL', '5'))  # segundos
        self.auto_predict = os.getenv('AUTO_PREDICT', 'true').lower() == 'true'
        self.scraper_enabled = os.getenv('SCRAPER_ENABLED', 'false').lower() == 'true'  # Por defecto false
        
        logger.info("🤖 Servicio de Automatización inicializado")
    
    def load_automation_config(self):
        """Cargar configuración específica de automatización"""
        try:
            from dotenv import load_dotenv
            
            # Cargar archivo de configuración específico
            automation_env = os.path.join(os.path.dirname(__file__), '.env.automation')
            if os.path.exists(automation_env):
                load_dotenv(automation_env, override=True)
                logger.info("✅ Configuración de automatización cargada")
            else:
                logger.warning("⚠️ Archivo .env.automation no encontrado, usando valores por defecto")
                
        except Exception as e:
            logger.error(f"❌ Error cargando configuración de automatización: {e}")
    
    def log_event(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [AUTOMATION] [{level}] {message}"
        print(log_entry)
        
        # También guardar en Redis para el frontend
        if self.redis_client:
            try:
                self.redis_client.lpush("automation:logs", log_entry)
                self.redis_client.ltrim("automation:logs", 0, 99)  # Mantener últimos 100
            except Exception as e:
                print(f"Error guardando log en Redis: {e}")
    
    def start_scraper(self):
        """Iniciar el scraper en proceso separado"""
        if not self.scraper_enabled:
            self.log_event("⚠️ Scraper deshabilitado por configuración")
            return False
        
        try:
            scraper_path = os.path.join("scrapping", "scraper_final.py")
            
            if not os.path.exists(scraper_path):
                self.log_event(f"❌ Scraper no encontrado: {scraper_path}", "ERROR")
                return False
            
            self.log_event("🚀 Iniciando scraper...")
            
            # Ejecutar scraper en proceso separado
            self.scraper_process = subprocess.Popen(
                [sys.executable, scraper_path],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.log_event(f"✅ Scraper iniciado con PID: {self.scraper_process.pid}")
            return True
            
        except Exception as e:
            self.log_event(f"❌ Error iniciando scraper: {e}", "ERROR")
            return False
    
    def stop_scraper(self):
        """Detener el scraper"""
        if self.scraper_process:
            try:
                self.scraper_process.terminate()
                self.scraper_process.wait(timeout=10)
                self.log_event("🛑 Scraper detenido")
            except subprocess.TimeoutExpired:
                self.scraper_process.kill()
                self.log_event("🔪 Scraper forzado a cerrar")
            except Exception as e:
                self.log_event(f"❌ Error deteniendo scraper: {e}", "ERROR")
            finally:
                self.scraper_process = None
    
    def is_scraper_running(self):
        """Verificar si hay un scraper corriendo (propio o externo)"""
        try:
            import psutil
            
            # Buscar procesos que contengan 'scraper' o 'simple_scraper'
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'scraper' in cmdline.lower() and 'python' in cmdline.lower():
                        # Verificar que no sea nuestro propio proceso
                        if self.scraper_process and proc.info['pid'] == self.scraper_process.pid:
                            continue
                        self.log_event(f"🔍 Scraper externo detectado: PID {proc.info['pid']}")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False
            
        except ImportError:
            # Si psutil no está disponible, verificar solo nuestro proceso
            return self.scraper_process is not None and self.scraper_process.poll() is None
    
    def check_for_new_numbers(self):
        """Verificar si hay nuevos números en Redis"""
        if not self.redis_client:
            return None
        
        try:
            # Obtener el último número de Redis
            latest_number = self.redis_client.get("roulette:latest")
            
            if latest_number is None:
                return None
            
            # Convertir a string de forma segura
            if isinstance(latest_number, bytes):
                latest_number = latest_number.decode('utf-8')
            else:
                latest_number = str(latest_number)
            
            # Verificar si es un número nuevo
            if latest_number != self.last_known_number:
                self.log_event(f"🆕 Nuevo número detectado: {self.last_known_number} → {latest_number}")
                
                old_number = self.last_known_number
                self.last_known_number = latest_number
                
                return {
                    'number': int(latest_number),
                    'previous_number': int(old_number) if old_number and old_number.isdigit() else None,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'redis_monitor'
                }
            
            return None
            
        except Exception as e:
            self.log_event(f"❌ Error verificando números: {e}", "ERROR")
            return None
    
    def process_new_number(self, number_data):
        """Procesar un nuevo número detectado"""
        try:
            number = number_data['number']
            self.log_event(f"🔄 Procesando nuevo número: {number}")
            
            # 1. Verificar predicciones pendientes
            pending_results = self.verify_pending_predictions(number)
            
            # 2. Generar nueva predicción automáticamente
            new_prediction = None
            if self.auto_predict:
                try:
                    new_prediction = self.ai_predictor.make_prediction('groups')
                    if new_prediction:
                        self.log_event(f"🎯 Nueva predicción generada: {new_prediction.prediction_id}")
                except Exception as pred_error:
                    self.log_event(f"❌ Error generando predicción: {pred_error}", "ERROR")
            
            # 3. Actualizar estadísticas en Redis
            self.update_automation_stats(number_data, pending_results, new_prediction)
            
            # 4. Notificar al frontend
            self.notify_frontend({
                'type': 'new_number',
                'number': number,
                'timestamp': number_data['timestamp'],
                'verified_predictions': len(pending_results),
                'new_prediction_generated': new_prediction is not None,
                'prediction_id': new_prediction.prediction_id if new_prediction else None
            })
            
            self.log_event(f"✅ Número {number} procesado completamente")
            
        except Exception as e:
            self.log_event(f"❌ Error procesando número: {e}", "ERROR")
    
    def verify_pending_predictions(self, actual_number):
        """Verificar predicciones pendientes contra el número real"""
        results = []
        
        try:
            if not self.redis_client:
                return results
            
            # Obtener predicciones pendientes
            try:
                pending_predictions = self.redis_client.lrange('ai:pending_predictions', 0, -1)
                if not pending_predictions:
                    return results
            except Exception as e:
                self.log_event(f"Error obteniendo predicciones pendientes: {e}", "ERROR")
                return results
            
            for pred_id_item in pending_predictions:
                try:
                    # Convertir a string de forma segura
                    if isinstance(pred_id_item, bytes):
                        pred_id = pred_id_item.decode('utf-8')
                    else:
                        pred_id = str(pred_id_item)
                    
                    # Verificar predicción
                    result = self.verify_single_prediction(pred_id, actual_number)
                    if result:
                        results.append(result)
                        self.log_event(f"✅ Predicción {pred_id} verificada: {'GANÓ' if result['overall_winner'] else 'PERDIÓ'}")
                        
                except Exception as verify_error:
                    self.log_event(f"❌ Error verificando predicción: {verify_error}", "ERROR")
            
            if results:
                self.log_event(f"📊 Verificadas {len(results)} predicciones pendientes")
            
        except Exception as e:
            self.log_event(f"❌ Error en verificación de predicciones: {e}", "ERROR")
        
        return results
    
    def verify_single_prediction(self, prediction_id, actual_number):
        """Verificar una predicción individual"""
        try:
            if not self.redis_client:
                return None
                
            pred_data = self.redis_client.hgetall(f"prediction:{prediction_id}")
            
            if not pred_data:
                return None
            
            # Decodificar datos de forma segura
            def safe_get_redis_value(data, key, default=''):
                try:
                    value = data.get(key, default)
                    if isinstance(value, bytes):
                        return value.decode('utf-8')
                    return str(value) if value is not None else default
                except Exception:
                    return default
            
            # Obtener grupos de predicción
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
            
            # Actualizar estadísticas
            self.update_prediction_stats(prediction_id, actual_number, overall_winner, group_results)
            
            return {
                "prediction_id": prediction_id,
                "actual_number": actual_number,
                "overall_winner": overall_winner,
                "group_results": group_results,
                "winning_groups": sum(1 for gr in group_results if gr["is_winner"]),
                "total_groups": len(groups)
            }
            
        except Exception as e:
            self.log_event(f"❌ Error verificando predicción {prediction_id}: {e}", "ERROR")
            return None
    
    def update_prediction_stats(self, prediction_id, actual_number, overall_winner, group_results):
        """Actualizar estadísticas de predicciones"""
        try:
            if not self.redis_client:
                return
                
            # Actualizar estadísticas globales
            stats_key = "ai:game_stats"
            try:
                self.redis_client.hincrby(stats_key, "total_predictions", 1)
                
                if overall_winner:
                    self.redis_client.hincrby(stats_key, "total_wins", 1)
                else:
                    self.redis_client.hincrby(stats_key, "total_losses", 1)
            except Exception as e:
                self.log_event(f"Error actualizando stats globales: {e}", "ERROR")
            
            # Actualizar estadísticas por grupo
            try:
                for group_result in group_results:
                    group_key = f"ai:group_stats:{group_result['group_name']}"
                    self.redis_client.hincrby(group_key, "total", 1)
                    
                    if group_result['is_winner']:
                        self.redis_client.hincrby(group_key, "wins", 1)
                    else:
                        self.redis_client.hincrby(group_key, "losses", 1)
            except Exception as e:
                self.log_event(f"Error actualizando stats por grupo: {e}", "ERROR")
            
            # Guardar resultado específico
            try:
                result_key = f"result:{prediction_id}"
                result_data = {
                    'prediction_id': prediction_id,
                    'actual_number': str(actual_number),
                    'is_winner': '1' if overall_winner else '0',
                    'winning_groups': str(sum(1 for gr in group_results if gr["is_winner"])),
                    'total_groups': str(len(group_results)),
                    'timestamp': datetime.now().isoformat(),
                    'verified': '1',
                    'auto_verified': '1'
                }
                
                self.redis_client.hset(result_key, mapping=result_data)
                self.redis_client.expire(result_key, 86400 * 7)  # 7 días
                
                # Remover de predicciones pendientes
                self.redis_client.lrem('ai:pending_predictions', 0, prediction_id)
            except Exception as e:
                self.log_event(f"Error guardando resultado: {e}", "ERROR")
                
        except Exception as e:
            self.log_event(f"❌ Error actualizando estadísticas: {e}", "ERROR")
    
    def update_automation_stats(self, number_data, pending_results, new_prediction):
        """Actualizar estadísticas del servicio de automatización"""
        try:
            if not self.redis_client:
                return
                
            # Obtener contador actual de forma segura
            try:
                current_count_raw = self.redis_client.hget('automation:stats', 'total_numbers_processed')
                current_count = 0
                if current_count_raw:
                    if isinstance(current_count_raw, bytes):
                        current_count_raw = current_count_raw.decode('utf-8')
                    current_count = int(current_count_raw)
            except (ValueError, TypeError, AttributeError):
                current_count = 0
            
            stats = {
                'last_number_processed': str(number_data['number']),
                'last_process_time': datetime.now().isoformat(),
                'predictions_verified': str(len(pending_results)),
                'auto_prediction_generated': '1' if new_prediction else '0',
                'total_numbers_processed': str(current_count + 1)
            }
            
            self.redis_client.hset('automation:stats', mapping=stats)
            
        except Exception as e:
            self.log_event(f"❌ Error actualizando stats de automatización: {e}", "ERROR")
    
    def notify_frontend(self, notification_data):
        """Notificar al frontend sobre eventos importantes"""
        try:
            if not self.redis_client:
                return
                
            notification = {
                'timestamp': datetime.now().isoformat(),
                'data': notification_data
            }
            
            # Guardar notificación en Redis para que el frontend la pueda leer
            self.redis_client.lpush('automation:notifications', json.dumps(notification))
            self.redis_client.ltrim('automation:notifications', 0, 49)  # Mantener últimas 50
            
            # También actualizar un contador de eventos
            self.redis_client.incr('automation:events_count')
            
        except Exception as e:
            self.log_event(f"❌ Error notificando frontend: {e}", "ERROR")
    
    def monitoring_loop(self):
        """Loop principal de monitoreo"""
        self.log_event("🔍 Iniciando loop de monitoreo")
        
        while self.is_running:
            try:
                # Verificar nuevos números
                new_number_data = self.check_for_new_numbers()
                
                if new_number_data:
                    self.process_new_number(new_number_data)
                
                # Verificar estado del scraper
                if self.scraper_enabled and self.scraper_process:
                    if self.scraper_process.poll() is not None:
                        self.log_event("⚠️ Scraper se detuvo, reiniciando...", "WARNING")
                        self.start_scraper()
                
                # Pausa antes del siguiente check
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.log_event(f"❌ Error en loop de monitoreo: {e}", "ERROR")
                time.sleep(self.check_interval * 2)  # Pausa más larga en caso de error
    
    def start(self):
        """Iniciar el servicio de automatización"""
        if self.is_running:
            self.log_event("⚠️ El servicio ya está ejecutándose")
            return
        
        self.log_event("🚀 INICIANDO SERVICIO DE AUTOMATIZACIÓN")
        self.log_event("=" * 60)
        
        # Configuración inicial
        self.is_running = True
        
        # Obtener número inicial
        if self.redis_client:
            try:
                initial_number = self.redis_client.get("roulette:latest")
                if initial_number:
                    if isinstance(initial_number, bytes):
                        self.last_known_number = initial_number.decode('utf-8')
                    else:
                        self.last_known_number = str(initial_number)
                    self.log_event(f"📍 Número inicial detectado: {self.last_known_number}")
            except Exception as e:
                self.log_event(f"Error obteniendo número inicial: {e}", "ERROR")
        
        # Iniciar scraper si está habilitado Y no hay otro scraper corriendo
        if self.scraper_enabled:
            # Verificar si ya hay un scraper corriendo
            if self.is_scraper_running():
                self.log_event("⚠️ Ya hay un scraper ejecutándose, no iniciando otro", "WARNING")
            else:
                self.start_scraper()
        
        # Iniciar thread de monitoreo
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.log_event("✅ Servicio de automatización iniciado exitosamente")
        self.log_event(f"   • Intervalo de verificación: {self.check_interval}s")
        self.log_event(f"   • Predicciones automáticas: {'✅' if self.auto_predict else '❌'}")
        self.log_event(f"   • Scraper habilitado: {'✅' if self.scraper_enabled else '❌'}")
    
    def stop(self):
        """Detener el servicio de automatización"""
        self.log_event("🛑 Deteniendo servicio de automatización...")
        
        self.is_running = False
        
        # Detener scraper
        self.stop_scraper()
        
        # Esperar a que termine el thread de monitoreo
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)
        
        self.log_event("✅ Servicio de automatización detenido")
    
    def get_status(self):
        """Obtener estado actual del servicio"""
        try:
            scraper_status = "running" if (self.scraper_process and self.scraper_process.poll() is None) else "stopped"
            
            # Obtener estadísticas de Redis
            automation_stats = {}
            if self.redis_client:
                try:
                    raw_stats = self.redis_client.hgetall('automation:stats')
                    if raw_stats:
                        # Decodificar bytes a string de forma segura
                        automation_stats = {}
                        for k, v in raw_stats.items():
                            key = k.decode('utf-8') if isinstance(k, bytes) else str(k)
                            value = v.decode('utf-8') if isinstance(v, bytes) else str(v)
                            automation_stats[key] = value
                except Exception as e:
                    self.log_event(f"Error obteniendo stats: {e}", "ERROR")
            
            return {
                'is_running': self.is_running,
                'scraper_enabled': self.scraper_enabled,
                'scraper_status': scraper_status,
                'scraper_pid': self.scraper_process.pid if self.scraper_process else None,
                'auto_predict': self.auto_predict,
                'check_interval': self.check_interval,
                'last_known_number': self.last_known_number,
                'monitoring_active': self.monitoring_thread.is_alive() if self.monitoring_thread else False,
                'stats': automation_stats,
                'last_check': self.last_check_time.isoformat()
            }
            
        except Exception as e:
            self.log_event(f"❌ Error obteniendo status: {e}", "ERROR")
            return {'error': str(e)}

# Instancia global del servicio
automation_service = None

def get_automation_service():
    """Obtener instancia del servicio de automatización"""
    global automation_service
    if automation_service is None:
        automation_service = AutomationService()
    return automation_service

def initialize_automation():
    """Inicializar el servicio de automatización"""
    service = get_automation_service()
    service.start()
    return service

if __name__ == "__main__":
    # Ejecutar como servicio independiente
    print("🤖 Iniciando Servicio de Automatización de AI Casino")
    
    service = AutomationService()
    
    try:
        service.start()
        
        # Mantener el servicio ejecutándose
        while True:
            time.sleep(60)  # Verificar cada minuto
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servicio...")
        service.stop()
        print("✅ Servicio detenido")