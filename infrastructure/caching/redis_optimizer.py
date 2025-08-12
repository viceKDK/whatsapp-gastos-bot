"""
Redis Cache Optimizer - FASE 5.2
⚡ Optimizaciones avanzadas para el cache distribuido Redis

Mejoras esperadas: 15% adicional en hit rate + gestión inteligente de memoria
"""

import asyncio
import threading
import time
import json
import statistics
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import hashlib

from shared.logger import get_logger
from shared.metrics import get_metrics_collector
from infrastructure.caching.redis_cache import DistributedRedisCache


logger = get_logger(__name__)


class CacheStrategy(Enum):
    """Estrategias de caching inteligente."""
    LRU = "lru"                    # Least Recently Used
    LFU = "lfu"                    # Least Frequently Used
    ADAPTIVE = "adaptive"          # Adaptivo basado en patrones
    PREDICTIVE = "predictive"      # Predictivo basado en uso


@dataclass
class CacheUsagePattern:
    """Patrón de uso de una clave de cache."""
    key: str
    namespace: str
    access_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)
    access_frequency: float = 0.0  # Accesos por hora
    hit_ratio: float = 0.0
    memory_size_bytes: int = 0
    ttl_optimal: int = 3600
    
    # Ventana deslizante de accesos
    access_timestamps: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update_access(self):
        """Actualiza métricas de acceso."""
        now = datetime.now()
        self.last_access = now
        self.access_count += 1
        
        # Actualizar ventana de timestamps
        self.access_timestamps.append(time.time())
        
        # Calcular frecuencia de acceso
        if len(self.access_timestamps) > 1:
            time_window = self.access_timestamps[-1] - self.access_timestamps[0]
            if time_window > 0:
                self.access_frequency = (len(self.access_timestamps) / time_window) * 3600  # Por hora
    
    @property
    def priority_score(self) -> float:
        """Score de prioridad para decisiones de eviction."""
        # Combinar frecuencia, recencia y hit ratio
        recency_score = max(0, 100 - (time.time() - self.access_timestamps[-1] if self.access_timestamps else 0) / 60)  # Últimos 100 minutos
        frequency_score = min(100, self.access_frequency * 10)  # Normalizar
        hit_score = self.hit_ratio
        
        return (recency_score * 0.3 + frequency_score * 0.5 + hit_score * 0.2)
    
    @property
    def is_hot_data(self) -> bool:
        """Si los datos son 'calientes' (acceso frecuente)."""
        return self.access_frequency > 10  # Más de 10 accesos/hora


