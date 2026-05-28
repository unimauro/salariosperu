#!/usr/bin/env python3
"""
Procesa PERSONALSP_2025.csv del MEF AIRHSP y genera agregados JSON
para la nueva hoja docs/estado.html.

Estrategia: usar el ÚLTIMO mes disponible (snapshot más reciente), porque
sumar todos los meses contaría a la misma persona 12 veces.

Output: scripts_cas/airhsp_agregados.json
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV = Path("/Users/unimauro/salariosperu-data/mef_airhsp/PERSONALSP_2025.csv")
OUT = ROOT / "scripts_cas" / "airhsp_agregados.json"


def main():
    if not CSV.exists():
        print(f"ERROR: {CSV} no existe", file=sys.stderr)
        return 1

    print(f"[1] Leyendo {CSV.name} ({CSV.stat().st_size/1024/1024:.0f} MB) …")
    # Lectura eficiente: solo columnas que necesitamos
    cols = [
        "PERIODO", "EJERCICIO", "MES", "NIVEL", "SECTOR", "PLIEGO",
        "UNIDAD_EJECUTORA", "DESC_TIPO_REGISTRO", "ESTADO_REGISTRO",
        "DESC_REGIMEN_LABORAL", "DESC_GRUPO_OCASIONAL", "DESC_CONDICION_LABORAL",
        "DESC_REGIMEN_PENSIONARIO", "CANTIDAD",
        "ING_IMPONIBLE_PERM_MENSUAL", "ING_NO_IMPONIBLE_PERM_MENSUAL",
        "INCENTIVO_UNICO_MENSUAL", "COSTO_TOTAL_ANUAL",
    ]
    df = pd.read_csv(CSV, usecols=cols, dtype={"PERIODO": str, "MES": str})
    print(f"   Total filas: {len(df):,}")
    print(f"   Periodos: {sorted(df['PERIODO'].unique())}")

    # Latest month snapshot
    latest = df["PERIODO"].max()
    print(f"\n[2] Foto del último periodo: {latest}")
    snap = df[df["PERIODO"] == latest].copy()
    print(f"   Filas en snapshot: {len(snap):,}")
    print(f"   Total servidores (suma CANTIDAD): {int(snap['CANTIDAD'].sum()):,}")

    # Filtrar solo OCUPADOS (activos en ese mes)
    snap_ocupado = snap[snap["ESTADO_REGISTRO"] == "OCUPADO"].copy()
    print(f"   Solo OCUPADO: {int(snap_ocupado['CANTIDAD'].sum()):,} servidores")

    # Filtro estricto: solo trabajadores ACTIVOS (no pensionistas, no sobrevivientes,
    # no modalidad formativa, no reconocimientos honoríficos).
    # Coincide con la metodología pública de Impacta/MEF.
    print(f"   Tipos de registro: {snap_ocupado['DESC_TIPO_REGISTRO'].value_counts().to_dict()}")

    TIPOS_ACTIVOS = {"Activos", "Contrato Administrativo de Servicios"}
    activos = snap_ocupado[snap_ocupado["DESC_TIPO_REGISTRO"].isin(TIPOS_ACTIVOS)].copy()
    print(f"   Solo {TIPOS_ACTIVOS}: {int(activos['CANTIDAD'].sum()):,} servidores trabajando")

    # ──────── Helpers ────────
    def ingreso_promedio(g):
        """Ingreso mensual promedio ponderado por CANTIDAD."""
        ing_total = (g["ING_IMPONIBLE_PERM_MENSUAL"].fillna(0)
                     + g["ING_NO_IMPONIBLE_PERM_MENSUAL"].fillna(0)
                     + g["INCENTIVO_UNICO_MENSUAL"].fillna(0))
        peso = g["CANTIDAD"].fillna(0)
        total_pers = peso.sum()
        if total_pers == 0:
            return 0.0
        return float(ing_total.sum() / total_pers)

    # ──────── KPIs nacionales ────────
    total_serv = int(activos["CANTIDAD"].sum())
    ing_prom = ingreso_promedio(activos)
    costo_total = float(activos["COSTO_TOTAL_ANUAL"].fillna(0).sum())
    n_pliegos = int(activos["PLIEGO"].nunique())
    n_ue = int(activos["UNIDAD_EJECUTORA"].nunique())

    print(f"\n[3] KPIs nacionales (snapshot {latest}):")
    print(f"   • Total servidores activos: {total_serv:,}")
    print(f"   • Ingreso promedio mensual: S/ {ing_prom:,.0f}")
    print(f"   • Costo total anual (todos): S/ {costo_total/1e9:,.1f} mil millones")
    print(f"   • Pliegos: {n_pliegos:,}")
    print(f"   • Unidades ejecutoras: {n_ue:,}")

    # ──────── Régimen laboral ────────
    reg = (activos.groupby("DESC_REGIMEN_LABORAL")
                   .apply(lambda g: pd.Series({
                       "cantidad": int(g["CANTIDAD"].sum()),
                       "ing_prom": ingreso_promedio(g),
                   }))
                   .sort_values("cantidad", ascending=False))
    print(f"\n[4] Régimen laboral:")
    print(reg)

    # ──────── Sector ────────
    sector = (activos.groupby("SECTOR")
                      .apply(lambda g: pd.Series({
                          "cantidad": int(g["CANTIDAD"].sum()),
                          "ing_prom": ingreso_promedio(g),
                      }))
                      .sort_values("cantidad", ascending=False))
    print(f"\n[5] Top 12 sectores:")
    print(sector.head(12))

    # ──────── Grupo ocupacional ────────
    grupo = (activos.groupby("DESC_GRUPO_OCASIONAL")
                     .apply(lambda g: pd.Series({
                         "cantidad": int(g["CANTIDAD"].sum()),
                         "ing_prom": ingreso_promedio(g),
                     }))
                     .sort_values("ing_prom", ascending=False))
    print(f"\n[6] Top 15 grupos ocupacionales POR SALARIO:")
    print(grupo.head(15))

    # ──────── Pliegos top ────────
    pliego = (activos.groupby("PLIEGO")
                      .apply(lambda g: pd.Series({
                          "cantidad": int(g["CANTIDAD"].sum()),
                          "ing_prom": ingreso_promedio(g),
                      }))
                      .sort_values("cantidad", ascending=False))
    print(f"\n[7] Top 20 pliegos por # servidores:")
    print(pliego.head(20))

    # ──────── Nivel de gobierno ────────
    nivel = (activos.groupby("NIVEL")
                     .apply(lambda g: pd.Series({
                         "cantidad": int(g["CANTIDAD"].sum()),
                         "ing_prom": ingreso_promedio(g),
                     }))
                     .sort_values("cantidad", ascending=False))
    print(f"\n[8] Nivel de gobierno:")
    print(nivel)

    # ──────── Construir JSON output ────────
    def df_to_records(df, name_col="name", value_cols=None):
        if value_cols is None:
            value_cols = list(df.columns)
        records = []
        for idx, row in df.iterrows():
            r = {name_col: str(idx)}
            for c in value_cols:
                v = row[c]
                if isinstance(v, (int, float)) and pd.notna(v):
                    r[c] = float(v) if isinstance(v, float) else int(v)
                else:
                    r[c] = str(v) if pd.notna(v) else None
            records.append(r)
        return records

    output = {
        "fuente": "MEF — Aplicativo Informático para el Registro Centralizado de Planillas (AIRHSP)",
        "fuente_url": "https://www.datosabiertos.gob.pe/dataset/personal-activo-y-pensionista-del-sector-p%C3%BAblico-registrado-en-el-airhsp",
        "csv_url": "https://fs.datosabiertos.mef.gob.pe/datastorefiles/PERSONALSP_2025.csv",
        "periodo": latest,
        "kpis": {
            "total_servidores": total_serv,
            "ingreso_promedio_mensual": round(ing_prom, 2),
            "costo_total_anual": round(costo_total, 2),
            "n_pliegos": n_pliegos,
            "n_unidades_ejecutoras": n_ue,
        },
        "por_regimen": df_to_records(reg, "regimen"),
        "por_sector": df_to_records(sector, "sector"),
        "por_grupo_ocupacional": df_to_records(grupo, "grupo"),
        "top_pliegos": df_to_records(pliego.head(30), "pliego"),
        "por_nivel": df_to_records(nivel, "nivel"),
    }

    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\n✓ Agregados escritos en {OUT.relative_to(ROOT)} ({OUT.stat().st_size/1024:.0f} KB)")

    # Inyectar en docs/estado.html
    estado = ROOT / "docs" / "estado.html"
    if estado.exists():
        html = estado.read_text()
        # Versión compacta del JSON para embeber
        payload = json.dumps(output, ensure_ascii=False, separators=(",", ":"))
        # Sanitizar contra cierre de script
        payload = payload.replace("</", "<\\/")
        import re as _re
        pat = _re.compile(
            r'(<script\s+id="airhsp-data"[^>]*>)([\s\S]*?)(</script>)',
            _re.IGNORECASE
        )
        new_html, n = pat.subn(rf"\g<1>{payload}\g<3>", html)
        if n:
            estado.write_text(new_html)
            print(f"✓ Patcheado docs/estado.html con payload ({len(payload)/1024:.0f} KB)")
        else:
            print("  ⚠ no se encontró el bloque <script id='airhsp-data'> en estado.html")
    else:
        print(f"  ⚠ {estado} no existe; se omite el patch")

    return 0


if __name__ == "__main__":
    sys.exit(main())
