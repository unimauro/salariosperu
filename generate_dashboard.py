#!/usr/bin/env python3
"""
Genera reportes HTML interactivos con Plotly para el dashboard de SalariosPerú.
Lee datos del CSV generado por el scraper y produce charts embebibles.
"""

import pandas as pd
import json
import re

# ========== CLASIFICADORES ==========

def classify_level(puesto):
    p = str(puesto).lower()
    if any(w in p for w in ['ceo', 'chief', 'gerente general', 'presidente', 'vp ejecutivo']):
        return 'C-Level'
    if any(w in p for w in ['vp ', 'vice president', 'director', 'managing director']):
        return 'VP / Director'
    if any(w in p for w in ['gerente', 'manager', 'head of', 'lead']):
        return 'Gerente'
    if any(w in p for w in ['subgerente', 'sub gerente', 'jefe', 'superintendent', 'supervisor']):
        return 'Jefe / Subgerente'
    if any(w in p for w in ['senior', 'sr ', 'sr.', 'specialist', 'especialista']):
        return 'Senior'
    if any(w in p for w in ['analista', 'analyst', 'ejecutivo', 'consultant', 'consultor']):
        return 'Analista'
    if any(w in p for w in ['asistente', 'assistant', 'trainee', 'practicante', 'junior', 'jr']):
        return 'Junior'
    return 'Otros'


def classify_sector(empresa):
    e = str(empresa).lower()
    if any(w in e for w in ['banco', 'bcp', 'interbank', 'bbva', 'scotiabank', 'mibanco', 'banbif', 'credicorp', 'financier', 'pichincha']):
        return 'Banca'
    if any(w in e for w in ['seguro', 'rimac', 'pacifico', 'mapfre', 'interseguro', 'positiva']):
        return 'Seguros'
    if any(w in e for w in ['minera', 'minsur', 'antamina', 'glencore', 'southern', 'cerro verde', 'brocal', 'buenaventura', 'shougang', 'nexa']):
        return 'Mineria'
    if any(w in e for w in ['alicorp', 'nestle', 'backus', 'inbev', 'gloria', 'san fernando', 'mondelez', 'pepsico', 'ajinomoto']):
        return 'Consumo Masivo'
    if any(w in e for w in ['deloitte', 'ey', 'ernst', 'pwc', 'kpmg', 'mckinsey', 'bcg', 'boston', 'accenture', 'management solutions']):
        return 'Consultoria'
    if any(w in e for w in ['culqi', 'yape', 'rappi', 'izipay', 'kushki', 'vtex', 'crehana', 'jokr', 'pedidosya', 'despegar']):
        return 'Fintech / Tech'
    if any(w in e for w in ['loreal', 'belcorp', 'yanbal', 'procter', 'colgate', 'kimberly', 'reckitt', 'estee']):
        return 'Cosmeticos'
    if any(w in e for w in ['falabella', 'ripley', 'sodimac', 'tottus', 'hiraoka', 'oxxo', 'makro', 'plaza vea', 'cencosud']):
        return 'Retail'
    if any(w in e for w in ['entel', 'telefonica', 'claro', 'bitel', 'movistar']):
        return 'Telecom'
    if any(w in e for w in ['latam', 'ransa', 'dp world', 'sky airline', 'talma', 'dhl']):
        return 'Logistica'
    return 'Otros'


# ========== CHART GENERATORS ==========

def plotly_config():
    """Config comun para todos los charts"""
    return {
        "responsive": True,
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "displaylogo": False
    }


def generate_salary_by_level(df):
    """Chart: Salario por nivel jerarquico (violin/box)"""
    level_order = ['C-Level', 'VP / Director', 'Gerente', 'Jefe / Subgerente', 'Senior', 'Analista', 'Junior']
    colors = ['#e74c3c', '#e67e22', '#f39c12', '#27ae60', '#3498db', '#9b59b6', '#1abc9c']

    traces = []
    for i, level in enumerate(level_order):
        subset = df[df['nivel'] == level]
        if len(subset) < 2:
            continue
        traces.append({
            "type": "box",
            "y": subset['salario_promedio'].tolist(),
            "name": level,
            "marker": {"color": colors[i % len(colors)]},
            "boxmean": True,
            "hoverinfo": "y+name"
        })

    layout = {
        "title": {"text": "Distribucion Salarial por Nivel Jerarquico<br><sub>Box plot con promedio (rombo) y mediana (linea)</sub>", "x": 0.5},
        "yaxis": {"title": "Salario Mensual (S/)", "tickformat": ",.0f", "gridcolor": "#f0f0f0"},
        "xaxis": {"title": ""},
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "height": 500,
        "margin": {"l": 80, "r": 30, "t": 70, "b": 60},
        "showlegend": False
    }

    return traces, layout


