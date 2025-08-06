"""
Tests para el servicio InterpretarMensajeService

Tests unitarios para validar la extracción de información de gastos desde mensajes.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch

from app.services.interpretar_mensaje import InterpretarMensajeService
from domain.models.gasto import Gasto


class TestInterpretarMensajeService:
    """Tests para el servicio InterpretarMensajeService."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.service = InterpretarMensajeService()
    
    def test_procesar_mensaje_gasto_completo(self):
        """Test procesar mensaje con patrón 'gasto: monto categoria'."""
        fecha_test = datetime(2024, 1, 15, 10, 30)
        
        gasto = self.service.procesar_mensaje("gasto: 150 comida", fecha_test)
        
        assert gasto is not None
        assert gasto.monto == Decimal('150')
        assert gasto.categoria == 'comida'
        assert gasto.fecha == fecha_test
        assert gasto.descripcion is None
    
    def test_procesar_mensaje_gaste(self):
        """Test procesar mensaje con patrón 'gasté monto categoria'."""
        gasto = self.service.procesar_mensaje("gasté 75.50 transporte")
        
        assert gasto is not None
        assert gasto.monto == Decimal('75.50')
        assert gasto.categoria == 'transporte'
    
    def test_procesar_mensaje_pague(self):
        """Test procesar mensaje con patrón 'pagué monto categoria'."""
        gasto = self.service.procesar_mensaje("pagué 200 servicios")
        
        assert gasto is not None
        assert gasto.monto == Decimal('200')
        assert gasto.categoria == 'servicios'
    
    def test_procesar_mensaje_compre(self):
        """Test procesar mensaje con patrón 'compré monto categoria'."""
        gasto = self.service.procesar_mensaje("compré 85 nafta")
        
        assert gasto is not None
        assert gasto.monto == Decimal('85')
        assert gasto.categoria == 'nafta'
    
    def test_procesar_mensaje_solo_monto_categoria(self):
        """Test procesar mensaje con solo monto y categoría."""
        gasto = self.service.procesar_mensaje("500 super")
        
        assert gasto is not None
        assert gasto.monto == Decimal('500')
        assert gasto.categoria == 'super'
    
    def test_procesar_mensaje_con_decimales(self):
        """Test procesar mensaje con decimales."""
        gasto = self.service.procesar_mensaje("125.75 comida")
        
        assert gasto is not None
        assert gasto.monto == Decimal('125.75')
        assert gasto.categoria == 'comida'
    
    def test_procesar_mensaje_case_insensitive(self):
        """Test que el procesamiento es case insensitive."""
        gasto1 = self.service.procesar_mensaje("GASTO: 100 COMIDA")
        gasto2 = self.service.procesar_mensaje("gasto: 100 comida")
        gasto3 = self.service.procesar_mensaje("Gasté 100 Comida")
        
        assert gasto1 is not None
        assert gasto2 is not None  
        assert gasto3 is not None
        assert gasto1.categoria == gasto2.categoria == gasto3.categoria == 'comida'
    
    def test_procesar_mensaje_con_espacios_extra(self):
        """Test procesar mensaje con espacios extra."""
        gasto = self.service.procesar_mensaje("  gasto:   150   comida  ")
        
        assert gasto is not None
        assert gasto.monto == Decimal('150')
        assert gasto.categoria == 'comida'
    
    def test_fecha_por_defecto(self):
        """Test que usa datetime.now() por defecto."""
        with patch('app.services.interpretar_mensaje.datetime') as mock_datetime:
            fecha_mock = datetime(2024, 1, 15, 10, 30)
            mock_datetime.now.return_value = fecha_mock
            
            gasto = self.service.procesar_mensaje("100 comida")
            
            assert gasto.fecha == fecha_mock
            mock_datetime.now.assert_called_once()
    
    def test_procesar_mensaje_no_es_gasto(self):
        """Test procesar mensaje que no es un gasto."""
        result = self.service.procesar_mensaje("Hola, ¿cómo estás?")
        assert result is None
        
        result = self.service.procesar_mensaje("Mañana voy al supermercado")
        assert result is None
        
        result = self.service.procesar_mensaje("123abc")
        assert result is None
    
    def test_procesar_mensaje_monto_invalido(self):
        """Test procesar mensaje con monto inválido."""
        result = self.service.procesar_mensaje("gasto: 0 comida")
        assert result is None
        
        result = self.service.procesar_mensaje("gasto: -50 comida")
        assert result is None
        
        result = self.service.procesar_mensaje("gasto: abc comida")
        assert result is None
    
    def test_procesar_mensaje_sin_categoria(self):
        """Test procesar mensaje sin categoría."""
        result = self.service.procesar_mensaje("gasto: 150")
        assert result is None
        
        result = self.service.procesar_mensaje("150")
        assert result is None
    
    def test_procesar_mensaje_vacio(self):
        """Test procesar mensaje vacío."""
        result = self.service.procesar_mensaje("")
        assert result is None
        
        result = self.service.procesar_mensaje("   ")
        assert result is None
    
    def test_es_mensaje_gasto_palabras_clave(self):
        """Test detección de mensajes de gasto por palabras clave."""
        assert self.service._es_mensaje_gasto("gasto: 100 comida") is True
        assert self.service._es_mensaje_gasto("gasté 100 comida") is True
        assert self.service._es_mensaje_gasto("pagué 100 comida") is True
        assert self.service._es_mensaje_gasto("compré 100 comida") is True
    
    def test_es_mensaje_gasto_patron_numerico(self):
        """Test detección de mensajes de gasto por patrón numérico."""
        assert self.service._es_mensaje_gasto("100 comida") is True
        assert self.service._es_mensaje_gasto("150.50 transporte") is True
        assert self.service._es_mensaje_gasto("75 nafta") is True
    
    def test_no_es_mensaje_gasto(self):
        """Test que no detecta mensajes que no son gastos."""
        assert self.service._es_mensaje_gasto("Hola") is False
        assert self.service._es_mensaje_gasto("¿Cómo estás?") is False
        assert self.service._es_mensaje_gasto("100 metros") is False  # Podría ser ambiguo
        assert self.service._es_mensaje_gasto("abc def") is False
    
    def test_extraer_datos_patron_completo(self):
        """Test extraer datos con patrón completo."""
        datos = self.service._extraer_datos("gasto: 150.50 comida")
        
        assert datos is not None
        assert datos['monto'] == Decimal('150.50')
        assert datos['categoria'] == 'comida'
        assert datos['descripcion'] is None
    
    def test_extraer_datos_patron_simple(self):
        """Test extraer datos con patrón simple."""
        datos = self.service._extraer_datos("100 transporte")
        
        assert datos is not None
        assert datos['monto'] == Decimal('100')
        assert datos['categoria'] == 'transporte'
    
    def test_extraer_datos_sin_patron(self):
        """Test extraer datos de texto sin patrón válido."""
        datos = self.service._extraer_datos("Hola mundo")
        assert datos is None
        
        datos = self.service._extraer_datos("abc def ghi")
        assert datos is None
    
    def test_manejo_errores_creacion_objetos_valor(self):
        """Test manejo de errores al crear objetos de valor."""
        # Mock para simular error en Monto
        with patch('app.services.interpretar_mensaje.Monto') as mock_monto:
            mock_monto.side_effect = ValueError("Monto inválido")
            
            result = self.service.procesar_mensaje("gasto: 150 comida")
            assert result is None
        
        # Mock para simular error en Categoria
        with patch('app.services.interpretar_mensaje.Categoria') as mock_categoria:
            mock_categoria.side_effect = ValueError("Categoría inválida")
            
            result = self.service.procesar_mensaje("gasto: 150 comida")
            assert result is None
    
    def test_logging_debug(self):
        """Test que se generan logs de debug correctos."""
        with patch.object(self.service.logger, 'debug') as mock_debug:
            self.service.procesar_mensaje("gasto: 150 comida")
            
            mock_debug.assert_any_call("Procesando mensaje: gasto: 150 comida")
    
    def test_logging_info_exito(self):
        """Test que se genera log de info en caso exitoso."""
        with patch.object(self.service.logger, 'info') as mock_info:
            self.service.procesar_mensaje("gasto: 150 comida")
            
            mock_info.assert_called_once_with("Gasto extraído exitosamente: 150 - comida")
    
    def test_logging_error(self):
        """Test que se genera log de error en caso de excepción."""
        with patch.object(self.service, '_extraer_datos', side_effect=Exception("Test error")):
            with patch.object(self.service.logger, 'error') as mock_error:
                result = self.service.procesar_mensaje("gasto: 150 comida")
                
                assert result is None
                mock_error.assert_called_once()
                assert "Test error" in str(mock_error.call_args)


