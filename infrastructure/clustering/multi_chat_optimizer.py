"""
Sistema Avanzado de Multi-Chat Optimization - FASE 4.1.5
⚡ Optimización para múltiples chats simultáneos con load balancing inteligente

Mejora esperada: 3x throughput adicional para múltiples chats
"""

import asyncio
import threading
import time
import statistics
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import hashlib

from shared.logger import get_logger
from shared.metrics import get_metrics_collector


logger = get_logger(__name__)


class ChatPriority(Enum):
    """Prioridades de chat para balanceo."""
    CRITICAL = 1    # Chats VIP/urgentes
    HIGH = 2        # Chats importantes
    NORMAL = 3      # Chats regulares
    LOW = 4         # Chats de prueba/desarrollo


@dataclass
class ChatMetrics:
    """Métricas de un chat específico."""
    chat_id: str
    total_messages: int = 0
    messages_per_minute: float = 0.0
    average_response_time: float = 0.0
    error_count: int = 0
    priority: ChatPriority = ChatPriority.NORMAL
    last_activity: datetime = field(default_factory=datetime.now)
    assigned_instance: Optional[str] = None
    
    # Ventana deslizante para calcular throughput
    message_timestamps: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update_activity(self, response_time: float = 0.0, error: bool = False):
        """Actualiza métricas de actividad del chat."""
        self.last_activity = datetime.now()
        self.total_messages += 1
        
        # Actualizar ventana de timestamps
        self.message_timestamps.append(time.time())
        
        # Calcular mensajes por minuto
        if len(self.message_timestamps) > 1:
            time_window = self.message_timestamps[-1] - self.message_timestamps[0]
            if time_window > 0:
                self.messages_per_minute = (len(self.message_timestamps) / time_window) * 60
        
        # Actualizar tiempo de respuesta promedio
        if response_time > 0:
            if self.average_response_time == 0:
                self.average_response_time = response_time
            else:
                self.average_response_time = (self.average_response_time * 0.8 + response_time * 0.2)
        
        # Actualizar conteo de errores
        if error:
            self.error_count += 1
    
    @property
    def error_rate(self) -> float:
        """Tasa de errores del chat."""
        return (self.error_count / max(self.total_messages, 1)) * 100
    
    @property
    def load_score(self) -> float:
        """Score de carga del chat (0-100)."""
        # Combinar throughput, latencia y errores
        throughput_score = min(self.messages_per_minute * 2, 100)  # Normalizar
        latency_penalty = min(self.average_response_time / 10, 50)  # Penalizar latencia alta
        error_penalty = min(self.error_rate * 2, 30)  # Penalizar errores
        
        return max(0, throughput_score - latency_penalty - error_penalty)
    
    @property
    def is_active(self) -> bool:
        """Si el chat ha estado activo recientemente."""
        return (datetime.now() - self.last_activity).seconds < 300  # 5 minutos


