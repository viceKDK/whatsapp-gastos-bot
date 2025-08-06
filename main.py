#!/usr/bin/env python3
"""
Bot Gastos WhatsApp - Punto de Entrada Principal

Automatiza el registro de gastos desde mensajes de WhatsApp Web.
"""

import sys
import signal
import argparse
from pathlib import Path
from typing import Optional

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings, StorageMode
from shared.logger import get_logger
from interface.cli.run_bot import BotRunner


def setup_signal_handlers(bot_runner: Optional['BotRunner'] = None) -> None:
    """
    Configura manejadores de señales para shutdown limpio.
    
    Args:
        bot_runner: Instancia del bot para shutdown limpio
    """
    def signal_handler(signum, frame):
        logger = get_logger(__name__)
        logger.info(f"Señal {signum} recibida, cerrando aplicación...")
        
        if bot_runner:
            bot_runner.stop()
        
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Terminación


def parse_arguments() -> argparse.Namespace:
    """
    Parsea argumentos de línea de comandos.
    
    Returns:
        Argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description="Bot Personal para Registrar Gastos desde WhatsApp Web",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                    # Ejecutar con configuración por defecto
  python main.py --mode dev         # Ejecutar en modo desarrollo
  python main.py --config           # Mostrar configuración actual
  python main.py --test-storage     # Probar almacenamiento configurado
  python main.py --dashboard        # Ejecutar dashboard web
  python main.py --dashboard --port 8000  # Dashboard en puerto 8000
  
Variables de entorno importantes:
  STORAGE_MODE               # excel o sqlite
  WHATSAPP_POLL_INTERVAL    # intervalo en segundos
  TARGET_CHAT_NAME          # nombre del chat a monitorear
  LOG_LEVEL                 # DEBUG, INFO, WARNING, ERROR
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['prod', 'dev'], 
        default='prod',
        help='Modo de ejecución (default: prod)'
    )
    
    parser.add_argument(
        '--config', 
        action='store_true',
        help='Mostrar configuración actual y salir'
    )
    
    parser.add_argument(
        '--test-storage', 
        action='store_true',
        help='Probar conexión con almacenamiento y salir'
    )
    
    parser.add_argument(
        '--validate-config', 
        action='store_true',
        help='Validar configuración y salir'
    )
    
    parser.add_argument(
        '--version', 
        action='store_true',
        help='Mostrar versión y salir'
    )
    
    parser.add_argument(
        '--dashboard',
        action='store_true',
        help='Ejecutar dashboard web en lugar del bot'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Puerto para el dashboard web (default: 5000)'
    )
    
    return parser.parse_args()


def show_version() -> None:
    """Muestra información de versión."""
    try:
        from app import __version__
        version = __version__
    except ImportError:
        version = "1.0.0"
    
    print(f"Bot Gastos WhatsApp v{version}")
    print(f"Python {sys.version}")
    print(f"Ruta del proyecto: {PROJECT_ROOT}")


def show_config() -> None:
    """Muestra la configuración actual."""
    try:
        settings = get_settings()
        config_dict = settings.to_dict()
        
        print("=== CONFIGURACIÓN ACTUAL ===")
        print()
        
        # Configuración principal
        print(f"Modo de almacenamiento: {config_dict['storage_mode']}")
        print(f"Archivo de datos: {settings.get_storage_file_path()}")
        print(f"Directorio del proyecto: {config_dict['project_root']}")
        print(f"Modo debug: {config_dict['debug_mode']}")
        print()
        
        # WhatsApp
        wa_config = config_dict['whatsapp']
        print("--- WhatsApp ---")
        print(f"Chat objetivo: {wa_config['target_chat_name']}")
        print(f"Intervalo polling: {wa_config['poll_interval_seconds']}s")
        print(f"Timeout conexión: {wa_config['connection_timeout_seconds']}s")
        print(f"Chrome headless: {wa_config['chrome_headless']}")
        print()
        
        # Logging
        log_config = config_dict['logging']
        print("--- Logging ---")
        print(f"Nivel: {log_config['level']}")
        print(f"Archivo: {log_config['file_path']}")
        print(f"Consola: {log_config['console_output']}")
        print()
        
        # Categorías
        cat_config = config_dict['categorias']
        print("--- Categorías ---")
        print(f"Válidas: {', '.join(sorted(cat_config['categorias_validas']))}")
        print(f"Permitir nuevas: {cat_config['permitir_categorias_nuevas']}")
        print(f"Validación estricta: {cat_config['validacion_estricta']}")
        
    except Exception as e:
        print(f"Error mostrando configuración: {e}")
        return False
    
    return True


def test_storage() -> bool:
    """
    Prueba la conexión con el sistema de almacenamiento.
    
    Returns:
        True si la prueba fue exitosa, False si no
    """
    try:
        logger = get_logger(__name__)
        settings = get_settings()
        
        print("=== PRUEBA DE ALMACENAMIENTO ===")
        print(f"Modo: {settings.storage_mode.value}")
        print(f"Archivo: {settings.get_storage_file_path()}")
        
        if settings.storage_mode == StorageMode.EXCEL:
            from infrastructure.storage.excel_writer import ExcelStorage
            storage = ExcelStorage(settings.excel.excel_file_path)
            
            # Probar estadísticas
            stats = storage.obtener_estadisticas()
            print(f"Total gastos: {stats['total_gastos']}")
            print(f"Monto total: ${stats['monto_total']:.2f}")
            print(f"Categorías: {list(stats['categorias'].keys())}")
            
        else:
            # TODO: Implementar test para SQLite cuando esté listo
            print("Prueba SQLite no implementada aún")
            return False
        
        print("✅ Prueba de almacenamiento exitosa")
        return True
        
    except Exception as e:
        logger.error(f"Error en prueba de almacenamiento: {e}")
        print(f"❌ Error en prueba: {e}")
        return False


def validate_config() -> bool:
    """
    Valida la configuración actual.
    
    Returns:
        True si la configuración es válida, False si no
    """
    try:
        settings = get_settings()
        errors = settings.validate_configuration()
        
        print("=== VALIDACIÓN DE CONFIGURACIÓN ===")
        
        if not errors:
            print("✅ Configuración válida")
            return True
        else:
            print("❌ Errores encontrados:")
            for error in errors:
                print(f"  - {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error validando configuración: {e}")
        return False


def run_dashboard_mode(args) -> int:
    """
    Ejecuta el dashboard web.
    
    Args:
        args: Argumentos parseados
        
    Returns:
        Código de salida
    """
    try:
        logger = get_logger(__name__)
        logger.info("Iniciando dashboard web...")
        
        # Importar dashboard
        from interface.web import run_dashboard
        
        # Ejecutar dashboard
        print(f"🌐 Iniciando Dashboard Web en http://127.0.0.1:{args.port}")
        print("💡 Presiona Ctrl+C para detener")
        
        run_dashboard(host='127.0.0.1', port=args.port, debug=(args.mode == 'dev'))
        
        return 0
        
    except ImportError as e:
        print(f"❌ Error: Dependencias del dashboard no están instaladas")
        print(f"📦 Instala con: pip install flask flask-cors")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Dashboard detenido por usuario")
        return 0
    except Exception as e:
        logger.error(f"Error ejecutando dashboard: {e}")
        print(f"❌ Error: {e}")
        return 1


def main() -> int:
    """
    Función principal de la aplicación.
    
    Returns:
        Código de salida (0 = éxito, 1 = error)
    """
    try:
        # Parsear argumentos
        args = parse_arguments()
        
        # Manejar comandos especiales
        if args.version:
            show_version()
            return 0
        
        if args.config:
            return 0 if show_config() else 1
        
        if args.validate_config:
            return 0 if validate_config() else 1
        
        if args.test_storage:
            return 0 if test_storage() else 1
        
        if args.dashboard:
            return run_dashboard_mode(args)
        
        # Configurar sistema
        settings = get_settings()
        logger = get_logger(__name__)
        
        # Configurar modo debug si corresponde
        if args.mode == 'dev':
            settings.debug_mode = True
            settings.logging.level = settings.logging.level.__class__.DEBUG
            logger.info("Modo desarrollo activado")
        
        # Log inicial
        logger.info("=== Iniciando Bot Gastos WhatsApp ===")
        logger.info(f"Modo: {args.mode}")
        logger.info(f"Storage: {settings.storage_mode.value}")
        logger.info(f"Chat objetivo: {settings.whatsapp.target_chat_name}")
        
        # Validar configuración
        config_errors = settings.validate_configuration()
        if config_errors:
            logger.error("Errores de configuración encontrados:")
            for error in config_errors:
                logger.error(f"  - {error}")
            return 1
        
        # Crear y configurar el bot runner
        bot_runner = BotRunner(settings)
        
        # Configurar manejadores de señales
        setup_signal_handlers(bot_runner)
        
        # Ejecutar bot
        logger.info("Bot iniciado. Presiona Ctrl+C para detener.")
        success = bot_runner.run()
        
        if success:
            logger.info("Bot terminado exitosamente")
            return 0
        else:
            logger.error("Bot terminado con errores")
            return 1
        
    except KeyboardInterrupt:
        print("\nInterrumpido por usuario")
        return 0
    except Exception as e:
        try:
            logger = get_logger(__name__)
            logger.exception(f"Error fatal en main: {e}")
        except:
            print(f"Error fatal: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)