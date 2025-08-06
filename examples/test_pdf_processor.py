"""
Ejemplo de uso del procesador PDF para facturas

Este script demuestra cómo usar el procesador PDF para extraer
información de gastos desde archivos PDF de facturas.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.pdf_processor import get_pdf_processor, process_pdf_invoice
from app.services.message_processor import process_pdf_message
from shared.logger import get_logger


def main():
    """Función principal de ejemplo."""
    logger = get_logger(__name__)
    
    print("🔧 Ejemplo de Procesador PDF para Facturas")
    print("=" * 50)
    
    # Verificar si hay un archivo PDF de ejemplo
    pdf_examples = [
        "examples/sample_invoice.pdf",
        "test_invoice.pdf",
        "factura_ejemplo.pdf"
    ]
    
    sample_pdf = None
    for pdf_file in pdf_examples:
        if Path(pdf_file).exists():
            sample_pdf = pdf_file
            break
    
    if not sample_pdf:
        print("⚠️  No se encontró archivo PDF de ejemplo.")
        print("\nPara probar el procesador PDF:")
        print("1. Coloca un archivo PDF de factura en el directorio")
        print("2. Renómbralo como 'test_invoice.pdf' o 'factura_ejemplo.pdf'")
        print("3. Ejecuta este script nuevamente")
        
        # Mostrar información del sistema
        show_pdf_info()
        return
    
    print(f"📄 Procesando archivo PDF: {sample_pdf}")
    print()
    
    try:
        # Método 1: Usar directamente el procesador PDF
        print("🔍 Método 1: Procesador PDF directo")
        pdf_processor = get_pdf_processor()
        pdf_result = pdf_processor.process_pdf_invoice(sample_pdf)
        
        print_pdf_result(pdf_result, "PDF Processor")
        
        # Método 2: Usar el procesador de mensajes
        print("\n🔍 Método 2: Procesador de mensajes")
        message_result = process_pdf_message(pdf_path=sample_pdf)
        
        print_message_result(message_result, "Message Processor")
        
        # Mostrar información del sistema
        show_pdf_info()
        
    except Exception as e:
        logger.error(f"Error en ejemplo PDF: {e}")
        print(f"❌ Error: {e}")


def print_pdf_result(result, method_name):
    """Imprime resultado del procesador PDF."""
    print(f"\n--- Resultado {method_name} ---")
    print(f"✅ Éxito: {result.success}")
    print(f"📊 Confianza: {result.confidence:.1%}")
    print(f"📑 Páginas procesadas: {result.pages_processed}")
    print(f"⏱️  Tiempo: {result.processing_time_seconds:.2f}s")
    
    if result.success:
        print(f"\n💰 Montos detectados: {result.detected_amounts}")
        print(f"🏷️  Categorías: {result.detected_categories}")
        print(f"📅 Fechas: {[d.strftime('%Y-%m-%d') for d in result.detected_dates]}")
        
        if result.suggested_gastos:
            print(f"\n💡 Sugerencias de gastos:")
            for i, suggestion in enumerate(result.suggested_gastos, 1):
                print(f"  {i}. ${suggestion['monto']} - {suggestion['categoria']}")
                if suggestion.get('descripcion'):
                    print(f"     📝 {suggestion['descripcion']}")
        
        if result.extracted_text:
            text_preview = result.extracted_text[:200].replace('\n', ' ')
            print(f"\n📝 Texto extraído (vista previa): {text_preview}...")
    
    else:
        print(f"❌ Error: {result.error_message}")


def print_message_result(result, method_name):
    """Imprime resultado del procesador de mensajes."""
    print(f"\n--- Resultado {method_name} ---")
    print(f"✅ Éxito: {result.success}")
    print(f"📊 Confianza: {result.confidence:.1%}")
    print(f"🔧 Fuente: {result.source}")
    print(f"⏱️  Tiempo: {result.processing_time_seconds:.2f}s")
    
    if result.success and result.gasto:
        print(f"\n💸 Gasto extraído:")
        print(f"  💰 Monto: ${result.gasto.monto}")
        print(f"  🏷️  Categoría: {result.gasto.categoria}")
        print(f"  📅 Fecha: {result.gasto.fecha.strftime('%Y-%m-%d')}")
        if result.gasto.descripcion:
            print(f"  📝 Descripción: {result.gasto.descripcion}")
    
    if result.suggestions:
        print(f"\n💡 Sugerencias alternativas:")
        for i, suggestion in enumerate(result.suggestions, 1):
            print(f"  {i}. {suggestion.get('description', 'N/A')}")
    
    if result.warnings:
        print(f"\n⚠️  Advertencias:")
        for warning in result.warnings:
            print(f"  • {warning}")
    
    if result.errors:
        print(f"\n❌ Errores:")
        for error in result.errors:
            print(f"  • {error}")


def show_pdf_info():
    """Muestra información del sistema PDF."""
    print("\n" + "=" * 50)
    print("🔧 Información del Sistema PDF")
    
    try:
        pdf_processor = get_pdf_processor()
        info = pdf_processor.get_pdf_info()
        
        print(f"📄 Soporte PDF disponible: {info['pdf_support_available']}")
        print(f"⚙️  PDF habilitado: {info['pdf_enabled']}")
        print(f"📑 Formatos soportados: {info['supported_formats']}")
        print(f"📖 Máximo páginas por PDF: {info['max_pages_per_pdf']}")
        
        if info.get('configuration'):
            config = info['configuration']
            print(f"\n⚙️  Configuración:")
            print(f"  • DPI conversión: {config.get('pdf_conversion_dpi', 'N/A')}")
            print(f"  • Páginas máximas: {config.get('max_pdf_pages', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error obteniendo información PDF: {e}")
    
    # Información de dependencias
    print(f"\n📦 Dependencias:")
    try:
        import PyPDF2
        print(f"  ✅ PyPDF2: {PyPDF2.__version__}")
    except ImportError:
        print(f"  ❌ PyPDF2: No instalado")
    
    try:
        import pdf2image
        print(f"  ✅ pdf2image: Disponible")
    except ImportError:
        print(f"  ❌ pdf2image: No instalado")
    
    try:
        import pytesseract
        print(f"  ✅ pytesseract: Disponible")
    except ImportError:
        print(f"  ❌ pytesseract: No instalado")
    
    try:
        import cv2
        print(f"  ✅ OpenCV: {cv2.__version__}")
    except ImportError:
        print(f"  ❌ OpenCV: No instalado")


if __name__ == "__main__":
    main()