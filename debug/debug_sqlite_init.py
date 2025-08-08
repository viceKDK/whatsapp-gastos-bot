#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug SQLite Init

Prueba paso a paso la inicialización de SQLite para encontrar dónde falla.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

def test_sqlite_direct():
    """Prueba crear SQLiteStorage directamente."""
    print("[TEST] Creación directa de SQLiteStorage")
    print("=" * 40)
    
    try:
        from infrastructure.storage.sqlite_writer import SQLiteStorage
        
        print("1. Importando SQLiteStorage... OK")
        
        print("2. Creando instancia...")
        storage = SQLiteStorage("data/test_direct.db")
        
        print("3. [OK] SQLiteStorage creado exitosamente")
        
        print("4. Probando get_last_processed_message_timestamp()...")
        result = storage.get_last_processed_message_timestamp()
        
        if result is None:
            print("5. [OK] Método devuelve None (BD limpia)")
            return True
        else:
            print(f"5. [PROBLEMA] Método devuelve: {result}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Falló en paso: {e}")
        return False

def test_hybrid_storage():
    """Prueba crear HybridStorage paso a paso."""
    print(f"\n[TEST] Creación de HybridStorage")
    print("=" * 40)
    
    try:
        from infrastructure.storage.hybrid_storage import HybridStorage
        
        print("1. Importando HybridStorage... OK")
        
        print("2. Creando instancia...")
        storage = HybridStorage("data/test_hybrid.xlsx")
        
        print("3. [OK] HybridStorage creado exitosamente")
        
        print("4. Probando get_last_processed_timestamp()...")
        result = storage.get_last_processed_timestamp()
        
        if result is None:
            print("5. [OK] Método devuelve None (BD limpia)")
            return True
        else:
            print(f"5. [PROBLEMA] Método devuelve: {result}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Falló en paso: {e}")
        return False

if __name__ == "__main__":
    print("Debugging SQLite initialization issue...\n")
    
    # Test 1: SQLite directo
    sqlite_ok = test_sqlite_direct()
    
    # Test 2: HybridStorage
    hybrid_ok = test_hybrid_storage()
    
    print(f"\n{'='*40}")
    print("RESUMEN")
    print("="*40)
    print(f"SQLite directo:  {'OK' if sqlite_ok else 'FAIL'}")
    print(f"HybridStorage:   {'OK' if hybrid_ok else 'FAIL'}")
    
    if sqlite_ok and hybrid_ok:
        print("\n[OK] Todo funciona - problema puede ser en otra parte")
    else:
        print("\n[X] Hay problemas de inicialización básica")