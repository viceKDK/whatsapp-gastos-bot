#!/usr/bin/env python3
"""
Ejemplo de Integración WhatsApp

Script de ejemplo para probar la integración completa de WhatsApp.
Este script permite probar la conectividad y funcionalidades básicas.

IMPORTANTE: Este script requiere Chrome instalado y acceso a WhatsApp Web.

Uso:
    python examples/test_whatsapp_integration.py

Variables de entorno opcionales:
    TARGET_CHAT_NAME - Nombre del chat a probar (default: "Test Chat")
    CHROME_HEADLESS - Ejecutar Chrome en modo headless (default: false)
    RESPONSE_DELAY_SECONDS - Delay antes de responder (default: 2.0)
"""

import sys
import time
import signal
from pathlib import Path
from typing import Optional

# Agregar project root al path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings, WhatsAppConfig
from infrastructure.whatsapp import WhatsAppEnhancedConnector
from app.services.message_processor import get_message_processor, MessageContent
from shared.logger import get_logger
from datetime import datetime


class WhatsAppIntegrationTester:
    """
    Tester para la integración de WhatsApp.
    
    Permite probar diferentes aspectos de la integración de forma interactiva.
    """
    
    def __init__(self):
        """Inicializa el tester."""
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        self.connector = None
        self.message_processor = None
        self.running = False
        
        # Configurar signal handler
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Maneja señales de interrupción."""
        self.logger.info(f"Señal {signum} recibida, deteniendo tester...")
        self.stop()
        sys.exit(0)
    
    def setup(self) -> bool:
        """
        Configura los componentes necesarios.
        
        Returns:
            True si la configuración fue exitosa
        """
        try:
            print("🔧 Configurando componentes...")
            
            # Configurar WhatsApp para testing
            self.settings.whatsapp.chrome_headless = False  # Mostrar browser para testing
            self.settings.whatsapp.auto_responses_enabled = True
            self.settings.whatsapp.response_delay_seconds = 1.0  # Más rápido para testing
            
            # Inicializar conector
            self.connector = WhatsAppEnhancedConnector(self.settings.whatsapp)
            
            # Inicializar procesador de mensajes
            self.message_processor = get_message_processor()
            
            print("✅ Componentes configurados correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configurando componentes: {e}")
            print(f"❌ Error: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión a WhatsApp Web.
        
        Returns:
            True si la conexión fue exitosa
        """
        try:
            print("\n🔌 Probando conexión a WhatsApp Web...")
            print(f"📱 Chat objetivo: {self.settings.whatsapp.target_chat_name}")
            print("📲 Escanea el código QR si aparece...")
            
            if self.connector.connect():
                print("✅ Conexión exitosa")
                print(f"📊 Respuestas automáticas: {'habilitadas' if self.connector.auto_responses_enabled else 'deshabilitadas'}")
                
                # Mostrar estadísticas
                stats = self.connector.get_enhanced_stats()
                print(f"📈 Estado: Conectado={stats['connection_stats']['connected']}, "
                      f"Chat seleccionado={stats['connection_stats']['chat_selected']}")
                
                return True
            else:
                print("❌ Error en conexión")
                return False
                
        except Exception as e:
            self.logger.error(f"Error probando conexión: {e}")
            print(f"❌ Error: {e}")
            return False
    
    def test_send_message(self, message: str = None) -> bool:
        """
        Prueba el envío de mensajes.
        
        Args:
            message: Mensaje a enviar (opcional)
            
        Returns:
            True si el envío fue exitoso
        """
        try:
            if not self.connector or not self.connector.sender:
                print("❌ Conector no inicializado")
                return False
            
            test_message = message or "🤖 *Test de Bot de Gastos* \\n\\nEste es un mensaje de prueba del sistema de respuestas automáticas.\\n\\n✅ Si ves este mensaje, la integración está funcionando correctamente."
            
            print(f"\n📤 Enviando mensaje de prueba...")
            
            result = self.connector.send_message(test_message)
            
            if result:
                print("✅ Mensaje enviado correctamente")
                
                # Mostrar estadísticas de envío
                send_stats = self.connector.sender.get_send_stats()
                print(f"📊 Mensajes enviados: {send_stats['messages_sent']}")
                
                return True
            else:
                print("❌ Error enviando mensaje")
                return False
                
        except Exception as e:
            self.logger.error(f"Error enviando mensaje: {e}")
            print(f"❌ Error: {e}")
            return False
    
    def test_message_processing(self) -> bool:
        """
        Prueba el procesamiento de mensajes de ejemplo.
        
        Returns:
            True si el procesamiento fue exitoso
        """
        try:
            print("\\n🧠 Probando procesamiento de mensajes...")
            
            test_messages = [
                "$150 comida almuerzo en restaurante",
                "1500 transporte taxi al aeropuerto",
                "$45.50 entretenimiento cine con amigos",
                "300 super compras semanales",
                "mensaje inválido para probar errores"
            ]
            
            for i, message in enumerate(test_messages, 1):
                print(f"\\n🔄 Test {i}/5: {message}")
                
                # Crear contenido del mensaje
                content = MessageContent(
                    text=message,
                    timestamp=datetime.now(),
                    message_type="text"
                )
                
                # Procesar mensaje
                result = self.message_processor.process_message(content)
                
                if result.success:
                    gasto = result.gasto
                    print(f"✅ Gasto extraído: ${gasto.monto} - {gasto.categoria}")
                    print(f"📊 Confianza: {result.confidence:.1%}")
                    print(f"⚡ Fuente: {result.source}")
                else:
                    print(f"❌ No se pudo procesar")
                    if result.errors:
                        print(f"🚨 Errores: {', '.join(result.errors)}")
                    if result.suggestions:
                        print(f"💡 Sugerencias: {len(result.suggestions)} disponibles")
            
            print("\\n✅ Pruebas de procesamiento completadas")
            return True
            
        except Exception as e:
            self.logger.error(f"Error probando procesamiento: {e}")
            print(f"❌ Error: {e}")
            return False
    
    def test_auto_responses(self) -> None:
        """
        Prueba las respuestas automáticas en modo interactivo.
        
        Escucha mensajes y responde automáticamente.
        """
        try:
            print("\\n🔄 Modo de prueba de respuestas automáticas")
            print("📱 Envía mensajes al chat para probar las respuestas")
            print("🛑 Presiona Ctrl+C para detener")
            print("-" * 50)
            
            self.running = True
            message_count = 0
            
            while self.running:
                # Obtener mensajes nuevos
                mensajes = self.connector.get_new_messages()
                
                if mensajes:
                    for mensaje_texto, fecha_mensaje in mensajes:
                        message_count += 1
                        print(f"\\n📨 Mensaje {message_count}: {mensaje_texto}")
                        
                        # Procesar mensaje
                        content = MessageContent(
                            text=mensaje_texto,
                            timestamp=fecha_mensaje,
                            message_type="text"
                        )
                        
                        processing_result = self.message_processor.process_message(content)
                        
                        # Mostrar resultado
                        if processing_result.success:
                            print(f"✅ Procesado: ${processing_result.gasto.monto} - {processing_result.gasto.categoria}")
                        else:
                            print(f"❌ Error procesando mensaje")
                        
                        # Enviar respuesta automática
                        try:
                            response_sent = self.connector.process_and_respond(mensaje_texto, processing_result)
                            if response_sent:
                                print("📤 Respuesta automática enviada")
                            else:
                                print("⚠️  No se pudo enviar respuesta")
                        except Exception as e:
                            print(f"⚠️  Error enviando respuesta: {e}")
                
                # Esperar antes del próximo poll
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\\n🛑 Detenido por usuario")
        except Exception as e:
            self.logger.error(f"Error en modo automático: {e}")
            print(f"❌ Error: {e}")
    
    def run_interactive_menu(self) -> None:
        """Ejecuta menú interactivo para pruebas."""
        while True:
            print("\\n" + "="*50)
            print("🤖 TESTER DE INTEGRACIÓN WHATSAPP")
            print("="*50)
            print("1. 🔌 Probar conexión")
            print("2. 📤 Enviar mensaje de prueba")  
            print("3. 🧠 Probar procesamiento de mensajes")
            print("4. 🔄 Modo respuestas automáticas")
            print("5. 📊 Mostrar estadísticas")
            print("6. ⚙️  Configurar parámetros")
            print("0. 🚪 Salir")
            print("-" * 50)
            
            try:
                opcion = input("Selecciona una opción: ").strip()
                
                if opcion == "0":
                    break
                elif opcion == "1":
                    self.test_connection()
                elif opcion == "2":
                    self.test_send_message()
                elif opcion == "3":
                    self.test_message_processing()
                elif opcion == "4":
                    self.test_auto_responses()
                elif opcion == "5":
                    self.show_stats()
                elif opcion == "6":
                    self.configure_parameters()
                else:
                    print("❌ Opción no válida")
                    
                input("\\nPresiona Enter para continuar...")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                input("\\nPresiona Enter para continuar...")
    
    def show_stats(self) -> None:
        """Muestra estadísticas del sistema."""
        try:
            print("\\n📊 ESTADÍSTICAS DEL SISTEMA")
            print("-" * 30)
            
            if self.connector:
                stats = self.connector.get_enhanced_stats()
                
                print("🔌 Conexión:")
                print(f"  - Conectado: {stats['connection_stats']['connected']}")
                print(f"  - Chat seleccionado: {stats['connection_stats']['chat_selected']}")
                print(f"  - Último mensaje: {stats['connection_stats']['last_message_time'] or 'N/A'}")
                
                print("\\n🤖 Respuestas automáticas:")
                print(f"  - Habilitadas: {stats['auto_responses_enabled']}")
                print(f"  - Delay: {stats['response_delay']}s")
                
                if 'sender_stats' in stats:
                    sender = stats['sender_stats']
                    print("\\n📤 Envío de mensajes:")
                    print(f"  - Mensajes enviados: {sender['messages_sent']}")
                    print(f"  - Último envío: {sender['last_send_time'] or 'N/A'}")
                    print(f"  - Puede enviar: {sender['can_send']}")
            
            if self.message_processor:
                proc_stats = self.message_processor.get_processing_stats()
                print("\\n🧠 Procesamiento:")
                print(f"  - Mensajes procesados: {proc_stats['processed_messages']}")
                print(f"  - Extracciones exitosas: {proc_stats['successful_extractions']}")
                print(f"  - Tasa de éxito: {proc_stats['success_rate_percent']:.1f}%")
                print(f"  - Uso OCR: {proc_stats['ocr_usage_count']}")
                print(f"  - Uso PDF: {proc_stats['pdf_usage_count']}")
                
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
    
    def configure_parameters(self) -> None:
        """Permite configurar parámetros del sistema."""
        try:
            print("\\n⚙️  CONFIGURACIÓN DE PARÁMETROS")
            print("-" * 30)
            
            print(f"Chat objetivo actual: {self.settings.whatsapp.target_chat_name}")
            new_chat = input("Nuevo chat objetivo (Enter para mantener): ").strip()
            if new_chat:
                self.settings.whatsapp.target_chat_name = new_chat
                print(f"✅ Chat objetivo actualizado: {new_chat}")
            
            print(f"\\nRespuestas automáticas: {'habilitadas' if self.settings.whatsapp.auto_responses_enabled else 'deshabilitadas'}")
            auto_resp = input("Habilitar respuestas automáticas? (s/n, Enter para mantener): ").strip().lower()
            if auto_resp in ['s', 'si', 'y', 'yes']:
                self.settings.whatsapp.auto_responses_enabled = True
                if self.connector:
                    self.connector.enable_auto_responses(True)
                print("✅ Respuestas automáticas habilitadas")
            elif auto_resp in ['n', 'no']:
                self.settings.whatsapp.auto_responses_enabled = False
                if self.connector:
                    self.connector.enable_auto_responses(False)
                print("✅ Respuestas automáticas deshabilitadas")
            
            print(f"\\nDelay de respuesta actual: {self.settings.whatsapp.response_delay_seconds}s")
            new_delay = input("Nuevo delay de respuesta en segundos (Enter para mantener): ").strip()
            if new_delay:
                try:
                    delay = float(new_delay)
                    self.settings.whatsapp.response_delay_seconds = delay
                    if self.connector:
                        self.connector.response_delay = delay
                    print(f"✅ Delay actualizado: {delay}s")
                except ValueError:
                    print("❌ Valor inválido")
                    
        except Exception as e:
            print(f"❌ Error configurando parámetros: {e}")
    
    def stop(self) -> None:
        """Detiene el tester."""
        self.running = False
        if self.connector:
            self.connector.disconnect()
        print("🛑 Tester detenido")
    
    def cleanup(self) -> None:
        """Limpia recursos."""
        try:
            if self.message_processor:
                deleted = self.message_processor.cleanup_temp_files()
                if deleted > 0:
                    print(f"🧹 Eliminados {deleted} archivos temporales")
        except Exception as e:
            self.logger.error(f"Error en cleanup: {e}")


def main():
    """Función principal del tester."""
    print("🤖 Bot de Gastos - Tester de Integración WhatsApp")
    print("=" * 60)
    
    tester = WhatsAppIntegrationTester()
    
    try:
        # Configurar componentes
        if not tester.setup():
            print("❌ Error en configuración inicial")
            return 1
        
        # Ejecutar menú interactivo
        tester.run_interactive_menu()
        
        return 0
        
    except KeyboardInterrupt:
        print("\\n👋 Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        return 1
    finally:
        tester.stop()
        tester.cleanup()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)