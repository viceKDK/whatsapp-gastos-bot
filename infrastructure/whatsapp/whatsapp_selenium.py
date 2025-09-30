"""
WhatsApp Selenium Integration

Implementación real del conector WhatsApp usando Selenium WebDriver.
Automatiza WhatsApp Web para leer mensajes de un chat específico.
"""

import time
import re
import subprocess
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)

from shared.logger import get_logger
from .ultra_fast_extractor import UltraFastExtractor


class MessageData:
    """⚡ Estructura de datos optimizada con lazy loading (65% mejora esperada)."""
    
    def __init__(self, element=None):
        self.timestamp = None
        self._text = None
        self._text_loaded = False
        self._element = element
        self._sender = None
        self._sender_loaded = False
        self.logger = get_logger(__name__)
    
    @property
    def text(self) -> str:
        """Lazy loading del texto del mensaje (solo cuando se necesita)."""
        if not self._text_loaded and self._element:
            self._text = self._extract_text_optimized(self._element)
            self._text_loaded = True
        return self._text or ""
    
    @property 
    def sender(self) -> str:
        """Lazy loading del remitente (solo cuando se necesita)."""
        if not self._sender_loaded and self._element:
            self._sender = self._extract_sender_optimized(self._element)
            self._sender_loaded = True
        return self._sender or ""
    
    def _extract_text_optimized(self, element) -> str:
        """Extracción optimizada de texto usando técnicas avanzadas."""
        try:
            # ⚡ MÉTODO 1: innerHTML + regex (más rápido que .text para elementos complejos)
            html = element.get_attribute('innerHTML')
            if html:
                # DEBUG: Ver qué HTML estamos procesando
                html_preview = html[:200] if html else "No HTML"
                
                # Regex optimizado para extraer texto principal de WhatsApp - CORREGIDO
                text_patterns = [
                    # 🎯 PATRONES ESPECÍFICOS PARA CONTENIDO DE MENSAJE (NO METADATOS)
                    r'<span[^>]*class="[^"]*selectable-text[^"]*"[^>]*data-a11y-announcement-message="[^"]*">([^<]+)</span>',  # Mensaje específico
                    r'<div[^>]*class="[^"]*copyable-text[^"]*"[^>]*data-a11y-announcement-message="[^"]*">([^<]+)</div>',      # Texto copiable con anuncio
                    r'<span[^>]*class="[^"]*selectable-text[^"]*"[^>]*>(?!(?:\d{1,2}:\d{2}|\d{1,2}/\d{1,2}))([^<]{5,})</span>',  # Texto seleccionable NO timestamps
                    r'<div[^>]*class="[^"]*copyable-text[^"]*"[^>]*>(?!(?:\d{1,2}:\d{2}|\d{1,2}/\d{1,2}))([^<]{5,})</div>',      # Texto copiable NO timestamps
                    
                    # 🔄 PATRONES PARA CONTENIDO ESPECÍFICO DE GASTOS
                    r'<span[^>]*dir="auto"[^>]*>(?!(?:\d{1,2}:\d{2}|\d{1,2}/\d{1,2}))([^<]*\d+[^<]*[a-zA-ZáéíóúñÁÉÍÓÚÑ]+[^<]*)</span>',  # Números + texto (gastos)
                    r'<span[^>]*dir="auto"[^>]*>(?!(?:\d{1,2}:\d{2}|\d{1,2}/\d{1,2}))([a-zA-ZáéíóúñÁÉÍÓÚÑ][^<]{5,})</span>',            # Texto largo sin timestamps
                    
                    # 🆘 FALLBACKS SEGUROS - EVITAR TIMESTAMPS
                    r'>(?!(?:\d{1,2}:\d{2}|\d{1,2}/\d{1,2}|\w{3}, \w{3}))([^<]*\d+[^<]*[a-zA-ZáéíóúñÁÉÍÓÚÑ]+[^<]{3,})<',  # Patrón gasto evitando timestamps
                    r'>(?!(?:\d{1,2}:\d{2}|\d{1,2}/\d{1,2}|\w{3}, \w{3}))([a-zA-ZáéíóúñÁÉÍÓÚÑ][^<]{8,})<',                # Texto largo evitando timestamps
                ]
                
                for i, pattern in enumerate(text_patterns):
                    matches = re.findall(pattern, html)
                    if matches:
                        # Tomar el match más largo
                        extracted = max(matches, key=len).strip()
                        # DEBUG: Ver qué extrajimos
                        self.logger.info(f"🔍 TEXTO EXTRAIDO (método regex {i+1}): '{extracted}' de HTML: '{html_preview}...'")
                        
                        # 🚨 VERIFICACIÓN: Si el texto completo del elemento empieza con [, devolver eso en lugar del extracto
                        full_text = element.text.strip() if element.text else ""
                        if full_text and full_text.startswith('['):
                            self.logger.info(f"🤖 TEXTO COMPLETO empieza con [, devolviendo mensaje completo: '{full_text[:100]}...'")
                            return full_text
                        
                        return extracted
            
            # ⚡ MÉTODO 2: Buscar elementos específicos de texto dentro del elemento mensaje
            try:
                # Buscar elementos de texto específicos dentro del mensaje
                text_elements = element.find_elements(By.CSS_SELECTOR, 
                    "span[dir='auto'], div[dir='auto'], .selectable-text, .copyable-text")
                
                if text_elements:
                    self.logger.info(f"🔍 ENCONTRADOS {len(text_elements)} elementos de texto internos")
                    
                    # 🚨 VERIFICACIÓN TEMPRANA: Si el elemento principal empieza con [, devolver texto completo
                    full_text = element.text.strip() if element.text else ""
                    if full_text and full_text.startswith('['):
                        self.logger.info(f"🤖 ELEMENTO PRINCIPAL empieza con [, devolviendo mensaje completo: '{full_text[:100]}...'")
                        return full_text
                    
                    for i, text_elem in enumerate(text_elements):
                        elem_text = text_elem.text.strip() if text_elem.text else ""
                        if elem_text and len(elem_text) > 4:
                            # Verificar si NO es timestamp
                            if not re.match(r'^\d{1,2}:\d{2}$', elem_text):
                                self.logger.info(f"🎯 ELEMENTO TEXTO #{i}: '{elem_text}'")
                                if self._looks_like_message_content(elem_text):
                                    return elem_text
            except Exception as e:
                self.logger.debug(f"Error buscando elementos internos: {e}")
            
            # ⚡ MÉTODO 3: Fallback con text completo
            text = element.text.strip() if element.text else ""
            if text:
                # DEBUG: Ver qué texto básico tenemos
                self.logger.info(f"🔍 TEXTO BASICO COMPLETO ({len(text)} chars): '{text[:100]}...'")
                
                # 🚨 VERIFICACIÓN CRÍTICA: Si empieza con [OK] (o [ en general), devolver mensaje completo
                # Esto evita fragmentar mensajes del bot como "[OK] Gasto registrado ($500 - super)"
                if text.startswith('['):
                    self.logger.info(f"🤖 MENSAJE DEL BOT DETECTADO (empieza con [): '{text[:100]}...'")
                    self.logger.info(f"🔄 DEVOLVIENDO MENSAJE COMPLETO sin fragmentar")
                    return text
                
                # Filtrar líneas y tomar la MÁS RELEVANTE (no solo la más larga)
                lines = [line.strip() for line in text.split('\n') 
                        if line.strip() and len(line.strip()) > 3]
                        
                self.logger.info(f"📋 ENCONTRADAS {len(lines)} LÍNEAS: {[line[:30] for line in lines]}")
                        
                if lines:
                    # 🎯 PRIORIZAR líneas que parecen mensajes de gastos
                    expense_lines = [line for line in lines if self._looks_like_expense_line(line)]
                    if expense_lines:
                        result = max(expense_lines, key=len)  # La línea de gasto más larga
                        self.logger.info(f"🎯 LINEA DE GASTO DETECTADA: '{result}' de {len(lines)} líneas totales")
                        return result
                    
                    # 🔄 Si no hay líneas de gastos, usar líneas con texto sustantivo
                    content_lines = [line for line in lines if self._looks_like_message_content(line)]
                    if content_lines:
                        result = max(content_lines, key=len)
                        self.logger.info(f"🔍 LINEA DE CONTENIDO: '{result}' de {len(lines)} líneas")
                        return result
                    
                    # 🔄 FALLBACK: la línea más larga
                    result = max(lines, key=len)
                    self.logger.info(f"🔄 LINEA MAS LARGA: '{result}' de {len(lines)} líneas")
                    return result
                    
                # Si no hay líneas válidas, devolver texto completo
                self.logger.info(f"🔍 DEVOLVIENDO TEXTO COMPLETO: '{text}'")
                return text
            
            self.logger.warning(f"⚠️ NO SE PUDO EXTRAER TEXTO - HTML: {html[:100] if html else 'No HTML'}")
            return ""
            
        except Exception as e:
            # ⚡ MÉTODO 3: Fallback básico
            self.logger.error(f"❌ ERROR en extracción: {e}")
            try:
                fallback = element.text.strip() if element.text else ""
                self.logger.info(f"🔄 FALLBACK: '{fallback}'")
                return fallback
            except:
                return ""
    
    def _looks_like_expense_line(self, line: str) -> bool:
        """Determina si una línea parece contener información de gasto."""
        import re
        
        # PRIMERO: Filtrar timestamps y metadatos comunes
        timestamp_patterns = [
            r'^\d{1,2}:\d{2}$',                    # Solo hora "23:27"
            r'^\d{1,2}/\d{1,2}(/\d{4})?$',        # Solo fecha "8/7" o "8/7/2025"
            r'^(hoy|ayer|today|yesterday)$',       # Indicadores temporales
            r'^\w{3},?\s+\w{3}$',                  # "Mié, Mar" etc
            r'^(mensaje|message|chat)$',           # Palabras de interfaz
        ]
        
        line_clean = line.strip()
        
        # Si es muy corto o coincide con timestamp, NO es gasto
        if len(line_clean) < 4:
            return False
            
        for pattern in timestamp_patterns:
            if re.match(pattern, line_clean, re.IGNORECASE):
                return False
        
        # SEGUNDO: Patrones que SÍ indican gastos
        expense_patterns = [
            r'\d+.*[a-zA-ZáéíóúñÁÉÍÓÚÑ]{3,}',                    # Número seguido de texto (250 carnicería)
            r'[a-zA-ZáéíóúñÁÉÍÓÚÑ]+.*\d+',                     # Texto seguido de número (Vice: 250)
            r'\b(gast[éoó]|compr[éé]|pagu[éé])\b',             # Verbos de gasto
            r'\b(vice|usuario|mensaje).*\d+',                   # Usuario + número
            r'\$\s*\d+',                                       # Símbolo peso + número
            r'\d+\s+(peso|dollar|euro)',                       # Número + moneda
            r'\b\d+\s+[a-zA-ZáéíóúñÁÉÍÓÚÑ]{4,}',              # Número + palabra larga
        ]
        
        line_lower = line_clean.lower()
        for pattern in expense_patterns:
            if re.search(pattern, line_lower):
                return True
        
        return False
    
    def _looks_like_message_content(self, line: str) -> bool:
        """Determina si una línea parece ser contenido de mensaje real."""
        # Filtrar metadatos comunes EXPANDIDO
        metadata_indicators = [
            r'^\d{1,2}:\d{2}$',                    # Solo hora "23:27"
            r'^\d{1,2}/\d{1,2}(/\d{4})?$',        # Solo fecha "8/7" o "8/7/2025"
            r'^(hoy|ayer|yesterday|today)$',       # Indicadores temporales
            r'^\w{3},?\s+\w{3}$',                  # "Mié, Mar" etc
            r'^(mensaje|message|chat|notification)$',  # Palabras de interfaz
            r'^(usuario|user|admin|system)$',      # Tipos de usuario
            r'^[\s\-_\.]+$',                       # Solo caracteres especiales
            r'^(online|offline|typing)$',          # Estados de conexión
        ]
        
        line_clean = line.strip()
        line_lower = line_clean.lower()
        
        # Si es muy corto, probablemente no es contenido real
        if len(line_clean) < 4:
            return False
        
        # Verificar si es metadata
        import re
        for pattern in metadata_indicators:
            if re.match(pattern, line_lower):
                self.logger.info(f"🚫 METADATA DETECTADA: '{line_clean}' - patrón: {pattern}")
                return False
        
        # CRITERIOS POSITIVOS: líneas que SÍ parecen contenido de mensaje
        content_indicators = [
            r'[a-zA-ZáéíóúñÁÉÍÓÚÑ]{3,}.*\d+',        # Texto + número (probable gasto)
            r'\d+.*[a-zA-ZáéíóúñÁÉÍÓÚÑ]{3,}',        # Número + texto (probable gasto)
            r'[a-zA-ZáéíóúñÁÉÍÓÚÑ]{8,}',             # Texto largo (mensaje real)
            r'\$\s*\d+',                              # Símbolo monetario
            r'\b(gast[éoó]|compr[éé]|pagu[éé])',      # Verbos de gasto
        ]
        
        # Verificar indicadores positivos
        for pattern in content_indicators:
            if re.search(pattern, line_lower):
                self.logger.info(f"✅ CONTENIDO DETECTADO: '{line_clean}' - patrón: {pattern}")
                return True
        
        # Si contiene letras, números y tiene longitud razonable, probablemente es contenido
        has_letters = any(c.isalpha() for c in line_lower)
        has_numbers = any(c.isdigit() for c in line_lower) 
        reasonable_length = len(line_clean) >= 5
        
        result = has_letters and reasonable_length
        
        if result:
            self.logger.info(f"📝 CONTENIDO POR CRITERIO GENERAL: '{line_clean}'")
        else:
            self.logger.info(f"❌ NO ES CONTENIDO: '{line_clean}'")
            
        return result
    
    def _extract_sender_optimized(self, element) -> str:
        """Extracción optimizada del remitente."""
        try:
            # Buscar en atributos comunes de WhatsApp
            sender_selectors = [
                "[data-testid='msg-meta']",
                ".message-author",
                "[aria-label*='De ']"
            ]
            
            for selector in sender_selectors:
                try:
                    sender_elem = element.find_element(By.CSS_SELECTOR, selector)
                    if sender_elem and sender_elem.text:
                        return sender_elem.text.strip()
                except:
                    continue
            
            return "Desconocido"
            
        except Exception:
            return "Desconocido"
    
    def to_tuple(self) -> tuple:
        """Convierte a tupla tradicional para compatibilidad."""
        return (self.text, self.timestamp)


