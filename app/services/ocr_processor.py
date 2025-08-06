"""
Procesador OCR para Recibos

Extrae información de gastos desde imágenes de recibos usando OCR.
"""

import re
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

from config.config_manager import get_config
from shared.logger import get_logger
from shared.validators import validate_gasto, ValidationLevel
from domain.models.gasto import Gasto


logger = get_logger(__name__)


@dataclass
class OCRResult:
    """Resultado del procesamiento OCR."""
    success: bool
    extracted_text: str = ""
    confidence: float = 0.0
    detected_amounts: List[float] = None
    detected_categories: List[str] = None
    detected_dates: List[datetime] = None
    suggested_gasto: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_seconds: float = 0.0
    
    def __post_init__(self):
        if self.detected_amounts is None:
            self.detected_amounts = []
        if self.detected_categories is None:
            self.detected_categories = []
        if self.detected_dates is None:
            self.detected_dates = []


class ImagePreprocessor:
    """Preprocesador de imágenes para mejorar OCR."""
    
    def __init__(self):
        self.logger = logger
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocesa imagen para mejorar la calidad del OCR.
        
        Args:
            image_path: Ruta de la imagen
            
        Returns:
            Imagen preprocesada como array numpy
        """
        try:
            # Cargar imagen
            image = cv2.imread(image_path)
            
            if image is None:
                raise ValueError(f"No se pudo cargar la imagen: {image_path}")
            
            # Pipeline de preprocesamiento
            processed = self._resize_image(image)
            processed = self._denoise_image(processed)
            processed = self._enhance_contrast(processed)
            processed = self._convert_to_grayscale(processed)
            processed = self._apply_threshold(processed)
            processed = self._morphological_operations(processed)
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Error preprocesando imagen: {e}")
            # Retornar imagen original en escala de grises como fallback
            return cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2GRAY)
    
    def _resize_image(self, image: np.ndarray) -> np.ndarray:
        """Redimensiona imagen para mejorar OCR."""
        height, width = image.shape[:2]
        
        # Si la imagen es muy pequeña, aumentarla
        if width < 800:
            scale_factor = 800 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Si es muy grande, reducirla
        elif width > 2000:
            scale_factor = 2000 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return image
    
    def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """Reduce ruido de la imagen."""
        return cv2.fastNlMeansDenoisingColored(image)
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Mejora el contraste de la imagen."""
        # Convertir a LAB para mejorar luminancia
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Aplicar CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Recombinar canales
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    def _convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convierte a escala de grises."""
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    def _apply_threshold(self, image: np.ndarray) -> np.ndarray:
        """Aplica umbralización adaptiva."""
        return cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    
    def _morphological_operations(self, image: np.ndarray) -> np.ndarray:
        """Aplica operaciones morfológicas para limpiar la imagen."""
        # Crear kernel para operaciones morfológicas
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        
        # Operación de apertura para eliminar ruido
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        
        # Operación de cierre para conectar elementos
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        
        return image


class TextExtractor:
    """Extractor de texto usando OCR."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logger
        
        # Configurar Tesseract si está disponible
        if HAS_OCR:
            self._configure_tesseract()
    
    def _configure_tesseract(self):
        """Configura parámetros de Tesseract."""
        try:
            # Configurar ruta de Tesseract si está especificada
            tesseract_path = getattr(self.config.ocr, 'tesseract_path', None)
            if tesseract_path and Path(tesseract_path).exists():
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
        except Exception as e:
            self.logger.warning(f"Error configurando Tesseract: {e}")
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrae texto de imagen usando OCR.
        
        Args:
            image: Imagen preprocesada
            
        Returns:
            Tupla (texto_extraído, confianza)
        """
        if not HAS_OCR:
            raise RuntimeError("pytesseract no está instalado")
        
        try:
            # Configurar parámetros de OCR
            ocr_config = self._get_ocr_config()
            
            # Extraer texto
            text = pytesseract.image_to_string(image, config=ocr_config)
            
            # Obtener datos detallados incluyendo confianza
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=ocr_config)
            
            # Calcular confianza promedio
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return text.strip(), avg_confidence / 100.0  # Normalizar a 0-1
            
        except Exception as e:
            self.logger.error(f"Error extrayendo texto: {e}")
            return "", 0.0
    
    def _get_ocr_config(self) -> str:
        """Obtiene configuración de OCR."""
        # Configurar idioma
        language = getattr(self.config.ocr, 'language', 'spa+eng')
        
        # Configurar PSM (Page Segmentation Mode)
        psm = 6  # Uniform block of text
        
        # Configurar OEM (OCR Engine Mode)
        oem = 3  # Default (legacy + LSTM)
        
        return f'-l {language} --oem {oem} --psm {psm}'


class ReceiptAnalyzer:
    """Analizador de recibos para extraer información estructurada."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logger
        
        # Patrones de expresiones regulares
        self.amount_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
            r'(\d{1,3}(?:,\d{3})*\.\d{2})\s*\$',      # 1,234.56 $
            r'TOTAL:?\s*\$?\s*(\d+(?:\.\d{2})?)',      # TOTAL: $123.45
            r'TOTAL\s+(\d+(?:\.\d{2})?)',              # TOTAL 123.45
            r'(\d+\.\d{2})\s*$',                       # 123.45 al final de línea
        ]
        
        self.date_patterns = [
            r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',     # DD/MM/YYYY
            r'(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})',       # YYYY/MM/DD
            r'(\d{1,2}\s+\w+\s+\d{4})',               # 15 Enero 2024
        ]
        
        # Categorías comunes en recibos
        self.category_keywords = {
            'comida': ['restaurant', 'comida', 'food', 'cafe', 'pizza', 'burger', 'taco', 'lunch', 'dinner'],
            'transporte': ['gasolina', 'gas', 'combustible', 'taxi', 'uber', 'metro', 'bus'],
            'supermercado': ['super', 'market', 'walmart', 'soriana', 'oxxo', 'seven', '7-eleven'],
            'farmacia': ['farmacia', 'pharmacy', 'medicina', 'drug', 'cvs', 'walgreens'],
            'ropa': ['clothing', 'ropa', 'shirt', 'pants', 'shoes', 'fashion'],
            'entretenimiento': ['cine', 'movie', 'theater', 'game', 'juego'],
            'servicios': ['service', 'servicio', 'repair', 'reparacion', 'maintenance']
        }
    
    def analyze_receipt(self, text: str) -> Dict[str, Any]:
        """
        Analiza texto de recibo para extraer información estructurada.
        
        Args:
            text: Texto extraído del recibo
            
        Returns:
            Diccionario con información extraída
        """
        try:
            result = {
                'amounts': self._extract_amounts(text),
                'dates': self._extract_dates(text),
                'categories': self._detect_categories(text),
                'merchant': self._extract_merchant(text),
                'items': self._extract_items(text)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analizando recibo: {e}")
            return {}
    
    def _extract_amounts(self, text: str) -> List[float]:
        """Extrae montos del texto."""
        amounts = []
        
        for pattern in self.amount_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    if 0.01 <= amount <= 10000:  # Filtrar montos razonables
                        amounts.append(amount)
                except (ValueError, IndexError):
                    continue
        
        # Eliminar duplicados y ordenar
        return sorted(list(set(amounts)), reverse=True)
    
    def _extract_dates(self, text: str) -> List[datetime]:
        """Extrae fechas del texto."""
        dates = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    date_str = match.group(1)
                    parsed_date = self._parse_date(date_str)
                    if parsed_date:
                        dates.append(parsed_date)
                except (ValueError, IndexError):
                    continue
        
        return dates
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parsea string de fecha en varios formatos."""
        formats = [
            '%d/%m/%Y', '%d-%m-%Y',
            '%m/%d/%Y', '%m-%d-%Y',
            '%Y/%m/%d', '%Y-%m-%d',
            '%d/%m/%y', '%d-%m-%y',
            '%m/%d/%y', '%m-%d-%y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _detect_categories(self, text: str) -> List[str]:
        """Detecta categorías basadas en palabras clave."""
        detected = []
        text_lower = text.lower()
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(category)
                    break
        
        return detected
    
    def _extract_merchant(self, text: str) -> Optional[str]:
        """Extrae nombre del comercio."""
        lines = text.strip().split('\n')
        
        # Usualmente el nombre del comercio está en las primeras líneas
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 3 and not line.isdigit():
                # Filtrar líneas que parecen direcciones o números
                if not re.match(r'^\d+\s+\w+', line) and not re.match(r'^[\d\s\-\(\)]+$', line):
                    return line
        
        return None
    
    def _extract_items(self, text: str) -> List[str]:
        """Extrae lista de items del recibo."""
        items = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Buscar líneas que contengan items (tienen precio al final)
            if re.search(r'\d+\.\d{2}\s*$', line):
                # Remover el precio y limpiar el texto
                item_text = re.sub(r'\s+\d+\.\d{2}\s*$', '', line).strip()
                if len(item_text) > 2:
                    items.append(item_text)
        
        return items[:10]  # Limitar a 10 items


class OCRProcessor:
    """Procesador principal de OCR para recibos."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logger
        self.preprocessor = ImagePreprocessor()
        self.text_extractor = TextExtractor()
        self.analyzer = ReceiptAnalyzer()
        
        # Verificar si OCR está habilitado
        self.ocr_enabled = getattr(self.config.ocr, 'enabled', True) and HAS_OCR
        
        if not self.ocr_enabled and HAS_OCR is False:
            self.logger.warning("OCR deshabilitado: pytesseract no está instalado")
    
    def process_receipt_image(self, image_path: str) -> OCRResult:
        """
        Procesa imagen de recibo completo.
        
        Args:
            image_path: Ruta de la imagen
            
        Returns:
            Resultado del procesamiento OCR
        """
        start_time = datetime.now()
        
        if not self.ocr_enabled:
            return OCRResult(
                success=False,
                error_message="OCR no está habilitado o pytesseract no está instalado"
            )
        
        try:
            # Verificar que el archivo existe
            if not Path(image_path).exists():
                return OCRResult(
                    success=False,
                    error_message=f"Archivo no encontrado: {image_path}"
                )
            
            # Verificar formato de imagen soportado
            supported_formats = getattr(self.config.ocr, 'supported_formats', ['.jpg', '.jpeg', '.png', '.pdf'])
            if not any(image_path.lower().endswith(fmt) for fmt in supported_formats):
                return OCRResult(
                    success=False,
                    error_message=f"Formato de imagen no soportado. Formatos válidos: {supported_formats}"
                )
            
            # Preprocesar imagen
            self.logger.debug(f"Preprocesando imagen: {image_path}")
            
            if getattr(self.config.ocr, 'preprocessing_enabled', True):
                processed_image = self.preprocessor.preprocess_image(image_path)
            else:
                # Cargar imagen sin preprocesamiento
                processed_image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2GRAY)
            
            # Extraer texto
            self.logger.debug("Extrayendo texto con OCR")
            text, confidence = self.text_extractor.extract_text(processed_image)
            
            if not text.strip():
                return OCRResult(
                    success=False,
                    error_message="No se pudo extraer texto de la imagen",
                    confidence=confidence
                )
            
            # Verificar confianza mínima
            min_confidence = getattr(self.config.ocr, 'confidence_threshold', 0.6)
            if confidence < min_confidence:
                self.logger.warning(f"Confianza OCR baja: {confidence:.2f} < {min_confidence}")
            
            # Analizar texto extraído
            self.logger.debug("Analizando texto extraído")
            analysis = self.analyzer.analyze_receipt(text)
            
            # Crear sugerencia de gasto
            suggested_gasto = self._create_suggested_gasto(analysis, text)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return OCRResult(
                success=True,
                extracted_text=text,
                confidence=confidence,
                detected_amounts=analysis.get('amounts', []),
                detected_categories=analysis.get('categories', []),
                detected_dates=analysis.get('dates', []),
                suggested_gasto=suggested_gasto,
                processing_time_seconds=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error procesando imagen OCR: {e}")
            
            return OCRResult(
                success=False,
                error_message=str(e),
                processing_time_seconds=processing_time
            )
    
    def _create_suggested_gasto(self, analysis: Dict[str, Any], text: str) -> Optional[Dict[str, Any]]:
        """Crea sugerencia de gasto basada en el análisis."""
        try:
            amounts = analysis.get('amounts', [])
            categories = analysis.get('categories', [])
            dates = analysis.get('dates', [])
            merchant = analysis.get('merchant', '')
            
            if not amounts:
                return None
            
            # Usar el monto más probable (usualmente el más grande)
            suggested_amount = amounts[0]
            
            # Usar la primera categoría detectada o 'otros'
            suggested_category = categories[0] if categories else 'otros'
            
            # Usar la fecha detectada o fecha actual
            suggested_date = dates[0] if dates else datetime.now()
            
            # Crear descripción
            description_parts = []
            if merchant:
                description_parts.append(merchant)
            
            items = analysis.get('items', [])
            if items:
                description_parts.extend(items[:3])  # Máximo 3 items
            
            suggested_description = ', '.join(description_parts)[:100]  # Limitar longitud
            
            suggested_gasto = {
                'monto': suggested_amount,
                'categoria': suggested_category,
                'fecha': suggested_date,
                'descripcion': suggested_description or None
            }
            
            # Validar sugerencia
            validation_result = validate_gasto(suggested_gasto, ValidationLevel.LENIENT)
            
            if validation_result.is_valid:
                return suggested_gasto
            else:
                self.logger.warning(f"Gasto sugerido no es válido: {validation_result.errors}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creando sugerencia de gasto: {e}")
            return None
    
    def process_multiple_images(self, image_paths: List[str]) -> List[OCRResult]:
        """
        Procesa múltiples imágenes de recibos.
        
        Args:
            image_paths: Lista de rutas de imágenes
            
        Returns:
            Lista de resultados OCR
        """
        results = []
        
        for image_path in image_paths:
            self.logger.info(f"Procesando imagen: {image_path}")
            result = self.process_receipt_image(image_path)
            results.append(result)
        
        return results
    
    def get_ocr_info(self) -> Dict[str, Any]:
        """
        Obtiene información del sistema OCR.
        
        Returns:
            Información del OCR
        """
        info = {
            'ocr_available': HAS_OCR,
            'ocr_enabled': self.ocr_enabled,
            'tesseract_available': False,
            'tesseract_version': None,
            'supported_languages': [],
            'configuration': {}
        }
        
        if HAS_OCR:
            try:
                # Verificar versión de Tesseract
                version = pytesseract.get_tesseract_version()
                info['tesseract_available'] = True
                info['tesseract_version'] = str(version)
                
                # Obtener idiomas disponibles
                languages = pytesseract.get_languages()
                info['supported_languages'] = languages
                
            except Exception as e:
                self.logger.warning(f"Error obteniendo información de Tesseract: {e}")
        
        # Agregar configuración actual
        if hasattr(self.config, 'ocr'):
            info['configuration'] = {
                'enabled': getattr(self.config.ocr, 'enabled', True),
                'language': getattr(self.config.ocr, 'language', 'spa+eng'),
                'confidence_threshold': getattr(self.config.ocr, 'confidence_threshold', 0.6),
                'preprocessing_enabled': getattr(self.config.ocr, 'preprocessing_enabled', True),
                'supported_formats': getattr(self.config.ocr, 'supported_formats', ['.jpg', '.jpeg', '.png', '.pdf'])
            }
        
        return info


# Instancia global del procesador OCR
_ocr_processor: Optional[OCRProcessor] = None


def get_ocr_processor() -> OCRProcessor:
    """Obtiene instancia global del procesador OCR."""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = OCRProcessor()
    return _ocr_processor


def process_receipt_image(image_path: str) -> OCRResult:
    """
    Función de conveniencia para procesar imagen de recibo.
    
    Args:
        image_path: Ruta de la imagen
        
    Returns:
        Resultado del procesamiento OCR
    """
    processor = get_ocr_processor()
    return processor.process_receipt_image(image_path)