def generate_sector_comparison(df):
    """Chart: Comparativa de salarios por sector (barras horizontales)"""
    by_sector = df.groupby('sector')['salario_promedio'].agg(['median', 'mean', 'count'])
    by_sector = by_sector[by_sector['count'] >= 5].sort_values('median', ascending=True)

    colors_map = {
        'Mineria': '#f39c12', 'Cosmeticos': '#e91e8c', 'Consultoria': '#2c3e50',
        'Fintech / Tech': '#3498db', 'Banca': '#27ae60', 'Consumo Masivo': '#e67e22',
        'Seguros': '#8e44ad', 'Telecom': '#16a085', 'Retail': '#d35400',
        'Logistica': '#2980b9', 'Otros': '#95a5a6'
    }
    bar_colors = [colors_map.get(s, '#95a5a6') for s in by_sector.index]

    traces = [
        {
            "type": "bar",
            "y": by_sector.index.tolist(),
            "x": by_sector['median'].tolist(),
            "orientation": "h",
            "name": "Mediana",
            "marker": {"color": bar_colors, "line": {"width": 0}},
            "text": [f"S/ {v:,.0f} ({int(c)} puestos)" for v, c in zip(by_sector['median'], by_sector['count'])],
            "textposition": "auto",
            "hovertemplate": "%{y}<br>Mediana: S/ %{x:,.0f}<extra></extra>"
        }
    ]

    layout = {
        "title": {"text": "Mediana Salarial por Sector<br><sub>Basado en puestos con salario reportado</sub>", "x": 0.5},
        "xaxis": {"title": "Salario Mediana (S/)", "tickformat": ",.0f", "gridcolor": "#f0f0f0"},
        "yaxis": {"title": "", "automargin": True},
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "height": 450,
        "margin": {"l": 130, "r": 30, "t": 70, "b": 50},
        "showlegend": False
    }

    return traces, layout


def generate_top_companies(df):
    """Chart: Top empresas por salario mediano"""
    empresa_stats = df.groupby('empresa')['salario_promedio'].agg(['median', 'count'])
    top = empresa_stats[empresa_stats['count'] >= 5].sort_values('median', ascending=True).tail(15)

    # Color gradient
    n = len(top)
    colors = [f'rgba(52, 152, 219, {0.4 + 0.6 * i / n})' for i in range(n)]

    traces = [{
        "type": "bar",
        "y": [name[:30] for name in top.index.tolist()],
        "x": top['median'].tolist(),
        "orientation": "h",
        "marker": {"color": colors, "line": {"width": 0}},
        "text": [f"S/ {v:,.0f} ({int(c)})" for v, c in zip(top['median'], top['count'])],
        "textposition": "auto",
        "hovertemplate": "%{y}<br>Mediana: S/ %{x:,.0f}<extra></extra>"
    }]

    layout = {
        "title": {"text": "Top 15 Empresas Mejor Pagadas<br><sub>Por salario mediano (min. 5 puestos reportados)</sub>", "x": 0.5},
        "xaxis": {"title": "Salario Mediana (S/)", "tickformat": ",.0f", "gridcolor": "#f0f0f0"},
        "yaxis": {"automargin": True},
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "height": 500,
        "margin": {"l": 180, "r": 30, "t": 70, "b": 50},
        "showlegend": False
    }

    return traces, layout


