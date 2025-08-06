"""
Interface Web Module

Dashboard web interactivo para visualización de gastos y métricas.
"""

from .dashboard_app import DashboardApp, get_dashboard_app, run_dashboard

__all__ = ['DashboardApp', 'get_dashboard_app', 'run_dashboard']