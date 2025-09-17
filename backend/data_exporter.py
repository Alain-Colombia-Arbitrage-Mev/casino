#!/usr/bin/env python3
"""
Data Exporter para AI Casino
Sistema para exportar datos a archivos JSON temporales
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataExporter:
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = export_dir
        self.ensure_export_directory()
    
    def ensure_export_directory(self):
        """Crear directorio de exportación si no existe"""
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
            logger.info(f"Directorio de exportación creado: {self.export_dir}")
    
    def export_roulette_history(self, numbers: List[Dict]) -> str:
        """Exportar historial de números a JSON"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"roulette_history_{timestamp}.json"
            filepath = os.path.join(self.export_dir, filename)
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_numbers": len(numbers),
                "numbers": numbers,
                "metadata": {
                    "export_type": "roulette_history",
                    "version": "1.0"
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Historial exportado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando historial: {e}")
            return ""
    
    def export_statistics(self, stats: Dict) -> str:
        """Exportar estadísticas a JSON"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"roulette_stats_{timestamp}.json"
            filepath = os.path.join(self.export_dir, filename)
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "statistics": stats,
                "metadata": {
                    "export_type": "roulette_statistics",
                    "version": "1.0"
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Estadísticas exportadas: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando estadísticas: {e}")
            return ""
    
    def export_predictions(self, predictions: List[Dict]) -> str:
        """Exportar predicciones a JSON"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ai_predictions_{timestamp}.json"
            filepath = os.path.join(self.export_dir, filename)
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_predictions": len(predictions),
                "predictions": predictions,
                "metadata": {
                    "export_type": "ai_predictions",
                    "version": "1.0"
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Predicciones exportadas: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando predicciones: {e}")
            return ""
    
    def export_game_results(self, results: List[Dict]) -> str:
        """Exportar resultados de juegos a JSON"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"game_results_{timestamp}.json"
            filepath = os.path.join(self.export_dir, filename)
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_results": len(results),
                "results": results,
                "metadata": {
                    "export_type": "game_results",
                    "version": "1.0"
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Resultados exportados: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando resultados: {e}")
            return ""
    
    def export_detailed_analysis(self, analysis_data: Dict) -> str:
        """Exportar análisis detallado a JSON"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"detailed_analysis_{timestamp}.json"
            filepath = os.path.join(self.export_dir, filename)
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "analysis": analysis_data,
                "metadata": {
                    "export_type": "detailed_analysis",
                    "version": "1.0"
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Análisis detallado exportado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exportando análisis: {e}")
            return ""
    
    def get_latest_export(self, export_type: str) -> str:
        """Obtener la exportación más reciente de un tipo"""
        try:
            files = [f for f in os.listdir(self.export_dir) if f.startswith(export_type)]
            if files:
                latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(self.export_dir, x)))
                return os.path.join(self.export_dir, latest_file)
            return ""
        except Exception as e:
            logger.error(f"Error obteniendo última exportación: {e}")
            return ""
    
    def cleanup_old_exports(self, keep_count: int = 10):
        """Limpiar exportaciones antiguas, manteniendo solo las más recientes"""
        try:
            files = [f for f in os.listdir(self.export_dir) if f.endswith('.json')]
            if len(files) > keep_count:
                # Ordenar por fecha de creación
                files_with_time = [(f, os.path.getctime(os.path.join(self.export_dir, f))) for f in files]
                files_with_time.sort(key=lambda x: x[1], reverse=True)
                
                # Eliminar archivos antiguos
                for filename, _ in files_with_time[keep_count:]:
                    filepath = os.path.join(self.export_dir, filename)
                    os.remove(filepath)
                    logger.info(f"Archivo antiguo eliminado: {filename}")
                    
        except Exception as e:
            logger.error(f"Error limpiando exportaciones: {e}")

# Instancia global del exportador
data_exporter = DataExporter()