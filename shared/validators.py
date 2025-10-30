"""
Sistema de Validaciones Robustas

Validadores centralizados para entrada de datos y integridad del sistema.
"""

import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from config.config_manager import get_config
from shared.logger import get_logger


logger = get_logger(__name__)


class ValidationLevel(Enum):
    """Niveles de validación."""
    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"


@dataclass
class ValidationResult:
    """Resultado de una validación."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_value: Any = None
    
    def add_error(self, error: str) -> None:
        """Agrega un error."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Agrega una advertencia."""
        self.warnings.append(warning)
    
    @property
    def has_errors(self) -> bool:
        """Indica si hay errores."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Indica si hay advertencias."""
        return len(self.warnings) > 0


class MontoValidator:
    """Validador para montos monetarios."""
    
    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        self.level = level
        self.config = get_config()
        self.logger = logger
    
    def validate(self, value: Any) -> ValidationResult:
        """
        Valida un monto.
        
        Args:
            value: Valor a validar
            
        Returns:
            Resultado de validación
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        try:
            # Intentar convertir a Decimal
            if isinstance(value, str):
                sanitized = self._sanitize_string_amount(value)
                decimal_value = Decimal(sanitized)
            elif isinstance(value, (int, float)):
                decimal_value = Decimal(str(value))
            elif isinstance(value, Decimal):
                decimal_value = value
            else:
                result.add_error(f"Tipo de dato no válido para monto: {type(value)}")
                return result
            
            # Validar rango
            min_amount = Decimal(str(self.config.validation.min_amount))
            max_amount = Decimal(str(self.config.validation.max_amount))
            
            if decimal_value < min_amount:
                result.add_error(f"El monto {decimal_value} es menor al mínimo permitido: {min_amount}")
            elif decimal_value > max_amount:
                result.add_error(f"El monto {decimal_value} excede el máximo permitido: {max_amount}")
            
            # Validar decimales
            decimal_places = abs(decimal_value.as_tuple().exponent)
            if decimal_places > 2:
                if self.level == ValidationLevel.STRICT:
                    result.add_error(f"El monto no puede tener más de 2 decimales: {decimal_value}")
                else:
                    result.add_warning(f"Monto redondeado de {decimal_value} a 2 decimales")
                    decimal_value = decimal_value.quantize(Decimal('0.01'))
            
            # Validar que sea positivo
            if decimal_value <= 0:
                result.add_error(f"El monto debe ser positivo: {decimal_value}")
            
            result.sanitized_value = decimal_value
            
        except InvalidOperation as e:
            result.add_error(f"No se puede convertir a monto válido: {value}")
        except Exception as e:
            result.add_error(f"Error validando monto: {str(e)}")
        
        return result
    
    def _sanitize_string_amount(self, value: str) -> str:
        """Limpia y sanitiza string de monto."""
        # Remover caracteres no numéricos excepto punto y coma
        sanitized = re.sub(r'[^\d.,\-]', '', value.strip())
        
        # Manejar formato con comas (ej: 1,500.25)
        if ',' in sanitized and '.' in sanitized:
            # Formato americano: 1,500.25
            sanitized = sanitized.replace(',', '')
        elif ',' in sanitized and '.' not in sanitized:
            # Podría ser formato europeo: 1.500,25 o americano: 1,500
            if sanitized.count(',') == 1:
                # Verificar si es decimal (últimos 2-3 dígitos)
                comma_pos = sanitized.rfind(',')
                after_comma = sanitized[comma_pos + 1:]
                if len(after_comma) <= 2:
                    # Probablemente decimal europeo
                    sanitized = sanitized.replace(',', '.')
                else:
                    # Probablemente separador de miles
                    sanitized = sanitized.replace(',', '')
        
        return sanitized


class CategoriaValidator:
    """Validador para categorías."""
    
    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        self.level = level
        self.config = get_config()
        self.logger = logger
    
    def validate(self, value: Any) -> ValidationResult:
        """
        Valida una categoría.
        
        Args:
            value: Valor a validar
            
        Returns:
            Resultado de validación
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        try:
            # Convertir a string
            if not isinstance(value, str):
                if value is None:
                    result.add_error("La categoría es requerida")
                    return result
                value = str(value)
            
            # Sanitizar
            sanitized = value.strip().lower()
            
            # Validar que no esté vacía
            if not sanitized:
                result.add_error("La categoría no puede estar vacía")
                return result
            
            # Validar longitud
            if len(sanitized) > 50:
                if self.level == ValidationLevel.STRICT:
                    result.add_error(f"Categoría muy larga (máximo 50 caracteres): {len(sanitized)}")
                else:
                    result.add_warning(f"Categoría truncada de {len(sanitized)} a 50 caracteres")
                    sanitized = sanitized[:50]
            
            # Validar caracteres
            if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\d_-]+$', value):
                if self.level == ValidationLevel.STRICT:
                    result.add_error(f"Categoría contiene caracteres no válidos: {value}")
                else:
                    result.add_warning("Categoría contiene caracteres especiales")
            
            # Sugerir categoría válida si no está en la lista
            valid_categories = [cat.lower() for cat in self.config.validation.custom_categories]
            if sanitized not in valid_categories and self.level != ValidationLevel.LENIENT:
                closest_match = self._find_closest_category(sanitized, valid_categories)
                if closest_match:
                    result.add_warning(f"¿Quisiste decir '{closest_match}'? Usando '{sanitized}'")
            
            result.sanitized_value = sanitized
            
        except Exception as e:
            result.add_error(f"Error validando categoría: {str(e)}")
        
        return result
    
    def _find_closest_category(self, input_category: str, valid_categories: List[str]) -> Optional[str]:
        """Encuentra la categoría más similar."""
        from difflib import get_close_matches
        
        matches = get_close_matches(input_category, valid_categories, n=1, cutoff=0.6)
        return matches[0] if matches else None


