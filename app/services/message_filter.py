"""
Filtro de Mensajes Inteligente

Sistema de filtros para omitir mensajes de confirmación, sistema y otros 
mensajes que no requieren procesamiento adicional.
"""

import re
from typing import List, Set, Optional, Tuple
from datetime import datetime

from shared.logger import get_logger


logger = get_logger(__name__)


class MessageFilter:
    """⚡ Filtro inteligente de mensajes (20% mejora en eficiencia)."""
    
    def __init__(self):
        # Patrones de mensajes a omitir (confirmaciones y sistema)
        self.confirmation_patterns = [
            # Confirmaciones de gastos registrados
            r"✅\s*gasto\s+registrado",
            r"💰\s*registrado",
            r"guardado\s+exitosamente",
            r"gasto\s+guardado",
            r"registro\s+exitoso",
            r"se\s+guardó\s+el\s+gasto",
            
            # Mensajes de error o no procesamiento
            r"❌\s*no\s+puedo\s+procesar",
            r"no\s+se\s+pudo\s+procesar",
            r"error\s+procesando",
            r"mensaje\s+no\s+válido",
            r"formato\s+incorrecto",
            
            # Mensajes de ayuda y sistema
            r"🤖.*ayuda",
            r"comandos\s+disponibles",
            r"usa\s+el\s+formato",
            r"ejemplo\s*:",
            
            # Mensajes automaticos del bot
            r"🔄\s*procesando",
            r"⏳\s*espera",
            r"🎯\s*analizando",
        ]
        
        # Frases exactas a omitir (case insensitive) - EXPANDIDAS PARA INCLUIR MENSAJES DEL BOT
        self.exact_phrases = {
            # Confirmaciones de gasto
            "gasto registrado",
            "registrado exitosamente", 
            "guardado correctamente",
            
            # Mensajes de error del bot
            "no puedo procesar ese mensaje",
            "formato incorrecto",
            "no se pudo procesar",
            "error procesando",
            
            # Mensajes de ayuda (removidos "ayuda", "help", "comandos" - son comandos válidos del usuario)
            "usa el formato",
            
            # Estados del bot
            "procesando...",
            "analizando mensaje...",
            "guardando...",
            
            # Fragmentos típicos de confirmaciones multilinea
            "fecha:",
            "desc:",
            "descripción:",
            "conf:",
            "confianza:",
            "($500 - supermercado)",  # Patrón específico visto en logs
            "fecha: fecha:",           # Duplicación vista en logs
            "desc: descripción:",      # Duplicación vista en logs
            "conf: confianza: 90%",    # Patrón específico visto en logs
        }
        
        # Palabras clave de confirmación
        self.confirmation_keywords = {
            "registrado", "guardado", "exitosamente", "correctamente",
            "confirmado", "procesado", "completado", "finalizado"
        }
        
        # Emojis de confirmación/sistema
        self.system_emojis = {
            "✅", "❌", "🤖", "🔄", "⏳", "🎯", "💾", "📊", "⚡", "🚀"
        }
        
        # Compilar patrones regex una sola vez para mejor rendimiento
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE)
            for pattern in self.confirmation_patterns
        ]
        
        # Estadísticas
        self.total_filtered = 0
        self.confirmation_filtered = 0
        self.system_filtered = 0
        self.error_filtered = 0
        
        logger.info(f"MessageFilter inicializado - {len(self.compiled_patterns)} patrones cargados")
    
    def should_process_message(self, text: str, timestamp: Optional[datetime] = None) -> bool:
        """
        ⚡ Determina si un mensaje debe ser procesado.
        
        Args:
            text: Texto del mensaje
            timestamp: Timestamp del mensaje (opcional)
            
        Returns:
            True si el mensaje debe procesarse, False si debe omitirse
        """
        logger.info(f"🔍 FILTRO DEBUG: Analizando mensaje '{text[:50]}...'")
        
        if not text or not text.strip():
            logger.info("❌ FILTRO: Mensaje vacío - RECHAZADO")
            return False
        
        # FILTRO PRIORITARIO: Ignorar mensajes del bot
        # ⚡ REGLA SIMPLE: Si empieza con [ o "No", es mensaje del bot - RECHAZAR INMEDIATAMENTE
        if text.strip().startswith('[') or text.strip().startswith('No'):
            patron = "con [" if text.strip().startswith('[') else "con 'No'"
            logger.info(f"🤖 FILTRO: Mensaje empieza {patron} - IGNORADO INMEDIATAMENTE")
            return False
            
        if self._is_bot_message(text.strip()):
            logger.info(f"🤖 FILTRO: Mensaje del bot detectado - IGNORADO")
            return False
        
        # Normalizar texto
        normalized_text = text.strip().lower()
        logger.info(f"🧹 FILTRO: Texto normalizado: '{normalized_text[:50]}...'")
        
        # ⚡ FILTRO RÁPIDO: Si contiene números + descripción, probablemente es gasto
        parece_gasto = self._looks_like_expense(normalized_text)
        logger.info(f"💰 FILTRO: ¿Parece gasto? {parece_gasto}")
        if parece_gasto:
            logger.info("✅ FILTRO: Parece gasto - PROCESANDO INMEDIATAMENTE")
            return True  # Procesar inmediatamente si parece gasto
        
        # Filtro 1: Mensajes muy cortos o solo emojis/espacios
        if len(normalized_text) < 3:
            logger.info(f"❌ FILTRO 1: Muy corto ({len(normalized_text)} chars) - RECHAZADO")
            self._record_filter("too_short")
            return False
        
        # Filtro 2: Solo contiene emojis de sistema
        solo_emojis = self._is_only_system_emojis(text)
        if solo_emojis:
            logger.info("❌ FILTRO 2: Solo emojis de sistema - RECHAZADO")
            self._record_filter("system_emojis") 
            return False
        
        # Filtro 3: Frases exactas a omitir
        if normalized_text in self.exact_phrases:
            logger.info(f"❌ FILTRO 3: Frase exacta filtrada '{normalized_text}' - RECHAZADO")
            self._record_filter("exact_phrase")
            return False
        
        # Filtro 4: Patrones de confirmación con regex
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(normalized_text):
                logger.info(f"❌ FILTRO 4: Patrón confirmación #{i} coincidió - RECHAZADO")
                self._record_filter("confirmation_pattern")
                return False
        
        # Filtro 5: Alto contenido de palabras de confirmación (solo para mensajes cortos SIN números)
        words = normalized_text.split()
        tiene_numeros = any(char.isdigit() for char in normalized_text)
        if not tiene_numeros:  # Solo si NO hay números
            confirmation_count = sum(1 for word in words if word in self.confirmation_keywords)
            
            if len(words) <= 4 and confirmation_count >= len(words) * 0.5:
                logger.info(f"❌ FILTRO 5: Alto ratio confirmación ({confirmation_count}/{len(words)}) - RECHAZADO")
                self._record_filter("high_confirmation_ratio")
                return False
        
        # Filtro 6: Mensajes que empiezan con emoji de sistema + confirmación
        inicia_emoji_sistema = self._starts_with_system_emoji(text)
        contiene_confirmacion = self._contains_confirmation(normalized_text)
        if inicia_emoji_sistema and contiene_confirmacion:
            logger.info("❌ FILTRO 6: Emoji sistema + confirmación - RECHAZADO")
            self._record_filter("system_confirmation")
            return False
        
        # Filtro 7: Mensajes repetidos típicos del bot
        es_patron_bot = self._is_bot_response_pattern(normalized_text)
        if es_patron_bot:
            logger.info("❌ FILTRO 7: Patrón respuesta bot - RECHAZADO")
            self._record_filter("bot_response")
            return False
        
        # Si pasa todos los filtros, debe procesarse
        logger.info("✅ FILTRO: Mensaje APROBADO para procesamiento")
        return True
    
    def _looks_like_expense(self, text: str) -> bool:
        """⚡ Detección rápida si parece un gasto (número + descripción)."""
        import re
        
        # Patrones rápidos para gastos - AMBOS FORMATOS
        expense_patterns = [
            r'\d+\s+\w+',                     # "300 nafta" (cantidad + categoría)
            r'\w+\s+\d+',                     # "nafta 300" (categoría + cantidad) 
            r'\$\s*\d+',                      # "$500"
            r'gasto:?\s*\d+',                 # "gasto: 100"
            r'(compré?|gasté|pagué)\s+\d+',   # "compré 200"
            r'\d+\s+(en|de|por)\s+\w+',       # "100 en comida"
        ]
        
        for i, pattern in enumerate(expense_patterns):
            if re.search(pattern, text):
                logger.info(f"💰 DETECCIÓN GASTO: Patrón #{i} '{pattern}' coincidió en '{text[:30]}...'")
                return True
        
        logger.info(f"❌ DETECCIÓN GASTO: Ningún patrón coincidió en '{text[:30]}...'")
        return False
    
    def _is_bot_message(self, text: str) -> bool:
        """Detecta si un mensaje fue enviado por el bot mismo."""
        import re
        
        # Patrones de mensajes típicos del bot
        bot_message_patterns = [
            r'^\[OK\]',                                    # Mensajes de confirmación [OK]
            r'^\[ERROR\]',                                # Mensajes de error [ERROR]  
            r'^\[INFO\]',                                 # Mensajes informativos [INFO]
            r'^\[.*\].*sistema',                          # Cualquier mensaje de sistema con [INFO], etc.
            r'^gasto registrado',                         # Confirmaciones de gasto
            r'^no pude procesar',                         # Mensajes de error de procesamiento
            r'^no puedo procesar',                        # Variante de error de procesamiento
            r'^usa el formato:',                          # Mensajes de ayuda de formato
            r'^formato correcto:',                        # Mensajes de formato
            r'^\$\d+.*registrado',                        # "$500 registrado..."
            r'^fecha:.*desc:',                            # Partes de confirmación multilinea
            r'^conf: confianza:',                         # Mensajes de confianza del bot
            r'registrado.*\(\$\d+.*\)',                   # "registrado ($500 - categoria)"
        ]
        
        text_lower = text.lower()
        
        for pattern in bot_message_patterns:
            if re.search(pattern, text_lower):
                logger.info(f"🤖 PATRÓN BOT DETECTADO: '{pattern}' en '{text[:30]}...'")
                return True
        
        return False
    
    def _is_only_system_emojis(self, text: str) -> bool:
        """Verifica si el texto contiene solo emojis de sistema."""
        # Remover espacios y verificar si todos los caracteres son emojis de sistema
        chars = [c for c in text if not c.isspace()]
        if not chars:
            return True
        
        # Encontrar caracteres que son emojis (usan más de 1 byte en UTF-8)
        emoji_chars = [c for c in chars if len(c.encode('utf-8')) > 1]
        
        # Si no hay emojis, no es "solo emojis de sistema"
        if not emoji_chars:
            return False
            
        # Si hay emojis, verificar que TODOS sean emojis de sistema
        return all(c in self.system_emojis for c in emoji_chars)
    
    def _starts_with_system_emoji(self, text: str) -> bool:
        """Verifica si el texto empieza con emoji de sistema."""
        if not text:
            return False
        
        first_char = text[0]
        return first_char in self.system_emojis
    
    def _contains_confirmation(self, normalized_text: str) -> bool:
        """Verifica si contiene palabras de confirmación."""
        return any(keyword in normalized_text for keyword in self.confirmation_keywords)
    
    def _is_bot_response_pattern(self, normalized_text: str) -> bool:
        """Detecta patrones típicos de respuestas automáticas del bot."""
        bot_patterns = [
            r"^(procesando|analizando|guardando|registrando)",
            r"(por favor|favor)\s+(espera|aguarda)",
            r"^(el\s+)?(gasto|registro)\s+(fue|está|se)\s+",
            r"^gracias\s+por\s+",
            r"^entendido[.,]?\s*$",
            r"^recibido[.,]?\s*$",
        ]
        
        for pattern in bot_patterns:
            if re.search(pattern, normalized_text):
                return True
        
        return False
    
    def _record_filter(self, filter_type: str):
        """Registra estadística de filtrado."""
        self.total_filtered += 1
        
        if filter_type in ["confirmation_pattern", "exact_phrase", "high_confirmation_ratio", "system_confirmation"]:
            self.confirmation_filtered += 1
        elif filter_type in ["system_emojis", "bot_response"]:
            self.system_filtered += 1
        elif "error" in filter_type.lower():
            self.error_filtered += 1
        
        logger.debug(f"Mensaje filtrado - Tipo: {filter_type}, Total filtrados: {self.total_filtered}")
    
    def get_filter_stats(self) -> dict:
        """Obtiene estadísticas de filtrado."""
        return {
            'total_filtered': self.total_filtered,
            'confirmation_filtered': self.confirmation_filtered,
            'system_filtered': self.system_filtered,
            'error_filtered': self.error_filtered,
            'patterns_loaded': len(self.compiled_patterns),
            'exact_phrases_loaded': len(self.exact_phrases)
        }
    
    def add_custom_pattern(self, pattern: str, pattern_type: str = "custom"):
        """
        Agrega un patrón personalizado de filtrado.
        
        Args:
            pattern: Patrón regex o texto exacto
            pattern_type: Tipo de patrón ("regex" o "exact")
        """
        if pattern_type == "regex":
            try:
                compiled = re.compile(pattern, re.IGNORECASE | re.UNICODE)
                self.compiled_patterns.append(compiled)
                logger.info(f"Patrón regex personalizado agregado: {pattern}")
            except re.error as e:
                logger.error(f"Error compilando patrón regex '{pattern}': {e}")
        else:
            # Agregar como frase exacta
            self.exact_phrases.add(pattern.lower())
            logger.info(f"Frase exacta personalizada agregada: {pattern}")
    
    def reset_stats(self):
        """Resetea las estadísticas de filtrado."""
        self.total_filtered = 0
        self.confirmation_filtered = 0
        self.system_filtered = 0 
        self.error_filtered = 0
        logger.info("Estadísticas de filtrado reseteadas")


