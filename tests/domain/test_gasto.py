"""
Tests para la entidad Gasto

Tests unitarios para validar el comportamiento de la entidad principal Gasto.
"""

import pytest
from decimal import Decimal
from datetime import datetime

from domain.models.gasto import Gasto


class TestGasto:
    """Tests para la entidad Gasto."""
    
    def test_crear_gasto_valido(self):
        """Test crear un gasto válido."""
        fecha = datetime(2024, 1, 15, 10, 30)
        gasto = Gasto(
            monto=Decimal('150.50'),
            categoria='comida',
            fecha=fecha,
            descripcion='Almuerzo en restaurante'
        )
        
        assert gasto.monto == Decimal('150.50')
        assert gasto.categoria == 'comida'
        assert gasto.fecha == fecha
        assert gasto.descripcion == 'Almuerzo en restaurante'
        assert gasto.id is None
    
    def test_crear_gasto_sin_descripcion(self):
        """Test crear un gasto sin descripción."""
        fecha = datetime.now()
        gasto = Gasto(
            monto=Decimal('50.00'),
            categoria='transporte',
            fecha=fecha
        )
        
        assert gasto.monto == Decimal('50.00')
        assert gasto.categoria == 'transporte'
        assert gasto.descripcion is None
    
    def test_normalizar_categoria(self):
        """Test que la categoría se normaliza correctamente."""
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='  COMIDA  ',
            fecha=datetime.now()
        )
        
        assert gasto.categoria == 'comida'
    
    def test_monto_debe_ser_decimal(self):
        """Test que el monto debe ser un Decimal."""
        with pytest.raises(TypeError, match="El monto debe ser un Decimal"):
            Gasto(
                monto=100.50,  # Float en lugar de Decimal
                categoria='comida',
                fecha=datetime.now()
            )
    
    def test_monto_debe_ser_positivo(self):
        """Test que el monto debe ser positivo."""
        with pytest.raises(ValueError, match="El monto debe ser positivo"):
            Gasto(
                monto=Decimal('0.00'),
                categoria='comida',
                fecha=datetime.now()
            )
        
        with pytest.raises(ValueError, match="El monto debe ser positivo"):
            Gasto(
                monto=Decimal('-50.00'),
                categoria='comida',
                fecha=datetime.now()
            )
    
    def test_monto_maximo_dos_decimales(self):
        """Test que el monto no puede tener más de 2 decimales."""
        with pytest.raises(ValueError, match="El monto no puede tener más de 2 decimales"):
            Gasto(
                monto=Decimal('100.123'),
                categoria='comida',
                fecha=datetime.now()
            )
    
    def test_categoria_requerida(self):
        """Test que la categoría es requerida."""
        with pytest.raises(ValueError, match="La categoría es requerida"):
            Gasto(
                monto=Decimal('100.00'),
                categoria='',
                fecha=datetime.now()
            )
        
        with pytest.raises(ValueError, match="La categoría no puede estar vacía"):
            Gasto(
                monto=Decimal('100.00'),
                categoria='   ',
                fecha=datetime.now()
            )
    
    def test_categoria_debe_ser_string(self):
        """Test que la categoría debe ser un string."""
        with pytest.raises(TypeError, match="La categoría debe ser un string"):
            Gasto(
                monto=Decimal('100.00'),
                categoria=123,
                fecha=datetime.now()
            )
    
    def test_es_del_mes(self):
        """Test método es_del_mes."""
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='comida',
            fecha=datetime(2024, 3, 15, 10, 30)
        )
        
        assert gasto.es_del_mes(2024, 3) is True
        assert gasto.es_del_mes(2024, 2) is False
        assert gasto.es_del_mes(2023, 3) is False
    
    def test_es_de_categoria(self):
        """Test método es_de_categoria."""
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='comida',
            fecha=datetime.now()
        )
        
        assert gasto.es_de_categoria('comida') is True
        assert gasto.es_de_categoria('COMIDA') is True
        assert gasto.es_de_categoria('  comida  ') is True
        assert gasto.es_de_categoria('transporte') is False
    
    def test_to_dict(self):
        """Test conversión a diccionario."""
        fecha = datetime(2024, 1, 15, 10, 30, 45)
        gasto = Gasto(
            monto=Decimal('150.50'),
            categoria='comida',
            fecha=fecha,
            descripcion='Test'
        )
        gasto.id = 123
        
        expected = {
            'id': 123,
            'monto': 150.50,
            'categoria': 'comida',
            'fecha': '2024-01-15T10:30:45',
            'descripcion': 'Test'
        }
        
        assert gasto.to_dict() == expected
    
    def test_from_dict(self):
        """Test creación desde diccionario."""
        data = {
            'id': 123,
            'monto': 150.50,
            'categoria': 'comida',
            'fecha': '2024-01-15T10:30:45',
            'descripcion': 'Test'
        }
        
        gasto = Gasto.from_dict(data)
        
        assert gasto.id == 123
        assert gasto.monto == Decimal('150.50')
        assert gasto.categoria == 'comida'
        assert gasto.fecha == datetime(2024, 1, 15, 10, 30, 45)
        assert gasto.descripcion == 'Test'
    
    def test_from_dict_sin_id(self):
        """Test creación desde diccionario sin ID."""
        data = {
            'monto': 100.00,
            'categoria': 'transporte',
            'fecha': '2024-01-15T10:30:45'
        }
        
        gasto = Gasto.from_dict(data)
        
        assert gasto.id is None
        assert gasto.monto == Decimal('100.00')
        assert gasto.categoria == 'transporte'
        assert gasto.descripcion is None
    
    def test_str_representation(self):
        """Test representación string."""
        fecha = datetime(2024, 1, 15, 10, 30)
        gasto = Gasto(
            monto=Decimal('150.50'),
            categoria='comida',
            fecha=fecha
        )
        
        expected = "Gasto($150.50, comida, 2024-01-15 10:30)"
        assert str(gasto) == expected
    
    def test_repr_representation(self):
        """Test representación técnica."""
        fecha = datetime(2024, 1, 15, 10, 30, 45)
        gasto = Gasto(
            monto=Decimal('150.50'),
            categoria='comida',
            fecha=fecha,
            descripcion='Test'
        )
        
        expected = ("Gasto(monto=150.50, categoria='comida', "
                   "fecha=2024-01-15T10:30:45, descripcion='Test', id=None)")
        assert repr(gasto) == expected
    
    def test_equality_comparison(self):
        """Test comparación de igualdad."""
        fecha = datetime(2024, 1, 15, 10, 30)
        
        gasto1 = Gasto(
            monto=Decimal('150.50'),
            categoria='comida',
            fecha=fecha,
            descripcion='Test'
        )
        
        gasto2 = Gasto(
            monto=Decimal('150.50'),
            categoria='comida',
            fecha=fecha,
            descripcion='Test'
        )
        
        # Diferentes IDs no afectan la igualdad
        gasto1.id = 1
        gasto2.id = 2
        
        assert gasto1 == gasto2
    
    def test_inequality_comparison(self):
        """Test comparación de desigualdad."""
        fecha = datetime(2024, 1, 15, 10, 30)
        
        gasto1 = Gasto(
            monto=Decimal('150.50'),
            categoria='comida',
            fecha=fecha
        )
        
        gasto2 = Gasto(
            monto=Decimal('200.00'),  # Diferente monto
            categoria='comida',
            fecha=fecha
        )
        
        assert gasto1 != gasto2
        assert gasto1 != "not a gasto"  # Diferente tipo


