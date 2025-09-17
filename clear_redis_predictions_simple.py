#!/usr/bin/env python3
"""
Script simple para limpiar predicciones problemáticas de Redis
"""

import redis
import json

def clear_problematic_predictions():
    try:
        # Conectar a Redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Obtener todas las claves de predicciones
        prediction_keys = r.keys('prediction:*')
        
        print(f"Encontradas {len(prediction_keys)} predicciones en Redis")
        
        cleared_count = 0
        for key in prediction_keys:
            try:
                # Intentar obtener la predicción
                pred_data = r.hgetall(key)
                
                # Si contiene datos problemáticos, eliminarla
                if pred_data:
                    # Verificar si tiene campos booleanos problemáticos
                    has_boolean_issue = False
                    for field, value in pred_data.items():
                        if isinstance(value, bool) or value in ['True', 'False']:
                            has_boolean_issue = True
                            break
                    
                    if has_boolean_issue:
                        r.delete(key)
                        cleared_count += 1
                        print(f"✅ Eliminada predicción problemática: {key}")
                        
            except Exception as e:
                print(f"❌ Error procesando {key}: {e}")
                # Si hay error, eliminar la clave problemática
                r.delete(key)
                cleared_count += 1
        
        print(f"\n🧹 Limpieza completada: {cleared_count} predicciones eliminadas")
        
        # Limpiar también las listas de predicciones pendientes
        try:
            r.delete('ai:pending_predictions')
            print("✅ Lista de predicciones pendientes limpiada")
        except:
            pass
            
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        return False

if __name__ == "__main__":
    print("=== LIMPIEZA DE PREDICCIONES PROBLEMÁTICAS ===\n")
    success = clear_problematic_predictions()
    if success:
        print("\n✅ Limpieza exitosa. Ahora puedes probar el sistema AI.")
    else:
        print("\n❌ Error en la limpieza.")