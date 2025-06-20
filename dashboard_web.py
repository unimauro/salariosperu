#!/usr/bin/env python3
"""
Generador de Dashboard Web Moderno para Salarios Perú
Crea una interfaz web interactiva con los análisis completos
"""

import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from datetime import datetime
from salarios_analyzer_simple import SalariosAnalyzerSimple
import glob

class DashboardWebGenerator:
    def __init__(self, data_source=None):
        """Inicializar el generador de dashboard web"""
        
        # Auto-detectar archivo de datos si no se especifica
        if data_source is None:
            csv_files = glob.glob("*.csv")
            if csv_files:
                completo_files = [f for f in csv_files if 'completo' in f]
                if completo_files:
                    data_source = max(completo_files, key=os.path.getsize)
                else:
                    data_source = max(csv_files, key=os.path.getsize)
            else:
                raise ValueError("No se encontraron archivos CSV")
        
        self.data_source = data_source
        self.analyzer = SalariosAnalyzerSimple(data_source)
        self.output_dir = "web_dashboard"
        
        # Crear directorio de salida
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"📊 Dashboard Web Generator inicializado")
        print(f"📁 Datos: {data_source}")
        print(f"📂 Salida: {self.output_dir}/")
    
    def generate_interactive_charts(self):
        """Genera gráficos interactivos con Plotly"""
        print("📈 Generando gráficos interactivos...")
        
        charts = {}
        df = self.analyzer.df
        
        # 1. Gráfico de barras: Top 15 empresas mejor pagadas
        empresa_stats = df.groupby('empresa').agg({
            'salario_promedio': 'mean',
            'puesto': 'count'
        }).round(2)
        empresa_stats = empresa_stats[empresa_stats['puesto'] >= 2]
        empresa_stats = empresa_stats.sort_values('salario_promedio', ascending=False).head(15)
        
        fig_empresas = px.bar(
            x=empresa_stats['salario_promedio'],
            y=empresa_stats.index,
            orientation='h',
            title='🏆 Top 15 Empresas Mejor Pagadas',
            labels={'x': 'Salario Promedio (S/)', 'y': 'Empresa'},
            color=empresa_stats['salario_promedio'],
            color_continuous_scale='viridis'
        )
        fig_empresas.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
        charts['empresas'] = fig_empresas.to_html(include_plotlyjs=True, div_id="chart-empresas")
        
        # 2. Gráfico de sectores
        sector_stats = df.groupby('sector')['salario_promedio'].mean().sort_values(ascending=False)
        
        fig_sectores = px.bar(
            x=sector_stats.index,
            y=sector_stats.values,
            title='🏭 Salario Promedio por Sector',
            labels={'x': 'Sector', 'y': 'Salario Promedio (S/)'},
            color=sector_stats.values,
            color_continuous_scale='plasma'
        )
        fig_sectores.update_layout(height=500, xaxis_tickangle=-45)
        charts['sectores'] = fig_sectores.to_html(include_plotlyjs=False, div_id="chart-sectores")
        
        # 3. Distribución de salarios (histograma)
        fig_distribucion = px.histogram(
            df, 
            x='salario_promedio',
            nbins=30,
            title='📊 Distribución de Salarios',
            labels={'x': 'Salario (S/)', 'y': 'Frecuencia'},
            color_discrete_sequence=['#636EFA']
        )
        fig_distribucion.update_layout(height=400)
        charts['distribucion'] = fig_distribucion.to_html(include_plotlyjs=False, div_id="chart-distribucion")
        
        # 4. Análisis por seniority
        def classify_seniority(puesto):
            puesto_lower = str(puesto).lower()
            senior_keywords = ['senior', 'sr', 'lead', 'principal', 'manager', 'gerente', 'director', 'chief', 'head']
            junior_keywords = ['junior', 'jr', 'trainee', 'intern', 'practicante', 'asistente', 'assistant']
            mid_keywords = ['analyst', 'analista', 'specialist', 'especialista', 'professional', 'officer', 'executive']
            
            if any(keyword in puesto_lower for keyword in senior_keywords):
                return 'Senior'
            elif any(keyword in puesto_lower for keyword in junior_keywords):
                return 'Junior'
            elif any(keyword in puesto_lower for keyword in mid_keywords):
                return 'Mid-Level'
            else:
                return 'Entry-Level'
        
        df['seniority_level'] = df['puesto'].apply(classify_seniority)
        seniority_stats = df.groupby('seniority_level')['salario_promedio'].mean().sort_values(ascending=False)
        
        fig_seniority = px.pie(
            values=seniority_stats.values,
            names=seniority_stats.index,
            title='📈 Salario Promedio por Nivel de Seniority',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_seniority.update_layout(height=400)
        charts['seniority'] = fig_seniority.to_html(include_plotlyjs=False, div_id="chart-seniority")
        
        # 5. Scatter plot: Salario vs Tamaño de empresa
        empresa_counts = df.groupby('empresa').size()
        df['empresa_size'] = df['empresa'].map(empresa_counts)
        
        # Datos agregados por empresa
        scatter_data = df.groupby(['empresa', 'sector']).agg({
            'salario_promedio': 'mean',
            'empresa_size': 'first'
        }).reset_index()
        
        fig_scatter = px.scatter(
            scatter_data,
            x='empresa_size',
            y='salario_promedio',
            color='sector',
            size='empresa_size',
            hover_name='empresa',
            title='💼 Salario vs Tamaño de Empresa por Sector',
            labels={'empresa_size': 'Número de Puestos', 'salario_promedio': 'Salario Promedio (S/)'}
        )
        fig_scatter.update_layout(height=500)
        charts['scatter'] = fig_scatter.to_html(include_plotlyjs=False, div_id="chart-scatter")
        
        return charts
    
    def generate_summary_stats(self):
        """Genera estadísticas de resumen"""
        df = self.analyzer.df
        
        stats = {
            'total_registros': len(df),
            'total_empresas': df['empresa'].nunique(),
            'total_puestos': df['puesto'].nunique(),
            'total_sectores': df['sector'].nunique(),
            'salario_promedio_general': round(df['salario_promedio'].mean(), 2),
            'salario_mediano': round(df['salario_promedio'].median(), 2),
            'salario_maximo': round(df['salario_promedio'].max(), 2),
            'salario_minimo': round(df['salario_promedio'].min(), 2),
            'ultima_actualizacion': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'archivo_datos': self.data_source
        }
        
        # Top 5 empresas y sectores
        stats['top_empresas'] = df.groupby('empresa')['salario_promedio'].mean().sort_values(ascending=False).head(5).round(2).to_dict()
        stats['top_sectores'] = df.groupby('sector')['salario_promedio'].mean().sort_values(ascending=False).head(5).round(2).to_dict()
        
        return stats
    
    def create_modern_dashboard(self):
        """Crea el dashboard web moderno"""
        print("🎨 Creando dashboard web moderno...")
        
        # Generar gráficos y estadísticas
        charts = self.generate_interactive_charts()
        stats = self.generate_summary_stats()
        
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Salarios Perú - Análisis Completo</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 1rem 0;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .logo {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .logo i {{
            font-size: 2rem;
            color: #667eea;
        }}
        
        .logo h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #333;
        }}
        
        .update-info {{
            font-size: 0.9rem;
            color: #666;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 2rem 0;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }}
        
        .stat-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        
        .stat-card.empresas .stat-icon {{ color: #ff6b6b; }}
        .stat-card.registros .stat-icon {{ color: #4ecdc4; }}
        .stat-card.salario .stat-icon {{ color: #45b7d1; }}
        .stat-card.sectores .stat-icon {{ color: #96ceb4; }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #333;
            margin-bottom: 0.5rem;
        }}
        
        .stat-label {{
            font-size: 1rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .charts-section {{
            margin: 3rem 0;
        }}
        
        .section-title {{
            text-align: center;
            margin-bottom: 2rem;
            color: white;
            font-size: 2rem;
            font-weight: 600;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
        }}
        
        .chart-container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        
        .chart-container:hover {{
            transform: translateY(-2px);
        }}
        
        .chart-full-width {{
            grid-column: 1 / -1;
        }}
        
        .top-lists {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 3rem 0;
        }}
        
        .top-list {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        
        .top-list h3 {{
            margin-bottom: 1.5rem;
            color: #333;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .top-item {{
            display: flex;
            justify-content: between;
            align-items: center;
            padding: 0.8rem 0;
            border-bottom: 1px solid #eee;
        }}
        
        .top-item:last-child {{
            border-bottom: none;
        }}
        
        .top-name {{
            font-weight: 600;
            color: #333;
            flex: 1;
        }}
        
        .top-value {{
            font-weight: 700;
            color: #667eea;
            font-size: 1.1rem;
        }}
        
        .footer {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            text-align: center;
            padding: 2rem;
            margin-top: 3rem;
            color: #666;
        }}
        
        .footer a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }}
        
        .footer a:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 0 15px;
            }}
            
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            }}
            
            .stat-card {{
                padding: 1.5rem;
            }}
            
            .stat-value {{
                font-size: 2rem;
            }}
        }}
        
        .loading {{
            display: none;
            text-align: center;
            padding: 2rem;
            color: white;
        }}
        
        .spinner {{
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 4px solid white;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo">
                    <i class="fas fa-chart-line"></i>
                    <h1>Salarios Perú - Dashboard Ejecutivo</h1>
                </div>
                <div class="update-info">
                    <i class="fas fa-clock"></i>
                    Actualizado: {stats['ultima_actualizacion']}
                </div>
            </div>
        </div>
    </header>

    <main class="container">
        <!-- Estadísticas Principales -->
        <div class="stats-grid">
            <div class="stat-card empresas">
                <div class="stat-icon">
                    <i class="fas fa-building"></i>
                </div>
                <div class="stat-value">{stats['total_empresas']:,}</div>
                <div class="stat-label">Empresas</div>
            </div>
            
            <div class="stat-card registros">
                <div class="stat-icon">
                    <i class="fas fa-users"></i>
                </div>
                <div class="stat-value">{stats['total_registros']:,}</div>
                <div class="stat-label">Registros</div>
            </div>
            
            <div class="stat-card salario">
                <div class="stat-icon">
                    <i class="fas fa-money-bill-wave"></i>
                </div>
                <div class="stat-value">S/ {stats['salario_promedio_general']:,}</div>
                <div class="stat-label">Salario Promedio</div>
            </div>
            
            <div class="stat-card sectores">
                <div class="stat-icon">
                    <i class="fas fa-industry"></i>
                </div>
                <div class="stat-value">{stats['total_sectores']}</div>
                <div class="stat-label">Sectores</div>
            </div>
        </div>

        <!-- Top Lists -->
        <div class="top-lists">
            <div class="top-list">
                <h3><i class="fas fa-trophy"></i> Top 5 Empresas</h3>
                {''.join([f'<div class="top-item"><span class="top-name">{empresa}</span><span class="top-value">S/ {salario:,.0f}</span></div>' for empresa, salario in list(stats['top_empresas'].items())[:5]])}
            </div>
            
            <div class="top-list">
                <h3><i class="fas fa-chart-pie"></i> Top 5 Sectores</h3>
                {''.join([f'<div class="top-item"><span class="top-name">{sector}</span><span class="top-value">S/ {salario:,.0f}</span></div>' for sector, salario in list(stats['top_sectores'].items())[:5]])}
            </div>
        </div>

        <!-- Gráficos Interactivos -->
        <section class="charts-section">
            <h2 class="section-title">📊 Análisis Interactivo</h2>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Cargando gráficos interactivos...</p>
            </div>
            
            <div class="charts-grid">
                <div class="chart-container chart-full-width">
                    {charts['empresas']}
                </div>
                
                <div class="chart-container">
                    {charts['sectores']}
                </div>
                
                <div class="chart-container">
                    {charts['distribucion']}
                </div>
                
                <div class="chart-container">
                    {charts['seniority']}
                </div>
                
                <div class="chart-container chart-full-width">
                    {charts['scatter']}
                </div>
            </div>
        </section>
    </main>

    <footer class="footer">
        <div class="container">
            <p>
                <i class="fas fa-database"></i>
                Datos procesados: {stats['total_registros']:,} registros de {stats['total_empresas']} empresas
                | 
                <i class="fas fa-file-csv"></i>
                Fuente: {stats['archivo_datos']}
                |
                <a href="https://github.com/tu-usuario/salariosperu" target="_blank">
                    <i class="fab fa-github"></i> Ver en GitHub
                </a>
            </p>
        </div>
    </footer>

    <script>
        // Mostrar loading inicialmente y ocultarlo cuando los gráficos estén listos
        document.addEventListener('DOMContentLoaded', function() {{
            const loading = document.getElementById('loading');
            loading.style.display = 'block';
            
            // Ocultar loading después de que Plotly termine de cargar
            setTimeout(() => {{
                loading.style.display = 'none';
            }}, 2000);
        }});

        // Añadir efectos de hover para las tarjetas
        document.querySelectorAll('.stat-card, .chart-container, .top-list').forEach(card => {{
            card.addEventListener('mouseenter', function() {{
                this.style.transform = 'translateY(-5px)';
            }});
            
            card.addEventListener('mouseleave', function() {{
                this.style.transform = 'translateY(0)';
            }});
        }});

        // Analytics simple
        console.log('📊 Dashboard Salarios Perú cargado');
        console.log('📈 Total registros:', {stats['total_registros']});
        console.log('🏢 Total empresas:', {stats['total_empresas']});
        console.log('💰 Salario promedio: S/', {stats['salario_promedio_general']});
    </script>
</body>
</html>
        """
        
        # Guardar el archivo HTML
        output_file = os.path.join(self.output_dir, 'index.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Dashboard web creado: {output_file}")
        return output_file
    
    def create_api_endpoints(self):
        """Crea archivos JSON para endpoints de API"""
        print("🔗 Creando endpoints JSON...")
        
        df = self.analyzer.df
        
        # API endpoints
        endpoints = {
            'stats': self.generate_summary_stats(),
            'empresas': df.groupby('empresa')['salario_promedio'].mean().sort_values(ascending=False).head(20).round(2).to_dict(),
            'sectores': df.groupby('sector')['salario_promedio'].mean().sort_values(ascending=False).round(2).to_dict(),
            'puestos': df.nlargest(50, 'salario_promedio')[['puesto', 'empresa', 'salario_promedio']].to_dict('records')
        }
        
        for endpoint, data in endpoints.items():
            file_path = os.path.join(self.output_dir, f'{endpoint}.json')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"   📄 {endpoint}.json")
        
        return endpoints


def main():
    """Función principal"""
    print("🎨 GENERADOR DE DASHBOARD WEB MODERNO")
    print("=" * 50)
    
    try:
        # Crear generador
        generator = DashboardWebGenerator()
        
        # Generar dashboard
        dashboard_file = generator.create_modern_dashboard()
        
        # Crear endpoints API
        generator.create_api_endpoints()
        
        print(f"\n✅ Dashboard web generado exitosamente!")
        print(f"📁 Directorio: {generator.output_dir}/")
        print(f"🌐 Archivo principal: {dashboard_file}")
        print(f"🔗 Abrir en navegador: file://{os.path.abspath(dashboard_file)}")
        
        # Opción para servir automáticamente
        serve = input("\n¿Quieres iniciar el servidor web automáticamente? (y/n): ").strip().lower()
        if serve in ['y', 'yes', 'sí', 's']:
            import webbrowser
            import http.server
            import socketserver
            import threading
            
            PORT = 8080
            os.chdir(generator.output_dir)
            
            handler = http.server.SimpleHTTPRequestHandler
            httpd = socketserver.TCPServer(("", PORT), handler)
            
            print(f"\n🚀 Servidor iniciado en: http://localhost:{PORT}")
            webbrowser.open(f'http://localhost:{PORT}')
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n🛑 Servidor detenido")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 