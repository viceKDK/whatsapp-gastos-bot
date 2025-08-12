#!/usr/bin/env python3
"""
Test simple del sistema de filtrado caracter por caracter
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.message_filter import MessageFilter

def test_early_rejection():
    """Test del filtrado temprano caracter por caracter."""
    print(">> Testing filtrado caracter por caracter...")
    
    # Crear instancia del filtro
    filter_instance = MessageFilter()
    
    # Test cases que deben ser rechazados tempranamente
    print("\n=== MENSAJES QUE DEBEN SER RECHAZADOS ===")
    
    bot_messages = [
        "[OK] Gasto registrado",
        "[ERROR] No se pudo procesar", 
        "No puedo procesar ese mensaje",
        "No se encontro categoria valida",
        "msg-check",
        "msg-status",
        "msg test message",
    ]
    
    rejected_count = 0
    for i, message in enumerate(bot_messages, 1):
        print(f"{i}. '{message}'")
        
        # Test filtrado temprano
        early_rejection = filter_instance._early_character_rejection(message)
        should_process = filter_instance.should_process_message(message)
        
        if early_rejection:
            filter_type, position = early_rejection
            print(f"   -> RECHAZADO TEMPRANO: {filter_type} en posicion {position}")
            rejected_count += 1
        elif not should_process:
            print(f"   -> Rechazado por filtros posteriores")
        else:
            print(f"   -> ERROR: No fue rechazado")
    
    print(f"\nRechazados tempranamente: {rejected_count}/{len(bot_messages)}")
    
    # Test cases que NO deben ser rechazados tempranamente
    print("\n=== MENSAJES QUE DEBEN SER ACEPTADOS ===")
    
    user_messages = [
        "500 internet",
        "internet 500",
        "300 nafta para el auto",
        "Normal que gaste tanto?",
        "Notebook nueva 50000",
    ]
    
    accepted_count = 0
    for i, message in enumerate(user_messages, 1):
        print(f"{i}. '{message}'")
        
        # Test filtrado temprano
        early_rejection = filter_instance._early_character_rejection(message)
        
        if early_rejection is None:
            print(f"   -> ACEPTADO para procesamiento completo")
            accepted_count += 1
        else:
            filter_type, position = early_rejection
            print(f"   -> ERROR: Rechazado tempranamente por {filter_type}")
    
    print(f"\nAceptados correctamente: {accepted_count}/{len(user_messages)}")
    
    # Resultado final
    total_correct = rejected_count + accepted_count
    total_tests = len(bot_messages) + len(user_messages)
    success_rate = (total_correct / total_tests) * 100
    
    print(f"\n" + "="*50)
    print(f"RESULTADO FINAL:")
    print(f"Casos correctos: {total_correct}/{total_tests}")
    print(f"Tasa de exito: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("EXCELENTE: Filtrado funcionando correctamente")
        return True
    else:
        print("NECESITA MEJORAS")
        return False


if __name__ == "__main__":
    print("Iniciando test simple de filtrado temprano...")
    success = test_early_rejection()
    
    if success:
        print("\nTEST EXITOSO!")
        print("El filtrado caracter por caracter funciona correctamente.")
        print("Los mensajes con '[' o 'No' al inicio se descartan tempranamente.")
    else:
        print("\nTEST FALLÓ")
        print("El filtrado necesita ajustes.")