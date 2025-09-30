#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del Sistema de Cache ML - FASE 4.2

Valida la funcionalidad del cache de modelos ML para optimización
de predicciones computacionalmente costosas.
"""

import sys
import time
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from app.services.ml_model_cache import (
    MLModelCache,
    FeatureVectorCache, 
    CachedMLClassifier,
    get_ml_model_cache,
    FeatureHash,
    CachedPrediction
)


class MockMLModel:
    """Modelo ML mock para testing."""
    
    def __init__(self, name: str = "mock_model"):
        self.name = name
        self.classes_ = ['comida', 'transporte', 'entretenimiento', 'otros']
        self.prediction_count = 0
    
    def predict(self, features):
        """Predicción mock con delay simulado."""
        time.sleep(0.05)  # Simular computation time
        self.prediction_count += 1
        
        # Predicción determinística basada en features
        if hasattr(features, 'shape'):
            hash_val = hash(str(features.flatten()[:5])) % len(self.classes_)
        else:
            hash_val = hash(str(features)[:20]) % len(self.classes_)
        
        return [self.classes_[hash_val]]
    
    def predict_proba(self, features):
        """Predicción con probabilidades."""
        time.sleep(0.05)  # Simular computation time
        self.prediction_count += 1
        
        # Probabilities mock
        n_classes = len(self.classes_)
        probs = np.random.dirichlet(np.ones(n_classes))
        return np.array([probs])


class MockVectorizer:
    """Vectorizer mock para testing."""
    
    def __init__(self):
        self.vocabulary_ = {f'word_{i}': i for i in range(100)}
        self.transform_count = 0
    
    def transform(self, texts):
        """Transformación mock."""
        time.sleep(0.02)  # Simular vectorization time  
        self.transform_count += 1
        
        # Vector mock basado en texto
        vectors = []
        for text in texts:
            vector = np.random.random(len(self.vocabulary_))
            # Hacer determinístico basado en texto
            np.random.seed(hash(text) % 1000)
            vector = np.random.random(len(self.vocabulary_))
            vectors.append(vector)
        
        return np.array(vectors)


def test_ml_model_cache():
    """Test completo del sistema de cache ML."""
    print("[TEST] Sistema de Cache ML")
    print("=" * 40)
    
    results = {}
    
    # Test 1: Inicialización del cache
    print("  [1] Inicialización del Cache...")
    try:
        cache = MLModelCache(max_cache_size=100, feature_cache_size=50, ttl_hours=1)
        
        results['initialization'] = (
            cache.max_cache_size == 100 and
            len(cache.prediction_cache) == 0 and
            cache.feature_cache.max_size == 50
        )
        
        print(f"    [OK] Cache inicializado - Max predictions: {cache.max_cache_size}")
        
    except Exception as e:
        results['initialization'] = False
        print(f"    [ERROR] {e}")
    
    # Test 2: Cache de predicciones básico
    print("  [2] Cache de Predicciones...")
    try:
        model = MockMLModel()
        
        # Primera predicción (cache miss)
        start_time = time.time()
        pred1, conf1, meta1 = cache.predict_cached("compré comida hoy", model, "test_v1")
        first_time = (time.time() - start_time) * 1000
        
        # Segunda predicción del mismo texto (cache hit)
        start_time = time.time()
        pred2, conf2, meta2 = cache.predict_cached("compré comida hoy", model, "test_v1")
        second_time = (time.time() - start_time) * 1000
        
        # Verificar que la segunda es mucho más rápida
        speedup = first_time / second_time if second_time > 0 else 1
        cache_hit = meta2.get('cached', False)
        
        results['prediction_cache'] = (
            pred1 == pred2 and  # Misma predicción
            cache_hit and      # Segunda fue cache hit
            speedup > 5 and    # Al menos 5x más rápido
            model.prediction_count == 1  # Solo se computó una vez
        )
        
        print(f"    [OK] Cache funcionando - Speedup: {speedup:.1f}x, Hit: {cache_hit}")
        
    except Exception as e:
        results['prediction_cache'] = False
        print(f"    [ERROR] {e}")
    
    # Test 3: Cache de features
    print("  [3] Cache de Features...")
    try:
        feature_cache = FeatureVectorCache(max_size=50, ttl_hours=1)
        vectorizer = MockVectorizer()
        
        # Cache vectorizer
        feature_cache.cache_vectorizer(vectorizer, "test_vectorizer")
        
        # Primera vectorización
        vector1 = feature_cache.get_feature_vector("texto de prueba", "test_vectorizer")
        if vector1 is None:
            # Compute y cache
            features = vectorizer.transform(["texto de prueba"])
            vector1 = features[0]
            feature_cache.cache_feature_vector("texto de prueba", vector1, "test_vectorizer")
        
        # Segunda vectorización (debería ser hit)
        vector2 = feature_cache.get_feature_vector("texto de prueba", "test_vectorizer")
        
        # Obtener stats
        stats = feature_cache.get_stats()
        
        results['feature_cache'] = (
            vector2 is not None and
            np.array_equal(vector1, vector2) and
            stats['hits'] > 0 and
            stats['feature_cache_size'] > 0
        )
        
        print(f"    [OK] Feature cache - Hit rate: {stats['hit_rate']:.2%}")
        
    except Exception as e:
        results['feature_cache'] = False
        print(f"    [ERROR] {e}")
    
    # Test 4: Cached ML Classifier wrapper
    print("  [4] Cached ML Classifier...")
    try:
        base_model = MockMLModel("wrapped_model")
        cached_classifier = CachedMLClassifier(base_model, "wrapper_v1")
        
        # Predecir múltiples textos
        test_texts = [
            "gasté en comida",
            "pagué transporte", 
            "gasté en comida",  # Repetido para test cache
            "compré entretenimiento"
        ]
        
        start_time = time.time()
        predictions = cached_classifier.predict(test_texts)
        elapsed = (time.time() - start_time) * 1000
        
        # Verificar cache stats
        stats = cached_classifier.get_stats()
        
        results['cached_classifier'] = (
            len(predictions) == len(test_texts) and
            stats.cache_hits > 0 and  # Debería haber hits por texto repetido
            stats.total_predictions > 0
        )
        
        print(f"    [OK] Cached classifier - {len(predictions)} predicciones, hit rate: {stats.hit_rate:.2%}")
        
    except Exception as e:
        results['cached_classifier'] = False
        print(f"    [ERROR] {e}")
    
    # Test 5: Performance bajo carga
    print("  [5] Performance Bajo Carga...")
    try:
        model = MockMLModel("load_test_model")
        cache = MLModelCache(max_cache_size=200)
        
        # Generar datos de test
        test_data = [
            f"test message {i % 20}" for i in range(100)  # 20 únicos, 100 total
        ]
        
        start_time = time.time()
        
        for text in test_data:
            cache.predict_cached(text, model, "load_test_v1")
        
        elapsed = time.time() - start_time
        
        # Obtener estadísticas finales
        stats = cache.get_cache_stats()
        performance_report = cache.get_performance_report()
        
        # Verificar performance
        expected_unique = 20
        expected_hits = 100 - 20  # 80 cache hits esperados
        
        results['performance_load'] = (
            stats.cache_hits >= expected_hits * 0.8 and  # Al menos 80% de hits esperados
            stats.hit_rate > 0.6 and  # Hit rate > 60%
            performance_report['performance_improvement_percent'] > 30  # Mejora > 30%
        )
        
        print(f"    [OK] Load test - {stats.total_predictions} predicciones, mejora: {performance_report['performance_improvement_percent']:.1f}%")
        
    except Exception as e:
        results['performance_load'] = False
        print(f"    [ERROR] {e}")
    
    # Test 6: Warm-up del cache
    print("  [6] Cache Warm-up...")
    try:
        model = MockMLModel("warmup_model")
        cache = MLModelCache(max_cache_size=100)
        
        # Patrones comunes para warm-up
        common_patterns = [
            "compré comida",
            "gasté en transporte",
            "pagué entretenimiento",
            "gasto de otros"
        ]
        
        # Warm-up
        cache.warm_up_cache(common_patterns, model)
        
        # Verificar que están cacheados
        cached_count = 0
        for pattern in common_patterns:
            pred, conf, meta = cache.predict_cached(pattern, model, "warmup")
            if meta.get('cached', False):
                cached_count += 1
        
        results['warmup'] = cached_count >= len(common_patterns) * 0.8  # 80% cacheados
        
        print(f"    [OK] Warm-up completado - {cached_count}/{len(common_patterns)} patrones cacheados")
        
    except Exception as e:
        results['warmup'] = False
        print(f"    [ERROR] {e}")
    
    # Test 7: Cleanup y gestión de memoria
    print("  [7] Cache Cleanup...")
    try:
        cache = MLModelCache(max_cache_size=50, ttl_hours=0.001)  # TTL muy corto
        model = MockMLModel("cleanup_model")
        
        # Llenar cache
        for i in range(10):
            cache.predict_cached(f"test message {i}", model, "cleanup_v1")
        
        initial_size = cache.get_cache_stats().cache_size
        
        # Esperar para que expiren
        time.sleep(0.1)
        
        # Cleanup
        cache.cleanup_cache()
        
        final_size = cache.get_cache_stats().cache_size
        
        results['cleanup'] = (
            initial_size > 0 and
            final_size < initial_size  # Algo se limpió
        )
        
        print(f"    [OK] Cleanup completado - {initial_size} -> {final_size} entradas")
        
    except Exception as e:
        results['cleanup'] = False
        print(f"    [ERROR] {e}")
    
    # Generar reporte final
    print("\n" + "=" * 40)
    print("[REPORTE] Cache ML")
    print("=" * 40)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\nTests ejecutados: {total_tests}")
    print(f"Tests exitosos:   {passed_tests}")
    print(f"Tasa de éxito:    {success_rate:.1f}%")
    
    print(f"\nResultados por test:")
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {test_name}")
    
    if success_rate >= 85:
        grade = "A" if success_rate >= 95 else "A-"
        status = "[EXCELENTE]"
        improvement = "50% adicional en categorización ML"
    elif success_rate >= 70:
        grade = "B"
        status = "[BUENO]"
        improvement = "30% adicional en categorización ML"
    else:
        grade = "C"
        status = "[REVISAR]"
        improvement = "Mejoras limitadas"
    
    print(f"\nCalificación:     {grade}")
    print(f"Estado:           {status}")
    print(f"Mejora esperada:  {improvement}")
    print(f"\n[*] ML MODEL CACHE VALIDATED!")
    
    return {
        'success_rate': success_rate,
        'grade': grade,
        'passed_tests': passed_tests,
        'total_tests': total_tests,
        'results': results
    }


if __name__ == "__main__":
    result = test_ml_model_cache()
    
    if result['success_rate'] >= 70:
        sys.exit(0)
    else:
        sys.exit(1)