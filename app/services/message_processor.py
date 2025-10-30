"""
Procesador de Mensajes Avanzado

Procesa mensajes de WhatsApp incluyendo texto e imágenes con OCR.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal

from app.services.interpretar_mensaje import InterpretarMensajeService
from app.services.ocr_processor import get_ocr_processor, OCRResult
from app.services.pdf_processor import get_pdf_processor, PDFResult
from domain.models.gasto import Gasto
from shared.logger import get_logger
from shared.metrics import performance_monitor, record_metric
from shared.validators import validate_gasto, ValidationLevel
from shared.fx import get_fx_rate


logger = get_logger(__name__)


@dataclass
class MessageContent:
    """Contenido de un mensaje."""
    text: Optional[str] = None
    image_path: Optional[str] = None
    image_data: Optional[bytes] = None
    pdf_path: Optional[str] = None
    pdf_data: Optional[bytes] = None
    timestamp: Optional[datetime] = None
    sender: Optional[str] = None
    message_type: str = "text"  # "text", "image", "pdf", "mixed"


@dataclass
class ProcessingResult:
    """Resultado del procesamiento de mensaje."""
    success: bool
    gasto: Optional[Gasto] = None
    confidence: float = 0.0
    source: str = "text"  # "text", "ocr", "pdf", "manual"
    extracted_text: Optional[str] = None
    suggestions: List[Dict[str, Any]] = None
    warnings: List[str] = None
    errors: List[str] = None
    processing_time_seconds: float = 0.0
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


class AdvancedMessageProcessor:
    """Procesador avanzado de mensajes con soporte OCR."""
    
    def __init__(self):
        self.logger = logger
        self.text_interpreter = InterpretarMensajeService()
        self.ocr_processor = get_ocr_processor()
        self.pdf_processor = get_pdf_processor()
        
        # Configuración
        self.temp_dir = Path(tempfile.gettempdir()) / "bot_gastos_images"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Métricas
        self.processed_messages = 0
        self.successful_extractions = 0
        self.ocr_usage_count = 0
        self.pdf_usage_count = 0
    
    @performance_monitor("process_message")
    def process_message(self, content: MessageContent) -> ProcessingResult:
        """
        Procesa un mensaje completo (texto y/o imagen).
        
        Args:
            content: Contenido del mensaje
            
        Returns:
            Resultado del procesamiento
        """
        start_time = datetime.now()
        self.processed_messages += 1
        
        # Log inicial del mensaje recibido
        logger.info(f"🔄 Procesando mensaje #{self.processed_messages}")
        logger.info(f"📝 Tipo: {content.message_type}")
        if content.text:
            logger.info(f"📱 Texto: '{content.text[:100]}{'...' if len(content.text) > 100 else ''}'")
        if content.sender:
            logger.info(f"👤 Remitente: {content.sender}")
        
        try:
            # Determinar tipo de procesamiento necesario
            if content.message_type == "pdf" or (content.pdf_path or content.pdf_data):
                return self._process_pdf_message(content, start_time)
            elif content.message_type == "image" or (content.image_path or content.image_data):
                return self._process_image_message(content, start_time)
            elif content.message_type == "text" or content.text:
                return self._process_text_message(content, start_time)
            elif content.message_type == "mixed":
                return self._process_mixed_message(content, start_time)
            else:
                return ProcessingResult(
                    success=False,
                    errors=["Tipo de mensaje no soportado"],
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )
                
        except Exception as e:
            self.logger.error(f"Error procesando mensaje: {e}")
            return ProcessingResult(
                success=False,
                errors=[str(e)],
                processing_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    def _process_text_message(self, content: MessageContent, start_time: datetime) -> ProcessingResult:
        """Procesa mensaje de solo texto."""
        try:
            if not content.text or not content.text.strip():
                return ProcessingResult(
                    success=False,
                    errors=["Mensaje de texto vacío"],
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Procesar con interpretador de texto
            gasto = self.text_interpreter.procesar_mensaje(
                content.text, 
                content.timestamp or datetime.now()
            )
            
            if gasto:
                self.successful_extractions += 1
                record_metric("gasto_extracted", 1, source="text")
                
                # Log de éxito con detalles del gasto
                logger.info(f"✅ Gasto procesado exitosamente!")
                logger.info(f"💰 Monto: ${gasto.monto}")
                logger.info(f"🏷️  Categoría: {gasto.categoria}")
                if gasto.descripcion:
                    logger.info(f"📄 Descripción: {gasto.descripcion}")
                logger.info(f"📅 Fecha: {gasto.fecha}")
                
                return ProcessingResult(
                    success=True,
                    gasto=gasto,
                    confidence=0.9,  # Alta confianza para texto estructurado
                    source="text",
                    extracted_text=content.text,
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            else:
                return ProcessingResult(
                    success=False,
                    warnings=["No se pudo extraer información de gasto del texto"],
                    extracted_text=content.text,
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )
                
        except Exception as e:
            self.logger.error(f"Error procesando mensaje de texto: {e}")
            return ProcessingResult(
                success=False,
                errors=[str(e)],
                processing_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    def _process_pdf_message(self, content: MessageContent, start_time: datetime) -> ProcessingResult:
        """Procesa mensaje con archivo PDF (factura)."""
        try:
            # Preparar archivo PDF para procesamiento
            pdf_path = self._prepare_pdf_file(content)
            
            if not pdf_path:
                return ProcessingResult(
                    success=False,
                    errors=["No se pudo preparar el archivo PDF para procesamiento"],
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Procesar con PDF processor
            self.logger.info(f"Procesando factura PDF: {pdf_path}")
            self.pdf_usage_count += 1
            
            pdf_result = self.pdf_processor.process_pdf_invoice(str(pdf_path))
            
            # Limpiar archivo temporal si fue creado
            if str(pdf_path).startswith(str(self.temp_dir)):
                try:
                    os.unlink(pdf_path)
                except OSError:
                    pass
            
            if not pdf_result.success:
                return ProcessingResult(
                    success=False,
                    errors=[pdf_result.error_message or "Error en procesamiento PDF"],
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Evaluar resultado PDF
            result = self._evaluate_pdf_result(pdf_result, content, start_time)
            
            # Registrar métricas
            record_metric("pdf_confidence", pdf_result.confidence, source="invoice")
            if result.success:
                record_metric("gasto_extracted", 1, source="pdf")
                self.successful_extractions += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error procesando mensaje con PDF: {e}")
            return ProcessingResult(
                success=False,
                errors=[str(e)],
                processing_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    def _process_image_message(self, content: MessageContent, start_time: datetime) -> ProcessingResult:
        """Procesa mensaje con imagen (recibo)."""
        try:
            # Preparar imagen para OCR
            image_path = self._prepare_image_file(content)
            
            if not image_path:
                return ProcessingResult(
                    success=False,
                    errors=["No se pudo preparar la imagen para procesamiento"],
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Procesar con OCR
            self.logger.info(f"Procesando imagen con OCR: {image_path}")
            self.ocr_usage_count += 1
            
            ocr_result = self.ocr_processor.process_receipt_image(str(image_path))
            
            # Limpiar archivo temporal si fue creado
            if str(image_path).startswith(str(self.temp_dir)):
                try:
                    os.unlink(image_path)
                except OSError:
                    pass
            
            if not ocr_result.success:
                return ProcessingResult(
                    success=False,
                    errors=[ocr_result.error_message or "Error en procesamiento OCR"],
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Evaluar resultado OCR
            result = self._evaluate_ocr_result(ocr_result, content, start_time)
            
            # Registrar métricas
            record_metric("ocr_confidence", ocr_result.confidence, source="receipt")
            if result.success:
                record_metric("gasto_extracted", 1, source="ocr")
                self.successful_extractions += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error procesando mensaje con imagen: {e}")
            return ProcessingResult(
                success=False,
                errors=[str(e)],
                processing_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    def _process_mixed_message(self, content: MessageContent, start_time: datetime) -> ProcessingResult:
        """Procesa mensaje mixto (texto + imagen)."""
        try:
            results = []
            
            # Procesar texto si está presente
            if content.text and content.text.strip():
                text_content = MessageContent(
                    text=content.text,
                    timestamp=content.timestamp,
                    sender=content.sender,
                    message_type="text"
                )
                text_result = self._process_text_message(text_content, start_time)
                results.append(("text", text_result))
            
            # Procesar imagen si está presente
            if content.image_path or content.image_data:
                image_content = MessageContent(
                    image_path=content.image_path,
                    image_data=content.image_data,
                    timestamp=content.timestamp,
                    sender=content.sender,
                    message_type="image"
                )
                image_result = self._process_image_message(image_content, start_time)
                results.append(("image", image_result))
            
            # Procesar PDF si está presente
            if content.pdf_path or content.pdf_data:
                pdf_content = MessageContent(
                    pdf_path=content.pdf_path,
                    pdf_data=content.pdf_data,
                    timestamp=content.timestamp,
                    sender=content.sender,
                    message_type="pdf"
                )
                pdf_result = self._process_pdf_message(pdf_content, start_time)
                results.append(("pdf", pdf_result))
            
            # Combinar resultados
            return self._combine_results(results, start_time)
            
        except Exception as e:
            self.logger.error(f"Error procesando mensaje mixto: {e}")
            return ProcessingResult(
                success=False,
                errors=[str(e)],
                processing_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    def _prepare_image_file(self, content: MessageContent) -> Optional[Path]:
        """Prepara archivo de imagen para procesamiento."""
        try:
            if content.image_path:
                # Usar ruta existente
                image_path = Path(content.image_path)
                if image_path.exists():
                    return image_path
            
            elif content.image_data:
                # Crear archivo temporal desde datos
                import uuid
                temp_filename = f"receipt_{uuid.uuid4().hex}.jpg"
                temp_path = self.temp_dir / temp_filename
                
                with open(temp_path, 'wb') as f:
                    f.write(content.image_data)
                
                return temp_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error preparando archivo de imagen: {e}")
            return None
    
    def _prepare_pdf_file(self, content: MessageContent) -> Optional[Path]:
        """Prepara archivo PDF para procesamiento."""
        try:
            if content.pdf_path:
                # Usar ruta existente
                pdf_path = Path(content.pdf_path)
                if pdf_path.exists():
                    return pdf_path
            
            elif content.pdf_data:
                # Crear archivo temporal desde datos
                import uuid
                temp_filename = f"invoice_{uuid.uuid4().hex}.pdf"
                temp_path = self.temp_dir / temp_filename
                
                with open(temp_path, 'wb') as f:
                    f.write(content.pdf_data)
                
                return temp_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error preparando archivo PDF: {e}")
            return None
    
    def _evaluate_pdf_result(self, pdf_result: PDFResult, content: MessageContent, 
                           start_time: datetime) -> ProcessingResult:
        """Evalúa resultado de PDF y crea ProcessingResult."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if pdf_result.suggested_gastos:
            # Usar la primera sugerencia (mejor confianza)
            best_suggestion = pdf_result.suggested_gastos[0]
            
            try:
                gasto = Gasto(
                    monto=Decimal(str(best_suggestion['monto'])),
                    categoria=best_suggestion['categoria'],
                    fecha=best_suggestion.get('fecha', datetime.now()),
                    descripcion=best_suggestion.get('descripcion')
                )
                
                # Validar gasto creado
                validation = validate_gasto(best_suggestion, ValidationLevel.LENIENT)
                
                warnings = []
                if validation.warnings:
                    warnings.extend(validation.warnings)
                
                if pdf_result.confidence < 0.7:
                    warnings.append(f"Confianza PDF baja: {pdf_result.confidence:.1%}")
                
                # Conversion USD->UYU si el texto menciona USD
                if self._text_mentions_usd(pdf_result.extracted_text or ""):
                    try:
                        fx = get_fx_rate('USD', 'UYU')
                        rate = fx.get('rate', 1.0)
                        gasto.monto = (gasto.monto * Decimal(str(rate))).quantize(Decimal('0.01'))
                        if gasto.descripcion:
                            gasto.descripcion = f"{gasto.descripcion} (USD->UYU @ {rate:.4f})"
                        else:
                            gasto.descripcion = f"USD->UYU @ {rate:.4f}"
                    except Exception:
                        warnings.append("No se pudo convertir USD a UYU, se registro en USD")
                
                # Crear sugerencias alternativas
                alternative_suggestions = []
                for i, suggestion in enumerate(pdf_result.suggested_gastos[1:], 1):
                    alt_suggestion = {
                        'type': 'pdf_alternative',
                        'monto': suggestion['monto'],
                        'categoria': suggestion['categoria'],
                        'confidence': suggestion.get('confidence', 0.5),
                        'description': f"Alternativa PDF {i}: ${suggestion['monto']}"
                    }
                    alternative_suggestions.append(alt_suggestion)
                
                return ProcessingResult(
                    success=True,
                    gasto=gasto,
                    confidence=pdf_result.confidence,
                    source="pdf",
                    extracted_text=pdf_result.extracted_text,
                    suggestions=alternative_suggestions,
                    warnings=warnings,
                    processing_time_seconds=processing_time
                )
                
            except Exception as e:
                self.logger.error(f"Error creando gasto desde PDF: {e}")
                return ProcessingResult(
                    success=False,
                    errors=[f"Error creando gasto: {str(e)}"],
                    extracted_text=pdf_result.extracted_text,
                    processing_time_seconds=processing_time
                )
        
        else:
            # No se pudo crear sugerencia automática
            manual_suggestions = []
            
            # Crear sugerencias manuales basadas en montos detectados
            for i, amount in enumerate(pdf_result.detected_amounts[:3]):
                suggestion = {
                    'type': 'pdf_detected_amount',
                    'monto': amount,
                    'categoria': pdf_result.detected_categories[0] if pdf_result.detected_categories else 'servicios',
                    'confidence': 0.6,
                    'description': f"Monto detectado en PDF: ${amount}"
                }
                manual_suggestions.append(suggestion)
            
            return ProcessingResult(
                success=False,
                warnings=["No se pudo extraer gasto automáticamente del PDF"],
                extracted_text=pdf_result.extracted_text,
                suggestions=manual_suggestions,
                processing_time_seconds=processing_time
            )
    
    def _evaluate_ocr_result(self, ocr_result: OCRResult, content: MessageContent, 
                           start_time: datetime) -> ProcessingResult:
        """Evalúa resultado de OCR y crea ProcessingResult."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if ocr_result.suggested_gasto:
            # Crear Gasto desde sugerencia
            try:
                gasto = Gasto(
                    monto=Decimal(str(ocr_result.suggested_gasto['monto'])),
                    categoria=ocr_result.suggested_gasto['categoria'],
                    fecha=ocr_result.suggested_gasto.get('fecha', datetime.now()),
                    descripcion=ocr_result.suggested_gasto.get('descripcion')
                )
                
                # Validar gasto creado
                validation = validate_gasto(ocr_result.suggested_gasto, ValidationLevel.LENIENT)
                
                warnings = []
                if validation.warnings:
                    warnings.extend(validation.warnings)
                
                if ocr_result.confidence < 0.7:
                    warnings.append(f"Confianza OCR baja: {ocr_result.confidence:.1%}")
                
                # Conversion USD->UYU si el texto menciona USD
                if self._text_mentions_usd(ocr_result.extracted_text or ""):
                    try:
                        fx = get_fx_rate('USD', 'UYU')
                        rate = fx.get('rate', 1.0)
                        gasto.monto = (gasto.monto * Decimal(str(rate))).quantize(Decimal('0.01'))
                        if gasto.descripcion:
                            gasto.descripcion = f"{gasto.descripcion} (USD->UYU @ {rate:.4f})"
                        else:
                            gasto.descripcion = f"USD->UYU @ {rate:.4f}"
                    except Exception:
                        warnings.append("No se pudo convertir USD a UYU, se registro en USD")
                
                return ProcessingResult(
                    success=True,
                    gasto=gasto,
                    confidence=ocr_result.confidence,
                    source="ocr",
                    extracted_text=ocr_result.extracted_text,
                    suggestions=self._create_alternative_suggestions(ocr_result),
                    warnings=warnings,
                    processing_time_seconds=processing_time
                )
                
            except Exception as e:
                self.logger.error(f"Error creando gasto desde OCR: {e}")
                return ProcessingResult(
                    success=False,
                    errors=[f"Error creando gasto: {str(e)}"],
                    extracted_text=ocr_result.extracted_text,
                    processing_time_seconds=processing_time
                )
        
        else:
            # No se pudo crear sugerencia automática, ofrecer alternativas
            return ProcessingResult(
                success=False,
                warnings=["No se pudo extraer gasto automáticamente"],
                extracted_text=ocr_result.extracted_text,
                suggestions=self._create_manual_suggestions(ocr_result),
                processing_time_seconds=processing_time
            )
    
    def _create_alternative_suggestions(self, ocr_result: OCRResult) -> List[Dict[str, Any]]:
        """Crea sugerencias alternativas basadas en OCR."""
        suggestions = []
        
        # Sugerencias basadas en otros montos detectados
        for i, amount in enumerate(ocr_result.detected_amounts[1:4], 1):  # Top 3 alternativas
            suggestion = {
                'type': 'alternative_amount',
                'monto': amount,
                'categoria': ocr_result.detected_categories[0] if ocr_result.detected_categories else 'otros',
                'confidence': max(0.1, ocr_result.confidence - (i * 0.2)),
                'description': f"Alternativa {i}: ${amount}"
            }
            suggestions.append(suggestion)
        
        # Sugerencias basadas en otras categorías
        for i, category in enumerate(ocr_result.detected_categories[1:], 1):
            if ocr_result.detected_amounts:
                suggestion = {
                    'type': 'alternative_category',
                    'monto': ocr_result.detected_amounts[0],
                    'categoria': category,
                    'confidence': max(0.1, ocr_result.confidence - (i * 0.15)),
                    'description': f"Categoría alternativa: {category}"
                }
                suggestions.append(suggestion)
        
        return suggestions[:5]  # Máximo 5 sugerencias
    
    def _create_manual_suggestions(self, ocr_result: OCRResult) -> List[Dict[str, Any]]:
        """Crea sugerencias manuales cuando no se puede extraer automáticamente."""
        suggestions = []
        
        # Sugerencias basadas en montos detectados
        for i, amount in enumerate(ocr_result.detected_amounts[:5]):
            suggestion = {
                'type': 'detected_amount',
                'monto': amount,
                'categoria': 'otros',
                'confidence': 0.5,
                'description': f"Monto detectado: ${amount}"
            }
            suggestions.append(suggestion)
        
        # Sugerencias basadas en categorías detectadas
        for category in ocr_result.detected_categories[:3]:
            suggestion = {
                'type': 'detected_category',
                'monto': 0,
                'categoria': category,
                'confidence': 0.3,
                'description': f"Categoría sugerida: {category}"
            }
            suggestions.append(suggestion)
        
        return suggestions

    def _text_mentions_usd(self, text: str) -> bool:
        """Detecta USD de forma estricta: solo si aparece USD o U$S/US$.
        No convierte si solo hay simbolo $ o palabras 'dolar(es)'.
        """
        try:
            t = (text or '').lower()
            return ('usd' in t) or ('u$s' in t) or ('us$' in t)
        except Exception:
            return False
    
    def _combine_results(self, results: List[Tuple[str, ProcessingResult]], 
                        start_time: datetime) -> ProcessingResult:
        """Combina resultados de procesamiento múltiple."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Buscar resultado exitoso con mayor confianza
        successful_results = [(source, result) for source, result in results if result.success]
        
        if successful_results:
            # Usar resultado con mayor confianza
            best_source, best_result = max(successful_results, key=lambda x: x[1].confidence)
            
            # Combinar warnings y suggestions de todos los resultados
            all_warnings = []
            all_suggestions = []
            
            for source, result in results:
                all_warnings.extend(result.warnings)
                all_suggestions.extend(result.suggestions)
            
            return ProcessingResult(
                success=True,
                gasto=best_result.gasto,
                confidence=best_result.confidence,
                source=f"mixed_{best_source}",
                extracted_text=best_result.extracted_text,
                suggestions=all_suggestions,
                warnings=all_warnings,
                processing_time_seconds=processing_time
            )
        
        else:
            # Ningún resultado exitoso, combinar errores
            all_errors = []
            all_warnings = []
            all_suggestions = []
            
            for source, result in results:
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)
                all_suggestions.extend(result.suggestions)
            
            return ProcessingResult(
                success=False,
                errors=all_errors,
                warnings=all_warnings,
                suggestions=all_suggestions,
                processing_time_seconds=processing_time
            )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de procesamiento."""
        success_rate = (self.successful_extractions / self.processed_messages * 100) if self.processed_messages > 0 else 0
        
        return {
            'processed_messages': self.processed_messages,
            'successful_extractions': self.successful_extractions,
            'success_rate_percent': success_rate,
            'ocr_usage_count': self.ocr_usage_count,
            'pdf_usage_count': self.pdf_usage_count,
            'ocr_available': self.ocr_processor.ocr_enabled,
            'pdf_available': self.pdf_processor.pdf_enabled,
            'temp_directory': str(self.temp_dir)
        }
    
    def cleanup_temp_files(self) -> int:
        """
        Limpia archivos temporales.
        
        Returns:
            Número de archivos eliminados
        """
        try:
            deleted_count = 0
            if self.temp_dir.exists():
                for file_path in self.temp_dir.glob("*"):
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except OSError:
                        continue
            
            self.logger.info(f"Eliminados {deleted_count} archivos temporales")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error limpiando archivos temporales: {e}")
            return 0


# Instancia global del procesador
_message_processor: Optional[AdvancedMessageProcessor] = None


def get_message_processor() -> AdvancedMessageProcessor:
    """Obtiene instancia global del procesador de mensajes."""
    global _message_processor
    if _message_processor is None:
        _message_processor = AdvancedMessageProcessor()
    return _message_processor


def process_text_message(text: str, timestamp: datetime = None) -> ProcessingResult:
    """
    Función de conveniencia para procesar mensaje de texto.
    
    Args:
        text: Texto del mensaje
        timestamp: Timestamp del mensaje
        
    Returns:
        Resultado del procesamiento
    """
    processor = get_message_processor()
    content = MessageContent(
        text=text,
        timestamp=timestamp or datetime.now(),
        message_type="text"
    )
    return processor.process_message(content)


def process_image_message(image_path: str = None, image_data: bytes = None, 
                         timestamp: datetime = None) -> ProcessingResult:
    """
    Función de conveniencia para procesar mensaje con imagen.
    
    Args:
        image_path: Ruta de la imagen
        image_data: Datos binarios de la imagen
        timestamp: Timestamp del mensaje
        
    Returns:
        Resultado del procesamiento
    """
    processor = get_message_processor()
    content = MessageContent(
        image_path=image_path,
        image_data=image_data,
        timestamp=timestamp or datetime.now(),
        message_type="image"
    )
    return processor.process_message(content)


def process_pdf_message(pdf_path: str = None, pdf_data: bytes = None, 
                       timestamp: datetime = None) -> ProcessingResult:
    """
    Función de conveniencia para procesar mensaje con PDF.
    
    Args:
        pdf_path: Ruta del archivo PDF
        pdf_data: Datos binarios del PDF
        timestamp: Timestamp del mensaje
        
    Returns:
        Resultado del procesamiento
    """
    processor = get_message_processor()
    content = MessageContent(
        pdf_path=pdf_path,
        pdf_data=pdf_data,
        timestamp=timestamp or datetime.now(),
        message_type="pdf"
    )
    return processor.process_message(content)
