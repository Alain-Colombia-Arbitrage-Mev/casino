from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import os
import re # Para extraer números de texto
import requests # Para OpenRouter
from roulette_analyzer import AnalizadorRuleta, RUEDA_EUROPEA # Importamos la clase
from supabase import create_client, Client # Importamos supabase
from dotenv import load_dotenv # Importar load_dotenv
import json # <--- Para parsear el JSON string
import random # <--- AÑADIDO (aunque el random.choice se eliminó, lo mantengo por si acaso)
import traceback # <--- AÑADIDO para manejar excepciones
import numpy as np
import datetime
import uuid
import math
import threading
import time
from datetime import datetime, timedelta

# Importación condicional de Google Cloud Speech
try:
    from google.cloud import speech
    from google.oauth2 import service_account
    speech_available = True
    print("Google Cloud Speech importado correctamente.")
except ImportError:
    speech_available = False
    print("Google Cloud Speech no disponible. Las funciones de reconocimiento de voz no funcionarán.")

# Importación condicional de ML Predictor
try:
    from ml_predictor import MLPredictor
    ml_predictor_available = True
    print("ML Predictor importado correctamente.")
except ImportError:
    ml_predictor_available = False
    print("ML Predictor no disponible. Las funciones de ML no funcionarán.")

# Importación del nuevo sistema avanzado de ML
try:
    from advanced_ml_predictor import AdvancedMLPredictor
    advanced_ml_available = True
    print("Advanced ML Predictor importado correctamente.")
except ImportError:
    advanced_ml_available = False
    print("Advanced ML Predictor no disponible.")

# Importación del sistema de evaluación de predicciones
try:
    from prediction_evaluator import PredictionEvaluator
    prediction_evaluator_available = True
    print("Prediction Evaluator importado correctamente.")
except ImportError:
    prediction_evaluator_available = False
    print("Prediction Evaluator no disponible.")

# Importación del sistema de entrenamiento con victorias
try:
    from victory_trainer import VictoryTrainer, create_victory_trainer
    victory_trainer_available = True
    print("Victory Trainer importado correctamente.")
except ImportError:
    victory_trainer_available = False
    print("Victory Trainer no disponible.")

# Importar nuevos sistemas
try:
    from sector_manager import SectorManager, create_sector_manager
    sector_manager_available = True
except ImportError as e:
    sector_manager_available = False
    print(f"⚠️ Sector Manager no disponible: {e}")

try:
    from number_processor import NumberProcessor, create_number_processor, procesar_numeros_rapido
    number_processor_available = True
except ImportError as e:
    number_processor_available = False
    print(f"⚠️ Number Processor no disponible: {e}")

# Cargar variables de entorno desde .env si existe (para desarrollo local)
load_dotenv()

app = Flask(__name__)

# Configuración de CORS simplificada
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:5001", "http://127.0.0.1:5001", "http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:3002", "http://127.0.0.1:3002"], supports_credentials=False, allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "OPTIONS"])

# Custom JSON encoder para manejar tipos de NumPy
class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'dtype') and np.issubdtype(obj.dtype, np.number):  # Para otros tipos numéricos de NumPy
            return obj.item()  # Convertir a tipo Python nativo
        return super(NumpyJSONEncoder, self).default(obj)

app.json_encoder = NumpyJSONEncoder  # Usar el encoder personalizado

# --- Configuración de Credenciales de Google Cloud ---
gcp_credentials = None

if speech_available:
    raw_google_creds_json_str = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")

    if raw_google_creds_json_str:
        try:
            credentials_info = json.loads(raw_google_creds_json_str)
            gcp_credentials = service_account.Credentials.from_service_account_info(credentials_info)
            print("Credenciales de Google Cloud cargadas desde la variable de entorno GOOGLE_APPLICATION_CREDENTIALS_JSON.")
        except Exception as e:
            print(f"Error al cargar credenciales desde GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}. Intentando fallback.")
            gcp_credentials = None # Asegurar que esté None si falla

    if not gcp_credentials: # Si no se cargaron desde la variable de entorno JSON
        # Usar la ruta explícita proporcionada por el usuario
        local_credentials_path = "backend/credentials/caloriasapp-253ec-bc2aa06fdb0b.json"
        # Si la ruta es relativa y estamos en la carpeta raíz, añadir la ruta completa
        if not os.path.exists(local_credentials_path) and os.path.exists(os.path.join(os.getcwd(), local_credentials_path)):
            local_credentials_path = os.path.join(os.getcwd(), local_credentials_path)
        # Si la ruta es relativa y estamos en la carpeta backend, usar ruta directa
        elif not os.path.exists(local_credentials_path) and os.path.exists("credentials/caloriasapp-253ec-bc2aa06fdb0b.json"):
            local_credentials_path = "credentials/caloriasapp-253ec-bc2aa06fdb0b.json"
        
        if os.path.exists(local_credentials_path):
            try:
                gcp_credentials = service_account.Credentials.from_service_account_file(local_credentials_path)
                print(f"Credenciales de Google Cloud cargadas desde: {local_credentials_path}")
                # Establecer variable de entorno para el API de Google
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local_credentials_path
            except Exception as e:
                print(f"Error al cargar credenciales desde {local_credentials_path}: {e}")
                gcp_credentials = None
        else:
            print(f"ADVERTENCIA: Archivo de credenciales no encontrado en {local_credentials_path}. STT no funcionará.")
else:
    print("Google Cloud Speech no disponible, no se cargarán credenciales.")
# --- Fin Configuración de Credenciales ---

# Configuración optimizada de Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Configuración adicional para optimizar la conexión
SUPABASE_OPTIONS = {
    "auto_refresh_token": True,
    "persist_session": True,
    "detection_of_session_in_url": False,
    "headers": {
        "apikey": SUPABASE_KEY,
        "User-Agent": "roulette-analyzer/1.0",
        "Prefer": "return=representation"  # Asegurar que Supabase retorne los datos insertados
    }
}

# Inicializar cliente de Supabase de forma global
supabase_client: Client | None = None
TABLE_NAME = "roulette_history" # Nombre de tu tabla en Supabase
ANALYZER_STATE_TABLE_NAME = "analyzer_state" # Nombre de la tabla de estado del analizador

# Definir los nombres de las nuevas tablas de sectores ANTES de su uso
SECTORES_DEFINICIONES_TABLE_NAME = "sectores_definiciones"
SECTORES_CONTEOS_TABLE_NAME = "sectores_conteos"

# Mapa global para ID de sector a nombre
map_id_a_nombre_sector: dict = {} # <--- HACER GLOBAL

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY, options=SUPABASE_OPTIONS)
        print(f"Cliente de Supabase inicializado. Intentando interactuar con la tabla '{TABLE_NAME}'.")
    except Exception as e:
        print(f"Error al inicializar el cliente de Supabase: {e}")
else:
    print("Advertencia: Variables de entorno SUPABASE_URL y/o SUPABASE_KEY no encontradas. Supabase no se utilizará.")

# Configurar timeouts y configuraciones robustas para Supabase
if supabase_client:
    # Configurar timeouts más agresivos para detectar problemas rápidamente
    try:
        # Test de conectividad inicial
        test_response = supabase_client.table(TABLE_NAME).select("id").limit(1).execute()
        print("✅ Conexión inicial con Supabase establecida correctamente")
        
        # Configurar el cliente HTTP subyacente si es posible
        if hasattr(supabase_client, '_client') and hasattr(supabase_client._client, 'timeout'):
            supabase_client._client.timeout = 10  # 10 segundos de timeout
            print("⚙️ Timeout configurado a 10 segundos")
            
    except Exception as e:
        print(f"⚠️ Advertencia en test inicial de Supabase: {e}")

# Configuración de OpenRouter
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL_ID = "google/gemini-2.5-pro-preview" # Modelo especificado por el usuario
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

if not OPENROUTER_API_KEY:
    print("Advertencia: OPENROUTER_API_KEY no encontrada. Las sugerencias de IA avanzada no estarán disponibles.")

# Cargar estado del analizador y el historial ANTES de que se defina el analizador global
# Esto es para que las definiciones de sectores, etc., estén disponibles cuando se cree la instancia.
# La carga del historial de números vendrá después de que la instancia se cree con las definiciones correctas.
# load_analyzer_state_from_supabase() # Se llamará después de inicializar supabase_client

analizador = AnalizadorRuleta(historial_max_longitud=25) # Usamos el historial que definimos

# Inicializamos el ML predictor si está disponible
ml_predictor = None
if ml_predictor_available:
    try:
        ml_predictor = MLPredictor()
        print("ML Predictor inicializado correctamente.")
    except Exception as e:
        print(f"Error al inicializar ML Predictor: {e}")
        ml_predictor = None

# Inicializamos el Advanced ML predictor
advanced_ml_predictor = None
if advanced_ml_available:
    try:
        advanced_ml_predictor = AdvancedMLPredictor()
        print("Advanced ML Predictor inicializado correctamente.")
        
        # Programar entrenamiento automático en background
        def entrenar_ml_background():
            """Entrena el sistema ML avanzado en background"""
            try:
                # Esperar a que supabase_client esté disponible
                import time
                max_wait_time = 30  # Esperar máximo 30 segundos
                wait_count = 0
                while not supabase_client and wait_count < max_wait_time:
                    time.sleep(1)
                    wait_count += 1
                
                if not supabase_client:
                    print("⚠️ Supabase client no disponible después de esperar. Saltando entrenamiento automático.")
                    return
                
                if advanced_ml_predictor and not advanced_ml_predictor.is_trained:
                    print("🔄 Iniciando entrenamiento automático del sistema ML avanzado...")
                    
                    # Verificar que la función load_extended_history_for_ml esté disponible
                    if 'load_extended_history_for_ml' not in globals():
                        print("❌ Función load_extended_history_for_ml no está disponible")
                        return
                    
                    extended_history = load_extended_history_for_ml()
                    
                    if extended_history and len(extended_history) >= 50:
                        # Convertir a números enteros si es necesario
                        if extended_history and hasattr(extended_history[0], 'numero'):
                            numbers = [obj.numero for obj in extended_history]
                        else:
                            numbers = extended_history
                        
                        success = advanced_ml_predictor.train_models(numbers)
                        if success:
                            print("✅ Sistema ML avanzado entrenado automáticamente")
                        else:
                            print("❌ Error en entrenamiento automático del sistema ML")
                    else:
                        print("⚠️ Historial insuficiente para entrenamiento automático")
            except Exception as e:
                print(f"❌ Error en entrenamiento automático: {e}")
                import traceback
                traceback.print_exc()
        
        # Ejecutar entrenamiento en thread separado para no bloquear el inicio
        threading.Thread(target=entrenar_ml_background, daemon=True).start()
        
    except Exception as e:
        print(f"Error al inicializar Advanced ML Predictor: {e}")
        advanced_ml_predictor = None

# Inicializamos el evaluador de predicciones
prediction_evaluator = None
if prediction_evaluator_available:
    try:
        prediction_evaluator = PredictionEvaluator(supabase_client)
        prediction_evaluator.load_statistics_from_db()  # Cargar estadísticas existentes
        print("Prediction Evaluator inicializado correctamente.")
    except Exception as e:
        print(f"Error al inicializar Prediction Evaluator: {e}")
        prediction_evaluator = None

# Inicializamos el sistema de entrenamiento con victorias
victory_trainer = None
if victory_trainer_available:
    try:
        victory_trainer = create_victory_trainer(supabase_client)
        if victory_trainer:
            print("Victory Trainer inicializado correctamente.")
        else:
            print("Error al crear Victory Trainer.")
    except Exception as e:
        print(f"Error al inicializar Victory Trainer: {e}")
        victory_trainer = None

# Variables globales necesarias para las funciones de carga
map_id_a_nombre_sector = {}
ANALYZER_STATE_TABLE_NAME = "analyzer_state"
SECTORES_DEFINICIONES_TABLE_NAME = "sectores_definiciones"
SECTORES_CONTEOS_TABLE_NAME = "sectores_conteos"

# Cache para las sugerencias de OpenRouter para evitar llamadas repetidas
openrouter_cache = {}
openrouter_cache_max_size = 20  # Limitar el tamaño máximo del caché

# Para incluir o no las sugerencias de IA externa en cada análisis (para evitar tiempos de espera)
# True = incluir sugerencias, False = omitir sugerencias para respuesta más rápida
INCLUIR_SUGERENCIAS_IA = False  # Configurado como False por defecto para respuestas rápidas

# Definimos la variable global necesaria para guardar historial
GUARDAR_HISTORIAL_SUPABASE = True

# Nueva tabla para números individuales
NUMEROS_INDIVIDUALES_TABLE_NAME = "roulette_numbers_individual"

# Sistema de cache para predicciones avanzadas
predicciones_cache = {}
predicciones_cache_expiry = {}
CACHE_EXPIRY_MINUTES = 5  # Cache válido por 5 minutos

# Configuración para entrenamiento automático
auto_training_enabled = True
last_training_time = None
training_interval_hours = 6  # Re-entrenar cada 6 horas si hay nuevos datos

