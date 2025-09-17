import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from collections import Counter, defaultdict
import datetime
import math
import warnings
warnings.filterwarnings('ignore')

class AdvancedMLPredictor:
    def __init__(self):
        self.models = {}
        self.sector_analyzer = SectorAnalyzer()
        self.strategy_analyzer = StrategyAnalyzer()
        self.temporal_analyzer = TemporalAnalyzer()
        self.ensemble_weights = {}
        self.performance_history = defaultdict(list)
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def create_advanced_features(self, history):
        """Crea características avanzadas para el ML"""
        if len(history) < 10:
            return np.array([])
            
        features = []
        
        # Características básicas
        last_numbers = history[-10:]  # Últimos 10 números
        features.extend(last_numbers)
        
        # Características estadísticas
        features.append(np.mean(last_numbers))  # Media
        features.append(np.std(last_numbers))   # Desviación estándar
        features.append(len(set(last_numbers))) # Números únicos
        
        # Características de frecuencia
        counter = Counter(history[-20:])  # Últimos 20 números
        for i in range(37):
            features.append(counter.get(i, 0))
            
        # Características de patrones
        # Diferencias entre números consecutivos
        if len(history) >= 5:
            diffs = [abs(history[i] - history[i-1]) for i in range(1, min(6, len(history)))]
            features.extend(diffs + [0] * (5 - len(diffs)))
        else:
            features.extend([0] * 5)
            
        # Características de sectores
        sector_features = self.sector_analyzer.get_sector_features(history)
        features.extend(sector_features)
        
        # Características temporales
        temporal_features = self.temporal_analyzer.get_temporal_features()
        features.extend(temporal_features)
        
        # Características de estrategias
        strategy_features = self.strategy_analyzer.get_strategy_features(history)
        features.extend(strategy_features)
        
        return np.array(features)
    
    def prepare_training_data(self, history):
        """Prepara datos de entrenamiento con ventana deslizante"""
        if len(history) < 20:
            return None, None
            
        X, y = [], []
        window_size = 15
        
        for i in range(window_size, len(history)):
            # Usar los últimos window_size números para predecir el siguiente
            sequence = history[i-window_size:i]
            target = history[i]
            
            features = self.create_advanced_features(sequence)
            if len(features) > 0:
                X.append(features)
                y.append(target)
                
        return np.array(X), np.array(y)
    
    def train_models(self, history):
        """Entrena múltiples modelos de ML"""
        print("🧠 Entrenando modelos de ML avanzados...")
        
        X, y = self.prepare_training_data(history)
        if X is None or len(X) < 10:
            print("❌ Datos insuficientes para entrenamiento")
            return False
            
        # Normalizar características
        X_scaled = self.scaler.fit_transform(X)
        
        # Dividir datos para entrenamiento y validación
        split_idx = int(len(X_scaled) * 0.8)
        X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Definir modelos
        models_config = {
            'random_forest': RandomForestClassifier(
                n_estimators=100, 
                max_depth=10, 
                random_state=42,
                class_weight='balanced'
            ),
            'gradient_boost': GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'svm': SVC(
                kernel='rbf',
                probability=True,
                class_weight='balanced',
                random_state=42
            ),
            'neural_network': MLPClassifier(
                hidden_layer_sizes=(100, 50, 25),
                activation='relu',
                solver='adam',
                random_state=42,
                max_iter=500
            )
        }
        
        # Entrenar cada modelo
        trained_models = {}
        for name, model in models_config.items():
            try:
                print(f"📚 Entrenando {name}...")
                model.fit(X_train, y_train)
                
                # Validar modelo
                y_pred = model.predict(X_val)
                accuracy = accuracy_score(y_val, y_pred)
                
                trained_models[name] = model
                self.performance_history[name].append(accuracy)
                
                print(f"✅ {name}: Precisión = {accuracy:.3f}")
                
            except Exception as e:
                print(f"❌ Error entrenando {name}: {e}")
                continue
        
        # Crear ensemble con votación ponderada
        if len(trained_models) >= 2:
            try:
                # Calcular pesos basados en rendimiento histórico
                weights = []
                model_list = []
                
                for name, model in trained_models.items():
                    avg_performance = np.mean(self.performance_history[name][-5:])  # Últimas 5 evaluaciones
                    # Asegurar que el peso no sea cero (mínimo 0.01)
                    weight = max(avg_performance, 0.01)
                    weights.append(weight)
                    model_list.append((name, model))
                    self.ensemble_weights[name] = weight
                
                # Verificar que la suma de pesos no sea cero
                if sum(weights) > 0:
                    # Crear ensemble
                    ensemble = VotingClassifier(
                        estimators=model_list,
                        voting='soft',
                        weights=weights
                    )
                    ensemble.fit(X_train, y_train)
                    
                    # Validar ensemble
                    ensemble_pred = ensemble.predict(X_val)
                    ensemble_accuracy = accuracy_score(y_val, ensemble_pred)
                    
                    trained_models['ensemble'] = ensemble
                    self.performance_history['ensemble'].append(ensemble_accuracy)
                    
                    print(f"🎯 Ensemble: Precisión = {ensemble_accuracy:.3f}")
                else:
                    print("⚠️ Todos los pesos son cero, usando pesos uniformes...")
                    # Usar pesos uniformes como respaldo
                    uniform_weights = [1.0] * len(model_list)
                    ensemble = VotingClassifier(
                        estimators=model_list,
                        voting='soft',
                        weights=uniform_weights
                    )
                    ensemble.fit(X_train, y_train)
                    
                    ensemble_pred = ensemble.predict(X_val)
                    ensemble_accuracy = accuracy_score(y_val, ensemble_pred)
                    
                    trained_models['ensemble'] = ensemble
                    self.performance_history['ensemble'].append(ensemble_accuracy)
                    
                    print(f"🎯 Ensemble (pesos uniformes): Precisión = {ensemble_accuracy:.3f}")
                    
            except Exception as e:
                print(f"⚠️ Error creando ensemble: {e}")
                print("Continuando sin ensemble...")
        else:
            print("⚠️ Necesario al menos 2 modelos para crear ensemble")
        
        self.models = trained_models
        self.is_trained = True
        
        return True
    
    def predict_advanced(self, history):
        """Genera predicciones avanzadas usando todos los métodos"""
        if not self.is_trained or not self.models:
            print("❌ Modelos no entrenados")
            return self.fallback_prediction(history)
        
        # Crear características para predicción
        features = self.create_advanced_features(history)
        if len(features) == 0:
            return self.fallback_prediction(history)
            
        features_scaled = self.scaler.transform([features])
        
        predictions = {}
        probabilities = {}
        
        # Obtener predicciones de cada modelo
        for name, model in self.models.items():
            try:
                pred = model.predict(features_scaled)[0]
                
                # Obtener probabilidades si el modelo las soporta
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(features_scaled)[0]
                    # Encontrar los top 5 números más probables
                    top_indices = np.argsort(proba)[-5:][::-1]
                    probabilities[name] = {
                        'main': int(pred),
                        'top_5': [int(idx) for idx in top_indices],
                        'confidence': float(proba[pred])
                    }
                else:
                    probabilities[name] = {
                        'main': int(pred),
                        'top_5': [int(pred)],
                        'confidence': 0.5
                    }
                
                predictions[name] = int(pred)
                
            except Exception as e:
                print(f"❌ Error en predicción {name}: {e}")
                continue
        
        # Combinar con análisis de sectores
        sector_predictions = self.sector_analyzer.predict_sectors(history)
        
        # Combinar con análisis de estrategias
        strategy_predictions = self.strategy_analyzer.predict_strategies(history)
        
        # Combinar con análisis temporal
        temporal_predictions = self.temporal_analyzer.predict_temporal(history)
        
        # Generar predicción final híbrida
        final_prediction = self.create_hybrid_prediction(
            predictions, 
            sector_predictions, 
            strategy_predictions, 
            temporal_predictions,
            probabilities
        )
        
        return final_prediction
    
    def create_hybrid_prediction(self, ml_predictions, sector_pred, strategy_pred, temporal_pred, probabilities):
        """Crea predicción híbrida combinando todos los métodos"""
        
        # Recopilar todos los números candidatos con sus pesos
        candidates = defaultdict(float)
        
        # Añadir predicciones ML con pesos basados en rendimiento
        for name, pred in ml_predictions.items():
            weight = self.ensemble_weights.get(name, 0.5)
            candidates[pred] += weight * 0.4  # 40% peso para ML
            
            # Añadir top 5 con pesos menores
            if name in probabilities:
                for i, num in enumerate(probabilities[name]['top_5'][:3]):
                    candidates[num] += weight * 0.1 / (i + 1)
        
        # Añadir predicciones de sectores (30% peso)
        for sector_name, numbers in sector_pred.items():
            weight = 0.3 / len(numbers) if numbers else 0
            for num in numbers:
                candidates[num] += weight
        
        # Añadir predicciones de estrategias (20% peso)
        for strategy_name, numbers in strategy_pred.items():
            weight = 0.2 / len(numbers) if numbers else 0
            for num in numbers:
                candidates[num] += weight
        
        # Añadir predicciones temporales (10% peso)
        for num in temporal_pred.get('preferred_numbers', []):
            candidates[num] += 0.1 / len(temporal_pred.get('preferred_numbers', [1]))
        
        # Ordenar candidatos por peso
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        
        # Generar grupos de predicción
        grupo_individual = sorted_candidates[0][0] if sorted_candidates else 0
        grupo_5 = [num for num, _ in sorted_candidates[:5]]
        grupo_10 = [num for num, _ in sorted_candidates[:10]]
        grupo_15 = [num for num, _ in sorted_candidates[:15]]
        grupo_20 = [num for num, _ in sorted_candidates[:20]]
        
        # NUEVO: Agregar 0 como protección en todos los grupos (si no está ya incluido)
        if 0 not in grupo_5:
            grupo_5 = [0] + grupo_5[:4]  # Agregar 0 al inicio y mantener 5 números
        if 0 not in grupo_10:
            grupo_10 = [0] + grupo_10[:9]  # Agregar 0 al inicio y mantener 10 números
        if 0 not in grupo_15:
            grupo_15 = [0] + grupo_15[:14]  # Agregar 0 al inicio y mantener 15 números
        if 0 not in grupo_20:
            grupo_20 = [0] + grupo_20[:19]  # Agregar 0 al inicio y mantener 20 números
        
        # Completar grupos si no hay suficientes candidatos (excluyendo el 0 ya agregado)
        all_numbers = set(range(1, 37))  # Excluir 0 porque ya se agregó como protección
        used_numbers = set(grupo_20) - {0}  # Excluir 0 del conteo
        remaining = list(all_numbers - used_numbers)
        
        while len(grupo_5) < 5:
            grupo_5.append(remaining.pop(0) if remaining else 1)
        while len(grupo_10) < 10:
            grupo_10.append(remaining.pop(0) if remaining else 1)
        while len(grupo_15) < 15:
            grupo_15.append(remaining.pop(0) if remaining else 1)
        while len(grupo_20) < 20:
            grupo_20.append(remaining.pop(0) if remaining else 1)
        
        return {
            'individual': grupo_individual,
            'grupo_5': grupo_5,
            'grupo_10': grupo_10,
            'grupo_15': grupo_15,
            'grupo_20': grupo_20,
            'ml_predictions': ml_predictions,
            'sector_predictions': sector_pred,
            'strategy_predictions': strategy_pred,
            'temporal_predictions': temporal_pred,
            'confidence_scores': {name: prob['confidence'] for name, prob in probabilities.items()},
            'hybrid_weights': dict(sorted_candidates[:10])
        }
    
    def fallback_prediction(self, history):
        """Predicción de respaldo cuando ML no está disponible"""
        if not history:
            return {
                'individual': 0,
                'grupo_5': [0, 1, 2, 3, 4],
                'grupo_10': [0] + list(range(1, 10)),
                'grupo_15': [0] + list(range(1, 15)),
                'grupo_20': [0] + list(range(1, 20))
            }
        
        # Usar análisis de frecuencia simple
        counter = Counter(history[-50:])  # Últimos 50 números
        most_common = [num for num, _ in counter.most_common(20)]
        
        # Completar si no hay suficientes
        remaining = [i for i in range(37) if i not in most_common]
        most_common.extend(remaining[:20-len(most_common)])
        
        # Crear grupos base
        grupo_5 = most_common[:5]
        grupo_10 = most_common[:10]
        grupo_15 = most_common[:15]
        grupo_20 = most_common[:20]
        
        # NUEVO: Agregar 0 como protección en todos los grupos (si no está ya incluido)
        if 0 not in grupo_5:
            grupo_5 = [0] + grupo_5[:4]
        if 0 not in grupo_10:
            grupo_10 = [0] + grupo_10[:9]
        if 0 not in grupo_15:
            grupo_15 = [0] + grupo_15[:14]
        if 0 not in grupo_20:
            grupo_20 = [0] + grupo_20[:19]
        
        return {
            'individual': most_common[0] if most_common else 0,
            'grupo_5': grupo_5,
            'grupo_10': grupo_10,
            'grupo_15': grupo_15,
            'grupo_20': grupo_20
        }
    
    def get_model_performance_stats(self):
        """Obtiene estadísticas de rendimiento de los modelos"""
        if not self.is_trained:
            return {"error": "Modelos no entrenados"}
        
        stats = {
            "training_status": "trained",
            "models_trained": len(self.models),
            "model_list": list(self.models.keys()),
            "ensemble_weights": self.ensemble_weights.copy(),
            "performance_history": {}
        }
        
        # Agregar historiales de rendimiento
        for model_name, performance_list in self.performance_history.items():
            if performance_list:
                stats["performance_history"][model_name] = {
                    "latest_accuracy": performance_list[-1],
                    "average_accuracy": np.mean(performance_list),
                    "best_accuracy": max(performance_list),
                    "worst_accuracy": min(performance_list),
                    "evaluations_count": len(performance_list)
                }
        
        return stats
    
    def get_detailed_analysis(self, history):
        """Obtiene análisis detallado de cada componente del sistema"""
        if not history or len(history) < 10:
            return {"error": "Historial insuficiente para análisis detallado"}
        
        analysis = {
            "sector_analysis": self.sector_analyzer.analyze_sector_trends(history),
            "strategy_analysis": self.strategy_analyzer.analyze_strategy_effectiveness(history),
            "temporal_analysis": self.temporal_analyzer.analyze_temporal_patterns(history),
            "feature_importance": self.get_feature_importance() if self.is_trained else None
        }
        
        return analysis
    
    def get_feature_importance(self):
        """Obtiene la importancia de características de los modelos"""
        if not self.is_trained or 'random_forest' not in self.models:
            return None
        
        try:
            rf_model = self.models['random_forest']
            if hasattr(rf_model, 'feature_importances_'):
                # Mapear importancias a nombres de características
                feature_names = [
                    'num_-5', 'num_-4', 'num_-3', 'num_-2', 'num_-1',  # Últimos 5 números
                    'mean', 'std', 'unique_count',  # Estadísticas básicas
                ] + [f'freq_{i}' for i in range(37)]  # Frecuencias por número
                
                # Agregar características de sectores, temporales y estrategias
                feature_names.extend(['sector_' + str(i) for i in range(len(self.sector_analyzer.sector_definitions) * 3)])
                feature_names.extend(['temporal_' + str(i) for i in range(9)])  # 9 características temporales
                feature_names.extend(['strategy_' + str(i) for i in range(15)])  # 15 características de estrategias
                
                importances = rf_model.feature_importances_
                
                # Emparejar nombres con importancias (limitado al número disponible)
                paired = list(zip(feature_names[:len(importances)], importances))
                
                # Ordenar por importancia
                paired.sort(key=lambda x: x[1], reverse=True)
                
                return {
                    "top_10_features": paired[:10],
                    "all_features": paired
                }
        except Exception as e:
            print(f"Error al obtener importancia de características: {e}")
            return None


