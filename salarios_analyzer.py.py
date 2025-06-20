#!/usr/bin/env python3
"""
Analizador Avanzado de Datos de Salarios Perú
Realiza análisis detallados con visualizaciones profesionales interactivas
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import numpy as np
from datetime import datetime
import warnings
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

warnings.filterwarnings('ignore')

# Configurar tema profesional
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
pio.templates.default = "plotly_white"

class SalariosAnalyzer:
    def __init__(self, data_source):
        """
        Inicializa el analizador con visualizaciones profesionales
        
        Args:
            data_source: Puede ser un archivo CSV, SQLite DB o DataFrame
        """
        self.df = self.load_data(data_source)
        self.setup_data()
        self.color_palette = {
            'Banca y Finanzas': '#FF6B6B',
            'Tecnología': '#4ECDC4', 
            'Consumo Masivo': '#45B7D1',
            'Consultoría': '#96CEB4',
            'Telecomunicaciones': '#FFEAA7',
            'Seguros': '#DDA0DD',
            'Bebidas': '#FFB347',
            'Cosmética': '#F8BBD0',
            'Otros': '#B0BEC5'
        }
    
    def load_data(self, source):
        """Carga datos desde diferentes fuentes"""
        if isinstance(source, pd.DataFrame):
            return source
        elif source.endswith('.csv'):
            return pd.read_csv(source)
        elif source.endswith('.db'):
            conn = sqlite3.connect(source)
            df = pd.read_sql_query("SELECT * FROM salarios", conn)
            conn.close()
            return df
        else:
            raise ValueError("Fuente de datos no soportada")
    
    def setup_data(self):
        """Prepara y limpia los datos para análisis avanzado"""
        # Convertir salarios a numérico
        numeric_cols = ['salario_minimo', 'salario_maximo', 'salario_promedio']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Limpiar nombres
        if 'empresa' in self.df.columns:
            self.df['empresa'] = self.df['empresa'].str.strip().str.title()
        if 'puesto' in self.df.columns:
            self.df['puesto'] = self.df['puesto'].str.strip()
        
        # Asignar sectores mejorado
        self.assign_sectors()
        
        # Crear métricas adicionales
        self.create_additional_metrics()
        
        print(f"✅ Datos preparados: {len(self.df)} registros")
        print(f"📊 Métricas calculadas y sectores asignados")
    
    def assign_sectors(self):
        """Asigna sectores de manera más sofisticada"""
        sectores = {
            'Banca y Finanzas': ['bcp', 'bbva', 'interbank', 'credicorp', 'banco', 'scotiabank', 
                               'yape', 'plin', 'culqi', 'izipay', 'financiera', 'credito'],
            'Tecnología': ['tech', 'software', 'ibm', 'microsoft', 'google', 'oracle', 'sap',
                          'accenture', 'tcs', 'globant', 'data', 'developer', 'programmer'],
            'Consultoría': ['ey', 'deloitte', 'pwc', 'kpmg', 'mckinsey', 'bcg', 'bain', 
                           'consulting', 'consultant', 'advisory'],
            'Telecomunicaciones': ['entel', 'movistar', 'claro', 'bitel', 'telecom', 'telefonica'],
            'Consumo Masivo': ['alicorp', 'gloria', 'nestle', 'unilever', 'procter', 'gamble',
                              'retail', 'falabella', 'ripley', 'tottus', 'wong', 'plaza'],
            'Seguros': ['rimac', 'pacifico', 'seguros', 'insurance', 'reaseguros'],
            'Bebidas': ['ab inbev', 'backus', 'coca cola', 'pepsi', 'cerveza'],
            'Cosmética': ['loreal', "l'oreal", 'nivea', 'cosmetic', 'beauty'],
            'Minería': ['antamina', 'southern', 'volcan', 'buenaventura', 'cerro verde', 'mining'],
            'Energía': ['enel', 'luz del sur', 'electroandes', 'energy', 'electric']
        }
        
        self.df['sector'] = 'Otros'
        self.df['sector_color'] = self.color_palette['Otros']
        
        for sector, keywords in sectores.items():
            for keyword in keywords:
                mask = (self.df['empresa'].str.lower().str.contains(keyword, na=False) | 
                       self.df['puesto'].str.lower().str.contains(keyword, na=False))
                self.df.loc[mask, 'sector'] = sector
                if sector in self.color_palette:
                    self.df.loc[mask, 'sector_color'] = self.color_palette[sector]
    
    def create_additional_metrics(self):
        """Crea métricas adicionales para análisis"""
        # Número de puestos por empresa
        empresa_counts = self.df.groupby('empresa').size()
        self.df['empresa_size'] = self.df['empresa'].map(empresa_counts)
        
        # Ranking de empresas por salario
        empresa_avg = self.df.groupby('empresa')['salario_promedio'].mean()
        empresa_ranks = empresa_avg.rank(ascending=False)
        self.df['empresa_rank'] = self.df['empresa'].map(empresa_ranks)
        
        # Categorías de empresa por tamaño
        self.df['size_category'] = pd.cut(
            self.df['empresa_size'],
            bins=[0, 2, 5, 10, float('inf')],
            labels=['Pequeña', 'Mediana', 'Grande', 'Corporativa']
        )
        
        # Seniority level (inferido del título del puesto)
        def detect_seniority(puesto):
            puesto_lower = str(puesto).lower()
            if any(word in puesto_lower for word in ['senior', 'sr', 'lead', 'principal', 'manager', 'gerente']):
                return 'Senior'
            elif any(word in puesto_lower for word in ['junior', 'jr', 'trainee', 'analyst', 'analista']):
                return 'Junior'
            else:
                return 'Mid-Level'
        
        self.df['seniority'] = self.df['puesto'].apply(detect_seniority)
    
    def bubble_chart_salary_vs_company_size(self):
        """Crea gráfico de burbujas profesional: Salario vs Tamaño de Empresa"""
        print("\n🫧 Generando Bubble Chart: Salario vs Tamaño de Empresa")
        
        # Preparar datos agregados
        bubble_data = self.df.groupby(['empresa', 'sector']).agg({
            'salario_promedio': 'mean',
            'empresa_size': 'first',
            'puesto': 'count'
        }).reset_index()
        
        bubble_data.columns = ['empresa', 'sector', 'salario_avg', 'num_empleados', 'num_puestos']
        
        # Crear bubble chart con Plotly
        fig = px.scatter(
            bubble_data,
            x='num_empleados',
            y='salario_avg',
            size='num_puestos',
            color='sector',
            hover_name='empresa',
            title='💰 Salario Promedio vs Tamaño de Empresa por Sector',
            labels={
                'num_empleados': 'Número de Empleados Registrados',
                'salario_avg': 'Salario Promedio (S/)',
                'num_puestos': 'Número de Puestos'
            },
            size_max=60,
            color_discrete_map=self.color_palette
        )
        
        # Personalizar diseño
        fig.update_layout(
            width=1200,
            height=700,
            font=dict(family="Arial, sans-serif", size=12),
            title_font_size=16,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
        
        # Añadir anotaciones para empresas destacadas
        top_companies = bubble_data.nlargest(5, 'salario_avg')
        for _, company in top_companies.iterrows():
            fig.add_annotation(
                x=company['num_empleados'],
                y=company['salario_avg'],
                text=company['empresa'],
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="black",
                font=dict(size=10)
            )
        
        fig.write_html("bubble_chart_salarios.html")
        fig.show()
        return fig
    
    def interactive_scatter_matrix(self):
        """Crea matriz de scatter plots interactiva"""
        print("\n📊 Generando Matriz de Correlaciones Interactiva")
        
        # Seleccionar variables numéricas
        numeric_vars = ['salario_promedio', 'empresa_size', 'empresa_rank']
        if len(numeric_vars) >= 2:
            fig = px.scatter_matrix(
                self.df,
                dimensions=numeric_vars,
                color='sector',
                title='🔍 Matriz de Correlaciones: Salarios y Métricas Empresariales',
                color_discrete_map=self.color_palette
            )
            
            fig.update_layout(
                width=900,
                height=700,
                font=dict(family="Arial, sans-serif", size=10)
            )
            
            fig.write_html("scatter_matrix_salarios.html")
            fig.show()
            return fig
    
    def advanced_salary_distribution_by_sector(self):
        """Visualización avanzada de distribución salarial por sector"""
        print("\n📈 Generando Distribución Salarial Avanzada por Sector")
        
        # Crear subplot con múltiples visualizaciones
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Distribución por Sector (Box Plot)',
                'Densidad Salarial por Sector', 
                'Salario Promedio por Sector',
                'Violín Plot - Distribución Detallada'
            ),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        sectors = self.df['sector'].unique()
        colors = [self.color_palette.get(sector, '#B0BEC5') for sector in sectors]
        
        # 1. Box plot
        for i, sector in enumerate(sectors):
            sector_data = self.df[self.df['sector'] == sector]['salario_promedio'].dropna()
            fig.add_trace(
                go.Box(y=sector_data, name=sector, marker_color=colors[i], showlegend=False),
                row=1, col=1
            )
        
        # 2. Histogram/Density
        for i, sector in enumerate(sectors):
            sector_data = self.df[self.df['sector'] == sector]['salario_promedio'].dropna()
            fig.add_trace(
                go.Histogram(x=sector_data, name=sector, opacity=0.7, 
                           marker_color=colors[i], showlegend=False),
                row=1, col=2
            )
        
        # 3. Bar chart promedio
        sector_avg = self.df.groupby('sector')['salario_promedio'].mean().sort_values(ascending=True)
        fig.add_trace(
            go.Bar(x=sector_avg.values, y=sector_avg.index, orientation='h',
                   marker_color=[self.color_palette.get(s, '#B0BEC5') for s in sector_avg.index],
                   showlegend=False),
            row=2, col=1
        )
        
        # 4. Violin plot
        for i, sector in enumerate(sectors):
            sector_data = self.df[self.df['sector'] == sector]['salario_promedio'].dropna()
            fig.add_trace(
                go.Violin(y=sector_data, name=sector, box_visible=True,
                         marker_color=colors[i], showlegend=False),
                row=2, col=2
            )
        
        fig.update_layout(
            height=800,
            width=1400,
            title_text="📊 Análisis Completo de Distribución Salarial por Sector",
            font=dict(family="Arial, sans-serif", size=11)
        )
        
        fig.write_html("distribucion_salarial_avanzada.html")
        fig.show()
        return fig
    
    def university_performance_radar(self):
        """Gráfico radar del rendimiento por universidad"""
        print("\n🎓 Generando Análisis Radar por Universidad")
        
        if 'universidad_principal' not in self.df.columns:
            print("❌ No hay datos de universidades")
            return
        
        # Preparar datos por universidad
        uni_data = self.df[self.df['universidad_principal'].notna()].copy()
        
        if uni_data.empty:
            print("❌ No hay datos de universidades válidos")
            return
        
        uni_metrics = uni_data.groupby('universidad_principal').agg({
            'salario_promedio': 'mean',
            'empresa_size': 'mean',
            'puesto': 'count'
        }).reset_index()
        
        # Normalizar métricas (0-100)
        for col in ['salario_promedio', 'empresa_size', 'puesto']:
            uni_metrics[f'{col}_norm'] = (uni_metrics[col] / uni_metrics[col].max()) * 100
        
        # Crear gráfico radar
        categories = ['Salario Promedio', 'Tamaño Empresa', 'Oportunidades Laborales']
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set3
        for i, (_, uni) in enumerate(uni_metrics.iterrows()):
            values = [
                uni['salario_promedio_norm'],
                uni['empresa_size_norm'], 
                uni['puesto_norm']
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],  # Cerrar el polígono
                theta=categories + [categories[0]],
                fill='toself',
                name=uni['universidad_principal'],
                line_color=colors[i % len(colors)],
                fillcolor=colors[i % len(colors)],
                opacity=0.6
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title="🎯 Rendimiento Comparativo por Universidad",
            width=800,
            height=600
        )
        
        fig.write_html("radar_universidades.html")
        fig.show()
        return fig
    
    def salary_heatmap_by_position_and_company(self):
        """Mapa de calor: Salarios por Puesto y Empresa"""
        print("\n🌡️ Generando Mapa de Calor: Salarios por Posición y Empresa")
        
        # Crear tabla pivote
        pivot_data = self.df.groupby(['puesto', 'empresa'])['salario_promedio'].mean().reset_index()
        pivot_table = pivot_data.pivot(index='puesto', columns='empresa', values='salario_promedio')
        
        # Filtrar para mostrar solo las combinaciones más relevantes
        top_positions = self.df['puesto'].value_counts().head(15).index
        top_companies = self.df['empresa'].value_counts().head(10).index
        
        filtered_pivot = pivot_table.loc[
            pivot_table.index.intersection(top_positions),
            pivot_table.columns.intersection(top_companies)
        ]
        
        # Crear heatmap interactivo
        fig = px.imshow(
            filtered_pivot.values,
            labels=dict(x="Empresa", y="Puesto", color="Salario (S/)"),
            x=filtered_pivot.columns,
            y=filtered_pivot.index,
            color_continuous_scale='RdYlBu_r',
            title='🌡️ Mapa de Calor: Salarios por Puesto y Empresa'
        )
        
        fig.update_layout(
            width=1200,
            height=800,
            font=dict(family="Arial, sans-serif", size=10)
        )
        
        fig.write_html("heatmap_salarios.html")
        fig.show()
        return fig
    
    def create_professional_dashboard(self):
        """Crea un dashboard completo profesional"""
        print("\n🚀 Generando Dashboard Profesional Completo")
        
        # Crear dashboard con 6 subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                '💰 Top 10 Empresas por Salario Promedio',
                '🏢 Distribución por Sector',
                '📊 Salarios por Nivel de Seniority', 
                '🎓 Performance por Universidad',
                '📈 Correlación: Tamaño vs Salario',
                '🎯 Métricas Clave'
            ),
            specs=[[{"type": "bar"}, {"type": "pie"}],
                   [{"type": "box"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "indicator"}]]
        )
        
        # 1. Top empresas
        top_companies = self.df.groupby('empresa')['salario_promedio'].mean().nlargest(10)
        fig.add_trace(
            go.Bar(x=top_companies.values, y=top_companies.index, orientation='h',
                   marker_color='lightblue', name="Salario Promedio"),
            row=1, col=1
        )
        
        # 2. Distribución por sector
        sector_counts = self.df['sector'].value_counts()
        fig.add_trace(
            go.Pie(labels=sector_counts.index, values=sector_counts.values,
                   marker_colors=[self.color_palette.get(s, '#B0BEC5') for s in sector_counts.index]),
            row=1, col=2
        )
        
        # 3. Salarios por seniority
        seniority_data = self.df.groupby('seniority')['salario_promedio'].apply(list)
        for level in seniority_data.index:
            fig.add_trace(
                go.Box(y=seniority_data[level], name=level, showlegend=False),
                row=2, col=1
            )
        
        # 4. Universidades (si hay datos)
        if 'universidad_principal' in self.df.columns and self.df['universidad_principal'].notna().sum() > 0:
            uni_avg = self.df[self.df['universidad_principal'].notna()].groupby('universidad_principal')['salario_promedio'].mean()
            fig.add_trace(
                go.Bar(x=uni_avg.index, y=uni_avg.values, marker_color='lightgreen'),
                row=2, col=2
            )
        
        # 5. Scatter: Tamaño vs Salario
        fig.add_trace(
            go.Scatter(
                x=self.df['empresa_size'],
                y=self.df['salario_promedio'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=self.df['sector'].map(self.color_palette),
                    opacity=0.7
                ),
                text=self.df['empresa'],
                hovertemplate='<b>%{text}</b><br>Empleados: %{x}<br>Salario: S/%{y}<extra></extra>'
            ),
            row=3, col=1
        )
        
        # 6. Métricas clave
        avg_salary = self.df['salario_promedio'].mean()
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=avg_salary,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Salario Promedio General (S/)"},
                delta={'reference': 8000},
                gauge={
                    'axis': {'range': [None, 25000]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 5000], 'color': "lightgray"},
                        {'range': [5000, 15000], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 15000
                    }
                }
            ),
            row=3, col=2
        )
        
        # Actualizar layout
        fig.update_layout(
            height=1200,
            width=1600,
            title_text="📊 Dashboard Profesional - Análisis de Salarios Perú 2025",
            title_x=0.5,
            font=dict(family="Arial, sans-serif", size=12),
            showlegend=False
        )
        
        fig.write_html("dashboard_profesional_salarios.html")
        fig.show()
        return fig
    
    def generate_executive_summary(self):
        """Genera resumen ejecutivo con métricas clave"""
        print("\n📋 RESUMEN EJECUTIVO")
        print("=" * 50)
        
        # Métricas clave
        total_records = len(self.df)
        avg_salary = self.df['salario_promedio'].mean()
        median_salary = self.df['salario_promedio'].median()
        top_sector = self.df['sector'].value_counts().index[0]
        
        # Top performers
        top_company = self.df.groupby('empresa')['salario_promedio'].mean().idxmax()
        top_company_salary = self.df.groupby('empresa')['salario_promedio'].mean().max()
        
        print(f"💼 **Registros analizados:** {total_records:,}")
        print(f"💰 **Salario promedio:** S/ {avg_salary:,.2f}")
        print(f"📊 **Salario mediano:** S/ {median_salary:,.2f}")
        print(f"🏆 **Empresa mejor pagada:** {top_company} (S/ {top_company_salary:,.2f})")
        print(f"🏭 **Sector dominante:** {top_sector}")
        
        if 'universidad_principal' in self.df.columns:
            uni_data = self.df[self.df['universidad_principal'].notna()]
            if not uni_data.empty:
                top_uni = uni_data.groupby('universidad_principal')['salario_promedio'].mean().idxmax()
                print(f"🎓 **Universidad mejor pagada:** {top_uni}")
        
        # Tendencias
        print(f"\n📈 **TENDENCIAS CLAVE:**")
        print(f"   • El sector {top_sector} domina el mercado laboral")
        print(f"   • Los salarios varían entre S/ {self.df['salario_promedio'].min():,.0f} y S/ {self.df['salario_promedio'].max():,.0f}")
        
        senior_avg = self.df[self.df['seniority'] == 'Senior']['salario_promedio'].mean()
        junior_avg = self.df[self.df['seniority'] == 'Junior']['salario_promedio'].mean()
        if not pd.isna(senior_avg) and not pd.isna(junior_avg):
            premium = ((senior_avg - junior_avg) / junior_avg) * 100
            print(f"   • Posiciones Senior pagan {premium:.0f}% más que Junior")


def main():
    """Función principal con menú interactivo"""
    print("🎨 ANALIZADOR PROFESIONAL DE SALARIOS PERÚ")
    print("=" * 50)
    
    # Buscar archivos disponibles automáticamente
    import os
    import glob
    
    # Buscar archivos CSV y DB en el directorio actual
    csv_files = glob.glob("*.csv")
    db_files = glob.glob("*.db")
    
    data_files = []
    if csv_files:
        data_files.extend(csv_files)
    if db_files:
        data_files.extend(db_files)
    
    if data_files:
        print("📁 Archivos de datos encontrados:")
        for i, file in enumerate(data_files, 1):
            file_size = os.path.getsize(file) / 1024  # KB
            print(f"   {i}. {file} ({file_size:.1f} KB)")
        
        # Sugerir el archivo más completo por defecto
        if csv_files:
            # Priorizar archivo completo si existe
            completo_files = [f for f in csv_files if 'completo' in f]
            if completo_files:
                default_file = max(completo_files, key=os.path.getsize)  # El más grande
            else:
                default_file = max(csv_files, key=os.path.getsize)  # El más grande
        else:
            # Para DB también priorizar completo
            completo_db = [f for f in db_files if 'completo' in f]
            if completo_db:
                default_file = max(completo_db, key=os.path.getsize)
            else:
                default_file = max(db_files, key=os.path.getsize)
        
        print(f"\n💡 Archivo sugerido: {default_file}")
        data_source = input("📁 Ingresa el nombre del archivo o número (Enter para usar sugerido): ").strip()
        
        if not data_source:
            data_source = default_file
        elif data_source.isdigit():
            file_index = int(data_source) - 1
            if 0 <= file_index < len(data_files):
                data_source = data_files[file_index]
            else:
                print("❌ Número de archivo inválido, usando sugerido")
                data_source = default_file
    else:
        print("⚠️  No se encontraron archivos de datos en el directorio actual")
        data_source = input("📁 Ingresa la ruta completa del archivo de datos: ")
        if not data_source.strip():
            data_source = 'salarios_simple.csv'
    
    try:
        # Crear analizador
        analyzer = SalariosAnalyzer(data_source)
        
        while True:
            print(f"\n🎯 MENÚ DE VISUALIZACIONES")
            print("1. 🫧 Bubble Chart - Salario vs Tamaño de Empresa")
            print("2. 📊 Matriz de Correlaciones Interactiva")
            print("3. 📈 Distribución Salarial Avanzada por Sector")
            print("4. 🎓 Análisis Radar por Universidad")
            print("5. 🌡️ Mapa de Calor - Salarios por Puesto/Empresa")
            print("6. 🚀 Dashboard Profesional Completo")
            print("7. 📋 Resumen Ejecutivo")
            print("8. 🎨 Generar TODAS las visualizaciones")
            print("9. ❌ Salir")
            
            choice = input("\n👉 Selecciona una opción (1-9): ").strip()
            
            if choice == '1':
                analyzer.bubble_chart_salary_vs_company_size()
            elif choice == '2':
                analyzer.interactive_scatter_matrix()
            elif choice == '3':
                analyzer.advanced_salary_distribution_by_sector()
            elif choice == '4':
                analyzer.university_performance_radar()
            elif choice == '5':
                analyzer.salary_heatmap_by_position_and_company()
            elif choice == '6':
                analyzer.create_professional_dashboard()
            elif choice == '7':
                analyzer.generate_executive_summary()
            elif choice == '8':
                print("\n🎨 Generando todas las visualizaciones...")
                analyzer.bubble_chart_salary_vs_company_size()
                analyzer.interactive_scatter_matrix()
                analyzer.advanced_salary_distribution_by_sector()
                analyzer.university_performance_radar()
                analyzer.salary_heatmap_by_position_and_company()
                analyzer.create_professional_dashboard()
                analyzer.generate_executive_summary()
                print("\n✅ ¡Todas las visualizaciones generadas!")
            elif choice == '9':
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida. Intenta de nuevo.")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
    
    def resumen_general(self):
        """Genera resumen estadístico general"""
        print("\n" + "="*70)
        print("📈 RESUMEN ESTADÍSTICO GENERAL")
        print("="*70)
        
        # Información básica
        print(f"📝 Total de registros: {len(self.df):,}")
        print(f"🏢 Empresas únicas: {self.df['empresa'].nunique()}")
        print(f"💼 Puestos únicos: {self.df['puesto'].nunique()}")
        
        if 'salario_promedio' in self.df.columns:
            salarios = self.df['salario_promedio'].dropna()
            print(f"\n💰 ESTADÍSTICAS SALARIALES (S/):")
            print(f"   • Salario promedio: S/ {salarios.mean():,.2f}")
            print(f"   • Salario mediano: S/ {salarios.median():,.2f}")
            print(f"   • Salario mínimo: S/ {salarios.min():,.2f}")
            print(f"   • Salario máximo: S/ {salarios.max():,.2f}")
            print(f"   • Desviación estándar: S/ {salarios.std():,.2f}")
        
        # Distribución por categorías
        if 'categoria_salario' in self.df.columns:
            print(f"\n📊 DISTRIBUCIÓN POR CATEGORÍAS:")
            categoria_dist = self.df['categoria_salario'].value_counts()
            for categoria, count in categoria_dist.items():
                porcentaje = (count / len(self.df)) * 100
                print(f"   • {categoria}: {count} ({porcentaje:.1f}%)")
    
    def top_empresas_mejor_pagadas(self, top_n=15):
        """Analiza las empresas que mejor pagan"""
        print(f"\n🏆 TOP {top_n} EMPRESAS MEJOR PAGADAS")
        print("="*60)
        
        if 'salario_promedio' not in self.df.columns:
            print("❌ No hay datos de salarios disponibles")
            return
        
        # Calcular estadísticas por empresa
        empresa_stats = self.df.groupby('empresa').agg({
            'salario_promedio': ['mean', 'median', 'count', 'max'],
            'puesto': 'count'
        }).round(2)
        
        empresa_stats.columns = ['Salario_Promedio', 'Salario_Mediano', 
                               'Count_Salarios', 'Salario_Maximo', 'Total_Puestos']
        
        # Filtrar empresas con al menos 2 puestos para mayor confiabilidad
        empresa_stats = empresa_stats[empresa_stats['Total_Puestos'] >= 2]
        empresa_stats = empresa_stats.sort_values('Salario_Promedio', ascending=False)
        
        print(empresa_stats.head(top_n))
        
        # Visualización
        plt.figure(figsize=(12, 8))
        top_empresas = empresa_stats.head(top_n)
        
        plt.barh(range(len(top_empresas)), top_empresas['Salario_Promedio'])
        plt.yticks(range(len(top_empresas)), top_empresas.index)
        plt.xlabel('Salario Promedio (S/)')
        plt.title(f'Top {top_n} Empresas Mejor Pagadas')
        plt.gca().invert_yaxis()
        
        # Añadir valores en las barras
        for i, v in enumerate(top_empresas['Salario_Promedio']):
            plt.text(v + 200, i, f'S/ {v:,.0f}', va='center')
        
        plt.tight_layout()
        plt.savefig('top_empresas_salarios.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return empresa_stats.head(top_n)
    
    def analisis_por_universidades(self):
        """Analiza salarios por universidad"""
        print("\n🎓 ANÁLISIS POR UNIVERSIDADES")
        print("="*50)
        
        if 'universidad_principal' not in self.df.columns:
            print("❌ No hay datos de universidades disponibles")
            return
        
        # Filtrar registros con universidad
        df_uni = self.df[self.df['universidad_principal'].notna()].copy()
        
        if df_uni.empty:
            print("❌ No se encontraron datos de universidades")
            return
        
        print(f"📚 Registros con universidad: {len(df_uni)}")
        
        # Estadísticas por universidad
        uni_stats = df_uni.groupby('universidad_principal').agg({
            'salario_promedio': ['mean', 'median', 'count', 'max'],
            'empresa': 'nunique'
        }).round(2)
        
        uni_stats.columns = ['Salario_Promedio', 'Salario_Mediano', 
                           'Num_Profesionales', 'Salario_Maximo', 'Empresas_Distintas']
        
        uni_stats = uni_stats.sort_values('Salario_Promedio', ascending=False)
        
        print("\n🏆 RANKING DE UNIVERSIDADES POR SALARIO PROMEDIO:")
        print(uni_stats)
        
        # Visualización
        if len(uni_stats) > 1:
            plt.figure(figsize=(12, 6))
            uni_stats['Salario_Promedio'].plot(kind='bar')
            plt.title('Salario Promedio por Universidad')
            plt.ylabel('Salario Promedio (S/)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('salarios_por_universidad.png', dpi=300, bbox_inches='tight')
            plt.show()
        
        return uni_stats
    
    def top_puestos_mejor_pagados(self, top_n=20):
        """Analiza los puestos mejor pagados"""
        print(f"\n💼 TOP {top_n} PUESTOS MEJOR PAGADOS")
        print("="*60)
        
        if 'salario_promedio' not in self.df.columns:
            print("❌ No hay datos de salarios disponibles")
            return
        
        # Top puestos individuales
        top_puestos = self.df.nlargest(top_n, 'salario_promedio')[
            ['puesto', 'empresa', 'salario_promedio', 'universidad_principal']
        ].copy()
        
        print("\n🥇 PUESTOS INDIVIDUALES MEJOR PAGADOS:")
        for idx, row in top_puestos.iterrows():
            universidad = row['universidad_principal'] if pd.notna(row['universidad_principal']) else 'No especificada'
            print(f"{row.name+1:2d}. {row['puesto']}")
            print(f"    💰 S/ {row['salario_promedio']:,.2f} | 🏢 {row['empresa']} | 🎓 {universidad}")
        
        # Promedio por tipo de puesto
        puesto_stats = self.df.groupby('puesto').agg({
            'salario_promedio': ['mean', 'count', 'max'],
            'empresa': 'nunique'
        }).round(2)
        
        puesto_stats.columns = ['Salario_Promedio', 'Apariciones', 'Salario_Maximo', 'Empresas']
        puesto_stats = puesto_stats[puesto_stats['Apariciones'] >= 2]  # Al menos 2 apariciones
        puesto_stats = puesto_stats.sort_values('Salario_Promedio', ascending=False)
        
        print(f"\n📊 TOP PUESTOS POR PROMEDIO (min. 2 apariciones):")
        print(puesto_stats.head(15))
        
        return top_puestos, puesto_stats
    
    def analisis_sectores(self):
        """Analiza salarios por sector/industria inferido"""
        print("\n🏭 ANÁLISIS POR SECTORES")
        print("="*40)
        
        # Definir sectores basado en nombres de empresas
        sectores = {
            'Banca y Finanzas': ['bcp', 'bbva', 'interbank', 'credicorp', 'banco'],
            'Tecnología': ['yape', 'culqi', 'google', 'microsoft', 'tech'],
            'Consumo Masivo': ['alicorp', 'procter', 'gamble', 'unilever', 'nestle'],
            'Consultoría': ['ey', 'deloitte', 'pwc', 'kpmg', 'mckinsey'],
            'Telecomunicaciones': ['entel', 'movistar', 'claro', 'telecom'],
            'Seguros': ['rimac', 'seguros', 'insurance'],
            'Bebidas': ['ab inbev', 'coca cola', 'pepsi'],
            'Cosmética': ['loreal', "l'oreal", 'cosmetic']
        }
        
        # Asignar sector a cada empresa
        self.df['sector'] = 'Otros'
        
        for sector, keywords in sectores.items():
            for keyword in keywords:
                mask = self.df['empresa'].str.lower().str.contains(keyword, na=False)
                self.df.loc[mask, 'sector'] = sector
        
        # Estadísticas por sector
        sector_stats = self.df.groupby('sector').agg({
            'salario_promedio': ['mean', 'median', 'count'],
            'empresa': 'nunique'
        }).round(2)
        
        sector_stats.columns = ['Salario_Promedio', 'Salario_Mediano', 'Num_Puestos', 'Num_Empresas']
        sector_stats = sector_stats.sort_values('Salario_Promedio', ascending=False)
        
        print("💰 SALARIOS PROMEDIO POR SECTOR:")
        print(sector_stats)
        
        # Visualización
        plt.figure(figsize=(12, 8))
        sector_stats['Salario_Promedio'].plot(kind='bar')
        plt.title('Salario Promedio por Sector')
        plt.ylabel('Salario Promedio (S/)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('salarios_por_sector.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return sector_stats
    
    def correlaciones_y_insights(self):
        """Análisis de correlaciones e insights adicionales"""
        print("\n🔍 CORRELACIONES E INSIGHTS")
        print("="*45)
        
        # Análisis de dispersión de salarios por empresa
        if 'salario_promedio' in self.df.columns:
            empresa_dispersion = self.df.groupby('empresa')['salario_promedio'].agg(['std', 'mean', 'count'])
            empresa_dispersion = empresa_dispersion[empresa_dispersion['count'] >= 3]
            empresa_dispersion['coef_variacion'] = empresa_dispersion['std'] / empresa_dispersion['mean']
            empresa_dispersion = empresa_dispersion.sort_values('coef_variacion', ascending=False)
            
            print("📊 EMPRESAS CON MAYOR DISPERSIÓN SALARIAL:")
            print("(Coeficiente de variación = Desviación estándar / Media)")
            print(empresa_dispersion.head(10))
        
        # Análisis de palabras clave en puestos mejor pagados
        if 'puesto' in self.df.columns and 'salario_promedio' in self.df.columns:
            top_20_percent = self.df.nlargest(int(len(self.df) * 0.2), 'salario_promedio')
            
            palabras_comunes = []
            for puesto in top_20_percent['puesto']:
                palabras = puesto.lower().split()
                palabras_comunes.extend(palabras)
            
            from collections import Counter
            contador_palabras = Counter(palabras_comunes)
            
            print(f"\n🔤 PALABRAS MÁS COMUNES EN EL TOP 20% DE PUESTOS:")
            for palabra, frecuencia in contador_palabras.most_common(15):
                if len(palabra) > 3:  # Filtrar palabras muy cortas
                    print(f"   • {palabra}: {frecuencia} veces")
    
    def generar_reporte_completo(self, output_file='reporte_salarios.txt'):
        """Genera un reporte completo en archivo de texto"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("REPORTE COMPLETO DE ANÁLISIS DE SALARIOS PERÚ\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Redirigir print al archivo
            import sys
            original_stdout = sys.stdout
            sys.stdout = f
            
            try:
                self.resumen_general()
                self.top_empresas_mejor_pagadas()
                self.analisis_por_universidades()
                self.top_puestos_mejor_pagados()
                self.analisis_sectores()
                self.correlaciones_y_insights()
            finally:
                sys.stdout = original_stdout
        
        print(f"✅ Reporte completo guardado en: {output_file}")
    
    def dashboard_interactivo(self):
        """Crea un dashboard visual interactivo"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Distribución de salarios
        if 'salario_promedio' in self.df.columns:
            self.df['salario_promedio'].hist(bins=30, ax=axes[0,0])
            axes[0,0].set_title('Distribución de Salarios')
            axes[0,0].set_xlabel('Salario (S/)')
            axes[0,0].set_ylabel('Frecuencia')
        
        # 2. Top 10 empresas
        if 'empresa' in self.df.columns:
            top_empresas = self.df['empresa'].value_counts().head(10)
            top_empresas.plot(kind='barh', ax=axes[0,1])
            axes[0,1].set_title('Top 10 Empresas por Número de Puestos')
        
        # 3. Boxplot de salarios por categoría
        if 'categoria_salario' in self.df.columns and 'salario_promedio' in self.df.columns:
            self.df.boxplot(column='salario_promedio', by='categoria_salario', ax=axes[1,0])
            axes[1,0].set_title('Distribución de Salarios por Categoría')
            plt.suptitle('')  # Remover título automático
        
        # 4. Salarios promedio por sector
        if 'sector' in self.df.columns:
            sector_avg = self.df.groupby('sector')['salario_promedio'].mean()
            sector_avg.plot(kind='bar', ax=axes[1,1])
            axes[1,1].set_title('Salario Promedio por Sector')
            axes[1,1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('dashboard_salarios.png', dpi=300, bbox_inches='tight')
        plt.show()


def main_simple():
    """Función principal simplificada para ejecutar análisis"""
    print("📊 ANALIZADOR DE SALARIOS PERÚ")
    print("=" * 40)
    
    # Buscar archivos disponibles
    import os
    import glob
    
    csv_files = glob.glob("*.csv")
    db_files = glob.glob("*.db")
    
    if csv_files or db_files:
        # Priorizar archivo completo si existe
        if csv_files:
            completo_files = [f for f in csv_files if 'completo' in f]
            if completo_files:
                data_source = max(completo_files, key=os.path.getsize)
            else:
                data_source = max(csv_files, key=os.path.getsize)
            print(f"📁 Usando archivo encontrado: {data_source}")
        else:
            completo_db = [f for f in db_files if 'completo' in f]
            if completo_db:
                data_source = max(completo_db, key=os.path.getsize)
            else:
                data_source = max(db_files, key=os.path.getsize)
            print(f"📁 Usando base de datos encontrada: {data_source}")
    else:
        data_source = input("Ingresa la ruta del archivo de datos (CSV o SQLite): ")
        if not data_source:
            print("❌ No se encontraron archivos de datos")
            return
    
    try:
        # Crear analizador
        analyzer = SalariosAnalyzer(data_source)
        
        # Ejecutar análisis completo
        analyzer.resumen_general()
        analyzer.top_empresas_mejor_pagadas()
        analyzer.analisis_por_universidades()
        analyzer.top_puestos_mejor_pagados()
        analyzer.analisis_sectores()
        analyzer.correlaciones_y_insights()
        
        # Generar dashboard
        analyzer.dashboard_interactivo()
        
        # Generar reporte
        analyzer.generar_reporte_completo()
        
        print("\n🎉 Análisis completado exitosamente!")
        print("\nArchivos generados:")
        print("- dashboard_salarios.png")
        print("- top_empresas_salarios.png")
        print("- salarios_por_universidad.png")
        print("- salarios_por_sector.png")
        print("- reporte_salarios.txt")
        
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")


if __name__ == "__main__":
    main()