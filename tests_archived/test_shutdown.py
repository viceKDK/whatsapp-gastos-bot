#!/usr/bin/env python3
"""
Test de shutdown rápido
"""

import sys
import signal
import time
from pathlib import Path

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings
from interface.cli.run_bot import BotRunner

def test_nuclear_shutdown():
    """Prueba el shutdown nuclear."""
    print("🧪 INICIANDO TEST DE SHUTDOWN NUCLEAR...")
    
    # Crear bot runner
    settings = get_settings()
    bot_runner = BotRunner(settings)
    
    # Configurar signal handler
    def signal_handler(signum, frame):
        print(f"\n💥 SIGNAL {signum} RECIBIDO - INICIANDO SHUTDOWN NUCLEAR...")
        start_time = time.time()
        
        bot_runner.stop()
        
        end_time = time.time()
        duration = end_time - start_time
        print(f"⚡ SHUTDOWN COMPLETADO EN {duration:.2f} SEGUNDOS")
        
        if duration < 2.0:
            print("✅ SHUTDOWN NUCLEAR EXITOSO - Menos de 2 segundos")
        else:
            print("❌ SHUTDOWN LENTO - Más de 2 segundos")
        
        import os
        os._exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("📊 Test configurado")
    print("💡 Presiona Ctrl+C para probar shutdown nuclear")
    print("⏱️ Target: < 2 segundos")
    
    # Loop infinito esperando la señal
    try:
        while True:
            time.sleep(1)
            print(".", end="", flush=True)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    test_nuclear_shutdown()