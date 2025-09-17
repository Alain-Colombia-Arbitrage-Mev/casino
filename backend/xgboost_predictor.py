#!/usr/bin/env python3
"""
XGBoost Predictor para Ruleta
Sistema avanzado de predicción usando XGBoost con features engineered
"""

import json
import redis
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass
import random
import pickle
import time

# Import del optimizador de estrategias
try:
    from ai_strategy_optimizer import create_strategy_optimizer
    STRATEGY_OPTIMIZER_AVAILABLE = True
except ImportError:
    STRATEGY_OPTIMIZER_AVAILABLE = False

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
    logger.info("XGBoost available for advanced predictions")
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available, falling back to statistical methods")

@dataclass
class XGBoostPredictionResult:
    """Resultado de predicción con XGBoost"""
    prediction_id: str
    timestamp: str
    last_number: int
    predicted_numbers: List[int]
    prediction_groups: Dict[str, List[int]]
    prediction_type: str
    confidence: float
    reasoning: str
    model_used: str  # 'xgboost' or 'statistical'
    feature_importance: Dict[str, float]
    probabilities: Dict[int, float]

class XGBoostRoulettePredictor:
    def __init__(self, redis_client):
        self.redis_client = redis_client

        # Sectores de la ruleta
        self.sectors = {
            'voisins_zero': [22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25],
            'tiers': [27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33],
            'orphelins': [17, 34, 6, 1, 20, 14, 31, 9]
        }

        # Números por color
        self.red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        self.black_numbers = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]

        # Modelo XGBoost
        self.xgb_model = None
        self.feature_columns = []
        self.is_model_trained = False
        self.number_to_label = {}
        self.label_to_number = {}

        # Cargar modelo si existe
        self._load_model()

        # Cache para optimización de velocidad
        self._feature_cache = {}
        self._prediction_cache = {}
        self._cache_timestamp = {}
        self._cache_ttl = 30  # 30 segundos TTL

        # Inicializar optimizador de estrategias
        self.strategy_optimizer = None
        if STRATEGY_OPTIMIZER_AVAILABLE:
            try:
                self.strategy_optimizer = create_strategy_optimizer(self.redis_client)
                logger.info("Strategy optimizer initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize strategy optimizer: {e}")

        # Contador para auto-entrenamiento
        self.predictions_since_retrain = 0
        self.auto_retrain_threshold = 15  # Re-entrenar cada 15 predicciones

        logger.info(f"XGBoost Predictor initialized (XGBoost: {'Available' if XGBOOST_AVAILABLE else 'Not Available'})")

    def get_color_for_number(self, number: int) -> str:
        """Obtener color para número"""
        if number == 0:
            return 'green'
        return 'red' if number in self.red_numbers else 'black'

    def _load_model(self):
        """Cargar modelo XGBoost desde Redis si existe"""
        try:
            if not XGBOOST_AVAILABLE:
                return

            model_data = self.redis_client.get('ml:models:xgboost:v1')
            if model_data:
                # Decodificar el modelo
                model_bytes = model_data.encode('latin1')  # Redis stores as string
                self.xgb_model = pickle.loads(model_bytes)

                # Cargar metadata
                metadata = self.redis_client.hgetall('ml:models:metadata')
                if metadata:
                    self.feature_columns = json.loads(metadata.get('feature_columns', '[]'))
                    self.is_model_trained = True
                    logger.info(f"XGBoost model loaded with {len(self.feature_columns)} features")

        except Exception as e:
            logger.error(f"Error loading XGBoost model: {e}")
            self.xgb_model = None
            self.is_model_trained = False

    def _save_model(self):
        """Guardar modelo XGBoost en Redis"""
        try:
            if not self.xgb_model or not XGBOOST_AVAILABLE:
                return

            # Serializar modelo
            model_bytes = pickle.dumps(self.xgb_model)
            model_str = model_bytes.decode('latin1')

            # Guardar en Redis
            self.redis_client.set('ml:models:xgboost:v1', model_str)

            # Guardar metadata
            metadata = {
                'model_type': 'xgboost',
                'feature_columns': json.dumps(self.feature_columns),
                'trained_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            self.redis_client.hset('ml:models:metadata', mapping=metadata)

            logger.info("XGBoost model saved to Redis")

        except Exception as e:
            logger.error(f"Error saving XGBoost model: {e}")

    def get_training_data(self, limit: int = 200) -> Tuple[pd.DataFrame, np.ndarray]:
        """Obtener datos de entrenamiento desde Redis"""
        try:
            # Obtener features históricas
            features_history = self.redis_client.lrange('ml:features:history', 0, limit - 1)

            if len(features_history) < 30:
                logger.warning(f"Insufficient training data: {len(features_history)} samples")
                return None, None

            # Procesar features
            features_data = []
            targets = []

            for feature_json in features_history:
                try:
                    feature_entry = json.loads(feature_json)
                    features = feature_entry.get('features', {})
                    target = feature_entry.get('target')

                    if features and target is not None:
                        features_data.append(features)
                        targets.append(target)

                except json.JSONDecodeError:
                    continue

            if len(features_data) < 30:
                logger.warning(f"Insufficient valid training data: {len(features_data)} samples")
                return None, None

            # Crear DataFrame
            df_features = pd.DataFrame(features_data)
            targets_array = np.array(targets)

            # Asegurar que todas las columnas sean numéricas
            for col in df_features.columns:
                df_features[col] = pd.to_numeric(df_features[col], errors='coerce')

            # Eliminar filas con NaN
            df_features = df_features.fillna(0)

            logger.info(f"Training data prepared: {len(df_features)} samples, {len(df_features.columns)} features")

            return df_features, targets_array

        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return None, None

    def train_xgboost_model(self, retrain: bool = False) -> bool:
        """Entrenar modelo XGBoost"""
        try:
            if not XGBOOST_AVAILABLE:
                logger.warning("XGBoost not available for training")
                return False

            if self.is_model_trained and not retrain:
                logger.info("Model already trained, use retrain=True to force retraining")
                return True

            # Obtener datos de entrenamiento
            X, y = self.get_training_data()

            if X is None or y is None:
                logger.error("Could not obtain training data")
                return False

            if len(X) < 30:
                logger.error(f"Insufficient training data: {len(X)} samples")
                return False

            # Obtener clases únicas y mapear a etiquetas secuenciales
            import numpy as np
            unique_numbers = sorted(np.unique(y))
            self.number_to_label = {num: i for i, num in enumerate(unique_numbers)}
            self.label_to_number = {i: num for i, num in enumerate(unique_numbers)}

            # Convertir números a etiquetas secuenciales
            if hasattr(y, 'map'):
                y_labels = y.map(self.number_to_label)
            else:
                # Si y es numpy array
                y_labels = np.array([self.number_to_label[num] for num in y])

            # Configurar modelo XGBoost para clasificación multi-clase
            self.xgb_model = xgb.XGBClassifier(
                objective='multi:softprob',  # Probabilidades para cada clase
                # num_class is automatically inferred by XGBClassifier
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )

            # Entrenar modelo con etiquetas secuenciales
            self.xgb_model.fit(X, y_labels)

            # Guardar nombres de features
            self.feature_columns = list(X.columns)
            self.is_model_trained = True

            # Guardar modelo
            self._save_model()

            # Evaluar modelo
            train_score = self.xgb_model.score(X, y)
            logger.info(f"XGBoost model trained successfully (Train accuracy: {train_score:.3f})")

            # Guardar métricas
            self.redis_client.hset('ml:models:metadata', mapping={
                'train_accuracy': str(train_score),
                'samples_used': str(len(X)),
                'features_count': str(len(self.feature_columns))
            })

            return True

        except Exception as e:
            logger.error(f"Error training XGBoost model: {e}")
            return False

    def predict_with_xgboost(self, features: Dict) -> Tuple[Dict[int, float], Dict[str, float]]:
        """Hacer predicción usando XGBoost"""
        try:
            if not self.is_model_trained or not XGBOOST_AVAILABLE:
                return {}, {}

            # Preparar features para predicción
            feature_df = pd.DataFrame([features])

            # Asegurar que tenemos todas las columnas necesarias
            for col in self.feature_columns:
                if col not in feature_df.columns:
                    feature_df[col] = 0

            # Reordenar columnas
            feature_df = feature_df[self.feature_columns]

            # Hacer predicción
            probabilities = self.xgb_model.predict_proba(feature_df)[0]

            # Convertir a diccionario {número: probabilidad} usando mapeo de etiquetas
            number_probs = {}
            for label, prob in enumerate(probabilities):
                if label in self.label_to_number:
                    number = self.label_to_number[label]
                    number_probs[number] = float(prob)

            # Llenar probabilidades faltantes con valor muy bajo para números no presentes
            for i in range(37):  # 0-36
                if i not in number_probs:
                    number_probs[i] = 0.001  # Probabilidad muy baja

            # Obtener importancia de features
            feature_importance = {}
            if hasattr(self.xgb_model, 'feature_importances_'):
                for i, importance in enumerate(self.xgb_model.feature_importances_):
                    if i < len(self.feature_columns):
                        feature_importance[self.feature_columns[i]] = float(importance)

            return number_probs, feature_importance

        except Exception as e:
            logger.error(f"Error in XGBoost prediction: {e}")
            return {}, {}

    def make_advanced_prediction(self, prediction_type: str = 'xgboost') -> Optional[XGBoostPredictionResult]:
        """Hacer predicción avanzada usando XGBoost o métodos estadísticos"""
        try:
            # Obtener último número y historial
            last_number = self._get_latest_number()
            if last_number is None:
                logger.warning("No latest number available")
                return None

            history = self._get_history(50)
            if not history:
                logger.warning("No history available")
                return None

            # Generar ID único
            prediction_id = f"xgb_pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
            timestamp = datetime.now().isoformat()

            # Extraer features actuales
            features = self._extract_advanced_features(history)

            # Intentar predicción con XGBoost
            number_probs = {}
            feature_importance = {}
            model_used = 'statistical'

            if self.is_model_trained and XGBOOST_AVAILABLE and prediction_type == 'xgboost':
                number_probs, feature_importance = self.predict_with_xgboost(features)
                if number_probs:
                    model_used = 'xgboost'

            # Si XGBoost no está disponible, usar métodos estadísticos
            if not number_probs:
                number_probs = self._statistical_prediction(history)
                model_used = 'statistical'

            # Generar grupos basados en probabilidades
            prediction_groups = self._generate_probability_based_groups(number_probs)

            # Números principales (top 6 por probabilidad)
            top_numbers = sorted(number_probs.items(), key=lambda x: x[1], reverse=True)[:6]
            predicted_numbers = [int(num) for num, prob in top_numbers]  # Convert to Python int

            # Calcular confianza
            confidence = self._calculate_confidence(number_probs, model_used)

            # Generar reasoning
            reasoning = self._generate_reasoning(model_used, feature_importance, top_numbers)

            # Crear resultado
            result = XGBoostPredictionResult(
                prediction_id=prediction_id,
                timestamp=timestamp,
                last_number=last_number,
                predicted_numbers=predicted_numbers,
                prediction_groups=prediction_groups,
                prediction_type=prediction_type,
                confidence=confidence,
                reasoning=reasoning,
                model_used=model_used,
                feature_importance=feature_importance,
                probabilities={int(k): float(v) for k, v in number_probs.items()}  # Convert to Python types
            )

            # Guardar predicción
            self._save_prediction(result)

            logger.info(f"Advanced prediction created: {prediction_id} (model: {model_used}, confidence: {confidence:.3f})")
            return result

        except Exception as e:
            logger.error(f"Error making advanced prediction: {e}")
            return None

    def _get_latest_number(self) -> Optional[int]:
        """Obtener último número"""
        try:
            latest = self.redis_client.get('roulette:latest')
            return int(latest) if latest else None
        except:
            return None

    def _get_history(self, limit: int = 50) -> List[int]:
        """Obtener historial"""
        try:
            history = self.redis_client.lrange('roulette:history', 0, limit - 1)
            return [int(num) for num in history if num.isdigit()]
        except:
            return []

    def _get_number_history(self, limit: int = 50) -> List[int]:
        """Alias para _get_history - obtener historial de números"""
        return self._get_history(limit)

    def _extract_features(self, last_number: int, history: List[int]) -> Dict:
        """Extraer features para ensemble - alias para _extract_advanced_features"""
        return self._extract_advanced_features(history)

    def _get_cache_key(self, data_type: str, params: tuple) -> str:
        """Generar clave de cache"""
        return f"{data_type}:{hash(params)}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verificar si el cache es válido"""
        if cache_key not in self._cache_timestamp:
            return False
        age = time.time() - self._cache_timestamp[cache_key]
        return age < self._cache_ttl

    def _get_cached_features(self, history_hash: str) -> Optional[Dict]:
        """Obtener features del cache si están disponibles"""
        cache_key = f"features:{history_hash}"
        if cache_key in self._feature_cache and self._is_cache_valid(cache_key):
            return self._feature_cache[cache_key]
        return None

    def _cache_features(self, history_hash: str, features: Dict):
        """Guardar features en cache"""
        cache_key = f"features:{history_hash}"
        self._feature_cache[cache_key] = features
        self._cache_timestamp[cache_key] = time.time()

    def _get_cached_prediction(self, prediction_key: str) -> Optional[Dict]:
        """Obtener predicción del cache"""
        if prediction_key in self._prediction_cache and self._is_cache_valid(prediction_key):
            return self._prediction_cache[prediction_key]
        return None

    def _cache_prediction(self, prediction_key: str, prediction: Dict):
        """Guardar predicción en cache"""
        self._prediction_cache[prediction_key] = prediction
        self._cache_timestamp[prediction_key] = time.time()

    def _extract_advanced_features(self, history: List[int]) -> Dict:
        """Extraer features avanzadas para predicción - OPTIMIZADO"""
        if len(history) < 5:
            return {}

        # Cache: verificar si ya calculamos las features para este historial
        history_hash = str(hash(tuple(history[:20])))  # Solo usar últimos 20 números para el hash
        cached_features = self._get_cached_features(history_hash)
        if cached_features:
            return cached_features

        features = {}

        # Features básicas
        features['last_1'] = history[0] if len(history) > 0 else 0
        features['last_2'] = history[1] if len(history) > 1 else 0
        features['last_3'] = history[2] if len(history) > 2 else 0

        # Features de color
        colors = [self.get_color_for_number(n) for n in history[:10]]
        features['red_count_10'] = colors.count('red')
        features['black_count_10'] = colors.count('black')
        features['green_count_10'] = colors.count('green')

        # Features de sectores
        for sector_name, sector_nums in self.sectors.items():
            count = sum(1 for n in history[:10] if n in sector_nums)
            features[f'sector_{sector_name}_count_10'] = count

        # Features estadísticas
        recent = history[:10]
        features['mean_last_10'] = float(np.mean(recent))
        features['std_last_10'] = float(np.std(recent))

        # Features de gaps
        for num in range(37):
            if num in history:
                features[f'gap_since_last_{num}'] = history.index(num)
            else:
                features[f'gap_since_last_{num}'] = 50  # Máximo

        # Features temporales (optimizado)
        now = datetime.now()
        features['hour'] = now.hour
        features['minute'] = now.minute

        # Guardar en cache para acelerar próximas llamadas
        self._cache_features(history_hash, features)

        return features

    def _statistical_prediction(self, history: List[int]) -> Dict[int, float]:
        """Predicción estadística cuando XGBoost no está disponible"""
        # Análisis de frecuencias
        freq_count = {}
        for num in history:
            freq_count[num] = freq_count.get(num, 0) + 1

        # Calcular probabilidades inversas (números menos frecuentes tienen mayor probabilidad)
        total_numbers = len(history)
        probs = {}

        for num in range(37):
            frequency = freq_count.get(num, 0)
            # Probabilidad inversa normalizada
            inverse_prob = (total_numbers - frequency) / total_numbers if total_numbers > 0 else 1/37
            probs[num] = max(inverse_prob, 0.01)  # Mínimo 1%

        # Normalizar probabilidades
        total_prob = sum(probs.values())
        for num in probs:
            probs[num] = probs[num] / total_prob

        return probs

    def _generate_probability_based_groups(self, number_probs: Dict[int, float]) -> Dict[str, List[int]]:
        """Generar grupos basados en probabilidades"""
        # Ordenar números por probabilidad
        sorted_numbers = sorted(number_probs.items(), key=lambda x: x[1], reverse=True)

        # Grupos de números principales (convert to Python int)
        groups = {
            'group_4': [int(num) for num, prob in sorted_numbers[:4]],
            'group_8': [int(num) for num, prob in sorted_numbers[:8]],
            'group_14': [int(num) for num, prob in sorted_numbers[:14]],
            'group_15': [int(num) for num, prob in sorted_numbers[:15]],
            'group_20': [int(num) for num, prob in sorted_numbers[:20]]
        }

        # Agregar grupos de estadísticas estándar
        # Columnas (1-34, 2-35, 3-36)
        column1 = [i for i in range(1, 37) if i % 3 == 1]  # 1,4,7,10,13,16,19,22,25,28,31,34
        column2 = [i for i in range(1, 37) if i % 3 == 2]  # 2,5,8,11,14,17,20,23,26,29,32,35
        column3 = [i for i in range(1, 37) if i % 3 == 0]  # 3,6,9,12,15,18,21,24,27,30,33,36

        # Docenas
        dozen1 = list(range(1, 13))    # 1-12
        dozen2 = list(range(13, 25))   # 13-24
        dozen3 = list(range(25, 37))   # 25-36

        # Pares/Impares (sin incluir el 0)
        even_numbers = [i for i in range(1, 37) if i % 2 == 0]
        odd_numbers = [i for i in range(1, 37) if i % 2 == 1]

        # Colores
        red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        black_numbers = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]

        # Agregar grupos estadísticos
        groups.update({
            'column_1': column1,
            'column_2': column2,
            'column_3': column3,
            'dozen_1': dozen1,
            'dozen_2': dozen2,
            'dozen_3': dozen3,
            'even': even_numbers,
            'odd': odd_numbers,
            'red': red_numbers,
            'black': black_numbers
        })

        return groups

    def _calculate_confidence(self, number_probs: Dict[int, float], model_used: str) -> float:
        """Calcular confianza de la predicción"""
        if not number_probs:
            return 0.3

        # Tomar probabilidades de los top 6 números
        top_probs = sorted(number_probs.values(), reverse=True)[:6]

        # Confianza basada en la concentración de probabilidad
        top_6_prob_sum = sum(top_probs)

        # Ajustar según el modelo usado
        base_confidence = top_6_prob_sum
        if model_used == 'xgboost':
            base_confidence *= 1.2  # XGBoost es más confiable
        else:
            base_confidence *= 0.8  # Métodos estadísticos son menos precisos

        return min(0.9, max(0.3, base_confidence))

    def _generate_reasoning(self, model_used: str, feature_importance: Dict, top_numbers: List) -> str:
        """Generar explicación de la predicción"""
        reasoning_parts = []

        # Información del modelo
        if model_used == 'xgboost':
            reasoning_parts.append("Predicción XGBoost")

            # Features más importantes
            if feature_importance:
                top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
                feature_names = [f"{name}({importance:.3f})" for name, importance in top_features]
                reasoning_parts.append(f"Features clave: {', '.join(feature_names)}")
        else:
            reasoning_parts.append("Predicción estadística")

        # Top números
        if top_numbers:
            top_3 = top_numbers[:3]
            number_info = [f"{num}({prob:.2%})" for num, prob in top_3]
            reasoning_parts.append(f"Top 3: {', '.join(number_info)}")

        return " | ".join(reasoning_parts)

    def _save_prediction(self, result: XGBoostPredictionResult):
        """Guardar predicción en Redis"""
        try:
            prediction_data = {
                'prediction_id': result.prediction_id,
                'timestamp': result.timestamp,
                'last_number': str(result.last_number),
                'predicted_numbers': json.dumps(result.predicted_numbers),
                'prediction_groups': json.dumps(result.prediction_groups),
                'prediction_type': result.prediction_type,
                'confidence': str(result.confidence),
                'reasoning': result.reasoning,
                'model_used': result.model_used,
                'status': 'pending'
            }

            # Guardar en hash
            self.redis_client.hset(f'prediction:{result.prediction_id}', mapping=prediction_data)

            # Agregar a lista de pendientes
            self.redis_client.lpush('ai:pending_predictions', result.prediction_id)
            self.redis_client.ltrim('ai:pending_predictions', 0, 49)  # Últimas 50

            logger.info(f"XGBoost prediction saved: {result.prediction_id}")

        except Exception as e:
            logger.error(f"Error saving prediction: {e}")

    def auto_train_with_strategies(self, force_retrain=False):
        """Auto-entrenamiento con optimización de estrategias"""
        try:
            if not self.strategy_optimizer:
                # Fallback al método original
                return self.auto_train_if_needed()

            # Incrementar contador
            self.predictions_since_retrain += 1

            # Verificar si necesitamos re-entrenar
            should_retrain = (
                force_retrain or
                self.predictions_since_retrain >= self.auto_retrain_threshold or
                not self.is_model_trained
            )

            if not should_retrain:
                return False

            logger.info(f"Iniciando auto-entrenamiento con optimización de estrategias")

            # Ejecutar auto-entrenamiento con optimización
            success = self.strategy_optimizer.auto_retrain_models(force_retrain=True)

            if success:
                # Actualizar también el modelo XGBoost local
                self.train_xgboost_model(retrain=True)

                # Resetear contador
                self.predictions_since_retrain = 0

                # Guardar timestamp de último entrenamiento
                self.redis_client.set('ai:last_auto_retrain', datetime.now().isoformat())

                logger.info("Auto-entrenamiento con estrategias completado exitosamente")

            return success

        except Exception as e:
            logger.error(f"Error en auto-entrenamiento con estrategias: {e}")
            return False

    def auto_train_if_needed(self):
        """Entrenar automáticamente si hay suficientes datos"""
        try:
            if self.is_model_trained:
                return

            # Verificar si hay suficientes datos
            features_count = self.redis_client.llen('ml:features:history')

            if features_count >= 50:  # Mínimo para entrenamiento
                logger.info(f"Auto-training XGBoost with {features_count} samples")
                success = self.train_xgboost_model()

                if success:
                    logger.info("Auto-training completed successfully")
                else:
                    logger.warning("Auto-training failed")

        except Exception as e:
            logger.error(f"Error in auto-training: {e}")

    def make_ensemble_prediction(self, prediction_type: str = 'ensemble') -> Optional[XGBoostPredictionResult]:
        """Hacer predicción usando ensemble de estrategias optimizadas"""
        try:
            if not self.strategy_optimizer:
                # Fallback a predicción normal
                return self.make_advanced_prediction(prediction_type)

            # Cache de predicción completa
            last_number = self._get_latest_number()
            if last_number is None:
                return None

            history = self._get_number_history(50)
            if len(history) < 10:
                return None

            # Verificar cache de predicción completa
            prediction_key = f"ensemble:{prediction_type}:{hash(tuple(history[:10]))}"
            cached_result = self._get_cached_prediction(prediction_key)
            if cached_result:
                # Retornar desde cache (súper rápido - <10ms)
                return cached_result

            # Extraer features para ensemble (con cache interno)
            features = self._extract_features(last_number, history)

            # Hacer predicción ensemble
            ensemble_result = self.strategy_optimizer.make_ensemble_prediction(features)

            if not ensemble_result:
                # Fallback a predicción normal si ensemble falla
                return self.make_advanced_prediction(prediction_type)

            # Convertir resultado ensemble a formato XGBoostPredictionResult
            number_probs = {}
            for i in range(37):
                number_probs[i] = ensemble_result.get('confidence', 0.3) / 37

            # Ajustar probabilidades basándose en la predicción ensemble
            predicted_number = ensemble_result.get('prediction', 0)
            if predicted_number in number_probs:
                number_probs[predicted_number] *= 5  # Aumentar probabilidad del número predicho

            # Generar grupos basados en las probabilidades ensemble
            groups = self._generate_probability_based_groups(number_probs)

            # Crear resultado
            result = XGBoostPredictionResult(
                prediction_id=f"ensemble_pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
                timestamp=datetime.now().isoformat(),
                last_number=last_number,
                predicted_numbers=list(range(37)),
                prediction_groups=groups,
                prediction_type='ensemble',
                confidence=ensemble_result.get('confidence', 0.3),
                reasoning=f"Ensemble prediction using {ensemble_result.get('model_count', 1)} models",
                model_used='ensemble',
                feature_importance={},
                probabilities={int(k): float(v) for k, v in number_probs.items()}  # Convert to Python types
            )

            # Guardar predicción
            self._save_prediction(result)

            # Guardar en cache para próximas predicciones rápidas
            self._cache_prediction(prediction_key, result)

            logger.info(f"Ensemble prediction created: {result.prediction_id}")
            return result

        except Exception as e:
            logger.error(f"Error en predicción ensemble: {e}")
            # Robustez: múltiples fallbacks para garantizar respuesta
            try:
                # Fallback 1: predicción avanzada
                return self.make_advanced_prediction(prediction_type)
            except Exception as e2:
                logger.error(f"Error en fallback avanzado: {e2}")
                try:
                    # Fallback 2: predicción estadística simple
                    return self._create_statistical_fallback(prediction_type)
                except Exception as e3:
                    logger.error(f"Error en fallback estadístico: {e3}")
                    # Fallback 3: predicción básica garantizada
                    return self._create_basic_fallback(prediction_type)

    def _create_statistical_fallback(self, prediction_type: str) -> XGBoostPredictionResult:
        """Fallback estadístico rápido y robusto"""
        try:
            history = self._get_history(20)  # Solo 20 números para rapidez
            if not history:
                return self._create_basic_fallback(prediction_type)

            # Análisis rápido de frecuencias
            from collections import Counter
            freq = Counter(history)

            # Top 6 números más frecuentes
            most_common = freq.most_common(6)
            predicted_numbers = [num for num, _ in most_common] if most_common else [7, 14, 21, 28, 35, 0]

            prediction_id = f"stat_pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

            return XGBoostPredictionResult(
                prediction_id=prediction_id,
                timestamp=datetime.now().isoformat(),
                last_number=history[0] if history else 0,
                predicted_numbers=predicted_numbers,
                prediction_groups={'quick_group': predicted_numbers},
                prediction_type='statistical_fallback',
                confidence=0.25,
                reasoning="Fallback estadístico basado en frecuencias recientes",
                model_used='statistical_fallback',
                feature_importance={},
                probabilities={num: 0.25/37 for num in range(37)}
            )
        except:
            return self._create_basic_fallback(prediction_type)

    def _create_basic_fallback(self, prediction_type: str) -> XGBoostPredictionResult:
        """Fallback básico garantizado - NUNCA falla"""
        prediction_id = f"basic_pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

        # Predicción básica con distribución uniforme
        predicted_numbers = [7, 14, 21, 0, 35, 28]  # Números distribuidos

        return XGBoostPredictionResult(
            prediction_id=prediction_id,
            timestamp=datetime.now().isoformat(),
            last_number=0,
            predicted_numbers=predicted_numbers,
            prediction_groups={'basic_group': predicted_numbers},
            prediction_type='basic_fallback',
            confidence=0.1,
            reasoning="Predicción básica de emergencia",
            model_used='basic_fallback',
            feature_importance={},
            probabilities={num: 1.0/37 for num in range(37)}
        )

    def get_strategy_performance_summary(self) -> Dict:
        """Obtener resumen del rendimiento de estrategias"""
        try:
            if not self.strategy_optimizer:
                return {'error': 'Strategy optimizer not available'}

            return self.strategy_optimizer.get_strategy_summary()

        except Exception as e:
            logger.error(f"Error getting strategy summary: {e}")
            return {'error': str(e)}

    def trigger_strategy_optimization(self, force=False) -> bool:
        """Trigger manual de optimización de estrategias"""
        try:
            if not self.strategy_optimizer:
                logger.warning("Strategy optimizer not available")
                return False

            return self.strategy_optimizer.auto_retrain_models(force_retrain=force)

        except Exception as e:
            logger.error(f"Error triggering strategy optimization: {e}")
            return False

# Función para verificar estado del modelo
def get_xgboost_status(redis_client):
    """Obtener estado del sistema XGBoost"""
    try:
        predictor = XGBoostRoulettePredictor(redis_client)

        status = {
            'xgboost_available': XGBOOST_AVAILABLE,
            'model_trained': predictor.is_model_trained,
            'feature_count': len(predictor.feature_columns),
            'training_data_available': redis_client.llen('ml:features:history'),
            'ready_for_prediction': predictor.is_model_trained and XGBOOST_AVAILABLE
        }

        if predictor.is_model_trained:
            metadata = redis_client.hgetall('ml:models:metadata')
            status['model_metadata'] = metadata

        return status

    except Exception as e:
        return {'error': str(e)}