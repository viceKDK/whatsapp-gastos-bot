"""
Caso de Uso: Procesar Mensaje

Orquestador principal que coordina la interpretación y registro de gastos.
"""

from typing import Optional
from datetime import datetime

from domain.models.gasto import Gasto
from app.services.interpretar_mensaje import InterpretarMensajeService
from app.services.registrar_gasto import RegistrarGastoService, StorageRepository
from shared.logger import get_logger


logger = get_logger(__name__)


class ProcesarMensajeUseCase:
    """Caso de uso para procesar mensajes de WhatsApp y registrar gastos."""
    
    def __init__(self, storage_repository: StorageRepository):
        self.interpretar_service = InterpretarMensajeService()
        self.registrar_service = RegistrarGastoService(storage_repository)
        self.logger = logger
    
    def procesar(self, mensaje_texto: str, fecha_mensaje: Optional[datetime] = None) -> Optional[Gasto]:
        """
        Procesa un mensaje completo: interpretación + registro.
        
        Args:
            mensaje_texto: Texto del mensaje de WhatsApp
            fecha_mensaje: Fecha del mensaje (opcional)
            
        Returns:
            Gasto registrado si fue exitoso, None si no
        """
        try:
            self.logger.info(f"Iniciando procesamiento de mensaje: '{mensaje_texto[:50]}...'")
            
            # Paso 1: Interpretar mensaje
            gasto = self.interpretar_service.procesar_mensaje(mensaje_texto, fecha_mensaje)
            
            if not gasto:
                self.logger.debug("Mensaje no contiene información de gasto válida")
                return None
            
            # Paso 2: Registrar gasto
            registro_exitoso = self.registrar_service.registrar_gasto(gasto)
            
            if not registro_exitoso:
                self.logger.error("Error registrando gasto interpretado")
                return None
            
            self.logger.info(f"Mensaje procesado exitosamente: {gasto.monto} - {gasto.categoria}")
            return gasto
            
        except Exception as e:
            self.logger.error(f"Error procesando mensaje: {str(e)}")
            return None
    
    def procesar_batch(self, mensajes: list[tuple[str, Optional[datetime]]]) -> list[Gasto]:
        """
        Procesa múltiples mensajes en batch.
        
        Args:
            mensajes: Lista de tuplas (texto_mensaje, fecha_mensaje)
            
        Returns:
            Lista de gastos registrados exitosamente
        """
        gastos_registrados = []
        
        self.logger.info(f"Iniciando procesamiento batch de {len(mensajes)} mensajes")
        
        for i, (texto, fecha) in enumerate(mensajes, 1):
            self.logger.debug(f"Procesando mensaje {i}/{len(mensajes)}")
            
            gasto = self.procesar(texto, fecha)
            if gasto:
                gastos_registrados.append(gasto)
        
        self.logger.info(f"Batch procesado: {len(gastos_registrados)}/{len(mensajes)} gastos registrados")
        return gastos_registrados