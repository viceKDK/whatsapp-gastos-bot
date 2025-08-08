"""
Bot Cluster Wrapper - Integración del Sistema de Clustering con Bot Principal

Wrapper que permite ejecutar múltiples instancias del bot de gastos WhatsApp
en modo cluster para máximo throughput y alta disponibilidad.
"""

import asyncio
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from pathlib import Path
import subprocess
import signal
import os

from shared.logger import get_logger
from infrastructure.clustering.whatsapp_cluster import (
    WhatsAppCluster, 
    MessageDistributionStrategy,
    BotStatus
)


logger = get_logger(__name__)


class ClusteredBotManager:
    """⚡ Manager para ejecutar múltiples instancias del bot en cluster."""
    
    def __init__(self, 
                 instance_configs: List[Dict[str, Any]],
                 distribution_strategy: MessageDistributionStrategy = MessageDistributionStrategy.HEALTH_BASED):
        """
        Inicializa manager de cluster.
        
        Args:
            instance_configs: Lista de configuraciones para cada instancia
                             [{'profile_name': 'profile1', 'max_load': 10}, ...]
            distribution_strategy: Estrategia de distribución de mensajes
        """
        self.instance_configs = instance_configs
        self.cluster = WhatsAppCluster(
            max_instances=len(instance_configs),
            distribution_strategy=distribution_strategy
        )
        
        # Procesos de las instancias
        self.bot_processes: Dict[str, subprocess.Popen] = {}
        self.instance_ids: Dict[str, str] = {}  # profile_name -> instance_id
        
        self.logger = logger
        
        # Callback para procesamiento de mensajes
        self.message_processor: Optional[Callable] = None
        
        self.logger.info(f"ClusteredBotManager inicializado con {len(instance_configs)} instancias")
    
    def set_message_processor(self, processor: Callable[[str, str], bool]):
        """
        Establece el procesador de mensajes para el cluster.
        
        Args:
            processor: Función que recibe (chat_id, message_text) y retorna bool
        """
        self.message_processor = processor
        self.logger.info("Message processor configurado para cluster")
    
    def start_cluster(self):
        """⚡ Inicia todas las instancias del bot en modo cluster."""
        self.logger.info("🚀 Iniciando cluster de bots WhatsApp...")
        
        # Iniciar sistema de clustering
        self.cluster.start_cluster()
        
        # Iniciar instancias individuales
        for config in self.instance_configs:
            self._start_bot_instance(config)
        
        # Esperar a que las instancias se registren
        self._wait_for_instances_ready()
        
        self.logger.info(f"✅ Cluster iniciado con {len(self.bot_processes)} instancias")
    
    def stop_cluster(self):
        """Detiene todas las instancias del cluster de manera segura."""
        self.logger.info("🛑 Deteniendo cluster de bots...")
        
        # Detener instancias individuales
        for profile_name, process in self.bot_processes.items():
            self._stop_bot_instance(profile_name, process)
        
        # Detener sistema de clustering
        self.cluster.stop_cluster()
        
        self.logger.info("✅ Cluster detenido completamente")
    
    def _start_bot_instance(self, config: Dict[str, Any]):
        """Inicia una instancia individual del bot."""
        profile_name = config['profile_name']
        
        try:
            # Registrar instancia en el cluster
            instance_id = self.cluster.register_instance(
                profile_name=profile_name,
                max_load=config.get('max_load', 10)
            )
            self.instance_ids[profile_name] = instance_id
            
            # En implementación real, aquí se iniciaría el proceso del bot
            # Por ahora simulamos con un proceso mock
            self._start_mock_bot_process(profile_name, config)
            
            self.logger.info(f"🤖 Bot iniciado: {profile_name} (ID: {instance_id})")
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando bot {profile_name}: {e}")
    
    def _start_mock_bot_process(self, profile_name: str, config: Dict[str, Any]):
        """Inicia un proceso mock para testing (en producción sería el bot real)."""
        # Crear script mock para simular instancia del bot
        mock_script = f'''
import time
import sys
import signal
import random

def signal_handler(sig, frame):
    print(f"Bot {profile_name} recibió señal de terminación")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print(f"Mock Bot {profile_name} iniciado")

# Simular trabajo del bot
while True:
    time.sleep(random.uniform(1, 3))  # Simular trabajo variable
    # En implementación real: procesar mensajes de WhatsApp
'''
        
        # Por ahora solo simulamos el proceso
        import threading
        def mock_bot_worker():
            time.sleep(0.1)  # Mock process
        
        worker = threading.Thread(target=mock_bot_worker, daemon=True)
        worker.start()
        
        # Simular proceso
        class MockProcess:
            def __init__(self, profile_name):
                self.profile_name = profile_name
                self.pid = os.getpid()
                self.returncode = None
                
            def terminate(self):
                self.logger.info(f"Terminando proceso mock para {self.profile_name}")
                
            def poll(self):
                return self.returncode
        
        self.bot_processes[profile_name] = MockProcess(profile_name)
    
    def _stop_bot_instance(self, profile_name: str, process):
        """Detiene una instancia individual del bot."""
        try:
            self.logger.info(f"🛑 Deteniendo bot: {profile_name}")
            
            # Terminar proceso de manera segura
            if hasattr(process, 'terminate'):
                process.terminate()
            
            # Esperar terminación
            timeout = 10
            while timeout > 0 and process.poll() is None:
                time.sleep(0.5)
                timeout -= 0.5
            
            # Force kill si no termina
            if process.poll() is None and hasattr(process, 'kill'):
                process.kill()
            
            # Desregistrar del cluster
            if profile_name in self.instance_ids:
                instance_id = self.instance_ids[profile_name]
                self.cluster.unregister_instance(instance_id)
                del self.instance_ids[profile_name]
            
            self.logger.info(f"✅ Bot detenido: {profile_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Error deteniendo bot {profile_name}: {e}")
    
    def _wait_for_instances_ready(self, timeout: int = 30):
        """Espera a que las instancias estén listas."""
        self.logger.info("⏳ Esperando que las instancias estén listas...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            ready_instances = sum(1 for inst in self.cluster.instances.values() 
                                if inst.status in [BotStatus.HEALTHY, BotStatus.BUSY])
            
            if ready_instances >= len(self.instance_configs):
                self.logger.info(f"✅ {ready_instances} instancias listas")
                return
            
            time.sleep(1)
        
        self.logger.warning(f"⚠️ Timeout esperando instancias. Solo {ready_instances}/{len(self.instance_configs)} listas")
    
    def process_message(self, chat_id: str, message_text: str, priority: int = 1) -> str:
        """
        ⚡ Procesa mensaje usando el cluster.
        
        Args:
            chat_id: ID del chat
            message_text: Texto del mensaje
            priority: Prioridad del mensaje
            
        Returns:
            ID del mensaje encolado
        """
        return self.cluster.submit_message(chat_id, message_text, priority)
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del cluster."""
        cluster_status = self.cluster.get_cluster_status()
        
        # Agregar información de procesos
        cluster_status['processes'] = {}
        for profile_name, process in self.bot_processes.items():
            cluster_status['processes'][profile_name] = {
                'pid': getattr(process, 'pid', None),
                'running': process.poll() is None if hasattr(process, 'poll') else True
            }
        
        return cluster_status
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Genera reporte de performance del cluster."""
        return self.cluster.get_performance_report()
    
    def scale_cluster(self, new_instance_config: Dict[str, Any]):
        """
        Escala el cluster agregando una nueva instancia.
        
        Args:
            new_instance_config: Configuración de la nueva instancia
        """
        self.logger.info(f"⚡ Escalando cluster: agregando {new_instance_config['profile_name']}")
        
        self.instance_configs.append(new_instance_config)
        self._start_bot_instance(new_instance_config)
        
        self.logger.info("✅ Cluster escalado exitosamente")
    
    def remove_instance(self, profile_name: str):
        """
        Remueve una instancia del cluster.
        
        Args:
            profile_name: Nombre del perfil a remover
        """
        if profile_name not in self.bot_processes:
            self.logger.warning(f"Instancia {profile_name} no encontrada")
            return
        
        self.logger.info(f"➖ Removiendo instancia: {profile_name}")
        
        # Detener instancia
        process = self.bot_processes[profile_name]
        self._stop_bot_instance(profile_name, process)
        
        # Remover de configuración
        self.instance_configs = [config for config in self.instance_configs 
                               if config['profile_name'] != profile_name]
        
        del self.bot_processes[profile_name]
        
        self.logger.info(f"✅ Instancia removida: {profile_name}")


