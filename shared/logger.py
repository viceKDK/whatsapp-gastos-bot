"""
Sistema de Logging Avanzado con Rotación

Configuración y gestión de logging avanzado para toda la aplicación con rotación,
filtros, contexto y métricas integradas.
"""

import logging
import logging.handlers
import json
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from functools import wraps
from contextvars import ContextVar

try:
    from config.config_manager import get_config
except ImportError:
    # Fallback si no existe config_manager
    from config.settings import get_settings, LogLevel


class ColoredFormatter(logging.Formatter):
    """Formatter que agrega colores a los logs de consola."""
    
    # Códigos ANSI para colores
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Verde
        'WARNING': '\033[33m',   # Amarillo
        'ERROR': '\033[31m',     # Rojo
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Aplicar color al nombre del level
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


# Context variables para tracking
request_id: ContextVar[str] = ContextVar('request_id', default='')
user_context: ContextVar[Dict[str, Any]] = ContextVar('user_context', default={})


class ContextFilter(logging.Filter):
    """Filtro que agrega información de contexto a los logs."""
    
    def filter(self, record):
        # Agregar request ID
        record.request_id = request_id.get('')
        
        # Agregar información de contexto de usuario
        context = user_context.get({})
        record.user_id = context.get('user_id', '')
        record.chat_name = context.get('chat_name', '')
        
        # Agregar thread info
        record.thread_name = threading.current_thread().name
        
        return True


class JSONFormatter(logging.Formatter):
    """Formatter que genera logs en formato JSON."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': getattr(record, 'thread_name', ''),
            'request_id': getattr(record, 'request_id', ''),
            'user_id': getattr(record, 'user_id', ''),
            'chat_name': getattr(record, 'chat_name', ''),
        }
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Agregar campos extra si existen
        for key, value in record.__dict__.items():
            if key not in log_entry and not key.startswith('_'):
                if isinstance(value, (str, int, float, bool, list, dict)):
                    log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


class PerformanceFilter(logging.Filter):
    """Filtro que captura métricas de performance."""
    
    def __init__(self):
        super().__init__()
        self.start_times = {}
        self.performance_stats = {
            'operations': {},
            'slow_operations': [],
            'error_count': 0
        }
    
    def filter(self, record):
        # Capturar errores
        if record.levelno >= logging.ERROR:
            self.performance_stats['error_count'] += 1
        
        # Capturar métricas de performance si están marcadas
        if hasattr(record, 'performance_data'):
            perf_data = record.performance_data
            operation = perf_data.get('operation', 'unknown')
            duration = perf_data.get('duration', 0)
            
            # Actualizar estadísticas
            if operation not in self.performance_stats['operations']:
                self.performance_stats['operations'][operation] = {
                    'count': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'max_time': 0
                }
            
            stats = self.performance_stats['operations'][operation]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['max_time'] = max(stats['max_time'], duration)
            
            # Marcar operaciones lentas
            if duration > 5.0:  # 5 segundos threshold
                self.performance_stats['slow_operations'].append({
                    'operation': operation,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                })
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de performance."""
        return self.performance_stats.copy()