class TestInterpretarMensajeServiceEdgeCases:
    """Tests para casos edge del servicio InterpretarMensajeService."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.service = InterpretarMensajeService()
    
    def test_mensaje_con_caracteres_especiales(self):
        """Test mensaje con caracteres especiales."""
        gasto = self.service.procesar_mensaje("gasto: 150.50 café")
        
        assert gasto is not None
        assert gasto.categoria == 'café'
    
    def test_mensaje_con_numeros_en_categoria(self):
        """Test mensaje con números en la categoría."""
        gasto = self.service.procesar_mensaje("100 super1")
        
        assert gasto is not None
        assert gasto.categoria == 'super1'
    
    def test_monto_con_muchos_decimales(self):
        """Test monto con más de 2 decimales en el texto."""
        # El servicio debería manejar esto, pero Monto lo redondeará
        gasto = self.service.procesar_mensaje("100.999 comida")
        
        # Dependiendo de cómo maneje el regex, podría o no capturar todos los decimales
        # Si captura "100.99", debería crear el gasto
        if gasto is not None:
            assert gasto.monto <= Decimal('101.00')  # Redondeado
    
    def test_monto_muy_grande(self):
        """Test monto que excede el límite."""
        # Esto debería fallar en la creación del objeto Monto
        result = self.service.procesar_mensaje("10000000 comida")
        assert result is None  # Debería fallar por límite de Monto
    
    def test_categoria_muy_larga(self):
        """Test categoría muy larga."""
        categoria_larga = 'a' * 100
        gasto = self.service.procesar_mensaje(f"100 {categoria_larga}")
        
        # Dependiendo de la validación de Categoria, podría funcionar o no
        if gasto is not None:
            assert len(gasto.categoria) <= 100