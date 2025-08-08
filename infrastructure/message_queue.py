"""
Sistema de Cola de Mensajes Asíncrono (FASE 3)

Sistema avanzado de procesamiento asíncrono de mensajes para máxima performance
en escenarios de alta carga. Permite procesamiento concurrente y no-bloqueante.
"""

import asyncio
import queue
import threading
import time
from datetime import datetime
from typing import List, Tuple, Optional, Callable, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import json

from shared.logger import get_logger


logger = get_logger(__name__)


@dataclass
class MessageTask:
    """Tarea de procesamiento de mensaje."""
    message_text: str
    message_timestamp: datetime
    chat_name: str
    priority: int = 1  # 1=alta, 2=media, 3=baja
    retries: int = 0
    max_retries: int = 3
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def __lt__(self, other):
        """Comparación para PriorityQueue basada en prioridad y timestamp."""
        if not isinstance(other, MessageTask):
            return NotImplemented
        
        # Primero por prioridad (menor valor = mayor prioridad)
        if self.priority != other.priority:
            return self.priority < other.priority
        
        # Después por timestamp (más antiguo primero)
        return self.created_at < other.created_at


@dataclass  
class ProcessingResult:
    """Resultado del procesamiento de un mensaje."""
    success: bool
    gasto_extraido: Optional[Any] = None
    error_message: Optional[str] = None
    processing_time_ms: float = 0
    method_used: str = "unknown"


