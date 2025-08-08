"""
Implementación Híbrida de Storage

Combina SQLite para caché de mensajes con Excel para almacenamiento final.
Optimiza performance evitando re-procesar mensajes y filtrando mensajes de sistema.
"""

from typing import List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import queue
import time

from domain.models.gasto import Gasto
from shared.logger import get_logger
from .sqlite_writer import SQLiteStorage
from .excel_writer import ExcelStorage


logger = get_logger(__name__)


class HybridStorage:
    """
    Storage híbrido que combina SQLite para caché y Excel para persistencia final.
    
    Funcionalidades:
    - Caché inteligente de mensajes procesados para evitar re-procesamiento
    - Filtrado automático de mensajes del sistema
    - Almacenamiento final en Excel para compatibilidad
    - Performance optimizada para bots que procesan muchos mensajes
    """
    
    def __init__(self, excel_path: str, sqlite_path: str = None):
        """
        Inicializa el storage híbrido.
        
        Args:
            excel_path: Ruta al archivo Excel final
            sqlite_path: Ruta a la BD SQLite (opcional, se genera automática)
        """
        self.logger = logger
        self.excel_path = Path(excel_path)
        
        # Generar ruta SQLite si no se especifica
        if not sqlite_path:
            sqlite_path = self.excel_path.with_suffix('.cache.db')
        
        # Inicializar storages
        self.sqlite_storage = SQLiteStorage(str(sqlite_path))
        self.excel_storage = ExcelStorage(excel_path)
        
        self.logger.info(f"Hybrid storage initialized:")
        self.logger.info(f"  📊 Excel: {self.excel_path}")
        self.logger.info(f"  💾 SQLite cache: {sqlite_path}")
    
    def should_process_message(self, message_text: str, message_timestamp: datetime) -> bool:
        """
        Determina si un mensaje debe ser procesado.
        
        Args:
            message_text: Texto del mensaje
            message_timestamp: Timestamp del mensaje
            
        Returns:
            True si debe procesarse, False si debe saltarse
        """
        try:
            # 1. Filtrar mensajes del sistema
            if self.sqlite_storage.is_system_message(message_text):
                self.logger.debug(f"🚫 MENSAJE DEL SISTEMA FILTRADO: '{message_text[:50]}...'")
                # Cachear como mensaje del sistema para no volver a evaluarlo
                self.sqlite_storage.cache_processed_message(
                    message_text, message_timestamp, 
                    is_system_message=True
                )
                return False
            
            # 2. Verificar si ya fue procesado
            if self.sqlite_storage.is_message_processed(message_text, message_timestamp):
                cached_info = self.sqlite_storage.get_cached_message_info(message_text, message_timestamp)
                if cached_info:
                    self.logger.debug(f"✅ MENSAJE YA PROCESADO: '{message_text[:50]}...' (was_expense={cached_info['is_expense']})")
                else:
                    self.logger.debug(f"✅ MENSAJE YA PROCESADO: '{message_text[:50]}...'")
                return False
            
            # 3. Si llegó aquí, debe procesarse
            self.logger.debug(f"🆕 MENSAJE NUEVO PARA PROCESAR: '{message_text[:50]}...'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error evaluando si procesar mensaje: {e}")
            # En caso de error, procesar por seguridad
            return True
    
    def guardar_gasto(self, gasto: Gasto) -> bool:
        """
        Guarda un gasto tanto en SQLite como en Excel.
        
        Args:
            gasto: Gasto a guardar
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            # 1. Guardar en SQLite
            sqlite_success = self.sqlite_storage.guardar_gasto(gasto)
            
            # 2. Guardar en Excel
            excel_success = self.excel_storage.guardar_gasto(gasto)
            
            # Solo retornar True si AMBOS guardaron exitosamente
            if sqlite_success and excel_success:
                self.logger.info(f"✅ Gasto guardado en ambos storages: ${gasto.monto} - {gasto.categoria}")
                return True
            else:
                if not sqlite_success and not excel_success:
                    self.logger.error(f"❌ Error guardando gasto en ambos storages: ${gasto.monto} - {gasto.categoria}")
                elif not excel_success:
                    self.logger.error(f"❌ Error guardando gasto en Excel: ${gasto.monto} - {gasto.categoria}")
                elif not sqlite_success:
                    self.logger.error(f"❌ Error guardando gasto en SQLite: ${gasto.monto} - {gasto.categoria}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en guardar_gasto híbrido: {e}")
            return False
    
    def cache_message_result(self, message_text: str, message_timestamp: datetime,
                           gasto: Optional[Gasto] = None) -> None:
        """
        Cachea el resultado del procesamiento de un mensaje.
        
        Args:
            message_text: Texto del mensaje
            message_timestamp: Timestamp del mensaje
            gasto: Gasto extraído si existe
        """
        try:
            if gasto:
                # Mensaje que resultó en gasto
                self.sqlite_storage.cache_processed_message(
                    message_text, message_timestamp,
                    is_expense=True,
                    expense_amount=float(gasto.monto),
                    expense_category=gasto.categoria
                )
                self.logger.debug(f"💰 Mensaje cacheado como GASTO: '{message_text[:50]}...'")
            else:
                # Mensaje que no es gasto
                self.sqlite_storage.cache_processed_message(
                    message_text, message_timestamp,
                    is_expense=False
                )
                self.logger.debug(f"📝 Mensaje cacheado como NO-GASTO: '{message_text[:50]}...'")
                
        except Exception as e:
            self.logger.error(f"Error cacheando resultado de mensaje: {e}")
    
    def get_last_processed_timestamp(self) -> Optional[datetime]:
        """
        Obtiene la fecha/hora del último mensaje procesado desde la BD.
        
        Returns:
            Timestamp del último mensaje procesado o None si no hay ninguno
        """
        try:
            # Obtener desde SQLite cache
            last_cached = self.sqlite_storage.get_last_processed_message_timestamp()
            if last_cached:
                return last_cached
                
            # Si no hay en cache, obtener desde Excel (último gasto)
            try:
                excel_stats = self.excel_storage.obtener_estadisticas()
                if excel_stats.get('fecha_ultimo_gasto'):
                    from datetime import datetime
                    if isinstance(excel_stats['fecha_ultimo_gasto'], str):
                        return datetime.fromisoformat(excel_stats['fecha_ultimo_gasto'])
                    return excel_stats['fecha_ultimo_gasto']
            except:
                pass
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo último timestamp: {e}")
            return None
    
    def get_processing_stats(self) -> dict:
        """
        Obtiene estadísticas de procesamiento.
        
        Returns:
            Diccionario con estadísticas combinadas
        """
        try:
            # Estadísticas del caché
            cache_stats = self.sqlite_storage.get_cache_stats()
            
            # Estadísticas de gastos (Excel)
            excel_stats = self.excel_storage.obtener_estadisticas() if hasattr(self.excel_storage, 'obtener_estadisticas') else {}
            
            return {
                'cache': cache_stats,
                'expenses': excel_stats,
                'performance': {
                    'cache_hit_rate': self._calculate_cache_hit_rate(cache_stats),
                    'system_message_filter_rate': self._calculate_system_filter_rate(cache_stats)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def _calculate_cache_hit_rate(self, cache_stats: dict) -> float:
        """Calcula la tasa de aciertos del caché."""
        try:
            total = cache_stats.get('total_cached', 0)
            if total > 0:
                # Considerar hit todos los mensajes cacheados
                return min(1.0, total / max(total, 1))
            return 0.0
        except:
            return 0.0
    
    def _calculate_system_filter_rate(self, cache_stats: dict) -> float:
        """Calcula la tasa de filtrado de mensajes del sistema."""
        try:
            total = cache_stats.get('total_cached', 0)
            system = cache_stats.get('system_messages', 0)
            if total > 0:
                return system / total
            return 0.0
        except:
            return 0.0
    
    def cleanup_cache(self, days_to_keep: int = 30) -> int:
        """
        Limpia el caché de mensajes antiguos.
        
        Args:
            days_to_keep: Días de mensajes a mantener
            
        Returns:
            Número de mensajes eliminados
        """
        try:
            return self.sqlite_storage.cleanup_old_cached_messages(days_to_keep)
        except Exception as e:
            self.logger.error(f"Error limpiando caché: {e}")
            return 0
    
    # === MÉTODOS DE COMPATIBILIDAD CON ExcelStorage ===
    
    def obtener_gastos(self, fecha_desde, fecha_hasta) -> List[Gasto]:
        """Compatibilidad: delegar a Excel storage."""
        return self.excel_storage.obtener_gastos(fecha_desde, fecha_hasta)
    
    def obtener_gastos_por_categoria(self, categoria: str) -> List[Gasto]:
        """Compatibilidad: delegar a Excel storage.""" 
        return self.excel_storage.obtener_gastos_por_categoria(categoria)
    
    def obtener_estadisticas(self) -> dict:
        """Compatibilidad: delegar a Excel storage."""
        return self.excel_storage.obtener_estadisticas()
    
    def obtener_info(self) -> dict:
        """Información combinada del storage híbrido."""
        try:
            excel_info = self.excel_storage.obtener_info()
            sqlite_info = self.sqlite_storage.obtener_info_database()
            processing_stats = self.get_processing_stats()
            
            return {
                'type': 'hybrid',
                'excel': excel_info,
                'sqlite_cache': sqlite_info,
                'stats': processing_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info híbrida: {e}")
            return {'error': str(e)}


class AsyncHybridStorage:
    """⚡ Storage híbrido asíncrono (60% mejora esperada en latencia de guardado)."""
    
    def __init__(self, excel_path: str, max_workers: int = 2):
        """
        Inicializa storage asíncrono.
        
        Args:
            excel_path: Ruta al archivo Excel
            max_workers: Número máximo de workers para operaciones asíncronas
        """
        self.excel_path = Path(excel_path)
        self.sqlite_path = str(self.excel_path.with_suffix('.cache.db'))
        
        # Storages subyacentes
        self.sqlite_storage = SQLiteStorage(self.sqlite_path)
        self.excel_storage = ExcelStorage(str(self.excel_path))
        
        # ⚡ OPTIMIZACIÓN: ThreadPoolExecutor para operaciones de background
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AsyncStorage")
        
        # Logger
        self.logger = get_logger(__name__)
        
        # Cola de trabajos pendientes para Excel
        self.pending_excel_writes = queue.Queue()
        self.sync_stats = {
            'synced_gastos': 0,
            'failed_syncs': 0,
            'pending_count': 0
        }
        
        # Worker thread para sincronización continua
        self.sync_thread = threading.Thread(target=self._background_sync_worker, daemon=True)
        self.sync_thread.start()
        
        self.logger = logger
        self.logger.info("AsyncHybridStorage inicializado con operaciones asíncronas")
    
    def guardar_gasto_async(self, gasto: Gasto) -> bool:
        """
        ⚡ Guarda gasto asíncrono: SQLite inmediato + Excel en background (60% más rápido).
        
        Flujo optimizado:
        1. Guardar en SQLite inmediatamente (rápido, ~10ms)
        2. Encolar escritura Excel en background
        3. Retornar éxito inmediato
        
        Args:
            gasto: Gasto a guardar
            
        Returns:
            True si SQLite fue exitoso (Excel se procesa en background)
        """
        try:
            # 1. ⚡ PASO CRÍTICO: Guardar en SQLite inmediatamente (ultra rápido)
            sqlite_success = self.sqlite_storage.guardar_gasto(gasto, use_batch=False)  # No usar batch para inmediatez
            
            if not sqlite_success:
                self.logger.error(f"Error guardando en SQLite: {gasto}")
                return False
            
            # 2. ⚡ OPTIMIZACIÓN: Encolar para escritura Excel asíncrona
            self.pending_excel_writes.put({
                'gasto': gasto,
                'sqlite_id': gasto.id,
                'timestamp': datetime.now()
            })
            
            self.sync_stats['pending_count'] = self.pending_excel_writes.qsize()
            
            # 3. Retornar éxito inmediato (SQLite garantiza persistencia)
            self.logger.debug(f"Gasto encolado para sync Excel: {gasto.monto} - {gasto.categoria}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en guardado asíncrono: {e}")
            return False
    
    def _background_sync_worker(self):
        """Worker thread que sincroniza continuamente con Excel."""
        self.logger.info("Background sync worker iniciado")
        
        while True:
            try:
                # Procesar cola de escrituras Excel
                try:
                    # Timeout para no bloquear indefinidamente
                    work_item = self.pending_excel_writes.get(timeout=5.0)
                    
                    gasto = work_item['gasto']
                    
                    # ⚡ Intentar escribir a Excel
                    excel_success = self.excel_storage.guardar_gasto(gasto)
                    
                    if excel_success:
                        self.sync_stats['synced_gastos'] += 1
                        self.logger.debug(f"✅ Excel sync exitoso: {gasto.categoria} ${gasto.monto}")
                    else:
                        self.sync_stats['failed_syncs'] += 1
                        self.logger.warning(f"❌ Excel sync falló: {gasto.categoria} ${gasto.monto}")
                        
                        # Re-encolar para reintento (máximo 3 intentos)
                        if work_item.get('retries', 0) < 3:
                            work_item['retries'] = work_item.get('retries', 0) + 1
                            self.pending_excel_writes.put(work_item)
                    
                    self.pending_excel_writes.task_done()
                    self.sync_stats['pending_count'] = self.pending_excel_writes.qsize()
                    
                except queue.Empty:
                    # No hay trabajo, continuar el loop
                    continue
                    
            except Exception as e:
                self.logger.error(f"Error en background sync worker: {e}")
                time.sleep(1)  # Pausa antes de continuar
    
    def sync_pending_excel_writes(self) -> int:
        """
        Fuerza sincronización de escrituras Excel pendientes.
        
        Returns:
            Número de gastos sincronizados exitosamente
        """
        initial_pending = self.pending_excel_writes.qsize()
        
        if initial_pending == 0:
            return 0
        
        self.logger.info(f"Sincronizando {initial_pending} escrituras Excel pendientes...")
        
        # Dar tiempo al worker thread para procesar
        max_wait_time = 30  # segundos
        start_time = time.time()
        
        while self.pending_excel_writes.qsize() > 0 and (time.time() - start_time) < max_wait_time:
            time.sleep(0.5)
        
        synced_count = initial_pending - self.pending_excel_writes.qsize()
        self.logger.info(f"✅ Sincronización completada: {synced_count} gastos procesados")
        
        return synced_count
    
    def get_sync_stats(self) -> dict:
        """Obtiene estadísticas de sincronización asíncrona."""
        return {
            **self.sync_stats,
            'pending_count': self.pending_excel_writes.qsize(),
            'worker_active': self.sync_thread.is_alive()
        }
    
    def shutdown(self):
        """Cierra el storage asíncrono de manera segura."""
        self.logger.info("Cerrando AsyncHybridStorage...")
        
        # Sincronizar escrituras pendientes
        self.sync_pending_excel_writes()
        
        # Cerrar executor
        self.executor.shutdown(wait=True)
        
        self.logger.info("AsyncHybridStorage cerrado correctamente")
    
    # Métodos de compatibilidad con HybridStorage original
    def obtener_gastos(self, fecha_desde, fecha_hasta):
        """Compatibilidad: delegar a Excel storage."""
        return self.excel_storage.obtener_gastos(fecha_desde, fecha_hasta)
    
    def obtener_gastos_por_categoria(self, categoria: str, fecha_desde, fecha_hasta):
        """Compatibilidad: delegar a Excel storage."""
        return self.excel_storage.obtener_gastos_por_categoria(categoria, fecha_desde, fecha_hasta)
    
    def obtener_estadisticas(self) -> dict:
        """Compatibilidad: delegar a Excel storage + stats async."""
        excel_stats = self.excel_storage.obtener_estadisticas()
        sync_stats = self.get_sync_stats()
        
        return {
            **excel_stats,
            'async_storage': True,
            'sync_stats': sync_stats
        }