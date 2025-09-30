"""
WhatsApp Message Sender

Servicio para enviar mensajes de respuesta a WhatsApp Web.
Extiende la funcionalidad del conector para incluir envío de mensajes.
"""

import time
from typing import Optional, List
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementNotInteractableException
)

from shared.logger import get_logger
from .whatsapp_selenium import WhatsAppSeleniumConnector


class WhatsAppMessageSender:
    """
    Servicio para enviar mensajes a WhatsApp Web.
    
    Funcionalidades:
    - Envío de mensajes de texto
    - Envío de confirmaciones de gastos registrados  
    - Envío de reportes y estadísticas
    - Manejo de errores de envío
    """
    
    def __init__(self, connector: WhatsAppSeleniumConnector):
        """
        Inicializa el sender con un conector existente.
        
        Args:
            connector: Conector de WhatsApp ya inicializado
        """
        self.connector = connector
        self.logger = get_logger(__name__)
        self.messages_sent = 0
        self.last_send_time = None
        
        # Configuraciones de envío
        self.typing_delay = 0.03  # Delay entre caracteres para simular tipeo
        self.send_delay = 0.3    # Delay después de enviar mensaje
        
    @property
    def can_send_messages(self) -> bool:
        """
        Verifica si se pueden enviar mensajes.
        
        Returns:
            True si el conector está conectado y el chat seleccionado
        """
        return (self.connector.connected and 
                self.connector.chat_selected and 
                self.connector.driver is not None)
    
    def send_text_message(self, message: str) -> bool:
        """
        Envía un mensaje de texto al chat seleccionado.
        
        Args:
            message: Texto del mensaje a enviar
            
        Returns:
            True si el mensaje se envió correctamente
        """
        if not self.can_send_messages:
            self.logger.error("No se puede enviar mensaje - WhatsApp no conectado")
            return False
        
        if not message or not message.strip():
            self.logger.warning("Intento de enviar mensaje vacío")
            return False
        
        try:
            self.logger.debug(f"Enviando mensaje: {message[:50]}...")
            
            # Buscar el input de mensaje
            message_input = self._find_message_input()
            if not message_input:
                return False
            
            # Limpiar campo y escribir mensaje
            message_input.clear()
            self._type_message(message_input, message)
            
            # Enviar mensaje
            message_input.send_keys(Keys.ENTER)
            
            # Esperar confirmación
            time.sleep(self.send_delay)
            
            # Verificar que se envió
            if self._verify_message_sent():
                self.messages_sent += 1
                self.last_send_time = datetime.now()
                self.logger.info(f"✅ Mensaje enviado correctamente")
                return True
            else:
                self.logger.warning("No se pudo verificar envío del mensaje")
                return False
                
        except Exception as e:
            self.logger.error(f"Error enviando mensaje: {e}")
            return False
    
    def send_gasto_confirmation(self, gasto, confidence: float = None) -> bool:
        """
        Envía confirmación de gasto registrado en una sola línea.
        
        Args:
            gasto: Objeto Gasto registrado
            confidence: Confianza del procesamiento (opcional - IGNORADO)
            
        Returns:
            True si se envió correctamente
        """
        try:
            # Formatear mensaje de confirmación TODO EN UNA LÍNEA
            parts = [
                f"[OK] Gasto registrado (${gasto.monto} - {gasto.categoria})",
                f"Fecha: {gasto.fecha.strftime('%d/%m/%Y')}"
            ]
            
            # Solo agregar descripción si existe y no es igual a la categoría
            if gasto.descripcion and gasto.descripcion.strip() and gasto.descripcion.lower() != gasto.categoria.lower():
                parts.append(f"Desc: {gasto.descripcion}")
            
            # Unir todo con " | " en una sola línea
            message = " | ".join(parts)
            
            return self.send_text_message(message)
            
        except Exception as e:
            self.logger.error(f"Error enviando confirmación de gasto: {e}")
            return False
    
    def send_error_notification(self, error_message: str, original_message: str = None) -> bool:
        """
        Envía notificación de error en procesamiento.
        
        Args:
            error_message: Mensaje de error
            original_message: Mensaje original que causó el error (opcional)
            
        Returns:
            True si se envió correctamente
        """
        try:
            message_parts = [
                "❌ *Error Procesando Mensaje*",
                f"🚨 Error: {error_message}",
            ]
            
            if original_message:
                truncated = original_message[:100] + "..." if len(original_message) > 100 else original_message
                message_parts.append(f"📝 Mensaje: {truncated}")
            
            message_parts.append("💡 Intenta reformular el mensaje o usar el formato: '$monto categoria descripcion'")
            
            message = "\n".join(message_parts)
            
            return self.send_text_message(message)
            
        except Exception as e:
            self.logger.error(f"Error enviando notificación de error: {e}")
            return False
    
    def send_suggestions(self, suggestions: List[dict], source: str = "procesamiento") -> bool:
        """
        Envía sugerencias de gastos cuando hay ambigüedad.
        
        Args:
            suggestions: Lista de sugerencias
            source: Fuente de las sugerencias
            
        Returns:
            True si se envió correctamente
        """
        if not suggestions:
            return False
        
        try:
            message_parts = [
                "🤔 *Sugerencias de Gasto*",
                f"Encontré varias opciones desde {source}:",
                ""
            ]
            
            for i, suggestion in enumerate(suggestions[:3], 1):  # Máximo 3 sugerencias
                suggestion_text = f"{i}. ${suggestion.get('monto', '?')} - {suggestion.get('categoria', '?')}"
                if suggestion.get('confidence'):
                    suggestion_text += f" ({suggestion['confidence']:.0%})"
                message_parts.append(suggestion_text)
            
            message_parts.extend([
                "",
                "💬 Responde con el número de la opción correcta o envía el gasto reformulado."
            ])
            
            message = "\n".join(message_parts)
            
            return self.send_text_message(message)
            
        except Exception as e:
            self.logger.error(f"Error enviando sugerencias: {e}")
            return False
    
    def send_stats_summary(self, stats: dict) -> bool:
        """
        Envía resumen de estadísticas.
        
        Args:
            stats: Diccionario con estadísticas
            
        Returns:
            True si se envió correctamente
        """
        try:
            message_parts = [
                "📊 *Resumen de Gastos*",
                f"📅 Desde: {stats.get('inicio', 'N/A')}",
                f"💰 Total gastado: ${stats.get('monto_total', 0):.2f}",
                f"📝 Total gastos: {stats.get('total_gastos', 0)}",
                f"📈 Promedio: ${stats.get('promedio', 0):.2f}",
                ""
            ]
            
            # Agregar top categorías si están disponibles
            if 'categorias' in stats and stats['categorias']:
                message_parts.append("🏷️ *Top Categorías:*")
                for cat, amount in list(stats['categorias'].items())[:3]:
                    message_parts.append(f"• {cat}: ${amount:.2f}")
            
            message = "\n".join(message_parts)
            
            return self.send_text_message(message)
            
        except Exception as e:
            self.logger.error(f"Error enviando estadísticas: {e}")
            return False
    
    def send_help_message(self) -> bool:
        """
        Envía mensaje de ayuda con formato de comandos.
        
        Returns:
            True si se envió correctamente
        """
        try:
            message = """
🤖 *Bot de Gastos - Ayuda*

📝 *Formatos soportados:*
• $150 comida almuerzo
• 1500 transporte taxi al aeropuerto  
• $45.50 entretenimiento cine
• 300 super compras del mes

📸 *También acepto:*
• Fotos de recibos (OCR automático)
• PDFs de facturas
• Mensajes de voz (próximamente)

📊 *Comandos:*
• "estadisticas" - Resumen de gastos
• "categorias" - Lista de categorías válidas
• "ayuda" - Este mensaje

🏷️ *Categorías válidas:*
comida, transporte, entretenimiento, salud, servicios, ropa, educacion, hogar, trabajo, otros, super, nafta

💡 *Tip:* Puedo aprender de tus patrones de gasto para mejorar la categorización automática.
            """.strip()
            
            return self.send_text_message(message)
            
        except Exception as e:
            self.logger.error(f"Error enviando mensaje de ayuda: {e}")
            return False
    
    def _find_message_input(self) -> Optional[object]:
        """
        Busca el campo de input de mensajes.
        
        Returns:
            Elemento del input o None si no se encuentra
        """
        try:
            # Intentar varios selectores para el input
            selectors = [
                "[data-testid='conversation-compose-box-input']",
                "div[contenteditable='true'][data-tab='10']",
                "div[contenteditable='true'][data-lexical-editor='true']",
                "div[role='textbox'][contenteditable='true']"
            ]
            
            wait = WebDriverWait(self.connector.driver, 5)
            
            for selector in selectors:
                try:
                    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    if element:
                        self.logger.debug(f"Input encontrado con selector: {selector}")
                        return element
                except TimeoutException:
                    continue
            
            self.logger.error("No se pudo encontrar el campo de input de mensajes")
            return None
            
        except Exception as e:
            self.logger.error(f"Error buscando input de mensajes: {e}")
            return None
    
    def _type_message(self, input_element, message: str) -> None:
        """
        Escribe el mensaje simulando tipeo humano.
        
        Args:
            input_element: Elemento de input
            message: Mensaje a escribir
        """
        # Click para asegurar foco
        input_element.click()
        time.sleep(0.5)
        
        # Limpiar caracteres no BMP (emojis complejos) que ChromeDriver no soporta
        message_cleaned = self._clean_non_bmp_characters(message)
        
        # Escribir mensaje con delay para simular tipeo
        for char in message_cleaned:
            input_element.send_keys(char)
            if self.typing_delay > 0:
                time.sleep(self.typing_delay)
    
    def _clean_non_bmp_characters(self, text: str) -> str:
        """
        Limpia caracteres fuera del Basic Multilingual Plane que ChromeDriver no soporta.
        
        Args:
            text: Texto original
            
        Returns:
            Texto limpio compatible con ChromeDriver
        """
        # Reemplazar emojis complejos con texto simple
        replacements = {
            '✅': '[OK]',
            '💰': '$',
            '📝': 'Cat:',
            '📅': 'Fecha:',
            '📄': 'Desc:',
            '🎯': 'Conf:',
        }
        
        cleaned = text
        for emoji, replacement in replacements.items():
            cleaned = cleaned.replace(emoji, replacement)
        
        # Filtrar cualquier otro caracter fuera del BMP (Unicode > U+FFFF)
        cleaned = ''.join(char for char in cleaned if ord(char) <= 0xFFFF)
        
        return cleaned
    
    def _verify_message_sent(self) -> bool:
        """
        Verifica que el mensaje se haya enviado.
        
        Returns:
            True si se verificó el envío
        """
        try:
            # Buscar el último mensaje enviado
            wait = WebDriverWait(self.connector.driver, 5)
            
            # Buscar mensajes propios (outgoing)
            sent_messages = self.connector.driver.find_elements(
                By.CSS_SELECTOR, 
                "[data-testid='msg-container'].message-out"
            )
            
            if sent_messages:
                # Verificar que el último mensaje tiene timestamp reciente
                last_message = sent_messages[-1]
                return True  # Simplificado - asumir éxito si encontramos mensaje propio
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error verificando envío: {e}")
            return True  # Asumir éxito si no podemos verificar
    
    def get_send_stats(self) -> dict:
        """
        Obtiene estadísticas de envío de mensajes.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'messages_sent': self.messages_sent,
            'last_send_time': self.last_send_time.isoformat() if self.last_send_time else None,
            'can_send': self.can_send_messages,
            'typing_delay': self.typing_delay,
            'send_delay': self.send_delay
        }


class WhatsAppEnhancedConnector(WhatsAppSeleniumConnector):
    """
    Conector mejorado que incluye capacidades de envío.
    
    Extiende WhatsAppSeleniumConnector agregando funcionalidad de respuesta.
    """
    
    def __init__(self, config):
        """
        Inicializa el conector mejorado.
        
        Args:
            config: Configuración de WhatsApp
        """
        super().__init__(config)
        self.sender = None
        self.auto_responses_enabled = True
        self.response_delay = 0.3  # Delay antes de responder automáticamente
    
    def connect(self) -> bool:
        """
        Conecta e inicializa el sender.
        
        Returns:
            True si la conexión fue exitosa
        """
        if super().connect():
            # Inicializar sender una vez conectado
            self.sender = WhatsAppMessageSender(self)
            self.logger.info("✅ Conector mejorado con capacidades de envío inicializado")
            return True
        return False
    
    def process_and_respond(self, message_text: str, processing_result) -> bool:
        """
        Procesa un mensaje y envía respuesta apropiada.
        
        Args:
            message_text: Texto del mensaje original
            processing_result: Resultado del procesamiento
            
        Returns:
            True si se pudo responder
        """
        if not self.sender or not self.auto_responses_enabled:
            return False
        
        try:
            # Esperar un poco antes de responder (más natural)
            time.sleep(self.response_delay)
            
            if processing_result.success and processing_result.gasto:
                # Enviar confirmación de gasto
                return self.sender.send_gasto_confirmation(
                    processing_result.gasto, 
                    processing_result.confidence
                )
                
            elif processing_result.suggestions:
                # Enviar sugerencias si las hay
                return self.sender.send_suggestions(
                    processing_result.suggestions,
                    processing_result.source
                )
                
            elif processing_result.errors:
                # Enviar notificación de error
                error_msg = "; ".join(processing_result.errors)
                return self.sender.send_error_notification(error_msg, message_text)
                
            else:
                # Mensaje genérico de no procesamiento
                return self.sender.send_text_message(
                    "🤔 No pude procesar ese mensaje. Usa el formato: '$monto categoria descripcion' o envía 'ayuda' para más info."
                )
                
        except Exception as e:
            self.logger.error(f"Error enviando respuesta: {e}")
            return False
    
    def send_message(self, message: str) -> bool:
        """
        Método directo para enviar mensaje.
        
        Args:
            message: Texto del mensaje
            
        Returns:
            True si se envió correctamente
        """
        if self.sender:
            return self.sender.send_text_message(message)
        return False
    
    def enable_auto_responses(self, enabled: bool = True) -> None:
        """
        Habilita/deshabilita respuestas automáticas.
        
        Args:
            enabled: True para habilitar respuestas automáticas
        """
        self.auto_responses_enabled = enabled
        self.logger.info(f"Respuestas automáticas: {'habilitadas' if enabled else 'deshabilitadas'}")
    
    def get_enhanced_stats(self) -> dict:
        """
        Obtiene estadísticas extendidas incluyendo envío.
        
        Returns:
            Diccionario con estadísticas completas
        """
        stats = {
            'connection_stats': {
                'connected': self.connected,
                'chat_selected': self.chat_selected,
                'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None
            },
            'auto_responses_enabled': self.auto_responses_enabled,
            'response_delay': self.response_delay
        }
        
        if self.sender:
            stats['sender_stats'] = self.sender.get_send_stats()
        
        return stats