class BotLogger:
    """Gestor centralizado de logging."""
    
    _instance: Optional['BotLogger'] = None
    _configured: bool = False
    
    def __new__(cls) -> 'BotLogger':
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa el logger si no está configurado."""
        if not self._configured:
            self.setup_logging()
            self._configured = True
    
    def setup_logging(self) -> None:
        """Configura el sistema de logging avanzado."""
        try:
            # Obtener configuración
            try:
                config = get_config()
                logging_config = config.logging
            except:
                # Fallback para configuración legacy
                settings = get_settings()
                logging_config = settings.logging
            
            # Configurar logger raíz
            root_logger = logging.getLogger()
            root_logger.setLevel(self._get_log_level_from_string(logging_config.level))
            
            # Limpiar handlers existentes
            root_logger.handlers.clear()
            
            # Crear filtros globales
            context_filter = ContextFilter()
            self.performance_filter = PerformanceFilter()
            
            # Configurar handler de archivo principal
            if hasattr(logging_config, 'file_path') and logging_config.file_path:
                self._setup_rotating_file_handler(logging_config, context_filter, self.performance_filter)
            
            # Configurar handler de archivo JSON (para análisis)
            if hasattr(logging_config, 'file_path'):
                json_file = str(Path(logging_config.file_path).with_suffix('.json'))
                self._setup_json_file_handler(json_file, logging_config, context_filter)
            
            # Configurar handler de consola
            if getattr(logging_config, 'console_enabled', True):
                self._setup_enhanced_console_handler(logging_config, context_filter)
            
            # Configurar handler de errores críticos
            self._setup_error_handler(logging_config)
            
            # Configurar loggers de terceros (reducir verbosidad)
            self._configure_third_party_loggers()
            
            # Programar limpieza de logs antiguos
            self._schedule_log_cleanup(logging_config)
            
            # Log inicial
            logger = logging.getLogger(__name__)
            logger.info("Sistema de logging avanzado configurado")
            logger.debug(f"Configuración: Level={logging_config.level}, "
                        f"File={getattr(logging_config, 'file_path', 'N/A')}, "
                        f"Console={getattr(logging_config, 'console_enabled', True)}")
            
        except Exception as e:
            # Fallback a configuración básica
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            logging.getLogger(__name__).error(f"Error configurando logging avanzado: {e}")
    
    def _setup_rotating_file_handler(self, logging_config, context_filter, performance_filter) -> None:
        """Configura el handler de archivo con rotación avanzada."""
        try:
            # Asegurar que el directorio existe
            log_file = Path(logging_config.file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Crear rotating file handler con configuración avanzada
            file_handler = logging.handlers.RotatingFileHandler(
                filename=logging_config.file_path,
                maxBytes=getattr(logging_config, 'max_file_size_mb', 10) * 1024 * 1024,
                backupCount=getattr(logging_config, 'backup_count', 5),
                encoding='utf-8'
            )
            
            # Configurar formatter con más información
            file_formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(thread_name)s - %(request_id)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            
            # Agregar filtros
            file_handler.addFilter(context_filter)
            file_handler.addFilter(performance_filter)
            
            # Agregar al logger raíz
            logging.getLogger().addHandler(file_handler)
            
        except Exception as e:
            print(f"Error configurando rotating file handler: {e}")
    
    def _setup_json_file_handler(self, json_file, logging_config, context_filter) -> None:
        """Configura handler para logs en formato JSON."""
        try:
            log_file = Path(json_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Crear handler con rotación diaria
            json_handler = logging.handlers.TimedRotatingFileHandler(
                filename=json_file,
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8'
            )
            
            # Usar formatter JSON
            json_handler.setFormatter(JSONFormatter())
            json_handler.addFilter(context_filter)
            
            # Solo logs de INFO y superior para JSON
            json_handler.setLevel(logging.INFO)
            
            logging.getLogger().addHandler(json_handler)
            
        except Exception as e:
            print(f"Error configurando JSON file handler: {e}")
    
    def _setup_enhanced_console_handler(self, logging_config, context_filter) -> None:
        """Configura handler de consola mejorado."""
        try:
            console_handler = logging.StreamHandler()
            
            # Formatter con colores y contexto
            console_formatter = ColoredFormatter(
                fmt='%(asctime)s - %(name)-20s - %(levelname)-8s - %(request_id)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            
            console_handler.setFormatter(console_formatter)
            console_handler.addFilter(context_filter)
            
            # Nivel diferente para consola (menos verbose)
            console_level = getattr(logging_config, 'console_level', logging_config.level)
            # Convertir cualquier tipo a int de logging
            console_level = self._get_log_level_from_string(console_level)
            console_handler.setLevel(console_level)
            
            logging.getLogger().addHandler(console_handler)
            
        except Exception as e:
            print(f"Error configurando enhanced console handler: {e}")
    
    def _setup_error_handler(self, logging_config) -> None:
        """Configura handler especial para errores críticos."""
        try:
            if not hasattr(logging_config, 'file_path'):
                return
                
            error_file = str(Path(logging_config.file_path).parent / 'errors.log')
            
            error_handler = logging.handlers.RotatingFileHandler(
                filename=error_file,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
                encoding='utf-8'
            )
            
            # Solo errores y críticos
            error_handler.setLevel(logging.ERROR)
            
            # Formatter detallado para errores
            error_formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s\n%(exc_text)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            error_handler.setFormatter(error_formatter)
            
            logging.getLogger().addHandler(error_handler)
            
        except Exception as e:
            print(f"Error configurando error handler: {e}")
    
    def _schedule_log_cleanup(self, logging_config) -> None:
        """Programa limpieza automática de logs antiguos."""
        try:
            if not hasattr(logging_config, 'file_path'):
                return
                
            def cleanup_old_logs():
                """Limpia logs antiguos."""
                try:
                    log_dir = Path(logging_config.file_path).parent
                    max_age_days = getattr(logging_config, 'max_log_age_days', 30)
                    cutoff_date = datetime.now() - timedelta(days=max_age_days)
                    
                    for log_file in log_dir.glob('*.log*'):
                        if log_file.stat().st_mtime < cutoff_date.timestamp():
                            log_file.unlink()
                            print(f"Eliminado log antiguo: {log_file}")
                
                except Exception as e:
                    print(f"Error en limpieza de logs: {e}")
            
            # Ejecutar limpieza en thread separado cada 24 horas
            def schedule_cleanup():
                while True:
                    time.sleep(24 * 60 * 60)  # 24 horas
                    cleanup_old_logs()
            
            cleanup_thread = threading.Thread(target=schedule_cleanup, daemon=True)
            cleanup_thread.start()
            
        except Exception as e:
            print(f"Error programando limpieza de logs: {e}")
    
    def _get_log_level_from_string(self, level_input) -> int:
        """Convierte string, LogLevel enum, o int a nivel de logging."""
        try:
            # Si ya es un entero de logging, devolverlo
            if isinstance(level_input, int):
                return level_input
            
            # Si es un enum LogLevel, obtener su valor string
            if hasattr(level_input, 'value'):
                level_str = level_input.value
            else:
                # Convertir a string si no lo es ya
                level_str = str(level_input)
            
            level_mapping = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARNING': logging.WARNING,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL
            }
            return level_mapping.get(level_str.upper(), logging.INFO)
            
        except Exception as e:
            print(f"Error convirtiendo log level {level_input}: {e}")
            return logging.INFO
    
    def _setup_file_handler(self, settings) -> None:
        """Configura el handler de archivo con rotación."""
        try:
            # Asegurar que el directorio existe
            log_file = Path(settings.logging.file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Crear rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=settings.logging.file_path,
                maxBytes=settings.logging.max_file_size_mb * 1024 * 1024,  # MB a bytes
                backupCount=settings.logging.backup_count,
                encoding='utf-8'
            )
            
            # Configurar formatter
            file_formatter = logging.Formatter(
                fmt=settings.logging.format_string,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            
            # Agregar al logger raíz
            logging.getLogger().addHandler(file_handler)
            
        except Exception as e:
            print(f"Error configurando file handler: {e}")
    
    def _setup_console_handler(self, settings) -> None:
        """Configura el handler de consola."""
        try:
            console_handler = logging.StreamHandler()
            
            # Usar formatter con colores si está en modo debug
            if settings.debug_mode:
                console_formatter = ColoredFormatter(
                    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S'
                )
            else:
                console_formatter = logging.Formatter(
                    fmt='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S'
                )
            
            console_handler.setFormatter(console_formatter)
            
            # Agregar al logger raíz
            logging.getLogger().addHandler(console_handler)
            
        except Exception as e:
            print(f"Error configurando console handler: {e}")
    
    def _configure_third_party_loggers(self) -> None:
        """Configura loggers de bibliotecas terceras para reducir ruido."""
        third_party_loggers = [
            'selenium',
            'selenium.webdriver',
            'urllib3',
            'openpyxl'
        ]
        
        for logger_name in third_party_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    @staticmethod
    def _get_log_level(log_level: LogLevel) -> int:
        """Convierte LogLevel enum a nivel de logging."""
        level_mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR
        }
        
        return level_mapping.get(log_level, logging.INFO)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Obtiene un logger configurado.
        
        Args:
            name: Nombre del logger (normalmente __name__)
            
        Returns:
            Logger configurado
        """
        return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """
    Función de conveniencia para obtener un logger configurado.
    
    Args:
        name: Nombre del logger (normalmente __name__)
        
    Returns:
        Logger configurado
    """
    bot_logger = BotLogger()
    return bot_logger.get_logger(name)