class FechaValidator:
    """Validador para fechas."""
    
    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        self.level = level
        self.config = get_config()
        self.logger = logger
    
    def validate(self, value: Any) -> ValidationResult:
        """
        Valida una fecha.
        
        Args:
            value: Valor a validar
            
        Returns:
            Resultado de validación
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        try:
            if isinstance(value, datetime):
                sanitized = value
            elif isinstance(value, date):
                sanitized = datetime.combine(value, datetime.min.time())
            elif isinstance(value, str):
                sanitized = self._parse_date_string(value)
                if not sanitized:
                    result.add_error(f"No se puede parsear la fecha: {value}")
                    return result
            else:
                result.add_error(f"Tipo de fecha no válido: {type(value)}")
                return result
            
            # Validar rango razonable
            now = datetime.now()
            min_date = datetime(1900, 1, 1)
            max_date = now + timedelta(days=1)  # Permitir hasta mañana
            
            if sanitized < min_date:
                result.add_error(f"Fecha muy antigua: {sanitized}")
            elif sanitized > max_date:
                result.add_error(f"Fecha en el futuro: {sanitized}")
            
            # Advertencia si es muy reciente o futura
            if sanitized > now:
                result.add_warning("Fecha en el futuro")
            elif (now - sanitized).days > 90:
                result.add_warning("Fecha de hace más de 90 días")
            
            result.sanitized_value = sanitized
            
        except Exception as e:
            result.add_error(f"Error validando fecha: {str(e)}")
        
        return result
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Parsea string de fecha en varios formatos."""
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d',
            '%m/%d/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None


class DescripcionValidator:
    """Validador para descripciones."""
    
    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        self.level = level
        self.logger = logger
    
    def validate(self, value: Any) -> ValidationResult:
        """
        Valida una descripción.
        
        Args:
            value: Valor a validar
            
        Returns:
            Resultado de validación
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        try:
            if value is None:
                result.sanitized_value = None
                return result
            
            # Convertir a string
            sanitized = str(value).strip()
            
            # Validar longitud
            if len(sanitized) > 500:
                if self.level == ValidationLevel.STRICT:
                    result.add_error(f"Descripción muy larga (máximo 500 caracteres): {len(sanitized)}")
                else:
                    result.add_warning(f"Descripción truncada de {len(sanitized)} a 500 caracteres")
                    sanitized = sanitized[:500]
            
            # Limpiar caracteres extraños
            if self.level != ValidationLevel.LENIENT:
                # Remover caracteres de control
                sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
                
                # Normalizar espacios
                sanitized = re.sub(r'\s+', ' ', sanitized).strip()
            
            result.sanitized_value = sanitized if sanitized else None
            
        except Exception as e:
            result.add_error(f"Error validando descripción: {str(e)}")
        
        return result


class GastoValidator:
    """Validador completo para gastos."""
    
    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        self.level = level
        self.monto_validator = MontoValidator(level)
        self.categoria_validator = CategoriaValidator(level)
        self.fecha_validator = FechaValidator(level)
        self.descripcion_validator = DescripcionValidator(level)
        self.logger = logger
    
    def validate(self, gasto_data: Dict[str, Any]) -> ValidationResult:
        """
        Valida datos completos de un gasto.
        
        Args:
            gasto_data: Diccionario con datos del gasto
            
        Returns:
            Resultado de validación
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        sanitized_data = {}
        
        try:
            # Validar campos requeridos
            config = get_config()
            required_fields = config.validation.required_fields
            
            for field in required_fields:
                if field not in gasto_data or gasto_data[field] is None:
                    result.add_error(f"Campo requerido faltante: {field}")
            
            if result.has_errors:
                return result
            
            # Validar monto
            if 'monto' in gasto_data:
                monto_result = self.monto_validator.validate(gasto_data['monto'])
                result.errors.extend(monto_result.errors)
                result.warnings.extend(monto_result.warnings)
                if monto_result.sanitized_value is not None:
                    sanitized_data['monto'] = monto_result.sanitized_value
            
            # Validar categoría
            if 'categoria' in gasto_data:
                categoria_result = self.categoria_validator.validate(gasto_data['categoria'])
                result.errors.extend(categoria_result.errors)
                result.warnings.extend(categoria_result.warnings)
                if categoria_result.sanitized_value is not None:
                    sanitized_data['categoria'] = categoria_result.sanitized_value
            
            # Validar fecha
            if 'fecha' in gasto_data:
                fecha_result = self.fecha_validator.validate(gasto_data['fecha'])
                result.errors.extend(fecha_result.errors)
                result.warnings.extend(fecha_result.warnings)
                if fecha_result.sanitized_value is not None:
                    sanitized_data['fecha'] = fecha_result.sanitized_value
            else:
                # Usar fecha actual si no se proporciona
                sanitized_data['fecha'] = datetime.now()
            
            # Validar descripción
            if 'descripcion' in gasto_data:
                desc_result = self.descripcion_validator.validate(gasto_data['descripcion'])
                result.errors.extend(desc_result.errors)
                result.warnings.extend(desc_result.warnings)
                sanitized_data['descripcion'] = desc_result.sanitized_value
            
            # Determinar validez final
            result.is_valid = not result.has_errors
            result.sanitized_value = sanitized_data
            
        except Exception as e:
            result.add_error(f"Error en validación completa: {str(e)}")
        
        return result


