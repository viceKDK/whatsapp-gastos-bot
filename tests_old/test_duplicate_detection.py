#!/usr/bin/env python3
"""
Test del sistema de detección de duplicados
"""

import sys
import os
import tempfile
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.models.gasto import Gasto
from infrastructure.storage.sqlite_writer import SQLiteStorage
from infrastructure.storage.hybrid_storage import HybridStorage
from decimal import Decimal

def test_duplicate_detection():
    """Test de la detección de duplicados en SQLite."""
    print(">> Testing detección de duplicados...")
    
    # Usar archivo temporal para el test
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        db_path = temp_db.name
    
    try:
        # Crear storage
        storage = SQLiteStorage(db_path)
        
        # Crear gasto original
        gasto_original = Gasto(
            monto=Decimal('300'),
            categoria='servicios',
            descripcion='internet',
            fecha=datetime(2025, 8, 8, 13, 0, 0)
        )
        
        print(f"1. Guardando gasto original: {gasto_original}")
        success1 = storage.guardar_gasto(gasto_original, use_batch=False)
        print(f"   -> Resultado: {'GUARDADO' if success1 else 'FALLO'}")
        
        # Intentar guardar duplicado exacto
        gasto_duplicado = Gasto(
            monto=Decimal('300'),
            categoria='servicios', 
            descripcion='internet',
            fecha=datetime(2025, 8, 8, 13, 30, 0)  # Diferente hora, mismo día
        )
        
        print(f"\n2. Intentando guardar duplicado: {gasto_duplicado}")
        success2 = storage.guardar_gasto(gasto_duplicado, use_batch=False)
        print(f"   -> Resultado: {'RECHAZADO (correcto)' if not success2 else 'ACEPTADO (incorrecto)'}")
        
        # Intentar guardar gasto similar pero válido
        gasto_similar = Gasto(
            monto=Decimal('500'),  # Diferente monto
            categoria='servicios',
            descripcion='internet',
            fecha=datetime(2025, 8, 8, 14, 0, 0)
        )
        
        print(f"\n3. Guardando gasto similar (diferente monto): {gasto_similar}")
        success3 = storage.guardar_gasto(gasto_similar, use_batch=False)
        print(f"   -> Resultado: {'GUARDADO (correcto)' if success3 else 'RECHAZADO (incorrecto)'}")
        
        # Verificar counts
        from datetime import date
        gastos = storage.obtener_gastos(date(2025, 8, 8), date(2025, 8, 8))
        print(f"\n4. Total gastos guardados: {len(gastos)}")
        for i, g in enumerate(gastos, 1):
            print(f"   {i}. ${g.monto} - {g.categoria} - {g.descripcion}")
        
        # Resultados
        expected_count = 2  # Original + similar (NO duplicado)
        if len(gastos) == expected_count and not success2:
            print(f"\nTEST EXITOSO: Duplicado detectado correctamente")
            return True
        else:
            print(f"\nTEST FALLO: Esperaba {expected_count} gastos, obtuvo {len(gastos)}")
            return False
            
    finally:
        # Limpiar archivo temporal
        try:
            os.unlink(db_path)
        except:
            pass

def test_hybrid_duplicate_detection():
    """Test de detección de duplicados en HybridStorage."""
    print(f"\n" + "="*60)
    print(">> Testing detección de duplicados en HybridStorage...")
    
    # Usar archivos temporales
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_excel:
        excel_path = temp_excel.name
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        db_path = temp_db.name
    
    try:
        # Crear hybrid storage
        storage = HybridStorage(excel_path, db_path)
        
        # Crear gastos de test
        gastos_test = [
            Gasto(monto=Decimal('700'), categoria='tecnologia', descripcion='laptop', 
                  fecha=datetime(2025, 8, 8, 0, 33, 0)),
            Gasto(monto=Decimal('700'), categoria='tecnologia', descripcion='laptop', 
                  fecha=datetime(2025, 8, 8, 0, 35, 0)),  # Duplicado
            Gasto(monto=Decimal('300'), categoria='servicios', descripcion='internet',
                  fecha=datetime(2025, 8, 8, 0, 33, 0)),
            Gasto(monto=Decimal('300'), categoria='servicios', descripcion='internet',
                  fecha=datetime(2025, 8, 8, 0, 40, 0)),  # Duplicado
        ]
        
        guardados = 0
        rechazados = 0
        
        for i, gasto in enumerate(gastos_test, 1):
            print(f"\n{i}. Guardando: ${gasto.monto} - {gasto.categoria}")
            success = storage.guardar_gasto(gasto)
            
            if success:
                guardados += 1
                print(f"   -> GUARDADO exitosamente")
            else:
                rechazados += 1
                print(f"   -> RECHAZADO (duplicado detectado)")
        
        print(f"\nResultados:")
        print(f"   Guardados: {guardados}")
        print(f"   Rechazados: {rechazados}")
        
        # Verificar que solo se guardaron los únicos
        expected_guardados = 2  # laptop + internet (1 de cada)
        expected_rechazados = 2  # duplicados
        
        if guardados == expected_guardados and rechazados == expected_rechazados:
            print(f"\nTEST HIBRIDO EXITOSO: Duplicados detectados correctamente")
            return True
        else:
            print(f"\nTEST HIBRIDO FALLO: Esperaba {expected_guardados} guardados y {expected_rechazados} rechazados")
            return False
            
    finally:
        # Limpiar archivos temporales
        try:
            os.unlink(excel_path)
            os.unlink(db_path)
        except:
            pass

if __name__ == "__main__":
    print("Iniciando tests de detección de duplicados...")
    
    # Test SQLite
    sqlite_success = test_duplicate_detection()
    
    # Test Hybrid
    hybrid_success = test_hybrid_duplicate_detection()
    
    print(f"\n" + "="*60)
    if sqlite_success and hybrid_success:
        print("TODOS LOS TESTS EXITOSOS!")
        print("   La deteccion de duplicados esta funcionando correctamente.")
        print("   Los gastos duplicados seran rechazados automaticamente.")
    else:
        print("ALGUNOS TESTS FALLARON")
        print("   La deteccion de duplicados necesita ajustes.")
    
    print("="*60)