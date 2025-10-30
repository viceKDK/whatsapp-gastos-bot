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

# EasyOCR fallback (no external binary required)
try:
    import easyocr  # type: ignore
    HAS_EASYOCR = True
except Exception:
    HAS_EASYOCR = False

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
        # EasyOCR: inicializacion diferida (para evitar problemas de consola en Windows)
        self._easyocr_reader = None
    
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
        try:
            # Intento 1: Tesseract (lazy import)
            try:
                import pytesseract as _pyt
                # asegurar config
                try:
                    tesseract_path = getattr(self.config.ocr, 'tesseract_path', None)
                    if tesseract_path and Path(tesseract_path).exists():
                        _pyt.pytesseract.tesseract_cmd = tesseract_path
                except Exception:
                    pass
                ocr_config = self._get_ocr_config()
                text = _pyt.image_to_string(image, config=ocr_config)
                data = _pyt.image_to_data(image, output_type=_pyt.Output.DICT, config=ocr_config)
                confidences = [int(conf) for conf in data.get('conf', []) if str(conf).isdigit() and int(conf) > 0]
                avg_confidence = (sum(confidences) / len(confidences)) if confidences else 0
                return text.strip(), avg_confidence / 100.0
            except Exception as e_tess:
                self.logger.warning(f"Fallo Tesseract, intentando EasyOCR: {e_tess}")
                # Intento 2: EasyOCR
                self._ensure_easyocr()
                if self._easyocr_reader is None:
                    raise RuntimeError("EasyOCR no disponible")
                if len(image.shape) == 2:
                    rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                else:
                    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = self._easyocr_reader.readtext(rgb, detail=1)
                texts = []
                confs = []
                for r in results:
                    try:
                        _, txt, conf = r
                        if txt and isinstance(conf, (float, int)):
                            texts.append(str(txt))
                            confs.append(float(conf))
                    except Exception:
                        continue
                text_joined = "\n".join(texts).strip()
                avg_conf = (sum(confs) / len(confs)) if confs else 0.0
                return text_joined, avg_conf
        except Exception as e:
            self.logger.error(f"Error extrayendo texto: {e}")
            return "", 0.0

    def _ensure_easyocr(self):
        """Inicializa EasyOCR de forma segura y silenciosa en Windows."""
        if self._easyocr_reader is not None or not HAS_EASYOCR:
            return
        try:
            import os, sys
            # Forzar stdout a utf-8 para evitar errores de encoding en barras de progreso
            try:
                if hasattr(sys.stdout, 'reconfigure'):
                    sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass
            os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
            # Inicializar lector (descarga modelos la primera vez)
            self._easyocr_reader = easyocr.Reader(['es', 'en'], gpu=False)
            self.logger.info("EasyOCR inicializado (fallback)")
        except Exception as e:
            self.logger.warning(f"No se pudo inicializar EasyOCR: {e}")
    
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
                'items': self._extract_items(text),
                'total_amount': self._extract_total_amount(text)
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

    def _extract_total_amount(self, text: str) -> Optional[float]:
        """Intenta extraer el monto asociado a 'TOTAL' o frases similares."""
        try:
            lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
            # Patrones de total
            total_tokens = [
                r'\btotal\b', r'\bttoal\b', r'\bimporte\s*total\b', r'\bmonto\s*total\b',
                r'\btotal\s*a\s*pagar\b', r'\btotal\s*final\b'
            ]
            money_pat = re.compile(r'(?:\$\s*)?(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})|\d+[\.,]\d{2})')
            def norm_amount(s: str) -> Optional[float]:
                if s.count(',')>0 and s.count('.')>0:
                    if s.rfind(',')>s.rfind('.'):  # 1.234,56
                        s = s.replace('.', '').replace(',', '.')
                    else:
                        s = s.replace(',', '')
                elif s.count(',')>0 and s.count('.')==0:
                    s = s.replace(',', '.')
                else:
                    s = s.replace(',', '')
                try:
                    v = float(s)
                    if 0.01 <= v <= 10000000:
                        return v
                except Exception:
                    return None
                return None
            # Buscar en la misma linea
            for i, ln in enumerate(lines):
                low = ln.lower()
                if any(re.search(tok, low) for tok in total_tokens):
                    m = money_pat.search(ln)
                    if m:
                        v = norm_amount(m.group(1))
                        if v is not None:
                            return v
                    # Buscar en la siguiente linea si no esta en la misma
                    if i+1 < len(lines):
                        m2 = money_pat.search(lines[i+1])
                        if m2:
                            v2 = norm_amount(m2.group(1))
                            if v2 is not None:
                                return v2
            return None
        except Exception:
            return None
    
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
        
        # Verificar si OCR está habilitado (Tesseract o EasyOCR)
        self.ocr_enabled = getattr(self.config.ocr, 'enabled', True) and (HAS_OCR or HAS_EASYOCR)
        
        if not HAS_OCR and HAS_EASYOCR:
            self.logger.info("Usando EasyOCR como fallback de OCR")
        elif not self.ocr_enabled:
            self.logger.warning("OCR deshabilitado: no hay motor disponible")
    
    def process_receipt_image(self, image_path: str, mode: str = 'auto', escalate: bool = True) -> OCRResult:
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
                error_message="OCR no está habilitado"
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
            
            # Extraer texto (primer intento)
            self.logger.debug("Extrayendo texto con OCR")
            text, confidence = self.text_extractor.extract_text(processed_image)
            
            if not text.strip():
                return OCRResult(
                    success=False,
                    error_message="No se pudo extraer texto de la imagen",
                    confidence=confidence
                )
            
            # Verificar confianza/sugerencia, y si es baja intentar variantes de preprocesado/rotacion
            min_confidence = getattr(self.config.ocr, 'confidence_threshold', 0.6)
            analysis = self.analyzer.analyze_receipt(text)
            suggested_gasto = self._create_suggested_gasto(analysis, text)
            # Escalada al modo pesado solo si corresponde
            use_heavy = (mode == 'heavy') or (mode != 'fast' and escalate and (confidence < min_confidence or not suggested_gasto))
            if use_heavy:
                self.logger.debug("Intentando variantes de OCR (rotaciones/umbrales)")
                text2, conf2 = self._extract_best_text_variants(processed_image)
                if text2 and conf2 > confidence:
                    text, confidence = text2, conf2
                    analysis = self.analyzer.analyze_receipt(text)
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
            
            # Usar 'total_amount' si se detecta; si no, el mayor monto
            total_amount = analysis.get('total_amount')
            suggested_amount = total_amount if total_amount else (amounts[0] if amounts else None)
            if suggested_amount is None:
                return None
            
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

    def _extract_best_text_variants(self, base_image) -> Tuple[str, float]:
        """Prueba variantes de preprocesado/rotacion y retorna el mejor texto/confianza."""
        candidates: List[Tuple[str, float]] = []
        try:
            images = []
            img = base_image
            images.append(img)
            # Rotaciones
            try:
                images.append(cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE))
                images.append(cv2.rotate(img, cv2.ROTATE_180))
                images.append(cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE))
            except Exception:
                pass
            # Umbrales alternativos
            try:
                gray = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                images.append(otsu)
                thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 5)
                images.append(thr)
            except Exception:
                pass
            # Escalado
            try:
                h, w = img.shape[:2]
                scale = 1.5 if max(h, w) < 1200 else 1.0
                if scale != 1.0:
                    images.append(cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC))
            except Exception:
                pass

            best_text, best_conf = "", 0.0
            for im in images:
                try:
                    t, c = self.text_extractor.extract_text(im)
                    if t and c > best_conf:
                        best_text, best_conf = t, c
                except Exception:
                    continue
            return best_text, best_conf
        except Exception:
            return "", 0.0
    
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


def process_receipt_image(image_path: str, mode: str = 'auto', escalate: bool = True) -> OCRResult:
    """
    Función de conveniencia para procesar imagen de recibo.
    
    Args:
        image_path: Ruta de la imagen
        
    Returns:
        Resultado del procesamiento OCR
    """
    processor = get_ocr_processor()
    return processor.process_receipt_image(image_path, mode=mode, escalate=escalate)
