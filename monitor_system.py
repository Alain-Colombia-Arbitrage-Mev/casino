#!/usr/bin/env python3
"""
Monitor del Sistema AI Casino - Validación y Sincronización
Verifica que Scraper → Backend → Frontend funcionen correctamente
"""

import time
import json
import requests
import redis
from datetime import datetime
from typing import Dict, Any

class AICasinoSystemMonitor:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.backend_url = "http://localhost:8080"
        self.frontend_url = "http://localhost:3000"

    def check_redis_connection(self) -> Dict[str, Any]:
        """Verificar conexión Redis"""
        try:
            self.redis_client.ping()
            return {"status": "online", "message": "Redis conectado correctamente"}
        except Exception as e:
            return {"status": "offline", "message": f"Error Redis: {e}"}

    def check_scraper_status(self) -> Dict[str, Any]:
        """Verificar estado del scraper"""
        try:
            # Verificar heartbeat del scraper
            heartbeat = self.redis_client.get("scraper:heartbeat")
            if not heartbeat:
                return {"status": "offline", "message": "No se encuentra heartbeat del scraper"}

            heartbeat_data = json.loads(heartbeat)
            last_update = heartbeat_data.get('last_update', 0)
            current_time = time.time()

            if current_time - last_update > 30:  # 30 segundos timeout
                return {
                    "status": "stale",
                    "message": f"Heartbeat obsoleto ({int(current_time - last_update)}s)",
                    "heartbeat": heartbeat_data
                }

            # Verificar datos recientes
            total_spins = self.redis_client.get("roulette:total_spins")
            current_number = self.redis_client.get("roulette:current_number")

            return {
                "status": "online",
                "message": "Scraper funcionando correctamente",
                "heartbeat": heartbeat_data,
                "total_spins": total_spins,
                "has_current_data": current_number is not None
            }

        except Exception as e:
            return {"status": "error", "message": f"Error verificando scraper: {e}"}

    def check_backend_status(self) -> Dict[str, Any]:
        """Verificar estado del backend"""
        try:
            # Test de ping básico
            response = requests.get(f"{self.backend_url}/ping", timeout=5)
            if response.status_code != 200:
                return {"status": "error", "message": f"Backend HTTP {response.status_code}"}

            # Verificar endpoint de estado del scraper
            scraper_status = requests.get(f"{self.backend_url}/api/system/scraper-status", timeout=5)
            if scraper_status.status_code == 200:
                scraper_data = scraper_status.json()
            else:
                scraper_data = {"error": "No se pudo obtener estado del scraper"}

            # Verificar datos de ruleta
            stats = requests.get(f"{self.backend_url}/api/roulette/stats", timeout=5)
            stats_data = stats.json() if stats.status_code == 200 else {}

            return {
                "status": "online",
                "message": "Backend funcionando correctamente",
                "ping": response.json(),
                "scraper_monitoring": scraper_data,
                "roulette_stats": stats_data
            }

        except Exception as e:
            return {"status": "offline", "message": f"Error conectando al backend: {e}"}

    def check_frontend_status(self) -> Dict[str, Any]:
        """Verificar estado del frontend"""
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                return {
                    "status": "online",
                    "message": "Frontend accesible",
                    "size": len(response.content)
                }
            else:
                return {"status": "error", "message": f"Frontend HTTP {response.status_code}"}

        except Exception as e:
            return {"status": "offline", "message": f"Error conectando al frontend: {e}"}

    def check_data_consistency(self) -> Dict[str, Any]:
        """Verificar consistencia de datos entre componentes"""
        try:
            # Datos en Redis
            redis_current = self.redis_client.get("roulette:current_number")
            redis_total = self.redis_client.get("roulette:total_spins")
            redis_history_length = self.redis_client.llen("roulette:history")

            # Datos del backend
            try:
                backend_stats = requests.get(f"{self.backend_url}/api/roulette/stats", timeout=5)
                backend_data = backend_stats.json() if backend_stats.status_code == 200 else {}
                backend_total = backend_data.get('total_numbers', 0)
            except:
                backend_data = {}
                backend_total = 0

            # Verificar consistencia
            consistency_issues = []

            if redis_total and str(redis_total) != str(backend_total):
                consistency_issues.append(f"Total spins: Redis={redis_total}, Backend={backend_total}")

            if not redis_current:
                consistency_issues.append("No hay número actual en Redis")

            if redis_history_length == 0:
                consistency_issues.append("Historial vacío en Redis")

            return {
                "consistent": len(consistency_issues) == 0,
                "issues": consistency_issues,
                "redis_data": {
                    "current_number": redis_current,
                    "total_spins": redis_total,
                    "history_length": redis_history_length
                },
                "backend_data": backend_data
            }

        except Exception as e:
            return {"consistent": False, "error": f"Error verificando consistencia: {e}"}

    def run_full_check(self) -> Dict[str, Any]:
        """Ejecutar verificación completa del sistema"""
        print("🔍 AI Casino - Monitor del Sistema")
        print("=" * 50)

        results = {
            "timestamp": datetime.now().isoformat(),
            "redis": self.check_redis_connection(),
            "scraper": self.check_scraper_status(),
            "backend": self.check_backend_status(),
            "frontend": self.check_frontend_status(),
            "data_consistency": self.check_data_consistency()
        }

        # Mostrar resultados
        for component, result in results.items():
            if component == "timestamp":
                continue

            status = result.get("status", "unknown")
            message = result.get("message", "No message")

            emoji = {
                "online": "✅",
                "offline": "❌",
                "error": "🔴",
                "stale": "⚠️",
                "unknown": "❓"
            }.get(status, "❓")

            print(f"{emoji} {component.upper()}: {status} - {message}")

        # Evaluación general del sistema
        all_online = all(
            results[comp].get("status") == "online"
            for comp in ["redis", "backend", "frontend"]
        )

        scraper_ok = results["scraper"].get("status") in ["online", "stale"]
        data_consistent = results["data_consistency"].get("consistent", False)

        if all_online and scraper_ok and data_consistent:
            overall_status = "🟢 SISTEMA FUNCIONANDO CORRECTAMENTE"
        elif all_online and scraper_ok:
            overall_status = "🟡 SISTEMA FUNCIONANDO CON PROBLEMAS MENORES"
        else:
            overall_status = "🔴 SISTEMA CON PROBLEMAS CRÍTICOS"

        print("\n" + "=" * 50)
        print(f"ESTADO GENERAL: {overall_status}")
        print("=" * 50)

        # Recomendaciones
        recommendations = self.get_recommendations(results)
        if recommendations:
            print("\n💡 RECOMENDACIONES:")
            for rec in recommendations:
                print(f"   • {rec}")

        return results

    def get_recommendations(self, results: Dict[str, Any]) -> list:
        """Obtener recomendaciones basadas en los resultados"""
        recommendations = []

        if results["redis"]["status"] != "online":
            recommendations.append("Verificar y reiniciar Redis")

        if results["scraper"]["status"] == "offline":
            recommendations.append("Reiniciar el scraper")
        elif results["scraper"]["status"] == "stale":
            recommendations.append("Verificar conectividad del scraper al sitio web")

        if results["backend"]["status"] != "online":
            recommendations.append("Verificar y reiniciar backend Go")

        if results["frontend"]["status"] != "online":
            recommendations.append("Verificar y reiniciar frontend Vue.js")

        if not results["data_consistency"]["consistent"]:
            recommendations.append("Sincronizar datos entre componentes")
            recommendations.append("Verificar integridad de datos en Redis")

        return recommendations

    def monitor_continuous(self, interval: int = 30):
        """Monitoreo continuo del sistema"""
        print(f"🔄 Iniciando monitoreo continuo (cada {interval}s)")
        print("Presiona Ctrl+C para detener")

        try:
            while True:
                self.run_full_check()
                print(f"\n⏰ Próxima verificación en {interval} segundos...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 Monitoreo detenido")

if __name__ == "__main__":
    monitor = AICasinoSystemMonitor()

    # Ejecutar verificación única
    monitor.run_full_check()

    # Opcional: Iniciar monitoreo continuo
    # monitor.monitor_continuous(30)