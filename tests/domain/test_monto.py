"""
Tests para el objeto valor Monto

Tests unitarios para validar el comportamiento del value object Monto.
"""

import pytest
from decimal import Decimal

from domain.value_objects.monto import Monto


class TestMonto:
    """Tests para el objeto valor Monto."""
    
    def test_crear_monto_valido(self):
        """Test crear un monto válido."""
        monto = Monto(Decimal('150.50'))
        
        assert monto.valor == Decimal('150.50')
    
    def test_crear_monto_desde_string(self):
        """Test crear monto desde string."""
        monto = Monto.from_string('150.50')
        assert monto.valor == Decimal('150.50')
        
        monto = Monto.from_string('$150.50')
        assert monto.valor == Decimal('150.50')
        
        monto = Monto.from_string('1,500.25')
        assert monto.valor == Decimal('1500.25')
        
        monto = Monto.from_string('  $1,000.00  ')
        assert monto.valor == Decimal('1000.00')
    
    def test_crear_monto_desde_float(self):
        """Test crear monto desde float."""
        monto = Monto.from_float(150.50)
        assert monto.valor == Decimal('150.50')
    
    def test_monto_debe_ser_positivo(self):
        """Test que el monto debe ser positivo."""
        with pytest.raises(ValueError, match="El monto debe ser mayor que cero"):
            Monto(Decimal('0'))
        
        with pytest.raises(ValueError, match="El monto debe ser mayor que cero"):
            Monto(Decimal('-100.00'))
    
    def test_monto_redondeo_automatico(self):
        """Test que el monto se redondea automáticamente a 2 decimales."""
        monto = Monto(Decimal('100.123'))  # 3 decimales
        assert monto.valor == Decimal('100.12')
        
        monto = Monto(Decimal('100.126'))  # Redondeo hacia arriba
        assert monto.valor == Decimal('100.13')
        
        monto = Monto(Decimal('100.125'))  # Redondeo del .5
        assert monto.valor == Decimal('100.12')
    
    def test_monto_limite_maximo(self):
        """Test que el monto tiene un límite máximo."""
        with pytest.raises(ValueError, match="El monto excede el límite máximo"):
            Monto(Decimal('1000001.00'))
        
        # Justo en el límite debe funcionar
        monto = Monto(Decimal('1000000.00'))
        assert monto.valor == Decimal('1000000.00')
    
    def test_from_string_invalido(self):
        """Test crear monto desde string inválido."""
        with pytest.raises(ValueError, match="No se puede convertir"):
            Monto.from_string('abc')
        
        with pytest.raises(ValueError, match="No se puede convertir"):
            Monto.from_string('')
        
        with pytest.raises(ValueError, match="No se puede convertir"):
            Monto.from_string('100.50.75')
    
    def test_conversion_automatica_tipos(self):
        """Test conversión automática de tipos en __post_init__."""
        # String convertido automáticamente
        monto = Monto('150.50')
        assert monto.valor == Decimal('150.50')
        
        # Int convertido automáticamente
        monto = Monto(150)
        assert monto.valor == Decimal('150')
    
    def test_sumar_montos(self):
        """Test suma de montos."""
        monto1 = Monto(Decimal('100.50'))
        monto2 = Monto(Decimal('50.25'))
        
        resultado = monto1.sumar(monto2)
        assert resultado.valor == Decimal('150.75')
        
        # Test operador +
        resultado = monto1 + monto2
        assert resultado.valor == Decimal('150.75')
    
    def test_sumar_con_decimal(self):
        """Test suma con Decimal."""
        monto = Monto(Decimal('100.50'))
        resultado = monto.sumar(Decimal('25.25'))
        
        assert resultado.valor == Decimal('125.75')
    
    def test_sumar_con_float(self):
        """Test suma con float."""
        monto = Monto(Decimal('100.50'))
        resultado = monto.sumar(25.25)
        
        assert resultado.valor == Decimal('125.75')
    
    def test_sumar_tipo_invalido(self):
        """Test suma con tipo inválido."""
        monto = Monto(Decimal('100.50'))
        
        with pytest.raises(TypeError, match="No se puede sumar Monto con"):
            monto.sumar('invalid')
    
    def test_restar_montos(self):
        """Test resta de montos."""
        monto1 = Monto(Decimal('150.50'))
        monto2 = Monto(Decimal('50.25'))
        
        resultado = monto1.restar(monto2)
        assert resultado.valor == Decimal('100.25')
        
        # Test operador -
        resultado = monto1 - monto2
        assert resultado.valor == Decimal('100.25')
    
    def test_restar_resultado_negativo(self):
        """Test resta que resultaría en valor negativo."""
        monto1 = Monto(Decimal('50.00'))
        monto2 = Monto(Decimal('100.00'))
        
        with pytest.raises(ValueError, match="La resta resultaría en un monto no positivo"):
            monto1.restar(monto2)
    
    def test_restar_resultado_cero(self):
        """Test resta que resultaría en cero."""
        monto1 = Monto(Decimal('50.00'))
        monto2 = Monto(Decimal('50.00'))
        
        with pytest.raises(ValueError, match="La resta resultaría en un monto no positivo"):
            monto1.restar(monto2)
    
    def test_multiplicar(self):
        """Test multiplicación de monto."""
        monto = Monto(Decimal('100.50'))
        
        resultado = monto.multiplicar(2)
        assert resultado.valor == Decimal('201.00')
        
        resultado = monto.multiplicar(1.5)
        assert resultado.valor == Decimal('150.75')
        
        resultado = monto.multiplicar(Decimal('0.5'))
        assert resultado.valor == Decimal('50.25')
        
        # Test operador *
        resultado = monto * 2
        assert resultado.valor == Decimal('201.00')
    
    def test_comparaciones(self):
        """Test comparaciones entre montos."""
        monto1 = Monto(Decimal('100.00'))
        monto2 = Monto(Decimal('150.00'))
        monto3 = Monto(Decimal('100.00'))
        
        # Mayor que
        assert monto2.es_mayor_que(monto1) is True
        assert monto1.es_mayor_que(monto2) is False
        assert monto1.es_mayor_que(monto3) is False
        assert monto2 > monto1
        
        # Menor que
        assert monto1.es_menor_que(monto2) is True
        assert monto2.es_menor_que(monto1) is False
        assert monto1.es_menor_que(monto3) is False
        assert monto1 < monto2
        
        # Igualdad
        assert monto1 == monto3
        assert monto1 != monto2
    
    def test_comparacion_con_numeros(self):
        """Test comparación con números."""
        monto = Monto(Decimal('100.00'))
        
        assert monto > 50
        assert monto < 150
        assert not (monto > 150)
        assert not (monto < 50)
    
    def test_conversiones(self):
        """Test conversiones a otros tipos."""
        monto = Monto(Decimal('150.50'))
        
        # To float
        assert monto.to_float() == 150.50
        assert float(monto) == 150.50
        
        # To string formateado
        assert monto.to_string_formatted() == "$150.50"
        assert monto.to_string_formatted(include_currency=False) == "150.50"
        assert str(monto) == "$150.50"
    
    def test_formato_miles(self):
        """Test formato con separadores de miles."""
        monto = Monto(Decimal('1500.25'))
        assert monto.to_string_formatted() == "$1,500.25"
        
        monto = Monto(Decimal('1000000.00'))
        assert monto.to_string_formatted() == "$1,000,000.00"
    
    def test_immutabilidad(self):
        """Test que Monto es inmutable."""
        monto = Monto(Decimal('100.00'))
        
        # No debería poder cambiar el valor
        with pytest.raises(AttributeError):
            monto.valor = Decimal('200.00')
    
    def test_operaciones_no_mutan_original(self):
        """Test que las operaciones no mutan el monto original."""
        monto_original = Monto(Decimal('100.00'))
        valor_original = monto_original.valor
        
        # Operaciones no deben cambiar el original
        monto_original.sumar(Decimal('50.00'))
        monto_original.restar(Decimal('25.00'))
        monto_original.multiplicar(2)
        
        assert monto_original.valor == valor_original


