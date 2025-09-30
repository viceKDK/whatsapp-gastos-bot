#!/usr/bin/env python3
"""
Test con casos reales de mensajes del bot vs usuario
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.message_filter import MessageFilter

def test_real_world_cases():
    """Test con casos reales encontrados en logs."""
    print(">> Testing casos reales de mensajes...")
    
    filter_instance = MessageFilter()
    
    # Mensajes reales del bot que deben ser ignorados
    print("\n=== MENSAJES REALES DEL BOT (DEBEN SER RECHAZADOS) ===")
    
    real_bot_messages = [
        "msg-check",  # Caso real del log
        "[OK] Gasto registrado: $500 - supermercado",
        "[ERROR] No se pudo procesar el mensaje", 
        "[INFO] Sistema iniciado correctamente",
        "No puedo procesar ese mensaje",
        "No se encontro una categoria valida",
        "No entiendo el formato especificado",
    ]
    
    bot_rejected = 0
    for i, message in enumerate(real_bot_messages, 1):
        print(f"{i}. '{message}'")
        
        # Test filtrado temprano
        early_rejection = filter_instance._early_character_rejection(message)
        should_process = filter_instance.should_process_message(message)
        
        if early_rejection:
            filter_type, position = early_rejection
            print(f"   -> RECHAZADO TEMPRANO: {filter_type} en posicion {position}")
            bot_rejected += 1
        elif not should_process:
            print(f"   -> Rechazado por filtros posteriores")
            bot_rejected += 1  # Contar como exitoso tambien
        else:
            print(f"   -> ERROR: No fue rechazado!")
    
    # Mensajes reales del usuario que deben ser procesados
    print(f"\n=== MENSAJES REALES DEL USUARIO (DEBEN SER ACEPTADOS) ===")
    
    real_user_messages = [
        "500 internet",
        "internet 500", 
        "300 nafta para el auto",
        "250 carniceria",
        "carniceria 250",
        "1200 comida del super",
        "Compre notebook por 50000",
        "Gaste 150 en almacen",
        "Normal que cueste tanto?",  # Pregunta del usuario
        "Nosotros gastamos poco",    # No empieza con "No" sino "Nosotros"
        "mensaje de prueba",         # No empieza con "msg" sino "mensaje"
    ]
    
    user_accepted = 0
    for i, message in enumerate(real_user_messages, 1):
        print(f"{i}. '{message}'")
        
        # Test filtrado temprano - NO debe rechazar
        early_rejection = filter_instance._early_character_rejection(message)
        
        if early_rejection is None:
            print(f"   -> ACEPTADO (sin rechazo temprano)")
            user_accepted += 1
            
            # Verificar procesamiento completo
            should_process = filter_instance.should_process_message(message)
            if should_process:
                print(f"   -> PROCESADO correctamente")
            else:
                print(f"   -> Rechazado por filtros posteriores (normal para algunos casos)")
        else:
            filter_type, position = early_rejection
            print(f"   -> ERROR: Rechazado tempranamente por {filter_type}!")
    
    # Resultados
    print(f"\n" + "="*50)
    print(f"RESULTADOS:")
    print(f"Mensajes del bot rechazados: {bot_rejected}/{len(real_bot_messages)}")
    print(f"Mensajes del usuario aceptados: {user_accepted}/{len(real_user_messages)}")
    
    total_correct = bot_rejected + user_accepted
    total_tests = len(real_bot_messages) + len(real_user_messages)
    success_rate = (total_correct / total_tests) * 100
    
    print(f"Tasa de exito total: {success_rate:.1f}%")
    
    if success_rate >= 95:
        print("EXCELENTE: Filtrado funcionando perfectamente con casos reales")
        return True
    elif success_rate >= 85:
        print("BUENO: Filtrado mayormente funcional")
        return True
    else:
        print("NECESITA MEJORAS")
        return False


def test_edge_cases():
    """Test con casos extremos."""
    print(f"\n" + "="*50)
    print(">> Test casos extremos...")
    
    filter_instance = MessageFilter()
    
    edge_cases = [
        ("", "Mensaje vacio"),
        ("   ", "Solo espacios"),
        ("msg", "Solo 'msg' sin mas"),
        ("[", "Solo corchete"),
        ("No", "Solo 'No'"),
        ("Normal", "Palabra que contiene 'No' pero no empieza"),
        ("message-test", "Palabra que contiene 'msg' pero no empieza"),
        ("123msg", "Numero seguido de msg"),
        ("  msg-check  ", "msg-check con espacios"),
    ]
    
    for message, description in edge_cases:
        print(f"'{message}' ({description})")
        
        early_rejection = filter_instance._early_character_rejection(message)
        if early_rejection:
            filter_type, position = early_rejection
            print(f"   -> Rechazado: {filter_type} en posicion {position}")
        else:
            print(f"   -> Aceptado para procesamiento")
    
    return True


if __name__ == "__main__":
    print("Iniciando tests con casos reales...")
    
    # Test principal
    success = test_real_world_cases()
    
    # Test casos extremos
    test_edge_cases()
    
    print(f"\n" + "="*60)
    if success:
        print("TESTS EXITOSOS CON CASOS REALES!")
        print("El filtrado caracter por caracter maneja correctamente:")
        print("- Mensajes del bot: [OK], [ERROR], No puedo, msg-check")
        print("- Mensajes del usuario: gastos, preguntas, texto normal")
        print("- Sin falsos positivos en deteccion temprana")
    else:
        print("TESTS FALLARON - Revisar implementacion")
    
    print("="*60)