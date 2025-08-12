"""
Sistema de Clustering y Load Balancing para Bot de Gastos WhatsApp (FASE 4.1)

Sistema avanzado de distribución de carga entre múltiples instancias del bot
para manejo óptimo de múltiples chats simultáneos y alta disponibilidad.
"""

import asyncio
import threading
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum
import queue
from pathlib import Path
import psutil

from shared.logger import get_logger
from shared.metrics import get_metrics_collector
from infrastructure.clustering.multi_chat_optimizer import (
    get_multi_chat_optimizer, 
    ChatPriority,
    MultiChatOptimizer
)


logger = get_logger(__name__)


class BotStatus(Enum):
    """Estados de una instancia del bot."""
    HEALTHY = "healthy"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class BotInstance:
    """Instancia individual del bot en el cluster."""
    instance_id: str
    profile_name: str
    status: BotStatus = BotStatus.OFFLINE
    current_load: int = 0
    max_load: int = 10
    last_heartbeat: datetime = field(default_factory=datetime.now)
    total_processed: int = 0
    error_count: int = 0
    average_response_time: float = 0.0
    
    # Performance metrics
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    def __post_init__(self):
        if not self.instance_id:
            self.instance_id = str(uuid.uuid4())[:8]
    
    @property
    def load_percentage(self) -> float:
        """Porcentaje de carga actual."""
        return (self.current_load / self.max_load) * 100
    
    @property
    def is_available(self) -> bool:
        """Si la instancia está disponible para nuevos mensajes."""
        return (self.status in [BotStatus.HEALTHY, BotStatus.BUSY] and 
                self.current_load < self.max_load)
    
    @property
    def health_score(self) -> float:
        """Score de salud (0-100) basado en múltiples métricas."""
        load_score = max(0, 100 - self.load_percentage)
        error_rate = (self.error_count / max(self.total_processed, 1)) * 100
        error_score = max(0, 100 - error_rate)
        
        # Penalizar por alta latencia
        latency_score = max(0, 100 - (self.average_response_time / 10))
        
        # Score compuesto
        return (load_score * 0.4 + error_score * 0.4 + latency_score * 0.2)
    
    def update_heartbeat(self):
        """Actualiza el timestamp de heartbeat."""
        self.last_heartbeat = datetime.now()
    
    def is_stale(self, timeout_seconds: int = 30) -> bool:
        """Si la instancia no ha reportado en X segundos."""
        return (datetime.now() - self.last_heartbeat).seconds > timeout_seconds


class MessageDistributionStrategy(Enum):
    """Estrategias de distribución de mensajes."""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    WEIGHTED_RANDOM = "weighted_random"
    HEALTH_BASED = "health_based"


@dataclass
class ClusterMessage:
    """Mensaje para procesamiento distribuido."""
    message_id: str
    chat_id: str
    message_text: str
    timestamp: datetime
    priority: int = 1
    retries: int = 0
    max_retries: int = 3
    assigned_instance: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __lt__(self, other):
        """Comparación para PriorityQueue."""
        if not isinstance(other, ClusterMessage):
            return NotImplemented
        
        # Primero por prioridad (menor valor = mayor prioridad)
        if self.priority != other.priority:
            return self.priority < other.priority
        
        # Después por timestamp (más antiguo primero)
        return self.created_at < other.created_at


