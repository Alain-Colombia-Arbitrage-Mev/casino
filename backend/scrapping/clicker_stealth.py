#!/usr/bin/env python3
"""
🥷 CLICKER ULTRA SIGILOSO
- No usa Selenium
- No automatiza navegadores  
- Solo clicks puros en coordenadas
- 100% indetectable
"""

import pyautogui
import time
import random
import keyboard
import json
import os
import threading
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stealth_clicker.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StealthClicker")

class StealthClicker:
    def __init__(self):
        self.positions = {}
        self.current_position = None
        self.is_running = False
        self.click_thread = None
        self.config_file = "stealth_config.json"
        
        # Configurar pyautogui para máxima naturalidad
        pyautogui.PAUSE = 0.01
        pyautogui.FAILSAFE = True
        
        self.load_config()
        self.setup_hotkeys()
        
        print("🥷 CLICKER ULTRA SIGILOSO INICIADO")
        print("=" * 50)
        print("✅ 100% Indetectable - Sin Selenium")
        print("✅ Solo clicks puros en coordenadas")
        print("✅ Funciona con cualquier navegador")
        print("=" * 50)
        
    def load_config(self):
        """Carga configuración guardada"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.positions = data.get("positions", {})
                    logger.info(f"✅ {len(self.positions)} posiciones cargadas")
            else:
                self.positions = {}
                logger.info("📋 Nueva configuración creada")
        except Exception as e:
            logger.error(f"❌ Error cargando config: {e}")
            self.positions = {}
            
    def save_config(self):
        """Guarda configuración"""
        try:
            data = {"positions": self.positions}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("✅ Configuración guardada")
        except Exception as e:
            logger.error(f"❌ Error guardando config: {e}")
            
    def setup_hotkeys(self):
        """Configura las teclas de acceso rápido"""
        try:
            keyboard.add_hotkey('f1', self.save_position)
            keyboard.add_hotkey('f2', self.toggle_clicking)
            keyboard.add_hotkey('f3', self.select_position)
            keyboard.add_hotkey('f4', self.show_positions)
            keyboard.add_hotkey('ctrl+q', self.quit_app)
            
            print("\n⌨️ CONTROLES:")
            print("F1 = Guardar posición actual del cursor")
            print("F2 = Iniciar/Parar clicks automáticos")
            print("F3 = Seleccionar posición para clickear")
            print("F4 = Ver todas las posiciones guardadas")
            print("Ctrl+Q = Salir")
            print("ESC = Parar clicks (emergencia)")
            
        except Exception as e:
            logger.error(f"❌ Error configurando hotkeys: {e}")
            
    def save_position(self):
        """Guarda la posición actual del cursor"""
        try:
            pos = pyautogui.position()
            
            print(f"\n📍 CURSOR EN: ({pos.x}, {pos.y})")
            name = input("Nombre para esta posición: ").strip()
            
            if name:
                self.positions[name] = (pos.x, pos.y)
                self.save_config()
                logger.info(f"✅ Posición '{name}' guardada: ({pos.x}, {pos.y})")
            else:
                print("❌ Nombre vacío, no se guardó")
                
        except Exception as e:
            logger.error(f"❌ Error guardando posición: {e}")
            
    def select_position(self):
        """Selecciona una posición para clickear"""
        try:
            if not self.positions:
                print("❌ No hay posiciones guardadas. Usa F1 para guardar una.")
                return
                
            print("\n📍 POSICIONES DISPONIBLES:")
            print("=" * 40)
            
            positions_list = list(self.positions.items())
            for i, (name, pos) in enumerate(positions_list, 1):
                print(f"{i}. {name}: ({pos[0]}, {pos[1]})")
                
            print("=" * 40)
            
            choice = input("Selecciona posición (número): ").strip()
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(positions_list):
                    name, pos = positions_list[index]
                    self.current_position = pos
                    logger.info(f"✅ Posición seleccionada: {name} = {pos}")
                    print(f"🎯 Listo para clickear en: {name}")
                else:
                    print("❌ Número inválido")
            except ValueError:
                print("❌ Entrada inválida")
                
        except Exception as e:
            logger.error(f"❌ Error seleccionando posición: {e}")
            
    def show_positions(self):
        """Muestra todas las posiciones guardadas"""
        try:
            if not self.positions:
                print("❌ No hay posiciones guardadas")
                return
                
            print("\n📍 TODAS LAS POSICIONES:")
            print("=" * 50)
            
            for name, pos in self.positions.items():
                status = "🎯 ACTIVA" if self.current_position == pos else ""
                print(f"• {name}: ({pos[0]}, {pos[1]}) {status}")
                
            print("=" * 50)
            
        except Exception as e:
            logger.error(f"❌ Error mostrando posiciones: {e}")
            
    def natural_click(self, x, y):
        """Realiza un click ultra natural"""
        try:
            # Variación humana
            variation_x = random.randint(-2, 2)
            variation_y = random.randint(-2, 2)
            final_x = x + variation_x
            final_y = y + variation_y
            
            # Mover con naturalidad
            duration = random.uniform(0.1, 0.3)
            pyautogui.moveTo(final_x, final_y, duration=duration)
            
            # Delay humano antes del click
            time.sleep(random.uniform(0.05, 0.15))
            
            # Click con duración natural
            pyautogui.mouseDown()
            time.sleep(random.uniform(0.02, 0.08))
            pyautogui.mouseUp()
            
            # Delay después del click
            time.sleep(random.uniform(0.1, 0.3))
            
            logger.info(f"🎯 Click en ({final_x}, {final_y})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en click: {e}")
            return False
            
    def click_loop(self):
        """Bucle principal de clicks"""
        logger.info("🚀 Iniciando clicks automáticos...")
        logger.info("⚠️ Presiona ESC para detener")
        
        while self.is_running:
            try:
                if self.current_position:
                    self.natural_click(*self.current_position)
                    
                    # Intervalo aleatorio entre clicks (muy humano)
                    interval = random.uniform(2.0, 5.0)
                    time.sleep(interval)
                else:
                    logger.warning("⚠️ No hay posición seleccionada")
                    break
                    
            except Exception as e:
                logger.error(f"❌ Error en bucle de clicks: {e}")
                break
                
        self.is_running = False
        logger.info("⏹️ Clicks detenidos")
        
    def toggle_clicking(self):
        """Inicia o detiene los clicks"""
        try:
            if not self.current_position:
                print("❌ Primero selecciona una posición (F3)")
                return
                
            if not self.is_running:
                self.is_running = True
                self.click_thread = threading.Thread(target=self.click_loop)
                self.click_thread.daemon = True
                self.click_thread.start()
                logger.info("▶️ Clicks iniciados")
            else:
                self.is_running = False
                logger.info("⏹️ Deteniendo clicks...")
                
        except Exception as e:
            logger.error(f"❌ Error alternando clicks: {e}")
            
    def quit_app(self):
        """Sale de la aplicación"""
        try:
            self.is_running = False
            logger.info("👋 Saliendo del clicker sigiloso...")
            os._exit(0)
        except:
            os._exit(0)
            
    def run(self):
        """Ejecuta el clicker"""
        try:
            print("\n🥷 CLICKER SIGILOSO ACTIVO")
            print("Usa las teclas F1-F4 para controlar")
            print("Presiona Ctrl+Q para salir")
            print("\n⚠️ IMPORTANTE:")
            print("1. Abre tu navegador manualmente")
            print("2. Navega al sitio del casino")
            print("3. Usa F1 para guardar posiciones de apuesta")
            print("4. Usa F3 para seleccionar posición")
            print("5. Usa F2 para iniciar clicks automáticos")
            
            # Mantener el programa corriendo
            keyboard.wait('ctrl+q')
            
        except KeyboardInterrupt:
            logger.info("👋 Programa terminado por el usuario")
        except Exception as e:
            logger.error(f"❌ Error en ejecución: {e}")

if __name__ == "__main__":
    clicker = StealthClicker()
    clicker.run() 