class SectorAnalyzer:
    def __init__(self):
        # Rueda europea para calcular vecinos correctamente
        self.rueda_europea = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
        
        # Primero calcular los sectores dinámicos usando el método auxiliar
        vecinos_calculados = self._calcular_sectores_vecinos()
        
        self.sector_definitions = {
            'vecinos_cero': [0, 32, 26, 3, 35, 12, 28, 7, 29, 18, 22, 9, 31, 14, 20, 1],
            'tercios': [33, 16, 24, 5, 10, 23, 8, 30, 11, 36, 13, 27],
            'orphelins': [17, 34, 6, 1, 20, 14, 31, 9],
            'calientes_izquierda': [4, 21, 2, 25, 17, 34, 6],
            'calientes_derecha': [19, 36, 13, 27, 15, 32, 26],
            
            # NUEVOS SECTORES SOLICITADOS
            'vecinos_5_del_7': vecinos_calculados['vecinos_5_del_7'],
            'vecinos_5_del_27': vecinos_calculados['vecinos_5_del_27'],
            'vecinos_5_del_31': vecinos_calculados['vecinos_5_del_31'],
            'vecinos_5_del_34': vecinos_calculados['vecinos_5_del_34'],
            'vecinos_9_del_0': vecinos_calculados['vecinos_9_del_0'],
            'vecinos_9_del_2': vecinos_calculados['vecinos_9_del_2']
        }
    
    def _calcular_sectores_vecinos(self):
        """Calcula todos los sectores de vecinos de una vez"""
        return {
            'vecinos_5_del_7': self._obtener_vecinos(7, 2),    # 5 vecinos del 7 (2 a cada lado + central)
            'vecinos_5_del_27': self._obtener_vecinos(27, 2),  # 5 vecinos del 27 (2 a cada lado + central)
            'vecinos_5_del_31': self._obtener_vecinos(31, 2),  # 5 vecinos del 31 (2 a cada lado + central)
            'vecinos_5_del_34': self._obtener_vecinos(34, 2),  # 5 vecinos del 34 (2 a cada lado + central)
            'vecinos_9_del_0': self._obtener_vecinos(0, 4),    # 9 vecinos del 0 (4 a cada lado + central)
            'vecinos_9_del_2': self._obtener_vecinos(2, 4)     # 9 vecinos del 2 (4 a cada lado + central)
        }
    
    def _obtener_vecinos(self, numero_central, cantidad_vecinos):
        """
        Obtiene vecinos de un número en la rueda europea.
        Args:
            numero_central: Número central
            cantidad_vecinos: Cantidad de vecinos a cada lado
        Returns:
            Lista de números vecinos (incluyendo el central)
        """
        try:
            idx_central = self.rueda_europea.index(numero_central)
        except ValueError:
            return [numero_central]  # Si no se encuentra, retornar solo el número central
        
        vecinos = []
        total_numeros = len(self.rueda_europea)
        
        # Obtener vecinos a ambos lados + el número central
        for i in range(-cantidad_vecinos, cantidad_vecinos + 1):
            idx_vecino = (idx_central + i) % total_numeros
            vecinos.append(self.rueda_europea[idx_vecino])
        
        return vecinos
        
    def get_sector_features(self, history):
        """Obtiene características de sectores para ML"""
        features = []
        
        recent_history = history[-20:] if len(history) >= 20 else history
        
        for sector_name, sector_numbers in self.sector_definitions.items():
            # Contar apariciones en el sector
            count = sum(1 for num in recent_history if num in sector_numbers)
            features.append(count)
            
            # Porcentaje del sector
            percentage = count / len(recent_history) if recent_history else 0
            features.append(percentage)
            
            # Último número del sector (posición)
            last_pos = -1
            for i, num in enumerate(reversed(recent_history)):
                if num in sector_numbers:
                    last_pos = i
                    break
            features.append(last_pos)
        
        return features
    
    def predict_sectors(self, history):
        """Predice números basado en análisis de sectores"""
        if len(history) < 10:
            return {}
        
        recent = history[-30:]
        predictions = {}
        
        for sector_name, sector_numbers in self.sector_definitions.items():
            # Contar frecuencia del sector
            sector_count = sum(1 for num in recent if num in sector_numbers)
            sector_ratio = sector_count / len(recent)
            
            # Si el sector está "frío", tiene mayor probabilidad
            expected_ratio = len(sector_numbers) / 37
            if sector_ratio < expected_ratio * 0.7:  # Sector frío
                predictions[f"{sector_name}_frio"] = sector_numbers[:5]
            elif sector_ratio > expected_ratio * 1.3:  # Sector caliente
                predictions[f"{sector_name}_caliente"] = sector_numbers[:3]
        
        return predictions
    
    def analyze_sector_trends(self, history):
        """Analiza tendencias detalladas de los sectores"""
        if len(history) < 10:
            return {"error": "Historial insuficiente"}
        
        recent = history[-30:] if len(history) >= 30 else history
        analysis = {}
        
        for sector_name, sector_numbers in self.sector_definitions.items():
            # Conteo total y reciente
            total_count = sum(1 for num in history if num in sector_numbers)
            recent_count = sum(1 for num in recent if num in sector_numbers)
            
            # Calcular tendencias
            expected_ratio = len(sector_numbers) / 37
            recent_ratio = recent_count / len(recent) if recent else 0
            historical_ratio = total_count / len(history) if history else 0
            
            # Determinar estado del sector
            if recent_ratio < expected_ratio * 0.6:
                estado = "muy_frio"
            elif recent_ratio < expected_ratio * 0.8:
                estado = "frio"
            elif recent_ratio > expected_ratio * 1.4:
                estado = "muy_caliente"
            elif recent_ratio > expected_ratio * 1.2:
                estado = "caliente"
            else:
                estado = "normal"
            
            # Últimas apariciones
            last_appearances = []
            for i, num in enumerate(reversed(recent)):
                if num in sector_numbers and len(last_appearances) < 3:
                    last_appearances.append({"numero": num, "posicion": i})
            
            analysis[sector_name] = {
                "total_apariciones": total_count,
                "apariciones_recientes": recent_count,
                "ratio_esperado": expected_ratio,
                "ratio_reciente": recent_ratio,
                "ratio_historico": historical_ratio,
                "estado": estado,
                "ultimas_apariciones": last_appearances,
                "numeros_sector": list(sector_numbers)
            }
        
        return analysis


