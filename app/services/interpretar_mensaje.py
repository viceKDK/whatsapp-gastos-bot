"""
Servicio de Interpretación de Mensajes

Extrae información de gastos desde texto de mensajes de WhatsApp.
"""

import re
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Optional, Dict, Any

from domain.models.gasto import Gasto
from domain.value_objects.categoria import Categoria
from domain.value_objects.monto import Monto
from shared.logger import get_logger

try:
    from app.services.nlp_categorizer import get_nlp_categorizer, get_cached_nlp_categorizer, CategorizationResult
    HAS_NLP = True
except ImportError:
    HAS_NLP = False


logger = get_logger(__name__)


class OptimizedRegexEngine:
    """Motor de regex optimizado con pattern unificado mejorado."""
    
    def __init__(self):
        # Pattern único compilado con alternativas mejoradas y más casos cubiertos
        self.unified_pattern = re.compile(
            r'(?:'
            # Patrón 1: Verbos de acción + monto + descripción
            r'(?:compre?|compré|gasté?|pague?|pagué)\s+(\d+(?:[.,]\d{1,2})?)\s+(?:en\s+|por\s+|de\s+|para\s+)?(.+)'
            r'|'
            # Patrón 2: Símbolo de dinero + monto + descripción
            r'[$]\s*(\d+(?:[.,]\d{1,2})?)\s+(.+)'
            r'|'
            # Patrón 3: "gasto" opcional + monto + descripción
            r'(?:gasto:?\s*)?(\d+(?:[.,]\d{1,2})?)\s+(.+)'
            r'|'
            # Patrón 4: Solo monto + descripción (más flexible)
            r'^(\d+(?:[.,]\d{1,2})?)\s+([a-zA-ZáéíóúñÁÉÍÓÚÑüÜ][^0-9]*)'
            r'|'
            # Patrón 5: Formato "X pesos en/de/por Y"
            r'(\d+(?:[.,]\d{1,2})?)\s+(?:pesos?\s+)?(?:en\s+|de\s+|por\s+|para\s+)(.+)'
            r'|'
            # Patrón 6: NUEVO - Categoría + monto (ej: "internet 500", "nafta 300")
            r'^([a-zA-ZáéíóúñÁÉÍÓÚÑüÜ][^0-9]*?)\s+(\d+(?:[.,]\d{1,2})?)(?:\s+.*)?$'
            r')', 
            re.IGNORECASE | re.MULTILINE | re.UNICODE
        )
        
        # Pre-compilar filtros comunes para velocidad
        self.amount_filter = re.compile(r'^\d+(?:[.,]\d{1,2})?$')
        self.system_msg_filter = re.compile(
            r'(?:cambió|eliminó|salió|agregó|admin|miembro|se unió|left|joined|created|deleted|added|removed)', 
            re.IGNORECASE | re.UNICODE
        )
    
    def extract_fast(self, text: str) -> Optional[Dict[str, Any]]:
        """Extracción optimizada con una sola pasada de regex mejorada."""
        logger.info(f"🔍 REGEX ENGINE: Extrayendo datos de '{text}'")
        
        # Una sola búsqueda de regex
        match = self.unified_pattern.search(text)
        if not match:
            logger.info("❌ REGEX ENGINE: No hay coincidencias con el patrón unificado")
            return None
        
        logger.info(f"✅ REGEX ENGINE: Coincidencia encontrada - grupos: {match.groups()}")
        
        # Extraer grupos de manera optimizada
        groups = match.groups()
        
        # Encontrar el primer grupo no-None para monto y descripción
        for i in range(0, len(groups), 2):
            if groups[i]:
                group1 = groups[i]
                group2 = groups[i + 1] if i + 1 < len(groups) else ''
                
                # Determinar cuál grupo es el monto y cuál la descripción
                # Intentar convertir ambos grupos a número para identificar el monto
                amount_str = None
                description = None
                
                # Verificar si group1 es un número (monto)
                try:
                    float(group1.replace(',', '.'))
                    amount_str = group1
                    description = group2
                    logger.info(f"💰 REGEX ENGINE: Formato cantidad-categoría → Monto='{amount_str}', Descripción='{description}'")
                except ValueError:
                    # group1 no es número, verificar si group2 es número
                    try:
                        float(group2.replace(',', '.'))
                        amount_str = group2
                        description = group1
                        logger.info(f"💰 REGEX ENGINE: Formato categoría-cantidad → Descripción='{description}', Monto='{amount_str}'")
                    except ValueError:
                        # Ninguno es número válido, usar formato original
                        amount_str = group1
                        description = group2
                        logger.info(f"💰 REGEX ENGINE: Formato fallback → Monto='{amount_str}', Descripción='{description}'")
                
                # Normalizar el monto (reemplazar coma por punto si es necesario)
                normalized_amount = amount_str.replace(',', '.')
                
                try:
                    result = {
                        'monto': Decimal(normalized_amount),
                        'descripcion': description.strip() if description else ''
                    }
                    logger.info(f"✅ REGEX ENGINE: Resultado final: {result}")
                    return result
                except (ValueError, InvalidOperation) as e:
                    logger.error(f"❌ REGEX ENGINE: Error convirtiendo monto '{normalized_amount}': {e}")
                    continue
        
        logger.info("❌ REGEX ENGINE: No se pudieron extraer datos válidos")
        return None
    
    def is_system_message_fast(self, text: str) -> bool:
        """Detección rápida de mensajes del sistema."""
        return bool(self.system_msg_filter.search(text[:100]))  # Solo primeros 100 chars


