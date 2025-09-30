#!/usr/bin/env python3
"""
Bot Gastos WhatsApp - Versión Optimizada para Bajo Consumo de RAM
Ejecuta Chrome en modo headless con configuración mínima de memoria.
"""

import sys
import signal
import argparse
import gc
from pathlib import Path
from typing import Optional

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings, StorageMode
from shared.logger import get_logger
from interface.cli.run_bot import BotRunner


def optimize_memory():
    """Optimizaciones de memoria para Python."""
    # Forzar recolección de basura
    gc.collect()
    # Configurar GC más agresivo
    gc.set_threshold(700, 10, 10)


def setup_optimized_signal_handlers(bot_runner: Optional['BotRunner'] = None) -> None:
    """Manejadores de señales optimizados para shutdown rápido."""
    def signal_handler(signum, frame):
        print("\n💀 CTRL+C DETECTADO - SHUTDOWN OPTIMIZADO...")
        
        # Matar Chrome inmediatamente
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                for process in ['chrome.exe', 'chromedriver.exe']:
                    subprocess.run(['taskkill', '/F', '/IM', process, '/T'], 
                                 capture_output=True, timeout=1)
        except:
            pass
        
        # Stop bot rápido
        if bot_runner:
            try:
                bot_runner.stop()
            except:
                pass
        
        # Limpieza de memoria y exit
        optimize_memory()
        print("✅ SHUTDOWN COMPLETO")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Punto de entrada optimizado."""
    parser = argparse.ArgumentParser(description="Bot Gastos WhatsApp - Optimizado")
    parser.add_argument("--headless", action="store_true", 
                       help="Forzar modo headless (menos RAM)")
    parser.add_argument("--minimal", action="store_true",
                       help="Configuración mínima de memoria")
    
    args = parser.parse_args()
    
    # Configuración optimizada
    settings = get_settings()
    
    # Forzar configuraciones de bajo consumo
    if args.headless or args.minimal:
        # Configurar para headless y mínimo consumo
        settings.chrome_headless = True
        settings.storage_mode = StorageMode.SQLITE  # Menos RAM que híbrido
        
        # Configuraciones adicionales de bajo consumo
        if hasattr(settings, 'selenium_timeout'):
            settings.selenium_timeout = 5  # Timeouts más cortos
        
        print("🔧 MODO OPTIMIZADO ACTIVADO:")
        print("   ✅ Chrome Headless")
        print("   ✅ Storage SQLite (menos RAM)")
        print("   ✅ Timeouts reducidos")
        print("   ✅ Recolección de basura agresiva")
    
    # Optimizaciones iniciales de memoria
    optimize_memory()
    
    logger = get_logger(__name__)
    logger.info("🚀 INICIANDO BOT GASTOS - VERSIÓN OPTIMIZADA")
    logger.info(f"💾 Storage mode: {settings.storage_mode}")
    logger.info(f"🌐 Chrome headless: {settings.chrome_headless}")
    
    # Crear y configurar el bot runner
    bot_runner = BotRunner(settings=settings)
    
    # Configurar manejadores de señales optimizados
    setup_optimized_signal_handlers(bot_runner)
    
    try:
        print("\n" + "="*50)
        print("🤖 BOT GASTOS - MODO OPTIMIZADO")
        print("="*50)
        print("💡 Presiona Ctrl+C para detener")
        print("📊 Logs en logs/bot.log")
        print("🔋 Ejecutándose con configuración de bajo consumo")
        print("="*50 + "\n")
        
        # Ejecutar el bot
        bot_runner.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupción manual detectada")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        raise
    finally:
        # Limpieza final
        try:
            bot_runner.stop()
        except:
            pass
        optimize_memory()
        logger.info("✅ Bot terminado correctamente")


if __name__ == "__main__":
    main()