"""
Sistema de Etiquetas y Filtros Avanzados

Permite organizar gastos con etiquetas personalizadas y aplicar 
filtros dinámicos para análisis detallado.
"""

import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

from domain.models.gasto import Gasto
from config.config_manager import get_config
from shared.logger import get_logger


logger = get_logger(__name__)


class FilterOperator(Enum):
    """Operadores para filtros."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"
    BETWEEN = "between"


@dataclass
class Tag:
    """Representa una etiqueta personalizada."""
    name: str
    color: str = "#007bff"  # Color por defecto (azul)
    description: str = ""
    created_at: datetime = None
    usage_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'usage_count': self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tag':
        """Crea desde diccionario."""
        return cls(
            name=data['name'],
            color=data.get('color', '#007bff'),
            description=data.get('description', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            usage_count=data.get('usage_count', 0)
        )


@dataclass
class FilterCondition:
    """Condición de filtro individual."""
    field: str  # 'monto', 'categoria', 'fecha', 'descripcion', 'tags'
    operator: FilterOperator
    value: Any
    case_sensitive: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'field': self.field,
            'operator': self.operator.value,
            'value': self.value,
            'case_sensitive': self.case_sensitive
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterCondition':
        """Crea desde diccionario."""
        return cls(
            field=data['field'],
            operator=FilterOperator(data['operator']),
            value=data['value'],
            case_sensitive=data.get('case_sensitive', False)
        )


@dataclass
class Filter:
    """Filtro completo con múltiples condiciones."""
    name: str
    conditions: List[FilterCondition]
    logic_operator: str = "AND"  # "AND" o "OR"
    description: str = ""
    created_at: datetime = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'name': self.name,
            'conditions': [cond.to_dict() for cond in self.conditions],
            'logic_operator': self.logic_operator,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'usage_count': self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Filter':
        """Crea desde diccionario."""
        return cls(
            name=data['name'],
            conditions=[FilterCondition.from_dict(cond) for cond in data['conditions']],
            logic_operator=data.get('logic_operator', 'AND'),
            description=data.get('description', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            last_used=datetime.fromisoformat(data['last_used']) if data.get('last_used') else None,
            usage_count=data.get('usage_count', 0)
        )


class TagManager:
    """Gestor de etiquetas personalizable."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logger
        self.tags_file = Path("data/tags.json")
        self.tags_file.parent.mkdir(exist_ok=True)
        
        # Cache de etiquetas
        self._tags: Dict[str, Tag] = {}
        self._gasto_tags: Dict[str, Set[str]] = defaultdict(set)  # gasto_id -> tags
        
        self.load_tags()
    
    def create_tag(self, name: str, color: str = "#007bff", description: str = "") -> Tag:
        """
        Crea una nueva etiqueta.
        
        Args:
            name: Nombre de la etiqueta
            color: Color hexadecimal
            description: Descripción opcional
            
        Returns:
            Tag creada
        """
        # Normalizar nombre
        name = name.strip().lower()
        
        if not name:
            raise ValueError("El nombre de la etiqueta no puede estar vacío")
        
        if name in self._tags:
            raise ValueError(f"Ya existe una etiqueta con el nombre '{name}'")
        
        # Validar color
        if not re.match(r'^#[0-9a-fA-F]{6}$', color):
            color = "#007bff"  # Color por defecto
        
        tag = Tag(name=name, color=color, description=description)
        self._tags[name] = tag
        
        self.save_tags()
        self.logger.info(f"Etiqueta creada: {name}")
        
        return tag
    
    def get_tag(self, name: str) -> Optional[Tag]:
        """Obtiene una etiqueta por nombre."""
        return self._tags.get(name.strip().lower())
    
    def list_tags(self) -> List[Tag]:
        """Lista todas las etiquetas."""
        return list(self._tags.values())
    
    def update_tag(self, name: str, color: Optional[str] = None, description: Optional[str] = None) -> bool:
        """
        Actualiza una etiqueta existente.
        
        Args:
            name: Nombre de la etiqueta
            color: Nuevo color (opcional)
            description: Nueva descripción (opcional)
            
        Returns:
            True si se actualizó correctamente
        """
        name = name.strip().lower()
        
        if name not in self._tags:
            return False
        
        tag = self._tags[name]
        
        if color and re.match(r'^#[0-9a-fA-F]{6}$', color):
            tag.color = color
        
        if description is not None:
            tag.description = description
        
        self.save_tags()
        self.logger.info(f"Etiqueta actualizada: {name}")
        
        return True
    
    def delete_tag(self, name: str) -> bool:
        """
        Elimina una etiqueta.
        
        Args:
            name: Nombre de la etiqueta
            
        Returns:
            True si se eliminó correctamente
        """
        name = name.strip().lower()
        
        if name not in self._tags:
            return False
        
        # Remover de todos los gastos
        for gasto_id in list(self._gasto_tags.keys()):
            self._gasto_tags[gasto_id].discard(name)
            if not self._gasto_tags[gasto_id]:
                del self._gasto_tags[gasto_id]
        
        # Eliminar etiqueta
        del self._tags[name]
        
        self.save_tags()
        self.logger.info(f"Etiqueta eliminada: {name}")
        
        return True
    
    def add_tag_to_gasto(self, gasto_id: str, tag_name: str) -> bool:
        """
        Agrega etiqueta a un gasto.
        
        Args:
            gasto_id: ID del gasto
            tag_name: Nombre de la etiqueta
            
        Returns:
            True si se agregó correctamente
        """
        tag_name = tag_name.strip().lower()
        
        if tag_name not in self._tags:
            self.logger.warning(f"Etiqueta '{tag_name}' no existe")
            return False
        
        self._gasto_tags[gasto_id].add(tag_name)
        
        # Incrementar contador de uso
        self._tags[tag_name].usage_count += 1
        
        self.save_tags()
        return True
    
    def remove_tag_from_gasto(self, gasto_id: str, tag_name: str) -> bool:
        """
        Remueve etiqueta de un gasto.
        
        Args:
            gasto_id: ID del gasto
            tag_name: Nombre de la etiqueta
            
        Returns:
            True si se removió correctamente
        """
        tag_name = tag_name.strip().lower()
        
        if gasto_id not in self._gasto_tags:
            return False
        
        if tag_name in self._gasto_tags[gasto_id]:
            self._gasto_tags[gasto_id].discard(tag_name)
            
            # Decrementar contador de uso
            if tag_name in self._tags:
                self._tags[tag_name].usage_count = max(0, self._tags[tag_name].usage_count - 1)
            
            # Limpiar si no hay más etiquetas
            if not self._gasto_tags[gasto_id]:
                del self._gasto_tags[gasto_id]
            
            self.save_tags()
            return True
        
        return False
    
    def get_gasto_tags(self, gasto_id: str) -> Set[str]:
        """Obtiene etiquetas de un gasto."""
        return self._gasto_tags.get(gasto_id, set()).copy()
    
    def get_gastos_with_tag(self, tag_name: str) -> Set[str]:
        """Obtiene IDs de gastos que tienen una etiqueta específica."""
        tag_name = tag_name.strip().lower()
        
        return {
            gasto_id for gasto_id, tags in self._gasto_tags.items()
            if tag_name in tags
        }
    
    def get_tag_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de uso de etiquetas."""
        total_tags = len(self._tags)
        total_tagged_gastos = len(self._gasto_tags)
        total_tag_assignments = sum(len(tags) for tags in self._gasto_tags.values())
        
        # Etiquetas más usadas
        most_used = sorted(
            self._tags.values(),
            key=lambda t: t.usage_count,
            reverse=True
        )[:5]
        
        return {
            'total_tags': total_tags,
            'total_tagged_gastos': total_tagged_gastos,
            'total_tag_assignments': total_tag_assignments,
            'most_used_tags': [
                {'name': tag.name, 'usage_count': tag.usage_count, 'color': tag.color}
                for tag in most_used
            ],
            'average_tags_per_gasto': total_tag_assignments / max(1, total_tagged_gastos)
        }
    
    def suggest_tags_for_gasto(self, gasto: Gasto) -> List[str]:
        """
        Sugiere etiquetas para un gasto basándose en patrones.
        
        Args:
            gasto: Gasto a analizar
            
        Returns:
            Lista de nombres de etiquetas sugeridas
        """
        suggestions = []
        
        descripcion = (gasto.descripcion or "").lower()
        categoria = gasto.categoria.lower()
        monto = float(gasto.monto)
        
        # Sugerencias basadas en monto
        if monto > 2000:
            suggestions.append("gasto_alto")
        elif monto < 100:
            suggestions.append("gasto_pequeño")
        
        # Sugerencias basadas en categoría
        if categoria == "comida":
            if "delivery" in descripcion or "uber" in descripcion:
                suggestions.append("delivery")
            if "restaurant" in descripcion:
                suggestions.append("restaurant")
        elif categoria == "transporte":
            if "nafta" in descripcion or "combustible" in descripcion:
                suggestions.append("combustible")
            if "taxi" in descripcion or "uber" in descripcion:
                suggestions.append("transporte_urbano")
        
        # Sugerencias basadas en día de la semana
        dia_semana = gasto.fecha.weekday()
        if dia_semana >= 5:  # Sábado o domingo
            suggestions.append("fin_de_semana")
        
        # Solo sugerir etiquetas que existen
        suggestions = [tag for tag in suggestions if tag in self._tags]
        
        return suggestions[:3]  # Máximo 3 sugerencias
    
    def save_tags(self):
        """Guarda etiquetas en archivo."""
        try:
            data = {
                'tags': {name: tag.to_dict() for name, tag in self._tags.items()},
                'gasto_tags': {
                    gasto_id: list(tags) 
                    for gasto_id, tags in self._gasto_tags.items()
                },
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.tags_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error guardando etiquetas: {e}")
    
    def load_tags(self):
        """Carga etiquetas desde archivo."""
        try:
            if self.tags_file.exists():
                with open(self.tags_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Cargar etiquetas
                if 'tags' in data:
                    self._tags = {
                        name: Tag.from_dict(tag_data)
                        for name, tag_data in data['tags'].items()
                    }
                
                # Cargar asignaciones
                if 'gasto_tags' in data:
                    self._gasto_tags = {
                        gasto_id: set(tags)
                        for gasto_id, tags in data['gasto_tags'].items()
                    }
                
                self.logger.info(f"Cargadas {len(self._tags)} etiquetas")
                
        except Exception as e:
            self.logger.error(f"Error cargando etiquetas: {e}")
            self._tags = {}
            self._gasto_tags = defaultdict(set)


class FilterEngine:
    """Motor de filtros para gastos."""
    
    def __init__(self, tag_manager: TagManager):
        self.tag_manager = tag_manager
        self.logger = logger
        self.filters_file = Path("data/filters.json")
        self.filters_file.parent.mkdir(exist_ok=True)
        
        # Cache de filtros guardados
        self._saved_filters: Dict[str, Filter] = {}
        
        self.load_filters()
    
    def apply_filter(self, gastos: List[Gasto], filter_obj: Union[Filter, Dict[str, Any]]) -> List[Gasto]:
        """
        Aplica filtro a lista de gastos.
        
        Args:
            gastos: Lista de gastos a filtrar
            filter_obj: Filtro a aplicar
            
        Returns:
            Lista filtrada de gastos
        """
        if isinstance(filter_obj, dict):
            filter_obj = Filter.from_dict(filter_obj)
        
        try:
            filtered_gastos = []
            
            for gasto in gastos:
                if self._evaluate_gasto(gasto, filter_obj):
                    filtered_gastos.append(gasto)
            
            # Actualizar estadísticas del filtro si es guardado
            if filter_obj.name in self._saved_filters:
                self._saved_filters[filter_obj.name].last_used = datetime.now()
                self._saved_filters[filter_obj.name].usage_count += 1
                self.save_filters()
            
            self.logger.debug(f"Filtro aplicado: {len(filtered_gastos)}/{len(gastos)} gastos coinciden")
            
            return filtered_gastos
            
        except Exception as e:
            self.logger.error(f"Error aplicando filtro: {e}")
            return gastos  # Retornar sin filtrar en caso de error
    
    def _evaluate_gasto(self, gasto: Gasto, filter_obj: Filter) -> bool:
        """Evalúa si un gasto cumple con las condiciones del filtro."""
        if not filter_obj.conditions:
            return True
        
        condition_results = []
        
        for condition in filter_obj.conditions:
            result = self._evaluate_condition(gasto, condition)
            condition_results.append(result)
        
        # Aplicar lógica AND/OR
        if filter_obj.logic_operator.upper() == "OR":
            return any(condition_results)
        else:  # AND por defecto
            return all(condition_results)
    
    def _evaluate_condition(self, gasto: Gasto, condition: FilterCondition) -> bool:
        """Evalúa una condición individual."""
        try:
            field_value = self._get_field_value(gasto, condition.field)
            
            if field_value is None:
                return condition.operator == FilterOperator.NOT_EQUALS
            
            return self._apply_operator(field_value, condition.operator, condition.value, condition.case_sensitive)
            
        except Exception as e:
            self.logger.error(f"Error evaluando condición: {e}")
            return False
    
    def _get_field_value(self, gasto: Gasto, field: str) -> Any:
        """Obtiene el valor de un campo del gasto."""
        if field == "monto":
            return float(gasto.monto)
        elif field == "categoria":
            return gasto.categoria
        elif field == "fecha":
            return gasto.fecha
        elif field == "descripcion":
            return gasto.descripcion or ""
        elif field == "tags":
            gasto_id = str(id(gasto))  # Usar ID del objeto como clave temporal
            return list(self.tag_manager.get_gasto_tags(gasto_id))
        elif field == "dia_semana":
            return gasto.fecha.weekday()  # 0=Lunes, 6=Domingo
        elif field == "mes":
            return gasto.fecha.month
        elif field == "año":
            return gasto.fecha.year
        else:
            return None
    
    def _apply_operator(self, field_value: Any, operator: FilterOperator, 
                       condition_value: Any, case_sensitive: bool = False) -> bool:
        """Aplica operador de comparación."""
        try:
            # Preparar valores para comparación de strings
            if isinstance(field_value, str) and not case_sensitive:
                field_value = field_value.lower()
                if isinstance(condition_value, str):
                    condition_value = condition_value.lower()
            
            if operator == FilterOperator.EQUALS:
                return field_value == condition_value
            
            elif operator == FilterOperator.NOT_EQUALS:
                return field_value != condition_value
            
            elif operator == FilterOperator.GREATER_THAN:
                return field_value > condition_value
            
            elif operator == FilterOperator.GREATER_EQUAL:
                return field_value >= condition_value
            
            elif operator == FilterOperator.LESS_THAN:
                return field_value < condition_value
            
            elif operator == FilterOperator.LESS_EQUAL:
                return field_value <= condition_value
            
            elif operator == FilterOperator.CONTAINS:
                return str(condition_value) in str(field_value)
            
            elif operator == FilterOperator.NOT_CONTAINS:
                return str(condition_value) not in str(field_value)
            
            elif operator == FilterOperator.STARTS_WITH:
                return str(field_value).startswith(str(condition_value))
            
            elif operator == FilterOperator.ENDS_WITH:
                return str(field_value).endswith(str(condition_value))
            
            elif operator == FilterOperator.IN:
                if isinstance(condition_value, (list, tuple, set)):
                    return field_value in condition_value
                return field_value == condition_value
            
            elif operator == FilterOperator.NOT_IN:
                if isinstance(condition_value, (list, tuple, set)):
                    return field_value not in condition_value
                return field_value != condition_value
            
            elif operator == FilterOperator.REGEX:
                pattern = re.compile(str(condition_value), 
                                   0 if case_sensitive else re.IGNORECASE)
                return bool(pattern.search(str(field_value)))
            
            elif operator == FilterOperator.BETWEEN:
                if isinstance(condition_value, (list, tuple)) and len(condition_value) == 2:
                    return condition_value[0] <= field_value <= condition_value[1]
                return False
            
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error aplicando operador {operator}: {e}")
            return False
    
    def create_quick_filter(self, field: str, operator: FilterOperator, value: Any) -> Filter:
        """Crea un filtro rápido con una sola condición."""
        condition = FilterCondition(field=field, operator=operator, value=value)
        
        return Filter(
            name=f"filtro_rapido_{field}_{operator.value}",
            conditions=[condition],
            description=f"Filtro rápido: {field} {operator.value} {value}"
        )
    
    def save_filter(self, filter_obj: Filter) -> bool:
        """
        Guarda un filtro para uso posterior.
        
        Args:
            filter_obj: Filtro a guardar
            
        Returns:
            True si se guardó correctamente
        """
        try:
            self._saved_filters[filter_obj.name] = filter_obj
            self.save_filters()
            self.logger.info(f"Filtro guardado: {filter_obj.name}")
            return True
        except Exception as e:
            self.logger.error(f"Error guardando filtro: {e}")
            return False
    
    def get_saved_filter(self, name: str) -> Optional[Filter]:
        """Obtiene un filtro guardado por nombre."""
        return self._saved_filters.get(name)
    
    def list_saved_filters(self) -> List[Filter]:
        """Lista todos los filtros guardados."""
        return list(self._saved_filters.values())
    
    def delete_saved_filter(self, name: str) -> bool:
        """Elimina un filtro guardado."""
        if name in self._saved_filters:
            del self._saved_filters[name]
            self.save_filters()
            self.logger.info(f"Filtro eliminado: {name}")
            return True
        return False
    
    def get_filter_suggestions(self, gastos: List[Gasto]) -> List[Dict[str, Any]]:
        """
        Sugiere filtros útiles basándose en los datos de gastos.
        
        Args:
            gastos: Lista de gastos para analizar
            
        Returns:
            Lista de sugerencias de filtros
        """
        if not gastos:
            return []
        
        suggestions = []
        
        # Analizar rangos de montos
        montos = [float(g.monto) for g in gastos]
        monto_min, monto_max = min(montos), max(montos)
        monto_medio = sum(montos) / len(montos)
        
        # Sugerir filtros por monto
        suggestions.append({
            'name': 'Gastos altos',
            'description': f'Gastos mayores a ${monto_medio*1.5:.0f}',
            'filter': self.create_quick_filter('monto', FilterOperator.GREATER_THAN, monto_medio * 1.5)
        })
        
        # Analizar categorías más comunes
        categorias = [g.categoria for g in gastos]
        categoria_counts = defaultdict(int)
        for cat in categorias:
            categoria_counts[cat] += 1
        
        categorias_comunes = sorted(categoria_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for categoria, count in categorias_comunes:
            suggestions.append({
                'name': f'Solo {categoria}',
                'description': f'Filtrar solo gastos de {categoria} ({count} gastos)',
                'filter': self.create_quick_filter('categoria', FilterOperator.EQUALS, categoria)
            })
        
        # Sugerir filtros por fecha
        fechas_recientes = datetime.now() - timedelta(days=7)
        suggestions.append({
            'name': 'Última semana',
            'description': 'Gastos de los últimos 7 días',
            'filter': self.create_quick_filter('fecha', FilterOperator.GREATER_EQUAL, fechas_recientes)
        })
        
        return suggestions[:5]  # Máximo 5 sugerencias
    
    def save_filters(self):
        """Guarda filtros en archivo."""
        try:
            data = {
                'filters': {name: filter_obj.to_dict() for name, filter_obj in self._saved_filters.items()},
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.filters_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error guardando filtros: {e}")
    
    def load_filters(self):
        """Carga filtros desde archivo."""
        try:
            if self.filters_file.exists():
                with open(self.filters_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'filters' in data:
                    self._saved_filters = {
                        name: Filter.from_dict(filter_data)
                        for name, filter_data in data['filters'].items()
                    }
                
                self.logger.info(f"Cargados {len(self._saved_filters)} filtros")
                
        except Exception as e:
            self.logger.error(f"Error cargando filtros: {e}")
            self._saved_filters = {}


class TagFilterSystem:
    """Sistema completo de etiquetas y filtros."""
    
    def __init__(self):
        self.logger = logger
        self.tag_manager = TagManager()
        self.filter_engine = FilterEngine(self.tag_manager)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas completas del sistema."""
        tag_stats = self.tag_manager.get_tag_statistics()
        filter_count = len(self.filter_engine.list_saved_filters())
        
        return {
            'tags': tag_stats,
            'saved_filters': filter_count,
            'system_ready': True
        }


# Instancia global del sistema
_tag_filter_system: Optional[TagFilterSystem] = None


def get_tag_filter_system() -> TagFilterSystem:
    """Obtiene instancia global del sistema de etiquetas y filtros."""
    global _tag_filter_system
    if _tag_filter_system is None:
        _tag_filter_system = TagFilterSystem()
    return _tag_filter_system