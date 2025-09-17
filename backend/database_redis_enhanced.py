#!/usr/bin/env python3
"""
Enhanced Redis Database Manager
Sistema mejorado con estructura optimizada, analytics avanzado y soporte para ML
"""

import redis
import json
import os
import pickle
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
import uuid
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedRedisManager:
    def __init__(self):
        # Redis connection
        self.redis_url = (
            os.getenv('REDIS_PUBLIC_URL') or
            os.getenv('Connection_redis') or
            os.getenv('REDIS_URL') or
            'redis://default:kuBKgwJxPrMoMOWqpobsGZIcpgnOFwoW@ballast.proxy.rlwy.net:58381'
        )

        # Inicializar Redis client
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis Enhanced Manager initialized successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None

        # Session management
        self.current_session_id = self._get_or_create_session()

        # Feature engineering constants
        self.RED_NUMBERS = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        self.BLACK_NUMBERS = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]

        # Sectores de la ruleta
        self.SECTORS = {
            'voisins_zero': [22,18,29,7,28,12,35,3,26,0,32,15,19,4,21,2,25],
            'tiers': [27,13,36,11,30,8,23,10,5,24,16,33],
            'orphelins': [17,34,6,1,20,14,31,9]
        }

    def get_color_for_number(self, number: int) -> str:
        """Determinar color para número de ruleta"""
        if number == 0:
            return 'green'
        return 'red' if number in self.RED_NUMBERS else 'black'

    def _get_or_create_session(self) -> str:
        """Obtener o crear ID de sesión actual"""
        try:
            session_id = self.redis_client.get('roulette:sessions:current')
            if not session_id:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.redis_client.set('roulette:sessions:current', session_id)

                # Crear metadata de la sesión
                session_data = {
                    'session_id': session_id,
                    'start_time': datetime.utcnow().isoformat(),
                    'numbers_count': 0,
                    'status': 'active'
                }
                self.redis_client.hset(f'roulette:sessions:{session_id}', mapping=session_data)

            return session_id
        except Exception as e:
            logger.error(f"Error managing session: {e}")
            return f"session_{int(time.time())}"

    # ============================================================================
    # ENHANCED NUMBER INSERTION WITH ANALYTICS
    # ============================================================================

    def insert_roulette_number_enhanced(self, number: int, custom_timestamp: Optional[str] = None) -> Dict:
        """Insertar número con analytics mejorado y features para ML"""

        if not (0 <= number <= 36):
            return {'success': False, 'error': f'Invalid number: {number}'}

        if not self.redis_client:
            return {'success': False, 'error': 'Redis not available'}

        try:
            timestamp = custom_timestamp or datetime.utcnow().isoformat()
            timestamp_unix = int(datetime.utcnow().timestamp())
            color = self.get_color_for_number(number)

            # Generate unique ID for this number entry
            entry_id = f"num_{timestamp_unix}_{number}"

            # Pipeline para operaciones atómicas
            pipe = self.redis_client.pipeline()

            # 1. DATOS BÁSICOS (mantenemos compatibilidad)
            pipe.lpush('roulette:history', str(number))
            pipe.set('roulette:latest', str(number))
            pipe.incr('roulette:total_spins')
            pipe.incr(f'roulette:colors:{color}')

            # 2. TIMELINE CON TIMESTAMPS
            pipe.zadd('roulette:timeline', {number: timestamp_unix})

            # 3. METADATA DETALLADA
            metadata = {
                'number': str(number),
                'color': color,
                'timestamp': timestamp,
                'timestamp_unix': str(timestamp_unix),
                'session_id': self.current_session_id,
                'entry_id': entry_id
            }
            pipe.hset(f'roulette:metadata:{entry_id}', mapping=metadata)

            # 4. ANALYTICS PATTERNS
            self._update_patterns(pipe, number, color, timestamp_unix)

            # 5. ROLLING STATISTICS (ventanas móviles)
            self._update_rolling_stats(pipe, number, color, timestamp_unix)

            # 6. MACHINE LEARNING FEATURES
            features = self._extract_features(number)
            if features:
                pipe.hset('ml:features:current', mapping=features)
                pipe.lpush('ml:features:history', json.dumps({
                    'timestamp': timestamp,
                    'features': features,
                    'target': number
                }))
                pipe.ltrim('ml:features:history', 0, 499)  # Mantener últimas 500

            # 7. PERFORMANCE METRICS
            pipe.hset('performance:metrics', mapping={
                'last_insert': timestamp,
                'total_operations': str(self.redis_client.get('performance:operations') or 0)
            })
            pipe.incr('performance:operations')

            # 8. LIMPIEZA (mantener tamaños controlados)
            pipe.ltrim('roulette:history', 0, 199)  # Últimos 200 números
            pipe.zremrangebyrank('roulette:timeline', 0, -201)  # Últimos 200 en timeline

            # Ejecutar pipeline
            pipe.execute()

            # Actualizar sesión
            self._update_session_stats()

            result = {
                'success': True,
                'data': {
                    'entry_id': entry_id,
                    'number': number,
                    'color': color,
                    'timestamp': timestamp,
                    'session_id': self.current_session_id,
                    'features_extracted': bool(features)
                }
            }

            logger.info(f"Enhanced insert: {number} ({color}) with features")
            return result

        except Exception as e:
            logger.error(f"Error in enhanced insert: {e}")
            return {'success': False, 'error': str(e)}

    def _update_patterns(self, pipe, number: int, color: str, timestamp_unix: int):
        """Actualizar patrones de analytics"""

        # 1. STREAKS (rachas de colores)
        last_colors = self.redis_client.lrange('analytics:patterns:streaks', 0, 4)
        if last_colors and last_colors[0] == color:
            # Continua la racha
            current_streak = int(self.redis_client.get('analytics:current_streak') or 1)
            pipe.set('analytics:current_streak', current_streak + 1)
        else:
            # Nueva racha
            pipe.set('analytics:current_streak', 1)

        pipe.lpush('analytics:patterns:streaks', color)
        pipe.ltrim('analytics:patterns:streaks', 0, 49)  # Últimos 50 colores

        # 2. GAPS (distancias entre repeticiones)
        last_position = self.redis_client.get(f'analytics:last_position:{number}')
        if last_position:
            gap = timestamp_unix - int(last_position)
            pipe.lpush(f'analytics:patterns:gaps:{number}', str(gap))
            pipe.ltrim(f'analytics:patterns:gaps:{number}', 0, 9)  # Últimos 10 gaps

        pipe.set(f'analytics:last_position:{number}', timestamp_unix)

        # 3. SECTORES
        for sector_name, sector_numbers in self.SECTORS.items():
            if number in sector_numbers:
                pipe.incr(f'analytics:patterns:sectors:{sector_name}')

    def _update_rolling_stats(self, pipe, number: int, color: str, timestamp_unix: int):
        """Actualizar estadísticas de ventanas móviles"""

        # Ventanas de tiempo (en segundos)
        windows = {
            '1min': 60,
            '5min': 300,
            '15min': 900
        }

        for window_name, window_seconds in windows.items():
            window_start = timestamp_unix - window_seconds

            # Obtener números en la ventana
            numbers_in_window = self.redis_client.zrangebyscore(
                'roulette:timeline',
                window_start,
                timestamp_unix
            )

            if numbers_in_window:
                # Calcular estadísticas
                colors_count = {'red': 0, 'black': 0, 'green': 0}
                for num in numbers_in_window:
                    num_int = int(float(num))
                    num_color = self.get_color_for_number(num_int)
                    colors_count[num_color] += 1

                # Almacenar estadísticas
                stats = {
                    'total': str(len(numbers_in_window)),
                    'red': str(colors_count['red']),
                    'black': str(colors_count['black']),
                    'green': str(colors_count['green']),
                    'last_update': str(timestamp_unix)
                }

                pipe.hset(f'analytics:rolling:{window_name}', mapping=stats)

    def _extract_features(self, current_number: int) -> Dict:
        """Extraer features para machine learning"""
        try:
            # Obtener historial reciente
            recent_numbers = self.redis_client.lrange('roulette:history', 0, 19)  # Últimos 20
            if len(recent_numbers) < 5:
                return {}  # Necesitamos al menos 5 números para features útiles

            # Convertir a enteros
            numbers = [int(n) for n in recent_numbers]

            features = {}

            # 1. FEATURES BÁSICAS
            features['current_number'] = current_number
            features['last_1'] = numbers[0] if len(numbers) > 0 else 0
            features['last_2'] = numbers[1] if len(numbers) > 1 else 0
            features['last_3'] = numbers[2] if len(numbers) > 2 else 0

            # 2. FEATURES DE COLOR
            colors = [self.get_color_for_number(n) for n in numbers[:10]]
            features['red_count_10'] = colors.count('red')
            features['black_count_10'] = colors.count('black')
            features['green_count_10'] = colors.count('green')

            # 3. FEATURES DE SECTORES
            for sector_name, sector_nums in self.SECTORS.items():
                sector_count = sum(1 for n in numbers[:10] if n in sector_nums)
                features[f'sector_{sector_name}_count_10'] = sector_count

            # 4. FEATURES ESTADÍSTICAS
            features['mean_last_10'] = np.mean(numbers[:10]) if len(numbers) >= 10 else 0
            features['std_last_10'] = np.std(numbers[:10]) if len(numbers) >= 10 else 0

            # 5. FEATURES DE PATRONES
            # Distancia desde la última aparición
            if current_number in numbers:
                features['gap_since_last'] = numbers.index(current_number)
            else:
                features['gap_since_last'] = 20  # Máximo

            # Par/Impar en últimos 10
            even_count = sum(1 for n in numbers[:10] if n != 0 and n % 2 == 0)
            features['even_count_10'] = even_count
            features['odd_count_10'] = 10 - even_count - colors[:10].count('green')

            # 6. FEATURES TEMPORALES
            features['hour'] = datetime.now().hour
            features['minute'] = datetime.now().minute

            return features

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {}

    def _update_session_stats(self):
        """Actualizar estadísticas de la sesión actual"""
        try:
            session_key = f'roulette:sessions:{self.current_session_id}'
            current_count = int(self.redis_client.hget(session_key, 'numbers_count') or 0)

            self.redis_client.hset(session_key, mapping={
                'numbers_count': current_count + 1,
                'last_update': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error updating session stats: {e}")

    # ============================================================================
    # ENHANCED DATA RETRIEVAL
    # ============================================================================

    def get_enhanced_roulette_numbers(self, limit: int = 20) -> List[Dict]:
        """Obtener números con metadata enhancida"""
        try:
            # Obtener números básicos
            history_numbers = self.redis_client.lrange('roulette:history', 0, limit - 1)

            if not history_numbers:
                return []

            enhanced_numbers = []

            for i, number_str in enumerate(history_numbers):
                number = int(number_str)
                color = self.get_color_for_number(number)

                # Buscar metadata si existe
                timeline_entries = self.redis_client.zrevrangebyscore(
                    'roulette:timeline', '+inf', '-inf',
                    start=i, num=1
                )

                timestamp = datetime.utcnow() - timedelta(seconds=i * 30)  # Fallback

                enhanced_numbers.append({
                    'id': i + 1,
                    'number': number,
                    'color': color,
                    'timestamp': timestamp.isoformat(),
                    'position_in_history': i
                })

            return enhanced_numbers

        except Exception as e:
            logger.error(f"Error getting enhanced numbers: {e}")
            return []

    def get_ml_features_history(self, limit: int = 100) -> List[Dict]:
        """Obtener historial de features para ML"""
        try:
            features_history = self.redis_client.lrange('ml:features:history', 0, limit - 1)

            parsed_features = []
            for feature_json in features_history:
                try:
                    feature_data = json.loads(feature_json)
                    parsed_features.append(feature_data)
                except json.JSONDecodeError:
                    continue

            return parsed_features

        except Exception as e:
            logger.error(f"Error getting ML features: {e}")
            return []

    def get_analytics_summary(self) -> Dict:
        """Obtener resumen completo de analytics"""
        try:
            summary = {}

            # 1. PATRONES
            summary['patterns'] = {}

            # Rachas actuales
            current_streak = self.redis_client.get('analytics:current_streak') or 0
            summary['patterns']['current_streak'] = int(current_streak)

            # Sectores
            summary['patterns']['sectors'] = {}
            for sector_name in self.SECTORS.keys():
                count = self.redis_client.get(f'analytics:patterns:sectors:{sector_name}') or 0
                summary['patterns']['sectors'][sector_name] = int(count)

            # 2. ROLLING STATS
            summary['rolling_stats'] = {}
            for window in ['1min', '5min', '15min']:
                stats = self.redis_client.hgetall(f'analytics:rolling:{window}')
                if stats:
                    summary['rolling_stats'][window] = {
                        k: int(v) if v.isdigit() else v for k, v in stats.items()
                    }

            # 3. ML STATUS
            summary['ml_status'] = {}
            features_count = self.redis_client.llen('ml:features:history')
            summary['ml_status']['features_available'] = features_count
            summary['ml_status']['ready_for_training'] = features_count >= 50

            # 4. PERFORMANCE
            performance = self.redis_client.hgetall('performance:metrics')
            summary['performance'] = performance

            return summary

        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return {}

    # ============================================================================
    # COMPATIBILITY METHODS
    # ============================================================================

    def get_last_roulette_numbers(self, limit: int = 20) -> List[Dict]:
        """Mantener compatibilidad con el sistema existente"""
        return self.get_enhanced_roulette_numbers(limit)

    def insert_roulette_number(self, number: int, custom_timestamp: Optional[str] = None) -> Dict:
        """Mantener compatibilidad con el sistema existente"""
        return self.insert_roulette_number_enhanced(number, custom_timestamp)

    def get_database_status(self) -> Dict:
        """Estado de la base de datos enhanced"""
        try:
            # Stats básicas
            history_count = self.redis_client.llen('roulette:history')
            total_spins = int(self.redis_client.get('roulette:total_spins') or 0)
            latest_number = self.redis_client.get('roulette:latest')

            # Contadores de colores
            red_count = int(self.redis_client.get('roulette:colors:red') or 0)
            black_count = int(self.redis_client.get('roulette:colors:black') or 0)
            green_count = int(self.redis_client.get('roulette:colors:green') or 0)

            # Info de Redis
            info = self.redis_client.info()
            memory_used = info.get('used_memory_human', 'N/A')

            # Analytics status
            analytics = self.get_analytics_summary()

            return {
                'success': True,
                'storage_type': 'redis_enhanced',
                'estado': {
                    'total_registros': {
                        'history': history_count,
                        'individual': history_count
                    },
                    'total_spins': total_spins,
                    'latest_number': latest_number,
                    'color_distribution': {
                        'red': red_count,
                        'black': black_count,
                        'green': green_count
                    },
                    'memory_usage': {
                        'used': memory_used
                    },
                    'analytics_status': analytics,
                    'session_id': self.current_session_id,
                    'redis_keys_count': self.redis_client.dbsize()
                }
            }

        except Exception as e:
            logger.error(f"Error getting database status: {e}")
            return {'success': False, 'error': str(e)}

# Instancia global
enhanced_db_manager = EnhancedRedisManager()