def generate_salary_distribution(df):
    """Chart: Histograma de distribucion salarial"""
    salarios = df['salario_promedio'].dropna()
    # Cap at 50K for better visualization
    salarios_capped = salarios[salarios <= 50000]

    traces = [{
        "type": "histogram",
        "x": salarios_capped.tolist(),
        "nbinsx": 30,
        "marker": {
            "color": "rgba(52, 152, 219, 0.7)",
            "line": {"color": "rgba(52, 152, 219, 1)", "width": 1}
        },
        "hovertemplate": "Rango: S/ %{x:,.0f}<br>Puestos: %{y}<extra></extra>"
    }]

    # Add median and mean lines
    median_val = salarios.median()
    mean_val = salarios.mean()

    layout = {
        "title": {"text": "Distribucion de Salarios en Peru<br><sub>Frecuencia de rangos salariales (hasta S/ 50,000)</sub>", "x": 0.5},
        "xaxis": {"title": "Salario Mensual (S/)", "tickformat": ",.0f", "gridcolor": "#f0f0f0"},
        "yaxis": {"title": "Cantidad de Puestos", "gridcolor": "#f0f0f0"},
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "height": 400,
        "margin": {"l": 60, "r": 30, "t": 70, "b": 50},
        "shapes": [
            {"type": "line", "x0": median_val, "x1": median_val, "y0": 0, "y1": 1, "yref": "paper",
             "line": {"color": "#e74c3c", "width": 2, "dash": "dash"}},
            {"type": "line", "x0": mean_val, "x1": mean_val, "y0": 0, "y1": 1, "yref": "paper",
             "line": {"color": "#f39c12", "width": 2, "dash": "dash"}}
        ],
        "annotations": [
            {"x": median_val, "y": 1, "yref": "paper", "text": f"Mediana: S/ {median_val:,.0f}",
             "showarrow": False, "font": {"color": "#e74c3c", "size": 11}, "yshift": 10},
            {"x": mean_val, "y": 0.92, "yref": "paper", "text": f"Promedio: S/ {mean_val:,.0f}",
             "showarrow": False, "font": {"color": "#f39c12", "size": 11}, "yshift": 10}
        ]
    }

    return traces, layout


def generate_treemap_empresas(df):
    """Chart: Treemap de empresas por cantidad de puestos y salario"""
    empresa_stats = df.groupby('empresa').agg(
        count=('puesto', 'count'),
        median_sal=('salario_promedio', 'median')
    ).reset_index()
    empresa_stats = empresa_stats[empresa_stats['count'] >= 3].nlargest(30, 'count')
    empresa_stats['sector'] = empresa_stats['empresa'].apply(classify_sector)

    labels = empresa_stats['empresa'].str[:25].tolist()
    parents = empresa_stats['sector'].tolist()
    values = empresa_stats['count'].tolist()
    colors = empresa_stats['median_sal'].tolist()
    text = [f"S/ {s:,.0f} mediana<br>{c} puestos" if pd.notna(s) else f"{c} puestos"
            for s, c in zip(empresa_stats['median_sal'], empresa_stats['count'])]

    # Add sector parents
    sectors = list(set(parents))
    all_labels = sectors + labels
    all_parents = [""] * len(sectors) + parents
    all_values = [0] * len(sectors) + values
    all_colors = [0] * len(sectors) + colors
    all_text = [""] * len(sectors) + text

    traces = [{
        "type": "treemap",
        "labels": all_labels,
        "parents": all_parents,
        "values": all_values,
        "marker": {
            "colors": all_colors,
            "colorscale": "Blues",
            "showscale": True,
            "colorbar": {"title": "Mediana S/", "tickformat": ",.0f"}
        },
        "text": all_text,
        "textinfo": "label+text",
        "hovertemplate": "%{label}<br>%{text}<extra></extra>",
        "textfont": {"size": 12}
    }]

    layout = {
        "title": {"text": "Mapa de Empresas: Tamano = Puestos, Color = Salario Mediano<br><sub>Top 30 empresas con mas posiciones reportadas</sub>", "x": 0.5},
        "paper_bgcolor": "white",
        "height": 550,
        "margin": {"l": 10, "r": 10, "t": 70, "b": 10}
    }

    return traces, layout


