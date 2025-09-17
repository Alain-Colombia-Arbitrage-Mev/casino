#!/usr/bin/env python3
"""
Script para arreglar el esquema de PostgreSQL
"""

import psycopg2
import psycopg2.extras
import json
import os
from dotenv import load_dotenv

load_dotenv()

def fix_postgres_schema():
    """Arreglar el esquema de PostgreSQL para que funcione correctamente"""
    
    db_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ No se encontró DATABASE_URL")
        return False
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("🔍 === VERIFICANDO ESQUEMA ACTUAL ===")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'roulette_history' 
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        print("Columnas actuales en roulette_history:")
        for col, dtype in columns:
            print(f"  - {col}: {dtype}")
        
        # Verificar si session_data existe
        has_session_data = any(col[0] == 'session_data' for col in columns)
        
        if has_session_data:
            print("✅ La columna session_data ya existe")
        else:
            print("\n🔧 === AGREGANDO COLUMNA session_data ===")
            try:
                cursor.execute('ALTER TABLE roulette_history ADD COLUMN session_data JSONB;')
                conn.commit()
                print("✅ Columna session_data agregada exitosamente")
            except Exception as e:
                print(f"⚠️ Error agregando columna: {e}")
                conn.rollback()
        
        # Verificar esquema final
        print("\n📊 === ESQUEMA FINAL ===")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'roulette_history' 
            ORDER BY ordinal_position;
        """)
        final_columns = cursor.fetchall()
        
        for col, dtype in final_columns:
            print(f"  - {col}: {dtype}")
        
        # Test de inserción
        print("\n🧪 === PROBANDO INSERCIÓN ===")
        test_data = {'test': True, 'timestamp': '2025-06-18T00:00:00'}
        cursor.execute("""
            INSERT INTO roulette_history (session_data) 
            VALUES (%s) RETURNING id;
        """, (psycopg2.extras.Json(test_data),))
        
        result = cursor.fetchone()
        test_id = result[0] if result else None
        print(f"✅ Test de inserción exitoso (ID: {test_id})")
        
        # Limpiar test
        cursor.execute("DELETE FROM roulette_history WHERE id = %s;", (test_id,))
        conn.commit()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🛠️ ARREGLANDO ESQUEMA DE POSTGRESQL")
    print("=" * 50)
    
    success = fix_postgres_schema()
    
    print("=" * 50)
    if success:
        print("✅ ESQUEMA ARREGLADO EXITOSAMENTE")
        print("PostgreSQL ahora debería funcionar correctamente")
    else:
        print("❌ ERROR ARREGLANDO ESQUEMA") 