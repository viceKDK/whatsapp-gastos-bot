#!/usr/bin/env python3
"""
Test manual de duplicados con el storage real
"""

import sys
import os
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from domain.models.gasto import Gasto
from infrastructure.storage.hybrid_storage import HybridStorage

def test_duplicate_with_real_storage():
    """Test duplicados con el storage real del sistema."""
    
    print("=== TEST DE DUPLICADOS CON STORAGE REAL ===")
    
    # Usar el storage real y forzar procesamiento inmediato (no batch)
    storage = HybridStorage('data/gastos.xlsx')
    
    # Forzar flush del batch para procesar cualquier pendiente
    storage.sqlite_storage.flush_batch()
    
    # Crear gasto de prueba (similar a los que aparecen en los logs)
    gasto_test = Gasto(
        monto=Decimal('300'),
        categoria='servicios',
        descripcion='internet',
        fecha=datetime(2025, 8, 8, 0, 33, 0)
    )
    
    print(f"\n1. Intentando guardar gasto: ${gasto_test.monto} - {gasto_test.categoria} - {gasto_test.descripcion}")
    
    # Intentar guardarlo
    resultado = storage.guardar_gasto(gasto_test)
    # Forzar flush del batch
    storage.sqlite_storage.flush_batch()
    
    if resultado:
        print("   -> RESULTADO: GUARDADO (era nuevo)")
    else:
        print("   -> RESULTADO: RECHAZADO (duplicado detectado)")
    
    # Intentar guardarlo de nuevo
    print(f"\n2. Intentando guardar el MISMO gasto otra vez...")
    resultado2 = storage.guardar_gasto(gasto_test)
    # Forzar flush del batch
    storage.sqlite_storage.flush_batch()
    
    if resultado2:
        print("   -> RESULTADO: GUARDADO (PROBLEMA - no debería pasar)")
    else:
        print("   -> RESULTADO: RECHAZADO (correcto - duplicado detectado)")
    
    # Gasto ligeramente diferente
    gasto_diferente = Gasto(
        monto=Decimal('300'),
        categoria='servicios', 
        descripcion='internet',
        fecha=datetime(2025, 8, 8, 1, 0, 0)  # Diferente hora
    )
    
    print(f"\n3. Intentando gasto similar con diferente hora...")
    resultado3 = storage.guardar_gasto(gasto_diferente)
    # Forzar flush del batch
    storage.sqlite_storage.flush_batch()
    
    if resultado3:
        print("   -> RESULTADO: GUARDADO (PROBLEMA - debería ser rechazado por similar)")  
    else:
        print("   -> RESULTADO: RECHAZADO (correcto - similar detectado)")

if __name__ == "__main__":
    test_duplicate_with_real_storage()
    print("\n" + "="*50)
    print("Test completado. Revisa los resultados arriba.")
    print("="*50)