def generate_level_vs_sector_heatmap(df):
    """Chart: Heatmap nivel vs sector"""
    level_order = ['C-Level', 'VP / Director', 'Gerente', 'Jefe / Subgerente', 'Senior', 'Analista', 'Junior']
    sectors = df.groupby('sector')['salario_promedio'].median().sort_values(ascending=False).index.tolist()
    sectors = [s for s in sectors if s != 'Otros'][:8]

    z = []
    hover_text = []
    for level in level_order:
        row = []
        hover_row = []
        for sector in sectors:
            subset = df[(df['nivel'] == level) & (df['sector'] == sector)]
            if len(subset) >= 2:
                med = subset['salario_promedio'].median()
                row.append(med)
                hover_row.append(f"{level} en {sector}<br>Mediana: S/ {med:,.0f}<br>{len(subset)} puestos")
            else:
                row.append(None)
                hover_row.append(f"{level} en {sector}<br>Sin datos suficientes")
        z.append(row)
        hover_text.append(hover_row)

    traces = [{
        "type": "heatmap",
        "z": z,
        "x": sectors,
        "y": level_order,
        "colorscale": "YlOrRd",
        "text": hover_text,
        "hoverinfo": "text",
        "colorbar": {"title": "Mediana S/", "tickformat": ",.0f"},
        "zmin": 2000,
        "zmax": 80000
    }]

    layout = {
        "title": {"text": "Salario por Nivel y Sector<br><sub>Mediana salarial (S/) - Mas oscuro = mejor pagado</sub>", "x": 0.5},
        "xaxis": {"title": "", "tickangle": -30},
        "yaxis": {"title": "", "autorange": "reversed"},
        "paper_bgcolor": "white",
        "height": 450,
        "margin": {"l": 120, "r": 30, "t": 70, "b": 80}
    }

    return traces, layout


# ========== HTML GENERATOR ==========

def chart_to_html(div_id, traces, layout, config=None):
    """Genera el HTML de un chart Plotly embebido"""
    if config is None:
        config = plotly_config()
    traces_json = json.dumps(traces, ensure_ascii=False)
    layout_json = json.dumps(layout, ensure_ascii=False)
    config_json = json.dumps(config, ensure_ascii=False)

    return f'''<div id="{div_id}" class="plotly-graph-div" style="height:{layout.get("height", 500)}px; width:100%;"></div>
<script>
if(document.getElementById("{div_id}")){{
    Plotly.newPlot("{div_id}",{traces_json},{layout_json},{config_json});
}}
</script>'''


def main():
    print("Generando reportes del dashboard...")

    df = pd.read_csv('salarios_completo.csv')
    valid = df[df['salario_promedio'].notna() & (df['salario_promedio'] > 100)].copy()
    valid['nivel'] = valid['puesto'].apply(classify_level)
    valid['sector'] = valid['empresa'].apply(classify_sector)

    charts = {}

    # 1. Distribucion de salarios
    t, l = generate_salary_distribution(valid)
    charts['distribucion'] = chart_to_html('chart-distribucion', t, l)

    # 2. Salario por nivel
    t, l = generate_salary_by_level(valid)
    charts['niveles'] = chart_to_html('chart-niveles', t, l)

    # 3. Sector comparison
    t, l = generate_sector_comparison(valid)
    charts['sectores'] = chart_to_html('chart-sectores', t, l)

    # 4. Top empresas
    t, l = generate_top_companies(valid)
    charts['top_empresas'] = chart_to_html('chart-top-empresas', t, l)

    # 5. Treemap
    t, l = generate_treemap_empresas(valid)
    charts['treemap'] = chart_to_html('chart-treemap', t, l)

    # 6. Heatmap nivel x sector
    t, l = generate_level_vs_sector_heatmap(valid)
    charts['heatmap'] = chart_to_html('chart-heatmap', t, l)

    # Save individual charts
    for name, html in charts.items():
        with open(f'docs/chart_{name}.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  Generado: docs/chart_{name}.html")

    # Generate combined snippet for embedding
    with open('docs/charts_generated.html', 'w', encoding='utf-8') as f:
        for name, html in charts.items():
            f.write(f'<!-- {name} -->\n{html}\n\n')

    print(f"\nTotal: {len(charts)} charts generados")
    print("Archivo combinado: docs/charts_generated.html")

    # Return charts dict for programmatic use
    return charts


if __name__ == "__main__":
    main()
