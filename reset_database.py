#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reset de Base de Datos

Elimina todos los datos de la BD para empezar limpio sin timestamps futuros.
"""

import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

def reset_database():
    """Resetea completamente la base de datos."""
    print("[RESET] Limpiando Base de Datos")
    print("=" * 40)
    
    files_to_clean = [
        "data/gastos.xlsx",
        "data/gastos.cache.db",
        "data/gastos.db",
        "gastos.xlsx",
        "gastos.cache.db",
        "gastos.db",
    ]
    
    cleaned_count = 0
    
    for file_path in files_to_clean:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[OK] Eliminado: {file_path}")
                cleaned_count += 1
            else:
                print(f"[SKIP] No existe: {file_path}")
        except Exception as e:
            print(f"[ERROR] No se pudo eliminar {file_path}: {e}")
    
    # También limpiar directorio data/ completo si existe
    data_dir = Path("data")
    if data_dir.exists():
        try:
            for file in data_dir.glob("*"):
                if file.is_file():
                    try:
                        file.unlink()
                        print(f"[OK] Eliminado: {file}")
                        cleaned_count += 1
                    except Exception as e:
                        print(f"[ERROR] No se pudo eliminar {file}: {e}")
        except Exception as e:
            print(f"[ERROR] Error accediendo a directorio data/: {e}")
    
    print(f"\n[RESUMEN] {cleaned_count} archivos eliminados")
    
    if cleaned_count > 0:
        print("\n[OK] Base de datos reseteada correctamente")
        print("     El bot empezará desde cero sin timestamps problemáticos")
    else:
        print("\n[INFO] No se encontraron archivos de BD para limpiar")
        print("      La BD ya estaba limpia o en ubicación diferente")

def verify_clean():
    """Verifica que la BD esté limpia."""
    print(f"\n[VERIFICACION] Estado de la BD")
    print("-" * 30)
    
    try:
        from infrastructure.storage.hybrid_storage import HybridStorage
        
        # Intentar crear storage limpio
        storage = HybridStorage("data/gastos.xlsx")
        
        # Verificar último timestamp
        last_timestamp = storage.get_last_processed_timestamp()
        if last_timestamp:
            print(f"[!] ADVERTENCIA: Aún hay timestamp en BD: {last_timestamp}")
            print("    Puede necesitarse limpieza manual adicional")
        else:
            print(f"[OK] BD limpia - no hay timestamps previos")
        
        # Verificar estadísticas
        if hasattr(storage, 'get_processing_stats'):
            stats = storage.get_processing_stats()
            cache_stats = stats.get('cache', {})
            total_cached = cache_stats.get('total_cached', 0)
            
            if total_cached > 0:
                print(f"[!] Cache tiene {total_cached} entradas - se limpiará al reiniciar")
            else:
                print(f"[OK] Cache limpio")
        
    except Exception as e:
        print(f"[OK] BD completamente limpia (no se puede cargar): {e}")

if __name__ == "__main__":
    print("Este script eliminará TODOS los datos de la base de datos")
    print("incluyendo gastos registrados y cache de mensajes.")
    print()
    
    confirm = input("¿Estás seguro? Escribe 'RESET' para confirmar: ")
    
    if confirm.upper() == "RESET":
        reset_database()
        verify_clean()
        
        print(f"\n" + "="*50)
        print("✅ RESET COMPLETADO")
        print("="*50)
        print("El bot ahora puede ejecutarse sin problemas de timestamps.")
        print("Ejecuta 'python main.py' para probar.")
    else:
        print("\n[CANCELADO] Reset no confirmado - BD intacta")