# Funciones de Ayuda para Supabase
def load_history_from_supabase():
    if not supabase_client:
        print("Cliente de Supabase no disponible, no se cargará el historial.")
        return
    try:
        print(f"Intentando cargar el último historial desde la tabla '{TABLE_NAME}'...")
        response = (
            supabase_client.table(TABLE_NAME)
            .select("numbers_string")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            ultimo_historial_str = response.data[0]['numbers_string']
            # La cadena se guarda con el más reciente primero, que es lo que espera cargar_numeros_desde_string
            analizador.cargar_numeros_desde_string(ultimo_historial_str, mas_reciente_primero=True)
            print(f"Historial cargado desde Supabase: {len(analizador.historial_numeros)} números. Último: {analizador.obtener_ultimo_numero_analizado().numero if analizador.historial_numeros else 'N/A'}")
        else:
            print("No se encontró historial previo en Supabase.")
    except Exception as e:
        print(f"Error al cargar historial desde Supabase: {e}. Verifica que la tabla '{TABLE_NAME}' exista y tenga las columnas correctas (numbers_string, created_at).")

# Nueva función para cargar un historial extendido para entrenamiento ML
def load_extended_history_for_ml():
    """
    Carga un historial extendido desde Supabase para entrenar modelos de ML.
    Returns:
        list: Lista de números de la ruleta (del más reciente al más antiguo)
    """
    if not supabase_client:
        print("Cliente de Supabase no disponible, no se cargará el historial extendido.")
        return []
        
    try:
        print("Cargando historial extendido para entrenamiento ML desde Supabase...")
        
        # Primero intentamos obtener los registros de números individuales (más preciso)
        response_individual = None
        try:
            response_individual = (
                supabase_client.table(NUMEROS_INDIVIDUALES_TABLE_NAME)
                .select("number_value")
                .order("id", desc=True)
                .limit(1000)  # Limitamos a 1000 números para evitar sobrecarga
                .execute()
            )
            
            if response_individual.data and len(response_individual.data) > 50:  # Asegurarnos de tener suficientes datos
                numeros = [entry['number_value'] for entry in response_individual.data]
                print(f"Cargados {len(numeros)} números individuales para entrenamiento ML.")
                return numeros
            else:
                print("Datos insuficientes en tabla de números individuales, intentando con el historial completo.")
        except Exception as e:
            print(f"Error al cargar números individuales, continuando con historial completo: {e}")
        
        # Si no hay suficientes números individuales, cargar desde el historial completo
        response = (
            supabase_client.table(TABLE_NAME)
            .select("numbers_string")
            .order("created_at", desc=True)
            .limit(50)  # Obtenemos las últimas 50 entradas del historial
            .execute()
        )
        
        if not response.data:
            print("No se encontró historial en Supabase para entrenamiento ML.")
            return []
            
        # Procesar todas las cadenas de números y combinarlas
        numeros_completos = []
        for entry in response.data:
            numeros_str = entry['numbers_string']
            if numeros_str:
                # Convertir cadena a lista de enteros y añadir al historial
                numeros_lista = [int(n.strip()) for n in numeros_str.split(",") if n.strip().isdigit()]
                numeros_completos.extend(numeros_lista)
                
        print(f"Cargados {len(numeros_completos)} números desde historial completo para entrenamiento ML.")
        return numeros_completos
        
    except Exception as e:
        print(f"Error al cargar historial extendido para ML: {e}")
        return []

# Funciones auxiliares para cache y entrenamiento
def get_cache_key(history_numbers):
    """Genera una clave de cache basada en los últimos números del historial"""
    if not history_numbers:
        return "empty"
    # Usar los últimos 10 números para la clave
    last_numbers = history_numbers[:10] if len(history_numbers) >= 10 else history_numbers
    return f"pred_{'_'.join(map(str, last_numbers))}"

def is_cache_valid(cache_key):
    """Verifica si el cache para una clave específica aún es válido"""
    if cache_key not in predicciones_cache_expiry:
        return False
    
    expiry_time = predicciones_cache_expiry[cache_key]
    current_time = datetime.now()
    
    return current_time < expiry_time

def get_cached_prediction(history_numbers):
    """Obtiene predicción del cache si está disponible y es válida"""
    cache_key = get_cache_key(history_numbers)
    
    if cache_key in predicciones_cache and is_cache_valid(cache_key):
        print(f"📋 Usando predicción en cache para {cache_key[:50]}...")
        return predicciones_cache[cache_key]
    
    return None

def cache_prediction(history_numbers, prediction):
    """Guarda una predicción en el cache"""
    cache_key = get_cache_key(history_numbers)
    
    # Limpiar cache antiguo si es muy grande (máximo 50 entradas)
    if len(predicciones_cache) >= 50:
        # Eliminar las entradas más antiguas
        old_keys = list(predicciones_cache.keys())[:10]
        for old_key in old_keys:
            predicciones_cache.pop(old_key, None)
            predicciones_cache_expiry.pop(old_key, None)
    
    # Guardar nueva predicción
    predicciones_cache[cache_key] = prediction
    predicciones_cache_expiry[cache_key] = datetime.now() + timedelta(minutes=CACHE_EXPIRY_MINUTES)
    
    print(f"💾 Predicción guardada en cache: {cache_key[:50]}...")

def should_retrain_model():
    """Determina si es necesario re-entrenar el modelo"""
    global last_training_time
    
    if not auto_training_enabled:
        return False
    
    if not last_training_time:
        return True
    
    time_since_training = datetime.now() - last_training_time
    return time_since_training.total_seconds() > (training_interval_hours * 3600)

def update_training_time():
    """Actualiza el tiempo de último entrenamiento"""
    global last_training_time
    last_training_time = datetime.now()

# Nueva función para cargar el estado del analizador
def load_analyzer_state_from_supabase():
    if not supabase_client:
        print("Cliente de Supabase no disponible, no se cargará el estado del analizador.")
        return
    try:
        print(f"Intentando cargar el estado del analizador desde la tabla '{ANALYZER_STATE_TABLE_NAME}'...")
        # Cargar estado principal del analizador (sin los conteos de sectores individuales)
        response_estado = supabase_client.table(ANALYZER_STATE_TABLE_NAME).select(
            "aciertos_individual, aciertos_grupo, aciertos_vecinos_0_10, aciertos_vecinos_7_27, "
            "total_predicciones_evaluadas, aciertos_tia_lu, tia_lu_estado_activa, "
            "tia_lu_estado_giros_jugados, tia_lu_estado_activada_con_33, "
            "tia_lu_estado_contador_desencadenantes_consecutivos, tia_lu_estado_ultimo_numero_fue_desencadenante"
        ).eq("id", 1).maybe_single().execute()

        if response_estado.data:
            data_estado = response_estado.data
            print("Estado principal del analizador encontrado en Supabase, actualizando instancia local.")
            analizador.aciertos_individual = data_estado.get('aciertos_individual', 0)
            analizador.aciertos_grupo = data_estado.get('aciertos_grupo', 0)
            analizador.aciertos_vecinos_0_10 = data_estado.get('aciertos_vecinos_0_10', 0)
            analizador.aciertos_vecinos_7_27 = data_estado.get('aciertos_vecinos_7_27', 0)
            analizador.total_predicciones_evaluadas = data_estado.get('total_predicciones_evaluadas', 0)
            analizador.aciertos_tia_lu = data_estado.get('aciertos_tia_lu', 0)
            
            analizador.tia_lu_estado["activa"] = data_estado.get('tia_lu_estado_activa', False)
            analizador.tia_lu_estado["giros_jugados"] = data_estado.get('tia_lu_estado_giros_jugados', 0)
            analizador.tia_lu_estado["activada_con_33"] = data_estado.get('tia_lu_estado_activada_con_33', False)
            analizador.tia_lu_estado["contador_desencadenantes_consecutivos"] = data_estado.get('tia_lu_estado_contador_desencadenantes_consecutivos', 0)
            analizador.tia_lu_estado["ultimo_numero_fue_desencadenante"] = data_estado.get('tia_lu_estado_ultimo_numero_fue_desencadenante', False)
        else:
            print("No se encontró estado principal previo del analizador en Supabase. Se usarán los valores por defecto.")

        # Cargar definiciones de sectores personalizados
        print(f"Intentando cargar definiciones de sectores desde '{SECTORES_DEFINICIONES_TABLE_NAME}'...")
        response_defs = supabase_client.table(SECTORES_DEFINICIONES_TABLE_NAME).select("id, nombre_sector, numeros").execute()
        
        definiciones_sectores = {}
        global map_id_a_nombre_sector
        map_id_a_nombre_sector.clear() # Limpiar por si se recarga

        if response_defs.data:
            for definicion in response_defs.data:
                try:
                    # Convertir la cadena de números "1,2,3" a un set de enteros
                    set_numeros = set(map(int, definicion['numeros'].split(',')))
                    definiciones_sectores[definicion['nombre_sector']] = set_numeros
                    map_id_a_nombre_sector[definicion['id']] = definicion['nombre_sector']
                except ValueError:
                    print(f"Advertencia: Formato de números inválido para el sector '{definicion['nombre_sector']}' con id '{definicion['id']}'. Se omitirá.")
            print(f"{len(definiciones_sectores)} definiciones de sectores cargadas.")
        else:
            print("No se encontraron definiciones de sectores en Supabase.")

        # Cargar conteos de sectores personalizados
        conteos_sectores = {nombre: 0 for nombre in definiciones_sectores} # Inicializar con 0
        if definiciones_sectores: # Solo cargar conteos si hay definiciones
            print(f"Intentando cargar conteos de sectores desde '{SECTORES_CONTEOS_TABLE_NAME}'...")
            response_counts = supabase_client.table(SECTORES_CONTEOS_TABLE_NAME).select("id_sector_definicion, conteo").eq("id_estado_analizador", 1).execute()
            
            if response_counts.data:
                for conteo_info in response_counts.data:
                    id_sector = conteo_info['id_sector_definicion']
                    nombre_sector = map_id_a_nombre_sector.get(id_sector)
                    if nombre_sector:
                        conteos_sectores[nombre_sector] = conteo_info['conteo']
                    else:
                        print(f"Advertencia: Conteo encontrado para id_sector_definicion '{id_sector}' desconocido. Se omitirá.")
                print(f"Conteos para {len(response_counts.data)} sectores cargados.")
            else:
                print("No se encontraron conteos de sectores en Supabase (o tabla vacía).")
        
        analizador.cargar_estado_sectores_personalizados(definiciones_sectores, conteos_sectores)
        print("Estado completo del analizador (incluyendo sectores) cargado/actualizado.")

    except Exception as e:
        print(f"Error EXCEPCIÓN al cargar el estado completo del analizador desde Supabase: {e}. Se usarán los valores por defecto.")

# --- Carga inicial de datos ---
if supabase_client: # Asegurarse que el cliente esté inicializado
    load_analyzer_state_from_supabase() # Carga definiciones de sectores y contadores de aciertos
    load_history_from_supabase() # Carga el historial de números

# MODIFICADO: save_individual_numbers_to_supabase
# Ahora acepta history_entry_id y guarda el mapeo correcto
def save_individual_numbers_to_supabase(history_entry_id: int, numeros_str: str):
    """
    Versión mejorada que usa NumberProcessor para manejo avanzado de números
    """
    if not supabase_client:
        print("Cliente de Supabase no disponible, no se guardarán los números individuales.")
        return False
    
    if not history_entry_id:
        print("ID de entrada de historial no válido, no se guardarán números individuales.")
        return False
        
    # Usar el NumberProcessor si está disponible
    if number_processor:
        try:
            exito, registros, mensaje = number_processor.procesar_y_preparar_para_db(numeros_str, history_entry_id)
            
            if not exito:
                print(f"❌ {mensaje}")
                return False
            
            if not registros:
                print(f"⚠️ No hay registros para insertar")
                return False
            
            # Insertar registros en Supabase
            max_retries = 3
            for intento in range(max_retries):
                try:
                    response = supabase_client.table(NUMEROS_INDIVIDUALES_TABLE_NAME).insert(registros).execute()
                    
                    if hasattr(response, 'error') and response.error:
                        print(f"Error al guardar números individuales: {response.error}")
                        if intento < max_retries - 1:
                            time.sleep(1)
                            continue
                        return False
                    
                    if response.data and len(response.data) == len(registros):
                        print(f"✅ {mensaje} - {len(response.data)} registros guardados exitosamente")
                        
                        # Verificar aciertos en sectores si el sector_manager está disponible
                        if sector_manager:
                            for registro in registros:
                                sectores_acertados = sector_manager.verificar_acierto_sectores(registro['number_value'])
                                if sectores_acertados:
                                    print(f"🎯 Número {registro['number_value']} acertó en sectores: {', '.join(sectores_acertados)}")
                        
                        return True
                    else:
                        print(f"⚠️ Respuesta inesperada: {len(response.data) if response.data else 0} de {len(registros)} registros insertados")
                        if intento < max_retries - 1:
                            time.sleep(1)
                            continue
                        return False
                        
                except Exception as e:
                    print(f"Error en intento {intento + 1}: {e}")
                    if intento < max_retries - 1:
                        time.sleep(1)
                        continue
                    return False
            
            return False
            
        except Exception as e:
            print(f"Error usando NumberProcessor: {e}")
            traceback.print_exc()
            # Fallback al método original
    
    # Método original como fallback
    max_retries = 3
    retry_delay = 1
    
    for intento in range(max_retries):
        try:
            # Procesar la cadena de números (método original)
            numeros_lista = []
            if "," in numeros_str:
                numeros_lista = [int(n.strip()) for n in numeros_str.split(",") if n.strip().isdigit()]
            else:
                if numeros_str.strip().isdigit():
                    numeros_lista = [int(numeros_str.strip())]
            
            if not numeros_lista:
                print(f"No se encontraron números válidos en la cadena: '{numeros_str}' para el historial ID: {history_entry_id}")
                return False

            # Preparar registros para inserción con timestamp
            timestamp_actual = datetime.now().isoformat()
            registros_a_insertar = []
            for numero_val in numeros_lista:
                numero_limpio = int(numero_val.item() if hasattr(numero_val, 'item') else numero_val)
                
                # Determinar color usando NumberProcessor si está disponible
                color = 'Desconocido'
                if number_processor:
                    color = number_processor.obtener_color_numero(numero_limpio)
                else:
                    # Método básico de determinación de color
                    if numero_limpio == 0:
                        color = 'Verde'
                    elif numero_limpio in {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}:
                        color = 'Rojo'
                    else:
                        color = 'Negro'
                
                registros_a_insertar.append({
                    "history_entry_id": history_entry_id,
                    "number_value": numero_limpio,
                    "color": color,
                    "created_at": timestamp_actual
                })
            
            if registros_a_insertar:
                print(f"Intentando guardar {len(registros_a_insertar)} números individuales (intento {intento + 1}/{max_retries})...")
                response = supabase_client.table(NUMEROS_INDIVIDUALES_TABLE_NAME).insert(registros_a_insertar).execute()
                
                if hasattr(response, 'error') and response.error:
                    print(f"Error al guardar números individuales: {response.error}")
                    if intento < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return False
                    
                elif response.data:
                    if len(response.data) == len(registros_a_insertar):
                        print(f"✅ {len(response.data)} números individuales guardados exitosamente (método fallback).")
                        
                        # Verificar aciertos en sectores
                        if sector_manager:
                            for registro in registros_a_insertar:
                                sectores_acertados = sector_manager.verificar_acierto_sectores(registro['number_value'])
                                if sectores_acertados:
                                    print(f"🎯 Número {registro['number_value']} acertó en sectores: {', '.join(sectores_acertados)}")
                        
                            return True
                    else:
                        print(f"⚠️ Se insertaron {len(response.data)} de {len(registros_a_insertar)} registros")
                        if intento < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        return False
                else:
                    print(f"Respuesta no esperada al guardar números individuales: {response}")
                    if intento < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return False
                
        except ValueError as e:
            print(f"Error al procesar valores numéricos: {e}")
            return False
        except Exception as e:
            print(f"Error en intento {intento + 1} al guardar números individuales: {e}")
            if intento < max_retries - 1:
                time.sleep(retry_delay)
                continue
            traceback.print_exc()
            return False
    
    print(f"❌ Falló al guardar números individuales después de {max_retries} intentos")
    return False

def save_history_to_supabase(numeros_str: str):
    if not supabase_client:
        print("Cliente de Supabase no disponible, no se guardará el historial.")
        return None

    inserted_history_id = None
    max_retries = 3
    retry_delay = 1  # segundos

    for intento in range(max_retries):
        try:
            print(f"Intentando guardar historial en Supabase (intento {intento + 1}/{max_retries}): '{numeros_str}'...")
            
            # Insertar con confirmación explícita
            response = supabase_client.table(TABLE_NAME).insert({
                "numbers_string": numeros_str,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            # Verificar respuesta de manera más robusta
            if hasattr(response, 'error') and response.error:
                print(f"Error devuelto por Supabase al guardar historial: {response.error}")
                if intento < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None
                
            elif response.data and len(response.data) > 0:
                inserted_history_id = response.data[0].get('id')
                print(f"✅ Historial guardado exitosamente. ID: {inserted_history_id}")
                
                # Verificar que realmente se guardó
                verification = supabase_client.table(TABLE_NAME).select("id").eq("id", inserted_history_id).execute()
                if not verification.data:
                    print(f"⚠️ Verificación falló para ID {inserted_history_id}, reintentando...")
                    if intento < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return None
                
                # Guardar números individuales con confirmación
                if inserted_history_id:
                    individual_success = save_individual_numbers_to_supabase(inserted_history_id, numeros_str)
                    if not individual_success and intento < max_retries - 1:
                        print("Fallo al guardar números individuales, reintentando...")
                        time.sleep(retry_delay)
                        continue
                
                return inserted_history_id
            else:
                print(f"Respuesta inesperada de Supabase: {response}")
                if intento < max_retries - 1:
                    time.sleep(retry_delay)
                    continue

        except Exception as e:
            print(f"Error en intento {intento + 1}: {e}")
            if intento < max_retries - 1:
                time.sleep(retry_delay)
                continue
            traceback.print_exc()
            
    print(f"❌ Falló al guardar historial después de {max_retries} intentos")
    return None

# Nueva función para guardar el estado del analizador
def save_analyzer_state_to_supabase():
    """Guarda el estado del analizador en Supabase."""
    if not supabase_client:
        print("Cliente de Supabase no disponible, no se guardará el estado del analizador.")
        return

    try:
        # Guardar estado principal del analizador
        state_data_principal = {
            "id": 1, 
            "aciertos_individual": analizador.aciertos_individual,
            "aciertos_grupo": analizador.aciertos_grupo,
            "aciertos_vecinos_0_10": analizador.aciertos_vecinos_0_10,
            "aciertos_vecinos_7_27": analizador.aciertos_vecinos_7_27,
            "total_predicciones_evaluadas": analizador.total_predicciones_evaluadas,
            "aciertos_tia_lu": analizador.aciertos_tia_lu,
            "tia_lu_estado_activa": analizador.tia_lu_estado["activa"],
            "tia_lu_estado_giros_jugados": analizador.tia_lu_estado["giros_jugados"],
            "tia_lu_estado_activada_con_33": analizador.tia_lu_estado["activada_con_33"],
            "tia_lu_estado_contador_desencadenantes_consecutivos": analizador.tia_lu_estado["contador_desencadenantes_consecutivos"],
            "tia_lu_estado_ultimo_numero_fue_desencadenante": analizador.tia_lu_estado["ultimo_numero_fue_desencadenante"],
            "updated_at": "now()"
        }
        
        print("Guardando estado principal del analizador...")
        response_principal = supabase_client.table(ANALYZER_STATE_TABLE_NAME).upsert(state_data_principal).execute()
        
        if not response_principal.data:
            print("Advertencia: No se recibió confirmación del guardado del estado principal.")
        
        # Guardar conteos de sectores personalizados si existen
        if not analizador.conteo_sectores_personalizados:
            return

        # Preparar datos de conteos para actualización
        datos_upsert_conteos = []
        for nombre_sector, conteo in analizador.conteo_sectores_personalizados.items():
            try:
                response_sector = supabase_client.table(SECTORES_DEFINICIONES_TABLE_NAME).select("id").eq("nombre_sector", nombre_sector).single().execute()
                if response_sector.data:
                    datos_upsert_conteos.append({
                        "id_estado_analizador": 1,
                        "id_sector_definicion": response_sector.data["id"],
                        "conteo": conteo
                        # Se elimina updated_at porque no existe en el esquema
                    })
            except Exception as e:
                print(f"Error al buscar ID para el sector '{nombre_sector}': {e}")
                continue

        if datos_upsert_conteos:
            print(f"Actualizando conteos para {len(datos_upsert_conteos)} sectores...")
            try:
                response_conteos = supabase_client.table(SECTORES_CONTEOS_TABLE_NAME).upsert(
                    datos_upsert_conteos,
                    on_conflict="id_estado_analizador,id_sector_definicion"
                ).execute()

                if not response_conteos.data:
                    print("Advertencia: No se recibió confirmación del guardado de conteos de sectores.")
            except Exception as e:
                print(f"Error al guardar conteos de sectores: {e}")
                traceback.print_exc()

    except Exception as e:
        print(f"Error al guardar el estado del analizador: {e}")
        traceback.print_exc()

# Cargar historial al iniciar la app
load_history_from_supabase()

# Cargar estado del analizador al iniciar la app
load_analyzer_state_from_supabase()

# Función para extraer número de texto
def extract_number_from_text(text: str) -> str | None:
    """Intenta extraer un número de una cadena de texto.
       Ej: 'salió el 23' -> '23', 'es el 5' -> '5' """
    if not text:
        return None
    
    # Primero, verificar si el texto ya es solo un número
    if text.strip().isdigit():
        return text.strip()

    # Lista de patrones a verificar
    patrones = [
        # Buscar patrones como "el [número]", "es [número]", "[número]"
        r'\b(\d{1,2})\b',  # Números de 1 o 2 dígitos como palabras completas
        
        # Patrones específicos
        r'salió\s+(?:el\s+)?(?:número\s+)?(\d{1,2})',
        r'salió\s+(?:el\s+)(\d{1,2})',
        r'salió\s+(\d{1,2})',
        r'es\s+(?:el\s+)?(?:número\s+)?(\d{1,2})',
        r'número\s+(\d{1,2})',
        r'cayó\s+(?:el\s+)?(?:número\s+)?(\d{1,2})',
    ]
    
    # Verificar cada patrón
    for patron in patrones:
        match = re.search(patron, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

# Función para OpenRouter
def obtener_sugerencia_openrouter(historial_numeros: list) -> str | None:
    if not OPENROUTER_API_KEY or not historial_numeros:
        if not OPENROUTER_API_KEY: 
            print("OpenRouter API Key no disponible.")
            return "Sugerencias de IA no disponibles (API Key no configurada)."
        if not historial_numeros: 
            print("No hay historial para enviar a OpenRouter.")
            return "No hay suficiente historial para generar sugerencias."
        return None
    
    # Comprobar si historial_numeros es una lista de objetos NumeroRoleta o de enteros
    historial_enteros = []
    if historial_numeros and hasattr(historial_numeros[0], 'numero'):
        historial_enteros = [n.numero for n in historial_numeros]
    else:
        historial_enteros = historial_numeros
    
    # Tomar los últimos N números para el prompt
    numeros_recientes_str = ",".join([str(n) for n in reversed(historial_enteros)])
    
    # Verificar si tenemos esta secuencia en caché
    if numeros_recientes_str in openrouter_cache:
        print("Usando sugerencia en caché para la secuencia de números.")
        return openrouter_cache[numeros_recientes_str]

    prompt_text = (
        f"Eres un experto analista de ruleta. Basándote en la siguiente secuencia de los últimos números de ruleta "
        f"(el primer número es el más reciente): {numeros_recientes_str}\n\n"
        f"Por favor, proporciona:\n"
        f"1. Una predicción del número individual con la mayor probabilidad de salir próximamente.\n"
        f"2. Un grupo de 20 números que consideres con alta probabilidad estadística (incluye siempre el número 1 en este grupo).\n"
        f"3. Una justificación detallada para estas predicciones, basada en los patrones que observes en la secuencia proporcionada.\n"
        f"4. Predicciones específicas para los vecinos del 0 y del 10 en la rueda física, y para el rango de números entre 7 y 27 (inclusivo).\n\n"
        f"Formatea tu respuesta de manera clara y concisa, lista para ser mostrada a un usuario."
    )
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5001",
        "X-Title": "Analizador de Ruleta"
    }
    payload = {
        "model": OPENROUTER_MODEL_ID,
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    print(f"Enviando solicitud a OpenRouter con el modelo: {OPENROUTER_MODEL_ID}")
    try:
        session = requests.Session()
        response = session.post(
            OPENROUTER_API_URL, 
            headers=headers, 
            json=payload, 
            timeout=20,
            verify=True
        )
        
        if response.status_code != 200:
            error_msg = f"Error en OpenRouter (Status {response.status_code}): {response.text}"
            print(error_msg)
            return f"Error al obtener sugerencias de IA: {error_msg}"
        
        data = response.json()
        if data.get("choices") and len(data["choices"]) > 0:
            sugerencia = data["choices"][0]["message"]["content"]
            print("Sugerencia recibida de OpenRouter.")
            
            # Guardar en caché
            openrouter_cache[numeros_recientes_str] = sugerencia.strip()
            
            # Limitar el tamaño del caché
            if len(openrouter_cache) > openrouter_cache_max_size:
                oldest_key = next(iter(openrouter_cache))
                del openrouter_cache[oldest_key]
                
            return openrouter_cache[numeros_recientes_str]
        else:
            error_msg = f"Respuesta no esperada de OpenRouter: {data}"
            print(error_msg)
            return f"Error al procesar respuesta de IA: {error_msg}"
            
    except requests.exceptions.Timeout:
        error_msg = "Tiempo de espera agotado al contactar el servicio de IA"
        print(error_msg)
        return error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión con el servicio de IA: {str(e)}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error inesperado al procesar sugerencias de IA: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return error_msg

def obtener_numeros_frecuentes(historial_numeros, cantidad):
    """
    Obtiene los números más frecuentes del historial.
    Args:
        historial_numeros: Lista de objetos NumeroRoleta o lista de enteros
        cantidad: Cantidad de números más frecuentes a retornar
    Returns:
        dict: Diccionario con los números más frecuentes y sus frecuencias
    """
    # Hacemos una copia profunda para evitar modificar datos originales
    # Convertir el historial a una lista de números enteros si son objetos NumeroRoleta
    numeros = []
    if historial_numeros and hasattr(historial_numeros[0], 'numero'):
        numeros = [n.numero for n in historial_numeros]
    else:
        # Hacemos una copia para evitar trabajar con la referencia original
        numeros = list(historial_numeros)

    # Contar frecuencias
    frecuencias = {}
    for num in numeros:
        frecuencias[num] = frecuencias.get(num, 0) + 1
    
    # Ordenar por frecuencia (descendente) y luego por número (ascendente)
    numeros_ordenados = sorted(frecuencias.items(), key=lambda x: (-x[1], x[0]))
    
    # Tomar los primeros 'cantidad' números
    top_numeros = numeros_ordenados[:cantidad]
    
    return {
        'numeros': [num for num, _ in top_numeros],
        'frecuencias': [freq for _, freq in top_numeros]
    }

def convert_to_serializable(obj):
    """Convierte objetos de NumPy y otros tipos no serializables a tipos Python nativos."""
    if isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, '__dict__'):
        return convert_to_serializable(obj.__dict__)
    return obj

def guardar_prediccion(session_id, grupo_20, color_predicho):
    """Guarda una nueva predicción en Supabase."""
    try:
        data = {
            "grupo_20": grupo_20,
            "color_predicho": color_predicho,
            "session_id": session_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        response = supabase_client.table("predicciones").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error al guardar predicción: {e}")
        return None

def guardar_numero_jugado(session_id, numero, color):
    """Guarda un nuevo número jugado en el historial."""
    try:
        data = {
            "numero": numero,
            "color": color,
            "session_id": session_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        response = supabase_client.table("historial_numeros").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error al guardar número jugado: {e}")
        return None

def obtener_ultima_prediccion(session_id):
    """Obtiene la última predicción para la sesión."""
    try:
        response = (supabase_client.table("predicciones")
                   .select("*")
                   .eq("session_id", session_id)
                   .order("created_at", desc=True)
                   .limit(1)
                   .execute())
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error al obtener última predicción: {e}")
        return None

def guardar_resultado_apuesta(session_id, numero_jugado, color_jugado, prediccion_id, acierto_numero, acierto_color):
    """Guarda el resultado de una apuesta."""
    try:
        data = {
            "numero_jugado": numero_jugado,
            "color_jugado": color_jugado,
            "prediccion_id": prediccion_id,
            "acierto_numero": acierto_numero,
            "acierto_color": acierto_color,
            "session_id": session_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        response = supabase_client.table("resultados_apuestas").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error al guardar resultado: {e}")
        return None

@app.route('/analizar', methods=['POST', 'OPTIONS'])
def analizar_numeros():
    if request.method == "OPTIONS":
        return make_response()

    session_id = request.headers.get('Authorization', str(uuid.uuid4()))

    try:
        # Validar y obtener datos de entrada
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "No se recibieron datos JSON", 
                "status": "error",
                "session_id": session_id
            }), 400

        # Obtener números de entrada
        numeros_str = data.get('numeros', '') or data.get('numeros_str', '') or str(data.get('nuevo_numero', ''))
        
        if not numeros_str.strip():
            return jsonify({
                "error": "No se proporcionaron números para analizar", 
                "status": "error",
                "session_id": session_id
            }), 400

        # Procesar apuesta individual si existe
        es_apuesta_individual, numero_apostado = procesar_apuesta_individual(numeros_str)

        # Evaluar predicciones previas si tenemos un número individual
        if es_apuesta_individual and numero_apostado is not None:
            evaluacion_resultado = evaluar_predicciones_previas(numero_apostado)
            if evaluacion_resultado:
                print("✅ Predicciones previas evaluadas exitosamente")

        # Resetear historial si se solicita
        if data.get('resetear', False):
            analizador.limpiar_historial()
            print("Historial limpiado por solicitud del usuario.")
        
        # Cargar y validar números
        print(f"Procesando números: {numeros_str}")
        analizador.cargar_numeros_desde_string(numeros_str)
        
        if len(analizador.historial_numeros) == 0:
            return jsonify({
                "error": "No se pudieron procesar los números proporcionados.",
                "status": "error",
                "session_id": session_id
            }), 400

        # Entrenar modelos ML si hay suficientes datos
        if len(analizador.historial_numeros) >= 10:
            try:
                # Priorizar el Advanced ML Predictor
                if advanced_ml_predictor:
                    # Cargar historial extendido para entrenamiento ML avanzado
                    extended_history = load_extended_history_for_ml()
                    
                    # Convertir objetos NumeroRoleta a enteros si es necesario
                    history_numbers = []
                    if extended_history:
                        for num in extended_history:
                            if hasattr(num, 'numero'):
                                history_numbers.append(num.numero)
                            else:
                                history_numbers.append(num)
                    else:
                        # Usar historial actual si no hay extendido
                        for num in analizador.historial_numeros:
                            if hasattr(num, 'numero'):
                                history_numbers.append(num.numero)
                            else:
                                history_numbers.append(num)
                    
                    # Entrenar el sistema avanzado
                    if len(history_numbers) >= 30:
                        print(f"🚀 Entrenando sistema ML avanzado con {len(history_numbers)} números")
                        success = advanced_ml_predictor.train_models(history_numbers)
                        if success:
                            print("✅ Sistema ML avanzado entrenado con éxito")
                        else:
                            print("⚠️ Entrenamiento del sistema avanzado falló, usando sistema básico")
                    else:
                        print("⚠️ Datos insuficientes para sistema avanzado, usando sistema básico")
                
                # Entrenar sistema básico como respaldo
                if ml_predictor:
                    extended_history = load_extended_history_for_ml()
                    
                    if len(extended_history) >= 50:
                        print(f"Entrenando modelos ML básicos con historial extendido de {len(extended_history)} números")
                        ml_predictor.entrenar_todos(extended_history)
                    else:
                        print("Usando historial actual para entrenar modelos ML básicos")
                        ml_predictor.entrenar_todos(analizador.historial_numeros)
                        
                    print("Modelos ML básicos entrenados con éxito")
                else:
                    print("ML Predictor básico no disponible.")
                    
            except Exception as e:
                print(f"Error al entrenar modelos ML: {e}")
                traceback.print_exc()

        # Generar análisis y predicciones
        try:
            resultado = generar_analisis_completo(analizador, ml_predictor)
        except Exception as e:
            print(f"Error al generar análisis: {e}")
            traceback.print_exc()
            resultado = {
                "error": "Error al generar análisis",
                "informe": "No disponible",
                "predicciones_ml": {},
                "datos_graficos": {"error": "No fue posible generar los datos para gráficos."}
            }

        # Guardar datos en Supabase con verificación
        try:
            if supabase_client and GUARDAR_HISTORIAL_SUPABASE:
                print("💾 Guardando datos en Supabase...")
                
                # Guardar historial y verificar éxito
                history_id = save_history_to_supabase(numeros_str)
                if history_id:
                    print(f"✅ Historial guardado exitosamente con ID: {history_id}")
                else:
                    print("⚠️ Fallo al guardar historial, pero continuando...")
                
                # Guardar estado del analizador
                save_analyzer_state_to_supabase()
                
                # Forzar una sincronización rápida para verificar consistencia
                print("🔄 Verificando sincronización...")
                sync_result = sincronizar_datos_con_verificacion()
                if sync_result["success"]:
                    print("✅ Sincronización verificada")
                else:
                    print(f"⚠️ Advertencia en sincronización: {sync_result.get('error', 'Error desconocido')}")
                    
        except Exception as e:
            print(f"Error al guardar datos en Supabase: {e}")
            traceback.print_exc()

        # Almacenar las predicciones generadas para la próxima evaluación
        global ultima_prediccion_generada
        ultima_prediccion_generada = {
            'individual': resultado.get('predicciones_ml', {}).get('ensemble', 0),
            'grupo_5': resultado.get('grupos_prediccion', {}).get('grupo_5', []),
            'grupo_10': resultado.get('grupos_prediccion', {}).get('grupo_10', []),
            'grupo_12': resultado.get('grupos_prediccion', {}).get('grupo_12', []),
            'grupo_15': resultado.get('grupos_prediccion', {}).get('grupo_15', []),
            'grupo_20': resultado.get('grupos_prediccion', {}).get('grupo_20', []),
            'ml_predictions': resultado.get('predicciones_ml', {}),
            'grupos_prediccion': resultado.get('grupos_prediccion', {}),
            'strategy_predictions': resultado.get('ml_predictions', {}).get('advanced_data', {}).get('strategy_predictions', {}),
            'sector_predictions': resultado.get('ml_predictions', {}).get('advanced_data', {}).get('sector_predictions', {})
        }

        # Preparar respuesta
        response_data = {
            "status": "success",
            "message": "Análisis completado correctamente",
            "session_id": session_id,
            **resultado
        }
        
        # Añadir estadísticas de evaluación si están disponibles
        if prediction_evaluator:
            try:
                group_stats = prediction_evaluator.get_group_statistics()
                response_data["estadisticas_evaluacion"] = group_stats
            except Exception as e:
                print(f"Error al obtener estadísticas de evaluación: {e}")
        
        return jsonify(response_data), 200

    except Exception as e:
        print(f"Error en /analizar: {e}")
        traceback.print_exc()
        return jsonify({
            "error": str(e), 
            "status": "error",
            "session_id": session_id
        }), 500

def check_consecutive_duplicate(number: int, recent_numbers: list) -> dict:
    """
    Verifica si un número es un duplicado consecutivo sospechoso.
    MEJORADO CON VALIDACIÓN REFORZADA para evitar duplicados accidentales.
    
    Args:
        number: Número a verificar
        recent_numbers: Lista de números recientes (más reciente primero)
    
    Returns:
        dict: {"is_duplicate": bool, "message": str}
    """
    if not recent_numbers:
        return {"is_duplicate": False, "message": ""}
    
    # VALIDACIÓN 1: Duplicado inmediato (último número igual)
    if recent_numbers[0] == number:
        return {
            "is_duplicate": True,
            "message": f"El número {number} se repite inmediatamente después del último número. ¿Está seguro de que es correcto? Esto es inusual en ruleta."
        }
    
    # VALIDACIÓN 2: Número aparece 2 o más veces en los últimos 3 números
    if len(recent_numbers) >= 2:
        last_three = recent_numbers[:3]
        if last_three.count(number) >= 1:  # Ya aparece en los últimos 3
            return {
                "is_duplicate": True,
                "message": f"El número {number} ya apareció recientemente en los últimos números (posición: {last_three.index(number) + 1}). ¿Está seguro?"
            }
    
    # VALIDACIÓN 3: Detectar patrones sospechosos (mismo número aparece frecuentemente)
    if len(recent_numbers) >= 4:
        last_five = recent_numbers[:5] if len(recent_numbers) >= 5 else recent_numbers
        count_in_recent = last_five.count(number)
        if count_in_recent >= 2:
            return {
                "is_duplicate": True,
                "message": f"El número {number} ya apareció {count_in_recent} veces en los últimos {len(last_five)} números. Esto es estadísticamente inusual."
            }
    
    # No es duplicado problemático
    return {"is_duplicate": False, "message": ""}

def procesar_apuesta_individual(numeros_str: str) -> tuple[bool, int | None]:
    """Procesa una posible apuesta individual."""
    try:
        partes = [p.strip() for p in numeros_str.split(',') if p.strip()]
        if len(partes) == 1 and partes[0].isdigit():
            num_temp = int(partes[0])
            if 0 <= num_temp <= 36:
                print(f"Detectada apuesta individual para el número: {num_temp}")
                return True, num_temp
    except ValueError as e:
        print(f"Error al procesar número: {e}")
    return False, None

def evaluar_predicciones_previas(numero_actual):
    """
    Evalúa las predicciones previas contra el número que acaba de salir
    """
    global prediction_evaluator, ultima_prediccion_generada, victory_trainer
    
    if not prediction_evaluator or not 'ultima_prediccion_generada' in globals():
        print("⚠️ No hay predicciones previas para evaluar")
        return None
    
    try:
        print(f"🔍 Evaluando predicciones previas contra el número: {numero_actual}")
        
        # Obtener las últimas predicciones generadas
        predicciones_a_evaluar = ultima_prediccion_generada.copy()
        
        # Asegurar que tenemos los grupos necesarios
        if 'grupo_12' not in predicciones_a_evaluar and 'grupos_prediccion' in predicciones_a_evaluar:
            grupos = predicciones_a_evaluar['grupos_prediccion']
            if 'grupo_10' in grupos and len(grupos['grupo_10']) >= 10:
                # Crear grupo_12 extendiendo grupo_10 con números adicionales
                grupo_12 = list(grupos['grupo_10'])
                if 'grupo_20' in grupos:
                    for num in grupos['grupo_20']:
                        if num not in grupo_12 and len(grupo_12) < 12:
                            grupo_12.append(num)
                predicciones_a_evaluar['grupo_12'] = grupo_12
        
        # Evaluar predicciones
        resultado_evaluacion = prediction_evaluator.evaluate_prediction(
            predicciones_a_evaluar, 
            numero_actual
        )
        
        # NUEVO: Registrar victorias en el Victory Trainer
        if victory_trainer and resultado_evaluacion['summary']['hits'] > 0:
            # Obtener números del contexto (historial actual)
            context_numbers = []
            if len(analizador.historial_numeros) > 1:
                # Usar los números anteriores al actual (excluyendo el que acabamos de añadir)
                context_numbers = [n.numero if hasattr(n, 'numero') else n 
                                 for n in analizador.historial_numeros[1:16]]  # Últimos 15 números de contexto
            
            # Registrar la victoria
            victory_recorded = victory_trainer.record_victory(
                prediction_data=predicciones_a_evaluar,
                actual_number=numero_actual,
                context_numbers=context_numbers
            )
            
            if victory_recorded:
                print("🎯 Victoria registrada en Victory Trainer")
            else:
                print("ℹ️ No se registró como victoria en Victory Trainer")
        
        # Mostrar resultado detallado
        summary = resultado_evaluacion['summary']
        print(f"📊 Resultado de evaluación:")
        print(f"   Total predicciones: {summary['total_predictions']}")
        print(f"   Aciertos: {summary['hits']}")
        print(f"   Fallos: {summary['misses']}")
        print(f"   Tasa de aciertos: {summary['hit_rate']:.1f}%")
        
        if summary['best_performers']:
            print(f"   🎯 Mejores predictores: {', '.join(summary['best_performers'])}")
        
        # Mostrar rendimiento por grupos
        for grupo, acerto in summary['group_performance'].items():
            estado = "✅ ACERTÓ" if acerto else "❌ FALLÓ"
            print(f"   {grupo}: {estado}")
        
        return resultado_evaluacion
        
    except Exception as e:
        print(f"❌ Error al evaluar predicciones: {e}")
        traceback.print_exc()
        return None

# Variable global para almacenar la última predicción
ultima_prediccion_generada = {}

def calcular_patrones_puxa_ultra(historial_numeros, top_n=5):
    """
    Calcula qué números suelen salir después de cada número específico.
    
    Args:
        historial_numeros: Lista de números de la ruleta o objetos NumeroRoleta (más reciente primero)
        top_n: Número de resultados a devolver para cada número
        
    Returns:
        Un diccionario donde las claves son los números (0-36) y los valores son listas
        de los números que aparecen con más frecuencia después de ese número específico.
    """
    # Convertir a lista de enteros si son objetos NumeroRoleta
    numeros_limpios = []
    for num in historial_numeros:
        if hasattr(num, 'numero'):
            numeros_limpios.append(num.numero)
        else:
            numeros_limpios.append(num)
    
    # Invertir para tener orden cronológico
    historial_cronologico = list(reversed(numeros_limpios))
    
    # Inicializar el diccionario de seguimiento
    patrones = {str(num): {} for num in range(37)}  # Usar strings como claves para serialización JSON
    
    # Analizar secuencias en el historial
    for i in range(len(historial_cronologico) - 1):
        numero_actual = historial_cronologico[i]
        siguiente_numero = historial_cronologico[i + 1]
        
        # Formato string para claves
        num_str = str(numero_actual)
        sig_num_str = str(siguiente_numero)
        
        # Incrementar contador para este patrón
        if sig_num_str not in patrones[num_str]:
            patrones[num_str][sig_num_str] = 0
        patrones[num_str][sig_num_str] += 1
    
    # Convertir a formato de resultado
    resultado = {}
    for num_str, frecuencias in patrones.items():
        if not frecuencias:  # Si no hay datos para este número
            resultado[num_str] = []
            continue
            
        # Ordenar por frecuencia y obtener los top_n
        nums_ordenados = sorted(
            [(int(sig_num), freq) for sig_num, freq in frecuencias.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Tomar los top_n números más frecuentes
        resultado[num_str] = [num for num, _ in nums_ordenados[:top_n]]
    
    return resultado

def generar_analisis_completo(analizador, ml_predictor):
    """Genera el análisis completo incluyendo predicciones avanzadas y datos gráficos."""
    informe = analizador.generar_informe_completo()
    
    try:
        datos_graficos = obtener_datos_para_graficos()
    except Exception as e:
        print(f"Error al generar datos para gráficos: {e}")
        datos_graficos = {"error": "No fue posible generar los datos para gráficos."}
    
    predicciones_ml = {}
    predicciones_avanzadas = {}
    
    if len(analizador.historial_numeros) >= 10:
        # Convertir historial a números enteros
        history_numbers = []
        for num in analizador.historial_numeros:
            if hasattr(num, 'numero'):
                history_numbers.append(num.numero)
            else:
                history_numbers.append(num)
        
        # Priorizar predicciones avanzadas
        try:
            if advanced_ml_predictor and advanced_ml_predictor.is_trained:
                print("🎯 Generando predicciones con sistema ML avanzado...")
                predicciones_avanzadas = advanced_ml_predictor.predict_advanced(history_numbers)
                
                # Convertir a formato compatible
                if predicciones_avanzadas:
                    predicciones_ml = {
                        "ensemble": predicciones_avanzadas.get('individual', 0),
                        "advanced_hybrid": predicciones_avanzadas.get('individual', 0),
                        "sector_based": predicciones_avanzadas.get('grupo_5', [0])[0] if predicciones_avanzadas.get('grupo_5') else 0,
                        "strategy_based": predicciones_avanzadas.get('grupo_10', [0])[0] if predicciones_avanzadas.get('grupo_10') else 0,
                        "grupos": {
                            "grupo_20": predicciones_avanzadas.get('grupo_20', list(range(20))),
                            "grupo_15": predicciones_avanzadas.get('grupo_15', list(range(15))),
                            "grupo_10": predicciones_avanzadas.get('grupo_10', list(range(10))),
                            "grupo_8": predicciones_avanzadas.get('grupo_10', list(range(10)))[:8],
                            "grupo_6": predicciones_avanzadas.get('grupo_10', list(range(10)))[:6],
                            "grupo_5": predicciones_avanzadas.get('grupo_5', list(range(5))),
                            "grupo_4": predicciones_avanzadas.get('grupo_5', list(range(5)))[:4]
                        },
                        "advanced_data": {
                            "ml_predictions": predicciones_avanzadas.get('ml_predictions', {}),
                            "sector_predictions": predicciones_avanzadas.get('sector_predictions', {}),
                            "strategy_predictions": predicciones_avanzadas.get('strategy_predictions', {}),
                            "temporal_predictions": predicciones_avanzadas.get('temporal_predictions', {}),
                            "confidence_scores": predicciones_avanzadas.get('confidence_scores', {}),
                            "hybrid_weights": predicciones_avanzadas.get('hybrid_weights', {})
                        }
                    }
                    print("✅ Predicciones avanzadas generadas exitosamente")
            else:
                    print("⚠️ Predicciones avanzadas vacías, usando sistema básico")
            else:
                print("⚠️ Sistema ML avanzado no disponible o no entrenado")
        except Exception as e:
            print(f"Error al generar predicciones avanzadas: {e}")
            traceback.print_exc()
        
        # Sistema básico como respaldo
        if not predicciones_ml and ml_predictor:
            try:
                print("🔄 Usando sistema ML básico como respaldo...")
                predicciones_ml = ml_predictor.predecir(analizador.historial_numeros)
                print("✅ Predicciones básicas generadas")
            except Exception as e:
                print(f"Error al generar predicciones ML básicas: {e}")
                traceback.print_exc()
        
        # Respaldo final con números aleatorios inteligentes
        if not predicciones_ml:
            print("🎲 Generando predicciones de respaldo...")
            # Usar análisis de frecuencia como respaldo inteligente
            counter = Counter(history_numbers[-50:])  # Últimos 50 números
            most_common = [num for num, _ in counter.most_common(20)]
            
            # Completar con números faltantes
            remaining = [i for i in range(37) if i not in most_common]
            most_common.extend(remaining[:20-len(most_common)])
            
            predicciones_ml = {
                "ensemble": most_common[0] if most_common else random.randint(0, 36),
                "frequency_based": most_common[1] if len(most_common) > 1 else random.randint(0, 36),
                "random_forest": most_common[2] if len(most_common) > 2 else random.randint(0, 36),
                "grupos": {
                    "grupo_20": most_common[:20],
                    "grupo_12": most_common[:12],
                    "grupo_8": most_common[:8],
                    "grupo_6": most_common[:6],
                    "grupo_4": most_common[:4]
                }
            }
    else:
        # Si no hay suficientes datos, proporcionar estructura de respaldo
        predicciones_ml = {
            "ensemble": random.randint(0, 36),
            "random_forest": random.randint(0, 36),
            "markov": random.randint(0, 36),
            "grupos": {
                "grupo_20": [random.randint(0, 36) for _ in range(20)],
                "grupo_12": [random.randint(0, 36) for _ in range(12)],
                "grupo_8": [random.randint(0, 36) for _ in range(8)],
                "grupo_6": [random.randint(0, 36) for _ in range(6)],
                "grupo_4": [random.randint(0, 36) for _ in range(4)]
            }
        }
    
    # Generar grupos de predicción basados en frecuencias (esto es diferente de las predicciones ML)
    grupos_prediccion = generar_grupos_prediccion(analizador.historial_numeros)
    
    # Obtener predicción de color
    prediccion_color = analizador.predecir_color()
    color_predicho = prediccion_color.get("color", "Negro")
    
    # Generar datos para sectores_stats
    sectores_stats = []
    if hasattr(analizador, 'sectores_personalizados_definiciones') and analizador.sectores_personalizados_definiciones:
        for nombre_sector, numeros in analizador.sectores_personalizados_definiciones.items():
            conteo = analizador.conteo_sectores_personalizados.get(nombre_sector, 0)
            total_numeros = len(analizador.historial_numeros) or 1  # Evitar división por cero
            porcentaje = round((conteo / total_numeros) * 100, 1)
            
            sectores_stats.append({
                "title": nombre_sector,
                "numbers": list(numeros),
                "appearance": conteo,
                "historyPercentage": porcentaje
            })
            
    # Añadir sectores detectados automáticamente si hay suficientes datos
    try:
        if len(analizador.historial_numeros) >= 20:
            sectores_auto = detectar_sectores_populares(analizador.historial_numeros)
            if sectores_auto:
                sectores_stats.extend(sectores_auto)
                print(f"Se detectaron {len(sectores_auto)} sectores automáticamente")
    except Exception as e:
        print(f"Error al detectar sectores automáticos: {e}")
    
    # Generar datos para estrategias_stats
    estrategias_stats = [
        {"name": "Estrategia Tía Lu", "probability": calcular_probabilidad_tia_lu(analizador)},
        {"name": "Vecinos del Cero", "probability": calcular_probabilidad_vecinos_cero(analizador)},
        {"name": "Tercios del Cilindro", "probability": calcular_probabilidad_tercios(analizador)},
        {"name": "Orphelins", "probability": calcular_probabilidad_orphelins(analizador)}
    ]
    
    # Generar estadísticas de docenas
    tendencias = analizador.analizar_tendencias()
    docenas_stats = []
    for docena, valor in tendencias.get("duzias", {}).items():
        total = len(analizador.historial_numeros) or 1
        porcentaje = round((valor / total) * 100, 1)
        docenas_stats.append({
            "name": docena,
            "value": valor,
            "percentage": porcentaje
        })
        
    # Generar estadísticas de columnas
    columnas_stats = []
    for columna, valor in tendencias.get("colunas", {}).items():
        total = len(analizador.historial_numeros) or 1
        porcentaje = round((valor / total) * 100, 1)
        columnas_stats.append({
            "name": columna,
            "value": valor,
            "percentage": porcentaje
        })
    
    # Generar estadísticas de color
    color_stats = []
    conteo_color = analizador.conteo_color
    total = len(analizador.historial_numeros) or 1
    for color, valor in conteo_color.items():
        porcentaje = round((valor / total) * 100, 1)
        color_stats.append({
            "name": color,
            "value": valor,
            "percentage": porcentaje
        })
    
    # Obtener terminales
    terminales_stats = analizador.obtener_datos_para_graficos().get("frecuencia_terminales", {}).get("data", [0] * 10)
    
    # Calcular patrones Puxa Ultra (números que suelen salir después de cada número)
    try:
        # Extraer solo los números enteros para evitar problemas con objetos completos
        numeros_enteros = [n.numero if hasattr(n, 'numero') else n for n in analizador.historial_numeros]
        puxa_ultra = calcular_patrones_puxa_ultra(numeros_enteros)
    except Exception as e:
        print(f"Error al calcular patrones Puxa Ultra: {e}")
        puxa_ultra = {}
    
    return {
        "informe": informe,
        "predicciones_ml": convert_to_serializable(predicciones_ml),
        "ml_predictions": convert_to_serializable(predicciones_ml),  # Duplicado para mantener compatibilidad
        "datos_graficos": convert_to_serializable(datos_graficos),
        "ultimo_numero": analizador.historial_numeros[0].numero if analizador.historial_numeros else None,
        "grupos_prediccion": convert_to_serializable(grupos_prediccion),
        "resultado_apuesta": None,
        "mensaje_resultado": "Procesando nueva jugada...",
        "sectores_stats": sectores_stats,
        "estrategias_stats": estrategias_stats,
        "docenas_stats": docenas_stats,
        "columnas_stats": columnas_stats,
        "color_stats": color_stats,
        "terminales_stats": terminales_stats,
        "puxa_ultra": puxa_ultra  # Añadir la información Puxa Ultra
    }

# Funciones auxiliares para calcular probabilidades de estrategias
def calcular_probabilidad_tia_lu(analizador):
    """Calcula la probabilidad de éxito para la estrategia Tía Lu"""
    # Verificar si hay suficientes datos para hacer una predicción significativa
    if len(analizador.historial_numeros) < 5:
        return 50  # Valor por defecto si hay pocos datos
        
    # Obtener historial de números
    numeros = [n.numero for n in analizador.historial_numeros]
    
    # Obtener datos detallados de la estrategia
    datos = obtener_datos_estrategia_tia_lu(numeros)
    
    # Si hay secuencias activas, usar la efectividad calculada
    if datos['data'][2] > 0:  # Secuencias activas
        return datos['data'][3]  # Efectividad en porcentaje
    
    # Verificar si alguno de los números desencadenantes apareció recientemente (últimos 3 números)
    numeros_recientes = numeros[:3]
    for num in datos['numeros_desencadenantes']:
        if num in numeros_recientes:
            # Número desencadenante reciente, probabilidad alta
            return 75
    
    # Historial suficiente pero sin activaciones recientes
    if analizador.total_predicciones_evaluadas > 0:
        # Usar el historial de aciertos si está disponible
        return round((analizador.aciertos_tia_lu / max(1, analizador.total_predicciones_evaluadas)) * 100)
    
    # Sin datos significativos, usar un valor predeterminado basado en estadísticas
    return 55  # Valor ligeramente optimista basado en experiencia

def calcular_probabilidad_vecinos_cero(analizador):
    """Calcula la probabilidad de éxito para la estrategia de Vecinos del Cero"""
    if analizador.total_predicciones_evaluadas == 0:
        return 45  # Valor por defecto
    return round((analizador.aciertos_vecinos_0_10 / max(1, analizador.total_predicciones_evaluadas)) * 100)

def calcular_probabilidad_tercios(analizador):
    """Calcula la probabilidad para la estrategia de Tercios del Cilindro"""
    # Para este ejemplo usamos un valor derivado de los datos disponibles
    return 40  # Valor simplificado para demostración

def calcular_probabilidad_orphelins(analizador):
    """Calcula la probabilidad para la estrategia de Orphelins"""
    # Valor de ejemplo
    return 35  # Valor simplificado para demostración

def generar_grupos_prediccion(historial_numeros):
    """Genera los grupos de predicción basados en frecuencias."""
    if not historial_numeros:
        return {
            "grupo_20": [0] + list(range(1, 20)),
            "grupo_10": [0] + list(range(1, 10)),
            "grupo_8": [0] + list(range(1, 8))
        }

    # Creamos una copia del historial para evitar modificaciones no deseadas
    historial_copia = list(historial_numeros) if isinstance(historial_numeros, list) else [n for n in historial_numeros]
    
    datos_frec_20 = obtener_numeros_frecuentes(historial_copia, 20)
    datos_frec_10 = obtener_numeros_frecuentes(historial_copia, 10)
    datos_frec_8 = obtener_numeros_frecuentes(historial_copia, 8)
    
    # Obtener los grupos base
    grupo_20 = datos_frec_20['numeros']
    grupo_10 = datos_frec_10['numeros']
    grupo_8 = datos_frec_8['numeros']
    
    # NUEVO: Agregar 0 como protección en todos los grupos (si no está ya incluido)
    if 0 not in grupo_20:
        grupo_20 = [0] + grupo_20[:19]  # Mantener 20 números incluyendo el 0
    if 0 not in grupo_10:
        grupo_10 = [0] + grupo_10[:9]   # Mantener 10 números incluyendo el 0
    if 0 not in grupo_8:
        grupo_8 = [0] + grupo_8[:7]     # Mantener 8 números incluyendo el 0

    return {
        "grupo_20": grupo_20,
        "grupo_10": grupo_10,
        "grupo_8": grupo_8
    }

# Mejorar el encoder JSON para manejar tipos de NumPy
class EnhancedJSONEncoder(NumpyJSONEncoder):
    def default(self, obj):
        try:
            if hasattr(obj, 'dtype'):
                if np.issubdtype(obj.dtype, np.floating):
                    return float(obj)
                elif np.issubdtype(obj.dtype, np.integer):
                    return int(obj)
            return super().default(obj)
        except:
            return str(obj)  # Fallback seguro

# Actualizar el encoder de la aplicación
app.json_encoder = EnhancedJSONEncoder

def obtener_datos_vecinos(historial_numeros, numero_central, rango=3):
    """
    Obtiene estadísticas de los vecinos de un número en la ruleta.
    Args:
        historial_numeros: Lista de números jugados
        numero_central: Número del cual queremos analizar los vecinos
        rango: Cantidad de números a cada lado para considerar vecinos
    Returns:
        dict: Estadísticas de los vecinos
    """
    # Definir la secuencia de la ruleta europea
    ruleta = RUEDA_EUROPEA
    
    # Encontrar la posición del número central
    pos_central = ruleta.index(numero_central)
    
    # Obtener los vecinos (considerando la naturaleza circular de la ruleta)
    vecinos = []
    for i in range(-rango, rango + 1):
        pos = (pos_central + i) % len(ruleta)
        vecinos.append(ruleta[pos])
    
    # Contar apariciones de los vecinos en el historial
    conteo = {num: 0 for num in vecinos}
    for num in historial_numeros:
        if isinstance(num, int) and num in conteo:
            conteo[num] += 1
    
    # Preparar datos para el gráfico
    return {
        'labels': [str(num) for num in vecinos],
        'data': [conteo[num] for num in vecinos]
    }

def obtener_datos_estrategia_tia_lu(historial_numeros):
    """
    Obtiene estadísticas de la estrategia Tía Lu basada en los números 33, 22 y 11.
    Cuando aparece alguno de estos números desencadenantes, se activa la estrategia
    y se apuesta a un conjunto específico de números.
    Returns:
        dict: Estadísticas de la estrategia
    """
    # Números desencadenantes de la estrategia (según las imágenes)
    numeros_desencadenantes = [33, 22, 11]
    
    # Números a los que apostar cuando se activa la estrategia
    numeros_apuesta = [16, 33, 1, 9, 22, 18, 26, 0, 32, 30, 11, 36]
    
    # Contar apariciones y resultados
    total_desencadenantes = 0
    aciertos = 0
    secuencias_activas = 0
    ultimo_desencadenante = None
    secuencia_actual = False
    apariciones_por_numero = {num: 0 for num in numeros_desencadenantes}
    
    # Analizar el historial para detectar patrones de la estrategia
    for i, num in enumerate(historial_numeros):
        # Registrar apariciones de cada número desencadenante
        if num in numeros_desencadenantes:
            apariciones_por_numero[num] += 1
            total_desencadenantes += 1
            ultimo_desencadenante = num
            
            # Si ya estaba en una secuencia, contar como acierto
            if secuencia_actual:
                aciertos += 1
            
            # Iniciar nueva secuencia
            secuencia_actual = True
            secuencias_activas += 1
        
        # Si estamos en una secuencia activa, verificar si el siguiente número está en la lista de apuesta
        elif secuencia_actual and num in numeros_apuesta:
            aciertos += 1
            # La secuencia continúa
        else:
            # Reiniciar secuencia si el número no está en la lista de apuesta
            secuencia_actual = False
    
    # Calcular efectividad si hay datos suficientes
    efectividad = round((aciertos / max(1, secuencias_activas)) * 100)
    
    return {
        'labels': ['Total Activaciones', 'Aciertos', 'Secuencias Activas', 'Efectividad (%)'],
        'data': [total_desencadenantes, aciertos, secuencias_activas, efectividad],
        'numeros_desencadenantes': numeros_desencadenantes,
        'numeros_apuesta': numeros_apuesta,
        'apariciones_por_numero': [
            {'numero': 33, 'apariciones': apariciones_por_numero.get(33, 0)},
            {'numero': 22, 'apariciones': apariciones_por_numero.get(22, 0)},
            {'numero': 11, 'apariciones': apariciones_por_numero.get(11, 0)}
        ],
        'ultimo_desencadenante': ultimo_desencadenante
    }

def obtener_datos_para_graficos():
    """
    Genera todos los datos necesarios para los gráficos del frontend.
    Returns:
        dict: Datos para todos los gráficos
    """
    numeros = [n.numero for n in analizador.historial_numeros]
    
    # Datos existentes
    datos = analizador.obtener_datos_para_graficos()
    
    # Agregar nuevas estadísticas
    datos['vecinos'] = {
        'vecinos_5': obtener_datos_vecinos(numeros, 5),
        'vecinos_7_27': obtener_datos_vecinos(numeros, 7, 2),  # Rango más pequeño para este grupo
        'vecinos_31': obtener_datos_vecinos(numeros, 31),
        'vecinos_34': obtener_datos_vecinos(numeros, 34),
        'vecinos_0': obtener_datos_vecinos(numeros, 0),
        'vecinos_2': obtener_datos_vecinos(numeros, 2)
    }
    
    # Agregar estadísticas de la estrategia Tía Lu
    datos['estrategia_tia_lu'] = obtener_datos_estrategia_tia_lu(numeros)
    
    return datos

def setup_database_tables():
    """Configura las tablas necesarias en Supabase si no existen."""
    if not supabase_client:
        print("Cliente de Supabase no disponible, no se pueden configurar las tablas.")
        return

    try:
        # Crear tabla predicciones si no existe
        supabase_client.table("predicciones").select("id").limit(1).execute()
    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
            print("Creando tabla predicciones...")
            supabase_client.postgrest.rpc('create_predicciones_table').execute()

    try:
        # Crear tabla historial_numeros si no existe
        supabase_client.table("historial_numeros").select("id").limit(1).execute()
    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
            print("Creando tabla historial_numeros...")
            supabase_client.postgrest.rpc('create_historial_numeros_table').execute()

    try:
        # Crear tabla resultados_apuestas si no existe
        supabase_client.table("resultados_apuestas").select("id").limit(1).execute()
    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
            print("Creando tabla resultados_apuestas...")
            supabase_client.postgrest.rpc('create_resultados_apuestas_table').execute()

# Llamar a la función de configuración al inicio
if supabase_client:
    setup_database_tables()

@app.route('/reconocer-voz', methods=['POST', 'OPTIONS'])
def reconocer_voz():
    """Endpoint para reconocer voz usando Google Speech-to-Text o simular el reconocimiento."""
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        data = request.get_json() or {}
        comando = data.get('comando', '')
        texto_directo = data.get('text', '')  # Para inserción directa de texto/números
        force_insert = data.get('force_insert', False)  # Para forzar inserción ignorando validaciones
        
        # Si tenemos texto directo (para inserción forzada), procesarlo directamente
        if texto_directo:
            print(f"Procesando texto directo: '{texto_directo}' (force_insert: {force_insert})")
            
            # Extraer números del texto
            numeros_extraidos = []
            if ',' in texto_directo:
                # Múltiples números separados por coma
                numeros_str_list = [n.strip() for n in texto_directo.split(',') if n.strip()]
                for num_str in numeros_str_list:
                    try:
                        num = int(num_str)
                        if 0 <= num <= 36:
                            numeros_extraidos.append(num)
                    except ValueError:
                        continue
            else:
                # Un solo número
                try:
                    num = int(texto_directo.strip())
                    if 0 <= num <= 36:
                        numeros_extraidos.append(num)
                except ValueError:
                    pass
            
            if numeros_extraidos:
                # Si force_insert es True, no hacer validación de duplicados
                if not force_insert:
                    # Verificar duplicados consecutivos para el primer número
                    primer_numero = numeros_extraidos[0]
                    try:
                        response = (
                            supabase_client.table(NUMEROS_INDIVIDUALES_TABLE_NAME)
                            .select("number_value")
                            .order("id", desc=True)
                            .limit(5)
                            .execute()
                        )
                        
                        if response.data:
                            ultimos_numeros = [entry['number_value'] for entry in response.data]
                            duplicate_check = check_consecutive_duplicate(primer_numero, ultimos_numeros)
                            
                            if duplicate_check["is_duplicate"]:
                                return jsonify({
                                    "texto_reconocido": f"Número {primer_numero}: {duplicate_check['message']}",
                                    "numero_reconocido": primer_numero,
                                    "confianza": 1.0,
                                    "modo": "texto_directo",
                                    "error": True,
                                    "isDuplicate": True,
                                    "message": duplicate_check["message"],
                                    "allowOverride": True
                                })
                    except Exception as e:
                        print(f"Error al verificar duplicados: {e}")
                
                # Procesar e insertar los números (force_insert o validación pasada)
                try:
                    numeros_str = ','.join(map(str, numeros_extraidos))
                    history_id = save_history_to_supabase(numeros_str)
                    
                    if history_id:
                        # Agregar números al analizador para mantenimiento del estado
                        for num in reversed(numeros_extraidos):  # Agregar en orden cronológico
                            analizador.agregar_numero(num)
                        
                        save_individual_numbers_to_supabase(history_id, numeros_str)
                        
                        primer_numero = numeros_extraidos[0]  # El más reciente
                        return jsonify({
                            "texto_reconocido": f"{'FORZADO: ' if force_insert else ''}Números procesados: {numeros_str}",
                            "numero_reconocido": primer_numero,
                            "numeros_procesados": numeros_extraidos,
                            "confianza": 1.0,
                            "modo": "texto_directo_forzado" if force_insert else "texto_directo",
                            "success": True
                        })
                    else:
                        return jsonify({
                            "error": "Error al guardar en la base de datos",
                            "modo": "texto_directo_error"
                        }), 500
                        
                except Exception as e:
                    print(f"Error al procesar números: {e}")
                    traceback.print_exc()
                    return jsonify({
                        "error": f"Error al procesar números: {str(e)}",
                        "modo": "texto_directo_error"
                    }), 500
            else:
                return jsonify({
                    "error": "No se encontraron números válidos en el texto",
                    "modo": "texto_directo_error"
                }), 400
        
        # Si no tenemos Google STT o no hay credenciales, usar modo simulación
        if not speech_available or gcp_credentials is None:
            print("Usando modo simulación para reconocimiento de voz")
            
            # Simulamos el reconocimiento extrayendo números si están en el comando
            # o generando un número aleatorio si no hay
            numero_reconocido = None
            
            if comando:
                # Intentar extraer número del comando
                numero_extraido = extract_number_from_text(comando)
                if numero_extraido:
                    numero_reconocido = int(numero_extraido)
            
            # Si no se extrajo ningún número, generar uno aleatorio
            if numero_reconocido is None:
                numero_reconocido = random.randint(0, 36)
            
            # MEJORADO: Verificar duplicados consecutivos más inteligentemente
            if supabase_client and numero_reconocido is not None:
                try:
                    # Obtener solo los últimos 5 números
                    response = (
                        supabase_client.table(NUMEROS_INDIVIDUALES_TABLE_NAME)
                        .select("number_value")
                        .order("id", desc=True)
                        .limit(5)
                        .execute()
                    )
                    
                    if response.data:
                        ultimos_numeros = [entry['number_value'] for entry in response.data]
                        duplicate_check = check_consecutive_duplicate(numero_reconocido, ultimos_numeros)
                        
                        if duplicate_check["is_duplicate"]:
                            return jsonify({
                                "texto_reconocido": f"Número {numero_reconocido}: {duplicate_check['message']}",
                                "numero_reconocido": numero_reconocido,
                                "confianza": 0.95,
                                "modo": "simulacion",
                                "error": True,
                                "isDuplicate": True,
                                "message": duplicate_check["message"],
                                "allowOverride": True
                            })
                except Exception as e:
                    print(f"Error al verificar duplicados: {e}")
                
            return jsonify({
                "texto_reconocido": f"Salió el {numero_reconocido}",
                "numero_reconocido": numero_reconocido,
                "confianza": 0.95,  # Alta confianza en modo simulación
                "modo": "simulacion"
            })
            
        # Si tenemos Google STT disponible, usar reconocimiento real
        # Nota: Esto requeriría un archivo de audio enviado por el cliente
        # Por simplicidad, en este ejemplo también generamos un número aleatorio
        print("Google STT disponible, pero usando simulación por simplicidad")
        numero_reconocido = random.randint(0, 36)
        
        # MEJORADO: Verificar duplicados consecutivos más inteligentemente
        if supabase_client and numero_reconocido is not None:
            try:
                # Obtener solo los últimos 5 números
                response = (
                    supabase_client.table(NUMEROS_INDIVIDUALES_TABLE_NAME)
                    .select("number_value")
                    .order("id", desc=True)
                    .limit(5)
                    .execute()
                )
                
                if response.data:
                    ultimos_numeros = [entry['number_value'] for entry in response.data]
                    duplicate_check = check_consecutive_duplicate(numero_reconocido, ultimos_numeros)
                    
                    if duplicate_check["is_duplicate"]:
                        return jsonify({
                            "texto_reconocido": f"Número {numero_reconocido}: {duplicate_check['message']}",
                            "numero_reconocido": numero_reconocido,
                            "confianza": 0.95,
                            "modo": "google_stt_simulado",
                            "error": True,
                            "isDuplicate": True,
                            "message": duplicate_check["message"],
                            "allowOverride": True
                        })
            except Exception as e:
                print(f"Error al verificar duplicados: {e}")
        
        return jsonify({
            "texto_reconocido": f"Salió el {numero_reconocido}",
            "numero_reconocido": numero_reconocido,
            "confianza": 0.95,
            "modo": "google_stt_simulado"
        })
        
    except Exception as e:
        print(f"Error en reconocimiento de voz: {e}")
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "numero_reconocido": random.randint(0, 36),  # Fallback a número aleatorio
            "modo": "error"
        }), 500

@app.route('/completar-jugada', methods=['POST', 'OPTIONS'])
def completar_jugada():
    """Completa una jugada a partir de un número base."""
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        data = request.get_json() or {}
        numero_base = data.get('numero_base', 0)
        cantidad = min(data.get('cantidad', 5), 20)  # Limitar a máximo 20 números
        
        # Convertir a entero si es una cadena
        if isinstance(numero_base, str):
            try:
                numero_base = int(numero_base)
            except ValueError:
                numero_base = 0
        
        # Asegurar que está en el rango válido
        numero_base = max(0, min(numero_base, 36))
        
        # Generar el resto de números para completar la jugada
        # Usar números cercanos en la ruleta y algunos aleatorios
        jugada_completa = [numero_base]
        
        # Obtener vecinos en la rueda
        idx_central = RUEDA_EUROPEA.index(numero_base)
        for i in [-3, 3, -5, 5]:  # Vecinos a varias posiciones
            idx_vecino = (idx_central + i) % len(RUEDA_EUROPEA)
            jugada_completa.append(RUEDA_EUROPEA[idx_vecino])
            if len(jugada_completa) >= cantidad:
                break
        
        # Si aún faltan números, añadir aleatorios
        while len(jugada_completa) < cantidad:
            nuevo_num = random.randint(0, 36)
            if nuevo_num not in jugada_completa:
                jugada_completa.append(nuevo_num)
        
        return jsonify({
            "jugada_completa": jugada_completa,
            "numero_base": numero_base,
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error al completar jugada: {e}")
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "jugada_completa": [random.randint(0, 36) for _ in range(5)],
            "status": "error"
        }), 500

@app.route('/ml-prediccion', methods=['GET', 'OPTIONS'])
def ml_prediccion():
    """Endpoint para obtener predicciones del modelo ML."""
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        # Verificar que hay suficiente historial para predecir
        if len(analizador.historial_numeros) < 5:
            return jsonify({
                "status": "error", 
                "message": "Historial insuficiente para generar predicciones ML",
                "prediccion_numeros": [random.randint(0, 36) for _ in range(5)],
                "session_id": session_id
            }), 400
        
        # Usar ML Predictor si está disponible
        if ml_predictor and ml_predictor_available:
            try:
                predicciones = ml_predictor.predecir(analizador.historial_numeros, solo_numeros=True)
                # Convertir valores a enteros nativos para asegurar la serialización
                predicciones = {k: int(v) if isinstance(v, (np.integer)) else v 
                              for k, v in predicciones.items()}
                
                # Obtener números con mayor probabilidad
                prediccion_numeros = [
                    predicciones.get('ensemble', 0),
                    predicciones.get('lstm', 0),
                    predicciones.get('random_forest', 0),
                    predicciones.get('markov', 0)
                ]
                
                # Completar hasta 5 números si es necesario
                if len(prediccion_numeros) < 5:
                    num_faltantes = 5 - len(prediccion_numeros)
                    for _ in range(num_faltantes):
                        num = random.randint(0, 36)
                        while num in prediccion_numeros:
                            num = random.randint(0, 36)
                        prediccion_numeros.append(num)
                
                return jsonify({
                    "status": "success",
                    "message": "Predicciones ML generadas con éxito",
                    "prediccion_numeros": prediccion_numeros,
                    "predicciones_detalle": predicciones,
                    "session_id": session_id
                })
            except Exception as e:
                print(f"Error al generar predicciones ML: {e}")
                traceback.print_exc()
        
        # Si no hay ML Predictor o falló, usar método alternativo
        print("ML Predictor no disponible o falló, usando predicción alternativa")
        
        # Generar números aleatorios pero con cierta lógica
        ultimo_numero = analizador.historial_numeros[0].numero if analizador.historial_numeros else 0
        
        # Usar algunos vecinos del último número
        prediccion_numeros = [ultimo_numero]
        idx_central = RUEDA_EUROPEA.index(ultimo_numero)
        
        # Añadir algunos vecinos del último número
        for offset in [1, -1, 3, -3]:
            idx_vecino = (idx_central + offset) % len(RUEDA_EUROPEA)
            prediccion_numeros.append(RUEDA_EUROPEA[idx_vecino])
        
        return jsonify({
            "status": "success",
            "message": "Predicciones generadas por método alternativo",
            "prediccion_numeros": prediccion_numeros,
            "session_id": session_id
        })
        
    except Exception as e:
        print(f"Error general en ML predicción: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Error en predicción: {str(e)}",
            "prediccion_numeros": [random.randint(0, 36) for _ in range(5)],
            "session_id": session_id
        }), 500

# Endpoint para generar números aleatorios
@app.route('/generar-numeros', methods=['GET'])
@cross_origin()
def generar_numeros():
    try:
        cantidad = request.args.get('cantidad', default=1, type=int)
        if cantidad < 1:
            cantidad = 1
        if cantidad > 100:  # Limitar a 100 números por seguridad
            cantidad = 100
            
        # Generar números aleatorios de ruleta (0-36)
        numeros = [random.randint(0, 36) for _ in range(cantidad)]
        
        return jsonify({
            "status": "success",
            "numeros": numeros
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "mensaje": str(e)
        }), 500

# Endpoint para procesar consultas de texto genéricas
@app.route('/consulta', methods=['POST'])
@cross_origin()
def procesar_consulta():
    try:
        datos = request.get_json()
        texto = datos.get('texto', '')
        
        # Procesar la consulta según su contenido
        respuesta = "He recibido tu consulta: " + texto
        
        # Aquí podrías implementar un sistema más avanzado para responder
        # Por ejemplo, conectar con un modelo de lenguaje para consultas específicas
        
        return jsonify({
            "status": "success",
            "respuesta": respuesta
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "mensaje": str(e)
        }), 500

# Endpoint para obtener detalles de la estrategia Tía Lu
@app.route('/estrategia-tia-lu', methods=['GET'])
@cross_origin()
def obtener_estrategia_tia_lu():
    try:
        # Obtener los últimos N números del historial (opcional)
        ultimos = request.args.get('ultimos', default=None, type=int)
        
        # Obtener historial actual
        if ultimos and ultimos > 0 and ultimos < len(analizador.historial_numeros):
            historial = analizador.historial_numeros[:ultimos]
        else:
            historial = analizador.historial_numeros
        
        # Convertir objetos NumeroRoleta a enteros
        numeros = [n.numero for n in historial]
        
        # Obtener datos de la estrategia
        datos_estrategia = obtener_datos_estrategia_tia_lu(numeros)
        
        # Calcular probabilidad actual
        probabilidad = calcular_probabilidad_tia_lu(analizador)
        
        # Determinar si la estrategia está activa actualmente
        esta_activa = False
        recomendacion = ""
        
        # Verificar si alguno de los números desencadenantes apareció recientemente
        if len(numeros) > 0 and numeros[0] in datos_estrategia['numeros_desencadenantes']:
            esta_activa = True
            recomendacion = f"La estrategia está activa. Se recomienda apostar a los números: {', '.join(map(str, datos_estrategia['numeros_apuesta']))}"
        elif len(numeros) > 1 and numeros[1] in datos_estrategia['numeros_desencadenantes']:
            esta_activa = True
            recomendacion = f"La estrategia está activa (2do giro). Se recomienda apostar a los números: {', '.join(map(str, datos_estrategia['numeros_apuesta']))}"
        else:
            recomendacion = "La estrategia no está activa en este momento. Espere a que aparezca alguno de los números desencadenantes (33, 22, 11)."
        
        return jsonify({
            "status": "success",
            "nombre": "Estrategia Tía Lu",
            "descripcion": "Estrategia basada en los números 33, 22 y 11. Cuando aparece alguno de estos números, se activa la estrategia y se apuesta a un conjunto específico de números.",
            "numeros_desencadenantes": datos_estrategia['numeros_desencadenantes'],
            "numeros_apuesta": datos_estrategia['numeros_apuesta'],
            "esta_activa": esta_activa,
            "recomendacion": recomendacion,
            "probabilidad": probabilidad,
            "estadisticas": {
                "total_activaciones": datos_estrategia['data'][0],
                "aciertos": datos_estrategia['data'][1],
                "secuencias_activas": datos_estrategia['data'][2],
                "efectividad": datos_estrategia['data'][3],
                "apariciones_por_numero": datos_estrategia['apariciones_por_numero'],
                "ultimo_desencadenante": datos_estrategia['ultimo_desencadenante']
            },
            "ultimos_numeros": numeros[:10] if len(numeros) > 10 else numeros
        })
    except Exception as e:
        print(f"Error al obtener detalles de la estrategia Tía Lu: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "mensaje": str(e)
        }), 500

@app.route('/predicciones-avanzadas', methods=['GET', 'OPTIONS'])
@cross_origin()
def predicciones_avanzadas():
    """
    Endpoint para obtener predicciones usando el sistema ML avanzado.
    Combina machine learning, análisis de sectores, estrategias y patrones temporales.
    """
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        # Verificar que hay suficiente historial
        if len(analizador.historial_numeros) < 15:
            return jsonify({
                "status": "warning",
                "message": "Historial insuficiente para predicciones avanzadas",
                "cantidad_numeros": len(analizador.historial_numeros),
                "requerido_minimo": 15,
                "predicciones_disponibles": False
            }), 200
        
        # Convertir historial a números enteros
        history_numbers = []
        for num in analizador.historial_numeros:
            if hasattr(num, 'numero'):
                history_numbers.append(num.numero)
            else:
                history_numbers.append(num)
        
        # Intentar obtener predicción del cache primero
        predicciones = get_cached_prediction(history_numbers)
        
        if not predicciones:
            # Verificar si necesitamos re-entrenar el modelo
            if advanced_ml_predictor and should_retrain_model():
                print("🔄 Re-entrenando sistema ML por intervalo de tiempo...")
                extended_history = load_extended_history_for_ml()
                
                if extended_history and len(extended_history) >= 50:
                    extended_numbers = []
                    for num in extended_history:
                        if hasattr(num, 'numero'):
                            extended_numbers.append(num.numero)
                        else:
                            extended_numbers.append(num)
                    
                    success = advanced_ml_predictor.train_models(extended_numbers)
                    if success:
                        update_training_time()
                        print("✅ Re-entrenamiento completado")
            
            # Entrenar el sistema si no está entrenado
            if advanced_ml_predictor and not advanced_ml_predictor.is_trained:
                print("🔄 Entrenando sistema avanzado bajo demanda...")
                extended_history = load_extended_history_for_ml()
                
                # Convertir historial extendido
                if extended_history:
                    extended_numbers = []
                    for num in extended_history:
                        if hasattr(num, 'numero'):
                            extended_numbers.append(num.numero)
                        else:
                            extended_numbers.append(num)
                else:
                    extended_numbers = history_numbers
                
                if len(extended_numbers) >= 30:
                    success = advanced_ml_predictor.train_models(extended_numbers)
                    if success:
                        update_training_time()
                    if not success:
                        return jsonify({
                            "status": "error",
                            "message": "Error al entrenar el sistema avanzado",
                            "session_id": session_id
                        }), 500
            
            # Generar predicciones avanzadas
            if advanced_ml_predictor and advanced_ml_predictor.is_trained:
                try:
                    predicciones = advanced_ml_predictor.predict_advanced(history_numbers)
                    
                    # Guardar en cache
                    if predicciones:
                        cache_prediction(history_numbers, predicciones)
                    
                    print("✅ Predicciones avanzadas generadas")
                except Exception as e:
                    print(f"Error en predicciones avanzadas: {e}")
                    return jsonify({
                        "status": "error", 
                        "message": f"Error generando predicciones: {str(e)}",
                        "session_id": session_id
                    }), 500
            else:
                return jsonify({
                    "status": "error",
                    "message": "Sistema ML avanzado no disponible",
                    "session_id": session_id
                }), 500
        
        # Preparar respuesta estructurada
        response_data = {
            "status": "success",
            "message": "Predicciones avanzadas generadas exitosamente",
            "session_id": session_id,
            "cantidad_numeros_analizados": len(history_numbers),
            "ultimos_numeros": history_numbers[:10],
            
            # Predicciones principales
            "prediccion_individual": predicciones.get('individual', 0),
            "grupos_prediccion": {
                "grupo_5": predicciones.get('grupo_5', []),
                "grupo_10": predicciones.get('grupo_10', []),
                "grupo_15": predicciones.get('grupo_15', []),
                "grupo_20": predicciones.get('grupo_20', [])
            },
            
            # Análisis detallado por método
            "analisis_ml": predicciones.get('ml_predictions', {}),
            "analisis_sectores": predicciones.get('sector_predictions', {}),
            "analisis_estrategias": predicciones.get('strategy_predictions', {}),
            "analisis_temporal": predicciones.get('temporal_predictions', {}),
            
            # Métricas de confianza
            "confianza": predicciones.get('confidence_scores', {}),
            "pesos_hibridos": predicciones.get('hybrid_weights', {}),
            
            # Recomendaciones estratégicas
            "recomendaciones": generar_recomendaciones_estrategicas(predicciones, history_numbers)
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error en predicciones avanzadas: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Error inesperado: {str(e)}",
            "session_id": session_id
        }), 500

def generar_recomendaciones_estrategicas(predicciones, history):
    """Genera recomendaciones estratégicas basadas en las predicciones"""
    recomendaciones = []
    
    # Análisis de estrategias activas
    strategy_pred = predicciones.get('strategy_predictions', {})
    if 'tia_lu_activa' in strategy_pred:
        recomendaciones.append({
            "tipo": "estrategia",
            "nombre": "Tía Lu Activa",
            "descripcion": "La estrategia Tía Lu está activa. Se recomienda apostar a los números objetivo.",
            "numeros": strategy_pred['tia_lu_activa'],
            "prioridad": "alta"
        })
    
    if 'fibonacci_secuencia' in strategy_pred:
        recomendaciones.append({
            "tipo": "estrategia",
            "nombre": "Secuencia Fibonacci",
            "descripcion": "Patrón Fibonacci detectado. Considere apostar a números de la secuencia.",
            "numeros": strategy_pred['fibonacci_secuencia'][:8],
            "prioridad": "media"
        })
    
    # Análisis de sectores
    sector_pred = predicciones.get('sector_predictions', {})
    sectores_frios = [k for k in sector_pred.keys() if 'frio' in k]
    if sectores_frios:
        recomendaciones.append({
            "tipo": "sector",
            "nombre": "Sectores Fríos",
            "descripcion": "Sectores con baja actividad reciente. Posible compensación.",
            "sectores": sectores_frios,
            "prioridad": "media"
        })
    
    # Análisis temporal
    temporal_pred = predicciones.get('temporal_predictions', {})
    if temporal_pred.get('preferred_numbers'):
        recomendaciones.append({
            "tipo": "temporal",
            "nombre": "Patrón Temporal",
            "descripcion": f"Números favorecidos en {temporal_pred.get('time_factor', 'esta hora')}",
            "numeros": temporal_pred['preferred_numbers'][:6],
            "prioridad": "baja"
        })
    
    # Análisis de confianza ML
    confidence = predicciones.get('confidence_scores', {})
    high_confidence = {k: v for k, v in confidence.items() if v > 0.7}
    if high_confidence:
        best_model = max(high_confidence.items(), key=lambda x: x[1])
        recomendaciones.append({
            "tipo": "ml_confidence",
            "nombre": f"Alta Confianza - {best_model[0]}",
            "descripcion": f"Modelo {best_model[0]} con {best_model[1]:.1%} de confianza",
            "numero": predicciones.get('ml_predictions', {}).get(best_model[0], 0),
            "confianza": best_model[1],
            "prioridad": "alta"
        })
    
    return recomendaciones

@app.route('/ml-analisis-extendido', methods=['GET', 'OPTIONS'])
@cross_origin()
def ml_analisis_extendido():
    """
    Endpoint para obtener análisis detallados basados en el historial extendido.
    Proporciona predicciones más precisas utilizando todos los datos disponibles en Supabase.
    """
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        # Cargar historial extendido
        historial_extendido = load_extended_history_for_ml()
        
        if len(historial_extendido) < 50:
            return jsonify({
                "status": "warning",
                "message": "Datos históricos insuficientes para análisis ML extendido",
                "cantidad_numeros": len(historial_extendido),
                "predicciones_disponibles": False
            }), 200
        
        # Realizar predicciones con el modelo ML
        predicciones = {}
        try:
            if ml_predictor and ml_predictor_available:
                # Entrenar el modelo con los datos extendidos
                ml_predictor.entrenar_todos(historial_extendido)
                
                # Obtener predicciones detalladas
                predicciones = ml_predictor.predecir(historial_extendido[:10])  # Usar los últimos 10 números para predecir
                
                # Convertir valores NumPy a tipos nativos de Python para JSON
                predicciones = convert_to_serializable(predicciones)
            else:
                print("ML Predictor no disponible para análisis extendido")
        except Exception as e:
            print(f"Error en predicciones ML extendidas: {e}")
            traceback.print_exc()
        
        # Analizar patrones frecuentes en el historial extendido
        patrones_frecuentes = {}
        try:
            # Obtener frecuencias de números
            conteo_numeros = {}
            for num in historial_extendido:
                conteo_numeros[num] = conteo_numeros.get(num, 0) + 1
            
            # Ordenar por frecuencia
            numeros_ordenados = sorted(conteo_numeros.items(), key=lambda x: x[1], reverse=True)
            top_numeros = numeros_ordenados[:10]
            
            # Calcular patrones de secuencia (qué números suelen salir después de cada número)
            patrones_secuencia = calcular_patrones_puxa_ultra(historial_extendido, top_n=8)
            
            patrones_frecuentes = {
                "numeros_mas_frecuentes": [{"numero": num, "frecuencia": freq} for num, freq in top_numeros],
                "patrones_secuencia": patrones_secuencia
            }
        except Exception as e:
            print(f"Error al analizar patrones frecuentes: {e}")
            traceback.print_exc()
        
        # Preparar respuesta con toda la información
        return jsonify({
            "status": "success",
            "cantidad_numeros_analizados": len(historial_extendido),
            "ultimos_numeros": historial_extendido[:20], # Incluir solo los últimos 20 números
            "predicciones_ml": predicciones,
            "patrones_frecuentes": patrones_frecuentes,
            "session_id": session_id
        }), 200
        
    except Exception as e:
        print(f"Error en análisis ML extendido: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Error en análisis ML extendido: {str(e)}",
            "session_id": session_id
        }), 500

