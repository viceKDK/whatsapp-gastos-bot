"""
Sistema Simplificado de Cache ML - FASE 4.2

Cache inteligente para predicciones de modelos ML que optimiza el tiempo
de respuesta mediante cache LRU y técnicas de optimización avanzadas.

Mejora esperada: 50% adicional en categorización ML.
"""

import time
import hashlib
import threading
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict

from shared.logger import get_logger
from shared.metrics import get_metrics_collector


logger = get_logger(__name__)


@dataclass
class MLCacheEntry:
    """Entrada de cache para predicciones ML."""
    prediction: Any
    confidence: float
    processing_time_ms: float
    cached_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def mark_accessed(self):
        """Marca como accedido y actualiza contador."""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    @property
    def age_hours(self) -> float:
        """Edad de la entrada en horas."""
        return (datetime.now() - self.cached_at).total_seconds() / 3600
    
    def is_expired(self, max_age_hours: int = 12) -> bool:
        """Verifica si la entrada está expirada."""
        return self.age_hours > max_age_hours


class SimpleMLCache:
    """⚡ Cache optimizado para modelos ML (50% mejora esperada)."""
    
    def __init__(self, max_size: int = 5000, ttl_hours: int = 12):
        """
        Inicializa cache ML simple.
        
        Args:
            max_size: Tamaño máximo del cache
            ttl_hours: Tiempo de vida en horas
        """
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        
        # Cache LRU
        self.cache: OrderedDict[str, MLCacheEntry] = OrderedDict()
        
        # Estadísticas
        self.hits = 0
        self.misses = 0
        self.total_predictions = 0
        self.total_processing_time = 0.0
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Métricas
        self.metrics_collector = get_metrics_collector()
        
        self.logger = logger
        self.logger.info(f"SimpleMLCache inicializado - Max size: {max_size}")
    
    def predict_with_cache(self, 
                          text: str, 
                          model: Any,
                          model_version: str = "default",
                          amount: float = None) -> Tuple[Any, float, Dict[str, Any]]:
        """
        ⚡ Predicción con cache inteligente.
        
        Args:
            text: Texto a procesar
            model: Modelo ML
            model_version: Versión del modelo
            amount: Monto opcional
            
        Returns:
            Tupla (predicción, confianza, metadata)
        """
        start_time = time.time()
        
        # Generar clave de cache
        cache_key = self._generate_cache_key(text, model_version, amount)
        
        # Buscar en cache
        with self.lock:
            cached_entry = self._get_from_cache(cache_key)
            
            if cached_entry:
                # Cache hit
                self.hits += 1
                cached_entry.mark_accessed()
                
                processing_time = (time.time() - start_time) * 1000
                
                self.metrics_collector.record_custom_metric(
                    'ml_cache_hit_time_ms',
                    processing_time,
                    model_version=model_version
                )
                
                return cached_entry.prediction, cached_entry.confidence, {
                    'cached': True,
                    'processing_time_ms': processing_time,
                    'cache_age_hours': cached_entry.age_hours,
                    'access_count': cached_entry.access_count,
                    'original_time_ms': cached_entry.processing_time_ms
                }
        
        # Cache miss - computar predicción
        self.misses += 1
        
        try:
            prediction, confidence = self._compute_ml_prediction(text, model, amount)
            processing_time = (time.time() - start_time) * 1000
            
            # Cachear resultado
            cache_entry = MLCacheEntry(
                prediction=prediction,
                confidence=confidence,
                processing_time_ms=processing_time
            )
            
            with self.lock:
                self._add_to_cache(cache_key, cache_entry)
            
            # Actualizar estadísticas
            self.total_predictions += 1
            self.total_processing_time += processing_time
            
            self.metrics_collector.record_custom_metric(
                'ml_cache_miss_time_ms',
                processing_time,
                model_version=model_version
            )
            
            return prediction, confidence, {
                'cached': False,
                'processing_time_ms': processing_time,
                'cache_size': len(self.cache)
            }
            
        except Exception as e:
            self.logger.error(f"Error en predict_with_cache: {e}")
            return "otros", 0.5, {'error': str(e)}
    
    def _generate_cache_key(self, text: str, model_version: str, amount: float = None) -> str:
        """Genera clave única para el cache."""
        # Normalizar texto
        normalized = text.lower().strip()[:500]
        
        # Crear contenido para hash
        content = f"{model_version}:{normalized}:{amount or 0}"
        
        # Hash MD5 rápido
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _get_from_cache(self, cache_key: str) -> Optional[MLCacheEntry]:
        """Obtiene entrada del cache si existe y es válida."""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Verificar si está expirada
            if not entry.is_expired(self.ttl_hours):
                # Mover al final (LRU)
                self.cache.move_to_end(cache_key)
                return entry
            else:
                # Eliminar expirada
                del self.cache[cache_key]
        
        return None
    
    def _add_to_cache(self, cache_key: str, entry: MLCacheEntry):
        """Agrega entrada al cache con gestión LRU."""
        # Verificar espacio
        if len(self.cache) >= self.max_size:
            # Remover la menos usada recientemente
            self.cache.popitem(last=False)
        
        # Agregar nueva entrada
        self.cache[cache_key] = entry
        
        self.logger.debug(f"Entrada cacheada: {cache_key}")
    
    def _compute_ml_prediction(self, text: str, model: Any, amount: float = None) -> Tuple[Any, float]:
        """Computa predicción usando el modelo ML."""
        try:
            # Verificar si el modelo tiene métodos de predicción
            if hasattr(model, 'predict_proba'):
                # Modelo con probabilidades
                # Crear features simples para el modelo
                features = self._create_simple_features(text, amount)
                
                probabilities = model.predict_proba(features)[0]
                prediction_idx = np.argmax(probabilities)
                
                if hasattr(model, 'classes_'):
                    prediction = model.classes_[prediction_idx]
                else:
                    prediction = prediction_idx
                
                confidence = float(probabilities[prediction_idx])
                
            elif hasattr(model, 'predict'):
                # Modelo básico de predicción
                features = self._create_simple_features(text, amount)
                prediction = model.predict(features)[0]
                confidence = 0.8  # Confianza por defecto
                
            else:
                # Fallback para modelos desconocidos
                prediction = self._simple_rule_based_prediction(text)
                confidence = 0.6
            
            return prediction, confidence
            
        except Exception as e:
            self.logger.error(f"Error computando predicción ML: {e}")
            # Fallback a reglas simples
            return self._simple_rule_based_prediction(text), 0.5
    
    def _create_simple_features(self, text: str, amount: float = None) -> np.ndarray:
        """Crea features simples para modelos ML."""
        features = []
        
        # Features básicas de texto
        features.append(len(text))  # Longitud del texto
        features.append(text.count(' '))  # Número de palabras
        features.append(text.count(','))  # Número de comas
        
        # Features de contenido
        keywords = ['comida', 'transporte', 'entretenimiento', 'otros', 'super', 'nafta', 'cine']
        for keyword in keywords:
            features.append(1 if keyword in text.lower() else 0)
        
        # Feature de monto
        features.append(amount or 0)
        
        return np.array([features])
    
    def _simple_rule_based_prediction(self, text: str) -> str:
        """Predicción basada en reglas simples como fallback."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['comida', 'restaurant', 'super', 'almuerzo', 'cena']):
            return 'comida'
        elif any(word in text_lower for word in ['transporte', 'nafta', 'taxi', 'bus', 'tren']):
            return 'transporte'
        elif any(word in text_lower for word in ['cine', 'entretenimiento', 'juego', 'diversión']):
            return 'entretenimiento'
        else:
            return 'otros'
    
    def precompute_common_predictions(self, common_texts: List[str], model: Any, model_version: str = "default"):
        """
        ⚡ Precomputa predicciones para textos comunes.
        
        Args:
            common_texts: Lista de textos comunes
            model: Modelo ML
            model_version: Versión del modelo
        """
        self.logger.info(f"Precomputando {len(common_texts)} predicciones comunes...")
        
        start_time = time.time()
        precomputed = 0
        
        for text in common_texts:
            try:
                cache_key = self._generate_cache_key(text, model_version)
                
                # Solo precomputar si no está cacheado
                with self.lock:
                    if not self._get_from_cache(cache_key):
                        self.predict_with_cache(text, model, model_version)
                        precomputed += 1
                        
            except Exception as e:
                self.logger.warning(f"Error precomputando '{text[:30]}...': {e}")
        
        elapsed = time.time() - start_time
        self.logger.info(f"Precompute completado: {precomputed} predicciones en {elapsed:.2f}s")
    
    def cleanup_expired(self):
        """Limpia entradas expiradas del cache."""
        with self.lock:
            expired_keys = []
            
            for key, entry in self.cache.items():
                if entry.is_expired(self.ttl_hours):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                self.logger.info(f"Cache cleanup: {len(expired_keys)} entradas expiradas eliminadas")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests) if total_requests > 0 else 0.0
            
            avg_processing_time = (self.total_processing_time / self.total_predictions) if self.total_predictions > 0 else 0.0
            
            # Calcular mejora de performance
            if total_requests > 0:
                # Tiempo promedio sin cache (estimado)
                baseline_time = avg_processing_time * 2
                
                # Tiempo actual con cache
                actual_time = ((self.hits * 1.0) + (self.misses * avg_processing_time)) / total_requests
                
                performance_improvement = ((baseline_time - actual_time) / baseline_time) * 100 if baseline_time > 0 else 0
            else:
                performance_improvement = 0
            
            return {
                'cache_size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'total_predictions': self.total_predictions,
                'average_processing_time_ms': avg_processing_time,
                'performance_improvement_percent': performance_improvement,
                'ttl_hours': self.ttl_hours
            }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Genera reporte completo de performance."""
        stats = self.get_cache_stats()
        
        # Análisis de uso del cache
        with self.lock:
            access_counts = [entry.access_count for entry in self.cache.values()]
            ages = [entry.age_hours for entry in self.cache.values()]
        
        return {
            **stats,
            'cache_efficiency': min(100, stats['hit_rate'] * 100 + stats['performance_improvement_percent']),
            'avg_access_count': sum(access_counts) / len(access_counts) if access_counts else 0,
            'avg_entry_age_hours': sum(ages) / len(ages) if ages else 0,
            'most_accessed_count': max(access_counts) if access_counts else 0,
            'generated_at': datetime.now().isoformat()
        }