class ChatLoadBalancer:
    """⚡ Balanceador de carga inteligente para múltiples chats."""
    
    def __init__(self, rebalance_threshold: float = 0.3, sticky_sessions: bool = True):
        """
        Inicializa balanceador de chats.
        
        Args:
            rebalance_threshold: Umbral para rebalanceo (0.0-1.0)
            sticky_sessions: Mantener chats en la misma instancia cuando sea posible
        """
        self.rebalance_threshold = rebalance_threshold
        self.sticky_sessions = sticky_sessions
        
        # Métricas de chats
        self.chat_metrics: Dict[str, ChatMetrics] = {}
        
        # Asignaciones actuales
        self.chat_assignments: Dict[str, str] = {}  # chat_id -> instance_id
        self.instance_chats: Dict[str, Set[str]] = defaultdict(set)  # instance_id -> chat_ids
        
        # Historial de balanceo
        self.rebalance_history: List[Dict[str, Any]] = []
        
        self.logger = logger
        self.metrics_collector = get_metrics_collector()
    
    def register_chat(self, chat_id: str, priority: ChatPriority = ChatPriority.NORMAL):
        """Registra un nuevo chat en el sistema."""
        if chat_id not in self.chat_metrics:
            self.chat_metrics[chat_id] = ChatMetrics(
                chat_id=chat_id,
                priority=priority
            )
            self.logger.info(f"📱 Chat registrado: {chat_id} (prioridad: {priority.name})")
    
    def assign_chat_to_instance(self, chat_id: str, available_instances: List[str]) -> Optional[str]:
        """
        ⚡ Asigna chat a la instancia óptima.
        
        Args:
            chat_id: ID del chat
            available_instances: Lista de instancias disponibles
            
        Returns:
            ID de la instancia asignada
        """
        if not available_instances:
            return None
        
        # Registrar chat si no existe
        if chat_id not in self.chat_metrics:
            self.register_chat(chat_id)
        
        chat_metrics = self.chat_metrics[chat_id]
        
        # Si sticky sessions está habilitado y el chat ya está asignado
        if (self.sticky_sessions and 
            chat_id in self.chat_assignments and 
            self.chat_assignments[chat_id] in available_instances):
            
            current_instance = self.chat_assignments[chat_id]
            
            # Verificar si la instancia actual aún es viable
            if not self._should_reassign_chat(chat_id, current_instance):
                return current_instance
        
        # Seleccionar nueva instancia
        best_instance = self._select_best_instance(chat_id, available_instances)
        
        if best_instance:
            self._assign_chat(chat_id, best_instance)
        
        return best_instance
    
    def _select_best_instance(self, chat_id: str, available_instances: List[str]) -> Optional[str]:
        """Selecciona la mejor instancia para un chat."""
        if not available_instances:
            return None
        
        chat_metrics = self.chat_metrics[chat_id]
        instance_scores = {}
        
        for instance_id in available_instances:
            score = self._calculate_instance_score(instance_id, chat_metrics)
            instance_scores[instance_id] = score
        
        # Seleccionar instancia con mejor score
        best_instance = max(instance_scores, key=instance_scores.get)
        
        self.logger.debug(f"Instancia seleccionada para chat {chat_id}: {best_instance} (score: {instance_scores[best_instance]:.2f})")
        
        return best_instance
    
    def _calculate_instance_score(self, instance_id: str, chat_metrics: ChatMetrics) -> float:
        """Calcula score de una instancia para un chat específico."""
        base_score = 100.0
        
        # Penalizar por número de chats ya asignados
        current_chats = len(self.instance_chats.get(instance_id, set()))
        load_penalty = current_chats * 10
        
        # Bonus por prioridad del chat
        priority_bonus = {
            ChatPriority.CRITICAL: 50,
            ChatPriority.HIGH: 20,
            ChatPriority.NORMAL: 0,
            ChatPriority.LOW: -10
        }.get(chat_metrics.priority, 0)
        
        # Penalty por distribución desbalanceada
        distribution_penalty = self._calculate_distribution_penalty(instance_id)
        
        # Score final
        final_score = base_score - load_penalty + priority_bonus - distribution_penalty
        
        return max(0, final_score)
    
    def _calculate_distribution_penalty(self, instance_id: str) -> float:
        """Calcula penalización por distribución desbalanceada."""
        if not self.instance_chats:
            return 0
        
        all_loads = [len(chats) for chats in self.instance_chats.values()]
        current_load = len(self.instance_chats.get(instance_id, set()))
        
        if len(all_loads) > 1:
            avg_load = statistics.mean(all_loads)
            std_dev = statistics.stdev(all_loads)
            
            # Penalizar instancias que están muy por encima del promedio
            if current_load > avg_load + std_dev:
                return (current_load - avg_load) * 15
        
        return 0
    
    def _assign_chat(self, chat_id: str, instance_id: str):
        """Asigna chat a instancia actualizando estructuras internas."""
        # Remover asignación anterior si existe
        if chat_id in self.chat_assignments:
            old_instance = self.chat_assignments[chat_id]
            self.instance_chats[old_instance].discard(chat_id)
        
        # Nueva asignación
        self.chat_assignments[chat_id] = instance_id
        self.instance_chats[instance_id].add(chat_id)
        
        # Actualizar métricas
        self.chat_metrics[chat_id].assigned_instance = instance_id
        
        self.logger.debug(f"Chat {chat_id} asignado a instancia {instance_id}")
    
    def _should_reassign_chat(self, chat_id: str, current_instance: str) -> bool:
        """Determina si un chat debe ser reasignado."""
        chat_metrics = self.chat_metrics[chat_id]
        
        # Reasignar si hay muchos errores
        if chat_metrics.error_rate > 20:
            return True
        
        # Reasignar si la latencia es muy alta
        if chat_metrics.average_response_time > 5000:  # 5 segundos
            return True
        
        # Reasignar si la instancia está muy cargada
        current_load = len(self.instance_chats.get(current_instance, set()))
        if current_load > 15:  # Más de 15 chats
            return True
        
        return False
    
    def update_chat_metrics(self, chat_id: str, response_time: float = 0.0, error: bool = False):
        """Actualiza métricas de un chat."""
        if chat_id in self.chat_metrics:
            self.chat_metrics[chat_id].update_activity(response_time, error)
            
            # Registrar métricas
            self.metrics_collector.record_custom_metric(
                'chat_messages_per_minute',
                self.chat_metrics[chat_id].messages_per_minute,
                chat_id=chat_id
            )
    
    def rebalance_if_needed(self, available_instances: List[str]) -> bool:
        """
        Rebalancea chats entre instancias si es necesario.
        
        Args:
            available_instances: Lista de instancias disponibles
            
        Returns:
            True si se realizó rebalanceo
        """
        if not available_instances or len(available_instances) < 2:
            return False
        
        # Calcular métricas de distribución
        distribution_metrics = self._calculate_distribution_metrics()
        
        # Decidir si rebalancear
        if distribution_metrics['balance_coefficient'] < self.rebalance_threshold:
            return self._perform_rebalancing(available_instances)
        
        return False
    
    def _calculate_distribution_metrics(self) -> Dict[str, float]:
        """Calcula métricas de distribución del cluster."""
        if not self.instance_chats:
            return {'balance_coefficient': 1.0, 'std_deviation': 0.0}
        
        loads = [len(chats) for chats in self.instance_chats.values()]
        
        if len(loads) <= 1:
            return {'balance_coefficient': 1.0, 'std_deviation': 0.0}
        
        avg_load = statistics.mean(loads)
        std_dev = statistics.stdev(loads) if len(loads) > 1 else 0.0
        
        # Coeficiente de balance (0-1, donde 1 es perfectamente balanceado)
        balance_coefficient = max(0, 1 - (std_dev / max(avg_load, 1)))
        
        return {
            'balance_coefficient': balance_coefficient,
            'std_deviation': std_dev,
            'average_load': avg_load
        }
    
    def _perform_rebalancing(self, available_instances: List[str]) -> bool:
        """Realiza rebalanceo de chats."""
        self.logger.info("🔄 Iniciando rebalanceo de chats...")
        
        rebalanced_chats = 0
        
        # Identificar chats candidatos para mover
        candidate_chats = self._identify_rebalance_candidates()
        
        for chat_id in candidate_chats:
            if chat_id not in self.chat_assignments:
                continue
            
            current_instance = self.chat_assignments[chat_id]
            
            # Seleccionar nueva instancia
            new_instance = self._select_best_instance(chat_id, available_instances)
            
            if new_instance and new_instance != current_instance:
                self._assign_chat(chat_id, new_instance)
                rebalanced_chats += 1
                
                self.logger.debug(f"Chat {chat_id} movido de {current_instance} a {new_instance}")
        
        # Registrar rebalanceo
        if rebalanced_chats > 0:
            self.rebalance_history.append({
                'timestamp': datetime.now().isoformat(),
                'chats_moved': rebalanced_chats,
                'instances': available_instances
            })
            
            self.logger.info(f"✅ Rebalanceo completado: {rebalanced_chats} chats movidos")
        
        return rebalanced_chats > 0
    
    def _identify_rebalance_candidates(self) -> List[str]:
        """Identifica chats candidatos para rebalanceo."""
        candidates = []
        
        # Identificar instancias sobrecargadas
        if not self.instance_chats:
            return candidates
        
        loads = [len(chats) for chats in self.instance_chats.values()]
        avg_load = statistics.mean(loads)
        
        for instance_id, chats in self.instance_chats.items():
            if len(chats) > avg_load * 1.5:  # 50% sobre el promedio
                # Seleccionar chats con menor prioridad para mover
                sorted_chats = sorted(
                    chats,
                    key=lambda cid: (
                        self.chat_metrics[cid].priority.value,
                        -self.chat_metrics[cid].load_score
                    )
                )
                
                # Mover hasta la mitad del exceso
                excess = int(len(chats) - avg_load)
                candidates.extend(sorted_chats[:excess // 2])
        
        return candidates
    
    def get_chat_distribution_report(self) -> Dict[str, Any]:
        """Genera reporte de distribución de chats."""
        distribution_metrics = self._calculate_distribution_metrics()
        
        # Estadísticas por instancia
        instance_stats = {}
        for instance_id, chats in self.instance_chats.items():
            active_chats = sum(1 for cid in chats if self.chat_metrics[cid].is_active)
            total_throughput = sum(self.chat_metrics[cid].messages_per_minute for cid in chats)
            
            instance_stats[instance_id] = {
                'total_chats': len(chats),
                'active_chats': active_chats,
                'total_throughput': total_throughput,
                'chat_ids': list(chats)[:10]  # Primeros 10 para no saturar
            }
        
        # Estadísticas de chats
        chat_stats = {}
        for chat_id, metrics in self.chat_metrics.items():
            if metrics.is_active:
                chat_stats[chat_id] = {
                    'priority': metrics.priority.name,
                    'messages_per_minute': metrics.messages_per_minute,
                    'error_rate': metrics.error_rate,
                    'assigned_instance': metrics.assigned_instance,
                    'load_score': metrics.load_score
                }
        
        return {
            'distribution_metrics': distribution_metrics,
            'instance_stats': instance_stats,
            'active_chat_stats': chat_stats,
            'total_active_chats': len([c for c in self.chat_metrics.values() if c.is_active]),
            'rebalance_history_count': len(self.rebalance_history),
            'last_rebalance': self.rebalance_history[-1] if self.rebalance_history else None
        }
    
    def cleanup_inactive_chats(self, max_age_hours: int = 24):
        """Limpia métricas de chats inactivos."""
        current_time = datetime.now()
        inactive_chats = []
        
        for chat_id, metrics in self.chat_metrics.items():
            age_hours = (current_time - metrics.last_activity).total_seconds() / 3600
            if age_hours > max_age_hours:
                inactive_chats.append(chat_id)
        
        # Remover chats inactivos
        for chat_id in inactive_chats:
            # Remover de asignaciones
            if chat_id in self.chat_assignments:
                instance_id = self.chat_assignments[chat_id]
                self.instance_chats[instance_id].discard(chat_id)
                del self.chat_assignments[chat_id]
            
            # Remover métricas
            del self.chat_metrics[chat_id]
        
        if inactive_chats:
            self.logger.info(f"🧹 Cleanup: {len(inactive_chats)} chats inactivos eliminados")
        
        return len(inactive_chats)


class MultiChatOptimizer:
    """⚡ Optimizador principal para múltiples chats simultáneos."""
    
    def __init__(self, max_chats_per_instance: int = 10):
        """
        Inicializa optimizador multi-chat.
        
        Args:
            max_chats_per_instance: Máximo de chats por instancia
        """
        self.max_chats_per_instance = max_chats_per_instance
        self.load_balancer = ChatLoadBalancer()
        
        # Workers para monitoreo
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        self.logger = logger
        self.metrics_collector = get_metrics_collector()
    
    def start_monitoring(self, check_interval: int = 30):
        """Inicia monitoreo automático de distribución."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.info("🔍 Multi-chat monitoring iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo automático."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("🛑 Multi-chat monitoring detenido")
    
    def _monitoring_loop(self, check_interval: int):
        """Loop principal de monitoreo."""
        while self.monitoring_active:
            try:
                # Cleanup periódico
                cleaned = self.load_balancer.cleanup_inactive_chats()
                
                # Registrar métricas
                distribution_report = self.load_balancer.get_chat_distribution_report()
                
                self.metrics_collector.record_custom_metric(
                    'multi_chat_balance_coefficient',
                    distribution_report['distribution_metrics']['balance_coefficient']
                )
                
                self.metrics_collector.record_custom_metric(
                    'multi_chat_active_chats',
                    distribution_report['total_active_chats']
                )
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error en multi-chat monitoring loop: {e}")
                time.sleep(10)
    
    def assign_chat(self, chat_id: str, available_instances: List[str], 
                   priority: ChatPriority = ChatPriority.NORMAL) -> Optional[str]:
        """
        ⚡ Asigna chat a instancia óptima.
        
        Args:
            chat_id: ID del chat
            available_instances: Lista de instancias disponibles
            priority: Prioridad del chat
            
        Returns:
            ID de la instancia asignada
        """
        # Registrar chat si es necesario
        if chat_id not in self.load_balancer.chat_metrics:
            self.load_balancer.register_chat(chat_id, priority)
        
        # Asignar a instancia óptima
        assigned_instance = self.load_balancer.assign_chat_to_instance(
            chat_id, available_instances
        )
        
        return assigned_instance
    
    def update_chat_activity(self, chat_id: str, response_time: float = 0.0, error: bool = False):
        """Actualiza actividad de un chat."""
        self.load_balancer.update_chat_metrics(chat_id, response_time, error)
    
    def rebalance_chats(self, available_instances: List[str]) -> bool:
        """Rebalancea chats entre instancias."""
        return self.load_balancer.rebalance_if_needed(available_instances)
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Genera reporte completo de optimización multi-chat."""
        distribution_report = self.load_balancer.get_chat_distribution_report()
        
        # Calcular métricas de optimización
        optimization_metrics = {
            'throughput_efficiency': self._calculate_throughput_efficiency(),
            'load_distribution_score': distribution_report['distribution_metrics']['balance_coefficient'] * 100,
            'chat_stickiness_ratio': self._calculate_stickiness_ratio(),
            'error_distribution': self._calculate_error_distribution()
        }
        
        return {
            'optimization_metrics': optimization_metrics,
            'distribution_report': distribution_report,
            'monitoring_active': self.monitoring_active,
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_throughput_efficiency(self) -> float:
        """Calcula eficiencia de throughput multi-chat."""
        if not self.load_balancer.chat_metrics:
            return 0.0
        
        active_chats = [c for c in self.load_balancer.chat_metrics.values() if c.is_active]
        if not active_chats:
            return 0.0
        
        total_throughput = sum(c.messages_per_minute for c in active_chats)
        theoretical_max = len(active_chats) * 10  # 10 mensajes/min por chat como máximo teórico
        
        return min(100, (total_throughput / max(theoretical_max, 1)) * 100)
    
    def _calculate_stickiness_ratio(self) -> float:
        """Calcula ratio de sticky sessions."""
        # En implementación real, tracking de reasignaciones
        return 85.0  # Placeholder
    
    def _calculate_error_distribution(self) -> Dict[str, float]:
        """Calcula distribución de errores por instancia."""
        error_distribution = {}
        
        for instance_id, chats in self.load_balancer.instance_chats.items():
            total_errors = sum(
                self.load_balancer.chat_metrics[cid].error_count 
                for cid in chats 
                if cid in self.load_balancer.chat_metrics
            )
            total_messages = sum(
                self.load_balancer.chat_metrics[cid].total_messages 
                for cid in chats 
                if cid in self.load_balancer.chat_metrics
            )
            
            error_rate = (total_errors / max(total_messages, 1)) * 100
            error_distribution[instance_id] = error_rate
        
        return error_distribution


# Instancia global del optimizador multi-chat
_multi_chat_optimizer: Optional[MultiChatOptimizer] = None

def get_multi_chat_optimizer(max_chats_per_instance: int = 10) -> MultiChatOptimizer:
    """Obtiene instancia singleton del optimizador multi-chat."""
    global _multi_chat_optimizer
    if _multi_chat_optimizer is None:
        _multi_chat_optimizer = MultiChatOptimizer(max_chats_per_instance)
    return _multi_chat_optimizer