def detectar_sectores_populares(historial_numeros, min_tamano_grupo=3, max_tamano_grupo=8, min_correlacion=0.3):
    """
    Detecta automáticamente sectores populares basados en números que se repiten con frecuencia juntos.
    
    Args:
        historial_numeros: Lista de números de la ruleta
        min_tamano_grupo: Tamaño mínimo de un grupo para considerarlo sector
        max_tamano_grupo: Tamaño máximo de un grupo para considerarlo sector
        min_correlacion: Correlación mínima entre números para considerarlos relacionados
        
    Returns:
        dict: Sectores detectados con sus métricas
    """
    if len(historial_numeros) < 20:  # Necesitamos suficientes datos para análisis
        return []
    
    # Convertir el historial a una lista simple de números
    numeros = [n.numero if hasattr(n, 'numero') else n for n in historial_numeros]
    total_numeros = len(numeros)
    
    # Calcular frecuencias individuales
    frecuencias = {}
    for num in numeros:
        frecuencias[num] = frecuencias.get(num, 0) + 1
    
    # Identificar números que aparecen más frecuentemente que el promedio
    freq_promedio = total_numeros / 37  # 37 números posibles (0-36)
    numeros_frecuentes = {num: freq for num, freq in frecuencias.items() 
                         if freq > freq_promedio * 1.2}  # 20% más que el promedio
    
    if not numeros_frecuentes:
        return []
    
    # Calcular matriz de co-ocurrencia (cuántas veces aparecen números cercanos)
    co_ocurrencia = {}
    for i in range(len(numeros) - 1):
        num_actual = numeros[i]
        # Mirar los próximos 5 números para detectar patrones
        for j in range(1, min(6, len(numeros) - i)):
            num_siguiente = numeros[i + j]
            par = (min(num_actual, num_siguiente), max(num_actual, num_siguiente))
            co_ocurrencia[par] = co_ocurrencia.get(par, 0) + 1
    
    # Normalizar co-ocurrencias por frecuencias individuales
    correlaciones = {}
    for (num1, num2), ocurrencias in co_ocurrencia.items():
        if num1 in numeros_frecuentes and num2 in numeros_frecuentes:
            # Fórmula de correlación simple
            correlacion = ocurrencias / math.sqrt(frecuencias[num1] * frecuencias[num2])
            correlaciones[(num1, num2)] = correlacion
    
    # Agrupar números en sectores basados en correlaciones
    pares_ordenados = sorted(correlaciones.items(), key=lambda x: x[1], reverse=True)
    
    # Iniciar con los pares más correlacionados
    sectores = []
    numeros_asignados = set()
    
    for (num1, num2), correlacion in pares_ordenados:
        if correlacion < min_correlacion:
            continue
            
        # Buscar si alguno de los números ya está en un sector existente
        sector_encontrado = False
        for sector in sectores:
            if num1 in sector['numeros'] or num2 in sector['numeros']:
                # Añadir el número que falta si no está ya en el sector
                if num1 not in sector['numeros'] and len(sector['numeros']) < max_tamano_grupo:
                    sector['numeros'].add(num1)
                    numeros_asignados.add(num1)
                    sector_encontrado = True
                if num2 not in sector['numeros'] and len(sector['numeros']) < max_tamano_grupo:
                    sector['numeros'].add(num2)
                    numeros_asignados.add(num2)
                    sector_encontrado = True
                break
        
        # Si no se encontró sector adecuado, crear uno nuevo
        if not sector_encontrado and (num1 not in numeros_asignados or num2 not in numeros_asignados):
            nuevo_sector = {
                'numeros': {num1, num2},
                'correlacion_promedio': correlacion
            }
            sectores.append(nuevo_sector)
            numeros_asignados.add(num1)
            numeros_asignados.add(num2)
    
    # Filtrar sectores por tamaño mínimo y calcular métricas
    sectores_filtrados = []
    for i, sector in enumerate(sectores):
        if len(sector['numeros']) >= min_tamano_grupo:
            # Calcular apariciones del sector
            apariciones = 0
            for num in numeros:
                if num in sector['numeros']:
                    apariciones += 1
            
            # Calcular porcentaje
            porcentaje = (apariciones / total_numeros) * 100
            
            sectores_filtrados.append({
                'title': f'Sector Auto {i+1}',
                'numbers': list(sector['numeros']),
                'appearance': apariciones,
                'historyPercentage': round(porcentaje, 1)
            })
    
    return sectores_filtrados

