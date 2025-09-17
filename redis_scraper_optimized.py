#!/usr/bin/env python3
"""
Scraper Optimizado SOLO REDIS - Ultra Rápido para Predicciones ML
Elimina PostgreSQL, solo Redis con datos ricos para ML
"""

import time
import json
import os
import redis
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager  # Comentado para usar ChromeDriver manual
from dotenv import load_dotenv

load_dotenv()

def log_message(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        print(f"[{timestamp}] [{level}] {message}")
    except UnicodeEncodeError:
        safe_message = message.encode('ascii', 'ignore').decode('ascii')
        print(f"[{timestamp}] [{level}] {safe_message}")

def get_number_color(number):
    """Determinar color del número"""
    if number == 0:
        return "green"
    red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    return "red" if number in red_numbers else "black"

def get_number_properties(number):
    """Obtener todas las propiedades del número para ML"""
    color = get_number_color(number)

    # Docenas (1-12, 13-24, 25-36)
    if number == 0:
        dozen = 0
    elif 1 <= number <= 12:
        dozen = 1
    elif 13 <= number <= 24:
        dozen = 2
    else:
        dozen = 3

    # Columnas (1,4,7,10... = Col1, 2,5,8,11... = Col2, 3,6,9,12... = Col3)
    if number == 0:
        column = 0
    else:
        column = ((number - 1) % 3) + 1

    # Par/Impar
    parity = "even" if number > 0 and number % 2 == 0 else "odd" if number > 0 else "zero"

    # Alto/Bajo (1-18 / 19-36)
    high_low = "low" if 1 <= number <= 18 else "high" if number >= 19 else "zero"

    return {
        "number": number,
        "color": color,
        "dozen": dozen,
        "column": column,
        "parity": parity,
        "high_low": high_low,
        "timestamp": datetime.now().isoformat()
    }

class OptimizedRedisRouletteManager:
    """Gestor optimizado SOLO REDIS con datos ricos para ML"""

    def __init__(self):
        self.redis_client = None
        self.connect_redis()

    def connect_redis(self):
        """Conectar solo a Redis"""
        try:
            # Usar variables de entorno para Redis
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            redis_db = int(os.getenv('REDIS_DB', '0'))

            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            self.redis_client.ping()
            log_message("✅ Redis conectado - Modo ULTRA RAPIDO")
        except Exception as e:
            log_message(f"❌ Error Redis: {e}", "ERROR")
            self.redis_client = None

    def validate_number(self, number):
        """Validar número 0-36"""
        try:
            num = int(number)
            return 0 <= num <= 36
        except (ValueError, TypeError):
            return False

    def save_roulette_number(self, number):
        """Guardar número con estructura Redis avanzada para análisis ML"""
        if not self.redis_client or not self.validate_number(number):
            return False

        number = int(number)
        props = get_number_properties(number)
        now = datetime.now()
        timestamp = now.isoformat()
        unix_timestamp = int(now.timestamp())

        try:
            # === OPERACIONES ATÓMICAS SEPARADAS ===
            # 1. Obtener datos necesarios ANTES del pipeline
            current_total_spins = self.redis_client.get("roulette:total_spins") or "0"
            session_start = self.redis_client.get("roulette:session_start") or timestamp
            last_10_numbers = self.redis_client.lrange("roulette:history", 0, 9)

            # 2. Calcular análisis avanzado
            analysis_data = self._generate_advanced_analysis(number, props, last_10_numbers, unix_timestamp)

            # 3. Pipeline optimizado sin .get() dentro
            pipe = self.redis_client.pipeline()

            # === DATOS BÁSICOS MEJORADOS ===
            pipe.set("roulette:current_number", json.dumps({
                "number": number,
                "color": props['color'],
                "timestamp": timestamp,
                "unix_timestamp": unix_timestamp,
                "spin_id": int(current_total_spins) + 1
            }))

            # === HISTORIALES OPTIMIZADOS ===
            detailed_entry = json.dumps({
                **props,
                "spin_id": int(current_total_spins) + 1,
                "unix_timestamp": unix_timestamp,
                "analysis": analysis_data
            })
            pipe.lpush("roulette:history_detailed", detailed_entry)
            pipe.ltrim("roulette:history_detailed", 0, 1999)  # Mantener 2000 spins

            pipe.lpush("roulette:history", number)
            pipe.ltrim("roulette:history", 0, 999)  # Últimos 1000 números

            # === CONTADORES Y ESTADÍSTICAS ===
            pipe.incr("roulette:total_spins")
            pipe.incr(f"roulette:freq:number:{number}")
            pipe.incr(f"roulette:freq:color:{props['color']}")
            pipe.incr(f"roulette:freq:dozen:{props['dozen']}")
            pipe.incr(f"roulette:freq:column:{props['column']}")
            pipe.incr(f"roulette:freq:parity:{props['parity']}")
            pipe.incr(f"roulette:freq:range:{props['high_low']}")

            # === ANÁLISIS TEMPORAL AVANZADO ===
            pipe.incr(f"roulette:time:hour:{now.hour}")
            pipe.incr(f"roulette:time:minute:{now.minute}")
            pipe.incr(f"roulette:time:day_of_week:{now.weekday()}")

            # === PATRONES Y SECUENCIAS ===
            for pattern_name, pattern_value in analysis_data['patterns'].items():
                if pattern_value:
                    pipe.incr(f"roulette:patterns:{pattern_name}")

            # === GAPS Y CICLOS ===
            if analysis_data['gap'] is not None:
                pipe.set(f"roulette:gap:{number}", analysis_data['gap'])
                pipe.lpush(f"roulette:gap_history:{number}", analysis_data['gap'])
                pipe.ltrim(f"roulette:gap_history:{number}", 0, 99)

            # === SECTORES Y POSICIONES ===
            sector = self.get_roulette_sector(number)
            pipe.incr(f"roulette:sectors:sector_{sector}")
            pipe.set(f"roulette:last_position:{number}", int(current_total_spins) + 1)

            # === MÉTRICAS AVANZADAS ===
            pipe.hset("roulette:metrics", mapping={
                "latest_number": str(number),
                "latest_color": props['color'],
                "latest_timestamp": timestamp,
                "total_spins": str(int(current_total_spins) + 1),
                "session_start": session_start,
                "hot_numbers": json.dumps(analysis_data['hot_numbers']),
                "cold_numbers": json.dumps(analysis_data['cold_numbers']),
                "streak_info": json.dumps(analysis_data['streak_info'])
            })

            # === DATOS PARA ML ===
            pipe.lpush("roulette:ml_features", json.dumps({
                "number": number,
                "features": analysis_data['ml_features'],
                "timestamp": unix_timestamp
            }))
            pipe.ltrim("roulette:ml_features", 0, 4999)  # Últimas 5000 características

            # === SEÑAL DE NUEVO DATO ===
            pipe.set("roulette:new_data_flag", json.dumps({
                "number": number,
                "timestamp": unix_timestamp,
                "trigger_prediction": True
            }), ex=300)  # Expira en 5 minutos

            # EJECUTAR PIPELINE ATÓMICO
            pipe.execute()

            log_message(f"🚀 Redis Optimizado: {number} ({props['color']}) - Sector {sector} - Análisis: {len(analysis_data['patterns'])} patrones")
            return True

        except Exception as e:
            log_message(f"❌ Error guardando en Redis: {e}", "ERROR")
            return False

    def _generate_advanced_analysis(self, number, props, last_numbers, timestamp):
        """Generar análisis avanzado del número para ML"""
        try:
            analysis = {
                'patterns': {},
                'gap': None,
                'hot_numbers': [],
                'cold_numbers': [],
                'streak_info': {},
                'ml_features': {}
            }

            # Análisis de patrones
            if len(last_numbers) >= 3:
                last_3 = [int(n) for n in last_numbers[:3]]

                # Patrones básicos
                analysis['patterns']['repeat'] = last_3[0] == number
                analysis['patterns']['alternating_color'] = self._check_color_alternation([number] + last_3[:2])
                analysis['patterns']['consecutive'] = abs(last_3[0] - number) == 1
                analysis['patterns']['same_dozen'] = props['dozen'] == get_number_properties(last_3[0])['dozen']
                analysis['patterns']['same_parity'] = props['parity'] == get_number_properties(last_3[0])['parity']

            # Cálculo de gap (distancia desde última aparición)
            if str(number) in [str(n) for n in last_numbers]:
                last_occurrence = [str(n) for n in last_numbers].index(str(number))
                analysis['gap'] = last_occurrence + 1

            # Números calientes y fríos (últimos 100 spins)
            if len(last_numbers) >= 50:
                from collections import Counter
                recent_counts = Counter([int(n) for n in last_numbers[:50]])
                sorted_counts = sorted(recent_counts.items(), key=lambda x: x[1], reverse=True)
                analysis['hot_numbers'] = [n for n, c in sorted_counts[:5]]  # Top 5 más frecuentes
                analysis['cold_numbers'] = [n for n in range(37) if n not in [x[0] for x in sorted_counts[:20]]][:5]

            # Información de rachas
            if len(last_numbers) >= 10:
                color_streak = self._calculate_color_streak([number] + [int(n) for n in last_numbers[:9]], props['color'])
                analysis['streak_info'] = {
                    'current_color_streak': color_streak,
                    'is_new_streak': color_streak == 1
                }

            # Características para ML
            analysis['ml_features'] = {
                'number': number,
                'color_numeric': {'red': 1, 'black': 0, 'green': 2}[props['color']],
                'dozen': props['dozen'],
                'column': props['column'],
                'parity_numeric': 1 if props['parity'] == 'even' else 0,
                'high_low_numeric': 1 if props['high_low'] == 'high' else 0,
                'hour': datetime.fromtimestamp(timestamp).hour,
                'minute': datetime.fromtimestamp(timestamp).minute,
                'gap': analysis['gap'] or 0,
                'recent_frequency': analysis['gap'] if analysis['gap'] else 100
            }

            return analysis

        except Exception as e:
            log_message(f"❌ Error en análisis avanzado: {e}", "ERROR")
            return {
                'patterns': {},
                'gap': None,
                'hot_numbers': [],
                'cold_numbers': [],
                'streak_info': {},
                'ml_features': {}
            }

    def _check_color_alternation(self, numbers):
        """Verificar si hay alternancia de colores"""
        if len(numbers) < 3:
            return False

        colors = [get_number_color(n) for n in numbers[:3]]
        return colors[0] != colors[1] and colors[1] != colors[2]

    def _calculate_color_streak(self, numbers, current_color):
        """Calcular racha actual de color"""
        streak = 1
        for num in numbers[1:]:
            if get_number_color(num) == current_color:
                streak += 1
            else:
                break
        return streak

    def get_roulette_sector(self, number):
        """Obtener sector de la ruleta (0-8 sectores)"""
        # Orden real de la ruleta europea
        wheel_order = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]

        try:
            position = wheel_order.index(number)
            return position // 5  # Dividir en 8 sectores aproximadamente
        except ValueError:
            return 0

    def get_ml_features(self):
        """Obtener features completos para ML"""
        if not self.redis_client:
            return {}

        try:
            # Historial reciente
            recent_numbers = [int(x) for x in self.redis_client.lrange("roulette:history", 0, 49)]
            recent_colors = [get_number_color(n) for n in recent_numbers[:10]]

            # Estadísticas
            total_spins = int(self.redis_client.get("roulette:total_spins") or 0)

            # Frecuencias
            number_frequencies = {}
            color_counts = {}
            for i in range(37):
                number_frequencies[i] = int(self.redis_client.get(f"roulette:numbers:{i}") or 0)

            for color in ['red', 'black', 'green']:
                color_counts[color] = int(self.redis_client.get(f"roulette:colors:{color}") or 0)

            # Gaps actuales
            current_gaps = {}
            for i in range(37):
                current_gaps[i] = int(self.redis_client.get(f"roulette:gap:{i}") or 0)

            # Patrones
            patterns = {
                'repeats': int(self.redis_client.get("roulette:patterns:repeat") or 0),
                'color_alternates': int(self.redis_client.get("roulette:patterns:color_alternate") or 0)
            }

            return {
                'recent_numbers': recent_numbers,
                'recent_colors': recent_colors,
                'total_spins': total_spins,
                'number_frequencies': number_frequencies,
                'color_counts': color_counts,
                'current_gaps': current_gaps,
                'patterns': patterns,
                'last_update': datetime.now().isoformat()
            }

        except Exception as e:
            log_message(f"❌ Error obteniendo features ML: {e}", "ERROR")
            return {}

    def clear_all_data(self):
        """Limpiar todos los datos de Redis"""
        if not self.redis_client:
            return False

        try:
            keys_to_delete = self.redis_client.keys("roulette:*")
            if keys_to_delete:
                self.redis_client.delete(*keys_to_delete)
                log_message(f"🧹 Limpiados {len(keys_to_delete)} keys de Redis")
            return True
        except Exception as e:
            log_message(f"❌ Error limpiando Redis: {e}", "ERROR")
            return False

