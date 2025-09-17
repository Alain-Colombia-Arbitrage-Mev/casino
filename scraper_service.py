#!/usr/bin/env python3
"""
Python Scraper Service - Solo maneja scraping y guarda en Redis
El resto lo maneja Go backend
"""

import time
import json
import redis
import random
from datetime import datetime
from typing import Dict, Any

class ScraperService:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            print("✅ Redis connected - Ready to send data to Go backend")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            self.redis_client = None

    def get_number_color(self, number: int) -> str:
        """Determina el color de un número de ruleta"""
        if number == 0:
            return "green"

        red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        return "red" if number in red_numbers else "black"

    def simulate_scraping(self) -> Dict[str, Any]:
        """Simula scraping de números de ruleta"""
        # Simular número random por ahora
        # TODO: Reemplazar con scraping real del casino
        number = random.randint(0, 36)
        color = self.get_number_color(number)
        timestamp = datetime.now().isoformat()

        return {
            "number": number,
            "color": color,
            "timestamp": timestamp,
            "source": "simulated_scraper"  # Cambiar a "live_casino" cuando sea real
        }

    def save_to_redis(self, data: Dict[str, Any]) -> bool:
        """Guarda datos en Redis para que Go backend los consuma"""
        if not self.redis_client:
            return False

        try:
            # Guardar en lista simple (compatibilidad)
            self.redis_client.lpush("roulette:history", data["number"])
            self.redis_client.ltrim("roulette:history", 0, 999)  # Keep last 1000

            # Guardar con metadata completa
            detailed_data = json.dumps(data)
            self.redis_client.lpush("roulette:history:detailed", detailed_data)
            self.redis_client.ltrim("roulette:history:detailed", 0, 999)

            # Guardar timestamp del último update
            self.redis_client.set("roulette:last_update", data["timestamp"])

            print(f"📊 Saved to Redis: {data['number']} ({data['color']}) at {data['timestamp']}")
            return True

        except Exception as e:
            print(f"❌ Error saving to Redis: {e}")
            return False

    def run_continuous_scraping(self, interval: int = 10):
        """Ejecuta scraping continuo"""
        print(f"🚀 Starting Python scraper service (interval: {interval}s)")
        print("📡 Data flow: Python Scraper → Redis → Go Backend → Frontend")

        while True:
            try:
                # Simular scraping
                data = self.simulate_scraping()

                # Guardar en Redis
                if self.save_to_redis(data):
                    print(f"✅ Number {data['number']} sent to Go backend via Redis")
                else:
                    print("❌ Failed to send data to Redis")

                # Esperar antes del siguiente scraping
                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n🛑 Stopping scraper service...")
                break
            except Exception as e:
                print(f"❌ Scraper error: {e}")
                time.sleep(5)  # Wait before retry

    def get_redis_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de Redis"""
        if not self.redis_client:
            return {"error": "Redis not connected"}

        try:
            history_count = self.redis_client.llen("roulette:history")
            detailed_count = self.redis_client.llen("roulette:history:detailed")
            last_update = self.redis_client.get("roulette:last_update")

            return {
                "history_count": history_count,
                "detailed_count": detailed_count,
                "last_update": last_update,
                "status": "connected"
            }
        except Exception as e:
            return {"error": str(e)}

def main():
    print("Python Scraper Service for AI Casino")
    print("Architecture: Python (scraping) + Go (API/ML) + Redis (data)")

    scraper = ScraperService()

    # Mostrar stats de Redis
    stats = scraper.get_redis_stats()
    print(f"📊 Redis Stats: {stats}")

    # Iniciar scraping continuo
    scraper.run_continuous_scraping(interval=8)  # Cada 8 segundos

if __name__ == "__main__":
    main()