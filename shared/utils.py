"""
Utilidades Compartidas

Funciones auxiliares reutilizables en toda la aplicación.
"""

import re
import os
import sys
import time
import functools
from pathlib import Path
from typing import Any, Callable, Optional, Union, Dict
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from shared.logger import get_logger


logger = get_logger(__name__)


def ensure_decimal(value: Union[str, int, float, Decimal]) -> Decimal:
    """
    Convierte un valor a Decimal de manera segura.
    
    Args:
        value: Valor a convertir
        
    Returns:
        Decimal representation del valor
        
    Raises:
        ValueError: Si el valor no se puede convertir
    """
    try:
        if isinstance(value, Decimal):
            return value
        
        # Convertir a string primero para evitar problemas de precisión con float
        return Decimal(str(value))
        
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(f"No se puede convertir '{value}' a Decimal: {e}")


def normalize_text(text: str) -> str:
    """
    Normaliza texto removiendo espacios extra y caracteres especiales.
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto normalizado
    """
    if not text:
        return ""
    
    # Remover espacios extra
    normalized = re.sub(r'\s+', ' ', text.strip())
    
    # Convertir a minúsculas
    normalized = normalized.lower()
    
    return normalized


def is_valid_file_path(path: Union[str, Path]) -> bool:
    """
    Verifica si una ruta de archivo es válida.
    
    Args:
        path: Ruta a verificar
        
    Returns:
        True si la ruta es válida
    """
    try:
        path_obj = Path(path)
        
        # Verificar que el directorio padre existe o se puede crear
        parent = path_obj.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError):
                return False
        
        return True
        
    except (ValueError, OSError):
        return False


def ensure_directory_exists(directory: Union[str, Path]) -> bool:
    """
    Asegura que un directorio existe, creándolo si es necesario.
    
    Args:
        directory: Directorio a asegurar
        
    Returns:
        True si el directorio existe o se pudo crear
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError) as e:
        logger.error(f"No se pudo crear directorio {directory}: {e}")
        return False


def format_currency(amount: Union[Decimal, float, int], currency_symbol: str = "$") -> str:
    """
    Formatea un monto como moneda.
    
    Args:
        amount: Monto a formatear
        currency_symbol: Símbolo de moneda
        
    Returns:
        String formateado como moneda
    """
    try:
        decimal_amount = ensure_decimal(amount)
        return f"{currency_symbol}{decimal_amount:,.2f}"
    except ValueError:
        return f"{currency_symbol}0.00"


def parse_date_flexible(date_str: str) -> Optional[datetime]:
    """
    Parsea fechas en múltiples formatos.
    
    Args:
        date_str: String de fecha
        
    Returns:
        Datetime object o None si no se puede parsear
    """
    if not date_str or not date_str.strip():
        return None
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    logger.warning(f"No se pudo parsear fecha: {date_str}")
    return None


def retry_operation(max_attempts: int = 3, delay_seconds: float = 1.0):
    """
    Decorador para reintentar operaciones fallidas.
    
    Args:
        max_attempts: Número máximo de intentos
        delay_seconds: Segundos entre intentos
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        logger.warning(f"Intento {attempt + 1} falló en {func.__name__}: {e}")
                        time.sleep(delay_seconds * (attempt + 1))  # Backoff exponencial
                    else:
                        logger.error(f"Todos los intentos fallaron en {func.__name__}")
            
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def timing_decorator(func: Callable) -> Callable:
    """
    Decorador para medir tiempo de ejecución de funciones.
    
    Args:
        func: Función a medir
        
    Returns:
        Función decorada que loggea el tiempo de ejecución
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            
            if execution_time > 1.0:
                logger.warning(f"{func.__name__} tomó {execution_time:.2f}s (operación lenta)")
            else:
                logger.debug(f"{func.__name__} ejecutado en {execution_time:.3f}s")
    
    return wrapper


def validate_environment() -> Dict[str, bool]:
    """
    Valida el entorno de ejecución.
    
    Returns:
        Diccionario con resultados de validación
    """
    results = {}
    
    # Verificar versión de Python
    results['python_version'] = sys.version_info >= (3, 9)
    
    # Verificar que estamos en directorio correcto
    main_py_exists = Path('main.py').exists()
    config_dir_exists = Path('config').exists()
    results['correct_directory'] = main_py_exists and config_dir_exists
    
    # Verificar permisos de escritura en directorios importantes
    results['data_writable'] = _check_directory_writable('data')
    results['logs_writable'] = _check_directory_writable('logs')
    
    # Verificar dependencias críticas
    results['selenium_available'] = _check_import('selenium')
    results['openpyxl_available'] = _check_import('openpyxl')
    
    return results


def _check_directory_writable(directory: str) -> bool:
    """Verifica si un directorio es escribible."""
    try:
        ensure_directory_exists(directory)
        test_file = Path(directory) / '.test_write'
        
        # Intentar escribir archivo de prueba
        test_file.write_text('test')
        test_file.unlink()  # Eliminar archivo de prueba
        
        return True
    except (OSError, PermissionError):
        return False


def _check_import(module_name: str) -> bool:
    """Verifica si un módulo se puede importar."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def get_project_root() -> Path:
    """
    Obtiene la ruta raíz del proyecto.
    
    Returns:
        Path object con la ruta raíz
    """
    # Buscar main.py desde el directorio actual hacia arriba
    current = Path.cwd()
    
    while current != current.parent:
        if (current / 'main.py').exists():
            return current
        current = current.parent
    
    # Si no encontramos main.py, usar directorio actual
    return Path.cwd()


def safe_cast(value: Any, target_type: type, default: Any = None) -> Any:
    """
    Convierte un valor a un tipo de manera segura.
    
    Args:
        value: Valor a convertir
        target_type: Tipo objetivo
        default: Valor por defecto si falla la conversión
        
    Returns:
        Valor convertido o default si falla
    """
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default


def clean_filename(filename: str, max_length: int = 255) -> str:
    """
    Limpia un nombre de archivo para que sea válido en el sistema.
    
    Args:
        filename: Nombre de archivo original
        max_length: Longitud máxima permitida
        
    Returns:
        Nombre de archivo limpio
    """
    # Caracteres no permitidos en nombres de archivo
    invalid_chars = '<>:"/\\|?*'
    
    cleaned = filename
    for char in invalid_chars:
        cleaned = cleaned.replace(char, '_')
    
    # Remover espacios al inicio y final
    cleaned = cleaned.strip()
    
    # Truncar si es muy largo
    if len(cleaned) > max_length:
        name, ext = os.path.splitext(cleaned)
        available_length = max_length - len(ext)
        cleaned = name[:available_length] + ext
    
    return cleaned or 'unnamed_file'


def get_system_info() -> Dict[str, Any]:
    """
    Obtiene información del sistema para debugging.
    
    Returns:
        Diccionario con información del sistema
    """
    return {
        'python_version': sys.version,
        'platform': sys.platform,
        'executable': sys.executable,
        'path': sys.path[:3],  # Primeras 3 rutas del path
        'cwd': str(Path.cwd()),
        'project_root': str(get_project_root()),
        'user': os.getenv('USER', os.getenv('USERNAME', 'unknown'))
    }