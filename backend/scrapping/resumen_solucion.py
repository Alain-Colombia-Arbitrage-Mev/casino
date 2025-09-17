#!/usr/bin/env python3
"""
RESUMEN DE LA SOLUCIÓN COMPLETA
Redis y PostgreSQL ahora sincronizados correctamente
"""

from database_sync import SyncedRouletteDatabase, log_message
import time
import sys

def purge_all_databases():
    """Función para limpiar completamente todas las bases de datos antes de ejecutar"""
    
    log_message("=" * 60)
    log_message("🧹 DEPURACIÓN COMPLETA DE BASES DE DATOS")
    log_message("=" * 60)
    
    print("\n⚠️  ADVERTENCIA:")
    print("   Esta operación eliminará TODOS los datos de:")
    print("   • Redis - Todas las claves de roulette")
    print("   • PostgreSQL - Tabla roulette_numbers completa")
    print("   • Archivos locales - Historial y contadores")
    
    # Confirmación del usuario
    response = input("\n¿Estás seguro de que quieres continuar? (si/no): ").lower()
    if response not in ['si', 's', 'yes', 'y']:
        log_message("❌ Operación cancelada por el usuario")
        return False
    
    log_message("🚀 Iniciando depuración completa...")
    
    # Inicializar base de datos
    db = SyncedRouletteDatabase()
    
    # Limpiar bases de datos
    redis_success, postgres_success = db.purge_all_data()
    
    # Limpiar archivos locales
    local_files_cleaned = clean_local_files()
    
    # Resultado final
    if redis_success and postgres_success and local_files_cleaned:
        log_message("🎉 ¡DEPURACIÓN COMPLETA EXITOSA!")
        log_message("✅ Redis: Limpio")
        log_message("✅ PostgreSQL: Limpio") 
        log_message("✅ Archivos locales: Limpios")
        print("\n🚀 Sistema listo para un inicio limpio")
        print("   Ejecuta: python scraper_final.py")
    else:
        log_message("⚠️ Depuración parcial:")
        log_message(f"   Redis: {'✅' if redis_success else '❌'}")
        log_message(f"   PostgreSQL: {'✅' if postgres_success else '❌'}")
        log_message(f"   Archivos locales: {'✅' if local_files_cleaned else '❌'}")
    
    db.close_connections()
    log_message("=" * 60)
    return redis_success and postgres_success and local_files_cleaned

def clean_local_files():
    """Limpiar archivos locales de datos"""
    import os
    
    log_message("🗂️ Limpiando archivos locales...")
    
    files_to_clean = [
        "roulette_data/history_counter.txt",
        "roulette_data/last_seen_numbers.json", 
        "roulette_data/pending_numbers.txt",
        "roulette_data/processed_numbers.txt",
        "roulette_data/roulette_numbers.json"
    ]
    
    cleaned_count = 0
    
    for file_path in files_to_clean:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                log_message(f"🗑️ Eliminado: {file_path}")
                cleaned_count += 1
            else:
                log_message(f"ℹ️ No existe: {file_path}")
        except Exception as e:
            log_message(f"❌ Error eliminando {file_path}: {e}", "ERROR")
    
    # Crear archivos básicos limpios
    try:
        os.makedirs("roulette_data", exist_ok=True)
        
        # Crear archivos con contenido inicial
        with open("roulette_data/history_counter.txt", "w") as f:
            f.write("0")
        
        with open("roulette_data/last_seen_numbers.json", "w") as f:
            f.write("[]")
            
        with open("roulette_data/processed_numbers.txt", "w") as f:
            f.write("")
            
        with open("roulette_data/pending_numbers.txt", "w") as f:
            f.write("")
            
        with open("roulette_data/roulette_numbers.json", "w") as f:
            f.write("[]")
        
        log_message("✅ Archivos locales reiniciados correctamente")
        return True
        
    except Exception as e:
        log_message(f"❌ Error reiniciando archivos: {e}", "ERROR")
        return False

