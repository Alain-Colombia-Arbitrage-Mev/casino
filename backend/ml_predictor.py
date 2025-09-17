"""
ML Predictor para el Analizador de Ruleta
Implementa modelos de aprendizaje automático para predecir números basados en patrones históricos.
"""

import numpy as np
import pandas as pd
import joblib
import os
from typing import List, Dict, Union, Tuple, Any
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
import pickle
import warnings
import random
warnings.filterwarnings("ignore")

# Importación condicional de TensorFlow para evitar problemas de compatibilidad
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import Dense, LSTM, Dropout
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    tensorflow_available = True
    print("TensorFlow importado correctamente.")
except ImportError:
    tensorflow_available = False
    print("TensorFlow no disponible. Las funciones de redes neuronales no funcionarán.")

# Constantes para crear features
MAX_SECUENCIA = 10  # Cuántos giros anteriores consideramos para el historial
RUEDA_EUROPEA = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]

# Rutas para guardar/cargar modelos
MODELO_DIR = os.path.join(os.path.dirname(__file__), "modelos")
if not os.path.exists(MODELO_DIR):
    os.makedirs(MODELO_DIR)

MODELO_MARKOV_PATH = os.path.join(MODELO_DIR, "modelo_markov.joblib")
MODELO_RF_PATH = os.path.join(MODELO_DIR, "modelo_rf.joblib")
MODELO_LSTM_PATH = os.path.join(MODELO_DIR, "modelo_lstm.h5")
SCALER_PATH = os.path.join(MODELO_DIR, "scaler.joblib")
LSTM_ENCODER_PATH = os.path.join(MODELO_DIR, "lstm_encoder.joblib")
RF_ENCODER_PATH = os.path.join(MODELO_DIR, "rf_encoder.joblib")

class ModeloMarkov:
    """Modelo basado en cadenas de Markov para predecir probabilidades de transición entre números."""
    
    def __init__(self):
        self.matriz_transicion = {}  # {numero_anterior: {numero_siguiente: probabilidad}}
        self.contador_ocurrencias = {}  # {numero: cantidad_total}
        self.ultimo_numero = None
    
    def entrenar(self, historial: List[int]):
        """Entrena el modelo Markov con el historial de números."""
        if len(historial) < 2:
            return
            
        # Reiniciar si entrenamos desde cero
        self.matriz_transicion = {}
        self.contador_ocurrencias = {}
        
        # Contar transiciones
        for i in range(len(historial) - 1):
            numero_actual = historial[i]
            numero_siguiente = historial[i + 1]
            
            # Inicializar si es la primera vez que vemos este número
            if numero_actual not in self.matriz_transicion:
                self.matriz_transicion[numero_actual] = {}
            
            # Incrementar contador de transición
            self.matriz_transicion[numero_actual][numero_siguiente] = \
                self.matriz_transicion[numero_actual].get(numero_siguiente, 0) + 1
            
            # Actualizar contador general
            self.contador_ocurrencias[numero_actual] = \
                self.contador_ocurrencias.get(numero_actual, 0) + 1
        
        # Añadir último número al contador
        self.contador_ocurrencias[historial[-1]] = \
            self.contador_ocurrencias.get(historial[-1], 0) + 1
        
        # Convertir conteos a probabilidades
        for num_actual, transiciones in self.matriz_transicion.items():
            total_transiciones = sum(transiciones.values())
            for num_siguiente in transiciones:
                transiciones[num_siguiente] /= total_transiciones
        
        self.ultimo_numero = historial[-1]
    
    def predecir(self, ultimo_numero=None, top_n=5) -> List[Tuple[int, float]]:
        """
        Predice los próximos números más probables.
        
        Args:
            ultimo_numero: Número desde el cual predecir (usa el último del entrenamiento si es None)
            top_n: Cantidad de predicciones a devolver
            
        Returns:
            Lista de tuplas (numero, probabilidad) ordenadas por probabilidad
        """
        if ultimo_numero is None:
            ultimo_numero = self.ultimo_numero
            
        if ultimo_numero is None or ultimo_numero not in self.matriz_transicion:
            # Si no tenemos datos para este número, usamos la distribución general
            total_numeros = sum(self.contador_ocurrencias.values())
            if total_numeros == 0:
                return [(0, 1/37)]  # Probabilidad uniforme si no hay datos
                
            probabilidades = {num: count/total_numeros 
                             for num, count in self.contador_ocurrencias.items()}
        else:
            # Usar la matriz de transición
            probabilidades = self.matriz_transicion[ultimo_numero]
        
        # Ordenar por probabilidad
        pred_ordenadas = sorted(probabilidades.items(), 
                               key=lambda x: x[1], reverse=True)
        
        return pred_ordenadas[:top_n]
    
    def guardar(self):
        """Guarda el modelo en disco."""
        modelo_data = {
            'matriz_transicion': self.matriz_transicion,
            'contador_ocurrencias': self.contador_ocurrencias,
            'ultimo_numero': self.ultimo_numero
        }
        joblib.dump(modelo_data, MODELO_MARKOV_PATH)
    
    def cargar(self) -> bool:
        """Carga el modelo desde disco. Retorna True si fue exitoso."""
        try:
            if os.path.exists(MODELO_MARKOV_PATH):
                modelo_data = joblib.load(MODELO_MARKOV_PATH)
                self.matriz_transicion = modelo_data['matriz_transicion']
                self.contador_ocurrencias = modelo_data['contador_ocurrencias']
                self.ultimo_numero = modelo_data['ultimo_numero']
                return True
            return False
        except Exception as e:
            print(f"Error al cargar modelo Markov: {e}")
            return False

