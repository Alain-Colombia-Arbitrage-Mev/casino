#!/usr/bin/env python3
"""
Script de migración de Supabase a PostgreSQL + Redis
Este script ayuda a migrar los datos existentes y cambiar la configuración
"""

import os
import sys
import shutil
import json
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_current_files():
    """Crear backup de los archivos actuales"""
    logger.info("🔄 Creando backup de archivos actuales...")
    
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        'app.py',
        'requirements.txt',
        '../frontend/utils/supabase.ts'
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, backup_path)
            logger.info(f"✅ Backup creado: {file_path} -> {backup_path}")
        else:
            logger.warning(f"⚠️ Archivo no encontrado: {file_path}")
    
    logger.info(f"✅ Backup completado en: {backup_dir}")
    return backup_dir

def switch_backend_files():
    """Cambiar los archivos del backend"""
    logger.info("🔄 Cambiando archivos del backend...")
    
    # Renombrar app.py actual a app_supabase.py
    if os.path.exists('app.py'):
        shutil.move('app.py', 'app_supabase.py')
        logger.info("✅ app.py -> app_supabase.py")
    
    # Renombrar app_new.py a app.py
    if os.path.exists('app_new.py'):
        shutil.move('app_new.py', 'app.py')
        logger.info("✅ app_new.py -> app.py")
    else:
        logger.error("❌ app_new.py no encontrado")
        return False
    
    return True

def switch_frontend_files():
    """Cambiar los archivos del frontend"""
    logger.info("🔄 Cambiando archivos del frontend...")
    
    frontend_utils_dir = '../frontend/utils'
    
    # Renombrar supabase.ts actual a supabase_backup.ts
    supabase_path = os.path.join(frontend_utils_dir, 'supabase.ts')
    if os.path.exists(supabase_path):
        backup_path = os.path.join(frontend_utils_dir, 'supabase_backup.ts')
        shutil.move(supabase_path, backup_path)
        logger.info("✅ supabase.ts -> supabase_backup.ts")
    
    # Copiar api.ts a supabase.ts para mantener compatibilidad
    api_path = os.path.join(frontend_utils_dir, 'api.ts')
    if os.path.exists(api_path):
        shutil.copy2(api_path, supabase_path)
        logger.info("✅ api.ts -> supabase.ts (para compatibilidad)")
    else:
        logger.error("❌ api.ts no encontrado")
        return False
    
    return True

def install_dependencies():
    """Instalar las nuevas dependencias"""
    logger.info("🔄 Instalando nuevas dependencias...")
    
    try:
        import subprocess
        
        # Instalar redis
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'redis==4.6.0'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Redis instalado correctamente")
        else:
            logger.error(f"❌ Error instalando Redis: {result.stderr}")
            return False
        
        # Verificar psycopg2-binary
        try:
            import psycopg2
            logger.info("✅ psycopg2-binary ya está disponible")
        except ImportError:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary==2.9.6'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ psycopg2-binary instalado correctamente")
            else:
                logger.error(f"❌ Error instalando psycopg2-binary: {result.stderr}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error instalando dependencias: {e}")
        return False

def test_connections():
    """Probar las conexiones a PostgreSQL y Redis"""
    logger.info("🔄 Probando conexiones...")
    
    try:
        # Importar el nuevo database manager
        from database import db_manager
        
        # Probar PostgreSQL
        try:
            status = db_manager.get_database_status()
            if status.get('success'):
                logger.info("✅ Conexión a PostgreSQL exitosa")
            else:
                logger.error(f"❌ Error en PostgreSQL: {status.get('error')}")
                return False
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            return False
        
        # Probar Redis
        try:
            if db_manager.redis_client:
                db_manager.redis_client.ping()
                logger.info("✅ Conexión a Redis exitosa")
            else:
                logger.warning("⚠️ Redis no disponible (continuará sin caché)")
        except Exception as e:
            logger.warning(f"⚠️ Redis no disponible: {e} (continuará sin caché)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando conexiones: {e}")
        return False

