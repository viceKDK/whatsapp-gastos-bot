"""
Tests del Interface Layer

Tests para interfaces de usuario, CLI y controladores.

Módulos:
- test_cli_runner.py: Tests para el runner de línea de comandos
- test_bot_runner.py: Tests para el orquestador principal del bot
- test_main.py: Tests para el punto de entrada principal

Los tests de interfaz:
- Validan la interacción con el usuario
- Prueban comandos y argumentos CLI
- Verifican outputs y mensajes
- Incluyen tests de integración end-to-end

Fixtures disponibles:
- mock_settings: Configuración mock para tests
- cli_runner: Runner para simular comandos CLI
- captured_output: Captura de output para verificación
"""

import pytest
from unittest.mock import Mock, patch
from io import StringIO
import sys

from config.settings import Settings, StorageMode, LogLevel


@pytest.fixture
def mock_settings():
    """Settings mock para tests de interface."""
    settings = Mock(spec=Settings)
    settings.storage_mode = StorageMode.EXCEL
    settings.excel.excel_file_path = "test_gastos.xlsx"
    settings.whatsapp.target_chat_name = "Test Chat"
    settings.whatsapp.poll_interval_seconds = 5
    settings.whatsapp.chrome_headless = True
    settings.logging.level = LogLevel.DEBUG
    settings.debug_mode = True
    
    # Métodos mock
    settings.validate_configuration.return_value = []
    settings.ensure_directories_exist.return_value = None
    settings.get_storage_file_path.return_value = "test_gastos.xlsx"
    
    return settings


@pytest.fixture
def captured_output():
    """Captura stdout y stderr para verificar outputs."""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    
    stdout_capture = StringIO()
    stderr_capture = StringIO()
    
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture
    
    yield stdout_capture, stderr_capture
    
    sys.stdout = old_stdout
    sys.stderr = old_stderr


@pytest.fixture
def mock_bot_runner():
    """Mock del BotRunner para tests."""
    runner = Mock()
    runner.run.return_value = True
    runner.stop.return_value = None
    runner.stats = {
        'mensajes_procesados': 0,
        'gastos_registrados': 0,
        'errores': 0
    }
    return runner