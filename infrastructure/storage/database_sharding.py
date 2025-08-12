"""
Database Sharding System - FASE 5.3
⚡ Sistema de particionamiento de base de datos para mejorar performance en BDs grandes

Mejora esperada: 60% mejora en queries masivas + escalabilidad horizontal
"""

import asyncio
import threading
import time
import json
import hashlib
import statistics
import sqlite3
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from collections import defaultdict
from enum import Enum
from pathlib import Path
import os

from shared.logger import get_logger
from shared.metrics import get_metrics_collector
from domain.models.gasto import Gasto


logger = get_logger(__name__)


class ShardingStrategy(Enum):
    """Estrategias de particionamiento."""
    DATE_BASED = "date_based"          # Por fecha (mes/año)
    HASH_BASED = "hash_based"          # Por hash de ID
    RANGE_BASED = "range_based"        # Por rango de valores
    CATEGORY_BASED = "category_based"  # Por categoría de gasto
    HYBRID = "hybrid"                  # Combinación de estrategias


class ShardStatus(Enum):
    """Estados de un shard."""
    ACTIVE = "active"
    READONLY = "readonly"
    ARCHIVING = "archiving"
    ARCHIVED = "archived"
    OFFLINE = "offline"


@dataclass
class ShardInfo:
    """Información de un shard."""
    shard_id: str
    database_path: str
    strategy: ShardingStrategy
    status: ShardStatus = ShardStatus.ACTIVE
    
    # Metadatos del shard
    record_count: int = 0
    size_mb: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    last_access: datetime = field(default_factory=datetime.now)
    
    # Criterios de particionamiento
    partition_key: Optional[str] = None
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    categories: List[str] = field(default_factory=list)
    
    # Métricas de rendimiento
    avg_query_time: float = 0.0
    total_queries: int = 0
    
    def update_access(self, query_time: float = 0.0):
        """Actualiza métricas de acceso del shard."""
        self.last_access = datetime.now()
        self.total_queries += 1
        
        if query_time > 0:
            if self.avg_query_time == 0:
                self.avg_query_time = query_time
            else:
                self.avg_query_time = (self.avg_query_time * 0.8 + query_time * 0.2)
    
    @property
    def is_active(self) -> bool:
        """Si el shard está activo para escritura."""
        return self.status == ShardStatus.ACTIVE
    
    @property
    def can_read(self) -> bool:
        """Si el shard permite lecturas."""
        return self.status in [ShardStatus.ACTIVE, ShardStatus.READONLY, ShardStatus.ARCHIVING]
    
    @property
    def age_days(self) -> int:
        """Edad del shard en días."""
        return (datetime.now() - self.created_at).days


