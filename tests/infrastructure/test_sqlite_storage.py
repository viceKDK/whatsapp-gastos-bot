"""
Tests para SQLiteStorage

Tests unitarios para validar el storage de SQLite.
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from pathlib import Path
import tempfile
import os
import sqlite3
from unittest.mock import Mock, patch

from infrastructure.storage.sqlite_writer import SQLiteStorage
from domain.models.gasto import Gasto


class TestSQLiteStorage:
    """Tests para SQLiteStorage."""
    
    def setup_method(self):
        """Setup para cada test."""
        # Crear archivo temporal para tests
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test_gastos.db')
        self.storage = SQLiteStorage(self.test_db_path)
    
    def teardown_method(self):
        """Cleanup después de cada test."""
        # Limpiar archivos temporales
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_inicializacion_crea_database(self):
        """Test que la inicialización crea la base de datos."""
        assert os.path.exists(self.test_db_path)
        assert Path(self.test_db_path).stat().st_size > 0
    
    def test_inicializacion_crea_tablas(self):
        """Test que se crean las tablas necesarias."""
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar que existe la tabla gastos
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gastos'")
            assert cursor.fetchone() is not None
            
            # Verificar que existe la tabla metadata
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'")
            assert cursor.fetchone() is not None
            
            # Verificar que existen los índices
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_gastos_fecha'")
            assert cursor.fetchone() is not None
    
    def test_inicializacion_crea_directorio(self):
        """Test que se crean directorios padre si no existen."""
        nested_path = os.path.join(self.temp_dir, 'subdir', 'test.db')
        storage = SQLiteStorage(nested_path)
        
        assert os.path.exists(nested_path)
        assert os.path.exists(os.path.dirname(nested_path))
        
        # Cleanup
        os.remove(nested_path)
        os.rmdir(os.path.dirname(nested_path))
    
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
        assert gasto.id is not None
        assert gasto.id > 0
    
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
            assert gasto.id is not None
        
        # Los IDs deben ser diferentes
        assert gastos[0].id != gastos[1].id
    
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
        montos = [g.monto for g in gastos_obtenidos]
        assert Decimal('100.00') in montos
        assert Decimal('200.00') in montos
        assert Decimal('300.00') not in montos
    
    def test_obtener_gastos_orden_descendente(self):
        """Test que los gastos se obtienen en orden descendente por fecha."""
        # Guardar gastos con fechas diferentes
        gastos_test = [
            Gasto(
                monto=Decimal('100.00'),
                categoria='test',
                fecha=datetime(2024, 1, 15, 10, 30)
            ),
            Gasto(
                monto=Decimal('200.00'),
                categoria='test',
                fecha=datetime(2024, 1, 10, 15, 30)
            ),
            Gasto(
                monto=Decimal('300.00'),
                categoria='test',
                fecha=datetime(2024, 1, 20, 9, 30)
            )
        ]
        
        for gasto in gastos_test:
            self.storage.guardar_gasto(gasto)
        
        gastos_obtenidos = self.storage.obtener_gastos(
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        # Deben estar ordenados por fecha DESC
        assert gastos_obtenidos[0].fecha > gastos_obtenidos[1].fecha
        assert gastos_obtenidos[1].fecha > gastos_obtenidos[2].fecha
    
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
    
    def test_obtener_gasto_por_id(self):
        """Test obtener gasto específico por ID."""
        gasto_original = Gasto(
            monto=Decimal('150.50'),
            categoria='comida',
            fecha=datetime(2024, 1, 15, 10, 30),
            descripcion='Test'
        )
        
        self.storage.guardar_gasto(gasto_original)
        gasto_id = gasto_original.id
        
        gasto_obtenido = self.storage.obtener_gasto_por_id(gasto_id)
        
        assert gasto_obtenido is not None
        assert gasto_obtenido.id == gasto_id
        assert gasto_obtenido.monto == Decimal('150.50')
        assert gasto_obtenido.categoria == 'comida'
        assert gasto_obtenido.descripcion == 'Test'
    
    def test_obtener_gasto_por_id_no_existe(self):
        """Test obtener gasto por ID que no existe."""
        gasto = self.storage.obtener_gasto_por_id(999)
        assert gasto is None
    
    def test_actualizar_gasto(self):
        """Test actualizar un gasto existente."""
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='comida',
            fecha=datetime(2024, 1, 15),
            descripcion='Original'
        )
        
        self.storage.guardar_gasto(gasto)
        original_id = gasto.id
        
        # Modificar gasto
        gasto.monto = Decimal('200.00')
        gasto.categoria = 'transporte'
        gasto.descripcion = 'Actualizado'
        
        result = self.storage.actualizar_gasto(gasto)
        
        assert result is True
        
        # Verificar que se actualizó
        gasto_actualizado = self.storage.obtener_gasto_por_id(original_id)
        assert gasto_actualizado.monto == Decimal('200.00')
        assert gasto_actualizado.categoria == 'transporte'
        assert gasto_actualizado.descripcion == 'Actualizado'
    
    def test_actualizar_gasto_sin_id(self):
        """Test actualizar gasto sin ID."""
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='comida',
            fecha=datetime.now()
        )
        
        result = self.storage.actualizar_gasto(gasto)
        assert result is False
    
    def test_actualizar_gasto_no_existe(self):
        """Test actualizar gasto que no existe."""
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='comida',
            fecha=datetime.now()
        )
        gasto.id = 999  # ID que no existe
        
        result = self.storage.actualizar_gasto(gasto)
        assert result is False
    
    def test_eliminar_gasto(self):
        """Test eliminar un gasto."""
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='comida',
            fecha=datetime.now()
        )
        
        self.storage.guardar_gasto(gasto)
        gasto_id = gasto.id
        
        result = self.storage.eliminar_gasto(gasto_id)
        assert result is True
        
        # Verificar que fue eliminado
        gasto_eliminado = self.storage.obtener_gasto_por_id(gasto_id)
        assert gasto_eliminado is None
    
    def test_eliminar_gasto_no_existe(self):
        """Test eliminar gasto que no existe."""
        result = self.storage.eliminar_gasto(999)
        assert result is False
    
    def test_obtener_estadisticas(self):
        """Test obtener estadísticas."""
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
        assert stats['categorias']['comida']['cantidad'] == 2
        assert stats['categorias']['comida']['total'] == 300.0
        assert stats['categorias']['transporte']['cantidad'] == 1
        assert stats['categorias']['transporte']['total'] == 50.0
        assert stats['fecha_primer_gasto'] is not None
        assert stats['fecha_ultimo_gasto'] is not None
    
    def test_obtener_estadisticas_base_vacia(self):
        """Test estadísticas con base de datos vacía."""
        stats = self.storage.obtener_estadisticas()
        
        assert stats['total_gastos'] == 0
        assert stats['monto_total'] == 0.0
        assert stats['categorias'] == {}
        assert stats['fecha_primer_gasto'] is None
        assert stats['fecha_ultimo_gasto'] is None
    
    def test_backup_database(self):
        """Test crear backup de la base de datos."""
        # Guardar un gasto primero
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='test',
            fecha=datetime.now()
        )
        self.storage.guardar_gasto(gasto)
        
        backup_path = self.storage.backup_database()
        
        assert backup_path != ""
        assert os.path.exists(backup_path)
        assert 'backup' in backup_path
        assert backup_path.endswith('.db')
        
        # Verificar que el backup contiene los datos
        backup_storage = SQLiteStorage(backup_path)
        gastos_backup = backup_storage.obtener_gastos(date(2024, 1, 1), date(2024, 12, 31))
        assert len(gastos_backup) == 1
        
        # Limpiar backup
        os.remove(backup_path)
    
    def test_ejecutar_migrations(self):
        """Test ejecutar migraciones."""
        result = self.storage.ejecutar_migrations()
        assert result is True
    
    def test_vacuum_database(self):
        """Test optimización con VACUUM."""
        result = self.storage.vacuum_database()
        assert result is True
    
    def test_obtener_info_database(self):
        """Test obtener información de la base de datos."""
        info = self.storage.obtener_info_database()
        
        assert info['ruta'] == str(self.storage.db_path)
        assert info['exists'] is True
        assert info['size_bytes'] > 0
        assert 'gastos' in info['tablas']
        assert 'metadata' in info['tablas']
        assert info['schema_version'] == '1.0'
    
    def test_manejo_error_guardar_gasto(self):
        """Test manejo de errores al guardar gasto."""
        # Corromper la base de datos cerrándola
        os.remove(self.test_db_path)
        
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='test',
            fecha=datetime.now()
        )
        
        result = self.storage.guardar_gasto(gasto)
        assert result is False
    
    def test_manejo_error_obtener_gastos(self):
        """Test manejo de errores al obtener gastos."""
        with patch('sqlite3.connect', side_effect=Exception("DB Error")):
            gastos = self.storage.obtener_gastos(date(2024, 1, 1), date(2024, 1, 31))
            assert gastos == []


class TestSQLiteStorageEdgeCases:
    """Tests para casos edge de SQLiteStorage."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test_gastos.db')
    
    def teardown_method(self):
        """Cleanup después de cada test."""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_ruta_con_espacios(self):
        """Test con ruta que contiene espacios."""
        path_con_espacios = os.path.join(self.temp_dir, 'base con espacios.db')
        storage = SQLiteStorage(path_con_espacios)
        
        assert os.path.exists(path_con_espacios)
        
        # Verificar que funciona normalmente
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='test',
            fecha=datetime.now()
        )
        
        result = storage.guardar_gasto(gasto)
        assert result is True
        
        # Cleanup
        os.remove(path_con_espacios)
    
    def test_gasto_sin_descripcion(self):
        """Test guardar gasto sin descripción."""
        storage = SQLiteStorage(self.test_db_path)
        
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='test',
            fecha=datetime.now()
        )
        
        result = storage.guardar_gasto(gasto)
        assert result is True
        
        # Verificar que se puede recuperar
        gastos = storage.obtener_gastos(date(2024, 1, 1), date(2024, 12, 31))
        assert len(gastos) == 1
        assert gastos[0].descripcion is None
    
    def test_descripcion_con_caracteres_especiales(self):
        """Test descripción con caracteres especiales y Unicode."""
        storage = SQLiteStorage(self.test_db_path)
        
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='test',
            fecha=datetime.now(),
            descripcion='Café con ñ, acentos: áéíóú, y emojis: 🍕🚗'
        )
        
        result = storage.guardar_gasto(gasto)
        assert result is True
        
        gastos = storage.obtener_gastos(date(2024, 1, 1), date(2024, 12, 31))
        assert len(gastos) == 1
        assert 'Café' in gastos[0].descripcion
        assert '🍕' in gastos[0].descripcion
    
    def test_muchos_gastos(self):
        """Test con muchos gastos para verificar performance."""
        storage = SQLiteStorage(self.test_db_path)
        
        # Crear 1000 gastos
        for i in range(1000):
            gasto = Gasto(
                monto=Decimal(f'{(i % 500) + 1}.{i % 100:02d}'),
                categoria=f'categoria{i % 10}',  # 10 categorías diferentes
                fecha=datetime(2024, (i % 12) + 1, (i % 28) + 1, 10, 30)
            )
            result = storage.guardar_gasto(gasto)
            assert result is True
        
        # Verificar que se guardaron todos
        gastos = storage.obtener_gastos(date(2024, 1, 1), date(2024, 12, 31))
        assert len(gastos) == 1000
        
        # Verificar estadísticas
        stats = storage.obtener_estadisticas()
        assert stats['total_gastos'] == 1000
        assert len(stats['categorias']) == 10
    
    def test_concurrencia_basica(self):
        """Test básico de concurrencia con múltiples conexiones."""
        storage1 = SQLiteStorage(self.test_db_path)
        storage2 = SQLiteStorage(self.test_db_path)  # Otra instancia de la misma DB
        
        # Guardar desde una instancia
        gasto1 = Gasto(
            monto=Decimal('100.00'),
            categoria='test1',
            fecha=datetime.now()
        )
        storage1.guardar_gasto(gasto1)
        
        # Guardar desde otra instancia
        gasto2 = Gasto(
            monto=Decimal('200.00'),
            categoria='test2',
            fecha=datetime.now()
        )
        storage2.guardar_gasto(gasto2)
        
        # Ambas instancias deben ver ambos gastos
        gastos1 = storage1.obtener_gastos(date(2024, 1, 1), date(2024, 12, 31))
        gastos2 = storage2.obtener_gastos(date(2024, 1, 1), date(2024, 12, 31))
        
        assert len(gastos1) == 2
        assert len(gastos2) == 2
    
    def test_transacciones_rollback(self):
        """Test que las transacciones hacen rollback en caso de error."""
        storage = SQLiteStorage(self.test_db_path)
        
        # Guardar un gasto válido
        gasto_valido = Gasto(
            monto=Decimal('100.00'),
            categoria='valid',
            fecha=datetime.now()
        )
        storage.guardar_gasto(gasto_valido)
        
        # Verificar que hay 1 gasto
        gastos_antes = storage.obtener_gastos(date(2024, 1, 1), date(2024, 12, 31))
        assert len(gastos_antes) == 1
        
        # Intentar operación que falle (simular error en medio de transacción)
        with patch.object(storage, 'logger') as mock_logger:
            with patch('sqlite3.connect') as mock_connect:
                mock_conn = Mock()
                mock_cursor = Mock()
                mock_cursor.execute.side_effect = Exception("Simulated error")
                mock_conn.cursor.return_value = mock_cursor
                mock_connect.return_value.__enter__.return_value = mock_conn
                
                gasto_invalido = Gasto(
                    monto=Decimal('200.00'),
                    categoria='invalid',
                    fecha=datetime.now()
                )
                
                result = storage.guardar_gasto(gasto_invalido)
                assert result is False
        
        # Verificar que sigue habiendo solo 1 gasto (no se corrompió)
        gastos_despues = storage.obtener_gastos(date(2024, 1, 1), date(2024, 12, 31))
        assert len(gastos_despues) == 1
        assert gastos_despues[0].categoria == 'valid'