# Importar Google Cloud Speech
import io
from google.cloud import speech

# Configuración de Google Cloud Speech
@app.route('/api/speech-recognition', methods=['POST'])
@cross_origin()
def speech_recognition():
    try:
        # Verificar si el archivo de audio está en la solicitud
        if 'audio' not in request.files:
            return jsonify({"error": "No se proporcionó archivo de audio"}), 400
        
        audio_file = request.files['audio']
        
        # Verificar que tenemos las credenciales inicializadas
        if not speech_available:
            return jsonify({"error": "Google Cloud Speech no está disponible en este servidor"}), 500
            
        if not gcp_credentials:
            return jsonify({"error": "Credenciales de Google Cloud no inicializadas correctamente"}), 500
        
        # Crear cliente de Speech usando las credenciales ya cargadas
        client = speech.SpeechClient(credentials=gcp_credentials)
        
        # Leer contenido del archivo
        audio_content = audio_file.read()
        
        # Configuración del reconocimiento
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="es-ES",
            enable_automatic_punctuation=False,
            model="default"
        )
        
        # Realizar reconocimiento
        response = client.recognize(config=config, audio=audio)
        
        # Procesar resultados
        results = []
        for result in response.results:
            for alternative in result.alternatives:
                results.append({
                    "transcript": alternative.transcript,
                    "confidence": alternative.confidence
                })
        
        # Devolver resultados
        return jsonify({
            "success": True,
            "results": results
        })
    
    except Exception as e:
        print(f"Error en reconocimiento de voz: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# SISTEMA DE PURGA AUTOMÁTICA DE BASE DE DATOS
# ============================================================================

def purgar_base_datos(mantener_horas=48, mantener_minimo=50):
    """
    Purga registros antiguos de la base de datos manteniendo:
    - Registros de las últimas 'mantener_horas' horas
    - Al menos 'mantener_minimo' registros más recientes
    """
    try:
        print(f"\n========== INICIANDO PURGA DE BASE DE DATOS ==========")
        print(f"Hora de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Configuración: Mantener últimas {mantener_horas} horas, mínimo {mantener_minimo} registros")
        
        # Calcular fecha límite
        fecha_limite = datetime.now() - timedelta(hours=mantener_horas)
        fecha_limite_str = fecha_limite.isoformat()
        
        print(f"Eliminando registros anteriores a: {fecha_limite.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Contador de registros eliminados
        total_eliminados = 0
        
        # 1. Obtener total de registros antes de la purga
        try:
            count_before_individual = supabase.table('roulette_numbers_individual').select('id', count='exact').execute()
            count_before_history = supabase.table('roulette_history').select('id', count='exact').execute()
            
            total_before_individual = count_before_individual.count or 0
            total_before_history = count_before_history.count or 0
            
            print(f"Registros antes de purgar:")
            print(f"- roulette_numbers_individual: {total_before_individual}")
            print(f"- roulette_history: {total_before_history}")
            
        except Exception as e:
            print(f"Error al contar registros iniciales: {e}")
            total_before_individual = 0
            total_before_history = 0
        
        # 2. Verificar que tenemos suficientes registros recientes
        try:
            recent_individual = supabase.table('roulette_numbers_individual')\
                .select('id')\
                .gte('created_at', fecha_limite_str)\
                .execute()
            
            registros_recientes = len(recent_individual.data) if recent_individual.data else 0
            print(f"Registros recientes (últimas {mantener_horas}h): {registros_recientes}")
            
            if registros_recientes < mantener_minimo:
                print(f"⚠️ ADVERTENCIA: Solo hay {registros_recientes} registros recientes.")
                print(f"Se mantendrán los últimos {mantener_minimo} registros independientemente de la fecha.")
                
                # Obtener los IDs de los últimos registros a mantener
                ultimos_registros = supabase.table('roulette_numbers_individual')\
                    .select('id')\
                    .order('created_at', desc=True)\
                    .limit(mantener_minimo)\
                    .execute()
                
                if ultimos_registros.data:
                    ids_a_mantener = [str(r['id']) for r in ultimos_registros.data]
                    
                    # Eliminar registros que NO están en la lista de IDs a mantener
                    if len(ids_a_mantener) > 0:
                        delete_result = supabase.table('roulette_numbers_individual')\
                            .delete()\
                            .not_.in_('id', ids_a_mantener)\
                            .execute()
                        
                        eliminados_individual = len(delete_result.data) if delete_result.data else 0
                        total_eliminados += eliminados_individual
                        print(f"✓ Eliminados {eliminados_individual} registros de roulette_numbers_individual (manteniendo últimos {mantener_minimo})")
                
            else:
                # Purga normal por fecha
                delete_result_individual = supabase.table('roulette_numbers_individual')\
                    .delete()\
                    .lt('created_at', fecha_limite_str)\
                    .execute()
                
                eliminados_individual = len(delete_result_individual.data) if delete_result_individual.data else 0
                total_eliminados += eliminados_individual
                print(f"✓ Eliminados {eliminados_individual} registros antiguos de roulette_numbers_individual")
        
        except Exception as e:
            print(f"❌ Error al purgar roulette_numbers_individual: {e}")
        
        # 3. Purgar tabla roulette_history (manteniendo consistencia)
        try:
            # Obtener IDs de history que ya no tienen números individuales asociados
            # o que son muy antiguos
            delete_result_history = supabase.table('roulette_history')\
                .delete()\
                .lt('created_at', fecha_limite_str)\
                .execute()
            
            eliminados_history = len(delete_result_history.data) if delete_result_history.data else 0
            total_eliminados += eliminados_history
            print(f"✓ Eliminados {eliminados_history} registros antiguos de roulette_history")
        
        except Exception as e:
            print(f"❌ Error al purgar roulette_history: {e}")
        
        # 4. Contar registros después de la purga
        try:
            count_after_individual = supabase.table('roulette_numbers_individual').select('id', count='exact').execute()
            count_after_history = supabase.table('roulette_history').select('id', count='exact').execute()
            
            total_after_individual = count_after_individual.count or 0
            total_after_history = count_after_history.count or 0
            
            print(f"\nRegistros después de purgar:")
            print(f"- roulette_numbers_individual: {total_after_individual} (eliminados: {total_before_individual - total_after_individual})")
            print(f"- roulette_history: {total_after_history} (eliminados: {total_before_history - total_after_history})")
            
        except Exception as e:
            print(f"Error al contar registros finales: {e}")
        
        print(f"\n✅ PURGA COMPLETADA")
        print(f"Total de registros eliminados: {total_eliminados}")
        print(f"Hora de finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        return {
            'success': True,
            'registros_eliminados': total_eliminados,
            'registros_antes': {
                'individual': total_before_individual,
                'history': total_before_history
            },
            'registros_despues': {
                'individual': total_after_individual,
                'history': total_after_history
            },
            'fecha_limite': fecha_limite_str
        }
        
    except Exception as e:
        error_msg = f"Error crítico durante la purga: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return {
            'success': False,
            'error': error_msg
        }

def purga_automatica():
    """
    Función que se ejecuta en un hilo separado para purgar automáticamente cada 48 horas
    """
    print("🔄 Sistema de purga automática iniciado")
    print(f"Próxima purga programada en 48 horas: {(datetime.now() + timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    while True:
        try:
            # Esperar 48 horas (48 * 60 * 60 segundos)
            time.sleep(48 * 60 * 60)
            
            print("\n🕐 Iniciando purga automática programada...")
            resultado = purgar_base_datos(mantener_horas=48, mantener_minimo=50)
            
            if resultado['success']:
                print("✅ Purga automática completada exitosamente")
            else:
                print(f"❌ Error en purga automática: {resultado.get('error', 'Error desconocido')}")
                
            print(f"🔄 Próxima purga programada en 48 horas: {(datetime.now() + timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            print(f"❌ Error crítico en el sistema de purga automática: {e}")
            traceback.print_exc()
            # En caso de error, esperar 1 hora antes de intentar de nuevo
            time.sleep(60 * 60)

@app.route('/purgar-db', methods=['POST', 'OPTIONS'])
@cross_origin()
def purgar_base_datos_manual():
    """
    Endpoint para ejecutar purga manual de la base de datos
    """
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
    
    try:
        # Obtener parámetros opcionales
        data = request.get_json() or {}
        mantener_horas = data.get('mantener_horas', 48)
        mantener_minimo = data.get('mantener_minimo', 50)
        
        # Validar parámetros
        if mantener_horas < 1 or mantener_horas > 168:  # Entre 1 hora y 1 semana
            return jsonify({
                'success': False,
                'error': 'mantener_horas debe estar entre 1 y 168 (1 semana)'
            }), 400
            
        if mantener_minimo < 10 or mantener_minimo > 1000:
            return jsonify({
                'success': False,
                'error': 'mantener_minimo debe estar entre 10 y 1000'
            }), 400
        
        print(f"\n📞 Purga manual solicitada:")
        print(f"- Mantener horas: {mantener_horas}")
        print(f"- Mantener mínimo: {mantener_minimo}")
        
        # Ejecutar purga
        resultado = purgar_base_datos(mantener_horas=mantener_horas, mantener_minimo=mantener_minimo)
        
        return jsonify(resultado)
        
    except Exception as e:
        error_msg = f"Error en purga manual: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/estado-db', methods=['GET', 'OPTIONS'])
@cross_origin()
def obtener_estado_db():
    """
    Endpoint para obtener información sobre el estado de la base de datos
    """
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
    
    try:
        # Contar registros totales
        count_individual = supabase.table('roulette_numbers_individual').select('id', count='exact').execute()
        count_history = supabase.table('roulette_history').select('id', count='exact').execute()
        
        # Obtener el registro más antiguo y más reciente
        oldest_individual = supabase.table('roulette_numbers_individual')\
            .select('created_at')\
            .order('created_at', desc=False)\
            .limit(1)\
            .execute()
            
        newest_individual = supabase.table('roulette_numbers_individual')\
            .select('created_at')\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
        
        # Calcular registros de las últimas 48 horas
        fecha_limite_48h = (datetime.now() - timedelta(hours=48)).isoformat()
        recent_48h = supabase.table('roulette_numbers_individual')\
            .select('id', count='exact')\
            .gte('created_at', fecha_limite_48h)\
            .execute()
        
        # Calcular registros de las últimas 24 horas
        fecha_limite_24h = (datetime.now() - timedelta(hours=24)).isoformat()
        recent_24h = supabase.table('roulette_numbers_individual')\
            .select('id', count='exact')\
            .gte('created_at', fecha_limite_24h)\
            .execute()
        
        estado = {
            'total_registros': {
                'individual': count_individual.count or 0,
                'history': count_history.count or 0
            },
            'registro_mas_antiguo': oldest_individual.data[0]['created_at'] if oldest_individual.data else None,
            'registro_mas_reciente': newest_individual.data[0]['created_at'] if newest_individual.data else None,
            'registros_ultimas_48h': recent_48h.count or 0,
            'registros_ultimas_24h': recent_24h.count or 0,
            'timestamp_consulta': datetime.now().isoformat()
        }
        
        # Calcular si necesita purga
        if estado['registro_mas_antiguo']:
            fecha_mas_antigua = datetime.fromisoformat(estado['registro_mas_antiguo'].replace('Z', '+00:00'))
            horas_transcurridas = (datetime.now() - fecha_mas_antigua.replace(tzinfo=None)).total_seconds() / 3600
            estado['horas_desde_mas_antiguo'] = round(horas_transcurridas, 2)
            estado['necesita_purga'] = horas_transcurridas > 48
        else:
            estado['horas_desde_mas_antiguo'] = 0
            estado['necesita_purga'] = False
        
        return jsonify({
            'success': True,
            'estado': estado
        })
        
    except Exception as e:
        error_msg = f"Error al obtener estado de la DB: {str(e)}"
        print(f"❌ {error_msg}")
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

# Iniciar el sistema de purga automática en un hilo separado
def iniciar_purga_automatica():
    """
    Inicia el sistema de purga automática en un hilo en segundo plano
    """
    try:
        purga_thread = threading.Thread(target=purga_automatica, daemon=True)
        purga_thread.start()
        print("✅ Sistema de purga automática iniciado correctamente")
    except Exception as e:
        print(f"❌ Error al iniciar sistema de purga automática: {e}")

# Función para forzar sincronización y verificar consistencia
def sincronizar_datos_con_verificacion():
    """
    Fuerza la sincronización con la base de datos y verifica la consistencia.
    Returns:
        dict: Resultado de la sincronización
    """
    if not supabase_client:
        return {"success": False, "error": "Cliente de Supabase no disponible"}
    
    try:
        print("🔄 Iniciando sincronización forzada con verificación...")
        
        # 1. Verificar conectividad con Supabase
        try:
            ping_test = supabase_client.table(TABLE_NAME).select("id").limit(1).execute()
            print("✅ Conectividad con Supabase confirmada")
        except Exception as e:
            return {"success": False, "error": f"Error de conectividad: {e}"}
        
        # 2. Verificar consistencia entre tablas
        try:
            # Contar registros en ambas tablas
            count_history = supabase_client.table(TABLE_NAME).select("id", count='exact').execute()
            count_individual = supabase_client.table(NUMEROS_INDIVIDUALES_TABLE_NAME).select("id", count='exact').execute()
            
            total_history = count_history.count or 0
            total_individual = count_individual.count or 0
            
            print(f"📊 Registros encontrados - Historial: {total_history}, Individuales: {total_individual}")
            
            # Verificar registros huérfanos
            orphaned_check = supabase_client.table(NUMEROS_INDIVIDUALES_TABLE_NAME)\
                .select("history_entry_id")\
                .not_.in_("history_entry_id", 
                         supabase_client.table(TABLE_NAME).select("id"))\
                .execute()
            
            orphaned_count = len(orphaned_check.data) if orphaned_check.data else 0
            if orphaned_count > 0:
                print(f"⚠️ Se encontraron {orphaned_count} registros individuales huérfanos")
                
        except Exception as e:
            print(f"Error en verificación de consistencia: {e}")
        
        # 3. Recargar estado del analizador
        try:
            print("🔄 Recargando estado del analizador...")
            load_analyzer_state_from_supabase()
            load_history_from_supabase()
            print("✅ Estado del analizador recargado")
        except Exception as e:
            print(f"Error al recargar estado: {e}")
        
        # 4. Verificar timestamp del último registro
        try:
            latest_record = supabase_client.table(NUMEROS_INDIVIDUALES_TABLE_NAME)\
                .select("created_at")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            if latest_record.data:
                ultimo_timestamp = latest_record.data[0]['created_at']
                print(f"📅 Último registro: {ultimo_timestamp}")
                
                # Calcular latencia
                from datetime import datetime
                ultimo_dt = datetime.fromisoformat(ultimo_timestamp.replace('Z', '+00:00'))
                latencia = (datetime.now(ultimo_dt.tzinfo) - ultimo_dt).total_seconds()
                print(f"⏱️ Latencia estimada: {latencia:.2f} segundos")
                
        except Exception as e:
            print(f"Error al verificar timestamps: {e}")
        
        return {
            "success": True,
            "message": "Sincronización completada",
            "stats": {
                "total_history": total_history,
                "total_individual": total_individual,
                "orphaned_records": orphaned_count
            }
        }
        
    except Exception as e:
        print(f"Error en sincronización forzada: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.route('/sincronizar', methods=['POST', 'OPTIONS'])
@cross_origin()
def sincronizar_manual():
    """
    Endpoint para forzar sincronización manual con la base de datos
    """
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        print(f"\n📞 Sincronización manual solicitada por sesión: {session_id}")
        
        # Ejecutar sincronización
        resultado = sincronizar_datos_con_verificacion()
        
        if resultado["success"]:
            return jsonify({
                "status": "success",
                "message": "Sincronización completada exitosamente",
                "session_id": session_id,
                **resultado
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Error en sincronización: {resultado['error']}",
                "session_id": session_id
            }), 500
        
    except Exception as e:
        error_msg = f"Error en sincronización manual: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "message": error_msg,
            "session_id": session_id
        }), 500

@app.route('/estadisticas-evaluacion', methods=['GET', 'OPTIONS'])
@cross_origin()
def obtener_estadisticas_evaluacion():
    """
    Endpoint para obtener estadísticas detalladas de evaluación de predicciones
    """
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        if not prediction_evaluator:
            return jsonify({
                "status": "error",
                "message": "Sistema de evaluación no disponible",
                "session_id": session_id
            }), 500
        
        # Obtener parámetros opcionales
        days = request.args.get('days', default=7, type=int)
        days = max(1, min(days, 30))  # Limitar entre 1 y 30 días
        
        # Obtener estadísticas básicas
        group_statistics = prediction_evaluator.get_group_statistics()
        
        # Obtener análisis de rendimiento reciente
        recent_performance = prediction_evaluator.get_recent_performance(days=days)
        
        return jsonify({
            "status": "success",
            "message": "Estadísticas de evaluación obtenidas",
            "session_id": session_id,
            "group_statistics": group_statistics,
            "recent_performance": recent_performance,
            "analysis_period_days": days,
            "export_data": prediction_evaluator.export_statistics()
        })
        
    except Exception as e:
        error_msg = f"Error al obtener estadísticas: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "message": error_msg,
            "session_id": session_id
        }), 500

