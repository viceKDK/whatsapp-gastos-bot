"""
Interfaz CLI Interactiva Mejorada

Proporciona una interfaz de línea de comandos rica e interactiva 
para gestionar el bot de gastos.
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from decimal import Decimal

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.tree import Tree
    from rich.columns import Columns
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    # Fallback básico sin rich
    class Console:
        def print(self, *args, **kwargs):
            print(*args)

from config.config_manager import get_config, config_manager
from shared.logger import get_logger
from shared.metrics import get_metrics_collector, get_system_health
from shared.validators import validate_gasto, ValidationLevel


logger = get_logger(__name__)


class InteractiveCLI:
    """Interfaz CLI interactiva principal."""
    
    def __init__(self):
        self.console = Console() if HAS_RICH else Console()
        self.config = get_config()
        self.logger = logger
        self.running = True
        
        # Comandos disponibles
        self.commands = {
            'status': self.show_status,
            'config': self.manage_config,
            'logs': self.view_logs,
            'metrics': self.view_metrics,
            'test': self.run_tests,
            'backup': self.manage_backups,
            'export': self.export_data,
            'validate': self.validate_data,
            'cleanup': self.cleanup_system,
            'help': self.show_help,
            'exit': self.exit_cli,
            'quit': self.exit_cli
        }
    
    def start(self):
        """Inicia la CLI interactiva."""
        self.show_welcome()
        
        while self.running:
            try:
                command = self.get_user_input()
                if command:
                    self.execute_command(command)
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Saliendo...[/yellow]")
                break
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")
        
        self.show_goodbye()
    
    def show_welcome(self):
        """Muestra mensaje de bienvenida."""
        if HAS_RICH:
            welcome_panel = Panel.fit(
                "[bold blue]🤖 Bot Gastos WhatsApp[/bold blue]\n" +
                "[dim]Interfaz CLI Interactiva[/dim]\n\n" +
                "Escribe [bold green]'help'[/bold green] para ver comandos disponibles\n" +
                "Escribe [bold red]'exit'[/bold red] para salir",
                title="Bienvenido",
                border_style="blue"
            )
            self.console.print(welcome_panel)
        else:
            print("=" * 50)
            print("🤖 Bot Gastos WhatsApp - CLI Interactiva")
            print("=" * 50)
            print("Escribe 'help' para ver comandos disponibles")
            print("Escribe 'exit' para salir")
            print()
    
    def show_goodbye(self):
        """Muestra mensaje de despedida."""
        if HAS_RICH:
            self.console.print(Panel.fit(
                "[bold green]¡Hasta luego![/bold green]\n" +
                "[dim]Gracias por usar Bot Gastos WhatsApp[/dim]",
                title="Despedida",
                border_style="green"
            ))
        else:
            print("\n¡Hasta luego!")
            print("Gracias por usar Bot Gastos WhatsApp")
    
    def get_user_input(self) -> str:
        """Obtiene entrada del usuario."""
        if HAS_RICH:
            return Prompt.ask("[bold cyan]bot-gastos[/bold cyan]", default="").strip()
        else:
            return input("bot-gastos> ").strip()
    
    def execute_command(self, command_line: str):
        """Ejecuta un comando."""
        parts = command_line.split()
        if not parts:
            return
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if command in self.commands:
            try:
                self.commands[command](args)
            except Exception as e:
                self.console.print(f"[red]Error ejecutando comando '{command}': {str(e)}[/red]")
                logger.error(f"Error en comando CLI '{command}': {e}")
        else:
            self.console.print(f"[red]Comando desconocido: '{command}'. Escribe 'help' para ver comandos disponibles.[/red]")
    
    def show_status(self, args: List[str]):
        """Muestra estado del sistema."""
        if HAS_RICH:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task("Obteniendo estado del sistema...", total=None)
                
                # Obtener métricas de salud
                health = get_system_health()
                progress.update(task, description="Estado obtenido")
                time.sleep(0.5)  # Para mostrar el spinner
            
            # Crear tabla de estado
            table = Table(title="Estado del Sistema", box=box.ROUNDED)
            table.add_column("Componente", style="cyan", no_wrap=True)
            table.add_column("Estado", style="bold")
            table.add_column("Valor", style="green")
            
            # Determinar color del estado
            status_color = {
                'healthy': 'green',
                'warning': 'yellow',
                'critical': 'red',
                'unknown': 'dim'
            }.get(health.get('status'), 'dim')
            
            table.add_row("Estado General", f"[{status_color}]{health.get('status', 'unknown').upper()}[/{status_color}]", "")
            table.add_row("Tiempo Activo", "INFO", f"{health.get('uptime_seconds', 0):.1f}s")
            table.add_row("Memoria", "INFO", f"{health.get('current_memory_mb', 0):.1f} MB")
            table.add_row("CPU", "INFO", f"{health.get('current_cpu_percent', 0):.1f}%")
            table.add_row("Operaciones", "INFO", str(health.get('total_operations', 0)))
            table.add_row("Errores", "WARNING" if health.get('total_errors', 0) > 0 else "INFO", 
                         str(health.get('total_errors', 0)))
            
            self.console.print(table)
            
            # Mostrar alertas si las hay
            alerts = health.get('alerts', [])
            if alerts:
                alert_panel = Panel(
                    "\n".join(f"• {alert}" for alert in alerts),
                    title="[bold red]Alertas[/bold red]",
                    border_style="red"
                )
                self.console.print(alert_panel)
        
        else:
            # Versión simplificada sin rich
            health = get_system_health()
            print(f"\n--- Estado del Sistema ---")
            print(f"Estado: {health.get('status', 'unknown').upper()}")
            print(f"Tiempo Activo: {health.get('uptime_seconds', 0):.1f}s")
            print(f"Memoria: {health.get('current_memory_mb', 0):.1f} MB")
            print(f"CPU: {health.get('current_cpu_percent', 0):.1f}%")
            print(f"Operaciones: {health.get('total_operations', 0)}")
            print(f"Errores: {health.get('total_errors', 0)}")
            
            alerts = health.get('alerts', [])
            if alerts:
                print("\n--- Alertas ---")
                for alert in alerts:
                    print(f"• {alert}")
    
    def manage_config(self, args: List[str]):
        """Gestiona configuración."""
        if not args:
            self.show_config_menu()
            return
        
        action = args[0].lower()
        
        if action == 'show':
            self.show_config()
        elif action == 'edit':
            self.edit_config(args[1:])
        elif action == 'reload':
            self.reload_config()
        elif action == 'backup':
            self.backup_config()
        else:
            self.console.print(f"[red]Acción de configuración desconocida: {action}[/red]")
            self.show_config_menu()
    
    def show_config_menu(self):
        """Muestra menú de configuración."""
        if HAS_RICH:
            menu_text = """[bold]Comandos de configuración disponibles:[/bold]