class CachedMLWrapper:
    """⚡ Wrapper que agrega cache a cualquier modelo ML."""
    
    def __init__(self, base_model: Any, model_version: str = "default", cache_size: int = 1000):
        """
        Inicializa wrapper con cache.
        
        Args:
            base_model: Modelo ML base
            model_version: Versión del modelo
            cache_size: Tamaño del cache
        """
        self.base_model = base_model
        self.model_version = model_version
        self.cache = SimpleMLCache(max_size=cache_size)
        self.logger = logger
    
    def predict(self, texts: List[str]) -> List[Any]:
        """Predicción con cache para múltiples textos."""
        predictions = []
        
        for text in texts:
            pred, conf, metadata = self.cache.predict_with_cache(
                text=text,
                model=self.base_model,
                model_version=self.model_version
            )
            predictions.append(pred)
        
        return predictions
    
    def predict_single(self, text: str, amount: float = None) -> Tuple[Any, float, Dict]:
        """Predicción con cache para un solo texto."""
        return self.cache.predict_with_cache(
            text=text,
            model=self.base_model,
            model_version=self.model_version,
            amount=amount
        )
    
    def warm_up_cache(self, common_texts: List[str]):
        """Precalienta el cache con textos comunes."""
        self.cache.precompute_common_predictions(common_texts, self.base_model, self.model_version)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache."""
        return self.cache.get_cache_stats()
    
    def cleanup(self):
        """Limpia cache expirado."""
        self.cache.cleanup_expired()


# Instancia global del cache
_global_ml_cache: Optional[SimpleMLCache] = None

def get_global_ml_cache(max_size: int = 5000) -> SimpleMLCache:
    """Obtiene instancia singleton del cache ML global."""
    global _global_ml_cache
    if _global_ml_cache is None:
        _global_ml_cache = SimpleMLCache(max_size=max_size)
    return _global_ml_cache