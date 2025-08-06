"""
Objeto de Valor: Monto

Representa una cantidad monetaria con validaciones.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union


@dataclass(frozen=True)
class Monto:
    """
    Objeto de valor que representa un monto monetario.
    
    Attributes:
        valor: Valor decimal del monto
    """
    
    valor: Decimal
    
    def __post_init__(self):
        """Validaciones post-inicialización."""
        if not isinstance(self.valor, Decimal):
            # Convertir a Decimal si es necesario
            try:
                object.__setattr__(self, 'valor', Decimal(str(self.valor)))
            except (ValueError, TypeError) as e:
                raise ValueError(f"Monto inválido: {e}")
        
        # Validar que sea positivo
        if self.valor <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        
        # Validar máximo 2 decimales
        if self.valor.as_tuple().exponent < -2:
            # Redondear a 2 decimales
            valor_redondeado = self.valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            object.__setattr__(self, 'valor', valor_redondeado)
        
        # Validar límite máximo razonable (1 millón)
        if self.valor > Decimal('1000000'):
            raise ValueError("El monto excede el límite máximo de $1,000,000")
    
    @classmethod
    def from_string(cls, monto_str: str) -> 'Monto':
        """
        Crea un Monto desde una cadena.
        
        Args:
            monto_str: String representando el monto (ej: "150", "150.50", "$150")
            
        Returns:
            Instancia de Monto
            
        Raises:
            ValueError: Si el string no es un monto válido
        """
        # Limpiar string (remover $, espacios, etc.)
        monto_limpio = monto_str.strip().replace('$', '').replace(',', '')
        
        try:
            return cls(Decimal(monto_limpio))
        except Exception as e:
            raise ValueError(f"No se puede convertir '{monto_str}' a monto: {e}")
    
    @classmethod
    def from_float(cls, monto_float: float) -> 'Monto':
        """
        Crea un Monto desde un float.
        
        Args:
            monto_float: Float representando el monto
            
        Returns:
            Instancia de Monto
        """
        # Convertir float a string para evitar problemas de precisión
        return cls(Decimal(str(monto_float)))
    
    def sumar(self, otro: Union['Monto', Decimal, float]) -> 'Monto':
        """
        Suma otro monto a este.
        
        Args:
            otro: Otro Monto, Decimal o float a sumar
            
        Returns:
            Nuevo Monto con la suma
        """
        if isinstance(otro, Monto):
            return Monto(self.valor + otro.valor)
        elif isinstance(otro, (Decimal, float)):
            return Monto(self.valor + Decimal(str(otro)))
        else:
            raise TypeError(f"No se puede sumar Monto con {type(otro)}")
    
    def restar(self, otro: Union['Monto', Decimal, float]) -> 'Monto':
        """
        Resta otro monto de este.
        
        Args:
            otro: Otro Monto, Decimal o float a restar
            
        Returns:
            Nuevo Monto con la resta
            
        Raises:
            ValueError: Si el resultado sería negativo
        """
        if isinstance(otro, Monto):
            resultado = self.valor - otro.valor
        elif isinstance(otro, (Decimal, float)):
            resultado = self.valor - Decimal(str(otro))
        else:
            raise TypeError(f"No se puede restar {type(otro)} de Monto")
        
        if resultado <= 0:
            raise ValueError("La resta resultaría en un monto no positivo")
        
        return Monto(resultado)
    
    def multiplicar(self, factor: Union[int, float, Decimal]) -> 'Monto':
        """
        Multiplica el monto por un factor.
        
        Args:
            factor: Factor de multiplicación
            
        Returns:
            Nuevo Monto multiplicado
        """
        resultado = self.valor * Decimal(str(factor))
        return Monto(resultado)
    
    def es_mayor_que(self, otro: 'Monto') -> bool:
        """Compara si este monto es mayor que otro."""
        return self.valor > otro.valor
    
    def es_menor_que(self, otro: 'Monto') -> bool:
        """Compara si este monto es menor que otro."""
        return self.valor < otro.valor
    
    def to_float(self) -> float:
        """Convierte a float (usar con cuidado por precisión)."""
        return float(self.valor)
    
    def to_string_formatted(self, include_currency: bool = True) -> str:
        """
        Convierte a string formateado.
        
        Args:
            include_currency: Si incluir símbolo de moneda
            
        Returns:
            String formateado del monto
        """
        formatted = f"{self.valor:,.2f}"
        
        if include_currency:
            return f"${formatted}"
        
        return formatted
    
    def __str__(self) -> str:
        """Representación string del monto."""
        return self.to_string_formatted()
    
    def __float__(self) -> float:
        """Conversión a float."""
        return self.to_float()
    
    def __add__(self, otro):
        """Operador + sobrecargado."""
        return self.sumar(otro)
    
    def __sub__(self, otro):
        """Operador - sobrecargado."""
        return self.restar(otro)
    
    def __mul__(self, factor):
        """Operador * sobrecargado."""
        return self.multiplicar(factor)
    
    def __gt__(self, otro):
        """Operador > sobrecargado."""
        if isinstance(otro, Monto):
            return self.es_mayor_que(otro)
        return self.valor > Decimal(str(otro))
    
    def __lt__(self, otro):
        """Operador < sobrecargado."""
        if isinstance(otro, Monto):
            return self.es_menor_que(otro)
        return self.valor < Decimal(str(otro))