@app.route('/resetear-estadisticas', methods=['POST', 'OPTIONS'])
@cross_origin()
def resetear_estadisticas_evaluacion():
    """Resetea las estadísticas de evaluación de predicciones"""
    if request.method == "OPTIONS":
        return make_response()
    
    try:
        if prediction_evaluator:
            prediction_evaluator.reset_statistics()
            return jsonify({
                "status": "success",
                "message": "Estadísticas de evaluación reseteadas exitosamente"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Evaluador de predicciones no disponible"
            }), 500
            
    except Exception as e:
        print(f"Error al resetear estadísticas: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error inesperado: {str(e)}"
        }), 500

@app.route('/entrenar-ml-avanzado', methods=['POST', 'OPTIONS'])
@cross_origin()
def entrenar_ml_avanzado_manual():
    """Endpoint para entrenamiento manual del sistema ML avanzado"""
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        if not advanced_ml_available or not advanced_ml_predictor:
            return jsonify({
                "status": "error",
                "message": "Sistema ML avanzado no disponible",
                "session_id": session_id
            }), 500
        
        # Obtener parámetros opcionales
        data = request.get_json() or {}
        force_retrain = data.get('force_retrain', False)
        
        # Verificar si ya está entrenado y no se fuerza el re-entrenamiento
        if advanced_ml_predictor.is_trained and not force_retrain:
            return jsonify({
                "status": "info",
                "message": "El sistema ya está entrenado. Use 'force_retrain': true para forzar re-entrenamiento",
                "is_trained": True,
                "session_id": session_id
            }), 200
        
        print("🔄 Iniciando entrenamiento manual del sistema ML avanzado...")
        
        # Cargar historial extendido
        extended_history = load_extended_history_for_ml()
        
        if not extended_history or len(extended_history) < 30:
            return jsonify({
                "status": "error",
                "message": f"Historial insuficiente para entrenamiento. Se requieren al menos 30 números, encontrados: {len(extended_history) if extended_history else 0}",
                "session_id": session_id
            }), 400
        
        # Convertir historial a números enteros
        if extended_history and hasattr(extended_history[0], 'numero'):
            numbers = [obj.numero for obj in extended_history]
        else:
            numbers = extended_history
        
        # Entrenar el sistema
        start_time = time.time()
        success = advanced_ml_predictor.train_models(numbers)
        training_time = time.time() - start_time
        
        if success:
            update_training_time()
            
            # Limpiar cache de predicciones después del entrenamiento
            predicciones_cache.clear()
            predicciones_cache_expiry.clear()
            
            return jsonify({
                "status": "success",
                "message": "Sistema ML avanzado entrenado exitosamente",
                "training_time_seconds": round(training_time, 2),
                "numbers_trained": len(numbers),
                "is_trained": True,
                "session_id": session_id
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Error durante el entrenamiento del sistema ML avanzado",
                "training_time_seconds": round(training_time, 2),
                "session_id": session_id
            }), 500
            
    except Exception as e:
        print(f"Error en entrenamiento manual: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Error inesperado durante el entrenamiento: {str(e)}",
            "session_id": session_id
        }), 500