class StrategyAnalyzer:
    def __init__(self):
        self.strategies = {
            'tia_lu': {
                'triggers': [33, 22, 11],
                'targets': [16, 33, 1, 9, 22, 18, 26, 0, 32, 30, 11, 36],
                'active_window': 5
            },
            'fibonacci': {
                'sequence': [1, 1, 2, 3, 5, 8, 13, 21, 34],
                'targets': [1, 2, 3, 5, 8, 13, 21, 34]
            },
            'vecinos_calientes': {
                'monitor_last': 10,
                'threshold': 2
            }
        }
        
    def get_strategy_features(self, history):
        """Obtiene características de estrategias para ML"""
        features = []
        
        if len(history) < 5:
            return [0] * 15  # Retornar características vacías
        
        recent = history[-10:]
        
        # Características de Tía Lu
        tia_lu_triggers = sum(1 for num in recent if num in self.strategies['tia_lu']['triggers'])
        features.append(tia_lu_triggers)
        
        # Última activación de Tía Lu
        last_trigger_pos = -1
        for i, num in enumerate(reversed(recent)):
            if num in self.strategies['tia_lu']['triggers']:
                last_trigger_pos = i
                break
        features.append(last_trigger_pos)
        
        # Características de Fibonacci
        fib_count = sum(1 for num in recent if num in self.strategies['fibonacci']['targets'])
        features.append(fib_count)
        
        # Patrones de repetición
        # Números que se repiten en los últimos 5
        last_5 = recent[-5:] if len(recent) >= 5 else recent
        unique_count = len(set(last_5))
        features.append(unique_count)
        
        # Tendencia par/impar - INCLUIR EL 0 EN ESTADÍSTICAS
        # El 0 se considera como par en algunas variantes de ruleta
        par_count = sum(1 for num in recent if num % 2 == 0)  # Incluir 0 como par
        features.append(par_count)
        
        # Tendencia rojo/negro (simplificado)
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        red_count = sum(1 for num in recent if num in red_numbers)
        features.append(red_count)
        
        # Análisis de docenas
        dozen1 = sum(1 for num in recent if 1 <= num <= 12)
        dozen2 = sum(1 for num in recent if 13 <= num <= 24)
        dozen3 = sum(1 for num in recent if 25 <= num <= 36)
        features.extend([dozen1, dozen2, dozen3])
        
        # Análisis de columnas - INCLUIR EL 0 CON LÓGICA ESPECIAL
        # El 0 no pertenece a ninguna columna tradicional, pero lo contamos separadamente
        col1 = sum(1 for num in recent if num != 0 and num % 3 == 1)
        col2 = sum(1 for num in recent if num != 0 and num % 3 == 2)
        col3 = sum(1 for num in recent if num != 0 and num % 3 == 0)
        col0 = sum(1 for num in recent if num == 0)  # Contar apariciones del 0
        features.extend([col1, col2, col3, col0])  # Agregamos col0 como nueva característica
        
        # Números altos vs bajos
        low_count = sum(1 for num in recent if 1 <= num <= 18)
        high_count = sum(1 for num in recent if 19 <= num <= 36)
        features.extend([low_count, high_count])
        
        return features
    
    def predict_strategies(self, history):
        """Predice números basado en estrategias"""
        if len(history) < 5:
            return {}
        
        predictions = {}
        recent = history[-10:]
        
        # Estrategia Tía Lu
        for i, num in enumerate(reversed(recent)):
            if num in self.strategies['tia_lu']['triggers'] and i < self.strategies['tia_lu']['active_window']:
                predictions['tia_lu_activa'] = self.strategies['tia_lu']['targets']
                break
        
        # Estrategia Fibonacci
        fib_recent = sum(1 for num in recent[-3:] if num in self.strategies['fibonacci']['targets'])
        if fib_recent >= 2:
            predictions['fibonacci_secuencia'] = self.strategies['fibonacci']['targets']
        
        # Estrategia de compensación (números fríos)
        all_numbers = set(range(37))
        recent_numbers = set(history[-20:])
        cold_numbers = list(all_numbers - recent_numbers)
        if cold_numbers:
            predictions['compensacion_frios'] = cold_numbers[:8]
        
        return predictions
    
    def analyze_strategy_effectiveness(self, history):
        """Analiza la efectividad de las estrategias"""
        if len(history) < 10:
            return {"error": "Historial insuficiente"}
        
        analysis = {}
        recent = history[-20:] if len(history) >= 20 else history
        
        # Análisis de Tía Lu
        tia_lu_triggers = [num for num in recent if num in self.strategies['tia_lu']['triggers']]
        tia_lu_targets_hit = [num for num in recent if num in self.strategies['tia_lu']['targets']]
        
        analysis['tia_lu'] = {
            "triggers_recientes": len(tia_lu_triggers),
            "targets_alcanzados": len(tia_lu_targets_hit),
            "ultima_activacion": None,
            "efectividad": 0
        }
        
        # Buscar última activación
        for i, num in enumerate(reversed(recent)):
            if num in self.strategies['tia_lu']['triggers']:
                analysis['tia_lu']['ultima_activacion'] = i
                break
        
        # Calcular efectividad simple
        if tia_lu_triggers:
            analysis['tia_lu']['efectividad'] = len(tia_lu_targets_hit) / len(tia_lu_triggers)
        
        # Análisis de Fibonacci
        fib_hits = [num for num in recent if num in self.strategies['fibonacci']['targets']]
        analysis['fibonacci'] = {
            "numeros_secuencia": len(fib_hits),
            "ratio_aparicion": len(fib_hits) / len(recent) if recent else 0,
            "numeros_encontrados": fib_hits
        }
        
        # Análisis de compensación
        all_numbers = set(range(37))
        recent_numbers = set(recent)
        cold_numbers = all_numbers - recent_numbers
        
        analysis['compensacion'] = {
            "numeros_frios": len(cold_numbers),
            "numeros_frios_lista": list(cold_numbers)[:10],  # Solo los primeros 10
            "ratio_cobertura": len(recent_numbers) / 37
        }
        
        return analysis


