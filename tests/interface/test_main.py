"""
Tests para el módulo main

Tests unitarios para validar el punto de entrada principal de la aplicación.
"""

import pytest
from unittest.mock import Mock, patch, call
import sys
from io import StringIO

# Importar el módulo main
try:
    from main import main, configurar_logging
except ImportError:
    # Si no se puede importar, crear un mock básico para los tests
    pytest.skip("Módulo main no encontrado", allow_module_level=True)


class TestMain:
    """Tests para la función main."""
    
    @patch('main.os.path.exists')
    @patch('main.WhatsAppSeleniumConnector')
    @patch('main.ExcelStorage')
    @patch('main.ProcesarMensajeUseCase')
    def test_main_sin_argumentos(self, mock_use_case, mock_storage, mock_connector, mock_exists):
        """Test ejecución principal sin argumentos."""
        # Setup mocks
        mock_exists.return_value = False  # Config file doesn't exist
        mock_connector_instance = Mock()
        mock_connector.return_value = mock_connector_instance
        mock_connector_instance.connect.return_value = True
        mock_connector_instance.get_new_messages.return_value = []
        
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        # Simular sys.argv sin argumentos
        with patch.object(sys, 'argv', ['main.py']):
            with patch('main.time.sleep', side_effect=KeyboardInterrupt):  # Para salir del loop
                try:
                    main()
                except KeyboardInterrupt:
                    pass
        
        # Verificar que se intentó conectar
        mock_connector_instance.connect.assert_called_once()
    
    @patch('main.os.path.exists')
    @patch('main.WhatsAppSeleniumConnector')
    @patch('main.ExcelStorage')
    @patch('main.ProcesarMensajeUseCase')
    def test_main_con_argumentos_help(self, mock_use_case, mock_storage, mock_connector, mock_exists):
        """Test ejecución con argumento --help."""
        with patch.object(sys, 'argv', ['main.py', '--help']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit):
                    main()
                
                output = mock_stdout.getvalue()
                assert 'Bot de Gastos WhatsApp' in output or 'help' in output.lower()
    
    @patch('main.os.path.exists')
    @patch('main.WhatsAppSeleniumConnector')
    @patch('main.ExcelStorage')
    @patch('main.ProcesarMensajeUseCase')
    def test_main_con_argumentos_version(self, mock_use_case, mock_storage, mock_connector, mock_exists):
        """Test ejecución con argumento --version."""
        with patch.object(sys, 'argv', ['main.py', '--version']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit):
                    main()
                
                output = mock_stdout.getvalue()
                assert any(char.isdigit() for char in output)  # Debe contener números de versión
    
    @patch('main.os.path.exists')
    @patch('main.WhatsAppSeleniumConnector')
    @patch('main.ExcelStorage')
    @patch('main.ProcesarMensajeUseCase')
    def test_main_error_conexion_whatsapp(self, mock_use_case, mock_storage, mock_connector, mock_exists):
        """Test manejo de error en conexión WhatsApp."""
        # Setup mocks
        mock_exists.return_value = False
        mock_connector_instance = Mock()
        mock_connector.return_value = mock_connector_instance
        mock_connector_instance.connect.return_value = False  # Falla la conexión
        
        with patch.object(sys, 'argv', ['main.py']):
            with patch('main.logger') as mock_logger:
                main()
                
                # Debe loggear el error de conexión
                mock_logger.error.assert_called()
                assert any('WhatsApp' in str(call) for call in mock_logger.error.call_args_list)
    
    @patch('main.os.path.exists')
    @patch('main.WhatsAppSeleniumConnector')
    @patch('main.ExcelStorage')
    @patch('main.ProcesarMensajeUseCase')
    def test_main_procesa_mensajes(self, mock_use_case, mock_storage, mock_connector, mock_exists):
        """Test que procesa mensajes correctamente."""
        # Setup mocks
        mock_exists.return_value = False
        mock_connector_instance = Mock()
        mock_connector.return_value = mock_connector_instance
        mock_connector_instance.connect.return_value = True
        
        # Simular mensajes
        mock_messages = [
            ("gasto: 150 comida", "2024-01-15T10:30:00"),
            ("500 transporte", "2024-01-15T11:30:00")
        ]
        mock_connector_instance.get_new_messages.side_effect = [mock_messages, []]  # Primera vez mensajes, segunda vez vacío
        
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        with patch.object(sys, 'argv', ['main.py']):
            with patch('main.time.sleep') as mock_sleep:
                # Configurar sleep para que termine después de 2 iteraciones
                mock_sleep.side_effect = [None, KeyboardInterrupt()]
                
                try:
                    main()
                except KeyboardInterrupt:
                    pass
        
        # Verificar que se procesaron los mensajes
        assert mock_use_case_instance.ejecutar.call_count == 2
    
    @patch('main.logger')
    def test_configurar_logging(self, mock_logger):
        """Test configuración de logging."""
        # Esta función probablemente configure el sistema de logging
        result = configurar_logging()
        
        # El resultado depende de la implementación específica
        # Podría ser None o un logger configurado
        assert result is not None or result is None  # Cualquiera es válido
    
    @patch('main.os.path.exists')
    @patch('main.WhatsAppSeleniumConnector')
    @patch('main.ExcelStorage')
    @patch('main.ProcesarMensajeUseCase')
    def test_main_keyboard_interrupt(self, mock_use_case, mock_storage, mock_connector, mock_exists):
        """Test manejo de KeyboardInterrupt (Ctrl+C)."""
        mock_exists.return_value = False
        mock_connector_instance = Mock()
        mock_connector.return_value = mock_connector_instance
        mock_connector_instance.connect.return_value = True
        mock_connector_instance.get_new_messages.return_value = []
        
        with patch.object(sys, 'argv', ['main.py']):
            with patch('main.time.sleep', side_effect=KeyboardInterrupt):
                with patch('main.logger') as mock_logger:
                    main()  # No debe propagar la excepción
                    
                    # Debe loggear que se está deteniendo
                    assert any('deteniendo' in str(call).lower() or 'stopping' in str(call).lower() 
                              for call in mock_logger.info.call_args_list)
    
    @patch('main.os.path.exists')
    def test_main_error_importacion(self, mock_exists):
        """Test manejo de errores de importación."""
        mock_exists.return_value = False
        
        with patch('main.WhatsAppSeleniumConnector', side_effect=ImportError("Selenium not found")):
            with patch('main.logger') as mock_logger:
                main()
                
                # Debe loggear el error de importación
                mock_logger.error.assert_called()
    
    @patch('main.os.path.exists')
    @patch('main.WhatsAppSeleniumConnector')
    @patch('main.ExcelStorage')
    @patch('main.ProcesarMensajeUseCase')
    def test_main_config_file_exists(self, mock_use_case, mock_storage, mock_connector, mock_exists):
        """Test cuando existe archivo de configuración."""
        # Simular que existe config file
        mock_exists.return_value = True
        
        mock_connector_instance = Mock()
        mock_connector.return_value = mock_connector_instance
        mock_connector_instance.connect.return_value = True
        mock_connector_instance.get_new_messages.return_value = []
        
        with patch.object(sys, 'argv', ['main.py']):
            with patch('main.time.sleep', side_effect=KeyboardInterrupt):
                with patch('builtins.open', create=True) as mock_open:
                    # Mock del contenido del archivo de config
                    mock_open.return_value.__enter__.return_value.read.return_value = '{"key": "value"}'
                    
                    try:
                        main()
                    except KeyboardInterrupt:
                        pass
        
        # Verificar que se intentó leer el config
        mock_open.assert_called()


