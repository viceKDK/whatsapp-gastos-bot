"""
Sistema de Métricas y Monitoreo de Performance

Recolecta, almacena y analiza métricas de performance del bot en tiempo real.
"""

import time
import json
import threading
import psutil
import queue
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from functools import wraps
import sqlite3
import statistics

from config.config_manager import get_config
from shared.logger import get_logger


logger = get_logger(__name__)


@dataclass
class MetricPoint:
    """Punto de métrica individual."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags
        }


@dataclass
class PerformanceMetrics:
    """Métricas de performance de una operación."""
    operation: str
    duration_seconds: float
    memory_usage_mb: float
    cpu_percent: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_metric_points(self) -> List[MetricPoint]:
        """Convierte a puntos de métrica."""
        timestamp = datetime.now()
        base_tags = {
            'operation': self.operation,
            'success': str(self.success)
        }
        
        if self.metadata:
            base_tags.update({k: str(v) for k, v in self.metadata.items()})
        
        points = [
            MetricPoint('operation_duration', self.duration_seconds, timestamp, base_tags),
            MetricPoint('memory_usage', self.memory_usage_mb, timestamp, base_tags),
            MetricPoint('cpu_usage', self.cpu_percent, timestamp, base_tags),
        ]
        
        return points


class MetricsCollector:
    """Recolector de métricas del sistema."""
    
    def __init__(self):
        self.logger = logger
        self._start_time = time.time()
        self._metrics_queue = queue.Queue()
        self._running = False
        self._thread = None
        self._process = psutil.Process()
        
        # Contadores
        self._operation_counts = defaultdict(int)
        self._error_counts = defaultdict(int)
        self._response_times = defaultdict(list)
        
        # Historia de métricas (en memoria)
        self._metric_history = defaultdict(lambda: deque(maxlen=1000))
        
        # Base de datos para persistencia
        self.config = get_config()
        self.db_path = Path(self.config.performance.metrics_file).with_suffix('.db')
        self._init_database()
    
    def _init_database(self):
        """Inicializa base de datos de métricas."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        value REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        tags TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error inicializando base de datos de métricas: {e}")
    
    def start(self):
        """Inicia recolección de métricas."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._collector_loop, daemon=True)
        self._thread.start()
        self.logger.info("Recolector de métricas iniciado")
    
    def stop(self):
        """Detiene recolección de métricas."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Recolector de métricas detenido")
    
    def _collector_loop(self):
        """Loop principal del recolector."""
        while self._running:
            try:
                # Recopilar métricas del sistema
                self._collect_system_metrics()
                
                # Procesar métricas de la cola
                self._process_metrics_queue()
                
                # Limpiar métricas antiguas
                self._cleanup_old_metrics()
                
                time.sleep(5)  # Recopilar cada 5 segundos
                
            except Exception as e:
                self.logger.error(f"Error en loop de recolector: {e}")
                time.sleep(1)
    
    def _collect_system_metrics(self):
        """Recopila métricas del sistema."""
        try:
            # Métricas de proceso
            memory_info = self._process.memory_info()
            cpu_percent = self._process.cpu_percent()
            
            timestamp = datetime.now()
            
            # Crear puntos de métrica
            metrics = [
                MetricPoint('process_memory_mb', memory_info.rss / 1024 / 1024, timestamp, {}),
                MetricPoint('process_cpu_percent', cpu_percent, timestamp, {}),
                MetricPoint('uptime_seconds', time.time() - self._start_time, timestamp, {}),
            ]
            
            # Métricas del sistema
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent()
            
            metrics.extend([
                MetricPoint('system_memory_percent', system_memory.percent, timestamp, {}),
                MetricPoint('system_cpu_percent', system_cpu, timestamp, {}),
                MetricPoint('system_memory_available_mb', system_memory.available / 1024 / 1024, timestamp, {}),
            ])
            
            # Enviar a cola para persistencia
            for metric in metrics:
                self._metrics_queue.put(metric)
                
            # Mantener en historia
            for metric in metrics:
                self._metric_history[metric.name].append((metric.timestamp, metric.value))
                
        except Exception as e:
            self.logger.error(f"Error recopilando métricas del sistema: {e}")
    
    def _process_metrics_queue(self):
        """Procesa métricas de la cola."""
        metrics_batch = []
        
        # Recopilar hasta 100 métricas de la cola
        for _ in range(100):
            try:
                metric = self._metrics_queue.get_nowait()
                metrics_batch.append(metric)
            except queue.Empty:
                break
        
        if metrics_batch:
            self._persist_metrics(metrics_batch)
    
    def _persist_metrics(self, metrics: List[MetricPoint]):
        """Persiste métricas en base de datos."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                for metric in metrics:
                    conn.execute('''
                        INSERT INTO metrics (name, value, timestamp, tags)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        metric.name,
                        metric.value,
                        metric.timestamp.isoformat(),
                        json.dumps(metric.tags)
                    ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error persistiendo métricas: {e}")
    
    def _cleanup_old_metrics(self):
        """Limpia métricas antiguas."""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)  # Mantener 7 días
            
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    DELETE FROM metrics 
                    WHERE timestamp < ?
                ''', (cutoff_date.isoformat(),))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error limpiando métricas antiguas: {e}")
    
    def record_operation(self, operation: str, duration: float, success: bool = True, **metadata):
        """
        Registra una operación.
        
        Args:
            operation: Nombre de la operación
            duration: Duración en segundos
            success: Si fue exitosa
            **metadata: Metadatos adicionales
        """
        try:
            # Actualizar contadores
            self._operation_counts[operation] += 1
            if not success:
                self._error_counts[operation] += 1
            
            # Mantener tiempos de respuesta
            self._response_times[operation].append(duration)
            if len(self._response_times[operation]) > 100:
                self._response_times[operation].pop(0)
            
            # Crear métrica
            memory_usage = self._process.memory_info().rss / 1024 / 1024
            cpu_percent = self._process.cpu_percent()
            
            perf_metrics = PerformanceMetrics(
                operation=operation,
                duration_seconds=duration,
                memory_usage_mb=memory_usage,
                cpu_percent=cpu_percent,
                success=success,
                metadata=metadata
            )
            
            # Enviar métricas a cola
            for metric_point in perf_metrics.to_metric_points():
                self._metrics_queue.put(metric_point)
                
        except Exception as e:
            self.logger.error(f"Error registrando operación: {e}")
    
    def record_custom_metric(self, name: str, value: float, **tags):
        """
        Registra una métrica personalizada.
        
        Args:
            name: Nombre de la métrica
            value: Valor numérico
            **tags: Tags adicionales
        """
        try:
            metric = MetricPoint(name, value, datetime.now(), tags)
            self._metrics_queue.put(metric)
            self._metric_history[name].append((metric.timestamp, value))
            
        except Exception as e:
            self.logger.error(f"Error registrando métrica personalizada: {e}")
    
    def get_operation_stats(self, operation: str = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de operaciones.
        
        Args:
            operation: Operación específica (todas si None)
            
        Returns:
            Estadísticas de operaciones
        """
        try:
            if operation:
                operations = {operation: self._operation_counts.get(operation, 0)}
            else:
                operations = dict(self._operation_counts)
            
            stats = {}
            for op, count in operations.items():
                response_times = self._response_times.get(op, [])
                error_count = self._error_counts.get(op, 0)
                
                stats[op] = {
                    'total_calls': count,
                    'error_count': error_count,
                    'success_rate': (count - error_count) / count if count > 0 else 0,
                    'avg_response_time': statistics.mean(response_times) if response_times else 0,
                    'min_response_time': min(response_times) if response_times else 0,
                    'max_response_time': max(response_times) if response_times else 0,
                    'p95_response_time': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Obtiene estado de salud del sistema.
        
        Returns:
            Estado de salud
        """
        try:
            memory_info = self._process.memory_info()
            cpu_percent = self._process.cpu_percent()
            
            # Obtener métricas recientes
            recent_metrics = self._get_recent_metrics(minutes=5)
            
            # Calcular promedios
            avg_memory = statistics.mean([m[1] for m in recent_metrics.get('process_memory_mb', [])] or [0])
            avg_cpu = statistics.mean([m[1] for m in recent_metrics.get('process_cpu_percent', [])] or [0])
            
            # Verificar thresholds de alerta
            config = get_config()
            thresholds = config.performance.alert_thresholds
            
            alerts = []
            if avg_memory > thresholds['memory_usage_mb']:
                alerts.append(f"Uso de memoria alto: {avg_memory:.1f}MB")
            
            if any(rt > thresholds['processing_time_seconds'] for rt_list in self._response_times.values() for rt in rt_list):
                alerts.append("Tiempos de respuesta lentos detectados")
            
            # Calcular tasa de errores
            total_ops = sum(self._operation_counts.values())
            total_errors = sum(self._error_counts.values())
            error_rate = (total_errors / total_ops * 100) if total_ops > 0 else 0
            
            if error_rate > thresholds['error_rate_percentage']:
                alerts.append(f"Tasa de errores alta: {error_rate:.1f}%")
            
            health_status = 'healthy' if not alerts else 'warning' if len(alerts) <= 2 else 'critical'
            
            return {
                'status': health_status,
                'uptime_seconds': time.time() - self._start_time,
                'current_memory_mb': memory_info.rss / 1024 / 1024,
                'current_cpu_percent': cpu_percent,
                'average_memory_mb': avg_memory,
                'average_cpu_percent': avg_cpu,
                'total_operations': total_ops,
                'total_errors': total_errors,
                'error_rate_percent': error_rate,
                'alerts': alerts,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de salud: {e}")
            return {'status': 'unknown', 'error': str(e)}
    
    def _get_recent_metrics(self, minutes: int = 5) -> Dict[str, List]:
        """Obtiene métricas recientes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent = {}
        
        for metric_name, history in self._metric_history.items():
            recent_points = [(timestamp, value) for timestamp, value in history 
                           if timestamp >= cutoff_time]
            recent[metric_name] = recent_points
        
        return recent
    
    def export_metrics(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Exporta métricas para un rango de tiempo.
        
        Args:
            start_time: Tiempo de inicio
            end_time: Tiempo final
            
        Returns:
            Lista de métricas
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute('''
                    SELECT name, value, timestamp, tags
                    FROM metrics
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                ''', (start_time.isoformat(), end_time.isoformat()))
                
                metrics = []
                for row in cursor.fetchall():
                    metrics.append({
                        'name': row[0],
                        'value': row[1],
                        'timestamp': row[2],
                        'tags': json.loads(row[3]) if row[3] else {}
                    })
                
                return metrics
                
        except Exception as e:
            self.logger.error(f"Error exportando métricas: {e}")
            return []


class MetricsReporter:
    """Generador de reportes de métricas."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.logger = logger
    
    def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """
        Genera reporte diario.
        
        Args:
            date: Fecha del reporte (hoy si None)
            
        Returns:
            Reporte diario
        """
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_time = date
        end_time = date + timedelta(days=1)
        
        try:
            # Obtener métricas del día
            metrics = self.collector.export_metrics(start_time, end_time)
            
            # Procesar métricas
            operations = defaultdict(list)
            system_metrics = defaultdict(list)
            
            for metric in metrics:
                if metric['name'] == 'operation_duration':
                    operation = metric['tags'].get('operation', 'unknown')
                    operations[operation].append(metric)
                elif metric['name'].startswith('process_') or metric['name'].startswith('system_'):
                    system_metrics[metric['name']].append(metric['value'])
            
            # Calcular estadísticas
            operation_stats = {}
            for operation, op_metrics in operations.items():
                durations = [m['value'] for m in op_metrics]
                success_count = len([m for m in op_metrics if m['tags'].get('success') == 'True'])
                
                operation_stats[operation] = {
                    'total_calls': len(durations),
                    'success_count': success_count,
                    'success_rate': success_count / len(durations) if durations else 0,
                    'avg_duration': statistics.mean(durations) if durations else 0,
                    'max_duration': max(durations) if durations else 0,
                    'min_duration': min(durations) if durations else 0
                }
            
            system_stats = {}
            for metric_name, values in system_metrics.items():
                if values:
                    system_stats[metric_name] = {
                        'avg': statistics.mean(values),
                        'max': max(values),
                        'min': min(values),
                        'count': len(values)
                    }
            
            return {
                'date': date.isoformat(),
                'operation_stats': operation_stats,
                'system_stats': system_stats,
                'total_metrics': len(metrics),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generando reporte diario: {e}")
            return {'error': str(e)}


# Instancia global del recolector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Obtiene instancia global del recolector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
        _metrics_collector.start()
    return _metrics_collector


def performance_monitor(operation_name: str = None):
    """
    Decorador para monitorear performance de funciones.
    
    Args:
        operation_name: Nombre de la operación
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            collector = get_metrics_collector()
            
            start_time = time.time()
            success = True
            error_msg = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_msg = str(e)
                raise
            finally:
                duration = time.time() - start_time
                collector.record_operation(
                    operation=op_name,
                    duration=duration,
                    success=success,
                    error_message=error_msg
                )
        
        return wrapper
    return decorator


def record_metric(name: str, value: float, **tags):
    """
    Función de conveniencia para registrar una métrica.
    
    Args:
        name: Nombre de la métrica
        value: Valor
        **tags: Tags adicionales
    """
    try:
        collector = get_metrics_collector()
        collector.record_custom_metric(name, value, **tags)
    except Exception as e:
        logger.error(f"Error registrando métrica: {e}")


def get_system_health() -> Dict[str, Any]:
    """
    Función de conveniencia para obtener estado de salud.
    
    Returns:
        Estado de salud del sistema
    """
    try:
        collector = get_metrics_collector()
        return collector.get_system_health()
    except Exception as e:
        logger.error(f"Error obteniendo estado de salud: {e}")
        return {'status': 'error', 'error': str(e)}


# ⚡ OPTIMIZACIÓN: Métricas específicas según el documento de optimización
PERFORMANCE_METRICS_OPTIMIZED = {
    'regex_processing_time_ms': 'histogram',
    'dom_search_time_ms': 'histogram', 
    'nlp_categorization_time_ms': 'histogram',
    'db_write_time_ms': 'histogram',
    'message_parsing_time_ms': 'histogram',
    'batch_processing_time_ms': 'histogram',
    'cache_lookup_time_ms': 'histogram',
    'cache_hit_rate': 'gauge',
    'messages_per_second': 'gauge'
}


class OptimizationMetricsCollector:
    """⚡ Collector especializado para métricas de optimización."""
    
    def __init__(self):
        self.base_collector = get_metrics_collector()
        self.optimization_baselines = {
            # Baselines pre-optimización (ms)
            'regex_processing_time_ms': 150.0,
            'dom_search_time_ms': 300.0,
            'nlp_categorization_time_ms': 300.0,
            'db_write_time_ms': 200.0,
            'message_parsing_time_ms': 100.0,
            'batch_processing_time_ms': 500.0,
            'cache_lookup_time_ms': 50.0,
        }
        
        self.improvement_tracking = defaultdict(list)
        self.logger = logger
    
    def record_optimization_metric(self, metric_name: str, value_ms: float, **tags):
        """
        ⚡ Registra métrica de optimización con cálculo automático de mejora.
        
        Args:
            metric_name: Nombre de la métrica (ej: 'regex_processing_time_ms')
            value_ms: Valor en milisegundos
            **tags: Tags adicionales
        """
        # Registrar en sistema base
        self.base_collector.record_custom_metric(metric_name, value_ms, **tags)
        
        # Calcular mejora vs baseline
        baseline = self.optimization_baselines.get(metric_name)
        if baseline:
            improvement_pct = ((baseline - value_ms) / baseline) * 100
            speedup = baseline / value_ms if value_ms > 0 else 1.0
            
            # Trackear mejora
            self.improvement_tracking[metric_name].append({
                'timestamp': datetime.now(),
                'value_ms': value_ms,
                'baseline_ms': baseline,
                'improvement_pct': improvement_pct,
                'speedup_factor': speedup
            })
            
            # Registrar métricas de mejora
            self.base_collector.record_custom_metric(
                f"{metric_name}_improvement_pct", 
                improvement_pct, 
                optimization=metric_name, **tags
            )
            self.base_collector.record_custom_metric(
                f"{metric_name}_speedup_factor", 
                speedup, 
                optimization=metric_name, **tags
            )
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """🎯 Obtiene resumen completo de optimizaciones."""
        summary = {}
        
        for metric_name, tracking_data in self.improvement_tracking.items():
            if tracking_data:
                recent_data = tracking_data[-10:]  # Últimos 10 valores
                
                avg_improvement = statistics.mean([d['improvement_pct'] for d in recent_data])
                avg_speedup = statistics.mean([d['speedup_factor'] for d in recent_data])
                current_value = recent_data[-1]['value_ms']
                baseline_value = recent_data[-1]['baseline_ms']
                
                summary[metric_name] = {
                    'current_avg_ms': current_value,
                    'baseline_ms': baseline_value,
                    'improvement_percent': f"{avg_improvement:.1f}%",
                    'speedup_factor': f"{avg_speedup:.1f}x",
                    'samples_count': len(recent_data),
                    'status': self._get_optimization_status(avg_improvement)
                }
        
        return {
            'optimization_summary': summary,
            'overall_status': self._get_overall_status(summary),
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_optimization_status(self, improvement_pct: float) -> str:
        """Determina estado de la optimización."""
        if improvement_pct >= 50:
            return "excellent"
        elif improvement_pct >= 25:
            return "good"
        elif improvement_pct >= 10:
            return "moderate"
        elif improvement_pct >= 0:
            return "minimal"
        else:
            return "degraded"
    
    def _get_overall_status(self, summary: Dict) -> str:
        """Determina estado general de optimizaciones."""
        if not summary:
            return "no_data"
        
        statuses = [opt['status'] for opt in summary.values() if isinstance(opt, dict)]
        excellent_count = statuses.count('excellent')
        good_count = statuses.count('good')
        
        if excellent_count >= len(statuses) * 0.7:
            return "highly_optimized"
        elif (excellent_count + good_count) >= len(statuses) * 0.6:
            return "well_optimized"
        else:
            return "needs_improvement"


# Instancia global del collector de optimizaciones
_optimization_collector: Optional[OptimizationMetricsCollector] = None

def get_optimization_collector() -> OptimizationMetricsCollector:
    """Obtiene instancia global del collector de optimizaciones."""
    global _optimization_collector
    if _optimization_collector is None:
        _optimization_collector = OptimizationMetricsCollector()
    return _optimization_collector