class IntelligentCacheOptimizer:
    """⚡ Optimizador inteligente para cache Redis distribuido."""
    
    def __init__(self, 
                 redis_cache: DistributedRedisCache,
                 strategy: CacheStrategy = CacheStrategy.ADAPTIVE,
                 memory_threshold_mb: float = 256,
                 optimization_interval: int = 300):  # 5 minutos
        """
        Inicializa optimizador de cache.
        
        Args:
            redis_cache: Instancia del cache Redis
            strategy: Estrategia de optimización
            memory_threshold_mb: Umbral de memoria para triggers
            optimization_interval: Intervalo de optimización en segundos
        """
        self.redis_cache = redis_cache
        self.strategy = strategy
        self.memory_threshold_mb = memory_threshold_mb
        self.optimization_interval = optimization_interval
        
        # Patrones de uso
        self.usage_patterns: Dict[str, CacheUsagePattern] = {}
        
        # Métricas de optimización
        self.optimization_stats = {
            'total_optimizations': 0,
            'keys_evicted': 0,
            'memory_saved_mb': 0.0,
            'hit_rate_improvement': 0.0,
            'last_optimization': None
        }
        
        # Workers de monitoreo
        self.monitoring_active = False
        self.optimization_thread: Optional[threading.Thread] = None
        
        # Cache de predicciones
        self.predicted_keys: Set[str] = set()
        
        self.logger = logger
        self.metrics_collector = get_metrics_collector()
        
        self.logger.info(f"IntelligentCacheOptimizer inicializado - Estrategia: {strategy.value}")
    
    def start_optimization(self):
        """Inicia optimización automática del cache."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.optimization_thread = threading.Thread(
            target=self._optimization_loop,
            daemon=True
        )
        self.optimization_thread.start()
        
        self.logger.info("🚀 Cache optimization iniciado")
    
    def stop_optimization(self):
        """Detiene la optimización automática."""
        self.monitoring_active = False
        if self.optimization_thread:
            self.optimization_thread.join(timeout=10)
        
        self.logger.info("🛑 Cache optimization detenido")
    
    def _optimization_loop(self):
        """Loop principal de optimización."""
        while self.monitoring_active:
            try:
                # Ejecutar ciclo de optimización
                self._run_optimization_cycle()
                
                # Esperar siguiente intervalo
                time.sleep(self.optimization_interval)
                
            except Exception as e:
                self.logger.error(f"Error en optimization loop: {e}")
                time.sleep(60)  # Esperar más tiempo en caso de error
    
    def _run_optimization_cycle(self):
        """Ejecuta un ciclo completo de optimización."""
        self.logger.debug("🔄 Ejecutando ciclo de optimización...")
        
        # 1. Analizar uso de memoria
        memory_stats = self.redis_cache.get_cache_stats()
        current_memory_mb = memory_stats.get('redis_memory_mb', 0)
        
        # 2. Recolectar patrones de uso
        self._collect_usage_patterns()
        
        # 3. Decidir si optimizar
        should_optimize = self._should_run_optimization(current_memory_mb)
        
        if should_optimize:
            # 4. Ejecutar optimización
            optimized = self._execute_optimization_strategy()
            
            if optimized:
                self.optimization_stats['total_optimizations'] += 1
                self.optimization_stats['last_optimization'] = datetime.now().isoformat()
                
                self.logger.info(f"✅ Ciclo de optimización completado - Memoria: {current_memory_mb:.1f}MB")
        
        # 5. Predictive pre-loading si está habilitado
        if self.strategy == CacheStrategy.PREDICTIVE:
            self._predictive_preload()
        
        # 6. Registrar métricas
        self._record_optimization_metrics(current_memory_mb)
    
    def _collect_usage_patterns(self):
        """Recolecta patrones de uso del cache."""
        try:
            # Obtener estadísticas de namespaces
            cache_stats = self.redis_cache.get_cache_stats()
            namespaces = cache_stats.get('namespaces', {})
            
            for namespace, key_count in namespaces.items():
                # Analizar claves en este namespace
                self._analyze_namespace_patterns(namespace)
                
        except Exception as e:
            self.logger.error(f"Error recolectando patrones de uso: {e}")
    
    def _analyze_namespace_patterns(self, namespace: str):
        """Analiza patrones de uso de un namespace."""
        try:
            # Obtener claves del namespace (limitado para performance)
            keys = self.redis_cache.get_keys_by_pattern(namespace, "*")[:100]
            
            for key in keys:
                full_key = f"{namespace}:{key}"
                
                if full_key not in self.usage_patterns:
                    # Crear nuevo patrón
                    self.usage_patterns[full_key] = CacheUsagePattern(
                        key=key,
                        namespace=namespace
                    )
                
                # Simular acceso (en implementación real, esto se haría en cada get/set)
                pattern = self.usage_patterns[full_key]
                pattern.update_access()
                
        except Exception as e:
            self.logger.error(f"Error analizando namespace {namespace}: {e}")
    
    def _should_run_optimization(self, current_memory_mb: float) -> bool:
        """Determina si debe ejecutar optimización."""
        # Criterios para optimización
        memory_pressure = current_memory_mb > self.memory_threshold_mb
        time_since_last = True  # Placeholder - verificar tiempo desde última optimización
        
        return memory_pressure or time_since_last
    
    def _execute_optimization_strategy(self) -> bool:
        """Ejecuta la estrategia de optimización configurada."""
        if self.strategy == CacheStrategy.LRU:
            return self._optimize_lru()
        elif self.strategy == CacheStrategy.LFU:
            return self._optimize_lfu()
        elif self.strategy == CacheStrategy.ADAPTIVE:
            return self._optimize_adaptive()
        elif self.strategy == CacheStrategy.PREDICTIVE:
            return self._optimize_predictive()
        
        return False
    
    def _optimize_lru(self) -> bool:
        """Optimización LRU - elimina claves menos recientes."""
        self.logger.debug("🗑️ Ejecutando optimización LRU...")
        
        # Ordenar patrones por recencia
        sorted_patterns = sorted(
            self.usage_patterns.values(),
            key=lambda p: p.last_access
        )
        
        # Eliminar 10% menos recientes
        to_evict = sorted_patterns[:max(1, len(sorted_patterns) // 10)]
        evicted_count = 0
        
        for pattern in to_evict:
            if self.redis_cache.delete(pattern.namespace, pattern.key):
                evicted_count += 1
                del self.usage_patterns[f"{pattern.namespace}:{pattern.key}"]
        
        self.optimization_stats['keys_evicted'] += evicted_count
        return evicted_count > 0
    
    def _optimize_lfu(self) -> bool:
        """Optimización LFU - elimina claves menos frecuentes."""
        self.logger.debug("📊 Ejecutando optimización LFU...")
        
        # Ordenar por frecuencia de acceso
        sorted_patterns = sorted(
            self.usage_patterns.values(),
            key=lambda p: p.access_frequency
        )
        
        # Eliminar 10% menos frecuentes
        to_evict = sorted_patterns[:max(1, len(sorted_patterns) // 10)]
        evicted_count = 0
        
        for pattern in to_evict:
            if pattern.access_frequency < 1:  # Menos de 1 acceso/hora
                if self.redis_cache.delete(pattern.namespace, pattern.key):
                    evicted_count += 1
                    del self.usage_patterns[f"{pattern.namespace}:{pattern.key}"]
        
        self.optimization_stats['keys_evicted'] += evicted_count
        return evicted_count > 0
    
    def _optimize_adaptive(self) -> bool:
        """Optimización adaptiva - combina múltiples criterios."""
        self.logger.debug("🎯 Ejecutando optimización adaptiva...")
        
        # Ordenar por score de prioridad (menor = candidato a eviction)
        sorted_patterns = sorted(
            self.usage_patterns.values(),
            key=lambda p: p.priority_score
        )
        
        evicted_count = 0
        memory_saved = 0.0
        
        for pattern in sorted_patterns[:20]:  # Máximo 20 claves
            # Criterios múltiples para eviction
            should_evict = (
                pattern.priority_score < 30 or  # Score muy bajo
                (pattern.access_frequency < 0.5 and  # Poco frecuente
                 (datetime.now() - pattern.last_access).hours > 24)  # Y no accedido en 24h
            )
            
            if should_evict:
                if self.redis_cache.delete(pattern.namespace, pattern.key):
                    evicted_count += 1
                    memory_saved += pattern.memory_size_bytes / 1024 / 1024  # MB
                    del self.usage_patterns[f"{pattern.namespace}:{pattern.key}"]
        
        self.optimization_stats['keys_evicted'] += evicted_count
        self.optimization_stats['memory_saved_mb'] += memory_saved
        
        return evicted_count > 0
    
    def _optimize_predictive(self) -> bool:
        """Optimización predictiva - basada en patrones de uso."""
        self.logger.debug("🔮 Ejecutando optimización predictiva...")
        
        # Identificar patrones de uso predecibles
        predictable_patterns = []
        
        for pattern in self.usage_patterns.values():
            if len(pattern.access_timestamps) > 10:  # Suficiente historia
                # Analizar periodicidad de acceso
                timestamps = list(pattern.access_timestamps)
                intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
                
                if len(intervals) > 5:
                    avg_interval = statistics.mean(intervals)
                    interval_std = statistics.stdev(intervals)
                    
                    # Si el patrón es regular (baja desviación estándar)
                    if interval_std < avg_interval * 0.3:
                        predictable_patterns.append((pattern, avg_interval))
        
        # Pre-cargar datos predecibles
        preloaded = 0
        for pattern, interval in predictable_patterns:
            # Lógica de pre-carga basada en predicción
            next_access_time = pattern.access_timestamps[-1] + interval
            
            if time.time() + 300 >= next_access_time:  # Próximo acceso en 5 minutos
                # Marcar para pre-carga (en implementación real, se pre-cargarían los datos)
                self.predicted_keys.add(f"{pattern.namespace}:{pattern.key}")
                preloaded += 1
        
        return preloaded > 0
    
    def _predictive_preload(self):
        """Pre-carga predictiva de claves."""
        if not self.predicted_keys:
            return
        
        # Simular pre-carga de claves predichas
        preloaded = len(self.predicted_keys)
        self.predicted_keys.clear()
        
        if preloaded > 0:
            self.logger.debug(f"🔮 Pre-carga predictiva: {preloaded} claves")
    
    def _record_optimization_metrics(self, current_memory_mb: float):
        """Registra métricas de optimización."""
        try:
            # Métricas básicas
            self.metrics_collector.record_custom_metric(
                'redis_optimizer_memory_mb',
                current_memory_mb
            )
            
            self.metrics_collector.record_custom_metric(
                'redis_optimizer_tracked_patterns',
                len(self.usage_patterns)
            )
            
            self.metrics_collector.record_custom_metric(
                'redis_optimizer_total_optimizations',
                self.optimization_stats['total_optimizations']
            )
            
            # Calcular hit rate mejorado
            if self.usage_patterns:
                avg_hit_ratio = statistics.mean(p.hit_ratio for p in self.usage_patterns.values())
                self.metrics_collector.record_custom_metric(
                    'redis_optimizer_avg_hit_ratio',
                    avg_hit_ratio
                )
            
        except Exception as e:
            self.logger.error(f"Error registrando métricas de optimización: {e}")
    
    def track_cache_access(self, namespace: str, key: str, hit: bool):
        """
        ⚡ Trackea acceso al cache para análisis de patrones.
        
        Args:
            namespace: Namespace del cache
            key: Clave accedida
            hit: Si fue un hit o miss
        """
        full_key = f"{namespace}:{key}"
        
        if full_key not in self.usage_patterns:
            self.usage_patterns[full_key] = CacheUsagePattern(
                key=key,
                namespace=namespace
            )
        
        pattern = self.usage_patterns[full_key]
        pattern.update_access()
        
        # Actualizar hit ratio
        if hit:
            pattern.hit_ratio = min(100, pattern.hit_ratio * 0.9 + 10)  # Weighted average
        else:
            pattern.hit_ratio = max(0, pattern.hit_ratio * 0.9)
    
    def suggest_ttl_optimization(self, namespace: str, key: str) -> int:
        """
        Sugiere TTL óptimo basado en patrones de uso.
        
        Args:
            namespace: Namespace del cache
            key: Clave del cache
            
        Returns:
            TTL sugerido en segundos
        """
        full_key = f"{namespace}:{key}"
        
        if full_key in self.usage_patterns:
            pattern = self.usage_patterns[full_key]
            
            # TTL basado en frecuencia de acceso
            if pattern.access_frequency > 10:  # Muy frecuente
                return 7200  # 2 horas
            elif pattern.access_frequency > 1:  # Frecuente
                return 3600  # 1 hora
            else:  # Poco frecuente
                return 1800  # 30 minutos
        
        return 3600  # TTL por defecto
    
    def get_hot_keys(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las claves más 'calientes' (acceso frecuente).
        
        Args:
            limit: Número máximo de claves a retornar
            
        Returns:
            Lista de claves calientes con métricas
        """
        hot_patterns = [p for p in self.usage_patterns.values() if p.is_hot_data]
        hot_patterns.sort(key=lambda p: p.priority_score, reverse=True)
        
        return [{
            'key': pattern.key,
            'namespace': pattern.namespace,
            'access_frequency': pattern.access_frequency,
            'hit_ratio': pattern.hit_ratio,
            'priority_score': pattern.priority_score,
            'last_access': pattern.last_access.isoformat()
        } for pattern in hot_patterns[:limit]]
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Genera reporte completo de optimización."""
        # Análisis de patrones
        if self.usage_patterns:
            total_patterns = len(self.usage_patterns)
            hot_keys = len([p for p in self.usage_patterns.values() if p.is_hot_data])
            avg_frequency = statistics.mean(p.access_frequency for p in self.usage_patterns.values())
            avg_hit_ratio = statistics.mean(p.hit_ratio for p in self.usage_patterns.values())
        else:
            total_patterns = hot_keys = avg_frequency = avg_hit_ratio = 0
        
        # Distribución por namespace
        namespace_distribution = defaultdict(int)
        for pattern in self.usage_patterns.values():
            namespace_distribution[pattern.namespace] += 1
        
        return {
            'optimization_stats': self.optimization_stats,
            'pattern_analysis': {
                'total_patterns': total_patterns,
                'hot_keys_count': hot_keys,
                'average_frequency': avg_frequency,
                'average_hit_ratio': avg_hit_ratio,
                'namespace_distribution': dict(namespace_distribution)
            },
            'strategy': self.strategy.value,
            'monitoring_active': self.monitoring_active,
            'memory_threshold_mb': self.memory_threshold_mb,
            'hot_keys': self.get_hot_keys(5),
            'generated_at': datetime.now().isoformat()
        }


class RedisCacheWrapper:
    """⚡ Wrapper optimizado para Redis cache con tracking automático."""
    
    def __init__(self, redis_cache: DistributedRedisCache, enable_optimization: bool = True):
        """
        Inicializa wrapper optimizado.
        
        Args:
            redis_cache: Instancia del cache Redis
            enable_optimization: Si habilitar optimización automática
        """
        self.redis_cache = redis_cache
        self.optimizer = IntelligentCacheOptimizer(redis_cache) if enable_optimization else None
        
        if self.optimizer:
            self.optimizer.start_optimization()
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get optimizado con tracking."""
        result = self.redis_cache.get(namespace, key)
        
        # Track acceso
        if self.optimizer:
            self.optimizer.track_cache_access(namespace, key, result is not None)
        
        return result
    
    def set(self, namespace: str, key: str, value: Any, ttl: Optional[int] = None, **kwargs) -> bool:
        """Set optimizado con TTL inteligente."""
        # Sugerir TTL óptimo si no se especifica
        if ttl is None and self.optimizer:
            ttl = self.optimizer.suggest_ttl_optimization(namespace, key)
        
        return self.redis_cache.set(namespace, key, value, ttl, **kwargs)
    
    def delete(self, namespace: str, key: str) -> bool:
        """Delete con limpieza de patrones."""
        result = self.redis_cache.delete(namespace, key)
        
        # Limpiar patrón de uso
        if self.optimizer and result:
            full_key = f"{namespace}:{key}"
            if full_key in self.optimizer.usage_patterns:
                del self.optimizer.usage_patterns[full_key]
        
        return result
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Obtiene reporte de optimización."""
        if self.optimizer:
            return self.optimizer.get_optimization_report()
        return {'optimization_enabled': False}
    
    def stop_optimization(self):
        """Detiene optimización automática."""
        if self.optimizer:
            self.optimizer.stop_optimization()


# Factory function para cache optimizado
def create_optimized_redis_cache(host: str = 'localhost', 
                                port: int = 6379, 
                                db: int = 0,
                                password: Optional[str] = None,
                                enable_optimization: bool = True) -> RedisCacheWrapper:
    """
    Crea instancia optimizada del cache Redis.
    
    Args:
        host: Host de Redis
        port: Puerto de Redis
        db: Base de datos Redis
        password: Contraseña de Redis
        enable_optimization: Si habilitar optimización automática
        
    Returns:
        Wrapper optimizado del cache Redis
    """
    redis_cache = DistributedRedisCache(host, port, db, password)
    return RedisCacheWrapper(redis_cache, enable_optimization)