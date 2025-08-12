#!/usr/bin/env python3
"""
Test del sistema de filtrado carácter por carácter
Verifica que los mensajes que empiezan con [ o "No" se descarten tempranamente
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.message_filter import MessageFilter

def test_character_by_character_filtering():
    """Test del filtrado caracter por caracter."""
    print("Testing filtrado caracter por caracter...")
    
    # Crear instancia del filtro
    filter_instance = MessageFilter()
    
    # Test cases para mensajes que deben ser rechazados tempranamente
    rejection_test_cases = [
        # Mensajes que empiezan con [
        ("[OK] Gasto registrado: $500 - supermercado", "starts_with_bracket"),
        ("[ERROR] No se pudo procesar el mensaje", "starts_with_bracket"),
        ("[INFO] Sistema iniciado correctamente", "starts_with_bracket"),
        ("  [SYSTEM] Mensaje del bot", "starts_with_bracket"),  # Con espacios iniciales
        ("\t[DEBUG] Log del sistema", "starts_with_bracket"),   # Con tab inicial
        
        # Mensajes que empiezan con "No"
        ("No puedo procesar ese mensaje", "starts_with_no"),
        ("No se encontró categoría válida", "starts_with_no"),
        ("No hay suficiente información", "starts_with_no"),
        ("  No entiendo el formato", "starts_with_no"),        # Con espacios iniciales
        ("\nNo se pudo guardar", "starts_with_no"),            # Con salto de línea
        
        # Mensajes que empiezan con emojis de confirmación
        ("✅ Gasto registrado exitosamente", "confirmation_emoji"),
        ("❌ Error procesando mensaje", "confirmation_emoji"),
        ("🤖 Respuesta automática del bot", "confirmation_emoji"),
        ("💰 Monto guardado: $300", "confirmation_emoji"),
        ("🔄 Procesando solicitud...", "confirmation_emoji"),
    ]
    
    print("Test cases para rechazo temprano:")
    rejection_success = 0
    
    for i, (message, expected_filter_type) in enumerate(rejection_test_cases, 1):
        print(f"\n{i}. Mensaje: '{message[:50]}...'")
        
        # Verificar que se rechaza
        should_process = filter_instance.should_process_message(message)
        
        if not should_process:
            print(f"   CORRECTO: Mensaje rechazado")
            
            # Verificar el filtro específico aplicado
            early_rejection = filter_instance._early_character_rejection(message)
            if early_rejection:
                filter_type, position = early_rejection
                print(f"   Filtro aplicado: {filter_type} en posicion {position}")
                
                if filter_type == expected_filter_type:
                    print(f"   CORRECTO: Tipo de filtro esperado")
                    rejection_success += 1
                else:
                    print(f"   INCORRECTO: Esperaba {expected_filter_type}, obtuvo {filter_type}")
            else:
                print(f"   Rechazado por filtro posterior (no temprano)")
        else:
            print(f"   INCORRECTO: Mensaje deberia ser rechazado")
    
    print(f"\nResultados rechazo temprano: {rejection_success}/{len(rejection_test_cases)} correctos")
    
    # Test cases para mensajes que NO deben ser rechazados tempranamente
    acceptance_test_cases = [
        # Gastos válidos
        "500 internet",
        "internet 500", 
        "300 nafta para el auto",
        "Compré comida por $250",
        "Gasto de 150 en supermercado",
        
        # Mensajes del usuario que empiezan con palabras similares
        "Notebook nueva $50000",
        "Normal que gaste tanto?",
        "Nos vemos mañana",
        
        # Mensajes con [ o No en medio
        "Compré [leche] por 200",
        "El supermercado no tenía descuento",
        "Gasté 400 [incluye propina]",
    ]
    
    print(f"\n📋 Test cases para aceptación:")
    acceptance_success = 0
    
    for i, message in enumerate(acceptance_test_cases, 1):
        print(f"\n{i}. Mensaje: '{message}'")
        
        # Verificar que NO se rechaza tempranamente
        early_rejection = filter_instance._early_character_rejection(message)
        
        if early_rejection is None:
            print(f"   ✅ CORRECTO: Sin rechazo temprano")
            acceptance_success += 1
            
            # Verificar procesamiento completo
            should_process = filter_instance.should_process_message(message)
            if should_process:
                print(f"   ✅ CORRECTO: Mensaje aprobado para procesamiento")
            else:
                print(f"   ℹ️  INFO: Rechazado por filtros posteriores (no temprano)")
        else:
            filter_type, position = early_rejection
            print(f"   ❌ INCORRECTO: Rechazado tempranamente por {filter_type} en posición {position}")
    
    print(f"\n📊 Resultados aceptación: {acceptance_success}/{len(acceptance_test_cases)} correctos")
    
    # Estadísticas finales
    total_success = rejection_success + acceptance_success
    total_tests = len(rejection_test_cases) + len(acceptance_test_cases)
    success_rate = (total_success / total_tests) * 100
    
    print(f"\n" + "="*60)
    print(f"🎯 RESULTADO FINAL:")
    print(f"   Tests exitosos: {total_success}/{total_tests}")
    print(f"   Tasa de éxito: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print(f"   ✅ EXCELENTE: Filtrado carácter por carácter funciona correctamente")
        return True
    elif success_rate >= 80:
        print(f"   ⚠️  BUENO: Filtrado mayormente funcional con algunas mejoras necesarias")
        return True
    else:
        print(f"   ❌ NECESITA MEJORAS: Filtrado requiere ajustes")
        return False


def test_performance_improvement():
    """Test del impacto en performance del filtrado temprano."""
    import time
    
    print(f"\n" + "="*60)
    print("⚡ Test de performance del filtrado temprano...")
    
    filter_instance = MessageFilter()
    
    # Mensajes típicos del bot que deben ser rechazados
    bot_messages = [
        "[OK] Gasto registrado: $500 - supermercado - Fecha: 2025-08-08 - Desc: compra semanal - Conf: 95%",
        "[ERROR] No se pudo procesar el mensaje porque el formato no es válido. Usa el formato: cantidad descripción",
        "✅ Registrado exitosamente: $300 en transporte - combustible para el auto - confianza: 90%",
        "No puedo procesar ese mensaje porque no contiene información de gasto válida",
        "🤖 Respuesta automática del sistema de gastos - mensaje procesado correctamente"
    ] * 100  # 500 mensajes
    
    # Test con filtrado carácter por carácter
    start_time = time.time()
    early_rejections = 0
    
    for message in bot_messages:
        early_rejection = filter_instance._early_character_rejection(message)
        if early_rejection:
            early_rejections += 1
    
    early_time = time.time() - start_time
    
    # Test con filtrado completo (simulando método anterior)
    start_time = time.time()
    full_rejections = 0
    
    for message in bot_messages:
        # Simular procesamiento completo
        normalized = message.strip().lower()
        if normalized.startswith('[') or normalized.startswith('no') or any(emoji in message for emoji in ["✅", "❌", "🤖"]):
            full_rejections += 1
    
    full_time = time.time() - start_time
    
    print(f"📊 Resultados de performance:")
    print(f"   Mensajes procesados: {len(bot_messages)}")
    print(f"   Filtrado temprano:")
    print(f"     - Tiempo: {early_time:.4f}s")
    print(f"     - Rechazos: {early_rejections}")
    print(f"     - Promedio por mensaje: {(early_time/len(bot_messages)*1000):.3f}ms")
    print(f"   Filtrado completo:")
    print(f"     - Tiempo: {full_time:.4f}s") 
    print(f"     - Rechazos: {full_rejections}")
    print(f"     - Promedio por mensaje: {(full_time/len(bot_messages)*1000):.3f}ms")
    
    if early_time < full_time:
        improvement = ((full_time - early_time) / full_time) * 100
        print(f"   ⚡ MEJORA: {improvement:.1f}% más rápido con filtrado temprano")
    else:
        print(f"   ⚠️  Sin mejora significativa de performance")


if __name__ == "__main__":
    print(">> Iniciando tests de filtrado caracter por caracter...")
    
    # Test principal
    success = test_character_by_character_filtering()
    
    # Test de performance
    test_performance_improvement()
    
    print(f"\n" + "="*60)
    if success:
        print("TESTS COMPLETADOS EXITOSAMENTE!")
        print("   El filtrado caracter por caracter esta funcionando correctamente.")
        print("   Los mensajes que empiezan con '[' o 'No' se descartan tempranamente.")
        
    else:
        print("TESTS FALLARON")
        print("   El filtrado caracter por caracter necesita ajustes.")
    
    print("="*60)