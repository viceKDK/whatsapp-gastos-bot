#!/usr/bin/env python3
"""
Script de Prueba para verificar que la extracción de texto no fragmenta mensajes del bot.

Simula mensajes de WhatsApp que empiezan con [ para verificar que se devuelven completos.
"""

import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


class MockElement:
    """Mock de un elemento de WhatsApp para testing."""
    
    def __init__(self, full_text, html_content=None):
        self.full_text = full_text
        self.html_content = html_content or f"<span>{full_text}</span>"
    
    @property
    def text(self):
        return self.full_text
    
    def get_attribute(self, attr):
        if attr == 'innerHTML':
            return self.html_content
        return None
    
    def find_elements(self, by, selector):
        # Simular elementos internos
        return []


def test_text_extraction():
    """Prueba la extracción de texto para mensajes del bot."""
    
    from infrastructure.whatsapp.whatsapp_selenium import MessageData
    from shared.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("INICIANDO PRUEBA DE EXTRACCION DE TEXTO")
    
    # Crear instancia de MessageData
    message_data = MessageData(None)
    
    # Casos de prueba
    test_cases = [
        # Mensajes del bot - DEBEN devolver texto completo
        "[OK] Gasto registrado ($500 - supermercado) | Fecha: 07/08/2025",
        "[ERROR] No se pudo procesar el mensaje",
        "[INFO] Sistema iniciado correctamente",
        
        # Mensajes del usuario - pueden ser fragmentados normalmente
        "500 nafta para el auto",
        "compe 1200 en el super",
        "gaste 300 transporte ayer",
    ]
    
    print("\n" + "="*70)
    print("PRUEBA DE EXTRACCION DE TEXTO - MENSAJES DEL BOT")
    print("="*70)
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n{i}. PROBANDO: '{test_text}'")
        
        # Crear mock element
        mock_element = MockElement(test_text)
        
        # Extraer texto
        extracted = message_data._extract_text_optimized(mock_element)
        
        # Verificar resultado
        if test_text.startswith('['):
            # Mensaje del bot - debe devolver texto completo
            if extracted == test_text:
                print(f"   OK CORRECTO: Mensaje del bot devuelto completo")
            else:
                print(f"   XX ERROR: Mensaje fragmentado!")
                print(f"       Original: '{test_text}'")
                print(f"       Extraido: '{extracted}'")
        else:
            # Mensaje del usuario - cualquier resultado válido es aceptable
            if extracted:
                print(f"   OK BIEN: Texto extraido: '{extracted}'")
            else:
                print(f"   XX ERROR: No se extrajo texto")
        
        print(f"   Resultado: '{extracted}'")
    
    print("\n" + "="*70)
    print("PRUEBA COMPLETADA")
    print("="*70)


if __name__ == "__main__":
    try:
        print(">> Iniciando prueba de extracción de texto...")
        test_text_extraction()
        print("\n>> Prueba completada")
        
    except KeyboardInterrupt:
        print("\n>> Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n>> Error en la prueba: {e}")
        import traceback
        traceback.print_exc()