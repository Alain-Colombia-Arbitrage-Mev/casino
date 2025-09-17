#!/usr/bin/env python3
"""
🚀 AI CASINO - Sistema de Inicio Unificado
Inicia todo el sistema en la secuencia correcta
"""

import os
import sys
import time
import subprocess
import json
import redis
from datetime import datetime

class AICasinoStarter:
    def __init__(self):
        self.redis_client = None
        self.processes = {}

    def log_message(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        colors = {
            "INFO": "\033[32m",    # Green
            "WARNING": "\033[33m", # Yellow
            "ERROR": "\033[31m",   # Red
            "RESET": "\033[0m"     # Reset
        }
        color = colors.get(level, "")
        reset = colors["RESET"]
        print(f"{color}[{timestamp}] [{level}] {message}{reset}")

    def test_redis_connection(self, host='localhost', port=6379, max_retries=30):
        """Test Redis connection with retries"""
        for attempt in range(max_retries):
            try:
                self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
                self.redis_client.ping()
                self.log_message("✅ Redis connection successful")
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    self.log_message(f"⏳ Redis attempt {attempt + 1}/{max_retries} failed, retrying in 2s...")
                    time.sleep(2)
                else:
                    self.log_message(f"❌ Redis connection failed after {max_retries} attempts: {e}", "ERROR")
                    return False
        return False

    def check_docker(self):
        """Check if Docker is available"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.log_message("✅ Docker is available")
                return True
            else:
                self.log_message("❌ Docker not found", "ERROR")
                return False
        except FileNotFoundError:
            self.log_message("❌ Docker not installed", "ERROR")
            return False

    def start_redis_docker(self):
        """Start Redis with Docker"""
        try:
            self.log_message("🔄 Starting Redis with Docker...")

            # Check if Redis container already exists
            result = subprocess.run(
                ['docker', 'ps', '-a', '--format', '{{.Names}}'],
                capture_output=True, text=True
            )

            if 'redis-casino' in result.stdout:
                self.log_message("🔄 Removing existing Redis container...")
                subprocess.run(['docker', 'rm', '-f', 'redis-casino'], capture_output=True)

            # Start new Redis container
            cmd = [
                'docker', 'run', '-d',
                '--name', 'redis-casino',
                '-p', '6379:6379',
                'redis:alpine'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self.log_message("✅ Redis container started")
                return True
            else:
                self.log_message(f"❌ Failed to start Redis: {result.stderr}", "ERROR")
                return False

        except Exception as e:
            self.log_message(f"❌ Error starting Redis: {e}", "ERROR")
            return False

    def start_backend(self):
        """Start Go backend"""
        try:
            self.log_message("🔄 Starting Go backend...")

            # Change to backend directory
            backend_dir = os.path.join(os.getcwd(), 'backend')
            if not os.path.exists(backend_dir):
                self.log_message("❌ Backend directory not found", "ERROR")
                return False

            # Start Go backend
            cmd = ['go', 'run', 'main_optimized.go', 'adaptive_ml.go']

            process = subprocess.Popen(
                cmd,
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.processes['backend'] = process
            self.log_message("✅ Go backend starting...")

            # Wait a bit for startup
            time.sleep(3)

            if process.poll() is None:
                self.log_message("✅ Go backend is running")
                return True
            else:
                stdout, stderr = process.communicate()
                self.log_message(f"❌ Backend failed to start: {stderr}", "ERROR")
                return False

        except Exception as e:
            self.log_message(f"❌ Error starting backend: {e}", "ERROR")
            return False

    def test_backend_api(self):
        """Test if backend API is responding"""
        try:
            import requests

            for attempt in range(10):
                try:
                    response = requests.get('http://localhost:5002/ping', timeout=5)
                    if response.status_code == 200:
                        self.log_message("✅ Backend API is responding")
                        return True
                except:
                    pass

                self.log_message(f"⏳ Backend API check {attempt + 1}/10, retrying...")
                time.sleep(2)

            self.log_message("❌ Backend API not responding", "ERROR")
            return False

        except ImportError:
            self.log_message("⚠️ Requests library not available, skipping API test", "WARNING")
            return True

    def start_scraper(self):
        """Start Redis scraper (simulation mode)"""
        try:
            self.log_message("🔄 Starting scraper in simulation mode...")

            # Start scraper simulation
            cmd = ['python', 'test_optimized_system.py']

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.processes['scraper'] = process
            self.log_message("✅ Scraper simulation started")
            return True

        except Exception as e:
            self.log_message(f"❌ Error starting scraper: {e}", "ERROR")
            return False

    def start_frontend(self):
        """Start frontend"""
        try:
            self.log_message("🔄 Starting frontend...")

            # Change to frontend directory
            frontend_dir = os.path.join(os.getcwd(), 'frontend')
            if not os.path.exists(frontend_dir):
                self.log_message("❌ Frontend directory not found", "ERROR")
                return False

            # Start frontend
            cmd = ['npm', 'run', 'dev']

            process = subprocess.Popen(
                cmd,
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.processes['frontend'] = process
            self.log_message("✅ Frontend starting...")

            # Wait a bit for startup
            time.sleep(5)

            if process.poll() is None:
                self.log_message("✅ Frontend is running")
                return True
            else:
                stdout, stderr = process.communicate()
                self.log_message(f"❌ Frontend failed to start: {stderr}", "ERROR")
                return False

        except Exception as e:
            self.log_message(f"❌ Error starting frontend: {e}", "ERROR")
            return False

    def show_system_status(self):
        """Show system status and URLs"""
        self.log_message("📊 System Status:")
        self.log_message("=" * 50)
        self.log_message("🔗 URLs:")
        self.log_message("   Frontend: http://localhost:3000")
        self.log_message("   Backend API: http://localhost:5002")
        self.log_message("   API Ping: http://localhost:5002/ping")
        self.log_message("   API Stats: http://localhost:5002/api/roulette/stats")
        self.log_message("=" * 50)
        self.log_message("🎮 System is ready for AI Casino action!")

    def cleanup_processes(self):
        """Cleanup all started processes"""
        self.log_message("🧹 Cleaning up processes...")

        for name, process in self.processes.items():
            if process and process.poll() is None:
                self.log_message(f"🔄 Terminating {name}...")
                process.terminate()
                time.sleep(2)
                if process.poll() is None:
                    process.kill()

    def run(self, use_docker=True):
        """Run the complete startup sequence"""
        try:
            self.log_message("🚀 AI CASINO - Sistema de Inicio Unificado")
            self.log_message("=" * 50)

            # Step 1: Start Redis
            if use_docker:
                if not self.check_docker():
                    self.log_message("❌ Docker required but not available", "ERROR")
                    return False

                if not self.start_redis_docker():
                    return False

            # Step 2: Test Redis connection
            if not self.test_redis_connection():
                return False

            # Step 3: Start Backend
            if not self.start_backend():
                return False

            # Step 4: Test Backend API
            if not self.test_backend_api():
                return False

            # Step 5: Start Scraper (simulation)
            if not self.start_scraper():
                return False

            # Step 6: Start Frontend
            if not self.start_frontend():
                return False

            # Show final status
            self.show_system_status()

            # Keep running
            self.log_message("✅ Sistema iniciado correctamente!")
            self.log_message("💡 Presiona Ctrl+C para detener el sistema")

            try:
                while True:
                    time.sleep(10)
                    # Check if processes are still running
                    dead_processes = []
                    for name, process in self.processes.items():
                        if process.poll() is not None:
                            dead_processes.append(name)

                    if dead_processes:
                        self.log_message(f"⚠️ Process died: {', '.join(dead_processes)}", "WARNING")
                        break

            except KeyboardInterrupt:
                self.log_message("🛑 Sistema detenido por usuario")
                return True

        except Exception as e:
            self.log_message(f"❌ Error general: {e}", "ERROR")
            return False

        finally:
            self.cleanup_processes()

def main():
    import argparse

    parser = argparse.ArgumentParser(description='AI Casino System Starter')
    parser.add_argument('--no-docker', action='store_true',
                       help='Don\'t use Docker for Redis (assumes Redis is already running)')

    args = parser.parse_args()

    starter = AICasinoStarter()
    success = starter.run(use_docker=not args.no_docker)

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())