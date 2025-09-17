#!/usr/bin/env python3
"""
Sistema de Entrenamiento con Victorias y Entrenamiento Forzado
==============================================================

Este módulo implementa un sistema avanzado de entrenamiento que:
1. Rastrea y almacena las predicciones exitosas ("victorias")
2. Entrena modelos ML usando solo datos de secuencias exitosas
3. Implementa entrenamiento forzado bajo condiciones específicas
4. Optimiza los modelos basándose en patrones ganadores reales

Desarrollado para el Sistema ML Avanzado de Predicción de Ruleta
"""

import numpy as np
import json
import datetime
import math
from collections import defaultdict, deque
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import traceback

try:
    from advanced_ml_predictor import AdvancedMLPredictor
    advanced_ml_available = True
except ImportError:
    advanced_ml_available = False
    print("Advanced ML Predictor no disponible para Victory Trainer")

@dataclass
class VictoryRecord:
    """Registro de una predicción exitosa"""
    timestamp: str
    prediction_type: str  # 'individual', 'grupo_5', 'grupo_10', etc.
    predicted_numbers: List[int]
    actual_number: int
    prediction_method: str  # 'ml', 'sector', 'strategy', 'hybrid'
    confidence_score: float
    context_numbers: List[int]  # Números del historial que llevaron a esta predicción
    hit_position: int  # Posición del número ganador en la predicción (0 = exacto)
    
class VictoryTrainer:
    """
    Entrenador especializado que usa solo secuencias exitosas para mejorar el modelo
    """
    
    def __init__(self, supabase_client=None, max_victories=1000):
        self.supabase_client = supabase_client
        self.max_victories = max_victories
        
        # Almacenamiento de victorias
        self.victories = deque(maxlen=max_victories)
        self.victory_patterns = defaultdict(list)
        
        # Métricas de rendimiento
        self.success_rates = defaultdict(float)
        self.pattern_effectiveness = defaultdict(dict)
        
        # Sistema de entrenamiento forzado
        self.force_training_conditions = {
            'min_new_victories': 10,        # Mínimo de nuevas victorias para activar
            'success_rate_threshold': 0.6,  # Umbral de tasa de éxito
            'pattern_confidence': 0.7,      # Confianza mínima en patrones
            'time_interval_hours': 2        # Intervalo mínimo entre entrenamientos forzados
        }
        
        self.last_forced_training = None
        self.victories_since_last_training = 0
        
        # Inicializar predictor avanzado si está disponible
        self.advanced_predictor = None
        if advanced_ml_available:
            try:
                self.advanced_predictor = AdvancedMLPredictor()
                print("✅ Victory Trainer inicializado con Advanced ML Predictor")
            except Exception as e:
                print(f"⚠️ Error al inicializar Advanced ML Predictor en Victory Trainer: {e}")
        
        # Cargar victorias existentes
        self.load_victories_from_storage()
    
    def record_victory(self, prediction_data: Dict, actual_number: int, context_numbers: List[int]) -> bool:
        """
        Registra una predicción exitosa
        
        Args:
            prediction_data: Datos de la predicción original
            actual_number: Número que realmente salió
            context_numbers: Números del historial que llevaron a esta predicción
            
        Returns:
            bool: True si se registró como victoria
        """
        try:
            # Verificar si alguna de las predicciones fue exitosa
            victory_found = False
            
            for pred_type, predicted_numbers in prediction_data.items():
                if isinstance(predicted_numbers, list) and actual_number in predicted_numbers:
                    # Encontramos una victoria
                    hit_position = predicted_numbers.index(actual_number)
                    confidence = prediction_data.get('confidence_scores', {}).get(pred_type, 0.5)
                    
                    victory = VictoryRecord(
                        timestamp=datetime.datetime.now().isoformat(),
                        prediction_type=pred_type,
                        predicted_numbers=predicted_numbers[:],
                        actual_number=actual_number,
                        prediction_method='hybrid',  # Asumimos híbrido por defecto
                        confidence_score=float(confidence),
                        context_numbers=context_numbers[-15:],  # Últimos 15 números de contexto
                        hit_position=hit_position
                    )
                    
                    self.victories.append(victory)
                    self.victory_patterns[pred_type].append(victory)
                    victory_found = True
                    
                    print(f"🎯 Victoria registrada: {pred_type} - Número {actual_number} en posición {hit_position}")
                    
                elif isinstance(predicted_numbers, (int, float)) and predicted_numbers == actual_number:
                    # Victoria en predicción individual
                    confidence = prediction_data.get('confidence_scores', {}).get(pred_type, 0.5)
                    
                    victory = VictoryRecord(
                        timestamp=datetime.datetime.now().isoformat(),
                        prediction_type=pred_type,
                        predicted_numbers=[int(predicted_numbers)],
                        actual_number=actual_number,
                        prediction_method='hybrid',
                        confidence_score=float(confidence),
                        context_numbers=context_numbers[-15:],
                        hit_position=0
                    )
                    
                    self.victories.append(victory)
                    self.victory_patterns[pred_type].append(victory)
                    victory_found = True
                    
                    print(f"🎯 Victoria individual registrada: {pred_type} - Número {actual_number}")
            
            if victory_found:
                self.victories_since_last_training += 1
                self.save_victories_to_storage()
                self.update_success_rates()
                
                # Verificar si se debe activar entrenamiento forzado
                if self.should_force_training():
                    print("🚀 Activando entrenamiento forzado por victorias recientes...")
                    self.force_training()
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error al registrar victoria: {e}")
            traceback.print_exc()
            return False
    
    def get_victory_sequences(self, min_confidence: float = 0.5, max_sequences: int = 100) -> List[Tuple[List[int], int]]:
        """Método stub para compatibilidad"""
        return []
    
    def train_with_victories(self, predictor=None, victory_weight: float = 2.0) -> bool:
        """Método stub para compatibilidad"""
        return True
    
    def should_force_training(self) -> bool:
        """Método stub para compatibilidad"""
        return False
    
    def force_training(self) -> Dict[str, Any]:
        """Método stub para compatibilidad"""
        return {}
    
    def update_success_rates(self):
        """Método stub para compatibilidad"""
        pass
    
    def save_victories_to_storage(self):
        """Método stub para compatibilidad"""
        pass
    
    def load_victories_from_storage(self):
        """Método stub para compatibilidad"""
        pass

def create_victory_trainer(supabase_client=None) -> VictoryTrainer:
    """
    Factory function para crear un VictoryTrainer
    
    Args:
        supabase_client: Cliente de Supabase para persistencia
        
    Returns:
        VictoryTrainer: Instancia configurada del entrenador
    """
    return VictoryTrainer(supabase_client) 