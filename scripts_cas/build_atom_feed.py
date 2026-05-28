#!/usr/bin/env python3
"""
Genera un feed Atom (RSS-compatible) con las convocatorias CAS detectadas
en los últimos 14 días. Lee de `cas_historico.csv` filtrando por
`primera_vez_visto`. Sale a `docs/cas-nuevas.atom`.

El feed se actualiza con cada build y queda servido por GitHub Pages en:
  https://unimauro.github.io/salariosperu/cas-nuevas.atom
"""
import csv
import html
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_HIST = Path("/Users/unimauro/salariosperu-data/cas_historico.csv")
OUT = ROOT / "docs" / "cas-nuevas.atom"
SITE_URL = "https://unimauro.github.io/salariosperu"

DAYS_BACK = 14
MAX_ENTRIES = 200


def fmt_atom_date(s):
    """'2026-05-28' → '2026-05-28T12:00:00Z' (Atom requiere RFC3339)."""
    try:
        dt = datetime.fromisoformat(str(s))
        if dt.hour == 0 and dt.minute == 0:
            dt = dt.replace(hour=12)  # mediodía para evitar zona horaria ambigua
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError):
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def esc(s):
    return html.escape(str(s or ""), quote=True)


def main():
    if not CSV_HIST.exists():
        print(f"ERROR: {CSV_HIST} no existe", file=sys.stderr)
        return 1

    with CSV_HIST.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    today = datetime.utcnow().date()
    cutoff = (today - timedelta(days=DAYS_BACK)).isoformat()

    # Filtrar: nuevas en los últimos N días (incluye vigentes y expiradas
    # que fueron nuevas reciente)
    recientes = [
        r for r in rows
        if r.get("primera_vez_visto", "") >= cutoff and r.get("url")
    ]
    # Más recientes primero
    recientes.sort(key=lambda r: (r.get("primera_vez_visto", ""), r.get("url", "")),
                   reverse=True)
    recientes = recientes[:MAX_ENTRIES]

    feed_updated = fmt_atom_date(today.isoformat())

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        '  <title>SalariosPerú — Nuevas convocatorias CAS</title>',
        f'  <subtitle>Las {len(recientes)} convocatorias del sector público peruano detectadas en los últimos {DAYS_BACK} días</subtitle>',
        f'  <link href="{SITE_URL}/cas-nuevas.atom" rel="self" type="application/atom+xml"/>',
        f'  <link href="{SITE_URL}/" rel="alternate" type="text/html"/>',
        f'  <id>tag:unimauro.github.io,2026:salariosperu/cas-nuevas</id>',
        f'  <updated>{feed_updated}</updated>',
        '  <author>',
        '    <name>SalariosPerú</name>',
        '    <uri>https://unimauro.github.io/salariosperu/</uri>',
        '  </author>',
        '  <generator>build_atom_feed.py</generator>',
        '',
    ]

    for r in recientes:
        url = r.get("url", "").strip()
        if not url:
            continue
        inst = r.get("institucion", "").strip() or "(sin institución)"
        puesto = r.get("puesto", "").strip() or "(sin puesto)"
        depto = r.get("departamento", "").strip() or "—"
        salario_raw = r.get("salario", "").strip()
        try:
            sal_int = int(float(salario_raw)) if salario_raw else None
        except ValueError:
            sal_int = None
        sal_str = f"S/ {sal_int:,}".replace(",", ",") if sal_int else "(salario no reportado)"
        fecha_limite = r.get("fecha_limite", "").strip() or "—"
        first_seen = r.get("primera_vez_visto", "")
        estado = r.get("estado", "vigente")

        title = f"{puesto} @ {inst} — {sal_str}"
        summary = (
            f"{puesto} en {inst}. Departamento: {depto}. "
            f"Salario: {sal_str}. Postular hasta: {fecha_limite}. "
            f"Estado: {estado}."
        )

        lines += [
            "  <entry>",
            f"    <title>{esc(title)}</title>",
            f"    <link href=\"{esc(url)}\" rel=\"alternate\" type=\"text/html\"/>",
            f"    <id>{esc(url)}</id>",
            f"    <published>{fmt_atom_date(first_seen)}</published>",
            f"    <updated>{fmt_atom_date(r.get('ultima_vez_visto', first_seen))}</updated>",
            f"    <category term=\"{esc(depto)}\" label=\"{esc(depto)}\"/>",
            f"    <category term=\"{esc(estado)}\"/>",
            f"    <summary type=\"text\">{esc(summary)}</summary>",
            "  </entry>",
        ]

    lines.append("</feed>")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ {OUT.relative_to(ROOT)}: {len(recientes)} entries · {OUT.stat().st_size/1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
