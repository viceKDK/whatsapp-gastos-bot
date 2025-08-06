"""
Tests para ExcelStorage

Tests unitarios para validar el storage de Excel.
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from pathlib import Path
import tempfile
import os
from unittest.mock import Mock, patch

from infrastructure.storage.excel_writer import ExcelStorage
from domain.models.gasto import Gasto


class TestExcelStorage:
    """Tests para ExcelStorage."""
    
    def setup_method(self):
        """Setup para cada test."""
        # Crear archivo temporal para tests
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, 'test_gastos.xlsx')
        self.storage = ExcelStorage(self.test_file_path)
    
    def teardown_method(self):
        """Cleanup después de cada test."""
        # Limpiar archivos temporales
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)
        os.rmdir(self.temp_dir)
    
    def test_inicializacion_crea_archivo(self):
        """Test que la inicialización crea el archivo Excel."""
        assert os.path.exists(self.test_file_path)
        assert Path(self.test_file_path).stat().st_size > 0
    
    def test_inicializacion_crea_directorio(self):
        """Test que se crean directorios padre si no existen."""
        nested_path = os.path.join(self.temp_dir, 'subdir', 'test.xlsx')
        storage = ExcelStorage(nested_path)
        
        assert os.path.exists(nested_path)
        assert os.path.exists(os.path.dirname(nested_path))
    
    def test_guardar_gasto_exitoso(self):
        """Test guardar un gasto exitosamente."""
        gasto = Gasto(
            monto=Decimal('150.50'),
            categoria='comida',
            fecha=datetime(2024, 1, 15, 10, 30),
            descripcion='Almuerzo'
        )
        
        result = self.storage.guardar_gasto(gasto)
        
        assert result is True
        assert gasto.id == 1  # Primera fila de datos después del header
    
    def test_guardar_multiple_gastos(self):
        """Test guardar múltiples gastos."""
        gastos = [
            Gasto(
                monto=Decimal('100.00'),
                categoria='comida',
                fecha=datetime(2024, 1, 15, 10, 30)
            ),
            Gasto(
                monto=Decimal('50.75'),
                categoria='transporte',
                fecha=datetime(2024, 1, 15, 11, 30)
            )
        ]
        
        for gasto in gastos:
            result = self.storage.guardar_gasto(gasto)
            assert result is True
        
        assert gastos[0].id == 1
        assert gastos[1].id == 2
    
    def test_obtener_gastos_rango_fechas(self):
        """Test obtener gastos en un rango de fechas."""
        # Guardar gastos de prueba
        gastos_test = [
            Gasto(
                monto=Decimal('100.00'),
                categoria='comida',
                fecha=datetime(2024, 1, 15, 10, 30)
            ),
            Gasto(
                monto=Decimal('200.00'),
                categoria='transporte',
                fecha=datetime(2024, 1, 20, 15, 30)
            ),
            Gasto(
                monto=Decimal('300.00'),
                categoria='servicios',
                fecha=datetime(2024, 2, 5, 9, 30)
            )
        ]
        
        for gasto in gastos_test:
            self.storage.guardar_gasto(gasto)
        
        # Obtener gastos de enero 2024
        gastos_obtenidos = self.storage.obtener_gastos(
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        assert len(gastos_obtenidos) == 2
        assert gastos_obtenidos[0].monto in [Decimal('100.00'), Decimal('200.00')]
        assert gastos_obtenidos[1].monto in [Decimal('100.00'), Decimal('200.00')]
    
    def test_obtener_gastos_archivo_no_existe(self):
        """Test obtener gastos cuando el archivo no existe."""
        # Crear storage con archivo que no existe
        nonexistent_path = os.path.join(self.temp_dir, 'nonexistent.xlsx')
        storage = ExcelStorage(nonexistent_path)
        os.remove(nonexistent_path)  # Eliminar el archivo creado
        
        gastos = storage.obtener_gastos(date(2024, 1, 1), date(2024, 1, 31))
        
        assert gastos == []
    
    def test_obtener_gastos_por_categoria(self):
        """Test obtener gastos por categoría."""
        # Guardar gastos de diferentes categorías
        gastos_test = [
            Gasto(
                monto=Decimal('100.00'),
                categoria='comida',
                fecha=datetime(2024, 1, 15)
            ),
            Gasto(
                monto=Decimal('150.00'),
                categoria='comida',
                fecha=datetime(2024, 1, 16)
            ),
            Gasto(
                monto=Decimal('50.00'),
                categoria='transporte',
                fecha=datetime(2024, 1, 17)
            )
        ]
        
        for gasto in gastos_test:
            self.storage.guardar_gasto(gasto)
        
        # Obtener solo gastos de comida
        gastos_comida = self.storage.obtener_gastos_por_categoria('comida')
        
        assert len(gastos_comida) == 2
        for gasto in gastos_comida:
            assert gasto.categoria == 'comida'
    
    def test_obtener_gastos_por_categoria_case_insensitive(self):
        """Test que obtener por categoría es case insensitive."""
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='comida',
            fecha=datetime(2024, 1, 15)
        )
        self.storage.guardar_gasto(gasto)
        
        gastos = self.storage.obtener_gastos_por_categoria('COMIDA')
        
        assert len(gastos) == 1
        assert gastos[0].categoria == 'comida'
    
    def test_backup_archivo(self):
        """Test crear backup del archivo."""
        # Guardar un gasto primero
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='test',
            fecha=datetime.now()
        )
        self.storage.guardar_gasto(gasto)
        
        backup_path = self.storage.backup_archivo()
        
        assert backup_path != ""
        assert os.path.exists(backup_path)
        assert 'backup' in backup_path
        
        # Limpiar backup
        if os.path.exists(backup_path):
            os.remove(backup_path)
    
    def test_backup_archivo_no_existe(self):
        """Test backup cuando el archivo no existe."""
        # Eliminar el archivo
        os.remove(self.test_file_path)
        
        backup_path = self.storage.backup_archivo()
        
        assert backup_path == ""
    
    def test_obtener_estadisticas(self):
        """Test obtener estadísticas del archivo."""
        # Guardar gastos de prueba
        gastos_test = [
            Gasto(
                monto=Decimal('100.00'),
                categoria='comida',
                fecha=datetime(2024, 1, 15, 10, 30)
            ),
            Gasto(
                monto=Decimal('200.00'),
                categoria='comida',
                fecha=datetime(2024, 1, 16, 11, 30)
            ),
            Gasto(
                monto=Decimal('50.00'),
                categoria='transporte',
                fecha=datetime(2024, 1, 17, 12, 30)
            )
        ]
        
        for gasto in gastos_test:
            self.storage.guardar_gasto(gasto)
        
        stats = self.storage.obtener_estadisticas()
        
        assert stats['total_gastos'] == 3
        assert stats['monto_total'] == 350.0
        assert 'comida' in stats['categorias']
        assert 'transporte' in stats['categorias']
        assert stats['categorias']['comida'] == 2
        assert stats['categorias']['transporte'] == 1
        assert 'fecha_primer_gasto' in stats
        assert 'fecha_ultimo_gasto' in stats
    
    def test_obtener_estadisticas_archivo_vacio(self):
        """Test estadísticas con archivo vacío."""
        stats = self.storage.obtener_estadisticas()
        
        assert stats['total_gastos'] == 0
        assert stats['monto_total'] == 0
        assert stats['categorias'] == []
    
    def test_manejo_error_guardar_gasto(self):
        """Test manejo de errores al guardar gasto."""
        # Mock para simular error
        with patch('infrastructure.storage.excel_writer.load_workbook', side_effect=Exception("Test error")):
            gasto = Gasto(
                monto=Decimal('100.00'),
                categoria='test',
                fecha=datetime.now()
            )
            
            result = self.storage.guardar_gasto(gasto)
            
            assert result is False
    
    def test_manejo_error_obtener_gastos(self):
        """Test manejo de errores al obtener gastos."""
        with patch('infrastructure.storage.excel_writer.load_workbook', side_effect=Exception("Test error")):
            gastos = self.storage.obtener_gastos(date(2024, 1, 1), date(2024, 1, 31))
            
            assert gastos == []
    
    def test_parseo_fecha_string(self):
        """Test que se pueden parsear fechas en formato string."""
        # Este test simula datos que podrían venir de Excel en diferentes formatos
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='test',
            fecha=datetime(2024, 1, 15, 10, 30)
        )
        self.storage.guardar_gasto(gasto)
        
        gastos = self.storage.obtener_gastos(date(2024, 1, 1), date(2024, 1, 31))
        
        assert len(gastos) == 1
        assert gastos[0].fecha.date() == date(2024, 1, 15)
    
    def test_aplicar_formato_fila(self):
        """Test que se aplica formato a las filas."""
        # Este test es más bien de integración, verificamos que no hay errores
        gasto = Gasto(
            monto=Decimal('1500.50'),
            categoria='test',
            fecha=datetime.now()
        )
        
        result = self.storage.guardar_gasto(gasto)
        assert result is True
        
        # Verificar que el archivo se puede leer de vuelta
        gastos = self.storage.obtener_gastos(date(2024, 1, 1), date(2024, 12, 31))
        assert len(gastos) >= 1


class TestExcelStorageEdgeCases:
    """Tests para casos edge de ExcelStorage."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, 'test_gastos.xlsx')
    
    def teardown_method(self):
        """Cleanup después de cada test."""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_ruta_con_espacios(self):
        """Test con ruta que contiene espacios."""
        path_con_espacios = os.path.join(self.temp_dir, 'archivo con espacios.xlsx')
        storage = ExcelStorage(path_con_espacios)
        
        assert os.path.exists(path_con_espacios)
        
        # Cleanup
        os.remove(path_con_espacios)
    
    def test_gasto_sin_descripcion(self):
        """Test guardar gasto sin descripción."""
        storage = ExcelStorage(self.test_file_path)
        
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='test',
            fecha=datetime.now()
        )
        
        result = storage.guardar_gasto(gasto)
        assert result is True
    
    def test_descripcion_con_caracteres_especiales(self):
        """Test descripción con caracteres especiales."""
        storage = ExcelStorage(self.test_file_path)
        
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='test',
            fecha=datetime.now(),
            descripcion='Café con ñ y acentos: áéíóú'
        )
        
        result = storage.guardar_gasto(gasto)
        assert result is True
        
        gastos = storage.obtener_gastos(date(2024, 1, 1), date(2024, 12, 31))
        assert len(gastos) == 1
        assert 'Café' in gastos[0].descripcion
    
    def test_monto_muy_grande(self):
        """Test con monto muy grande."""
        storage = ExcelStorage(self.test_file_path)
        
        gasto = Gasto(
            monto=Decimal('999999.99'),
            categoria='test',
            fecha=datetime.now()
        )
        
        result = storage.guardar_gasto(gasto)
        assert result is True
        
        gastos = storage.obtener_gastos(date(2024, 1, 1), date(2024, 12, 31))
        assert gastos[0].monto == Decimal('999999.99')
    
    def test_muchos_gastos(self):
        """Test con muchos gastos para verificar performance."""
        storage = ExcelStorage(self.test_file_path)
        
        # Crear 100 gastos
        for i in range(100):
            gasto = Gasto(
                monto=Decimal(f'{i + 1}.00'),
                categoria=f'categoria{i % 5}',  # 5 categorías diferentes
                fecha=datetime(2024, 1, i % 28 + 1, 10, 30)  # Distribuir en enero
            )
            result = storage.guardar_gasto(gasto)
            assert result is True
        
        # Verificar que se guardaron todos
        gastos = storage.obtener_gastos(date(2024, 1, 1), date(2024, 1, 31))
        assert len(gastos) == 100
        
        # Verificar estadísticas
        stats = storage.obtener_estadisticas()
        assert stats['total_gastos'] == 100