import psycopg2
import redis
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
from contextlib import contextmanager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        # PostgreSQL connection - try multiple environment variables
        self.pg_connection_string = (
            os.getenv('DATABASE_PUBLIC_URL') or
            os.getenv('DATABASE_URL') or
            'postgresql://postgres:JqPnbywtvvZyINvBFikSRYdKqGmtTFFj@trolley.proxy.rlwy.net:10515/railway'
        )
        
        # Redis connection - try multiple environment variables
        self.redis_url = (
            os.getenv('REDIS_PUBLIC_URL') or
            os.getenv('Connection_redis') or
            os.getenv('REDIS_URL') or
            'redis://default:kuBKgwJxPrMoMOWqpobsGZIcpgnOFwoW@ballast.proxy.rlwy.net:58381'
        )
        
        # Initialize Redis client
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None
    
    @contextmanager
    def get_db_connection(self):
        """Context manager for PostgreSQL connections"""
        conn = None
        try:
            conn = psycopg2.connect(self.pg_connection_string)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_color_for_number(self, number: int) -> str:
        """Determine color for roulette number"""
        if number == 0:
            return 'green'
        
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        return 'red' if number in red_numbers else 'black'
    
    # ============================================================================
    # REDIS CACHE OPERATIONS
    # ============================================================================
    
    def cache_recent_numbers(self, numbers: List[Dict], limit: int = 50):
        """Cache recent numbers in Redis for fast retrieval"""
        if not self.redis_client:
            return
        
        try:
            # Store as JSON string with expiration
            cache_data = {
                'numbers': numbers[:limit],
                'timestamp': datetime.utcnow().isoformat(),
                'count': len(numbers)
            }
            
            self.redis_client.setex(
                'recent_numbers', 
                300,  # 5 minutes expiration
                json.dumps(cache_data)
            )
            
            # Also store individual numbers for quick lookup
            for i, num_data in enumerate(numbers[:20]):  # Store top 20 for quick access
                self.redis_client.setex(
                    f'recent_number_{i}',
                    300,
                    json.dumps(num_data)
                )
                
            logger.info(f"✅ Cached {len(numbers)} recent numbers in Redis")
            
        except Exception as e:
            logger.error(f"❌ Redis cache error: {e}")
    
    def get_cached_recent_numbers(self, limit: int = 20) -> Optional[List[Dict]]:
        """Get recent numbers from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get('recent_numbers')
            if cached_data:
                data = json.loads(cached_data)
                numbers = data.get('numbers', [])
                logger.info(f"✅ Retrieved {len(numbers)} numbers from Redis cache")
                return numbers[:limit]
        except Exception as e:
            logger.error(f"❌ Redis retrieval error: {e}")
        
        return None
    
    def invalidate_cache(self):
        """Invalidate Redis cache"""
        if not self.redis_client:
            return
        
        try:
            # Delete main cache
            self.redis_client.delete('recent_numbers')
            
            # Delete individual number caches
            for i in range(20):
                self.redis_client.delete(f'recent_number_{i}')
                
            logger.info("✅ Redis cache invalidated")
        except Exception as e:
            logger.error(f"❌ Redis cache invalidation error: {e}")
    
    # ============================================================================
    # ROULETTE NUMBERS OPERATIONS
    # ============================================================================
    
    def get_last_roulette_numbers(self, limit: int = 20) -> List[Dict]:
        """Get the most recent roulette numbers from Redis"""
        
        if not self.redis_client:
            logger.warning("⚠️ Redis not available, returning empty list")
            return []
        
        try:
            # Get numbers from Redis roulette:history list
            history_numbers = self.redis_client.lrange('roulette:history', 0, limit - 1)
            
            if not history_numbers:
                logger.info("📭 No numbers found in roulette:history")
                return []
            
            # Transform to match frontend expectations
            numbers = []
            for i, number_str in enumerate(history_numbers):
                try:
                    number = int(number_str)
                    color = self.get_color_for_number(number)
                    
                    numbers.append({
                        'id': i + 1,  # Sequential ID
                        'history_entry_id': i + 1,
                        'number': number,  # Frontend expects 'number'
                        'number_value': number,  # Keep original field name too
                        'color': color,
                        'created_at': datetime.utcnow().isoformat(),  # Current timestamp as placeholder
                        'timestamp': datetime.utcnow().isoformat()
                    })
                except ValueError:
                    logger.warning(f"⚠️ Invalid number in Redis history: {number_str}")
                    continue
            
            logger.info(f"✅ Retrieved {len(numbers)} numbers from Redis roulette:history")
            return numbers
            
        except Exception as e:
            logger.error(f"❌ Error getting roulette numbers from Redis: {e}")
            return []
    
    def insert_roulette_number(self, number: int, custom_timestamp: Optional[str] = None) -> Dict:
        """Insert a new roulette number into Redis"""
        
        # Validate number
        if not (0 <= number <= 36):
            logger.error(f"Invalid roulette number: {number}")
            return {'success': False, 'error': f'Invalid roulette number: {number}'}
        
        if not self.redis_client:
            logger.error("❌ Redis not available for inserting number")
            return {'success': False, 'error': 'Redis not available'}
        
        color = self.get_color_for_number(number)
        timestamp = custom_timestamp or datetime.utcnow().isoformat()
        
        try:
            # Update Redis keys
            # 1. Add to the beginning of roulette:history list (most recent first)
            self.redis_client.lpush('roulette:history', str(number))
            
            # 2. Update roulette:latest with the new number
            self.redis_client.set('roulette:latest', str(number))
            
            # 3. Update color counters
            if color == 'red':
                self.redis_client.incr('roulette:colors:red')
            elif color == 'black':
                self.redis_client.incr('roulette:colors:black')
            elif color == 'green':
                self.redis_client.incr('roulette:colors:green')
            
            # 4. Update total spins counter
            self.redis_client.incr('roulette:total_spins')
            
            # 5. Update stats hash
            stats_data = {
                'last_update': timestamp,
                'latest_number': str(number),
                'latest_color': color,
                'numbers_processed': str(self.redis_client.get('roulette:total_spins') or '1')
            }
            self.redis_client.hset('roulette:stats', mapping=stats_data)
            
            # 6. Keep only the last 100 numbers in history (trim the list)
            self.redis_client.ltrim('roulette:history', 0, 99)
            
            # Generate a sequential ID based on current list length
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
            
            logger.info(f"✅ Inserted number {number} into Redis successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error inserting number {number} into Redis: {e}")
            return {'success': False, 'error': str(e)}
    
    def insert_multiple_numbers(self, numbers: List[int], force: bool = False) -> Dict:
        """Insert multiple numbers with proper chronological order"""
        
        if not numbers:
            return {'success': False, 'error': 'No numbers provided'}
        
        # Validate all numbers
        invalid_numbers = [n for n in numbers if not (0 <= n <= 36)]
        if invalid_numbers and not force:
            return {'success': False, 'error': f'Invalid numbers: {invalid_numbers}'}
        
        # Filter valid numbers
        valid_numbers = [n for n in numbers if 0 <= n <= 36]
        
        if not valid_numbers:
            return {'success': False, 'error': 'No valid numbers to insert'}
        
        # Process in reverse order (oldest first chronologically)
        process_order = list(reversed(valid_numbers))
        
        results = []
        base_time = datetime.utcnow()
        
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    for i, number in enumerate(process_order):
                        # Calculate timestamp for chronological order
                        adjusted_time = base_time - timedelta(seconds=(len(process_order) - i - 1))
                        
                        color = self.get_color_for_number(number)
                        
                        # Insert into history
                        cur.execute("""
                            INSERT INTO roulette_history (numbers_string, created_at)
                            VALUES (%s, %s)
                            RETURNING id
                        """, (str(number), adjusted_time))
                        
                        history_result = cur.fetchone()
                        if not history_result:
                            continue
                        history_id = history_result[0]
                        
                        # Insert into individual numbers
                        cur.execute("""
                            INSERT INTO roulette_numbers_individual 
                            (history_entry_id, number_value, color, created_at)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id, history_entry_id, number_value, color, created_at
                        """, (history_id, number, color, adjusted_time))
                        
                        row = cur.fetchone()
                        if row:
                            results.append({
                                'id': row[0],
                                'history_entry_id': row[1],
                                'number': row[2],
                                'number_value': row[2],
                                'color': row[3],
                                'created_at': row[4].isoformat() if row[4] else None
                            })
                    
                    conn.commit()
                    
                    # Invalidate cache
                    self.invalidate_cache()
                    
                    logger.info(f"✅ Inserted {len(results)} numbers successfully")
                    
                    return {
                        'success': True,
                        'processed_count': len(results),
                        'total_input': len(valid_numbers),
                        'numbers': [r['number'] for r in results],
                        'last_played': valid_numbers[0],  # First in original order is most recent
                        'individual_entries': results
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error inserting multiple numbers: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============================================================================
    # STATISTICS AND ANALYSIS
    # ============================================================================
    
    def get_roulette_stats(self, limit: int = 500) -> Optional[Dict]:
        """Get comprehensive roulette statistics"""
        
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get recent numbers for analysis
                    cur.execute("""
                        SELECT number_value, color, created_at
                        FROM roulette_numbers_individual
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (limit,))
                    
                    rows = cur.fetchall()
                    
                    if not rows:
                        return None
                    
                    # Initialize counters
                    number_counts = {}
                    red_count = black_count = 0
                    odd_count = even_count = 0
                    columns = {'c1': 0, 'c2': 0, 'c3': 0}
                    dozens = {'d1': 0, 'd2': 0, 'd3': 0}
                    terminals = [0] * 10
                    
                    # Get last 20 numbers for display (most recent first)
                    last_numbers = [row[0] for row in rows[:20]]
                    
                    # Analyze all numbers
                    for number, color, _ in rows:
                        # Count occurrences
                        number_counts[number] = number_counts.get(number, 0) + 1
                        
                        # Color analysis
                        if color == 'red':
                            red_count += 1
                        elif color == 'black':
                            black_count += 1
                        
                        # Odd/Even analysis (excluding 0)
                        if number != 0:
                            if number % 2 == 0:
                                even_count += 1
                            else:
                                odd_count += 1
                        
                        # Column analysis
                        if number != 0:
                            if number % 3 == 1:
                                columns['c1'] += 1
                            elif number % 3 == 2:
                                columns['c2'] += 1
                            else:
                                columns['c3'] += 1
                        
                        # Dozen analysis
                        if 1 <= number <= 12:
                            dozens['d1'] += 1
                        elif 13 <= number <= 24:
                            dozens['d2'] += 1
                        elif 25 <= number <= 36:
                            dozens['d3'] += 1
                        
                        # Terminal analysis
                        terminals[number % 10] += 1
                    
                    # Get hot and cold numbers
                    sorted_numbers = sorted(number_counts.items(), key=lambda x: x[1], reverse=True)
                    hot_numbers = [num for num, _ in sorted_numbers[:5]]
                    cold_numbers = [num for num, _ in sorted_numbers[-5:]]
                    
                    # Get hot terminals
                    terminal_data = [(i, count) for i, count in enumerate(terminals)]
                    terminal_data.sort(key=lambda x: x[1], reverse=True)
                    hot_terminals = [t[0] for t in terminal_data[:3]]
                    
                    return {
                        'hot_numbers': hot_numbers,
                        'cold_numbers': cold_numbers,
                        'red_vs_black': {'red': red_count, 'black': black_count},
                        'odd_vs_even': {'odd': odd_count, 'even': even_count},
                        'columns': columns,
                        'dozens': dozens,
                        'last_numbers': last_numbers,
                        'terminals': {
                            'counts': terminals,
                            'hot': hot_terminals
                        }
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return None
    
    # ============================================================================
    # ANALYZER STATE OPERATIONS
    # ============================================================================
    
    def get_analyzer_state(self) -> Optional[Dict]:
        """Get current analyzer state"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM analyzer_state WHERE id = 1")
                    row = cur.fetchone()
                    
                    if not row:
                        # Initialize default state
                        cur.execute("""
                            INSERT INTO analyzer_state (id) VALUES (1)
                            RETURNING *
                        """)
                        row = cur.fetchone()
                        if row:
                            conn.commit()
                    
                    if not row:
                        return None
                    
                    # Convert to dict (assuming column order from schema)
                    columns = [
                        'id', 'aciertos_individual', 'aciertos_grupo', 'aciertos_vecinos_0_10',
                        'aciertos_vecinos_7_27', 'total_predicciones_evaluadas', 'aciertos_tia_lu',
                        'tia_lu_estado_activa', 'tia_lu_estado_giros_jugados', 'tia_lu_estado_activada_con_33',
                        'tia_lu_estado_contador_desencadenantes_consecutivos', 'tia_lu_estado_ultimo_numero_fue_desencadenante',
                        'updated_at'
                    ]
                    
                    return dict(zip(columns, row))
                    
        except Exception as e:
            logger.error(f"❌ Error getting analyzer state: {e}")
            return None
    
    def update_analyzer_state(self, updates: Dict) -> bool:
        """Update analyzer state"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Build dynamic update query
                    set_clauses = []
                    values = []
                    
                    for key, value in updates.items():
                        set_clauses.append(f"{key} = %s")
                        values.append(value)
                    
                    if set_clauses:
                        set_clauses.append("updated_at = %s")
                        values.append(datetime.utcnow())
                        
                        query = f"""
                            UPDATE analyzer_state 
                            SET {', '.join(set_clauses)}
                            WHERE id = 1
                        """
                        
                        cur.execute(query, values)
                        conn.commit()
                        
                        logger.info(f"✅ Updated analyzer state: {list(updates.keys())}")
                        return True
                    
        except Exception as e:
            logger.error(f"❌ Error updating analyzer state: {e}")
            return False
        
        return False
    
    # ============================================================================
    # DATABASE MAINTENANCE
    # ============================================================================
    
    def get_database_status(self) -> Dict:
        """Get database status and statistics"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get table counts
                    cur.execute("SELECT COUNT(*) FROM roulette_history")
                    history_result = cur.fetchone()
                    history_count = history_result[0] if history_result else 0
                    
                    cur.execute("SELECT COUNT(*) FROM roulette_numbers_individual")
                    individual_result = cur.fetchone()
                    individual_count = individual_result[0] if individual_result else 0
                    
                    # Get oldest and newest records
                    cur.execute("""
                        SELECT MIN(created_at), MAX(created_at) 
                        FROM roulette_numbers_individual
                    """)
                    date_result = cur.fetchone()
                    oldest = newest = None
                    if date_result:
                        oldest, newest = date_result
                    
                    # Calculate hours since oldest
                    hours_since_oldest = 0
                    if oldest:
                        hours_since_oldest = (datetime.utcnow() - oldest.replace(tzinfo=None)).total_seconds() / 3600
                    
                    # Get recent record counts
                    cur.execute("""
                        SELECT 
                            COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as last_24h,
                            COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '48 hours') as last_48h
                        FROM roulette_numbers_individual
                    """)
                    recent_result = cur.fetchone()
                    recent_counts = recent_result if recent_result else (0, 0)
                    
                    return {
                        'success': True,
                        'estado': {
                            'total_registros': {
                                'history': history_count,
                                'individual': individual_count
                            },
                            'registro_mas_antiguo': oldest.isoformat() if oldest else None,
                            'registro_mas_reciente': newest.isoformat() if newest else None,
                            'horas_desde_mas_antiguo': hours_since_oldest,
                            'registros_ultimas_24h': recent_counts[0] if recent_counts else 0,
                            'registros_ultimas_48h': recent_counts[1] if recent_counts else 0,
                            'necesita_purga': hours_since_oldest > 48 and individual_count > 100
                        }
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error getting database status: {e}")
            return {'success': False, 'error': str(e)}
    
    def purge_old_records(self, keep_hours: int = 48, keep_minimum: int = 50) -> Dict:
        """Purge old records from database"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Calculate cutoff time
                    cutoff_time = datetime.utcnow() - timedelta(hours=keep_hours)
                    
                    # Count records to be deleted
                    cur.execute("""
                        SELECT COUNT(*) FROM roulette_numbers_individual 
                        WHERE created_at < %s
                    """, (cutoff_time,))
                    
                    old_result = cur.fetchone()
                    old_count = old_result[0] if old_result else 0
                    
                    # Get total count
                    cur.execute("SELECT COUNT(*) FROM roulette_numbers_individual")
                    total_result = cur.fetchone()
                    total_count = total_result[0] if total_result else 0
                    
                    # Check if we should keep minimum records
                    records_to_keep = total_count - old_count
                    if records_to_keep < keep_minimum:
                        # Adjust cutoff to keep minimum records
                        cur.execute("""
                            SELECT created_at FROM roulette_numbers_individual
                            ORDER BY created_at DESC
                            LIMIT 1 OFFSET %s
                        """, (keep_minimum - 1,))
                        
                        result = cur.fetchone()
                        if result:
                            cutoff_time = result[0]
                    
                    # Delete old individual records (cascade will handle history)
                    cur.execute("""
                        DELETE FROM roulette_numbers_individual 
                        WHERE created_at < %s
                    """, (cutoff_time,))
                    
                    deleted_individual = cur.rowcount
                    
                    # Delete orphaned history records
                    cur.execute("""
                        DELETE FROM roulette_history 
                        WHERE id NOT IN (
                            SELECT DISTINCT history_entry_id 
                            FROM roulette_numbers_individual
                        )
                    """)
                    
                    deleted_history = cur.rowcount
                    conn.commit()
                    
                    # Invalidate cache
                    self.invalidate_cache()
                    
                    logger.info(f"✅ Purged {deleted_individual} individual records and {deleted_history} history records")
                    
                    return {
                        'success': True,
                        'deleted_individual': deleted_individual,
                        'deleted_history': deleted_history,
                        'cutoff_time': cutoff_time.isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error purging records: {e}")
            return {'success': False, 'error': str(e)}

# Global database manager instance
db_manager = DatabaseManager()