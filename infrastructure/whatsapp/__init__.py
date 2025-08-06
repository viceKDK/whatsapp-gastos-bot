"""
WhatsApp Integration Module

Módulo para integración con WhatsApp Web usando Selenium.

Componentes:
- whatsapp_selenium.py: Implementación principal del conector WhatsApp
- whatsapp_sender.py: Servicios de envío de mensajes y respuestas
- WhatsAppSeleniumConnector: Clase principal para automatización
- WhatsAppMessageSender: Servicio para enviar mensajes
- WhatsAppEnhancedConnector: Conector con capacidades de envío
"""

from .whatsapp_selenium import WhatsAppSeleniumConnector
from .whatsapp_sender import WhatsAppMessageSender, WhatsAppEnhancedConnector

__all__ = [
    'WhatsAppSeleniumConnector',
    'WhatsAppMessageSender', 
    'WhatsAppEnhancedConnector'
]