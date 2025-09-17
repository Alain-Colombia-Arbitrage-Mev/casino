"""
Base de datos sincronizada para el scraper
Maneja la sincronización entre Redis y PostgreSQL
"""

import redis
import psycopg2
import psycopg2.extras
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class SyncedRouletteDatabase:
    """
    Clase para manejar la sincronización de datos entre Redis y PostgreSQL
    """
    
    def __init__(self):
        self.setup_logging()
        self.redis_client = self.connect_redis()
        self.pg_connection = self.connect_postgresql()
        
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_redis(self) -> Optional[redis.Redis]:
        """Conectar a Redis"""
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            
            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            
            # Probar conexión
            client.ping()
            self.logger.info("Conexión a Redis establecida")
            return client
            
        except Exception as e:
            self.logger.error(f"Error conectando a Redis: {e}")
            return None
    
    def connect_postgresql(self) -> Optional[psycopg2.extensions.connection]:
        """Conectar a PostgreSQL"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                # Construir URL desde componentes individuales
                db_host = os.getenv('DB_HOST', 'localhost')
                db_port = os.getenv('DB_PORT', '5432')
                db_name = os.getenv('DB_NAME', 'aicasino')
                db_user = os.getenv('DB_USER', 'postgres')
                db_password = os.getenv('DB_PASSWORD', '')
                
                database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            connection = psycopg2.connect(database_url)
            connection.autocommit = True
            
            self.logger.info("Conexión a PostgreSQL establecida")
            return connection
            
        except Exception as e:
            self.logger.error(f"Error conectando a PostgreSQL: {e}")
            return None
    
    def save_number(self, number: int, timestamp: Optional[datetime] = None) -> bool:
        """
        Guardar número en ambas bases de datos (Redis y PostgreSQL)
        
        Args:
            number: Número de la ruleta (0-36)
            timestamp: Timestamp del número (opcional, usa datetime.now() si no se proporciona)
            
        Returns:
            bool: True si se guardó exitosamente en ambas bases
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        success_redis = self.save_to_redis(number, timestamp)
        success_pg = self.save_to_postgresql(number, timestamp)
        
        if success_redis and success_pg:
            self.logger.info(f"Número {number} guardado exitosamente en ambas bases de datos")
            return True
        else:
            self.logger.warning(f"Número {number} guardado parcialmente (Redis: {success_redis}, PostgreSQL: {success_pg})")
            return False
    
    def save_to_redis(self, number: int, timestamp: datetime) -> bool:
        """Guardar número en Redis"""
        if not self.redis_client:
            return False
        
        try:
            # Datos del número
            number_data = {
                'number': number,
                'timestamp': timestamp.isoformat(),
                'color': self.get_number_color(number),
                'parity': 'even' if number % 2 == 0 and number != 0 else 'odd',
                'range': 'high' if number > 18 else 'low',
                'dozen': self.get_dozen(number),
                'column': self.get_column(number)
            }
            
            # Guardar en Redis con múltiples estructuras para diferentes consultas
            
            # 1. Último número (clave simple)
            self.redis_client.set('roulette:last_number', json.dumps(number_data))
            
            # 2. Lista de números recientes (lista limitada)
            self.redis_client.lpush('roulette:recent_numbers', json.dumps(number_data))
            self.redis_client.ltrim('roulette:recent_numbers', 0, 999)  # Mantener últimos 1000
            
            # 3. Contador de números
            self.redis_client.incr('roulette:total_count')
            
            # 4. Estadísticas por color
            self.redis_client.hincrby('roulette:stats:color', number_data['color'], 1)
            
            # 5. Estadísticas por paridad
            self.redis_client.hincrby('roulette:stats:parity', number_data['parity'], 1)
            
            # 6. Estadísticas por rango
            self.redis_client.hincrby('roulette:stats:range', number_data['range'], 1)
            
            # 7. Frecuencia de números individuales
            self.redis_client.hincrby('roulette:frequency', str(number), 1)
            
            # 8. Timestamp de última actualización
            self.redis_client.set('roulette:last_update', timestamp.isoformat())
            
            # 9. Notificación de nuevo número (para el servicio de automatización)
            self.redis_client.publish('roulette:new_number', json.dumps(number_data))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando en Redis: {e}")
            return False
    
    def save_to_postgresql(self, number: int, timestamp: datetime) -> bool:
        """Guardar número en PostgreSQL"""
        if not self.pg_connection:
            return False
        
        try:
            with self.pg_connection.cursor() as cursor:
                # Insertar en tabla principal de números
                insert_query = """
                INSERT INTO roulette_numbers (number, timestamp, color, parity, range_type, dozen, column_num)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_query, (
                    number,
                    timestamp,
                    self.get_number_color(number),
                    'even' if number % 2 == 0 and number != 0 else 'odd',
                    'high' if number > 18 else 'low',
                    self.get_dozen(number),
                    self.get_column(number)
                ))
                
                # Actualizar estadísticas en tabla separada (opcional)
                self.update_statistics(cursor, number)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando en PostgreSQL: {e}")
            return False
    
    def update_statistics(self, cursor, number: int):
        """Actualizar estadísticas en PostgreSQL"""
        try:
            # Actualizar o insertar estadísticas del número
            upsert_query = """
            INSERT INTO number_statistics (number, frequency, last_seen)
            VALUES (%s, 1, NOW())
            ON CONFLICT (number) 
            DO UPDATE SET 
                frequency = number_statistics.frequency + 1,
                last_seen = NOW()
            """
            cursor.execute(upsert_query, (number,))
            
        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas: {e}")
    
    def get_number_color(self, number: int) -> str:
        """Obtener color del número"""
        if number == 0:
            return 'green'
        
        red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        return 'red' if number in red_numbers else 'black'
    
    def get_dozen(self, number: int) -> int:
        """Obtener docena del número (1, 2, 3)"""
        if number == 0:
            return 0
        elif 1 <= number <= 12:
            return 1
        elif 13 <= number <= 24:
            return 2
        else:
            return 3
    
    def get_column(self, number: int) -> int:
        """Obtener columna del número (1, 2, 3)"""
        if number == 0:
            return 0
        return ((number - 1) % 3) + 1
    
    def get_recent_numbers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener números recientes desde Redis"""
        if not self.redis_client:
            return []
        
        try:
            recent_data = self.redis_client.lrange('roulette:recent_numbers', 0, limit - 1)
            return [json.loads(data) for data in recent_data]
        except Exception as e:
            self.logger.error(f"Error obteniendo números recientes: {e}")
            return []
    
    def get_last_number(self) -> Optional[Dict[str, Any]]:
        """Obtener último número desde Redis"""
        if not self.redis_client:
            return None
        
        try:
            last_data = self.redis_client.get('roulette:last_number')
            return json.loads(last_data) if last_data else None
        except Exception as e:
            self.logger.error(f"Error obteniendo último número: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas desde Redis"""
        if not self.redis_client:
            return {}
        
        try:
            stats = {
                'total_count': int(self.redis_client.get('roulette:total_count') or 0),
                'last_update': self.redis_client.get('roulette:last_update'),
                'color_stats': self.redis_client.hgetall('roulette:stats:color'),
                'parity_stats': self.redis_client.hgetall('roulette:stats:parity'),
                'range_stats': self.redis_client.hgetall('roulette:stats:range'),
                'frequency': self.redis_client.hgetall('roulette:frequency')
            }
            
            # Convertir strings a integers donde sea necesario
            for key in ['color_stats', 'parity_stats', 'range_stats', 'frequency']:
                if stats[key]:
                    stats[key] = {k: int(v) for k, v in stats[key].items()}
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def clear_redis_data(self) -> bool:
        """Limpiar datos de Redis (para testing)"""
        if not self.redis_client:
            return False
        
        try:
            keys_to_delete = [
                'roulette:last_number',
                'roulette:recent_numbers',
                'roulette:total_count',
                'roulette:stats:color',
                'roulette:stats:parity',
                'roulette:stats:range',
                'roulette:frequency',
                'roulette:last_update'
            ]
            
            for key in keys_to_delete:
                self.redis_client.delete(key)
            
            self.logger.info("Datos de Redis limpiados")
            return True
            
        except Exception as e:
            self.logger.error(f"Error limpiando Redis: {e}")
            return False
    
    def test_connections(self) -> Dict[str, bool]:
        """Probar conexiones a ambas bases de datos"""
        redis_ok = False
        postgresql_ok = False
        
        # Probar Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
                redis_ok = True
            except:
                pass
        
        # Probar PostgreSQL
        if self.pg_connection:
            try:
                with self.pg_connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    postgresql_ok = True
            except:
                pass
        
        return {
            'redis': redis_ok,
            'postgresql': postgresql_ok
        }
    
    def close_connections(self):
        """Cerrar conexiones"""
        try:
            if self.redis_client:
                self.redis_client.close()
        except Exception as e:
            self.logger.error(f"Error cerrando Redis: {e}")
        
        try:
            if self.pg_connection:
                self.pg_connection.close()
        except Exception as e:
            self.logger.error(f"Error cerrando PostgreSQL: {e}")
        
        self.logger.info("Conexiones cerradas")

# Función de conveniencia para crear instancia
def create_synced_database() -> SyncedRouletteDatabase:
    """Crear instancia de base de datos sincronizada"""
    return SyncedRouletteDatabase()

# Para testing
if __name__ == "__main__":
    # Crear instancia
    db = create_synced_database()
    
    # Probar conexiones
    connections = db.test_connections()
    print(f"Estado de conexiones: {connections}")
    
    # Probar guardado de número
    if connections['redis'] or connections['postgresql']:
        test_number = 17
        success = db.save_number(test_number)
        print(f"Guardado de número {test_number}: {'Exitoso' if success else 'Falló'}")
        
        # Obtener último número
        last = db.get_last_number()
        print(f"Último número: {last}")
        
        # Obtener estadísticas
        stats = db.get_statistics()
        print(f"Estadísticas: {stats}")
    
    # Cerrar conexiones
    db.close_connections()