#!/usr/bin/env python3
"""
Monitor de sincronización en tiempo real
Verifica que Redis y PostgreSQL se mantengan sincronizados
"""

import time
import os
from datetime import datetime
from database_sync import SyncedRouletteDatabase, log_message

def clear_screen():
    """Limpiar la pantalla"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_sync_dashboard():
    """Mostrar dashboard de sincronización"""
    db = SyncedRouletteDatabase()
    
    iterations = 0
    try:
        while True:
            clear_screen()
            print("🎯 MONITOR DE SINCRONIZACIÓN EN TIEMPO REAL")
            print("=" * 50)
            print(f"Iteración: {iterations + 1}")
            print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 50)
            
            # Obtener estado
            status = db.get_sync_status()
            
            if status:
                redis_info = status['redis']
                postgres_info = status['postgres']
                
                print("\n📊 ESTADO ACTUAL:")
                print(f"   Redis      - Último: {redis_info['latest']:<3} | Total: {redis_info['count']:<6}")
                print(f"   PostgreSQL - Último: {postgres_info['latest']:<3} | Total: {postgres_info['count']:<6}")
                
                # Verificar sincronización
                if status['synced']:
                    print("   Estado: 🎉 PERFECTAMENTE SINCRONIZADO")
                else:
                    print("   Estado: ⚠️  En proceso de sincronización")
                
                # Calcular diferencias
                redis_count = redis_info['count']
                postgres_count = postgres_info['count']
                
                if redis_count == postgres_count:
                    print(f"   Diferencia: ✅ Mismo número de registros ({redis_count})")
                else:
                    diff = abs(redis_count - postgres_count)
                    print(f"   Diferencia: ❌ {diff} registros de diferencia")
                
                # Mostrar tendencia
                if iterations > 0:
                    print(f"\n📈 ACTIVIDAD:")
                    print(f"   Nuevos registros desde última verificación")
                    print(f"   Redis: +{redis_count - getattr(show_sync_dashboard, 'last_redis_count', 0)}")
                    print(f"   PostgreSQL: +{postgres_count - getattr(show_sync_dashboard, 'last_postgres_count', 0)}")
                
                # Guardar para próxima iteración
                show_sync_dashboard.last_redis_count = redis_count
                show_sync_dashboard.last_postgres_count = postgres_count
                
            else:
                print("❌ Error obteniendo estado de sincronización")
            
            print("\n" + "=" * 50)
            print("Presiona Ctrl+C para salir")
            print("Actualizando cada 5 segundos...")
            
            time.sleep(5)
            iterations += 1
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor detenido por usuario")
    finally:
        db.close_connections()

if __name__ == "__main__":
    show_sync_dashboard() 