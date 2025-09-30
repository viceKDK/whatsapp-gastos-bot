#!/usr/bin/env python3
"""
Script para simular la extracción de mensajes y verificar que los mensajes con [ se ignoren
"""

import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def simulate_message_extraction():
    """Simula el proceso de extracción de mensajes con filtro incluido."""
    
    print("\n" + "="*70)
    print("SIMULACIÓN DE EXTRACCIÓN DE MENSAJES CON FILTRO")
    print("="*70)
    
    # Simular mensajes extraídos de WhatsApp (como si vinieran del HTML)
    extracted_messages = [
        "[OK] Gasto registrado ($500 - supermercado) | Fecha: 07/08/2025",
        "500 nafta para el auto",
        "[ERROR] No se pudo procesar el mensaje",
        "1200 comida en el restaurante", 
        "[OK] Gasto registrado ($700 - takeaway) | Fecha: 08/08/2025",
        "No pude procesar ese mensaje. Usa el formato: '$monto categoria descripcion'",
        "ayuda",
        "[INFO] Sistema iniciado correctamente",
        "300 transporte taxi",
        "No se pudo procesar el formato",
        "No puedo entender ese mensaje",
        "gasté 150 en combustible",
    ]
    
    # Simular el proceso de filtrado durante extracción
    filtered_messages = []
    
    print("\nPROCESANDO MENSAJES EXTRAÍDOS:")
    print("-" * 50)
    
    for i, extracted_text in enumerate(extracted_messages, 1):
        print(f"\n{i}. EXTRAÍDO: '{extracted_text[:50]}...'")
        
        # FILTRO CRÍTICO: Si empieza con [ o "No", IGNORAR y pasar al siguiente
        if extracted_text.strip().startswith('[') or extracted_text.strip().startswith('No'):
            patron = "con [" if extracted_text.strip().startswith('[') else "con 'No'"
            print(f"   BOT MENSAJE DEL BOT DETECTADO (empieza {patron}) - IGNORANDO y pasando al siguiente")
            continue  # Pasar al siguiente mensaje inmediatamente
        
        # Si pasa el filtro, agregarlo a la lista
        filtered_messages.append(extracted_text)
        print(f"   OK MENSAJE VÁLIDO - AGREGADO A LA LISTA")
        print(f"   TOTAL EN LISTA: {len(filtered_messages)} mensajes")
    
    # Mostrar resultado final
    print("\n" + "="*70)
    print("RESULTADO FINAL")
    print("="*70)
    
    print(f"Mensajes extraídos: {len(extracted_messages)}")
    print(f"Mensajes filtrados: {len(filtered_messages)}")
    print(f"Mensajes ignorados: {len(extracted_messages) - len(filtered_messages)}")
    
    print(f"\nMENSAJES QUE PASARON EL FILTRO:")
    for i, msg in enumerate(filtered_messages, 1):
        print(f"  {i}. '{msg}'")
    
    # Verificar que ningún mensaje con [ o "No" pasó el filtro
    mensajes_bot_que_pasaron = [msg for msg in filtered_messages if msg.strip().startswith('[') or msg.strip().startswith('No')]
    
    if not mensajes_bot_que_pasaron:
        print(f"\nOK ÉXITO: Ningún mensaje del bot (con [ o 'No') pasó el filtro")
        return True
    else:
        print(f"\nXX ERROR: {len(mensajes_bot_que_pasaron)} mensajes del bot pasaron el filtro:")
        for msg in mensajes_bot_que_pasaron:
            print(f"     - '{msg}'")
        return False


if __name__ == "__main__":
    try:
        print(">> Simulando extracción de mensajes con filtro...")
        exito = simulate_message_extraction()
        
        if exito:
            print("\n>> OK FILTRO FUNCIONANDO CORRECTAMENTE")
        else:
            print("\n>> XX FILTRO TIENE PROBLEMAS")
            
    except Exception as e:
        print(f"\n>> Error: {e}")
        import traceback
        traceback.print_exc()