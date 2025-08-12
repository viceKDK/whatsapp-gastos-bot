"""
Advanced ML Model Optimization - FASE 4.3
⚡ Optimización avanzada de modelos ML con cache inteligente y predicciones mejoradas

Mejora esperada: 20% adicional en categorización + reducción de latencia ML
"""

import asyncio
import threading
import time
import json
import pickle
import hashlib
import statistics
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import numpy as np
from abc import ABC, abstractmethod

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

from shared.logger import get_logger
from shared.metrics import get_metrics_collector


logger = get_logger(__name__)


class ModelType(Enum):
    """Tipos de modelos ML soportados."""
    SKLEARN = "sklearn"
    SIMPLE_RULES = "simple_rules"
    HYBRID = "hybrid"
    NEURAL_NETWORK = "neural_network"


class PredictionConfidence(Enum):
    """Niveles de confianza en predicciones."""
    VERY_HIGH = "very_high"    # >95%
    HIGH = "high"              # 80-95%
    MEDIUM = "medium"          # 60-80%
    LOW = "low"                # 40-60%
    VERY_LOW = "very_low"      # <40%


@dataclass
class MLPredictionResult:
    """Resultado de predicción ML con metadata."""
    prediction: Any
    confidence: float
    model_version: str
    processing_time_ms: float
    features_used: List[str]
    confidence_level: PredictionConfidence = PredictionConfidence.MEDIUM
    cache_key: Optional[str] = None
    
    def __post_init__(self):
        """Determina nivel de confianza basado en score."""
        if self.confidence >= 0.95:
            self.confidence_level = PredictionConfidence.VERY_HIGH
        elif self.confidence >= 0.80:
            self.confidence_level = PredictionConfidence.HIGH
        elif self.confidence >= 0.60:
            self.confidence_level = PredictionConfidence.MEDIUM
        elif self.confidence >= 0.40:
            self.confidence_level = PredictionConfidence.LOW
        else:
            self.confidence_level = PredictionConfidence.VERY_LOW


@dataclass
class ModelPerformanceMetrics:
    """Métricas de rendimiento de un modelo ML."""
    model_id: str
    total_predictions: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    average_processing_time: float = 0.0
    average_confidence: float = 0.0
    confidence_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Ventanas deslizantes para tracking
    recent_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    recent_confidences: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def update_prediction(self, processing_time: float, confidence: float, from_cache: bool):
        """Actualiza métricas con nueva predicción."""
        self.total_predictions += 1
        
        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            # Solo actualizar tiempos para predicciones no cacheadas
            self.recent_times.append(processing_time)
            
        self.recent_confidences.append(confidence)
        
        # Actualizar promedios
        if self.recent_times:
            self.average_processing_time = statistics.mean(self.recent_times)
        
        if self.recent_confidences:
            self.average_confidence = statistics.mean(self.recent_confidences)
    
    @property
    def cache_hit_rate(self) -> float:
        """Tasa de acierto del cache."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0
    
    @property
    def performance_score(self) -> float:
        """Score de rendimiento del modelo (0-100)."""
        # Combinar velocidad, confianza y cache hit rate
        speed_score = max(0, 100 - self.average_processing_time)  # Menos tiempo = mejor score
        confidence_score = self.average_confidence * 100
        cache_score = self.cache_hit_rate
        
        return (speed_score * 0.3 + confidence_score * 0.5 + cache_score * 0.2)


class BaseMLModel(ABC):
    """Clase base para modelos ML optimizados."""
    
    def __init__(self, model_id: str, version: str = "1.0"):
        self.model_id = model_id
        self.version = version
        self.logger = logger
    
    @abstractmethod
    def predict(self, features: Dict[str, Any]) -> Tuple[Any, float]:
        """
        Realiza predicción.
        
        Args:
            features: Características para predicción
            
        Returns:
            Tupla (predicción, confianza)
        """
        pass
    
    @abstractmethod
    def get_feature_names(self) -> List[str]:
        """Obtiene nombres de características usadas."""
        pass
    
    def generate_cache_key(self, features: Dict[str, Any]) -> str:
        """Genera clave de cache para las características."""
        # Normalizar características para cache consistente
        normalized_features = self._normalize_features(features)
        content = f"{self.model_id}:{self.version}:{json.dumps(normalized_features, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _normalize_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza características para cache consistente."""
        normalized = {}
        for key, value in features.items():
            if isinstance(value, str):
                normalized[key] = value.lower().strip()
            elif isinstance(value, float):
                normalized[key] = round(value, 4)  # Redondear para consistencia
            else:
                normalized[key] = value
        
        return normalized