class MessageDistributor:
    """⚡ Distribuidor inteligente de mensajes entre instancias."""
    
    def __init__(self, strategy: MessageDistributionStrategy = MessageDistributionStrategy.HEALTH_BASED):
        self.strategy = strategy
        self.round_robin_index = 0
        self.logger = logger
    
    def select_instance(self, instances: List[BotInstance], message: ClusterMessage) -> Optional[BotInstance]:
        """
        Selecciona la mejor instancia para procesar un mensaje.
        
        Args:
            instances: Lista de instancias disponibles
            message: Mensaje a procesar
            
        Returns:
            Instancia seleccionada o None si no hay disponibles
        """
        # Filtrar instancias disponibles
        available_instances = [inst for inst in instances if inst.is_available]
        
        if not available_instances:
            return None
        
        if self.strategy == MessageDistributionStrategy.ROUND_ROBIN:
            return self._round_robin_selection(available_instances)
        
        elif self.strategy == MessageDistributionStrategy.LEAST_LOADED:
            return self._least_loaded_selection(available_instances)
        
        elif self.strategy == MessageDistributionStrategy.HEALTH_BASED:
            return self._health_based_selection(available_instances)
        
        elif self.strategy == MessageDistributionStrategy.WEIGHTED_RANDOM:
            return self._weighted_random_selection(available_instances)
        
        return available_instances[0]  # Fallback
    
    def _round_robin_selection(self, instances: List[BotInstance]) -> BotInstance:
        """Selección round-robin simple."""
        selected = instances[self.round_robin_index % len(instances)]
        self.round_robin_index += 1
        return selected
    
    def _least_loaded_selection(self, instances: List[BotInstance]) -> BotInstance:
        """Selecciona la instancia con menor carga."""
        return min(instances, key=lambda inst: inst.current_load)
    
    def _health_based_selection(self, instances: List[BotInstance]) -> BotInstance:
        """Selecciona basado en health score (mejor estrategia)."""
        return max(instances, key=lambda inst: inst.health_score)
    
    def _weighted_random_selection(self, instances: List[BotInstance]) -> BotInstance:
        """Selección aleatoria ponderada por disponibilidad."""
        import random
        
        # Peso inversamente proporcional a la carga
        weights = [max(1, inst.max_load - inst.current_load) for inst in instances]
        return random.choices(instances, weights=weights)[0]


