#!/usr/bin/env python3
"""
Servicio Automático para el Sistema de Ruleta
Escucha números de Redis y genera predicciones automáticamente
"""

import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Importar nuestros módulos existentes
try:
    from redis_manager import get_redis_manager
except ImportError:
    print("❌ Redis manager no disponible")

try:
    from roulette_analyzer import AnalizadorRuleta
except ImportError:
    print("❌ Analizador no disponible")

try:
    from ml_predictor import MLPredictor
except ImportError:
    print("⚠️ ML Predictor no disponible")

try:
    from advanced_ml_predictor import AdvancedMLPredictor
except ImportError:
    print("⚠️ Advanced ML no disponible")

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutomaticRouletteService:
    """Servicio automático que procesa números y genera predicciones"""
    
    def __init__(self):
        """Inicializar el servicio automático"""
        self.redis_manager = None
        self.analyzer = None
        self.ml_predictor = None
        self.advanced_ml = None
        self.running = False
        self.last_processed_number = None
        
        # Hilo para el procesamiento automático
        self.processing_thread = None
        
        # Configuración
        self.prediction_confidence_threshold = 0.6
        self.min_history_for_prediction = 10
        
        # Estadísticas
        self.stats = {
            'numbers_processed': 0,
            'predictions_generated': 0,
            'predictions_evaluated': 0,
            'wins': 0,
            'losses': 0
        }
        
        logger.info("🤖 Servicio Automático de Ruleta inicializado")
    
    def initialize_components(self) -> bool:
        """Inicializar todos los componentes necesarios"""
        try:
            # Inicializar Redis Manager
            logger.info("🔌 Conectando a Redis...")
            self.redis_manager = get_redis_manager()
            
            # Inicializar Analizador de Ruleta (básico si no existe)
            logger.info("🎯 Inicializando Analizador básico...")
            self.analyzer = BasicAnalyzer()  # Versión básica
            
            logger.info("🎉 Componentes básicos inicializados correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando componentes: {e}")
            return False
    
    def start_service(self):
        """Iniciar el servicio automático"""
        if self.running:
            logger.warning("⚠️ El servicio ya está en ejecución")
            return
        
        if not self.initialize_components():
            logger.error("❌ No se pudo inicializar el servicio")
            return
        
        self.running = True
        logger.info("🚀 Iniciando servicio automático...")
        
        # Iniciar hilo de procesamiento
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        logger.info("✅ Servicio automático iniciado correctamente")
    
    def stop_service(self):
        """Detener el servicio automático"""
        logger.info("🛑 Deteniendo servicio automático...")
        self.running = False
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
        
        if self.redis_manager:
            self.redis_manager.set_system_status("stopped", "Servicio detenido manualmente")
            self.redis_manager.close()
        
        logger.info("✅ Servicio automático detenido")
    
    def _processing_loop(self):
        """Loop principal de procesamiento"""
        logger.info("🔄 Iniciando loop de procesamiento automático...")
        
        while self.running:
            try:
                # Verificar si hay un nuevo número
                latest_number_data = self.redis_manager.get_latest_number()
                
                if latest_number_data:
                    current_number = int(latest_number_data['number'])
                    timestamp = latest_number_data.get('timestamp')
                    
                    # Verificar si es un número nuevo
                    if current_number != self.last_processed_number:
                        logger.info(f"🆕 Nuevo número detectado: {current_number}")
                        
                        # Procesar el nuevo número
                        self._process_new_number(current_number, timestamp)
                        self.last_processed_number = current_number
                        self.stats['numbers_processed'] += 1
                    else:
                        # No hay números nuevos, esperar un poco más
                        time.sleep(5)
                else:
                    # Sin datos en Redis, esperar
                    logger.debug("⏳ Esperando nuevos números en Redis...")
                    time.sleep(10)
                
            except Exception as e:
                logger.error(f"❌ Error en loop de procesamiento: {e}")
                time.sleep(15)  # Esperar antes de reintentar
        
        logger.info("🔚 Loop de procesamiento terminado")
    
    def _process_new_number(self, number: int, timestamp: str = None):
        """Procesar un nuevo número y generar predicciones"""
        try:
            logger.info(f"🔢 Procesando número: {number}")
            
            # Evaluar predicciones activas primero
            self._evaluate_active_predictions(number)
            
            # Agregar número al analizador
            self.analyzer.add_number(number)
            
            # Verificar si tenemos suficiente historial para predicciones
            if len(self.analyzer.history) < self.min_history_for_prediction:
                logger.info(f"📊 Historial insuficiente ({len(self.analyzer.history)}/{self.min_history_for_prediction})")
                return
            
            # Generar nuevas predicciones con diferentes estrategias
            predictions = self._generate_enhanced_predictions()
            
            if predictions:
                # Almacenar predicciones en Redis con metadatos mejorados
                for prediction in predictions:
                    prediction['timestamp'] = timestamp or datetime.now().isoformat()
                    prediction['trigger_number'] = number
                    if self.redis_manager.store_prediction(prediction):
                        self.stats['predictions_generated'] += 1
                
                logger.info(f"💾 {len(predictions)} predicciones mejoradas generadas y almacenadas")
            
        except Exception as e:
            logger.error(f"❌ Error procesando número {number}: {e}")
    
    def _evaluate_active_predictions(self, result_number: int):
        """Evaluar predicciones activas contra el número resultado"""
        try:
            active_predictions = self.redis_manager.get_active_predictions()
            
            for prediction in active_predictions:
                prediction_id = prediction['id']
                predicted_numbers = prediction.get('predicted_numbers', [])
                
                # Verificar si fue un acierto
                is_win = result_number in predicted_numbers
                
                # Actualizar resultado
                self.redis_manager.update_prediction_result(prediction_id, result_number, is_win)
                
                # Actualizar estadísticas locales
                self.stats['predictions_evaluated'] += 1
                if is_win:
                    self.stats['wins'] += 1
                else:
                    self.stats['losses'] += 1
                
                logger.info(f"📊 Predicción {prediction_id}: {'WIN ✅' if is_win else 'LOSE ❌'} (número: {result_number})")
            
        except Exception as e:
            logger.error(f"❌ Error evaluando predicciones: {e}")
    
    def _generate_basic_predictions(self) -> List[Dict]:
        """Generar predicciones básicas"""
        predictions = []
        
        try:
            # Análisis básico de patrones
            recent_numbers = self.analyzer.get_recent_numbers(10)
            
            # 1. Predicción por frecuencia de números
            frequency_prediction = self._generate_frequency_prediction()
            if frequency_prediction:
                predictions.append(frequency_prediction)
            
            # 2. Predicción por sectores básicos
            sector_prediction = self._generate_basic_sector_prediction()
            if sector_prediction:
                predictions.append(sector_prediction)
            
            logger.info(f"🎯 Generadas {len(predictions)} predicciones básicas")
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error generando predicciones: {e}")
            return []
    
    def _generate_enhanced_predictions(self) -> List[Dict]:
        """Generar predicciones mejoradas con múltiples estrategias"""
        predictions = []
        
        try:
            recent_numbers = self.analyzer.get_recent_numbers(20)
            
            # 1. Predicción por análisis de gaps (distancias entre repeticiones)
            gap_prediction = self._generate_gap_analysis_prediction()
            if gap_prediction:
                predictions.append(gap_prediction)
            
            # 2. Predicción por patrones de colores
            color_pattern_prediction = self._generate_color_pattern_prediction()
            if color_pattern_prediction:
                predictions.append(color_pattern_prediction)
            
            # 3. Predicción por análisis de vecinos en la rueda
            neighbor_prediction = self._generate_neighbor_analysis_prediction()
            if neighbor_prediction:
                predictions.append(neighbor_prediction)
            
            # 4. Predicción híbrida combinando múltiples factores
            hybrid_prediction = self._generate_hybrid_prediction()
            if hybrid_prediction:
                predictions.append(hybrid_prediction)
            
            logger.info(f"🎯 Generadas {len(predictions)} predicciones mejoradas")
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error generando predicciones mejoradas: {e}")
            return self._generate_basic_predictions()  # Fallback a predicciones básicas
    
    def _generate_frequency_prediction(self) -> Optional[Dict]:
        """Generar predicción basada en frecuencia de números"""
        try:
            # Obtener estadísticas de frecuencia
            frequency_stats = self.analyzer.get_frequency_stats()
            
            # Seleccionar números menos frecuentes (teoría de compensación)
            least_frequent = sorted(frequency_stats.items(), key=lambda x: x[1])[:12]
            predicted_numbers = [num for num, freq in least_frequent]
            
            return {
                'type': 'frequency_analysis',
                'method': 'Análisis de Frecuencia',
                'predicted_numbers': predicted_numbers,
                'confidence': 0.5,
                'description': 'Predicción basada en números menos frecuentes'
            }
            
        except Exception as e:
            logger.error(f"❌ Error en predicción de frecuencia: {e}")
            return None
    
    def _generate_basic_sector_prediction(self) -> Optional[Dict]:
        """Generar predicción básica de sectores"""
        try:
            # Definir sectores básicos
            sectors = {
                'Primera_Docena': list(range(1, 13)),
                'Segunda_Docena': list(range(13, 25)),
                'Tercera_Docena': list(range(25, 37)),
                'Rojos': [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36],
                'Negros': [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
            }
            
            # Analizar frecuencia por sector
            recent_numbers = self.analyzer.get_recent_numbers(20)
            sector_counts = {}
            
            for sector_name, sector_numbers in sectors.items():
                count = sum(1 for num in recent_numbers if num in sector_numbers)
                sector_counts[sector_name] = count
            
            # Seleccionar sector menos frecuente
            least_frequent_sector = min(sector_counts.items(), key=lambda x: x[1])
            sector_name = least_frequent_sector[0]
            
            return {
                'type': 'basic_sector',
                'method': 'Análisis Básico de Sectores',
                'predicted_numbers': sectors[sector_name][:10],
                'confidence': 0.4,
                'sector_name': sector_name,
                'description': f'Predicción del sector {sector_name}'
            }
            
        except Exception as e:
            logger.error(f"❌ Error en predicción de sector: {e}")
            return None
    
    def get_service_status(self) -> Dict:
        """Obtener estado completo del servicio"""
        try:
            redis_status = self.redis_manager.get_system_status() if self.redis_manager else None
            redis_stats = self.redis_manager.get_stats() if self.redis_manager else {}
            active_predictions = self.redis_manager.get_active_predictions() if self.redis_manager else []
            
            return {
                'service_running': self.running,
                'components': {
                    'redis_manager': self.redis_manager is not None,
                    'analyzer': self.analyzer is not None,
                },
                'redis_status': redis_status,
                'redis_statistics': redis_stats,
                'local_statistics': self.stats,
                'active_predictions_count': len(active_predictions),
                'last_processed_number': self.last_processed_number,
                'history_size': len(self.analyzer.history) if self.analyzer else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado del servicio: {e}")
            return {'error': str(e)}


class BasicAnalyzer:
    """Analizador básico para cuando no está disponible el completo"""
    
    def __init__(self, max_history=100):
        self.history = []
        self.max_history = max_history
    
    def add_number(self, number: int):
        """Agregar número al historial"""
        if 0 <= number <= 36:
            self.history.insert(0, number)  # Más reciente primero
            if len(self.history) > self.max_history:
                self.history.pop()
    
    def get_recent_numbers(self, count: int) -> List[int]:
        """Obtener números recientes"""
        return self.history[:count]
    
    def get_frequency_stats(self) -> Dict[int, int]:
        """Obtener estadísticas de frecuencia"""
        frequency = {}
        for i in range(37):
            frequency[i] = self.history.count(i)
        return frequency


# Instancia global del servicio
automatic_service = AutomaticRouletteService()

def start_automatic_service():
    """Iniciar el servicio automático"""
    automatic_service.start_service()

def stop_automatic_service():
    """Detener el servicio automático"""
    automatic_service.stop_service()

def get_service_status():
    """Obtener estado del servicio"""
    return automatic_service.get_service_status()

if __name__ == "__main__":
    # Ejecutar servicio automático cuando se ejecuta directamente
    try:
        logger.info("🚀 Iniciando servicio automático de ruleta...")
        start_automatic_service()
        
        # Mantener el servicio ejecutándose
        while True:
            time.sleep(30)
            status = get_service_status()
            logger.info(f"📊 Estado: Ejecutando={status['service_running']}, Predicciones activas={status['active_predictions_count']}")
            
    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo servicio por interrupción del usuario...")
        stop_automatic_service()
    except Exception as e:
        logger.error(f"❌ Error fatal en servicio automático: {e}")
        stop_automatic_service()

    def _generate_gap_analysis_prediction(self) -> Optional[Dict]:
        """Generar predicción basada en análisis de gaps entre números"""
        try:
            recent_numbers = self.analyzer.get_recent_numbers(30)
            if len(recent_numbers) < 10:
                return None
            
            # Calcular gaps para cada número (0-36)
            number_gaps = {}
            for target_num in range(37):
                gaps = []
                last_position = -1
                
                for i, num in enumerate(recent_numbers):
                    if num == target_num:
                        if last_position != -1:
                            gaps.append(i - last_position)
                        last_position = i
                
                if gaps:
                    avg_gap = sum(gaps) / len(gaps)
                    number_gaps[target_num] = {
                        'avg_gap': avg_gap,
                        'last_seen': last_position,
                        'current_gap': len(recent_numbers) - last_position - 1 if last_position != -1 else len(recent_numbers)
                    }
            
            # Seleccionar números con gaps más largos que su promedio
            overdue_numbers = []
            for num, data in number_gaps.items():
                if data['current_gap'] > data['avg_gap'] * 1.5:  # 50% más que su promedio
                    overdue_numbers.append(num)
            
            if overdue_numbers:
                return {
                    'type': 'gap_analysis',
                    'method': 'Análisis de Gaps',
                    'predicted_numbers': overdue_numbers[:8],  # Top 8
                    'confidence': min(0.7, 0.4 + len(overdue_numbers) * 0.02),
                    'description': f'Números con gaps superiores a su promedio: {overdue_numbers[:8]}'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error en análisis de gaps: {e}")
            return None
    
    def _generate_color_pattern_prediction(self) -> Optional[Dict]:
        """Generar predicción basada en patrones de colores"""
        try:
            recent_numbers = self.analyzer.get_recent_numbers(15)
            if len(recent_numbers) < 8:
                return None
            
            # Definir colores
            red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
            black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
            
            # Analizar secuencia de colores
            color_sequence = []
            for num in recent_numbers:
                if num == 0:
                    color_sequence.append('green')
                elif num in red_numbers:
                    color_sequence.append('red')
                else:
                    color_sequence.append('black')
            
            # Detectar patrones
            red_count = color_sequence.count('red')
            black_count = color_sequence.count('black')
            green_count = color_sequence.count('green')
            
            # Predecir color menos frecuente
            color_counts = {'red': red_count, 'black': black_count, 'green': green_count}
            min_color = min(color_counts.items(), key=lambda x: x[1])[0]
            
            if min_color == 'red':
                predicted_numbers = red_numbers[:10]
            elif min_color == 'black':
                predicted_numbers = black_numbers[:10]
            else:
                predicted_numbers = [0]
            
            return {
                'type': 'color_pattern',
                'method': 'Análisis de Patrones de Color',
                'predicted_numbers': predicted_numbers,
                'confidence': 0.6,
                'description': f'Color menos frecuente: {min_color} ({color_counts[min_color]}/{len(recent_numbers)})'
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis de colores: {e}")
            return None
    
    def _generate_neighbor_analysis_prediction(self) -> Optional[Dict]:
        """Generar predicción basada en análisis de vecinos en la rueda"""
        try:
            recent_numbers = self.analyzer.get_recent_numbers(10)
            if len(recent_numbers) < 5:
                return None
            
            # Rueda europea
            wheel = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
            
            # Analizar vecinos de los últimos números
            neighbor_candidates = set()
            for num in recent_numbers[:3]:  # Últimos 3 números
                try:
                    idx = wheel.index(num)
                    # Agregar 2 vecinos a cada lado
                    for i in range(-2, 3):
                        neighbor_idx = (idx + i) % len(wheel)
                        neighbor_candidates.add(wheel[neighbor_idx])
                except ValueError:
                    continue
            
            # Filtrar números que ya salieron recientemente
            filtered_neighbors = [n for n in neighbor_candidates if n not in recent_numbers[:5]]
            
            if filtered_neighbors:
                return {
                    'type': 'neighbor_analysis',
                    'method': 'Análisis de Vecinos en Rueda',
                    'predicted_numbers': filtered_neighbors[:12],
                    'confidence': 0.55,
                    'description': f'Vecinos de últimos números que no han salido recientemente'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error en análisis de vecinos: {e}")
            return None
    
    def _generate_hybrid_prediction(self) -> Optional[Dict]:
        """Generar predicción híbrida combinando múltiples factores"""
        try:
            recent_numbers = self.analyzer.get_recent_numbers(25)
            if len(recent_numbers) < 15:
                return None
            
            # Combinar diferentes análisis
            candidate_scores = {}
            
            # Factor 1: Frecuencia inversa (números menos frecuentes)
            frequency_stats = {}
            for i in range(37):
                frequency_stats[i] = recent_numbers.count(i)
            
            for num, freq in frequency_stats.items():
                # Puntuación más alta para números menos frecuentes
                candidate_scores[num] = candidate_scores.get(num, 0) + (5 - freq) * 0.3
            
            # Factor 2: Distancia desde última aparición
            for i, num in enumerate(recent_numbers):
                distance_score = i * 0.1  # Más puntos por mayor distancia
                candidate_scores[num] = candidate_scores.get(num, 0) + distance_score
            
            # Factor 3: Análisis de sectores
            sector_voisins = [22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25]
            sector_tiers = [27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33]
            sector_orphelins = [17, 34, 6, 1, 20, 14, 31, 9]
            
            # Contar apariciones por sector
            voisins_count = sum(1 for n in recent_numbers[:10] if n in sector_voisins)
            tiers_count = sum(1 for n in recent_numbers[:10] if n in sector_tiers)
            orphelins_count = sum(1 for n in recent_numbers[:10] if n in sector_orphelins)
            
            # Bonificar sector menos activo
            if voisins_count <= tiers_count and voisins_count <= orphelins_count:
                for num in sector_voisins:
                    candidate_scores[num] = candidate_scores.get(num, 0) + 0.5
            elif tiers_count <= orphelins_count:
                for num in sector_tiers:
                    candidate_scores[num] = candidate_scores.get(num, 0) + 0.5
            else:
                for num in sector_orphelins:
                    candidate_scores[num] = candidate_scores.get(num, 0) + 0.5
            
            # Seleccionar top números por puntuación
            sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
            top_numbers = [num for num, score in sorted_candidates[:15]]
            
            return {
                'type': 'hybrid_analysis',
                'method': 'Análisis Híbrido Multi-Factor',
                'predicted_numbers': top_numbers,
                'confidence': 0.65,
                'description': f'Combinación de frecuencia, distancia y análisis sectorial'
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis híbrido: {e}")
            return None