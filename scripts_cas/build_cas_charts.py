#!/usr/bin/env python3
"""
Regenera los 7 charts CAS encriptados de docs/index.html a partir de
salariosperu-data/cas_vigentes.csv. Idempotente.

Conserva layout/config/titles existentes; solo reemplaza el blob cifrado
(data de Plotly) y actualiza los contadores visibles en texto.

Uso:
  ./venv/bin/python scripts_cas/build_cas_charts.py
"""
import base64
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "docs" / "index.html"
CSV = Path("/Users/unimauro/salariosperu-data/cas_vigentes.csv")
KEY = bytes.fromhex("5a6c3d8e9f1b2a4c7e8d5f3a2b1c0e9d")

# ───────────────────── CLASIFICADORES ─────────────────────

# Roles granulares (chart-cas-roles, 17 keywords)
ROLES_17 = [
    "Médico", "Especialista", "Ingeniero", "Coordinador", "Analista",
    "Profesional", "Abogado", "Psicólogo", "Jefe", "Gerente",
    "Enfermero", "Asistente", "Operador", "Técnico", "Auxiliar",
    "Chofer", "Secretario",
]

# Categorías de rol para heatmap (7)
ROL_CATS_7 = ["Especialista", "Coordinador", "Profesional", "Analista",
              "Asistente", "Técnico", "Auxiliar"]

# Niveles para box plots (6)  — (label, color, keywords)
NIVELES_6 = [
    ("Gerente/Jefe",     "#e74c3c", ["gerente", "jefe", "director", "subgerente", "sub gerente"]),
    ("Coordinador/Esp.", "#e67e22", ["coordinador", "especialista", "supervisor"]),
    ("Profesional",      "#f39c12", ["profesional", "médico", "medico", "abogado", "psicólogo",
                                     "psicologo", "ingeniero", "enfermer", "arquitect", "contador",
                                     "economista", "biólog", "biolog"]),
    ("Asistente",        "#27ae60", ["asistente", "analista", "ejecutivo"]),
    ("Técnico",          "#3498db", ["técnico", "tecnico", "operador", "chofer"]),
    ("Auxiliar/Apoyo",   "#9b59b6", ["auxiliar", "apoyo", "secretario", "secretaria", "asistencial"]),
]

# Tipos de institución (10 categorías para treemap/burbujas; el heatmap usa 9 sin "Otros")
TIPO_INST_RULES = [
    ("Ministerios",          ["ministerio"]),
    ("Gobiernos Regionales", ["gobierno regional", "gore "]),
    ("Salud / Hospitales",   ["hospital", "red de salud", "essalud", "instituto nacional de salud",
                              "instituto nacional materno", "inen", "insn"]),
    ("Justicia",             ["poder judicial", "fiscal", "tribunal", "corte superior",
                              "inpe", "academia de la magistratura"]),
    ("Municipalidades",      ["municipalidad", "municipio"]),
    ("Educación",            ["universidad", "escuela", "instituto pedagógico",
                              "instituto tecnológico", "minedu", "pronabec", "sineace", "peip"]),
    ("Programas Sociales",   ["inabif", "midis", "qali warma", "cuna más", "cuna mas",
                              "pensión 65", "pension 65", "juntos"]),
    ("Sup. y Fiscalización", ["sunat", "sunafil", "sunarp", "sbs", "indecopi", "osce",
                              "osinergmin", "osiptel", "sutran", "contraloría", "contraloria"]),
    ("Identidad / Civil",    ["reniec", "migraciones", "registro nacional"]),
]


def classify_rol_17(puesto):
    p = (puesto or "").lower()
    for r in ROLES_17:
        if r.lower() in p:
            return r
    return None


def classify_rol_cat(puesto):
    p = (puesto or "").lower()
    if "especialista" in p: return "Especialista"
    if "coordinador" in p:  return "Coordinador"
    if "analista" in p:     return "Analista"
    if "profesional" in p:  return "Profesional"
    if "asistente" in p:    return "Asistente"
    if "auxiliar" in p:     return "Auxiliar"
    if "técnico" in p or "tecnico" in p: return "Técnico"
    return None


def classify_nivel(puesto):
    p = (puesto or "").lower()
    for label, color, kws in NIVELES_6:
        for kw in kws:
            if kw in p:
                return label
    return None


def classify_tipo_inst(inst):
    e = (inst or "").lower()
    for label, kws in TIPO_INST_RULES:
        for kw in kws:
            if kw in e:
                return label
    return "Otros"


# ───────────────────── CHART BUILDERS ─────────────────────