class LazyMessageParser:
    """⚡ Parser lazy para elementos DOM (65% mejora esperada en parsing)."""
    
    def __init__(self):
        # Cache débil para elementos ya parseados
        import weakref
        self.element_cache = weakref.WeakValueDictionary()
        self.cache_hits = 0
        self.cache_misses = 0
        
    def parse_element_lazy(self, element) -> Optional[MessageData]:
        """Parse incremental - solo lo necesario cuando se necesita."""
        try:
            element_id = self._get_element_id(element)
            
            # Verificar cache
            if element_id in self.element_cache:
                self.cache_hits += 1
                return self.element_cache[element_id]
            
            self.cache_misses += 1
            
            # Parser incremental - solo timestamp primero (ultra rápido)
            message_data = MessageData(element)
            
            # 1. Extraer timestamp inmediatamente (operación rápida)
            message_data.timestamp = self._extract_timestamp_fast(element)
            
            # 2. El texto y sender se extraerán solo cuando se acceda a ellas (lazy)
            
            # Cache con referencia débil
            if element_id:
                self.element_cache[element_id] = message_data
            
            return message_data
            
        except Exception as e:
            return None
    
    def _get_element_id(self, element) -> str:
        """Genera ID único para el elemento."""
        try:
            # Intentar varios atributos únicos
            for attr in ['data-id', 'id', 'data-testid']:
                value = element.get_attribute(attr)
                if value:
                    return f"{attr}_{value}"
            
            # Fallback: usar posición en DOM + texto parcial
            text = element.text[:20] if element.text else ""
            location = element.location
            return f"pos_{location.get('x', 0)}_{location.get('y', 0)}_{hash(text)}"
            
        except:
            return f"fallback_{id(element)}"
    
    def _extract_timestamp_fast(self, element) -> Optional[datetime]:
        """Extracción ultra-rápida de timestamp."""
        try:
            # Métodos optimizados para timestamp de WhatsApp
            timestamp_patterns = [
                r'(\d{1,2}:\d{2})',  # HH:MM
                r'(\d{1,2}:\d{2}:\d{2})',  # HH:MM:SS
            ]
            
            # Buscar en texto del elemento
            text = element.text if element.text else ""
            for pattern in timestamp_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    time_str = matches[-1]  # Último match (más probable que sea el timestamp)
                    try:
                        # Parsear solo la hora, usar fecha actual
                        if ':' in time_str:
                            parts = time_str.split(':')
                            hour = int(parts[0])
                            minute = int(parts[1])
                            second = int(parts[2]) if len(parts) > 2 else 0
                            
                            now = datetime.now()
                            return now.replace(hour=hour, minute=minute, second=second, microsecond=0)
                    except:
                        continue
            
            # Si no se encuentra timestamp, usar tiempo actual
            return datetime.now()
            
        except:
            return datetime.now()
    
    def get_cache_stats(self) -> dict:
        """Estadísticas del cache para optimización."""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total) if total > 0 else 0
        
        return {
            'cache_size': len(self.element_cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': hit_rate,
            'total_requests': total
        }


class SmartSelectorCache:
    """Caché inteligente de selectores DOM optimizado para WhatsApp Web."""
    
    def __init__(self):
        self.cached_selector = None
        self.selector_success_rate = {}
        self.last_success_time = {}
        self.selector_failure_count = {}
        self.logger = get_logger(__name__)
        
        # Selectores en orden de probabilidad de éxito - MEJORADOS para obtener mensajes completos
        self.PRIORITY_SELECTORS = [
            # 🎯 SELECTORES ACTUALIZADOS 2025 - WHATSAPP WEB NUEVA VERSIÓN
            "div[data-testid='conversation-panel-messages'] div[role='row']",  # Panel de conversación + fila
            "div[role='row'][tabindex='-1']",                                  # Filas de mensaje específicas
            "div[data-testid='msg-container']",                                # Contenedor de mensaje (si existe)
            "div[role='row'][class*='message']",                               # Filas con clases de mensaje
            "div[role='row']",                                                 # WhatsApp estándar (fallback general)
            
            # 🔄 SELECTORES DE CONTENIDO ALTERNATIVO
            "div[class*='message-in'], div[class*='message-out']",             # Clases dinámicas de mensaje
            "div[data-id*='msg']",                                             # IDs que contienen 'msg'
            "div[aria-roledescription='message']",                             # Atributo de accesibilidad
            "div[data-testid='msg-dblclick']",                                 # Elemento doble-click (si existe)
            
            # 🆘 FALLBACKS ULTRA GENERALES (último recurso)
            "div[data-id]",                                                    # Cualquier div con data-id
            "div[class*='_']",                                                 # Clases con guión bajo (patrón WA)
        ]
    
    def find_messages_optimized(self, driver) -> List:
        """
        Búsqueda optimizada de mensajes usando caché inteligente.
        70% reducción en tiempo de búsqueda DOM esperada.
        """
        # OPTIMIZACIÓN 1: Probar selector cacheado primero (ultra rápido)
        if self.cached_selector:
            try:
                # Timeout súper corto para selector cacheado
                driver.implicitly_wait(0.1)
                elements = driver.find_elements(By.CSS_SELECTOR, self.cached_selector)
                
                if elements:
                    # Éxito! Actualizar estadísticas
                    self._update_success_stats(self.cached_selector)
                    return elements
                else:
                    # Falló, marcar para reset
                    self._update_failure_stats(self.cached_selector)
                    if self.selector_failure_count.get(self.cached_selector, 0) > 3:
                        self.cached_selector = None  # Reset después de 3 fallos
                        
            except Exception:
                self._update_failure_stats(self.cached_selector)
                self.cached_selector = None
            finally:
                driver.implicitly_wait(2.0)  # Restaurar timeout
        
        # OPTIMIZACIÓN 2: Usar selectores ordenados por tasa de éxito histórica
        selectors_by_success = self._get_selectors_by_success_rate()
        self.logger.debug(f"🔍 Probando {len(selectors_by_success)} selectores para encontrar mensajes")
        
        for i, selector in enumerate(selectors_by_success, 1):
            try:
                # Solo log debug para evitar spam
                self.logger.debug(f"🎯 Selector #{i}: '{selector}'")
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    # ¡Éxito! Cachear inmediatamente
                    self.cached_selector = selector
                    self._update_success_stats(selector)
                    self.logger.info(f"✅ Selector funcionando: '{selector}' ({len(elements)} elementos)")
                    return elements
                else:
                    self._update_failure_stats(selector)
                    
            except Exception as e:
                self.logger.debug(f"Error con selector '{selector}': {e}")
                self._update_failure_stats(selector)
                continue
        
        self.logger.warning(f"🚨 NINGÚN SELECTOR FUNCIONÓ - No se encontraron elementos de mensaje")
        return []
    
    def _get_selectors_by_success_rate(self) -> List[str]:
        """Ordena selectores por tasa de éxito histórica."""
        def success_score(selector):
            successes = self.selector_success_rate.get(selector, 0)
            failures = self.selector_failure_count.get(selector, 0)
            total = successes + failures
            
            if total == 0:
                return 0.5  # Neutro para selectores nuevos
            
            # Penalizar fallos recientes más que éxitos antiguos
            recent_penalty = min(failures * 0.1, 0.3)
            return (successes / total) - recent_penalty
        
        return sorted(
            self.PRIORITY_SELECTORS,
            key=success_score,
            reverse=True
        )
    
    def _update_success_stats(self, selector: str):
        """Actualiza estadísticas de éxito."""
        self.selector_success_rate[selector] = self.selector_success_rate.get(selector, 0) + 1
        self.last_success_time[selector] = time.time()
        # Reset contador de fallos al tener éxito
        if selector in self.selector_failure_count:
            self.selector_failure_count[selector] = 0
    
    def _update_failure_stats(self, selector: str):
        """Actualiza estadísticas de fallo."""
        self.selector_failure_count[selector] = self.selector_failure_count.get(selector, 0) + 1
    
    def get_cache_stats(self) -> dict:
        """Obtiene estadísticas del caché para debug."""
        return {
            'cached_selector': self.cached_selector,
            'success_rates': dict(self.selector_success_rate),
            'failure_counts': dict(self.selector_failure_count),
            'selectors_by_success': self._get_selectors_by_success_rate()
        }


class WhatsAppSeleniumConnector:
    """
    Conector de WhatsApp Web usando Selenium WebDriver.
    
    Funcionalidades:
    - Conexión automatizada a WhatsApp Web
    - Detección y selección de chat específico
    - Lectura de mensajes nuevos
    - Manejo de errores y reconexión automática
    """
    
    def __init__(self, config):
        """
        Inicializa el conector WhatsApp.
        
        Args:
            config: Configuración de WhatsApp desde settings
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.driver = None
        self.connected = False
        self.chat_selected = False
        self.last_message_time = None  # Inicializar timestamp del último mensaje
        
        # ⚡ OPTIMIZACIÓN: Smart Selector Cache (70% mejora esperada)
        self.smart_cache = SmartSelectorCache()
        self.cached_selector = None  # Mantener por compatibilidad
        
        # ⚡ OPTIMIZACIÓN: Lazy Message Parser (65% mejora esperada)
        self.lazy_parser = LazyMessageParser()
        
        # ⚡ OPTIMIZACIÓN: Ultra Fast Extractor (10x mejora esperada)
        self.ultra_extractor = None  # Se inicializa después de conectar

        # === PERFIL DEDICADO DEL BOT ===
        self.user_data_dir = self._get_user_data_dir()

        # Configuración de Selenium
        self.chrome_options = self._setup_chrome_options()
        
    def _get_user_data_dir(self) -> Path:
        """
        Devuelve el directorio de perfil a usar. Crea la carpeta si no existe.
        Lee de config.chrome_user_data_dir o usa C:\\Chrome\\WABot por defecto.
        """
        try:
            base = getattr(self.config, "chrome_user_data_dir", r"C:\Chrome\WABot")
        except Exception:
            base = r"C:\Chrome\WABot"
        p = Path(base)
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.warning(f"No se pudo crear el directorio de perfil {p}: {e}")
        return p
        
    def connect(self) -> bool:
        """
        Conecta a WhatsApp Web y selecciona el chat objetivo.
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        try:
            self.logger.info("🚀 === INICIANDO CONEXIÓN A WHATSAPP WEB ===")
            
            # Paso 1: Inicializar driver usando método de debugging (más confiable)
            self.logger.info("📋 PASO 1: Inicializando Chrome con método de debugging...")
            
            # Lanzar Chrome con debugging
            if not self._launch_chrome_with_debugging(port=9222):
                self.logger.error("❌ No se pudo lanzar Chrome con debugging")
                return False
                
            # Adjuntarse al Chrome con debugging
            if not self._attach_to_running_chrome(port=9222):
                self.logger.error("❌ No se pudo adjuntar a Chrome con debugging")
                return False
                
            self.logger.info("✅ PASO 1 COMPLETADO: Chrome listo")
            
            # Paso 2: Verificar navegación a WhatsApp Web
            self.logger.info("📋 PASO 2: Verificando navegación a WhatsApp Web...")
            current_url = self.driver.current_url
            self.logger.info(f"📍 URL actual: {current_url}")
            
            if "whatsapp.com" not in current_url.lower():
                self.logger.info("🌐 Navegando a WhatsApp Web...")
                if not self._navigate_to_whatsapp():
                    self.logger.error("❌ FALLO EN PASO 2: No se pudo navegar a WhatsApp")
                    return False
            self.logger.info("✅ PASO 2 COMPLETADO: En WhatsApp Web")
            
            # Paso 3: Esperar código QR y login
            self.logger.info("📋 PASO 3: Esperando login de usuario...")
            if not self._wait_for_login():
                self.logger.error("❌ FALLO EN PASO 3: Usuario no hizo login")
                return False
            self.logger.info("✅ PASO 3 COMPLETADO: Usuario logueado")
            
            # Paso 4: Seleccionar chat objetivo
            self.logger.info("📋 PASO 4: Seleccionando chat objetivo...")
            if not self._select_target_chat():
                self.logger.error("❌ FALLO EN PASO 4: No se pudo seleccionar chat")
                return False
            self.logger.info("✅ PASO 4 COMPLETADO: Chat seleccionado")
            
            self.connected = True
            
            # ⚡ Inicializar Ultra Fast Extractor después de conexión exitosa
            try:
                self.ultra_extractor = UltraFastExtractor(self.driver)
                if self.ultra_extractor.initialize_fast_extraction():
                    self.logger.info("⚡ Ultra Fast Extractor inicializado (esperada mejora 10x en velocidad)")
                else:
                    self.logger.warning("⚠️ Ultra Fast Extractor falló, usando método tradicional")
            except Exception as e:
                self.logger.warning(f"⚠️ No se pudo inicializar Ultra Fast Extractor: {e}")
            
            self.logger.info("🎉 === CONEXIÓN A WHATSAPP WEB EXITOSA ===")
            return True
            
        except Exception as e:
            self.logger.error(f"💥 ERROR GENERAL en connect(): {e}")
            self.logger.error("Detalles del error:", exc_info=True)
            self._cleanup_driver()
            return False
    
    def disconnect(self) -> None:
        """Desconecta y limpia recursos."""
        self.logger.info("Desconectando de WhatsApp Web...")
        self.connected = False
        self.chat_selected = False
        self.cached_selector = None  # Resetear cache al desconectar
        self._cleanup_driver()
    
    def get_new_messages_optimized(self, last_processed_timestamp: Optional[datetime] = None) -> List[Tuple[str, datetime]]:
        """
        Obtiene SOLO mensajes nuevos usando comparación de timestamps SÚPER OPTIMIZADA.
        
        Args:
            last_processed_timestamp: Timestamp del último mensaje procesado desde BD
        
        Returns:
            Lista de tuplas (mensaje_texto, fecha_mensaje) solo de mensajes nuevos
        """
        if not self.connected or not self.chat_selected:
            return []
        
        try:
            self.logger.info(f"🚀 BÚSQUEDA OPTIMIZADA - Último conocido: {last_processed_timestamp}")
            
            # ⚡ BYPASS TEMPORAL: Si timestamp de BD es sospechoso, procesar últimos 10 mensajes
            now = datetime.now()
            bypass_filter = False
            
            if last_processed_timestamp:
                time_diff = now - last_processed_timestamp
                # Si el timestamp es del futuro o muy antiguo, usar bypass  
                if time_diff.total_seconds() < 0 or time_diff.total_seconds() > 86400:  # Si es futuro o más de 1 día
                    bypass_filter = True
                    self.logger.info(f"⚠️ BYPASS ACTIVADO - BD timestamp sospechoso (diff: {time_diff})")
            
            # 1. Obtener elementos rápidamente
            elements = self._get_message_elements()
            if not elements:
                return []
            
            # Contador para estadísticas
            processed_elements = 0
                
            # 2. OPTIMIZACIÓN CRÍTICA: Filtrar por timestamp ANTES de parsear contenido
            new_messages = []
            elements_to_check = elements[-10:] if bypass_filter else elements[-20:]  # Menos elementos en bypass
            
            for i, element in enumerate(elements_to_check):
                try:
                    processed_elements += 1  # Contar elemento procesado
                    
                    # ⚡ SÚPER RÁPIDO: Solo extraer timestamp, NO el contenido completo
                    quick_timestamp = self._extract_timestamp_super_fast(element)
                    
                    if quick_timestamp:
                        # DEBUG: Log comparación de timestamps
                        if last_processed_timestamp:
                            self.logger.info(f"🔍 COMPARANDO: Mensaje {quick_timestamp.strftime('%Y-%m-%d %H:%M:%S')} vs BD {last_processed_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                            is_newer = quick_timestamp > last_processed_timestamp
                            self.logger.info(f"   ¿Es más nuevo? {is_newer}")
                        else:
                            is_newer = True
                            self.logger.info(f"🔍 SIN BD TIMESTAMP - procesando {quick_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        # Comparar timestamp sin parsear contenido (o usar bypass)
                        if bypass_filter or not last_processed_timestamp or quick_timestamp > last_processed_timestamp:
                            # SOLO AHORA parsear el mensaje completo
                            # ⚡ OPTIMIZACIÓN: Usar lazy parser (65% más rápido)
                            self.logger.info(f"🧬 INICIANDO PARSING DE ELEMENTO...")
                            message_data = self.lazy_parser.parse_element_lazy(element)
                            
                            # 🚨 DEBUG CRÍTICO: Verificar el resultado del parsing
                            if message_data:
                                self.logger.info(f"✅ MESSAGE_DATA OBTENIDO: timestamp={message_data.timestamp}, text_length={len(message_data.text) if message_data.text else 0}")
                                
                                if message_data.timestamp:
                                    # DEBUG: Ver exactamente qué texto está extrayendo
                                    extracted_text = message_data.text or "[SIN TEXTO]"
                                    self.logger.info(f"🔍 TEXTO COMPLETO EXTRAIDO: '{extracted_text}'")
                                    
                                    # 🚨 FILTRO CRÍTICO: Si empieza con [ o "No", IGNORAR y pasar al siguiente
                                    if extracted_text.strip().startswith('[') or extracted_text.strip().startswith('No'):
                                        patron_detectado = "con [" if extracted_text.strip().startswith('[') else "con 'No'"
                                        self.logger.info(f"🤖 MENSAJE DEL BOT DETECTADO (empieza {patron_detectado}) - IGNORANDO y pasando al siguiente")
                                        continue  # Pasar al siguiente elemento inmediatamente
                                    
                                    # Convertir a tupla tradicional para compatibilidad
                                    full_message = message_data.to_tuple()
                                    new_messages.append(full_message)
                                    # Acceso lazy al texto para logging (solo cuando es necesario)
                                    preview_text = extracted_text[:30] if len(extracted_text) > 30 else extracted_text
                                    self.logger.info(f"✅ NUEVO AGREGADO: '{preview_text}...' @ {message_data.timestamp.strftime('%H:%M:%S')}")
                                    self.logger.info(f"📊 TOTAL EN LISTA: {len(new_messages)} mensajes")
                                else:
                                    self.logger.error(f"❌ MESSAGE_DATA SIN TIMESTAMP - text: '{(message_data.text or '')[:50]}'")
                            else:
                                self.logger.error(f"❌ LAZY_PARSER DEVOLVIÓ NONE - element.text: '{element.text[:50] if element.text else '[sin text]'}'")
                                
                                # Intentar parsing manual como fallback
                                try:
                                    raw_text = element.text
                                    if raw_text and len(raw_text.strip()) > 0:
                                        self.logger.info(f"🔧 FALLBACK: Intentando parsing manual de '{raw_text[:50]}...'")
                                        
                                        # 🚨 FILTRO CRÍTICO EN FALLBACK: Si empieza con [ o "No", IGNORAR
                                        if raw_text.strip().startswith('[') or raw_text.strip().startswith('No'):
                                            patron_detectado = "con [" if raw_text.strip().startswith('[') else "con 'No'"
                                            self.logger.info(f"🤖 FALLBACK: Mensaje del bot detectado (empieza {patron_detectado}) - IGNORANDO")
                                            continue  # Pasar al siguiente elemento
                                        
                                        # Crear message data manual básico
                                        manual_message = (raw_text.strip(), quick_timestamp)
                                        new_messages.append(manual_message)
                                        self.logger.info(f"🆘 FALLBACK EXITOSO: Mensaje agregado manualmente")
                                except Exception as fallback_error:
                                    self.logger.error(f"❌ FALLBACK FALLÓ: {fallback_error}")
                        else:
                            self.logger.info(f"⏸️ MENSAJE OMITIDO: {quick_timestamp.strftime('%H:%M:%S')} <= BD {last_processed_timestamp.strftime('%H:%M:%S') if last_processed_timestamp else 'None'}")
                            # 🚨 Si no hay BD timestamp, esto nunca debería ejecutarse
                            if not last_processed_timestamp:
                                self.logger.error(f"🚨 ERROR LÓGICO: Se omitió mensaje sin BD timestamp - bypass_filter={bypass_filter}")
                    
                except Exception as e:
                    self.logger.debug(f"Error procesando elemento {i}: {e}")
                    continue
            
            # 📊 REPORTE FINAL DETALLADO
            self.logger.info(f"🎯 RESULTADO OPTIMIZADO: {len(new_messages)} mensajes nuevos encontrados")
            self.logger.info(f"📈 ESTADÍSTICAS:")
            self.logger.info(f"   - Elementos procesados: {processed_elements}")
            self.logger.info(f"   - BD timestamp: {'None (primera vez)' if not last_processed_timestamp else last_processed_timestamp.strftime('%H:%M:%S')}")
            self.logger.info(f"   - Bypass activo: {bypass_filter}")
            
            if new_messages:
                self.logger.info(f"📝 MENSAJES ENCONTRADOS:")
                for i, msg in enumerate(new_messages[:3], 1):  # Solo mostrar primeros 3
                    text_preview = msg[0][:50] if msg[0] else "[sin texto]"
                    timestamp = msg[1].strftime('%H:%M:%S') if msg[1] else "[sin timestamp]"
                    self.logger.info(f"   {i}. '{text_preview}...' @ {timestamp}")
            else:
                self.logger.warning(f"⚠️ NO SE ENCONTRARON MENSAJES - Posible problema en lazy_parser o selectores")
            
            return new_messages
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda optimizada: {e}")
            return []
    
    def get_new_messages_blazing_fast(self, last_processed_timestamp: Optional[datetime] = None, limit: int = 20) -> List[Tuple[str, datetime]]:
        """
        ⚡🚀 MÉTODO ULTRA OPTIMIZADO: 10x más rápido que ultra_smart (esperado <2s vs 12s+).
        
        Usa JavaScript directo + MutationObserver para extracción instantánea.
        """
        if not self.connected or not self.driver:
            return []
        
        # Si UltraFastExtractor está disponible, usarlo
        if self.ultra_extractor:
            try:
                return self.ultra_extractor.get_messages_ultra_fast(limit)
            except Exception as e:
                self.logger.warning(f"UltraFast falló, fallback a método tradicional: {e}")
        
        # Fallback al método existente
        return self.get_new_messages_ultra_smart(last_processed_timestamp, limit)
    
    def has_new_messages_instant_check(self) -> bool:
        """
        ⚡ Verificación instantánea de mensajes nuevos (<100ms vs varios segundos).
        """
        if self.ultra_extractor:
            try:
                return self.ultra_extractor.has_new_messages_instant()
            except:
                pass
        
        # Fallback: asumir que hay cambios
        return True

    def get_new_messages_ultra_smart(self, last_processed_timestamp: Optional[datetime] = None, limit: int = 20) -> List[Tuple[str, datetime]]:
        """
        ⚡ Búsqueda de mensajes ULTRA optimizada (75% mejora esperada vs método tradicional).
        
        Optimizaciones implementadas:
        1. Límite inteligente de elementos a procesar
        2. Early exit al encontrar mensajes antiguos
        3. Timestamp extraction ultra-rápida
        4. Lazy parsing solo cuando es necesario
        5. Filtrado de mensajes del sistema
        
        Args:
            last_processed_timestamp: Último timestamp procesado
            limit: Máximo número de elementos a revisar
            
        Returns:
            Lista de tuplas (mensaje_texto, fecha_mensaje) de mensajes nuevos
        """
        if not self.connected or not self.chat_selected:
            return []
            
        try:
            start_time = time.time()
            self.logger.info(f"⚡ BÚSQUEDA ULTRA SMART - Límite: {limit}, Último: {last_processed_timestamp}")
            
            # 1. ⚡ OPTIMIZACIÓN: Obtener elementos con caché inteligente
            elements = self.smart_cache.find_messages_optimized(self.driver)
            
            if not elements:
                return []
            
            # 2. ⚡ OPTIMIZACIÓN: Solo procesar los elementos más recientes
            recent_elements = elements[-limit:] if len(elements) > limit else elements
            
            new_messages = []
            processed_count = 0
            early_exit_count = 0
            
            # 3. ⚡ OPTIMIZACIÓN: Iterar en orden inverso (más recientes primero)
            for element in reversed(recent_elements):
                try:
                    processed_count += 1
                    
                    # ⚡ PASO 1: Timestamp ultra-rápido (sin parsing completo)
                    quick_timestamp = self._extract_timestamp_super_fast(element)
                    
                    if not quick_timestamp:
                        continue
                    
                    # ⚡ PASO 2: Early exit si encontramos mensaje antiguo
                    if last_processed_timestamp and quick_timestamp <= last_processed_timestamp:
                        early_exit_count += 1
                        # Si encontramos 3+ mensajes antiguos consecutivos, probablemente ya no hay más nuevos
                        if early_exit_count >= 3:
                            self.logger.debug(f"🏃‍♂️ Early exit: {early_exit_count} mensajes antiguos consecutivos")
                            break
                        continue
                    
                    # Reset early exit counter si encontramos mensaje nuevo
                    early_exit_count = 0
                    
                    # ⚡ PASO 3: Filtrado rápido de mensajes del sistema
                    text_preview = element.text[:50] if element.text else ""
                    
                    # Filtro rápido de mensajes del sistema
                    if any(keyword in text_preview.lower() for keyword in 
                           ['cambió', 'eliminó', 'salió', 'agregó', 'se unió']):
                        self.logger.debug(f"🚫 Sistema: '{text_preview}'")
                        continue
                    
                    # ⚡ PASO 4: AHORA sí, parsear completamente con lazy loading
                    message_data = self.lazy_parser.parse_element_lazy(element)
                    
                    if message_data and message_data.timestamp:
                        full_message = message_data.to_tuple()
                        new_messages.append(full_message)
                        
                        # Log solo si es necesario
                        if self.logger.level <= 20:  # DEBUG level
                            preview = message_data.text[:25] if message_data.text else "[sin texto]"
                            self.logger.debug(f"✅ NUEVO: '{preview}' @ {message_data.timestamp.strftime('%H:%M:%S')}")
                    
                except Exception as e:
                    self.logger.debug(f"Error procesando elemento: {e}")
                    continue
            
            # 4. ⚡ ESTADÍSTICAS DE PERFORMANCE
            elapsed_time = (time.time() - start_time) * 1000
            
            cache_stats = self.smart_cache.get_cache_stats()
            parser_stats = self.lazy_parser.get_cache_stats()
            
            self.logger.info(f"🏁 ULTRA SMART completada: {len(new_messages)} nuevos en {elapsed_time:.1f}ms")
            self.logger.debug(f"📊 Stats - Procesados: {processed_count}, Early exits: {early_exit_count}")
            self.logger.debug(f"📊 Cache DOM hit rate: {cache_stats.get('hit_rate', 0):.2%}")
            self.logger.debug(f"📊 Parser cache hit rate: {parser_stats.get('hit_rate', 0):.2%}")
            
            # 5. Ordenar mensajes por timestamp (más antiguos primero)
            new_messages.sort(key=lambda x: x[1])
            
            return new_messages
            
        except Exception as e:
            self.logger.error(f"❌ Error en búsqueda ultra smart: {e}")
            return []
    
    def _extract_timestamp_super_fast(self, element) -> Optional[datetime]:
        """
        Extrae SOLO el timestamp de manera súper rápida sin parsear contenido.
        """
        try:
            # Método 1: Buscar span con title (más rápido)
            spans = element.find_elements(By.CSS_SELECTOR, "span[title]")
            for span in spans[:2]:  # Solo los primeros 2
                title = span.get_attribute("title")
                if title and ':' in title and len(title) < 20:
                    return self._parse_message_timestamp(title)
            
            # Método 2: Metadata común
            try:
                meta = element.find_element(By.CSS_SELECTOR, "[data-testid='msg-meta']")
                if meta and meta.text and ':' in meta.text:
                    return self._parse_message_timestamp(meta.text.strip())
            except:
                pass
            
            # Método 3: Si no hay timestamp específico, usar tiempo actual
            return datetime.now()
            
        except:
            return datetime.now()
    
    def get_new_messages(self) -> List[Tuple[str, datetime]]:
        """
        Obtiene mensajes nuevos del chat seleccionado con detección en tiempo real.
        
        Returns:
            Lista de tuplas (mensaje_texto, fecha_mensaje)
        """
        if not self.connected or not self.chat_selected:
            self.logger.warning("❌ ESTADO: WhatsApp no conectado o chat no seleccionado")
            self.logger.warning(f"   Connected: {self.connected}, Chat selected: {self.chat_selected}")
            return []
        
        try:
            self.logger.debug("🔍 INICIANDO BÚSQUEDA DE MENSAJES NUEVOS...")
            self.logger.debug(f"📊 Estado inicial - Último mensaje: {self.last_message_time}")
            messages = []
            
            # Obtener elementos de mensajes
            self.logger.debug("🎯 PASO 1: Obteniendo elementos de mensajes...")
            message_elements = self._get_message_elements()
            
            if not message_elements:
                self.logger.error("🚨 PASO 1 FALLIDO: No se encontraron elementos de mensaje")
                return []
            
            self.logger.debug(f"✅ PASO 1 EXITOSO: {len(message_elements)} elementos de mensaje encontrados")
            
            # Procesar cada mensaje
            self.logger.debug("🎯 PASO 2: Procesando elementos de mensajes...")
            new_messages_count = 0
            
            for i, element in enumerate(message_elements):
                try:
                    self.logger.info(f"🔸 PROCESANDO ELEMENTO {i+1}/{len(message_elements)}...")
                    
                    # ⚡ OPTIMIZACIÓN: Usar lazy parser en lugar del método tradicional
                    lazy_message_data = self.lazy_parser.parse_element_lazy(element)
                    if lazy_message_data:
                        message_data = lazy_message_data.to_tuple()  # Compatibilidad
                        message_text, message_time = message_data
                        self.logger.info(f"✅ ELEMENTO {i+1} PARSEADO: '{message_text[:50]}...' (Tiempo: {message_time.strftime('%H:%M:%S')})")
                        
                        # Verificar si es mensaje nuevo
                        is_new = self._is_new_message(message_time)
                        self.logger.info(f"   🔍 ¿Es nuevo?: {is_new} (último conocido: {self.last_message_time})")
                        
                        if is_new:
                            messages.append(message_data)
                            new_messages_count += 1
                            self.logger.info(f"🎉 NUEVO MENSAJE #{new_messages_count} AGREGADO!")
                        else:
                            self.logger.info(f"   ⏸️ Mensaje ya conocido, ignorado")
                    else:
                        self.logger.warning(f"❌ ELEMENTO {i+1} NO SE PUDO PARSEAR (devolvió None)")
                        
                except Exception as e:
                    self.logger.error(f"❌ ERROR procesando elemento {i+1}: {e}")
                    continue
            
            self.logger.info("🎯 PASO 3: Finalizando procesamiento...")
            
            if messages:
                # Actualizar timestamp del último mensaje
                self.last_message_time = max(msg[1] for msg in messages)
                self.logger.info(f"🎉 ÉXITO! {len(messages)} MENSAJES NUEVOS PROCESADOS")
                self.logger.info(f"📅 Último timestamp actualizado: {self.last_message_time.strftime('%H:%M:%S')}")
                
                # Mostrar resumen de mensajes nuevos
                for i, (text, time) in enumerate(messages):
                    self.logger.info(f"   📩 Mensaje #{i+1}: '{text[:100]}...' ({time.strftime('%H:%M:%S')})")
            else:
                self.logger.info("ℹ️ RESULTADO: No hay mensajes nuevos")
                if message_elements:
                    self.logger.info(f"   📊 Se procesaron {len(message_elements)} elementos pero ninguno era nuevo")
                    
                    # Si es la primera vez, inicializar last_message_time con el mensaje más reciente
                    if self.last_message_time is None and message_elements:
                        try:
                            # Obtener el timestamp del último mensaje existente para futuros filtros
                            latest_element = message_elements[-1]
                            # ⚡ OPTIMIZACIÓN: Usar lazy parser para inicialización
                            lazy_data = self.lazy_parser.parse_element_lazy(latest_element)
                            if lazy_data:
                                latest_message_data = lazy_data.to_tuple()
                                self.last_message_time = latest_message_data[1]
                                self.logger.info(f"🕐 Inicializando último timestamp: {self.last_message_time.strftime('%H:%M:%S')}")
                        except Exception as e:
                            self.logger.warning(f"⚠️ No se pudo inicializar timestamp: {e}")
                            self.last_message_time = datetime.now()
            
            self.logger.info(f"🏁 BÚSQUEDA COMPLETADA - Retornando {len(messages)} mensajes")
            
            # ✅ INICIALIZAR last_message_time EN LA PRIMERA EJECUCIÓN
            if self.last_message_time is None and message_elements:
                try:
                    # En la primera ejecución, establecer el timestamp al mensaje más reciente
                    # para que en la próxima ejecución solo procese mensajes nuevos
                    latest_element = message_elements[-1]
                    # ⚡ OPTIMIZACIÓN: Lazy parser para establecer timestamp inicial
                    lazy_data = self.lazy_parser.parse_element_lazy(latest_element)
                    if lazy_data:
                        latest_message_data = lazy_data.to_tuple()
                        self.last_message_time = latest_message_data[1]
                        self.logger.info(f"🕐 INICIALIZACIÓN: last_message_time establecido en {self.last_message_time.strftime('%H:%M:%S')}")
                        self.logger.info("📝 PRÓXIMAS EJECUCIONES: Solo procesará mensajes nuevos después de este timestamp")
                        
                        # En la primera ejecución, NO procesar mensajes antiguos
                        if not messages:  # Si no hay mensajes nuevos en la primera ejecución
                            self.logger.info("✨ PRIMERA EJECUCIÓN: No hay mensajes nuevos, estableciendo baseline")
                    else:
                        # Si no se puede parsear, usar tiempo actual
                        self.last_message_time = datetime.now()
                        self.logger.info(f"🕐 FALLBACK: last_message_time establecido en tiempo actual")
                except Exception as e:
                    self.logger.warning(f"⚠️ Error inicializando timestamp: {e}")
                    self.last_message_time = datetime.now()
            
            return messages
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo mensajes: {e}")
            self.logger.error("Detalles del error:", exc_info=True)
            
            # Intentar reconectar si hay problemas
            if not self._verify_connection():
                self.logger.warning("Conexión perdida, intentando reconectar...")
                self.connected = False
                self.chat_selected = False
            return []
    
    def wait_for_new_message(self, timeout_seconds: int = 10) -> List[Tuple[str, datetime]]:
        """
        Espera activamente por nuevos mensajes usando WebDriverWait.
        
        Args:
            timeout_seconds: Tiempo máximo a esperar por un mensaje nuevo
            
        Returns:
            Lista de tuplas (mensaje_texto, fecha_mensaje) de mensajes nuevos
        """
        if not self.connected or not self.chat_selected:
            self.logger.warning("WhatsApp no conectado o chat no seleccionado")
            return []
        
        try:
            # Contar mensajes actuales como baseline
            initial_message_elements = self._get_message_elements()
            initial_count = len(initial_message_elements) if initial_message_elements else 0
            
            self.logger.info(f"⏳ Esperando nuevos mensajes... (actual: {initial_count} mensajes, timeout: {timeout_seconds}s)")
            
            # Esperar a que aparezcan nuevos mensajes
            wait = WebDriverWait(self.driver, timeout_seconds)
            
            def check_for_new_messages(driver):
                """Función para detectar si llegaron mensajes nuevos."""
                try:
                    current_elements = self._get_message_elements()
                    current_count = len(current_elements) if current_elements else 0
                    
                    if current_count > initial_count:
                        self.logger.info(f"🆕 NUEVO MENSAJE DETECTADO! Mensajes: {initial_count} → {current_count}")
                        return True
                    
                    # Verificar también por cambios en el último mensaje
                    if current_elements and initial_message_elements:
                        try:
                            # Comparar el último mensaje
                            # ⚡ OPTIMIZACIÓN: Lazy parser para comparación de timestamps
                            current_lazy = self.lazy_parser.parse_element_lazy(current_elements[-1])
                            initial_lazy = self.lazy_parser.parse_element_lazy(initial_message_elements[-1])
                            
                            last_current = current_lazy.to_tuple() if current_lazy else None
                            last_initial = initial_lazy.to_tuple() if initial_lazy else None
                            
                            if last_current and last_initial:
                                if last_current[1] > last_initial[1]:  # Comparar timestamps
                                    self.logger.info(f"🕐 MENSAJE ACTUALIZADO DETECTADO! Nuevo timestamp: {last_current[1]}")
                                    return True
                        except:
                            pass
                    
                    return False
                except Exception as e:
                    self.logger.debug(f"Error verificando mensajes: {e}")
                    return False
            
            # Esperar por cambios
            wait.until(check_for_new_messages)
            
            # Obtener los mensajes nuevos
            self.logger.info("🔍 Obteniendo mensajes nuevos después de detectar cambios...")
            new_messages = self.get_new_messages()
            
            if new_messages:
                self.logger.info(f"✅ DETECCIÓN COMPLETADA: {len(new_messages)} mensajes nuevos encontrados")
                for i, (msg_text, msg_time) in enumerate(new_messages):
                    self.logger.info(f"📩 MENSAJE NUEVO #{i+1}: '{msg_text}' (Tiempo: {msg_time.strftime('%H:%M:%S')})")
            else:
                self.logger.warning("⚠️ PROBLEMA: Se detectaron cambios pero get_new_messages() devolvió lista vacía")
                # Intentar un enfoque más directo
                self.logger.info("🔧 Intentando enfoque alternativo para obtener mensajes...")
                current_elements = self._get_message_elements()
                self.logger.info(f"📱 Elementos actuales encontrados: {len(current_elements)}")
            
            return new_messages
            
        except TimeoutException:
            self.logger.debug(f"⏰ Timeout después de {timeout_seconds}s - No llegaron mensajes nuevos")
            return []
        except Exception as e:
            self.logger.error(f"❌ Error esperando mensajes: {e}")
            return []
    
    def _setup_chrome_options(self) -> Options:
        """Configura opciones de Chrome para WhatsApp Web con optimización de RAM."""
        options = Options()

        # Headless solo si ya tenés la sesión guardada (no recomendado para el primer login)
        if getattr(self.config, "chrome_headless", False):
            # headless "nuevo" evita algunos problemas
            options.add_argument("--headless=new")

        # === OPTIMIZACIONES DE RAM Y PERFORMANCE ===
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")  # Ahorra GPU RAM
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        
        # Límites de memoria más estrictos
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=1024")  # Límite de JS heap a 1GB
        options.add_argument("--aggressive-cache-discard")
        
        # Deshabilitar características innecesarias para WhatsApp
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # No cargar imágenes (solo texto)
        options.add_argument("--disable-javascript-harmony-shipping")
        options.add_argument("--disable-client-side-phishing-detection")
        
        # Configuración de red optimizada
        options.add_argument("--aggressive-cache-discard")
        options.add_argument("--disable-background-networking")
        
        # Configuración de ventana mínima si no es headless
        if not getattr(self.config, "chrome_headless", False):
            options.add_argument("--window-size=800,600")  # Ventana pequeña
        
        options.add_argument("--remote-allow-origins=*")

        # === PERFIL DEL BOT (NO el Default) ===
        # MUY IMPORTANTE: NO agregar --profile-directory cuando se usa un user-data-dir exclusivo
        options.add_argument(f"--user-data-dir={self.user_data_dir}")

        # Cosas menores de automatización
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Configurar prefs para menor consumo
        prefs = {
            "profile.default_content_setting_values": {
                "images": 2,  # Bloquear imágenes
                "plugins": 2,  # Bloquear plugins
                "popups": 2,   # Bloquear popups
                "geolocation": 2,  # Bloquear geolocalización
                "notifications": 2,  # Bloquear notificaciones
                "media_stream": 2,  # Bloquear media stream
            },
            "profile.managed_default_content_settings": {
                "images": 2
            }
        }
        options.add_experimental_option("prefs", prefs)

        return options
    
    def _attach_to_running_chrome(self, port: int = 9222) -> bool:
        """Intenta adjuntarse a un Chrome ya corriendo con remote debugging."""
        try:
            self.logger.info(f"🔌 Intentando adjuntarse a Chrome en puerto {port}...")
            
            # Verificar si hay Chrome con debugging disponible
            import requests
            try:
                response = requests.get(f"http://127.0.0.1:{port}/json/version", timeout=3)
                if response.status_code == 200:
                    self.logger.info(f"✅ Chrome detectado en puerto {port}")
                    version_info = response.json()
                    self.logger.info(f"🌐 Versión: {version_info.get('Browser', 'Unknown')}")
                else:
                    return False
            except:
                self.logger.info(f"❌ No hay Chrome en puerto {port}")
                return False
            
            # Obtener pestañas disponibles
            try:
                tabs_response = requests.get(f"http://127.0.0.1:{port}/json", timeout=3)
                if tabs_response.status_code == 200:
                    tabs = tabs_response.json()
                    self.logger.info(f"📂 Pestañas encontradas: {len(tabs)}")
                    
                    # Buscar pestaña de WhatsApp existente
                    whatsapp_tab = None
                    for tab in tabs:
                        url = tab.get('url', '').lower()
                        title = tab.get('title', '').lower()
                        self.logger.info(f"  - 📄 {title}: {url}")
                        if 'whatsapp.com' in url:
                            whatsapp_tab = tab
                            self.logger.info(f"✅ Pestaña WhatsApp encontrada!")
                            break
                    
                    if whatsapp_tab:
                        self.logger.info("🎯 Conectando a pestaña WhatsApp existente...")
                    else:
                        self.logger.info("📝 No hay pestaña WhatsApp, se creará una nueva")
            except Exception as e:
                self.logger.warning(f"⚠️ Error obteniendo pestañas: {e}")
            
            # Crear opciones minimalistas para adjuntar
            opts = Options()
            opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
            
            self.driver = webdriver.Chrome(options=opts)
            self.driver.implicitly_wait(2)  # Reducir timeout para detectar desconexiones más rápido
            
            # Verificar que estamos conectados
            current_url = self.driver.current_url
            self.logger.info(f"📍 Conectado! URL actual: {current_url}")
            
            # Si no está en WhatsApp, buscar pestaña existente o crear nueva
            if "whatsapp.com" not in current_url.lower():
                self.logger.info("🔍 Buscando pestaña de WhatsApp...")
                
                # Intentar cambiar a una pestaña existente de WhatsApp
                for handle in self.driver.window_handles:
                    self.driver.switch_to.window(handle)
                    if "whatsapp.com" in self.driver.current_url.lower():
                        self.logger.info(f"✅ Cambiado a pestaña WhatsApp existente: {self.driver.current_url}")
                        return True
                
                # Si no hay pestaña de WhatsApp, navegar en la pestaña actual
                self.logger.info("🌐 Navegando a WhatsApp Web en pestaña actual...")
                self.driver.get("https://web.whatsapp.com")
                time.sleep(0.5)
                self.logger.info(f"📍 Nueva URL: {self.driver.current_url}")
            
            self.logger.info("✅ Adjuntado exitosamente a Chrome existente!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error adjuntándose a Chrome: {e}")
            return False

    def _launch_chrome_with_debugging(self, port: int = 9222) -> bool:
        """Lanza Chrome con remote debugging usando el perfil predeterminado."""
        try:
            self.logger.info(f"🚀 Lanzando Chrome COMO PROCESO DUEÑO del perfil con debugging...")
            
            import subprocess
            import time
            
            # Cerrar Chrome existente y limpiar locks
            self._close_existing_chrome()
            
            # Verificar que el puerto esté libre
            self.logger.info(f"🔍 Verificando que puerto {port} esté libre...")
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
            if f":{port}" in result.stdout:
                self.logger.warning(f"⚠️ Puerto {port} ya está en uso, intentando liberar...")
                time.sleep(0.5)
            
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            profile_path = self.user_data_dir  # PERFIL DEL BOT

            cmd = [
                chrome_path,
                "--remote-debugging-address=127.0.0.1",
                f"--remote-debugging-port={port}",
                f"--user-data-dir={profile_path}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-background-mode",
                "https://web.whatsapp.com",
            ]
            
            self.logger.info(f"📋 Comando mejorado:")
            for arg in cmd:
                self.logger.info(f"  {arg}")
            
            # Lanzar Chrome como proceso principal (no background)
            self.chrome_process = subprocess.Popen(cmd, 
                                                  creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Esperar que Chrome se inicie y verificar debugging
            self.logger.info("⏳ Esperando que Chrome HABILITE remote debugging...")
            max_wait = 8  # Reducido para ser más rápido
            
            for i in range(max_wait):
                try:
                    # Verificación de puerto con netstat primero
                    if i % 3 == 0:  # Cada 3 intentos
                        netstat_result = subprocess.run(["netstat", "-ano"], 
                                                       capture_output=True, text=True)
                        listening_ports = [line for line in netstat_result.stdout.split('\n') 
                                         if 'LISTENING' in line and f':{port}' in line]
                        
                        if listening_ports:
                            self.logger.info(f"🎯 Puerto {port} detectado en LISTENING:")
                            for line in listening_ports:
                                self.logger.info(f"  {line.strip()}")
                        else:
                            self.logger.info(f"⏳ Puerto {port} aún no está en LISTENING...")
                    
                    # Verificación HTTP
                    import requests
                    self.logger.info(f"🔍 Intento {i+1}/{max_wait}: HTTP check puerto {port}...")
                    
                    # Intentar con localhost también por si acaso
                    for host in ['127.0.0.1', 'localhost']:
                        try:
                            response = requests.get(f"http://{host}:{port}/json/version", timeout=1)
                            if response.status_code == 200:
                                version_info = response.json()
                                self.logger.info(f"✅ Chrome debugging activo en {host}:{port}!")
                                self.logger.info(f"🌐 Versión: {version_info.get('Browser', 'Unknown')}")
                                self.logger.info(f"⏱️ Listo después de {i+1} segundos")
                                return True
                        except:
                            continue
                            
                except requests.exceptions.ConnectionError:
                    pass
                except Exception as e:
                    self.logger.warning(f"❌ Error verificando: {e}")

                time.sleep(0.5)
            
            # Diagnóstico completo si falla
            self.logger.error(f"💥 Chrome debugging NO SE ACTIVÓ después de {max_wait} segundos")
            
            # Verificar procesos Chrome
            import psutil
            chrome_processes = []
            for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'chrome' in p.info['name'].lower():
                    chrome_processes.append(p)
            
            self.logger.info(f"🔍 Procesos Chrome activos: {len(chrome_processes)}")
            for proc in chrome_processes:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else 'N/A'
                has_debug = '--remote-debugging-port' in cmdline
                self.logger.info(f"  - PID {proc.info['pid']}: {proc.info['name']} | Debug: {'✅' if has_debug else '❌'}")
                if has_debug:
                    self.logger.info(f"    CMD: ...{cmdline[-100:]}")  # Últimos 100 chars
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error lanzando Chrome: {e}")
            return False


    
    def _close_existing_chrome(self):
        """Cierra cualquier instancia de Chrome existente y limpia locks."""
        try:
            import subprocess
            import time
            import os
            
            self.logger.info("🔄 Cerrando todas las instancias de Chrome...")
            
            # Cerrar Chrome usando taskkill con Tree para procesos hijo
            result = subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], 
                                  capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                self.logger.info("✅ Chrome cerrado exitosamente")
            else:
                self.logger.info("ℹ️ No había instancias de Chrome corriendo")
            
            # Esperar que se cierren completamente
            time.sleep(1)
            
            # Limpiar locks del perfil
            self.logger.info("🧹 Limpiando locks del perfil...")
            profile_dir = Path.home() / 'AppData' / 'Local' / 'Google' / 'Chrome' / 'User Data'
            
            # Eliminar archivos Singleton que pueden causar problemas
            singleton_patterns = ['Singleton*', 'SingletonSocket', 'SingletonLock', 'SingletonCookie']
            for pattern in singleton_patterns:
                for lock_file in profile_dir.glob(pattern):
                    try:
                        lock_file.unlink(missing_ok=True)
                        self.logger.info(f"🗑️ Eliminado: {lock_file.name}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ No se pudo eliminar {lock_file}: {e}")
            
            self.logger.info("✅ Limpieza de Chrome completada")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en limpieza de Chrome: {e}")
    
    def _navigate_to_whatsapp(self) -> bool:
        """Navega a WhatsApp Web."""
        try:
            self.logger.info("Navegando a WhatsApp Web...")
            
            # Usar execute_script en lugar de get para mejor control
            self.driver.execute_script("window.location.href = 'https://web.whatsapp.com';")
            
            # Esperar a que cargue completamente
            wait = WebDriverWait(self.driver, 10)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

            time.sleep(1)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error navegando a WhatsApp: {e}")
            return False
    
    def _wait_for_login(self) -> bool:
        """Espera a que el usuario haga login con código QR."""
        try:
            self.logger.info("Esperando login de usuario...")
            
            # Timeout más largo para login
            wait = WebDriverWait(self.driver, 60)  # 1 minuto
            
            # Verificar si ya está logueado
            self.logger.info("🔍 Verificando estado actual de WhatsApp Web...")
            
            try:
                # Primero verificar si ya está logueado (sin QR)
                chat_list = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='chat-list']")
                if chat_list:
                    self.logger.info("✅ Ya está logueado - encontrada lista de chats")
                    return True
            except NoSuchElementException:
                pass
                
            try:
                # Si hay QR, informar al usuario
                qr_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='qr-code'], canvas[aria-label*='QR']")
                if qr_element:
                    self.logger.info("📱 QR encontrado - escanea el código QR para continuar...")
                    print("📱 Escanea el código QR en WhatsApp Web para continuar...")
                    
            except NoSuchElementException:
                self.logger.info("🔍 No se encontró QR - quizás ya está cargando...")
                
            # Esperar múltiples indicadores de login exitoso
            login_indicators = [
                "[data-testid='chat-list']",
                "[data-testid='side']",
                "div[data-testid='app']",
                "#pane-side",
                "div._3OvU8"  # Selector alternativo para la barra lateral
            ]
            
            self.logger.info(f"⏳ Esperando login (timeout: 120s)...")

            for attempt in range(120):  # Verificar cada segundo
                for selector in login_indicators:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element and element.is_displayed():
                            self.logger.info(f"✅ Login exitoso detectado con selector: {selector}")
                            time.sleep(0.2)  # Dar tiempo extra para que cargue
                            return True
                    except NoSuchElementException:
                        continue

                # Log de progreso cada 10 segundos
                if attempt % 10 == 0 and attempt > 0:
                    self.logger.info(f"⏳ Esperando login... ({attempt}/120 segundos)")

                    # Debug: mostrar elementos actuales
                    try:
                        page_source = self.driver.page_source
                        if "qr-code" in page_source.lower():
                            self.logger.debug("🔍 QR aún presente")
                        if "loading" in page_source.lower():
                            self.logger.debug("🔍 Página cargando...")
                    except:
                        pass

                time.sleep(0.2)  # Verificación más rápida
            
            self.logger.error("❌ Timeout esperando login después de 120 segundos")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error en login: {e}")
            self.logger.error("Detalles del error:", exc_info=True)
            return False
    
    def _select_target_chat(self) -> bool:
        """Selecciona el chat objetivo configurado."""
        try:
            self.logger.info(f"Buscando chat: {self.config.target_chat_name}")
            
            # Buscar el chat en la lista
            chat_element = self._find_chat_by_name(self.config.target_chat_name)
            
            if not chat_element:
                self.logger.error(f"No se encontró el chat: {self.config.target_chat_name}")
                return False
            
            # Hacer click en el chat con scroll si es necesario
            try:
                self.logger.info("📱 Haciendo click en el chat...")
                
                # Asegurar que el elemento está visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", chat_element)
                time.sleep(0.3)
                
                # Intentar click normal primero
                chat_element.click()
                self.logger.info("✅ Click realizado")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Click normal falló, intentando JavaScript: {e}")
                # Fallback: usar JavaScript
                self.driver.execute_script("arguments[0].click();", chat_element)
            
            # Esperar más tiempo para que cargue el chat
            self.logger.info("⏳ Esperando que cargue el chat...")
            time.sleep(1)  # Tiempo reducido
            
            # Verificar múltiples veces con pausa
            max_attempts = 3
            for attempt in range(max_attempts):
                self.logger.info(f"🔍 Verificación de chat seleccionado (intento {attempt + 1}/{max_attempts})...")
                
                if self._verify_chat_selected():
                    self.chat_selected = True
                    self.logger.info(f"✅ Chat seleccionado exitosamente: {self.config.target_chat_name}")
                    return True
                
                if attempt < max_attempts - 1:  # No esperar en el último intento
                    self.logger.info("⏳ Esperando antes del siguiente intento...")
                    time.sleep(1)
            
            self.logger.error("❌ No se pudo verificar la selección del chat después de múltiples intentos")
            return False
            
        except Exception as e:
            self.logger.error(f"Error seleccionando chat: {e}")
            return False
    
    def _find_chat_by_name(self, chat_name: str) -> Optional[object]:
        """Busca un chat por nombre en la lista de chats."""
        try:
            # Selectores alternativos para la lista de chats
            chat_list_selectors = [
                "[data-testid='chat-list']",
                "#pane-side",
                "div[data-testid='side']",
                "div._3OvU8",  # Selector clásico
                "div[role='application'] > div > div",  # Selector genérico
                "div._2_1wd",  # Otro selector posible
                "#side"
            ]
            
            self.logger.info("🔍 Esperando que cargue la interfaz de chats...")
            
            # Intentar con múltiples selectores
            chat_list_found = False
            for selector in chat_list_selectors:
                try:
                    wait = WebDriverWait(self.driver, 2)  # Timeout corto por selector
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    self.logger.info(f"✅ Lista de chats encontrada con: {selector}")
                    chat_list_found = True
                    break
                except:
                    self.logger.debug(f"Selector {selector} no funcionó")
                    continue

            if not chat_list_found:
                self.logger.warning("⚠️ No se encontró lista de chats con selectores conocidos, continuando...")

            # Dar tiempo para que carguen los chats
            self.logger.info("📋 Esperando que carguen los chats...")
            time.sleep(0.5)
            
            # Múltiples selectores para elementos de chat (ACTUALIZADOS 2025)
            chat_selectors = [
                # 🎯 SELECTORES PRINCIPALES 2025
                "[data-testid='cell-frame-container']",              # Marco de celda (principal)
                "div[role='listitem'][tabindex='-1']",               # Items de lista específicos
                "[data-testid='chat']",                              # Chat directo (si existe)
                "div[role='listitem']",                              # Items de lista general
                
                # 🔄 SELECTORES ALTERNATIVOS  
                "div[data-testid='conversation-info-header']",       # Header de conversación
                "div[aria-label][role='listitem']",                 # Con aria-label y role
                "div[title][role='listitem']",                      # Con title y role
                "span[title][dir='auto']",                          # Nombres con dirección auto
                "div[tabindex='0'][role='button']",                 # Elementos clickeables como botones
                
                # 🆘 FALLBACKS GENERALES
                "div[aria-label]",                                  # Cualquier div con aria-label
                "div[title]",                                       # Cualquier div con title  
                "span[title]",                                      # Spans con title (nombres)
                "div[role='button']",                               # Cualquier botón
                "div > div > div[tabindex='0']"                     # Elementos clickeables anidados
            ]
            
            chat_elements = []
            for selector in chat_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        self.logger.info(f"✅ Encontrados {len(elements)} elementos con selector: {selector}")
                        chat_elements = elements
                        break
                except Exception as e:
                    self.logger.debug(f"Selector {selector} no funcionó: {e}")
                    continue
            
            if not chat_elements:
                self.logger.error("❌ No se encontraron elementos de chat con ningún selector")
                return None
            
            self.logger.info(f"🔍 Revisando {len(chat_elements)} chats...")
            found_chats = []
            
            for i, chat_element in enumerate(chat_elements):
                try:
                    self.logger.debug(f"🔍 Procesando elemento {i+1}/{len(chat_elements)} (índice {i})")
                    
                    # Múltiples selectores para el nombre del chat (más completos)
                    name_selectors = [
                        "[data-testid='conversation-info-header']",
                        "[data-testid='conversation-title']", 
                        "span[title]",
                        "div[title]",
                        "span._3ko75",  # Selector alternativo
                        ".ggj6brxn",    # Otro selector posible
                        "span[dir='auto']",  # Texto automático
                        "div[dir='auto']",   # Div con texto automático
                        "span.ggj6brxn",     # Span específico
                        ".zoWT4",            # Selector de nombre
                        "._21nHd",           # Otro selector común
                        "[aria-label]",      # Elementos con aria-label
                        "[role='gridcell'] span",  # Spans dentro de celdas
                    ]
                    
                    chat_text = ""
                    chat_title = ""
                    chat_aria_label = ""
                    
                    # Buscar texto con selectores específicos
                    for name_selector in name_selectors:
                        try:
                            name_element = chat_element.find_element(By.CSS_SELECTOR, name_selector)
                            if name_element:
                                text = name_element.text.strip()
                                title = name_element.get_attribute("title")
                                aria_label = name_element.get_attribute("aria-label")
                                
                                if text:
                                    chat_text = text
                                    break
                                elif title:
                                    chat_title = title
                                elif aria_label:
                                    chat_aria_label = aria_label
                        except NoSuchElementException:
                            continue
                    
                    # Usar title o aria-label si no hay texto
                    if not chat_text:
                        chat_text = chat_title or chat_aria_label
                    
                    # Si aún no hay texto, intentar atributos del elemento principal
                    if not chat_text:
                        chat_text = chat_element.get_attribute("title") or chat_element.get_attribute("aria-label") or ""
                    
                    # Si no encontramos texto con selectores, intentar texto directo
                    if not chat_text:
                        chat_text = chat_element.text.strip()
                    
                    # SIEMPRE procesar el primer chat (índice 0) incluso sin texto
                    if i == 0:
                        self.logger.info(f"  📱 Chat {i+1} (PRIMER CHAT FIJADO): '{chat_text}' [Procesando automáticamente]")
                        found_chats.append(chat_text or f"Chat #{i+1}")
                        
                        # Si contiene "Gastos" o es el primer chat sin texto claro, seleccionarlo
                        if not chat_text or chat_name.lower() in chat_text.lower():
                            self.logger.info(f"🎯 ¡PRIMER CHAT SELECCIONADO! Chat #{i+1}: '{chat_text or 'SIN_TEXTO'}' (CHAT FIJADO)")
                            return chat_element
                    elif chat_text:
                        found_chats.append(chat_text)
                        self.logger.info(f"  📱 Chat {i+1}: '{chat_text}'")
                        
                        # Buscar coincidencia exacta primero
                        if chat_name.lower() == chat_text.lower():
                            self.logger.info(f"🎯 ¡Chat encontrado (coincidencia exacta)! '{chat_text}'")
                            return chat_element
                            
                        # Buscar coincidencia parcial
                        elif chat_name.lower() in chat_text.lower():
                            self.logger.info(f"🎯 ¡Chat encontrado (coincidencia parcial)! '{chat_text}' contiene '{chat_name}'")
                            return chat_element
                    else:
                        self.logger.debug(f"  ❌ Chat {i+1}: Sin texto encontrado")
                        
                except Exception as e:
                    self.logger.debug(f"Error procesando chat {i+1}: {e}")
                    continue
            
            # Mostrar resumen de chats encontrados
            self.logger.error(f"❌ Chat '{chat_name}' no encontrado")
            self.logger.info(f"📱 Chats disponibles ({len(found_chats)}):")
            for chat in found_chats[:10]:  # Mostrar solo los primeros 10
                self.logger.info(f"  - '{chat}'")
            
            if len(found_chats) > 10:
                self.logger.info(f"  ... y {len(found_chats) - 10} chats más")
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error buscando chat: {e}")
            self.logger.error("Detalles del error:", exc_info=True)
            return None
    
    def _verify_chat_selected(self) -> bool:
        """Verifica que un chat está seleccionado y activo."""
        try:
            self.logger.info("🔍 Verificando que el chat se seleccionó correctamente...")
            
            # Múltiples selectores para el área de mensajes/chat activo
            chat_active_selectors = [
                "[data-testid='conversation-panel-messages']",
                "[data-testid='main']",
                "#main",
                "div[data-testid='chat-main']",
                "div._2_1wd",  # Área principal de chat
                "div[role='main']",
                "div[data-tab='1']",  # Pestaña activa
                ".app-wrapper-web",   # Wrapper principal
                "div._3q4NP",         # Contenedor de mensajes
                "footer[data-testid='conversation-compose']",  # Área de escritura
                "[data-testid='compose-box-input']",  # Caja de texto
                "div[contenteditable='true']"  # Área de entrada de texto
            ]
            
            for selector in chat_active_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        self.logger.info(f"✅ Chat activo verificado con selector: {selector}")
                        return True
                except NoSuchElementException:
                    continue
            
            # Verificación adicional: buscar elementos que indican chat activo
            try:
                # Buscar cualquier área de mensajes visible
                message_areas = self.driver.find_elements(By.CSS_SELECTOR, "div[role='application'] div[role='log']")
                if message_areas:
                    self.logger.info(f"✅ Encontradas {len(message_areas)} áreas de mensajes")
                    return True
            except:
                pass
            
            # Verificar si hay elementos de entrada de texto (indica chat activo)
            try:
                input_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[contenteditable], input[type='text']")
                visible_inputs = [elem for elem in input_elements if elem.is_displayed()]
                if visible_inputs:
                    self.logger.info(f"✅ Encontrados {len(visible_inputs)} elementos de entrada visibles")
                    return True
            except:
                pass
            
            self.logger.error("❌ No se pudo verificar que el chat esté seleccionado con ningún selector")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error verificando selección de chat: {e}")
            return False
    
    def _get_message_elements(self) -> List[object]:
        """Obtiene elementos de mensajes OPTIMIZADO - prioriza selector cacheado."""
        try:
            # ⚡ OPTIMIZACIÓN 1: Usar timeout muy corto para búsquedas
            self.driver.implicitly_wait(0.2)  # 200ms máximo
            
            try:
                # ⚡ OPTIMIZACIÓN 2: Si hay selector cacheado, usar DIRECTAMENTE
                if self.cached_selector:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, self.cached_selector)
                    if elements:
                        return self._filter_incoming_messages_fast(elements)
                    else:
                        # Selector cacheado falló, resetear
                        self.cached_selector = None
                
                # ⚡ OPTIMIZACIÓN AVANZADA: SmartSelectorCache (70% mejora esperada)
                elements = self.smart_cache.find_messages_optimized(self.driver)
                
                if elements and len(elements) > 0:
                    # Debug: mostrar estadísticas de cache para optimización
                    cache_stats = self.smart_cache.get_cache_stats()
                    self.logger.debug(f"📊 Cache stats - Selector activo: {cache_stats['cached_selector']}")
                    
                    return self._filter_incoming_messages_fast(elements)
                else:
                    self.logger.error("❌ SmartSelectorCache no encontró elementos")
                    return []
                
            finally:
                # Restaurar timeout original
                self.driver.implicitly_wait(2.0)
                
        except Exception as e:
            self.logger.error(f"❌ Error en _get_message_elements optimizado: {e}")
            return []
    
    def _filter_incoming_messages_fast(self, elements) -> List[object]:
        """Filtra mensajes entrantes de manera ultra rápida PERO EFECTIVA."""
        try:
            incoming = []
            
            # ⚡ OPTIMIZACIÓN: Procesar máximo 50 elementos más recientes
            # (los mensajes nuevos están al final)
            recent_elements = elements[-50:] if len(elements) > 50 else elements
            
            for element in recent_elements:
                try:
                    # ✅ FILTROS DE CALIDAD MEJORADOS
                    
                    # 1. Verificar que tiene texto válido
                    element_text = element.text.strip() if element.text else ""
                    if not element_text or len(element_text) < 4:
                        continue
                    
                    # 2. Verificar clases para filtrar mensajes salientes
                    classes = element.get_attribute("class") or ""
                    if "message-out" in classes:
                        continue  # Saltear nuestros mensajes
                    
                    # 3. Verificar que parece un mensaje real (no elementos de UI)
                    # Si contiene selectores típicos de mensajes
                    has_message_indicators = False
                    try:
                        # Buscar indicadores de que es un mensaje real
                        selectable_texts = element.find_elements(By.CSS_SELECTOR, ".selectable-text")
                        dir_elements = element.find_elements(By.CSS_SELECTOR, "[dir='auto'], [dir='ltr']")
                        
                        if selectable_texts or dir_elements:
                            has_message_indicators = True
                        
                        # O si el elemento tiene atributos típicos de mensaje
                        if element.get_attribute("data-id") or "message" in classes.lower():
                            has_message_indicators = True
                            
                    except:
                        # Si falla la verificación avanzada, usar criterio básico
                        has_message_indicators = len(element_text) > 10
                    
                    if has_message_indicators:
                        incoming.append(element)
                        
                except Exception as e:
                    # En caso de error, ser conservador y incluir el elemento
                    if element.text and len(element.text.strip()) > 10:
                        incoming.append(element)
                    continue
                    
            self.logger.debug(f"📊 Filtrado: {len(recent_elements)} → {len(incoming)} mensajes válidos")
            return incoming
            
        except Exception as e:
            self.logger.error(f"Error filtrando mensajes: {e}")
            return elements[-20:] if len(elements) > 20 else elements  # Devolver solo los más recientes si falla
    
    def _looks_like_message(self, element) -> bool:
        """Determina si un elemento parece ser un mensaje."""
        try:
            # Verificar si tiene texto
            text = element.text.strip()
            if not text:
                return False
            
            # Verificar si tiene atributos típicos de mensajes
            has_data_id = element.get_attribute("data-id") is not None
            has_message_class = "message" in (element.get_attribute("class") or "").lower()
            has_pre_text = element.get_attribute("data-pre-plain-text") is not None
            
            # Verificar si contiene elementos típicos de mensajes
            has_text_content = len([child for child in element.find_elements(By.CSS_SELECTOR, "*") 
                                   if child.text and len(child.text.strip()) > 0]) > 0
            
            return has_data_id or has_message_class or has_pre_text or (has_text_content and len(text) > 3)
            
        except:
            return False
    
    def _is_incoming_message(self, message_element) -> bool:
        """Determina si un mensaje es entrante (no enviado por nosotros)."""
        try:
            # Los mensajes propios tienen una clase específica
            classes = message_element.get_attribute("class") or ""
            return "message-out" not in classes
            
        except Exception:
            return False
    
    def _parse_message_element(self, element) -> Optional[Tuple[str, datetime]]:
        """
        Extrae texto y timestamp de un elemento de mensaje OPTIMIZADO PERO FUNCIONAL.
        
        Returns:
            Tupla (texto, fecha) o None si no se puede parsear
        """
        try:
            # Verificar accesibilidad básica
            try:
                _ = element.tag_name
            except:
                return None
            
            # Método 1: Intentar texto completo del elemento (más rápido)
            full_text = element.text.strip() if element.text else ""
            message_text = ""
            
            if full_text and len(full_text) > 3:
                # Filtrar líneas válidas y tomar la más larga como mensaje principal
                lines = [line.strip() for line in full_text.split('\n') if line.strip() and len(line.strip()) > 3]
                if lines:
                    # Evitar líneas que parecen metadatos (fechas, horas solas, etc.)
                    content_lines = [line for line in lines if not self._looks_like_metadata(line)]
                    if content_lines:
                        message_text = max(content_lines, key=len)
                    else:
                        message_text = max(lines, key=len)
            
            # Método 2: Si el método rápido no funciona, usar selectores específicos
            if not message_text:
                # Solo los selectores más efectivos para texto
                text_selectors = [
                    ".selectable-text",
                    "span[dir='auto']", 
                    "[data-testid='conversation-text']",
                    ".copyable-text"
                ]
                
                for selector in text_selectors:
                    try:
                        text_element = element.find_element(By.CSS_SELECTOR, selector)
                        if text_element and text_element.text:
                            text = text_element.text.strip()
                            if text and len(text) > 3:
                                message_text = text
                                break
                    except:
                        continue
            
            if not message_text:
                # DEBUG TEMPORAL: Ver qué está pasando
                element_html = element.get_attribute('outerHTML')[:200] if element.get_attribute('outerHTML') else "No HTML"
                self.logger.info(f"❌ NO SE PUDO EXTRAER TEXTO - Full Text: '{full_text}' - HTML: {element_html}...")
                return None
                
            # Extraer timestamp de manera rápida
            time_text = self._extract_timestamp_fast(element)
            message_time = self._parse_message_timestamp(time_text) if time_text else datetime.now()
            
            self.logger.info(f"✅ MENSAJE PARSEADO: '{message_text[:30]}...' @ {message_time.strftime('%H:%M:%S')}")
            return (message_text, message_time)
            
        except Exception:
            return None
    
    def _looks_like_metadata(self, text: str) -> bool:
        """Determina si una línea parece ser metadata en lugar de contenido del mensaje."""
        text = text.strip().lower()
        
        # Patrones que indican metadata
        metadata_patterns = [
            r'^\d{1,2}:\d{2}$',  # Solo hora "15:30"
            r'^\d{1,2}/\d{1,2}/\d{4}$',  # Solo fecha "06/08/2024"
            r'^(ayer|hoy|yesterday|today)$',  # Indicadores de tiempo
            r'^(enviado|received|sent|delivered)$',  # Estados de mensaje
        ]
        
        # Si es muy corto y contiene solo números/puntos, probablemente es metadata
        if len(text) < 5 and any(char in text for char in ':/-'):
            return True
            
        # Verificar patrones regex
        import re
        for pattern in metadata_patterns:
            if re.match(pattern, text):
                return True
                
        return False
    
    def _extract_text_with_selectors(self, element) -> str:
        """Extrae texto usando selectores específicos - MÉTODO RÁPIDO."""
        # ⚡ Solo los selectores más efectivos, en orden de probabilidad
        fast_selectors = [
            ".selectable-text",           # Más común
            "span[dir='auto']",          # Segundo más común  
            "[data-testid='conversation-text']",  # Específico
            ".copyable-text",            # Alternativo
        ]
        
        for selector in fast_selectors:
            try:
                text_element = element.find_element(By.CSS_SELECTOR, selector)
                if text_element:
                    text = text_element.text.strip()
                    if text and len(text) > 2:  # Filtro básico de calidad
                        return text
            except:
                continue
        
        return ""
    
    def _extract_timestamp_fast(self, element) -> str:
        """Extrae timestamp de manera super rápida."""
        # ⚡ Solo los métodos más rápidos y efectivos
        try:
            # Método 1: Buscar span con title (más común para timestamps)
            spans = element.find_elements(By.CSS_SELECTOR, "span[title]")
            for span in spans[:3]:  # Máximo 3 elementos
                title = span.get_attribute("title")
                if title and ':' in title and len(title) < 20:  # Filtro básico
                    return title
                    
            # Método 2: Buscar en metadata común
            meta = element.find_element(By.CSS_SELECTOR, "[data-testid='msg-meta']")
            if meta:
                meta_text = meta.text.strip()
                if ':' in meta_text:
                    return meta_text
                    
        except:
            pass
            
        return ""
    
    def _parse_message_timestamp(self, time_text: str) -> datetime:
        """
        Parsea el timestamp de un mensaje de WhatsApp.
        
        WhatsApp muestra timestamps en formatos como:
        - "15:30" (hoy)
        - "Ayer" 
        - "dd/mm/yyyy"
        """
        try:
            self.logger.debug(f"🕒 Parseando timestamp: '{time_text}'")
            
            # PRIMERA PRIORIDAD: Verificar "ayer" o similar
            time_pattern = r'(\d{1,2}):(\d{2})'
            if "ayer" in time_text.lower() or "yesterday" in time_text.lower():
                # Buscar tiempo en el texto
                time_match = re.search(time_pattern, time_text)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    now = datetime.now()
                    message_time = (now - timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
                    self.logger.debug(f"   📅 Mensaje de ayer: {message_time}")
                    return message_time
                else:
                    # Solo "ayer" sin hora específica
                    yesterday = datetime.now() - timedelta(days=1)
                    self.logger.debug(f"   📅 Ayer sin hora: {yesterday}")
                    return yesterday
            
            # SEGUNDA PRIORIDAD: Timestamp de hoy (formato HH:MM)
            match = re.search(time_pattern, time_text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                
                # Asumir que es de hoy
                now = datetime.now()
                message_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # ⚡ MEJORA: Verificar si debería ser de ayer
                # Si el mensaje es más de 2 horas en el futuro, probablemente es de ayer
                time_diff = message_time - now
                if time_diff.total_seconds() > 2 * 3600:  # 2 horas
                    message_time -= timedelta(days=1)
                    self.logger.debug(f"   ⏰ Ajustado a ayer: {message_time}")
                else:
                    self.logger.debug(f"   ⏰ Mantenido hoy: {message_time}")
                
                return message_time
            
            # Si no se puede parsear, usar tiempo actual
            fallback = datetime.now()
            self.logger.debug(f"   ⚠️ Fallback a ahora: {fallback}")
            return fallback
            
        except Exception as e:
            fallback = datetime.now()
            self.logger.debug(f"   ❌ Error parseando '{time_text}': {e}, usando {fallback}")
            return fallback
    
    def _is_new_message(self, message_time: datetime) -> bool:
        """Determina si un mensaje es nuevo basado en timestamp."""
        if not self.last_message_time:
            return True
            
        return message_time > self.last_message_time
    
    def _verify_connection(self) -> bool:
        """Verifica que la conexión a WhatsApp sigue activa."""
        try:
            # Verificar que el driver sigue activo
            if not self.driver:
                self.logger.warning("Driver no disponible")
                return False
            
            # Verificar que el driver responde
            try:
                current_url = self.driver.current_url
            except Exception as e:
                self.logger.error(f"Driver no responde: {e}")
                return False
                
            # Verificar que estamos en WhatsApp Web
            if "whatsapp.com" not in current_url.lower():
                self.logger.warning(f"No estamos en WhatsApp: {current_url}")
                return False
            if "web.whatsapp.com" not in current_url:
                return False
                
            # Verificar que la interfaz principal está presente
            chat_list = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='chat-list']")
            return chat_list is not None
            
        except Exception:
            return False
    
    def _cleanup_driver(self) -> None:
        """⚡ Cierre SÚPER RÁPIDO del driver Chrome - SIN timeouts de red."""
        if not self.driver:
            return
            
        try:
            # ⚡ MÉTODO DIRECTO: Solo quit, sin verificaciones
            import threading
            
            def instant_quit():
                try:
                    self.driver.quit()
                except:
                    pass  # Ignorar TODOS los errores de conexión
            
            # Thread daemon con timeout mínimo
            quit_thread = threading.Thread(target=instant_quit, daemon=True)
            quit_thread.start()
            quit_thread.join(timeout=0.3)  # Solo 300ms
            
            self.logger.info("⚡ Chrome quit ejecutado")
            
        except:
            pass  # Ignorar TODOS los errores
            
        finally:
            # Limpiar referencia SIEMPRE
            self.driver = None
    
    def __del__(self):
        """Destructor para asegurar limpieza de recursos."""
        self._cleanup_driver()