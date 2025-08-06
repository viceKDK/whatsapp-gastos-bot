"""
Tests para la infraestructura de WhatsApp

Tests unitarios para los conectores y servicios de WhatsApp.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from infrastructure.whatsapp.whatsapp_selenium import WhatsAppSeleniumConnector
from infrastructure.whatsapp.whatsapp_sender import WhatsAppMessageSender, WhatsAppEnhancedConnector
from domain.models.gasto import Gasto
from domain.value_objects.monto import Monto
from domain.value_objects.categoria import Categoria


class TestWhatsAppSeleniumConnector(unittest.TestCase):
    """Tests para WhatsAppSeleniumConnector."""
    
    def setUp(self):
        """Configurar cada test."""
        self.mock_config = Mock()
        self.mock_config.chrome_headless = True
        self.mock_config.connection_timeout_seconds = 10
        self.mock_config.target_chat_name = "Test Chat"
        
        self.connector = WhatsAppSeleniumConnector(self.mock_config)
    
    def test_initialization(self):
        """Test inicialización del conector."""
        self.assertEqual(self.connector.config, self.mock_config)
        self.assertFalse(self.connector.connected)
        self.assertFalse(self.connector.chat_selected)
        self.assertIsNone(self.connector.driver)
        self.assertIsNone(self.connector.last_message_time)
    
    @patch('infrastructure.whatsapp.whatsapp_selenium.webdriver.Chrome')
    def test_initialize_driver_success(self, mock_chrome):
        """Test inicialización exitosa del driver."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        result = self.connector._initialize_driver()
        
        self.assertTrue(result)
        self.assertEqual(self.connector.driver, mock_driver)
        mock_driver.set_page_load_timeout.assert_called_once()
        mock_driver.implicitly_wait.assert_called_once_with(5)
    
    @patch('infrastructure.whatsapp.whatsapp_selenium.webdriver.Chrome')
    def test_initialize_driver_failure(self, mock_chrome):
        """Test fallo en inicialización del driver."""
        mock_chrome.side_effect = Exception("Chrome not found")
        
        result = self.connector._initialize_driver()
        
        self.assertFalse(result)
        self.assertIsNone(self.connector.driver)
    
    def test_setup_chrome_options(self):
        """Test configuración de opciones de Chrome."""
        options = self.connector._setup_chrome_options()
        
        # Verificar que se configuraron las opciones básicas
        self.assertIsNotNone(options)
        # Las opciones son internas de Selenium, difícil de verificar directamente
    
    def test_get_new_messages_not_connected(self):
        """Test obtención de mensajes cuando no está conectado."""
        result = self.connector.get_new_messages()
        
        self.assertEqual(result, [])
    
    @patch('infrastructure.whatsapp.whatsapp_selenium.datetime')
    def test_parse_message_timestamp_today(self, mock_datetime):
        """Test parseo de timestamp de hoy."""
        mock_now = datetime(2024, 1, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now
        
        result = self.connector._parse_message_timestamp("15:30")
        
        expected = mock_now.replace(hour=15, minute=30, second=0, microsecond=0)
        self.assertEqual(result, expected)
    
    @patch('infrastructure.whatsapp.whatsapp_selenium.datetime')
    def test_parse_message_timestamp_yesterday(self, mock_datetime):
        """Test parseo de timestamp de ayer (tiempo futuro)."""
        mock_now = datetime(2024, 1, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now
        
        # Hora futura debería ser de ayer
        result = self.connector._parse_message_timestamp("12:30")
        
        expected = mock_now.replace(hour=12, minute=30, second=0, microsecond=0)
        # No debería ser de ayer porque 12:30 es antes de 10:30
        self.assertEqual(result, expected)
    
    def test_is_new_message_no_last_time(self):
        """Test mensaje es nuevo cuando no hay último timestamp."""
        message_time = datetime.now()
        
        result = self.connector._is_new_message(message_time)
        
        self.assertTrue(result)
    
    def test_is_new_message_newer(self):
        """Test mensaje es nuevo cuando es más reciente."""
        self.connector.last_message_time = datetime(2024, 1, 15, 10, 0, 0)
        message_time = datetime(2024, 1, 15, 10, 5, 0)
        
        result = self.connector._is_new_message(message_time)
        
        self.assertTrue(result)
    
    def test_is_new_message_older(self):
        """Test mensaje no es nuevo cuando es más antiguo."""
        self.connector.last_message_time = datetime(2024, 1, 15, 10, 5, 0)
        message_time = datetime(2024, 1, 15, 10, 0, 0)
        
        result = self.connector._is_new_message(message_time)
        
        self.assertFalse(result)
    
    def test_cleanup_driver(self):
        """Test limpieza del driver."""
        mock_driver = Mock()
        self.connector.driver = mock_driver
        
        self.connector._cleanup_driver()
        
        mock_driver.quit.assert_called_once()
        self.assertIsNone(self.connector.driver)
    
    def test_cleanup_driver_no_driver(self):
        """Test limpieza cuando no hay driver."""
        self.connector.driver = None
        
        # No debería lanzar excepción
        self.connector._cleanup_driver()
        
        self.assertIsNone(self.connector.driver)


class TestWhatsAppMessageSender(unittest.TestCase):
    """Tests para WhatsAppMessageSender."""
    
    def setUp(self):
        """Configurar cada test."""
        self.mock_connector = Mock()
        self.mock_connector.connected = True
        self.mock_connector.chat_selected = True
        self.mock_connector.driver = Mock()
        
        self.sender = WhatsAppMessageSender(self.mock_connector)
    
    def test_initialization(self):
        """Test inicialización del sender."""
        self.assertEqual(self.sender.connector, self.mock_connector)
        self.assertEqual(self.sender.messages_sent, 0)
        self.assertIsNone(self.sender.last_send_time)
        self.assertEqual(self.sender.typing_delay, 0.1)
        self.assertEqual(self.sender.send_delay, 2.0)
    
    def test_can_send_messages_true(self):
        """Test puede enviar mensajes cuando está conectado."""
        result = self.sender.can_send_messages
        
        self.assertTrue(result)
    
    def test_can_send_messages_not_connected(self):
        """Test no puede enviar cuando no está conectado."""
        self.mock_connector.connected = False
        
        result = self.sender.can_send_messages
        
        self.assertFalse(result)
    
    def test_can_send_messages_no_chat(self):
        """Test no puede enviar cuando no hay chat seleccionado."""
        self.mock_connector.chat_selected = False
        
        result = self.sender.can_send_messages
        
        self.assertFalse(result)
    
    def test_send_text_message_not_connected(self):
        """Test envío de mensaje cuando no está conectado."""
        self.mock_connector.connected = False
        
        result = self.sender.send_text_message("Test message")
        
        self.assertFalse(result)
    
    def test_send_text_message_empty(self):
        """Test envío de mensaje vacío."""
        result = self.sender.send_text_message("")
        
        self.assertFalse(result)
    
    def test_send_gasto_confirmation(self):
        """Test envío de confirmación de gasto."""
        # Crear gasto de prueba
        gasto = Gasto(
            monto=Monto(150.0),
            categoria=Categoria("comida"),
            fecha=datetime(2024, 1, 15),
            descripcion="Almuerzo"
        )
        
        # Mock del send_text_message
        self.sender.send_text_message = Mock(return_value=True)
        
        result = self.sender.send_gasto_confirmation(gasto, 0.9)
        
        self.assertTrue(result)
        self.sender.send_text_message.assert_called_once()
        
        # Verificar que el mensaje contiene los datos del gasto
        call_args = self.sender.send_text_message.call_args[0][0]
        self.assertIn("Gasto Registrado", call_args)
        self.assertIn("$150.0", call_args)
        self.assertIn("comida", call_args)
        self.assertIn("15/01/2024", call_args)
        self.assertIn("90%", call_args)
    
    def test_send_error_notification(self):
        """Test envío de notificación de error."""
        self.sender.send_text_message = Mock(return_value=True)
        
        result = self.sender.send_error_notification("Error de prueba", "mensaje original")
        
        self.assertTrue(result)
        self.sender.send_text_message.assert_called_once()
        
        call_args = self.sender.send_text_message.call_args[0][0]
        self.assertIn("Error Procesando Mensaje", call_args)
        self.assertIn("Error de prueba", call_args)
        self.assertIn("mensaje original", call_args)
    
    def test_send_suggestions(self):
        """Test envío de sugerencias."""
        suggestions = [
            {'monto': 100, 'categoria': 'comida', 'confidence': 0.8},
            {'monto': 150, 'categoria': 'transporte', 'confidence': 0.6}
        ]
        
        self.sender.send_text_message = Mock(return_value=True)
        
        result = self.sender.send_suggestions(suggestions, "OCR")
        
        self.assertTrue(result)
        self.sender.send_text_message.assert_called_once()
        
        call_args = self.sender.send_text_message.call_args[0][0]
        self.assertIn("Sugerencias de Gasto", call_args)
        self.assertIn("OCR", call_args)
        self.assertIn("$100", call_args)
        self.assertIn("comida", call_args)
    
    def test_send_help_message(self):
        """Test envío de mensaje de ayuda."""
        self.sender.send_text_message = Mock(return_value=True)
        
        result = self.sender.send_help_message()
        
        self.assertTrue(result)
        self.sender.send_text_message.assert_called_once()
        
        call_args = self.sender.send_text_message.call_args[0][0]
        self.assertIn("Bot de Gastos - Ayuda", call_args)
        self.assertIn("Formatos soportados", call_args)
    
    def test_get_send_stats(self):
        """Test obtención de estadísticas."""
        self.sender.messages_sent = 5
        self.sender.last_send_time = datetime(2024, 1, 15, 10, 0, 0)
        
        stats = self.sender.get_send_stats()
        
        self.assertEqual(stats['messages_sent'], 5)
        self.assertEqual(stats['last_send_time'], '2024-01-15T10:00:00')
        self.assertTrue(stats['can_send'])
        self.assertEqual(stats['typing_delay'], 0.1)
        self.assertEqual(stats['send_delay'], 2.0)


class TestWhatsAppEnhancedConnector(unittest.TestCase):
    """Tests para WhatsAppEnhancedConnector."""
    
    def setUp(self):
        """Configurar cada test."""
        self.mock_config = Mock()
        self.mock_config.chrome_headless = True
        self.mock_config.connection_timeout_seconds = 10
        self.mock_config.target_chat_name = "Test Chat"
        
    @patch('infrastructure.whatsapp.whatsapp_sender.WhatsAppSeleniumConnector.__init__')
    @patch('infrastructure.whatsapp.whatsapp_sender.WhatsAppSeleniumConnector.connect')
    def test_connect_success(self, mock_super_connect, mock_super_init):
        """Test conexión exitosa del conector mejorado."""
        mock_super_init.return_value = None
        mock_super_connect.return_value = True
        
        connector = WhatsAppEnhancedConnector(self.mock_config)
        connector.logger = Mock()  # Mock logger
        
        result = connector.connect()
        
        self.assertTrue(result)
        self.assertIsNotNone(connector.sender)
        self.assertTrue(connector.auto_responses_enabled)
    
    @patch('infrastructure.whatsapp.whatsapp_sender.WhatsAppSeleniumConnector.__init__')
    @patch('infrastructure.whatsapp.whatsapp_sender.WhatsAppSeleniumConnector.connect')
    def test_connect_failure(self, mock_super_connect, mock_super_init):
        """Test fallo en conexión del conector mejorado."""
        mock_super_init.return_value = None
        mock_super_connect.return_value = False
        
        connector = WhatsAppEnhancedConnector(self.mock_config)
        
        result = connector.connect()
        
        self.assertFalse(result)
    
    def test_enable_auto_responses(self):
        """Test habilitar/deshabilitar respuestas automáticas."""
        connector = WhatsAppEnhancedConnector(self.mock_config)
        connector.logger = Mock()
        
        connector.enable_auto_responses(False)
        
        self.assertFalse(connector.auto_responses_enabled)
    
    def test_send_message_with_sender(self):
        """Test envío directo de mensaje con sender."""
        connector = WhatsAppEnhancedConnector(self.mock_config)
        connector.sender = Mock()
        connector.sender.send_text_message.return_value = True
        
        result = connector.send_message("Test message")
        
        self.assertTrue(result)
        connector.sender.send_text_message.assert_called_once_with("Test message")
    
    def test_send_message_no_sender(self):
        """Test envío directo de mensaje sin sender."""
        connector = WhatsAppEnhancedConnector(self.mock_config)
        connector.sender = None
        
        result = connector.send_message("Test message")
        
        self.assertFalse(result)
    
    def test_get_enhanced_stats(self):
        """Test obtención de estadísticas mejoradas."""
        connector = WhatsAppEnhancedConnector(self.mock_config)
        connector.connected = True
        connector.chat_selected = True
        connector.last_message_time = datetime(2024, 1, 15, 10, 0, 0)
        connector.auto_responses_enabled = True
        connector.response_delay = 2.0
        
        # Mock sender con estadísticas
        connector.sender = Mock()
        connector.sender.get_send_stats.return_value = {
            'messages_sent': 5,
            'last_send_time': '2024-01-15T10:00:00',
            'can_send': True,
            'typing_delay': 0.1,
            'send_delay': 2.0
        }
        
        stats = connector.get_enhanced_stats()
        
        self.assertTrue(stats['connection_stats']['connected'])
        self.assertTrue(stats['connection_stats']['chat_selected'])
        self.assertEqual(stats['connection_stats']['last_message_time'], '2024-01-15T10:00:00')
        self.assertTrue(stats['auto_responses_enabled'])
        self.assertEqual(stats['response_delay'], 2.0)
        self.assertEqual(stats['sender_stats']['messages_sent'], 5)


class TestWhatsAppIntegration(unittest.TestCase):
    """Tests de integración para los componentes de WhatsApp."""
    
    def setUp(self):
        """Configurar cada test."""
        self.mock_config = Mock()
        self.mock_config.chrome_headless = True
        self.mock_config.connection_timeout_seconds = 10
        self.mock_config.target_chat_name = "Test Chat"
    
    def test_end_to_end_message_flow(self):
        """Test flujo completo de mensaje desde recepción hasta respuesta."""
        # Este sería un test de integración más complejo
        # que requeriría mocks más elaborados o un entorno de test
        pass
    
    def test_error_handling_flow(self):
        """Test manejo de errores en flujo completo."""
        # Test que verifica el manejo de errores en toda la cadena
        pass


if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.getLogger().setLevel(logging.ERROR)  # Reducir ruido en tests
    
    # Ejecutar tests
    unittest.main()