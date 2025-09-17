# roulette_analyzer.py

# Constantes de la Ruleta (Europea con un solo cero)
RUEDA_EUROPEA = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]

# Sectores (Nombres comunes)
VOISINS_DU_ZERO = {22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25} # 17 números
TERCIOS_DEL_CILINDRO = {27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33} # 12 números (Traducción de TIERS_DU_CYLINDRE)
ORPHELINS = {1, 20, 14, 31, 9, 17, 34, 6} # 8 números
# Mantener la constante TIERS_DU_CYLINDRE para compatibilidad
TIERS_DU_CYLINDRE = TERCIOS_DEL_CILINDRO

# Nuevo sector dinámico TOP (se actualizará con los números más frecuentes)
TOP_SECTOR = set()  # Se inicializa vacío, se llenará dinámicamente

# Columnas en el tapete
COLUMNA_1 = {1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34}
COLUMNA_2 = {2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35}
COLUMNA_3 = {3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36}

class NumeroRoleta:
    def __init__(self, numero):
        if not (0 <= numero <= 36):
            raise ValueError("El número debe estar entre 0 y 36.")
        self.numero = numero
        self.terminal = self._calcular_terminal()
        self.coluna = self._calcular_coluna()
        self.duzia = self._calcular_duzia()
        self.alto_baixo = self._calcular_alto_baixo()
        self.par_impar = self._calcular_par_impar()
        self.cor = self._calcular_cor() # Rojo/Negro/Verde para el 0
        self.setor = self._calcular_setor()
        
        # Propiedades de vecinos (se calcularán con funciones auxiliares)
        self.vecinos_5_2 = None # Necesita la rueda para calcularse
        self.vecinos_0_10 = None # Necesita la rueda para calcularse
        self.vecinos_5_de_7_27 = None # Necesita la rueda para calcularse

        # Propiedades más complejas o predictivas (se definirán más adelante)
        self.puxa_ult = None 
        self.cavalo = None 
        self.lado = None # PA e VB, PB e VA

    def _calcular_terminal(self):
        return self.numero % 10

    def _calcular_coluna(self):
        if self.numero == 0:
            return None
        if self.numero in COLUMNA_1:
            return "C1"
        if self.numero in COLUMNA_2:
            return "C2"
        if self.numero in COLUMNA_3:
            return "C3"
        return None # No debería ocurrir para números 1-36

    def _calcular_duzia(self):
        if self.numero == 0:
            return None
        if 1 <= self.numero <= 12:
            return "D1"
        if 13 <= self.numero <= 24:
            return "D2"
        if 25 <= self.numero <= 36:
            return "D3"
        return None

    def _calcular_alto_baixo(self):
        if self.numero == 0:
            return None
        if 1 <= self.numero <= 18:
            return "Baixo"
        if 19 <= self.numero <= 36:
            return "Alto"
        return None

    def _calcular_par_impar(self):
        if self.numero == 0:
            return None # El cero no es par ni impar en apuestas de ruleta
        return "Par" if self.numero % 2 == 0 else "Impar"

    def _calcular_cor(self):
        rojos = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        negros = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
        if self.numero == 0:
            return "Verde"
        if self.numero in rojos:
            return "Rojo"
        if self.numero in negros:
            return "Negro"
        return None

    def _calcular_setor(self):
        if self.numero in VOISINS_DU_ZERO:
            return "Voisins du Zéro"
        if self.numero in TERCIOS_DEL_CILINDRO:
            return "Tercios del Cilindro"
        if self.numero in ORPHELINS:
            return "Orphelins"
        return None

    def __str__(self):
        return (
            f"Número: {self.numero}\n"
            f"  Terminal: {self.terminal}\n"
            f"  Coluna: {self.coluna}\n"
            f"  Duzia: {self.duzia}\n"
            f"  Alto/Baixo: {self.alto_baixo}\n"
            f"  Par/Impar: {self.par_impar}\n"
            f"  Cor: {self.cor}\n"
            f"  Setor: {self.setor}\n"
            f"  Puxa.Ult (sugeridos por este N°): {self.puxa_ult if self.puxa_ult else 'N/A'}\n"
            # Añadir más propiedades a medida que se implementen
        )

# --- Funciones Auxiliares para Cálculo de Vecinos ---
def obtener_vecinos_en_rueda(numero_central, cantidad_vecinos, rueda):
    """
    Obtiene una cantidad de vecinos a cada lado de un número en la rueda.
    Devuelve una lista de (cantidad_vecinos * 2 + 1) números.
    """
    try:
        idx_central = rueda.index(numero_central)
    except ValueError:
        return [] # El número no está en la rueda

    total_numeros_rueda = len(rueda)
    vecinos = []
    for i in range(-cantidad_vecinos, cantidad_vecinos + 1):
        idx_vecino = (idx_central + i + total_numeros_rueda) % total_numeros_rueda
        vecinos.append(rueda[idx_vecino])
    return vecinos

