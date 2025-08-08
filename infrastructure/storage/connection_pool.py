"""
Connection Pool para SQLite (FASE 3)

Sistema de pool de conexiones para operaciones concurrentes de base de datos.
Optimiza performance en escenarios de alta concurrencia y múltiples workers.
"""

import sqlite3
import threading
import queue
import time
import contextlib
from typing import Optional, Dict, Any, ContextManager
from pathlib import Path
from datetime import datetime

from shared.logger import get_logger


logger = get_logger(__name__)


class PooledConnection:
    """Conexión SQLite en el pool con metadata adicional."""
    
    def __init__(self, connection: sqlite3.Connection, pool_id: int):
        self.connection = connection
        self.pool_id = pool_id
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.usage_count = 0
        self.is_healthy = True
    
    def mark_used(self):
        """Marca la conexión como usada."""
        self.last_used = datetime.now()
        self.usage_count += 1
    
    def check_health(self) -> bool:
        """Verifica si la conexión está saludable."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            self.is_healthy = True
            return True
        except Exception:
            self.is_healthy = False
            return False


class SQLiteConnectionPool:
    """⚡ Pool de conexiones SQLite optimizado para concurrencia (FASE 3)."""
    
    def __init__(self, db_path: str, pool_size: int = 5, max_pool_size: int = 10):
        """
        Inicializa pool de conexiones SQLite.
        
        Args:
            db_path: Ruta a la base de datos
            pool_size: Tamaño inicial del pool
            max_pool_size: Tamaño máximo del pool
        """
        self.db_path = Path(db_path)
        self.pool_size = pool_size
        self.max_pool_size = max_pool_size
        
        # Pool de conexiones
        self.available_connections = queue.Queue(maxsize=max_pool_size)
        self.all_connections = {}  # pool_id -> PooledConnection
        self.connection_counter = 0
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Estadísticas
        self.stats = {
            'connections_created': 0,
            'connections_reused': 0,
            'connections_closed': 0,
            'active_connections': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'total_requests': 0,
            'average_wait_time': 0.0
        }
        
        self.logger = logger
        
        # Crear conexiones iniciales
        self._initialize_pool()
        
        self.logger.info(f"SQLiteConnectionPool inicializado - Pool: {pool_size}, Max: {max_pool_size}")
    
    def _initialize_pool(self):
        """Inicializa el pool con conexiones base."""
        for _ in range(self.pool_size):
            try:
                conn = self._create_connection()
                if conn:
                    self.available_connections.put(conn, block=False)
            except queue.Full:
                break
    
    def _create_connection(self) -> Optional[PooledConnection]:
        """Crea una nueva conexión SQLite optimizada."""
        try:
            # ⚡ OPTIMIZACIÓN: Configuración de conexión para concurrencia
            connection = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,  # Timeout largo para operaciones concurrentes
                check_same_thread=False,  # Permitir uso en múltiples threads
                isolation_level=None  # Autocommit mode para mejor performance
            )
            
            # ⚡ OPTIMIZACIÓN: Configuraciones de performance
            cursor = connection.cursor()
            
            # WAL mode para mejor concurrencia
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Configuraciones de performance
            cursor.execute("PRAGMA synchronous=NORMAL")  # Balance entre performance y seguridad
            cursor.execute("PRAGMA cache_size=10000")     # Cache de 10MB
            cursor.execute("PRAGMA temp_store=MEMORY")    # Tablas temporales en memoria
            cursor.execute("PRAGMA mmap_size=268435456")  # Memory-mapped I/O (256MB)
            
            cursor.close()
            
            with self.lock:
                self.connection_counter += 1
                pool_id = self.connection_counter
                
                pooled_conn = PooledConnection(connection, pool_id)
                self.all_connections[pool_id] = pooled_conn
                self.stats['connections_created'] += 1
                self.stats['active_connections'] += 1
                
            self.logger.debug(f"🔗 Conexión creada: #{pool_id}")
            return pooled_conn
            
        except Exception as e:
            self.logger.error(f"❌ Error creando conexión: {e}")
            return None
    
    @contextlib.contextmanager
    def get_connection(self, timeout: float = 5.0) -> ContextManager[sqlite3.Connection]:
        """
        ⚡ Context manager para obtener conexión del pool.
        
        Args:
            timeout: Timeout para obtener conexión
            
        Yields:
            Conexión SQLite lista para usar
        """
        start_time = time.time()
        pooled_conn = None
        
        try:
            self.stats['total_requests'] += 1
            
            # 1. Intentar obtener conexión del pool
            try:
                pooled_conn = self.available_connections.get(timeout=timeout)
                self.stats['pool_hits'] += 1
                self.stats['connections_reused'] += 1
                
                # Verificar salud de la conexión
                if not pooled_conn.check_health():
                    self.logger.warning(f"⚠️ Conexión #{pooled_conn.pool_id} no saludable, creando nueva")
                    self._close_connection(pooled_conn)
                    pooled_conn = self._create_connection()
                    if not pooled_conn:
                        raise Exception("No se pudo crear nueva conexión")
                
            except queue.Empty:
                # 2. Pool vacío, crear nueva conexión si es posible
                self.stats['pool_misses'] += 1
                
                with self.lock:
                    if len(self.all_connections) < self.max_pool_size:
                        pooled_conn = self._create_connection()
                    
                if not pooled_conn:
                    raise Exception(f"Pool agotado (máx: {self.max_pool_size})")
            
            # Actualizar estadísticas de tiempo
            wait_time = time.time() - start_time
            total_requests = self.stats['total_requests']
            self.stats['average_wait_time'] = (
                (self.stats['average_wait_time'] * (total_requests - 1) + wait_time) / total_requests
            )
            
            # Marcar como usada
            pooled_conn.mark_used()
            
            self.logger.debug(f"🔗 Conexión #{pooled_conn.pool_id} obtenida en {wait_time*1000:.1f}ms")
            
            # Yield la conexión SQLite
            yield pooled_conn.connection
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo conexión: {e}")
            raise
            
        finally:
            # 3. Devolver conexión al pool
            if pooled_conn:
                try:
                    # Verificar que la conexión sigue siendo válida
                    if pooled_conn.check_health():
                        self.available_connections.put(pooled_conn, timeout=1.0)
                        self.logger.debug(f"🔗 Conexión #{pooled_conn.pool_id} devuelta al pool")
                    else:
                        self.logger.warning(f"⚠️ Conexión #{pooled_conn.pool_id} dañada, eliminando del pool")
                        self._close_connection(pooled_conn)
                        
                except queue.Full:
                    # Pool lleno, cerrar conexión extra
                    self.logger.debug(f"🔗 Pool lleno, cerrando conexión #{pooled_conn.pool_id}")
                    self._close_connection(pooled_conn)
    
    def _close_connection(self, pooled_conn: PooledConnection):
        """Cierra una conexión y la remueve del pool."""
        try:
            pooled_conn.connection.close()
            
            with self.lock:
                if pooled_conn.pool_id in self.all_connections:
                    del self.all_connections[pooled_conn.pool_id]
                    self.stats['connections_closed'] += 1
                    self.stats['active_connections'] -= 1
                    
            self.logger.debug(f"🔗 Conexión #{pooled_conn.pool_id} cerrada")
            
        except Exception as e:
            self.logger.error(f"❌ Error cerrando conexión: {e}")
    
    def execute_query(self, query: str, params: tuple = None, fetch: str = None) -> Any:
        """
        ⚡ Ejecuta query usando conexión del pool.
        
        Args:
            query: Query SQL
            params: Parámetros para el query
            fetch: Tipo de fetch ('one', 'all', 'many', None)
            
        Returns:
            Resultado del query
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch == 'one':
                result = cursor.fetchone()
            elif fetch == 'all':
                result = cursor.fetchall()
            elif fetch == 'many':
                result = cursor.fetchmany()
            else:
                result = cursor.rowcount
            
            cursor.close()
            return result
    
    def execute_many(self, query: str, params_list: list) -> int:
        """
        ⚡ Ejecuta múltiples queries usando conexión del pool.
        
        Args:
            query: Query SQL
            params_list: Lista de parámetros
            
        Returns:
            Número de filas afectadas
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            rowcount = cursor.rowcount
            cursor.close()
            return rowcount
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del pool."""
        with self.lock:
            pool_utilization = (len(self.all_connections) - self.available_connections.qsize()) / len(self.all_connections) if self.all_connections else 0
            
            return {
                **self.stats,
                'pool_size': len(self.all_connections),
                'available_connections': self.available_connections.qsize(),
                'pool_utilization': pool_utilization,
                'hit_rate': (self.stats['pool_hits'] / self.stats['total_requests']) if self.stats['total_requests'] > 0 else 0
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Realiza chequeo de salud del pool."""
        healthy_connections = 0
        unhealthy_connections = 0
        
        with self.lock:
            for pooled_conn in self.all_connections.values():
                if pooled_conn.check_health():
                    healthy_connections += 1
                else:
                    unhealthy_connections += 1
        
        return {
            'healthy_connections': healthy_connections,
            'unhealthy_connections': unhealthy_connections,
            'total_connections': len(self.all_connections),
            'pool_healthy': unhealthy_connections == 0
        }
    
    def cleanup_connections(self):
        """Limpia conexiones viejas o no utilizadas."""
        current_time = datetime.now()
        connections_to_close = []
        
        with self.lock:
            for pooled_conn in self.all_connections.values():
                # Cerrar conexiones muy viejas (más de 1 hora sin uso)
                time_since_use = (current_time - pooled_conn.last_used).seconds
                if time_since_use > 3600:  # 1 hora
                    connections_to_close.append(pooled_conn)
        
        for pooled_conn in connections_to_close:
            self.logger.info(f"🧹 Limpiando conexión vieja #{pooled_conn.pool_id}")
            self._close_connection(pooled_conn)
        
        return len(connections_to_close)
    
    def close_all(self):
        """Cierra todas las conexiones del pool."""
        self.logger.info("🛑 Cerrando todas las conexiones del pool")
        
        with self.lock:
            # Cerrar todas las conexiones
            for pooled_conn in list(self.all_connections.values()):
                self._close_connection(pooled_conn)
            
            # Limpiar cola
            while not self.available_connections.empty():
                try:
                    self.available_connections.get_nowait()
                except queue.Empty:
                    break
        
        self.logger.info("✅ Todas las conexiones cerradas")


class PoolManager:
    """⚡ Manager singleton para pools de conexiones."""
    
    _pools = {}
    _lock = threading.Lock()
    
    @classmethod
    def get_pool(cls, db_path: str, pool_size: int = 5, max_pool_size: int = 10) -> SQLiteConnectionPool:
        """
        Obtiene o crea pool de conexiones para una BD.
        
        Args:
            db_path: Ruta a la base de datos
            pool_size: Tamaño inicial del pool
            max_pool_size: Tamaño máximo del pool
            
        Returns:
            Pool de conexiones
        """
        db_key = str(Path(db_path).resolve())
        
        with cls._lock:
            if db_key not in cls._pools:
                cls._pools[db_key] = SQLiteConnectionPool(db_path, pool_size, max_pool_size)
                logger.info(f"🔗 Nuevo pool creado para {db_key}")
            
            return cls._pools[db_key]
    
    @classmethod
    def close_all_pools(cls):
        """Cierra todos los pools de conexiones."""
        with cls._lock:
            for db_key, pool in cls._pools.items():
                logger.info(f"🛑 Cerrando pool para {db_key}")
                pool.close_all()
            
            cls._pools.clear()
            logger.info("✅ Todos los pools cerrados")
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict]:
        """Obtiene estadísticas de todos los pools."""
        with cls._lock:
            return {db_key: pool.get_stats() for db_key, pool in cls._pools.items()}