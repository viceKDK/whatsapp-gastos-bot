"""
Servicio de Interpretación de Mensajes

Extrae información de gastos desde texto de mensajes de WhatsApp.
"""

import re
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any

from domain.models.gasto import Gasto
from domain.value_objects.categoria import Categoria
from domain.value_objects.monto import Monto
from shared.logger import get_logger

try:
    from app.services.nlp_categorizer import get_nlp_categorizer, CategorizationResult
    HAS_NLP = True
except ImportError:
    HAS_NLP = False


logger = get_logger(__name__)


class InterpretarMensajeService:
    """Servicio para extraer datos de gasto desde mensajes de texto."""
    
    # Patrones regex para extraer información
    PATRON_GASTO = re.compile(r'(?:gasto|gasté|pagué|compré)?\s*:?\s*(\d+(?:\.\d{1,2})?)\s+(.+)', re.IGNORECASE)
    PATRON_SOLO_MONTO = re.compile(r'^(\d+(?:\.\d{1,2})?)\s+(.+)$', re.IGNORECASE)
    PATRON_MONTO_DESCRIPCION = re.compile(r'(\d+(?:\.\d{1,2})?)\s+(.+)', re.IGNORECASE)
    # Nuevos patrones ampliados
    PATRON_COMPRE = re.compile(r'compre?\s+(\d+(?:\.\d{1,2})?)\s+(.+)', re.IGNORECASE)  # "compre 2500 ropa"
    PATRON_GASTE = re.compile(r'(?:gaste|gasté)\s+(\d+(?:\.\d{1,2})?)\s+(?:en\s+)?(.+)', re.IGNORECASE)  # "gasté 150 en nafta"
    PATRON_PAGUE = re.compile(r'(?:pague|pagué)\s+(\d+(?:\.\d{1,2})?)\s+(?:por\s+|de\s+)?(.+)', re.IGNORECASE)  # "pagué 500 por comida"
    PATRON_CON_SIGNO = re.compile(r'[$$]\s*(\d+(?:\.\d{1,2})?)\s+(.+)', re.IGNORECASE)  # "$150 nafta"
    
    def __init__(self, enable_nlp_categorization: bool = True):
        self.logger = logger
        self.enable_nlp = enable_nlp_categorization and HAS_NLP
        self.nlp_categorizer = get_nlp_categorizer() if self.enable_nlp else None
        
        if self.enable_nlp:
            self.logger.info("Categorizador NLP habilitado")
        else:
            self.logger.info("Categorizador NLP deshabilitado o no disponible")
    
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
            self.logger.debug(f"Procesando mensaje: {texto}")
            
            # Limpiar texto
            texto_limpio = texto.strip()
            
            if not self._es_mensaje_gasto(texto_limpio):
                self.logger.debug("Mensaje no parece contener información de gasto")
                return None
            
            # Extraer monto y categoría
            datos_extraidos = self._extraer_datos(texto_limpio)
            
            if not datos_extraidos:
                self.logger.debug("No se pudieron extraer datos del mensaje")
                return None
            
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
        Determina si un mensaje contiene información de gasto.
        
        Args:
            texto: Texto del mensaje
            
        Returns:
            True si parece ser un mensaje de gasto, False si no
        """
        palabras_clave = ['gasto', 'gasté', 'pagué', 'compré', 'compre', 'gaste', 'pague']
        texto_lower = texto.lower()
        
        # Buscar palabras clave o patrón numérico
        tiene_palabra_clave = any(palabra in texto_lower for palabra in palabras_clave)
        tiene_patron_numerico = bool(self.PATRON_SOLO_MONTO.match(texto))
        tiene_signo_pesos = '$' in texto and any(char.isdigit() for char in texto)
        
        return tiene_palabra_clave or tiene_patron_numerico or tiene_signo_pesos
    
    def _extraer_datos(self, texto: str) -> Optional[Dict[str, Any]]:
        """
        Extrae monto, categoría y descripción del texto.
        
        Args:
            texto: Texto limpio del mensaje
            
        Returns:
            Dict con datos extraídos o None si no se puede extraer
        """
        # Lista de patrones a probar en orden
        patrones = [
            self.PATRON_COMPRE,        # "compre 2500 ropa"
            self.PATRON_GASTE,         # "gasté 150 en nafta" 
            self.PATRON_PAGUE,         # "pagué 500 por comida"
            self.PATRON_CON_SIGNO,     # "$150 nafta"
            self.PATRON_GASTO,         # "gasto: 500 comida"
            self.PATRON_SOLO_MONTO,    # "150 nafta"
        ]
        
        match = None
        for patron in patrones:
            if patron == self.PATRON_GASTO:
                match = patron.search(texto)
            else:
                match = patron.match(texto)
            if match:
                break
        
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
        
        # Si NLP está habilitado, usar categorización automática
        if self.enable_nlp and self.nlp_categorizer:
            try:
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
            'comida': ['comida', 'restaurant', 'almuerzo', 'cena', 'pizza', 'burger', 'delivery', 'desayuno', 'merienda', 'snack', 'hamburguer', 'empanadas', 'asado', 'parrilla', 'sandwich', 'cafe', 'yogurt', 'frutas', 'verduras'],
            'transporte': ['nafta', 'gasolina', 'combustible', 'taxi', 'uber', 'bus', 'bondi', 'colectivo', 'remis', 'metro', 'subte', 'tren', 'peaje', 'estacionamiento', 'parking'],
            'servicios': ['luz', 'agua', 'gas', 'internet', 'telefono', 'ute', 'ose', 'antel', 'cable', 'netflix', 'spotify', 'wifi', 'celular', 'movil', 'tv', 'directv'],
            'supermercado': ['super', 'market', 'tienda', 'almacen', 'supermercado', 'mercado', 'compras', 'abarrotes', 'verduleria', 'carniceria', 'panaderia'],
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