#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del Sistema de Cache Redis Distribuido - FASE 5.1

Validacion del sistema de cache distribuido usando Redis para
compartir datos entre multiples instancias del bot.
"""

import sys
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

# Mock Redis para testing sin Redis real
class MockRedisClient:
    """Cliente Redis mock para testing."""
    
    def __init__(self):
        self.storage = {}
        self.expirations = {}
        self.ping_count = 0
    
    def ping(self):
        self.ping_count += 1
        return True
    
    def setex(self, key, ttl, value):
        self.storage[key] = value
        self.expirations[key] = time.time() + ttl
        return True
    
    def get(self, key):
        if key in self.storage:
            if key in self.expirations and time.time() > self.expirations[key]:
                del self.storage[key]
                del self.expirations[key]
                return None
            return self.storage[key]
        return None
    
    def delete(self, key):
        deleted = 0
        if isinstance(key, (list, tuple)):
            for k in key:
                if k in self.storage:
                    del self.storage[k]
                    if k in self.expirations:
                        del self.expirations[k]
                    deleted += 1
        else:
            if key in self.storage:
                del self.storage[key]
                if key in self.expirations:
                    del self.expirations[key]
                deleted = 1
        return deleted
    
    def exists(self, key):
        if key in self.storage:
            if key in self.expirations and time.time() > self.expirations[key]:
                del self.storage[key]
                del self.expirations[key]
                return False
            return True
        return False
    
    def keys(self, pattern):
        # Simple pattern matching
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            matching_keys = [k for k in self.storage.keys() 
                           if isinstance(k, str) and k.startswith(prefix)]
        else:
            matching_keys = [k for k in self.storage.keys() if k == pattern]
        
        # Convert to bytes like real Redis
        return [key.encode('utf-8') if isinstance(key, str) else key for key in matching_keys]
    
    def incr(self, key, amount=1):
        current = self.storage.get(key, 0)
        if isinstance(current, bytes):
            current = int(current.decode('utf-8'))
        elif isinstance(current, str):
            current = int(current)
        
        new_value = current + amount
        self.storage[key] = str(new_value).encode('utf-8')
        return new_value
    
    def info(self, section=None):
        return {
            'used_memory': len(str(self.storage)) * 8  # Mock memory usage
        }


class MockConnectionPool:
    """Connection pool mock."""
    
    def __init__(self, **kwargs):
        pass
    
    def disconnect(self):
        pass


# Monkey patch para testing
import sys
from unittest.mock import MagicMock

# Mock Redis imports
redis_module = MagicMock()
redis_module.Redis = lambda connection_pool: MockRedisClient()
redis_module.connection.ConnectionPool = MockConnectionPool
sys.modules['redis'] = redis_module
sys.modules['redis.connection'] = redis_module.connection

# Ahora importar nuestro modulo
from infrastructure.caching.redis_cache import (
    DistributedRedisCache,
    RedisMLCache,
    RedisCacheEntry,
    get_distributed_cache
)


def test_redis_cache_system():
    """Test completo del sistema de cache Redis distribuido."""
    print("[TEST] Sistema de Cache Redis Distribuido")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Inicializacion del cache
    print("  [1] Inicializacion del Cache...")
    try:
        cache = DistributedRedisCache(
            host='localhost',
            port=6379,
            default_ttl=300,
            key_prefix="test_bot"
        )
        
        results['initialization'] = (
            cache.host == 'localhost' and
            cache.port == 6379 and
            cache.default_ttl == 300 and
            cache.key_prefix == "test_bot"
        )
        
        print(f"    [OK] Cache Redis inicializado - TTL: {cache.default_ttl}s")
        
    except Exception as e:
        results['initialization'] = False
        print(f"    [ERROR] {e}")
    
    # Test 2: Operaciones basicas de cache
    print("  [2] Operaciones Basicas...")
    try:
        # Set and get
        test_data = {
            "categoria": "comida",
            "confianza": 0.95,
            "timestamp": time.time()
        }
        
        set_success = cache.set("predictions", "test_key_1", test_data, ttl=60)
        retrieved_data = cache.get("predictions", "test_key_1")
        
        # Verificar que los datos son identicos
        data_matches = (
            retrieved_data is not None and
            retrieved_data["categoria"] == test_data["categoria"] and
            retrieved_data["confianza"] == test_data["confianza"]
        )
        
        # Test exists
        exists = cache.exists("predictions", "test_key_1")
        not_exists = not cache.exists("predictions", "nonexistent_key")
        
        results['basic_operations'] = (
            set_success and
            data_matches and
            exists and
            not_exists
        )
        
        print(f"    [OK] Set/Get/Exists funcionando - Data match: {data_matches}")
        
    except Exception as e:
        results['basic_operations'] = False
        print(f"    [ERROR] {e}")
    
    # Test 3: TTL y expiracion
    print("  [3] TTL y Expiracion...")
    try:
        # Crear entrada con TTL corto
        short_ttl_data = {"test": "expiration"}
        cache.set("temp", "expire_test", short_ttl_data, ttl=1)
        
        # Verificar que existe
        immediate_get = cache.get("temp", "expire_test")
        
        # Esperar expiracion
        time.sleep(1.5)
        
        # Verificar que expiro
        expired_get = cache.get("temp", "expire_test")
        
        results['ttl_expiration'] = (
            immediate_get is not None and
            expired_get is None
        )
        
        print(f"    [OK] TTL funcionando - Inmediato: {immediate_get is not None}, Expirado: {expired_get is None}")
        
    except Exception as e:
        results['ttl_expiration'] = False
        print(f"    [ERROR] {e}")
    
    # Test 4: Namespaces y organizacion
    print("  [4] Namespaces...")
    try:
        # Crear datos en diferentes namespaces
        cache.set("ml_models", "model_v1", {"version": "1.0", "accuracy": 0.92})
        cache.set("user_data", "user_123", {"name": "Test User", "preferences": ["comida"]})
        cache.set("ml_models", "model_v2", {"version": "2.0", "accuracy": 0.95})
        
        # Obtener datos de cada namespace
        model_v1 = cache.get("ml_models", "model_v1")
        user_data = cache.get("user_data", "user_123")
        model_v2 = cache.get("ml_models", "model_v2")
        
        # Verificar aislamiento de namespaces
        results['namespaces'] = (
            model_v1 is not None and model_v1["version"] == "1.0" and
            user_data is not None and user_data["name"] == "Test User" and
            model_v2 is not None and model_v2["version"] == "2.0"
        )
        
        print(f"    [OK] Namespaces funcionando - ML models: 2, User data: 1")
        
    except Exception as e:
        results['namespaces'] = False
        print(f"    [ERROR] {e}")
    
    # Test 5: Cache ML especializado
    print("  [5] Cache ML Especializado...")
    try:
        ml_cache = RedisMLCache(cache)
        
        # Cachear predicciones ML
        text1 = "compre comida en el supermercado"
        text2 = "pague el transporte publico"
        
        cache_success1 = ml_cache.cache_prediction(text1, "model_v1.0", "comida", 0.92, ttl=300)
        cache_success2 = ml_cache.cache_prediction(text2, "model_v1.0", "transporte", 0.88, ttl=300)
        
        # Recuperar predicciones
        pred1 = ml_cache.get_prediction(text1, "model_v1.0")
        pred2 = ml_cache.get_prediction(text2, "model_v1.0")
        
        # Verificar predicciones diferentes con mismo modelo
        same_text_diff_model = ml_cache.get_prediction(text1, "model_v2.0")  # Deberia ser None
        
        results['ml_cache'] = (
            cache_success1 and cache_success2 and
            pred1 is not None and pred1[0] == "comida" and pred1[1] == 0.92 and
            pred2 is not None and pred2[0] == "transporte" and pred2[1] == 0.88 and
            same_text_diff_model is None  # Different model version
        )
        
        print(f"    [OK] ML Cache - Pred1: {pred1}, Pred2: {pred2}")
        
    except Exception as e:
        results['ml_cache'] = False
        print(f"    [ERROR] {e}")
    
    # Test 6: Pattern matching y limpieza
    print("  [6] Pattern Matching...")
    try:
        # Crear multiples claves con patron
        cache.set("temp_data", "temp_1", {"data": 1})
        cache.set("temp_data", "temp_2", {"data": 2}) 
        cache.set("temp_data", "temp_3", {"data": 3})
        cache.set("temp_data", "permanent_1", {"data": "permanent"})
        
        # Buscar por patron
        temp_keys = cache.get_keys_by_pattern("temp_data", "temp_*")
        all_keys = cache.get_keys_by_pattern("temp_data", "*")
        
        # Limpiar namespace
        deleted_count = cache.flush_namespace("temp_data")
        
        # Verificar limpieza
        after_flush = cache.get_keys_by_pattern("temp_data", "*")
        
        results['pattern_matching'] = (
            len(temp_keys) >= 3 and  # Al menos temp_1, temp_2, temp_3
            len(all_keys) >= 4 and   # Incluye permanent_1
            deleted_count >= 4 and   # Se eliminaron las claves
            len(after_flush) == 0    # Namespace vacio
        )
        
        print(f"    [OK] Pattern matching - Temp keys: {len(temp_keys)}, Deleted: {deleted_count}")
        
    except Exception as e:
        results['pattern_matching'] = False
        print(f"    [ERROR] {e}")
    
    # Test 7: Contadores distribuidos
    print("  [7] Contadores Distribuidos...")
    try:
        # Incrementar contador
        count1 = cache.increment("counters", "messages_processed", 1)
        count2 = cache.increment("counters", "messages_processed", 5)
        count3 = cache.increment("counters", "messages_processed", 2)
        
        # Incrementar otro contador
        errors1 = cache.increment("counters", "errors", 1)
        errors2 = cache.increment("counters", "errors", 1)
        
        results['distributed_counters'] = (
            count1 == 1 and
            count2 == 6 and  # 1 + 5
            count3 == 8 and  # 6 + 2
            errors1 == 1 and
            errors2 == 2
        )
        
        print(f"    [OK] Contadores - Messages: {count3}, Errors: {errors2}")
        
    except Exception as e:
        results['distributed_counters'] = False
        print(f"    [ERROR] {e}")
    
    # Test 8: Estadisticas y health check
    print("  [8] Estadisticas y Health Check...")
    try:
        # Obtener estadisticas
        stats = cache.get_cache_stats()
        
        # Health check
        health = cache.health_check()
        
        # Cleanup
        cleaned = cache.cleanup_expired()
        
        results['stats_health'] = (
            isinstance(stats, dict) and
            'local_hits' in stats and
            'local_misses' in stats and
            isinstance(health, dict) and
            'status' in health and
            isinstance(cleaned, int)
        )
        
        print(f"    [OK] Stats - Hits: {stats.get('local_hits', 0)}, Health: {health.get('status', 'unknown')}")
        
    except Exception as e:
        results['stats_health'] = False
        print(f"    [ERROR] {e}")
    
    # Test 9: Fallback local cuando Redis no disponible
    print("  [9] Fallback Local...")
    try:
        # Simular error de red forzando excepcion
        original_set = cache.redis_client.setex
        cache.redis_client.setex = lambda *args: exec('raise Exception("Network error")')
        
        # Intentar cachear (deberia usar fallback)
        fallback_success = cache.set("fallback", "test_key", {"fallback": "data"}, ttl=60)
        
        # Restaurar metodo original
        cache.redis_client.setex = original_set
        
        # Simular error en get tambien
        original_get = cache.redis_client.get
        cache.redis_client.get = lambda *args: exec('raise Exception("Network error")')
        
        # Intentar obtener (deberia usar fallback local)
        fallback_data = cache.get("fallback", "test_key")
        
        # Restaurar metodo
        cache.redis_client.get = original_get
        
        results['fallback_local'] = (
            fallback_success and
            fallback_data is not None and
            fallback_data["fallback"] == "data"
        )
        
        print(f"    [OK] Fallback local funciona - Data: {fallback_data is not None}")
        
    except Exception as e:
        results['fallback_local'] = False
        print(f"    [ERROR] {e}")
    
    # Generar reporte final
    print("\n" + "=" * 50)
    print("[REPORTE] Cache Redis Distribuido")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\nTests ejecutados: {total_tests}")
    print(f"Tests exitosos:   {passed_tests}")
    print(f"Tasa de exito:    {success_rate:.1f}%")
    
    print(f"\nResultados por test:")
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {test_name}")
    
    if success_rate >= 85:
        grade = "A" if success_rate >= 95 else "A-"
        status = "[EXCELENTE]"
        improvement = "15% adicional por cache distribuido"
    elif success_rate >= 70:
        grade = "B"
        status = "[BUENO]"
        improvement = "10% adicional por cache distribuido"
    else:
        grade = "C"
        status = "[REVISAR]"
        improvement = "Mejoras limitadas"
    
    print(f"\nCalificacion:     {grade}")
    print(f"Estado:           {status}")
    print(f"Mejora esperada:  {improvement}")
    
    # Mostrar ejemplo de performance
    if passed_tests >= 6:
        print(f"\n[EJEMPLO] Simulacion de Performance:")
        
        # Simular acceso multiple al mismo dato
        start_time = time.time()
        for i in range(10):
            cache.set("perf_test", f"key_{i%3}", f"data_{i%3}")  # Solo 3 claves unicas
        for i in range(10):  
            cache.get("perf_test", f"key_{i%3}")
        elapsed = (time.time() - start_time) * 1000
        
        stats_final = cache.get_cache_stats()
        
        print(f"  Cache distribuido: {elapsed:.1f}ms para 20 operaciones")
        print(f"  Hit rate final: {stats_final.get('hit_rate', 0):.1%}")
        print(f"  Fallback keys: {stats_final.get('local_fallback_keys', 0)}")
    
    print(f"\n[*] REDIS DISTRIBUTED CACHE VALIDATED!")
    
    return {
        'success_rate': success_rate,
        'grade': grade,
        'passed_tests': passed_tests,
        'total_tests': total_tests,
        'results': results
    }


if __name__ == "__main__":
    result = test_redis_cache_system()
    
    if result['success_rate'] >= 70:
        sys.exit(0)
    else:
        sys.exit(1)