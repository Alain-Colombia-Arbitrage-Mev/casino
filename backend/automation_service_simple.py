#!/usr/bin/env python3
"""
Servicio de Automatización Simplificado para AI Casino
Versión que funciona sin dependencias complejas
"""

import os
import sys
import time
import json
import threading
import logging
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAutomationService:
    """Servicio de automatización simplificado"""
    
    def __init__(self):
        self.is_running = False
        self.monitoring_thread = None
        self.last_known_number = None
        self.last_check_time = datetime.now()
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Configuración
        self.check_interval = 5  # segundos
        self.auto_predict = True
        
        # Archivos de datos locales
        self.numbers_file = self.data_dir / "numbers.json"
        self.stats_file = self.data_dir / "automation_stats.json"
        self.logs_file = self.data_dir / "automation_logs.json"
        
        # Inicializar archivos
        self.init_data_files()
        
        logger.info("🤖 Servicio de Automatización Simplificado inicializado")
    
    def init_data_files(self):
        """Inicializar archivos de datos"""
        try:
            # Archivo de números
            if not self.numbers_file.exists():
                with open(self.numbers_file, 'w') as f:
                    json.dump({"latest": None, "history": []}, f)
            
            # Archivo de estadísticas
            if not self.stats_file.exists():
                with open(self.stats_file, 'w') as f:
                    json.dump({
                        "total_numbers_processed": 0,
                        "last_process_time": None,
                        "predictions_generated": 0,
                        "service_start_time": datetime.now().isoformat()
                    }, f)
            
            # Archivo de logs
            if not self.logs_file.exists():
                with open(self.logs_file, 'w') as f:
                    json.dump([], f)
                    
        except Exception as e:
            logger.error(f"Error inicializando archivos: {e}")
    
    def log_event(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        
        print(f"[{timestamp}] [AUTOMATION] [{level}] {message}")
        
        # Guardar en archivo
        try:
            with open(self.logs_file, 'r') as f:
                logs = json.load(f)
            
            logs.append(log_entry)
            logs = logs[-100:]  # Mantener últimos 100
            
            with open(self.logs_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error guardando log: {e}")
    
    def check_for_new_numbers(self):
        """Verificar si hay nuevos números"""
        try:
            # Leer archivo de números
            with open(self.numbers_file, 'r') as f:
                data = json.load(f)
            
            latest_number = data.get("latest")
            
            if latest_number is None:
                return None
            
            # Verificar si es un número nuevo
            if str(latest_number) != str(self.last_known_number):
                self.log_event(f"🆕 Nuevo número detectado: {self.last_known_number} → {latest_number}")
                
                old_number = self.last_known_number
                self.last_known_number = str(latest_number)
                
                return {
                    'number': int(latest_number),
                    'previous_number': int(old_number) if old_number and str(old_number).isdigit() else None,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'file_monitor'
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
            
            # Simular procesamiento de predicciones
            self.log_event(f"🎯 Generando predicción para número {number}")
            
            # Actualizar estadísticas
            self.update_stats(number_data)
            
            # Simular grupos de predicción
            prediction_groups = self.generate_simple_prediction(number)
            self.log_event(f"📊 Grupos generados: {list(prediction_groups.keys())}")
            
            self.log_event(f"✅ Número {number} procesado completamente")
            
        except Exception as e:
            self.log_event(f"❌ Error procesando número: {e}", "ERROR")
    
    def generate_simple_prediction(self, current_number):
        """Generar predicción simple basada en el número actual"""
        try:
            # Leer historial
            with open(self.numbers_file, 'r') as f:
                data = json.load(f)
            
            history = data.get("history", [])
            
            # Análisis simple de patrones
            red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
            
            # Generar grupos de predicción
            groups = {
                "high_low": list(range(19, 37)) if current_number <= 18 else list(range(1, 19)),
                "even_odd": [n for n in range(1, 37) if n % 2 == 0] if current_number % 2 == 1 else [n for n in range(1, 37) if n % 2 == 1],
                "red_black": list(red_numbers) if current_number not in red_numbers else [n for n in range(1, 37) if n not in red_numbers],
                "dozen": []
            }
            
            # Docena opuesta
            if 1 <= current_number <= 12:
                groups["dozen"] = list(range(13, 25))
            elif 13 <= current_number <= 24:
                groups["dozen"] = list(range(25, 37))
            else:
                groups["dozen"] = list(range(1, 13))
            
            return groups
            
        except Exception as e:
            self.log_event(f"Error generando predicción: {e}", "ERROR")
            return {}
    
    def update_stats(self, number_data):
        """Actualizar estadísticas"""
        try:
            with open(self.stats_file, 'r') as f:
                stats = json.load(f)
            
            stats["total_numbers_processed"] = stats.get("total_numbers_processed", 0) + 1
            stats["last_process_time"] = datetime.now().isoformat()
            stats["last_number"] = number_data["number"]
            stats["predictions_generated"] = stats.get("predictions_generated", 0) + 1
            
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            self.log_event(f"Error actualizando estadísticas: {e}", "ERROR")
    
    def add_test_number(self, number):
        """Agregar número de prueba (para testing)"""
        try:
            with open(self.numbers_file, 'r') as f:
                data = json.load(f)
            
            data["latest"] = number
            data["history"].append({
                "number": number,
                "timestamp": datetime.now().isoformat()
            })
            
            # Mantener últimos 100 números
            data["history"] = data["history"][-100:]
            
            with open(self.numbers_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.log_event(f"📝 Número de prueba agregado: {number}")
            
        except Exception as e:
            self.log_event(f"Error agregando número de prueba: {e}", "ERROR")
    
    def monitoring_loop(self):
        """Loop principal de monitoreo"""
        self.log_event("🔍 Iniciando loop de monitoreo")
        
        while self.is_running:
            try:
                # Verificar nuevos números
                new_number_data = self.check_for_new_numbers()
                
                if new_number_data:
                    self.process_new_number(new_number_data)
                
                # Pausa antes del siguiente check
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.log_event(f"❌ Error en loop de monitoreo: {e}", "ERROR")
                time.sleep(self.check_interval * 2)
    
    def start(self):
        """Iniciar el servicio"""
        if self.is_running:
            self.log_event("⚠️ El servicio ya está ejecutándose")
            return
        
        self.log_event("🚀 INICIANDO SERVICIO DE AUTOMATIZACIÓN SIMPLIFICADO")
        self.log_event("=" * 60)
        
        self.is_running = True
        
        # Obtener número inicial
        try:
            with open(self.numbers_file, 'r') as f:
                data = json.load(f)
            
            initial_number = data.get("latest")
            if initial_number:
                self.last_known_number = str(initial_number)
                self.log_event(f"📍 Número inicial: {self.last_known_number}")
        except Exception as e:
            self.log_event(f"Error obteniendo número inicial: {e}", "ERROR")
        
        # Iniciar thread de monitoreo
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.log_event("✅ Servicio iniciado exitosamente")
        self.log_event(f"   • Intervalo de verificación: {self.check_interval}s")
        self.log_event(f"   • Predicciones automáticas: {'✅' if self.auto_predict else '❌'}")
        self.log_event(f"   • Directorio de datos: {self.data_dir}")
    
    def stop(self):
        """Detener el servicio"""
        self.log_event("🛑 Deteniendo servicio...")
        
        self.is_running = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        self.log_event("✅ Servicio detenido")
    
    def get_status(self):
        """Obtener estado actual"""
        try:
            # Leer estadísticas
            stats = {}
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    stats = json.load(f)
            
            return {
                'is_running': self.is_running,
                'auto_predict': self.auto_predict,
                'check_interval': self.check_interval,
                'last_known_number': self.last_known_number,
                'monitoring_active': self.monitoring_thread.is_alive() if self.monitoring_thread else False,
                'stats': stats,
                'last_check': self.last_check_time.isoformat(),
                'data_directory': str(self.data_dir)
            }
            
        except Exception as e:
            self.log_event(f"❌ Error obteniendo status: {e}", "ERROR")
            return {'error': str(e)}
    
    def get_logs(self, limit=50):
        """Obtener logs recientes"""
        try:
            if self.logs_file.exists():
                with open(self.logs_file, 'r') as f:
                    logs = json.load(f)
                return logs[-limit:]
            return []
        except Exception as e:
            return [{"error": f"Error obteniendo logs: {e}"}]

# Instancia global
simple_automation_service = None

def get_simple_automation_service():
    """Obtener instancia del servicio simplificado"""
    global simple_automation_service
    if simple_automation_service is None:
        simple_automation_service = SimpleAutomationService()
    return simple_automation_service

if __name__ == "__main__":
    print("🤖 Iniciando Servicio de Automatización Simplificado")
    
    service = SimpleAutomationService()
    
    try:
        service.start()
        
        # Agregar algunos números de prueba después de 5 segundos
        time.sleep(5)
        service.add_test_number(17)
        
        time.sleep(3)
        service.add_test_number(23)
        
        # Mantener ejecutándose
        while True:
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servicio...")
        service.stop()
        print("✅ Servicio detenido")