#!/usr/bin/env python3
"""
Script de Instalación Automatizada - Bot Gastos WhatsApp

Instala y configura automáticamente todas las dependencias y 
configuraciones necesarias para ejecutar el bot.
"""

import os
import sys
import subprocess
import platform
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import tempfile
import shutil


class Colors:
    """Códigos de colores para terminal."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class BotInstaller:
    """Instalador automatizado del Bot de Gastos WhatsApp."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.python_version = sys.version_info
        self.project_root = Path(__file__).parent.parent
        self.requirements_file = self.project_root / 'requirements.txt'
        self.config_dir = self.project_root / 'config'
        self.data_dir = self.project_root / 'data'
        self.logs_dir = self.project_root / 'logs'
        self.errors = []
        self.warnings = []
        
    def print_header(self):
        """Imprime header de instalación."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}")
        print("🤖 BOT GASTOS WHATSAPP - INSTALADOR AUTOMATIZADO")
        print(f"{'=' * 60}{Colors.END}\n")
        
    def print_step(self, step: str, description: str = ""):
        """Imprime paso de instalación."""
        print(f"{Colors.BOLD}{Colors.BLUE}[PASO]{Colors.END} {step}")
        if description:
            print(f"    {description}")
        print()
        
    def print_success(self, message: str):
        """Imprime mensaje de éxito."""
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
        
    def print_warning(self, message: str):
        """Imprime advertencia."""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
        self.warnings.append(message)
        
    def print_error(self, message: str):
        """Imprime error."""
        print(f"{Colors.RED}❌ {message}{Colors.END}")
        self.errors.append(message)
        
    def check_system_requirements(self) -> bool:
        """Verifica requisitos del sistema."""
        self.print_step("1/10", "Verificando requisitos del sistema...")
        
        # Verificar Python version
        if self.python_version < (3, 8):
            self.print_error(f"Python 3.8+ requerido, encontrado: {sys.version}")
            return False
        
        self.print_success(f"Python {sys.version.split()[0]} ✓")
        
        # Verificar pip
        try:
            subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                          capture_output=True, check=True)
            self.print_success("pip disponible ✓")
        except subprocess.CalledProcessError:
            self.print_error("pip no está disponible")
            return False
        
        # Verificar sistema operativo compatible
        supported_os = ['windows', 'linux', 'darwin']
        if self.system not in supported_os:
            self.print_warning(f"SO no oficialmente soportado: {self.system}")
        else:
            self.print_success(f"SO compatible: {platform.system()} ✓")
        
        return True
    
    def install_system_dependencies(self) -> bool:
        """Instala dependencias del sistema."""
        self.print_step("2/10", "Instalando dependencias del sistema...")
        
        if self.system == 'linux':
            return self._install_linux_dependencies()
        elif self.system == 'windows':
            return self._install_windows_dependencies()
        elif self.system == 'darwin':
            return self._install_macos_dependencies()
        else:
            self.print_warning("Dependencias del sistema no configuradas para este SO")
            return True
    
    def _install_linux_dependencies(self) -> bool:
        """Instala dependencias en Linux."""
        try:
            # Detectar distribución
            if shutil.which('apt'):
                # Ubuntu/Debian
                deps = [
                    'python3-dev',
                    'python3-pip',
                    'tesseract-ocr',
                    'tesseract-ocr-spa',
                    'tesseract-ocr-eng',
                    'libtesseract-dev',
                    'chromium-browser',
                    'chromium-chromedriver'
                ]
                
                print("    Instalando dependencias APT...")
                cmd = ['sudo', 'apt', 'update']
                subprocess.run(cmd, check=True)
                
                cmd = ['sudo', 'apt', 'install', '-y'] + deps
                subprocess.run(cmd, check=True)
                
            elif shutil.which('yum') or shutil.which('dnf'):
                # Red Hat/Fedora
                pkg_manager = 'dnf' if shutil.which('dnf') else 'yum'
                deps = [
                    'python3-devel',
                    'python3-pip',
                    'tesseract',
                    'tesseract-langpack-spa',
                    'tesseract-langpack-eng',
                    'chromium',
                    'chromedriver'
                ]
                
                print(f"    Instalando dependencias {pkg_manager.upper()}...")
                cmd = ['sudo', pkg_manager, 'install', '-y'] + deps
                subprocess.run(cmd, check=True)
            
            self.print_success("Dependencias del sistema instaladas ✓")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Error instalando dependencias del sistema: {e}")
            return False
        except Exception as e:
            self.print_warning(f"Error instalando dependencias del sistema: {e}")
            return True  # Continue anyway
    
    def _install_windows_dependencies(self) -> bool:
        """Instala dependencias en Windows."""
        self.print_warning("Instalación manual requerida en Windows:")
        print("    1. Instalar Google Chrome")
        print("    2. Descargar ChromeDriver y agregarlo al PATH")
        print("    3. Instalar Tesseract OCR desde: https://github.com/UB-Mannheim/tesseract/wiki")
        print("    4. Agregar Tesseract al PATH del sistema")
        
        # Verificar si están disponibles
        chrome_available = shutil.which('chrome') or shutil.which('google-chrome')
        if chrome_available:
            self.print_success("Google Chrome detectado ✓")
        else:
            self.print_warning("Google Chrome no detectado")
        
        tesseract_available = shutil.which('tesseract')
        if tesseract_available:
            self.print_success("Tesseract OCR detectado ✓")
        else:
            self.print_warning("Tesseract OCR no detectado")
        
        return True
    
    def _install_macos_dependencies(self) -> bool:
        """Instala dependencias en macOS."""
        try:
            if shutil.which('brew'):
                deps = [
                    'tesseract',
                    'tesseract-lang',
                    'chromium',
                    'chromedriver'
                ]
                
                print("    Instalando dependencias Homebrew...")
                for dep in deps:
                    cmd = ['brew', 'install', dep]
                    try:
                        subprocess.run(cmd, check=True, capture_output=True)
                        self.print_success(f"{dep} instalado ✓")
                    except subprocess.CalledProcessError:
                        self.print_warning(f"Error instalando {dep}")
                
                return True
            else:
                self.print_warning("Homebrew no encontrado. Instalar desde: https://brew.sh/")
                return True
                
        except Exception as e:
            self.print_warning(f"Error instalando dependencias de macOS: {e}")
            return True
    
    def create_virtual_environment(self) -> bool:
        """Crea entorno virtual."""
        self.print_step("3/10", "Creando entorno virtual...")
        
        venv_path = self.project_root / 'venv'
        
        try:
            if venv_path.exists():
                self.print_warning("Entorno virtual ya existe, eliminando...")
                shutil.rmtree(venv_path)
            
            # Crear venv
            subprocess.run([
                sys.executable, '-m', 'venv', str(venv_path)
            ], check=True)
            
            self.print_success(f"Entorno virtual creado: {venv_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Error creando entorno virtual: {e}")
            return False
    
    def install_python_dependencies(self) -> bool:
        """Instala dependencias Python."""
        self.print_step("4/10", "Instalando dependencias Python...")
        
        # Determinar ejecutable Python del venv
        if self.system == 'windows':
            python_exe = self.project_root / 'venv' / 'Scripts' / 'python.exe'
            pip_exe = self.project_root / 'venv' / 'Scripts' / 'pip.exe'
        else:
            python_exe = self.project_root / 'venv' / 'bin' / 'python'
            pip_exe = self.project_root / 'venv' / 'bin' / 'pip'
        
        try:
            # Actualizar pip
            subprocess.run([
                str(python_exe), '-m', 'pip', 'install', '--upgrade', 'pip'
            ], check=True)
            
            # Instalar desde requirements.txt
            if self.requirements_file.exists():
                subprocess.run([
                    str(pip_exe), 'install', '-r', str(self.requirements_file)
                ], check=True)
            else:
                # Dependencias básicas si no hay requirements.txt
                basic_deps = [
                    'selenium>=4.15.0',
                    'openpyxl>=3.1.0',
                    'pytesseract>=0.3.10',
                    'Pillow>=10.0.0',
                    'pyyaml>=6.0',
                    'python-dotenv>=1.0.0',
                    'click>=8.1.0',
                    'rich>=13.0.0',
                    'psutil>=5.9.0'
                ]
                
                for dep in basic_deps:
                    subprocess.run([
                        str(pip_exe), 'install', dep
                    ], check=True)
            
            self.print_success("Dependencias Python instaladas ✓")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Error instalando dependencias Python: {e}")
            return False
    
    def create_directory_structure(self) -> bool:
        """Crea estructura de directorios."""
        self.print_step("5/10", "Creando estructura de directorios...")
        
        directories = [
            self.config_dir,
            self.data_dir,
            self.logs_dir,
            self.project_root / 'exports',
            self.project_root / 'backups',
            self.project_root / 'temp'
        ]
        
        try:
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                self.print_success(f"Directorio creado: {directory.name}")
            
            return True
            
        except Exception as e:
            self.print_error(f"Error creando directorios: {e}")
            return False
    
    def create_configuration_files(self) -> bool:
        """Crea archivos de configuración."""
        self.print_step("6/10", "Creando archivos de configuración...")
        
        try:
            # Crear config.yaml por defecto
            config_file = self.config_dir / 'config.yaml'
            if not config_file.exists():
                default_config = {
                    '_metadata': {
                        'version': '1.0',
                        'created_by': 'Bot Gastos WhatsApp Installer',
                        'description': 'Configuración del sistema de gastos'
                    },
                    'whatsapp': {
                        'target_chat_name': 'Gastos Bot',
                        'chrome_headless': False,
                        'connection_timeout_seconds': 60,
                        'message_polling_interval_seconds': 5,
                        'chrome_profile_path': None,
                        'max_reconnection_attempts': 3
                    },
                    'storage': {
                        'primary_storage': 'excel',
                        'excel_file_path': 'data/gastos.xlsx',
                        'sqlite_db_path': 'data/gastos.db',
                        'backup_enabled': True,
                        'backup_interval_hours': 24,
                        'max_backup_files': 10
                    },
                    'logging': {
                        'level': 'INFO',
                        'file_path': 'logs/bot_gastos.log',
                        'max_file_size_mb': 10,
                        'backup_count': 5,
                        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        'console_enabled': True
                    },
                    'ocr': {
                        'enabled': True,
                        'language': 'spa+eng',
                        'confidence_threshold': 0.6,
                        'preprocessing_enabled': True,
                        'supported_formats': ['.jpg', '.jpeg', '.png', '.pdf']
                    },
                    'validation': {
                        'max_amount': 1000000.0,
                        'min_amount': 0.01,
                        'required_fields': ['monto', 'categoria'],
                        'custom_categories': [
                            'comida', 'transporte', 'servicios', 'entretenimiento',
                            'salud', 'educacion', 'hogar', 'ropa', 'otros'
                        ]
                    },
                    'export': {
                        'default_format': 'excel',
                        'output_directory': 'exports',
                        'include_charts': True,
                        'date_format': '%Y-%m-%d',
                        'supported_formats': ['excel', 'csv', 'pdf', 'json']
                    },
                    'performance': {
                        'metrics_enabled': True,
                        'metrics_file': 'logs/metrics.json',
                        'alert_thresholds': {
                            'memory_usage_mb': 500.0,
                            'processing_time_seconds': 10.0,
                            'error_rate_percentage': 5.0
                        }
                    }
                }
                
                import yaml
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(default_config, f, default_flow_style=False, 
                            allow_unicode=True, indent=2, sort_keys=False)
                
                self.print_success("config.yaml creado ✓")
            else:
                self.print_success("config.yaml ya existe ✓")
            
            # Crear .env template
            env_file = self.project_root / '.env.template'
            env_content = """# Configuración de Entorno - Bot Gastos WhatsApp