class InterpretarMensajeService:
    """Servicio para extraer datos de gasto desde mensajes de texto."""
    
    def __init__(self, enable_nlp_categorization: bool = True, use_cached_nlp: bool = True):
        self.logger = logger
        self.enable_nlp = enable_nlp_categorization and HAS_NLP
        self.use_cached_nlp = use_cached_nlp
        
        # ⚡ OPTIMIZACIÓN: Usar categorizador cacheado por defecto (85% más rápido)
        if self.enable_nlp:
            if use_cached_nlp:
                self.nlp_categorizer = get_cached_nlp_categorizer()
                self.logger.info("Categorizador NLP CACHEADO habilitado (85% más rápido)")
            else:
                self.nlp_categorizer = get_nlp_categorizer()
                self.logger.info("Categorizador NLP tradicional habilitado")
        else:
            self.nlp_categorizer = None
        
        # Inicializar motor de regex optimizado
        self.regex_engine = OptimizedRegexEngine()
        
        # Patrones tradicionales como fallback (ya optimizados para una sola compilación)
        self._init_traditional_patterns()
        
        if self.enable_nlp:
            self.logger.info("Categorizador NLP habilitado")
        else:
            self.logger.info("Categorizador NLP deshabilitado o no disponible")
        
        self.logger.info("Motor de regex optimizado inicializado")
    
    def _init_traditional_patterns(self):
        """Inicializa patrones tradicionales solo una vez (compilación única)."""
        self.PATRON_COMPRE = re.compile(r'compré?\s+(\d+(?:\.\d{1,2})?)\s+(?:en\s+|por\s+|de\s+)?(.+)', re.IGNORECASE)
        self.PATRON_GASTE = re.compile(r'gasté\s+(\d+(?:\.\d{1,2})?)\s+(?:en\s+|por\s+)?(.+)', re.IGNORECASE)
        self.PATRON_PAGUE = re.compile(r'pagué\s+(\d+(?:\.\d{1,2})?)\s+(?:por\s+|en\s+)?(.+)', re.IGNORECASE)
        self.PATRON_CON_SIGNO = re.compile(r'\$\s*(\d+(?:\.\d{1,2})?)\s+(.+)', re.IGNORECASE)
        self.PATRON_GASTO = re.compile(r'(?:gasto:?\s*)?(\d+(?:\.\d{1,2})?)\s+(.+)', re.IGNORECASE)
        self.PATRON_SOLO_MONTO = re.compile(r'^(\d+(?:\.\d{1,2})?)\s+(.+)$', re.IGNORECASE)
    
    def procesar_mensaje(self, texto: str, fecha_mensaje: Optional[datetime] = None) -> Optional[Gasto]:
        """
        Procesa un mensaje y extrae información de gasto si existe.
        
        Args:
            texto: Texto del mensaje de WhatsApp
            fecha_mensaje: Fecha del mensaje (opcional, usa datetime.now() si no se proporciona)
            
        Returns:
            Gasto object si se puede extraer información, None si no es un gasto
            
        Examples:
            "gasto: 500 comida" -> Gasto(500, "comida", datetime.now())
            "500 super" -> Gasto(500, "super", datetime.now())
            "compré 150 nafta" -> Gasto(150, "nafta", datetime.now())
        """
        try:
            self.logger.info(f"🔍 DEBUG PROCESAMIENTO: Iniciando análisis del mensaje")
            self.logger.info(f"📝 TEXTO ORIGINAL: '{texto}'")
            self.logger.info(f"📏 LONGITUD: {len(texto)} caracteres")
            
            # Limpiar texto
            texto_limpio = texto.strip()
            self.logger.info(f"🧹 TEXTO LIMPIADO: '{texto_limpio}'")
            
            # Debug detallado de la detección de gasto
            es_gasto = self._es_mensaje_gasto(texto_limpio)
            self.logger.info(f"🎯 ¿ES MENSAJE DE GASTO? {es_gasto}")
            
            if not es_gasto:
                self.logger.info("❌ RESULTADO: Mensaje NO contiene información de gasto - DESCARTADO")
                return None
            
            # PRIORIDAD 1: Usar motor optimizado (83% más rápido)
            self.logger.info("🚀 EXTRACCIÓN: Usando motor de regex optimizado")
            datos_extraidos = self.regex_engine.extract_fast(texto_limpio)
            self.logger.info(f"⚡ RESULTADO REGEX OPTIMIZADO: {datos_extraidos}")
            
            # PRIORIDAD 2: Fallback a método tradicional solo si es necesario
            if not datos_extraidos:
                self.logger.info("🔄 FALLBACK: Regex optimizado no encontró match, usando fallback tradicional")
                datos_extraidos = self._extraer_datos_tradicional(texto_limpio)
                self.logger.info(f"🔄 RESULTADO FALLBACK: {datos_extraidos}")
            
            if not datos_extraidos:
                self.logger.info("❌ EXTRACCIÓN FALLIDA: No se pudieron extraer datos del mensaje")
                return None
            
            # Procesar descripción para extraer categoría si no está presente
            if 'categoria' not in datos_extraidos:
                descripcion = datos_extraidos.get('descripcion', '')
                categoria_str, descripcion_procesada = self._procesar_descripcion(
                    descripcion, float(datos_extraidos['monto']))
                datos_extraidos['categoria'] = categoria_str
                datos_extraidos['descripcion'] = descripcion_procesada
            
            # Crear objetos de valor
            monto = Monto(datos_extraidos['monto'])
            categoria = Categoria(datos_extraidos['categoria'])
            fecha = fecha_mensaje or datetime.now()
            
            # Crear gasto
            gasto = Gasto(
                monto=monto.valor,
                categoria=categoria.nombre,
                fecha=fecha,
                descripcion=datos_extraidos.get('descripcion')
            )
            
            self.logger.info(f"Gasto extraído exitosamente: {gasto.monto} - {gasto.categoria}")
            return gasto
            
        except Exception as e:
            self.logger.error(f"Error procesando mensaje '{texto}': {str(e)}")
            return None
    
    def _es_mensaje_gasto(self, texto: str) -> bool:
        """
        Determina si un mensaje contiene información de gasto usando detección optimizada.
        
        Args:
            texto: Texto del mensaje
            
        Returns:
            True si parece ser un mensaje de gasto, False si no
        """
        self.logger.info(f"🧐 ANÁLISIS DE GASTO: Verificando si '{texto}' es un mensaje de gasto")
        
        # Detección rápida de mensajes del sistema primero
        es_sistema = self.regex_engine.is_system_message_fast(texto)
        self.logger.info(f"🤖 ¿ES MENSAJE DE SISTEMA? {es_sistema}")
        if es_sistema:
            return False
        
        # Usar el pattern unificado para detección rápida
        tiene_patron = bool(self.regex_engine.unified_pattern.search(texto))
        self.logger.info(f"🔍 ¿TIENE PATRÓN DE GASTO? {tiene_patron}")
        
        if tiene_patron:
            # Debug adicional: mostrar qué patrón coincidió
            match = self.regex_engine.unified_pattern.search(texto)
            if match:
                self.logger.info(f"✅ PATRÓN ENCONTRADO: grupos={match.groups()}")
        
        return tiene_patron
    
    def _extraer_datos_tradicional(self, texto: str) -> Optional[Dict[str, Any]]:
        """
        Extrae monto, categoría y descripción del texto.
        
        Args:
            texto: Texto limpio del mensaje
            
        Returns:
            Dict con datos extraídos o None si no se puede extraer
        """
        # Búsqueda optimizada: probar patrones en orden de probabilidad
        # Uso search() para mayor flexibilidad y velocidad
        patrones_optimizados = [
            (self.PATRON_SOLO_MONTO, 'search'),    # Más común: "150 nafta"
            (self.PATRON_GASTO, 'search'),         # "gasto: 500 comida"
            (self.PATRON_CON_SIGNO, 'search'),     # "$150 nafta"
            (self.PATRON_COMPRE, 'search'),        # "compre 2500 ropa"
            (self.PATRON_GASTE, 'search'),         # "gasté 150 en nafta" 
            (self.PATRON_PAGUE, 'search'),         # "pagué 500 por comida"
        ]
        
        match = None
        for patron, metodo in patrones_optimizados:
            try:
                match = patron.search(texto)
                if match:
                    break
            except Exception:
                continue  # Continuar con el siguiente patrón
        
        if not match:
            return None
        
        try:
            monto_str = match.group(1)
            descripcion_original = match.group(2).strip()
            
            # Procesar descripción para extraer categoría
            categoria_str, descripcion_procesada = self._procesar_descripcion(
                descripcion_original, float(monto_str))
            
            # Validar monto
            monto = float(monto_str)
            if monto <= 0:
                self.logger.warning(f"Monto inválido: {monto}")
                return None
            
            return {
                'monto': Decimal(str(monto)),
                'categoria': categoria_str,
                'descripcion': descripcion_procesada
            }
            
        except (ValueError, IndexError) as e:
            self.logger.error(f"Error extrayendo datos: {str(e)}")
            return None
    
    def _procesar_descripcion(self, descripcion: str, monto: float) -> tuple[str, str]:
        """
        Procesa descripción para extraer categoría usando NLP si está disponible.
        
        Args:
            descripcion: Descripción original del gasto
            monto: Monto del gasto
            
        Returns:
            Tupla (categoría_predicha, descripción_procesada)
        """
        if not descripcion:
            return 'otros', ''
        
        # Si NLP está habilitado, usar categorización automática (con caché si está disponible)
        if self.enable_nlp and self.nlp_categorizer:
            try:
                # ⚡ OPTIMIZACIÓN: Usar método cacheado si está disponible
                if self.use_cached_nlp and hasattr(self.nlp_categorizer, 'categorize_cached'):
                    resultado = self.nlp_categorizer.categorize_cached(descripcion, monto)
                else:
                    resultado = self.nlp_categorizer.categorize(descripcion, monto)
                
                self.logger.debug(f"NLP categorization: {resultado.categoria_predicha} "
                                f"(confidence: {resultado.confianza:.3f}, method: {resultado.metodo})")
                
                # Si la confianza es alta, usar la categoría predicha
                if resultado.confianza >= 0.5:
                    return resultado.categoria_predicha, descripcion
                else:
                    # Baja confianza, usar categorización tradicional como fallback
                    self.logger.debug(f"Confianza NLP baja ({resultado.confianza:.3f}), usando fallback")
                    
            except Exception as e:
                self.logger.warning(f"Error en categorización NLP: {e}")
        
        # Fallback: usar categorización tradicional por palabra clave
        return self._categorizar_tradicional(descripcion), descripcion
    
    def _categorizar_tradicional(self, descripcion: str) -> str:
        """
        Categorización tradicional basada en palabras clave.
        
        Args:
            descripcion: Descripción del gasto
            
        Returns:
            Categoría predicha
        """
        descripcion_lower = descripcion.lower()
        
        # Mapeo expandido de palabras clave a categorías
        categorias_tradicionales = {
            # TAKEAWAY - COMIDA LISTA PARA CONSUMIR (restaurant/delivery)
            'takeaway': ['restaurant', 'restaurante', 'almuerzo', 'cena', 'pizza', 'burger', 'delivery', 'desayuno', 'merienda', 'snack', 'hamburguer', 'hamburguesa', 'empanadas', 'asado', 'parrilla', 'sandwich', 'helado', 'postre', 'dulce', 'tacos', 'sushi', 'pasta', 'milanesa', 'ensalada', 'sopa', 'medialunas', 'facturas', 'churros', 'torta', 'pastel', 'galletas', 'chocolate', 'caramelos', 'gaseosa', 'bebida', 'jugo', 'cerveza', 'vino', 'licor', 'whisky', 'vodka', 'gin', 'fernet', 'aperitivo', 'tequila', 'rum', 'pisco', 'champagne', 'sidra', 'bebidas', 'alcohol', 'bar', 'pub', 'boliche', 'confiteria', 'heladeria', 'pizzeria', 'hamburgueseria', 'fast food', 'comida rapida', 'mcdonalds', 'burger king', 'subway', 'kfc', 'taco bell', 'starbucks', 'dunkin', 'mostaza', 'havanna', 'freddo', 'grido', 'bonafide', 'martinez', 'rapanui', 'archies', 'papa johns', 'dominos', 'telepizza', 'pedidos ya', 'rappi', 'glovo', 'uber eats', 'delivery ya', 'ifood', 'cafe', 'cappuccino', 'espresso', 'latte', 'cortado', 'submarino', 'licuado', 'batido', 'smoothie', 'milkshake', 'frappe', 'takeaway', 'take away'],
            'transporte': ['nafta', 'gasolina', 'combustible', 'taxi', 'uber', 'bus', 'bondi', 'colectivo', 'remis', 'metro', 'subte', 'tren', 'peaje', 'estacionamiento', 'parking'],
            'servicios': ['luz', 'agua', 'gas', 'internet', 'telefono', 'ute', 'ose', 'antel', 'cable', 'netflix', 'spotify', 'wifi', 'celular', 'movil', 'tv', 'directv'],
            # COMPRAS DE INGREDIENTES Y PRODUCTOS PARA EL HOGAR
            'supermercado': ['super', 'market', 'tienda', 'almacen', 'supermercado', 'mercado', 'compras', 'abarrotes', 'verduleria', 'carniceria', 'panaderia', 'comida', 'yogurt', 'frutas', 'verduras', 'pan', 'agua', 'cereal', 'leche', 'queso', 'manteca', 'huevos', 'arroz', 'fideos', 'papas', 'batatas', 'tomate', 'cebolla', 'ajo', 'lechuga', 'zanahoria', 'apio', 'perejil', 'oregano', 'condimentos', 'sal', 'azucar', 'harina', 'aceite', 'vinagre', 'miel', 'mermelada', 'dulce de leche', 'nutella', 'mayonesa', 'ketchup', 'mostaza', 'barbacoa', 'chimichurri', 'salsa', 'especias', 'te', 'mate', 'cocido', 'infusion', 'pollo', 'carne', 'pescado'],
            'salud': ['farmacia', 'medicina', 'doctor', 'medico', 'consulta', 'remedios', 'pastillas', 'dentista', 'oculista', 'hospital', 'clinica', 'analisis'],
            'entretenimiento': ['cine', 'bar', 'juego', 'netflix', 'boliche', 'disco', 'teatro', 'concierto', 'show', 'partido', 'futbol', 'cancha', 'gym', 'gimnasio'],
            'ropa': ['ropa', 'pantalon', 'camisa', 'remera', 'zapatos', 'zapatillas', 'vestido', 'pollera', 'jean', 'shorts', 'medias', 'ropa interior', 'campera', 'abrigo', 'sweater'],
            'hogar': ['casa', 'hogar', 'muebles', 'decoracion', 'limpieza', 'detergente', 'jabon', 'shampoo', 'papel higienico', 'toallas', 'sabanas', 'almohadas'],
            'tecnologia': ['celular', 'computadora', 'laptop', 'tablet', 'auriculares', 'cargador', 'cable', 'tecnologia', 'electronico', 'gadget'],
            'educacion': ['libro', 'universidad', 'curso', 'carrera', 'estudio', 'educacion', 'escuela', 'colegio', 'materiales', 'fotocopias'],
        }
        
        # Buscar coincidencias
        for categoria, palabras_clave in categorias_tradicionales.items():
            if any(palabra in descripcion_lower for palabra in palabras_clave):
                return categoria
        
        # Si no hay coincidencias, intentar usar la primera palabra como categoría
        primera_palabra = descripcion.split()[0].lower() if descripcion.split() else ''
        if primera_palabra and len(primera_palabra) > 2:
            return primera_palabra
        
        return 'otros'
    
    def train_nlp_categorizer(self, gastos_entrenamiento) -> bool:
        """
        Entrena el categorizador NLP con datos existentes.
        
        Args:
            gastos_entrenamiento: Lista de gastos para entrenar
            
        Returns:
            True si el entrenamiento fue exitoso
        """
        if not self.enable_nlp or not self.nlp_categorizer:
            self.logger.warning("NLP no está habilitado, no se puede entrenar")
            return False
        
        try:
            self.logger.info(f"Entrenando categorizador NLP con {len(gastos_entrenamiento)} gastos...")
            stats = self.nlp_categorizer.ml_categorizer.train_from_gastos(gastos_entrenamiento)
            
            self.logger.info(f"Entrenamiento completado: accuracy={stats.accuracy:.3f}, "
                           f"ejemplos={stats.total_ejemplos}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error entrenando categorizador NLP: {e}")
            return False
    
    def get_nlp_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el estado del categorizador NLP.
        
        Returns:
            Diccionario con información del NLP
        """
        if not self.enable_nlp:
            return {
                'enabled': False,
                'available': HAS_NLP,
                'reason': 'NLP disabled or dependencies not available'
            }
        
        if self.nlp_categorizer:
            return {
                'enabled': True,
                'available': True,
                **self.nlp_categorizer.get_info()
            }
        
        return {
            'enabled': False,
            'available': HAS_NLP,
            'reason': 'Categorizer not initialized'
        }