class ConfigValidator:
    """Validador para archivos de configuración."""
    
    def __init__(self):
        self.logger = logger
    
    def validate_config_file(self, config_path: str) -> ValidationResult:
        """
        Valida un archivo de configuración.
        
        Args:
            config_path: Ruta al archivo de configuración
            
        Returns:
            Resultado de validación
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        try:
            import yaml
            from pathlib import Path
            
            config_file = Path(config_path)
            
            # Verificar que el archivo existe
            if not config_file.exists():
                result.add_error(f"Archivo de configuración no encontrado: {config_path}")
                return result
            
            # Intentar cargar YAML
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                result.add_error(f"Error parseando YAML: {e}")
                return result
            
            # Validar estructura
            required_sections = ['whatsapp', 'storage', 'logging']
            for section in required_sections:
                if section not in config_data:
                    result.add_error(f"Sección requerida faltante: {section}")
            
            # Validar secciones específicas
            if 'whatsapp' in config_data:
                self._validate_whatsapp_config(config_data['whatsapp'], result)
            
            if 'storage' in config_data:
                self._validate_storage_config(config_data['storage'], result)
            
            if 'logging' in config_data:
                self._validate_logging_config(config_data['logging'], result)
            
            result.is_valid = not result.has_errors
            
        except Exception as e:
            result.add_error(f"Error validando archivo de configuración: {str(e)}")
        
        return result
    
    def _validate_whatsapp_config(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """Valida configuración de WhatsApp."""
        if 'target_chat_name' not in config or not config['target_chat_name'].strip():
            result.add_error("whatsapp.target_chat_name es requerido")
        
        if 'connection_timeout_seconds' in config:
            timeout = config['connection_timeout_seconds']
            if not isinstance(timeout, int) or timeout <= 0:
                result.add_error("whatsapp.connection_timeout_seconds debe ser un entero positivo")
    
    def _validate_storage_config(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """Valida configuración de storage."""
        if 'primary_storage' in config:
            storage_type = config['primary_storage']
            if storage_type not in ['excel', 'sqlite']:
                result.add_error(f"storage.primary_storage no válido: {storage_type}")
    
    def _validate_logging_config(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """Valida configuración de logging."""
        if 'level' in config:
            level = config['level']
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if level not in valid_levels:
                result.add_error(f"logging.level no válido: {level}")


# Instancias globales de validadores
monto_validator = MontoValidator()
categoria_validator = CategoriaValidator()
fecha_validator = FechaValidator()
descripcion_validator = DescripcionValidator()
gasto_validator = GastoValidator()
config_validator = ConfigValidator()


def validate_gasto(gasto_data: Dict[str, Any], level: ValidationLevel = ValidationLevel.NORMAL) -> ValidationResult:
    """
    Función de conveniencia para validar un gasto.
    
    Args:
        gasto_data: Datos del gasto
        level: Nivel de validación
        
    Returns:
        Resultado de validación
    """
    validator = GastoValidator(level)
    return validator.validate(gasto_data)
