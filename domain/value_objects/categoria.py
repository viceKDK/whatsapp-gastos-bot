"""
Objeto de Valor: Categoria

Representa una categoría de gasto con validaciones.
"""

from dataclasses import dataclass
from typing import Set, ClassVar


@dataclass(frozen=True)
class Categoria:
    """
    Objeto de valor que representa una categoría de gasto.
    
    Attributes:
        nombre: Nombre de la categoría (normalizado)
    """
    
    # Categorías predefinidas válidas
    CATEGORIAS_VALIDAS: ClassVar[Set[str]] = {
        'comida', 'transporte', 'entretenimiento', 'salud', 'servicios',
        'ropa', 'educacion', 'hogar', 'trabajo', 'otros', 'super', 'nafta'
    }
    
    nombre: str
    
    def __post_init__(self):
        """Validaciones post-inicialización."""
        if not isinstance(self.nombre, str):
            raise TypeError("La categoría debe ser un string")
        
        if not self.nombre or not self.nombre.strip():
            raise ValueError("La categoría no puede estar vacía")
        
        # Normalizar: lowercase, sin espacios extra
        nombre_normalizado = self.nombre.lower().strip()
        object.__setattr__(self, 'nombre', nombre_normalizado)
        
        # Validar longitud
        if len(self.nombre) > 50:
            raise ValueError("La categoría no puede tener más de 50 caracteres")
        
        # Validar caracteres permitidos (solo letras, números y algunos especiales)
        if not self.nombre.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            raise ValueError("La categoría contiene caracteres no permitidos")
    
    @classmethod
    def crear_con_validacion_estricta(cls, nombre: str) -> 'Categoria':
        """
        Crea una categoría con validación estricta contra categorías predefinidas.
        
        Args:
            nombre: Nombre de la categoría
            
        Returns:
            Instancia de Categoria
            
        Raises:
            ValueError: Si la categoría no está en la lista de válidas
        """
        categoria = cls(nombre)
        
        if categoria.nombre not in cls.CATEGORIAS_VALIDAS:
            categorias_sugeridas = cls._encontrar_categorias_similares(categoria.nombre)
            mensaje = f"Categoría '{categoria.nombre}' no es válida."
            
            if categorias_sugeridas:
                mensaje += f" ¿Quisiste decir: {', '.join(categorias_sugeridas)}?"
            
            raise ValueError(mensaje)
        
        return categoria
    
    @classmethod
    def _encontrar_categorias_similares(cls, nombre: str, max_sugerencias: int = 3) -> list[str]:
        """
        Encuentra categorías similares usando distancia de edición simple.
        
        Args:
            nombre: Nombre a buscar
            max_sugerencias: Máximo número de sugerencias
            
        Returns:
            Lista de categorías similares
        """
        def distancia_simple(s1: str, s2: str) -> int:
            """Calcula distancia de edición simple."""
            if len(s1) < len(s2):
                return distancia_simple(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        # Calcular distancias y ordenar
        distancias = [
            (categoria, distancia_simple(nombre, categoria))
            for categoria in cls.CATEGORIAS_VALIDAS
        ]
        
        # Filtrar solo las relativamente cercanas y ordenar por distancia
        distancias_cercanas = [
            (cat, dist) for cat, dist in distancias
            if dist <= min(3, len(nombre) // 2 + 1)
        ]
        
        distancias_cercanas.sort(key=lambda x: x[1])
        
        return [cat for cat, _ in distancias_cercanas[:max_sugerencias]]
    
    @classmethod
    def agregar_categoria_valida(cls, nueva_categoria: str) -> None:
        """
        Agrega una nueva categoría a la lista de válidas.
        
        Args:
            nueva_categoria: Nueva categoría a agregar
        """
        categoria_normalizada = nueva_categoria.lower().strip()
        cls.CATEGORIAS_VALIDAS.add(categoria_normalizada)
    
    @classmethod
    def obtener_categorias_validas(cls) -> Set[str]:
        """
        Obtiene el conjunto de categorías válidas.
        
        Returns:
            Set con las categorías válidas
        """
        return cls.CATEGORIAS_VALIDAS.copy()
    
    def es_valida_estricta(self) -> bool:
        """
        Verifica si la categoría está en la lista de válidas.
        
        Returns:
            True si es una categoría válida predefinida
        """
        return self.nombre in self.CATEGORIAS_VALIDAS
    
    def es_similar_a(self, otra_categoria: str) -> bool:
        """
        Verifica si esta categoría es similar a otra (distancia <= 1).
        
        Args:
            otra_categoria: Categoría a comparar
            
        Returns:
            True si son similares
        """
        otra_normalizada = otra_categoria.lower().strip()
        
        # Exactamente igual
        if self.nombre == otra_normalizada:
            return True
        
        # Una contiene a la otra
        if self.nombre in otra_normalizada or otra_normalizada in self.nombre:
            return True
        
        # Usar algoritmo de distancia simple
        return self._encontrar_categorias_similares(otra_normalizada, 1) != []
    
    def to_display_name(self) -> str:
        """
        Convierte a nombre para mostrar (capitalizado).
        
        Returns:
            Nombre de la categoría capitalizado
        """
        return self.nombre.capitalize()
    
    def __str__(self) -> str:
        """Representación string de la categoría."""
        return self.nombre