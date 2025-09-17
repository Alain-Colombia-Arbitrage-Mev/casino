#!/usr/bin/env python3
"""
AI Predictor para Ruleta - Optimizado para Redis
Sistema de predicción inteligente usando únicamente Redis como fuente de datos
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
    prediction_groups: Dict[str, List[int]]
    prediction_type: str
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

        logger.info("🤖 AI Predictor inicializado (Redis optimizado)")

    def get_color_for_number(self, number: int) -> str:
        """Obtener color para número"""
        if number == 0:
            return 'green'
        return 'red' if number in self.red_numbers else 'black'

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
        """Obtener historial de números desde Redis optimizado"""
        try:
            # Obtener directamente desde la lista de Redis
            history_raw = self.redis_client.lrange('roulette:history', 0, limit - 1)
            history = []

            for num_str in history_raw:
                try:
                    number = int(num_str)
                    if 0 <= number <= 36:  # Validar rango
                        history.append(number)
                except ValueError:
                    continue

            logger.info(f"📊 Historial obtenido: {len(history)} números válidos")
            return history

        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []

    def analyze_patterns_optimized(self, history: List[int]) -> Dict:
        """Análisis optimizado de patrones usando Redis"""
        if not history:
            return {}

        try:
            # Análisis de frecuencias (más eficiente)
            number_freq = {}
            color_sequence = []
            sector_hits = {sector: 0 for sector in self.sectors.keys()}

            # Un solo bucle para todos los análisis
            for i, number in enumerate(history):
                # Frecuencia de números
                number_freq[number] = number_freq.get(number, 0) + 1

                # Secuencia de colores (solo últimos 15)
                if i < 15:
                    color_sequence.append(self.get_color_for_number(number))

                # Análisis de sectores (solo últimos 25)
                if i < 25:
                    for sector_name, sector_nums in self.sectors.items():
                        if number in sector_nums:
                            sector_hits[sector_name] += 1

            # Calcular números calientes y fríos más eficientemente
            sorted_freq = sorted(number_freq.items(), key=lambda x: x[1], reverse=True)
            hot_numbers = [num for num, _ in sorted_freq[:12]]  # Top 12 calientes
            cold_numbers = [num for num, _ in sorted_freq[-8:]]  # Bottom 8 fríos

            # Análisis de gaps simplificado (solo para números calientes)
            gaps = {}
            for hot_num in hot_numbers[:6]:  # Solo los 6 más calientes
                positions = [i for i, num in enumerate(history[:30]) if num == hot_num]
                if len(positions) > 1:
                    gaps[hot_num] = [positions[i] - positions[i+1] for i in range(len(positions)-1)]

            # Análisis de rachas de colores
            color_streaks = self._analyze_color_streaks(color_sequence)

            return {
                'hot_numbers': hot_numbers,
                'cold_numbers': cold_numbers,
                'recent_colors': color_sequence,
                'sector_frequency': sector_hits,
                'number_gaps': gaps,
                'total_spins': len(history),
                'color_streaks': color_streaks,
                'analysis_quality': min(1.0, len(history) / 50.0)  # Calidad del análisis
            }

        except Exception as e:
            logger.error(f"Error en análisis de patrones: {e}")
            return {}

    def _analyze_color_streaks(self, color_sequence: List[str]) -> Dict:
        """Analizar rachas de colores"""
        if not color_sequence:
            return {}

        streaks = {'red': 0, 'black': 0, 'green': 0}
        current_color = color_sequence[0]
        current_streak = 1
        max_streaks = {'red': 0, 'black': 0, 'green': 0}

        for color in color_sequence[1:]:
            if color == current_color:
                current_streak += 1
            else:
                max_streaks[current_color] = max(max_streaks[current_color], current_streak)
                current_color = color
                current_streak = 1

        max_streaks[current_color] = max(max_streaks[current_color], current_streak)

        return {
            'current_streak': current_streak,
            'current_color': current_color,
            'max_streaks': max_streaks
        }

    def generate_smart_groups(self, analysis: Dict) -> Tuple[Dict[str, List[int]], float, str]:
        """Generar grupos inteligentes optimizados"""
        hot_numbers = analysis.get('hot_numbers', [])
        cold_numbers = analysis.get('cold_numbers', [])
        recent_colors = analysis.get('recent_colors', [])
        sector_freq = analysis.get('sector_frequency', {})
        quality = analysis.get('analysis_quality', 0.5)

        # Todos los números
        all_numbers = list(range(37))

        # 🛡️ SISTEMA DE PROTECCIÓN INTELIGENTE
        history = self.get_history(20)

        # Protección del cero mejorada
        zero_protection = self._should_protect_zero(history)

        # Análisis probabilístico de colores
        color_probabilities = self._analyze_color_probabilities(recent_colors)

        # Análisis de sector óptimo
        optimal_sector = self._find_optimal_sector(sector_freq)

        groups = {}
        reasoning_parts = []

        # Grupo de 20 - Estrategia balanceada
        group_20 = self._build_group_20(hot_numbers, cold_numbers, color_probabilities, optimal_sector, all_numbers)
        if zero_protection['active']:
            group_20 = self._apply_zero_protection(group_20, "G20")
        groups['group_20'] = list(set(group_20))[:20]
        reasoning_parts.append(f"G20: Balanceado {'🛡️' if 0 in groups['group_20'] else ''}")

        # Grupo de 15 - Enfoque calientes + sector
        group_15 = self._build_group_15(hot_numbers, optimal_sector, all_numbers)
        if zero_protection['active']:
            group_15 = self._apply_zero_protection(group_15, "G15")
        groups['group_15'] = list(set(group_15))[:15]
        reasoning_parts.append(f"G15: Calientes+Sector {'🛡️' if 0 in groups['group_15'] else ''}")

        # Grupo de 12 - Selectivo
        group_12 = self._build_group_12(hot_numbers, color_probabilities, all_numbers)
        if zero_protection['active']:
            group_12 = self._apply_zero_protection(group_12, "G12")
        groups['group_12'] = list(set(group_12))[:12]
        reasoning_parts.append(f"G12: Selectivo {'🛡️' if 0 in groups['group_12'] else ''}")

        # Grupo de 9 - Precisión media
        group_9 = self._build_group_9(hot_numbers, cold_numbers, all_numbers)
        if zero_protection['active']:
            group_9 = self._apply_zero_protection(group_9, "G9")
        groups['group_9'] = list(set(group_9))[:9]
        reasoning_parts.append(f"G9: Precisión {'🛡️' if 0 in groups['group_9'] else ''}")

        # Grupo de 6 - Alta precisión
        group_6 = self._build_group_6(hot_numbers, all_numbers)
        if zero_protection['active']:
            group_6 = self._apply_zero_protection(group_6, "G6")
        groups['group_6'] = list(set(group_6))[:6]
        reasoning_parts.append(f"G6: Alta precisión {'🛡️' if 0 in groups['group_6'] else ''}")

        # Grupo de 4 - Máxima precisión
        group_4 = self._build_group_4(hot_numbers, color_probabilities, all_numbers)
        if zero_protection['active']:
            group_4 = self._apply_zero_protection(group_4, "G4")
        groups['group_4'] = list(set(group_4))[:4]
        reasoning_parts.append(f"G4: Máxima precisión {'🛡️' if 0 in groups['group_4'] else ''}")

        # Calcular confianza mejorada
        base_confidence = 0.4
        hot_bonus = min(0.2, len(hot_numbers) * 0.015)
        quality_bonus = quality * 0.15
        protection_bonus = 0.08 if zero_protection['active'] else 0
        color_bonus = max(color_probabilities.values()) * 0.1 if color_probabilities else 0

        confidence = min(0.88, base_confidence + hot_bonus + quality_bonus + protection_bonus + color_bonus)

        return groups, confidence, " | ".join(reasoning_parts)

    def _should_protect_zero(self, history: List[int]) -> Dict:
        """Determinar si se debe proteger el cero"""
        if not history:
            return {'active': False, 'reason': 'No history'}

        # Buscar posición del último cero
        zero_positions = [i for i, num in enumerate(history) if num == 0]

        if not zero_positions:
            # No hay ceros en historial reciente - proteger
            return {'active': True, 'reason': f'No zero in last {len(history)} spins'}

        last_zero_pos = zero_positions[0]  # Posición del cero más reciente

        # Proteger si el cero salió muy recientemente (últimos 3) o hace mucho (más de 15)
        if last_zero_pos <= 2:
            return {'active': True, 'reason': f'Zero very recent (pos {last_zero_pos})'}
        elif last_zero_pos >= 15:
            return {'active': True, 'reason': f'Zero too distant (pos {last_zero_pos})'}

        return {'active': False, 'reason': f'Zero at normal distance (pos {last_zero_pos})'}

    def _analyze_color_probabilities(self, recent_colors: List[str]) -> Dict:
        """Análisis probabilístico de colores"""
        if not recent_colors:
            return {}

        color_count = {'red': 0, 'black': 0, 'green': 0}
        for color in recent_colors:
            color_count[color] += 1

        total = len(recent_colors)
        # Probabilidades inversas (apostar al menos frecuente)
        probabilities = {}
        for color, count in color_count.items():
            probabilities[color] = 1.0 - (count / total) if total > 0 else 0.33

        return probabilities

    def _find_optimal_sector(self, sector_freq: Dict) -> Dict:
        """Encontrar sector óptimo"""
        if not sector_freq:
            return {'name': 'voisins_zero', 'numbers': self.sectors['voisins_zero'], 'score': 0.5}

        # Sector menos frecuente = mejor oportunidad
        min_sector = min(sector_freq.items(), key=lambda x: x[1])
        sector_name = min_sector[0]
        frequency = min_sector[1]

        return {
            'name': sector_name,
            'numbers': self.sectors[sector_name],
            'score': max(0.3, 1.0 - (frequency / 10.0))  # Score más alto = menos frecuente
        }

    def _build_group_20(self, hot_numbers, cold_numbers, color_probs, optimal_sector, all_numbers):
        """Construir grupo de 20 números - estrategia balanceada"""
        group = []

        # 50% números calientes
        if hot_numbers:
            group.extend(random.sample(hot_numbers, min(10, len(hot_numbers))))

        # 15% números fríos
        if cold_numbers:
            cold_selection = [n for n in cold_numbers if n not in group]
            group.extend(random.sample(cold_selection, min(3, len(cold_selection))))

        # 20% números del sector óptimo
        sector_nums = [n for n in optimal_sector['numbers'] if n not in group]
        group.extend(random.sample(sector_nums, min(4, len(sector_nums))))

        # 15% números del color más probable
        if color_probs:
            best_color = max(color_probs.items(), key=lambda x: x[1])[0]
            if best_color == 'red':
                color_nums = [n for n in self.red_numbers if n not in group]
            elif best_color == 'black':
                color_nums = [n for n in self.black_numbers if n not in group]
            else:
                color_nums = [0] if 0 not in group else []

            group.extend(random.sample(color_nums, min(3, len(color_nums))))

        # Completar hasta 19 (dejar espacio para protección)
        remaining = [n for n in all_numbers if n not in group]
        while len(group) < 19 and remaining:
            group.append(remaining.pop(random.randint(0, len(remaining) - 1)))

        return group

    def _build_group_15(self, hot_numbers, optimal_sector, all_numbers):
        """Construir grupo de 15 números - calientes + sector"""
        group = []

        # 70% números calientes
        if hot_numbers:
            group.extend(hot_numbers[:10])

        # 30% números del sector óptimo
        sector_nums = [n for n in optimal_sector['numbers'] if n not in group]
        group.extend(random.sample(sector_nums, min(4, len(sector_nums))))

        # Completar hasta 14
        remaining = [n for n in all_numbers if n not in group]
        while len(group) < 14 and remaining:
            group.append(remaining.pop(random.randint(0, len(remaining) - 1)))

        return group

    def _build_group_12(self, hot_numbers, color_probs, all_numbers):
        """Construir grupo de 12 números - selectivo"""
        group = []

        # 75% números calientes top
        if hot_numbers:
            group.extend(hot_numbers[:9])

        # 25% color más probable
        if color_probs:
            best_color = max(color_probs.items(), key=lambda x: x[1])[0]
            if best_color == 'red':
                color_nums = [n for n in self.red_numbers if n not in group]
            elif best_color == 'black':
                color_nums = [n for n in self.black_numbers if n not in group]
            else:
                color_nums = [0] if 0 not in group else []

            group.extend(random.sample(color_nums, min(2, len(color_nums))))

        # Completar hasta 11
        remaining = [n for n in all_numbers if n not in group]
        while len(group) < 11 and remaining:
            group.append(remaining.pop(random.randint(0, len(remaining) - 1)))

        return group

    def _build_group_9(self, hot_numbers, cold_numbers, all_numbers):
        """Construir grupo de 9 números - precisión media"""
        group = []

        # 80% números calientes top
        if hot_numbers:
            group.extend(hot_numbers[:7])

        # 20% contraste con fríos
        if cold_numbers:
            cold_selection = [n for n in cold_numbers if n not in group]
            group.extend(random.sample(cold_selection, min(1, len(cold_selection))))

        # Completar hasta 8
        remaining = [n for n in all_numbers if n not in group]
        while len(group) < 8 and remaining:
            group.append(remaining.pop(random.randint(0, len(remaining) - 1)))

        return group

    def _build_group_6(self, hot_numbers, all_numbers):
        """Construir grupo de 6 números - alta precisión"""
        group = []

        # 90% números súper calientes
        if hot_numbers:
            group.extend(hot_numbers[:5])

        # Completar hasta 5
        remaining = [n for n in all_numbers if n not in group]
        while len(group) < 5 and remaining:
            group.append(remaining.pop(random.randint(0, len(remaining) - 1)))

        return group

    def _build_group_4(self, hot_numbers, color_probs, all_numbers):
        """Construir grupo de 4 números - máxima precisión"""
        group = []

        # Top 3 números calientes
        if hot_numbers:
            group.extend(hot_numbers[:3])

        # Completar hasta 3
        remaining = [n for n in all_numbers if n not in group]
        while len(group) < 3 and remaining:
            group.append(remaining.pop(random.randint(0, len(remaining) - 1)))

        return group

    def _apply_zero_protection(self, group: List[int], group_name: str) -> List[int]:
        """Aplicar protección del cero reemplazando un número aleatorio"""
        if 0 not in group and group:
            replace_idx = random.randint(0, len(group) - 1)
            group[replace_idx] = 0
            logger.info(f"🛡️ Protección del cero aplicada a {group_name}")
        return group

    def make_prediction(self, prediction_type: str = 'groups') -> Optional[PredictionResult]:
        """Hacer predicción optimizada"""
        try:
            # Obtener datos
            last_number = self.get_latest_number()
            if last_number is None:
                logger.warning("No hay último número disponible")
                return None

            history = self.get_history(60)  # Más historial para mejor análisis
            if not history:
                logger.warning("No hay historial disponible")
                return None

            # Análisis optimizado
            analysis = self.analyze_patterns_optimized(history)

            # Generar ID único
            prediction_id = f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
            timestamp = datetime.now().isoformat()

            # Generar grupos inteligentes
            prediction_groups, confidence, reasoning = self.generate_smart_groups(analysis)

            # Seleccionar números principales según el tipo
            if prediction_type == 'groups':
                predicted_numbers = prediction_groups.get('group_6', [])
            else:
                predicted_numbers = prediction_groups.get('group_4', [])

            # Crear resultado
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

            # Guardar en Redis optimizado
            self.save_prediction_optimized(result)

            logger.info(f"🎯 Predicción creada: {prediction_id} - Confianza: {confidence:.2f}")
            return result

        except Exception as e:
            logger.error(f"Error haciendo predicción: {e}")
            return None

    def save_prediction_optimized(self, prediction: PredictionResult):
        """Guardar predicción optimizada en Redis"""
        try:
            # Usar pipeline para operaciones atómicas
            pipe = self.redis_client.pipeline()

            prediction_data = {
                'prediction_id': prediction.prediction_id,
                'timestamp': prediction.timestamp,
                'last_number': str(prediction.last_number),
                'predicted_numbers': json.dumps(prediction.predicted_numbers),
                'prediction_groups': json.dumps(prediction.prediction_groups),
                'prediction_type': prediction.prediction_type,
                'confidence': str(prediction.confidence),
                'reasoning': prediction.reasoning,
                'status': 'pending'
            }

            # Guardar predicción
            pipe.hset(f'prediction:{prediction.prediction_id}', mapping=prediction_data)

            # Añadir a lista de pendientes
            pipe.lpush('ai:pending_predictions', prediction.prediction_id)

            # Mantener solo las últimas 50 predicciones pendientes
            pipe.ltrim('ai:pending_predictions', 0, 49)

            # Ejecutar todas las operaciones
            pipe.execute()

            logger.info(f"💾 Predicción guardada: {prediction.prediction_id}")

        except Exception as e:
            logger.error(f"Error guardando predicción: {e}")

    def get_pending_predictions(self) -> List[str]:
        """Obtener predicciones pendientes optimizado"""
        try:
            pending = self.redis_client.lrange('ai:pending_predictions', 0, -1)
            return [pred_id for pred_id in pending if pred_id]
        except Exception as e:
            logger.error(f"Error obteniendo predicciones pendientes: {e}")
            return []

    def get_game_stats(self) -> Dict:
        """Obtener estadísticas del juego optimizadas"""
        try:
            # Obtener estadísticas globales de IA
            stats = self.redis_client.hgetall("ai:game_stats")

            total_predictions = int(stats.get('total_predictions', 0))
            total_wins = int(stats.get('total_wins', 0))
            total_losses = int(stats.get('total_losses', 0))

            win_rate = (total_wins / total_predictions * 100) if total_predictions > 0 else 0

            return {
                'total_games': total_predictions,
                'wins': total_wins,
                'losses': total_losses,
                'win_rate': round(win_rate, 2),
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}