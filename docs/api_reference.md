# 📖 API Reference - Bot Gastos WhatsApp

Esta referencia documenta todas las clases, métodos y funciones públicas del sistema.

## 📋 Tabla de Contenidos

- [Domain Layer](#domain-layer)
- [Application Layer](#application-layer) 
- [Infrastructure Layer](#infrastructure-layer)
- [Shared Components](#shared-components)
- [Configuration](#configuration)

---

## 🧠 Domain Layer

### `domain.models.gasto.Gasto`

Entidad principal que representa un gasto registrado.

#### Constructor

```python
Gasto(monto: Decimal, categoria: str, fecha: datetime, descripcion: Optional[str] = None)
```

**Parámetros:**
- `monto`: Cantidad del gasto (debe ser positivo)
- `categoria`: Categoría del gasto (se normaliza a lowercase)
- `fecha`: Fecha y hora del gasto
- `descripcion`: Descripción opcional del gasto

**Raises:**
- `ValueError`: Si el monto no es positivo
- `TypeError`: Si los tipos no son correctos

#### Métodos

##### `es_del_mes(año: int, mes: int) -> bool`

Verifica si el gasto pertenece a un mes específico.

```python
gasto = Gasto(Decimal('100'), 'comida', datetime(2025, 8, 6))
assert gasto.es_del_mes(2025, 8) == True
```

##### `es_de_categoria(categoria: str) -> bool`

Verifica si el gasto pertenece a una categoría específica.

```python
gasto = Gasto(Decimal('100'), 'comida', datetime.now())
assert gasto.es_de_categoria('COMIDA') == True  # Case insensitive
```

##### `to_dict() -> dict`

Convierte el gasto a diccionario para serialización.

```python
{
    'id': 1,
    'monto': 100.0,
    'categoria': 'comida',
    'fecha': '2025-08-06T14:30:00',
    'descripcion': None
}
```

##### `from_dict(data: dict) -> 'Gasto'` (classmethod)

Crea un Gasto desde un diccionario.

#### Propiedades

- `id`: Identificador único (asignado por storage)
- `monto`: Decimal - Cantidad del gasto
- `categoria`: str - Categoría normalizada
- `fecha`: datetime - Fecha y hora
- `descripcion`: Optional[str] - Descripción opcional

---

### `domain.value_objects.monto.Monto`

Objeto de valor inmutable para representar cantidades monetarias.

#### Constructor

```python
Monto(valor: Decimal)
```

**Validaciones automáticas:**
- Debe ser mayor que cero
- Máximo 2 decimales (redondea automáticamente)
- Límite máximo de $1,000,000

#### Métodos de Creación

##### `from_string(monto_str: str) -> 'Monto'` (classmethod)

```python
monto = Monto.from_string("150.50")
monto = Monto.from_string("$1,500")  # Remueve $ y ,
```

##### `from_float(monto_float: float) -> 'Monto'` (classmethod)

```python
monto = Monto.from_float(150.50)
```

#### Operaciones

##### `sumar(otro: Union['Monto', Decimal, float]) -> 'Monto'`

```python
monto1 = Monto(Decimal('100'))
monto2 = Monto(Decimal('50'))
total = monto1.sumar(monto2)  # Monto(150)
```

##### `restar(otro: Union['Monto', Decimal, float]) -> 'Monto'`

**Raises:** `ValueError` si el resultado sería negativo

##### `multiplicar(factor: Union[int, float, Decimal]) -> 'Monto'`

```python
monto = Monto(Decimal('100'))
doble = monto.multiplicar(2)  # Monto(200)
```

#### Comparaciones

```python
monto1.es_mayor_que(monto2) -> bool
monto1.es_menor_que(monto2) -> bool

# También soporta operadores
monto1 > monto2
monto1 < monto2
```

#### Conversiones

```python
monto.to_float() -> float
monto.to_string_formatted(include_currency=True) -> str  # "$100.00"
str(monto)  # "$100.00"
float(monto)  # 100.0
```

---

### `domain.value_objects.categoria.Categoria`

Objeto de valor para categorías de gastos con validación.

#### Constructor

```python
Categoria(nombre: str)
```

Normaliza automáticamente a lowercase y valida caracteres.

#### Categorías Válidas

```python
Categoria.CATEGORIAS_VALIDAS = {
    'comida', 'transporte', 'entretenimiento', 'salud', 'servicios',
    'ropa', 'educacion', 'hogar', 'trabajo', 'otros', 'super', 'nafta'
}
```

#### Métodos

##### `crear_con_validacion_estricta(nombre: str) -> 'Categoria'` (classmethod)

Valida contra lista de categorías predefinidas.

**Raises:** `ValueError` con sugerencias si la categoría no es válida.

##### `agregar_categoria_valida(nueva_categoria: str)` (classmethod)

```python
Categoria.agregar_categoria_valida("streaming")
```

##### `obtener_categorias_validas() -> Set[str]` (classmethod)

##### `es_similar_a(otra_categoria: str) -> bool`

Verifica similitud usando distancia de edición.

##### `to_display_name() -> str`

Retorna nombre capitalizado para mostrar.

---

## 🔄 Application Layer

### `app.services.interpretar_mensaje.InterpretarMensajeService`

Servicio para extraer información de gastos desde texto.

#### Constructor

```python
InterpretarMensajeService()
```

#### Métodos

##### `procesar_mensaje(texto: str, fecha_mensaje: Optional[datetime] = None) -> Optional[Gasto]`

Procesa un mensaje y extrae información de gasto.

**Parámetros:**
- `texto`: Texto del mensaje de WhatsApp
- `fecha_mensaje`: Fecha del mensaje (default: datetime.now())

**Returns:** `Gasto` si se extrajo información válida, `None` si no

**Formatos soportados:**
```python
"gasto: 500 comida"      # Formato completo
"500 super"              # Formato simple
"gasté 150 nafta"        # Variante con verbo
"compré 75 ropa"         # Otra variante
```

**Ejemplo:**
```python
service = InterpretarMensajeService()
gasto = service.procesar_mensaje("gasto: 150 comida")
# Returns: Gasto(monto=150, categoria='comida', fecha=now)
```

#### Patrones de Reconocimiento

- `PATRON_GASTO`: Patrón principal con palabras clave
- `PATRON_SOLO_MONTO`: Patrón simple número + categoría

---

### `app.services.registrar_gasto.RegistrarGastoService`

Servicio para persistir gastos en el storage configurado.

#### Constructor

```python
RegistrarGastoService(storage_repository: StorageRepository)
```

#### Métodos

##### `registrar_gasto(gasto: Gasto) -> bool`

Registra un nuevo gasto con validaciones de negocio.

**Validaciones incluidas:**
- Detección de duplicados (5 minutos)
- Límite máximo de monto ($100,000)
- Validaciones de integridad

##### `obtener_gastos_periodo(fecha_desde: date, fecha_hasta: Optional[date] = None) -> List[Gasto]`

##### `obtener_gastos_categoria(categoria: str) -> List[Gasto]`

---

### `app.usecases.procesar_mensaje.ProcesarMensajeUseCase`

Caso de uso principal que orquesta interpretación y registro.

#### Constructor

```python
ProcesarMensajeUseCase(storage_repository: StorageRepository)
```

#### Métodos

##### `procesar(mensaje_texto: str, fecha_mensaje: Optional[datetime] = None) -> Optional[Gasto]`

Procesa mensaje completo: interpretación + registro.

##### `procesar_batch(mensajes: list[tuple[str, Optional[datetime]]]) -> list[Gasto]`

Procesa múltiples mensajes en lote.

---

## 🔌 Infrastructure Layer

### `infrastructure.storage.excel_writer.ExcelStorage`

Implementación de storage usando archivos Excel.

#### Constructor

```python
ExcelStorage(archivo_path: str)
```

Crea el archivo Excel automáticamente si no existe.

#### Métodos

##### `guardar_gasto(gasto: Gasto) -> bool`

Guarda gasto en Excel con formato automático.

##### `obtener_gastos(fecha_desde: date, fecha_hasta: date) -> List[Gasto]`

##### `obtener_gastos_por_categoria(categoria: str) -> List[Gasto]`

##### `backup_archivo() -> str`

Crea backup timestamped del archivo.

##### `obtener_estadisticas() -> dict`

```python
{
    'total_gastos': 150,
    'monto_total': 15750.50,
    'categorias': {'comida': 45, 'transporte': 30, ...},
    'fecha_primer_gasto': '2025-01-01T10:00:00',
    'fecha_ultimo_gasto': '2025-08-06T14:30:00'
}
```

#### Configuración de Columnas

```python
COLUMNAS = {
    'A': {'nombre': 'Fecha', 'ancho': 12},
    'B': {'nombre': 'Hora', 'ancho': 10}, 
    'C': {'nombre': 'Monto', 'ancho': 12},
    'D': {'nombre': 'Categoría', 'ancho': 15},
    'E': {'nombre': 'Descripción', 'ancho': 30}
}
```

---

### Storage Repository Protocol

Interface que deben implementar todos los storages.

```python
class StorageRepository(Protocol):
    def guardar_gasto(self, gasto: Gasto) -> bool: ...
    def obtener_gastos(self, fecha_desde: date, fecha_hasta: date) -> List[Gasto]: ...
    def obtener_gastos_por_categoria(self, categoria: str) -> List[Gasto]: ...
```

---

## 🛠️ Shared Components

### `shared.logger`

Sistema de logging centralizado.

#### Funciones

##### `get_logger(name: str) -> logging.Logger`

Obtiene logger configurado.

```python
logger = get_logger(__name__)
logger.info("Mensaje informativo")
logger.error("Error occurred", exc_info=True)
```

##### `log_exception(logger: logging.Logger, exc: Exception, context: str = "")`

Utility para loggear excepciones consistentemente.

##### `log_function_entry(logger: logging.Logger, func_name: str, **kwargs)`

Para debugging de entrada a funciones.

##### `log_performance(logger: logging.Logger, operation: str, duration_seconds: float)`

Para métricas de performance.

---

### `shared.utils`

Utilidades generales del sistema.

#### Funciones de Conversión

##### `ensure_decimal(value: Union[str, int, float, Decimal]) -> Decimal`

Convierte valor a Decimal de manera segura.

##### `normalize_text(text: str) -> str`

Normaliza texto removiendo espacios extra.

##### `format_currency(amount: Union[Decimal, float, int], currency_symbol: str = "$") -> str`

Formatea monto como moneda.

#### Funciones de Validación

##### `is_valid_file_path(path: Union[str, Path]) -> bool`

##### `ensure_directory_exists(directory: Union[str, Path]) -> bool`

##### `validate_environment() -> Dict[str, bool]`

Valida entorno de ejecución:
```python
{
    'python_version': True,
    'correct_directory': True,
    'data_writable': True,
    'logs_writable': True,
    'selenium_available': True,
    'openpyxl_available': True
}
```

#### Decoradores

##### `@retry_operation(max_attempts: int = 3, delay_seconds: float = 1.0)`

Reintentar operaciones fallidas.

```python
@retry_operation(max_attempts=3, delay_seconds=2.0)
def operacion_inestable():
    # código que puede fallar
    pass
```

##### `@timing_decorator`

Medir tiempo de ejecución.

```python
@timing_decorator
def funcion_a_medir():
    # código a medir
    pass
```

#### Funciones de Sistema

##### `get_project_root() -> Path`

##### `get_system_info() -> Dict[str, Any]`

Información del sistema para debugging.

---

## ⚙️ Configuration

### `config.settings`

Sistema de configuración centralizada.

#### Clases de Configuración

##### `Settings`

Configuración principal del sistema.

**Propiedades:**
- `storage_mode: StorageMode` - Modo de almacenamiento
- `database: DatabaseConfig` - Configuración BD
- `excel: ExcelConfig` - Configuración Excel
- `whatsapp: WhatsAppConfig` - Configuración WhatsApp
- `logging: LoggingConfig` - Configuración logging
- `categorias: CategoriaConfig` - Configuración categorías

#### Métodos

##### `Settings.load_from_env() -> Settings` (classmethod)

Carga configuración desde variables de entorno.

##### `get_storage_file_path() -> str`

Obtiene ruta del archivo según modo configurado.

##### `ensure_directories_exist()`

Crea directorios necesarios.

##### `validate_configuration() -> list[str]`

Valida configuración, retorna lista de errores.

##### `to_dict() -> dict`

Convierte configuración a diccionario.

#### Funciones Globales

##### `get_settings() -> Settings`

Obtiene instancia singleton de configuración.

##### `reload_settings() -> Settings`

Recarga configuración desde entorno.

---

### Enums de Configuración

#### `StorageMode`
- `EXCEL = "excel"`
- `SQLITE = "sqlite"`

#### `LogLevel`
- `DEBUG = "DEBUG"`
- `INFO = "INFO"`
- `WARNING = "WARNING"`
- `ERROR = "ERROR"`

---

## 📊 Interface Layer

### `interface.cli.run_bot.BotRunner`

Runner principal del bot CLI.

#### Constructor

```python
BotRunner(settings: Settings)
```

#### Métodos

##### `run() -> bool`

Ejecuta el bot principal.

**Returns:** `True` si se ejecutó sin errores críticos

##### `stop()`

Detiene el bot de manera limpia.

#### Propiedades

##### `stats`

Estadísticas de ejecución:
```python
{
    'inicio': datetime,
    'mensajes_procesados': int,
    'gastos_registrados': int, 
    'errores': int,
    'ultima_actividad': datetime
}
```

---

## 🔧 Constantes del Sistema

### `shared.constants`

#### Límites

```python
class Limits:
    MIN_AMOUNT = 0.01
    MAX_AMOUNT = 1000000.00
    MAX_DAILY_AMOUNT = 100000.00
    MAX_CATEGORY_LENGTH = 50
    MAX_DESCRIPTION_LENGTH = 500
```

#### Patrones de Mensajes

```python
class MessagePatterns:
    GASTO_PATTERN = r'(?:gasto|gasté|pagué|compré)?\s*:?\s*(\d+(?:\.\d{1,2})?)\s+(\w+)'
    SIMPLE_PATTERN = r'^(\d+(?:\.\d{1,2})?)\s+(\w+)$'
    GASTO_KEYWORDS = {'gasto', 'gasté', 'pagué', 'compré', ...}
```

#### Estados

```python
class BotStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"

class MessageStatus(Enum):
    NEW = "new"
    PROCESSED = "processed"
    FAILED = "failed"
```

---

## 🚨 Manejo de Errores

### Excepciones Personalizadas

El sistema usa excepciones estándar de Python con mensajes descriptivos:

- `ValueError`: Datos inválidos (montos negativos, categorías vacías)
- `TypeError`: Tipos incorrectos
- `FileNotFoundError`: Archivos no encontrados
- `PermissionError`: Problemas de permisos
- `ConnectionError`: Problemas de conexión (WhatsApp)

### Formato de Error Logs

```python
# Estructura estándar de logs de error
logger.error(f"Error específico: {descripción}", exc_info=True)

# Para excepciones con contexto
log_exception(logger, exception, "contexto donde ocurrió")
```

---

## 📈 Performance

### Métricas Monitoreadas

- Tiempo de procesamiento de mensajes
- Operaciones de storage (lecturas/escrituras)
- Conexiones WhatsApp
- Uso de memoria

### Optimizaciones Implementadas

- Cache de patrones regex compilados
- Batch processing para múltiples mensajes
- Logging asíncrono con rotación
- Validaciones tempranas para evitar procesamiento innecesario

---

## 🔗 Enlaces Útiles

- **Documentación Usuario:** [user_guide.md](user_guide.md)
- **Guía Desarrollador:** [developer_guide.md](developer_guide.md)
- **Instalación:** [installation_guide.md](installation_guide.md)
- **Configuración:** [configuration_guide.md](configuration_guide.md)
- **Troubleshooting:** [troubleshooting_guide.md](troubleshooting_guide.md)