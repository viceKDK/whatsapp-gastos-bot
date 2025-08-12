"""
Sistema de Cache Redis Distribuido - FASE 5.1

Cache distribuido usando Redis para múltiples instancias del bot,
permitiendo compartir predicciones ML y datos entre procesos.

Mejora esperada: 15% adicional por cache compartido entre instancias.
"""

import json
import pickle
import hashlib
import time
import threading
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

try:
    import redis
    from redis.connection import ConnectionPool
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

from shared.logger import get_logger
from shared.metrics import get_metrics_collector


logger = get_logger(__name__)


@dataclass
class RedisCacheEntry:
    """Entrada de cache Redis con metadata."""
    data: Any
    cached_at: float = field(default_factory=time.time)
    ttl: int = 3600  # TTL en segundos
    access_count: int = 0
    cache_type: str = "generic"
    
    def is_expired(self) -> bool:
        """Verifica si la entrada está expirada."""
        return (time.time() - self.cached_at) > self.ttl
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para Redis."""
        return {
            'data': self.data,
            'cached_at': self.cached_at,
            'ttl': self.ttl,
            'access_count': self.access_count,
            'cache_type': self.cache_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RedisCacheEntry':
        """Crea instancia desde diccionario Redis."""
        return cls(**data)


class DistributedRedisCache:
    """⚡ Sistema de cache distribuido usando Redis (15% mejora adicional)."""
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 default_ttl: int = 3600,
                 key_prefix: str = "bot_gastos",
                 max_connections: int = 10):
        """
        Inicializa cache Redis distribuido.
        
        Args:
            host: Host de Redis
            port: Puerto de Redis
            db: Base de datos Redis
            password: Contraseña de Redis
            default_ttl: TTL por defecto en segundos
            key_prefix: Prefijo para claves
            max_connections: Máximo de conexiones en pool
        """
        if not HAS_REDIS:
            raise ImportError("Redis no está disponible. Instalar con: pip install redis")
        
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        
        # Pool de conexiones Redis
        self.connection_pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={}
        )
        
        # Cliente Redis
        self.redis_client = redis.Redis(connection_pool=self.connection_pool)
        
        # Estadísticas locales
        self.local_hits = 0
        self.local_misses = 0
        self.network_errors = 0
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Métricas
        self.metrics_collector = get_metrics_collector()
        
        # Fallback cache local para casos sin conexión
        self.local_fallback: Dict[str, Any] = {}
        
        self.logger = logger
        self.logger.info(f"DistributedRedisCache inicializado - {host}:{port}/{db}")
        
        # Test de conexión
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Prueba la conexión a Redis."""
        try:
            self.redis_client.ping()
            self.logger.info("Conexión Redis establecida correctamente")
            return True
        except Exception as e:
            self.logger.warning(f"Error conectando a Redis: {e}. Usando cache local.")
            return False
    
    def _generate_key(self, namespace: str, key: str) -> str:
        """Genera clave completa de Redis."""
        return f"{self.key_prefix}:{namespace}:{key}"
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serializa datos para Redis."""
        try:
            # Intentar JSON primero (más rápido)
            if isinstance(data, (dict, list, str, int, float, bool)) or data is None:
                return json.dumps(data).encode('utf-8')
            else:
                # Usar pickle para objetos complejos
                return pickle.dumps(data)
        except Exception:
            # Fallback a pickle
            return pickle.dumps(data)
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserializa datos desde Redis."""
        try:
            # Intentar JSON primero
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Usar pickle para objetos complejos
            return pickle.loads(data)
    
    def set(self, 
            namespace: str, 
            key: str, 
            value: Any, 
            ttl: Optional[int] = None,
            cache_type: str = "generic") -> bool:
        """
        ⚡ Establece valor en cache distribuido.
        
        Args:
            namespace: Namespace del cache
            key: Clave del cache
            value: Valor a cachear
            ttl: TTL en segundos
            cache_type: Tipo de cache
            
        Returns:
            True si se cacheó exitosamente
        """
        ttl = ttl or self.default_ttl
        redis_key = self._generate_key(namespace, key)
        
        try:
            # Crear entrada de cache
            cache_entry = RedisCacheEntry(
                data=value,
                ttl=ttl,
                cache_type=cache_type
            )
            
            # Serializar
            serialized_data = self._serialize_data(cache_entry.to_dict())
            
            # Guardar en Redis con TTL
            with self.lock:
                result = self.redis_client.setex(redis_key, ttl, serialized_data)
                
                if result:
                    self.metrics_collector.record_custom_metric(
                        'redis_cache_set_success',
                        1,
                        namespace=namespace,
                        cache_type=cache_type
                    )
                    
                    self.logger.debug(f"Valor cacheado en Redis: {redis_key}")
                    return True
                else:
                    # Fallback a cache local
                    self.local_fallback[redis_key] = {
                        'data': value,
                        'cached_at': time.time(),
                        'ttl': ttl
                    }
                    return True
                    
        except Exception as e:
            self.network_errors += 1
            self.logger.error(f"Error cacheando en Redis {redis_key}: {e}")
            
            # Fallback a cache local
            self.local_fallback[redis_key] = {
                'data': value,
                'cached_at': time.time(),
                'ttl': ttl
            }
            return True
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """
        ⚡ Obtiene valor desde cache distribuido.
        
        Args:
            namespace: Namespace del cache
            key: Clave del cache
            
        Returns:
            Valor cacheado o None si no existe
        """
        redis_key = self._generate_key(namespace, key)
        
        try:
            # Intentar obtener desde Redis
            with self.lock:
                serialized_data = self.redis_client.get(redis_key)
                
                if serialized_data:
                    # Deserializar
                    cache_data = self._deserialize_data(serialized_data)
                    cache_entry = RedisCacheEntry.from_dict(cache_data)
                    
                    # Verificar expiración (doble check)
                    if not cache_entry.is_expired():
                        self.local_hits += 1
                        
                        # Actualizar contador de acceso
                        cache_entry.access_count += 1
                        updated_data = self._serialize_data(cache_entry.to_dict())
                        self.redis_client.setex(redis_key, cache_entry.ttl, updated_data)
                        
                        self.metrics_collector.record_custom_metric(
                            'redis_cache_hit',
                            1,
                            namespace=namespace
                        )
                        
                        return cache_entry.data
                    else:
                        # Eliminar expirado
                        self.redis_client.delete(redis_key)
                
                # Si no está en Redis, verificar cache local
                if redis_key in self.local_fallback:
                    local_entry = self.local_fallback[redis_key]
                    
                    if (time.time() - local_entry['cached_at']) <= local_entry['ttl']:
                        self.local_hits += 1
                        return local_entry['data']
                    else:
                        # Limpiar expirado
                        del self.local_fallback[redis_key]
                
                # Cache miss
                self.local_misses += 1
                self.metrics_collector.record_custom_metric(
                    'redis_cache_miss',
                    1,
                    namespace=namespace
                )
                
                return None
                
        except Exception as e:
            self.network_errors += 1
            self.logger.error(f"Error obteniendo desde Redis {redis_key}: {e}")
            
            # Fallback a cache local
            if redis_key in self.local_fallback:
                local_entry = self.local_fallback[redis_key]
                
                if (time.time() - local_entry['cached_at']) <= local_entry['ttl']:
                    return local_entry['data']
            
            return None
    
    def delete(self, namespace: str, key: str) -> bool:
        """
        Elimina valor del cache distribuido.
        
        Args:
            namespace: Namespace del cache
            key: Clave del cache
            
        Returns:
            True si se eliminó exitosamente
        """
        redis_key = self._generate_key(namespace, key)
        
        try:
            with self.lock:
                # Eliminar de Redis
                result = self.redis_client.delete(redis_key)
                
                # Eliminar de cache local también
                if redis_key in self.local_fallback:
                    del self.local_fallback[redis_key]
                
                return bool(result)
                
        except Exception as e:
            self.logger.error(f"Error eliminando de Redis {redis_key}: {e}")
            
            # Al menos eliminar del cache local
            if redis_key in self.local_fallback:
                del self.local_fallback[redis_key]
                return True
            
            return False
    
    def exists(self, namespace: str, key: str) -> bool:
        """
        Verifica si una clave existe en el cache.
        
        Args:
            namespace: Namespace del cache
            key: Clave del cache
            
        Returns:
            True si la clave existe
        """
        redis_key = self._generate_key(namespace, key)
        
        try:
            # Verificar en Redis
            result = self.redis_client.exists(redis_key)
            if result:
                return True
            
            # Verificar en cache local
            if redis_key in self.local_fallback:
                local_entry = self.local_fallback[redis_key]
                return (time.time() - local_entry['cached_at']) <= local_entry['ttl']
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error verificando existencia en Redis {redis_key}: {e}")
            
            # Fallback a cache local
            if redis_key in self.local_fallback:
                local_entry = self.local_fallback[redis_key]
                return (time.time() - local_entry['cached_at']) <= local_entry['ttl']
            
            return False
    
    def get_keys_by_pattern(self, namespace: str, pattern: str = "*") -> List[str]:
        """
        Obtiene claves por patrón.
        
        Args:
            namespace: Namespace del cache
            pattern: Patrón de búsqueda
            
        Returns:
            Lista de claves que coinciden
        """
        try:
            redis_pattern = self._generate_key(namespace, pattern)
            keys = self.redis_client.keys(redis_pattern)
            
            # Remover prefijo para retornar claves limpias
            prefix_len = len(f"{self.key_prefix}:{namespace}:")
            return [key.decode('utf-8')[prefix_len:] for key in keys]
            
        except Exception as e:
            self.logger.error(f"Error obteniendo claves por patrón: {e}")
            return []
    
    def flush_namespace(self, namespace: str) -> int:
        """
        Limpia todas las claves de un namespace.
        
        Args:
            namespace: Namespace a limpiar
            
        Returns:
            Número de claves eliminadas
        """
        try:
            pattern = self._generate_key(namespace, "*")
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                self.logger.info(f"Namespace '{namespace}' limpiado: {deleted} claves eliminadas")
                return deleted
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error limpiando namespace {namespace}: {e}")
            return 0
    
    def increment(self, namespace: str, key: str, amount: int = 1) -> int:
        """
        Incrementa contador distribuido.
        
        Args:
            namespace: Namespace del cache
            key: Clave del contador
            amount: Cantidad a incrementar
            
        Returns:
            Valor actualizado del contador
        """
        redis_key = self._generate_key(namespace, key)
        
        try:
            return self.redis_client.incr(redis_key, amount)
        except Exception as e:
            self.logger.error(f"Error incrementando contador {redis_key}: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache distribuido."""
        try:
            # Estadísticas de Redis
            redis_info = self.redis_client.info('memory')
            redis_used_memory = redis_info.get('used_memory', 0)
            redis_used_memory_mb = redis_used_memory / 1024 / 1024
            
            # Estadísticas generales
            total_requests = self.local_hits + self.local_misses
            hit_rate = (self.local_hits / total_requests) if total_requests > 0 else 0
            
            # Conteo de claves por namespace
            namespaces = {}
            try:
                all_keys = self.redis_client.keys(f"{self.key_prefix}:*")
                for key in all_keys:
                    key_str = key.decode('utf-8')
                    parts = key_str.split(':')
                    if len(parts) >= 3:
                        namespace = parts[1]
                        namespaces[namespace] = namespaces.get(namespace, 0) + 1
            except:
                pass
            
            return {
                'redis_connected': True,
                'redis_memory_mb': redis_used_memory_mb,
                'local_hits': self.local_hits,
                'local_misses': self.local_misses,
                'hit_rate': hit_rate,
                'network_errors': self.network_errors,
                'local_fallback_keys': len(self.local_fallback),
                'namespaces': namespaces,
                'total_redis_keys': len(all_keys) if 'all_keys' in locals() else 0
            }
            
        except Exception as e:
            return {
                'redis_connected': False,
                'error': str(e),
                'local_hits': self.local_hits,
                'local_misses': self.local_misses,
                'network_errors': self.network_errors,
                'local_fallback_keys': len(self.local_fallback)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica la salud del cache distribuido."""
        try:
            start_time = time.time()
            
            # Test básico de Redis
            test_key = f"healthcheck:{int(time.time())}"
            self.redis_client.setex(test_key, 10, "test_value")
            retrieved = self.redis_client.get(test_key)
            self.redis_client.delete(test_key)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'redis_connected': True,
                'latency_ms': latency_ms,
                'read_write_ok': retrieved == b"test_value",
                'network_errors': self.network_errors
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'redis_connected': False,
                'error': str(e),
                'network_errors': self.network_errors
            }
    
    def cleanup_expired(self) -> int:
        """Limpia entradas expiradas del cache local."""
        cleaned = 0
        current_time = time.time()
        
        expired_keys = []
        for key, entry in self.local_fallback.items():
            if (current_time - entry['cached_at']) > entry['ttl']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.local_fallback[key]
            cleaned += 1
        
        if cleaned > 0:
            self.logger.info(f"Cache local cleanup: {cleaned} entradas expiradas eliminadas")
        
        return cleaned
    
    def close(self):
        """Cierra conexiones al cache."""
        try:
            self.connection_pool.disconnect()
            self.logger.info("Conexiones Redis cerradas")
        except Exception as e:
            self.logger.error(f"Error cerrando conexiones Redis: {e}")


class RedisMLCache:
    """⚡ Cache especializado para ML usando Redis distribuido."""
    
    def __init__(self, redis_cache: DistributedRedisCache):
        """
        Inicializa cache ML con Redis.
        
        Args:
            redis_cache: Instancia de cache Redis distribuido
        """
        self.redis_cache = redis_cache
        self.namespace = "ml_predictions"
        self.logger = logger
    
    def cache_prediction(self, 
                        text: str, 
                        model_version: str, 
                        prediction: Any, 
                        confidence: float,
                        ttl: int = 3600) -> bool:
        """
        Cachea predicción ML en Redis distribuido.
        
        Args:
            text: Texto original
            model_version: Versión del modelo
            prediction: Predicción
            confidence: Confianza
            ttl: TTL en segundos
            
        Returns:
            True si se cacheó exitosamente
        """
        cache_key = self._generate_ml_key(text, model_version)
        
        cache_data = {
            'prediction': prediction,
            'confidence': confidence,
            'text_hash': hashlib.md5(text.encode()).hexdigest()[:16],
            'model_version': model_version
        }
        
        # TTL inteligente basado en confianza  
        adaptive_ttl = max(600, int(ttl * (confidence / 100) * 2))  # Min 10 min, max basado en confianza
        final_ttl = adaptive_ttl if ttl == 3600 else ttl  # Usar adaptivo solo si es TTL por defecto
        
        return self.redis_cache.set(
            self.namespace, 
            cache_key, 
            cache_data, 
            ttl=final_ttl,
            cache_type="ml_prediction"
        )
    
    def get_prediction(self, text: str, model_version: str) -> Optional[Tuple[Any, float]]:
        """
        Obtiene predicción cacheada desde Redis.
        
        Args:
            text: Texto original
            model_version: Versión del modelo
            
        Returns:
            Tupla (predicción, confianza) o None si no existe
        """
        cache_key = self._generate_ml_key(text, model_version)
        
        cached_data = self.redis_cache.get(self.namespace, cache_key)
        
        if cached_data:
            return cached_data['prediction'], cached_data['confidence']
        
        return None
    
    def _generate_ml_key(self, text: str, model_version: str) -> str:
        """Genera clave de cache para predicciones ML."""
        # Normalizar texto
        normalized = text.lower().strip()[:500]
        
        # Hash combinado
        content = f"{model_version}:{normalized}"
        return hashlib.md5(content.encode()).hexdigest()[:16]


# Instancia global del cache distribuido
_distributed_cache_instance: Optional[DistributedRedisCache] = None

def get_distributed_cache(host: str = 'localhost', 
                         port: int = 6379,
                         db: int = 0,
                         password: Optional[str] = None) -> DistributedRedisCache:
    """Obtiene instancia singleton del cache distribuido."""
    global _distributed_cache_instance
    
    if _distributed_cache_instance is None:
        _distributed_cache_instance = DistributedRedisCache(
            host=host,
            port=port,
            db=db,
            password=password
        )
    
    return _distributed_cache_instance