# --- Clase Principal del Analizador ---
class AnalizadorRuleta:
    def __init__(self, historial_max_longitud=25):
        self.historial_numeros = [] # Lista de objetos NumeroRoleta
        self.historial_max_longitud = historial_max_longitud
        self.tabla_puxa_ult = self._definir_tabla_puxa_ult()
        
        # Contadores de aciertos para las predicciones
        self.aciertos_individual = 0
        self.aciertos_grupo = 0
        self.aciertos_vecinos_0_10 = 0
        self.aciertos_vecinos_7_27 = 0
        self.total_predicciones_evaluadas = 0
        self.aciertos_color = 0

        # Estrategia Tia Lu / 33-22-11
        self.tia_lu_triggers = {11, 22, 33}
        self.tia_lu_numeros_base = {16, 33, 1, 9, 22, 18, 26, 0, 32, 30, 11, 36}
        self.tia_lu_numeros_extra_si_33 = {17, 34, 6} # Vecinos de 34 (17,6) + 34
        self._reset_estado_tia_lu() # Inicializa el estado
        self.aciertos_tia_lu = 0

        # Sectores Personalizados: ahora se cargarán desde app.py
        self.sectores_personalizados_definiciones = {} # nombre_sector -> {set de números}
        self.conteo_sectores_personalizados = {} # nombre_sector -> conteo
        
        # Sector TOP (números más frecuentes) - inicialización
        self.max_numeros_top = 8  # Máximo de números a incluir en el sector TOP
        self.top_sector = set()
        self.top_ultima_actualizacion = 0  # Contador de actualizaciones
        
        # Para llevar estadísticas
        self.conteo_columnas = {'C1': 0, 'C2': 0, 'C3': 0}
        self.conteo_docenas = {'D1': 0, 'D2': 0, 'D3': 0}
        self.conteo_paridad = {'Par': 0, 'Impar': 0}
        self.conteo_altobajo = {'Alto': 0, 'Baixo': 0}
        self.conteo_color = {'Negro': 0, 'Rojo': 0}
        self.conteo_sectores = {'Voisins du Zero': 0, 'Tercios del Cilindro': 0, 'Orphelins': 0}
        
        self.conteo_terminales = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}

    def _reset_estado_tia_lu(self):
        self.tia_lu_estado = {
            "activa": False, 
            "giros_jugados": 0, 
            "activada_con_33": False, # Si el 33 fue el SEGUNDO número que activó la estrategia
            "contador_desencadenantes_consecutivos": 0,
            "ultimo_numero_fue_desencadenante": False # Para rastrear la consecutividad
        }

    def _definir_tabla_puxa_ult(self):
        """
        Define la tabla de números que "puxan" a otros.
        Esto es un PLACEHOLDER y necesita ser definido con una estrategia real.
        Formato: {numero_que_salio: [lista_de_numeros_que_puxa]}
        """
        # Ejemplo MUY simplificado:
        return {
            0: [26, 32, 15, 4], # Si sale 0, tiende a llamar a estos
            1: [13, 14, 16, 33, 34],
            5: [10, 24, 8],
            10: [5, 8, 11, 23, 28, 13], 
            17: [25, 34, 6, 20],
            23: [8, 10, 5, 4],
            36: [13, 11, 30],
            # ... Completar con más números y sus "puxadas" según la estrategia
        }

    def _inicializar_sectores_personalizados_base(self):
        return {
            "SECTOR 1": {0, 32, 15, 19, 4, 21, 2, 25, 17},
            "SECTOR 2": {34, 6, 27, 13, 36, 11, 30, 8, 23},
            "SECTOR 3": {10, 5, 24, 16, 33, 1, 20, 14, 31},
            "SECTOR 4": {9, 22, 18, 29, 7, 28, 12, 35, 3, 26}
            # Futuro: Añadir lógica para que estos puedan ser dinámicos
        }

    def cargar_estado_sectores_personalizados(self, definiciones: dict, conteos: dict):
        self.sectores_personalizados_definiciones = definiciones
        self.conteo_sectores_personalizados = conteos
        # Asegurar que todos los sectores definidos tengan una entrada de conteo
        for nombre_sector in self.sectores_personalizados_definiciones:
            if nombre_sector not in self.conteo_sectores_personalizados:
                self.conteo_sectores_personalizados[nombre_sector] = 0

    def agregar_numero(self, numero_int):
        """
        Agrega un nuevo número al historial y realiza los cálculos de propiedades.
        """
        num_obj = NumeroRoleta(numero_int)
        
        # Calcular vecinos específicos basados en la rueda
        # "5/2: Vecinos de los números 5 y 2 en la rueda física"
        # Asumo que se refiere a X vecinos alrededor del 5 Y X vecinos alrededor del 2.
        # La especificación "5/2" es un poco ambigua, podría significar "2 vecinos del 5".
        # Por ahora, tomaré 2 vecinos a cada lado del 5 y 2 vecinos a cada lado del 2.
        num_obj.vecinos_5_2 = {
            "num_5": obtener_vecinos_en_rueda(5, 2, RUEDA_EUROPEA),
            "num_2": obtener_vecinos_en_rueda(2, 2, RUEDA_EUROPEA)
        }

        # "0/10: Vecinos del 0 y 10 en la rueda física"
        # Similarmente, tomaré 2 vecinos a cada lado.
        num_obj.vecinos_0_10 = {
            "num_0": obtener_vecinos_en_rueda(0, 2, RUEDA_EUROPEA),
            "num_10": obtener_vecinos_en_rueda(10, 2, RUEDA_EUROPEA)
        }

        # "5v7/27: 5 números vecinos del 7 y 27 en la rueda física"
        # Esto es más claro: 5 vecinos en total (2 a cada lado + el central)
        num_obj.vecinos_5_de_7_27 = {
            "num_7": obtener_vecinos_en_rueda(7, 2, RUEDA_EUROPEA), # 2 vecinos a cada lado = 5 números
            "num_27": obtener_vecinos_en_rueda(27, 2, RUEDA_EUROPEA) # 2 vecinos a cada lado = 5 números
        }
        
        # Asignar Puxa.Ult basado en el número actual
        num_obj.puxa_ult = self.tabla_puxa_ult.get(num_obj.numero, [])

        # ---- Predicciones Previas (para evaluación de aciertos) ----
        pred_individual_previa = None
        pred_grupo_previa = None
        pred_rangos_previas = None
        pred_tia_lu_previa = None

        if len(self.historial_numeros) > 0: # Solo si había historial para hacer predicciones
            pred_individual_previa = self.predecir_numero_individual()
            pred_grupo_previa = self.predecir_grupo_numeros()
            pred_rangos_previas = self.predicciones_especificas_rangos()
            pred_tia_lu_previa = self.predecir_numeros_tia_lu() # Predicción Tia Lu basada en estado *antes* de num_obj

        # ---- Actualización de Estado Estrategia Tia Lu ----
        self._actualizar_estado_tia_lu(num_obj.numero)
        
        # ---- Evaluación de Aciertos ----
        if pred_individual_previa: # Implica que las otras predicciones previas también se hicieron
            self._evaluar_aciertos(num_obj, pred_individual_previa, pred_grupo_previa, pred_rangos_previas, pred_tia_lu_previa)
            self.total_predicciones_evaluadas += 1

        # ---- Actualización de conteo de Sectores Personalizados ----
        for nombre_sector, numeros_del_sector in self.sectores_personalizados_definiciones.items(): # Usar definiciones
            if num_obj.numero in numeros_del_sector:
                self.conteo_sectores_personalizados[nombre_sector] = self.conteo_sectores_personalizados.get(nombre_sector, 0) + 1
        # ---- Fin Actualización de Sectores Personalizados ----

        self.historial_numeros.append(num_obj)
        if len(self.historial_numeros) > self.historial_max_longitud:
            self.historial_numeros.pop(0) # Mantener solo los últimos N números

        # Actualizar el sector TOP de números más frecuentes (cada 3 nuevos números)
        self.top_ultima_actualizacion += 1
        if self.top_ultima_actualizacion >= 3:  # Actualizar cada 3 números para evitar recalcular constantemente
            self._actualizar_sector_top()
            self.top_ultima_actualizacion = 0
        
        return num_obj

    def obtener_ultimo_numero_analizado(self):
        if not self.historial_numeros:
            return None
        return self.historial_numeros[-1]

    def mostrar_historial_completo(self):
        print("\n--- Historial de Números ---")
        for num_obj in reversed(self.historial_numeros): # Más reciente primero
            print(f"N°: {num_obj.numero}")
            # Se podrían imprimir más detalles si es necesario

    def limpiar_historial(self):
        """Limpia el historial de números y resetea contadores de aciertos y estados de estrategias."""
        self.historial_numeros = []
        self.aciertos_individual = 0
        self.aciertos_grupo = 0
        self.aciertos_vecinos_0_10 = 0
        self.aciertos_vecinos_7_27 = 0
        self.aciertos_color = 0
        self.total_predicciones_evaluadas = 0
        
        self._reset_estado_tia_lu() # Resetear estado de Estrategia Tia Lu
        self.aciertos_tia_lu = 0
        
        # Resetear conteo de sectores personalizados (se mantienen las definiciones)
        for nombre_sector in self.conteo_sectores_personalizados:
            self.conteo_sectores_personalizados[nombre_sector] = 0
        # print("Historial limpiado.")

    def cargar_numeros_desde_string(self, numeros_str: str, mas_reciente_primero: bool = True):
        """
        Limpia el historial actual y carga números desde un string separado por comas.
        Si mas_reciente_primero es True (default), invierte la lista para procesar el más antiguo primero.
        """
        self.limpiar_historial()
        try:
            # Eliminar espacios y luego dividir
            numeros_int = [int(n.strip()) for n in numeros_str.split(',') if n.strip()]
        except ValueError:
            print(f"Error: El string de números '{numeros_str}' contiene valores no numéricos o formato incorrecto.")
            return

        if not numeros_int:
            print("No se proporcionaron números para cargar.")
            return

        if mas_reciente_primero:
            numeros_int.reverse() # Procesar el más antiguo de la tanda primero

        # print(f"Cargando {len(numeros_int)} números. Lista para procesar (más antiguo primero): {numeros_int}")
        for num in numeros_int:
            self.agregar_numero(num) 
        
        # print(f"Historial cargado. Último número: {self.historial_numeros[-1].numero if self.historial_numeros else 'N/A'}")
        # print(f"Longitud del historial: {len(self.historial_numeros)} de max {self.historial_max_longitud}")

    # --- Funciones de Análisis (a desarrollar) ---
    def analizar_tendencias(self):
        """Analiza tendencias en todas las propiedades."""
        if len(self.historial_numeros) < 2:
            print("No hay suficientes datos para analizar tendencias.")
            return {}

        tendencias = {
            "alto_baixo": [], "par_impar": [], "colunas": [], "duzias": [],
            "terminales": [], "sectores": []
        }
        
        # Ejemplo simple de conteo de frecuencia para la última propiedad
        for prop in tendencias.keys():
            conteo = {}
            for num_obj in self.historial_numeros:
                valor = None
                if prop == "alto_baixo": valor = num_obj.alto_baixo
                elif prop == "par_impar": valor = num_obj.par_impar
                elif prop == "colunas": valor = num_obj.coluna
                elif prop == "duzias": 
                    valor = num_obj.duzia
                    if valor:
                        conteo[valor] = conteo.get(valor, 0) + 1
                        # Agregar información del rango
                        conteo[f"{valor} ({self._obtener_rango_docena(valor)})"] = conteo.pop(valor)
                elif prop == "terminales": valor = num_obj.terminal
                elif prop == "sectores": valor = num_obj.setor
                
                if valor is not None and prop != "duzias":
                    conteo[valor] = conteo.get(valor, 0) + 1
            tendencias[prop] = conteo
        
        return tendencias

    def _calcular_porcentajes(self, conteo_dict, total_tiros):
        """Calcula porcentajes para un diccionario de conteos."""
        if not total_tiros: # Evitar división por cero
            return {key: "0.00%" for key in conteo_dict}
        
        porcentajes = {}
        for key, count in conteo_dict.items():
            porcentaje = (count / total_tiros) * 100
            porcentajes[key] = f"{porcentaje:.2f}%"
        return porcentajes

    def frecuencia_numeros_individuales(self, top_n=None):
        """Calcula la frecuencia de cada número individual en el historial.
           Devuelve un diccionario {numero: frecuencia} ordenado por frecuencia descendente.
           Si top_n está especificado, devuelve solo los N números más frecuentes.
        """
        if not self.historial_numeros:
            return {}

        conteos = {}
        for num_obj in self.historial_numeros:
            conteos[num_obj.numero] = conteos.get(num_obj.numero, 0) + 1
        
        # Ordenar por frecuencia (descendente), luego por número (ascendente) como desempate
        numeros_ordenados = sorted(conteos.items(), key=lambda item: (-item[1], item[0]))
        
        if top_n:
            return dict(numeros_ordenados[:top_n])
        return dict(numeros_ordenados)

    def frecuencia_terminales(self):
        """Calcula la frecuencia de los terminales (incluyendo el 0)."""
        frecuencias = {i: 0 for i in range(0, 10)}  # Incluir terminales del 0 al 9
        for num_obj in self.historial_numeros:
            # Incluir TODOS los terminales, incluyendo el 0
            frecuencias[num_obj.terminal] += 1
        #print(f"Frecuencia Terminales (0-9): {frecuencias}")
        return frecuencias

    def obtener_datos_para_graficos(self):
        """Prepara datos estructurados para ser usados por bibliotecas de gráficos como Chart.js."""
        # Contenido original comentado para desactivar gráficos:
        if not self.historial_numeros:
            return {
                "error": "No hay suficientes datos para generar gráficos.",
                "labels_historial": [],
                "numeros_historial": [],
                "frecuencias_simples": {},
                "frecuencia_terminales": {},
                "actividad_sectores": {},
                "frecuencia_numeros_top": {}
            }

        # 1. Historial para gráfico de línea
        labels_historial = [f"T{i+1}" for i in range(len(self.historial_numeros))]
        numeros_historial = [num.numero for num in self.historial_numeros]

        # 2. Frecuencias de propiedades simples (Columnas, Docenas, Alto/Bajo, Par/Impar)
        tendencias = self.analizar_tendencias()
        frecuencias_simples = {}
        propiedades_simples = ["colunas", "duzias", "alto_baixo", "par_impar"]
        for prop_key in propiedades_simples:
            datos_prop = tendencias.get(prop_key, {})
            if datos_prop:
                frecuencias_simples[prop_key] = {
                    "labels": list(datos_prop.keys()),
                    "data": list(datos_prop.values())
                }
            else:
                 frecuencias_simples[prop_key] = {"labels": [], "data": []}

        # 3. Frecuencia de Terminales
        frec_term = self.frecuencia_terminales()
        frecuencia_terminales_chart = {
            "labels": [str(i) for i in frec_term.keys()],
            "data": list(frec_term.values())
        }

        # 4. Actividad de Sectores
        act_sect = self.sectores_activos_inactivos()
        # Filtrar None y también 0 para no mostrar sectores sin actividad en el gráfico
        act_sect_filtrado = {k: v for k, v in act_sect.items() if k is not None and v > 0}
        actividad_sectores_chart = {
            "labels": list(act_sect_filtrado.keys()),
            "data": list(act_sect_filtrado.values())
        }
        
        # 5. Frecuencia de Números Individuales (Top N)
        frec_numeros_top_dict = self.frecuencia_numeros_individuales(top_n=5)
        frecuencia_numeros_top_chart = {
            "labels": [str(n) for n in frec_numeros_top_dict.keys()],
            "data": list(frec_numeros_top_dict.values())
        }

        return {
            "labels_historial": labels_historial,
            "numeros_historial": numeros_historial,
            "frecuencias_simples": frecuencias_simples,
            "frecuencia_terminales": frecuencia_terminales_chart,
            "actividad_sectores": actividad_sectores_chart,
            "frecuencia_numeros_top": frecuencia_numeros_top_chart
        }

    def sectores_activos_inactivos(self):
        """Identifica sectores más activos e inactivos."""
        conteo_sectores = {
            "Voisins du Zéro": 0, 
            "Tercios del Cilindro": 0, 
            "Orphelins": 0,
            "TOP (Números Frecuentes)": 0,
            None: 0
        }
        
        for num_obj in self.historial_numeros:
            # Cambiar "Tiers du Cylindre" a "Tercios del Cilindro" en los resultados
            sector = num_obj.setor
            if sector == "Tiers du Cylindre":
                sector = "Tercios del Cilindro"
            conteo_sectores[sector] = conteo_sectores.get(sector, 0) + 1
            
            # Contar también para el sector TOP
            if num_obj.numero in self.top_sector:
                conteo_sectores["TOP (Números Frecuentes)"] = conteo_sectores.get("TOP (Números Frecuentes)", 0) + 1
        
        return conteo_sectores

    def analisis_rangos_especiales(self):
        """Análisis de rangos 0/10 y 7-27."""
        # Esta función dependerá de cómo se definan exactamente estos análisis.
        # Podría ser la frecuencia con la que los números caen DENTRO de los vecinos calculados
        # o la frecuencia de los propios números 0, 10, 7, 27.
        
        # Por ejemplo, frecuencia de aparición de los números 0, 10, 7, 27
        conteo_especiales = {"0":0, "10":0, "7":0, "27":0}
        # Y cuántas veces el número salido es vecino de 0, 10, 7, 27
        # Esto es más complejo y requiere definir qué se considera "caer en el rango"
        
        for num_obj in self.historial_numeros:
            if num_obj.numero == 0: conteo_especiales["0"] += 1
            if num_obj.numero == 10: conteo_especiales["10"] += 1
            if num_obj.numero == 7: conteo_especiales["7"] += 1
            if num_obj.numero == 27: conteo_especiales["27"] += 1
                
        #print(f"Conteo números especiales (0,10,7,27): {conteo_especiales}")
        return {"conteo_numeros_clave": conteo_especiales}

    def deteccion_repeticiones_alternancias(self):
        """Detecta repeticiones y alternancias en propiedades."""
        # Ejemplo: Repetición de Par/Impar
        # Ejemplo: Alternancia Alto/Bajo
        # Este es un análisis más avanzado que requiere comparar números consecutivos.
        # Por ahora, es un placeholder.
        #print("Detección de repeticiones y alternancias (TODO)")
        return {}

    # --- Funciones de Predicción (a desarrollar) ---
    def predecir_numero_individual(self):
        """
        Predice un número individual con mayor probabilidad.
        Debe incluir una justificación detallada.
        La propiedad "Puxa.Ult" parece ser clave aquí. Su lógica necesita ser definida.
        """
        # Lógica placeholder - podría ser el más frecuente, o basado en "Puxa.Ult"
        if not self.historial_numeros:
            return {"numero": None, "justificacion": "No hay historial."}

        ultimo_num_obj = self.obtener_ultimo_numero_analizado()
        
        # Prioridad 1: Puxa.Ult del último número aparecido
        # La propiedad "Puxa.Ult" de la que hablamos es la que el *último número que salió* tiende a llamar.
        # Esta ya está en ultimo_num_obj.puxa_ult
        
        if ultimo_num_obj.puxa_ult:
            # ¿Cómo elegir uno de la lista de puxa_ult? ¿El primero? ¿El más "fuerte"?
            # Por ahora, tomemos el primero si existe, como ejemplo.
            prediccion = ultimo_num_obj.puxa_ult[0] 
            justificacion = (
                f"Basado en Puxa.Ult del último número ({ultimo_num_obj.numero}), "
                f"que sugiere los siguientes números: {ultimo_num_obj.puxa_ult}. "
                f"Se elige el primero: {prediccion}."
            )
            return {"numero": prediccion, "justificacion": justificacion}

        # Si no hay Puxa.Ult definido para el último número, o la lista está vacía,
        # recurrir a otra lógica (placeholder actual: predecir el último número que salió).
        # Esta sección se puede mejorar con más heurísticas.
        prediccion_alternativa = ultimo_num_obj.numero 
        justificacion_alternativa = (
            f"No hay Puxa.Ult específico definido o la lista está vacía para el último número ({ultimo_num_obj.numero}). "
            f"Placeholder: Se considera el último número aparecido ({prediccion_alternativa}) como posible repetición o "
            f"se necesita una estrategia de predicción alternativa aquí."
        )
        
        #print(f"Predicción Individual: {prediccion}, Justificación: {justificacion}")
        return {"numero": prediccion_alternativa, "justificacion": justificacion_alternativa}

    def predecir_grupo_numeros(self, cantidad=20):
        """
        Predice un grupo de números con mayor probabilidad.
        Siempre incluye el número 0 y 1 y el sector TOP.
        """
        if not self.historial_numeros:
            return {"grupo": sorted(list({0, 1})), "justificacion": "No hay historial, se devuelve solo 0 y 1."}

        # Incluir los números fijos y el sector TOP
        predicciones_grupo = {0, 1}  # Siempre incluir el 0 y el 1
        predicciones_grupo.update(self.top_sector)  # Añadir números del sector TOP
        
        # Añadir los últimos X números distintos que han salido
        ultimos_distintos = []
        for num_obj in reversed(self.historial_numeros):
            if num_obj.numero not in ultimos_distintos:
                ultimos_distintos.append(num_obj.numero)
        
        for num in ultimos_distintos:
            if len(predicciones_grupo) < cantidad:
                predicciones_grupo.add(num)
            else:
                break
        
        # Rellenar con otros números si es necesario (aleatorio o basado en alguna heurística simple)
        idx_rueda = 0
        while len(predicciones_grupo) < cantidad and idx_rueda < len(RUEDA_EUROPEA):
            predicciones_grupo.add(RUEDA_EUROPEA[idx_rueda])
            idx_rueda +=1
            
        grupo_ordenado = sorted(list(predicciones_grupo))
        justificacion = f"Grupo que incluye los números del sector TOP (más frecuentes: {sorted(list(self.top_sector))}), más los últimos números distintos del historial y relleno si es necesario."
        
        return {"grupo": grupo_ordenado, "justificacion": justificacion}

    def predicciones_especificas_rangos(self):
        """Predicciones para vecinos del 0/10 y rango 7-27."""
        # Esto podría ser tomar los conjuntos de vecinos calculados para el último número
        # y presentarlos como posibles apuestas.
        ultimo_num = self.obtener_ultimo_numero_analizado()
        if not ultimo_num:
            return {"vecinos_0_10": [], "rango_7_27_vecinos": [], "justificacion": "No hay último número."}

        preds = {
            "vecinos_0_10_del_ultimo": {
                "0": ultimo_num.vecinos_0_10["num_0"] if ultimo_num.vecinos_0_10 else [],
                "10": ultimo_num.vecinos_0_10["num_10"] if ultimo_num.vecinos_0_10 else []
            },
            "vecinos_7_27_del_ultimo": {
                "7": ultimo_num.vecinos_5_de_7_27["num_7"] if ultimo_num.vecinos_5_de_7_27 else [],
                "27": ultimo_num.vecinos_5_de_7_27["num_27"] if ultimo_num.vecinos_5_de_7_27 else []
            },
            "justificacion": "Grupos de vecinos de 0, 10, 7, 27 basados en la rueda y el último número."
        }
        #print(f"Predicciones Específicas Rangos: {preds}")
        return preds

    def _actualizar_estado_tia_lu(self, numero_actual):
        """Actualiza el estado de la Estrategia Tia Lu basado en el número actual."""
        es_desencadenante_actual = numero_actual in self.tia_lu_triggers

        if self.tia_lu_estado["activa"]:
            self.tia_lu_estado["giros_jugados"] += 1
            if self.tia_lu_estado["giros_jugados"] > 3:
                self._reset_estado_tia_lu() # Termina la estrategia después de 3 giros
                # Es importante resetear aquí para que la evaluación del nuevo número no la reactive inmediatamente.
                # Necesitamos recalcular el contador de desencadenantes para el número actual después del reset.
                if es_desencadenante_actual:
                    self.tia_lu_estado["contador_desencadenantes_consecutivos"] = 1
                    self.tia_lu_estado["ultimo_numero_fue_desencadenante"] = True
                # else, se queda en 0 y False por el _reset_estado_tia_lu()

        # Esta parte se ejecuta incluso si la estrategia se desactivó justo arriba,
        # para determinar si se debe activar una *nueva* secuencia de Tia Lu.
        if not self.tia_lu_estado["activa"]: # Si no está activa (o se acaba de desactivar)
            if es_desencadenante_actual:
                if self.tia_lu_estado["ultimo_numero_fue_desencadenante"]:
                    self.tia_lu_estado["contador_desencadenantes_consecutivos"] += 1
                else:
                    self.tia_lu_estado["contador_desencadenantes_consecutivos"] = 1
                
                self.tia_lu_estado["ultimo_numero_fue_desencadenante"] = True

                if self.tia_lu_estado["contador_desencadenantes_consecutivos"] >= 2:
                    # Activar la estrategia
                    self.tia_lu_estado["activa"] = True
                    self.tia_lu_estado["giros_jugados"] = 1 # Primer giro de la nueva activación
                    # El número que activa (el segundo) es el 'numero_actual'
                    self.tia_lu_estado["activada_con_33"] = (numero_actual == 33)
                    # No reseteamos el contador_desencadenantes_consecutivos aquí, 
                    # porque podría ser parte de una secuencia más larga de desencadenantes.
            else:
                # No es desencadenante, se rompe cualquier racha
                self.tia_lu_estado["contador_desencadenantes_consecutivos"] = 0
                self.tia_lu_estado["ultimo_numero_fue_desencadenante"] = False
    
    def predecir_numeros_tia_lu(self):
        """Genera predicciones si la Estrategia Tia Lu está activa."""
        if not self.tia_lu_estado["activa"]:
            return None

        numeros_a_apostar = set(self.tia_lu_numeros_base) # Usar set para evitar duplicados si base ya tiene 0,1
        
        # Si la estrategia se activó porque el *segundo* desencadenante fue un 33
        if self.tia_lu_estado["activada_con_33"]:
            numeros_a_apostar.update(self.tia_lu_numeros_extra_si_33)

        justificacion = (
            f"Estrategia Tia Lu ({self.tia_lu_estado['giros_jugados']}/3). "
            f"Activada con { '33' if self.tia_lu_estado['activada_con_33'] else '11 o 22' } como 2do trigger. "
            f"Números base: {sorted(list(self.tia_lu_numeros_base))}. "
            f"{ 'Extras por 33: ' + str(sorted(list(self.tia_lu_numeros_extra_si_33))) if self.tia_lu_estado['activada_con_33'] else '' }"
        )
        return {"numeros": sorted(list(numeros_a_apostar)), "justificacion": justificacion}

    def _evaluar_aciertos(self, nuevo_numero_obj, pred_individual, pred_grupo, pred_rangos, pred_tia_lu):
        """Evalúa si el nuevo número acierta las predicciones previas."""
        numero_actual = nuevo_numero_obj.numero

        # Acierto Individual
        if pred_individual["numero"] is not None and numero_actual == pred_individual["numero"]:
            self.aciertos_individual += 1

        # Acierto Grupo
        if numero_actual in pred_grupo["grupo"]:
            self.aciertos_grupo += 1

        # Acierto Vecinos 0/10
        # El número actual debe estar en los vecinos del 0 del último número O en los vecinos del 10 del último número
        # (según las predicciones de rangos que se basan en el último número del historial PREVIO)
        vecinos_0_del_ultimo_previa = pred_rangos.get("vecinos_0_10_del_ultimo", {}).get("0", [])
        vecinos_10_del_ultimo_previa = pred_rangos.get("vecinos_0_10_del_ultimo", {}).get("10", [])
        if numero_actual in vecinos_0_del_ultimo_previa or numero_actual in vecinos_10_del_ultimo_previa:
            self.aciertos_vecinos_0_10 += 1

        # Acierto Vecinos 7/27
        vecinos_7_del_ultimo_previa = pred_rangos.get("vecinos_7_27_del_ultimo", {}).get("7", [])
        vecinos_27_del_ultimo_previa = pred_rangos.get("vecinos_7_27_del_ultimo", {}).get("27", [])
        if numero_actual in vecinos_7_del_ultimo_previa or numero_actual in vecinos_27_del_ultimo_previa:
            self.aciertos_vecinos_7_27 += 1

        # Acierto Estrategia Tia Lu
        if pred_tia_lu and pred_tia_lu.get("numeros") and numero_actual in pred_tia_lu["numeros"]:
            self.aciertos_tia_lu += 1

        # Acierto Color
        pred_color_previa = self.predecir_color()
        if pred_color_previa["color"] and nuevo_numero_obj.cor == pred_color_previa["color"]:
            self.aciertos_color += 1

    def _actualizar_sector_top(self):
        """Actualiza el sector TOP con los números más frecuentes en el historial"""
        # Contar frecuencias
        contador = {}
        for num_obj in self.historial_numeros:
            contador[num_obj.numero] = contador.get(num_obj.numero, 0) + 1
            
        # Ordenar por frecuencia (de mayor a menor)
        numeros_ordenados = sorted(contador.items(), key=lambda x: x[1], reverse=True)
        
        # Tomar los top N números (máximo max_numeros_top)
        self.top_sector = set([num for num, _ in numeros_ordenados[:self.max_numeros_top]])
        
        # Actualizar también la variable global
        global TOP_SECTOR
        TOP_SECTOR = self.top_sector.copy()
        
        print(f"Sector TOP actualizado: {self.top_sector}")

    def predecir_color(self):
        """
        Predice el próximo color basado en el análisis del historial.
        """
        if not self.historial_numeros:
            return {"color": None, "justificacion": "No hay historial para predecir color."}

        # Contar frecuencias de colores
        conteo_colores = {"Rojo": 0, "Negro": 0, "Verde": 0}
        ultimos_colores = []
        
        for num_obj in self.historial_numeros:
            color = num_obj.cor
            conteo_colores[color] = conteo_colores.get(color, 0) + 1
            ultimos_colores.append(color)

        # Obtener el último color
        ultimo_color = ultimos_colores[-1] if ultimos_colores else None
        
        # Calcular porcentajes
        total_tiros = len(self.historial_numeros)
        porcentajes = {color: (count/total_tiros)*100 for color, count in conteo_colores.items()}
        
        # Analizar secuencia de colores
        secuencia_actual = ""
        if len(ultimos_colores) >= 3:
            secuencia_actual = " → ".join(ultimos_colores[-3:])

        # Determinar predicción basada en varios factores
        if ultimo_color == "Verde":
            # Después del verde (0), es más probable que salga Rojo o Negro
            prediccion = "Rojo" if conteo_colores["Rojo"] < conteo_colores["Negro"] else "Negro"
            justificacion = f"Último número fue Verde (0). Equilibrando hacia {prediccion} que tiene menor frecuencia."
        else:
            # Analizar si hay una racha del mismo color
            racha_actual = 1
            for i in range(len(ultimos_colores)-2, -1, -1):
                if ultimos_colores[i] == ultimo_color:
                    racha_actual += 1
                else:
                    break
            
            if racha_actual >= 3:
                # Después de una racha larga, es más probable el cambio
                prediccion = "Negro" if ultimo_color == "Rojo" else "Rojo"
                justificacion = f"Racha de {racha_actual} {ultimo_color}(s) consecutivos sugiere cambio a {prediccion}."
            else:
                # Usar el color menos frecuente como predicción
                prediccion = "Rojo" if conteo_colores["Rojo"] < conteo_colores["Negro"] else "Negro"
                justificacion = f"Basado en frecuencias: Rojo {porcentajes['Rojo']:.1f}%, Negro {porcentajes['Negro']:.1f}%"
                if racha_actual == 2:
                    justificacion += f". Además, hay una pequeña racha de {ultimo_color}."

        return {
            "color": prediccion,
            "justificacion": justificacion,
            "estadisticas": {
                "conteo": conteo_colores,
                "porcentajes": porcentajes,
                "ultima_secuencia": secuencia_actual,
                "racha_actual": ultimo_color
            }
        }

    def generar_informe_completo(self):
        """Genera un informe completo con el formato de respuesta deseado."""
        ultimo_numero_obj = self.obtener_ultimo_numero_analizado()
        if not ultimo_numero_obj:
            return "No hay datos para mostrar."

        output = []
        output.append("--- INFORME DE RULETA ---")
        output.append(f"ÚLTIMO NÚMERO APARECIDO: {ultimo_numero_obj.numero}")
        output.append("  Propiedades:")
        output.append(f"    Terminal: {ultimo_numero_obj.terminal}")
        output.append(f"    Coluna: {ultimo_numero_obj.coluna}")
        output.append(f"    Docena: {ultimo_numero_obj.duzia} ({self._obtener_rango_docena(ultimo_numero_obj.duzia)})")
        output.append(f"    Alto/Baixo: {ultimo_numero_obj.alto_baixo}")
        output.append(f"    Par/Impar: {ultimo_numero_obj.par_impar}")
        output.append(f"    Cor: {ultimo_numero_obj.cor}")
        output.append(f"    Setor: {ultimo_numero_obj.setor}")
        output.append(f"    Puxa.Ult (números que {ultimo_numero_obj.numero} tiende a llamar): {ultimo_numero_obj.puxa_ult if ultimo_numero_obj.puxa_ult else 'N/A o no definido'}")
        
        if ultimo_numero_obj.vecinos_5_2:
            output.append(f"    Vecinos 5 (rueda, 2 a cada lado): {ultimo_numero_obj.vecinos_5_2['num_5']}")
            output.append(f"    Vecinos 2 (rueda, 2 a cada lado): {ultimo_numero_obj.vecinos_5_2['num_2']}")
        if ultimo_numero_obj.vecinos_0_10:
            output.append(f"    Vecinos 0 (rueda, 2 a cada lado): {ultimo_numero_obj.vecinos_0_10['num_0']}")
            output.append(f"    Vecinos 10 (rueda, 2 a cada lado): {ultimo_numero_obj.vecinos_0_10['num_10']}")
        if ultimo_numero_obj.vecinos_5_de_7_27:
            output.append(f"    Vecinos 7 (rueda, 5 en total): {ultimo_numero_obj.vecinos_5_de_7_27['num_7']}")
            output.append(f"    Vecinos 27 (rueda, 5 en total): {ultimo_numero_obj.vecinos_5_de_7_27['num_27']}")

        output.append("\nRESUMEN DE TENDENCIAS PRINCIPALES (basado en el historial actual):")
        total_tiros_historial = len(self.historial_numeros)
        output.append(f"  Total de Tiros Analizados: {total_tiros_historial}")
        
        tendencias = self.analizar_tendencias()
        
        # Primero mostrar las docenas con formato especial
        docenas = tendencias.get("duzias", {})
        if docenas:
            output.append("\n  ANÁLISIS DE DOCENAS:")
            porcentajes_docenas = self._calcular_porcentajes(docenas, total_tiros_historial)
            for docena, conteo in docenas.items():
                output.append(f"    - {docena}: {conteo} apariciones ({porcentajes_docenas.get(docena, 'N/A')})")
            
            # Agregar análisis de docenas consecutivas
            docenas_consecutivas = self._analizar_docenas_consecutivas()
            if docenas_consecutivas:
                output.append("\n    Patrones de Docenas Consecutivas:")
                for patron, conteo in docenas_consecutivas.items():
                    output.append(f"      - {patron}: {conteo} veces")
        
        # Luego mostrar el resto de las propiedades
        propiedades_a_mostrar_con_porcentaje = {
            "Columnas": tendencias.get("colunas", {}),
            "Alto/Bajo": tendencias.get("alto_baixo", {}),
            "Par/Impar": tendencias.get("par_impar", {})
        }

        for nombre_prop, conteo_prop in propiedades_a_mostrar_con_porcentaje.items():
            if conteo_prop:
                porcentajes_prop = self._calcular_porcentajes(conteo_prop, total_tiros_historial)
                output.append(f"  {nombre_prop}:")
                for categoria, conteo_val in conteo_prop.items():
                    output.append(f"    - {categoria}: {conteo_val} ({porcentajes_prop.get(categoria, 'N/A')})")
            else:
                output.append(f"  {nombre_prop}: (Sin datos suficientes)")
        
        frec_term = self.frecuencia_terminales()
        if frec_term:
            porcentajes_term = self._calcular_porcentajes(frec_term, total_tiros_historial)
            output.append(f"  Frecuencia Terminales:")
            # Convertir terminales (int) a string para el output formateado
            frec_term_str_keys = {str(k): v for k,v in frec_term.items()}
            porcentajes_term_str_keys = {str(k): v for k,v in porcentajes_term.items()}
            sorted_terminals = sorted(frec_term_str_keys.items(), key=lambda item: int(item[0])) # Ordenar por terminal 0-9
            for terminal_str, conteo_val in sorted_terminals:
                output.append(f"    - Terminal {terminal_str}: {conteo_val} ({porcentajes_term_str_keys.get(terminal_str, 'N/A')})")
        else:
            output.append(f"  Frecuencia Terminales: (Sin datos suficientes)")
            
        act_sect = self.sectores_activos_inactivos()
        act_sect_filtrado = {k: v for k, v in act_sect.items() if k is not None and v > 0} # Filtrar None y sin apariciones
        if act_sect_filtrado:
            porcentajes_sect = self._calcular_porcentajes(act_sect_filtrado, total_tiros_historial)
            output.append(f"  Actividad Sectores:")
            for sector, conteo_val in act_sect_filtrado.items():
                 output.append(f"    - {sector}: {conteo_val} ({porcentajes_sect.get(sector, 'N/A')})")
        else:
            output.append(f"  Actividad Sectores: (Sin datos suficientes o sin actividad)")
        
        frec_numeros = self.frecuencia_numeros_individuales(top_n=5) # Mostrar los 5 más frecuentes
        if frec_numeros:
            output.append(f"  Números Más Frecuentes (Top 5):")
            for num, conteo_val in frec_numeros.items():
                porcentaje_num = (conteo_val / total_tiros_historial) * 100 if total_tiros_historial > 0 else 0
                output.append(f"    - N° {num}: {conteo_val} ({porcentaje_num:.2f}%)")
        else:
            output.append(f"  Números Más Frecuentes: (Sin datos suficientes)")

        # Añadir información sobre el sector TOP
        output.append("\nSECTOR TOP (NÚMEROS MÁS FRECUENTES):")
        if self.top_sector:
            output.append(f"  Números actuales: {sorted(list(self.top_sector))}")
            output.append(f"  Total de números en TOP: {len(self.top_sector)}")
        else:
            output.append("  El sector TOP está vacío (se necesitan más datos)")
        
        output.append("\nPREDICCIONES:")
        pred_ind = self.predecir_numero_individual()
        output.append(f"  Individual: {pred_ind['numero']}")
        output.append(f"    Justificación: {pred_ind['justificacion']}")

        pred_grup = self.predecir_grupo_numeros()
        output.append(f"  Grupo (20 números): {pred_grup['grupo']}")
        output.append(f"    Justificación: {pred_grup['justificacion']}")

        pred_rangos = self.predicciones_especificas_rangos()
        output.append(f"  Específicas Vecinos 0/10 (del último {ultimo_numero_obj.numero}):")
        output.append(f"    Vecinos del 0: {pred_rangos['vecinos_0_10_del_ultimo']['0']}")
        output.append(f"    Vecinos del 10: {pred_rangos['vecinos_0_10_del_ultimo']['10']}")
        output.append(f"  Específicas Vecinos 7/27 (del último {ultimo_numero_obj.numero}):")
        output.append(f"    Vecinos del 7 (5 en total): {pred_rangos['vecinos_7_27_del_ultimo']['7']}")
        output.append(f"    Vecinos del 27 (5 en total): {pred_rangos['vecinos_7_27_del_ultimo']['27']}")
        output.append(f"    Justificación: {pred_rangos['justificacion']}")
        
        # Predicción Estrategia Tia Lu
        pred_tia_lu_actual = self.predecir_numeros_tia_lu() # Basada en el estado actual (después de procesar el último número)
        if pred_tia_lu_actual:
            output.append("\nPREDICCIÓN ESTRATEGIA TIA LU (PARA PRÓXIMO GIRO):")
            output.append(f"  Números: {pred_tia_lu_actual['numeros']}")
            output.append(f"  Justificación: {pred_tia_lu_actual['justificacion']}")
            if self.tia_lu_estado["activa"]:
                 output.append(f"  Estado actual: Activa, Giro {self.tia_lu_estado['giros_jugados']} de 3.")
            else:
                 output.append(f"  Estado actual: Inactiva (o esperando condición de activación). Contador triggers: {self.tia_lu_estado['contador_desencadenantes_consecutivos']}") 

        # Añadir predicción de color después de las predicciones existentes
        output.append("\nPREDICCIÓN DE COLOR:")
        pred_color = self.predecir_color()
        output.append(f"  Color Predicho: {pred_color['color']}")
        output.append(f"  Justificación: {pred_color['justificacion']}")
        output.append("  Estadísticas de Color:")
        for color, conteo in pred_color['estadisticas']['conteo'].items():
            porcentaje = pred_color['estadisticas']['porcentajes'][color]
            output.append(f"    - {color}: {conteo} apariciones ({porcentaje:.1f}%)")
        if pred_color['estadisticas']['ultima_secuencia']:
            output.append(f"  Última Secuencia: {pred_color['estadisticas']['ultima_secuencia']}")

        output.append("\n--- SEGUIMIENTO DE ACIERTOS DE PREDICCIONES ---")
        if self.total_predicciones_evaluadas > 0:
            output.append(f"  Total de Giros con Predicciones Evaluadas: {self.total_predicciones_evaluadas}")
            output.append(f"  Aciertos Pred. Individual: {self.aciertos_individual} ({ (self.aciertos_individual/self.total_predicciones_evaluadas)*100 :.2f}%)")
            output.append(f"  Aciertos Pred. Grupo (20+0,1): {self.aciertos_grupo} ({ (self.aciertos_grupo/self.total_predicciones_evaluadas)*100 :.2f}%)")
            output.append(f"  Aciertos Pred. Vecinos 0/10 (del previo): {self.aciertos_vecinos_0_10} ({ (self.aciertos_vecinos_0_10/self.total_predicciones_evaluadas)*100 :.2f}%)")
            output.append(f"  Aciertos Pred. Vecinos 7/27 (del previo): {self.aciertos_vecinos_7_27} ({ (self.aciertos_vecinos_7_27/self.total_predicciones_evaluadas)*100 :.2f}%)")
            output.append(f"  Aciertos Pred. Color: {self.aciertos_color} ({ (self.aciertos_color/self.total_predicciones_evaluadas)*100 :.2f}%)")
            output.append(f"  Aciertos Estrategia Tia Lu: {self.aciertos_tia_lu} ({ (self.aciertos_tia_lu/self.total_predicciones_evaluadas)*100 :.2f}%)")
        else:
            output.append("  Aún no se han evaluado predicciones (se necesita al menos un número en el historial previo al actual).")
        
        output.append("\n--- ACTIVIDAD SECTORES PERSONALIZADOS ---")
        total_tiros_historial = len(self.historial_numeros)
        if total_tiros_historial > 0 and self.sectores_personalizados_definiciones:
            # Ordenar los sectores por nombre para una visualización consistente
            for nombre_sector in sorted(self.sectores_personalizados_definiciones.keys()):
                numeros_del_sector = self.sectores_personalizados_definiciones[nombre_sector]
                conteo = self.conteo_sectores_personalizados.get(nombre_sector, 0)
                porcentaje = (conteo / total_tiros_historial) * 100
                output.append(f"  {nombre_sector} (Números: {sorted(list(numeros_del_sector))}):")
                output.append(f"    Apariciones: {conteo} ({porcentaje:.2f}% del historial)")
        elif not self.sectores_personalizados_definiciones:
            output.append("  No hay definiciones de sectores personalizados cargadas.")
        else:
            output.append("  No hay historial para analizar actividad de sectores personalizados.")
        
        return "\n".join(output)

    def _obtener_rango_docena(self, docena: str) -> str:
        """Retorna el rango de números para una docena dada."""
        rangos = {
            "D1": "números 1-12",
            "D2": "números 13-24",
            "D3": "números 25-36"
        }
        return rangos.get(docena, "")

    def _analizar_docenas_consecutivas(self):
        """Analiza patrones de docenas consecutivas en el historial."""
        if len(self.historial_numeros) < 2:
            return {}
        
        patrones = {}
        for i in range(len(self.historial_numeros) - 1):
            docena_actual = self.historial_numeros[i].duzia
            docena_siguiente = self.historial_numeros[i + 1].duzia
            if docena_actual and docena_siguiente:
                patron = f"{docena_actual} → {docena_siguiente}"
                patrones[patron] = patrones.get(patron, 0) + 1
        
        # Ordenar por frecuencia
        return dict(sorted(patrones.items(), key=lambda x: x[1], reverse=True))

