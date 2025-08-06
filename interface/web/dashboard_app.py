"""
Dashboard Web Interactivo

Interfaz web con gráficos en tiempo real para visualizar gastos,
métricas y análisis usando Flask y Chart.js.
"""

import os
import json
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


logger = get_logger(__name__)


class DashboardDataProvider:
    """Proveedor de datos para el dashboard."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logger
        
        # Inicializar conexión a datos
        self.storage = self._initialize_storage()
        self.metrics_collector = get_metrics_collector()
    
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
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas resumidas."""
        try:
            if not self.storage:
                return self._get_empty_stats()
            
            # Obtener gastos del último mes
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            recent_gastos = self.storage.obtener_gastos_por_fecha(start_date, end_date)
            all_gastos = self.storage.obtener_todos_gastos()
            
            # Calcular estadísticas
            total_gastos = len(all_gastos)
            total_monto = sum(float(g.monto) for g in all_gastos)
            
            gastos_mes = len(recent_gastos)
            monto_mes = sum(float(g.monto) for g in recent_gastos)
            
            promedio_diario = monto_mes / 30 if monto_mes > 0 else 0
            
            # Categoría más común
            if all_gastos:
                categorias = [g.categoria for g in all_gastos]
                categoria_mas_comun = max(set(categorias), key=categorias.count)
            else:
                categoria_mas_comun = "N/A"
            
            # Gasto más alto
            gasto_mas_alto = max((float(g.monto) for g in all_gastos), default=0)
            
            return {
                'total_gastos': total_gastos,
                'total_monto': total_monto,
                'gastos_este_mes': gastos_mes,
                'monto_este_mes': monto_mes,
                'promedio_diario': promedio_diario,
                'categoria_mas_comun': categoria_mas_comun,
                'gasto_mas_alto': gasto_mas_alto,
                'ultima_actualizacion': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return self._get_empty_stats()
    
    def get_gastos_por_categoria(self, days: int = 30) -> Dict[str, Any]:
        """Obtiene gastos agrupados por categoría."""
        try:
            if not self.storage:
                return {'categories': [], 'amounts': []}
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            gastos = self.storage.obtener_gastos_por_fecha(start_date, end_date)
            
            # Agrupar por categoría
            categoria_montos = {}
            for gasto in gastos:
                categoria = gasto.categoria
                monto = float(gasto.monto)
                categoria_montos[categoria] = categoria_montos.get(categoria, 0) + monto
            
            # Ordenar por monto (mayor a menor)
            sorted_categories = sorted(categoria_montos.items(), key=lambda x: x[1], reverse=True)
            
            categories = [item[0] for item in sorted_categories]
            amounts = [item[1] for item in sorted_categories]
            
            return {
                'categories': categories,
                'amounts': amounts,
                'total_categories': len(categories),
                'period_days': days
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo gastos por categoría: {e}")
            return {'categories': [], 'amounts': []}
    
    def get_gastos_temporales(self, days: int = 30) -> Dict[str, Any]:
        """Obtiene gastos en serie temporal."""
        try:
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
            
            return {
                'dates': dates,
                'amounts': amounts,
                'period_days': days,
                'total_days': len(dates)
            }
            
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
            health = get_system_health()
            operation_stats = self.metrics_collector.get_operation_stats()
            
            return {
                'health': health,
                'operations': operation_stats,
                'timestamp': datetime.now().isoformat()
            }
            
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
        
        self.data_provider = DashboardDataProvider()
        self.logger = logger
        
        # Configurar rutas
        self.setup_routes()
    
    def setup_routes(self):
        """Configura las rutas de la aplicación."""
        
        @self.app.route('/')
        def dashboard():
            """Página principal del dashboard."""
            return render_template('dashboard.html', 
                                 title="Bot Gastos Dashboard",
                                 version="1.0.0")
        
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