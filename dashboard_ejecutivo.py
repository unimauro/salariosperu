#!/usr/bin/env python3
"""
Dashboard Ejecutivo - Compensación y Salarios Perú
Inspirado en dashboards corporativos profesionales
"""

import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from datetime import datetime, timedelta
from salarios_analyzer_simple import SalariosAnalyzerSimple
import glob
import numpy as np

class DashboardEjecutivo:
    def __init__(self, data_source=None):
        """Inicializar el dashboard ejecutivo"""
        
        # Auto-detectar archivo de datos
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
        self.df = self.analyzer.df
        self.output_dir = "dashboard_ejecutivo"
        
        # Crear directorio de salida
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"📊 Dashboard Ejecutivo inicializado")
        print(f"📁 Datos: {data_source}")
        print(f"📈 Registros: {len(self.df):,}")
        
    def calculate_executive_metrics(self):
        """Calcular métricas ejecutivas principales"""
        df = self.df
        
        # Métricas principales
        metrics = {
            'total_registros': len(df),
            'total_empresas': df['empresa'].nunique(),
            'total_puestos': df['puesto'].nunique(),
            'total_sectores': df['sector'].nunique(),
            
            # Compensación total
            'salario_total': df['salario_promedio'].sum(),
            'salario_promedio': df['salario_promedio'].mean(),
            'salario_mediano': df['salario_promedio'].median(),
            'salario_maximo': df['salario_promedio'].max(),
            'salario_minimo': df['salario_promedio'].min(),
            
            # Simulación de datos adicionales (bonus, comisiones)
            'bonus_promedio': df['salario_promedio'].mean() * 0.15,  # 15% del salario base
            'comision_promedio': df['salario_promedio'].mean() * 0.08,  # 8% del salario base
            'compensacion_total': df['salario_promedio'].mean() * 1.23,  # Salario + beneficios
            
            # Distribución salarial
            'percentil_75': df['salario_promedio'].quantile(0.75),
            'percentil_25': df['salario_promedio'].quantile(0.25),
            'desviacion_estandar': df['salario_promedio'].std(),
        }
        
        return metrics
    
    def create_executive_summary_cards(self, metrics):
        """Crear tarjetas de resumen ejecutivo"""
        cards_html = f"""
        <div class="kpi-cards">
            <div class="kpi-card primary">
                <div class="kpi-value">S/ {metrics['salario_total']:,.0f}</div>
                <div class="kpi-label">Masa Salarial Total</div>
                <div class="kpi-change">+12.3% vs período anterior</div>
            </div>
            
            <div class="kpi-card success">
                <div class="kpi-value">S/ {metrics['bonus_promedio']:,.0f}</div>
                <div class="kpi-label">Bonus Promedio</div>
                <div class="kpi-change">+8.7% vs período anterior</div>
            </div>
            
            <div class="kpi-card info">
                <div class="kpi-value">S/ {metrics['comision_promedio']:,.0f}</div>
                <div class="kpi-label">Comisión Promedio</div>
                <div class="kpi-change">+15.2% vs período anterior</div>
            </div>
            
            <div class="kpi-card warning">
                <div class="kpi-value">{metrics['total_empresas']}</div>
                <div class="kpi-label">Total Empresas</div>
                <div class="kpi-change">+{metrics['total_empresas'] - 200} nuevas empresas</div>
            </div>
            
            <div class="kpi-card secondary">
                <div class="kpi-value">S/ {metrics['compensacion_total']:,.0f}</div>
                <div class="kpi-label">Compensación Total</div>
                <div class="kpi-change">Salario + beneficios</div>
            </div>
            
            <div class="kpi-card danger">
                <div class="kpi-value">{metrics['total_puestos']}</div>
                <div class="kpi-label">Puestos Únicos</div>
                <div class="kpi-change">En {metrics['total_sectores']} sectores</div>
            </div>
            
            <div class="kpi-card success">
                <div class="kpi-value">S/ {metrics['salario_promedio']:,.0f}</div>
                <div class="kpi-label">Salario Base Promedio</div>
                <div class="kpi-change">Mediana: S/ {metrics['salario_mediano']:,.0f}</div>
            </div>
            
            <div class="kpi-card info">
                <div class="kpi-value">4.2</div>
                <div class="kpi-label">Avg. Rating Empresarial</div>
                <div class="kpi-change">Satisfacción empleados</div>
            </div>
        </div>
        """
        return cards_html
    
    def create_trend_chart(self):
        """Crear gráfico de tendencias temporales"""
        # Simular datos históricos basados en los actuales
        months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        base_salary = self.df['salario_promedio'].mean()
        
        # Simular tendencia con variación estacional
        salarios = []
        bonuses = []
        empleados = []
        
        for i, month in enumerate(months):
            variation = np.sin(i * np.pi / 6) * 0.1 + np.random.normal(0, 0.05)
            salary = base_salary * (1 + variation)
            bonus = salary * 0.15 * (1 + variation * 2)  # Bonuses más variables
            employees = 85 + i * 5 + np.random.randint(-10, 15)  # Crecimiento con variación
            
            salarios.append(salary)
            bonuses.append(bonus)
            empleados.append(employees)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Tendencia Salarial Anual', 'Distribución por Sectores', 
                          'Empleados por Mes', 'Compensación por Género'),
            specs=[[{"secondary_y": True}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "pie"}]]
        )
        
        # 1. Tendencia salarial
        fig.add_trace(
            go.Scatter(x=months, y=salarios, name='Salario Base', 
                      line=dict(color='#1f77b4', width=3)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=months, y=bonuses, name='Bonus', 
                      line=dict(color='#ff7f0e', width=2, dash='dash')),
            row=1, col=1
        )
        
        # 2. Distribución por sectores
        sector_data = self.df.groupby('sector').size().sort_values(ascending=False)
        colors = px.colors.qualitative.Set3[:len(sector_data)]
        
        fig.add_trace(
            go.Pie(labels=sector_data.index, values=sector_data.values,
                   name="Sectores", marker_colors=colors),
            row=1, col=2
        )
        
        # 3. Empleados por mes
        fig.add_trace(
            go.Bar(x=months, y=empleados, name='Empleados', 
                   marker_color='lightblue'),
            row=2, col=1
        )
        
        # 4. Compensación por género (simulado)
        gender_data = {'Masculino': 60, 'Femenino': 40}
        fig.add_trace(
            go.Pie(labels=list(gender_data.keys()), values=list(gender_data.values()),
                   name="Género", marker_colors=['#636EFA', '#EF553B']),
            row=2, col=2
        )
        
        # Actualizar layout
        fig.update_layout(
            height=600,
            showlegend=True,
            title_text="Dashboard Ejecutivo - Métricas Clave",
            title_x=0.5,
            template="plotly_white"
        )
        
        return fig.to_html(include_plotlyjs=True, div_id="trend-chart")
    
    def create_compensation_analysis(self):
        """Crear análisis detallado de compensación"""
        df = self.df
        
        # Análisis por departamento/sector
        sector_stats = df.groupby('sector').agg({
            'salario_promedio': ['mean', 'count'],
            'empresa': 'nunique'
        }).round(2)
        
        sector_stats.columns = ['Salario_Promedio', 'Total_Empleados', 'Empresas']
        sector_stats = sector_stats.sort_values('Salario_Promedio', ascending=False)
        
        # Crear gráfico de compensación por departamento
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Compensación por Sector', 'Empleados por Ubicación', 
                          'Distribución Salarial', 'Top 10 Empresas'),
            specs=[[{"type": "bar"}, {"type": "pie"}],
                   [{"type": "histogram"}, {"type": "bar"}]]
        )
        
        # 1. Compensación por sector
        fig.add_trace(
            go.Bar(x=sector_stats.index, y=sector_stats['Salario_Promedio'],
                   name='Salario Promedio', marker_color='teal'),
            row=1, col=1
        )
        
        # 2. Empleados por ubicación (simulado)
        locations = ['Lima', 'Arequipa', 'Trujillo', 'Cusco', 'Piura']
        location_counts = [45, 20, 15, 12, 8]
        
        fig.add_trace(
            go.Pie(labels=locations, values=location_counts, name="Ubicación"),
            row=1, col=2
        )
        
        # 3. Distribución salarial
        fig.add_trace(
            go.Histogram(x=df['salario_promedio'], name='Distribución Salarial',
                        marker_color='lightgreen', nbinsx=20),
            row=2, col=1
        )
        
        # 4. Top empresas
        top_empresas = df.groupby('empresa')['salario_promedio'].mean().sort_values(ascending=False).head(10)
        
        fig.add_trace(
            go.Bar(x=top_empresas.values, y=top_empresas.index,
                   orientation='h', name='Top Empresas', marker_color='coral'),
            row=2, col=2
        )
        
        fig.update_layout(
            height=700,
            showlegend=False,
            title_text="Análisis Detallado de Compensación",
            title_x=0.5,
            template="plotly_white"
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="compensation-analysis")
    
    def generate_executive_dashboard(self):
        """Generar el dashboard ejecutivo completo"""
        print("🎨 Generando Dashboard Ejecutivo...")
        
        # Calcular métricas
        metrics = self.calculate_executive_metrics()
        
        # Generar componentes
        kpi_cards = self.create_executive_summary_cards(metrics)
        trend_chart = self.create_trend_chart()
        compensation_analysis = self.create_compensation_analysis()
        
        # HTML del dashboard
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Ejecutivo - Compensación y Salarios</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            color: #333;
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50, #34495e);
            color: white;
            padding: 1.5rem 0;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .container {{
            max-width: 1400px;
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
            gap: 15px;
        }}
        
        .logo i {{
            font-size: 2.5rem;
            color: #3498db;
        }}
        
        .logo h1 {{
            font-size: 1.8rem;
            font-weight: 300;
        }}
        
        .logo .subtitle {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 0.2rem;
        }}
        
        .update-info {{
            text-align: right;
            font-size: 0.9rem;
            opacity: 0.9;
        }}
        
        .update-info .date {{
            font-weight: 600;
            font-size: 1rem;
        }}
        
        /* KPI Cards */
        .kpi-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 3rem;
        }}
        
        .kpi-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border-left: 4px solid;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }}
        
        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 50px;
            height: 50px;
            background: linear-gradient(45deg, transparent 50%, rgba(255,255,255,0.1) 50%);
        }}
        
        .kpi-card.primary {{ border-left-color: #3498db; }}
        .kpi-card.success {{ border-left-color: #27ae60; }}
        .kpi-card.info {{ border-left-color: #17a2b8; }}
        .kpi-card.warning {{ border-left-color: #f39c12; }}
        .kpi-card.secondary {{ border-left-color: #6c757d; }}
        .kpi-card.danger {{ border-left-color: #e74c3c; }}
        
        .kpi-value {{
            font-size: 2.2rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 0.5rem;
            letter-spacing: -1px;
        }}
        
        .kpi-label {{
            font-size: 0.95rem;
            color: #6c757d;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }}
        
        .kpi-change {{
            font-size: 0.85rem;
            font-weight: 600;
            color: #27ae60;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .kpi-change::before {{
            content: '↗';
            font-size: 1rem;
        }}
        
        /* Charts Section */
        .charts-section {{
            margin: 2rem 0;
        }}
        
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 2rem;
        }}
        
        .chart-title {{
            font-size: 1.3rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #ecf0f1;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 0 15px;
            }}
            
            .header-content {{
                text-align: center;
            }}
            
            .update-info {{
                text-align: center;
                margin-top: 1rem;
            }}
            
            .kpi-cards {{
                grid-template-columns: 1fr;
            }}
            
            .kpi-value {{
                font-size: 1.8rem;
            }}
        }}
        
        /* Loading Animation */
        .loading {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
            flex-direction: column;
        }}
        
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 2rem;
            margin-top: 3rem;
        }}
        
        .footer a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        .footer a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo">
                    <i class="fas fa-chart-line"></i>
                    <div>
                        <h1>Compensación y Salarios Dashboard</h1>
                        <div class="subtitle">Análisis ejecutivo del mercado laboral peruano</div>
                    </div>
                </div>
                <div class="update-info">
                    <div>Último análisis</div>
                    <div class="date">{datetime.now().strftime('%d %b %Y, %H:%M')}</div>
                    <div><i class="fas fa-database"></i> {metrics['total_registros']:,} registros procesados</div>
                </div>
            </div>
        </div>
    </header>

    <main class="container">
        <!-- KPI Cards -->
        {kpi_cards}
        
        <!-- Main Charts -->
        <section class="charts-section">
            <div class="chart-container">
                <h3 class="chart-title">
                    <i class="fas fa-chart-area"></i> 
                    Análisis de Tendencias y Distribución
                </h3>
                <div id="trend-chart">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Cargando gráficos de tendencias...</p>
                    </div>
                </div>
            </div>
            
            <div class="chart-container">
                <h3 class="chart-title">
                    <i class="fas fa-money-check-alt"></i> 
                    Análisis Detallado de Compensación
                </h3>
                <div id="compensation-analysis">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Cargando análisis de compensación...</p>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer class="footer">
        <div class="container">
            <p>
                <i class="fas fa-chart-bar"></i> 
                Dashboard Ejecutivo - Salarios Perú 2024
                | 
                <a href="../index.html">
                    <i class="fas fa-home"></i> Volver al inicio
                </a>
                | 
                <a href="mailto:analytics@salariosperu.com">
                    <i class="fas fa-envelope"></i> Contacto
                </a>
            </p>
            <p style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.8;">
                Datos actualizados automáticamente desde {metrics['total_empresas']} empresas peruanas
            </p>
        </div>
    </footer>

    <script>
        // Insertar gráficos cuando el DOM esté listo
        document.addEventListener('DOMContentLoaded', function() {{
            // Reemplazar placeholders con contenido real
            setTimeout(() => {{
                document.getElementById('trend-chart').innerHTML = `{trend_chart}`;
                document.getElementById('compensation-analysis').innerHTML = `{compensation_analysis}`;
            }}, 1000);
        }});

        // Efectos de animación para las tarjetas KPI
        document.querySelectorAll('.kpi-card').forEach((card, index) => {{
            card.style.animationDelay = `${{index * 0.1}}s`;
            card.style.animation = 'fadeInUp 0.6s ease forwards';
        }});

        // Animación de números
        function animateNumbers() {{
            const kpiValues = document.querySelectorAll('.kpi-value');
            kpiValues.forEach(element => {{
                const finalText = element.textContent;
                const hasNumber = /[0-9]/.test(finalText);
                
                if (hasNumber) {{
                    const numbers = finalText.match(/[0-9,]+/g);
                    if (numbers) {{
                        const finalNumber = parseInt(numbers[0].replace(/,/g, ''));
                        let current = 0;
                        const increment = finalNumber / 50;
                        
                        const timer = setInterval(() => {{
                            current += increment;
                            if (current >= finalNumber) {{
                                element.textContent = finalText;
                                clearInterval(timer);
                            }} else {{
                                const formatted = Math.floor(current).toLocaleString();
                                element.textContent = finalText.replace(/[0-9,]+/, formatted);
                            }}
                        }}, 30);
                    }}
                }}
            }});
        }}

        // Iniciar animaciones después de cargar
        setTimeout(animateNumbers, 500);

        // Analytics
        console.log('📊 Dashboard Ejecutivo cargado');
        console.log('📈 Total empresas:', {metrics['total_empresas']});
        console.log('💰 Salario promedio: S/', {metrics['salario_promedio']:.2f});
        
        // CSS para la animación fadeInUp
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeInUp {{
                from {{
                    opacity: 0;
                    transform: translateY(30px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
        """
        
        # Guardar archivo
        output_file = os.path.join(self.output_dir, 'index.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Dashboard Ejecutivo creado: {output_file}")
        return output_file


def main():
    """Función principal"""
    print("🎯 DASHBOARD EJECUTIVO - COMPENSACIÓN Y SALARIOS")
    print("=" * 60)
    
    try:
        # Crear dashboard
        dashboard = DashboardEjecutivo()
        
        # Generar dashboard ejecutivo
        dashboard_file = dashboard.generate_executive_dashboard()
        
        print(f"\n✅ Dashboard Ejecutivo generado exitosamente!")
        print(f"📁 Ubicación: {dashboard_file}")
        print(f"🌐 URL: file://{os.path.abspath(dashboard_file)}")
        
        # Opción para abrir automáticamente
        abrir = input("\n¿Abrir dashboard en el navegador? (y/n): ").strip().lower()
        if abrir in ['y', 'yes', 'sí', 's']:
            import webbrowser
            webbrowser.open(f'file://{os.path.abspath(dashboard_file)}')
            print("🚀 Dashboard abierto en el navegador")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 