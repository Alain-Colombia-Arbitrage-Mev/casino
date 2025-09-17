#!/usr/bin/env python3
"""
Configuración centralizada para el sistema de ruleta
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración principal del sistema"""
    
    # Base de datos
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/roulette_db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Scraping
    LOGIN_URL = os.getenv("LOGIN_URL", "https://bcgame.com/login")
    DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://bcgame.com/game/lightning-roulette")
    ROULETTE_USERNAME = os.getenv("ROULETTE_USERNAME", "")
    ROULETTE_PASSWORD = os.getenv("ROULETTE_PASSWORD", "")
    REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "30"))
    
    # IA y Predicciones
    MIN_HISTORY_FOR_PREDICTION = int(os.getenv("MIN_HISTORY_FOR_PREDICTION", "10"))
    PREDICTION_CONFIDENCE_THRESHOLD = float(os.getenv("PREDICTION_CONFIDENCE_THRESHOLD", "0.6"))
    MAX_PREDICTIONS_STORED = int(os.getenv("MAX_PREDICTIONS_STORED", "100"))
    
    # Sectores de la ruleta
    VOISINS_ZERO = [22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25]
    TIERS = [27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33]
    ORPHELINS = [17, 34, 6, 1, 20, 14, 31, 9]
    
    # Números por color
    RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
    
    # Rueda europea
    EUROPEAN_WHEEL = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "roulette_system.log")
    
    # Servicio automático
    AUTO_SERVICE_ENABLED = os.getenv("AUTO_SERVICE_ENABLED", "true").lower() == "true"
    AUTO_SERVICE_INTERVAL = int(os.getenv("AUTO_SERVICE_INTERVAL", "10"))
    
    # Protección del cero
    ZERO_PROTECTION_ENABLED = os.getenv("ZERO_PROTECTION_ENABLED", "true").lower() == "true"
    ZERO_PROTECTION_THRESHOLD = int(os.getenv("ZERO_PROTECTION_THRESHOLD", "15"))
    
    @classmethod
    def validate_config(cls):
        """Valida la configuración y muestra advertencias"""
        warnings = []
        
        if not cls.ROULETTE_USERNAME or cls.ROULETTE_USERNAME == "tu_usuario":
            warnings.append("⚠️ ROULETTE_USERNAME no configurado")
        
        if not cls.ROULETTE_PASSWORD or cls.ROULETTE_PASSWORD == "tu_password":
            warnings.append("⚠️ ROULETTE_PASSWORD no configurado")
        
        if cls.DATABASE_URL == "postgresql://user:password@localhost:5432/roulette_db":
            warnings.append("⚠️ DATABASE_URL usando valores por defecto")
        
        if cls.REDIS_URL == "redis://localhost:6379":
            warnings.append("⚠️ REDIS_URL usando valores por defecto")
        
        return warnings
    
    @classmethod
    def get_number_color(cls, number):
        """Obtiene el color de un número"""
        if number == 0:
            return "green"
        elif number in cls.RED_NUMBERS:
            return "red"
        elif number in cls.BLACK_NUMBERS:
            return "black"
        else:
            return "unknown"
    
    @classmethod
    def get_number_sector(cls, number):
        """Obtiene el sector de un número"""
        if number in cls.VOISINS_ZERO:
            return "voisins_zero"
        elif number in cls.TIERS:
            return "tiers"
        elif number in cls.ORPHELINS:
            return "orphelins"
        else:
            return "unknown"
    
    @classmethod
    def get_wheel_neighbors(cls, number, distance=2):
        """Obtiene vecinos de un número en la rueda"""
        try:
            idx = cls.EUROPEAN_WHEEL.index(number)
            neighbors = []
            
            for i in range(-distance, distance + 1):
                neighbor_idx = (idx + i) % len(cls.EUROPEAN_WHEEL)
                neighbors.append(cls.EUROPEAN_WHEEL[neighbor_idx])
            
            return neighbors
        except ValueError:
            return [number]  # Si el número no está en la rueda, devolver solo él mismo

# Instancia global de configuración
config = Config()