def log_exception(logger: logging.Logger, exc: Exception, context: str = "") -> None:
    """
    Utilidad para loggear excepciones de manera consistente.
    
    Args:
        logger: Logger a usar
        exc: Excepción a loggear
        context: Contexto adicional sobre dónde ocurrió
    """
    context_msg = f" en {context}" if context else ""
    logger.exception(f"Excepción{context_msg}: {type(exc).__name__}: {str(exc)}")


def log_function_entry(logger: logging.Logger, func_name: str, **kwargs) -> None:
    """
    Utilidad para loggear entrada a funciones en modo debug.
    
    Args:
        logger: Logger a usar
        func_name: Nombre de la función
        **kwargs: Argumentos de la función a loggear
    """
    if logger.isEnabledFor(logging.DEBUG):
        args_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        logger.debug(f"Entrando a {func_name}({args_str})")


def log_performance(logger: logging.Logger, operation: str, duration_seconds: float, **metadata) -> None:
    """
    Utilidad para loggear métricas de performance con metadata.
    
    Args:
        logger: Logger a usar
        operation: Descripción de la operación
        duration_seconds: Duración en segundos
        **metadata: Metadata adicional
    """
    # Crear record con datos de performance
    performance_data = {
        'operation': operation,
        'duration': duration_seconds,
        **metadata
    }
    
    if duration_seconds > 1.0:
        logger.warning(f"Operación lenta detectada: {operation} tomó {duration_seconds:.2f}s", 
                      extra={'performance_data': performance_data})
    else:
        logger.debug(f"Performance: {operation} tomó {duration_seconds:.3f}s",
                    extra={'performance_data': performance_data})