# --- Ejemplo de Uso ---
if __name__ == "__main__":
    analizador = AnalizadorRuleta(historial_max_longitud=25)

    # Simular la llegada de números
    numeros_llegados = [10, 0, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 5, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12]
    
    for num_int in numeros_llegados:
        print(f"\n--- Agregando número: {num_int} ---")
        num_procesado = analizador.agregar_numero(num_int)
        # print(num_procesado) # Muestra las propiedades del número recién agregado
        # print(f"  Vecinos 5/2: {num_procesado.vecinos_5_2}")
        # print(f"  Vecinos 0/10: {num_procesado.vecinos_0_10}")
        # print(f"  Vecinos 5 de 7/27: {num_procesado.vecinos_5_de_7_27}")


    # Mostrar historial
    # analizador.mostrar_historial_completo()

    # Realizar análisis y mostrar informe completo basado en el último número
    print("\n=====================================")
    informe = analizador.generar_informe_completo()
    print(informe)
    print("=====================================\n")

    # Ejemplo de cómo se podría actualizar con un nuevo número
    print("\n--- Agregando nuevo número: 3 ---")
    analizador.agregar_numero(3)
    informe_actualizado = analizador.generar_informe_completo()
    print(informe_actualizado)
    print("=====================================\n")

    # --- NUEVO EJEMPLO DE USO CON CARGA DESDE STRING ---
    print("\n***********************************************************")
    print("* EJEMPLO CON CARGA DE HISTORIAL DESDE STRING DE USUARIO *")
    print("***********************************************************\n")
    
    # El usuario proveerá 15 números, el más reciente primero.
    # Ajustamos historial_max_longitud para el ejemplo, aunque la clase puede manejar más.
    analizador_con_string = AnalizadorRuleta(historial_max_longitud=15) 

    # String de 15 números, el 21 es el más reciente, el 30 es el más antiguo de esta tanda.
    numeros_entrada_usuario_str = "21,5,18,31,9,22,0,32,15,19,4,2,25,17,30" 
    print(f"Entrada de usuario (formato: más reciente primero): '{numeros_entrada_usuario_str}'")

    analizador_con_string.cargar_numeros_desde_string(numeros_entrada_usuario_str, mas_reciente_primero=True)
    
    print("\n--- Informe después de cargar el string ---")
    informe_desde_string = analizador_con_string.generar_informe_completo()
    print(informe_desde_string)
    print("=====================================\n")

    nuevo_numero_individual_str = 35
    print(f"--- Agregando nuevo número individual: {nuevo_numero_individual_str} después de cargar string ---")
    analizador_con_string.agregar_numero(nuevo_numero_individual_str)
    informe_actualizado_str = analizador_con_string.generar_informe_completo()
    print(informe_actualizado_str)
    print("=====================================\n")

    # Ejemplo con string vacío o inválido
    print("--- Probando carga con string vacío ---")
    analizador_con_string.cargar_numeros_desde_string("")
    informe_vacio = analizador_con_string.generar_informe_completo() # Debería indicar que no hay datos
    print(informe_vacio)
    print("=====================================\n")

    print("--- Probando carga con string inválido ---")
    analizador_con_string.cargar_numeros_desde_string("1,2,abc,4")
    informe_invalido = analizador_con_string.generar_informe_completo() # Debería indicar que no hay datos (o el último estado válido)
    print(informe_invalido) # El historial se limpia, así que no habrá datos.
    print("=====================================\n") 