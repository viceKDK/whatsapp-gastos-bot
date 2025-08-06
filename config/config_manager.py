"""
Gestor de Configuración Avanzada

Sistema centralizado para manejo de configuración usando archivos YAML.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict

from shared.logger import get_logger


logger = get_logger(__name__)


@dataclass
class WhatsAppConfig:
    """Configuración para WhatsApp."""
    target_chat_name: str = "Gastos Bot"
    chrome_headless: bool = False
    connection_timeout_seconds: int = 60
    message_polling_interval_seconds: int = 5
    chrome_profile_path: Optional[str] = None
    max_reconnection_attempts: int = 3


@dataclass
class StorageConfig:
    """Configuración para almacenamiento."""
    primary_storage: str = "excel"  # "excel", "sqlite"
    excel_file_path: str = "data/gastos.xlsx"
    sqlite_db_path: str = "data/gastos.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_backup_files: int = 10


@dataclass
class LoggingConfig:
    """Configuración para logging."""
    level: str = "INFO"
    file_path: str = "logs/bot_gastos.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_enabled: bool = True


@dataclass
class OCRConfig:
    """Configuración para OCR de recibos y PDF."""
    enabled: bool = True
    language: str = "spa+eng"  # Spanish + English
    confidence_threshold: float = 0.6
    preprocessing_enabled: bool = True
    supported_formats: list = None
    
    # Configuración específica para PDF
    pdf_enabled: bool = True
    pdf_conversion_dpi: int = 200
    max_pdf_pages: int = 10
    tesseract_path: Optional[str] = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['.jpg', '.jpeg', '.png', '.pdf']


@dataclass
class ValidationConfig:
    """Configuración para validaciones."""
    max_amount: float = 1000000.0
    min_amount: float = 0.01
    required_fields: list = None
    custom_categories: list = None
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = ['monto', 'categoria']
        if self.custom_categories is None:
            self.custom_categories = [
                'comida', 'transporte', 'servicios', 'entretenimiento',
                'salud', 'educacion', 'hogar', 'ropa', 'otros'
            ]


@dataclass
class ExportConfig:
    """Configuración para exportación."""
    default_format: str = "excel"
    output_directory: str = "exports"
    include_charts: bool = True
    date_format: str = "%Y-%m-%d"
    supported_formats: list = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['excel', 'csv', 'pdf', 'json']


@dataclass
class PerformanceConfig:
    """Configuración para monitoreo de performance."""
    metrics_enabled: bool = True
    metrics_file: str = "logs/metrics.json"
    alert_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                'memory_usage_mb': 500.0,
                'processing_time_seconds': 10.0,
                'error_rate_percentage': 5.0
            }


@dataclass
class BotConfig:
    """Configuración completa del bot."""
    whatsapp: WhatsAppConfig
    storage: StorageConfig
    logging: LoggingConfig
    ocr: OCRConfig
    validation: ValidationConfig
    export: ExportConfig
    performance: PerformanceConfig
    
    @classmethod
    def default(cls) -> 'BotConfig':
        """Crea configuración con valores por defecto."""
        return cls(
            whatsapp=WhatsAppConfig(),
            storage=StorageConfig(),
            logging=LoggingConfig(),
            ocr=OCRConfig(),
            validation=ValidationConfig(),
            export=ExportConfig(),
            performance=PerformanceConfig()
        )


class ConfigManager:
    """Gestor de configuración usando archivos YAML."""
    
    DEFAULT_CONFIG_FILE = "config/config.yaml"
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_file: Ruta al archivo de configuración
        """
        self.config_file = Path(config_file or self.DEFAULT_CONFIG_FILE)
        self.logger = logger
        self._config: Optional[BotConfig] = None
        
        # Asegurar que el directorio de configuración existe
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> BotConfig:
        """
        Carga la configuración desde archivo YAML.
        
        Returns:
            Configuración cargada
        """
        try:
            if not self.config_file.exists():
                self.logger.info(f"Archivo de configuración no existe: {self.config_file}")
                self.logger.info("Creando configuración por defecto...")
                self._config = BotConfig.default()
                self.save_config()
                return self._config
            
            self.logger.info(f"Cargando configuración desde: {self.config_file}")
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            
            # Convertir YAML a objetos de configuración
            self._config = self._parse_yaml_config(yaml_data)
            
            self.logger.info("Configuración cargada exitosamente")
            return self._config
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            self.logger.info("Usando configuración por defecto")
            self._config = BotConfig.default()
            return self._config
    
    def save_config(self, config: Optional[BotConfig] = None) -> bool:
        """
        Guarda la configuración en archivo YAML.
        
        Args:
            config: Configuración a guardar (usa la actual si no se proporciona)
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            config_to_save = config or self._config
            if not config_to_save:
                raise ValueError("No hay configuración para guardar")
            
            # Convertir a diccionario
            config_dict = asdict(config_to_save)
            
            # Agregar metadata
            config_dict['_metadata'] = {
                'version': '1.0',
                'created_by': 'Bot Gastos WhatsApp',
                'description': 'Configuración del sistema de gastos'
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(
                    config_dict, 
                    f, 
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                    sort_keys=False
                )
            
            self.logger.info(f"Configuración guardada en: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {e}")
            return False
    
    def get_config(self) -> BotConfig:
        """
        Obtiene la configuración actual.
        
        Returns:
            Configuración actual (carga desde archivo si no está en memoria)
        """
        if self._config is None:
            return self.load_config()
        return self._config
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Actualiza configuración con nuevos valores.
        
        Args:
            updates: Diccionario con actualizaciones
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            config = self.get_config()
            
            # Aplicar actualizaciones usando dot notation
            for key_path, value in updates.items():
                self._set_nested_value(config, key_path, value)
            
            # Guardar configuración actualizada
            return self.save_config(config)
            
        except Exception as e:
            self.logger.error(f"Error actualizando configuración: {e}")
            return False
    
    def validate_config(self, config: Optional[BotConfig] = None) -> bool:
        """
        Valida la configuración.
        
        Args:
            config: Configuración a validar
            
        Returns:
            True si la configuración es válida
        """
        try:
            config_to_validate = config or self.get_config()
            
            # Validaciones básicas
            errors = []
            
            # Validar WhatsApp config
            if not config_to_validate.whatsapp.target_chat_name.strip():
                errors.append("whatsapp.target_chat_name no puede estar vacío")
            
            if config_to_validate.whatsapp.connection_timeout_seconds <= 0:
                errors.append("whatsapp.connection_timeout_seconds debe ser positivo")
            
            # Validar storage config
            valid_storage_types = ['excel', 'sqlite']
            if config_to_validate.storage.primary_storage not in valid_storage_types:
                errors.append(f"storage.primary_storage debe ser uno de: {valid_storage_types}")
            
            # Validar logging config
            valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if config_to_validate.logging.level not in valid_log_levels:
                errors.append(f"logging.level debe ser uno de: {valid_log_levels}")
            
            # Validar validation config
            if config_to_validate.validation.max_amount <= config_to_validate.validation.min_amount:
                errors.append("validation.max_amount debe ser mayor que min_amount")
            
            if errors:
                self.logger.error("Errores de validación encontrados:")
                for error in errors:
                    self.logger.error(f"  - {error}")
                return False
            
            self.logger.info("Configuración validada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validando configuración: {e}")
            return False
    
    def _parse_yaml_config(self, yaml_data: Dict[str, Any]) -> BotConfig:
        """Convierte datos YAML a objetos de configuración."""
        try:
            return BotConfig(
                whatsapp=WhatsAppConfig(**yaml_data.get('whatsapp', {})),
                storage=StorageConfig(**yaml_data.get('storage', {})),
                logging=LoggingConfig(**yaml_data.get('logging', {})),
                ocr=OCRConfig(**yaml_data.get('ocr', {})),
                validation=ValidationConfig(**yaml_data.get('validation', {})),
                export=ExportConfig(**yaml_data.get('export', {})),
                performance=PerformanceConfig(**yaml_data.get('performance', {}))
            )
        except Exception as e:
            self.logger.warning(f"Error parseando configuración YAML: {e}")
            self.logger.info("Usando valores por defecto para secciones con errores")
            
            # Crear configuración con valores por defecto para secciones problemáticas
            return BotConfig(
                whatsapp=self._safe_parse_section(yaml_data, 'whatsapp', WhatsAppConfig),
                storage=self._safe_parse_section(yaml_data, 'storage', StorageConfig),
                logging=self._safe_parse_section(yaml_data, 'logging', LoggingConfig),
                ocr=self._safe_parse_section(yaml_data, 'ocr', OCRConfig),
                validation=self._safe_parse_section(yaml_data, 'validation', ValidationConfig),
                export=self._safe_parse_section(yaml_data, 'export', ExportConfig),
                performance=self._safe_parse_section(yaml_data, 'performance', PerformanceConfig)
            )
    
    def _safe_parse_section(self, yaml_data: Dict, section_name: str, section_class):
        """Parsea una sección de configuración de forma segura."""
        try:
            section_data = yaml_data.get(section_name, {})
            return section_class(**section_data)
        except Exception as e:
            self.logger.warning(f"Error en sección '{section_name}': {e}. Usando valores por defecto.")
            return section_class()
    
    def _set_nested_value(self, obj: Any, key_path: str, value: Any) -> None:
        """Establece un valor usando dot notation (ej: 'whatsapp.target_chat_name')."""
        keys = key_path.split('.')
        current = obj
        
        # Navegar hasta el penúltimo nivel
        for key in keys[:-1]:
            if hasattr(current, key):
                current = getattr(current, key)
            else:
                raise ValueError(f"Clave no encontrada: {key}")
        
        # Establecer el valor final
        final_key = keys[-1]
        if hasattr(current, final_key):
            setattr(current, final_key, value)
        else:
            raise ValueError(f"Clave no encontrada: {final_key}")


# Instancia global del gestor de configuración
config_manager = ConfigManager()


def get_config() -> BotConfig:
    """
    Función de conveniencia para obtener la configuración.
    
    Returns:
        Configuración actual del bot
    """
    return config_manager.get_config()


def reload_config() -> BotConfig:
    """
    Recarga la configuración desde archivo.
    
    Returns:
        Configuración recargada
    """
    return config_manager.load_config()