def create_migration_summary():
    """Crear un resumen de la migración"""
    summary = {
        "migration_date": datetime.now().isoformat(),
        "changes": {
            "backend": {
                "old_file": "app.py (renamed to app_supabase.py)",
                "new_file": "app.py (from app_new.py)",
                "database": "Changed from Supabase to PostgreSQL + Redis"
            },
            "frontend": {
                "old_file": "supabase.ts (renamed to supabase_backup.ts)",
                "new_file": "supabase.ts (from api.ts for compatibility)",
                "api_calls": "Changed from Supabase client to direct HTTP API calls"
            },
            "dependencies": {
                "added": ["redis==4.6.0"],
                "existing": ["psycopg2-binary==2.9.6"]
            }
        },
        "database_config": {
            "postgresql": "postgresql://postgres:JqPnbywtvvZyINvBFikSRYdKqGmtTFFj@postgres.railway.internal:5432/railway",
            "redis": "redis://default:kuBKgwJxPrMoMOWqpobsGZIcpgnOFwoW@redis.railway.internal:6379"
        },
        "rollback_instructions": [
            "1. Rename app.py to app_new.py",
            "2. Rename app_supabase.py to app.py",
            "3. Rename supabase.ts to api.ts",
            "4. Rename supabase_backup.ts to supabase.ts",
            "5. Restart the application"
        ]
    }
    
    with open('migration_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("✅ Resumen de migración creado: migration_summary.json")

def main():
    """Función principal de migración"""
    logger.info("🚀 Iniciando migración de Supabase a PostgreSQL + Redis")
    
    try:
        # 1. Crear backup
        backup_dir = backup_current_files()
        
        # 2. Instalar dependencias
        if not install_dependencies():
            logger.error("❌ Error instalando dependencias. Migración abortada.")
            return False
        
        # 3. Cambiar archivos del backend
        if not switch_backend_files():
            logger.error("❌ Error cambiando archivos del backend. Migración abortada.")
            return False
        
        # 4. Cambiar archivos del frontend
        if not switch_frontend_files():
            logger.error("❌ Error cambiando archivos del frontend. Migración abortada.")
            return False
        
        # 5. Probar conexiones
        if not test_connections():
            logger.error("❌ Error en las conexiones. Revise la configuración.")
            return False
        
        # 6. Crear resumen
        create_migration_summary()
        
        logger.info("🎉 ¡Migración completada exitosamente!")
        logger.info("📋 Pasos siguientes:")
        logger.info("   1. Reinicie el servidor backend: python app.py")
        logger.info("   2. Reinicie el servidor frontend")
        logger.info("   3. Verifique que todo funcione correctamente")
        logger.info(f"   4. El backup está en: {backup_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        return False

def rollback():
    """Función para revertir la migración"""
    logger.info("🔄 Iniciando rollback de la migración...")
    
    try:
        # Revertir backend
        if os.path.exists('app_supabase.py'):
            if os.path.exists('app.py'):
                shutil.move('app.py', 'app_new.py')
            shutil.move('app_supabase.py', 'app.py')
            logger.info("✅ Backend revertido")
        
        # Revertir frontend
        frontend_utils_dir = '../frontend/utils'
        supabase_path = os.path.join(frontend_utils_dir, 'supabase.ts')
        backup_path = os.path.join(frontend_utils_dir, 'supabase_backup.ts')
        
        if os.path.exists(backup_path):
            if os.path.exists(supabase_path):
                api_path = os.path.join(frontend_utils_dir, 'api.ts')
                if not os.path.exists(api_path):
                    shutil.copy2(supabase_path, api_path)
            shutil.move(backup_path, supabase_path)
            logger.info("✅ Frontend revertido")
        
        logger.info("🎉 Rollback completado exitosamente!")
        logger.info("📋 Reinicie los servidores para aplicar los cambios")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error durante el rollback: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        main()