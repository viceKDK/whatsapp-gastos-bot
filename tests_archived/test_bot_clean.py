#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Bot Limpio

Simula el inicio del bot para ver si aparece el timestamp problemático.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

def test_bot_startup():
    """Simula el inicio del bot para probar timestamps."""
    print("[TEST] Simulación Inicio Bot")
    print("=" * 40)
    
    try:
        # Simular el flujo del run_bot.py
        from interface.cli.run_bot import BotRunner
        from config.settings import get_settings
        
        print("1. Cargando configuración...")
        settings = get_settings()
        
        print("2. Creando BotRunner...")
        bot = BotRunner(settings)
        
        print("3. Inicializando storage...")
        success = bot._initialize_components()
        
        if success:
            print("[OK] Componentes inicializados correctamente")
            
            # Verificar el timestamp que devuelve el storage
            if hasattr(bot.storage_repository, 'get_last_processed_timestamp'):
                last_timestamp = bot.storage_repository.get_last_processed_timestamp()
                
                if last_timestamp is None:
                    print("[OK] get_last_processed_timestamp() devuelve None")
                    print("     No hay timestamp problemático!")
                    return True
                else:
                    print(f"[PROBLEMA] Timestamp persistente detectado: {last_timestamp}")
                    return False
            else:
                print("[INFO] Storage no tiene método get_last_processed_timestamp")
                return True
        else:
            print("[ERROR] No se pudieron inicializar componentes")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error en simulación: {e}")
        return False

if __name__ == "__main__":
    success = test_bot_startup()
    
    print(f"\n{'='*40}")
    if success:
        print("[OK] Bot puede iniciarse sin timestamp problematico")
        print("     Listo para ejecutar 'python main.py'")
    else:
        print("[X] Todavia hay problemas de timestamp")
        print("     Revisar logs para mas detalles")