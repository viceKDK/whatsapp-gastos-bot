#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug de Selectores WhatsApp

Muestra exactamente qué elementos y texto están siendo seleccionados.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from config.settings import get_settings
from infrastructure.whatsapp import WhatsAppEnhancedConnector
from selenium.webdriver.common.by import By

def debug_whatsapp_selectors():
    """Debug de selectores de WhatsApp para identificar el problema."""
    print("[DEBUG] Selectores de WhatsApp")
    print("=" * 40)
    
    settings = get_settings()
    connector = WhatsAppEnhancedConnector(settings.whatsapp)
    
    try:
        print("1. Intentando conectar...")
        if not connector.connect():
            print("[X] No se pudo conectar")
            return
        
        print("[OK] Conectado, esperando carga...")
        import time
        time.sleep(3)
        
        print("2. Probando selectores diferentes...")
        
        # Selectores que puede estar usando
        test_selectors = [
            ("div[role='row']", "WhatsApp estándar"),
            ("[data-testid='msg-container']", "Nuevo WhatsApp"),
            ("div[data-id]", "Atributo común"),
            (".message", "Clase message"),
            (".selectable-text", "Texto seleccionable"),
            ("span[dir='auto']", "Texto direccional"),
            ("[data-testid='conversation-text']", "Texto conversación"),
        ]
        
        for selector, description in test_selectors:
            try:
                elements = connector.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"\n{description}: {len(elements)} elementos")
                
                # Mostrar primeros 3 elementos
                for i, element in enumerate(elements[-3:], 1):
                    try:
                        # Ver texto básico
                        basic_text = element.text.strip() if element.text else ""
                        
                        # Ver innerHTML
                        html = element.get_attribute('innerHTML')[:100] if element.get_attribute('innerHTML') else ""
                        
                        print(f"  {i}. Texto: '{basic_text[:50]}...'")
                        print(f"     HTML: '{html}...'")
                        
                        # Si contiene algo como Vice o números, es probablemente un mensaje
                        if any(keyword in basic_text.lower() for keyword in ['vice', '250', '500', 'carnicería', 'pizza']):
                            print(f"     [TARGET ENCONTRADO!] Este contiene palabras clave")
                        
                    except Exception as e:
                        print(f"  {i}. ERROR: {e}")
                        
            except Exception as e:
                print(f"{description}: ERROR - {e}")
        
        print(f"\n3. Verificando elementos actuales con SmartCache...")
        
        # Usar el mismo método que está usando el bot
        elements = connector.smart_cache.find_messages_optimized(connector.driver)
        print(f"SmartCache encontró: {len(elements)} elementos")
        
        # Analizar los últimos 5 elementos
        for i, element in enumerate(elements[-5:], 1):
            try:
                # Usar el mismo método que usa MessageData 
                message_data = connector.lazy_parser.parse_element_lazy(element)
                
                if message_data:
                    print(f"  {i}. ELEMENT -> '{message_data.text[:50]}...' @ {message_data.timestamp}")
                    
                    # Verificar si contiene palabras clave del usuario
                    if any(keyword in message_data.text.lower() for keyword in ['vice', '250', '500', 'carnicería', 'pizza', 'súper']):
                        print(f"     [MATCH!] Contiene mensaje del usuario")
                        
                        # Probar el filtro también
                        from app.services.message_filter import get_message_filter
                        filter_service = get_message_filter()
                        should_process = filter_service.should_process_message(message_data.text, message_data.timestamp)
                        print(f"     [FILTER] Debería procesarse: {should_process}")
                else:
                    print(f"  {i}. ELEMENT -> No se pudo parsear")
                    
            except Exception as e:
                print(f"  {i}. ERROR parseando: {e}")
        
    finally:
        try:
            connector.disconnect()
        except:
            pass

if __name__ == "__main__":
    print("ESTE TEST REQUIERE QUE WHATSAPP WEB ESTÉ ABIERTO")
    print("Y EL CHAT 'Gastos' ESTÉ SELECCIONADO")
    print()
    input("Presiona ENTER cuando esté listo...")
    
    debug_whatsapp_selectors()