PLOTLY_CONFIG = {
    "responsive": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

def build_distribucion(df_sal):
    return [{
        "type": "histogram",
        "x": [float(s) for s in df_sal["salario"]],
        "marker": {"color": "#3498db", "line": {"color": "white", "width": 1}},
        "nbinsx": 30,
        "hovertemplate": "Salario: S/ %{x:,.0f}<br>Convocatorias: %{y}<extra></extra>",
    }]


def build_roles(df_sal):
    sub = df_sal[df_sal["rol_granular"].notna()].copy()
    grouped = sub.groupby("rol_granular")["salario"].median().sort_values()
    return [{
        "type": "bar",
        "orientation": "h",
        "x": [float(v) for v in grouped.values],
        "y": list(grouped.index),
        "marker": {"color": [float(v) for v in grouped.values],
                   "colorscale": "Viridis",
                   "showscale": False,
                   "line": {"color": "white", "width": 1}},
        "text": [f"S/ {v:,.0f}" for v in grouped.values],
        "textposition": "outside",
        "hovertemplate": "<b>%{y}</b><br>Mediana: S/ %{x:,.0f}<extra></extra>",
    }]


def build_instituciones(df_all):
    counts = df_all["institucion"].value_counts().head(20).sort_values()
    return [{
        "type": "bar",
        "orientation": "h",
        "x": [int(v) for v in counts.values],
        "y": list(counts.index),
        "marker": {"color": "#1abc9c", "line": {"color": "white", "width": 1}},
        "text": [str(int(v)) for v in counts.values],
        "textposition": "outside",
        "hovertemplate": "<b>%{y}</b><br>Convocatorias: %{x}<extra></extra>",
    }]


def build_heatmap(df_sal):
    """9 instituciones (sin 'Otros') × 7 roles. z = mediana salario."""
    inst_order = ["Ministerios", "Gobiernos Regionales", "Salud / Hospitales",
                  "Justicia", "Educación", "Municipalidades",
                  "Programas Sociales", "Sup. y Fiscalización", "Identidad / Civil"]
    cats = ROL_CATS_7
    sub = df_sal[df_sal["rol_cat"].notna() & (df_sal["tipo_inst"] != "Otros")].copy()
    z = []
    for inst in inst_order:
        row = []
        for cat in cats:
            cell = sub[(sub["tipo_inst"] == inst) & (sub["rol_cat"] == cat)]
            row.append(float(cell["salario"].median()) if len(cell) >= 2 else None)
        z.append(row)
    return [{
        "type": "heatmap",
        "x": cats,
        "y": inst_order,
        "z": z,
        "colorscale": "Viridis",
        "hoverongaps": False,
        "hovertemplate": "%{y} × %{x}<br>Mediana: S/ %{z:,.0f}<extra></extra>",
        "colorbar": {"title": "S/", "thickness": 12},
    }]


def build_treemap(df_all, df_sal):
    """Top 10 tipo_inst + top instituciones (hasta ~50 leaf)."""
    # Mediana por institucion (para color) y count (para size)
    inst_count = df_all.groupby("institucion").size()
    inst_med = df_sal.groupby("institucion")["salario"].median()
    inst_tipo = df_all.groupby("institucion")["tipo_inst"].agg(lambda s: s.value_counts().index[0])

    # Top 50 instituciones por count
    top_inst = inst_count.sort_values(ascending=False).head(50)

    tipo_order = ["Educación", "Gobiernos Regionales", "Ministerios",
                  "Sup. y Fiscalización", "Identidad / Civil", "Otros",
                  "Salud / Hospitales", "Municipalidades", "Justicia",
                  "Programas Sociales"]

    labels, parents, values, colors, texts = [], [], [], [], []
    for t in tipo_order:
        labels.append(t); parents.append(""); values.append(0)
        colors.append(0); texts.append("")

    for inst, cnt in top_inst.items():
        labels.append(inst)
        parents.append(inst_tipo.get(inst, "Otros"))
        values.append(int(cnt))
        med = inst_med.get(inst)
        colors.append(float(med) if pd.notna(med) else 0)
        texts.append(f"S/ {med:,.0f}" if pd.notna(med) else "—")

    return [{
        "type": "treemap",
        "labels": labels,
        "parents": parents,
        "values": values,
        "marker": {"colors": colors, "colorscale": "Viridis", "showscale": True,
                   "colorbar": {"title": "S/ med.", "thickness": 12}},
        "text": texts,
        "textinfo": "label+value+text",
        "hovertemplate": "<b>%{label}</b><br>Convocatorias: %{value}<br>%{text}<extra></extra>",
        "textfont": {"size": 12},
    }]


def build_burbujas(df_sal):
    """10 traces (uno por tipo_inst). x = mean salario, y = count, size = count."""
    traces = []
    tipos = sorted(df_sal["tipo_inst"].dropna().unique())
    palette = ["#3498db", "#e74c3c", "#27ae60", "#f39c12", "#9b59b6",
               "#1abc9c", "#e67e22", "#34495e", "#16a085", "#c0392b"]
    for i, tipo in enumerate(tipos):
        sub = df_sal[df_sal["tipo_inst"] == tipo]
        per_inst = sub.groupby("institucion").agg(
            x=("salario", "mean"),
            y=("salario", "count"),
        ).sort_values("y", ascending=False).head(30)  # cap por categoría
        if len(per_inst) == 0:
            continue
        sizes = [max(8, min(40, int(c * 1.5))) for c in per_inst["y"]]
        traces.append({
            "type": "scatter",
            "mode": "markers",
            "name": tipo,
            "x": [round(float(v), 0) for v in per_inst["x"]],
            "y": [int(v) for v in per_inst["y"]],
            "text": list(per_inst.index),
            "customdata": [[int(c)] for c in per_inst["y"]],
            "marker": {"size": sizes, "opacity": 0.75,
                       "color": palette[i % len(palette)],
                       "line": {"width": 1.5, "color": "white"}},
            "hovertemplate": ("<b>%{text}</b><br>" + tipo +
                              "<br>Salario prom: S/ %{x:,.0f}<br>Convocatorias: %{y}<extra></extra>"),
        })
    return traces


def build_niveles(df_sal):
    traces = []
    for label, color, _kws in NIVELES_6:
        sub = df_sal[df_sal["nivel"] == label]
        if len(sub) < 2:
            continue
        traces.append({
            "type": "box",
            "name": f"{label} (n={len(sub)})",
            "y": [float(s) for s in sub["salario"]],
            "marker": {"color": color},
            "boxmean": True,
            "hovertemplate": label + "<br>S/ %{y:,.0f}<extra></extra>",
        })
    return traces


# ───────────────────── HTML PATCHING ─────────────────────

def encrypt(data):
    nonce = os.urandom(12)
    ct = AESGCM(KEY).encrypt(nonce, json.dumps(data, ensure_ascii=False).encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("ascii")


def patch_chart(html, chart_id, data):
    """Reemplaza el blob cifrado del chart_id en plotlyEnc(...)."""
    new_b64 = encrypt(data)
    pattern = re.compile(rf'(plotlyEnc\("{re.escape(chart_id)}",\s*")[^"]+(")')
    new_html, n = pattern.subn(rf'\g<1>{new_b64}\g<2>', html)
    return new_html, n


def update_counters(html, total, total_sal):
    """Actualiza '1,194' y '1,193' (cuenta vieja → cuenta nueva)."""
    # Hacer match en numeros 1,194 / 1194 y 1,193 / 1193 (en contexto CAS)
    replacements = 0
    # Más conservador: solo en pasajes con "CAS" o "convocatoria" cerca
    new_html = html
    for old, new in [("1,194", f"{total:,}"), ("1194", f"{total:,}"),
                     ("1,193", f"{total_sal:,}"), ("1193", f"{total_sal:,}")]:
        new_html2, n = re.subn(re.escape(old), new, new_html)
        new_html = new_html2
        replacements += n
    return new_html, replacements


SPANISH_MONTHS = {1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
                  7: "jul", 8: "ago", 9: "set", 10: "oct", 11: "nov", 12: "dic"}


def format_fecha(iso_str):
    """'2026-05-28T03:39:48' → '28-may-2026'."""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(str(iso_str))
        return f"{dt.day:02d}-{SPANISH_MONTHS[dt.month]}-{dt.year}"
    except (ValueError, TypeError):
        return str(iso_str)[:10] if iso_str else "—"


def build_search_payload(df):
    """Construye el array JSON para el buscador CAS.
    Campos cortos para reducir tamaño: i=institucion, p=puesto,
    d=departamento, s=salario, f=fecha_limite, u=url."""
    out = []
    for _, r in df.iterrows():
        salario = r.get("salario")
        try:
            salario = int(salario) if pd.notna(salario) and float(salario) > 0 else None
        except (ValueError, TypeError):
            salario = None
        out.append({
            "i": str(r.get("institucion", "") or "")[:120],
            "p": str(r.get("puesto", "") or "")[:200],
            "d": str(r.get("departamento", "") or "")[:60],
            "s": salario,
            "f": str(r.get("fecha_limite", "") or ""),
            "u": str(r.get("url", "") or ""),
        })
    # Orden por salario desc para que el primer render sea útil incluso si JS tarda
    out.sort(key=lambda x: (x["s"] is None, -(x["s"] or 0)))
    return out


def patch_search_data(html, payload):
    """Reemplaza el contenido del <script id=cas-buscar-data>...</script>."""
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # Sanitizar contra cierre de script
    body = body.replace("</", "<\\/")
    pat = re.compile(
        r'(<script\s+id="cas-buscar-data"[^>]*>)([\s\S]*?)(</script>)',
        re.IGNORECASE
    )
    new_html, n = pat.subn(rf"\g<1>{body}\g<3>", html)
    return new_html, n, len(body)


def update_actualizado(html, fecha):
    """Reemplaza 'actualizado diario' por la fecha real del scrape.
    Idempotente: si ya está reemplazado con un patrón 'actualizado al', el
    primer pase no encuentra match y se hace un segundo barrido con regex."""
    repls = [
        ("(actualizado diario)",                            f"(actualizado al {fecha})"),
        ("actualizado diario vía GitHub Actions",           f"actualizado al {fecha} vía GitHub Actions"),
        ("actualizado diario v&iacute;a GitHub Actions",    f"actualizado al {fecha} v&iacute;a GitHub Actions"),
        ("actualizado diario por GitHub Actions",           f"actualizado al {fecha} por GitHub Actions"),
        ("actualizadas a diario",                           f"actualizadas al {fecha}"),
    ]
    n_total = 0
    for old, new in repls:
        html, n = re.subn(re.escape(old), new, html)
        n_total += n
    # Segundo barrido: si en una corrida previa ya quedó 'actualizado al <fecha vieja>',
    # lo refrescamos a la fecha nueva.
    html, n2 = re.subn(r"actualizado al \d{2}-[a-z]{3}-\d{4}", f"actualizado al {fecha}", html)
    html, n3 = re.subn(r"actualizadas al \d{2}-[a-z]{3}-\d{4}", f"actualizadas al {fecha}", html)
    return html, n_total + n2 + n3


def main():
    if not CSV.exists():
        print(f"ERROR: {CSV} no existe", file=sys.stderr)
        return 1

    print(f"[1/3] Leyendo {CSV.name} …")
    df = pd.read_csv(CSV)
    df["salario"] = pd.to_numeric(df["salario"], errors="coerce")
    df["tipo_inst"] = df["institucion"].apply(classify_tipo_inst)

    sal = df[df["salario"].notna() & (df["salario"] > 100)].copy()
    sal["nivel"]         = sal["puesto"].apply(classify_nivel)
    sal["rol_granular"]  = sal["puesto"].apply(classify_rol_17)
    sal["rol_cat"]       = sal["puesto"].apply(classify_rol_cat)

    total, total_sal = len(df), len(sal)
    print(f"   Total: {total}  ·  con salario válido: {total_sal}")
    print(f"   tipo_inst: {dict(df['tipo_inst'].value_counts())}")
    print(f"   nivel asignado: {sal['nivel'].notna().sum()}/{total_sal}")

    print("[2/3] Generando charts …")
    charts = {
        "chart-cas-distribucion":  build_distribucion(sal),
        "chart-cas-roles":         build_roles(sal),
        "chart-cas-instituciones": build_instituciones(df),
        "chart-cas-heatmap":       build_heatmap(sal),
        "chart-cas-treemap":       build_treemap(df, sal),
        "chart-cas-burbujas":      build_burbujas(sal),
        "chart-cas-niveles":       build_niveles(sal),
    }

    print("[3/3] Patcheando docs/index.html …")
    html = HTML.read_text()

    patched_count = 0
    for cid, data in charts.items():
        html, n = patch_chart(html, cid, data)
        patched_count += n
        n_traces = len(data) if isinstance(data, list) else 1
        print(f"   ✓ {cid}: {n_traces} trace(s), reemplazos={n}")

    html, n_counters = update_counters(html, total, total_sal)
    print(f"   ✓ Contadores actualizados: {n_counters} reemplazos (1,194→{total:,}, 1,193→{total_sal:,})")

    # Fecha de última extracción (del primer row del CSV)
    fecha_raw = df["fecha_extraccion"].iloc[0] if len(df) else None
    fecha = format_fecha(fecha_raw)
    html, n_fecha = update_actualizado(html, fecha)
    print(f"   ✓ Fecha del scrape actualizada: {fecha} ({n_fecha} reemplazos)")

    # Buscador CAS: payload JSON embebido
    payload = build_search_payload(df)
    html, n_search, payload_bytes = patch_search_data(html, payload)
    print(f"   ✓ Buscador CAS: {len(payload):,} filas · {payload_bytes/1024:.0f} KB · {n_search} bloque(s)")

    HTML.write_text(html)
    print(f"\nListo. docs/index.html escrito ({patched_count} charts patcheados).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
