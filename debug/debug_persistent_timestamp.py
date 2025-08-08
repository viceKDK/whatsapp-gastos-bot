#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Timestamp Persistente

Rastrea de dónde viene el timestamp 22:37:00 que no se elimina.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

def check_all_files():
    """Busca archivos que puedan contener el timestamp persistente."""
    print("[DEBUG] Buscando archivos con timestamps")
    print("=" * 50)
    
    # Patrones de archivos que pueden contener datos
    search_patterns = [
        "*.xlsx", "*.xls", "*.csv",
        "*.db", "*.sqlite", "*.sqlite3",
        "*.json", "*.pkl", "*.cache",
        "*.log", "*.txt"
    ]
    
    root_dir = Path(".")
    found_files = []
    
    for pattern in search_patterns:
        for file_path in root_dir.rglob(pattern):
            if file_path.is_file():
                found_files.append(file_path)
    
    print(f"Archivos encontrados que pueden contener datos:")
    for i, file_path in enumerate(found_files, 1):
        size = file_path.stat().st_size if file_path.exists() else 0
        modified = datetime.fromtimestamp(file_path.stat().st_mtime) if file_path.exists() else "N/A"
        print(f"  {i}. {file_path} ({size} bytes, modificado: {modified})")
        
        # Verificar si contiene '22:37' en archivos pequeños de texto
        if file_path.suffix in ['.txt', '.log', '.json', '.csv'] and size < 1024*1024:  # < 1MB
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if '22:37' in content or '22.37' in content:
                    print(f"    [!] CONTIENE 22:37: {file_path}")
            except:
                pass
    
    return found_files

def test_storage_creation():
    """Prueba crear storage desde cero y ver qué timestamp devuelve."""
    print(f"\n[DEBUG] Creación de Storage desde Cero")
    print("=" * 50)
    
    try:
        from infrastructure.storage.hybrid_storage import HybridStorage
        
        print("1. Creando HybridStorage...")
        storage = HybridStorage("data/gastos_test.xlsx")
        
        print("2. Consultando último timestamp...")
        last_timestamp = storage.get_last_processed_timestamp()
        
        if last_timestamp:
            print(f"[!] PROBLEMA: Storage devuelve timestamp: {last_timestamp}")
            print(f"    Esto significa que hay datos persistentes en algún lado")
        else:
            print(f"[OK] Storage está limpio (no devuelve timestamp)")
        
        # Verificar estadísticas
        if hasattr(storage, 'get_processing_stats'):
            stats = storage.get_processing_stats()
            print(f"3. Estadísticas: {stats}")
        
        return last_timestamp
        
    except Exception as e:
        print(f"[ERROR] No se pudo crear storage: {e}")
        return None

def check_environment():
    """Verifica el entorno y variables que puedan afectar.""" 
    print(f"\n[DEBUG] Verificación de Entorno")
    print("=" * 50)
    
    # Verificar directorio de trabajo
    cwd = os.getcwd()
    print(f"Directorio actual: {cwd}")
    
    # Verificar archivos ocultos
    hidden_files = []
    for item in os.listdir('.'):
        if item.startswith('.') and os.path.isfile(item):
            hidden_files.append(item)
    
    if hidden_files:
        print(f"Archivos ocultos: {hidden_files}")
    
    # Verificar variables de entorno relacionadas
    db_vars = {k: v for k, v in os.environ.items() if 'db' in k.lower() or 'database' in k.lower() or 'storage' in k.lower()}
    if db_vars:
        print(f"Variables de BD: {db_vars}")

def manual_timestamp_search():
    """Busca manualmente el timestamp en código fuente."""
    print(f"\n[DEBUG] Búsqueda Manual de 22:37")
    print("=" * 50)
    
    search_dirs = ['infrastructure', 'app', 'config', '.']
    suspicious_files = []
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if '22:37' in content or '22.37' in content:
                                    suspicious_files.append(file_path)
                                    print(f"[FOUND] {file_path}")
                        except:
                            pass
    
    return suspicious_files

if __name__ == "__main__":
    print("Investigando de dónde viene el timestamp persistente 22:37:00\n")
    
    # 1. Buscar todos los archivos
    files = check_all_files()
    
    # 2. Probar creación de storage
    persistent_timestamp = test_storage_creation() 
    
    # 3. Verificar entorno
    check_environment()
    
    # 4. Búsqueda manual en código
    suspicious_files = manual_timestamp_search()
    
    print(f"\n" + "="*50)
    print("RESUMEN DEL DIAGNÓSTICO")
    print("="*50)
    
    if persistent_timestamp:
        print(f"[PROBLEMA] Timestamp persistente detectado: {persistent_timestamp}")
        print("Posibles causas:")
        print("- Cache de SQLite no eliminado correctamente")
        print("- Datos hardcodeados en el código")
        print("- Archivos de configuración con datos viejos")
    else:
        print(f"[OK] No se detectó timestamp persistente en storage")
    
    if suspicious_files:
        print(f"\nArchivos con '22:37' encontrados:")
        for file in suspicious_files:
            print(f"  - {file}")
    else:
        print(f"\n[OK] No se encontró '22:37' en código fuente")