class WhatsAppCluster:
    """⚡ Sistema de clustering para Bot de Gastos WhatsApp (3x throughput esperado)."""
    
    def __init__(self, 
                 max_instances: int = 3,
                 distribution_strategy: MessageDistributionStrategy = MessageDistributionStrategy.HEALTH_BASED,
                 heartbeat_interval: int = 10,
                 enable_multi_chat: bool = True,
                 chat_balancing: bool = True):
        """
        Inicializa cluster de bots WhatsApp.
        
        Args:
            max_instances: Número máximo de instancias del bot
            distribution_strategy: Estrategia de distribución de mensajes
            heartbeat_interval: Intervalo de heartbeat en segundos
            enable_multi_chat: Habilita soporte para múltiples chats
            chat_balancing: Habilita balanceado por chat
        """
        self.max_instances = max_instances
        self.heartbeat_interval = heartbeat_interval
        self.enable_multi_chat = enable_multi_chat
        self.chat_balancing = chat_balancing
        
        # Instancias del cluster
        self.instances: Dict[str, BotInstance] = {}
        
        # Distribución de mensajes
        self.message_distributor = MessageDistributor(distribution_strategy)
        self.pending_messages = queue.PriorityQueue()
        
        # Multi-chat support
        self.chat_assignments: Dict[str, str] = {}  # chat_id -> instance_id
        self.chat_load_balance: Dict[str, int] = {}  # chat_id -> message_count
        self.instance_chats: Dict[str, List[str]] = {}  # instance_id -> [chat_ids]
        
        # Threading para operaciones asíncronas
        self.executor = ThreadPoolExecutor(max_workers=max_instances * 2, thread_name_prefix="Cluster")
        self.running = False
        
        # Monitoreo
        self.cluster_stats = {
            'total_messages_processed': 0,
            'total_messages_failed': 0,
            'average_cluster_load': 0.0,
            'active_instances': 0,
            'message_queue_size': 0,
            'active_chats': 0,
            'chat_distribution': {},
            'multi_chat_efficiency': 0.0
        }
        
        self.metrics_collector = get_metrics_collector()
        self.logger = logger
        
        # Multi-chat optimizer
        if self.enable_multi_chat:
            self.multi_chat_optimizer = get_multi_chat_optimizer()
        else:
            self.multi_chat_optimizer = None
        
        self.logger.info(f"WhatsAppCluster inicializado - Máx instancias: {max_instances}, Multi-chat: {enable_multi_chat}")
    
    def start_cluster(self):
        """⚡ Inicia el sistema de clustering."""
        if self.running:
            return
        
        self.running = True
        
        # Iniciar worker de distribución de mensajes
        self.executor.submit(self._message_distribution_worker)
        
        # Iniciar worker de monitoreo de salud
        self.executor.submit(self._health_monitoring_worker)
        
        # Iniciar worker de métricas
        self.executor.submit(self._metrics_collection_worker)
        
        # Iniciar multi-chat optimizer si está habilitado
        if self.multi_chat_optimizer:
            self.multi_chat_optimizer.start_monitoring()
        
        self.logger.info("✅ WhatsApp Cluster iniciado")
    
    def stop_cluster(self):
        """Detiene el cluster de manera segura."""
        self.logger.info("Deteniendo WhatsApp Cluster...")
        self.running = False
        
        # Detener multi-chat optimizer
        if self.multi_chat_optimizer:
            self.multi_chat_optimizer.stop_monitoring()
        
        # Procesar mensajes pendientes
        self._process_pending_messages()
        
        self.executor.shutdown(wait=True)
        self.logger.info("WhatsApp Cluster detenido")
    
    def register_instance(self, profile_name: str, max_load: int = 10) -> str:
        """
        Registra nueva instancia en el cluster.
        
        Args:
            profile_name: Nombre del perfil de Chrome
            max_load: Carga máxima que puede manejar
            
        Returns:
            ID de la instancia registrada
        """
        instance = BotInstance(
            instance_id=str(uuid.uuid4())[:8],
            profile_name=profile_name,
            status=BotStatus.HEALTHY,
            max_load=max_load
        )
        
        self.instances[instance.instance_id] = instance
        
        self.logger.info(f"🔗 Instancia registrada: {instance.instance_id} (perfil: {profile_name})")
        return instance.instance_id
    
    def unregister_instance(self, instance_id: str):
        """Desregistra instancia del cluster."""
        if instance_id in self.instances:
            del self.instances[instance_id]
            self.logger.info(f"❌ Instancia desregistrada: {instance_id}")
    
    def submit_message(self, chat_id: str, message_text: str, priority: int = 1) -> str:
        """
        ⚡ Envía mensaje para procesamiento distribuido.
        
        Args:
            chat_id: ID del chat
            message_text: Texto del mensaje
            priority: Prioridad (1=alta, 2=media, 3=baja)
            
        Returns:
            ID del mensaje encolado
        """
        message = ClusterMessage(
            message_id=str(uuid.uuid4())[:8],
            chat_id=chat_id,
            message_text=message_text,
            timestamp=datetime.now(),
            priority=priority
        )
        
        # Encolar con prioridad
        self.pending_messages.put((priority, time.time(), message))
        
        self.cluster_stats['message_queue_size'] = self.pending_messages.qsize()
        
        # Actualizar estadísticas multi-chat
        if self.enable_multi_chat and self.multi_chat_optimizer:
            self.cluster_stats['active_chats'] = len([c for c in self.multi_chat_optimizer.load_balancer.chat_metrics.values() if c.is_active])
            
            # Distribución de chats por instancia
            for instance_id, chats in self.instance_chats.items():
                self.cluster_stats['chat_distribution'][instance_id] = len(chats)
            
            # Eficiencia multi-chat
            optimization_report = self.multi_chat_optimizer.get_optimization_report()
            self.cluster_stats['multi_chat_efficiency'] = optimization_report['optimization_metrics']['load_distribution_score']
        
        self.logger.debug(f"📨 Mensaje encolado: {message.message_id} (prioridad {priority})")
        return message.message_id
    
    def _message_distribution_worker(self):
        """Worker que distribuye mensajes entre instancias."""
        self.logger.info("🚀 Message distribution worker iniciado")
        
        while self.running:
            try:
                # Obtener mensaje pendiente
                try:
                    priority, timestamp, message = self.pending_messages.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Seleccionar instancia óptima con balanceo multi-chat
                selected_instance = self._select_instance_for_chat(message)
                
                if not selected_instance:
                    # No hay instancias disponibles, re-encolar
                    self.pending_messages.put((priority + 1, time.time(), message))  # Menor prioridad
                    time.sleep(0.5)
                    continue
                
                # Asignar mensaje a la instancia
                message.assigned_instance = selected_instance.instance_id
                selected_instance.current_load += 1
                
                # Procesar mensaje en background
                future = self.executor.submit(self._process_message_on_instance, message, selected_instance)
                
                self.logger.debug(f"📤 Mensaje {message.message_id} asignado a instancia {selected_instance.instance_id}")
                
            except Exception as e:
                self.logger.error(f"Error en message distribution worker: {e}")
                time.sleep(1.0)
        
        self.logger.info("🛑 Message distribution worker terminado")
    
    def _select_instance_for_chat(self, message: ClusterMessage) -> Optional[BotInstance]:
        """
        ⚡ Selecciona instancia óptima considerando multi-chat balancing.
        
        Args:
            message: Mensaje con chat_id
            
        Returns:
            Instancia seleccionada o None si no hay disponibles
        """
        available_instances = [inst for inst in self.instances.values() if inst.is_available]
        
        if not available_instances:
            return None
        
        # Si multi-chat está habilitado, usar optimizador avanzado
        if self.multi_chat_optimizer and self.enable_multi_chat:
            # Determinar prioridad del chat basado en el mensaje
            priority = ChatPriority.NORMAL
            if message.priority == 1:
                priority = ChatPriority.HIGH
            elif message.priority >= 3:
                priority = ChatPriority.LOW
            
            # Obtener asignación óptima
            available_instance_ids = [inst.instance_id for inst in available_instances]
            selected_instance_id = self.multi_chat_optimizer.assign_chat(
                message.chat_id, available_instance_ids, priority
            )
            
            # Encontrar instancia correspondiente
            for instance in available_instances:
                if instance.instance_id == selected_instance_id:
                    
                    # Actualizar estructuras internas del cluster
                    self.chat_assignments[message.chat_id] = selected_instance_id
                    self.chat_load_balance[message.chat_id] = self.chat_load_balance.get(message.chat_id, 0) + 1
                    
                    if selected_instance_id not in self.instance_chats:
                        self.instance_chats[selected_instance_id] = []
                    
                    if message.chat_id not in self.instance_chats[selected_instance_id]:
                        self.instance_chats[selected_instance_id].append(message.chat_id)
                    
                    return instance
        
        # Fallback al distribuidor tradicional
        return self.message_distributor.select_instance(available_instances, message)
    
    def _process_message_on_instance(self, message: ClusterMessage, instance: BotInstance) -> bool:
        """
        Procesa mensaje en una instancia específica.
        
        Args:
            message: Mensaje a procesar
            instance: Instancia que procesará el mensaje
            
        Returns:
            True si se procesó exitosamente
        """
        start_time = time.time()
        
        try:
            # Simular procesamiento del mensaje
            # En implementación real, aquí se llamaría al bot instance
            processing_time = self._simulate_message_processing(message)
            
            # Actualizar estadísticas de la instancia
            instance.total_processed += 1
            instance.current_load = max(0, instance.current_load - 1)
            
            # Actualizar tiempo de respuesta promedio
            total_time = processing_time * 1000  # ms
            if instance.average_response_time == 0:
                instance.average_response_time = total_time
            else:
                instance.average_response_time = (instance.average_response_time * 0.8 + total_time * 0.2)
            
            # Actualizar estadísticas del cluster
            self.cluster_stats['total_messages_processed'] += 1
            
            # Registrar métricas
            self.metrics_collector.record_operation(
                operation=f"cluster_message_processing",
                duration=processing_time,
                success=True,
                instance_id=instance.instance_id,
                chat_id=message.chat_id
            )
            
            # Actualizar métricas de multi-chat optimizer
            if self.multi_chat_optimizer:
                self.multi_chat_optimizer.update_chat_activity(
                    message.chat_id, 
                    processing_time * 1000,  # Convertir a ms
                    error=False
                )
            
            instance.update_heartbeat()
            
            return True
            
        except Exception as e:
            # Error en procesamiento
            instance.error_count += 1
            instance.current_load = max(0, instance.current_load - 1)
            self.cluster_stats['total_messages_failed'] += 1
            
            self.logger.error(f"❌ Error procesando mensaje {message.message_id} en instancia {instance.instance_id}: {e}")
            
            # Actualizar métricas de error en multi-chat optimizer
            if self.multi_chat_optimizer:
                self.multi_chat_optimizer.update_chat_activity(
                    message.chat_id, 
                    error=True
                )
            
            # Re-intentar en otra instancia si hay retries disponibles
            if message.retries < message.max_retries:
                message.retries += 1
                message.assigned_instance = None
                self.pending_messages.put((message.priority + 1, time.time(), message))
                self.logger.info(f"🔄 Re-encolando mensaje {message.message_id} (retry {message.retries})")
            
            return False
    
    def _simulate_message_processing(self, message: ClusterMessage) -> float:
        """Simula procesamiento de mensaje (para testing)."""
        # Tiempo variable basado en longitud del mensaje
        base_time = 0.1  # 100ms base
        length_factor = len(message.message_text) * 0.001  # 1ms por carácter
        processing_time = base_time + length_factor
        
        time.sleep(processing_time)
        return processing_time
    
    def _health_monitoring_worker(self):
        """Worker que monitorea la salud de las instancias."""
        self.logger.info("🏥 Health monitoring worker iniciado")
        
        while self.running:
            try:
                current_time = datetime.now()
                
                for instance_id, instance in list(self.instances.items()):
                    # Verificar si la instancia está obsoleta
                    if instance.is_stale():
                        instance.status = BotStatus.OFFLINE
                        self.logger.warning(f"⚠️ Instancia {instance_id} marcada como OFFLINE (sin heartbeat)")
                    
                    # Actualizar métricas de sistema para la instancia
                    self._update_instance_system_metrics(instance)
                    
                    # Evaluar estado basado en carga y errores
                    self._evaluate_instance_health(instance)
                
                # Actualizar estadísticas del cluster
                self._update_cluster_stats()
                
                # Rebalancear multi-chat si es necesario
                if self.multi_chat_optimizer and self.chat_balancing:
                    available_instance_ids = [inst.instance_id for inst in self.instances.values() 
                                            if inst.status != BotStatus.OFFLINE]
                    self.multi_chat_optimizer.rebalance_chats(available_instance_ids)
                
                time.sleep(min(self.heartbeat_interval, 2))  # Max 2 segundos para tests
                
            except Exception as e:
                self.logger.error(f"Error en health monitoring worker: {e}")
                time.sleep(5.0)
        
        self.logger.info("🛑 Health monitoring worker terminado")
    
    def _update_instance_system_metrics(self, instance: BotInstance):
        """Actualiza métricas del sistema para una instancia."""
        try:
            # Simular métricas del sistema (en implementación real se obtendría del proceso real)
            process = psutil.Process()  # Proceso actual como proxy
            instance.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            instance.cpu_usage_percent = process.cpu_percent()
            
        except Exception:
            # Si no se pueden obtener métricas, usar valores por defecto
            instance.memory_usage_mb = 50.0
            instance.cpu_usage_percent = 10.0
    
    def _evaluate_instance_health(self, instance: BotInstance):
        """Evalúa y actualiza el estado de salud de una instancia."""
        if instance.status == BotStatus.OFFLINE:
            return
        
        # Evaluar basado en carga
        if instance.load_percentage >= 90:
            instance.status = BotStatus.OVERLOADED
        elif instance.load_percentage >= 70:
            instance.status = BotStatus.BUSY
        else:
            # Evaluar tasa de errores
            if instance.total_processed > 10:  # Suficiente muestra
                error_rate = (instance.error_count / instance.total_processed) * 100
                if error_rate > 20:
                    instance.status = BotStatus.ERROR
                else:
                    instance.status = BotStatus.HEALTHY
            else:
                instance.status = BotStatus.HEALTHY
    
    def _update_cluster_stats(self):
        """Actualiza estadísticas globales del cluster."""
        active_instances = [inst for inst in self.instances.values() 
                          if inst.status != BotStatus.OFFLINE]
        
        self.cluster_stats['active_instances'] = len(active_instances)
        
        if active_instances:
            total_load = sum(inst.load_percentage for inst in active_instances)
            self.cluster_stats['average_cluster_load'] = total_load / len(active_instances)
        else:
            self.cluster_stats['average_cluster_load'] = 0.0
        
        self.cluster_stats['message_queue_size'] = self.pending_messages.qsize()
    
    def _metrics_collection_worker(self):
        """Worker que recolecta métricas del cluster."""
        self.logger.info("📊 Metrics collection worker iniciado")
        
        while self.running:
            try:
                # Registrar métricas del cluster
                self.metrics_collector.record_custom_metric(
                    'cluster_active_instances', 
                    self.cluster_stats['active_instances']
                )
                
                self.metrics_collector.record_custom_metric(
                    'cluster_average_load', 
                    self.cluster_stats['average_cluster_load']
                )
                
                self.metrics_collector.record_custom_metric(
                    'cluster_queue_size', 
                    self.cluster_stats['message_queue_size']
                )
                
                # Métricas por instancia
                for instance in self.instances.values():
                    self.metrics_collector.record_custom_metric(
                        'instance_load_percentage', 
                        instance.load_percentage,
                        instance_id=instance.instance_id
                    )
                    
                    self.metrics_collector.record_custom_metric(
                        'instance_health_score', 
                        instance.health_score,
                        instance_id=instance.instance_id
                    )
                
                time.sleep(5)  # Recolectar cada 5 segundos para tests
                
            except Exception as e:
                self.logger.error(f"Error en metrics collection worker: {e}")
                time.sleep(10.0)
        
        self.logger.info("🛑 Metrics collection worker terminado")
    
    def _process_pending_messages(self):
        """Procesa mensajes pendientes durante el shutdown."""
        self.logger.info("Procesando mensajes pendientes...")
        
        processed = 0
        while not self.pending_messages.empty() and processed < 50:  # Límite de seguridad
            try:
                priority, timestamp, message = self.pending_messages.get_nowait()
                # Procesar mensaje de manera síncrona
                processed += 1
            except queue.Empty:
                break
        
        if processed > 0:
            self.logger.info(f"✅ {processed} mensajes pendientes procesados")
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del cluster."""
        instances_status = {}
        for instance_id, instance in self.instances.items():
            instances_status[instance_id] = {
                'profile_name': instance.profile_name,
                'status': instance.status.value,
                'load_percentage': instance.load_percentage,
                'health_score': instance.health_score,
                'total_processed': instance.total_processed,
                'error_count': instance.error_count,
                'average_response_time': instance.average_response_time,
                'memory_usage_mb': instance.memory_usage_mb,
                'cpu_usage_percent': instance.cpu_usage_percent
            }
        
        return {
            'cluster_stats': self.cluster_stats,
            'instances': instances_status,
            'distribution_strategy': self.message_distributor.strategy.value,
            'running': self.running
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Genera reporte de performance del cluster."""
        total_processed = sum(inst.total_processed for inst in self.instances.values())
        total_errors = sum(inst.error_count for inst in self.instances.values())
        
        if total_processed > 0:
            cluster_error_rate = (total_errors / total_processed) * 100
            avg_response_time = sum(inst.average_response_time for inst in self.instances.values()) / len(self.instances) if self.instances else 0
        else:
            cluster_error_rate = 0
            avg_response_time = 0
        
        # Calcular throughput
        uptime_hours = 1  # Placeholder - en implementación real calcular uptime real
        throughput_per_hour = total_processed / uptime_hours if uptime_hours > 0 else 0
        
        return {
            'total_messages_processed': total_processed,
            'total_errors': total_errors,
            'cluster_error_rate_percent': cluster_error_rate,
            'average_response_time_ms': avg_response_time,
            'throughput_messages_per_hour': throughput_per_hour,
            'cluster_efficiency': max(0, 100 - cluster_error_rate),
            'load_distribution_efficiency': self._calculate_load_distribution_efficiency(),
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_load_distribution_efficiency(self) -> float:
        """Calcula eficiencia de distribución de carga."""
        if not self.instances:
            return 0.0
        
        loads = [inst.load_percentage for inst in self.instances.values()]
        if not loads:
            return 100.0
        
        # Calcular desviación estándar de las cargas
        import statistics
        if len(loads) > 1:
            std_dev = statistics.stdev(loads)
            # Eficiencia inversamente proporcional a la desviación estándar
            efficiency = max(0, 100 - std_dev)
        else:
            efficiency = 100.0
        
        return efficiency


# ⚡ Instancia singleton del cluster
_cluster_instance: Optional[WhatsAppCluster] = None

def get_whatsapp_cluster(max_instances: int = 3) -> WhatsAppCluster:
    """Obtiene instancia singleton del cluster."""
    global _cluster_instance
    if _cluster_instance is None:
        _cluster_instance = WhatsAppCluster(max_instances=max_instances)
    return _cluster_instance

def shutdown_cluster():
    """Cierra el cluster global."""
    global _cluster_instance
    if _cluster_instance:
        _cluster_instance.stop_cluster()
        _cluster_instance = None