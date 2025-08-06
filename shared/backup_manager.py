"""
Sistema de Backups Automáticos

Gestiona backups automáticos y programados de datos, configuración y logs.
"""

import os
import shutil
import zipfile
import json
import threading
import time
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import schedule

from config.config_manager import get_config
from shared.logger import get_logger


logger = get_logger(__name__)


class BackupType(Enum):
    """Tipos de backup."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    CONFIG_ONLY = "config_only"


class BackupStatus(Enum):
    """Estados de backup."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackupInfo:
    """Información de un backup."""
    id: str
    type: BackupType
    status: BackupStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    size_bytes: int = 0
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'id': self.id,
            'type': self.type.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'file_path': self.file_path,
            'size_bytes': self.size_bytes,
            'checksum': self.checksum,
            'error_message': self.error_message,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupInfo':
        """Crea desde diccionario."""
        return cls(
            id=data['id'],
            type=BackupType(data['type']),
            status=BackupStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            file_path=data.get('file_path'),
            size_bytes=data.get('size_bytes', 0),
            checksum=data.get('checksum'),
            error_message=data.get('error_message'),
            metadata=data.get('metadata', {})
        )


class BackupManager:
    """Gestor de backups automáticos."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logger
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Estado interno
        self._running = False
        self._scheduler_thread = None
        self._current_backup: Optional[BackupInfo] = None
        self._backup_history: List[BackupInfo] = []
        
        # Archivos de metadatos
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        
        # Cargar historial existente
        self._load_backup_history()
        
        # Configurar programación automática si está habilitada
        if getattr(self.config.storage, 'backup_enabled', True):
            self.setup_automatic_backups()
    
    def setup_automatic_backups(self):
        """Configura backups automáticos."""
        try:
            interval_hours = getattr(self.config.storage, 'backup_interval_hours', 24)
            
            # Programar backup diario
            schedule.every(interval_hours).hours.do(self._scheduled_backup)
            
            # Programar backup semanal completo los domingos
            schedule.every().sunday.at("02:00").do(self._scheduled_weekly_backup)
            
            # Programar limpieza mensual
            schedule.every().month.do(self._cleanup_old_backups)
            
            self.logger.info(f"Backups automáticos configurados cada {interval_hours} horas")
            
        except Exception as e:
            self.logger.error(f"Error configurando backups automáticos: {e}")
    
    def start_scheduler(self):
        """Inicia el scheduler de backups."""
        if self._running:
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        self.logger.info("Scheduler de backups iniciado")
    
    def stop_scheduler(self):
        """Detiene el scheduler de backups."""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        self.logger.info("Scheduler de backups detenido")
    
    def _scheduler_loop(self):
        """Loop principal del scheduler."""
        while self._running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
            except Exception as e:
                self.logger.error(f"Error en scheduler loop: {e}")
                time.sleep(60)
    
    def _scheduled_backup(self):
        """Ejecuta backup programado."""
        self.logger.info("Ejecutando backup programado")
        self.create_backup(BackupType.INCREMENTAL)
    
    def _scheduled_weekly_backup(self):
        """Ejecuta backup semanal completo."""
        self.logger.info("Ejecutando backup semanal completo")
        self.create_backup(BackupType.FULL)
    
    def create_backup(self, backup_type: BackupType = BackupType.FULL, 
                     description: str = None) -> Optional[BackupInfo]:
        """
        Crea un backup.
        
        Args:
            backup_type: Tipo de backup
            description: Descripción opcional
            
        Returns:
            Información del backup creado
        """
        if self._current_backup and self._current_backup.status == BackupStatus.RUNNING:
            self.logger.warning("Ya hay un backup en ejecución")
            return None
        
        try:
            # Crear información del backup
            backup_id = self._generate_backup_id()
            backup_info = BackupInfo(
                id=backup_id,
                type=backup_type,
                status=BackupStatus.PENDING,
                created_at=datetime.now(),
                metadata={'description': description or f"Backup {backup_type.value}"}
            )
            
            self._current_backup = backup_info
            
            # Ejecutar backup en thread separado
            backup_thread = threading.Thread(
                target=self._execute_backup,
                args=(backup_info,),
                daemon=True
            )
            backup_thread.start()
            
            return backup_info
            
        except Exception as e:
            self.logger.error(f"Error iniciando backup: {e}")
            return None
    
    def _execute_backup(self, backup_info: BackupInfo):
        """Ejecuta el proceso de backup."""
        try:
            backup_info.status = BackupStatus.RUNNING
            self.logger.info(f"Iniciando backup {backup_info.id} tipo {backup_info.type.value}")
            
            # Determinar archivos a respaldar
            files_to_backup = self._get_files_to_backup(backup_info.type)
            
            if not files_to_backup:
                backup_info.status = BackupStatus.FAILED
                backup_info.error_message = "No hay archivos para respaldar"
                self.logger.error("No hay archivos para respaldar")
                return
            
            # Crear archivo de backup
            backup_filename = self._generate_backup_filename(backup_info)
            backup_path = self.backup_dir / backup_filename
            
            # Crear ZIP con los archivos
            total_size = 0
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_backup:
                    try:
                        if file_path.exists():
                            # Calcular ruta relativa para el archivo en el ZIP
                            arcname = file_path.name if file_path.is_file() else str(file_path)
                            zipf.write(file_path, arcname)
                            total_size += file_path.stat().st_size
                            self.logger.debug(f"Agregado al backup: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Error agregando archivo {file_path}: {e}")
            
            # Calcular checksum
            checksum = self._calculate_file_checksum(backup_path)
            
            # Actualizar información del backup
            backup_info.file_path = str(backup_path)
            backup_info.size_bytes = backup_path.stat().st_size
            backup_info.checksum = checksum
            backup_info.completed_at = datetime.now()
            backup_info.status = BackupStatus.COMPLETED
            backup_info.metadata['files_count'] = len(files_to_backup)
            backup_info.metadata['original_size_bytes'] = total_size
            backup_info.metadata['compression_ratio'] = (
                1 - (backup_info.size_bytes / total_size)
            ) if total_size > 0 else 0
            
            # Agregar al historial
            self._backup_history.append(backup_info)
            self._save_backup_history()
            
            # Limpiar backups antiguos si es necesario
            self._cleanup_old_backups()
            
            self.logger.info(f"Backup {backup_info.id} completado exitosamente. Tamaño: {backup_info.size_bytes} bytes")
            
        except Exception as e:
            backup_info.status = BackupStatus.FAILED
            backup_info.error_message = str(e)
            self.logger.error(f"Error ejecutando backup {backup_info.id}: {e}")
            
        finally:
            self._current_backup = None
    
    def _get_files_to_backup(self, backup_type: BackupType) -> List[Path]:
        """
        Obtiene lista de archivos a respaldar según el tipo.
        
        Args:
            backup_type: Tipo de backup
            
        Returns:
            Lista de archivos a respaldar
        """
        files = []
        
        try:
            if backup_type == BackupType.CONFIG_ONLY:
                # Solo archivos de configuración
                config_files = [
                    Path("config"),
                    Path(".env") if Path(".env").exists() else None
                ]
                files.extend([f for f in config_files if f and f.exists()])
                
            else:
                # Archivos de datos
                data_dir = Path(self.config.storage.excel_file_path).parent
                if data_dir.exists():
                    files.append(data_dir)
                
                sqlite_file = Path(self.config.storage.sqlite_db_path)
                if sqlite_file.exists():
                    files.append(sqlite_file)
                
                # Archivos de configuración
                config_dir = Path("config")
                if config_dir.exists():
                    files.append(config_dir)
                
                # Logs (solo para backup completo)
                if backup_type == BackupType.FULL:
                    logs_dir = Path(self.config.logging.file_path).parent
                    if logs_dir.exists():
                        files.append(logs_dir)
                
                # Para backups incrementales, solo archivos modificados recientemente
                if backup_type == BackupType.INCREMENTAL:
                    files = self._filter_recent_files(files, days=1)
                elif backup_type == BackupType.DIFFERENTIAL:
                    last_full_backup = self._get_last_full_backup()
                    if last_full_backup:
                        files = self._filter_files_since_backup(files, last_full_backup)
            
            return files
            
        except Exception as e:
            self.logger.error(f"Error obteniendo archivos para backup: {e}")
            return []
    
    def _filter_recent_files(self, files: List[Path], days: int) -> List[Path]:
        """Filtra archivos modificados recientemente."""
        cutoff_time = datetime.now() - timedelta(days=days)
        filtered_files = []
        
        for file_path in files:
            try:
                if file_path.is_file():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime >= cutoff_time:
                        filtered_files.append(file_path)
                elif file_path.is_dir():
                    # Para directorios, incluir si contiene archivos recientes
                    for subfile in file_path.rglob('*'):
                        if subfile.is_file():
                            mtime = datetime.fromtimestamp(subfile.stat().st_mtime)
                            if mtime >= cutoff_time:
                                filtered_files.append(file_path)
                                break
            except Exception as e:
                self.logger.warning(f"Error verificando archivo {file_path}: {e}")
        
        return filtered_files
    
    def _filter_files_since_backup(self, files: List[Path], 
                                  reference_backup: BackupInfo) -> List[Path]:
        """Filtra archivos modificados desde un backup de referencia."""
        if not reference_backup.completed_at:
            return files
        
        cutoff_time = reference_backup.completed_at
        return self._filter_recent_files(files, 
                                       (datetime.now() - cutoff_time).days)
    
    def _get_last_full_backup(self) -> Optional[BackupInfo]:
        """Obtiene el último backup completo."""
        for backup in reversed(self._backup_history):
            if (backup.type == BackupType.FULL and 
                backup.status == BackupStatus.COMPLETED):
                return backup
        return None
    
    def _generate_backup_id(self) -> str:
        """Genera ID único para backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}"
    
    def _generate_backup_filename(self, backup_info: BackupInfo) -> str:
        """Genera nombre de archivo para backup."""
        timestamp = backup_info.created_at.strftime("%Y%m%d_%H%M%S")
        return f"{backup_info.id}_{backup_info.type.value}.zip"
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calcula checksum MD5 de un archivo."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _cleanup_old_backups(self):
        """Limpia backups antiguos."""
        try:
            max_backups = getattr(self.config.storage, 'max_backup_files', 10)
            
            # Ordenar por fecha (más reciente primero)
            completed_backups = [
                b for b in self._backup_history
                if b.status == BackupStatus.COMPLETED and b.file_path
            ]
            completed_backups.sort(key=lambda x: x.completed_at, reverse=True)
            
            # Eliminar backups excedentes
            for backup_to_remove in completed_backups[max_backups:]:
                try:
                    backup_file = Path(backup_to_remove.file_path)
                    if backup_file.exists():
                        backup_file.unlink()
                        self.logger.info(f"Backup antiguo eliminado: {backup_to_remove.id}")
                    
                    # Remover del historial
                    self._backup_history.remove(backup_to_remove)
                    
                except Exception as e:
                    self.logger.warning(f"Error eliminando backup {backup_to_remove.id}: {e}")
            
            self._save_backup_history()
            
        except Exception as e:
            self.logger.error(f"Error en limpieza de backups: {e}")
    
    def restore_backup(self, backup_id: str, restore_path: Optional[str] = None) -> bool:
        """
        Restaura un backup.
        
        Args:
            backup_id: ID del backup a restaurar
            restore_path: Ruta de restauración (usa directorio actual si None)
            
        Returns:
            True si la restauración fue exitosa
        """
        try:
            # Buscar backup
            backup_info = self.get_backup_info(backup_id)
            if not backup_info:
                self.logger.error(f"Backup no encontrado: {backup_id}")
                return False
            
            if backup_info.status != BackupStatus.COMPLETED:
                self.logger.error(f"Backup no completado: {backup_id}")
                return False
            
            backup_file = Path(backup_info.file_path)
            if not backup_file.exists():
                self.logger.error(f"Archivo de backup no existe: {backup_file}")
                return False
            
            # Verificar checksum
            if backup_info.checksum:
                current_checksum = self._calculate_file_checksum(backup_file)
                if current_checksum != backup_info.checksum:
                    self.logger.error(f"Checksum no coincide para backup {backup_id}")
                    return False
            
            # Ruta de restauración
            if restore_path:
                restore_dir = Path(restore_path)
            else:
                restore_dir = Path.cwd() / "restored" / backup_id
            
            restore_dir.mkdir(parents=True, exist_ok=True)
            
            # Extraer archivo
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(restore_dir)
            
            self.logger.info(f"Backup {backup_id} restaurado en: {restore_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restaurando backup {backup_id}: {e}")
            return False
    
    def get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """
        Obtiene información de un backup.
        
        Args:
            backup_id: ID del backup
            
        Returns:
            Información del backup
        """
        for backup in self._backup_history:
            if backup.id == backup_id:
                return backup
        return None
    
    def list_backups(self) -> List[BackupInfo]:
        """
        Lista todos los backups.
        
        Returns:
            Lista de información de backups
        """
        return self._backup_history.copy()
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de backups.
        
        Returns:
            Estadísticas de backups
        """
        try:
            completed_backups = [
                b for b in self._backup_history
                if b.status == BackupStatus.COMPLETED
            ]
            
            failed_backups = [
                b for b in self._backup_history
                if b.status == BackupStatus.FAILED
            ]
            
            total_size = sum(b.size_bytes for b in completed_backups)
            
            stats = {
                'total_backups': len(self._backup_history),
                'completed_backups': len(completed_backups),
                'failed_backups': len(failed_backups),
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'oldest_backup': min(
                    (b.created_at for b in completed_backups),
                    default=None
                ),
                'newest_backup': max(
                    (b.created_at for b in completed_backups),
                    default=None
                ),
                'backup_types': {
                    bt.value: len([
                        b for b in completed_backups 
                        if b.type == bt
                    ])
                    for bt in BackupType
                },
                'current_backup': (
                    self._current_backup.to_dict() 
                    if self._current_backup else None
                )
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def _load_backup_history(self):
        """Carga historial de backups desde archivo."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._backup_history = [
                        BackupInfo.from_dict(item) 
                        for item in data.get('backups', [])
                    ]
                self.logger.debug(f"Cargados {len(self._backup_history)} backups del historial")
            
        except Exception as e:
            self.logger.error(f"Error cargando historial de backups: {e}")
            self._backup_history = []
    
    def _save_backup_history(self):
        """Guarda historial de backups en archivo."""
        try:
            data = {
                'version': '1.0',
                'updated_at': datetime.now().isoformat(),
                'backups': [backup.to_dict() for backup in self._backup_history]
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error guardando historial de backups: {e}")
    
    def cancel_current_backup(self) -> bool:
        """
        Cancela el backup actual si está en ejecución.
        
        Returns:
            True si se canceló exitosamente
        """
        if self._current_backup and self._current_backup.status == BackupStatus.RUNNING:
            self._current_backup.status = BackupStatus.CANCELLED
            self.logger.info(f"Backup {self._current_backup.id} cancelado")
            return True
        return False


# Instancia global del gestor de backups
_backup_manager: Optional[BackupManager] = None


def get_backup_manager() -> BackupManager:
    """Obtiene instancia global del gestor de backups."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
        _backup_manager.start_scheduler()
    return _backup_manager


def create_backup(backup_type: BackupType = BackupType.FULL, 
                 description: str = None) -> Optional[BackupInfo]:
    """
    Función de conveniencia para crear backup.
    
    Args:
        backup_type: Tipo de backup
        description: Descripción opcional
        
    Returns:
        Información del backup creado
    """
    manager = get_backup_manager()
    return manager.create_backup(backup_type, description)