# Copia este archivo como .env y configura tus valores

# WhatsApp
WHATSAPP_CHAT_NAME="Gastos Bot"
WHATSAPP_HEADLESS=false

# Storage
STORAGE_TYPE=excel
DATA_PATH=data/

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bot_gastos.log

# OCR
OCR_LANGUAGE=spa+eng
TESSERACT_PATH=/usr/bin/tesseract

# Chrome
CHROME_DRIVER_PATH=/usr/bin/chromedriver
CHROME_BINARY_PATH=/usr/bin/google-chrome
"""
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            self.print_success(".env.template creado ✓")
            return True
            
        except Exception as e:
            self.print_error(f"Error creando archivos de configuración: {e}")
            return False
    
    def setup_database(self) -> bool:
        """Configura base de datos inicial."""
        self.print_step("7/10", "Configurando base de datos...")
        
        try:
            # Crear archivo Excel vacío
            excel_file = self.data_dir / 'gastos.xlsx'
            if not excel_file.exists():
                from openpyxl import Workbook
                wb = Workbook()
                ws = wb.active
                ws.title = "Gastos"
                
                # Headers
                headers = ['Fecha', 'Hora', 'Monto', 'Categoría', 'Descripción']
                for col, header in enumerate(headers, 1):
                    ws.cell(row=1, column=col, value=header)
                
                wb.save(str(excel_file))
                self.print_success("Archivo Excel creado ✓")
            else:
                self.print_success("Archivo Excel ya existe ✓")
            
            # Inicializar SQLite
            sqlite_file = self.data_dir / 'gastos.db'
            if not sqlite_file.exists():
                import sqlite3
                conn = sqlite3.connect(str(sqlite_file))
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE gastos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monto DECIMAL(10, 2) NOT NULL,
                        categoria VARCHAR(50) NOT NULL,
                        descripcion TEXT,
                        fecha DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('CREATE INDEX idx_gastos_fecha ON gastos(fecha)')
                cursor.execute('CREATE INDEX idx_gastos_categoria ON gastos(categoria)')
                
                conn.commit()
                conn.close()
                
                self.print_success("Base de datos SQLite creada ✓")
            else:
                self.print_success("Base de datos SQLite ya existe ✓")
            
            return True
            
        except Exception as e:
            self.print_error(f"Error configurando base de datos: {e}")
            return False
    
    def create_launcher_scripts(self) -> bool:
        """Crea scripts de lanzamiento."""
        self.print_step("8/10", "Creando scripts de lanzamiento...")
        
        try:
            # Script para Windows
            if self.system == 'windows':
                bat_content = f"""@echo off