def set_request_context(request_id: str = None, user_id: str = None, chat_name: str = None) -> None:
    """
    Establece contexto para el request actual.
    
    Args:
        request_id: ID único del request
        user_id: ID del usuario
        chat_name: Nombre del chat
    """
    if request_id:
        request_id.set(request_id)
    
    if user_id or chat_name:
        context = user_context.get({})
        if user_id:
            context['user_id'] = user_id
        if chat_name:
            context['chat_name'] = chat_name
        user_context.set(context)


def clear_request_context() -> None:
    """Limpia el contexto del request actual."""
    request_id.set('')
    user_context.set({})


def with_performance_logging(operation_name: str = None):
    """
    Decorador para loggear automáticamente performance de funciones.
    
    Args:
        operation_name: Nombre de la operación (usa nombre de función si no se proporciona)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_performance(logger, op_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_performance(logger, f"{op_name}[ERROR]", duration, error=str(e))
                raise
        
        return wrapper
    return decorator


def with_error_logging(logger: logging.Logger = None, reraise: bool = True):
    """
    Decorador para loggear automáticamente errores de funciones.
    
    Args:
        logger: Logger a usar (crea uno si no se proporciona)
        reraise: Si re-lanzar la excepción después de loggearla
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logger or get_logger(func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_exception(func_logger, e, f"{func.__module__}.{func.__name__}")
                if reraise:
                    raise
                return None
        
        return wrapper
    return decorator


class LoggerAdapter(logging.LoggerAdapter):
    """Adapter que agrega contexto automáticamente a todos los logs."""
    
    def process(self, msg, kwargs):
        # Agregar contexto automáticamente
        extra = kwargs.get('extra', {})
        
        # Agregar información de contexto actual
        extra.update({
            'request_id': request_id.get(''),
            'user_context': user_context.get({})
        })
        
        kwargs['extra'] = extra
        return msg, kwargs


def get_contextual_logger(name: str, **default_context) -> LoggerAdapter:
    """
    Obtiene un logger que incluye contexto automáticamente.
    
    Args:
        name: Nombre del logger
        **default_context: Contexto por defecto para este logger
        
    Returns:
        LoggerAdapter con contexto
    """
    base_logger = get_logger(name)
    return LoggerAdapter(base_logger, default_context)


def log_structured(logger: logging.Logger, level: int, message: str, **structured_data) -> None:
    """
    Logea un mensaje con datos estructurados.
    
    Args:
        logger: Logger a usar
        level: Nivel de logging
        message: Mensaje principal
        **structured_data: Datos estructurados adicionales
    """
    logger.log(level, message, extra={'structured_data': structured_data})


def get_performance_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas de performance del sistema de logging.
    
    Returns:
        Diccionario con estadísticas
    """
    try:
        bot_logger = BotLogger()
        if hasattr(bot_logger, 'performance_filter'):
            return bot_logger.performance_filter.get_stats()
        return {}
    except Exception as e:
        return {'error': str(e)}