class ClusterHealthMonitor:
    """Monitor de salud del cluster con alertas automáticas."""
    
    def __init__(self, cluster_manager: ClusteredBotManager):
        self.cluster_manager = cluster_manager
        self.running = False
        self.monitor_thread = None
        self.alert_callbacks: List[Callable] = []
        self.logger = logger
    
    def add_alert_callback(self, callback: Callable[[str, Dict], None]):
        """Agrega callback para alertas del cluster."""
        self.alert_callbacks.append(callback)
    
    def start_monitoring(self, check_interval: int = 60):
        """Inicia monitoreo continuo del cluster."""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, 
            args=(check_interval,), 
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.info("🏥 Cluster health monitoring iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("🛑 Cluster health monitoring detenido")
    
    def _monitoring_loop(self, check_interval: int):
        """Loop principal de monitoreo."""
        while self.running:
            try:
                status = self.cluster_manager.get_cluster_status()
                self._check_cluster_health(status)
                time.sleep(check_interval)
            except Exception as e:
                self.logger.error(f"Error en monitoring loop: {e}")
                time.sleep(10)
    
    def _check_cluster_health(self, status: Dict[str, Any]):
        """Verifica la salud del cluster y envía alertas si es necesario."""
        cluster_stats = status['cluster_stats']
        instances = status['instances']
        
        # Verificar instancias offline
        offline_instances = [name for name, inst in instances.items() 
                           if inst['status'] == 'offline']
        if offline_instances:
            self._send_alert('instances_offline', {
                'offline_instances': offline_instances,
                'count': len(offline_instances)
            })
        
        # Verificar alta carga promedio
        if cluster_stats['average_cluster_load'] > 80:
            self._send_alert('high_cluster_load', {
                'load_percentage': cluster_stats['average_cluster_load']
            })
        
        # Verificar cola de mensajes grande
        if cluster_stats['message_queue_size'] > 100:
            self._send_alert('large_message_queue', {
                'queue_size': cluster_stats['message_queue_size']
            })
        
        # Verificar alta tasa de errores
        performance = self.cluster_manager.get_performance_report()
        if performance['cluster_error_rate_percent'] > 10:
            self._send_alert('high_error_rate', {
                'error_rate': performance['cluster_error_rate_percent']
            })
    
    def _send_alert(self, alert_type: str, data: Dict[str, Any]):
        """Envía alerta a todos los callbacks registrados."""
        alert_data = {
            'type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        self.logger.warning(f"🚨 ALERTA CLUSTER: {alert_type} - {data}")
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_type, alert_data)
            except Exception as e:
                self.logger.error(f"Error ejecutando alert callback: {e}")


def create_default_cluster_config(num_instances: int = 3) -> List[Dict[str, Any]]:
    """
    Crea configuración por defecto para el cluster.
    
    Args:
        num_instances: Número de instancias a crear
        
    Returns:
        Lista de configuraciones de instancias
    """
    configs = []
    for i in range(num_instances):
        configs.append({
            'profile_name': f'whatsapp_bot_profile_{i+1}',
            'max_load': 10,
            'chrome_port': 9222 + i,  # Puertos diferentes para cada instancia
            'user_data_dir': f'chrome_profiles/profile_{i+1}'
        })
    
    return configs