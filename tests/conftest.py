"""
Configuración Global de Tests - pytest conftest.py

Este archivo contiene fixtures y configuraciones compartidas por todos los tests.
Se carga automáticamente por pytest en toda la suite de tests.
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock
from decimal import Decimal
from datetime import datetime, date

# Asegurar que el proyecto esté en el path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Importaciones del proyecto
from domain.models.gasto import Gasto
from config.settings import Settings, StorageMode, LogLevel


# =============================================================================
# CONFIGURACIÓN DE ENTORNO DE TEST
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configuración automática del entorno de test."""
    # Variables de entorno para tests
    os.environ['DEBUG_MODE'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    os.environ['STORAGE_MODE'] = 'excel'
    os.environ['CHROME_HEADLESS'] = 'true'
    os.environ['WHATSAPP_POLL_INTERVAL'] = '5'
    
    yield
    
    # Cleanup después de todos los tests
    test_vars = [
        'DEBUG_MODE', 'LOG_LEVEL', 'STORAGE_MODE', 
        'CHROME_HEADLESS', 'WHATSAPP_POLL_INTERVAL'
    ]
    for var in test_vars:
        os.environ.pop(var, None)


# =============================================================================
# FIXTURES DE DATOS DE TEST
# =============================================================================

@pytest.fixture
def sample_gasto():
    """Gasto de ejemplo estándar para tests."""
    return Gasto(
        monto=Decimal('150.50'),
        categoria='comida',
        fecha=datetime(2025, 8, 6, 14, 30, 0),
        descripcion='Almuerzo en restaurante'
    )


@pytest.fixture
def sample_gastos_list():
    """Lista de gastos de ejemplo para tests."""
    return [
        Gasto(
            monto=Decimal('100.00'),
            categoria='comida',
            fecha=datetime(2025, 8, 6, 12, 0, 0)
        ),
        Gasto(
            monto=Decimal('50.00'),
            categoria='transporte',
            fecha=datetime(2025, 8, 6, 13, 0, 0)
        ),
        Gasto(
            monto=Decimal('75.50'),
            categoria='entretenimiento',
            fecha=datetime(2025, 8, 6, 15, 30, 0)
        )
    ]


@pytest.fixture
def sample_messages():
    """Mensajes de WhatsApp de ejemplo para tests."""
    return [
        "gasto: 500 comida",
        "150 transporte",
        "gasté 75.50 entretenimiento",
        "compré 200 ropa",
        "pagué 1200 salud",
        "300 super",
        "45.00 cafe"
    ]


@pytest.fixture
def invalid_messages():
    """Mensajes inválidos para tests."""
    return [
        "Hola, ¿cómo estás?",  # No es gasto
        "$500 comida",          # Símbolo $ no permitido
        "quinientos comida",    # Texto en lugar de número
        "500",                  # Falta categoría
        "500 comida rapida",    # Categoría con espacios
        "-100 comida"           # Monto negativo
    ]


# =============================================================================
# FIXTURES DE CONFIGURACIÓN
# =============================================================================

@pytest.fixture
def mock_settings():
    """Settings mock completo para tests."""
    settings = Mock(spec=Settings)
    
    # Configuración básica
    settings.storage_mode = StorageMode.EXCEL
    settings.debug_mode = True
    
    # Mock de submódulos de configuración
    settings.excel = Mock()
    settings.excel.excel_file_path = "test_gastos.xlsx"
    settings.excel.auto_backup = True
    
    settings.whatsapp = Mock()
    settings.whatsapp.target_chat_name = "Test Gastos"
    settings.whatsapp.poll_interval_seconds = 5
    settings.whatsapp.chrome_headless = True
    settings.whatsapp.connection_timeout_seconds = 10
    
    settings.logging = Mock()
    settings.logging.level = LogLevel.DEBUG
    settings.logging.file_path = "test_bot.log"
    settings.logging.console_output = True
    
    settings.categorias = Mock()
    settings.categorias.categorias_validas = {
        'comida', 'transporte', 'entretenimiento', 'salud', 'test'
    }
    settings.categorias.permitir_categorias_nuevas = True
    
    # Métodos mock
    settings.validate_configuration.return_value = []
    settings.ensure_directories_exist.return_value = None
    settings.get_storage_file_path.return_value = "test_gastos.xlsx"
    
    return settings


# =============================================================================
# FIXTURES DE ARCHIVOS TEMPORALES
# =============================================================================

@pytest.fixture
def temp_directory():
    """Directorio temporal limpio para cada test."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_excel_file(temp_directory):
    """Archivo Excel temporal para tests."""
    return str(temp_directory / "test_gastos.xlsx")


@pytest.fixture
def temp_sqlite_file(temp_directory):
    """Archivo SQLite temporal para tests."""
    return str(temp_directory / "test_gastos.db")


@pytest.fixture
def temp_log_file(temp_directory):
    """Archivo de log temporal para tests."""
    return str(temp_directory / "test_bot.log")


# =============================================================================
# FIXTURES DE FECHAS
# =============================================================================

@pytest.fixture
def fecha_hoy():
    """Fecha actual para tests."""
    return date.today()


@pytest.fixture
def fecha_ayer():
    """Fecha de ayer para tests de rangos."""
    from datetime import timedelta
    return date.today() - timedelta(days=1)


@pytest.fixture
def fecha_manana():
    """Fecha de mañana para tests de rangos."""
    from datetime import timedelta
    return date.today() + timedelta(days=1)


# =============================================================================
# FIXTURES DE MOCKS PARA SERVICIOS EXTERNOS
# =============================================================================

@pytest.fixture
def mock_storage_repository():
    """Mock del storage repository."""
    mock_repo = Mock()
    mock_repo.guardar_gasto.return_value = True
    mock_repo.obtener_gastos.return_value = []
    mock_repo.obtener_gastos_por_categoria.return_value = []
    return mock_repo


@pytest.fixture
def mock_whatsapp_connector():
    """Mock del conector de WhatsApp."""
    mock_connector = Mock()
    mock_connector.connect.return_value = True
    mock_connector.disconnect.return_value = None
    mock_connector.get_new_messages.return_value = []
    return mock_connector


# =============================================================================
# CONFIGURACIÓN DE PYTEST
# =============================================================================

def pytest_configure(config):
    """Configuración de pytest."""
    # Marcadores personalizados
    config.addinivalue_line(
        "markers", "slow: marca tests como lentos"
    )
    config.addinivalue_line(
        "markers", "integration: tests de integración"
    )
    config.addinivalue_line(
        "markers", "unit: tests unitarios"
    )
    config.addinivalue_line(
        "markers", "external: tests que requieren servicios externos"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica la colección de tests automáticamente."""
    # Agregar marcador 'slow' a tests de integración
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(pytest.mark.slow)
            
        # Agregar marcador por directorio
        if "tests/domain" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "tests/infrastructure" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "tests/interface" in str(item.fspath):
            item.add_marker(pytest.mark.integration)