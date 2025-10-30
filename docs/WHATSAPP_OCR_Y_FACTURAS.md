# WhatsApp Bot - OCR de Facturas y Transferencias

## Objetivo
El bot de WhatsApp para gastos reconoce imagenes y archivos PDF enviados al chat de gastos y extrae la informacion relevante para registrar un gasto. Soporta:

- Imagenes de recibos o facturas (JPG o PNG) con OCR
- Archivos PDF de facturas (texto nativo o escaneados)
- Archivos PDF de transferencias o comprobantes bancarios

---

## Flujo de uso en WhatsApp
- Envia una foto o PDF al chat configurado (`whatsapp.target_chat_name`).
- El bot detecta el tipo de contenido: `texto`, `imagen` (OCR) o `pdf`.
- Para imagenes, aplica OCR; para PDFs intenta extraer texto directo y, si no se puede, realiza OCR pagina por pagina.
- Interpreta los datos, sugiere un gasto o lo registra directamente si la confianza es alta.
- Devuelve confirmacion, advertencias o solicita que elijas entre sugerencias.

Ejemplo de confirmacion:
```
Gasto registrado
Monto: $4560.00
Categoria: servicios
Fecha: 2025-10-29
Descripcion: Factura ACME S.A., N 000123
Origen: pdf o ocr (confianza 0.86)
```

---

## Datos que se extraen

### Facturas o recibos (imagen o PDF)
- Monto total (Total, Importe o Subtotal)
- Fecha del comprobante
- Comercio o proveedor
- Categoria sugerida (por palabras clave)
- Numero de factura (si aparece)
- Impuestos (IVA o Impuesto, cuando es reconocible)
- Items o descripciones (limitado a los primeros terminos relevantes)

### Transferencias (PDF)
- Monto transferido
- Fecha y hora
- Referencia o numero de comprobante
- Origen o destino (alias, CBU o IBAN si figuran en el PDF)
- Concepto o descripcion y moneda

Notas:
- Si faltan campos o la confianza es baja, el bot devuelve sugerencias y pide confirmacion.
- Los archivos PDF con texto embebido se analizan primero sin OCR para mayor precision.

---

## Configuracion relevante
Archivo: `config/config.yaml` (se genera si no existe). Secciones clave:

```yaml
ocr:
  enabled: true               # Habilita OCR para imagenes y PDFs
  language: "spa+eng"         # Idiomas Tesseract
  confidence_threshold: 0.6    # Minimo para registrar sin pedir confirmacion
  preprocessing_enabled: true  # Limpieza y mejora de imagen antes del OCR
  supported_formats: [".jpg", ".jpeg", ".png", ".pdf"]

  # PDF
  pdf_enabled: true
  pdf_conversion_dpi: 200      # DPI al rasterizar PDFs escaneados
  max_pdf_pages: 10            # Maximo de paginas por PDF

  # Windows (opcional)
  tesseract_path: "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

whatsapp:
  target_chat_name: "Gastos Bot"  # Chat a monitorear
```

Requisitos (instalador guia en `scripts/install.py`):
- Tesseract OCR y paquetes de idiomas espanol e ingles
- Librerias Python: `pytesseract`, `opencv-python`, `PyPDF2`, `pdf2image`, `Pillow`

---

## Como probar con archivos de ejemplo en la raiz
Puedes dejar dos archivos de ejemplo en la raiz del proyecto, por ejemplo:
- `factura_ejemplo.pdf` (factura)
- `transferencia_ejemplo.pdf` (comprobante de transferencia)

Luego ejecuta desde consola estos comandos para verificar extraccion local sin pasar por WhatsApp:

Procesar PDF (factura o transferencia):
```bash
python -c "from app.services.message_processor import process_pdf_message;print(process_pdf_message(pdf_path='factura_ejemplo.pdf'))"

python -c "from app.services.message_processor import process_pdf_message;print(process_pdf_message(pdf_path='transferencia_ejemplo.pdf'))"
```

Procesar imagen (recibo o factura en JPG o PNG):
```bash
python -c "from app.services.message_processor import process_image_message;print(process_image_message(image_path='mi_recibo.jpg'))"
```

La salida esperada es un objeto con `success`, `confidence`, `source` (`ocr` o `pdf`), `extracted_text`, y `gasto` cuando se pudo armar automaticamente. Si no, veras `suggestions` para elegir.

---

## Comportamiento y validaciones
- El motor prioriza el texto directo de PDF; si no hay, convierte a imagenes y aplica OCR.
- Se calculan montos, fechas y categorias con reglas y expresiones regulares.
- Si hay multiples montos plausibles, se sugieren alternativas ordenadas por probabilidad.
- Toda sugerencia pasa por validaciones (`validation.*` en `config`).

Mensajes de error comunes:
- Imagen borrosa u oscura: mejora iluminacion o recorta la foto.
- PDF escaneado de baja calidad: intenta subir un PDF con texto embebido.
- Idiomas no soportados: agrega el paquete de idioma en Tesseract o ajusta `ocr.language`.

---

## Privacidad y logs
- Los archivos se procesan localmente; no se suben a servicios externos.
- Logs: `logs/bot_gastos.log` y metricas en `logs/metrics.json`.
- Archivos temporales se limpian automaticamente tras el procesamiento.

---

## Notas de implementacion
- Codigo principal:
  - OCR de imagenes: `app/services/ocr_processor.py`
  - PDFs de facturas y transferencias: `app/services/pdf_processor.py`
  - Orquestacion por tipo de mensaje: `app/services/message_processor.py`
- Integracion de WhatsApp: ver `docs/WHATSAPP_INTEGRATION.md` para ejecucion y pruebas end-to-end.
