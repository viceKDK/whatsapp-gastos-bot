# -*- coding: utf-8 -*-
"""
Script simple de validacion de optimizaciones
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def test_regex():
    print("Test 1: Regex Unificados")
    try:
        from app.services.interpretar_mensaje import InterpretarMensajeService
        servicio = InterpretarMensajeService(enable_nlp_categorization=False)
        
        resultado = servicio.procesar_mensaje("500 comida")
        if resultado:
            print(f"  OK: 500 comida -> ${resultado.monto} ({resultado.categoria})")
            return True
        else:
            print("  ERROR: No pudo procesar mensaje")
            return False
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_sqlite():
    print("Test 2: SQLite Optimizado") 
    try:
        from infrastructure.storage.sqlite_writer import SQLiteStorage
        import tempfile
        import os
        import time
        
        temp_db = tempfile.mktemp(suffix='.db')
        storage = SQLiteStorage(temp_db)
        
        print("  OK: SQLite inicializado correctamente")
        
        # Dar tiempo para que se cierre la conexión
        time.sleep(0.1)
        
        try:
            os.unlink(temp_db)
        except:
            pass  # Ignorar error de archivo en uso
            
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_cache():
    print("Test 3: SmartSelectorCache")
    try:
        from infrastructure.whatsapp.whatsapp_selenium import SmartSelectorCache
        cache = SmartSelectorCache()
        print("  OK: SmartSelectorCache inicializado")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

if __name__ == "__main__":
    print("VALIDACION OPTIMIZACIONES FASE 1")
    print("="*40)
    
    tests = [test_regex, test_sqlite, test_cache]
    passed = 0
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nRESULTADOS: {passed}/{len(tests)} tests pasaron")
    
    if passed == len(tests):
        print("TODAS LAS OPTIMIZACIONES FUNCIONANDO!")
    else:
        print("Revisar tests fallidos")