cd /d "{self.project_root}"
call venv\\Scripts\\activate
python main.py %*
pause
"""
                bat_file = self.project_root / 'run_bot.bat'
                with open(bat_file, 'w', encoding='utf-8') as f:
                    f.write(bat_content)
                self.print_success("Script Windows creado: run_bot.bat")
            
            # Script para Unix
            else:
                sh_content = f"""#!/bin/bash
cd "{self.project_root}"
source venv/bin/activate
python main.py "$@"
"""
                sh_file = self.project_root / 'run_bot.sh'
                with open(sh_file, 'w', encoding='utf-8') as f:
                    f.write(sh_content)
                
                # Hacer ejecutable
                os.chmod(sh_file, 0o755)
                self.print_success("Script Unix creado: run_bot.sh")
            
            # Script de actualización
            update_content = f"""#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent
venv_python = project_root / "venv" / ("Scripts" if sys.platform == "win32" else "bin") / "python"

print("Actualizando Bot Gastos WhatsApp...")
subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"])
print("Actualización completada!")
"""
            
            update_file = self.project_root / 'update.py'
            with open(update_file, 'w', encoding='utf-8') as f:
                f.write(update_content)
            
            self.print_success("Script de actualización creado ✓")
            return True
            
        except Exception as e:
            self.print_error(f"Error creando scripts de lanzamiento: {e}")
            return False
    
    def run_initial_tests(self) -> bool:
        """Ejecuta tests iniciales."""
        self.print_step("9/10", "Ejecutando tests iniciales...")
        
        try:
            # Test de importaciones críticas
            test_imports = [
                ('selenium', 'Selenium WebDriver'),
                ('openpyxl', 'OpenPyXL'),
                ('pytesseract', 'PyTesseract'),
                ('yaml', 'PyYAML'),
                ('PIL', 'Pillow')
            ]
            
            for module, name in test_imports:
                try:
                    __import__(module)
                    self.print_success(f"{name} importado ✓")
                except ImportError:
                    self.print_warning(f"{name} no disponible")
            
            # Test de configuración
            try:
                sys.path.insert(0, str(self.project_root))
                from config.config_manager import get_config
                config = get_config()
                self.print_success("Configuración cargada ✓")
            except Exception as e:
                self.print_warning(f"Error cargando configuración: {e}")
            
            return True
            
        except Exception as e:
            self.print_error(f"Error en tests iniciales: {e}")
            return False
    
    def print_installation_summary(self):
        """Imprime resumen de instalación."""
        self.print_step("10/10", "Resumen de instalación")
        
        if not self.errors:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ INSTALACIÓN COMPLETADA EXITOSAMENTE{Colors.END}\n")
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ INSTALACIÓN COMPLETADA CON ERRORES{Colors.END}\n")
        
        # Mostrar errores si los hay
        if self.errors:
            print(f"{Colors.RED}{Colors.BOLD}ERRORES ENCONTRADOS:{Colors.END}")
            for error in self.errors:
                print(f"  • {error}")
            print()
        
        # Mostrar advertencias si las hay
        if self.warnings:
            print(f"{Colors.YELLOW}{Colors.BOLD}ADVERTENCIAS:{Colors.END}")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()
        
        # Instrucciones de uso
        print(f"{Colors.BOLD}PRÓXIMOS PASOS:{Colors.END}")
        print("1. Revisar la configuración en: config/config.yaml")
        print("2. Configurar el nombre del chat de WhatsApp")
        print("3. Ejecutar el bot:")
        
        if self.system == 'windows':
            print(f"   {Colors.CYAN}run_bot.bat{Colors.END}")
        else:
            print(f"   {Colors.CYAN}./run_bot.sh{Colors.END}")
        
        print(f"\n{Colors.BOLD}DOCUMENTACIÓN:{Colors.END}")
        print("• Consultar docs/ para guías detalladas")
        print("• Revisar README.md para instrucciones completas")
        
        print(f"\n{Colors.GREEN}¡Bot Gastos WhatsApp listo para usar! 🚀{Colors.END}")
    
    def run_installation(self):
        """Ejecuta instalación completa."""
        self.print_header()
        
        steps = [
            self.check_system_requirements,
            self.install_system_dependencies,
            self.create_virtual_environment,
            self.install_python_dependencies,
            self.create_directory_structure,
            self.create_configuration_files,
            self.setup_database,
            self.create_launcher_scripts,
            self.run_initial_tests
        ]
        
        for step in steps:
            if not step():
                if self.errors:
                    print(f"\n{Colors.RED}Instalación detenida debido a errores críticos.{Colors.END}")
                    return False
        
        self.print_installation_summary()
        return len(self.errors) == 0


def main():
    """Función principal."""
    installer = BotInstaller()
    success = installer.run_installation()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()