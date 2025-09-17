#!/usr/bin/env python3
"""
Sistema de Procesamiento Mejorado de Números
============================================

Módulo para procesar y validar números de la ruleta con soporte para:
- Números separados por comas
- Validación de rangos (0-36)
- Detección automática de formatos
- Integración con las tablas de Supabase
- Manejo de colores automático
"""

import re
import datetime
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass
import traceback

@dataclass
class NumeroProcessed:
    """Representación de un número procesado"""
    valor: int
    color: str
    es_valido: bool
    posicion_original: int

@dataclass
class ResultadoProcesamiento:
    """Resultado del procesamiento de una cadena de números"""
    numeros_validos: List[NumeroProcessed]
    numeros_invalidos: List[str]
    formato_detectado: str
    total_procesados: int
    cadena_original: str

class NumberProcessor:
    """
    Procesador principal de números de ruleta
    """
    
    def __init__(self):
        # Definir colores de la ruleta europea
        self.numeros_rojos = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        self.numeros_negros = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
        self.numero_verde = {0}
        
        # Patrones de detección
        self.patrones_reconocimiento = [
            # Números separados por comas
            r'^(\d{1,2}(?:\s*,\s*\d{1,2})*)\s*$',
            
            # Números separados por espacios
            r'^(\d{1,2}(?:\s+\d{1,2})*)\s*$',
            
            # Números separados por guiones o pipes
            r'^(\d{1,2}(?:\s*[-|]\s*\d{1,2})*)\s*$',
            
            # Un solo número
            r'^(\d{1,2})\s*$',
            
            # Texto con números (ej: "salió el 23, 14, 5")
            r'.*?(\d{1,2}(?:\s*[,\s]\s*\d{1,2})*)',
        ]
    
    def obtener_color_numero(self, numero: int) -> str:
        """
        Obtiene el color de un número de ruleta
        
        Args:
            numero: Número de la ruleta (0-36)
            
        Returns:
            Color del número: 'Rojo', 'Negro', 'Verde'
        """
        if numero in self.numeros_rojos:
            return 'Rojo'
        elif numero in self.numeros_negros:
            return 'Negro'
        elif numero in self.numero_verde:
            return 'Verde'
        else:
            return 'Desconocido'
    
    def es_numero_valido(self, numero: Union[int, str]) -> bool:
        """
        Verifica si un número es válido para la ruleta europea
        
        Args:
            numero: Número a validar
            
        Returns:
            True si el número está en el rango 0-36
        """
        try:
            num_int = int(numero)
            return 0 <= num_int <= 36
        except (ValueError, TypeError):
            return False
    
    def detectar_formato(self, cadena: str) -> str:
        """
        Detecta el formato de la cadena de números
        
        Args:
            cadena: Cadena a analizar
            
        Returns:
            Tipo de formato detectado
        """
        cadena_limpia = cadena.strip()
        
        if ',' in cadena_limpia:
            return 'comas'
        elif '-' in cadena_limpia or '|' in cadena_limpia:
            return 'separadores'
        elif ' ' in cadena_limpia and len(cadena_limpia.split()) > 1:
            return 'espacios'
        elif cadena_limpia.isdigit():
            return 'numero_simple'
        else:
            return 'texto_mixto'
    
    def extraer_numeros_de_texto(self, texto: str) -> List[str]:
        """
        Extrae números de una cadena de texto usando patrones
        
        Args:
            texto: Texto del cual extraer números
            
        Returns:
            Lista de números como strings
        """
        numeros_encontrados = []
        
        for patron in self.patrones_reconocimiento:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                numeros_str = match.group(1)
                
                # Dividir por diferentes separadores
                if ',' in numeros_str:
                    numeros_encontrados = [n.strip() for n in numeros_str.split(',')]
                elif '-' in numeros_str:
                    numeros_encontrados = [n.strip() for n in numeros_str.split('-')]
                elif '|' in numeros_str:
                    numeros_encontrados = [n.strip() for n in numeros_str.split('|')]
                elif ' ' in numeros_str:
                    numeros_encontrados = [n.strip() for n in numeros_str.split()]
                else:
                    numeros_encontrados = [numeros_str.strip()]
                
                break
        
        # Filtrar números vacíos
        return [n for n in numeros_encontrados if n]
    
    def procesar_cadena_numeros(self, cadena: str) -> ResultadoProcesamiento:
        """
        Procesa una cadena de números y devuelve resultado detallado
        
        Args:
            cadena: Cadena de números a procesar
            
        Returns:
            ResultadoProcesamiento con detalles completos
        """
        try:
            cadena_original = cadena
            cadena_limpia = cadena.strip()
            
            if not cadena_limpia:
                return ResultadoProcesamiento(
                    numeros_validos=[],
                    numeros_invalidos=[],
                    formato_detectado='vacio',
                    total_procesados=0,
                    cadena_original=cadena_original
                )
            
            # Detectar formato
            formato = self.detectar_formato(cadena_limpia)
            
            # Extraer números
            numeros_str = self.extraer_numeros_de_texto(cadena_limpia)
            
            # Procesar cada número
            numeros_validos = []
            numeros_invalidos = []
            
            for i, num_str in enumerate(numeros_str):
                if self.es_numero_valido(num_str):
                    numero_int = int(num_str)
                    color = self.obtener_color_numero(numero_int)
                    
                    numero_procesado = NumeroProcessed(
                        valor=numero_int,
                        color=color,
                        es_valido=True,
                        posicion_original=i
                    )
                    numeros_validos.append(numero_procesado)
                else:
                    numeros_invalidos.append(num_str)
            
            return ResultadoProcesamiento(
                numeros_validos=numeros_validos,
                numeros_invalidos=numeros_invalidos,
                formato_detectado=formato,
                total_procesados=len(numeros_str),
                cadena_original=cadena_original
            )
            
        except Exception as e:
            print(f"Error al procesar cadena de números: {e}")
            traceback.print_exc()
            return ResultadoProcesamiento(
                numeros_validos=[],
                numeros_invalidos=[cadena],
                formato_detectado='error',
                total_procesados=0,
                cadena_original=cadena
            )
    
    def convertir_a_formato_supabase(self, resultado: ResultadoProcesamiento, history_entry_id: int) -> List[Dict[str, Any]]:
        """
        Convierte el resultado procesado al formato requerido por Supabase
        
        Args:
            resultado: Resultado del procesamiento
            history_entry_id: ID de la entrada de historial
            
        Returns:
            Lista de registros para insertar en roulette_numbers_individual
        """
        registros = []
        timestamp = datetime.datetime.now().isoformat()
        
        for numero in resultado.numeros_validos:
            registro = {
                'history_entry_id': history_entry_id,
                'number_value': numero.valor,
                'color': numero.color,
                'created_at': timestamp
            }
            registros.append(registro)
        
        return registros
    
    def procesar_y_preparar_para_db(self, cadena: str, history_entry_id: int) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Procesa números y los prepara para inserción en base de datos
        
        Args:
            cadena: Cadena de números a procesar
            history_entry_id: ID de la entrada de historial
            
        Returns:
            Tupla (éxito, registros_para_db, mensaje_resultado)
        """
        try:
            resultado = self.procesar_cadena_numeros(cadena)
            
            if not resultado.numeros_validos:
                mensaje = f"No se encontraron números válidos en: '{cadena}'"
                if resultado.numeros_invalidos:
                    mensaje += f" (inválidos: {', '.join(resultado.numeros_invalidos)})"
                return False, [], mensaje
            
            registros = self.convertir_a_formato_supabase(resultado, history_entry_id)
            
            mensaje = f"Procesados {len(resultado.numeros_validos)} números válidos"
            if resultado.numeros_invalidos:
                mensaje += f" ({len(resultado.numeros_invalidos)} inválidos ignorados)"
            
            return True, registros, mensaje
            
        except Exception as e:
            mensaje = f"Error al procesar números: {e}"
            print(mensaje)
            traceback.print_exc()
            return False, [], mensaje
    
    def obtener_estadisticas_procesamiento(self, resultados: List[ResultadoProcesamiento]) -> Dict[str, Any]:
        """
        Obtiene estadísticas de múltiples procesamientos
        
        Args:
            resultados: Lista de resultados de procesamiento
            
        Returns:
            Diccionario con estadísticas
        """
        if not resultados:
            return {'total_procesamientos': 0}
        
        total_numeros_validos = sum(len(r.numeros_validos) for r in resultados)
        total_numeros_invalidos = sum(len(r.numeros_invalidos) for r in resultados)
        
        formatos_detectados = {}
        colores_procesados = {'Rojo': 0, 'Negro': 0, 'Verde': 0}
        
        for resultado in resultados:
            formato = resultado.formato_detectado
            formatos_detectados[formato] = formatos_detectados.get(formato, 0) + 1
            
            for numero in resultado.numeros_validos:
                colores_procesados[numero.color] += 1
        
        return {
            'total_procesamientos': len(resultados),
            'total_numeros_validos': total_numeros_validos,
            'total_numeros_invalidos': total_numeros_invalidos,
            'formatos_detectados': formatos_detectados,
            'distribucion_colores': colores_procesados,
            'tasa_exito': total_numeros_validos / max(1, total_numeros_validos + total_numeros_invalidos)
        }
    
    def validar_secuencia_continua(self, numeros: List[int]) -> Dict[str, Any]:
        """
        Valida si una secuencia de números parece realista para una sesión de ruleta
        
        Args:
            numeros: Lista de números a validar
            
        Returns:
            Diccionario con análisis de la secuencia
        """
        if not numeros:
            return {'es_valida': False, 'razon': 'Lista vacía'}
        
        # Verificar que todos los números sean válidos
        numeros_invalidos = [n for n in numeros if not self.es_numero_valido(n)]
        if numeros_invalidos:
            return {
                'es_valida': False,
                'razon': f'Números inválidos: {numeros_invalidos}'
            }
        
        # Verificar duplicados consecutivos (posible error de entrada)
        duplicados_consecutivos = []
        for i in range(1, len(numeros)):
            if numeros[i] == numeros[i-1]:
                duplicados_consecutivos.append(numeros[i])
        
        # Análisis de distribución
        distribucion_colores = {'Rojo': 0, 'Negro': 0, 'Verde': 0}
        for numero in numeros:
            color = self.obtener_color_numero(numero)
            distribucion_colores[color] += 1
        
        # Verificar si la distribución es muy desbalanceada (posible error)
        total_numeros = len(numeros)
        proporcion_verde = distribucion_colores['Verde'] / total_numeros
        
        warnings = []
        if proporcion_verde > 0.1:  # Más del 10% verdes es sospechoso
            warnings.append(f"Proporción alta de verdes: {proporcion_verde:.2%}")
        
        if duplicados_consecutivos:
            warnings.append(f"Números duplicados consecutivos: {set(duplicados_consecutivos)}")
        
        return {
            'es_valida': True,
            'warnings': warnings,
            'distribucion_colores': distribucion_colores,
            'total_numeros': total_numeros,
            'numeros_unicos': len(set(numeros)),
            'duplicados_consecutivos': len(duplicados_consecutivos)
        }

def create_number_processor() -> NumberProcessor:
    """Factory function para crear NumberProcessor"""
    try:
        processor = NumberProcessor()
        print("✅ Number Processor creado exitosamente")
        return processor
    except Exception as e:
        print(f"❌ Error al crear Number Processor: {e}")
        traceback.print_exc()
        return None

# Función utilitaria para uso rápido
def procesar_numeros_rapido(cadena: str) -> List[int]:
    """
    Función utilitaria para procesar rápidamente una cadena y devolver solo los números válidos
    
    Args:
        cadena: Cadena de números a procesar
        
    Returns:
        Lista de enteros válidos
    """
    processor = NumberProcessor()
    resultado = processor.procesar_cadena_numeros(cadena)
    return [num.valor for num in resultado.numeros_validos] 