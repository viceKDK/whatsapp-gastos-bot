"""
Dashboard Web Interactivo

Interfaz web con gráficos en tiempo real para visualizar gastos,
métricas y análisis usando Flask y Chart.js.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from decimal import Decimal
import sqlite3

try:
    from flask import Flask, render_template, jsonify, request, send_from_directory
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

from config.config_manager import get_config
from shared.logger import get_logger
from shared.metrics import get_metrics_collector, get_system_health
from infrastructure.storage.sqlite_writer import SQLiteStorage
from infrastructure.storage.excel_writer import ExcelStorage
from app.services.dashboard_analytics import moving_average
from app.services.data_aggregator import aggregate_category_details
from app.services.export_service import rows_to_csv


logger = get_logger(__name__)


class DashboardDataProvider:
    """Proveedor de datos para el dashboard."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logger
        
        # Inicializar conexión a datos
        self.storage = self._initialize_storage()
        self.metrics_collector = get_metrics_collector()
        # Control de caché interna (deshabilitable si usamos Flask-Caching)
        self.use_internal_cache = True
    
    def _initialize_storage(self):
        """Inicializa conexión al storage principal."""
        try:
            storage_type = self.config.storage.primary_storage
            
            if storage_type == "sqlite":
                db_path = Path(self.config.storage.sqlite_db_path)
                if db_path.exists():
                    return SQLiteStorage(str(db_path))
            elif storage_type == "excel":
                excel_path = Path(self.config.storage.excel_file_path)
                if excel_path.exists():
                    return ExcelStorage(str(excel_path))
            
            # Fallback a Excel si no existe SQLite
            excel_path = Path(self.config.storage.excel_file_path)
            if excel_path.exists():
                return ExcelStorage(str(excel_path))
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error inicializando storage para dashboard: {e}")
            return None

    # --- Simple cache (TTL) para acelerar respuestas (fallback si no hay Flask-Caching) ---
    _cache_store: Dict[str, Any] = {}
    _cache_time: Dict[str, datetime] = {}

    def _cache_get(self, key: str, ttl_seconds: int) -> Optional[Any]:
        now = datetime.now()
        if not getattr(self, 'use_internal_cache', True):
            return None
        ts = self._cache_time.get(key)
        if ts and (now - ts).total_seconds() <= ttl_seconds:
            return self._cache_store.get(key)
        return None

    def _cache_set(self, key: str, value: Any) -> None:
        if not getattr(self, 'use_internal_cache', True):
            return
        self._cache_store[key] = value
        self._cache_time[key] = datetime.now()

    # --- FX rate provider (with simple caching) ---
    def get_fx_rate(self, base: str = 'USD', quote: str = 'UYU', ttl_seconds: int = 6 * 60 * 60) -> Dict[str, Any]:
        """Obtiene tasa de cambio con caché y múltiples proveedores."""
        base = (base or 'USD').upper()
        quote = (quote or 'UYU').upper()

        if base == quote:
            return {
                'base': base,
                'quote': quote,
                'rate': 1.0,
                'provider': 'local',
                'timestamp': datetime.now().isoformat(),
                'cached': False,
            }

        cache_key = f'fx:{base}->{quote}'
        cached = self._cache_get(cache_key, ttl_seconds)
        if cached is not None:
            return { **cached, 'cached': True }

        def _try_exchangerate_host() -> Optional[Dict[str, Any]]:
            import requests
            url = f'https://api.exchangerate.host/latest?base={base}&symbols={quote}'
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            data = resp.json() or {}
            rate_val = (data.get('rates') or {}).get(quote)
            if rate_val is None:
                return None
            rate = float(rate_val)
            if rate <= 0:
                return None
            return {
                'base': base,
                'quote': quote,
                'rate': rate,
                'provider': 'exchangerate.host',
                'timestamp': datetime.now().isoformat(),
            }

        def _try_er_api() -> Optional[Dict[str, Any]]:
            import requests
            url = f'https://open.er-api.com/v6/latest/{base}'
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            data = resp.json() or {}
            if data.get('result') != 'success':
                return None
            rates = data.get('rates') or {}
            rate_val = rates.get(quote)
            if rate_val is None:
                return None
            rate = float(rate_val)
            if rate <= 0:
                return None
            return {
                'base': base,
                'quote': quote,
                'rate': rate,
                'provider': 'open.er-api.com',
                'timestamp': datetime.now().isoformat(),
            }

        def _try_frankfurter() -> Optional[Dict[str, Any]]:
            """Frankfurter (ECB data): https://www.frankfurter.app/"""
            import requests
            url = f'https://api.frankfurter.app/latest?from={base}&to={quote}'
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            data = resp.json() or {}
            rates = data.get('rates') or {}
            rate_val = rates.get(quote)
            if rate_val is None:
                return None
            rate = float(rate_val)
            if rate <= 0:
                return None
            return {
                'base': base,
                'quote': quote,
                'rate': rate,
                'provider': 'frankfurter.app',
                'timestamp': datetime.now().isoformat(),
            }

        def _try_fawaz_gh_cdn() -> Optional[Dict[str, Any]]:
            """Static JSON on jsdelivr CDN: https://github.com/fawazahmed0/currency-api"""
            import requests
            path = f'https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/{base.lower()}/{quote.lower()}.json'
            resp = requests.get(path, timeout=8)
            resp.raise_for_status()
            data = resp.json() or {}
            rate_val = data.get(quote.lower())
            if rate_val is None:
                return None
            rate = float(rate_val)
            if rate <= 0:
                return None
            return {
                'base': base,
                'quote': quote,
                'rate': rate,
                'provider': 'cdn.jsdelivr currency-api',
                'timestamp': datetime.now().isoformat(),
            }

        # Intento 1: exchangerate.host
        try:
            payload = _try_exchangerate_host()
            if payload:
                self._cache_set(cache_key, payload)
                payload['cached'] = False
                return payload
        except Exception as e1:
            self.logger.warning(f"FX primary provider failure (exchangerate.host): {e1}")

        # Intento 2: open.er-api.com
        try:
            payload = _try_er_api()
            if payload:
                self._cache_set(cache_key, payload)
                payload['cached'] = False
                return payload
        except Exception as e2:
            self.logger.warning(f"FX secondary provider failure (open.er-api.com): {e2}")

        # Intento 3: frankfurter.app
        try:
            payload = _try_frankfurter()
            if payload:
                self._cache_set(cache_key, payload)
                payload['cached'] = False
                return payload
        except Exception as e3:
            self.logger.warning(f"FX tertiary provider failure (frankfurter.app): {e3}")

        # Intento 4: fawazahmed0 currency-api via jsDelivr CDN
        try:
            payload = _try_fawaz_gh_cdn()
            if payload:
                self._cache_set(cache_key, payload)
                payload['cached'] = False
                return payload
        except Exception as e4:
            self.logger.warning(f"FX fallback provider failure (jsdelivr currency-api): {e4}")

        # Si existe un valor viejo en cache_store (aunque esté vencido), úsalo marcado como stale
        stale = self._cache_store.get(cache_key)
        if stale:
            return { **stale, 'cached': True, 'stale': True }

        # Fallback fijo
        fallback = 40.0 if base == 'USD' and quote == 'UYU' else 1.0
        return {
            'base': base,
            'quote': quote,
            'rate': fallback,
            'provider': 'fallback',
            'timestamp': datetime.now().isoformat(),
            'cached': False,
        }
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas resumidas con comparaciones."""
        try:
            cached = self._cache_get('summary', 30)
            if cached is not None:
                return cached
            if not self.storage:
                return self._get_empty_stats()

            now = datetime.now()
            start_this_month = datetime(now.year, now.month, 1)
            end_this_month = now

            # Mes anterior
            if now.month == 1:
                start_last_month = datetime(now.year - 1, 12, 1)
                end_last_month = datetime(now.year - 1, 12, 31, 23, 59, 59)
            else:
                start_last_month = datetime(now.year, now.month - 1, 1)
                last_day = (start_this_month - timedelta(days=1)).day
                end_last_month = datetime(now.year, now.month - 1, last_day, 23, 59, 59)

            # Datos
            gastos_mes_actual = self.storage.obtener_gastos_por_fecha(start_this_month, end_this_month)
            gastos_mes_anterior = self.storage.obtener_gastos_por_fecha(start_last_month, end_last_month)
            all_gastos = self.storage.obtener_todos_gastos()

            monto_mes_actual = sum(float(g.monto) for g in gastos_mes_actual)
            monto_mes_anterior = sum(float(g.monto) for g in gastos_mes_anterior)
            total_monto = sum(float(g.monto) for g in all_gastos)

            cambio_porcentual = ((monto_mes_actual - monto_mes_anterior) / monto_mes_anterior) * 100 if monto_mes_anterior > 0 else 0

            dias_transcurridos = (now - start_this_month).days + 1
            promedio_diario = (monto_mes_actual / dias_transcurridos) if dias_transcurridos > 0 else 0

            dias_en_mes = (datetime(now.year, now.month + 1, 1) - timedelta(days=1)).day if now.month < 12 else 31
            proyeccion_mensual = promedio_diario * dias_en_mes

            if all_gastos:
                categorias = [g.categoria for g in all_gastos]
                categoria_mas_comun = max(set(categorias), key=categorias.count)
            else:
                categoria_mas_comun = "N/A"

            gasto_mas_alto = max((float(g.monto) for g in gastos_mes_actual), default=0)

            result = {
                'total_gastos': len(all_gastos),
                'total_monto': total_monto,
                'gastos_este_mes': len(gastos_mes_actual),
                'monto_este_mes': monto_mes_actual,
                'promedio_diario': promedio_diario,
                'proyeccion_mensual': proyeccion_mensual,
                'monto_mes_anterior': monto_mes_anterior,
                'cambio_porcentual': cambio_porcentual,
                'cambio_absoluto': monto_mes_actual - monto_mes_anterior,
                'categoria_mas_comun': categoria_mas_comun,
                'gasto_mas_alto': gasto_mas_alto,
                'ultima_actualizacion': datetime.now().isoformat(),
                'periodo': {
                    'inicio': start_this_month.isoformat(),
                    'fin': end_this_month.isoformat(),
                    'dias_transcurridos': dias_transcurridos,
                    'dias_totales': dias_en_mes
                }
            }
            self._cache_set('summary', result)
            return result

        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return self._get_empty_stats()
    
    def get_gastos_por_categoria(self, days: int = 30) -> Dict[str, Any]:
        """Obtiene gastos agrupados por categoría con detalles."""
        try:
            cache_key = f'categories:{days}'
            cached = self._cache_get(cache_key, 30)
            if cached is not None:
                return cached
            if not self.storage:
                return {'categories': [], 'amounts': [], 'details': []}

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            gastos = self.storage.obtener_gastos_por_fecha(start_date, end_date)

            agg = aggregate_category_details(gastos)
            categories = agg['categories']
            amounts = agg['amounts']
            details = agg['details']
            total_amount = agg['total_amount']

            result = {
                'categories': categories,
                'amounts': amounts,
                'details': details,
                'total_categories': len(categories),
                'total_amount': total_amount,
                'period_days': days
            }
            self._cache_set(cache_key, result)
            return result

        except Exception as e:
            self.logger.error(f"Error obteniendo gastos por categoría: {e}")
            return {'categories': [], 'amounts': [], 'details': []}
    
    def get_gastos_temporales(self, days: int = 30) -> Dict[str, Any]:
        """Obtiene gastos en serie temporal."""
        try:
            cache_key = f'timeline:{days}'
            cached = self._cache_get(cache_key, 30)
            if cached is not None:
                return cached
            if not self.storage:
                return {'dates': [], 'amounts': []}
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            gastos = self.storage.obtener_gastos_por_fecha(start_date, end_date)
            
            # Agrupar por fecha
            fecha_montos = {}
            current_date = start_date
            
            # Inicializar todas las fechas con 0
            while current_date <= end_date:
                fecha_str = current_date.strftime('%Y-%m-%d')
                fecha_montos[fecha_str] = 0
                current_date += timedelta(days=1)
            
            # Sumar gastos por fecha
            for gasto in gastos:
                fecha_str = gasto.fecha.strftime('%Y-%m-%d')
                if fecha_str in fecha_montos:
                    fecha_montos[fecha_str] += float(gasto.monto)
            
            # Convertir a listas ordenadas
            sorted_dates = sorted(fecha_montos.items())
            dates = [item[0] for item in sorted_dates]
            amounts = [item[1] for item in sorted_dates]
            
            result = {
                'dates': dates,
                'amounts': amounts,
                'period_days': days,
                'total_days': len(dates)
            }
            self._cache_set(cache_key, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error obteniendo serie temporal: {e}")
            return {'dates': [], 'amounts': []}
    
    def get_gastos_recientes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene gastos más recientes."""
        try:
            if not self.storage:
                return []
            
            gastos = self.storage.obtener_todos_gastos()
            
            # Ordenar por fecha (más reciente primero)
            gastos_ordenados = sorted(gastos, key=lambda g: g.fecha, reverse=True)
            gastos_recientes = gastos_ordenados[:limit]
            
            # Convertir a formato JSON serializable
            result = []
            for gasto in gastos_recientes:
                result.append({
                    'id': getattr(gasto, 'id', 'N/A'),
                    'monto': float(gasto.monto),
                    'categoria': gasto.categoria,
                    'descripcion': gasto.descripcion or '',
                    'fecha': gasto.fecha.strftime('%Y-%m-%d %H:%M'),
                    'fecha_iso': gasto.fecha.isoformat()
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error obteniendo gastos recientes: {e}")
            return []
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema."""
        try:
            cached = self._cache_get('metrics', 15)
            if cached is not None:
                return cached
            health = get_system_health()
            operation_stats = self.metrics_collector.get_operation_stats()
            result = {
                'health': health,
                'operations': operation_stats,
                'timestamp': datetime.now().isoformat()
            }
            self._cache_set('metrics', result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error obteniendo métricas del sistema: {e}")
            return {
                'health': {'status': 'unknown'},
                'operations': {},
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_empty_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas vacías como fallback."""
        return {
            'total_gastos': 0,
            'total_monto': 0.0,
            'gastos_este_mes': 0,
            'monto_este_mes': 0.0,
            'promedio_diario': 0.0,
            'categoria_mas_comun': 'N/A',
            'gasto_mas_alto': 0.0,
            'ultima_actualizacion': datetime.now().isoformat()
        }

    def get_balance_info(self) -> Dict[str, Any]:
        """Obtiene información de balance consolidado."""
        try:
            if not self.storage:
                return {'balance': 0, 'cambio': 0}

            all_gastos = self.storage.obtener_todos_gastos()
            total_balance = sum(float(g.monto) for g in all_gastos)

            now = datetime.now()
            if now.month == 1:
                start_last_month = datetime(now.year - 1, 12, 1)
                end_last_month = datetime(now.year - 1, 12, 31, 23, 59, 59)
            else:
                start_last_month = datetime(now.year, now.month - 1, 1)
                last_day = (datetime(now.year, now.month, 1) - timedelta(days=1)).day
                end_last_month = datetime(now.year, now.month - 1, last_day, 23, 59, 59)

            gastos_mes_anterior = self.storage.obtener_gastos_por_fecha(start_last_month, end_last_month)
            balance_mes_anterior = sum(float(g.monto) for g in gastos_mes_anterior)

            cambio_porcentual = ((total_balance - balance_mes_anterior) / balance_mes_anterior * 100) if balance_mes_anterior > 0 else 0

            return {
                'balance_total': total_balance,
                'balance_mes_anterior': balance_mes_anterior,
                'cambio_porcentual': cambio_porcentual,
                'cambio_absoluto': total_balance - balance_mes_anterior,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error obteniendo balance: {e}")
            return {'balance': 0, 'cambio': 0}

    def get_spending_info(self, limite_mensual: float = 50000) -> Dict[str, Any]:
        """Obtiene información de gastos y límite mensual."""
        try:
            cached = self._cache_get('spending', 30)
            if cached is not None:
                return cached
            if not self.storage:
                return self._get_empty_spending()

            now = datetime.now()
            start_month = datetime(now.year, now.month, 1)
            gastos_mes = self.storage.obtener_gastos_por_fecha(start_month, now)

            total_mes = sum(float(g.monto) for g in gastos_mes)
            porcentaje_usado = (total_mes / limite_mensual * 100) if limite_mensual > 0 else 0

            dias_en_mes = (datetime(now.year, now.month + 1, 1) - timedelta(days=1)).day if now.month < 12 else 31
            dias_restantes = max(0, dias_en_mes - now.day)

            dias_transcurridos = max(1, now.day)
            promedio_diario = total_mes / dias_transcurridos if dias_transcurridos > 0 else 0
            proyeccion = promedio_diario * dias_en_mes

            monto_restante = limite_mensual - total_mes
            limite_diario_restante = (monto_restante / dias_restantes) if dias_restantes > 0 else 0

            result = {
                'total_gastado': total_mes,
                'limite_mensual': limite_mensual,
                'monto_restante': monto_restante,
                'porcentaje_usado': porcentaje_usado,
                'promedio_diario': promedio_diario,
                'limite_diario_restante': limite_diario_restante,
                'proyeccion_mes': proyeccion,
                'dias_restantes': dias_restantes,
                'alerta': {
                    'nivel': 'normal' if porcentaje_usado < 80 else 'warning' if porcentaje_usado < 100 else 'danger',
                    'mensaje': self._get_spending_alert_message(porcentaje_usado)
                },
                'timestamp': datetime.now().isoformat()
            }
            self._cache_set('spending', result)
            return result

        except Exception as e:
            self.logger.error(f"Error obteniendo spending info: {e}")
            return self._get_empty_spending()

    def _get_spending_alert_message(self, porcentaje: float) -> str:
        """Genera mensaje de alerta según el porcentaje usado."""
        if porcentaje < 80:
            return "Gasto dentro del límite"
        elif porcentaje < 100:
            return "Acercándote al límite de gastos"
        else:
            return "¡Límite de gastos superado!"

    def _get_empty_spending(self) -> Dict[str, Any]:
        """Retorna spending info vacío."""
        return {
            'total_gastado': 0,
            'limite_mensual': 50000,
            'monto_restante': 50000,
            'porcentaje_usado': 0,
            'promedio_diario': 0,
            'limite_diario_restante': 0,
            'proyeccion_mes': 0,
            'dias_restantes': 30,
            'alerta': {'nivel': 'normal', 'mensaje': 'Sin gastos registrados'},
            'timestamp': datetime.now().isoformat()
        }

    def search_gastos(
        self,
        query: str = '',
        categoria: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        min_monto: Optional[float] = None,
        max_monto: Optional[float] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Búsqueda avanzada de gastos."""
        try:
            # no cache: consultas variables
            if not self.storage:
                return []

            if not fecha_desde:
                dt_desde = datetime.now() - timedelta(days=365)
            else:
                dt_desde = datetime.fromisoformat(fecha_desde)

            dt_hasta = datetime.fromisoformat(fecha_hasta) if fecha_hasta else datetime.now()

            gastos = self.storage.obtener_gastos_por_fecha(dt_desde, dt_hasta)

            if categoria:
                gastos = [g for g in gastos if g.categoria.lower() == categoria.lower()]

            if min_monto is not None:
                gastos = [g for g in gastos if float(g.monto) >= min_monto]

            if max_monto is not None:
                gastos = [g for g in gastos if float(g.monto) <= max_monto]

            if query:
                q = query.lower()
                gastos = [
                    g for g in gastos
                    if (g.descripcion and q in g.descripcion.lower()) or q in g.categoria.lower()
                ]

            gastos = sorted(gastos, key=lambda g: g.fecha, reverse=True)[:limit]

            return [
                {
                    'id': getattr(g, 'id', None),
                    'monto': float(g.monto),
                    'categoria': g.categoria,
                    'descripcion': g.descripcion or '',
                    'fecha': g.fecha.strftime('%Y-%m-%d %H:%M'),
                    'fecha_iso': g.fecha.isoformat()
                }
                for g in gastos
            ]

        except Exception as e:
            self.logger.error(f"Error en búsqueda de gastos: {e}")
            return []

    def get_month_comparison(self) -> Dict[str, Any]:
        """Compara mes actual con mes anterior, por categoría y totales."""
        try:
            cached = self._cache_get('month_comparison', 60)
            if cached is not None:
                return cached
            if not self.storage:
                return {'mes_actual': {}, 'mes_anterior': {}, 'cambios': {}}

            now = datetime.now()
            start_this = datetime(now.year, now.month, 1)
            gastos_this = self.storage.obtener_gastos_por_fecha(start_this, now)

            if now.month == 1:
                start_last = datetime(now.year - 1, 12, 1)
                end_last = datetime(now.year - 1, 12, 31, 23, 59, 59)
            else:
                start_last = datetime(now.year, now.month - 1, 1)
                last_day = (start_this - timedelta(days=1)).day
                end_last = datetime(now.year, now.month - 1, last_day, 23, 59, 59)

            gastos_last = self.storage.obtener_gastos_por_fecha(start_last, end_last)

            def group_by_category(gastos):
                result: Dict[str, float] = {}
                for g in gastos:
                    result[g.categoria] = result.get(g.categoria, 0.0) + float(g.monto)
                return result

            this_by_cat = group_by_category(gastos_this)
            last_by_cat = group_by_category(gastos_last)

            all_categories = set(this_by_cat.keys()) | set(last_by_cat.keys())
            cambios_categoria: Dict[str, Any] = {}
            for cat in all_categories:
                this_val = this_by_cat.get(cat, 0.0)
                last_val = last_by_cat.get(cat, 0.0)
                if last_val > 0:
                    cambio_pct = ((this_val - last_val) / last_val) * 100
                else:
                    cambio_pct = 100 if this_val > 0 else 0
                cambios_categoria[cat] = {
                    'mes_actual': this_val,
                    'mes_anterior': last_val,
                    'cambio_absoluto': this_val - last_val,
                    'cambio_porcentual': cambio_pct
                }

            total_this = sum(this_by_cat.values())
            total_last = sum(last_by_cat.values())
            cambio_total_pct = ((total_this - total_last) / total_last * 100) if total_last > 0 else 0

            result = {
                'mes_actual': {
                    'total': total_this,
                    'count': len(gastos_this),
                    'por_categoria': this_by_cat
                },
                'mes_anterior': {
                    'total': total_last,
                    'count': len(gastos_last),
                    'por_categoria': last_by_cat
                },
                'cambios': {
                    'total_absoluto': total_this - total_last,
                    'total_porcentual': cambio_total_pct,
                    'por_categoria': cambios_categoria,
                    'categorias_nuevas': list(set(this_by_cat.keys()) - set(last_by_cat.keys())),
                    'categorias_eliminadas': list(set(last_by_cat.keys()) - set(this_by_cat.keys()))
                },
                'timestamp': datetime.now().isoformat()
            }
            self._cache_set('month_comparison', result)
            return result
        except Exception as e:
            self.logger.error(f"Error en comparación mensual: {e}")
            return {'mes_actual': {}, 'mes_anterior': {}, 'cambios': {}}

    def get_trends_info(self, days: int = 90) -> Dict[str, Any]:
        """Tendencias básicas: promedios móviles y top categorías en período."""
        try:
            cache_key = f'trends:{days}'
            cached = self._cache_get(cache_key, 60)
            if cached is not None:
                return cached
            tl = self.get_gastos_temporales(days)
            amounts = tl.get('amounts', [])
            dates = tl.get('dates', [])
            mov_avg: List[float] = moving_average(amounts, window=7)

            cats = self.get_gastos_por_categoria(days)
            top_categorias = [
                {'categoria': d['categoria'], 'total': d['total'], 'porcentaje': d['porcentaje']}
                for d in cats.get('details', [])[:5]
            ]

            result = {
                'timeline': {'dates': dates, 'amounts': amounts, 'moving_avg_7d': mov_avg},
                'top_categorias': top_categorias,
                'timestamp': datetime.now().isoformat()
            }
            self._cache_set(cache_key, result)
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo tendencias: {e}")
            return {'timeline': {'dates': [], 'amounts': [], 'moving_avg_7d': []}, 'top_categorias': []}

    def export_data(self, formato: str = 'json', fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None) -> Any:
        """Exporta datos de gastos en el formato solicitado."""
        try:
            if not self.storage:
                return [] if formato == 'json' else ''

            dt_desde = datetime.fromisoformat(fecha_desde) if fecha_desde else (datetime.now() - timedelta(days=365))
            dt_hasta = datetime.fromisoformat(fecha_hasta) if fecha_hasta else datetime.now()

            gastos = self.storage.obtener_gastos_por_fecha(dt_desde, dt_hasta)
            rows = [
                {
                    'id': getattr(g, 'id', None),
                    'fecha': g.fecha.strftime('%Y-%m-%d'),
                    'hora': g.fecha.strftime('%H:%M:%S'),
                    'monto': float(g.monto),
                    'categoria': g.categoria,
                    'descripcion': g.descripcion or ''
                }
                for g in gastos
            ]

            if formato == 'json':
                return rows
            elif formato == 'csv':
                return rows_to_csv(rows)
            else:
                return rows
        except Exception as e:
            self.logger.error(f"Error exportando datos: {e}")
            return [] if formato == 'json' else ''


class DashboardApp:
    """Aplicación Flask para el dashboard."""
    
    def __init__(self):
        if not HAS_FLASK:
            raise RuntimeError("Flask not installed. Install with: pip install flask flask-cors")
        
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        
        # Configurar CORS para desarrollo
        CORS(self.app)

        # Opcional: compresión si está instalada
        try:
            from flask_compress import Compress  # type: ignore
            Compress(self.app)
        except Exception:
            pass

        # Opcional: Flask-Caching si está instalada
        self.cache = None
        try:
            from flask_caching import Cache  # type: ignore
            self.cache = Cache(self.app, config={
                'CACHE_TYPE': 'SimpleCache',
                'CACHE_DEFAULT_TIMEOUT': 30
            })
        except Exception:
            self.cache = None
        
        self.data_provider = DashboardDataProvider()
        self.logger = logger

        # Configurar rutas
        self.setup_routes()
        
        # Deshabilitar caché interna del proveedor si usamos Flask-Caching
        if self.cache is not None and hasattr(self.data_provider, 'use_internal_cache'):
            self.data_provider.use_internal_cache = False
    
    def setup_routes(self):
        """Configura las rutas de la aplicación."""
        
        
        @self.app.route('/api/summary')
        def api_summary():
            """API endpoint para estadísticas resumidas."""
            try:
                stats = self.data_provider.get_summary_stats()
                return jsonify({
                    'success': True,
                    'data': stats
                })
            except Exception as e:
                self.logger.error(f"Error en API summary: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/categories')
        def api_categories():
            """API endpoint para gastos por categoría."""
            try:
                days = request.args.get('days', 30, type=int)
                data = self.data_provider.get_gastos_por_categoria(days)
                return jsonify({
                    'success': True,
                    'data': data
                })
            except Exception as e:
                self.logger.error(f"Error en API categories: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/timeline')
        def api_timeline():
            """API endpoint para serie temporal de gastos."""
            try:
                days = request.args.get('days', 30, type=int)
                data = self.data_provider.get_gastos_temporales(days)
                return jsonify({
                    'success': True,
                    'data': data
                })
            except Exception as e:
                self.logger.error(f"Error en API timeline: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/recent')
        def api_recent():
            """API endpoint para gastos recientes."""
            try:
                limit = request.args.get('limit', 10, type=int)
                data = self.data_provider.get_gastos_recientes(limit)
                return jsonify({
                    'success': True,
                    'data': data
                })
            except Exception as e:
                self.logger.error(f"Error en API recent: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """API endpoint para métricas del sistema."""
            try:
                data = self.data_provider.get_system_metrics()
                return jsonify({
                    'success': True,
                    'data': data
                })
            except Exception as e:
                self.logger.error(f"Error en API metrics: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/v2/balance')
        def api_balance():
            """API endpoint para balance consolidado."""
            try:
                data = self.data_provider.get_balance_info()
                return jsonify({'success': True, 'data': data})
            except Exception as e:
                self.logger.error(f"Error en API balance: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/v2/spending')
        def api_spending():
            """API endpoint para información de gastos y límites."""
            try:
                data = self.data_provider.get_spending_info()
                return jsonify({'success': True, 'data': data})
            except Exception as e:
                self.logger.error(f"Error en API spending: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/v2/search')
        def api_search():
            """API endpoint para búsqueda de gastos."""
            try:
                query = request.args.get('query', '')
                categoria = request.args.get('categoria', 'all')
                fecha_desde = request.args.get('from')
                fecha_hasta = request.args.get('to')
                min_monto = request.args.get('min', type=float)
                max_monto = request.args.get('max', type=float)
                limit = request.args.get('limit', 50, type=int)

                data = self.data_provider.search_gastos(
                    query=query,
                    categoria=(categoria if categoria != 'all' else None),
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    min_monto=min_monto,
                    max_monto=max_monto,
                    limit=limit
                )
                return jsonify({'success': True, 'data': data, 'count': len(data)})
            except Exception as e:
                self.logger.error(f"Error en API search: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/v2/export')
        def api_export():
            """API endpoint para exportar datos."""
            try:
                from flask import Response
                formato = request.args.get('format', 'json')
                fecha_desde = request.args.get('from')
                fecha_hasta = request.args.get('to')

                data = self.data_provider.export_data(
                    formato=formato,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta
                )

                if formato == 'json':
                    return jsonify({'success': True, 'data': data})
                elif formato == 'csv':
                    return Response(
                        data,
                        mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment;filename=gastos.csv'}
                    )
                else:
                    return jsonify({'success': False, 'error': 'Formato no soportado'}), 400
            except Exception as e:
                self.logger.error(f"Error en API export: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/v2/trends')
        def api_trends():
            """API endpoint para tendencias."""
            try:
                days = request.args.get('days', 90, type=int)
                data = self.data_provider.get_trends_info(days)
                return jsonify({'success': True, 'data': data})
            except Exception as e:
                self.logger.error(f"Error en API trends: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/v2/month-comparison')
        def api_month_comparison():
            """API endpoint para comparación mes actual vs anterior."""
            try:
                data = self.data_provider.get_month_comparison()
                return jsonify({'success': True, 'data': data})
            except Exception as e:
                self.logger.error(f"Error en API month-comparison: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/v2/fx')
        def api_fx():
            """Obtiene tasa de cambio con caché del servidor."""
            try:
                base = (request.args.get('base') or 'USD').upper()
                quote = (request.args.get('quote') or 'UYU').upper()
                data = self.data_provider.get_fx_rate(base, quote)
                return jsonify({'success': True, 'data': data})
            except Exception as e:
                self.logger.error(f"Error en API fx: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # Aplicar caché a endpoints si Flask-Caching está disponible
        self._apply_route_caching()

    def _apply_route_caching(self) -> None:
        try:
            if not self.cache:
                return
            wrap = self.app.view_functions

            def cache_endpoint(name: str, timeout: int = 30, query_string: bool = False):
                if name in wrap:
                    wrap[name] = self.cache.cached(timeout=timeout, query_string=query_string)(wrap[name])

            cache_endpoint('api_summary', timeout=30)
            cache_endpoint('api_categories', timeout=30, query_string=True)
            cache_endpoint('api_timeline', timeout=30, query_string=True)
            cache_endpoint('api_recent', timeout=15, query_string=True)
            cache_endpoint('api_metrics', timeout=15)
            cache_endpoint('api_balance', timeout=30)
            cache_endpoint('api_spending', timeout=30)
            cache_endpoint('api_trends', timeout=60, query_string=True)
            cache_endpoint('api_month_comparison', timeout=60)
        except Exception as e:
            # No bloquear si falla el cacheo
            self.logger.debug(f"No se pudo aplicar cache a rutas: {e}")
        
        @self.app.route('/api/refresh')
        def api_refresh():
            """API endpoint para refrescar datos."""
            try:
                # Reinicializar proveedor de datos
                self.data_provider = DashboardDataProvider()
                return jsonify({
                    'success': True,
                    'message': 'Datos refrescados exitosamente',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Error refrescando datos: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'success': False,
                'error': 'Endpoint no encontrado'
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                'success': False,
                'error': 'Error interno del servidor'
            }), 500
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Ejecuta la aplicación."""
        try:
            self.logger.info(f"Iniciando dashboard web en http://{host}:{port}")
            self.app.run(host=host, port=port, debug=debug, use_reloader=False)
        except Exception as e:
            self.logger.error(f"Error ejecutando dashboard: {e}")
            raise


# Instancia global de la aplicación
_dashboard_app: Optional[DashboardApp] = None


def get_dashboard_app() -> DashboardApp:
    """Obtiene instancia global de la aplicación dashboard."""
    global _dashboard_app
    if _dashboard_app is None:
        _dashboard_app = DashboardApp()
    return _dashboard_app


def run_dashboard(host='127.0.0.1', port=5000, debug=False):
    """
    Función de conveniencia para ejecutar el dashboard.
    
    Args:
        host: Host para bind del servidor
        port: Puerto para el servidor
        debug: Modo debug de Flask
    """
    app = get_dashboard_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_dashboard(debug=True)