class TemporalAnalyzer:
    def __init__(self):
        self.time_patterns = {}
        
    def get_temporal_features(self):
        """Obtiene características temporales"""
        now = datetime.datetime.now()
        
        features = [
            now.hour / 24.0,          # Hora normalizada
            now.minute / 60.0,        # Minuto normalizado
            now.weekday() / 6.0,      # Día de la semana normalizado
            now.day / 31.0,           # Día del mes normalizado
            (now.month - 1) / 11.0,   # Mes normalizado
        ]
        
        # Características cíclicas (seno y coseno para periodicidad)
        features.extend([
            math.sin(2 * math.pi * now.hour / 24),
            math.cos(2 * math.pi * now.hour / 24),
            math.sin(2 * math.pi * now.weekday() / 7),
            math.cos(2 * math.pi * now.weekday() / 7)
        ])
        
        return features
    
    def predict_temporal(self, history):
        """Predice basado en patrones temporales"""
        now = datetime.datetime.now()
        
        # Predicciones simples basadas en hora
        if 9 <= now.hour <= 12:  # Mañana
            preferred = [7, 14, 21, 28, 35]
        elif 13 <= now.hour <= 17:  # Tarde
            preferred = [3, 9, 15, 21, 27, 33]
        elif 18 <= now.hour <= 22:  # Noche
            preferred = [1, 8, 15, 22, 29, 36]
        else:  # Madrugada
            preferred = [0, 6, 12, 18, 24, 30]
        
        return {
            'preferred_numbers': preferred,
            'time_factor': f"{now.hour}:{now.minute:02d}",
            'day_type': 'weekend' if now.weekday() >= 5 else 'weekday'
        } 
    
    def analyze_temporal_patterns(self, history):
        """Analiza patrones temporales en el historial"""
        now = datetime.datetime.now()
        
        analysis = {
            "hora_actual": now.hour,
            "minuto_actual": now.minute,
            "dia_semana": now.weekday(),
            "tipo_dia": 'fin_de_semana' if now.weekday() >= 5 else 'dia_laboral',
            "periodo_dia": self._get_period_of_day(now.hour),
            "patrones_horarios": self._analyze_hourly_patterns(now.hour),
            "numeros_preferidos_actuales": self.predict_temporal(history).get('preferred_numbers', [])
        }
        
        return analysis
    
    def _get_period_of_day(self, hour):
        """Determina el período del día"""
        if 6 <= hour < 12:
            return "mañana"
        elif 12 <= hour < 18:
            return "tarde"
        elif 18 <= hour < 24:
            return "noche"
        else:
            return "madrugada"
    
    def _analyze_hourly_patterns(self, current_hour):
        """Analiza patrones según la hora actual"""
        # Esto es una implementación simplificada
        # En una implementación real, se analizaría el historial con timestamps
        patterns = {
            "periodo_activo": self._get_period_of_day(current_hour),
            "actividad_esperada": "alta" if 9 <= current_hour <= 23 else "baja",
            "recomendacion": "periodo_favorable" if 9 <= current_hour <= 22 else "periodo_menos_favorable"
        }
        
        return patterns 