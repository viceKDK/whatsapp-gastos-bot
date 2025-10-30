import os
from pathlib import Path
from datetime import datetime

from app.services.ocr_processor import OCRProcessor


def safe_rename_sequence(folder: Path) -> list[tuple[Path, Path]]:
    imgs = []
    for ext in ('*.jpg', '*.jpeg', '*.png'):
        imgs.extend(folder.glob(ext))
    imgs = sorted(imgs, key=lambda p: p.name.lower())
    mapping: list[tuple[Path, Path]] = []
    # Renombrado en dos pasos para evitar colisiones
    temp_map = []
    for idx, p in enumerate(imgs, 1):
        tmp = p.with_name(f"__tmp_ren_{idx:03d}{p.suffix.lower()}")
        p.rename(tmp)
        temp_map.append(tmp)
    for idx, tmp in enumerate(temp_map, 1):
        newp = folder / f"{idx:03d}{tmp.suffix.lower()}"
        tmp.rename(newp)
        mapping.append((None, newp))  # old not tracked after tmp; document final set
    return mapping


def main() -> int:
    base = Path('imagen factura')
    if not base.exists():
        print("Directorio 'imagen factura' no existe")
        return 1

    # Renombrar a secuencia
    mapping = safe_rename_sequence(base)

    # Procesar con regla TOTAL y OCR
    ocrp = OCRProcessor()
    results = []
    for _, p in mapping:
        # Modo rapido primero; si no hay, auto con escalado
        r = ocrp.process_receipt_image(str(p), mode='fast', escalate=False)
        sg = r.suggested_gasto
        if not sg:
            r = ocrp.process_receipt_image(str(p), mode='auto', escalate=True)
            sg = r.suggested_gasto

        converted = False
        desc = sg.get('descripcion') if sg else ''
        if desc and 'USD->UYU' in desc:
            converted = True

        # Estimado si no hay sugerencia pero hay montos detectados
        estimado = False
        if not sg and r.detected_amounts:
            est = max(r.detected_amounts)
            sg = {'monto': est}
            estimado = True

        monto = f"{sg['monto']:.2f}" if sg and sg.get('monto') is not None else '—'
        conf = f"{r.confidence:.3f}" if r.confidence else '0.000'
        if sg and not estimado:
            status = 'ok'
        elif sg and estimado:
            status = 'estimado'
        else:
            status = 'sin monto confiable'
        note = 'conversion USD->UYU aplicada' if converted else ''
        results.append((p.name, status, conf, monto, note))

    # Actualizar documento principal, agregando PRUEBA 2
    doc = Path('docs') / 'RESULTADO_OCR_IMAGEN_FACTURAS.md'
    lines = []
    if doc.exists():
        lines = doc.read_text(encoding='utf-8').splitlines()
        lines.append('')
        lines.append('---')
        lines.append('')
    else:
        lines.append('# Resultado OCR Imagen Facturas')
        lines.append('')

    lines.append('PRUEBA 2 (renombradas y regla TOTAL aplicada)')
    lines.append(f'Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append('')
    lines.append('Listado')
    for name, status, conf, monto, note in results:
        extra = f" ({note})" if note else ''
        lines.append(f"- imagen factura/{name}: {status}, conf={conf}, monto={monto} UYU{extra}")

    doc.write_text('\n'.join(lines), encoding='utf-8')
    print(f"Escrito PRUEBA 2 en: {doc}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