class MessageQueue:
    """⚡ Sistema de cola asíncrono para procesamiento de mensajes (FASE 3)."""
    
    def __init__(self, max_workers: int = 3, queue_max_size: int = 1000):
        """
        Inicializa sistema de cola asíncrono.
        
        Args:
            max_workers: Número de workers concurrentes
            queue_max_size: Tamaño máximo de la cola
        """
        self.max_workers = max_workers
        self.queue_max_size = queue_max_size
        
        # ⚡ Colas con prioridad
        self.high_priority_queue = queue.PriorityQueue(maxsize=queue_max_size)
        self.medium_priority_queue = queue.Queue(maxsize=queue_max_size // 2)
        self.low_priority_queue = queue.Queue(maxsize=queue_max_size // 4)
        
        # Pool de workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="MsgQueue")
        
        # Worker threads
        self.workers = []
        self.running = False
        
        # Estadísticas
        self.stats = {
            'messages_processed': 0,
            'messages_failed': 0,
            'messages_queued': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'queue_size': 0,
            'worker_utilization': 0.0
        }
        
        # Callbacks para procesamiento
        self.message_processor: Optional[Callable] = None
        self.result_callback: Optional[Callable] = None
        
        self.logger = logger
        self.logger.info(f"MessageQueue inicializado con {max_workers} workers")
    
    def set_message_processor(self, processor: Callable[[str, datetime], ProcessingResult]):
        """
        Establece la función que procesará los mensajes.
        
        Args:
            processor: Función que recibe (texto, timestamp) y retorna ProcessingResult
        """
        self.message_processor = processor
        self.logger.info("Procesador de mensajes configurado")
    
    def set_result_callback(self, callback: Callable[[ProcessingResult], None]):
        """
        Establece callback para manejar resultados de procesamiento.
        
        Args:
            callback: Función que recibe ProcessingResult
        """
        self.result_callback = callback
        self.logger.info("Callback de resultados configurado")
    
    def start_workers(self):
        """⚡ Inicia workers asíncronos para procesamiento concurrente."""
        if self.running:
            return
            
        self.running = True
        
        # Crear workers
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"MessageWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            
        self.logger.info(f"✅ {len(self.workers)} workers iniciados")
    
    def stop_workers(self, timeout: float = 10.0):
        """Detiene workers de manera segura."""
        if not self.running:
            return
            
        self.logger.info("Deteniendo workers...")
        self.running = False
        
        # Esperar a que terminen los workers
        start_time = time.time()
        for worker in self.workers:
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time > 0:
                worker.join(timeout=remaining_time)
        
        self.executor.shutdown(wait=True)
        self.workers.clear()
        self.logger.info("Workers detenidos")
    
    def enqueue_message(self, message_text: str, message_timestamp: datetime, 
                       chat_name: str = "default", priority: int = 1) -> bool:
        """
        ⚡ Encola mensaje para procesamiento asíncrono.
        
        Args:
            message_text: Texto del mensaje
            message_timestamp: Timestamp del mensaje
            chat_name: Nombre del chat
            priority: Prioridad (1=alta, 2=media, 3=baja)
            
        Returns:
            True si se encoló exitosamente
        """
        try:
            task = MessageTask(
                message_text=message_text,
                message_timestamp=message_timestamp,
                chat_name=chat_name,
                priority=priority
            )
            
            # Seleccionar cola según prioridad
            if priority == 1:
                self.high_priority_queue.put((priority, time.time(), task), timeout=1.0)
            elif priority == 2:
                self.medium_priority_queue.put(task, timeout=1.0)
            else:
                self.low_priority_queue.put(task, timeout=1.0)
            
            self.stats['messages_queued'] += 1
            self.stats['queue_size'] = self.get_queue_size()
            
            self.logger.debug(f"📨 Mensaje encolado (prioridad {priority}): '{message_text[:30]}'")
            return True
            
        except queue.Full:
            self.logger.warning("❌ Cola llena, mensaje descartado")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error encolando mensaje: {e}")
            return False
    
    def _worker_loop(self):
        """Loop principal del worker que procesa mensajes."""
        worker_name = threading.current_thread().name
        self.logger.debug(f"🚀 Worker {worker_name} iniciado")
        
        while self.running:
            try:
                # Buscar tarea con prioridad
                task = self._get_next_task()
                
                if task is None:
                    time.sleep(0.1)  # Pausa corta si no hay tareas
                    continue
                
                # Procesar tarea
                start_time = time.time()
                result = self._process_task(task)
                processing_time = (time.time() - start_time) * 1000
                
                # Actualizar estadísticas
                self._update_stats(result, processing_time)
                
                # Ejecutar callback si está configurado
                if self.result_callback and result:
                    try:
                        self.result_callback(result)
                    except Exception as e:
                        self.logger.error(f"❌ Error en callback: {e}")
                
                self.logger.debug(f"✅ {worker_name} procesó mensaje en {processing_time:.1f}ms")
                
            except Exception as e:
                self.logger.error(f"❌ Error en worker {worker_name}: {e}")
                time.sleep(1.0)  # Pausa más larga en caso de error
        
        self.logger.debug(f"🛑 Worker {worker_name} terminado")
    
    def _get_next_task(self) -> Optional[MessageTask]:
        """Obtiene la siguiente tarea con sistema de prioridades."""
        try:
            # 1. Prioridad alta (con timeout corto)
            try:
                _, _, task = self.high_priority_queue.get(timeout=0.1)
                return task
            except queue.Empty:
                pass
            
            # 2. Prioridad media
            try:
                task = self.medium_priority_queue.get(timeout=0.1)
                return task
            except queue.Empty:
                pass
            
            # 3. Prioridad baja
            try:
                task = self.low_priority_queue.get(timeout=0.1)
                return task
            except queue.Empty:
                pass
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo tarea: {e}")
            return None
    
    def _process_task(self, task: MessageTask) -> Optional[ProcessingResult]:
        """Procesa una tarea de mensaje."""
        if not self.message_processor:
            return ProcessingResult(
                success=False,
                error_message="No message processor configured"
            )
        
        try:
            # Procesar mensaje
            result = self.message_processor(task.message_text, task.message_timestamp)
            
            if not result.success and task.retries < task.max_retries:
                # Re-encolar para retry
                task.retries += 1
                self.enqueue_message(
                    task.message_text, 
                    task.message_timestamp, 
                    task.chat_name, 
                    min(task.priority + 1, 3)  # Bajar prioridad en retry
                )
                self.logger.debug(f"🔄 Retry {task.retries}/{task.max_retries}: {task.message_text[:30]}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando tarea: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e)
            )
    
    def _update_stats(self, result: ProcessingResult, processing_time: float):
        """Actualiza estadísticas de procesamiento."""
        if result.success:
            self.stats['messages_processed'] += 1
        else:
            self.stats['messages_failed'] += 1
        
        self.stats['total_processing_time'] += processing_time
        
        total_messages = self.stats['messages_processed'] + self.stats['messages_failed']
        if total_messages > 0:
            self.stats['average_processing_time'] = self.stats['total_processing_time'] / total_messages
        
        self.stats['queue_size'] = self.get_queue_size()
    
    def get_queue_size(self) -> int:
        """Obtiene el tamaño total de las colas."""
        return (self.high_priority_queue.qsize() + 
                self.medium_priority_queue.qsize() + 
                self.low_priority_queue.qsize())
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de colas."""
        return {
            **self.stats,
            'workers_active': len([w for w in self.workers if w.is_alive()]),
            'workers_total': len(self.workers),
            'running': self.running,
            'high_priority_size': self.high_priority_queue.qsize(),
            'medium_priority_size': self.medium_priority_queue.qsize(),
            'low_priority_size': self.low_priority_queue.qsize()
        }
    
    def clear_queues(self):
        """Limpia todas las colas."""
        while not self.high_priority_queue.empty():
            try:
                self.high_priority_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.medium_priority_queue.empty():
            try:
                self.medium_priority_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.low_priority_queue.empty():
            try:
                self.low_priority_queue.get_nowait()
            except queue.Empty:
                break
        
        self.logger.info("🧹 Colas limpiadas")


class MessageQueueManager:
    """⚡ Manager principal para el sistema de colas (singleton pattern)."""
    
    _instance = None
    _queue = None
    
    @classmethod
    def get_instance(cls, max_workers: int = 3) -> MessageQueue:
        """Obtiene instancia singleton del sistema de colas."""
        if cls._instance is None:
            cls._instance = cls()
            cls._queue = MessageQueue(max_workers=max_workers)
        return cls._queue
    
    @classmethod
    def shutdown(cls):
        """Cierra el sistema de colas."""
        if cls._queue:
            cls._queue.stop_workers()
            cls._queue = None
        cls._instance = None