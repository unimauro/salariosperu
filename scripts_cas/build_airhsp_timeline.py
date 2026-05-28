#!/usr/bin/env python3
"""
Procesa todos los PERSONALSP_YYYY.csv disponibles del MEF AIRHSP y emite
una serie de tiempo de agregados anuales.

Output: scripts_cas/airhsp_timeline.json — agregados por cada año disponible,
listos para alimentar un selector de año + chart de timeline en estado.html.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path("/Users/unimauro/salariosperu-data/mef_airhsp")
OUT = ROOT / "scripts_cas" / "airhsp_timeline.json"

COLS = [
    "PERIODO", "EJERCICIO", "MES", "NIVEL", "SECTOR", "PLIEGO",
    "UNIDAD_EJECUTORA", "DESC_TIPO_REGISTRO", "ESTADO_REGISTRO",
    "DESC_REGIMEN_LABORAL", "DESC_GRUPO_OCASIONAL",
    "CANTIDAD", "ING_IMPONIBLE_PERM_MENSUAL",
    "ING_NO_IMPONIBLE_PERM_MENSUAL", "INCENTIVO_UNICO_MENSUAL",
    "COSTO_TOTAL_ANUAL",
]

TIPOS_ACTIVOS = {"Activos", "Contrato Administrativo de Servicios"}


def ingreso_promedio(g):
    ing_total = (g["ING_IMPONIBLE_PERM_MENSUAL"].fillna(0)
                 + g["ING_NO_IMPONIBLE_PERM_MENSUAL"].fillna(0)
                 + g["INCENTIVO_UNICO_MENSUAL"].fillna(0))
    peso = g["CANTIDAD"].fillna(0)
    total = peso.sum()
    return float(ing_total.sum() / total) if total else 0.0


def process_one_year(csv_path, year):
    print(f"\n[{year}] leyendo {csv_path.name} ({csv_path.stat().st_size/1e6:.0f} MB)…", flush=True)
    df = pd.read_csv(csv_path, usecols=COLS, dtype={"PERIODO": str, "MES": str})
    print(f"  Filas crudas: {len(df):,}")

    latest = df["PERIODO"].max()
    snap = df[df["PERIODO"] == latest].copy()
    snap = snap[snap["ESTADO_REGISTRO"] == "OCUPADO"]
    snap = snap[snap["DESC_TIPO_REGISTRO"].isin(TIPOS_ACTIVOS)]

    total = int(snap["CANTIDAD"].sum())
    ing_p = ingreso_promedio(snap)
    costo = float(snap["COSTO_TOTAL_ANUAL"].fillna(0).sum())
    n_pliegos = int(snap["PLIEGO"].nunique())
    print(f"  Snapshot {latest}: {total:,} activos · S/ {ing_p:,.0f} prom · {n_pliegos} pliegos")

    # Agregados por dimensión
    reg = snap.groupby("DESC_REGIMEN_LABORAL").apply(lambda g: pd.Series({
        "cantidad": int(g["CANTIDAD"].sum()),
        "ing_prom": round(ingreso_promedio(g), 0),
    })).reset_index().to_dict(orient="records")

    sec = snap.groupby("SECTOR").apply(lambda g: pd.Series({
        "cantidad": int(g["CANTIDAD"].sum()),
        "ing_prom": round(ingreso_promedio(g), 0),
    })).reset_index().sort_values("cantidad", ascending=False).head(20).to_dict(orient="records")

    grp = snap.groupby("DESC_GRUPO_OCASIONAL").apply(lambda g: pd.Series({
        "cantidad": int(g["CANTIDAD"].sum()),
        "ing_prom": round(ingreso_promedio(g), 0),
    })).reset_index().to_dict(orient="records")

    return {
        "year": year,
        "periodo": latest,
        "kpis": {
            "total_servidores": total,
            "ingreso_promedio_mensual": round(ing_p, 0),
            "costo_total_anual": round(costo, 0),
            "n_pliegos": n_pliegos,
        },
        "por_regimen": reg,
        "por_sector": sec,
        "por_grupo": grp,
    }


def main():
    csvs = sorted(DATA_DIR.glob("PERSONALSP_*.csv"))
    if not csvs:
        print(f"ERROR: no se encontraron CSVs en {DATA_DIR}", file=sys.stderr)
        return 1

    print(f"Encontrados {len(csvs)} archivos:")
    for f in csvs:
        print(f"  - {f.name} ({f.stat().st_size/1e6:.0f} MB)")

    results = []
    for f in csvs:
        try:
            year = int(f.stem.split("_")[-1])
        except ValueError:
            continue
        try:
            results.append(process_one_year(f, year))
        except Exception as e:
            print(f"  ⚠ error procesando {f.name}: {e}", file=sys.stderr)

    out = {
        "fuente": "MEF — AIRHSP",
        "anios_disponibles": [r["year"] for r in results],
        "snapshots": results,  # uno por año
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"\n✓ {OUT.name} escrito ({OUT.stat().st_size/1024:.0f} KB)")

    # Inyectar en estado.html (mismo patrón que airhsp-data)
    estado = ROOT / "docs" / "estado.html"
    if estado.exists():
        html = estado.read_text()
        payload = json.dumps(out, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        import re
        pat = re.compile(
            r'(<script\s+id="airhsp-timeline"[^>]*>)([\s\S]*?)(</script>)',
            re.IGNORECASE
        )
        new_html, n = pat.subn(rf"\g<1>{payload}\g<3>", html)
        if n:
            estado.write_text(new_html)
            print(f"✓ docs/estado.html: airhsp-timeline patcheado ({len(payload)/1024:.0f} KB)")
        else:
            print(f"  ⚠ no se encontró <script id=airhsp-timeline> — agrégalo a estado.html")

    print("\n=== Evolución total servidores activos ===")
    for r in results:
        print(f"  {r['year']}: {r['kpis']['total_servidores']:>10,}  |  S/ {r['kpis']['ingreso_promedio_mensual']:>6,.0f} prom")

    return 0


if __name__ == "__main__":
    sys.exit(main())