class SmartMessageQueue:
    """Cola inteligente que pre-filtra mensajes para optimizar procesamiento."""
    
    def __init__(self, message_filter: MessageFilter):
        self.filter = message_filter
        self.pending_messages = []
        self.processed_count = 0
        self.skipped_count = 0
        
    def add_messages(self, messages: List[Tuple[str, datetime]]) -> int:
        """
        Agrega mensajes a la cola aplicando filtros.
        
        Args:
            messages: Lista de tuplas (texto, timestamp)
            
        Returns:
            Número de mensajes que pasaron el filtro
        """
        filtered_count = 0
        
        for text, timestamp in messages:
            if self.filter.should_process_message(text, timestamp):
                self.pending_messages.append((text, timestamp))
                filtered_count += 1
            else:
                self.skipped_count += 1
                logger.debug(f"Mensaje saltado por filtro: '{text[:50]}...'")
        
        logger.info(f"Cola actualizada: {filtered_count} mensajes agregados, {self.skipped_count} saltados")
        return filtered_count
    
    def get_next_message(self) -> Optional[Tuple[str, datetime]]:
        """Obtiene el siguiente mensaje a procesar."""
        if self.pending_messages:
            message = self.pending_messages.pop(0)
            self.processed_count += 1
            return message
        return None
    
    def has_pending(self) -> bool:
        """Verifica si hay mensajes pendientes."""
        return len(self.pending_messages) > 0
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas de la cola."""
        return {
            'pending_messages': len(self.pending_messages),
            'processed_count': self.processed_count,
            'skipped_count': self.skipped_count,
            'filter_stats': self.filter.get_filter_stats()
        }


# Instancia global del filtro
_message_filter_instance: Optional[MessageFilter] = None

def get_message_filter() -> MessageFilter:
    """Obtiene instancia singleton del filtro de mensajes."""
    global _message_filter_instance
    if _message_filter_instance is None:
        _message_filter_instance = MessageFilter()
    return _message_filter_instance


def create_smart_queue() -> SmartMessageQueue:
    """Crea una cola inteligente con filtro."""
    filter_instance = get_message_filter()
    return SmartMessageQueue(filter_instance)