class OptimizedRouletteScraper:
    """Scraper optimizado solo Redis"""

    def __init__(self):
        self.driver = None
        self.redis_manager = OptimizedRedisRouletteManager()
        self.last_number = None
        self.consecutive_errors = 0
        self.session_start = datetime.now()
        self.data_validation_enabled = True
        self.heartbeat_interval = 5  # segundos

    def setup_chrome_driver(self):
        """Configurar Chrome driver optimizado"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Usar ChromeDriver instalado manualmente en el contenedor
        chromedriver_path = "/usr/local/bin/chromedriver"
        driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    def setup_session(self):
        """Configurar sesión del scraper"""
        log_message("🔧 Configurando sesión optimizada...")

        try:
            self.driver = self.setup_chrome_driver()

            # Login (usar variables de entorno)
            login_url = os.getenv("LOGIN_URL", "https://www.iamonstro.com.br/sistema/index.php")
            username = os.getenv("ROULETTE_USERNAME", "tu_usuario")
            password = os.getenv("ROULETTE_PASSWORD", "tu_password")
            dashboard_url = os.getenv("DASHBOARD_URL", "https://www.iamonstro.com.br/sistema/dashboard.php?mesa=Lightning%20Roulette")

            self.driver.get(login_url)
            time.sleep(2)

            wait = WebDriverWait(self.driver, 10)
            email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_field.clear()
            email_field.send_keys(username)

            password_field = self.driver.find_element(By.NAME, "senha")
            password_field.clear()
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)

            time.sleep(3)
            self.driver.get(dashboard_url)
            time.sleep(2)

            log_message("✅ Sesión configurada - Modo Ultra Rápido")
            return True

        except Exception as e:
            log_message(f"❌ Error configurando sesión: {e}", "ERROR")
            if self.driver:
                self.driver.quit()
                self.driver = None
            return False

    def validate_data_integrity(self, number_data):
        """Validar integridad de datos antes de enviar a Redis"""
        if not self.data_validation_enabled:
            return True

        try:
            # Validaciones básicas
            number = number_data.get('number')
            if not isinstance(number, int) or number < 0 or number > 36:
                log_message(f"❌ Número inválido: {number}", "ERROR")
                return False

            # Validar consistencia de propiedades
            color = number_data.get('color')
            expected_color = get_number_color(number)
            if color != expected_color:
                log_message(f"❌ Color inconsistente: {number} debería ser {expected_color}, pero es {color}", "ERROR")
                return False

            # Validar timestamp
            timestamp = number_data.get('timestamp')
            if not timestamp:
                log_message("❌ Timestamp faltante", "ERROR")
                return False

            # Validar que no sea un número duplicado reciente
            if hasattr(self, 'last_number') and self.last_number == number:
                time_diff = time.time() - number_data.get('raw_timestamp', 0)
                if time_diff < 5:  # No debería repetirse en menos de 5 segundos
                    log_message(f"⚠️ Posible número duplicado: {number}", "WARNING")
                    return False

            log_message(f"✅ Datos validados correctamente: {number}", "DEBUG")
            return True

        except Exception as e:
            log_message(f"❌ Error validando datos: {e}", "ERROR")
            return False

    def send_heartbeat(self):
        """Enviar heartbeat al sistema para indicar que el scraper está activo"""
        try:
            heartbeat_data = {
                'scraper_status': 'active',
                'timestamp': datetime.now().isoformat(),
                'session_start': self.session_start.isoformat(),
                'consecutive_errors': self.consecutive_errors,
                'last_update': time.time()
            }

            self.redis_manager.redis_client.setex(
                'scraper:heartbeat',
                self.heartbeat_interval * 2,  # TTL el doble del intervalo
                json.dumps(heartbeat_data)
            )

            # También actualizar status general
            self.redis_manager.redis_client.setex(
                'system:scraper_status',
                self.heartbeat_interval * 2,
                'online'
            )

            log_message("💓 Heartbeat enviado", "DEBUG")
            return True

        except Exception as e:
            log_message(f"❌ Error enviando heartbeat: {e}", "ERROR")
            return False

    def notify_backend_new_data(self, number_data):
        """Notificar al backend que hay nuevos datos disponibles"""
        try:
            notification = {
                'event': 'new_roulette_number',
                'number': number_data.get('number'),
                'timestamp': number_data.get('timestamp'),
                'trigger_prediction': True,
                'data_key': 'roulette:current_number'
            }

            # Enviar notificación al canal de eventos
            self.redis_manager.redis_client.publish(
                'roulette:events',
                json.dumps(notification)
            )

            # También crear un flag para el backend
            self.redis_manager.redis_client.setex(
                'roulette:new_data_flag',
                30,  # 30 segundos TTL
                json.dumps({
                    'has_new_data': True,
                    'last_number': number_data.get('number'),
                    'timestamp': time.time()
                })
            )

            log_message(f"🔔 Backend notificado sobre nuevo número: {number_data.get('number')}", "INFO")
            return True

        except Exception as e:
            log_message(f"❌ Error notificando al backend: {e}", "ERROR")
            return False

    def extract_numbers_fast(self):
        """Extraer números ultra rápido con validación avanzada"""
        if not self.driver:
            return []

        try:
            self.driver.refresh()
            time.sleep(1.5)

            numbers = self.driver.execute_script("""
            var table = document.querySelector("table");
            if (!table) return [];

            var rows = table.querySelectorAll("tr");
            var numbers = [];

            for (var i = rows.length - 1; i >= 0; i--) {
                var cells = rows[i].querySelectorAll("td");
                if (cells.length > 0) {
                    var text = cells[0].textContent.trim();

                    // Validación estricta: solo números válidos de ruleta
                    if (text && /^[0-9]+$/.test(text)) {
                        var num = parseInt(text, 10);
                        if (num >= 0 && num <= 36 && !isNaN(num)) {
                            numbers.push(num);
                        }
                    }
                }
            }

            return numbers.slice(0, 20); // Limitar a 20 números máximo
            """)

            # Validación adicional en Python
            if numbers and len(numbers) > 0:
                # Filtrar números válidos y eliminar duplicados consecutivos
                valid_numbers = []
                for num in numbers:
                    if isinstance(num, (int, float)) and 0 <= num <= 36:
                        valid_numbers.append(int(num))

                # Eliminar números negativos que puedan haberse colado
                valid_numbers = [n for n in valid_numbers if n >= 0]

                if valid_numbers:
                    log_message(f"⚡ Extraídos {len(valid_numbers)} números válidos. Más reciente: {valid_numbers[0]}")
                    return valid_numbers
                else:
                    log_message("⚠️ No se encontraron números válidos después de filtrado")
                    return []
            else:
                log_message("⚠️ No se encontraron números válidos")
                return []

        except Exception as e:
            log_message(f"❌ Error extrayendo números: {e}", "ERROR")
            return []

    def run(self):
        """Ejecutar scraper optimizado"""
        log_message("🚀 SCRAPER ULTRA RÁPIDO - SOLO REDIS OPTIMIZADO")
        log_message("⚡ Arquitectura: Scraper Python → Redis (Ultra Rico) → Go ML → Frontend")

        # Limpiar datos previos
        log_message("🧹 Limpiando datos previos...")
        self.redis_manager.clear_all_data()

        # Marcar inicio de sesión
        if self.redis_manager.redis_client:
            self.redis_manager.redis_client.set("roulette:session_start", datetime.now().isoformat())

        try:
            # Configurar sesión
            if not self.setup_session():
                log_message("❌ No se pudo configurar la sesión")
                return

            refresh_interval = int(os.getenv("REFRESH_INTERVAL", "8"))

            # Loop principal ultra optimizado
            while True:
                try:
                    numbers = self.extract_numbers_fast()

                    if not numbers:
                        self.consecutive_errors += 1
                        log_message(f"❌ Sin números. Errores: {self.consecutive_errors}")

                        if self.consecutive_errors >= 3:
                            log_message("🔄 Reconfiguración de sesión...")
                            if self.driver:
                                self.driver.quit()
                            if self.setup_session():
                                self.consecutive_errors = 0
                            else:
                                time.sleep(30)
                        else:
                            time.sleep(refresh_interval)
                        continue

                    self.consecutive_errors = 0
                    current_number = numbers[0]

                    if current_number == self.last_number:
                        log_message(f"⏸️ Sin cambios ({current_number}). Esperando...")
                        time.sleep(refresh_interval)
                        continue

                    # ¡NUEVO NÚMERO DETECTADO!
                    last_num_str = str(self.last_number) if self.last_number is not None else "None"
                    log_message(f"🆕 NUEVO NÚMERO: {last_num_str} → {current_number}")

                    # Preparar datos para validación
                    number_data = {
                        'number': current_number,
                        'color': get_number_color(current_number),
                        'timestamp': datetime.now().isoformat(),
                        'raw_timestamp': time.time(),
                        **get_number_properties(current_number)
                    }

                    # Validar datos antes de guardar
                    if self.validate_data_integrity(number_data):
                        # Guardar en Redis con datos ricos
                        success = self.redis_manager.save_roulette_number(current_number)

                        if success:
                            self.last_number = current_number
                            self.consecutive_errors = 0  # Reset error counter

                            # Notificar al backend sobre nuevos datos
                            self.notify_backend_new_data(number_data)

                            # Enviar heartbeat
                            self.send_heartbeat()

                            # Mostrar stats rápidas
                            if self.redis_manager.redis_client:
                                total = self.redis_manager.redis_client.get("roulette:total_spins")
                                log_message(f"📊 Total spins: {total}, Tiempo activo: {datetime.now() - self.session_start}")
                        else:
                            self.consecutive_errors += 1
                            log_message(f"❌ Error guardando en Redis (errores consecutivos: {self.consecutive_errors})", "ERROR")
                    else:
                        self.consecutive_errors += 1
                        log_message(f"❌ Validación falló (errores consecutivos: {self.consecutive_errors})", "ERROR")

                    time.sleep(refresh_interval)

                except KeyboardInterrupt:
                    log_message("🛑 Detenido por usuario")
                    break
                except Exception as e:
                    self.consecutive_errors += 1
                    log_message(f"❌ Error: {e}")
                    time.sleep(10)

        finally:
            if self.driver:
                self.driver.quit()
            log_message("🔌 Scraper optimizado cerrado")

def main():
    """Función principal"""
    scraper = OptimizedRouletteScraper()
    scraper.run()

if __name__ == "__main__":
    main()