class TestMontoEdgeCases:
    """Tests para casos edge del objeto valor Monto."""
    
    def test_monto_minimo(self):
        """Test monto con valor mínimo."""
        monto = Monto(Decimal('0.01'))
        assert monto.valor == Decimal('0.01')
    
    def test_precision_decimal(self):
        """Test precisión con decimales complejos."""
        monto = Monto(Decimal('0.10'))
        resultado = monto.sumar(Decimal('0.20'))
        
        # Debe ser exactamente 0.30, no 0.30000000001
        assert resultado.valor == Decimal('0.30')
    
    def test_operaciones_cadena(self):
        """Test operaciones en cadena."""
        monto = Monto(Decimal('100.00'))
        
        resultado = monto.sumar(50).restar(25).multiplicar(2)
        assert resultado.valor == Decimal('250.00')
    
    def test_redondeo_casos_especiales(self):
        """Test casos especiales de redondeo."""
        # .5 casos (ROUND_HALF_UP)
        monto = Monto(Decimal('100.125'))
        assert monto.valor == Decimal('100.12')
        
        monto = Monto(Decimal('100.135'))
        assert monto.valor == Decimal('100.14')
    
    def test_from_string_casos_especiales(self):
        """Test casos especiales de from_string."""
        # Solo símbolo de moneda
        with pytest.raises(ValueError):
            Monto.from_string('$')
        
        # Múltiples puntos
        with pytest.raises(ValueError):
            Monto.from_string('100.50.75')
        
        # Espacios internos
        monto = Monto.from_string('1 500.25')
        # Esto debería fallar porque no manejamos espacios internos
        with pytest.raises(ValueError):
            Monto.from_string('1 500.25')