class MLPredictor:
    """
    Clase para realizar predicciones de números de ruleta usando diferentes modelos.
    """
    
    # Constantes necesarias para los cálculos
    RUEDA_EUROPEA = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
    NUMEROS_ROJOS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    NUMEROS_NEGROS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
    
    def __init__(self, load_models=True):
        """Inicializa el predictor ML."""
        # Crear directorio si no existe
        os.makedirs(MODELO_DIR, exist_ok=True)
        
        # Inicializar modelos
        self.modelo_rf = None
        self.rf_encoder = None
        self.rf_trained = False
        
        self.modelo_lstm = None
        self.lstm_encoder = None
        self.lstm_trained = False
        
        # Cargar modelos si existen
        if os.path.exists(MODELO_RF_PATH):
            self.modelo_rf = joblib.load(MODELO_RF_PATH)
            print("Modelo Random Forest cargado.")
            self.rf_trained = True
        
        if os.path.exists(RF_ENCODER_PATH):
            self.rf_encoder = joblib.load(RF_ENCODER_PATH)
            print("Encoder RF cargado.")
        
        # Cargar modelos LSTM solo si TensorFlow está disponible
        if tensorflow_available:
            if os.path.exists(MODELO_LSTM_PATH):
                try:
                    self.modelo_lstm = load_model(MODELO_LSTM_PATH)
                    print("Modelo LSTM cargado.")
                    self.lstm_trained = True
                except Exception as e:
                    print(f"Error al cargar modelo LSTM: {e}")
            
            if os.path.exists(LSTM_ENCODER_PATH):
                try:
                    self.lstm_encoder = joblib.load(LSTM_ENCODER_PATH)
                    print("Encoder LSTM cargado.")
                except Exception as e:
                    print(f"Error al cargar encoder LSTM: {e}")
        else:
            print("TensorFlow no disponible - no se cargarán modelos LSTM.")
        
    def _extraer_features(self, historial_objetos: List[Any]) -> pd.DataFrame:
        """
        Extrae características para el modelo de Random Forest.
        
        Args:
            historial_objetos: Lista de objetos NumeroRoleta del analizador
            
        Returns:
            DataFrame con features
        """
        if not historial_objetos:
            return pd.DataFrame()
            
        # Convertir historial a números enteros
        historial_numeros = [obj.numero for obj in historial_objetos]
        
        features = []
        for i in range(len(historial_numeros)):
            # Tomamos los últimos 5 números como features (rellenamos con -1 si no hay suficientes)
            ultimos_5 = [-1] * 5
            for j in range(min(5, i + 1)):
                ultimos_5[5-j-1] = historial_numeros[i-j]
                
            # Añadimos otras características
            num_actual = historial_objetos[i]
            row = {
                'num_1': ultimos_5[0],
                'num_2': ultimos_5[1],
                'num_3': ultimos_5[2],
                'num_4': ultimos_5[3],
                'num_5': ultimos_5[4],
                'color': num_actual.cor,
                'paridad': num_actual.par_impar,
                'columna': num_actual.coluna,
                'docena': num_actual.duzia,
                'terminal': num_actual.terminal,
                'sector': num_actual.setor
            }
            features.append(row)
            
        return pd.DataFrame(features)
    
    def _preparar_datos_rf(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara los datos para el modelo Random Forest."""
        if df.empty:
            return np.array([]), np.array([])
            
        # Separar features y target
        y = df.iloc[1:]['num_1'].values  # El número que salió
        X = df.iloc[:-1].copy()  # Características hasta el penúltimo
        
        # Codificar variables categóricas
        categoricas = ['color', 'paridad', 'columna', 'docena', 'sector']
        dummies_por_columna = {}
        
        for col in categoricas:
            dummies = pd.get_dummies(X[col], prefix=col, dummy_na=True)
            dummies_por_columna[col] = dummies.columns.tolist()
            X = pd.concat([X.drop(col, axis=1), dummies], axis=1)
        
        # Guardar las columnas para usar en predicción
        self.columnas_rf = X.columns.tolist()
        self.dummies_por_columna = dummies_por_columna
        
        return X.values, y

    def _preparar_datos_prediccion_rf(self, df: pd.DataFrame) -> np.ndarray:
        """Prepara los datos para predicción asegurando todas las columnas del entrenamiento."""
        if not hasattr(self, 'columnas_rf') or not hasattr(self, 'dummies_por_columna'):
            raise ValueError("El modelo RF no ha sido entrenado correctamente")
        
        X = df.copy()
        categoricas = ['color', 'paridad', 'columna', 'docena', 'sector']
        
        # Crear dummies para cada columna categórica
        for col in categoricas:
            # Crear dummies con las mismas columnas que en entrenamiento
            dummies = pd.get_dummies(X[col], prefix=col, dummy_na=True)
            expected_cols = self.dummies_por_columna[col]
            
            # Añadir columnas faltantes con 0s
            for expected_col in expected_cols:
                if expected_col not in dummies.columns:
                    dummies[expected_col] = 0
                
            # Reordenar columnas para que coincidan con el entrenamiento
            dummies = dummies[expected_cols]
            X = pd.concat([X.drop(col, axis=1), dummies], axis=1)
        
        # Asegurar que todas las columnas del entrenamiento estén presentes y en el mismo orden
        for col in self.columnas_rf:
            if col not in X.columns:
                X[col] = 0
        
        return X[self.columnas_rf].values
    
    def _preparar_datos_lstm(self, historial: List[int]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara los datos para el modelo LSTM."""
        if not historial or len(historial) < MAX_SECUENCIA + 1:
            return np.array([]), np.array([])
            
        X, y = [], []
        
        # Crear secuencias de entrenamiento
        for i in range(len(historial) - MAX_SECUENCIA):
            X.append(historial[i:i + MAX_SECUENCIA])
            y.append(historial[i + MAX_SECUENCIA])
            
        # Codificar números (one-hot o normalización)
        X_array = np.array(X)
        y_array = np.array(y)
        
        if self.lstm_encoder is None:
            self.lstm_encoder = MinMaxScaler(feature_range=(0, 1))
            # Adaptamos el escalador a todos los posibles valores de ruleta (0-36)
            self.lstm_encoder.fit(np.array(list(range(37))).reshape(-1, 1))
            joblib.dump(self.lstm_encoder, LSTM_ENCODER_PATH)
            
        # Normalizar valores
        X_scaled = np.array([self.lstm_encoder.transform(x.reshape(-1, 1)).flatten() 
                            for x in X_array])
        
        # Reshape para LSTM [muestras, timesteps, features]
        X_reshaped = X_scaled.reshape(X_scaled.shape[0], MAX_SECUENCIA, 1)
        
        return X_reshaped, y_array
        
    def entrenar_todos(self, historial_objetos: List[Any]):
        """Entrena todos los modelos disponibles."""
        if not historial_objetos or len(historial_objetos) < MAX_SECUENCIA + 1:
            print("Historial insuficiente para entrenar modelos.")
            return False
            
        # Extraer solo los números del historial
        historial_numeros = [obj.numero for obj in historial_objetos]
        
        # 1. Entrenar Markov
        self.modelo_markov.entrenar(historial_numeros)
        self.modelo_markov.guardar()
        
        # 2. Entrenar Random Forest
        df_features = self._extraer_features(historial_objetos)
        X_rf, y_rf = self._preparar_datos_rf(df_features)
        
        if len(X_rf) > 0 and len(y_rf) > 0:
            self.modelo_rf = RandomForestClassifier(n_estimators=100, random_state=42)
            self.modelo_rf.fit(X_rf, y_rf)
            joblib.dump(self.modelo_rf, MODELO_RF_PATH)
            print("Modelo Random Forest entrenado y guardado.")
        
        # 3. Entrenar LSTM
        X_lstm, y_lstm = self._preparar_datos_lstm(historial_numeros)
        
        if len(X_lstm) > 0 and len(y_lstm) > 0:
            # Definir modelo LSTM
            self.modelo_lstm = Sequential([
                LSTM(50, activation='relu', input_shape=(MAX_SECUENCIA, 1), return_sequences=True),
                Dropout(0.2),
                LSTM(50, activation='relu'),
                Dropout(0.2),
                Dense(37, activation='softmax')  # 37 posibles outputs (0-36)
            ])
            
            self.modelo_lstm.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy']
            )
            
            # Entrenar con early stopping para evitar overfitting
            early_stop = tf.keras.callbacks.EarlyStopping(
                monitor='val_loss', patience=5, restore_best_weights=True
            )
            
            self.modelo_lstm.fit(
                X_lstm, y_lstm,
                epochs=50,
                batch_size=32,
                validation_split=0.2,
                callbacks=[early_stop],
                verbose=1
            )
            
            self.modelo_lstm.save(MODELO_LSTM_PATH)
            print("Modelo LSTM entrenado y guardado.")
            
        return True
            
    def predecir(self, historial, solo_numeros=False):
        """
        Realiza predicciones con todos los modelos disponibles.
        
        Args:
            historial: Lista de números o instancias de NumeroRuleta
            solo_numeros: Si es True, devuelve sólo el número final, no probabilidades completas
            
        Returns:
            dict: Predicciones de cada modelo y predicción de conjunto
        """
        if not historial:
            return {"error": "Historial vacío"}
        
        # Convertir historial a formatos necesarios
        historial_limpio = self._preparar_datos(historial)
        
        try:
            # Usar el modelo Random Forest si está disponible
            rf_prediccion = None
            if self.rf_model:
                rf_prediccion = self._predecir_con_random_forest(historial_limpio)
            
            # Usar el modelo LSTM si está disponible
            lstm_prediccion = None
            if self.lstm_model:
                lstm_prediccion = self._predecir_con_lstm(historial_limpio)
                
            # Usar cadenas de Markov
            markov_prediccion = self._predecir_con_markov(historial_limpio)
            
            # Generar predicción de conjunto mediante ponderación
            prediccion_ponderada = self._generar_prediccion_ponderada(
                rf=rf_prediccion,
                lstm=lstm_prediccion,
                markov=markov_prediccion
            )
            
            # Generar grupos de predicciones de diferentes tamaños
            grupos_predicciones = self._generar_grupos_predicciones(
                historial_limpio, 
                rf_prediccion, 
                lstm_prediccion, 
                markov_prediccion, 
                prediccion_ponderada
            )
            
            resultado = {
                "random_forest": rf_prediccion if rf_prediccion is not None else None,
                "lstm": lstm_prediccion if lstm_prediccion is not None else None,
                "markov": markov_prediccion if markov_prediccion is not None else None,
                "ensemble": prediccion_ponderada,
                "grupos": grupos_predicciones
            }
            
            if solo_numeros:
                # Convertir sólo a números
                for key in resultado.keys():
                    if key != "grupos" and resultado[key] is not None:
                        resultado[key] = int(resultado[key])
            
            return resultado
        
        except Exception as e:
            print(f"Error en predicción ML: {e}")
            return {"error": str(e)}

    def _generar_grupos_predicciones(self, historial, rf_pred=None, lstm_pred=None, markov_pred=None, ensemble_pred=None):
        """
        Genera grupos de números de diferentes tamaños basados en las predicciones y análisis estadístico.
        
        Args:
            historial: Lista de números limpios
            rf_pred: Predicción del modelo Random Forest
            lstm_pred: Predicción del modelo LSTM
            markov_pred: Predicción de la cadena de Markov
            ensemble_pred: Predicción ponderada del conjunto
            
        Returns:
            dict: Grupos de números de diferentes tamaños
        """
        # Calcular frecuencias de números en el historial reciente
        frecuencias = {}
        for i in range(37):  # Números 0-36
            frecuencias[i] = 0
        
        for num in historial[:20]:  # Considerar solo los últimos 20 giros
            if 0 <= num <= 36:
                frecuencias[num] += 1
        
        # Ordenar números por frecuencia
        numeros_ordenados = sorted(frecuencias.items(), key=lambda x: x[1], reverse=True)
        
        # Calcular vecinos de las predicciones principales
        vecinos = set()
        predicciones_base = []
        
        # Añadir predicciones de los diferentes modelos
        if ensemble_pred is not None:
            predicciones_base.append(int(ensemble_pred))
        if rf_pred is not None:
            predicciones_base.append(int(rf_pred))
        if lstm_pred is not None:
            predicciones_base.append(int(lstm_pred))
        if markov_pred is not None:
            predicciones_base.append(int(markov_pred))
        
        # Eliminar duplicados
        predicciones_base = list(set(predicciones_base))
        
        # Añadir vecinos en la rueda
        for pred in predicciones_base:
            idx = self.RUEDA_EUROPEA.index(pred)
            for i in range(-3, 4):  # Vecinos a 3 posiciones de distancia
                vecino_idx = (idx + i) % len(self.RUEDA_EUROPEA)
                vecinos.add(self.RUEDA_EUROPEA[vecino_idx])
        
        # Crear los grupos de diferentes tamaños
        grupo_20 = []
        grupo_12 = []
        grupo_8 = []
        grupo_6 = []
        grupo_4 = []
        
        # Priorizar predicciones de los modelos
        for pred in predicciones_base:
            if pred not in grupo_4 and len(grupo_4) < 4:
                grupo_4.append(pred)
            if pred not in grupo_6 and len(grupo_6) < 6:
                grupo_6.append(pred)
            if pred not in grupo_8 and len(grupo_8) < 8:
                grupo_8.append(pred)
            if pred not in grupo_12 and len(grupo_12) < 12:
                grupo_12.append(pred)
            if pred not in grupo_20 and len(grupo_20) < 20:
                grupo_20.append(pred)
        
        # Añadir vecinos
        for vecino in vecinos:
            if vecino not in grupo_6 and len(grupo_6) < 6:
                grupo_6.append(vecino)
            if vecino not in grupo_8 and len(grupo_8) < 8:
                grupo_8.append(vecino)
            if vecino not in grupo_12 and len(grupo_12) < 12:
                grupo_12.append(vecino)
            if vecino not in grupo_20 and len(grupo_20) < 20:
                grupo_20.append(vecino)
        
        # Completar con números frecuentes
        for num, _ in numeros_ordenados:
            if num not in grupo_4 and len(grupo_4) < 4:
                grupo_4.append(num)
            if num not in grupo_6 and len(grupo_6) < 6:
                grupo_6.append(num)
            if num not in grupo_8 and len(grupo_8) < 8:
                grupo_8.append(num)
            if num not in grupo_12 and len(grupo_12) < 12:
                grupo_12.append(num)
            if num not in grupo_20 and len(grupo_20) < 20:
                grupo_20.append(num)
        
        # NUEVO: Agregar 0 como protección en todos los grupos (si no está ya incluido)        if 0 not in grupo_4:            grupo_4 = [0] + grupo_4[:3]   # Mantener 4 números incluyendo el 0        if 0 not in grupo_6:            grupo_6 = [0] + grupo_6[:5]   # Mantener 6 números incluyendo el 0        if 0 not in grupo_8:            grupo_8 = [0] + grupo_8[:7]   # Mantener 8 números incluyendo el 0        if 0 not in grupo_12:            grupo_12 = [0] + grupo_12[:11] # Mantener 12 números incluyendo el 0        if 0 not in grupo_20:            grupo_20 = [0] + grupo_20[:19] # Mantener 20 números incluyendo el 0                return {            "grupo_20": grupo_20,            "grupo_12": grupo_12,            "grupo_8": grupo_8,            "grupo_6": grupo_6,            "grupo_4": grupo_4        }
        
    def predecir_markov(self, cantidad=5) -> Tuple[List[int], List[float]]:
        """
        Predice números usando el modelo Markov.
        
        Args:
            cantidad: Número de predicciones a generar
            
        Returns:
            Tupla (numeros, probabilidades)
        """
        if not self.modelo_markov:
            return [0] * cantidad, [1/37] * cantidad
            
        pred = self.modelo_markov.predecir(top_n=cantidad)
        if not pred:
            return [0] * cantidad, [1/37] * cantidad
            
        return [p[0] for p in pred], [p[1] for p in pred]
    
    def entrenar_random_forest(self, historial_objetos: List[Any]):
        """Entrena solo el modelo Random Forest."""
        if not historial_objetos or len(historial_objetos) < 2:
            print("Historial insuficiente para entrenar Random Forest.")
            return False
            
        df_features = self._extraer_features(historial_objetos)
        X_rf, y_rf = self._preparar_datos_rf(df_features)
        
        if len(X_rf) > 0 and len(y_rf) > 0:
            self.modelo_rf = RandomForestClassifier(n_estimators=100, random_state=42)
            self.modelo_rf.fit(X_rf, y_rf)
            
            # Guardar el modelo y las columnas
            modelo_data = {
                'modelo_rf': self.modelo_rf,
                'columnas_rf': self.columnas_rf,
                'dummies_por_columna': self.dummies_por_columna
            }
            joblib.dump(modelo_data, MODELO_RF_PATH)
            print("Modelo Random Forest entrenado y guardado con información de columnas.")
            return True
        return False
    
    def entrenar_lstm(self, historial_objetos: List[Any]):
        """Entrena solo el modelo LSTM."""
        if not historial_objetos or len(historial_objetos) < MAX_SECUENCIA + 1:
            print("Historial insuficiente para entrenar LSTM.")
            return False
            
        historial_numeros = [obj.numero for obj in historial_objetos]
        X_lstm, y_lstm = self._preparar_datos_lstm(historial_numeros)
        
        if len(X_lstm) > 0 and len(y_lstm) > 0:
            self.modelo_lstm = Sequential([
                LSTM(50, activation='relu', input_shape=(MAX_SECUENCIA, 1), return_sequences=True),
                Dropout(0.2),
                LSTM(50, activation='relu'),
                Dropout(0.2),
                Dense(37, activation='softmax')  # 37 posibles outputs (0-36)
            ])
            
            self.modelo_lstm.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy']
            )
            
            early_stop = tf.keras.callbacks.EarlyStopping(
                monitor='val_loss', patience=5, restore_best_weights=True
            )
            
            self.modelo_lstm.fit(
                X_lstm, y_lstm,
                epochs=50,
                batch_size=32,
                validation_split=0.2,
                callbacks=[early_stop],
                verbose=1
            )
            
            self.modelo_lstm.save(MODELO_LSTM_PATH)
            print("Modelo LSTM entrenado y guardado.")
            return True
        return False
    
    def predecir_random_forest(self, cantidad=5) -> Tuple[List[int], List[float]]:
        """
        Predice números usando el modelo Random Forest.
        
        Args:
            cantidad: Número de predicciones a generar
            
        Returns:
            Tupla (numeros, probabilidades)
        """
        if self.modelo_rf is None:
            return [0] * cantidad, [1/37] * cantidad
            
        # Obtener el último objeto del historial para predicción
        ultimo_estado = None
        for i in range(1, 10):  # Intentar con los últimos estados disponibles
            try:
                ultimo_estado = self._extraer_features([self.modelo_rf.history_[-i]])
                break
            except (AttributeError, IndexError):
                continue
                
        if ultimo_estado is None or ultimo_estado.empty:
            return [0] * cantidad, [1/37] * cantidad
            
        # Preparar datos
        df_ultimo = self._extraer_features([ultimo_estado])
        X_pred = self._preparar_datos_prediccion_rf(df_ultimo)
        
        # Predecir probabilidades
        pred_probs = self.modelo_rf.predict_proba(X_pred)
        
        # Obtener los N números más probables
        indices_top = np.argsort(pred_probs[0])[-cantidad:][::-1]
        numeros_top = [self.modelo_rf.classes_[i] for i in indices_top]
        probs_top = [pred_probs[0][i] for i in indices_top]
        
        return numeros_top, probs_top
    
    def predecir_lstm(self, cantidad=5) -> List[int]:
        """
        Predice números usando el modelo LSTM.
        
        Args:
            cantidad: Número de predicciones a generar
            
        Returns:
            Lista de números predichos
        """
        if self.modelo_lstm is None:
            return [0] * cantidad
            
        # Obtener secuencia de entrada
        secuencia = [0] * MAX_SECUENCIA  # Secuencia por defecto
        
        # TODO: Mejorar para obtener una secuencia real del historial disponible
        
        # Normalizar
        seq_scaled = self.lstm_encoder.transform(np.array(secuencia).reshape(-1, 1)).flatten()
        
        # Reshape para LSTM [1, timesteps, features]
        seq_reshaped = seq_scaled.reshape(1, MAX_SECUENCIA, 1)
        
        # Predecir probabilidades
        prediccion = self.modelo_lstm.predict(seq_reshaped)[0]
        
        # Obtener los N números más probables
        indices_top = np.argsort(prediccion)[-cantidad:][::-1]
        
        return indices_top.tolist()
    
    def predecir_ensemble(self, cantidad=5) -> List[int]:
        """
        Predice números combinando todos los modelos disponibles.
        
        Args:
            cantidad: Número de predicciones a generar
            
        Returns:
            Lista de números predichos
        """
        # Obtener predicciones de cada modelo disponible
        numeros_ponderados = {}
        
        # Markov
        pred_markov, prob_markov = self.predecir_markov(cantidad * 2)  # Obtener más para tener variedad
        for i, (num, prob) in enumerate(zip(pred_markov, prob_markov)):
            peso = self.calcular_confianza_markov() * (1 / (i + 1))
            numeros_ponderados[num] = numeros_ponderados.get(num, 0) + peso
        
        # Random Forest
        if self.modelo_rf is not None:
            pred_rf, prob_rf = self.predecir_random_forest(cantidad * 2)
            for i, (num, prob) in enumerate(zip(pred_rf, prob_rf)):
                peso = self.calcular_confianza_random_forest() * (1 / (i + 1))
                numeros_ponderados[num] = numeros_ponderados.get(num, 0) + peso
        
        # LSTM
        if self.modelo_lstm is not None:
            pred_lstm = self.predecir_lstm(cantidad * 2)
            for i, num in enumerate(pred_lstm):
                peso = self.calcular_confianza_lstm() * (1 / (i + 1))
                numeros_ponderados[num] = numeros_ponderados.get(num, 0) + peso
        
        # Ordenar por peso total
        top_ensemble = sorted(numeros_ponderados.items(), key=lambda x: x[1], reverse=True)[:cantidad]
        
        return [n[0] for n in top_ensemble]
    
    def calcular_confianza_markov(self) -> float:
        """Calcula un valor de confianza para el modelo Markov."""
        # Simple heurística: si tiene suficientes datos en la matriz de transición
        if hasattr(self.modelo_markov, 'matriz_transicion') and self.modelo_markov.matriz_transicion:
            return 0.8
        return 0.3
    
    def calcular_confianza_random_forest(self) -> float:
        """Calcula un valor de confianza para el modelo Random Forest."""
        if self.modelo_rf is None:
            return 0.0
        # Podría basarse en métricas de entrenamiento del modelo
        return 0.6
    
    def calcular_confianza_lstm(self) -> float:
        """Calcula un valor de confianza para el modelo LSTM."""
        if self.modelo_lstm is None:
            return 0.0
        # Podría basarse en métricas de entrenamiento del modelo
        return 0.7

    def _preparar_datos(self, historial):
        """
        Convierte el historial a un formato limpio de números enteros.
        """
        # Si es una lista de objetos NumeroRoleta
        if historial and hasattr(historial[0], 'numero'):
            return [n.numero for n in historial]
        # Si ya es una lista de números
        return historial

    def _predecir_con_random_forest(self, historial_limpio):
        """
        Realiza una predicción usando el modelo Random Forest.
        """
        if not self.rf_model or len(historial_limpio) < 10:
            return None
            
        try:
            # Construir características para el modelo
            features = self._extraer_caracteristicas_rf(historial_limpio)
            # Predecir y devolver el número más probable
            prediccion = self.rf_model.predict([features])[0]
            return prediccion
        except Exception as e:
            print(f"Error en predicción Random Forest: {e}")
            return None
            
    def _predecir_con_lstm(self, historial_limpio):
        """
        Realiza una predicción usando el modelo LSTM.
        """
        if not self.lstm_model or len(historial_limpio) < 10:
            return None
            
        try:
            # Preparar los datos para el modelo LSTM
            # Esto simplemente es un placeholder, necesitaríamos implementar la lógica real
            # basada en cómo está entrenado el modelo LSTM
            return None  # Por ahora devolvemos None hasta implementar el modelo LSTM
        except Exception as e:
            print(f"Error en predicción LSTM: {e}")
            return None
            
    def _predecir_con_markov(self, historial_limpio):
        """
        Realiza una predicción usando cadenas de Markov.
        """
        if len(historial_limpio) < 3:
            return None
            
        try:
            # Crear un diccionario de transiciones
            transiciones = {}
            for i in range(len(historial_limpio) - 1):
                estado_actual = historial_limpio[i]
                estado_siguiente = historial_limpio[i + 1]
                
                if estado_actual not in transiciones:
                    transiciones[estado_actual] = {}
                    
                if estado_siguiente not in transiciones[estado_actual]:
                    transiciones[estado_actual][estado_siguiente] = 0
                    
                transiciones[estado_actual][estado_siguiente] += 1
                
            # Obtener último número
            ultimo_numero = historial_limpio[-1]
            
            # Si no hay transiciones para el último número, elegir aleatoriamente
            if ultimo_numero not in transiciones:
                return random.randint(0, 36)
                
            # Calcular transición más probable
            transiciones_desde_ultimo = transiciones[ultimo_numero]
            max_count = 0
            prediccion = None
            
            for num, count in transiciones_desde_ultimo.items():
                if count > max_count:
                    max_count = count
                    prediccion = num
                    
            # Si no hay predicción, elegir aleatoriamente
            if prediccion is None:
                return random.randint(0, 36)
                
            return prediccion
        except Exception as e:
            print(f"Error en predicción Markov: {e}")
            return random.randint(0, 36)
            
    def _generar_prediccion_ponderada(self, rf=None, lstm=None, markov=None):
        """
        Genera una predicción ponderada basada en los diferentes modelos.
        """
        predicciones = []
        
        if rf is not None:
            predicciones.append((rf, 0.4))  # 40% de peso para Random Forest
        if lstm is not None:
            predicciones.append((lstm, 0.4))  # 40% de peso para LSTM
        if markov is not None:
            predicciones.append((markov, 0.2))  # 20% de peso para Markov
            
        if not predicciones:
            return random.randint(0, 36)
            
        # Si solo hay una predicción, usarla directamente
        if len(predicciones) == 1:
            return predicciones[0][0]
            
        # Calcular la predicción ponderada
        # En este caso simple, devolvemos la predicción con más peso
        predicciones.sort(key=lambda x: x[1], reverse=True)
        return predicciones[0][0]
        
    def _extraer_caracteristicas_rf(self, historial):
        """
        Extrae características para el modelo Random Forest.
        Esta es una función simplificada. En una implementación real,
        se extraerían características significativas del historial.
        """
        # Tomar los últimos 10 números o menos
        ultimos_n = historial[-10:] if len(historial) >= 10 else historial
        
        # Rellenar con ceros si hay menos de 10 números
        while len(ultimos_n) < 10:
            ultimos_n.insert(0, 0)
            
        # Convertir a características simples
        caracteristicas = []
        
        # Últimos números normalizados
        for num in ultimos_n:
            caracteristicas.append(num / 36)  # Normalizar a [0, 1]
            
        # Contar apariciones de ciertas características
        num_rojos = sum(1 for num in ultimos_n if num in self.NUMEROS_ROJOS)
        num_negros = sum(1 for num in ultimos_n if num in self.NUMEROS_NEGROS)
        num_pares = sum(1 for num in ultimos_n if num % 2 == 0)  # Incluir el 0 como par
        num_impares = sum(1 for num in ultimos_n if num % 2 == 1)
        
        caracteristicas.extend([
            num_rojos / len(ultimos_n),
            num_negros / len(ultimos_n),
            num_pares / len(ultimos_n),
            num_impares / len(ultimos_n)
        ])
        
        return caracteristicas 