def show_solution_summary():
    """Mostrar resumen completo de la solución"""
    
    log_message("=" * 60)
    log_message("🎯 RESUMEN DE LA SOLUCIÓN COMPLETA")
    log_message("=" * 60)
    
    print("\n📊 PROBLEMA ORIGINAL:")
    print("   ❌ Redis tenía datos actualizados (hasta 18 junio)")
    print("   ❌ PostgreSQL tenía datos viejos (hasta 31 mayo)")
    print("   ❌ Estructuras diferentes e incompatibles")
    print("   ❌ Errores de columnas faltantes")
    
    print("\n🔧 SOLUCIÓN IMPLEMENTADA:")
    print("   ✅ Clase SyncedRouletteDatabase para mantener ambas bases sincronizadas")
    print("   ✅ Esquema PostgreSQL simplificado y corregido (tabla: roulette_numbers)")
    print("   ✅ Redis con estructura optimizada (claves especializadas)")
    print("   ✅ Scraper final sin login repetido (scraper_final.py)")
    print("   ✅ Intervalos reducidos: 60s → 10s para mayor velocidad")
    
    print("\n📋 ARCHIVOS CREADOS:")
    print("   📄 database_sync.py - Clase de sincronización")
    print("   📄 scraper_final.py - Scraper optimizado")
    print("   📄 fix_postgres_schema.py - Corrección de esquema")
    
    # Verificar estado actual
    db = SyncedRouletteDatabase()
    
    print("\n🔍 ESTADO ACTUAL DE LAS BASES:")
    status = db.get_sync_status()
    
    if status:
        redis_info = status['redis']
        postgres_info = status['postgres']
        
        print(f"\n📊 COMPARACIÓN DETALLADA:")
        print(f"   Redis - Último número: {redis_info['latest']}")
        print(f"   Redis - Total registros: {redis_info['count']}")
        print(f"   PostgreSQL - Último número: {postgres_info['latest']}")
        print(f"   PostgreSQL - Total registros: {postgres_info['count']}")
        
        if status['synced']:
            print("   🎉 ¡BASES COMPLETAMENTE SINCRONIZADAS!")
        else:
            print("   ⚠️ Bases funcionando pero en proceso de sincronización")
            print("   💡 Esto es normal - PostgreSQL usa nueva tabla limpia")
    
    print("\n🚀 PRÓXIMOS PASOS:")
    print("   1. Ejecutar: python scraper_final.py")
    print("   2. Monitorear: python database_sync.py")
    print("   3. Las bases se sincronizarán automáticamente")
    
    print("\n✨ CARACTERÍSTICAS FINALES:")
    print("   🔄 Sin login repetido (sesión persistente)")
    print("   ⚡ Intervalos de 10 segundos (was 60s)")
    print("   💾 Guardado simultáneo en Redis + PostgreSQL")
    print("   🎯 Detección inteligente de números nuevos")
    print("   📊 Monitoreo de estado de sincronización")
    
    db.close_connections()
    
    log_message("=" * 60)
    log_message("✅ SOLUCIÓN COMPLETA IMPLEMENTADA")
    log_message("=" * 60)

if __name__ == "__main__":
    print("\n🎯 SISTEMA DE GESTIÓN DE RULETA")
    print("=" * 40)
    print("1. Mostrar resumen de la solución")
    print("2. Depurar todas las bases de datos")
    print("3. Salir")
    
    while True:
        try:
            choice = input("\nSelecciona una opción (1-3): ").strip()
            
            if choice == "1":
                show_solution_summary()
                break
            elif choice == "2":
                success = purge_all_databases()
                if success:
                    print("\n✨ Las bases de datos están limpias y listas para usar")
                else:
                    print("\n⚠️ Hubo algunos problemas durante la limpieza")
                break
            elif choice == "3":
                print("👋 ¡Hasta luego!")
                sys.exit(0)
            else:
                print("❌ Opción inválida. Por favor selecciona 1, 2 o 3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            sys.exit(0) 