"""
CLI Runner para el Bot

Orquestador principal que ejecuta el bot desde línea de comandos.
"""

import time
import threading
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from config.settings import Settings, StorageMode
from shared.logger import get_logger
from app.usecases.procesar_mensaje import ProcesarMensajeUseCase
from infrastructure.storage.excel_writer import ExcelStorage
from infrastructure.storage.hybrid_storage import HybridStorage
from infrastructure.whatsapp import WhatsAppEnhancedConnector
from app.services.message_processor import get_message_processor, MessageContent
from app.services.message_filter import get_message_filter, create_smart_queue


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
        
        # Filtro inteligente de mensajes
        self.message_filter = get_message_filter()
        self.smart_queue = create_smart_queue()
        
        # Cache inteligente para detectar cambios
        self.last_page_hash = None
        self.no_change_count = 0
        self.max_no_change_before_log = 3  # Log cada 3 ciclos sin cambios
        
        # Estadísticas
        self.stats = {
            'inicio': None,
            'mensajes_procesados': 0,
            'mensajes_filtrados': 0,
            'gastos_registrados': 0,
            'errores': 0,
            'ultima_actividad': None,
            'ciclos_saltados_sin_cambios': 0,  # Nueva estadística
            'total_ciclos': 0  # Nueva estadística
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
        """⚡ Detiene el bot de manera SÚPER RÁPIDA."""
        self.logger.info("🛑 STOP SIGNAL RECIBIDO - Terminación NUCLEAR...")
        self.running = False
        
        # ⚡ FASE 1: MATAR TODOS LOS PROCESOS CHROME/CHROMEDRIVER INMEDIATAMENTE
        try:
            import subprocess
            import platform
            import os
            
            if platform.system() == "Windows":
                # Matar TODOS los procesos relacionados con Chrome
                processes_to_kill = ['chrome.exe', 'chromedriver.exe', 'chromedriver', 'msedgedriver.exe']
                for process in processes_to_kill:
                    try:
                        subprocess.run(['taskkill', '/F', '/IM', process, '/T'], 
                                     capture_output=True, timeout=1)
                    except:
                        pass
                self.logger.info("⚡ Todos los procesos browser terminados")
        except:
            pass
        
        # ⚡ FASE 2: FORZAR CIERRE DE THREADS SELENIUM
        try:
            import threading
            
            # Listar todos los threads activos
            active_threads = threading.active_count()
            self.logger.info(f"🧵 {active_threads} threads activos - forzando cierre...")
            
            # Matar threads de Selenium específicamente
            for thread in threading.enumerate():
                if thread != threading.current_thread():
                    if any(keyword in str(thread).lower() for keyword in ['selenium', 'chrome', 'webdriver']):
                        try:
                            # No podemos forzar kill threads en Python, pero podemos limpiar referencias
                            thread._stop = True
                        except:
                            pass
        except:
            pass
        
        # ⚡ FASE 3: LIMPIAR REFERENCIAS RÁPIDAMENTE
        if self.whatsapp_connector:
            try:
                # Forzar desconexión sin timeouts
                if hasattr(self.whatsapp_connector, 'connected'):
                    self.whatsapp_connector.connected = False
                if hasattr(self.whatsapp_connector, 'chat_selected'):
                    self.whatsapp_connector.chat_selected = False
                if hasattr(self.whatsapp_connector, 'driver'):
                    # Intentar quit rápido con timeout muy corto
                    try:
                        if self.whatsapp_connector.driver:
                            self.whatsapp_connector.driver.quit()
                    except:
                        pass
                    self.whatsapp_connector.driver = None
                if hasattr(self.whatsapp_connector, 'sender'):
                    self.whatsapp_connector.sender = None
            except:
                pass
        
        # ⚡ FASE 4: LIMPIAR STORAGE CONNECTIONS
        if self.storage_repository:
            try:
                if hasattr(self.storage_repository, 'close'):
                    self.storage_repository.close()
                if hasattr(self.storage_repository, '_connection'):
                    self.storage_repository._connection = None
            except:
                pass
        
        self.logger.info("💀 Terminación NUCLEAR completada - saliendo inmediatamente")
    
    def _get_page_state_hash(self) -> Optional[str]:
        """
        Obtiene un hash del estado actual de la página para detectar cambios.
        
        Returns:
            Hash MD5 del estado actual de los últimos 5 mensajes, None si hay error
        """
        try:
            if not self.whatsapp_connector or not self.whatsapp_connector.connected:
                return None
            
            # Obtener los últimos 5 elementos del chat para generar el hash
            if hasattr(self.whatsapp_connector, 'get_last_messages_for_hash'):
                # Método optimizado que solo obtiene texto de últimos mensajes
                elements_text = self.whatsapp_connector.get_last_messages_for_hash(count=5)
            else:
                # Fallback: obtener mensajes de forma tradicional
                try:
                    driver = self.whatsapp_connector.driver
                    if not driver:
                        return None
                    
                    # Selector para mensajes (ajustar según la estructura actual de WhatsApp)
                    message_selector = "div[data-testid='msg-container'] span[dir='ltr']"
                    elements = driver.find_elements("css selector", message_selector)
                    
                    # Tomar solo los últimos 5 mensajes
                    elements_text = [elem.text.strip() for elem in elements[-5:] if elem.text.strip()]
                except Exception:
                    return None
            
            if not elements_text:
                return None
            
            # Crear hash del contenido
            content = "|".join(elements_text)
            return hashlib.md5(content.encode('utf-8')).hexdigest()
            
        except Exception as e:
            self.logger.debug(f"Error obteniendo hash de página: {e}")
            return None
    
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
                # Usar storage híbrido que combina SQLite cache + Excel final
                self.storage_repository = HybridStorage(self.settings.excel.excel_file_path)
                self.logger.info(f"Storage híbrido inicializado:")
                self.logger.info(f"  📊 Excel final: {self.settings.excel.excel_file_path}")
                self.logger.info(f"  💾 SQLite cache: habilitado")
            else:
                # TODO: Implementar SQLite puro si se necesita
                self.logger.error("Solo storage híbrido (Excel+SQLite cache) está implementado")
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
                    
                    # ⚡ POLLING CONTINUO: Esperar antes del siguiente ciclo
                    if self.whatsapp_connector and self.whatsapp_connector.connected:
                        # Conexión activa - polling rápido
                        time.sleep(min(self.settings.whatsapp.poll_interval_seconds, 5))
                    else:
                        # Sin conexión - esperar más tiempo antes de reintentar
                        time.sleep(10)
                    
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
        """Procesa mensajes nuevos de WhatsApp usando detección optimizada con hash."""
        try:
            self.logger.debug("🎯 INICIANDO PROCESAMIENTO DE MENSAJES NUEVOS...")
            
            # Verificar estado de conexión ANTES de procesar
            if not self.whatsapp_connector.connected or not self.whatsapp_connector.chat_selected:
                self.logger.warning("🚨 CONEXIÓN PERDIDA - Intentando reconectar...")
                self.logger.warning(f"   Estado: Connected={self.whatsapp_connector.connected}, Chat={self.whatsapp_connector.chat_selected}")
                
                # Intentar reconectar
                if not self._reconnect_whatsapp():
                    self.logger.error("❌ RECONEXIÓN FALLIDA - Esperando 10 segundos antes del siguiente intento")
                    time.sleep(10)  # Esperar antes del siguiente intento
                    return
            
            # ⚡ OPTIMIZACIÓN CRÍTICA: Verificar si la página cambió usando hash
            current_hash = self._get_page_state_hash()
            if current_hash is None:
                self.logger.debug("⚠️ No se pudo obtener hash de página - continuando con procesamiento normal")
            elif current_hash == self.last_page_hash:
                # Página sin cambios - incrementar contador y saltar procesamiento
                self.no_change_count += 1
                self.stats['ciclos_saltados_sin_cambios'] += 1
                self.stats['total_ciclos'] += 1
                
                # Log cada N ciclos para mostrar que está funcionando
                if self.no_change_count % self.max_no_change_before_log == 0:
                    efficiency = (self.stats['ciclos_saltados_sin_cambios'] / self.stats['total_ciclos']) * 100 if self.stats['total_ciclos'] > 0 else 0
                    self.logger.info(f"💤 Página sin cambios detectada ({self.no_change_count} ciclos) - saltando procesamiento")
                    self.logger.info(f"⚡ Eficiencia: {efficiency:.1f}% ciclos saltados ({self.stats['ciclos_saltados_sin_cambios']}/{self.stats['total_ciclos']})")
                    
                # Log debug cada ciclo
                self.logger.debug(f"📄 Página sin cambios (ciclo {self.no_change_count}) - no hay nuevos mensajes")
                return
            else:
                # Hay cambios - resetear contador y actualizar hash
                if self.no_change_count > 0:
                    self.logger.info(f"🔄 Cambios detectados después de {self.no_change_count} ciclos sin actividad")
                    self.no_change_count = 0
                
                self.last_page_hash = current_hash
                self.stats['total_ciclos'] += 1
                self.logger.debug(f"🆕 Página cambió - procesando nuevos mensajes (hash: {current_hash[:8]}...)")
            
            # ⚡ NUEVA OPTIMIZACIÓN: Obtener timestamp del último mensaje procesado desde BD
            last_processed = None
            if hasattr(self.storage_repository, 'get_last_processed_timestamp'):
                last_processed = self.storage_repository.get_last_processed_timestamp()
                self.logger.info(f"📅 Último mensaje conocido en BD: {last_processed}")
            
            # ⚡ USAR MÉTODO OPTIMIZADO que filtra por timestamp ANTES de parsear
            if hasattr(self.whatsapp_connector, 'get_new_messages_optimized'):
                self.logger.info("🚀 USANDO BÚSQUEDA OPTIMIZADA POR TIMESTAMP...")
                mensajes = self.whatsapp_connector.get_new_messages_optimized(last_processed)
            else:
                # Fallback al método anterior si no está disponible
                self.logger.debug("🔄 Fallback a método anterior...")
                timeout = min(self.settings.whatsapp.poll_interval_seconds, 30)
                mensajes = self.whatsapp_connector.wait_for_new_message(timeout)
                if not mensajes:
                    mensajes = self.whatsapp_connector.get_new_messages()
            
            if not mensajes:
                self.logger.debug("ℹ️ No hay mensajes nuevos para procesar")
                return
            
            # ⚡ APLICAR FILTRO INTELIGENTE ANTES DE PROCESAMIENTO PESADO
            mensajes_filtrados = []
            mensajes_bot_ignorados = 0
            
            for mensaje_texto, fecha_mensaje in mensajes:
                if self.message_filter.should_process_message(mensaje_texto, fecha_mensaje):
                    mensajes_filtrados.append((mensaje_texto, fecha_mensaje))
                else:
                    self.stats['mensajes_filtrados'] += 1
                    # Verificar si es mensaje del bot para log específico
                    if self.message_filter._is_bot_message(mensaje_texto.strip()):
                        mensajes_bot_ignorados += 1
                        self.logger.debug(f"🤖 MENSAJE DEL BOT IGNORADO: '{mensaje_texto[:50]}...'")
                    else:
                        self.logger.debug(f"⚡ FILTRADO: '{mensaje_texto[:50]}...' (confirmación/sistema)")
            
            if mensajes_bot_ignorados > 0:
                self.logger.info(f"🤖 {mensajes_bot_ignorados} mensajes del bot ignorados silenciosamente")
            
            if not mensajes_filtrados:
                self.logger.info("ℹ️ Todos los mensajes fueron filtrados (confirmaciones/sistema)")
                return
            
            self.logger.info(f"🚀 PROCESANDO {len(mensajes_filtrados)} MENSAJES (filtrados {len(mensajes)-len(mensajes_filtrados)})")
            
            for i, (mensaje_texto, fecha_mensaje) in enumerate(mensajes_filtrados, 1):
                self.logger.info(f"🔸 PROCESANDO MENSAJE {i}/{len(mensajes_filtrados)}: '{mensaje_texto[:100]}...'")
                self.logger.info(f"   📅 Fecha: {fecha_mensaje.strftime('%Y-%m-%d %H:%M:%S')}")
                
                self.stats['mensajes_procesados'] += 1
                self.stats['ultima_actividad'] = datetime.now()
                
                # ✅ VERIFICAR CACHÉ ANTES DE PROCESAR (OPTIMIZACIÓN CRÍTICA)
                if hasattr(self.storage_repository, 'should_process_message'):
                    should_process = self.storage_repository.should_process_message(mensaje_texto, fecha_mensaje)
                    if not should_process:
                        self.logger.info(f"⚡ MENSAJE SALTADO (ya procesado): '{mensaje_texto[:50]}...'")
                        continue
                
                # Procesar con procesador avanzado
                self.logger.debug(f"🧠 ENVIANDO A PROCESADOR AVANZADO...")
                content = MessageContent(
                    text=mensaje_texto,
                    timestamp=fecha_mensaje,
                    message_type="text"
                )
                
                processing_result = self.advanced_processor.process_message(content)
                self.logger.debug(f"🔍 RESULTADO DEL PROCESADOR: success={processing_result.success}")
                
                if processing_result.gasto:
                    self.logger.info(f"💰 GASTO DETECTADO: ${processing_result.gasto.monto} - {processing_result.gasto.categoria}")
                else:
                    self.logger.debug(f"❌ NO SE DETECTÓ GASTO")
                    if processing_result.errors:
                        self.logger.debug(f"   🚨 Errores: {processing_result.errors}")
                    if processing_result.warnings:
                        self.logger.debug(f"   ⚠️ Warnings: {processing_result.warnings}")
                
                # ✅ CACHEAR RESULTADO INMEDIATAMENTE
                if hasattr(self.storage_repository, 'cache_message_result'):
                    self.storage_repository.cache_message_result(
                        mensaje_texto, fecha_mensaje, processing_result.gasto
                    )
                
                if processing_result.success and processing_result.gasto:
                    # Registrar en storage
                    self.logger.debug(f"💾 GUARDANDO GASTO EN STORAGE...")
                    try:
                        storage_result = self.storage_repository.guardar_gasto(processing_result.gasto)
                        self.logger.debug(f"💾 RESULTADO DEL GUARDADO: {storage_result}")
                        
                        if storage_result:
                            self.stats['gastos_registrados'] += 1
                            self.logger.info(f"✅ GASTO REGISTRADO EXITOSAMENTE!")
                            self.logger.info(f"💰 ${processing_result.gasto.monto} - {processing_result.gasto.categoria}")
                            
                            # Mostrar en consola si no es modo headless
                            if not self.settings.whatsapp.chrome_headless:
                                print(f"💰 {datetime.now().strftime('%H:%M:%S')} - "
                                      f"${processing_result.gasto.monto} en {processing_result.gasto.categoria}")
                        else:
                            self.logger.warning(f"🚫 GASTO RECHAZADO: Posible duplicado detectado")
                        
                    except Exception as e:
                        self.logger.error(f"❌ EXCEPCIÓN guardando gasto: {e}")
                        processing_result.success = False
                        processing_result.errors.append(f"Error guardando: {str(e)}")
                
                # Enviar respuesta automática si está habilitada Y no es mensaje del bot
                try:
                    # Verificar que no sea mensaje del bot antes de responder
                    if not self.message_filter._is_bot_message(mensaje_texto.strip()):
                        self.logger.debug(f"📤 ENVIANDO RESPUESTA AUTOMÁTICA...")
                        self.whatsapp_connector.process_and_respond(mensaje_texto, processing_result)
                        self.logger.debug(f"✅ Respuesta automática enviada")
                    else:
                        self.logger.debug(f"🤖 Mensaje del bot detectado - NO enviando respuesta automática")
                except Exception as e:
                    self.logger.warning(f"⚠️ Error enviando respuesta automática: {e}")
                
                # Manejar comandos especiales (solo si no es mensaje del bot)
                if not self.message_filter._is_bot_message(mensaje_texto.strip()):
                    self.logger.debug(f"🎯 VERIFICANDO COMANDOS ESPECIALES...")
                    self._handle_special_commands(mensaje_texto.lower().strip())
                else:
                    self.logger.debug(f"🤖 Mensaje del bot - OMITIENDO comandos especiales")
                
                self.logger.info(f"✅ MENSAJE {i} PROCESADO COMPLETAMENTE")
                
        except Exception as e:
            self.stats['errores'] += 1
            self.logger.error(f"Error procesando mensajes: {e}")
    
    def _reconnect_whatsapp(self) -> bool:
        """
        Intenta reconectar WhatsApp.
        
        Returns:
            True si la reconexión fue exitosa, False si no
        """
        try:
            self.logger.info("🔄 INICIANDO RECONEXIÓN DE WHATSAPP...")
            
            # Limpiar estado actual
            if self.whatsapp_connector:
                try:
                    self.whatsapp_connector.disconnect()
                except:
                    pass
            
            # Reinicializar conector
            self.whatsapp_connector = WhatsAppEnhancedConnector(self.settings.whatsapp)
            
            # Intentar reconectar
            if self.whatsapp_connector.connect():
                # Configurar respuestas automáticas
                self.whatsapp_connector.enable_auto_responses(
                    self.settings.whatsapp.auto_responses_enabled
                )
                self.whatsapp_connector.response_delay = self.settings.whatsapp.response_delay_seconds
                
                if self.whatsapp_connector.sender:
                    self.whatsapp_connector.sender.typing_delay = self.settings.whatsapp.typing_delay_seconds
                    self.whatsapp_connector.sender.send_delay = self.settings.whatsapp.response_delay_seconds
                
                self.logger.info("✅ RECONEXIÓN EXITOSA!")
                return True
            else:
                self.logger.error("❌ RECONEXIÓN FALLIDA - No se pudo conectar")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ ERROR EN RECONEXIÓN: {e}")
            return False
    
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
        
        # Calcular eficiencia del sistema de hash
        efficiency = (self.stats['ciclos_saltados_sin_cambios'] / self.stats['total_ciclos']) * 100 if self.stats['total_ciclos'] > 0 else 0
        
        self.logger.info(f"📊 Estadísticas: {tiempo_ejecutando} ejecutando, "
                        f"{self.stats['mensajes_procesados']} mensajes procesados, "
                        f"{self.stats['mensajes_filtrados']} filtrados, "
                        f"{self.stats['gastos_registrados']} gastos, "
                        f"{self.stats['errores']} errores")
        
        self.logger.info(f"⚡ Optimización Hash: {efficiency:.1f}% eficiencia "
                        f"({self.stats['ciclos_saltados_sin_cambios']}/{self.stats['total_ciclos']} ciclos saltados)")
        
        if horas > 0:
            rate = self.stats['gastos_registrados'] / horas
            self.logger.info(f"📈 Tasa: {rate:.1f} gastos/hora")
            
        # Mostrar estadísticas del caché si está disponible
        if hasattr(self.storage_repository, 'get_processing_stats'):
            try:
                cache_stats = self.storage_repository.get_processing_stats()
                cache_info = cache_stats.get('cache', {})
                if cache_info:
                    self.logger.info(f"💾 Caché: {cache_info.get('total_cached', 0)} msgs, "
                                   f"{cache_info.get('system_messages', 0)} sistema, "
                                   f"{cache_info.get('expense_messages', 0)} gastos")
            except Exception as e:
                self.logger.debug(f"No se pudieron obtener stats del caché: {e}")
    
    def _cleanup(self) -> None:
        """⚡ Limpieza INSTANTÁNEA de recursos."""
        # 💀 NO CLEANUP - Salir inmediatamente para evitar delays
        # Solo limpiar referencias críticas sin logs ni stats para máxima velocidad
        try:
            if self.whatsapp_connector:
                self.whatsapp_connector.connected = False
                self.whatsapp_connector.driver = None
        except:
            pass
        
        # Sin logs ni stats - exit directo


