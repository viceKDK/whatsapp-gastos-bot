"""
Configuración Global del Sistema

Gestiona todos los parámetros configurables del bot.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Set, Optional
from enum import Enum


class StorageMode(Enum):
    """Modos de almacenamiento disponibles."""
    EXCEL = "excel"
    SQLITE = "sqlite"


class LogLevel(Enum):
    """Niveles de logging."""
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class DatabaseConfig:
    """Configuración de base de datos."""
    sqlite_file_path: str = "data/gastos.db"
    backup_enabled: bool = True
    backup_frequency_hours: int = 24


@dataclass
class ExcelConfig:
    """Configuración de Excel."""
    excel_file_path: str = "data/gastos.xlsx"
    auto_backup: bool = True
    max_backups: int = 5


@dataclass
class WhatsAppConfig:
    """Configuración de WhatsApp."""
    poll_interval_seconds: int = 1
    connection_timeout_seconds: int = 5
    target_chat_name: str = "Gastos"
    chrome_headless: bool = False
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 1

    # Configuración de respuestas automáticas
    auto_responses_enabled: bool = True
    response_delay_seconds: float = 0.3
    typing_delay_seconds: float = 0.03
    send_confirmations: bool = True
    send_error_notifications: bool = True
    send_suggestions: bool = True


@dataclass
class LoggingConfig:
    """Configuración de logging."""
    level: LogLevel = LogLevel.INFO
    file_path: str = "logs/bot.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    console_output: bool = True
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class CategoriaConfig:
    """Configuración de categorías."""
    categorias_validas: Set[str] = field(default_factory=lambda: {
        'comida', 'transporte', 'entretenimiento', 'salud', 'servicios',
        'ropa', 'educacion', 'hogar', 'trabajo', 'otros', 'super', 'nafta'
    })
    permitir_categorias_nuevas: bool = True
    validacion_estricta: bool = False


@dataclass
class Settings:
    """Configuración principal del sistema."""
    
    # Modo de almacenamiento
    storage_mode: StorageMode = StorageMode.EXCEL
    
    # Configuraciones por componente
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    excel: ExcelConfig = field(default_factory=ExcelConfig)
    whatsapp: WhatsAppConfig = field(default_factory=WhatsAppConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    categorias: CategoriaConfig = field(default_factory=CategoriaConfig)
    
    # Configuración general
    project_root: str = field(default_factory=lambda: str(Path(__file__).parent.parent))
    debug_mode: bool = False
    
    @classmethod
    def load_from_env(cls) -> 'Settings':
        """
        Carga configuración desde variables de entorno.
        
        Returns:
            Instancia de Settings con valores de entorno
        """
        settings = cls()
        
        # Storage mode
        storage_mode_str = os.getenv('STORAGE_MODE', 'excel').lower()
        if storage_mode_str in [mode.value for mode in StorageMode]:
            settings.storage_mode = StorageMode(storage_mode_str)
        
        # Database config
        settings.database.sqlite_file_path = os.getenv('SQLITE_FILE_PATH', settings.database.sqlite_file_path)
        settings.database.backup_enabled = os.getenv('DB_BACKUP_ENABLED', 'true').lower() == 'true'
        
        # Excel config  
        settings.excel.excel_file_path = os.getenv('EXCEL_FILE_PATH', settings.excel.excel_file_path)
        settings.excel.auto_backup = os.getenv('EXCEL_AUTO_BACKUP', 'true').lower() == 'true'
        
        # WhatsApp config
        settings.whatsapp.poll_interval_seconds = int(os.getenv('WHATSAPP_POLL_INTERVAL', '30'))
        settings.whatsapp.connection_timeout_seconds = int(os.getenv('WHATSAPP_TIMEOUT', '10'))
        settings.whatsapp.target_chat_name = os.getenv('TARGET_CHAT_NAME', settings.whatsapp.target_chat_name)
        settings.whatsapp.chrome_headless = os.getenv('CHROME_HEADLESS', 'false').lower() == 'true'
        
        # WhatsApp responses config
        settings.whatsapp.auto_responses_enabled = os.getenv('AUTO_RESPONSES_ENABLED', 'true').lower() == 'true'
        settings.whatsapp.response_delay_seconds = float(os.getenv('RESPONSE_DELAY_SECONDS', '2.0'))
        settings.whatsapp.send_confirmations = os.getenv('SEND_CONFIRMATIONS', 'true').lower() == 'true'
        settings.whatsapp.send_error_notifications = os.getenv('SEND_ERROR_NOTIFICATIONS', 'true').lower() == 'true'
        settings.whatsapp.send_suggestions = os.getenv('SEND_SUGGESTIONS', 'true').lower() == 'true'
        
        # Logging config
        log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        if hasattr(LogLevel, log_level_str):
            settings.logging.level = LogLevel[log_level_str]
        
        settings.logging.file_path = os.getenv('LOG_FILE_PATH', settings.logging.file_path)
        settings.logging.console_output = os.getenv('LOG_CONSOLE', 'true').lower() == 'true'
        
        # Categories config
        categorias_env = os.getenv('VALID_CATEGORIES', '')
        if categorias_env:
            categorias_list = [cat.strip().lower() for cat in categorias_env.split(',') if cat.strip()]
            if categorias_list:
                settings.categorias.categorias_validas = set(categorias_list)
        
        settings.categorias.permitir_categorias_nuevas = os.getenv('ALLOW_NEW_CATEGORIES', 'true').lower() == 'true'
        settings.categorias.validacion_estricta = os.getenv('STRICT_CATEGORY_VALIDATION', 'false').lower() == 'true'
        
        # General config
        settings.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        
        return settings
    
    def get_storage_file_path(self) -> str:
        """
        Obtiene la ruta del archivo de almacenamiento según el modo configurado.
        
        Returns:
            Ruta del archivo de almacenamiento
        """
        if self.storage_mode == StorageMode.EXCEL:
            return self.excel.excel_file_path
        else:
            return self.database.sqlite_file_path
    
    def ensure_directories_exist(self) -> None:
        """Crea los directorios necesarios si no existen."""
        directories = [
            Path(self.logging.file_path).parent,
            Path(self.get_storage_file_path()).parent,
            Path(self.project_root) / "logs",
            Path(self.project_root) / "data"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_configuration(self) -> list[str]:
        """
        Valida la configuración y retorna lista de errores.
        
        Returns:
            Lista de mensajes de error (vacía si no hay errores)
        """
        errors = []
        
        # Validar intervalos
        if self.whatsapp.poll_interval_seconds < 1:
            errors.append("El intervalo de polling no puede ser menor a 1 segundo")

        if self.whatsapp.connection_timeout_seconds < 3:
            errors.append("El timeout de conexión no puede ser menor a 3 segundos")
        
        # Validar paths
        try:
            Path(self.get_storage_file_path()).parent
        except Exception as e:
            errors.append(f"Ruta de almacenamiento inválida: {e}")
        
        try:
            Path(self.logging.file_path).parent
        except Exception as e:
            errors.append(f"Ruta de logging inválida: {e}")
        
        # Validar categorías
        if not self.categorias.categorias_validas:
            errors.append("Debe haber al menos una categoría válida")
        
        return errors
    
    def to_dict(self) -> dict:
        """
        Convierte la configuración a diccionario.
        
        Returns:
            Diccionario con toda la configuración
        """
        return {
            'storage_mode': self.storage_mode.value,
            'database': {
                'sqlite_file_path': self.database.sqlite_file_path,
                'backup_enabled': self.database.backup_enabled,
                'backup_frequency_hours': self.database.backup_frequency_hours
            },
            'excel': {
                'excel_file_path': self.excel.excel_file_path,
                'auto_backup': self.excel.auto_backup,
                'max_backups': self.excel.max_backups
            },
            'whatsapp': {
                'poll_interval_seconds': self.whatsapp.poll_interval_seconds,
                'connection_timeout_seconds': self.whatsapp.connection_timeout_seconds,
                'target_chat_name': self.whatsapp.target_chat_name,
                'chrome_headless': self.whatsapp.chrome_headless,
                'max_retry_attempts': self.whatsapp.max_retry_attempts,
                'retry_delay_seconds': self.whatsapp.retry_delay_seconds,
                'auto_responses_enabled': self.whatsapp.auto_responses_enabled,
                'response_delay_seconds': self.whatsapp.response_delay_seconds,
                'typing_delay_seconds': self.whatsapp.typing_delay_seconds,
                'send_confirmations': self.whatsapp.send_confirmations,
                'send_error_notifications': self.whatsapp.send_error_notifications,
                'send_suggestions': self.whatsapp.send_suggestions
            },
            'logging': {
                'level': self.logging.level.value,
                'file_path': self.logging.file_path,
                'max_file_size_mb': self.logging.max_file_size_mb,
                'backup_count': self.logging.backup_count,
                'console_output': self.logging.console_output,
                'format_string': self.logging.format_string
            },
            'categorias': {
                'categorias_validas': list(self.categorias.categorias_validas),
                'permitir_categorias_nuevas': self.categorias.permitir_categorias_nuevas,
                'validacion_estricta': self.categorias.validacion_estricta
            },
            'project_root': self.project_root,
            'debug_mode': self.debug_mode
        }


# Instancia global de configuración
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Obtiene la instancia global de configuración.
    
    Returns:
        Instancia de Settings (singleton)
    """
    global _settings_instance
    
    if _settings_instance is None:
        # PRIMERO: Intentar cargar desde YAML
        try:
            from config.config_manager import ConfigManager
            config_manager = ConfigManager()
            yaml_config = config_manager.get_config()
            
            # Crear Settings desde YAML
            _settings_instance = Settings()
            
            # Aplicar configuración WhatsApp desde YAML
            if hasattr(yaml_config, 'whatsapp'):
                _settings_instance.whatsapp.target_chat_name = getattr(yaml_config.whatsapp, 'target_chat_name', 'Gastos')
                _settings_instance.whatsapp.chrome_headless = getattr(yaml_config.whatsapp, 'chrome_headless', False)
                _settings_instance.whatsapp.connection_timeout_seconds = getattr(yaml_config.whatsapp, 'connection_timeout_seconds', 60)
                _settings_instance.whatsapp.poll_interval_seconds = getattr(yaml_config.whatsapp, 'message_polling_interval_seconds', 30)
            
            # Aplicar configuración Logging desde YAML
            if hasattr(yaml_config, 'logging'):
                level_str = getattr(yaml_config.logging, 'level', 'INFO')
                if hasattr(LogLevel, level_str):
                    _settings_instance.logging.level = LogLevel[level_str]
                _settings_instance.logging.file_path = getattr(yaml_config.logging, 'file_path', 'logs/bot.log')
                _settings_instance.logging.console_output = getattr(yaml_config.logging, 'console_enabled', True)
                
            print(f"[OK] Configuracion cargada desde YAML - headless: {_settings_instance.whatsapp.chrome_headless}")
            
        except Exception as e:
            print(f"[WARN] Error cargando YAML, usando env vars: {e}")
            # FALLBACK: Cargar desde variables de entorno
            _settings_instance = Settings.load_from_env()
        
        _settings_instance.ensure_directories_exist()
        
        # Validar configuración
        errors = _settings_instance.validate_configuration()
        if errors:
            raise ValueError(f"Errores de configuración: {', '.join(errors)}")
    
    return _settings_instance


def reload_settings() -> Settings:
    """
    Recarga la configuración desde el entorno.
    
    Returns:
        Nueva instancia de Settings
    """
    global _settings_instance
    _settings_instance = None
    return get_settings()


def clear_settings_cache():
    """Limpia el cache de configuración para forzar recarga."""
    global _settings_instance
    _settings_instance = None