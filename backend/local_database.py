"""
Base de datos local para funcionar sin Redis ni PostgreSQL
Usa SQLite y archivos JSON como alternativa
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

class LocalDatabase:
    """Base de datos local usando SQLite y JSON"""
    
    def __init__(self, db_path: str = "data/aicasino.db", cache_path: str = "data/cache.json"):
        self.db_path = Path(db_path)
        self.cache_path = Path(cache_path)
        self.setup_logging()
        self.init_database()
        self.init_cache()
    
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        """Inicializar base de datos SQLite"""
        try:
            # Crear directorio si no existe
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Conectar y crear tablas
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla de números de ruleta
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS roulette_numbers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL,
                    color TEXT NOT NULL,
                    parity TEXT NOT NULL,
                    range_type TEXT NOT NULL,
                    dozen INTEGER NOT NULL,
                    column_num INTEGER NOT NULL
                )
                """)
                
                # Tabla de estadísticas
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS number_statistics (
                    number INTEGER PRIMARY KEY,
                    frequency INTEGER DEFAULT 1,
                    last_seen DATETIME NOT NULL
                )
                """)
                
                # Tabla de predicciones
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_type TEXT NOT NULL,
                    prediction_data TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    status TEXT DEFAULT 'pending'
                )
                """)
                
                # Índices para mejor rendimiento
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_numbers_timestamp ON roulette_numbers(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_numbers_number ON roulette_numbers(number)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp)")
                
                conn.commit()
                
            self.logger.info(f"Base de datos SQLite inicializada: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Error inicializando base de datos: {e}")
            raise
    
    def init_cache(self):
        """Inicializar cache JSON"""
        try:
            # Crear directorio si no existe
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Crear cache inicial si no existe
            if not self.cache_path.exists():
                initial_cache = {
                    "last_number": None,
                    "recent_numbers": [],
                    "stats": {
                        "total_count": 0,
                        "color_stats": {"red": 0, "black": 0, "green": 0},
                        "parity_stats": {"even": 0, "odd": 0},
                        "range_stats": {"low": 0, "high": 0},
                        "frequency": {}
                    },
                    "last_update": None
                }
                
                with open(self.cache_path, 'w') as f:
                    json.dump(initial_cache, f, indent=2)
            
            self.logger.info(f"Cache JSON inicializado: {self.cache_path}")
            
        except Exception as e:
            self.logger.error(f"Error inicializando cache: {e}")
            raise
    
    def save_number(self, number: int, timestamp: Optional[datetime] = None) -> bool:
        """Guardar número en base de datos y cache"""
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            # Guardar en SQLite
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                INSERT INTO roulette_numbers (number, timestamp, color, parity, range_type, dozen, column_num)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    number,
                    timestamp.isoformat(),
                    self.get_number_color(number),
                    'even' if number % 2 == 0 and number != 0 else 'odd',
                    'high' if number > 18 else 'low',
                    self.get_dozen(number),
                    self.get_column(number)
                ))
                
                # Actualizar estadísticas
                cursor.execute("""
                INSERT OR REPLACE INTO number_statistics (number, frequency, last_seen)
                VALUES (?, COALESCE((SELECT frequency FROM number_statistics WHERE number = ?) + 1, 1), ?)
                """, (number, number, timestamp.isoformat()))
                
                conn.commit()
            
            # Actualizar cache
            self.update_cache(number, timestamp)
            
            self.logger.info(f"Número {number} guardado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando número {number}: {e}")
            return False
    
    def update_cache(self, number: int, timestamp: datetime):
        """Actualizar cache JSON"""
        try:
            # Leer cache actual
            with open(self.cache_path, 'r') as f:
                cache = json.load(f)
            
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
            
            # Actualizar último número
            cache['last_number'] = number_data
            
            # Actualizar números recientes (mantener últimos 100)
            cache['recent_numbers'].insert(0, number_data)
            cache['recent_numbers'] = cache['recent_numbers'][:100]
            
            # Actualizar estadísticas
            cache['stats']['total_count'] += 1
            cache['stats']['color_stats'][number_data['color']] += 1
            cache['stats']['parity_stats'][number_data['parity']] += 1
            cache['stats']['range_stats'][number_data['range']] += 1
            
            # Frecuencia de números
            if str(number) not in cache['stats']['frequency']:
                cache['stats']['frequency'][str(number)] = 0
            cache['stats']['frequency'][str(number)] += 1
            
            # Timestamp de actualización
            cache['last_update'] = timestamp.isoformat()
            
            # Guardar cache actualizado
            with open(self.cache_path, 'w') as f:
                json.dump(cache, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error actualizando cache: {e}")
    
    def get_recent_numbers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener números recientes"""
        try:
            with open(self.cache_path, 'r') as f:
                cache = json.load(f)
            return cache['recent_numbers'][:limit]
        except Exception as e:
            self.logger.error(f"Error obteniendo números recientes: {e}")
            return []
    
    def get_last_number(self) -> Optional[Dict[str, Any]]:
        """Obtener último número"""
        try:
            with open(self.cache_path, 'r') as f:
                cache = json.load(f)
            return cache['last_number']
        except Exception as e:
            self.logger.error(f"Error obteniendo último número: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        try:
            with open(self.cache_path, 'r') as f:
                cache = json.load(f)
            return cache['stats']
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def save_prediction(self, prediction_type: str, prediction_data: Dict[str, Any], confidence: float) -> bool:
        """Guardar predicción"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                INSERT INTO predictions (prediction_type, prediction_data, confidence, timestamp)
                VALUES (?, ?, ?, ?)
                """, (
                    prediction_type,
                    json.dumps(prediction_data),
                    confidence,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
            
            self.logger.info(f"Predicción {prediction_type} guardada")
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando predicción: {e}")
            return False
    
    def get_predictions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener predicciones recientes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT * FROM predictions 
                ORDER BY timestamp DESC 
                LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                
                predictions = []
                for row in rows:
                    predictions.append({
                        'id': row[0],
                        'prediction_type': row[1],
                        'prediction_data': json.loads(row[2]),
                        'confidence': row[3],
                        'timestamp': row[4],
                        'status': row[5]
                    })
                
                return predictions
                
        except Exception as e:
            self.logger.error(f"Error obteniendo predicciones: {e}")
            return []
    
    def get_number_color(self, number: int) -> str:
        """Obtener color del número"""
        if number == 0:
            return 'green'
        
        red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        return 'red' if number in red_numbers else 'black'
    
    def get_dozen(self, number: int) -> int:
        """Obtener docena del número"""
        if number == 0:
            return 0
        elif 1 <= number <= 12:
            return 1
        elif 13 <= number <= 24:
            return 2
        else:
            return 3
    
    def get_column(self, number: int) -> int:
        """Obtener columna del número"""
        if number == 0:
            return 0
        return ((number - 1) % 3) + 1
    
    def test_connection(self) -> bool:
        """Probar conexión a la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            self.logger.error(f"Error probando conexión: {e}")
            return False
    
    def clear_data(self) -> bool:
        """Limpiar todos los datos (para testing)"""
        try:
            # Limpiar SQLite
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM roulette_numbers")
                cursor.execute("DELETE FROM number_statistics")
                cursor.execute("DELETE FROM predictions")
                conn.commit()
            
            # Reinicializar cache
            self.init_cache()
            
            self.logger.info("Datos limpiados exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error limpiando datos: {e}")
            return False

# Función de conveniencia
def create_local_database() -> LocalDatabase:
    """Crear instancia de base de datos local"""
    return LocalDatabase()

# Para testing
if __name__ == "__main__":
    # Crear instancia
    db = create_local_database()
    
    # Probar conexión
    if db.test_connection():
        print("✅ Base de datos local funcionando")
        
        # Probar guardado de número
        success = db.save_number(17)
        print(f"Guardado de número: {'✅' if success else '❌'}")
        
        # Obtener último número
        last = db.get_last_number()
        print(f"Último número: {last}")
        
        # Obtener estadísticas
        stats = db.get_statistics()
        print(f"Estadísticas: {stats}")
        
    else:
        print("❌ Error en base de datos local")