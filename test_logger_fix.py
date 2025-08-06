#!/usr/bin/env python3
"""
Script para probar la corrección del logger
"""

import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    print("🧪 Probando logger corregido...")
    
    # Importar y usar el logger
    from shared.logger import get_logger
    
    logger = get_logger("test")
    
    print("✅ Logger importado correctamente")
    
    # Probar diferentes niveles
    logger.debug("Test DEBUG")
    logger.info("Test INFO")  
    logger.warning("Test WARNING")
    logger.error("Test ERROR")
    
    print("✅ Logger funcionando correctamente")
    print("✅ Problema solucionado!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("❌ El problema persiste")
    sys.exit(1)