@app.route('/estado-ml-avanzado', methods=['GET', 'OPTIONS'])
@cross_origin()
def obtener_estado_ml_avanzado():
    """Obtiene el estado del sistema ML avanzado"""
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        if not advanced_ml_available or not advanced_ml_predictor:
            return jsonify({
                "status": "unavailable",
                "message": "Sistema ML avanzado no disponible",
                "ml_available": False,
                "session_id": session_id
            }), 200
        
        # Información del estado del entrenamiento
        estado = {
            "status": "available",
            "ml_available": True,
            "is_trained": advanced_ml_predictor.is_trained,
            "models_available": list(advanced_ml_predictor.models.keys()) if hasattr(advanced_ml_predictor, 'models') else [],
            "ensemble_weights": advanced_ml_predictor.ensemble_weights if hasattr(advanced_ml_predictor, 'ensemble_weights') else {},
            "session_id": session_id
        }
        
        # Información del cache
        estado["cache_info"] = {
            "cached_predictions": len(predicciones_cache),
            "cache_expiry_minutes": CACHE_EXPIRY_MINUTES
        }
        
        # Información de entrenamiento automático
        estado["auto_training"] = {
            "enabled": auto_training_enabled,
            "interval_hours": training_interval_hours,
            "last_training": last_training_time.isoformat() if last_training_time else None,
            "needs_retrain": should_retrain_model()
        }
        
        # Información del historial disponible
        try:
            extended_history = load_extended_history_for_ml()
            estado["data_info"] = {
                "extended_history_size": len(extended_history) if extended_history else 0,
                "current_history_size": len(analizador.historial_numeros),
                "minimum_required": 30
            }
        except Exception as e:
            estado["data_info"] = {
                "error": f"Error al cargar información del historial: {str(e)}"
            }
        
        return jsonify(estado), 200
        
    except Exception as e:
        print(f"Error al obtener estado ML: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error inesperado: {str(e)}",
            "session_id": session_id
        }), 500