class ShardSelector:
    """⚡ Selector inteligente de shards basado en criterios."""
    
    def __init__(self, strategy: ShardingStrategy = ShardingStrategy.DATE_BASED):
        self.strategy = strategy
        self.logger = logger
    
    def select_shard_for_write(self, gasto: Gasto, available_shards: List[ShardInfo]) -> Optional[ShardInfo]:
        """
        Selecciona shard óptimo para escritura.
        
        Args:
            gasto: Gasto a escribir
            available_shards: Lista de shards disponibles
            
        Returns:
            Shard seleccionado o None si no hay disponibles
        """
        active_shards = [s for s in available_shards if s.is_active]
        
        if not active_shards:
            return None
        
        if self.strategy == ShardingStrategy.DATE_BASED:
            return self._select_by_date(gasto, active_shards)
        elif self.strategy == ShardingStrategy.CATEGORY_BASED:
            return self._select_by_category(gasto, active_shards)
        elif self.strategy == ShardingStrategy.HASH_BASED:
            return self._select_by_hash(gasto, active_shards)
        elif self.strategy == ShardingStrategy.HYBRID:
            return self._select_hybrid(gasto, active_shards)
        
        # Fallback: seleccionar shard con menos carga
        return min(active_shards, key=lambda s: s.record_count)
    
    def select_shards_for_read(self, 
                              query_filters: Dict[str, Any], 
                              available_shards: List[ShardInfo]) -> List[ShardInfo]:
        """
        Selecciona shards relevantes para una consulta.
        
        Args:
            query_filters: Filtros de la consulta
            available_shards: Lista de shards disponibles
            
        Returns:
            Lista de shards relevantes
        """
        readable_shards = [s for s in available_shards if s.can_read]
        
        if not readable_shards:
            return []
        
        # Filtrar por criterios de consulta
        relevant_shards = []
        
        for shard in readable_shards:
            if self._is_shard_relevant(shard, query_filters):
                relevant_shards.append(shard)
        
        return relevant_shards if relevant_shards else readable_shards
    
    def _select_by_date(self, gasto: Gasto, shards: List[ShardInfo]) -> ShardInfo:
        """Selecciona shard basado en fecha."""
        target_date = gasto.fecha.date()
        
        # Buscar shard que cubra esta fecha
        for shard in shards:
            if (shard.date_range_start and shard.date_range_end and
                shard.date_range_start <= target_date <= shard.date_range_end):
                return shard
        
        # Si no hay shard específico, crear criterio para nuevo shard
        # Por ahora, usar el shard con menos carga
        return min(shards, key=lambda s: s.record_count)
    
    def _select_by_category(self, gasto: Gasto, shards: List[ShardInfo]) -> ShardInfo:
        """Selecciona shard basado en categoría."""
        # Buscar shard que maneje esta categoría
        for shard in shards:
            if gasto.categoria in shard.categories:
                return shard
        
        # Si no hay shard específico para la categoría, usar balanceado
        return min(shards, key=lambda s: s.record_count)
    
    def _select_by_hash(self, gasto: Gasto, shards: List[ShardInfo]) -> ShardInfo:
        """Selecciona shard basado en hash del ID."""
        # Usar hash del ID para distribución uniforme
        gasto_hash = hash(str(gasto.id)) % len(shards)
        return shards[gasto_hash]
    
    def _select_hybrid(self, gasto: Gasto, shards: List[ShardInfo]) -> ShardInfo:
        """Selecciona shard usando estrategia híbrida."""
        # Prioridad: fecha > categoría > balance de carga
        
        # 1. Intentar por fecha
        date_shard = self._select_by_date(gasto, shards)
        if (date_shard.date_range_start and date_shard.date_range_end and
            date_shard.date_range_start <= gasto.fecha.date() <= date_shard.date_range_end):
            return date_shard
        
        # 2. Intentar por categoría
        category_shards = [s for s in shards if gasto.categoria in s.categories]
        if category_shards:
            return min(category_shards, key=lambda s: s.record_count)
        
        # 3. Balance de carga
        return min(shards, key=lambda s: s.record_count)
    
    def _is_shard_relevant(self, shard: ShardInfo, query_filters: Dict[str, Any]) -> bool:
        """Determina si un shard es relevante para una consulta."""
        # Filtro por fecha
        if 'fecha_inicio' in query_filters and 'fecha_fin' in query_filters:
            query_start = query_filters['fecha_inicio']
            query_end = query_filters['fecha_fin']
            
            if shard.date_range_start and shard.date_range_end:
                # Verificar si hay solapamiento de fechas
                if (query_end < shard.date_range_start or 
                    query_start > shard.date_range_end):
                    return False
        
        # Filtro por categoría
        if 'categoria' in query_filters:
            query_category = query_filters['categoria']
            if shard.categories and query_category not in shard.categories:
                return False
        
        return True


