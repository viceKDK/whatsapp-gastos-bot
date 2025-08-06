"""
Tests del Infrastructure Layer

Tests para implementaciones concretas de storage, WhatsApp y servicios externos.

Módulos:
- test_excel_storage.py: Tests para almacenamiento en Excel
- test_sqlite_storage.py: Tests para almacenamiento en SQLite (futuro)
- test_whatsapp_integration.py: Tests de integración con WhatsApp

Los tests de infraestructura:
- Pueden usar archivos temporales para testing
- Validan implementaciones concretas
- Incluyen tests de integración real
- Pueden ser más lentos que tests unitarios

Fixtures disponibles:
- temp_excel_file: Archivo Excel temporal para tests
- temp_sqlite_file: Base SQLite temporal para tests
- temp_directory: Directorio temporal limpio
"""

import pytest
import tempfile
from pathlib import Path
from datetime import date


@pytest.fixture
def temp_directory():
    """Directorio temporal para tests de infraestructura."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_excel_file(temp_directory):
    """Archivo Excel temporal para tests."""
    excel_path = temp_directory / "test_gastos.xlsx"
    return str(excel_path)


@pytest.fixture
def temp_sqlite_file(temp_directory):
    """Archivo SQLite temporal para tests."""
    sqlite_path = temp_directory / "test_gastos.db"
    return str(sqlite_path)


@pytest.fixture
def fecha_hoy():
    """Fecha actual para filtros de tests."""
    return date.today()


@pytest.fixture
def fecha_ayer():
    """Fecha de ayer para tests de rangos."""
    from datetime import timedelta
    return date.today() - timedelta(days=1)