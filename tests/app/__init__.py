"""
Tests del Application Layer

Tests para servicios de aplicación y casos de uso.

Módulos:
- test_interpretar_mensaje.py: Tests del servicio de interpretación de mensajes
- test_registrar_gasto.py: Tests del servicio de registro de gastos
- test_procesar_mensaje.py: Tests del caso de uso principal

Los tests de aplicación:
- Pueden usar mocks para dependencias externas
- Validan la orquestación entre servicios
- Prueban la lógica de aplicación específica
- Incluyen tests de integración entre capas

Fixtures comunes disponibles:
- mock_storage_repository: Mock del repository de almacenamiento
- sample_gasto: Gasto de ejemplo para tests
- sample_messages: Mensajes de prueba
"""

import pytest
from unittest.mock import Mock
from decimal import Decimal
from datetime import datetime

from domain.models.gasto import Gasto


@pytest.fixture
def mock_storage_repository():
    """Mock del storage repository para tests de aplicación."""
    mock_repo = Mock()
    mock_repo.guardar_gasto.return_value = True
    mock_repo.obtener_gastos.return_value = []
    mock_repo.obtener_gastos_por_categoria.return_value = []
    return mock_repo


@pytest.fixture
def sample_gasto():
    """Gasto de ejemplo para tests."""
    return Gasto(
        monto=Decimal('150.50'),
        categoria='comida',
        fecha=datetime(2025, 8, 6, 14, 30, 0)
    )


@pytest.fixture
def sample_messages():
    """Mensajes de ejemplo para tests."""
    return [
        ("gasto: 500 comida", datetime(2025, 8, 6, 12, 0, 0)),
        ("150 transporte", datetime(2025, 8, 6, 13, 0, 0)),
        ("gasté 75 entretenimiento", datetime(2025, 8, 6, 14, 0, 0)),
        ("compré 200 ropa", datetime(2025, 8, 6, 15, 0, 0)),
    ]