class ExpenseCategorizerModel(BaseMLModel):
    """⚡ Modelo optimizado para categorización de gastos."""
    
    def __init__(self):
        super().__init__("expense_categorizer", "2.0")
        
        # Reglas de categorización inteligente
        self.category_patterns = {
            'transporte': [
                'nafta', 'gasolina', 'combustible', 'uber', 'taxi', 'colectivo',
                'subte', 'tren', 'estacionamiento', 'peaje', 'cochera'
            ],
            'supermercado': [
                'super', 'mercado', 'walmart', 'carrefour', 'coto', 'disco',
                'jumbo', 'vea', 'dia', 'comida', 'almacen', 'verduleria'
            ],
            'carniceria': [
                'carniceria', 'carnicería', 'carne', 'asado', 'pollo', 'pescado',
                'fiambreria', 'fiambrería', 'embutidos'
            ],
            'restaurante': [
                'restaurant', 'restaurante', 'pizza', 'hamburguesa', 'delivery',
                'pedidos', 'ya', 'rappi', 'glovo', 'mcdonald', 'burger'
            ],
            'salud': [
                'farmacia', 'medicina', 'doctor', 'medico', 'hospital',
                'clinica', 'obra social', 'dentista', 'oculista'
            ],
            'entretenimiento': [
                'cine', 'teatro', 'netflix', 'spotify', 'juegos', 'bar',
                'boliche', 'disco', 'evento', 'entrada'
            ],
            'servicios': [
                'luz', 'gas', 'agua', 'internet', 'cable', 'telefono',
                'celular', 'seguro', 'expensas', 'alquiler'
            ],
            'educacion': [
                'colegio', 'universidad', 'curso', 'libros', 'material',
                'estudio', 'academia', 'idiomas'
            ],
            'ropa': [
                'ropa', 'zapatillas', 'zapatos', 'camisa', 'pantalon',
                'vestido', 'abrigo', 'shopping', 'tienda'
            ],
            'hogar': [
                'muebles', 'electrodomesticos', 'decoracion', 'jardin',
                'herramientas', 'pintura', 'reparacion', 'ferreteria'
            ]
        }
        
        # Pesos por confianza de coincidencia
        self.pattern_weights = {
            'exact_match': 0.95,      # Coincidencia exacta
            'substring_match': 0.80,   # Subcadena
            'fuzzy_match': 0.65,      # Coincidencia difusa
            'keyword_match': 0.50     # Palabras clave
        }
    
    def predict(self, features: Dict[str, Any]) -> Tuple[str, float]:
        """
        Predice categoría de gasto.
        
        Args:
            features: Dict con 'description', 'amount', etc.
            
        Returns:
            Tupla (categoría, confianza)
        """
        description = features.get('description', '').lower().strip()
        amount = features.get('amount', 0)
        
        if not description:
            return 'otros', 0.1
        
        # Buscar coincidencias en patrones
        category_scores = {}
        
        for category, patterns in self.category_patterns.items():
            max_score = 0
            
            for pattern in patterns:
                score = self._calculate_pattern_match(description, pattern)
                max_score = max(max_score, score)
            
            if max_score > 0:
                category_scores[category] = max_score
        
        # Aplicar ajustes contextuales basados en cantidad
        category_scores = self._apply_amount_context(category_scores, amount)
        
        # Seleccionar mejor categoría
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            confidence = category_scores[best_category]
            return best_category, confidence
        
        return 'otros', 0.2
    
    def _calculate_pattern_match(self, description: str, pattern: str) -> float:
        """Calcula score de coincidencia entre descripción y patrón."""
        pattern = pattern.lower()
        
        # Coincidencia exacta
        if pattern == description:
            return self.pattern_weights['exact_match']
        
        # Coincidencia de subcadena
        if pattern in description:
            return self.pattern_weights['substring_match']
        
        # Coincidencia difusa (palabras en común)
        description_words = set(description.split())
        pattern_words = set(pattern.split())
        
        if pattern_words.intersection(description_words):
            overlap_ratio = len(pattern_words.intersection(description_words)) / len(pattern_words.union(description_words))
            return self.pattern_weights['fuzzy_match'] * overlap_ratio
        
        return 0.0
    
    def _apply_amount_context(self, scores: Dict[str, float], amount: float) -> Dict[str, float]:
        """Aplica contexto de cantidad para ajustar scores."""
        adjusted_scores = scores.copy()
        
        # Ajustar basado en rangos típicos por categoría
        amount_boosts = {
            'transporte': (50, 2000),      # Rango típico de transporte
            'supermercado': (100, 5000),   # Compras de supermercado
            'carniceria': (200, 1500),     # Compras de carnicería
            'restaurante': (300, 3000),    # Salidas a comer
            'servicios': (500, 10000),     # Servicios mensuales
            'ropa': (500, 5000),           # Compras de ropa
        }
        
        for category, score in scores.items():
            if category in amount_boosts:
                min_amount, max_amount = amount_boosts[category]
                if min_amount <= amount <= max_amount:
                    adjusted_scores[category] = min(0.95, score * 1.2)  # 20% boost
        
        return adjusted_scores
    
    def get_feature_names(self) -> List[str]:
        """Obtiene nombres de características usadas."""
        return ['description', 'amount']


