"""
Constantes del Sistema

Valores constantes utilizados en toda la aplicación.
"""

from enum import Enum
from typing import Set


# Información del Proyecto
# ========================
PROJECT_NAME = "Bot Gastos WhatsApp"
VERSION = "1.0.0"
AUTHOR = "Desarrollador"
DESCRIPTION = "Bot personal para registrar gastos desde WhatsApp Web"


# Configuración de Archivos
# =========================
DEFAULT_DATA_DIR = "data"
DEFAULT_LOGS_DIR = "logs"
DEFAULT_CONFIG_DIR = "config"

DEFAULT_EXCEL_FILE = "gastos.xlsx"
DEFAULT_SQLITE_FILE = "gastos.db"
DEFAULT_LOG_FILE = "bot.log"
DEFAULT_ENV_FILE = ".env"


# Configuración de WhatsApp
# =========================
DEFAULT_POLL_INTERVAL = 30  # segundos
DEFAULT_CONNECTION_TIMEOUT = 10  # segundos
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5  # segundos

# Selectores CSS de WhatsApp Web (pueden cambiar)
WHATSAPP_SELECTORS = {
    'message_container': '[data-testid="conversation-panel-messages"]',
    'message_item': '[data-testid="msg-container"]',
    'message_text': 'span.selectable-text',
    'message_time': '[data-testid="msg-meta"]',
    'chat_input': '[data-testid="compose-box-input"]',
    'send_button': '[data-testid="compose-btn-send"]',
    'chat_list': '[data-testid="chat-list"]',
    'chat_item': '[data-testid="list-item-"]'
}


# Patrones de Mensajes
# ====================
class MessagePatterns:
    """Patrones regex para reconocimiento de mensajes."""
    
    # Patrón principal para gastos
    GASTO_PATTERN = r'(?:gasto|gasté|pagué|compré)?\s*:?\s*(\d+(?:\.\d{1,2})?)\s+(\w+)'
    
    # Patrón simple (solo número + categoría)
    SIMPLE_PATTERN = r'^(\d+(?:\.\d{1,2})?)\s+(\w+)$'
    
    # Palabras clave que indican un gasto
    GASTO_KEYWORDS = {
        'gasto', 'gasté', 'gastos', 'pagué', 'pague', 'compré', 'compre',
        'costo', 'costó', 'precio', 'vale', 'sale', 'invertí', 'invierte'
    }
    
    # Patrones para extraer montos
    MONTO_PATTERNS = [
        r'\$(\d+(?:\.\d{1,2})?)',  # $100, $150.50
        r'(\d+(?:\.\d{1,2})?)\$',  # 100$, 150.50$
        r'(\d+(?:\.\d{1,2})?)'     # 100, 150.50
    ]


# Categorías de Gastos
# ====================
class DefaultCategories:
    """Categorías predefinidas de gastos."""
    
    CORE_CATEGORIES: Set[str] = {
        'comida', 'transporte', 'entretenimiento', 'salud', 'servicios',
        'ropa', 'educacion', 'hogar', 'trabajo', 'otros'
    }
    
    EXTENDED_CATEGORIES: Set[str] = {
        'super', 'supermercado', 'nafta', 'combustible', 'medicina',
        'farmacia', 'cine', 'restaurante', 'cafe', 'taxi', 'colectivo',
        'uber', 'tren', 'subte', 'peluqueria', 'gimnasio', 'libros',
        'streaming', 'internet', 'celular', 'luz', 'gas', 'agua',
        'alquiler', 'expensas', 'impuestos', 'banco', 'seguros'
    }
    
    ALL_CATEGORIES: Set[str] = CORE_CATEGORIES | EXTENDED_CATEGORIES
    
    # Mapeo de alias comunes
    CATEGORY_ALIASES = {
        'comida': ['food', 'restaurant', 'almuerzo', 'cena', 'desayuno'],
        'transporte': ['transport', 'viaje', 'taxi', 'uber', 'colectivo'],
        'entretenimiento': ['fun', 'diversión', 'cine', 'teatro', 'juegos'],
        'salud': ['health', 'médico', 'doctor', 'farmacia', 'medicina'],
        'servicios': ['service', 'luz', 'gas', 'agua', 'internet'],
        'super': ['supermercado', 'mercado', 'compras', 'grocery'],
        'nafta': ['combustible', 'gas', 'gasolina', 'fuel']
    }


