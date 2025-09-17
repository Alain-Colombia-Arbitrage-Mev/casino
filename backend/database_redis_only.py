#!/usr/bin/env python3
"""
Database Manager - Solo Redis
Sistema simplificado que usa únicamente Redis para almacenamiento de alta velocidad
"""

import redis
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisOnlyDatabaseManager:
    def __init__(self):
        # Redis connection - múltiples variables de entorno
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
            logger.info("✅ Redis connection established (Redis-only mode)")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None

    def get_color_for_number(self, number: int) -> str:
        """Determinar color para número de ruleta"""
        if number == 0:
            return 'green'

        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        return 'red' if number in red_numbers else 'black'

    # ============================================================================
    # OPERACIONES DE NÚMEROS DE RULETA (SOLO REDIS)
    # ============================================================================

    def get_last_roulette_numbers(self, limit: int = 20) -> List[Dict]:
        """Obtener números más recientes desde Redis únicamente"""

        if not self.redis_client:
            logger.warning("⚠️ Redis not available, returning empty list")
            return []

        try:
            # Obtener números desde Redis roulette:history list
            history_numbers = self.redis_client.lrange('roulette:history', 0, limit - 1)

            if not history_numbers:
                logger.info("📭 No numbers found in roulette:history")
                return []

            # Transformar para compatibilidad con frontend
            numbers = []
            for i, number_str in enumerate(history_numbers):
                try:
                    number = int(number_str)
                    color = self.get_color_for_number(number)

                    # Generar timestamp simulado (más reciente primero)
                    timestamp = datetime.utcnow() - timedelta(seconds=i * 30)

                    numbers.append({
                        'id': i + 1,
                        'history_entry_id': i + 1,
                        'number': number,
                        'number_value': number,
                        'color': color,
                        'created_at': timestamp.isoformat(),
                        'timestamp': timestamp.isoformat()
                    })
                except ValueError:
                    logger.warning(f"⚠️ Invalid number in Redis history: {number_str}")
                    continue

            logger.info(f"✅ Retrieved {len(numbers)} numbers from Redis")
            return numbers

        except Exception as e:
            logger.error(f"❌ Error getting roulette numbers from Redis: {e}")
            return []

    def insert_roulette_number(self, number: int, custom_timestamp: Optional[str] = None) -> Dict:
        """Insertar nuevo número en Redis únicamente"""

        # Validar número
        if not (0 <= number <= 36):
            logger.error(f"Invalid roulette number: {number}")
            return {'success': False, 'error': f'Invalid roulette number: {number}'}

        if not self.redis_client:
            logger.error("❌ Redis not available for inserting number")
            return {'success': False, 'error': 'Redis not available'}

        color = self.get_color_for_number(number)
        timestamp = custom_timestamp or datetime.utcnow().isoformat()

        try:
            # Operaciones Redis (atómicas)
            pipe = self.redis_client.pipeline()

            # 1. Añadir al inicio de roulette:history (más reciente primero)
            pipe.lpush('roulette:history', str(number))

            # 2. Actualizar roulette:latest
            pipe.set('roulette:latest', str(number))

            # 3. Actualizar contadores de colores
            if color == 'red':
                pipe.incr('roulette:colors:red')
            elif color == 'black':
                pipe.incr('roulette:colors:black')
            elif color == 'green':
                pipe.incr('roulette:colors:green')

            # 4. Actualizar total spins
            pipe.incr('roulette:total_spins')

            # 5. Mantener solo últimos 200 números
            pipe.ltrim('roulette:history', 0, 199)

            # 6. Actualizar hash de estadísticas
            pipe.hset('roulette:stats', mapping={
                'last_update': timestamp,
                'latest_number': str(number),
                'latest_color': color
            })

            # Ejecutar todas las operaciones
            results = pipe.execute()

            # Obtener longitud actual del historial
            history_length = self.redis_client.llen('roulette:history')

            result = {
                'success': True,
                'data': {
                    'id': history_length,
                    'history_entry_id': history_length,
                    'number': number,
                    'number_value': number,
                    'color': color,
                    'created_at': timestamp,
                    'timestamp': timestamp
                }
            }

            logger.info(f"✅ Inserted number {number} ({color}) into Redis successfully")
            return result

        except Exception as e:
            logger.error(f"❌ Error inserting number {number} into Redis: {e}")
            return {'success': False, 'error': str(e)}

    def insert_multiple_numbers(self, numbers: List[int], force: bool = False) -> Dict:
        """Insertar múltiples números en orden cronológico correcto"""

        if not numbers:
            return {'success': False, 'error': 'No numbers provided'}

        # Validar números
        invalid_numbers = [n for n in numbers if not (0 <= n <= 36)]
        if invalid_numbers and not force:
            return {'success': False, 'error': f'Invalid numbers: {invalid_numbers}'}

        # Filtrar números válidos
        valid_numbers = [n for n in numbers if 0 <= n <= 36]

        if not valid_numbers:
            return {'success': False, 'error': 'No valid numbers to insert'}

        if not self.redis_client:
            return {'success': False, 'error': 'Redis not available'}

        try:
            # Procesar en orden inverso para mantener cronología correcta
            # (el último en la lista será el más reciente en Redis)
            results = []
            base_time = datetime.utcnow()

            for i, number in enumerate(reversed(valid_numbers)):
                # Calcular timestamp para orden cronológico
                adjusted_time = base_time - timedelta(seconds=(len(valid_numbers) - i - 1) * 10)

                # Insertar número
                insert_result = self.insert_roulette_number(number, adjusted_time.isoformat())

                if insert_result.get('success'):
                    results.append(insert_result['data'])
                else:
                    logger.warning(f"Failed to insert number {number}: {insert_result.get('error')}")

            logger.info(f"✅ Inserted {len(results)} numbers successfully")

            return {
                'success': True,
                'processed_count': len(results),
                'total_input': len(valid_numbers),
                'numbers': [r['number'] for r in results],
                'last_played': valid_numbers[-1],  # Último en lista original = más reciente
                'individual_entries': results
            }

        except Exception as e:
            logger.error(f"❌ Error inserting multiple numbers: {e}")
            return {'success': False, 'error': str(e)}

    # ============================================================================
    # ESTADÍSTICAS Y ANÁLISIS (SOLO REDIS)
    # ============================================================================

    def get_roulette_stats(self, limit: int = 100) -> Optional[Dict]:
        """Obtener estadísticas completas desde Redis"""

        if not self.redis_client:
            return None

        try:
            # Obtener números recientes para análisis
            recent_numbers_data = self.get_last_roulette_numbers(limit)

            if not recent_numbers_data:
                return None

            # Extraer solo los números
            recent_numbers = [item['number'] for item in recent_numbers_data]

            # Inicializar contadores
            number_counts = {}
            red_count = black_count = green_count = 0
            odd_count = even_count = 0
            columns = {'c1': 0, 'c2': 0, 'c3': 0}
            dozens = {'d1': 0, 'd2': 0, 'd3': 0}
            terminals = [0] * 10

            # Analizar números
            for number in recent_numbers:
                # Contar ocurrencias
                number_counts[number] = number_counts.get(number, 0) + 1

                # Análisis de color
                color = self.get_color_for_number(number)
                if color == 'red':
                    red_count += 1
                elif color == 'black':
                    black_count += 1
                else:
                    green_count += 1

                # Análisis par/impar (excluyendo 0)
                if number != 0:
                    if number % 2 == 0:
                        even_count += 1
                    else:
                        odd_count += 1

                # Análisis de columnas
                if number != 0:
                    if number % 3 == 1:
                        columns['c1'] += 1
                    elif number % 3 == 2:
                        columns['c2'] += 1
                    else:
                        columns['c3'] += 1

                # Análisis de docenas
                if 1 <= number <= 12:
                    dozens['d1'] += 1
                elif 13 <= number <= 24:
                    dozens['d2'] += 1
                elif 25 <= number <= 36:
                    dozens['d3'] += 1

                # Análisis de terminales
                terminals[number % 10] += 1

            # Números calientes y fríos
            sorted_numbers = sorted(number_counts.items(), key=lambda x: x[1], reverse=True)
            hot_numbers = [num for num, _ in sorted_numbers[:5]]
            cold_numbers = [num for num, _ in sorted_numbers[-5:]]

            # Terminales calientes
            terminal_data = [(i, count) for i, count in enumerate(terminals)]
            terminal_data.sort(key=lambda x: x[1], reverse=True)
            hot_terminals = [t[0] for t in terminal_data[:3]]

            return {
                'hot_numbers': hot_numbers,
                'cold_numbers': cold_numbers,
                'red_vs_black': {'red': red_count, 'black': black_count, 'green': green_count},
                'odd_vs_even': {'odd': odd_count, 'even': even_count},
                'columns': columns,
                'dozens': dozens,
                'last_numbers': recent_numbers[:20],  # Últimos 20
                'terminals': {
                    'counts': terminals,
                    'hot': hot_terminals
                },
                'total_analyzed': len(recent_numbers)
            }

        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return None

    # ============================================================================
    # ESTADO DEL SISTEMA (SOLO REDIS)
    # ============================================================================

    def get_database_status(self) -> Dict:
        """Obtener estado del sistema Redis"""
        try:
            if not self.redis_client:
                return {'success': False, 'error': 'Redis not available'}

            # Obtener información básica
            history_count = self.redis_client.llen('roulette:history')
            total_spins = int(self.redis_client.get('roulette:total_spins') or 0)
            latest_number = self.redis_client.get('roulette:latest')

            # Obtener contadores de colores
            red_count = int(self.redis_client.get('roulette:colors:red') or 0)
            black_count = int(self.redis_client.get('roulette:colors:black') or 0)
            green_count = int(self.redis_client.get('roulette:colors:green') or 0)

            # Obtener estadísticas del sistema
            system_stats = self.redis_client.hgetall('system:stats')
            roulette_stats = self.redis_client.hgetall('roulette:stats')

            # Información de memoria Redis
            info = self.redis_client.info()
            memory_used = info.get('used_memory_human', 'N/A')
            memory_peak = info.get('used_memory_peak_human', 'N/A')

            return {
                'success': True,
                'storage_type': 'redis_only',
                'estado': {
                    'total_registros': {
                        'history': history_count,
                        'individual': history_count  # Mismo valor en Redis-only
                    },
                    'total_spins': total_spins,
                    'latest_number': latest_number,
                    'color_distribution': {
                        'red': red_count,
                        'black': black_count,
                        'green': green_count
                    },
                    'memory_usage': {
                        'used': memory_used,
                        'peak': memory_peak
                    },
                    'last_update': roulette_stats.get('last_update', 'N/A'),
                    'sistema_activo': True,
                    'redis_keys_count': self.redis_client.dbsize()
                }
            }

        except Exception as e:
            logger.error(f"❌ Error getting database status: {e}")
            return {'success': False, 'error': str(e)}

    def purge_old_records(self, keep_count: int = 100) -> Dict:
        """Purgar registros antiguos de Redis (mantener solo los más recientes)"""
        try:
            if not self.redis_client:
                return {'success': False, 'error': 'Redis not available'}

            # Obtener cuenta actual
            current_count = self.redis_client.llen('roulette:history')

            if current_count <= keep_count:
                return {
                    'success': True,
                    'message': f'No purge needed. Current: {current_count}, Keep: {keep_count}',
                    'deleted': 0,
                    'remaining': current_count
                }

            # Recortar la lista para mantener solo los más recientes
            self.redis_client.ltrim('roulette:history', 0, keep_count - 1)

            # Obtener nueva cuenta
            new_count = self.redis_client.llen('roulette:history')
            deleted = current_count - new_count

            # Actualizar estadísticas del sistema
            self.redis_client.hset('system:stats', mapping={
                'last_purge': datetime.utcnow().isoformat(),
                'last_purge_deleted': str(deleted)
            })

            logger.info(f"✅ Purged {deleted} old records from Redis")

            return {
                'success': True,
                'deleted': deleted,
                'remaining': new_count,
                'purge_timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error purging records: {e}")
            return {'success': False, 'error': str(e)}

    # ============================================================================
    # OPERACIONES DE ANÁLISIS Y PREDICCIONES
    # ============================================================================

    def get_analysis_data(self, limit: int = 50) -> Dict:
        """Obtener datos para análisis de IA"""
        try:
            if not self.redis_client:
                return {}

            # Obtener historial de números
            history_raw = self.redis_client.lrange('roulette:history', 0, limit - 1)
            history = [int(num) for num in history_raw if num.isdigit()]

            if not history:
                return {}

            # Análisis de patrones
            number_freq = {}
            recent_colors = []

            # Calcular frecuencias y patrones
            for number in history:
                number_freq[number] = number_freq.get(number, 0) + 1

                # Análisis de colores
                color = self.get_color_for_number(number)
                recent_colors.append(color)

            # Números calientes y fríos
            sorted_freq = sorted(number_freq.items(), key=lambda x: x[1], reverse=True)
            hot_numbers = [num for num, freq in sorted_freq[:10]]
            cold_numbers = [num for num, freq in sorted_freq[-10:]]

            # Análisis de sectores
            sectors = {
                'voisins_zero': [22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25],
                'tiers': [27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33],
                'orphelins': [17, 34, 6, 1, 20, 14, 31, 9]
            }

            sector_freq = {}
            for sector_name, sector_nums in sectors.items():
                count = sum(1 for num in history[:30] if num in sector_nums)
                sector_freq[sector_name] = count

            return {
                'history': history,
                'hot_numbers': hot_numbers,
                'cold_numbers': cold_numbers,
                'recent_colors': recent_colors[:15],  # Últimos 15 colores
                'sector_frequency': sector_freq,
                'total_spins': len(history),
                'number_frequencies': number_freq
            }

        except Exception as e:
            logger.error(f"❌ Error getting analysis data: {e}")
            return {}

# Instancia global del manager
db_manager = RedisOnlyDatabaseManager()