@app.route('/analisis-detallado-ml', methods=['GET', 'OPTIONS'])
@cross_origin()
def obtener_analisis_detallado_ml():
    """Obtiene análisis detallado del sistema ML avanzado"""
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        if not advanced_ml_available or not advanced_ml_predictor:
            return jsonify({
                "status": "error",
                "message": "Sistema ML avanzado no disponible",
                "session_id": session_id
            }), 500
        
        if not advanced_ml_predictor.is_trained:
            return jsonify({
                "status": "warning",
                "message": "Sistema ML no está entrenado",
                "session_id": session_id
            }), 200
        
        # Verificar que hay suficiente historial
        if len(analizador.historial_numeros) < 10:
            return jsonify({
                "status": "warning",
                "message": "Historial insuficiente para análisis detallado",
                "cantidad_numeros": len(analizador.historial_numeros),
                "session_id": session_id
            }), 200
        
        # Convertir historial a números enteros
        history_numbers = []
        for num in analizador.historial_numeros:
            if hasattr(num, 'numero'):
                history_numbers.append(num.numero)
            else:
                history_numbers.append(num)
        
        # Obtener estadísticas de rendimiento
        performance_stats = advanced_ml_predictor.get_model_performance_stats()
        
                 # Obtener análisis detallado
        detailed_analysis = advanced_ml_predictor.get_detailed_analysis(history_numbers)
        
        # Preparar respuesta
        response_data = {
            "status": "success",
            "session_id": session_id,
            "cantidad_numeros_analizados": len(history_numbers),
            "ultimos_10_numeros": history_numbers[:10],
            
            # Estadísticas de rendimiento
            "rendimiento_modelos": performance_stats,
            
            # Análisis detallado por componente
            "analisis_detallado": detailed_analysis,
            
            # Información del cache actual
            "cache_info": {
                "predicciones_en_cache": len(predicciones_cache),
                "tiempo_expiracion_minutos": CACHE_EXPIRY_MINUTES,
                "cache_keys": list(predicciones_cache.keys())[:5]  # Solo las primeras 5 claves
            },
            
            # Información de entrenamiento
            "info_entrenamiento": {
                "entrenamiento_automatico": auto_training_enabled,
                "ultimo_entrenamiento": last_training_time.isoformat() if last_training_time else None,
                "necesita_reentrenamiento": should_retrain_model(),
                "intervalo_reentrenamiento_horas": training_interval_hours
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error en análisis detallado ML: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Error inesperado: {str(e)}",
            "session_id": session_id
        }), 500

# ============================================================================
# ENDPOINTS PARA SISTEMA DE ENTRENAMIENTO CON VICTORIAS
# ============================================================================

@app.route('/entrenar-con-victorias', methods=['POST', 'OPTIONS'])
@cross_origin()
def entrenar_con_victorias():
    """Endpoint para entrenar el modelo usando solo las victorias recientes"""
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        if not victory_trainer_available or not victory_trainer:
            return jsonify({
                "status": "error",
                "message": "Sistema de entrenamiento con victorias no disponible",
                "session_id": session_id
            }), 500
        
        # Obtener parámetros opcionales
        data = request.get_json() or {}
        victory_weight = float(data.get('victory_weight', 2.0))
        min_confidence = float(data.get('min_confidence', 0.3))
        
        # Validar parámetros
        victory_weight = max(1.0, min(victory_weight, 5.0))  # Entre 1.0 y 5.0
        min_confidence = max(0.1, min(min_confidence, 1.0))  # Entre 0.1 y 1.0
        
        print(f"🎯 Iniciando entrenamiento con victorias (peso: {victory_weight}, confianza mínima: {min_confidence})")
        
        start_time = time.time()
        
        # Obtener secuencias de victoria
        victory_sequences = victory_trainer.get_victory_sequences(
            min_confidence=min_confidence, 
            max_sequences=100
        )
        
        if len(victory_sequences) < 5:
            return jsonify({
                "status": "warning",
                "message": f"Victorias insuficientes para entrenamiento: {len(victory_sequences)} encontradas (mínimo 5)",
                "total_victories": len(victory_trainer.victories),
                "session_id": session_id
            }), 200
        
        # Entrenar con victorias
        success = victory_trainer.train_with_victories(
            predictor=advanced_ml_predictor,
            victory_weight=victory_weight
        )
        
        training_time = time.time() - start_time
        
        if success:
            # Limpiar cache después del entrenamiento
            predicciones_cache.clear()
            predicciones_cache_expiry.clear()
            
            return jsonify({
                "status": "success",
                "message": "Entrenamiento con victorias completado exitosamente",
                "training_time_seconds": round(training_time, 2),
                "victory_sequences_used": len(victory_sequences),
                "total_victories": len(victory_trainer.victories),
                "victory_weight_applied": victory_weight,
                "min_confidence_filter": min_confidence,
                "session_id": session_id
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Error durante el entrenamiento con victorias",
                "training_time_seconds": round(training_time, 2),
                "session_id": session_id
            }), 500
            
    except Exception as e:
        print(f"Error en entrenamiento con victorias: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Error inesperado: {str(e)}",
            "session_id": session_id
        }), 500