class AdvancedMLOptimizer:
    """⚡ Optimizador avanzado para modelos ML con cache inteligente."""
    
    def __init__(self, 
                 cache_size: int = 10000,
                 auto_model_selection: bool = True,
                 performance_monitoring: bool = True):
        """
        Inicializa optimizador ML avanzado.
        
        Args:
            cache_size: Tamaño del cache de predicciones
            auto_model_selection: Selección automática del mejor modelo
            performance_monitoring: Monitoreo de rendimiento
        """
        self.cache_size = cache_size
        self.auto_model_selection = auto_model_selection
        self.performance_monitoring = performance_monitoring
        
        # Modelos disponibles
        self.models: Dict[str, BaseMLModel] = {}
        self.active_model_id: Optional[str] = None
        
        # Cache de predicciones (LRU)
        from collections import OrderedDict
        self.prediction_cache: OrderedDict = OrderedDict()
        
        # Métricas de rendimiento
        self.model_metrics: Dict[str, ModelPerformanceMetrics] = {}
        
        # Workers de monitoreo
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        self.logger = logger
        self.metrics_collector = get_metrics_collector()
        
        # Registrar modelo por defecto
        self._register_default_models()
        
        self.logger.info("AdvancedMLOptimizer inicializado")
    
    def _register_default_models(self):
        """Registra modelos por defecto."""
        # Modelo de categorización de gastos
        expense_model = ExpenseCategorizerModel()
        self.register_model(expense_model)
        
        # Establecer como modelo activo por defecto
        self.active_model_id = expense_model.model_id
    
    def register_model(self, model: BaseMLModel):
        """
        Registra un nuevo modelo ML.
        
        Args:
            model: Instancia del modelo ML
        """
        self.models[model.model_id] = model
        self.model_metrics[model.model_id] = ModelPerformanceMetrics(model.model_id)
        
        self.logger.info(f"🤖 Modelo registrado: {model.model_id} v{model.version}")
    
    def predict_optimized(self, 
                         features: Dict[str, Any], 
                         model_id: Optional[str] = None,
                         use_cache: bool = True) -> MLPredictionResult:
        """
        ⚡ Realiza predicción optimizada con cache inteligente.
        
        Args:
            features: Características para predicción
            model_id: ID del modelo a usar (None para auto-selección)
            use_cache: Si usar cache de predicciones
            
        Returns:
            Resultado de predicción con metadata
        """
        # Seleccionar modelo
        selected_model = self._select_model(model_id)
        if not selected_model:
            raise ValueError(f"Modelo no encontrado: {model_id}")
        
        start_time = time.time()
        
        # Generar clave de cache
        cache_key = selected_model.generate_cache_key(features)
        
        # Verificar cache
        if use_cache and cache_key in self.prediction_cache:
            cached_result = self.prediction_cache[cache_key]
            
            # Mover al final para LRU
            self.prediction_cache.move_to_end(cache_key)
            
            # Actualizar métricas
            processing_time = (time.time() - start_time) * 1000
            self.model_metrics[selected_model.model_id].update_prediction(
                processing_time, cached_result['confidence'], from_cache=True
            )
            
            self.logger.debug(f"🎯 Cache HIT para {selected_model.model_id}")
            
            return MLPredictionResult(
                prediction=cached_result['prediction'],
                confidence=cached_result['confidence'],
                model_version=selected_model.version,
                processing_time_ms=processing_time,
                features_used=selected_model.get_feature_names(),
                cache_key=cache_key
            )
        
        # Realizar predicción
        prediction, confidence = selected_model.predict(features)
        processing_time = (time.time() - start_time) * 1000
        
        # Cachear resultado si tiene suficiente confianza
        if use_cache and confidence >= 0.6:  # Solo cachear predicciones confiables
            self._cache_prediction(cache_key, prediction, confidence)
        
        # Actualizar métricas
        self.model_metrics[selected_model.model_id].update_prediction(
            processing_time, confidence, from_cache=False
        )
        
        self.logger.debug(f"🤖 Predicción directa de {selected_model.model_id}: {confidence:.2f} confianza")
        
        return MLPredictionResult(
            prediction=prediction,
            confidence=confidence,
            model_version=selected_model.version,
            processing_time_ms=processing_time,
            features_used=selected_model.get_feature_names(),
            cache_key=cache_key
        )
    
    def _select_model(self, model_id: Optional[str]) -> Optional[BaseMLModel]:
        """Selecciona modelo a usar."""
        if model_id:
            return self.models.get(model_id)
        
        if self.auto_model_selection:
            return self._auto_select_best_model()
        
        return self.models.get(self.active_model_id)
    
    def _auto_select_best_model(self) -> Optional[BaseMLModel]:
        """Selecciona automáticamente el mejor modelo basado en métricas."""
        if not self.models:
            return None
        
        # Si solo hay un modelo, usarlo
        if len(self.models) == 1:
            return list(self.models.values())[0]
        
        # Seleccionar basado en performance score
        best_model_id = None
        best_score = -1
        
        for model_id, metrics in self.model_metrics.items():
            if metrics.total_predictions > 10:  # Suficiente muestra
                score = metrics.performance_score
                if score > best_score:
                    best_score = score
                    best_model_id = model_id
        
        return self.models.get(best_model_id) if best_model_id else self.models.get(self.active_model_id)
    
    def _cache_prediction(self, cache_key: str, prediction: Any, confidence: float):
        """Cachea predicción con gestión LRU."""
        # Evitar cache overflow
        if len(self.prediction_cache) >= self.cache_size:
            # Remover el más antiguo (LRU)
            self.prediction_cache.popitem(last=False)
        
        # Agregar nueva predicción
        self.prediction_cache[cache_key] = {
            'prediction': prediction,
            'confidence': confidence,
            'cached_at': time.time()
        }
    
    def start_monitoring(self, check_interval: int = 300):
        """Inicia monitoreo automático de rendimiento."""
        if not self.performance_monitoring or self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.info("📊 ML performance monitoring iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo automático."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        self.logger.info("🛑 ML performance monitoring detenido")
    
    def _monitoring_loop(self, check_interval: int):
        """Loop principal de monitoreo."""
        while self.monitoring_active:
            try:
                # Recolectar y registrar métricas
                self._collect_performance_metrics()
                
                # Optimizar cache si es necesario
                self._optimize_cache()
                
                # Auto-seleccionar mejor modelo
                if self.auto_model_selection:
                    self._update_active_model()
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error en ML monitoring loop: {e}")
                time.sleep(60)
    
    def _collect_performance_metrics(self):
        """Recolecta métricas de rendimiento de modelos."""
        for model_id, metrics in self.model_metrics.items():
            # Registrar métricas principales
            self.metrics_collector.record_custom_metric(
                'ml_model_cache_hit_rate',
                metrics.cache_hit_rate,
                model_id=model_id
            )
            
            self.metrics_collector.record_custom_metric(
                'ml_model_avg_processing_time',
                metrics.average_processing_time,
                model_id=model_id
            )
            
            self.metrics_collector.record_custom_metric(
                'ml_model_avg_confidence',
                metrics.average_confidence,
                model_id=model_id
            )
            
            self.metrics_collector.record_custom_metric(
                'ml_model_performance_score',
                metrics.performance_score,
                model_id=model_id
            )
    
    def _optimize_cache(self):
        """Optimiza el cache de predicciones."""
        # Limpiar predicciones muy antiguas (más de 1 hora)
        current_time = time.time()
        expired_keys = []
        
        for cache_key, cached_data in self.prediction_cache.items():
            if current_time - cached_data['cached_at'] > 3600:  # 1 hora
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.prediction_cache[key]
        
        if expired_keys:
            self.logger.debug(f"🧹 Cache cleanup: {len(expired_keys)} predicciones expiradas eliminadas")
    
    def _update_active_model(self):
        """Actualiza modelo activo basado en rendimiento."""
        best_model = self._auto_select_best_model()
        if best_model and best_model.model_id != self.active_model_id:
            old_model = self.active_model_id
            self.active_model_id = best_model.model_id
            self.logger.info(f"🔄 Modelo activo cambiado: {old_model} → {best_model.model_id}")
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Genera reporte completo de optimización ML."""
        # Métricas generales
        total_predictions = sum(m.total_predictions for m in self.model_metrics.values())
        total_cache_hits = sum(m.cache_hits for m in self.model_metrics.values())
        total_cache_misses = sum(m.cache_misses for m in self.model_metrics.values())
        
        overall_cache_hit_rate = (total_cache_hits / max(total_predictions, 1)) * 100
        
        # Métricas por modelo
        model_reports = {}
        for model_id, metrics in self.model_metrics.items():
            model_reports[model_id] = {
                'total_predictions': metrics.total_predictions,
                'cache_hit_rate': metrics.cache_hit_rate,
                'average_processing_time': metrics.average_processing_time,
                'average_confidence': metrics.average_confidence,
                'performance_score': metrics.performance_score
            }
        
        # Análisis del cache
        cache_analysis = {
            'cache_size': len(self.prediction_cache),
            'cache_limit': self.cache_size,
            'cache_utilization_percent': (len(self.prediction_cache) / self.cache_size) * 100
        }
        
        return {
            'overall_metrics': {
                'total_predictions': total_predictions,
                'overall_cache_hit_rate': overall_cache_hit_rate,
                'active_model_id': self.active_model_id,
                'registered_models': len(self.models)
            },
            'model_metrics': model_reports,
            'cache_analysis': cache_analysis,
            'optimization_settings': {
                'auto_model_selection': self.auto_model_selection,
                'performance_monitoring': self.performance_monitoring,
                'monitoring_active': self.monitoring_active
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def clear_cache(self):
        """Limpia completamente el cache de predicciones."""
        cleared_count = len(self.prediction_cache)
        self.prediction_cache.clear()
        self.logger.info(f"🧹 Cache limpiado: {cleared_count} predicciones eliminadas")
    
    def get_cached_predictions_info(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene información de predicciones cacheadas."""
        cached_info = []
        
        for cache_key, cached_data in list(self.prediction_cache.items())[-limit:]:
            cached_info.append({
                'cache_key': cache_key,
                'prediction': str(cached_data['prediction'])[:50],  # Truncar para legibilidad
                'confidence': cached_data['confidence'],
                'age_minutes': (time.time() - cached_data['cached_at']) / 60
            })
        
        return cached_info


# Instancia global del optimizador ML
_ml_optimizer_instance: Optional[AdvancedMLOptimizer] = None

def get_ml_optimizer(cache_size: int = 10000, 
                    auto_model_selection: bool = True,
                    performance_monitoring: bool = True) -> AdvancedMLOptimizer:
    """
    Obtiene instancia singleton del optimizador ML.
    
    Args:
        cache_size: Tamaño del cache de predicciones
        auto_model_selection: Selección automática del mejor modelo
        performance_monitoring: Monitoreo de rendimiento
        
    Returns:
        Instancia del optimizador ML
    """
    global _ml_optimizer_instance
    if _ml_optimizer_instance is None:
        _ml_optimizer_instance = AdvancedMLOptimizer(
            cache_size, auto_model_selection, performance_monitoring
        )
        _ml_optimizer_instance.start_monitoring()
    return _ml_optimizer_instance


def shutdown_ml_optimizer():
    """Cierra el optimizador ML global."""
    global _ml_optimizer_instance
    if _ml_optimizer_instance:
        _ml_optimizer_instance.stop_monitoring()
        _ml_optimizer_instance = None