class DatabaseShardManager:
    """⚡ Manager principal del sistema de sharding de base de datos."""
    
    def __init__(self, 
                 base_path: str = "data/shards",
                 strategy: ShardingStrategy = ShardingStrategy.DATE_BASED,
                 max_shard_size_mb: float = 50,
                 max_records_per_shard: int = 10000):
        """
        Inicializa manager de sharding.
        
        Args:
            base_path: Directorio base para shards
            strategy: Estrategia de particionamiento
            max_shard_size_mb: Tamaño máximo por shard
            max_records_per_shard: Máximo registros por shard
        """
        self.base_path = Path(base_path)
        self.strategy = strategy
        self.max_shard_size_mb = max_shard_size_mb
        self.max_records_per_shard = max_records_per_shard
        
        # Asegurar directorio base existe
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Shards activos
        self.shards: Dict[str, ShardInfo] = {}
        self.shard_connections: Dict[str, sqlite3.Connection] = {}
        
        # Selector de shards
        self.shard_selector = ShardSelector(strategy)
        
        # Estadísticas
        self.sharding_stats = {
            'total_shards': 0,
            'active_shards': 0,
            'total_records': 0,
            'total_queries': 0,
            'avg_query_time': 0.0,
            'last_maintenance': None
        }
        
        # Workers de mantenimiento
        self.maintenance_active = False
        self.maintenance_thread: Optional[threading.Thread] = None
        
        self.logger = logger
        self.metrics_collector = get_metrics_collector()
        
        # Inicializar shards existentes
        self._initialize_existing_shards()
        
        self.logger.info(f"DatabaseShardManager inicializado - Estrategia: {strategy.value}")
    
    def _initialize_existing_shards(self):
        """Inicializa shards existentes en el directorio."""
        if not self.base_path.exists():
            return
        
        # Buscar archivos de base de datos
        db_files = list(self.base_path.glob("*.db"))
        
        for db_file in db_files:
            try:
                shard_id = db_file.stem
                shard_info = self._load_shard_metadata(shard_id, str(db_file))
                
                if shard_info:
                    self.shards[shard_id] = shard_info
                    self.logger.debug(f"Shard cargado: {shard_id}")
                
            except Exception as e:
                self.logger.error(f"Error cargando shard {db_file}: {e}")
        
        self._update_sharding_stats()
        self.logger.info(f"📊 Shards inicializados: {len(self.shards)}")
    
    def _load_shard_metadata(self, shard_id: str, db_path: str) -> Optional[ShardInfo]:
        """Carga metadatos de un shard."""
        try:
            # Obtener estadísticas del archivo
            stat = os.stat(db_path)
            size_mb = stat.st_size / 1024 / 1024
            
            # Crear conexión temporal para obtener metadatos
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM gastos")
            record_count = cursor.fetchone()[0]
            
            # Obtener rango de fechas
            cursor.execute("SELECT MIN(fecha), MAX(fecha) FROM gastos WHERE fecha IS NOT NULL")
            date_range = cursor.fetchone()
            
            date_start = date_end = None
            if date_range[0] and date_range[1]:
                date_start = datetime.fromisoformat(date_range[0]).date()
                date_end = datetime.fromisoformat(date_range[1]).date()
            
            conn.close()
            
            # Crear ShardInfo
            shard_info = ShardInfo(
                shard_id=shard_id,
                database_path=db_path,
                strategy=self.strategy,
                record_count=record_count,
                size_mb=size_mb,
                date_range_start=date_start,
                date_range_end=date_end
            )
            
            return shard_info
            
        except Exception as e:
            self.logger.error(f"Error cargando metadatos del shard {shard_id}: {e}")
            return None
    
    def create_shard(self, shard_id: str, partition_criteria: Dict[str, Any] = None) -> ShardInfo:
        """
        Crea nuevo shard con criterios específicos.
        
        Args:
            shard_id: ID único del shard
            partition_criteria: Criterios de particionamiento
            
        Returns:
            Información del shard creado
        """
        db_path = self.base_path / f"{shard_id}.db"
        
        if db_path.exists():
            raise ValueError(f"Shard {shard_id} ya existe")
        
        # Crear shard info
        shard_info = ShardInfo(
            shard_id=shard_id,
            database_path=str(db_path),
            strategy=self.strategy
        )
        
        # Aplicar criterios de particionamiento
        if partition_criteria:
            if 'date_range_start' in partition_criteria:
                shard_info.date_range_start = partition_criteria['date_range_start']
            if 'date_range_end' in partition_criteria:
                shard_info.date_range_end = partition_criteria['date_range_end']
            if 'categories' in partition_criteria:
                shard_info.categories = partition_criteria['categories']
        
        # Crear base de datos
        self._create_shard_database(str(db_path))
        
        # Registrar shard
        self.shards[shard_id] = shard_info
        
        self.logger.info(f"📋 Nuevo shard creado: {shard_id}")
        return shard_info
    
    def _create_shard_database(self, db_path: str):
        """Crea estructura de base de datos para un shard."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crear tabla de gastos (misma estructura que la principal)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                categoria TEXT NOT NULL,
                descripcion TEXT,
                monto REAL NOT NULL,
                metodo_pago TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices optimizados para cada estrategia
        if self.strategy in [ShardingStrategy.DATE_BASED, ShardingStrategy.HYBRID]:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fecha ON gastos(fecha)')
        
        if self.strategy in [ShardingStrategy.CATEGORY_BASED, ShardingStrategy.HYBRID]:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_categoria ON gastos(categoria)')
        
        # Índices generales
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_monto ON gastos(monto)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON gastos(created_at)')
        
        conn.commit()
        conn.close()
    
    def insert_gasto(self, gasto: Gasto) -> bool:
        """
        ⚡ Inserta gasto en el shard apropiado.
        
        Args:
            gasto: Gasto a insertar
            
        Returns:
            True si se insertó exitosamente
        """
        start_time = time.time()
        
        try:
            # Seleccionar shard apropiado
            available_shards = list(self.shards.values())
            selected_shard = self.shard_selector.select_shard_for_write(gasto, available_shards)
            
            if not selected_shard:
                # Crear nuevo shard si no hay disponibles
                selected_shard = self._create_auto_shard(gasto)
            
            # Verificar si el shard necesita división
            if self._should_split_shard(selected_shard):
                selected_shard = self._handle_shard_split(selected_shard, gasto)
            
            # Insertar en shard
            success = self._insert_into_shard(selected_shard, gasto)
            
            if success:
                # Actualizar métricas del shard
                selected_shard.record_count += 1
                selected_shard.update_access(time.time() - start_time)
                
                # Actualizar estadísticas globales
                self.sharding_stats['total_records'] += 1
                self.sharding_stats['total_queries'] += 1
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error insertando gasto en shard: {e}")
            return False
    
    def query_gastos(self, 
                    filters: Dict[str, Any] = None,
                    limit: Optional[int] = None,
                    offset: int = 0) -> List[Gasto]:
        """
        ⚡ Consulta gastos distribuida entre shards.
        
        Args:
            filters: Filtros de consulta
            limit: Límite de resultados
            offset: Offset para paginación
            
        Returns:
            Lista de gastos encontrados
        """
        start_time = time.time()
        filters = filters or {}
        
        try:
            # Seleccionar shards relevantes
            available_shards = list(self.shards.values())
            relevant_shards = self.shard_selector.select_shards_for_read(filters, available_shards)
            
            if not relevant_shards:
                return []
            
            # Consultar en cada shard relevante
            all_results = []
            for shard in relevant_shards:
                shard_results = self._query_shard(shard, filters)
                all_results.extend(shard_results)
                
                # Actualizar métricas del shard
                shard.update_access(time.time() - start_time)
            
            # Ordenar resultados combinados
            all_results.sort(key=lambda g: g.fecha, reverse=True)
            
            # Aplicar paginación
            if limit:
                end_idx = offset + limit
                all_results = all_results[offset:end_idx]
            
            # Actualizar estadísticas globales
            self.sharding_stats['total_queries'] += 1
            query_time = time.time() - start_time
            
            if self.sharding_stats['avg_query_time'] == 0:
                self.sharding_stats['avg_query_time'] = query_time
            else:
                self.sharding_stats['avg_query_time'] = (
                    self.sharding_stats['avg_query_time'] * 0.8 + query_time * 0.2
                )
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"Error consultando gastos distribuidos: {e}")
            return []
    
    def _create_auto_shard(self, gasto: Gasto) -> ShardInfo:
        """Crea shard automáticamente basado en el gasto."""
        # Generar ID basado en estrategia
        if self.strategy == ShardingStrategy.DATE_BASED:
            shard_id = f"gastos_{gasto.fecha.year}_{gasto.fecha.month:02d}"
            criteria = {
                'date_range_start': gasto.fecha.date().replace(day=1),
                'date_range_end': self._get_month_end(gasto.fecha.date())
            }
        elif self.strategy == ShardingStrategy.CATEGORY_BASED:
            shard_id = f"gastos_{gasto.categoria}"
            criteria = {
                'categories': [gasto.categoria]
            }
        else:
            shard_id = f"gastos_{len(self.shards) + 1}"
            criteria = {}
        
        return self.create_shard(shard_id, criteria)
    
    def _get_month_end(self, target_date: date) -> date:
        """Obtiene último día del mes."""
        if target_date.month == 12:
            return target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            return target_date.replace(month=target_date.month + 1, day=1) - timedelta(days=1)
    
    def _should_split_shard(self, shard: ShardInfo) -> bool:
        """Determina si un shard debe dividirse."""
        return (shard.record_count >= self.max_records_per_shard or 
                shard.size_mb >= self.max_shard_size_mb)
    
    def _handle_shard_split(self, shard: ShardInfo, new_gasto: Gasto) -> ShardInfo:
        """Maneja la división de un shard saturado."""
        self.logger.info(f"🔀 Dividiendo shard saturado: {shard.shard_id}")
        
        # Por simplicidad, crear nuevo shard para el nuevo gasto
        # En implementación completa, se redistribuirían los datos
        new_shard = self._create_auto_shard(new_gasto)
        
        # Marcar shard original como readonly si está muy lleno
        if shard.record_count >= self.max_records_per_shard:
            shard.status = ShardStatus.READONLY
        
        return new_shard
    
    def _insert_into_shard(self, shard: ShardInfo, gasto: Gasto) -> bool:
        """Inserta gasto en un shard específico."""
        try:
            conn = self._get_shard_connection(shard.shard_id)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO gastos (fecha, categoria, descripcion, monto, metodo_pago)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                gasto.fecha.isoformat(),
                gasto.categoria,
                gasto.descripcion,
                gasto.monto.valor,
                gasto.metodo_pago or 'efectivo'
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error insertando en shard {shard.shard_id}: {e}")
            return False
    
    def _query_shard(self, shard: ShardInfo, filters: Dict[str, Any]) -> List[Gasto]:
        """Consulta gastos en un shard específico."""
        try:
            conn = self._get_shard_connection(shard.shard_id)
            cursor = conn.cursor()
            
            # Construir query dinámicamente
            where_clauses = []
            params = []
            
            if 'fecha_inicio' in filters:
                where_clauses.append('fecha >= ?')
                params.append(filters['fecha_inicio'].isoformat())
            
            if 'fecha_fin' in filters:
                where_clauses.append('fecha <= ?')
                params.append(filters['fecha_fin'].isoformat())
            
            if 'categoria' in filters:
                where_clauses.append('categoria = ?')
                params.append(filters['categoria'])
            
            if 'monto_min' in filters:
                where_clauses.append('monto >= ?')
                params.append(filters['monto_min'])
            
            if 'monto_max' in filters:
                where_clauses.append('monto <= ?')
                params.append(filters['monto_max'])
            
            # Construir query completo
            query = "SELECT * FROM gastos"
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            query += " ORDER BY fecha DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convertir a objetos Gasto
            gastos = []
            for row in rows:
                # Adaptar según estructura real de Gasto
                gasto = self._row_to_gasto(row)
                if gasto:
                    gastos.append(gasto)
            
            return gastos
            
        except Exception as e:
            self.logger.error(f"Error consultando shard {shard.shard_id}: {e}")
            return []
    
    def _row_to_gasto(self, row: Tuple) -> Optional[Gasto]:
        """Convierte fila de DB a objeto Gasto."""
        try:
            # Adaptar según estructura real de Gasto y tabla
            return Gasto(
                id=row[0],
                fecha=datetime.fromisoformat(row[1]),
                categoria=row[2],
                descripcion=row[3] or "",
                monto_valor=row[4]
            )
        except Exception as e:
            self.logger.error(f"Error convirtiendo fila a Gasto: {e}")
            return None
    
    def _get_shard_connection(self, shard_id: str) -> sqlite3.Connection:
        """Obtiene conexión a shard (pool de conexiones simple)."""
        if shard_id not in self.shard_connections:
            shard_info = self.shards[shard_id]
            conn = sqlite3.connect(shard_info.database_path)
            conn.row_factory = sqlite3.Row  # Acceso por nombre de columna
            self.shard_connections[shard_id] = conn
        
        return self.shard_connections[shard_id]
    
    def start_maintenance(self, check_interval: int = 3600):
        """Inicia mantenimiento automático de shards."""
        if self.maintenance_active:
            return
        
        self.maintenance_active = True
        self.maintenance_thread = threading.Thread(
            target=self._maintenance_loop,
            args=(check_interval,),
            daemon=True
        )
        self.maintenance_thread.start()
        
        self.logger.info("🔧 Shard maintenance iniciado")
    
    def stop_maintenance(self):
        """Detiene el mantenimiento automático."""
        self.maintenance_active = False
        if self.maintenance_thread:
            self.maintenance_thread.join(timeout=10)
        
        self.logger.info("🛑 Shard maintenance detenido")
    
    def _maintenance_loop(self, check_interval: int):
        """Loop principal de mantenimiento."""
        while self.maintenance_active:
            try:
                # Ejecutar tareas de mantenimiento
                self._run_maintenance_cycle()
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error en maintenance loop: {e}")
                time.sleep(300)  # 5 minutos en caso de error
    
    def _run_maintenance_cycle(self):
        """Ejecuta ciclo de mantenimiento."""
        self.logger.debug("🔄 Ejecutando ciclo de mantenimiento de shards...")
        
        # 1. Actualizar estadísticas de shards
        self._update_shard_statistics()
        
        # 2. Archivar shards antiguos si es necesario
        self._archive_old_shards()
        
        # 3. Optimizar conexiones
        self._optimize_connections()
        
        # 4. Registrar métricas
        self._record_sharding_metrics()
        
        self.sharding_stats['last_maintenance'] = datetime.now().isoformat()
    
    def _update_shard_statistics(self):
        """Actualiza estadísticas de todos los shards."""
        for shard in self.shards.values():
            try:
                # Actualizar tamaño del archivo
                if os.path.exists(shard.database_path):
                    stat = os.stat(shard.database_path)
                    shard.size_mb = stat.st_size / 1024 / 1024
                
            except Exception as e:
                self.logger.error(f"Error actualizando estadísticas del shard {shard.shard_id}: {e}")
    
    def _archive_old_shards(self):
        """Archiva shards antiguos para liberar recursos."""
        current_date = datetime.now()
        
        for shard in list(self.shards.values()):
            # Archivar shards de más de 1 año sin acceso reciente
            days_since_access = (current_date - shard.last_access).days
            
            if (days_since_access > 365 and 
                shard.status == ShardStatus.READONLY and
                shard.record_count > 0):
                
                shard.status = ShardStatus.ARCHIVING
                self.logger.info(f"📦 Archivando shard antiguo: {shard.shard_id}")
                
                # En implementación completa, mover a storage de archivo
                # Por ahora solo cambiar estado
                shard.status = ShardStatus.ARCHIVED
    
    def _optimize_connections(self):
        """Optimiza conexiones de shards."""
        # Cerrar conexiones inactivas
        inactive_connections = []
        
        for shard_id, conn in self.shard_connections.items():
            shard = self.shards.get(shard_id)
            if shard and (datetime.now() - shard.last_access).seconds > 3600:  # 1 hora
                inactive_connections.append(shard_id)
        
        for shard_id in inactive_connections:
            try:
                self.shard_connections[shard_id].close()
                del self.shard_connections[shard_id]
                self.logger.debug(f"Conexión cerrada para shard inactivo: {shard_id}")
            except Exception as e:
                self.logger.error(f"Error cerrando conexión del shard {shard_id}: {e}")
    
    def _record_sharding_metrics(self):
        """Registra métricas de sharding."""
        try:
            self.metrics_collector.record_custom_metric(
                'sharding_total_shards',
                len(self.shards)
            )
            
            active_shards = len([s for s in self.shards.values() if s.is_active])
            self.metrics_collector.record_custom_metric(
                'sharding_active_shards',
                active_shards
            )
            
            self.metrics_collector.record_custom_metric(
                'sharding_total_records',
                sum(s.record_count for s in self.shards.values())
            )
            
            self.metrics_collector.record_custom_metric(
                'sharding_avg_query_time',
                self.sharding_stats['avg_query_time']
            )
            
        except Exception as e:
            self.logger.error(f"Error registrando métricas de sharding: {e}")
    
    def _update_sharding_stats(self):
        """Actualiza estadísticas globales de sharding."""
        self.sharding_stats['total_shards'] = len(self.shards)
        self.sharding_stats['active_shards'] = len([s for s in self.shards.values() if s.is_active])
        self.sharding_stats['total_records'] = sum(s.record_count for s in self.shards.values())
    
    def get_sharding_report(self) -> Dict[str, Any]:
        """Genera reporte completo del sistema de sharding."""
        # Estadísticas por shard
        shard_reports = {}
        for shard_id, shard in self.shards.items():
            shard_reports[shard_id] = {
                'status': shard.status.value,
                'record_count': shard.record_count,
                'size_mb': shard.size_mb,
                'avg_query_time': shard.avg_query_time,
                'total_queries': shard.total_queries,
                'age_days': shard.age_days,
                'date_range': f"{shard.date_range_start} to {shard.date_range_end}" if shard.date_range_start else None,
                'categories': shard.categories
            }
        
        # Distribución de datos
        total_records = sum(s.record_count for s in self.shards.values())
        distribution_analysis = {}
        
        if total_records > 0:
            for shard_id, shard in self.shards.items():
                distribution_analysis[shard_id] = {
                    'percentage': (shard.record_count / total_records) * 100,
                    'load_factor': shard.record_count / self.max_records_per_shard
                }
        
        return {
            'sharding_stats': self.sharding_stats,
            'configuration': {
                'strategy': self.strategy.value,
                'max_shard_size_mb': self.max_shard_size_mb,
                'max_records_per_shard': self.max_records_per_shard,
                'maintenance_active': self.maintenance_active
            },
            'shard_details': shard_reports,
            'distribution_analysis': distribution_analysis,
            'performance_metrics': {
                'total_shards': len(self.shards),
                'active_connections': len(self.shard_connections),
                'average_shard_size': statistics.mean([s.size_mb for s in self.shards.values()]) if self.shards else 0,
                'load_balance_score': self._calculate_load_balance_score()
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_load_balance_score(self) -> float:
        """Calcula score de balance de carga entre shards."""
        if len(self.shards) < 2:
            return 100.0
        
        loads = [s.record_count for s in self.shards.values() if s.is_active]
        if not loads:
            return 100.0
        
        std_dev = statistics.stdev(loads) if len(loads) > 1 else 0
        avg_load = statistics.mean(loads)
        
        # Score basado en desviación estándar relativa
        if avg_load > 0:
            cv = std_dev / avg_load  # Coeficiente de variación
            score = max(0, 100 - (cv * 100))
        else:
            score = 100.0
        
        return score
    
    def close_all_connections(self):
        """Cierra todas las conexiones de shards."""
        for conn in self.shard_connections.values():
            try:
                conn.close()
            except Exception as e:
                self.logger.error(f"Error cerrando conexión: {e}")
        
        self.shard_connections.clear()
        self.logger.info("🔌 Todas las conexiones de shards cerradas")


# Factory function para manager de sharding
def create_database_shard_manager(base_path: str = "data/shards",
                                 strategy: ShardingStrategy = ShardingStrategy.DATE_BASED,
                                 max_shard_size_mb: float = 50,
                                 auto_maintenance: bool = True) -> DatabaseShardManager:
    """
    Crea manager de sharding de base de datos.
    
    Args:
        base_path: Directorio base para shards
        strategy: Estrategia de particionamiento
        max_shard_size_mb: Tamaño máximo por shard
        auto_maintenance: Si iniciar mantenimiento automático
        
    Returns:
        Manager de sharding configurado
    """
    manager = DatabaseShardManager(base_path, strategy, max_shard_size_mb)
    
    if auto_maintenance:
        manager.start_maintenance()
    
    return manager