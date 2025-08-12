"""
Predictive Pre-processing System - FASE 6.1
⚡ Sistema de pre-procesamiento predictivo para reducir latencia percibida

Mejora esperada: 40% reducción en latencia percibida + predicción de patrones
"""

import asyncio
import threading
import time
import json
import hashlib
import statistics
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import re

from shared.logger import get_logger
from shared.metrics import get_metrics_collector


logger = get_logger(__name__)


class PredictionType(Enum):
    """Tipos de predicciones soportadas."""
    NEXT_CATEGORY = "next_category"        # Próxima categoría probable
    SIMILAR_EXPENSE = "similar_expense"    # Gastos similares
    RECURRING_PATTERN = "recurring_pattern" # Patrones recurrentes
    AUTO_COMPLETE = "auto_complete"        # Auto-completado
    BULK_PROCESSING = "bulk_processing"    # Procesamiento en lote


@dataclass
class UserBehaviorPattern:
    """Patrón de comportamiento de usuario."""
    user_id: str = "default"
    
    # Patrones de categorización
    frequent_categories: Dict[str, int] = field(default_factory=dict)
    category_sequences: List[List[str]] = field(default_factory=list)
    time_patterns: Dict[str, List[datetime]] = field(default_factory=dict)  # categoria -> [timestamps]
    
    # Patrones de descripción
    description_patterns: Dict[str, Set[str]] = field(default_factory=dict)  # categoria -> {descriptions}
    common_keywords: Dict[str, float] = field(default_factory=dict)  # keyword -> frequency
    
    # Patrones de montos
    amount_ranges: Dict[str, Tuple[float, float]] = field(default_factory=dict)  # categoria -> (min, max)
    typical_amounts: Dict[str, List[float]] = field(default_factory=dict)  # categoria -> [amounts]
    
    # Ventanas temporales para análisis
    recent_expenses: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update_pattern(self, categoria: str, descripcion: str, monto: float, fecha: datetime):
        """Actualiza patrones con nuevo gasto."""
        # Categorías frecuentes
        self.frequent_categories[categoria] = self.frequent_categories.get(categoria, 0) + 1
        
        # Secuencias de categorías
        if len(self.recent_expenses) > 0:
            last_category = self.recent_expenses[-1][0] if self.recent_expenses else None
            if last_category:
                sequence = [last_category, categoria]
                self.category_sequences.append(sequence)
                
                # Mantener solo últimas 50 secuencias
                if len(self.category_sequences) > 50:
                    self.category_sequences.pop(0)
        
        # Patrones temporales
        if categoria not in self.time_patterns:
            self.time_patterns[categoria] = []
        self.time_patterns[categoria].append(fecha)
        
        # Mantener solo últimos 20 timestamps por categoría
        if len(self.time_patterns[categoria]) > 20:
            self.time_patterns[categoria].pop(0)
        
        # Patrones de descripción
        if categoria not in self.description_patterns:
            self.description_patterns[categoria] = set()
        
        # Extraer palabras clave de la descripción
        keywords = self._extract_keywords(descripcion)
        for keyword in keywords:
            self.description_patterns[categoria].add(keyword)
            self.common_keywords[keyword] = self.common_keywords.get(keyword, 0) + 1
        
        # Patrones de montos
        if categoria not in self.typical_amounts:
            self.typical_amounts[categoria] = []
        
        self.typical_amounts[categoria].append(monto)
        # Mantener solo últimos 20 montos por categoría
        if len(self.typical_amounts[categoria]) > 20:
            self.typical_amounts[categoria].pop(0)
        
        # Actualizar rangos de montos
        if categoria in self.typical_amounts and self.typical_amounts[categoria]:
            amounts = self.typical_amounts[categoria]
            self.amount_ranges[categoria] = (min(amounts), max(amounts))
        
        # Agregar a gastos recientes
        self.recent_expenses.append((categoria, descripcion, monto, fecha))
    
    def _extract_keywords(self, descripcion: str) -> List[str]:
        """Extrae palabras clave de una descripción."""
        # Limpiar y normalizar
        descripcion = descripcion.lower().strip()
        
        # Remover caracteres especiales y dividir
        palabras = re.findall(r'\b\w+\b', descripcion)
        
        # Filtrar palabras muy cortas o comunes
        stop_words = {'de', 'la', 'el', 'en', 'un', 'una', 'del', 'con', 'por', 'para', 'y', 'o'}
        keywords = [p for p in palabras if len(p) > 2 and p not in stop_words]
        
        return keywords
    
    def predict_next_category(self, last_categories: List[str] = None) -> List[Tuple[str, float]]:
        """Predice próxima categoría probable."""
        if not last_categories and self.recent_expenses:
            # Usar últimas 3 categorías si no se especifican
            last_categories = [exp[0] for exp in list(self.recent_expenses)[-3:]]
        
        if not last_categories:
            # Fallback a categorías más frecuentes
            return self._get_frequent_categories()
        
        # Buscar secuencias similares
        sequence_matches = defaultdict(int)
        
        for seq in self.category_sequences:
            if len(seq) >= 2 and len(last_categories) >= 1:
                if seq[-2] == last_categories[-1]:  # Coincidencia con última categoría
                    sequence_matches[seq[-1]] += 1
        
        # Convertir a probabilidades
        total_matches = sum(sequence_matches.values())
        if total_matches > 0:
            predictions = [(cat, count / total_matches) 
                          for cat, count in sequence_matches.items()]
            predictions.sort(key=lambda x: x[1], reverse=True)
            return predictions[:5]  # Top 5 predicciones
        
        # Fallback a categorías frecuentes
        return self._get_frequent_categories()
    
    def _get_frequent_categories(self) -> List[Tuple[str, float]]:
        """Obtiene categorías más frecuentes."""
        total_expenses = sum(self.frequent_categories.values())
        if total_expenses == 0:
            return []
        
        predictions = [(cat, count / total_expenses) 
                      for cat, count in self.frequent_categories.items()]
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:5]
    
    def predict_similar_expenses(self, partial_description: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Predice gastos similares basado en descripción parcial."""
        partial_keywords = self._extract_keywords(partial_description)
        if not partial_keywords:
            return []
        
        # Buscar en gastos recientes
        similar_expenses = []
        
        for categoria, descripcion, monto, fecha in self.recent_expenses:
            # Calcular similitud basada en keywords
            expense_keywords = self._extract_keywords(descripcion)
            
            # Calcular score de similitud (Jaccard similarity)
            intersection = set(partial_keywords).intersection(set(expense_keywords))
            union = set(partial_keywords).union(set(expense_keywords))
            
            if union:
                similarity = len(intersection) / len(union)
                
                if similarity > 0.3:  # Umbral de similitud
                    similar_expenses.append({
                        'categoria': categoria,
                        'descripcion': descripcion,
                        'monto': monto,
                        'fecha': fecha,
                        'similarity': similarity
                    })
        
        # Ordenar por similitud
        similar_expenses.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_expenses[:limit]
    
    def predict_recurring_patterns(self) -> List[Dict[str, Any]]:
        """Identifica patrones recurrentes de gastos."""
        recurring_patterns = []
        
        for categoria, timestamps in self.time_patterns.items():
            if len(timestamps) < 3:  # Necesita al menos 3 ocurrencias
                continue
            
            # Analizar intervalos entre gastos
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).days
                intervals.append(interval)
            
            if intervals:
                avg_interval = statistics.mean(intervals)
                std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
                
                # Considerar recurrente si la desviación es baja
                if std_interval < avg_interval * 0.3 and avg_interval <= 31:  # Máximo mensual
                    
                    # Predecir próximo gasto
                    last_timestamp = timestamps[-1]
                    next_predicted = last_timestamp + timedelta(days=int(avg_interval))
                    
                    # Monto típico
                    typical_amount = None
                    if categoria in self.typical_amounts and self.typical_amounts[categoria]:
                        typical_amount = statistics.median(self.typical_amounts[categoria])
                    
                    recurring_patterns.append({
                        'categoria': categoria,
                        'avg_interval_days': avg_interval,
                        'next_predicted_date': next_predicted,
                        'confidence': max(0.5, 1 - (std_interval / max(avg_interval, 1))),
                        'typical_amount': typical_amount,
                        'pattern_strength': len(timestamps)
                    })
        
        # Ordenar por confianza
        recurring_patterns.sort(key=lambda x: x['confidence'], reverse=True)
        return recurring_patterns
    
    def suggest_auto_complete(self, partial_text: str, limit: int = 5) -> List[str]:
        """Sugiere auto-completado para descripción parcial."""
        if not partial_text or len(partial_text) < 2:
            return []
        
        partial_lower = partial_text.lower()
        suggestions = set()
        
        # Buscar en descripciones recientes
        for _, descripcion, _, _ in self.recent_expenses:
            if partial_lower in descripcion.lower():
                suggestions.add(descripcion)
        
        # Buscar en patrones de descripción
        for categoria, descriptions in self.description_patterns.items():
            for desc_keyword in descriptions:
                if partial_lower in desc_keyword.lower():
                    # Generar sugerencia basada en patrón
                    suggestions.add(f"{partial_text} {desc_keyword}")
        
        return list(suggestions)[:limit]


@dataclass
class PredictionRequest:
    """Solicitud de predicción."""
    request_id: str
    prediction_type: PredictionType
    input_data: Dict[str, Any]
    user_id: str = "default"
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    
    def __lt__(self, other):
        """Comparación para PriorityQueue."""
        if not isinstance(other, PredictionRequest):
            return NotImplemented
        
        # Menor prioridad = mayor importancia
        if self.priority != other.priority:
            return self.priority < other.priority
        
        return self.created_at < other.created_at


class PredictivePreprocessor:
    """⚡ Sistema de pre-procesamiento predictivo para reducir latencia."""
    
    def __init__(self, 
                 background_processing: bool = True,
                 prediction_cache_size: int = 1000,
                 pattern_update_interval: int = 300):
        """
        Inicializa pre-procesador predictivo.
        
        Args:
            background_processing: Habilitar procesamiento en background
            prediction_cache_size: Tamaño del cache de predicciones
            pattern_update_interval: Intervalo de actualización de patrones (segundos)
        """
        self.background_processing = background_processing
        self.prediction_cache_size = prediction_cache_size
        self.pattern_update_interval = pattern_update_interval
        
        # Patrones de usuario
        self.user_patterns: Dict[str, UserBehaviorPattern] = {}
        
        # Cache de predicciones pre-calculadas
        from collections import OrderedDict
        self.prediction_cache: OrderedDict = OrderedDict()
        
        # Queue de procesamiento en background
        import queue
        self.prediction_queue: queue.PriorityQueue = queue.PriorityQueue()
        
        # Workers de background
        self.background_active = False
        self.background_workers: List[threading.Thread] = []
        
        # Callbacks para predicciones
        self.prediction_callbacks: Dict[PredictionType, List[Callable]] = defaultdict(list)
        
        # Métricas
        self.preprocessing_stats = {
            'total_predictions': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'background_predictions': 0,
            'pattern_updates': 0
        }
        
        self.logger = logger
        self.metrics_collector = get_metrics_collector()
        
        if background_processing:
            self.start_background_processing()
        
        self.logger.info("PredictivePreprocessor inicializado")
    
    def start_background_processing(self):
        """Inicia procesamiento en background."""
        if self.background_active:
            return
        
        self.background_active = True
        
        # Iniciar workers de predicción
        for i in range(2):  # 2 workers
            worker = threading.Thread(
                target=self._prediction_worker,
                name=f"PredictionWorker-{i}",
                daemon=True
            )
            worker.start()
            self.background_workers.append(worker)
        
        # Iniciar worker de actualización de patrones
        pattern_worker = threading.Thread(
            target=self._pattern_update_worker,
            daemon=True
        )
        pattern_worker.start()
        self.background_workers.append(pattern_worker)
        
        self.logger.info("🚀 Background processing iniciado")
    
    def stop_background_processing(self):
        """Detiene procesamiento en background."""
        self.background_active = False
        
        # Esperar que terminen los workers
        for worker in self.background_workers:
            worker.join(timeout=5)
        
        self.background_workers.clear()
        self.logger.info("🛑 Background processing detenido")
    
    def register_expense_pattern(self, 
                                categoria: str, 
                                descripcion: str, 
                                monto: float,
                                fecha: datetime = None,
                                user_id: str = "default"):
        """
        ⚡ Registra patrón de gasto para predicciones futuras.
        
        Args:
            categoria: Categoría del gasto
            descripcion: Descripción del gasto
            monto: Monto del gasto
            fecha: Fecha del gasto
            user_id: ID del usuario
        """
        fecha = fecha or datetime.now()
        
        # Obtener o crear patrón de usuario
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = UserBehaviorPattern(user_id)
        
        # Actualizar patrón
        pattern = self.user_patterns[user_id]
        pattern.update_pattern(categoria, descripcion, monto, fecha)
        
        # Invalidar cache relacionado
        self._invalidate_related_cache(user_id, categoria)
        
        # Disparar pre-predicciones en background
        if self.background_processing:
            self._trigger_background_predictions(user_id, categoria)
        
        self.preprocessing_stats['pattern_updates'] += 1
        
        self.logger.debug(f"Patrón registrado: {categoria} - {descripcion[:20]}...")
    
    def predict_next_category(self, 
                            user_id: str = "default",
                            last_categories: List[str] = None,
                            use_cache: bool = True) -> List[Tuple[str, float]]:
        """
        ⚡ Predice próxima categoría probable.
        
        Args:
            user_id: ID del usuario
            last_categories: Últimas categorías usadas
            use_cache: Si usar cache de predicciones
            
        Returns:
            Lista de (categoría, probabilidad) ordenada por probabilidad
        """
        cache_key = self._generate_cache_key('next_category', user_id, {'last_categories': last_categories})
        
        # Verificar cache
        if use_cache and cache_key in self.prediction_cache:
            self.preprocessing_stats['cache_hits'] += 1
            result = self.prediction_cache[cache_key]
            # Mover al final para LRU
            self.prediction_cache.move_to_end(cache_key)
            return result
        
        # Calcular predicción
        if user_id not in self.user_patterns:
            self.preprocessing_stats['cache_misses'] += 1
            return []
        
        pattern = self.user_patterns[user_id]
        predictions = pattern.predict_next_category(last_categories)
        
        # Cachear resultado
        if use_cache:
            self._cache_prediction(cache_key, predictions)
        
        self.preprocessing_stats['total_predictions'] += 1
        self.preprocessing_stats['cache_misses'] += 1
        
        return predictions
    
    def predict_similar_expenses(self,
                               partial_description: str,
                               user_id: str = "default",
                               limit: int = 5,
                               use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        ⚡ Predice gastos similares basado en descripción parcial.
        
        Args:
            partial_description: Descripción parcial
            user_id: ID del usuario
            limit: Límite de resultados
            use_cache: Si usar cache
            
        Returns:
            Lista de gastos similares con metadata
        """
        cache_key = self._generate_cache_key('similar_expenses', user_id, {
            'partial_description': partial_description[:20],  # Truncar para cache
            'limit': limit
        })
        
        # Verificar cache
        if use_cache and cache_key in self.prediction_cache:
            self.preprocessing_stats['cache_hits'] += 1
            result = self.prediction_cache[cache_key]
            self.prediction_cache.move_to_end(cache_key)
            return result
        
        # Calcular predicción
        if user_id not in self.user_patterns:
            self.preprocessing_stats['cache_misses'] += 1
            return []
        
        pattern = self.user_patterns[user_id]
        similar_expenses = pattern.predict_similar_expenses(partial_description, limit)
        
        # Cachear resultado
        if use_cache:
            self._cache_prediction(cache_key, similar_expenses)
        
        self.preprocessing_stats['total_predictions'] += 1
        self.preprocessing_stats['cache_misses'] += 1
        
        return similar_expenses
    
    def predict_recurring_patterns(self,
                                 user_id: str = "default",
                                 use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        ⚡ Identifica patrones recurrentes de gastos.
        
        Args:
            user_id: ID del usuario
            use_cache: Si usar cache
            
        Returns:
            Lista de patrones recurrentes
        """
        cache_key = self._generate_cache_key('recurring_patterns', user_id, {})
        
        # Verificar cache
        if use_cache and cache_key in self.prediction_cache:
            self.preprocessing_stats['cache_hits'] += 1
            result = self.prediction_cache[cache_key]
            self.prediction_cache.move_to_end(cache_key)
            return result
        
        # Calcular predicción
        if user_id not in self.user_patterns:
            self.preprocessing_stats['cache_misses'] += 1
            return []
        
        pattern = self.user_patterns[user_id]
        recurring_patterns = pattern.predict_recurring_patterns()
        
        # Cachear resultado
        if use_cache:
            self._cache_prediction(cache_key, recurring_patterns)
        
        self.preprocessing_stats['total_predictions'] += 1
        self.preprocessing_stats['cache_misses'] += 1
        
        return recurring_patterns
    
    def suggest_auto_complete(self,
                            partial_text: str,
                            user_id: str = "default",
                            limit: int = 5,
                            use_cache: bool = True) -> List[str]:
        """
        ⚡ Sugiere auto-completado para descripción.
        
        Args:
            partial_text: Texto parcial
            user_id: ID del usuario
            limit: Límite de sugerencias
            use_cache: Si usar cache
            
        Returns:
            Lista de sugerencias de auto-completado
        """
        if len(partial_text) < 2:
            return []
        
        cache_key = self._generate_cache_key('auto_complete', user_id, {
            'partial_text': partial_text[:20],
            'limit': limit
        })
        
        # Verificar cache
        if use_cache and cache_key in self.prediction_cache:
            self.preprocessing_stats['cache_hits'] += 1
            result = self.prediction_cache[cache_key]
            self.prediction_cache.move_to_end(cache_key)
            return result
        
        # Calcular sugerencias
        if user_id not in self.user_patterns:
            self.preprocessing_stats['cache_misses'] += 1
            return []
        
        pattern = self.user_patterns[user_id]
        suggestions = pattern.suggest_auto_complete(partial_text, limit)
        
        # Cachear resultado
        if use_cache:
            self._cache_prediction(cache_key, suggestions)
        
        self.preprocessing_stats['total_predictions'] += 1
        self.preprocessing_stats['cache_misses'] += 1
        
        return suggestions
    
    def queue_background_prediction(self,
                                  prediction_type: PredictionType,
                                  input_data: Dict[str, Any],
                                  user_id: str = "default",
                                  priority: int = 2):
        """
        Encola predicción para procesamiento en background.
        
        Args:
            prediction_type: Tipo de predicción
            input_data: Datos de entrada
            user_id: ID del usuario
            priority: Prioridad (1=alta, 2=media, 3=baja)
        """
        if not self.background_processing:
            return
        
        request_id = hashlib.md5(
            f"{prediction_type.value}:{user_id}:{json.dumps(input_data, sort_keys=True)}".encode()
        ).hexdigest()[:8]
        
        request = PredictionRequest(
            request_id=request_id,
            prediction_type=prediction_type,
            input_data=input_data,
            user_id=user_id,
            priority=priority
        )
        
        self.prediction_queue.put((priority, time.time(), request))
        self.logger.debug(f"Predicción encolada: {prediction_type.value} (prioridad {priority})")
    
    def _generate_cache_key(self, prediction_type: str, user_id: str, params: Dict[str, Any]) -> str:
        """Genera clave de cache para predicción."""
        content = f"{prediction_type}:{user_id}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _cache_prediction(self, cache_key: str, result: Any):
        """Cachea resultado de predicción."""
        # Evitar overflow del cache
        if len(self.prediction_cache) >= self.prediction_cache_size:
            self.prediction_cache.popitem(last=False)  # Remover más antiguo
        
        self.prediction_cache[cache_key] = result
    
    def _invalidate_related_cache(self, user_id: str, categoria: str):
        """Invalida cache relacionado con usuario y categoría."""
        keys_to_remove = []
        
        for cache_key in self.prediction_cache.keys():
            # Usar heurística simple para invalidar cache relacionado
            if user_id in str(cache_key):  # Cache específico del usuario
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self.prediction_cache[key]
        
        if keys_to_remove:
            self.logger.debug(f"Cache invalidado: {len(keys_to_remove)} entradas")
    
    def _trigger_background_predictions(self, user_id: str, categoria: str):
        """Dispara predicciones en background basadas en nueva entrada."""
        # Pre-calcular próxima categoría
        self.queue_background_prediction(
            PredictionType.NEXT_CATEGORY,
            {'last_categories': [categoria]},
            user_id,
            priority=2
        )
        
        # Pre-calcular patrones recurrentes
        self.queue_background_prediction(
            PredictionType.RECURRING_PATTERN,
            {},
            user_id,
            priority=3
        )
    
    def _prediction_worker(self):
        """Worker de procesamiento de predicciones en background."""
        self.logger.info(f"🔄 {threading.current_thread().name} iniciado")
        
        while self.background_active:
            try:
                # Obtener siguiente solicitud
                try:
                    priority, timestamp, request = self.prediction_queue.get(timeout=1.0)
                except:
                    continue
                
                # Procesar predicción
                self._process_background_prediction(request)
                self.preprocessing_stats['background_predictions'] += 1
                
                self.prediction_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error en prediction worker: {e}")
                time.sleep(1.0)
        
        self.logger.info(f"🛑 {threading.current_thread().name} terminado")
    
    def _process_background_prediction(self, request: PredictionRequest):
        """Procesa solicitud de predicción en background."""
        try:
            if request.prediction_type == PredictionType.NEXT_CATEGORY:
                self.predict_next_category(
                    request.user_id,
                    request.input_data.get('last_categories'),
                    use_cache=True
                )
            elif request.prediction_type == PredictionType.RECURRING_PATTERN:
                self.predict_recurring_patterns(
                    request.user_id,
                    use_cache=True
                )
            
            self.logger.debug(f"Background prediction procesada: {request.request_id}")
            
        except Exception as e:
            self.logger.error(f"Error procesando background prediction {request.request_id}: {e}")
    
    def _pattern_update_worker(self):
        """Worker de actualización periódica de patrones."""
        self.logger.info("📊 Pattern update worker iniciado")
        
        while self.background_active:
            try:
                # Ejecutar análisis de patrones
                self._analyze_patterns()
                
                # Registrar métricas
                self._record_preprocessing_metrics()
                
                time.sleep(self.pattern_update_interval)
                
            except Exception as e:
                self.logger.error(f"Error en pattern update worker: {e}")
                time.sleep(60)
        
        self.logger.info("🛑 Pattern update worker terminado")
    
    def _analyze_patterns(self):
        """Analiza y optimiza patrones de usuarios."""
        for user_id, pattern in self.user_patterns.items():
            try:
                # Limpiar patrones antiguos
                current_time = datetime.now()
                
                # Remover timestamps muy antiguos (>6 meses)
                for categoria in list(pattern.time_patterns.keys()):
                    old_timestamps = []
                    for ts in pattern.time_patterns[categoria]:
                        if (current_time - ts).days > 180:
                            old_timestamps.append(ts)
                    
                    for old_ts in old_timestamps:
                        pattern.time_patterns[categoria].remove(old_ts)
                    
                    # Remover categoría si no tiene timestamps
                    if not pattern.time_patterns[categoria]:
                        del pattern.time_patterns[categoria]
                
            except Exception as e:
                self.logger.error(f"Error analizando patrones del usuario {user_id}: {e}")
    
    def _record_preprocessing_metrics(self):
        """Registra métricas de pre-procesamiento."""
        try:
            self.metrics_collector.record_custom_metric(
                'predictive_preprocessing_total_predictions',
                self.preprocessing_stats['total_predictions']
            )
            
            self.metrics_collector.record_custom_metric(
                'predictive_preprocessing_cache_hits',
                self.preprocessing_stats['cache_hits']
            )
            
            total_requests = self.preprocessing_stats['cache_hits'] + self.preprocessing_stats['cache_misses']
            if total_requests > 0:
                hit_rate = (self.preprocessing_stats['cache_hits'] / total_requests) * 100
                self.metrics_collector.record_custom_metric(
                    'predictive_preprocessing_cache_hit_rate',
                    hit_rate
                )
            
            self.metrics_collector.record_custom_metric(
                'predictive_preprocessing_background_predictions',
                self.preprocessing_stats['background_predictions']
            )
            
            self.metrics_collector.record_custom_metric(
                'predictive_preprocessing_active_patterns',
                len(self.user_patterns)
            )
            
        except Exception as e:
            self.logger.error(f"Error registrando métricas de preprocessing: {e}")
    
    def get_preprocessing_report(self) -> Dict[str, Any]:
        """Genera reporte completo del sistema predictivo."""
        # Análisis de patrones por usuario
        user_pattern_analysis = {}
        
        for user_id, pattern in self.user_patterns.items():
            user_pattern_analysis[user_id] = {
                'frequent_categories': dict(list(pattern.frequent_categories.items())[:5]),
                'total_expenses_tracked': len(pattern.recent_expenses),
                'categories_with_patterns': len(pattern.time_patterns),
                'recurring_patterns_count': len(pattern.predict_recurring_patterns()),
                'unique_keywords': len(pattern.common_keywords)
            }
        
        # Análisis del cache
        cache_analysis = {
            'cache_size': len(self.prediction_cache),
            'cache_limit': self.prediction_cache_size,
            'cache_utilization_percent': (len(self.prediction_cache) / self.prediction_cache_size) * 100
        }
        
        # Métricas de rendimiento
        total_requests = self.preprocessing_stats['cache_hits'] + self.preprocessing_stats['cache_misses']
        performance_metrics = {
            'cache_hit_rate': (self.preprocessing_stats['cache_hits'] / max(total_requests, 1)) * 100,
            'background_processing_ratio': (self.preprocessing_stats['background_predictions'] / max(self.preprocessing_stats['total_predictions'], 1)) * 100
        }
        
        return {
            'preprocessing_stats': self.preprocessing_stats,
            'user_pattern_analysis': user_pattern_analysis,
            'cache_analysis': cache_analysis,
            'performance_metrics': performance_metrics,
            'configuration': {
                'background_processing': self.background_processing,
                'prediction_cache_size': self.prediction_cache_size,
                'pattern_update_interval': self.pattern_update_interval,
                'background_active': self.background_active
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def clear_user_patterns(self, user_id: str = None):
        """Limpia patrones de usuario específico o todos."""
        if user_id:
            if user_id in self.user_patterns:
                del self.user_patterns[user_id]
                self.logger.info(f"Patrones del usuario {user_id} eliminados")
        else:
            self.user_patterns.clear()
            self.logger.info("Todos los patrones de usuario eliminados")
        
        # Limpiar cache relacionado
        self.prediction_cache.clear()
    
    def export_patterns(self, user_id: str = "default") -> Dict[str, Any]:
        """Exporta patrones de usuario para análisis."""
        if user_id not in self.user_patterns:
            return {}
        
        pattern = self.user_patterns[user_id]
        
        return {
            'user_id': user_id,
            'frequent_categories': pattern.frequent_categories,
            'category_sequences': pattern.category_sequences[-10:],  # Últimas 10
            'recurring_patterns': pattern.predict_recurring_patterns(),
            'common_keywords': dict(list(pattern.common_keywords.items())[:20]),  # Top 20
            'amount_ranges': pattern.amount_ranges,
            'exported_at': datetime.now().isoformat()
        }


# Instancia global del pre-procesador predictivo
_predictive_preprocessor_instance: Optional[PredictivePreprocessor] = None

def get_predictive_preprocessor(background_processing: bool = True,
                              prediction_cache_size: int = 1000,
                              pattern_update_interval: int = 300) -> PredictivePreprocessor:
    """
    Obtiene instancia singleton del pre-procesador predictivo.
    
    Args:
        background_processing: Habilitar procesamiento en background
        prediction_cache_size: Tamaño del cache de predicciones
        pattern_update_interval: Intervalo de actualización de patrones
        
    Returns:
        Instancia del pre-procesador predictivo
    """
    global _predictive_preprocessor_instance
    if _predictive_preprocessor_instance is None:
        _predictive_preprocessor_instance = PredictivePreprocessor(
            background_processing, prediction_cache_size, pattern_update_interval
        )
    return _predictive_preprocessor_instance


def shutdown_predictive_preprocessor():
    """Cierra el pre-procesador predictivo global."""
    global _predictive_preprocessor_instance
    if _predictive_preprocessor_instance:
        _predictive_preprocessor_instance.stop_background_processing()
        _predictive_preprocessor_instance = None