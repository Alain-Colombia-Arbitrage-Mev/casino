#!/usr/bin/env python3
"""
AI Strategy Optimizer - Auto-entrenamiento continuo y generación de estrategias dinámicas
Optimiza automáticamente las estrategias de predicción basándose en el rendimiento en tiempo real
"""

import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import redis
from dataclasses import dataclass
from collections import defaultdict
import time

# ML imports
try:
    import xgboost as xgb
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.model_selection import GridSearchCV, cross_val_score
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class StrategyPerformance:
    """Clase para trackear el rendimiento de una estrategia"""
    strategy_id: str
    success_rate: float
    total_predictions: int
    correct_predictions: int
    avg_confidence: float
    last_updated: str
    model_type: str
    hyperparameters: Dict[str, Any]
    feature_importance: Dict[str, float]

@dataclass
class AdaptiveStrategy:
    """Estrategia adaptativa generada dinámicamente"""
    strategy_id: str
    name: str
    description: str
    model_config: Dict[str, Any]
    target_groups: List[str]
    performance_threshold: float
    created_at: str
    is_active: bool

class AIStrategyOptimizer:
    """Sistema de optimización automática de estrategias de IA"""

    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.strategies = {}
        self.models = {}
        self.performance_history = defaultdict(list)

        # Configuración de auto-entrenamiento
        self.auto_retrain_threshold = 10  # Re-entrenar cada 10 nuevos números
        self.min_samples_for_training = 30
        self.performance_window = 50  # Ventana para evaluar rendimiento

        # Configuración de ensemble
        self.ensemble_models = {
            'xgboost': self._create_xgboost_config,
            'random_forest': self._create_rf_config,
            'gradient_boost': self._create_gb_config,
            'logistic': self._create_logistic_config
        }

        # Métricas de evaluación
        self.strategy_metrics = {}

        logger.info("AI Strategy Optimizer initialized")

    def _create_xgboost_config(self, hyperparams=None):
        """Crear configuración XGBoost optimizada"""
        default_params = {
            'objective': 'multi:softprob',
            'n_estimators': 150,
            'max_depth': 8,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }
        if hyperparams:
            default_params.update(hyperparams)
        return xgb.XGBClassifier(**default_params)

    def _create_rf_config(self, hyperparams=None):
        """Crear configuración Random Forest"""
        default_params = {
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'random_state': 42
        }
        if hyperparams:
            default_params.update(hyperparams)
        return RandomForestClassifier(**default_params)

    def _create_gb_config(self, hyperparams=None):
        """Crear configuración Gradient Boosting"""
        default_params = {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 6,
            'random_state': 42
        }
        if hyperparams:
            default_params.update(hyperparams)
        return GradientBoostingClassifier(**default_params)

    def _create_logistic_config(self, hyperparams=None):
        """Crear configuración Logistic Regression"""
        default_params = {
            'random_state': 42,
            'max_iter': 1000,
            'multi_class': 'ovr'
        }
        if hyperparams:
            default_params.update(hyperparams)
        return LogisticRegression(**default_params)

    def auto_retrain_models(self, force_retrain=False):
        """Auto-entrenamiento basado en nuevos datos"""
        try:
            # Obtener datos de entrenamiento actualizados
            training_data = self._get_training_data()

            if training_data is None or len(training_data) < self.min_samples_for_training:
                logger.warning(f"Insufficient data for auto-retraining: {len(training_data) if training_data is not None else 0}")
                return False

            # Verificar si necesitamos re-entrenar
            last_retrain = self.redis_client.get('ai:last_retrain_timestamp')
            new_samples_count = self.redis_client.get('ai:new_samples_since_retrain') or 0
            new_samples_count = int(new_samples_count)

            should_retrain = (
                force_retrain or
                last_retrain is None or
                new_samples_count >= self.auto_retrain_threshold
            )

            if not should_retrain:
                logger.info(f"Auto-retrain not needed. New samples: {new_samples_count}/{self.auto_retrain_threshold}")
                return False

            logger.info(f"Starting auto-retrain with {len(training_data)} samples")

            # Preparar datos
            X, y = self._prepare_training_data(training_data)

            # Re-entrenar todos los modelos del ensemble
            results = {}
            for model_name, model_creator in self.ensemble_models.items():
                try:
                    logger.info(f"Auto-retraining {model_name}")

                    # Optimizar hiperparámetros si es necesario
                    best_params = self._optimize_hyperparameters(model_name, X, y)

                    # Crear y entrenar modelo
                    model = model_creator(best_params)
                    model.fit(X, y)

                    # Evaluar rendimiento
                    train_score = model.score(X, y)
                    cv_scores = cross_val_score(model, X, y, cv=5)

                    # Guardar modelo y métricas
                    self.models[model_name] = model
                    results[model_name] = {
                        'train_accuracy': train_score,
                        'cv_mean': cv_scores.mean(),
                        'cv_std': cv_scores.std(),
                        'hyperparameters': best_params
                    }

                    logger.info(f"{model_name} retrained - Accuracy: {train_score:.3f}, CV: {cv_scores.mean():.3f}±{cv_scores.std():.3f}")

                except Exception as e:
                    logger.error(f"Error retraining {model_name}: {e}")
                    results[model_name] = {'error': str(e)}

            # Actualizar timestamps y contadores
            self.redis_client.set('ai:last_retrain_timestamp', datetime.now().isoformat())
            self.redis_client.set('ai:new_samples_since_retrain', 0)

            # Guardar resultados de re-entrenamiento
            self.redis_client.hset('ai:retrain_results', mapping={
                'timestamp': datetime.now().isoformat(),
                'results': json.dumps(results),
                'samples_used': len(training_data)
            })

            # Generar nuevas estrategias basadas en el rendimiento
            self._generate_adaptive_strategies(results)

            logger.info(f"Auto-retrain completed successfully with {len(results)} models")
            return True

        except Exception as e:
            logger.error(f"Error in auto-retrain: {e}")
            return False

    def _optimize_hyperparameters(self, model_name: str, X, y):
        """Optimización automática de hiperparámetros"""
        try:
            param_grids = {
                'xgboost': {
                    'n_estimators': [100, 150, 200],
                    'max_depth': [6, 8, 10],
                    'learning_rate': [0.05, 0.1, 0.15]
                },
                'random_forest': {
                    'n_estimators': [50, 100, 150],
                    'max_depth': [8, 10, 12],
                    'min_samples_split': [2, 5, 10]
                },
                'gradient_boost': {
                    'n_estimators': [50, 100, 150],
                    'learning_rate': [0.05, 0.1, 0.15],
                    'max_depth': [4, 6, 8]
                },
                'logistic': {
                    'C': [0.1, 1.0, 10.0],
                    'solver': ['liblinear', 'lbfgs']
                }
            }

            if model_name not in param_grids:
                return {}

            # Crear modelo base
            base_model = self.ensemble_models[model_name]()

            # Grid search con validación cruzada
            grid_search = GridSearchCV(
                base_model,
                param_grids[model_name],
                cv=3,
                scoring='accuracy',
                n_jobs=-1
            )

            grid_search.fit(X, y)

            logger.info(f"Best params for {model_name}: {grid_search.best_params_}")
            return grid_search.best_params_

        except Exception as e:
            logger.error(f"Error optimizing hyperparameters for {model_name}: {e}")
            return {}

    def _generate_adaptive_strategies(self, retrain_results):
        """Generar nuevas estrategias adaptativas basadas en el rendimiento"""
        try:
            # Analizar qué modelos están rindiendo mejor
            best_models = sorted(
                [(name, results.get('cv_mean', 0)) for name, results in retrain_results.items()
                 if 'error' not in results],
                key=lambda x: x[1],
                reverse=True
            )

            if not best_models:
                logger.warning("No valid models for strategy generation")
                return

            # Crear estrategias dinámicas
            strategies = []

            # Estrategia 1: Ensemble de los mejores modelos
            top_models = [model[0] for model in best_models[:3]]
            ensemble_strategy = AdaptiveStrategy(
                strategy_id=f"ensemble_{int(time.time())}",
                name="Dynamic Ensemble Strategy",
                description=f"Ensemble de los mejores modelos: {', '.join(top_models)}",
                model_config={
                    'type': 'ensemble',
                    'models': top_models,
                    'weights': [model[1] for model in best_models[:3]]
                },
                target_groups=['group_4', 'group_8', 'group_14', 'group_15', 'group_20'],
                performance_threshold=0.6,
                created_at=datetime.now().isoformat(),
                is_active=True
            )
            strategies.append(ensemble_strategy)

            # Estrategia 2: Especialización por grupos
            for group_size in [4, 8, 14, 15, 20]:
                specialized_strategy = AdaptiveStrategy(
                    strategy_id=f"specialized_group_{group_size}_{int(time.time())}",
                    name=f"Specialized Group {group_size} Strategy",
                    description=f"Modelo especializado para grupo de {group_size} números",
                    model_config={
                        'type': 'specialized',
                        'target_group_size': group_size,
                        'model': best_models[0][0],
                        'confidence_threshold': 0.7
                    },
                    target_groups=[f'group_{group_size}'],
                    performance_threshold=0.65,
                    created_at=datetime.now().isoformat(),
                    is_active=True
                )
                strategies.append(specialized_strategy)

            # Estrategia 3: Adaptativa basada en tiempo
            temporal_strategy = AdaptiveStrategy(
                strategy_id=f"temporal_{int(time.time())}",
                name="Temporal Adaptive Strategy",
                description="Estrategia que se adapta según patrones temporales",
                model_config={
                    'type': 'temporal',
                    'time_windows': ['1min', '5min', '15min'],
                    'model': best_models[0][0],
                    'adaptation_rate': 0.1
                },
                target_groups=['group_8', 'group_15'],
                performance_threshold=0.55,
                created_at=datetime.now().isoformat(),
                is_active=True
            )
            strategies.append(temporal_strategy)

            # Guardar estrategias en Redis
            for strategy in strategies:
                strategy_key = f"ai:strategies:{strategy.strategy_id}"
                strategy_data = {
                    'name': strategy.name,
                    'description': strategy.description,
                    'model_config': json.dumps(strategy.model_config),
                    'target_groups': json.dumps(strategy.target_groups),
                    'performance_threshold': strategy.performance_threshold,
                    'created_at': strategy.created_at,
                    'is_active': strategy.is_active
                }
                self.redis_client.hset(strategy_key, mapping=strategy_data)

            logger.info(f"Generated {len(strategies)} adaptive strategies")

        except Exception as e:
            logger.error(f"Error generating adaptive strategies: {e}")

    def evaluate_strategy_performance(self, strategy_id: str, actual_results: List[Dict]):
        """Evaluar el rendimiento de una estrategia específica"""
        try:
            strategy_key = f"ai:strategies:{strategy_id}"
            if not self.redis_client.exists(strategy_key):
                logger.warning(f"Strategy {strategy_id} not found")
                return None

            # Calcular métricas de rendimiento
            total_predictions = len(actual_results)
            correct_predictions = sum(1 for result in actual_results if result.get('success', False))
            success_rate = correct_predictions / total_predictions if total_predictions > 0 else 0

            avg_confidence = sum(result.get('confidence', 0) for result in actual_results) / total_predictions if total_predictions > 0 else 0

            # Crear objeto de rendimiento
            performance = StrategyPerformance(
                strategy_id=strategy_id,
                success_rate=success_rate,
                total_predictions=total_predictions,
                correct_predictions=correct_predictions,
                avg_confidence=avg_confidence,
                last_updated=datetime.now().isoformat(),
                model_type="adaptive",
                hyperparameters={},
                feature_importance={}
            )

            # Guardar métricas
            performance_key = f"ai:performance:{strategy_id}"
            performance_data = {
                'success_rate': success_rate,
                'total_predictions': total_predictions,
                'correct_predictions': correct_predictions,
                'avg_confidence': avg_confidence,
                'last_updated': performance.last_updated
            }
            self.redis_client.hset(performance_key, mapping=performance_data)

            # Actualizar historial
            self.performance_history[strategy_id].append(performance)

            logger.info(f"Strategy {strategy_id} performance: {success_rate:.3f} ({correct_predictions}/{total_predictions})")

            return performance

        except Exception as e:
            logger.error(f"Error evaluating strategy performance: {e}")
            return None

    def get_best_strategy(self) -> Optional[str]:
        """Obtener la estrategia con mejor rendimiento actual"""
        try:
            strategy_keys = self.redis_client.keys("ai:performance:*")
            if not strategy_keys:
                return None

            best_strategy = None
            best_score = 0

            for key in strategy_keys:
                performance_data = self.redis_client.hgetall(key)
                success_rate = float(performance_data.get('success_rate', 0))
                total_predictions = int(performance_data.get('total_predictions', 0))

                # Solo considerar estrategias con suficientes predicciones
                if total_predictions >= 10 and success_rate > best_score:
                    best_score = success_rate
                    best_strategy = key.replace('ai:performance:', '')

            return best_strategy

        except Exception as e:
            logger.error(f"Error getting best strategy: {e}")
            return None

    def make_ensemble_prediction(self, features: Dict) -> Dict:
        """Hacer predicción usando ensemble de modelos"""
        try:
            if not self.models:
                logger.warning("No models available for ensemble prediction")
                return {}

            predictions = {}
            confidences = {}

            # Preparar features para predicción
            feature_df = pd.DataFrame([features])

            # Hacer predicciones con cada modelo
            for model_name, model in self.models.items():
                try:
                    # Asegurar que tenemos todas las features necesarias
                    if hasattr(model, 'feature_names_in_'):
                        required_features = model.feature_names_in_
                        for feature in required_features:
                            if feature not in feature_df.columns:
                                feature_df[feature] = 0
                        feature_df = feature_df[required_features]

                    # Hacer predicción
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(feature_df)[0]
                        pred = model.predict(feature_df)[0]
                        conf = max(proba)
                    else:
                        pred = model.predict(feature_df)[0]
                        conf = 0.5  # Confianza por defecto

                    predictions[model_name] = pred
                    confidences[model_name] = conf

                except Exception as e:
                    logger.error(f"Error in {model_name} prediction: {e}")

            if not predictions:
                return {}

            # Combinar predicciones (voting ensemble)
            final_prediction = max(set(predictions.values()), key=list(predictions.values()).count)
            final_confidence = sum(confidences.values()) / len(confidences)

            return {
                'prediction': final_prediction,
                'confidence': final_confidence,
                'individual_predictions': predictions,
                'individual_confidences': confidences,
                'model_count': len(predictions)
            }

        except Exception as e:
            logger.error(f"Error in ensemble prediction: {e}")
            return {}

    def _get_training_data(self):
        """Obtener datos de entrenamiento actualizados desde Redis"""
        try:
            # Obtener features desde el sistema Redis Enhanced
            features_list = self.redis_client.lrange('ml:features:history', 0, -1)

            if not features_list:
                logger.warning("No features found in Redis")
                return None

            training_data = []
            for feature_str in features_list:
                try:
                    feature_data = json.loads(feature_str)
                    training_data.append(feature_data)
                except json.JSONDecodeError:
                    continue

            logger.info(f"Retrieved {len(training_data)} training samples from Redis")
            return training_data

        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return None

    def _prepare_training_data(self, training_data):
        """Preparar datos para entrenamiento"""
        try:
            if not training_data:
                return None, None

            # Convertir a DataFrame
            df = pd.DataFrame(training_data)

            # Extraer target (número de la ruleta)
            if 'target_number' not in df.columns:
                logger.error("No target_number column found in training data")
                return None, None

            y = df['target_number'].values

            # Extraer features (excluir target y metadata)
            feature_columns = [col for col in df.columns
                             if col not in ['target_number', 'timestamp', 'session_id', 'entry_id']]

            if not feature_columns:
                logger.error("No feature columns found")
                return None, None

            X = df[feature_columns]

            # Convertir a tipos numéricos
            X = X.apply(pd.to_numeric, errors='coerce').fillna(0)

            logger.info(f"Prepared training data: {len(X)} samples, {len(feature_columns)} features")
            return X, y

        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return None, None

    def get_strategy_summary(self) -> Dict:
        """Obtener resumen de todas las estrategias"""
        try:
            summary = {
                'total_strategies': 0,
                'active_strategies': 0,
                'best_strategy': None,
                'avg_performance': 0,
                'last_retrain': None,
                'models_available': list(self.models.keys())
            }

            # Contar estrategias
            strategy_keys = self.redis_client.keys("ai:strategies:*")
            summary['total_strategies'] = len(strategy_keys)

            active_count = 0
            for key in strategy_keys:
                strategy_data = self.redis_client.hgetall(key)
                if strategy_data.get('is_active') == 'True':
                    active_count += 1

            summary['active_strategies'] = active_count
            summary['best_strategy'] = self.get_best_strategy()

            # Último re-entrenamiento
            last_retrain = self.redis_client.get('ai:last_retrain_timestamp')
            if last_retrain:
                summary['last_retrain'] = last_retrain

            return summary

        except Exception as e:
            logger.error(f"Error getting strategy summary: {e}")
            return {}

def create_strategy_optimizer(redis_client) -> AIStrategyOptimizer:
    """Factory function para crear el optimizador de estrategias"""
    if not ML_AVAILABLE:
        logger.error("ML libraries not available for strategy optimization")
        return None

    return AIStrategyOptimizer(redis_client)