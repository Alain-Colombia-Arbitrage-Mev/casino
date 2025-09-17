#!/usr/bin/env python3
"""
Sistema de Gestión de Sectores Personalizados
=============================================

Este módulo maneja la definición, almacenamiento y análisis de sectores 
personalizados de la ruleta, integrándose con las tablas de Supabase.

Características:
- Creación y gestión de sectores personalizados
- Almacenamiento en sectores_definiciones
- Seguimiento de aciertos por sector en sectores_conteos
- Análisis estadístico de rendimiento por sector
- Integración con el sistema de predicciones
"""

import json
import datetime
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import traceback

@dataclass
class SectorDefinicion:
    """Definición de un sector personalizado"""
    id: Optional[int]
    nombre_sector: str
    numeros: List[int]
    created_at: Optional[str] = None
    
    def to_dict(self):
        return {
            'nombre_sector': self.nombre_sector,
            'numeros': ','.join(map(str, self.numeros)),
            'created_at': self.created_at or datetime.datetime.now().isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        numeros_list = []
        if isinstance(data.get('numeros'), str):
            numeros_list = [int(n.strip()) for n in data['numeros'].split(',') if n.strip().isdigit()]
        elif isinstance(data.get('numeros'), list):
            numeros_list = [int(n) for n in data['numeros'] if isinstance(n, (int, str)) and str(n).isdigit()]
        
        return cls(
            id=data.get('id'),
            nombre_sector=data.get('nombre_sector', ''),
            numeros=numeros_list,
            created_at=data.get('created_at')
        )

@dataclass
class SectorConteo:
    """Conteo de aciertos para un sector"""
    id_sector_definicion: int
    conteo: int
    updated_at: Optional[str] = None

class SectorManager:
    """
    Gestor principal de sectores personalizados
    """
    
    def __init__(self, supabase_client=None):
        self.supabase_client = supabase_client
        self.sectores_cache = {}  # Cache local para mejorar rendimiento
        self.conteos_cache = {}
        
        # Sectores predefinidos comunes
        self.sectores_predefinidos = {
            'Vecinos_Cero': [32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26],
            'Tier': [5, 8, 10, 11, 13, 16, 23, 24, 27, 30, 33, 36],
            'Orphelins': [1, 6, 9, 14, 17, 20, 31, 34],
            'Primera_Docena': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'Segunda_Docena': [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
            'Tercera_Docena': [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36],
            'Primera_Columna': [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34],
            'Segunda_Columna': [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
            'Tercera_Columna': [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
            'Rojos': [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36],
            'Negros': [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35],
            'Pares': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36],
            'Impares': [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35]
        }
        
        # Cargar sectores existentes
        self.cargar_sectores_desde_db()
    
    def crear_sector(self, nombre: str, numeros: List[int]) -> bool:
        """
        Crea un nuevo sector personalizado
        
        Args:
            nombre: Nombre del sector
            numeros: Lista de números del sector (0-36)
            
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            # Validar entrada
            if not nombre or not numeros:
                print("❌ Nombre y números son requeridos para crear un sector")
                return False
            
            # Validar números
            numeros_validos = []
            for num in numeros:
                if isinstance(num, (int, str)) and 0 <= int(num) <= 36:
                    numeros_validos.append(int(num))
                else:
                    print(f"⚠️ Número inválido ignorado: {num}")
            
            if not numeros_validos:
                print("❌ No hay números válidos para el sector")
                return False
            
            # Verificar si ya existe
            if self.existe_sector(nombre):
                print(f"⚠️ El sector '{nombre}' ya existe")
                return False
            
            # Crear sector
            sector = SectorDefinicion(
                id=None,
                nombre_sector=nombre,
                numeros=numeros_validos
            )
            
            # Guardar en base de datos
            if self.supabase_client:
                response = self.supabase_client.table('sectores_definiciones')\
                    .insert(sector.to_dict()).execute()
                
                if response.data:
                    sector.id = response.data[0]['id']
                    self.sectores_cache[nombre] = sector
                    
                    # Inicializar conteo en 0
                    self.inicializar_conteo_sector(sector.id)
                    
                    print(f"✅ Sector '{nombre}' creado con {len(numeros_validos)} números")
                    return True
                else:
                    print(f"❌ Error al guardar sector en DB: {response}")
                    return False
            else:
                # Modo sin DB - solo cache local
                sector.id = len(self.sectores_cache) + 1
                self.sectores_cache[nombre] = sector
                print(f"✅ Sector '{nombre}' creado localmente")
                return True
                
        except Exception as e:
            print(f"❌ Error al crear sector: {e}")
            traceback.print_exc()
            return False
    
    def existe_sector(self, nombre: str) -> bool:
        """Verifica si un sector existe"""
        return nombre in self.sectores_cache
    
    def obtener_sector(self, nombre: str) -> Optional[SectorDefinicion]:
        """Obtiene un sector por nombre"""
        return self.sectores_cache.get(nombre)
    
    def listar_sectores(self) -> Dict[str, SectorDefinicion]:
        """Lista todos los sectores disponibles"""
        return self.sectores_cache.copy()
    
    def eliminar_sector(self, nombre: str) -> bool:
        """
        Elimina un sector personalizado
        
        Args:
            nombre: Nombre del sector a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            if not self.existe_sector(nombre):
                print(f"⚠️ El sector '{nombre}' no existe")
                return False
            
            sector = self.sectores_cache[nombre]
            
            # Eliminar de base de datos
            if self.supabase_client and sector.id:
                response = self.supabase_client.table('sectores_definiciones')\
                    .delete().eq('id', sector.id).execute()
                
                if response.data:
                    del self.sectores_cache[nombre]
                    print(f"✅ Sector '{nombre}' eliminado")
                    return True
                else:
                    print(f"❌ Error al eliminar sector de DB")
                    return False
            else:
                # Modo local
                del self.sectores_cache[nombre]
                print(f"✅ Sector '{nombre}' eliminado localmente")
                return True
                
        except Exception as e:
            print(f"❌ Error al eliminar sector: {e}")
            return False
    
    def verificar_acierto_sectores(self, numero_ganador: int) -> List[str]:
        """
        Verifica qué sectores contienen el número ganador
        
        Args:
            numero_ganador: Número que salió en la ruleta
            
        Returns:
            Lista de nombres de sectores que contienen el número
        """
        sectores_con_acierto = []
        
        for nombre, sector in self.sectores_cache.items():
            if numero_ganador in sector.numeros:
                sectores_con_acierto.append(nombre)
                # Actualizar conteo
                self.incrementar_conteo_sector(nombre)
        
        return sectores_con_acierto
    
    def incrementar_conteo_sector(self, nombre_sector: str) -> bool:
        """Incrementa el conteo de aciertos para un sector"""
        try:
            sector = self.obtener_sector(nombre_sector)
            if not sector:
                return False
            
            # Actualizar cache local
            self.conteos_cache[nombre_sector] = self.conteos_cache.get(nombre_sector, 0) + 1
            
            # Actualizar en base de datos
            if self.supabase_client and sector.id:
                # Usar upsert para actualizar o insertar
                conteo_data = {
                    'id_estado_analizador': 1,  # ID fijo del analizador principal
                    'id_sector_definicion': sector.id,
                    'conteo': self.conteos_cache[nombre_sector],
                    'updated_at': datetime.datetime.now().isoformat()
                }
                
                response = self.supabase_client.table('sectores_conteos')\
                    .upsert(conteo_data, on_conflict='id_estado_analizador,id_sector_definicion')\
                    .execute()
                
                if response.data:
                    print(f"📊 Conteo actualizado para sector '{nombre_sector}': {self.conteos_cache[nombre_sector]}")
                    return True
            
            return True
            
        except Exception as e:
            print(f"❌ Error al incrementar conteo: {e}")
            return False
    
    def obtener_conteo_sector(self, nombre_sector: str) -> int:
        """Obtiene el conteo actual de un sector"""
        return self.conteos_cache.get(nombre_sector, 0)
    
    def obtener_estadisticas_sectores(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas de todos los sectores
        
        Returns:
            Dict con estadísticas por sector
        """
        estadisticas = {}
        
        for nombre, sector in self.sectores_cache.items():
            conteo = self.obtener_conteo_sector(nombre)
            
            estadisticas[nombre] = {
                'numeros': sector.numeros,
                'cantidad_numeros': len(sector.numeros),
                'aciertos_totales': conteo,
                'probabilidad_teorica': len(sector.numeros) / 37,  # Incluyendo el 0
                'created_at': sector.created_at
            }
        
        return estadisticas
    
    def cargar_sectores_desde_db(self):
        """Carga sectores desde la base de datos"""
        try:
            # Primero cargar sectores predefinidos
            for nombre, numeros in self.sectores_predefinidos.items():
                sector = SectorDefinicion(
                    id=None,
                    nombre_sector=nombre,
                    numeros=numeros,
                    created_at=datetime.datetime.now().isoformat()
                )
                self.sectores_cache[nombre] = sector
            
            if not self.supabase_client:
                print("ℹ️ Sectores predefinidos cargados (sin conexión DB)")
                return
            
            # Cargar sectores personalizados desde DB
            response = self.supabase_client.table('sectores_definiciones')\
                .select('*').execute()
            
            if response.data:
                for sector_data in response.data:
                    sector = SectorDefinicion.from_dict(sector_data)
                    self.sectores_cache[sector.nombre_sector] = sector
                
                print(f"✅ Cargados {len(response.data)} sectores personalizados desde DB")
            
            # Cargar conteos
            response_conteos = self.supabase_client.table('sectores_conteos')\
                .select('*, sectores_definiciones(nombre_sector)')\
                .execute()
            
            if response_conteos.data:
                for conteo_data in response_conteos.data:
                    if conteo_data.get('sectores_definiciones'):
                        nombre = conteo_data['sectores_definiciones']['nombre_sector']
                        self.conteos_cache[nombre] = conteo_data['conteo']
                
                print(f"✅ Cargados conteos para {len(response_conteos.data)} sectores")
            
        except Exception as e:
            print(f"⚠️ Error al cargar sectores desde DB: {e}")
            # Asegurar que al menos los sectores predefinidos estén disponibles
            if not self.sectores_cache:
                for nombre, numeros in self.sectores_predefinidos.items():
                    sector = SectorDefinicion(
                        id=None,
                        nombre_sector=nombre,
                        numeros=numeros
                    )
                    self.sectores_cache[nombre] = sector
    
    def inicializar_conteo_sector(self, sector_id: int):
        """Inicializa el conteo de un sector en 0"""
        try:
            if self.supabase_client:
                conteo_data = {
                    'id_estado_analizador': 1,
                    'id_sector_definicion': sector_id,
                    'conteo': 0,
                    'updated_at': datetime.datetime.now().isoformat()
                }
                
                self.supabase_client.table('sectores_conteos')\
                    .upsert(conteo_data, on_conflict='id_estado_analizador,id_sector_definicion')\
                    .execute()
        except Exception as e:
            print(f"Error al inicializar conteo: {e}")
    
    def crear_sectores_predefinidos_en_db(self):
        """Crea los sectores predefinidos en la base de datos si no existen"""
        if not self.supabase_client:
            return
        
        try:
            for nombre, numeros in self.sectores_predefinidos.items():
                # Verificar si ya existe
                existing = self.supabase_client.table('sectores_definiciones')\
                    .select('id').eq('nombre_sector', nombre).execute()
                
                if not existing.data:
                    # No existe, crearlo
                    sector = SectorDefinicion(
                        id=None,
                        nombre_sector=nombre,
                        numeros=numeros
                    )
                    
                    response = self.supabase_client.table('sectores_definiciones')\
                        .insert(sector.to_dict()).execute()
                    
                    if response.data:
                        sector_id = response.data[0]['id']
                        self.inicializar_conteo_sector(sector_id)
                        print(f"✅ Sector predefinido '{nombre}' creado en DB")
            
        except Exception as e:
            print(f"Error al crear sectores predefinidos: {e}")
    
    def resetear_conteos(self) -> bool:
        """Resetea todos los conteos de sectores a 0"""
        try:
            # Resetear cache local
            self.conteos_cache = {nombre: 0 for nombre in self.sectores_cache.keys()}
            
            # Resetear en base de datos
            if self.supabase_client:
                # Actualizar todos los conteos a 0
                for nombre, sector in self.sectores_cache.items():
                    if sector.id:
                        conteo_data = {
                            'id_estado_analizador': 1,
                            'id_sector_definicion': sector.id,
                            'conteo': 0,
                            'updated_at': datetime.datetime.now().isoformat()
                        }
                        
                        self.supabase_client.table('sectores_conteos')\
                            .upsert(conteo_data, on_conflict='id_estado_analizador,id_sector_definicion')\
                            .execute()
                
                print("✅ Conteos de sectores reseteados")
                return True
            
            return True
            
        except Exception as e:
            print(f"❌ Error al resetear conteos: {e}")
            return False

def create_sector_manager(supabase_client=None) -> SectorManager:
    """Factory function para crear SectorManager"""
    try:
        manager = SectorManager(supabase_client=supabase_client)
        print("✅ Sector Manager creado exitosamente")
        return manager
    except Exception as e:
        print(f"❌ Error al crear Sector Manager: {e}")
        traceback.print_exc()
        return None 