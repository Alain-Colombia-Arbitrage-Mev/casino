#!/usr/bin/env python3
"""
AI Predictor para Ruleta
Sistema de predicción inteligente basado en patrones históricos
"""

import json
import redis
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass
import random

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Resultado de una predicción"""
    prediction_id: str
    timestamp: str
    last_number: int
    predicted_numbers: List[int]
    prediction_groups: Dict[str, List[int]]  # Múltiples grupos de números
    prediction_type: str  # 'individual', 'group', 'color', 'sector'
    confidence: float
    reasoning: str

@dataclass
class GameResult:
    """Resultado de un juego"""
    prediction_id: str
    actual_number: int
    predicted_numbers: List[int]
    prediction_type: str
    is_winner: bool
    timestamp: str
    confidence: float

class RouletteAIPredictor:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        
        # Definir sectores de la ruleta
        self.sectors = {
            'voisins_zero': [22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25],
            'tiers': [27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33],
            'orphelins': [17, 34, 6, 1, 20, 14, 31, 9]
        }
        
        # Números por color
        self.red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        self.black_numbers = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
        
        # Patrones de análisis
        self.analysis_patterns = {
            'hot_numbers': [],
            'cold_numbers': [],
            'recent_colors': [],
            'sector_frequency': {},
            'number_gaps': {}
        }
    
    def get_latest_number(self) -> Optional[int]:
        """Obtener el último número desde Redis"""
        try:
            latest = self.redis_client.get('roulette:latest')
            if latest:
                return int(latest)
            return None
        except Exception as e:
            logger.error(f"Error obteniendo último número: {e}")
            return None
    
    def get_history(self, limit: int = 50) -> List[int]:
        """Obtener historial de números desde Redis"""
        try:
            history = self.redis_client.lrange('roulette:history', 0, limit - 1)
            return [int(num) for num in history if num.isdigit()]
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []
    
    def analyze_patterns(self, history: List[int]) -> Dict:
        """Analizar patrones en el historial"""
        if not history:
            return {}
        
        # Frecuencia de números
        number_freq = {}
        for num in history:
            number_freq[num] = number_freq.get(num, 0) + 1
        
        # Números calientes y fríos
        sorted_freq = sorted(number_freq.items(), key=lambda x: x[1], reverse=True)
        hot_numbers = [num for num, freq in sorted_freq[:8]]
        cold_numbers = [num for num, freq in sorted_freq[-8:]]
        
        # Análisis de colores recientes
        recent_colors = []
        for num in history[:10]:
            if num == 0:
                recent_colors.append('green')
            elif num in self.red_numbers:
                recent_colors.append('red')
            else:
                recent_colors.append('black')
        
        # Análisis de sectores
        sector_freq = {}
        for sector_name, sector_nums in self.sectors.items():
            count = sum(1 for num in history[:20] if num in sector_nums)
            sector_freq[sector_name] = count
        
        # Análisis de gaps (distancia entre repeticiones)
        gaps = {}
        for i, num in enumerate(history):
            if num in history[i+1:]:
                next_occurrence = history[i+1:].index(num) + 1
                if num not in gaps:
                    gaps[num] = []
                gaps[num].append(next_occurrence)
        
        return {
            'hot_numbers': hot_numbers,
            'cold_numbers': cold_numbers,
            'recent_colors': recent_colors,
            'sector_frequency': sector_freq,
            'number_gaps': gaps,
            'total_spins': len(history)
        }
    
    def predict_individual_numbers(self, analysis: Dict) -> Tuple[List[int], float, str]:
        """Predecir números individuales basado en análisis"""
        hot_numbers = analysis.get('hot_numbers', [])
        cold_numbers = analysis.get('cold_numbers', [])
        recent_colors = analysis.get('recent_colors', [])
        
        # Estrategia: combinar números calientes con algunos fríos
        predicted = []
        reasoning = []
        
        # Agregar números calientes (60% de la predicción)
        if hot_numbers:
            hot_selection = random.sample(hot_numbers, min(3, len(hot_numbers)))
            predicted.extend(hot_selection)
            reasoning.append(f"Números calientes: {hot_selection}")
        
        # Agregar algunos números fríos (20% de la predicción)
        if cold_numbers:
            cold_selection = random.sample(cold_numbers, min(1, len(cold_numbers)))
            predicted.extend(cold_selection)
            reasoning.append(f"Números fríos: {cold_selection}")
        
        # Análisis de color para balance (20% de la predicción)
        if recent_colors:
            color_count = {'red': recent_colors.count('red'),
                          'black': recent_colors.count('black'),
                          'green': recent_colors.count('green')}
            
            # Si hay desbalance, predecir el color menos frecuente
            min_color = min(color_count.items(), key=lambda x: x[1])[0]
            if min_color == 'red':
                color_nums = random.sample(self.red_numbers, 2)
            elif min_color == 'black':
                color_nums = random.sample(self.black_numbers, 2)
            else:
                color_nums = [0]
            
            predicted.extend(color_nums)
            reasoning.append(f"Balance de color ({min_color}): {color_nums}")
        
        # Remover duplicados y limitar a 6 números
        predicted = list(set(predicted))[:6]
        
        # Calcular confianza basada en la calidad del análisis
        confidence = min(0.85, 0.3 + (len(analysis.get('hot_numbers', [])) * 0.05) +
                        (analysis.get('total_spins', 0) * 0.01))
        
        return predicted, confidence, " | ".join(reasoning)
    
    def generate_multiple_groups(self, analysis: Dict) -> Tuple[Dict[str, List[int]], float, str]:
        """Generar múltiples grupos de números con diferentes tamaños usando AI y probabilidades"""
        hot_numbers = analysis.get('hot_numbers', [])
        cold_numbers = analysis.get('cold_numbers', [])
        recent_colors = analysis.get('recent_colors', [])
        
        # Todos los números de la ruleta
        all_numbers = list(range(37))  # 0-36
        
        # 🛡️ PROTECCIÓN DEL CERO: Detectar si el 0 apareció recientemente
        history = self.get_history(15)  # Últimos 15 números
        zero_appeared_recently = 0 in history[:10]  # En los últimos 10
        zero_last_position = history.index(0) if 0 in history else -1
        
        # Protección más inteligente: activar si el 0 no ha salido en mucho tiempo O si salió muy recientemente
        zero_protection = (zero_appeared_recently or 
                          (zero_last_position == -1 and len(history) >= 10) or  # No ha salido en 15+ giros
                          (zero_last_position > 20))  # No ha salido en 20+ giros
        
        logger.info(f"🛡️ PROTECCIÓN DEL CERO: {'ACTIVADA' if zero_protection else 'INACTIVA'} (Cero reciente: {zero_appeared_recently})")
        
        # Crear pools de números con diferentes estrategias usando probabilidades
        hot_pool = hot_numbers[:12] if hot_numbers else []
        cold_pool = cold_numbers[:8] if cold_numbers else []
        
        # Análisis probabilístico de colores
        color_probabilities = {}
        if recent_colors and len(recent_colors) >= 5:
            color_count = {'red': recent_colors.count('red'),
                          'black': recent_colors.count('black'),
                          'green': recent_colors.count('green')}
            total_colors = len(recent_colors)
            
            # Calcular probabilidades inversas (apostar al menos frecuente)
            for color, count in color_count.items():
                color_probabilities[color] = 1.0 - (count / total_colors)
            
            # Seleccionar color con mayor probabilidad inversa
            best_color = max(color_probabilities.items(), key=lambda x: x[1])[0]
            
            if best_color == 'red':
                color_balance = {'preferred': self.red_numbers, 'probability': color_probabilities[best_color]}
            elif best_color == 'black':
                color_balance = {'preferred': self.black_numbers, 'probability': color_probabilities[best_color]}
            else:
                color_balance = {'preferred': [0], 'probability': color_probabilities[best_color]}
        else:
            color_balance = {'preferred': self.red_numbers, 'probability': 0.5}
        
        # Análisis probabilístico de sectores
        sector_analysis = analysis.get('sector_frequency', {})
        if sector_analysis:
            # Usar probabilidades inversas para sectores también
            total_sector_hits = sum(sector_analysis.values())
            sector_probabilities = {}
            for sector, hits in sector_analysis.items():
                sector_probabilities[sector] = 1.0 - (hits / total_sector_hits) if total_sector_hits > 0 else 0.33
            
            best_sector = max(sector_probabilities.items(), key=lambda x: x[1])[0]
            sector_numbers = self.sectors[best_sector]
            sector_probability = sector_probabilities[best_sector]
        else:
            sector_numbers = self.sectors['voisins_zero']
            sector_probability = 0.5
        
        # Generar grupos con IA mejorada y protección del cero
        groups = {}
        reasoning_parts = []
        
        # 🛡️ Función helper para añadir protección del cero
        def add_zero_protection(group_list, group_name):
            if zero_protection and 0 not in group_list:
                if len(group_list) > 0:
                    # Reemplazar un número aleatorio con el 0
                    replace_idx = random.randint(0, len(group_list) - 1)
                    group_list[replace_idx] = 0
                    logger.info(f"🛡️ Cero añadido a {group_name} como protección")
                else:
                    group_list.append(0)
            return group_list
        
        # Grupo de 20 números - Estrategia AI balanceada con probabilidades
        group_20 = []
        
        # Añadir números calientes con probabilidad ponderada
        if hot_pool:
            hot_count = min(10, len(hot_pool))
            # Usar probabilidades decrecientes para números calientes
            weighted_hot = []
            for i, num in enumerate(hot_pool[:hot_count]):
                weight = 1.0 - (i * 0.1)  # Peso decreciente
                if random.random() < weight:
                    weighted_hot.append(num)
            group_20.extend(weighted_hot[:8])
        
        # Añadir números fríos con probabilidad menor
        if cold_pool:
            cold_selection = [num for num in cold_pool[:6] if random.random() < 0.4]
            group_20.extend(cold_selection[:3])
        
        # Añadir números del color preferido con probabilidad
        if color_balance.get('preferred') and random.random() < color_balance['probability']:
            color_nums = [n for n in color_balance['preferred'] if n not in group_20]
            color_selection = random.sample(color_nums, min(5, len(color_nums)))
            group_20.extend(color_selection)
        
        # Añadir números del sector con probabilidad
        if random.random() < sector_probability:
            sector_nums = [n for n in sector_numbers if n not in group_20]
            sector_selection = random.sample(sector_nums, min(4, len(sector_nums)))
            group_20.extend(sector_selection)
        
        # Completar hasta 20 números
        remaining = [n for n in all_numbers if n not in group_20]
        while len(group_20) < 19:  # Dejar espacio para posible protección del cero
            if remaining:
                group_20.append(remaining.pop(random.randint(0, len(remaining) - 1)))
            else:
                break
        
        # 🛡️ Aplicar protección del cero
        group_20 = add_zero_protection(group_20, "Grupo 20")
        groups['group_20'] = list(set(group_20))[:20]
        reasoning_parts.append(f"Grupo 20: AI balanceado (prob. color: {color_balance['probability']:.2f}, sector: {sector_probability:.2f}) {'🛡️' if 0 in groups['group_20'] else ''}")
        
        # Grupo de 15 números - AI enfocado en patrones calientes
        group_15 = []
        
        # Priorizar números calientes con alta probabilidad
        if hot_pool:
            for num in hot_pool[:10]:
                if random.random() < 0.8:  # 80% probabilidad para calientes
                    group_15.append(num)
        
        # Añadir números del sector más probable
        sector_nums = [n for n in sector_numbers if n not in group_15]
        sector_add = random.sample(sector_nums, min(6, len(sector_nums)))
        group_15.extend(sector_add)
        
        # Completar hasta 15
        remaining = [n for n in all_numbers if n not in group_15]
        while len(group_15) < 14:
            if remaining:
                group_15.append(remaining.pop(random.randint(0, len(remaining) - 1)))
            else:
                break
        
        # 🛡️ Aplicar protección del cero
        group_15 = add_zero_protection(group_15, "Grupo 15")
        groups['group_15'] = list(set(group_15))[:15]
        reasoning_parts.append(f"Grupo 15: AI calientes + sector {'🛡️' if 0 in groups['group_15'] else ''}")
        
        # Grupo de 12 números - AI sector específico
        group_12 = []
        
        # Enfoque en sector con números calientes
        sector_hot = [n for n in sector_numbers if n in hot_pool]
        group_12.extend(sector_hot[:6])
        
        # Añadir resto del sector
        remaining_sector = [n for n in sector_numbers if n not in group_12]
        group_12.extend(random.sample(remaining_sector, min(4, len(remaining_sector))))
        
        # Añadir números del color preferido
        if color_balance.get('preferred'):
            color_nums = [n for n in color_balance['preferred'] if n not in group_12]
            group_12.extend(random.sample(color_nums, min(2, len(color_nums))))
        
        # Completar hasta 12
        remaining = [n for n in all_numbers if n not in group_12]
        while len(group_12) < 11:
            if remaining:
                group_12.append(remaining.pop(random.randint(0, len(remaining) - 1)))
            else:
                break
        
        # 🛡️ Aplicar protección del cero
        group_12 = add_zero_protection(group_12, "Grupo 12")
        groups['group_12'] = list(set(group_12))[:12]
        reasoning_parts.append(f"Grupo 12: AI sector + color {'🛡️' if 0 in groups['group_12'] else ''}")
        
        # Grupo de 8 números - AI ultra selectivo
        group_8 = []
        
        # Solo los números más calientes con alta probabilidad
        if hot_pool:
            for num in hot_pool[:6]:
                if random.random() < 0.9:  # 90% probabilidad para ultra calientes
                    group_8.append(num)
        
        # Añadir 1-2 números fríos como contraste
        if cold_pool and len(group_8) < 7:
            cold_add = random.sample(cold_pool[:3], min(1, len(cold_pool[:3])))
            group_8.extend(cold_add)
        
        # Completar hasta 8
        remaining = [n for n in all_numbers if n not in group_8]
        while len(group_8) < 7:
            if remaining:
                group_8.append(remaining.pop(random.randint(0, len(remaining) - 1)))
            else:
                break
        
        # 🛡️ Aplicar protección del cero
        group_8 = add_zero_protection(group_8, "Grupo 8")
        groups['group_8'] = list(set(group_8))[:8]
        reasoning_parts.append(f"Grupo 8: AI ultra selectivo {'🛡️' if 0 in groups['group_8'] else ''}")
        
        # Grupo de 4 números - AI máxima precisión
        group_4 = []
        
        # Solo los 3 números más calientes
        if hot_pool:
            group_4.extend(hot_pool[:3])
        
        # Añadir el número del color más probable
        if color_balance.get('preferred') and len(group_4) < 4:
            color_nums = [n for n in color_balance['preferred'] if n not in group_4]
            if color_nums:
                group_4.append(random.choice(color_nums))
        
        # Completar hasta 4
        remaining = [n for n in all_numbers if n not in group_4]
        while len(group_4) < 3:
            if remaining:
                group_4.append(remaining.pop(random.randint(0, len(remaining) - 1)))
            else:
                break
        
        # 🛡️ Aplicar protección del cero
        group_4 = add_zero_protection(group_4, "Grupo 4")
        groups['group_4'] = list(set(group_4))[:4]
        reasoning_parts.append(f"Grupo 4: AI máxima precisión {'🛡️' if 0 in groups['group_4'] else ''}")
        
        # Calcular confianza basada en calidad de datos y probabilidades
        base_confidence = 0.4
        hot_bonus = min(0.2, len(hot_pool) * 0.02)
        history_bonus = min(0.15, analysis.get('total_spins', 0) * 0.003)
        probability_bonus = (color_balance['probability'] + sector_probability) * 0.1
        zero_bonus = 0.05 if zero_protection else 0
        
        confidence = min(0.85, base_confidence + hot_bonus + history_bonus + probability_bonus + zero_bonus)
        
        return groups, confidence, " | ".join(reasoning_parts)
    
    def predict_sectors(self, analysis: Dict) -> Tuple[str, List[int], float, str]:
        """Predecir sector basado en frecuencias"""
        sector_freq = analysis.get('sector_frequency', {})
        
        if not sector_freq:
            # Predicción por defecto
            sector = 'voisins_zero'
            return sector, self.sectors[sector], 0.4, "Predicción por defecto"
        
        # Encontrar el sector menos frecuente (estrategia contraria)
        min_sector = min(sector_freq.items(), key=lambda x: x[1])[0]
        sector_numbers = self.sectors[min_sector]
        
        confidence = 0.6 + (20 - sector_freq[min_sector]) * 0.02
        reasoning = f"Sector {min_sector} menos frecuente ({sector_freq[min_sector]} apariciones)"
        
        return min_sector, sector_numbers, confidence, reasoning
    
    def predict_colors(self, analysis: Dict) -> Tuple[str, float, str]:
        """Predecir color basado en tendencias"""
        recent_colors = analysis.get('recent_colors', [])
        
        if not recent_colors:
            return 'red', 0.4, "Predicción por defecto"
        
        # Contar colores recientes
        color_count = {
            'red': recent_colors.count('red'),
            'black': recent_colors.count('black'),
            'green': recent_colors.count('green')
        }
        
        # Estrategia: predecir el color menos frecuente
        min_color = min(color_count.items(), key=lambda x: x[1])[0]
        
        # Calcular confianza basada en el desbalance
        total = len(recent_colors)
        min_freq = color_count[min_color]
        confidence = 0.5 + ((total - min_freq * 3) / total) * 0.3
        
        reasoning = f"Color {min_color} menos frecuente: {min_freq}/{total} en últimos giros"
        
        return min_color, confidence, reasoning
    
    def make_prediction(self, prediction_type: str = 'individual') -> Optional[PredictionResult]:
        """Hacer una predicción completa"""
        try:
            # Obtener último número y historial
            last_number = self.get_latest_number()
            if last_number is None:
                logger.warning("No hay último número disponible")
                return None
            
            history = self.get_history(50)
            if not history:
                logger.warning("No hay historial disponible")
                return None
            
            # Analizar patrones
            analysis = self.analyze_patterns(history)
            
            # Generar ID único para la predicción
            prediction_id = f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
            timestamp = datetime.now().isoformat()
            
            # Generar múltiples grupos de números
            prediction_groups, group_confidence, group_reasoning = self.generate_multiple_groups(analysis)
            
            # Hacer predicción según el tipo
            if prediction_type == 'individual':
                predicted_numbers, confidence, reasoning = self.predict_individual_numbers(analysis)
            elif prediction_type == 'groups':
                # Usar el grupo de 8 números como predicción principal
                predicted_numbers = prediction_groups.get('group_8', [])
                confidence = group_confidence
                reasoning = group_reasoning
            elif prediction_type == 'sector':
                sector, predicted_numbers, confidence, reasoning = self.predict_sectors(analysis)
                reasoning = f"Sector {sector}: {reasoning}"
            elif prediction_type == 'color':
                color, confidence, reasoning = self.predict_colors(analysis)
                if color == 'red':
                    predicted_numbers = self.red_numbers
                elif color == 'black':
                    predicted_numbers = self.black_numbers
                else:
                    predicted_numbers = [0]
                reasoning = f"Color {color}: {reasoning}"
            else:
                logger.error(f"Tipo de predicción no válido: {prediction_type}")
                return None
            
            # Crear resultado de predicción
            result = PredictionResult(
                prediction_id=prediction_id,
                timestamp=timestamp,
                last_number=last_number,
                predicted_numbers=predicted_numbers,
                prediction_groups=prediction_groups,
                prediction_type=prediction_type,
                confidence=confidence,
                reasoning=reasoning
            )
            
            # Guardar predicción en Redis
            self.save_prediction(result)
            
            logger.info(f"Predicción creada: {prediction_id} - {predicted_numbers} (confianza: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error haciendo predicción: {e}")
            return None
    
    def save_prediction(self, prediction: PredictionResult):
        """Guardar predicción en Redis"""
        try:
            prediction_data = {
                'prediction_id': prediction.prediction_id,
                'timestamp': prediction.timestamp,
                'last_number': prediction.last_number,
                'predicted_numbers': json.dumps(prediction.predicted_numbers),
                'prediction_groups': json.dumps(prediction.prediction_groups),
                'prediction_type': prediction.prediction_type,
                'confidence': prediction.confidence,
                'reasoning': prediction.reasoning,
                'status': 'pending'
            }
            
            # Guardar en hash de predicciones
            self.redis_client.hset(f'prediction:{prediction.prediction_id}', mapping=prediction_data)
            
            # Agregar a lista de predicciones pendientes
            self.redis_client.lpush('ai:pending_predictions', prediction.prediction_id)
            
            # Mantener solo las últimas 100 predicciones
            self.redis_client.ltrim('ai:pending_predictions', 0, 99)
            
            logger.info(f"Predicción guardada: {prediction.prediction_id}")
            
        except Exception as e:
            logger.error(f"Error guardando predicción: {e}")
    
    def check_prediction_result(self, prediction_id: str, actual_number: int) -> Optional[GameResult]:
        """Verificar resultado de una predicción"""
        try:
            # Obtener datos de la predicción
            prediction_data = self.redis_client.hgetall(f'prediction:{prediction_id}')
            if not prediction_data:
                logger.error(f"Predicción no encontrada: {prediction_id}")
                return None
            
            predicted_numbers = json.loads(prediction_data['predicted_numbers'])
            prediction_type = prediction_data['prediction_type']
            confidence = float(prediction_data['confidence'])
            
            # Verificar si ganó
            is_winner = actual_number in predicted_numbers
            
            # Crear resultado del juego
            result = GameResult(
                prediction_id=prediction_id,
                actual_number=actual_number,
                predicted_numbers=predicted_numbers,
                prediction_type=prediction_type,
                is_winner=is_winner,
                timestamp=datetime.now().isoformat(),
                confidence=confidence
            )
            
            # Guardar resultado
            try:
                self.save_game_result(result)
            except Exception as save_error:
                logger.error(f"Error guardando resultado: {save_error}")
            
            # Actualizar estado de la predicción
            try:
                self.redis_client.hset(f'prediction:{prediction_id}', 'status', 'completed')
                self.redis_client.hset(f'prediction:{prediction_id}', 'actual_number', actual_number)
                self.redis_client.hset(f'prediction:{prediction_id}', 'is_winner', '1' if is_winner else '0')
                
                # Remover de predicciones pendientes
                self.redis_client.lrem('ai:pending_predictions', 1, prediction_id)
            except Exception as update_error:
                logger.error(f"Error actualizando predicción: {update_error}")
            
            logger.info(f"Resultado verificado: {prediction_id} - {'GANÓ' if is_winner else 'PERDIÓ'}")
            return result
            
        except Exception as e:
            logger.error(f"Error verificando resultado: {e}")
            return None
    
    def save_game_result(self, result: GameResult):
        """Guardar resultado del juego en Redis"""
        try:
            result_data = {
                'prediction_id': result.prediction_id,
                'actual_number': result.actual_number,
                'predicted_numbers': json.dumps(result.predicted_numbers),
                'prediction_type': result.prediction_type,
                'is_winner': '1' if result.is_winner else '0',
                'timestamp': result.timestamp,
                'confidence': result.confidence
            }
            
            # Guardar resultado individual
            try:
                self.redis_client.hset(f'result:{result.prediction_id}', mapping=result_data)
                
                # Agregar a lista de resultados
                self.redis_client.lpush('game:results', result.prediction_id)
                
                # Mantener solo los últimos 200 resultados
                self.redis_client.ltrim('game:results', 0, 199)
            except Exception as redis_error:
                logger.error(f"Error en operaciones Redis: {redis_error}")
            
            # Actualizar estadísticas de victorias/derrotas
            try:
                if result.is_winner:
                    self.redis_client.incr('stats:wins')
                else:
                    self.redis_client.incr('stats:losses')
                
                # Actualizar estadísticas por tipo de predicción
                self.redis_client.incr(f'stats:{result.prediction_type}:total')
                if result.is_winner:
                    self.redis_client.incr(f'stats:{result.prediction_type}:wins')
            except Exception as stats_error:
                logger.error(f"Error actualizando estadísticas: {stats_error}")
            
            logger.info(f"Resultado guardado: {result.prediction_id}")
            
        except Exception as e:
            logger.error(f"Error guardando resultado: {e}")
    
    def get_pending_predictions(self) -> List[str]:
        """Obtener predicciones pendientes"""
        try:
            return self.redis_client.lrange('ai:pending_predictions', 0, -1)
        except Exception as e:
            logger.error(f"Error obteniendo predicciones pendientes: {e}")
            return []
    
    def get_game_stats(self) -> Dict:
        """Obtener estadísticas del juego"""
        try:
            wins = int(self.redis_client.get('stats:wins') or 0)
            losses = int(self.redis_client.get('stats:losses') or 0)
            total = wins + losses
            
            win_rate = (wins / total * 100) if total > 0 else 0
            
            # Estadísticas por tipo
            types_stats = {}
            for pred_type in ['individual', 'sector', 'color']:
                type_total = int(self.redis_client.get(f'stats:{pred_type}:total') or 0)
                type_wins = int(self.redis_client.get(f'stats:{pred_type}:wins') or 0)
                type_rate = (type_wins / type_total * 100) if type_total > 0 else 0
                
                types_stats[pred_type] = {
                    'total': type_total,
                    'wins': type_wins,
                    'losses': type_total - type_wins,
                    'win_rate': type_rate
                }
            
            return {
                'total_games': total,
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'by_type': types_stats
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}