# Límites y Validaciones
# ======================
class Limits:
    """Límites del sistema."""
    
    # Límites monetarios
    MIN_AMOUNT = 0.01  # Monto mínimo
    MAX_AMOUNT = 1000000.00  # Monto máximo
    MAX_DAILY_AMOUNT = 100000.00  # Máximo por día
    
    # Límites de texto
    MAX_CATEGORY_LENGTH = 50
    MAX_DESCRIPTION_LENGTH = 500
    MAX_MESSAGE_LENGTH = 1000
    
    # Límites de archivos
    MAX_LOG_SIZE_MB = 10
    MAX_BACKUP_COUNT = 5
    MAX_EXCEL_ROWS = 1000000  # Límite Excel
    
    # Límites temporales
    MAX_MESSAGE_AGE_HOURS = 24  # Ignorar mensajes muy antiguos
    DUPLICATE_DETECTION_MINUTES = 5  # Ventana para detectar duplicados


# Estados del Sistema
# ===================
class BotStatus(Enum):
    """Estados posibles del bot."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class MessageStatus(Enum):
    """Estados de procesamiento de mensajes."""
    NEW = "new"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"


# Colores para Consola
# ====================
class Colors:
    """Códigos ANSI para colores en consola."""
    
    # Colores básicos
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Estilos
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    
    # Colores temáticos
    SUCCESS = GREEN
    WARNING = YELLOW
    ERROR = RED
    INFO = CYAN
    DEBUG = MAGENTA


# URLs y Referencias
# ==================
DOCUMENTATION_URLS = {
    'selenium': 'https://selenium-python.readthedocs.io/',
    'openpyxl': 'https://openpyxl.readthedocs.io/',
    'whatsapp_web': 'https://web.whatsapp.com/',
    'project_repo': 'https://github.com/usuario/bot-gastos-whatsapp'  # Actualizar con URL real
}

HELP_MESSAGES = {
    'setup': """
Para configurar el bot:
1. Instala dependencias: pip install -r requirements.txt
2. Copia configuración: cp config/.env.example config/.env
3. Edita config/.env con tus settings
4. Ejecuta: python main.py
    """,
    
    'troubleshooting': """
Problemas comunes:
- Error ChromeDriver: Asegúrate de tener Chrome instalado
- No procesa mensajes: Verifica TARGET_CHAT_NAME en config
- Permisos: Ejecuta con permisos de administrador si es necesario
    """,
    
    'message_format': """
Formatos de mensaje soportados:
- gasto: 500 comida
- 150 transporte  
- gasté 75 entretenimiento
- compré 200 ropa
    """
}


# Configuración de Desarrollo
# ===========================
class DevSettings:
    """Configuraciones para desarrollo."""
    
    # Intervalos más rápidos para testing
    DEV_POLL_INTERVAL = 5  # segundos
    DEV_LOG_LEVEL = "DEBUG"
    
    # Datos de prueba
    TEST_MESSAGES = [
        ("gasto: 100 comida", "Test expense 1"),
        ("250 transporte", "Test expense 2"),
        ("gasté 75 entretenimiento", "Test expense 3")
    ]
    
    TEST_CATEGORIES = ['test_cat1', 'test_cat2', 'test_cat3']


# Metadatos del Sistema
# ====================
SYSTEM_INFO = {
    'name': PROJECT_NAME,
    'version': VERSION,
    'author': AUTHOR,
    'description': DESCRIPTION,
    'python_required': '>=3.9',
    'license': 'Personal Use',
    'keywords': ['whatsapp', 'bot', 'expenses', 'automation', 'python']
}