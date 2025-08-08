#!/usr/bin/env python3
"""
Script de Diagnóstico de Selectores WhatsApp

Prueba los selectores actualizados para WhatsApp Web 2025 
y diagnostica problemas de detección de mensajes.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings
from shared.logger import get_logger
from infrastructure.whatsapp.whatsapp_selenium import WhatsAppSeleniumConnector


def diagnose_whatsapp_selectors():
    """Diagnostica los selectores de WhatsApp Web para encontrar problemas."""
    
    logger = get_logger(__name__)
    print("\n" + "="*70)
    print("DIAGNOSTICO DE SELECTORES WHATSAPP WEB")
    print("="*70)
    
    try:
        # Configurar WhatsApp connector
        settings = get_settings()
        connector = WhatsAppSeleniumConnector(settings.whatsapp)
        
        # Intentar conectar
        print("\n1. CONECTANDO A WHATSAPP WEB...")
        if not connector.connect():
            print("XX ERROR: No se pudo conectar a WhatsApp Web")
            return False
        
        print("OK Conectado a WhatsApp Web")
        
        # Verificar estado del chat
        print(f"\n2. VERIFICANDO CHAT: '{settings.whatsapp.target_chat_name}'")
        if not connector.chat_selected:
            print("XX ERROR: Chat no seleccionado")
            connector.disconnect()
            return False
        
        print("OK Chat seleccionado correctamente")
        
        # Diagnóstico de selectores de mensajes
        print("\n3. DIAGNOSTICANDO SELECTORES DE MENSAJES...")
        if hasattr(connector, 'cached_selector_manager'):
            selector_manager = connector.cached_selector_manager
            
            # Probar cada selector manualmente
            for i, selector in enumerate(selector_manager.PRIORITY_SELECTORS, 1):
                print(f"\nProbando selector #{i}: {selector}")
                
                try:
                    elements = connector.driver.find_elements(
                        connector.webdriver.common.by.By.CSS_SELECTOR, 
                        selector
                    )
                    print(f"  -> Elementos encontrados: {len(elements)}")
                    
                    if elements:
                        print(f"  -> EXITO! Primer elemento:")
                        first_element = elements[0]
                        
                        # Intentar extraer información del elemento
                        try:
                            element_html = first_element.get_attribute('innerHTML')[:100]
                            element_text = first_element.text[:100] if first_element.text else "[sin texto]"
                            print(f"       HTML: {element_html}...")
                            print(f"       Texto: {element_text}...")
                        except Exception as e:
                            print(f"       Error extrayendo info: {e}")
                        
                        # Si encontramos elementos, este selector funciona
                        print(f"  -> ✓ Selector FUNCIONAL")
                        break
                    else:
                        print(f"  -> Sin elementos")
                        
                except Exception as e:
                    print(f"  -> ERROR: {e}")
        
        else:
            print("XX ERROR: No se puede acceder al selector manager")
        
        # Intentar búsqueda de mensajes nuevos
        print("\n4. PROBANDO BUSQUEDA DE MENSAJES NUEVOS...")
        try:
            messages = connector.get_new_messages()
            print(f"Mensajes detectados: {len(messages)}")
            
            if messages:
                print("MENSAJES ENCONTRADOS:")
                for i, (text, timestamp) in enumerate(messages[:3], 1):
                    print(f"  {i}. '{text[:50]}...' @ {timestamp}")
            else:
                print("Sin mensajes nuevos detectados")
                
        except Exception as e:
            print(f"ERROR en búsqueda de mensajes: {e}")
        
        # Intentar búsqueda optimizada por timestamp
        print("\n5. PROBANDO BUSQUEDA OPTIMIZADA...")
        try:
            if hasattr(connector, 'get_new_messages_optimized'):
                messages = connector.get_new_messages_optimized(None)
                print(f"Mensajes optimizados: {len(messages)}")
                
                if messages:
                    print("MENSAJES OPTIMIZADOS:")
                    for i, (text, timestamp) in enumerate(messages[:3], 1):
                        print(f"  {i}. '{text[:50]}...' @ {timestamp}")
            else:
                print("Método optimizado no disponible")
                
        except Exception as e:
            print(f"ERROR en búsqueda optimizada: {e}")
        
        # Mostrar estadísticas del selector cache
        print("\n6. ESTADISTICAS DE SELECTORES...")
        try:
            if hasattr(connector, 'cached_selector_manager'):
                stats = connector.cached_selector_manager.get_stats()
                print(f"Selector cacheado: {stats.get('cached_selector', 'Ninguno')}")
                print(f"Tasas de éxito: {stats.get('success_rates', {})}")
                print(f"Conteos de fallo: {stats.get('failure_counts', {})}")
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
        
        # Limpiar
        print("\n7. DESCONECTANDO...")
        connector.disconnect()
        print("OK Desconectado")
        
        print("\n" + "="*70)
        print("DIAGNOSTICO COMPLETADO")
        print("="*70)
        return True
        
    except Exception as e:
        logger.error(f"Error en diagnóstico: {e}")
        print(f"ERROR CRITICO: {e}")
        return False


def test_manual_selectors():
    """Prueba manual de selectores comunes para WhatsApp Web."""
    
    print("\n" + "="*50)
    print("PRUEBA MANUAL DE SELECTORES COMUNES")
    print("="*50)
    
    # Lista de selectores a probar manualmente
    common_selectors = [
        # Selectores de mensaje modernos
        "div[role='row']",
        "div[data-testid='conversation-panel-messages'] div[role='row']",
        "div[role='row'][tabindex='-1']",
        "div[data-testid='msg-container']",
        
        # Selectores de contenido de texto
        "span[data-testid='conversation-text']",
        "div.copyable-text", 
        "span.selectable-text",
        "div[dir='auto']",
        "span[dir='auto']",
        
        # Selectores fallback
        "div[data-id]",
        "div[class*='message']",
        "div[aria-roledescription='message']",
    ]
    
    print("Para usar en inspección manual de WhatsApp Web:")
    for i, selector in enumerate(common_selectors, 1):
        print(f"{i:2d}. {selector}")
    
    print("\nInstrucciones:")
    print("1. Abre WhatsApp Web en Chrome")
    print("2. Abre DevTools (F12)")  
    print("3. Ve a Console")
    print("4. Prueba cada selector con: document.querySelectorAll('SELECTOR')")
    print("5. Anota cuáles devuelven elementos de mensaje")


if __name__ == "__main__":
    try:
        print(">> Iniciando diagnóstico de selectores WhatsApp...")
        
        # Ejecutar diagnóstico automático
        success = diagnose_whatsapp_selectors()
        
        # Mostrar selectores para prueba manual
        test_manual_selectors()
        
        if success:
            print("\n>> DIAGNOSTICO EXITOSO")
        else:
            print("\n>> DIAGNOSTICO CON PROBLEMAS")
            
    except KeyboardInterrupt:
        print("\n>> Diagnóstico interrumpido por el usuario")
    except Exception as e:
        print(f"\n>> Error en diagnóstico: {e}")
        import traceback
        traceback.print_exc()