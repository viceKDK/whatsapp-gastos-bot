"""
Ejecutor del Dashboard Web

Script para lanzar fácilmente el dashboard web interactivo.
"""

import sys
import argparse
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from interface.web import run_dashboard
from shared.logger import get_logger


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Dashboard Web Bot Gastos')
    parser.add_argument('--host', default='127.0.0.1', 
                       help='Host para el servidor (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Puerto para el servidor (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                       help='Ejecutar en modo debug')
    parser.add_argument('--public', action='store_true',
                       help='Permitir conexiones externas (equivale a --host 0.0.0.0)')
    
    args = parser.parse_args()
    
    logger = get_logger(__name__)
    
    # Configurar host
    host = args.host
    if args.public:
        host = '0.0.0.0'
        logger.warning("Dashboard configurado para conexiones públicas. "
                      "Asegúrate de que sea seguro en tu red.")
    
    # Mostrar información de inicio
    print("🚀 Iniciando Dashboard Web Bot Gastos")
    print("=" * 40)
    print(f"🌐 URL: http://{host}:{args.port}")
    print(f"🔧 Debug: {'Habilitado' if args.debug else 'Deshabilitado'}")
    print(f"🔒 Acceso: {'Público' if args.public else 'Solo local'}")
    print("=" * 40)
    print("💡 Presiona Ctrl+C para detener el servidor")
    print()
    
    try:
        # Verificar dependencias
        try:
            import flask
            import flask_cors
        except ImportError as e:
            print(f"❌ Error: Dependencia faltante: {e}")
            print("📦 Instala las dependencias con:")
            print("   pip install flask flask-cors")
            return 1
        
        # Ejecutar dashboard
        run_dashboard(host=host, port=args.port, debug=args.debug)
        
    except KeyboardInterrupt:
        print("\n👋 Dashboard detenido por el usuario")
        return 0
    except Exception as e:
        logger.error(f"Error ejecutando dashboard: {e}")
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())