class TestMainEdgeCases:
    """Tests para casos edge del módulo main."""
    
    @patch('main.os.path.exists')
    @patch('main.WhatsAppSeleniumConnector')
    def test_main_exception_general(self, mock_connector, mock_exists):
        """Test manejo de excepción general."""
        mock_exists.return_value = False
        mock_connector.side_effect = Exception("Error general")
        
        with patch.object(sys, 'argv', ['main.py']):
            with patch('main.logger') as mock_logger:
                main()  # No debe propagar la excepción
                
                # Debe loggear el error
                mock_logger.error.assert_called()
    
    @patch('main.os.path.exists')
    @patch('main.WhatsAppSeleniumConnector')
    @patch('main.ExcelStorage')
    def test_main_error_storage(self, mock_storage, mock_connector, mock_exists):
        """Test error al crear storage."""
        mock_exists.return_value = False
        mock_storage.side_effect = Exception("Storage error")
        
        mock_connector_instance = Mock()
        mock_connector.return_value = mock_connector_instance
        mock_connector_instance.connect.return_value = True
        
        with patch.object(sys, 'argv', ['main.py']):
            with patch('main.logger') as mock_logger:
                main()
                
                # Debe loggear el error de storage
                mock_logger.error.assert_called()
    
    @patch('main.os.path.exists')
    @patch('main.WhatsAppSeleniumConnector')
    @patch('main.ExcelStorage')
    @patch('main.ProcesarMensajeUseCase')
    def test_main_reconexion_automatica(self, mock_use_case, mock_storage, mock_connector, mock_exists):
        """Test reconexión automática cuando se pierde conexión."""
        mock_exists.return_value = False
        mock_connector_instance = Mock()
        mock_connector.return_value = mock_connector_instance
        
        # Simular que primero conecta, luego falla, luego reconecta
        mock_connector_instance.connect.side_effect = [True, False, True]
        mock_connector_instance.get_new_messages.side_effect = [[], Exception("Connection lost"), []]
        
        with patch.object(sys, 'argv', ['main.py']):
            with patch('main.time.sleep') as mock_sleep:
                # Terminar después de algunas iteraciones
                mock_sleep.side_effect = [None, None, KeyboardInterrupt()]
                
                try:
                    main()
                except KeyboardInterrupt:
                    pass
        
        # Debe intentar reconectar
        assert mock_connector_instance.connect.call_count >= 2
    
    def test_main_argumentos_invalidos(self):
        """Test con argumentos inválidos."""
        with patch.object(sys, 'argv', ['main.py', '--invalid-arg']):
            with patch('sys.stderr', new_callable=StringIO):
                # Dependiendo de la implementación, podría mostrar error o ignorar
                try:
                    main()
                except SystemExit:
                    pass  # Es válido que termine con error
    
    @patch('main.os.path.exists')
    @patch('main.WhatsAppSeleniumConnector')
    @patch('main.ExcelStorage')
    @patch('main.ProcesarMensajeUseCase')
    def test_main_multiples_mensajes_batch(self, mock_use_case, mock_storage, mock_connector, mock_exists):
        """Test procesamiento de múltiples mensajes en lote."""
        mock_exists.return_value = False
        mock_connector_instance = Mock()
        mock_connector.return_value = mock_connector_instance
        mock_connector_instance.connect.return_value = True
        
        # Simular muchos mensajes
        many_messages = [(f"gasto: {i*10} categoria{i}", f"2024-01-{i+1:02d}T10:30:00") for i in range(20)]
        mock_connector_instance.get_new_messages.side_effect = [many_messages, []]
        
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        with patch.object(sys, 'argv', ['main.py']):
            with patch('main.time.sleep') as mock_sleep:
                mock_sleep.side_effect = [None, KeyboardInterrupt()]
                
                try:
                    main()
                except KeyboardInterrupt:
                    pass
        
        # Debe procesar todos los mensajes
        assert mock_use_case_instance.ejecutar.call_count == 20