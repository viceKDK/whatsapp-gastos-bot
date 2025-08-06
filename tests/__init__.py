"""
Test Suite - Bot Gastos WhatsApp

Conjunto completo de tests para validar funcionalidad del bot.

Estructura de Tests:
- domain/: Tests para entidades y objetos de valor
- app/: Tests para servicios y casos de uso  
- infrastructure/: Tests para storage y integraciones externas
- interface/: Tests para CLI y interfaces de usuario

Uso:
    pytest                    # Ejecutar todos los tests
    pytest tests/domain/      # Tests del dominio únicamente
    pytest tests/app/         # Tests de aplicación únicamente
    pytest -v                 # Verbose output
    pytest --cov             # Con coverage
"""

# Configuración común para tests
import os
import sys
from pathlib import Path

# Asegurar que el proyecto esté en el path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configurar entorno de test
os.environ.setdefault('DEBUG_MODE', 'true')
os.environ.setdefault('LOG_LEVEL', 'DEBUG')
os.environ.setdefault('STORAGE_MODE', 'excel')  # Para tests usar Excel por simplicidad