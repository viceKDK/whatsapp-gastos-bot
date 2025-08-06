"""
Entidad Gasto

Representa un gasto registrado en el sistema.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Optional


@dataclass
class Gasto:
    """
    Entidad principal que representa un gasto.
    
    Attributes:
        monto: Cantidad del gasto (debe ser positivo)
        categoria: Categoría del gasto (comida, transporte, etc.)
        fecha: Fecha y hora del gasto
        descripcion: Descripción opcional del gasto
        id: Identificador único (asignado por el storage)
    """
    
    monto: Decimal
    categoria: str
    fecha: datetime
    descripcion: Optional[str] = None
    id: Optional[int] = field(default=None, init=False)
    
    def __post_init__(self):
        """Validaciones post-inicialización."""
        self._validar_monto()
        self._validar_categoria()
        self._normalizar_categoria()
    
    def _validar_monto(self) -> None:
        """Valida que el monto sea positivo."""
        if not isinstance(self.monto, Decimal):
            raise TypeError("El monto debe ser un Decimal")
        
        if self.monto <= 0:
            raise ValueError("El monto debe ser positivo")
        
        # Validar que tenga máximo 2 decimales
        if self.monto.as_tuple().exponent < -2:
            raise ValueError("El monto no puede tener más de 2 decimales")
    
    def _validar_categoria(self) -> None:
        """Valida que la categoría sea válida."""
        if not self.categoria:
            raise ValueError("La categoría es requerida")
        
        if not isinstance(self.categoria, str):
            raise TypeError("La categoría debe ser un string")
        
        if len(self.categoria.strip()) == 0:
            raise ValueError("La categoría no puede estar vacía")
    
    def _normalizar_categoria(self) -> None:
        """Normaliza la categoría (lowercase, sin espacios extra)."""
        self.categoria = self.categoria.lower().strip()
    
    def es_del_mes(self, año: int, mes: int) -> bool:
        """
        Verifica si el gasto pertenece a un mes específico.
        
        Args:
            año: Año a verificar
            mes: Mes a verificar (1-12)
            
        Returns:
            True si el gasto es del mes especificado
        """
        return self.fecha.year == año and self.fecha.month == mes
    
    def es_de_categoria(self, categoria: str) -> bool:
        """
        Verifica si el gasto pertenece a una categoría específica.
        
        Args:
            categoria: Categoría a verificar
            
        Returns:
            True si coincide con la categoría
        """
        return self.categoria == categoria.lower().strip()
    
    def to_dict(self) -> dict:
        """
        Convierte el gasto a diccionario para serialización.
        
        Returns:
            Diccionario con los datos del gasto
        """
        return {
            'id': self.id,
            'monto': float(self.monto),
            'categoria': self.categoria,
            'fecha': self.fecha.isoformat(),
            'descripcion': self.descripcion
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Gasto':
        """
        Crea un Gasto desde un diccionario.
        
        Args:
            data: Diccionario con los datos del gasto
            
        Returns:
            Instancia de Gasto
        """
        gasto = cls(
            monto=Decimal(str(data['monto'])),
            categoria=data['categoria'],
            fecha=datetime.fromisoformat(data['fecha']),
            descripcion=data.get('descripcion')
        )
        
        if 'id' in data and data['id'] is not None:
            gasto.id = data['id']
        
        return gasto
    
    def __str__(self) -> str:
        """Representación string del gasto."""
        fecha_str = self.fecha.strftime("%Y-%m-%d %H:%M")
        return f"Gasto(${self.monto}, {self.categoria}, {fecha_str})"
    
    def __repr__(self) -> str:
        """Representación técnica del gasto."""
        return (f"Gasto(monto={self.monto}, categoria='{self.categoria}', "
                f"fecha={self.fecha.isoformat()}, descripcion='{self.descripcion}', id={self.id})")
    
    def __eq__(self, other) -> bool:
        """Comparación de igualdad basada en contenido, no en ID."""
        if not isinstance(other, Gasto):
            return False
        
        return (self.monto == other.monto and
                self.categoria == other.categoria and
                self.fecha == other.fecha and
                self.descripcion == other.descripcion)