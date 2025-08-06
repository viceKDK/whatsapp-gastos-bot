"""
CLI Runner para el Bot

Orquestador principal que ejecuta el bot desde línea de comandos.
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Optional

from config.settings import Settings, StorageMode
from shared.logger import get_logger
from app.usecases.procesar_mensaje import ProcesarMensajeUseCase
from infrastructure.storage.excel_writer import ExcelStorage
from infrastructure.whatsapp import WhatsAppEnhancedConnector
from app.services.message_processor import get_message_processor, MessageContent


class BotRunner:
    """Runner principal del bot que orquesta todos los componentes."""
    
    def __init__(self, settings: Settings):
        """
        Inicializa el bot runner.
        
        Args:
            settings: Configuración del sistema
        """
        self.settings = settings
        self.logger = get_logger(__name__)
        self.running = False
        self.whatsapp_connector = None
        self.storage_repository = None
        self.message_processor = None
        self.advanced_processor = None
        
        # Estadísticas
        self.stats = {
            'inicio': None,
            'mensajes_procesados': 0,
            'gastos_registrados': 0,
            'errores': 0,
            'ultima_actividad': None
        }
    
    def run(self) -> bool:
        """
        Ejecuta el bot principal.
        
        Returns:
            True si se ejecutó exitosamente, False si hubo errores
        """
        try:
            self.logger.info("Iniciando componentes del bot...")
            
            # Inicializar componentes
            if not self._initialize_components():
                self.logger.error("Error inicializando componentes")
                return False
            
            # Marcar como running
            self.running = True
            self.stats['inicio'] = datetime.now()
            
            # Mostrar información inicial
            self._show_startup_info()
            
            # Bucle principal
            return self._main_loop()
            
        except Exception as e:
            self.logger.exception(f"Error en run: {e}")
            return False
        finally:
            self._cleanup()
    
    def stop(self) -> None:
        """Detiene el bot de manera limpia."""
        self.logger.info("Deteniendo bot...")
        self.running = False
    
    def _initialize_components(self) -> bool:
        """
        Inicializa todos los componentes del bot.
        
        Returns:
            True si todos los componentes se inicializaron correctamente
        """
        try:
            # Inicializar storage
            if not self._initialize_storage():
                return False
            
            # Inicializar WhatsApp connector (placeholder por ahora)
            if not self._initialize_whatsapp():
                return False
            
            # Inicializar processors
            self.message_processor = ProcesarMensajeUseCase(self.storage_repository)
            self.advanced_processor = get_message_processor()
            
            self.logger.info("Todos los componentes inicializados correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando componentes: {e}")
            return False
    
    def _initialize_storage(self) -> bool:
        """
        Inicializa el sistema de almacenamiento.
        
        Returns:
            True si se inicializó correctamente
        """
        try:
            if self.settings.storage_mode == StorageMode.EXCEL:
                self.storage_repository = ExcelStorage(self.settings.excel.excel_file_path)
                self.logger.info(f"Storage Excel inicializado: {self.settings.excel.excel_file_path}")
            else:
                # TODO: Implementar SQLite storage
                self.logger.error("SQLite storage no implementado aún")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando storage: {e}")
            return False
    
    def _initialize_whatsapp(self) -> bool:
        """
        Inicializa el conector de WhatsApp.
        
        Returns:
            True si se inicializó correctamente
        """
        try:
            # Usar el conector mejorado con capacidades de envío
            self.whatsapp_connector = WhatsAppEnhancedConnector(self.settings.whatsapp)
            
            # Intentar conexión
            if self.whatsapp_connector.connect():
                # Configurar respuestas automáticas
                self.whatsapp_connector.enable_auto_responses(
                    self.settings.whatsapp.auto_responses_enabled
                )
                self.whatsapp_connector.response_delay = self.settings.whatsapp.response_delay_seconds
                
                if self.whatsapp_connector.sender:
                    self.whatsapp_connector.sender.typing_delay = self.settings.whatsapp.typing_delay_seconds
                    self.whatsapp_connector.sender.send_delay = self.settings.whatsapp.response_delay_seconds
                
                self.logger.info("WhatsApp Enhanced connector inicializado correctamente")
                return True
            else:
                self.logger.error("Error conectando con WhatsApp Web")
                return False
                
        except Exception as e:
            self.logger.error(f"Error inicializando WhatsApp: {e}")
            self.logger.error("Asegúrate de tener Chrome instalado y acceso a Internet")
            return False
    
    def _show_startup_info(self) -> None:
        """Muestra información de inicio del bot."""
        print("\n" + "="*60)
        print("🤖 BOT GASTOS WHATSAPP INICIADO")
        print("="*60)
        print(f"📅 Inicio: {self.stats['inicio'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💾 Storage: {self.settings.storage_mode.value.upper()}")
        print(f"💬 Chat: {self.settings.whatsapp.target_chat_name}")
        print(f"⚡ Modo: TIEMPO REAL (timeout: {self.settings.whatsapp.poll_interval_seconds}s)")
        print(f"📝 Log Level: {self.settings.logging.level.value}")
        print("="*60)
        print("🎯 El bot está escuchando mensajes en TIEMPO REAL...")
        print("💡 Los mensajes se procesan instantáneamente al llegar")
        print("Presiona Ctrl+C para detener")
        print("="*60 + "\n")
    
    def _main_loop(self) -> bool:
        """
        Bucle principal del bot.
        
        Returns:
            True si se ejecutó sin errores críticos
        """
        try:
            last_stats_time = datetime.now()
            
            while self.running:
                try:
                    # Verificar mensajes nuevos
                    self._process_new_messages()
                    
                    # Mostrar estadísticas cada 5 minutos
                    if datetime.now() - last_stats_time >= timedelta(minutes=5):
                        self._show_stats()
                        last_stats_time = datetime.now()
                    
                    # NO necesitamos sleep - wait_for_new_message ya maneja la espera
                    
                except KeyboardInterrupt:
                    self.logger.info("Interrupción de teclado recibida")
                    break
                except Exception as e:
                    self.stats['errores'] += 1
                    self.logger.error(f"Error en loop principal: {e}")
                    
                    # Si hay demasiados errores, salir
                    if self.stats['errores'] > 10:
                        self.logger.error("Demasiados errores, deteniendo bot")
                        break
                    
                    # Esperar un poco más en caso de error
                    time.sleep(min(60, self.settings.whatsapp.poll_interval_seconds * 2))
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Error crítico en main loop: {e}")
            return False
    
    def _process_new_messages(self) -> None:
        """Procesa mensajes nuevos de WhatsApp usando detección en tiempo real."""
        try:
            # Usar wait_for_new_message para detección en tiempo real
            # En lugar del intervalo fijo, esperamos activamente por mensajes
            timeout = min(self.settings.whatsapp.poll_interval_seconds, 30)  # Máximo 30s
            mensajes = self.whatsapp_connector.wait_for_new_message(timeout)
            
            # Si no hay mensajes después del timeout, verificar una vez más por si acaso
            if not mensajes:
                mensajes = self.whatsapp_connector.get_new_messages()
            
            if not mensajes:
                return
            
            self.logger.info(f"🚀 PROCESANDO {len(mensajes)} MENSAJES NUEVOS")
            
            for mensaje_texto, fecha_mensaje in mensajes:
                self.stats['mensajes_procesados'] += 1
                self.stats['ultima_actividad'] = datetime.now()
                
                # Procesar con procesador avanzado
                content = MessageContent(
                    text=mensaje_texto,
                    timestamp=fecha_mensaje,
                    message_type="text"
                )
                
                processing_result = self.advanced_processor.process_message(content)
                
                if processing_result.success and processing_result.gasto:
                    # Registrar en storage
                    try:
                        self.storage_repository.guardar_gasto(processing_result.gasto)
                        self.stats['gastos_registrados'] += 1
                        
                        # Log del gasto registrado
                        self.logger.info(f"💰 Gasto registrado: ${processing_result.gasto.monto} - {processing_result.gasto.categoria}")
                        
                        # Mostrar en consola si no es modo headless
                        if not self.settings.whatsapp.chrome_headless:
                            print(f"💰 {datetime.now().strftime('%H:%M:%S')} - "
                                  f"${processing_result.gasto.monto} en {processing_result.gasto.categoria}")
                        
                    except Exception as e:
                        self.logger.error(f"Error guardando gasto: {e}")
                        processing_result.success = False
                        processing_result.errors.append(f"Error guardando: {str(e)}")
                
                # Enviar respuesta automática si está habilitada
                try:
                    self.whatsapp_connector.process_and_respond(mensaje_texto, processing_result)
                except Exception as e:
                    self.logger.warning(f"Error enviando respuesta automática: {e}")
                
                # Manejar comandos especiales
                self._handle_special_commands(mensaje_texto.lower().strip())
                
        except Exception as e:
            self.stats['errores'] += 1
            self.logger.error(f"Error procesando mensajes: {e}")
    
    def _handle_special_commands(self, message_text: str) -> None:
        """
        Maneja comandos especiales del usuario.
        
        Args:
            message_text: Texto del mensaje en minúsculas
        """
        try:
            if message_text in ['ayuda', 'help', '?']:
                self.whatsapp_connector.sender.send_help_message()
                
            elif message_text in ['estadisticas', 'stats', 'resumen']:
                # Obtener estadísticas del storage
                if hasattr(self.storage_repository, 'obtener_estadisticas'):
                    stats = self.storage_repository.obtener_estadisticas()
                    self.whatsapp_connector.sender.send_stats_summary(stats)
                    
            elif message_text in ['categorias', 'categories']:
                categories_msg = f"🏷️ *Categorías válidas:*\n{', '.join(sorted(self.settings.categorias.categorias_validas))}"
                self.whatsapp_connector.send_message(categories_msg)
                
        except Exception as e:
            self.logger.error(f"Error manejando comando especial: {e}")
    
    def _show_stats(self) -> None:
        """Muestra estadísticas del bot."""
        if not self.stats['inicio']:
            return
        
        tiempo_ejecutando = datetime.now() - self.stats['inicio']
        horas = tiempo_ejecutando.total_seconds() / 3600
        
        self.logger.info(f"📊 Estadísticas: {tiempo_ejecutando} ejecutando, "
                        f"{self.stats['mensajes_procesados']} mensajes, "
                        f"{self.stats['gastos_registrados']} gastos, "
                        f"{self.stats['errores']} errores")
        
        if horas > 0:
            rate = self.stats['gastos_registrados'] / horas
            self.logger.info(f"📈 Tasa: {rate:.1f} gastos/hora")
    
    def _cleanup(self) -> None:
        """Limpia recursos al finalizar."""
        try:
            self.logger.info("Limpiando recursos...")
            
            # Desconectar WhatsApp
            if self.whatsapp_connector:
                self.whatsapp_connector.disconnect()
            
            # Mostrar estadísticas finales
            if self.stats['inicio']:
                tiempo_total = datetime.now() - self.stats['inicio']
                self.logger.info(f"🏁 Bot detenido después de {tiempo_total}")
                self.logger.info(f"📊 Total: {self.stats['gastos_registrados']} gastos registrados, "
                               f"{self.stats['errores']} errores")
            
        except Exception as e:
            self.logger.error(f"Error en cleanup: {e}")