class TestGastoEdgeCases:
    """Tests para casos edge de la entidad Gasto."""
    
    def test_gasto_con_monto_minimo(self):
        """Test gasto con monto mínimo válido."""
        gasto = Gasto(
            monto=Decimal('0.01'),
            categoria='test',
            fecha=datetime.now()
        )
        
        assert gasto.monto == Decimal('0.01')
    
    def test_gasto_con_categoria_unicode(self):
        """Test gasto con caracteres especiales en categoría."""
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='café ñandú',
            fecha=datetime.now()
        )
        
        assert gasto.categoria == 'café ñandú'
    
    def test_gasto_con_descripcion_larga(self):
        """Test gasto con descripción muy larga."""
        descripcion_larga = 'A' * 1000
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='test',
            fecha=datetime.now(),
            descripcion=descripcion_larga
        )
        
        assert len(gasto.descripcion) == 1000
    
    def test_fecha_futura(self):
        """Test gasto con fecha futura."""
        fecha_futura = datetime(2030, 12, 31, 23, 59)
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='test',
            fecha=fecha_futura
        )
        
        assert gasto.fecha == fecha_futura
    
    def test_fecha_muy_antigua(self):
        """Test gasto con fecha muy antigua."""
        fecha_antigua = datetime(1900, 1, 1, 0, 0)
        gasto = Gasto(
            monto=Decimal('100.00'),
            categoria='test',
            fecha=fecha_antigua
        )
        
        assert gasto.fecha == fecha_antigua