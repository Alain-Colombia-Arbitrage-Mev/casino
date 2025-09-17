#!/usr/bin/env python3
"""
Sistema de logging centralizado para el sistema de ruleta
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from config import config

class ColoredFormatter(logging.Formatter):
    """Formatter con colores para la consola"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Verde
        'WARNING': '\033[33m',  # Amarillo
        'ERROR': '\033[31m',    # Rojo
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Formato: [TIMESTAMP] [LEVEL] [MODULE] MESSAGE
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        return super().format(record)

class RouletteLogger:
    """Logger centralizado para el sistema de ruleta"""
    
    def __init__(self, name="roulette_system"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
        
        # Evitar duplicar handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura los handlers de logging"""
        
        # Handler para consola con colores
        console_handler = logging.StreamHandler()
        console_formatter = ColoredFormatter(
            fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Handler para archivo con rotación
        if config.LOG_FILE:
            # Crear directorio de logs si no existe
            log_dir = os.path.dirname(config.LOG_FILE) or 'logs'
            os.makedirs(log_dir, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                config.LOG_FILE,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_formatter = logging.Formatter(
                fmt='[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message, **kwargs):
        """Log debug message"""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message, **kwargs):
        """Log info message"""
        self.logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message, **kwargs):
        """Log warning message"""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message, **kwargs):
        """Log error message"""
        self.logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message, **kwargs):
        """Log critical message"""
        self.logger.critical(self._format_message(message, **kwargs))
    
    def _format_message(self, message, **kwargs):
        """Formatea el mensaje con contexto adicional"""
        if kwargs:
            context_parts = [f"{k}={v}" for k, v in kwargs.items()]
            context = " | ".join(context_parts)
            return f"{message} | {context}"
        return message
    
    def log_prediction(self, prediction_id, prediction_type, numbers, confidence):
        """Log específico para predicciones"""
        self.info(
            f"🎯 Nueva predicción generada",
            prediction_id=prediction_id,
            type=prediction_type,
            numbers=numbers,
            confidence=f"{confidence:.2f}"
        )
    
    def log_prediction_result(self, prediction_id, actual_number, is_winner, groups_won=None):
        """Log específico para resultados de predicciones"""
        result_emoji = "✅" if is_winner else "❌"
        self.info(
            f"{result_emoji} Resultado de predicción",
            prediction_id=prediction_id,
            actual_number=actual_number,
            result="WIN" if is_winner else "LOSE",
            groups_won=groups_won
        )
    
    def log_scraping_activity(self, numbers_found, source="unknown"):
        """Log específico para actividad de scraping"""
        if numbers_found:
            self.info(
                f"🔍 Números extraídos del scraping",
                count=len(numbers_found),
                numbers=numbers_found,
                source=source
            )
        else:
            self.warning(f"⚠️ No se encontraron números en scraping", source=source)
    
    def log_database_operation(self, operation, success, details=None):
        """Log específico para operaciones de base de datos"""
        emoji = "✅" if success else "❌"
        level = "info" if success else "error"
        
        getattr(self, level)(
            f"{emoji} Operación de base de datos: {operation}",
            success=success,
            details=details or "N/A"
        )
    
    def log_system_status(self, component, status, details=None):
        """Log específico para estado del sistema"""
        status_emojis = {
            "starting": "🚀",
            "running": "✅",
            "stopping": "🛑",
            "error": "❌",
            "warning": "⚠️"
        }
        
        emoji = status_emojis.get(status, "ℹ️")
        self.info(
            f"{emoji} {component}: {status}",
            details=details or "N/A"
        )

# Instancia global del logger
logger = RouletteLogger()

# Funciones de conveniencia
def log_info(message, **kwargs):
    logger.info(message, **kwargs)

def log_error(message, **kwargs):
    logger.error(message, **kwargs)

def log_warning(message, **kwargs):
    logger.warning(message, **kwargs)

def log_debug(message, **kwargs):
    logger.debug(message, **kwargs)

def log_prediction(prediction_id, prediction_type, numbers, confidence):
    logger.log_prediction(prediction_id, prediction_type, numbers, confidence)

def log_prediction_result(prediction_id, actual_number, is_winner, groups_won=None):
    logger.log_prediction_result(prediction_id, actual_number, is_winner, groups_won)

def log_scraping_activity(numbers_found, source="unknown"):
    logger.log_scraping_activity(numbers_found, source)

def log_database_operation(operation, success, details=None):
    logger.log_database_operation(operation, success, details)

def log_system_status(component, status, details=None):
    logger.log_system_status(component, status, details)