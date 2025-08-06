"""
Ejemplo de uso del Dashboard Web

Este script demuestra cómo usar el dashboard web para visualizar
datos de gastos en tiempo real.
"""

import sys
import time
import threading
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from interface.web import get_dashboard_app
from shared.logger import get_logger


def main():
    """Función principal de ejemplo."""
    logger = get_logger(__name__)
    
    print("🌐 Ejemplo de Dashboard Web")
    print("=" * 50)
    
    try:
        # Verificar dependencias
        try:
            import flask
            import flask_cors
        except ImportError as e:
            print(f"❌ Error: Dependencia faltante: {e}")
            print("\n📦 Instala las dependencias con:")
            print("   pip install flask flask-cors")
            print("\n🚀 O instala todas las dependencias:")
            print("   pip install -r requirements.txt")
            return
        
        print("✅ Dependencias verificadas")
        
        # Crear aplicación dashboard
        print("🔧 Inicializando dashboard...")
        dashboard_app = get_dashboard_app()
        
        print("📊 Verificando datos disponibles...")
        data_provider = dashboard_app.data_provider
        
        # Verificar estadísticas
        stats = data_provider.get_summary_stats()
        print(f"   📈 Total gastos: {stats['total_gastos']}")
        print(f"   💰 Monto total: ${stats['total_monto']:.2f}")
        print(f"   📅 Gastos este mes: {stats['gastos_este_mes']}")
        
        # Verificar datos de categorías
        categories = data_provider.get_gastos_por_categoria()
        print(f"   🏷️  Categorías detectadas: {len(categories['categories'])}")
        
        # Verificar gastos recientes
        recent = data_provider.get_gastos_recientes()
        print(f"   ⏰ Gastos recientes: {len(recent)}")
        
        # Verificar métricas del sistema
        metrics = data_provider.get_system_metrics()
        health_status = metrics['health'].get('status', 'unknown')
        print(f"   💚 Estado del sistema: {health_status}")
        
        print("\n" + "=" * 50)
        print("🚀 DASHBOARD LISTO PARA USAR")
        print("=" * 50)
        print("\n📋 URLs disponibles:")
        print("   🏠 Dashboard principal: http://127.0.0.1:5000/")
        print("   📊 API estadísticas:    http://127.0.0.1:5000/api/summary")
        print("   🏷️  API categorías:      http://127.0.0.1:5000/api/categories")
        print("   📈 API timeline:        http://127.0.0.1:5000/api/timeline")
        print("   ⏰ API gastos recientes: http://127.0.0.1:5000/api/recent")
        print("   💚 API métricas:        http://127.0.0.1:5000/api/metrics")
        
        print("\n🎨 Funcionalidades del dashboard:")
        print("   • Gráfico de línea de gastos en el tiempo")
        print("   • Gráfico de dona de gastos por categoría")
        print("   • Estadísticas resumidas en tiempo real")
        print("   • Lista de gastos más recientes")
        print("   • Métricas del sistema y estado de salud")
        print("   • Actualización automática cada 30 segundos")
        print("   • Filtros por período (semana, mes, 3 meses)")
        
        print("\n⚡ Para iniciar el dashboard ejecuta:")
        print("   python run_dashboard.py")
        print("\n   O con opciones:")
        print("   python run_dashboard.py --debug --port 8000")
        print("   python run_dashboard.py --public  # Para acceso externo")
        
        print("\n💡 Consejos:")
        print("   • Usa --debug para desarrollo")
        print("   • Usa --public solo en redes seguras")
        print("   • El dashboard se actualiza automáticamente")
        print("   • Compatible con móviles y tablets")
        
        # Opción para ejecutar inmediatamente
        response = input("\n❓ ¿Quieres iniciar el dashboard ahora? (y/N): ")
        if response.lower() == 'y':
            print("\n🚀 Iniciando dashboard en modo demo...")
            print("   (Presiona Ctrl+C para detener)")
            
            try:
                dashboard_app.run(debug=True, port=5000)
            except KeyboardInterrupt:
                print("\n👋 Dashboard detenido")
        
    except Exception as e:
        logger.error(f"Error en ejemplo dashboard: {e}")
        print(f"❌ Error: {e}")


def demo_data_generation():
    """Genera datos de demostración en background."""
    # Esta función podría generar datos de prueba
    # para mostrar el dashboard con información
    pass


if __name__ == "__main__":
    main()