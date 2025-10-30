import sys
from pathlib import Path
from datetime import datetime

from app.services.message_processor import process_image_message


def main() -> int:
    base = Path('imagen factura')
    if not base.exists():
        print("Directorio 'imagen factura' no existe", file=sys.stderr)
        return 1

    imgs = []
    for ext in ('*.jpg', '*.jpeg', '*.png'):
        imgs.extend(base.glob(ext))

    lines = []
    lines.append('# Resultado OCR Imagen Facturas')
    lines.append('')
    lines.append('Generado: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    lines.append('')
    lines.append('Reglas:')
    lines.append('- Monto: se toma el monto mayor detectado en la imagen')
    lines.append('- Moneda: pesos uruguayos (UYU); solo se convierte USD->UYU si aparece USD/US$/U$S en el texto')
    lines.append('- Categoria: obligatoria (si falta, el bot la pide); descripcion: opcional')
    lines.append('')

    if not imgs:
        lines.append('No se encontraron imagenes en imagen factura')
    else:
        lines.append(f'Total imagenes: {len(imgs)}')
        lines.append('')
        for p in sorted(imgs, key=lambda x: x.name.lower()):
            try:
                r = process_image_message(image_path=str(p))
                converted = False
                desc = r.gasto.descripcion if r.gasto else ''
                if desc and 'USD->UYU' in desc:
                    converted = True
                monto = f"{float(r.gasto.monto):.2f}" if r.gasto else '—'
                conf = f"{r.confidence:.3f}" if r.confidence else '0.000'
                status = 'ok' if r.success and r.gasto else 'sin monto confiable'
                note = 'conversion USD->UYU aplicada' if converted else ''
                lines.append(f"- {p.as_posix()}: {status}, conf={conf}, monto={monto} UYU{(' ('+note+')') if note else ''}")
            except Exception as e:
                lines.append(f"- {p.as_posix()}: error: {e}")

    out = Path('docs') / 'RESULTADO_OCR_IMAGEN_FACTURAS.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(f"Escrito: {out}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

