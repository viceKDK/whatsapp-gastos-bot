"""
Servicio de Registro de Gastos

Maneja la persistencia de gastos en el sistema de almacenamiento configurado.
"""

from typing import List, Optional, Protocol
from datetime import datetime, date

from domain.models.gasto import Gasto
from shared.logger import get_logger


logger = get_logger(__name__)


class StorageRepository(Protocol):
    """Protocol que define la interfaz para repositorios de almacenamiento."""
    
    def guardar_gasto(self, gasto: Gasto) -> bool:
        """Guarda un gasto en el almacenamiento."""
        ...
    
    def obtener_gastos(self, fecha_desde: date, fecha_hasta: date) -> List[Gasto]:
        """Obtiene gastos en un rango de fechas."""
        ...
    
    def obtener_gastos_por_categoria(self, categoria: str) -> List[Gasto]:
        """Obtiene gastos de una categoría específica."""
        ...


class RegistrarGastoService:
    """Servicio para registrar y gestionar gastos."""
    
    def __init__(self, storage_repository: StorageRepository):
        self.storage = storage_repository
        self.logger = logger
    
    def registrar_gasto(self, gasto: Gasto) -> bool:
        """
        Registra un nuevo gasto en el sistema.
        
        Args:
            gasto: Instancia de Gasto a registrar
            
        Returns:
            True si el gasto se registró exitosamente, False si no
        """
        try:
            self.logger.info(f"Registrando gasto: {gasto.monto} - {gasto.categoria}")
            
            # Validaciones adicionales del negocio
            if not self._validar_gasto(gasto):
                self.logger.warning("Gasto no pasó validaciones del negocio")
                return False
            
            # Guardar en almacenamiento
            resultado = self.storage.guardar_gasto(gasto)
            
            if resultado:
                self.logger.info(f"💾 GUARDADO EN EXCEL: ${gasto.monto} - {gasto.categoria}")
                self.logger.info(f"📊 ID: {getattr(gasto, 'id', 'N/A')} | Fecha: {gasto.fecha}")
            else:
                self.logger.error("❌ ERROR guardando gasto en almacenamiento")
            
            return resultado
            
        except Exception as e:
            self.logger.error(f"Error registrando gasto: {str(e)}")
            return False
    
    def obtener_gastos_periodo(self, fecha_desde: date, fecha_hasta: Optional[date] = None) -> List[Gasto]:
        """
        Obtiene gastos en un período de tiempo.
        
        Args:
            fecha_desde: Fecha inicio del período
            fecha_hasta: Fecha fin del período (opcional, default: hoy)
            
        Returns:
            Lista de gastos en el período
        """
        try:
            if fecha_hasta is None:
                fecha_hasta = date.today()
            
            self.logger.debug(f"Obteniendo gastos desde {fecha_desde} hasta {fecha_hasta}")
            
            gastos = self.storage.obtener_gastos(fecha_desde, fecha_hasta)
            
            self.logger.info(f"Encontrados {len(gastos)} gastos en el período")
            return gastos
            
        except Exception as e:
            self.logger.error(f"Error obteniendo gastos: {str(e)}")
            return []
    
    def obtener_gastos_categoria(self, categoria: str) -> List[Gasto]:
        """
        Obtiene todos los gastos de una categoría específica.
        
        Args:
            categoria: Nombre de la categoría
            
        Returns:
            Lista de gastos de la categoría
        """
        try:
            self.logger.debug(f"Obteniendo gastos de categoría: {categoria}")
            
            gastos = self.storage.obtener_gastos_por_categoria(categoria.lower())
            
            self.logger.info(f"Encontrados {len(gastos)} gastos en categoría '{categoria}'")
            return gastos
            
        except Exception as e:
            self.logger.error(f"Error obteniendo gastos por categoría: {str(e)}")
            return []
    
    def _validar_gasto(self, gasto: Gasto) -> bool:
        """
        Realiza validaciones del negocio sobre el gasto.
        
        Args:
            gasto: Gasto a validar
            
        Returns:
            True si es válido, False si no
        """
        # Validar que no sea un gasto duplicado muy reciente
        if self._es_gasto_duplicado_reciente(gasto):
            self.logger.warning("Gasto parece ser duplicado reciente")
            return False
        
        # Validar monto razonable (no más de $100,000)
        if gasto.monto > 100000:
            self.logger.warning(f"Monto muy alto: {gasto.monto}")
            return False
        
        return True
    
    def _es_gasto_duplicado_reciente(self, gasto: Gasto) -> bool:
        """
        Verifica si existe un gasto muy similar en los últimos 5 minutos.
        
        Args:
            gasto: Gasto a verificar
            
        Returns:
            True si parece duplicado, False si no
        """
        try:
            # Obtener gastos del día actual
            gastos_hoy = self.storage.obtener_gastos(gasto.fecha.date(), gasto.fecha.date())
            
            # Buscar gastos similares en los últimos 5 minutos
            for gasto_existente in gastos_hoy:
                diferencia_tiempo = abs((gasto.fecha - gasto_existente.fecha).total_seconds())
                
                if (diferencia_tiempo < 300 and  # 5 minutos
                    gasto.monto == gasto_existente.monto and
                    gasto.categoria == gasto_existente.categoria):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error verificando duplicados: {str(e)}")
            # En caso de error, asumimos que no es duplicado
            return False