@app.route('/entrenamiento-forzado', methods=['POST', 'OPTIONS'])
@cross_origin()
def activar_entrenamiento_forzado():
    """Endpoint para activar el entrenamiento forzado manualmente"""
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        if not victory_trainer_available or not victory_trainer:
            return jsonify({
                "status": "error",
                "message": "Sistema de entrenamiento con victorias no disponible",
                "session_id": session_id
            }), 500
        
        # Obtener parámetros opcionales
        data = request.get_json() or {}
        force_execution = data.get('force_execution', False)
        
        # Verificar condiciones antes de forzar
        if not force_execution and not victory_trainer.should_force_training():
            conditions = victory_trainer.get_current_conditions()
            return jsonify({
                "status": "warning",
                "message": "Las condiciones para entrenamiento forzado no se cumplen",
                "conditions": conditions,
                "suggestion": "Use 'force_execution': true para forzar la ejecución de todos modos",
                "session_id": session_id
            }), 200
        
        print("🚀 Activando entrenamiento forzado manual...")
        
        # Ejecutar entrenamiento forzado
        result = victory_trainer.force_training()
        
        if result['success']:
            # Limpiar cache después del entrenamiento
            predicciones_cache.clear()
            predicciones_cache_expiry.clear()
            
            return jsonify({
                "status": "success",
                "message": "Entrenamiento forzado completado exitosamente",
                "session_id": session_id,
                **result
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Error en entrenamiento forzado",
                "session_id": session_id,
                **result
            }), 500
            
    except Exception as e:
        print(f"Error en entrenamiento forzado: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Error inesperado: {str(e)}",
            "session_id": session_id
        }), 500

@app.route('/estadisticas-victorias', methods=['GET', 'OPTIONS'])
@cross_origin()
def obtener_estadisticas_victorias():
    """Endpoint para obtener estadísticas del sistema de victorias"""
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        if not victory_trainer_available or not victory_trainer:
            return jsonify({
                "status": "error",
                "message": "Sistema de entrenamiento con victorias no disponible",
                "session_id": session_id
            }), 500
        
        # Obtener estadísticas completas
        training_stats = victory_trainer.get_training_statistics()
        
        # Obtener mejores patrones
        best_patterns = victory_trainer.get_best_patterns(top_n=10)
        
        # Preparar respuesta
        response_data = {
            "status": "success",
            "session_id": session_id,
            "estadisticas_entrenamiento": training_stats,
            "mejores_patrones": best_patterns,
            "configuracion_entrenamiento_forzado": victory_trainer.force_training_conditions,
            "condiciones_actuales": victory_trainer.get_current_conditions()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error al obtener estadísticas de victorias: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Error inesperado: {str(e)}",
            "session_id": session_id
        }), 500

@app.route('/configurar-entrenamiento-forzado', methods=['POST', 'OPTIONS'])
@cross_origin()
def configurar_entrenamiento_forzado():
    """Endpoint para configurar los parámetros del entrenamiento forzado"""
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        if not victory_trainer_available or not victory_trainer:
            return jsonify({
                "status": "error",
                "message": "Sistema de entrenamiento con victorias no disponible",
                "session_id": session_id
            }), 500
        
        # Obtener nueva configuración
        data = request.get_json() or {}
        
        # Validar y aplicar nueva configuración
        new_config = {}
        
        if 'min_new_victories' in data:
            new_config['min_new_victories'] = max(1, min(int(data['min_new_victories']), 100))
        
        if 'success_rate_threshold' in data:
            new_config['success_rate_threshold'] = max(0.1, min(float(data['success_rate_threshold']), 1.0))
        
        if 'pattern_confidence' in data:
            new_config['pattern_confidence'] = max(0.1, min(float(data['pattern_confidence']), 1.0))
        
        if 'time_interval_hours' in data:
            new_config['time_interval_hours'] = max(1, min(int(data['time_interval_hours']), 48))
        
        # Aplicar configuración
        victory_trainer.force_training_conditions.update(new_config)
        
        print(f"⚙️ Configuración de entrenamiento forzado actualizada: {new_config}")
        
        return jsonify({
            "status": "success",
            "message": "Configuración actualizada exitosamente",
            "configuracion_anterior": victory_trainer.force_training_conditions,
            "cambios_aplicados": new_config,
            "session_id": session_id
        }), 200
        
    except Exception as e:
        print(f"Error al configurar entrenamiento forzado: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Error inesperado: {str(e)}",
            "session_id": session_id
        }), 500

@app.route('/resetear-victorias', methods=['POST', 'OPTIONS'])
@cross_origin()
def resetear_victorias():
    """Endpoint para resetear las victorias almacenadas"""
    if request.method == "OPTIONS":
        return make_response()
    
    session_id = request.headers.get('Authorization', str(uuid.uuid4()))
    
    try:
        if not victory_trainer_available or not victory_trainer:
            return jsonify({
                "status": "error",
                "message": "Sistema de entrenamiento con victorias no disponible",
                "session_id": session_id
            }), 500
        
        # Obtener confirmación
        data = request.get_json() or {}
        confirm_reset = data.get('confirm_reset', False)
        
        if not confirm_reset:
            return jsonify({
                "status": "warning",
                "message": "Se requiere confirmación para resetear las victorias",
                "current_victories": len(victory_trainer.victories),
                "suggestion": "Use 'confirm_reset': true para confirmar el reseteo",
                "session_id": session_id
            }), 200
        
        # Contar victorias antes del reseteo
        victories_before = len(victory_trainer.victories)
        
        # Resetear victorias
        victory_trainer.victories.clear()
        victory_trainer.victory_patterns.clear()
        victory_trainer.success_rates.clear()
        victory_trainer.victories_since_last_training = 0
        victory_trainer.last_forced_training = None
        
        # Guardar estado vacío
        victory_trainer.save_victories_to_storage()
        
        print(f"🔄 Victorias reseteadas: {victories_before} victorias eliminadas")
        
        return jsonify({
            "status": "success",
            "message": "Victorias reseteadas exitosamente",
            "victories_cleared": victories_before,
            "session_id": session_id
        }), 200
        
    except Exception as e:
        print(f"Error al resetear victorias: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Error inesperado: {str(e)}",
            "session_id": session_id
        }), 500

# Inicializamos el sector manager
sector_manager = None
if sector_manager_available:
    try:
        sector_manager = create_sector_manager(supabase_client)
        if sector_manager:
            print("Sector Manager inicializado correctamente.")
            # Crear sectores predefinidos en DB si no existen
            sector_manager.crear_sectores_predefinidos_en_db()
        else:
            print("Error al crear Sector Manager.")
    except Exception as e:
        print(f"Error al inicializar Sector Manager: {e}")
        sector_manager = None

# Inicializamos el number processor
number_processor = None
if number_processor_available:
    try:
        number_processor = create_number_processor()
        if number_processor:
            print("Number Processor inicializado correctamente.")
        else:
            print("Error al crear Number Processor.")
    except Exception as e:
        print(f"Error al inicializar Number Processor: {e}")
        number_processor = None

# ========================================
# ENDPOINTS PARA GESTIÓN DE SECTORES
# ========================================

@app.route('/sectores', methods=['GET', 'OPTIONS'])
@cross_origin()
def obtener_sectores():
    """Obtiene la lista de todos los sectores disponibles"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'OK'}), 200
    
    try:
        if not sector_manager:
            return jsonify({
                'success': False,
                'error': 'Sector Manager no disponible'
            }), 503
        
        sectores = sector_manager.listar_sectores()
        estadisticas = sector_manager.obtener_estadisticas_sectores()
        
        # Convertir sectores a formato JSON serializable
        sectores_data = {}
        for nombre, sector in sectores.items():
            sectores_data[nombre] = {
                'id': sector.id,
                'nombre': sector.nombre_sector,
                'numeros': sector.numeros,
                'cantidad_numeros': len(sector.numeros),
                'created_at': sector.created_at
            }
        
        return jsonify({
            'success': True,
            'sectores': sectores_data,
            'estadisticas': estadisticas,
            'total_sectores': len(sectores_data)
        }), 200
        
    except Exception as e:
        print(f"Error al obtener sectores: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sectores/crear', methods=['POST', 'OPTIONS'])
@cross_origin()
def crear_sector():
    """Crea un nuevo sector personalizado"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'OK'}), 200
    
    try:
        if not sector_manager:
            return jsonify({
                'success': False,
                'error': 'Sector Manager no disponible'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Datos JSON requeridos'
            }), 400
        
        nombre = data.get('nombre', '').strip()
        numeros = data.get('numeros', [])
        
        # Validar entrada
        if not nombre:
            return jsonify({
                'success': False,
                'error': 'Nombre del sector es requerido'
            }), 400
        
        if not numeros or not isinstance(numeros, list):
            return jsonify({
                'success': False,
                'error': 'Lista de números es requerida'
            }), 400
        
        # Procesar números si vienen como string separado por comas
        if len(numeros) == 1 and isinstance(numeros[0], str) and ',' in numeros[0]:
            if number_processor:
                numeros_procesados = procesar_numeros_rapido(numeros[0])
                numeros = numeros_procesados
            else:
                try:
                    numeros = [int(n.strip()) for n in numeros[0].split(',') if n.strip().isdigit()]
                except:
                    return jsonify({
                        'success': False,
                        'error': 'Error al procesar números separados por comas'
                    }), 400
        
        # Crear sector
        exito = sector_manager.crear_sector(nombre, numeros)
        
        if exito:
            return jsonify({
                'success': True,
                'message': f'Sector "{nombre}" creado exitosamente',
                'sector': {
                    'nombre': nombre,
                    'numeros': numeros,
                    'cantidad_numeros': len(numeros)
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Error al crear el sector'
            }), 500
            
    except Exception as e:
        print(f"Error al crear sector: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sectores/eliminar/<string:nombre>', methods=['DELETE', 'OPTIONS'])
@cross_origin()
def eliminar_sector(nombre):
    """Elimina un sector personalizado"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'OK'}), 200
    
    try:
        if not sector_manager:
            return jsonify({
                'success': False,
                'error': 'Sector Manager no disponible'
            }), 503
        
        if not nombre:
            return jsonify({
                'success': False,
                'error': 'Nombre del sector es requerido'
            }), 400
        
        exito = sector_manager.eliminar_sector(nombre)
        
        if exito:
            return jsonify({
                'success': True,
                'message': f'Sector "{nombre}" eliminado exitosamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Error al eliminar el sector "{nombre}" o no existe'
            }), 404
            
    except Exception as e:
        print(f"Error al eliminar sector: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sectores/estadisticas', methods=['GET', 'OPTIONS'])
@cross_origin()
def obtener_estadisticas_sectores():
    """Obtiene estadísticas detalladas de todos los sectores"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'OK'}), 200
    
    try:
        if not sector_manager:
            return jsonify({
                'success': False,
                'error': 'Sector Manager no disponible'
            }), 503
        
        estadisticas = sector_manager.obtener_estadisticas_sectores()
        
        # Agregar métricas adicionales
        total_aciertos = sum(stats.get('aciertos_totales', 0) for stats in estadisticas.values())
        
        mejores_sectores = sorted(
            [(nombre, stats) for nombre, stats in estadisticas.items()],
            key=lambda x: x[1].get('aciertos_totales', 0),
            reverse=True
        )[:5]
        
        return jsonify({
            'success': True,
            'estadisticas_por_sector': estadisticas,
            'resumen': {
                'total_sectores': len(estadisticas),
                'total_aciertos': total_aciertos,
                'mejores_sectores': [
                    {
                        'nombre': nombre,
                        'aciertos': stats.get('aciertos_totales', 0),
                        'cantidad_numeros': stats.get('cantidad_numeros', 0)
                    }
                    for nombre, stats in mejores_sectores
                ]
            }
        }), 200
        
    except Exception as e:
        print(f"Error al obtener estadísticas de sectores: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sectores/resetear-conteos', methods=['POST', 'OPTIONS'])
@cross_origin()
def resetear_conteos_sectores():
    """Resetea los conteos de todos los sectores a 0"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'OK'}), 200
    
    try:
        if not sector_manager:
            return jsonify({
                'success': False,
                'error': 'Sector Manager no disponible'
            }), 503
        
        data = request.get_json() or {}
        confirmacion = data.get('confirmar', False)
        
        if not confirmacion:
            return jsonify({
                'success': False,
                'error': 'Confirmación requerida para resetear conteos',
                'required_param': 'confirmar: true'
            }), 400
        
        exito = sector_manager.resetear_conteos()
        
        if exito:
            return jsonify({
                'success': True,
                'message': 'Conteos de sectores reseteados exitosamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Error al resetear conteos'
            }), 500
            
    except Exception as e:
        print(f"Error al resetear conteos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sectores/analizar-numero/<int:numero>', methods=['GET', 'OPTIONS'])
@cross_origin()
def analizar_numero_en_sectores(numero):
    """Analiza en qué sectores se encuentra un número específico"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'OK'}), 200
    
    try:
        if not sector_manager:
            return jsonify({
                'success': False,
                'error': 'Sector Manager no disponible'
            }), 503
        
        if not (0 <= numero <= 36):
            return jsonify({
                'success': False,
                'error': 'Número debe estar entre 0 y 36'
            }), 400
        
        sectores_que_contienen = []
        for nombre, sector in sector_manager.listar_sectores().items():
            if numero in sector.numeros:
                conteo = sector_manager.obtener_conteo_sector(nombre)
                sectores_que_contienen.append({
                    'nombre': nombre,
                    'cantidad_numeros': len(sector.numeros),
                    'aciertos_totales': conteo,
                    'probabilidad_teorica': len(sector.numeros) / 37
                })
        
        # Obtener color del número
        color = 'Desconocido'
        if number_processor:
            color = number_processor.obtener_color_numero(numero)
        
        return jsonify({
            'success': True,
            'numero': numero,
            'color': color,
            'sectores_que_contienen': sectores_que_contienen,
            'total_sectores_con_numero': len(sectores_que_contienen)
        }), 200
        
    except Exception as e:
        print(f"Error al analizar número en sectores: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Endpoint para purgar todas las estadísticas
@app.route('/purge-statistics', methods=['POST', 'OPTIONS'])
@cross_origin()
def purge_statistics():
    """Purga todas las estadísticas de la base de datos"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'OK'}), 200
    
    try:
        operations_completed = {}
        
        # 1. Truncar tabla de números individuales (mantiene estructura pero borra datos)
        if supabase_client:
            try:
                supabase_client.table('roulette_numbers_individual').delete().neq('id', 0).execute()
                operations_completed['roulette_numbers_individual'] = True
                print("✅ Tabla roulette_numbers_individual purgada")
            except Exception as e:
                print(f"⚠️ Error al purgar roulette_numbers_individual: {e}")
                operations_completed['roulette_numbers_individual'] = False
        else:
            operations_completed['roulette_numbers_individual'] = False
            print("⚠️ Cliente Supabase no disponible para purgar roulette_numbers_individual")
        
        # 2. Truncar tabla de historial (mantiene estructura pero borra datos)
        if supabase_client:
            try:
                supabase_client.table('roulette_history').delete().neq('id', 0).execute()
                operations_completed['roulette_history'] = True
                print("✅ Tabla roulette_history purgada")
            except Exception as e:
                print(f"⚠️ Error al purgar roulette_history: {e}")
                operations_completed['roulette_history'] = False
        else:
            operations_completed['roulette_history'] = False
            print("⚠️ Cliente Supabase no disponible para purgar roulette_history")
        
        # 3. Resetear analizador global si existe
        global analizador
        if analizador:
            try:
                analizador.historial_numeros = []
                analizador.frecuencia_numeros = {}
                analizador.conteo_color = {"rojo": 0, "negro": 0, "verde": 0}
                analizador.conteo_par_impar = {"par": 0, "impar": 0}
                analizador.conteo_columnas = {"columna_1": 0, "columna_2": 0, "columna_3": 0}
                analizador.conteo_docenas = {"docena_1": 0, "docena_2": 0, "docena_3": 0}
                analizador.numeros_calientes = []
                analizador.numeros_frios = []
                analizador.ultimos_numeros = []
                operations_completed['analizador_global'] = True
                print("✅ Analizador global reseteado")
            except Exception as e:
                print(f"⚠️ Error al resetear analizador global: {e}")
                operations_completed['analizador_global'] = False
        else:
            operations_completed['analizador_global'] = False
            print("⚠️ Analizador global no disponible")
        
        # 4. Resetear predictor ML avanzado si existe
        global advanced_ml_predictor
        if advanced_ml_predictor:
            try:
                # Marcar como no entrenado para forzar re-entrenamiento
                advanced_ml_predictor.is_trained = False
                advanced_ml_predictor.models = {}
                advanced_ml_predictor.ensemble_weights = {}
                operations_completed['ml_predictor'] = True
                print("✅ Predictor ML avanzado reseteado")
            except Exception as e:
                print(f"⚠️ Error al resetear predictor ML: {e}")
                operations_completed['ml_predictor'] = False
        else:
            operations_completed['ml_predictor'] = False
            print("⚠️ Predictor ML avanzado no disponible")
        
        # 5. Resetear victory trainer si existe
        global victory_trainer
        if victory_trainer:
            try:
                victory_trainer.victories = []
                operations_completed['victory_trainer'] = True
                print("✅ Victory trainer reseteado")
            except Exception as e:
                print(f"⚠️ Error al resetear victory trainer: {e}")
                operations_completed['victory_trainer'] = False
        else:
            operations_completed['victory_trainer'] = False
            print("⚠️ Victory trainer no disponible")
        
        # 6. Resetear evaluador de predicciones si existe
        global prediction_evaluator
        if prediction_evaluator:
            try:
                prediction_evaluator.reset_statistics()
                operations_completed['prediction_evaluator'] = True
                print("✅ Evaluador de predicciones reseteado")
            except Exception as e:
                print(f"⚠️ Error al resetear evaluador de predicciones: {e}")
                operations_completed['prediction_evaluator'] = False
        else:
            operations_completed['prediction_evaluator'] = False
            print("⚠️ Evaluador de predicciones no disponible")
        
        # Contar operaciones exitosas
        successful_operations = sum(1 for success in operations_completed.values() if success)
        total_operations = len(operations_completed)
        
        return jsonify({
            'success': True,
            'message': f'Purga completada: {successful_operations}/{total_operations} operaciones exitosas',
            'operations_completed': operations_completed,
            'details': {
                'database_tables_purged': operations_completed.get('roulette_numbers_individual', False) and operations_completed.get('roulette_history', False),
                'global_variables_reset': operations_completed.get('analizador_global', False) and operations_completed.get('ml_predictor', False) and operations_completed.get('victory_trainer', False),
                'total_successful': successful_operations,
                'total_attempted': total_operations
            }
        }), 200
        
    except Exception as e:
        print(f"Error al purgar estadísticas: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error al purgar estadísticas: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Iniciar el sistema de purga automática
    iniciar_purga_automatica()
    
    port = int(os.environ.get("PORT", 5001))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        use_reloader=True,
        threaded=True
    ) 