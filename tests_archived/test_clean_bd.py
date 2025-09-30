#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test BD Limpia

Verifica que get_last_processed_timestamp() ahora devuelve None.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

def test_clean_storage():
    """Prueba que la BD esté realmente limpia."""
    print("[TEST] Verificación BD Limpia")
    print("=" * 40)
    
    try:
        from infrastructure.storage.hybrid_storage import HybridStorage
        
        print("1. Creando storage...")
        storage = HybridStorage("data/gastos.xlsx")
        
        print("2. Obteniendo último timestamp...")
        last_timestamp = storage.get_last_processed_timestamp()
        
        if last_timestamp is None:
            print("[OK] BD está limpia - get_last_processed_timestamp() devuelve None")
            print("     El bot NO debería mostrar timestamp problemático")
            return True
        else:
            print(f"[PROBLEMA] Aún devuelve timestamp: {last_timestamp}")
            print("     El cache SQLite puede tener datos viejos")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error creando storage: {e}")
        return False

if __name__ == "__main__":
    success = test_clean_storage()
    
    print(f"\n{'='*40}")
    if success:
        print("✅ BD LIMPIA - Listo para ejecutar bot sin problemas")
    else:
        print("❌ BD TODAVÍA TIENE DATOS - Necesita limpieza adicional")