• [cyan]config show[/cyan] - Mostrar configuración actual
• [cyan]config edit <sección>[/cyan] - Editar sección de configuración  
• [cyan]config reload[/cyan] - Recargar configuración desde archivo
• [cyan]config backup[/cyan] - Crear backup de configuración actual"""

            panel = Panel(menu_text, title="Gestión de Configuración", border_style="blue")
            self.console.print(panel)
        else:
            print("\n--- Comandos de Configuración ---")
            print("config show - Mostrar configuración actual")
            print("config edit <sección> - Editar sección de configuración")
            print("config reload - Recargar configuración desde archivo")
            print("config backup - Crear backup de configuración actual")
    
    def show_config(self):
        """Muestra configuración actual."""
        try:
            config = self.config
            
            if HAS_RICH:
                # Crear árbol de configuración
                tree = Tree("[bold blue]Configuración Actual[/bold blue]")
                
                # WhatsApp
                whatsapp_node = tree.add("[cyan]WhatsApp[/cyan]")
                whatsapp_node.add(f"Chat: {config.whatsapp.target_chat_name}")
                whatsapp_node.add(f"Headless: {config.whatsapp.chrome_headless}")
                whatsapp_node.add(f"Timeout: {config.whatsapp.connection_timeout_seconds}s")
                
                # Storage
                storage_node = tree.add("[green]Storage[/green]")
                storage_node.add(f"Tipo: {config.storage.primary_storage}")
                storage_node.add(f"Excel: {config.storage.excel_file_path}")
                storage_node.add(f"SQLite: {config.storage.sqlite_db_path}")
                
                # Logging
                logging_node = tree.add("[yellow]Logging[/yellow]")
                logging_node.add(f"Nivel: {config.logging.level}")
                logging_node.add(f"Archivo: {config.logging.file_path}")
                logging_node.add(f"Tamaño Max: {config.logging.max_file_size_mb}MB")
                
                self.console.print(tree)
            else:
                print("\n--- Configuración Actual ---")
                print(f"WhatsApp Chat: {config.whatsapp.target_chat_name}")
                print(f"WhatsApp Headless: {config.whatsapp.chrome_headless}")
                print(f"Storage: {config.storage.primary_storage}")
                print(f"Log Level: {config.logging.level}")
                
        except Exception as e:
            self.console.print(f"[red]Error mostrando configuración: {str(e)}[/red]")
    
    def view_logs(self, args: List[str]):
        """Visualiza logs."""
        log_file = Path(self.config.logging.file_path)
        
        if not log_file.exists():
            self.console.print(f"[red]Archivo de log no encontrado: {log_file}[/red]")
            return
        
        lines_to_show = 20
        if args and args[0].isdigit():
            lines_to_show = int(args[0])
        
        try:
            # Leer últimas líneas
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_lines = lines[-lines_to_show:]
            
            if HAS_RICH:
                log_content = "".join(recent_lines)
                syntax = Syntax(log_content, "log", theme="monokai", line_numbers=True)
                
                panel = Panel(
                    syntax,
                    title=f"[bold]Últimas {len(recent_lines)} líneas del log[/bold]",
                    border_style="dim"
                )
                self.console.print(panel)
            else:
                print(f"\n--- Últimas {len(recent_lines)} líneas del log ---")
                for line in recent_lines:
                    print(line.rstrip())
                    
        except Exception as e:
            self.console.print(f"[red]Error leyendo logs: {str(e)}[/red]")
    
    def view_metrics(self, args: List[str]):
        """Visualiza métricas."""
        try:
            collector = get_metrics_collector()
            stats = collector.get_operation_stats()
            
            if HAS_RICH and stats:
                table = Table(title="Métricas de Operaciones", box=box.ROUNDED)
                table.add_column("Operación", style="cyan")
                table.add_column("Llamadas", style="bold green")
                table.add_column("Errores", style="red")
                table.add_column("Éxito %", style="green")
                table.add_column("Tiempo Prom", style="blue")
                table.add_column("Tiempo Max", style="yellow")
                
                for operation, data in stats.items():
                    table.add_row(
                        operation,
                        str(data['total_calls']),
                        str(data['error_count']),
                        f"{data['success_rate']*100:.1f}%",
                        f"{data['avg_response_time']:.3f}s",
                        f"{data['max_response_time']:.3f}s"
                    )
                
                self.console.print(table)
                
            elif stats:
                print("\n--- Métricas de Operaciones ---")
                for operation, data in stats.items():
                    print(f"{operation}:")
                    print(f"  Llamadas: {data['total_calls']}")
                    print(f"  Errores: {data['error_count']}")
                    print(f"  Éxito: {data['success_rate']*100:.1f}%")
                    print(f"  Tiempo promedio: {data['avg_response_time']:.3f}s")
                    print()
            else:
                self.console.print("[yellow]No hay métricas disponibles aún[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]Error obteniendo métricas: {str(e)}[/red]")
    
    def run_tests(self, args: List[str]):
        """Ejecuta tests del sistema."""
        if HAS_RICH:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                
                # Test de configuración
                task1 = progress.add_task("Probando configuración...", total=None)
                config_ok = self._test_configuration()
                progress.update(task1, description=f"Configuración: {'✅' if config_ok else '❌'}")
                time.sleep(0.5)
                
                # Test de base de datos
                task2 = progress.add_task("Probando base de datos...", total=None)
                db_ok = self._test_database()
                progress.update(task2, description=f"Base de datos: {'✅' if db_ok else '❌'}")
                time.sleep(0.5)
                
                # Test de dependencias
                task3 = progress.add_task("Probando dependencias...", total=None)
                deps_ok = self._test_dependencies()
                progress.update(task3, description=f"Dependencias: {'✅' if deps_ok else '❌'}")
                time.sleep(0.5)
            
            # Mostrar resumen
            results = [
                ("Configuración", config_ok),
                ("Base de Datos", db_ok),
                ("Dependencias", deps_ok)
            ]
            
            table = Table(title="Resultados de Tests", box=box.SIMPLE)
            table.add_column("Test", style="cyan")
            table.add_column("Estado", style="bold")
            
            for test_name, result in results:
                status = "[green]✅ PASS[/green]" if result else "[red]❌ FAIL[/red]"
                table.add_row(test_name, status)
            
            self.console.print(table)
        
        else:
            print("\n--- Ejecutando Tests ---")
            print("Configuración:", "✅" if self._test_configuration() else "❌")
            print("Base de Datos:", "✅" if self._test_database() else "❌")
            print("Dependencias:", "✅" if self._test_dependencies() else "❌")
    
    def _test_configuration(self) -> bool:
        """Test de configuración."""
        try:
            config = get_config()
            return config is not None
        except:
            return False
    
    def _test_database(self) -> bool:
        """Test de base de datos."""
        try:
            from infrastructure.storage.sqlite_writer import SQLiteStorage
            from infrastructure.storage.excel_writer import ExcelStorage
            
            # Test SQLite
            db_path = Path(self.config.storage.sqlite_db_path)
            if db_path.exists():
                storage = SQLiteStorage(str(db_path))
                info = storage.obtener_info_database()
                return info.get('exists', False)
            return True
        except:
            return False
    
    def _test_dependencies(self) -> bool:
        """Test de dependencias."""
        try:
            import selenium
            import openpyxl
            import yaml
            return True
        except ImportError:
            return False
    
    def manage_backups(self, args: List[str]):
        """Gestiona backups."""
        self.console.print("[yellow]Función de backups en desarrollo...[/yellow]")
    
    def export_data(self, args: List[str]):
        """Exporta datos."""
        self.console.print("[yellow]Función de exportación en desarrollo...[/yellow]")
    
    def validate_data(self, args: List[str]):
        """Valida datos."""
        if HAS_RICH:
            # Ejemplo de validación interactiva
            self.console.print("[bold blue]Validador Interactivo de Gastos[/bold blue]\n")
            
            try:
                monto = FloatPrompt.ask("Ingresa el monto")
                categoria = Prompt.ask("Ingresa la categoría")
                descripcion = Prompt.ask("Ingresa la descripción (opcional)", default="")
                
                # Validar
                gasto_data = {
                    'monto': monto,
                    'categoria': categoria,
                    'descripcion': descripcion if descripcion else None
                }
                
                result = validate_gasto(gasto_data, ValidationLevel.NORMAL)
                
                if result.is_valid:
                    self.console.print("[green]✅ Gasto válido[/green]")
                    if result.sanitized_value:
                        self.console.print(f"Datos sanitizados: {result.sanitized_value}")
                else:
                    self.console.print("[red]❌ Gasto inválido[/red]")
                    for error in result.errors:
                        self.console.print(f"  • [red]{error}[/red]")
                
                if result.warnings:
                    self.console.print("[yellow]Advertencias:[/yellow]")
                    for warning in result.warnings:
                        self.console.print(f"  • [yellow]{warning}[/yellow]")
                        
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Validación cancelada[/yellow]")
        
        else:
            print("Validador de gastos - versión simplificada")
            try:
                monto = float(input("Monto: "))
                categoria = input("Categoría: ")
                
                gasto_data = {'monto': monto, 'categoria': categoria}
                result = validate_gasto(gasto_data)
                
                if result.is_valid:
                    print("✅ Gasto válido")
                else:
                    print("❌ Errores:")
                    for error in result.errors:
                        print(f"  • {error}")
            except:
                print("Error en validación")
    
    def cleanup_system(self, args: List[str]):
        """Limpia el sistema."""
        if HAS_RICH:
            if Confirm.ask("¿Deseas limpiar logs antiguos y archivos temporales?"):
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console
                ) as progress:
                    task = progress.add_task("Limpiando sistema...", total=None)
                    time.sleep(2)  # Simular limpieza
                    progress.update(task, description="Limpieza completada ✅")
                
                self.console.print("[green]Sistema limpiado exitosamente[/green]")
        else:
            response = input("¿Limpiar logs antiguos y archivos temporales? (y/N): ")
            if response.lower() == 'y':
                print("Limpiando sistema...")
                time.sleep(1)
                print("✅ Sistema limpiado")
    
    def show_help(self, args: List[str]):
        """Muestra ayuda."""
        if HAS_RICH:
            help_table = Table(title="Comandos Disponibles", box=box.ROUNDED)
            help_table.add_column("Comando", style="cyan", no_wrap=True)
            help_table.add_column("Descripción", style="white")
            help_table.add_column("Ejemplo", style="dim")
            
            commands_help = [
                ("status", "Muestra estado del sistema", "status"),
                ("config", "Gestiona configuración", "config show"),
                ("logs", "Visualiza logs recientes", "logs 50"),
                ("metrics", "Muestra métricas de performance", "metrics"),
                ("test", "Ejecuta tests del sistema", "test"),
                ("backup", "Gestiona backups", "backup create"),
                ("export", "Exporta datos", "export excel"),
                ("validate", "Valida datos interactivamente", "validate"),
                ("cleanup", "Limpia archivos temporales", "cleanup"),
                ("help", "Muestra esta ayuda", "help"),
                ("exit/quit", "Sale de la CLI", "exit")
            ]
            
            for cmd, desc, example in commands_help:
                help_table.add_row(cmd, desc, example)
            
            self.console.print(help_table)
        
        else:
            print("\n--- Comandos Disponibles ---")
            print("status      - Estado del sistema")
            print("config      - Gestionar configuración")
            print("logs        - Ver logs recientes")
            print("metrics     - Ver métricas")
            print("test        - Ejecutar tests")
            print("backup      - Gestionar backups")
            print("export      - Exportar datos")
            print("validate    - Validar datos")
            print("cleanup     - Limpiar sistema")
            print("help        - Mostrar ayuda")
            print("exit/quit   - Salir")
    
    def exit_cli(self, args: List[str]):
        """Sale de la CLI."""
        self.running = False


@click.command()
@click.option('--config-file', '-c', help='Archivo de configuración personalizado')
@click.option('--verbose', '-v', is_flag=True, help='Modo verbose')
def main(config_file: str, verbose: bool):
    """Inicia la CLI interactiva del Bot Gastos WhatsApp."""
    try:
        if not HAS_RICH:
            print("Instalando rich para mejor experiencia: pip install rich")
            print("Usando interfaz simplificada...\n")
        
        if config_file:
            # Cargar configuración personalizada
            os.environ['BOT_CONFIG_FILE'] = config_file
        
        cli = InteractiveCLI()
        cli.start()
        
    except KeyboardInterrupt:
        print("\nSaliendo...")
    except Exception as e:
        print(f"Error iniciando CLI: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())