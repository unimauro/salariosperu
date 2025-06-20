#!/usr/bin/env python3
"""
Dashboard Ejecutivo Mejorado - Análisis Avanzado de Salarios
Con análisis específicos de TI, Ventas/Marketing y puestos no gerenciales
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
import re

class DashboardEjecutivoMejorado:
    def __init__(self, data_source=None):
        """Inicializar el dashboard ejecutivo mejorado"""
        
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
        
        print(f"📊 Dashboard Ejecutivo Mejorado inicializado")
        print(f"📁 Datos: {data_source}")
        print(f"📈 Registros: {len(self.df):,}")
        
    def classify_job_categories(self, df):
        """Clasificar puestos en categorías específicas"""
        def classify_ti(puesto):
            puesto_lower = str(puesto).lower()
            ti_keywords = [
                'desarrollador', 'developer', 'programador', 'programmer',
                'ingeniero de software', 'software engineer', 'devops',
                'analista de sistemas', 'systems analyst', 'qa', 'testing',
                'arquitecto de software', 'tech lead', 'scrum master',
                'data scientist', 'data analyst', 'big data', 'machine learning',
                'frontend', 'backend', 'fullstack', 'mobile developer',
                'cybersecurity', 'seguridad informatica', 'cloud', 'aws', 'azure'
            ]
            return any(keyword in puesto_lower for keyword in ti_keywords)
        
        def classify_ventas_marketing(puesto):
            puesto_lower = str(puesto).lower()
            
            # Primero verificar si es gerencial (excluir)
            gerencial_keywords = [
                'gerente', 'director', 'jefe', 'head', 'chief', 'presidente',
                'ceo', 'cfo', 'cto', 'manager', 'supervisor', 'coordinador',
                'lead', 'líder', 'encargado'
            ]
            
            if any(keyword in puesto_lower for keyword in gerencial_keywords):
                return False  # Excluir puestos gerenciales
            
            # Luego verificar si es ventas/marketing
            ventas_keywords = [
                'vendedor', 'ventas', 'sales', 'comercial', 'account manager',
                'business development', 'key account', 'inside sales',
                'marketing', 'brand', 'digital marketing', 'social media',
                'community manager', 'seo', 'sem', 'publicidad', 'advertising',
                'market research', 'product marketing', 'growth'
            ]
            return any(keyword in puesto_lower for keyword in ventas_keywords)
        
        def classify_gerencial(puesto):
            puesto_lower = str(puesto).lower()
            gerencial_keywords = [
                'gerente', 'director', 'jefe', 'head', 'chief', 'presidente',
                'ceo', 'cfo', 'cto', 'manager', 'supervisor', 'coordinador',
                'lead', 'líder', 'encargado'
            ]
            return any(keyword in puesto_lower for keyword in gerencial_keywords)
        
        df['es_ti'] = df['puesto'].apply(classify_ti)
        df['es_ventas_marketing'] = df['puesto'].apply(classify_ventas_marketing)
        df['es_gerencial'] = df['puesto'].apply(classify_gerencial)
        df['es_no_gerencial'] = ~df['es_gerencial']
        
        return df
    
    def create_ti_quartiles_chart(self, df):
        """Crear análisis de quartiles para puestos TI agrupados por rangos"""
        ti_jobs = df[df['es_ti'] == True].copy()
        
        if len(ti_jobs) == 0:
            return "<p>No se encontraron puestos de TI en el dataset</p>"
        
        # Clasificar puestos TI en subcategorías más generales
        def classify_ti_level(puesto):
            puesto_lower = str(puesto).lower()
            
            if any(word in puesto_lower for word in ['senior', 'sr.', 'lead', 'principal', 'architect']):
                return 'Senior TI'
            elif any(word in puesto_lower for word in ['data scientist', 'data analyst', 'big data', 'machine learning']):
                return 'Data Science/Analytics'
            elif any(word in puesto_lower for word in ['cloud', 'devops', 'infrastructure', 'aws', 'azure']):
                return 'Cloud/DevOps'
            elif any(word in puesto_lower for word in ['cybersecurity', 'security', 'seguridad']):
                return 'Cybersecurity'
            elif any(word in puesto_lower for word in ['frontend', 'backend', 'fullstack', 'mobile', 'web']):
                return 'Development'
            elif any(word in puesto_lower for word in ['qa', 'testing', 'quality']):
                return 'QA/Testing'
            elif any(word in puesto_lower for word in ['tech lead', 'scrum master', 'product owner']):
                return 'Tech Leadership'
            else:
                return 'TI General'
        
        ti_jobs['ti_category'] = ti_jobs['puesto'].apply(classify_ti_level)
        
        # Calcular quartiles por categoría TI
        quartiles_data = []
        
        for category in ti_jobs['ti_category'].unique():
            category_salaries = ti_jobs[ti_jobs['ti_category'] == category]['salario_promedio']
            
            if len(category_salaries) >= 3:  # Mínimo 3 salarios para quartiles
                quartiles = {
                    'category': category,
                    'count': len(category_salaries),
                    'min': category_salaries.min(),
                    'q1': category_salaries.quantile(0.25),
                    'median': category_salaries.median(),
                    'q3': category_salaries.quantile(0.75),
                    'max': category_salaries.max(),
                    'mean': category_salaries.mean()
                }
                quartiles_data.append(quartiles)
        
        if not quartiles_data:
            return "<p>No hay suficientes datos para análisis de quartiles TI</p>"
        
        quartiles_df = pd.DataFrame(quartiles_data)
        quartiles_df = quartiles_df.sort_values('median', ascending=True)
        
        # Crear gráfico de quartiles horizontal estilo corporativo
        fig = go.Figure()
        
        for i, row in quartiles_df.iterrows():
            # Barra principal (Q1 a Q3)
            fig.add_trace(go.Bar(
                name=f"{row['category']} (Q1-Q3)",
                y=[row['category']],
                x=[row['q3'] - row['q1']],
                base=row['q1'],
                orientation='h',
                marker_color='#2E8B57',
                opacity=0.8,
                showlegend=False,
                text=f"Q1-Q3: S/ {row['q1']:,.0f} - S/ {row['q3']:,.0f}",
                textposition='inside'
            ))
            
            # Línea de min a Q1
            fig.add_trace(go.Scatter(
                x=[row['min'], row['q1']],
                y=[row['category'], row['category']],
                mode='lines',
                line=dict(color='#1F5F3F', width=3),
                showlegend=False
            ))
            
            # Línea de Q3 a max
            fig.add_trace(go.Scatter(
                x=[row['q3'], row['max']],
                y=[row['category'], row['category']],
                mode='lines',
                line=dict(color='#1F5F3F', width=3),
                showlegend=False
            ))
            
            # Punto para la mediana
            fig.add_trace(go.Scatter(
                x=[row['median']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='orange', size=12, symbol='circle', line=dict(color='white', width=2)),
                name='Mediana' if i == 0 else '',
                showlegend=True if i == 0 else False,
                text=f"Mediana: S/ {row['median']:,.0f}",
                textposition='top center'
            ))
            
            # Puntos para min y max
            fig.add_trace(go.Scatter(
                x=[row['min']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='#1F5F3F', size=8, symbol='diamond'),
                name='Min/Max' if i == 0 else '',
                showlegend=True if i == 0 else False,
                text=f"Min: S/ {row['min']:,.0f}",
                textposition='bottom center'
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['max']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='#1F5F3F', size=8, symbol='diamond'),
                showlegend=False,
                text=f"Max: S/ {row['max']:,.0f}",
                textposition='bottom center'
            ))
        
        fig.update_layout(
            title='Análisis de Quartiles - Puestos TI por Categoría<br><sub>Distribución salarial (Min, Q1, Mediana, Q3, Max)</sub>',
            xaxis_title='Salario (S/)',
            yaxis_title='Categoría TI',
            height=500,
            template="plotly_white",
            title_x=0.5,
            xaxis=dict(tickformat=',.0f'),
            yaxis={'categoryorder':'total ascending'},
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="ti-quartiles")
    
    def create_ventas_marketing_quartiles_chart(self, df):
        """Crear análisis de quartiles para puestos Ventas/Marketing agrupados"""
        vm_jobs = df[df['es_ventas_marketing'] == True].copy()
        
        if len(vm_jobs) == 0:
            return "<p>No se encontraron puestos de Ventas/Marketing en el dataset</p>"
        
        # Clasificar puestos Ventas/Marketing en subcategorías (excluyendo gerenciales)
        def classify_vm_level(puesto):
            puesto_lower = str(puesto).lower()
            
            # Verificar que no sea gerencial (ya fueron filtrados en classify_ventas_marketing)
            if any(word in puesto_lower for word in ['senior', 'sr.', 'principal']):
                return 'Senior Ventas/Marketing'
            elif any(word in puesto_lower for word in ['account manager', 'key account', 'business development']):
                return 'Account Management'
            elif any(word in puesto_lower for word in ['digital marketing', 'social media', 'seo', 'sem']):
                return 'Marketing Digital'
            elif any(word in puesto_lower for word in ['inside sales', 'sales representative', 'vendedor']):
                return 'Ventas Directas'
            elif any(word in puesto_lower for word in ['brand', 'product marketing']):
                return 'Brand/Product Marketing'
            elif any(word in puesto_lower for word in ['market research', 'analyst', 'research']):
                return 'Research/Analytics'
            else:
                return 'Ventas/Marketing General'
        
        vm_jobs['vm_category'] = vm_jobs['puesto'].apply(classify_vm_level)
        
        # Calcular quartiles por categoría
        quartiles_data = []
        
        for category in vm_jobs['vm_category'].unique():
            category_salaries = vm_jobs[vm_jobs['vm_category'] == category]['salario_promedio']
            
            if len(category_salaries) >= 2:  # Mínimo 2 salarios
                quartiles = {
                    'category': category,
                    'count': len(category_salaries),
                    'min': category_salaries.min(),
                    'q1': category_salaries.quantile(0.25),
                    'median': category_salaries.median(),
                    'q3': category_salaries.quantile(0.75),
                    'max': category_salaries.max(),
                    'mean': category_salaries.mean()
                }
                quartiles_data.append(quartiles)
        
        if not quartiles_data:
            return "<p>No hay suficientes datos para análisis de quartiles Ventas/Marketing</p>"
        
        quartiles_df = pd.DataFrame(quartiles_data)
        quartiles_df = quartiles_df.sort_values('median', ascending=True)
        
        # Crear gráfico de quartiles horizontal
        fig = go.Figure()
        
        for i, row in quartiles_df.iterrows():
            # Barra principal (Q1 a Q3)
            fig.add_trace(go.Bar(
                name=f"{row['category']} (Q1-Q3)",
                y=[row['category']],
                x=[row['q3'] - row['q1']],
                base=row['q1'],
                orientation='h',
                marker_color='#FF6347',
                opacity=0.8,
                showlegend=False,
                text=f"Q1-Q3: S/ {row['q1']:,.0f} - S/ {row['q3']:,.0f}",
                textposition='inside'
            ))
            
            # Líneas para rangos
            fig.add_trace(go.Scatter(
                x=[row['min'], row['q1']],
                y=[row['category'], row['category']],
                mode='lines',
                line=dict(color='#CC4125', width=3),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['q3'], row['max']],
                y=[row['category'], row['category']],
                mode='lines',
                line=dict(color='#CC4125', width=3),
                showlegend=False
            ))
            
            # Punto mediana
            fig.add_trace(go.Scatter(
                x=[row['median']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='orange', size=12, symbol='circle', line=dict(color='white', width=2)),
                name='Mediana' if i == 0 else '',
                showlegend=True if i == 0 else False
            ))
            
            # Puntos min/max
            fig.add_trace(go.Scatter(
                x=[row['min']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='#CC4125', size=8, symbol='diamond'),
                name='Min/Max' if i == 0 else '',
                showlegend=True if i == 0 else False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['max']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='#CC4125', size=8, symbol='diamond'),
                showlegend=False
            ))
        
        fig.update_layout(
            title='Análisis de Quartiles - Ventas/Marketing por Categoría<br><sub>Distribución salarial (Min, Q1, Mediana, Q3, Max)</sub>',
            xaxis_title='Salario (S/)',
            yaxis_title='Categoría Ventas/Marketing',
            height=500,
            template="plotly_white",
            title_x=0.5,
            xaxis=dict(tickformat=',.0f'),
            yaxis={'categoryorder':'total ascending'}
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="vm-quartiles")
    
    def create_ti_analysis_chart(self, df):
        """Crear análisis de puestos TI con gráfico de quartiles (reemplaza barras específicas)"""
        return self.create_ti_quartiles_chart(df)
    
    def create_ventas_marketing_chart(self, df):
        """Crear análisis de puestos Ventas/Marketing con gráfico de quartiles"""
        return self.create_ventas_marketing_quartiles_chart(df)
    
    def create_mineria_quartiles_chart(self, df):
        """Crear análisis de quartiles para puestos de Minería por cargos principales"""
        if len(df) == 0:
            return "<p>No se encontraron datos para análisis de minería</p>"
        
        # Filtrar por sector minería
        mineria_keywords = ['minería', 'mineria', 'mining', 'extractiva']
        mineria_jobs = df[df['sector'].str.lower().str.contains('|'.join(mineria_keywords), na=False)].copy()
        
        if len(mineria_jobs) == 0:
            return "<p>No se encontraron puestos en el sector minería</p>"
        
        # Clasificar puestos de minería por cargos principales
        def classify_mineria_role(puesto):
            puesto_lower = str(puesto).lower()
            
            if any(word in puesto_lower for word in ['ingeniero minas', 'mining engineer', 'geólogo', 'geology']):
                return 'Ingeniería de Minas y Geología'
            elif any(word in puesto_lower for word in ['operaciones', 'operations', 'planta', 'plant', 'producción']):
                return 'Operaciones y Producción'
            elif any(word in puesto_lower for word in ['seguridad', 'safety', 'medio ambiente', 'environmental']):
                return 'Seguridad y Medio Ambiente'
            elif any(word in puesto_lower for word in ['mantenimiento', 'maintenance', 'mecánico', 'eléctrico']):
                return 'Mantenimiento'
            elif any(word in puesto_lower for word in ['exploración', 'exploration', 'prospección']):
                return 'Exploración'
            elif any(word in puesto_lower for word in ['metalurgia', 'metallurgy', 'procesamiento']):
                return 'Metalurgia y Procesamiento'
            else:
                return 'Otros Cargos Minería'
        
        mineria_jobs['mineria_role'] = mineria_jobs['puesto'].apply(classify_mineria_role)
        
        # Calcular quartiles por cargo
        quartiles_data = []
        
        for role in mineria_jobs['mineria_role'].unique():
            role_salaries = mineria_jobs[mineria_jobs['mineria_role'] == role]['salario_promedio']
            
            if len(role_salaries) >= 2:  # Mínimo 2 salarios
                quartiles = {
                    'category': role,
                    'count': len(role_salaries),
                    'min': role_salaries.min(),
                    'q1': role_salaries.quantile(0.25),
                    'median': role_salaries.median(),
                    'q3': role_salaries.quantile(0.75),
                    'max': role_salaries.max(),
                    'mean': role_salaries.mean()
                }
                quartiles_data.append(quartiles)
        
        if not quartiles_data:
            return "<p>No hay suficientes datos para análisis de quartiles en minería</p>"
        
        quartiles_df = pd.DataFrame(quartiles_data)
        quartiles_df = quartiles_df.sort_values('median', ascending=True)
        
        # Crear gráfico de quartiles horizontal
        fig = go.Figure()
        
        for i, row in quartiles_df.iterrows():
            # Barra principal (Q1 a Q3)
            fig.add_trace(go.Bar(
                name=f"{row['category']} (Q1-Q3)",
                y=[row['category']],
                x=[row['q3'] - row['q1']],
                base=row['q1'],
                orientation='h',
                marker_color='#8B4513',  # Marrón minería
                opacity=0.8,
                showlegend=False,
                text=f"Q1-Q3: S/ {row['q1']:,.0f} - S/ {row['q3']:,.0f}",
                textposition='inside'
            ))
            
            # Líneas y puntos como en el análisis TI
            fig.add_trace(go.Scatter(
                x=[row['min'], row['q1']],
                y=[row['category'], row['category']],
                mode='lines',
                line=dict(color='#654321', width=3),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['q3'], row['max']],
                y=[row['category'], row['category']],
                mode='lines',
                line=dict(color='#654321', width=3),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['median']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='orange', size=12, symbol='circle', line=dict(color='white', width=2)),
                name='Mediana' if i == 0 else '',
                showlegend=True if i == 0 else False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['min']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='#654321', size=8, symbol='diamond'),
                name='Min/Max' if i == 0 else '',
                showlegend=True if i == 0 else False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['max']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='#654321', size=8, symbol='diamond'),
                showlegend=False
            ))
        
        fig.update_layout(
            title='⛏️ Análisis Salarial Minería - Distribución de Sueldos por Cargo Principal<br><sub>Quartiles salariales por especialización minera (Min, Q1, Mediana, Q3, Max)</sub>',
            xaxis_title='Salario (S/)',
            yaxis_title='Cargo Minería',
            height=500,
            template="plotly_white",
            title_x=0.5,
            xaxis=dict(tickformat=',.0f'),
            yaxis={'categoryorder':'total ascending'},
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="mineria-quartiles")

    def create_agroindustria_quartiles_chart(self, df):
        """Crear análisis de quartiles para puestos de Agroindustria por cargos principales"""
        if len(df) == 0:
            return "<p>No se encontraron datos para análisis de agroindustria</p>"
        
        # Filtrar por sector agroindustria
        agro_keywords = ['agricultura', 'agroindustria', 'agro', 'alimentos']
        agro_jobs = df[df['sector'].str.lower().str.contains('|'.join(agro_keywords), na=False)].copy()
        
        if len(agro_jobs) == 0:
            return "<p>No se encontraron puestos en el sector agroindustria</p>"
        
        # Clasificar puestos de agroindustria por cargos principales
        def classify_agro_role(puesto):
            puesto_lower = str(puesto).lower()
            
            if any(word in puesto_lower for word in ['agrónomo', 'agronomy', 'cultivo', 'crop']):
                return 'Agronomía y Cultivos'
            elif any(word in puesto_lower for word in ['producción', 'production', 'planta', 'manufacturing']):
                return 'Producción y Manufactura'
            elif any(word in puesto_lower for word in ['calidad', 'quality', 'control', 'aseguramiento']):
                return 'Control de Calidad'
            elif any(word in puesto_lower for word in ['comercial', 'ventas', 'marketing', 'trade']):
                return 'Comercial y Marketing'
            elif any(word in puesto_lower for word in ['logística', 'logistics', 'supply', 'cadena']):
                return 'Logística y Supply Chain'
            elif any(word in puesto_lower for word in ['investigación', 'research', 'desarrollo', 'innovation']):
                return 'I+D e Innovación'
            else:
                return 'Otros Cargos Agroindustria'
        
        agro_jobs['agro_role'] = agro_jobs['puesto'].apply(classify_agro_role)
        
        # Calcular quartiles por cargo
        quartiles_data = []
        
        for role in agro_jobs['agro_role'].unique():
            role_salaries = agro_jobs[agro_jobs['agro_role'] == role]['salario_promedio']
            
            if len(role_salaries) >= 2:  # Mínimo 2 salarios
                quartiles = {
                    'category': role,
                    'count': len(role_salaries),
                    'min': role_salaries.min(),
                    'q1': role_salaries.quantile(0.25),
                    'median': role_salaries.median(),
                    'q3': role_salaries.quantile(0.75),
                    'max': role_salaries.max(),
                    'mean': role_salaries.mean()
                }
                quartiles_data.append(quartiles)
        
        if not quartiles_data:
            return "<p>No hay suficientes datos para análisis de quartiles en agroindustria</p>"
        
        quartiles_df = pd.DataFrame(quartiles_data)
        quartiles_df = quartiles_df.sort_values('median', ascending=True)
        
        # Crear gráfico de quartiles horizontal
        fig = go.Figure()
        
        for i, row in quartiles_df.iterrows():
            # Barra principal (Q1 a Q3)
            fig.add_trace(go.Bar(
                name=f"{row['category']} (Q1-Q3)",
                y=[row['category']],
                x=[row['q3'] - row['q1']],
                base=row['q1'],
                orientation='h',
                marker_color='#228B22',  # Verde agroindustria
                opacity=0.8,
                showlegend=False,
                text=f"Q1-Q3: S/ {row['q1']:,.0f} - S/ {row['q3']:,.0f}",
                textposition='inside'
            ))
            
            # Líneas y puntos
            fig.add_trace(go.Scatter(
                x=[row['min'], row['q1']],
                y=[row['category'], row['category']],
                mode='lines',
                line=dict(color='#006400', width=3),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['q3'], row['max']],
                y=[row['category'], row['category']],
                mode='lines',
                line=dict(color='#006400', width=3),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['median']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='orange', size=12, symbol='circle', line=dict(color='white', width=2)),
                name='Mediana' if i == 0 else '',
                showlegend=True if i == 0 else False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['min']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='#006400', size=8, symbol='diamond'),
                name='Min/Max' if i == 0 else '',
                showlegend=True if i == 0 else False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['max']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='#006400', size=8, symbol='diamond'),
                showlegend=False
            ))
        
        fig.update_layout(
            title='🌾 Análisis Salarial Agroindustria - Distribución de Sueldos por Cargo Principal<br><sub>Quartiles salariales por especialización agroindustrial (Min, Q1, Mediana, Q3, Max)</sub>',
            xaxis_title='Salario (S/)',
            yaxis_title='Cargo Agroindustria',
            height=500,
            template="plotly_white",
            title_x=0.5,
            xaxis=dict(tickformat=',.0f'),
            yaxis={'categoryorder':'total ascending'},
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="agroindustria-quartiles")
    
    def create_no_gerencial_chart(self, df):
        """Crear análisis de puestos no gerenciales con gráfico de barras mejorado"""
        no_ger_jobs = df[df['es_no_gerencial'] == True].copy()
        
        if len(no_ger_jobs) == 0:
            return "<p>No se encontraron puestos no gerenciales en el dataset</p>"
        
        # Agrupar por puesto no gerencial y obtener más información
        no_ger_analysis = no_ger_jobs.groupby('puesto').agg({
            'salario_promedio': 'mean',
            'empresa': ['nunique', 'first'],
            'sector': 'first'
        }).round(0)
        
        no_ger_analysis.columns = ['salario_promedio', 'total_empresas', 'empresa_ejemplo', 'sector']
        no_ger_analysis = no_ger_analysis.sort_values('salario_promedio', ascending=False).head(15)
        
        # Crear gráfico de barras horizontal más limpio
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=no_ger_analysis.index,
            x=no_ger_analysis['salario_promedio'],
            orientation='h',
            marker=dict(
                color='#2E86AB',
                opacity=0.8,
                line=dict(color='white', width=1)
            ),
            text=[f'S/ {val:,.0f}' for val in no_ger_analysis['salario_promedio']],
            textposition='outside',
            textfont=dict(size=11, color='#2c3e50'),
            hovertemplate='<b>%{y}</b><br>' +
                         'Salario: S/ %{x:,.0f}<br>' +
                         'Empresas: %{customdata[0]}<br>' +
                         'Sector: %{customdata[1]}<br>' +
                         'Ejemplo: %{customdata[2]}<br>' +
                         '<extra></extra>',
            customdata=list(zip(no_ger_analysis['total_empresas'], 
                               no_ger_analysis['sector'],
                               no_ger_analysis['empresa_ejemplo']))
        ))
        
        fig.update_layout(
            title='🏆 Top 15 Puestos No Gerenciales Mejor Pagados<br><sub>💰 Ordenados por salario promedio descendente</sub>',
            xaxis_title='💰 Salario Promedio (S/)',
            yaxis_title='',
            height=650,
            template="plotly_white",
            title_x=0.5,
            margin=dict(l=300, r=100, t=100, b=80),  # Más margen izquierdo para las etiquetas
            xaxis=dict(
                tickformat=',.0f',
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            yaxis=dict(
                showgrid=False,
                tickfont=dict(size=10)
            ),
            showlegend=False
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="no-ger-chart")
    
    def create_no_gerencial_bubble_chart(self, df):
        """Crear gráfico de burbujas mejorado para puestos no gerenciales"""
        no_ger_jobs = df[df['es_no_gerencial'] == True].copy()
        
        if len(no_ger_jobs) == 0:
            return "<p>No se encontraron puestos no gerenciales para el análisis de burbujas</p>"
        
        # Agrupar por empresa para puestos no gerenciales
        bubble_data = no_ger_jobs.groupby(['empresa', 'sector']).agg({
            'salario_promedio': 'mean',
            'puesto': 'count'
        }).reset_index()
        
        bubble_data = bubble_data[bubble_data['puesto'] >= 2]  # Al menos 2 puestos
        bubble_data = bubble_data.sort_values('salario_promedio', ascending=False).head(25)
        
        # Crear gráfico de burbujas con Plotly Go para mejor control
        fig = go.Figure()
        
        # Definir colores por sector
        sectores_unicos = bubble_data['sector'].unique()
        colores = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#F4A460', '#98D8E8']
        color_map = {sector: colores[i % len(colores)] for i, sector in enumerate(sectores_unicos)}
        
        for sector in sectores_unicos:
            sector_data = bubble_data[bubble_data['sector'] == sector]
            
            fig.add_trace(go.Scatter(
                x=sector_data['puesto'],
                y=sector_data['salario_promedio'],
                mode='markers+text',
                marker=dict(
                    size=sector_data['puesto'],  # Tamaño proporcional
                    color=color_map[sector],
                    opacity=0.7,
                    line=dict(width=2, color='white'),
                    sizemin=15,
                    sizeref=0.1,  # Factor de escala para el tamaño
                    sizemode='diameter'
                ),
                text=sector_data['empresa'].str[:15] + '...',  # Nombres truncados
                textposition='middle center',
                textfont=dict(size=9, color='white', family='Arial Black'),
                name=sector,
                hovertemplate='<b>%{hovertext}</b><br>' +
                             '💰 Salario Promedio: S/ %{y:,.0f}<br>' +
                             '👥 Puestos No Gerenciales: %{x}<br>' +
                             '🏭 Sector: ' + sector + '<br>' +
                             '<extra></extra>',
                hovertext=sector_data['empresa']
            ))
        
        fig.update_layout(
            title='🔵 Análisis de Burbujas - Empresas con Múltiples Puestos No Gerenciales<br><sub>💰 Tamaño de burbuja = Cantidad de puestos | 🎨 Color = Sector industrial</sub>',
            xaxis_title='👥 Número de Puestos No Gerenciales',
            yaxis_title='💰 Salario Promedio (S/)',
            height=600,
            template="plotly_white",
            title_x=0.5,
            xaxis=dict(
                tickformat='d',
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                range=[1.5, bubble_data['puesto'].max() + 0.5]
            ),
            yaxis=dict(
                tickformat=',.0f',
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            ),
            showlegend=True,
            plot_bgcolor='rgba(248,249,250,0.8)'
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="bubble-no-ger")

    def create_gerencial_bubble_chart(self, df):
        """Crear gráfico de burbujas para puestos netamente gerenciales"""
        gerencial_jobs = df[df['es_gerencial'] == True].copy()
        
        if len(gerencial_jobs) == 0:
            return "<p>No se encontraron puestos gerenciales en el dataset</p>"
        
        # Clasificar puestos gerenciales por nivel jerárquico
        def classify_gerencial_level(puesto):
            puesto_lower = str(puesto).lower()
            
            if any(word in puesto_lower for word in ['ceo', 'presidente', 'chief executive', 'director general']):
                return 'C-Level/Presidencia'
            elif any(word in puesto_lower for word in ['cfo', 'cto', 'coo', 'chief']):
                return 'C-Level Especializado'
            elif any(word in puesto_lower for word in ['director', 'directora']):
                return 'Directores'
            elif any(word in puesto_lower for word in ['gerente general', 'general manager']):
                return 'Gerentes Generales'
            elif any(word in puesto_lower for word in ['gerente', 'manager']):
                return 'Gerentes Especializados'
            elif any(word in puesto_lower for word in ['jefe', 'head', 'líder', 'lead']):
                return 'Jefaturas/Heads'
            elif any(word in puesto_lower for word in ['supervisor', 'coordinador', 'encargado']):
                return 'Supervisión/Coordinación'
            else:
                return 'Otros Gerenciales'
        
        gerencial_jobs['nivel_gerencial'] = gerencial_jobs['puesto'].apply(classify_gerencial_level)
        
        # Agrupar por nivel gerencial y calcular métricas
        bubble_data = gerencial_jobs.groupby('nivel_gerencial').agg({
            'salario_promedio': ['mean', 'count', 'median', 'max'],
            'empresa': 'nunique'
        }).round(0)
        
        bubble_data.columns = ['salario_promedio', 'cantidad_registros', 'salario_mediano', 'salario_maximo', 'empresas_diferentes']
        bubble_data = bubble_data.reset_index()
        
        # Filtrar niveles con al menos 2 registros
        bubble_data = bubble_data[bubble_data['cantidad_registros'] >= 2]
        
        if len(bubble_data) == 0:
            return "<p>No hay suficientes datos para análisis de burbujas gerenciales</p>"
        
        # Crear gráfico de burbujas con Plotly Go para mayor control
        fig = go.Figure()
        
        # Definir colores específicos por nivel gerencial (gradiente de poder/jerarquía)
        colors = {
            'C-Level/Presidencia': '#8B0000',      # Rojo oscuro - Máximo nivel
            'C-Level Especializado': '#DC143C',    # Crimson
            'Directores': '#FF4500',               # Orange Red
            'Gerentes Generales': '#FF6347',       # Tomato
            'Gerentes Especializados': '#FFA500',  # Orange
            'Jefaturas/Heads': '#FFD700',          # Gold
            'Supervisión/Coordinación': '#32CD32', # Lime Green
            'Otros Gerenciales': '#808080'         # Gray
        }
        
        for _, row in bubble_data.iterrows():
            fig.add_trace(go.Scatter(
                x=[row['salario_promedio']],
                y=[row['cantidad_registros']],
                mode='markers+text',
                marker=dict(
                    size=max(30, row['empresas_diferentes'] * 12),  # Tamaño mínimo 30
                    color=colors.get(row['nivel_gerencial'], '#808080'),
                    line=dict(width=3, color='white'),
                    opacity=0.85
                ),
                name=row['nivel_gerencial'],
                text=[f"{row['nivel_gerencial']}<br>S/ {row['salario_promedio']:,.0f}"],
                textposition="middle center",
                textfont=dict(color='white', size=10, family='Arial Black'),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             f'💰 Salario Promedio: S/ {row["salario_promedio"]:,.0f}<br>' +
                             f'📊 Salario Mediano: S/ {row["salario_mediano"]:,.0f}<br>' +
                             f'🔝 Salario Máximo: S/ {row["salario_maximo"]:,.0f}<br>' +
                             f'👥 Cantidad Registros: {row["cantidad_registros"]}<br>' +
                             f'🏢 Empresas Diferentes: {row["empresas_diferentes"]}<br>' +
                             '<extra></extra>'
            ))
        
        fig.update_layout(
            title='🎯 Análisis de Burbujas - Puestos Gerenciales por Nivel Jerárquico<br><sub>📊 Tamaño de burbuja = Número de empresas diferentes | 💰 Color = Nivel jerárquico</sub>',
            xaxis_title='💰 Salario Promedio (S/)',
            yaxis_title='👥 Cantidad de Registros',
            height=700,
            template="plotly_white",
            title_x=0.5,
            xaxis=dict(
                tickformat=',.0f',
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            ),
            showlegend=True,
            plot_bgcolor='rgba(248,249,250,0.8)'
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="gerencial-bubble")

    def create_menor_pagados_chart(self, df):
        """Crear análisis de puestos menor pagados por industria/sector"""
        if len(df) == 0:
            return "<p>No se encontraron datos para análisis de puestos menor pagados</p>"
        
        # Obtener los 30 puestos con menor salario promedio
        df_sorted = df.sort_values('salario_promedio', ascending=True)
        menor_pagados = df_sorted.head(30).copy()
        
        # Agrupar por sector para análisis de industrias con menores salarios
        sector_analysis = df.groupby('sector').agg({
            'salario_promedio': ['mean', 'min', 'count'],
            'puesto': 'nunique'
        }).round(0)
        
        sector_analysis.columns = ['salario_promedio', 'salario_minimo', 'total_puestos', 'puestos_unicos']
        sector_analysis = sector_analysis.reset_index()
        sector_analysis = sector_analysis[sector_analysis['total_puestos'] >= 3]  # Al menos 3 puestos
        sector_analysis = sector_analysis.sort_values('salario_promedio', ascending=True).head(15)
        
        # Crear subplot con dos gráficos
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                '📉 Top 30 Puestos con Menores Salarios',
                '🏭 Sectores/Industrias con Menores Sueldos Promedio'
            ),
            vertical_spacing=0.12,
            row_heights=[0.6, 0.4]
        )
        
        # Gráfico 1: Puestos individuales menor pagados
        fig.add_trace(
            go.Bar(
                x=menor_pagados['salario_promedio'],
                y=menor_pagados['puesto'],
                orientation='h',
                marker_color='#e74c3c',
                opacity=0.8,
                text=[f"S/ {x:,.0f}" for x in menor_pagados['salario_promedio']],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>' +
                             'Salario: S/ %{x:,.0f}<br>' +
                             'Empresa: %{customdata[0]}<br>' +
                             'Sector: %{customdata[1]}<br>' +
                             '<extra></extra>',
                customdata=list(zip(menor_pagados['empresa'], menor_pagados['sector'])),
                name='Puestos Menor Pagados'
            ),
            row=1, col=1
        )
        
        # Gráfico 2: Sectores con menores salarios promedio
        fig.add_trace(
            go.Bar(
                x=sector_analysis['salario_promedio'],
                y=sector_analysis['sector'],
                orientation='h',
                marker_color='#f39c12',
                opacity=0.8,
                text=[f"S/ {x:,.0f}" for x in sector_analysis['salario_promedio']],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>' +
                             'Salario Promedio: S/ %{x:,.0f}<br>' +
                             'Salario Mínimo: S/ %{customdata[0]:,.0f}<br>' +
                             'Total Puestos: %{customdata[1]}<br>' +
                             'Puestos Únicos: %{customdata[2]}<br>' +
                             '<extra></extra>',
                customdata=list(zip(sector_analysis['salario_minimo'], 
                                  sector_analysis['total_puestos'],
                                  sector_analysis['puestos_unicos'])),
                name='Sectores Menor Pagados'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title='📉 Análisis Salarial - Puestos y Sectores con Menores Sueldos<br><sub>💰 Identificación de oportunidades de mejora salarial por industria</sub>',
            height=800,
            template="plotly_white",
            title_x=0.5,
            showlegend=False
        )
        
        # Actualizar ejes
        fig.update_xaxes(title_text="💰 Salario Promedio (S/)", tickformat=',.0f', row=1, col=1)
        fig.update_xaxes(title_text="💰 Salario Promedio (S/)", tickformat=',.0f', row=2, col=1)
        fig.update_yaxes(title_text="Puesto", row=1, col=1)
        fig.update_yaxes(title_text="Sector/Industria", row=2, col=1)
        
        return fig.to_html(include_plotlyjs=False, div_id="menor-pagados")
    
    def calculate_real_metrics(self):
        """Calcular métricas reales desde los datos"""
        df = self.classify_job_categories(self.df.copy())
        
        # Métricas REALES calculadas desde los datos
        metrics = {
            # Datos principales
            'total_registros': len(df),
            'total_empresas': df['empresa'].nunique(),
            'total_puestos': df['puesto'].nunique(),
            'total_sectores': df['sector'].nunique(),
            
            # Compensación REAL
            'masa_salarial_total': df['salario_promedio'].sum(),
            'salario_promedio': df['salario_promedio'].mean(),
            'salario_mediano': df['salario_promedio'].median(),
            'salario_maximo': df['salario_promedio'].max(),
            'salario_minimo': df['salario_promedio'].min(),
            
            # Análisis por categorías REALES
            'total_ti': len(df[df['es_ti'] == True]),
            'promedio_ti': df[df['es_ti'] == True]['salario_promedio'].mean() if len(df[df['es_ti'] == True]) > 0 else 0,
            'total_ventas_marketing': len(df[df['es_ventas_marketing'] == True]),
            'promedio_ventas_marketing': df[df['es_ventas_marketing'] == True]['salario_promedio'].mean() if len(df[df['es_ventas_marketing'] == True]) > 0 else 0,
            'total_gerencial': len(df[df['es_gerencial'] == True]),
            'promedio_gerencial': df[df['es_gerencial'] == True]['salario_promedio'].mean() if len(df[df['es_gerencial'] == True]) > 0 else 0,
            'total_no_gerencial': len(df[df['es_no_gerencial'] == True]),
            'promedio_no_gerencial': df[df['es_no_gerencial'] == True]['salario_promedio'].mean() if len(df[df['es_no_gerencial'] == True]) > 0 else 0,
            
            # Top performers reales
            'top_empresa_salario': df.groupby('empresa')['salario_promedio'].mean().max(),
            'top_empresa_nombre': df.groupby('empresa')['salario_promedio'].mean().idxmax(),
            'top_sector_salario': df.groupby('sector')['salario_promedio'].mean().max(),
            'top_sector_nombre': df.groupby('sector')['salario_promedio'].mean().idxmax(),
        }
        
        return metrics
    
    def create_real_kpi_cards(self, metrics):
        """Crear KPIs con datos 100% reales"""
        cards_html = f"""
        <div class="kpi-cards">
            <div class="kpi-card primary">
                <div class="kpi-value">S/ {metrics['masa_salarial_total']:,.0f}</div>
                <div class="kpi-label">Masa Salarial Total</div>
                <div class="kpi-source">Suma de todos los salarios reales</div>
                <div class="kpi-change real">📊 Datos reales del CSV</div>
            </div>
            
            <div class="kpi-card success">
                <div class="kpi-value">{metrics['total_ti']}</div>
                <div class="kpi-label">Puestos TI</div>
                <div class="kpi-source">Promedio: S/ {metrics['promedio_ti']:,.0f}</div>
                <div class="kpi-change real">💻 Datos reales identificados</div>
            </div>
            
            <div class="kpi-card info">
                <div class="kpi-value">{metrics['total_ventas_marketing']}</div>
                <div class="kpi-label">Puestos Ventas/Marketing</div>
                <div class="kpi-source">Promedio: S/ {metrics['promedio_ventas_marketing']:,.0f}</div>
                <div class="kpi-change real">📈 Datos reales identificados</div>
            </div>
            
            <div class="kpi-card warning">
                <div class="kpi-value">{metrics['total_no_gerencial']}</div>
                <div class="kpi-label">Puestos No Gerenciales</div>
                <div class="kpi-source">Promedio: S/ {metrics['promedio_no_gerencial']:,.0f}</div>
                <div class="kpi-change real">👥 Datos reales filtrados</div>
            </div>
            
            <div class="kpi-card secondary">
                <div class="kpi-value">{metrics['top_empresa_nombre'][:20]}</div>
                <div class="kpi-label">Top Empresa</div>
                <div class="kpi-source">S/ {metrics['top_empresa_salario']:,.0f} promedio</div>
                <div class="kpi-change real">🏆 Mejor pagadora real</div>
            </div>
            
            <div class="kpi-card danger">
                <div class="kpi-value">{metrics['top_sector_nombre']}</div>
                <div class="kpi-label">Top Sector</div>
                <div class="kpi-source">S/ {metrics['top_sector_salario']:,.0f} promedio</div>
                <div class="kpi-change real">🎯 Sector líder real</div>
            </div>
            
            <div class="kpi-card primary">
                <div class="kpi-value">S/ {metrics['salario_promedio']:,.0f}</div>
                <div class="kpi-label">Salario Promedio General</div>
                <div class="kpi-source">Mediana: S/ {metrics['salario_mediano']:,.0f}</div>
                <div class="kpi-change real">📊 Calculado desde datos reales</div>
            </div>
            
            <div class="kpi-card info">
                <div class="kpi-value">{metrics['total_empresas']}</div>
                <div class="kpi-label">Total Empresas</div>
                <div class="kpi-source">{metrics['total_registros']:,} puestos analizados</div>
                <div class="kpi-change real">📊 Datos reales extraídos</div>
            </div>
        </div>
        """
        return cards_html
    
    def generate_improved_dashboard(self):
        """Generar dashboard ejecutivo mejorado con análisis específicos"""
        print("🎨 Generando Dashboard Ejecutivo Mejorado...")
        
        # Clasificar trabajos y calcular métricas
        df_classified = self.classify_job_categories(self.df.copy())
        metrics = self.calculate_real_metrics()
        
        # Generar componentes
        ti_chart = self.create_ti_analysis_chart(df_classified)
        vm_chart = self.create_ventas_marketing_chart(df_classified)
        mineria_chart = self.create_mineria_quartiles_chart(df_classified)
        agroindustria_chart = self.create_agroindustria_quartiles_chart(df_classified)
        bubble_gerencial = self.create_gerencial_bubble_chart(df_classified)
        menor_pagados_chart = self.create_menor_pagados_chart(df_classified)
        
        # HTML del dashboard mejorado
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Análisis Salarial Ejecutivo - Estudio de Sueldos Especializado</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
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
        
        .update-info {{
            text-align: right;
            font-size: 0.9rem;
            opacity: 0.9;
        }}
        

        /* Charts */
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
        
        .chart-description {{
            color: #666;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            font-style: italic;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 0 15px;
            }}
            
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
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
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo">
                    <i class="fas fa-chart-line"></i>
                    <div>
                        <h1>Dashboard Análisis Salarial Ejecutivo</h1>
                        <div>Estudio de sueldos por categorías: TI, Ventas/Marketing, Sectores Clave, Gerenciales y Análisis Completo</div>
                    </div>
                </div>
                <div class="update-info">
                    <div>📊 Procesado: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
                    <div>📁 Fuente: {self.data_source}</div>
                    <div>📈 {metrics['total_registros']:,} registros analizados</div>
                </div>
            </div>
        </div>
    </header>

    <main class="container">
        <!-- Análisis TI -->
        <section class="chart-container">
            <h3 class="chart-title">
                <i class="fas fa-laptop-code"></i> 
                Análisis Salarial TI - Distribución de Sueldos por Categoría Tecnológica
            </h3>
            <p class="chart-description">
                <strong>Análisis salarial por quartiles:</strong> {metrics['total_ti']} puestos TI agrupados por categorías tecnológicas. 
                Barras verdes = rango salarial intercuartílico (Q1-Q3), puntos naranjas = sueldo mediano.
            </p>
            <div id="ti-chart">{ti_chart}</div>
        </section>
        
        <!-- Análisis Ventas/Marketing -->
        <section class="chart-container">
            <h3 class="chart-title">
                <i class="fas fa-chart-line"></i> 
                Análisis Salarial Ventas/Marketing - Sueldos por Especialización Comercial
            </h3>
            <p class="chart-description">
                <strong>Análisis salarial por quartiles:</strong> {metrics['total_ventas_marketing']} puestos Ventas/Marketing agrupados por especialización. 
                Barras rojas = rango salarial intercuartílico (Q1-Q3), puntos naranjas = sueldo mediano.
            </p>
            <div id="vm-chart">{vm_chart}</div>
        </section>
        
        <!-- Análisis Minería -->
        <section class="chart-container">
            <h3 class="chart-title">
                <i class="fas fa-mountain"></i> 
                Análisis Salarial Minería - Distribución de Sueldos por Cargo Principal
            </h3>
            <p class="chart-description">
                <strong>Análisis salarial por quartiles:</strong> Sueldos en el sector minero por especialización. 
                Barras marrones = rango salarial intercuartílico (Q1-Q3), puntos naranjas = sueldo mediano.
            </p>
            <div id="mineria-chart">{mineria_chart}</div>
        </section>
        
        <!-- Análisis Agroindustria -->
        <section class="chart-container">
            <h3 class="chart-title">
                <i class="fas fa-seedling"></i> 
                Análisis Salarial Agroindustria - Distribución de Sueldos por Cargo Principal
            </h3>
            <p class="chart-description">
                <strong>Análisis salarial por quartiles:</strong> Sueldos en el sector agroindustrial por especialización. 
                Barras verdes = rango salarial intercuartílico (Q1-Q3), puntos naranjas = sueldo mediano.
            </p>
            <div id="agroindustria-chart">{agroindustria_chart}</div>
        </section>
        
        <!-- Análisis Gerenciales -->
        <section class="chart-container">
            <h3 class="chart-title">
                <i class="fas fa-crown"></i> 
                Análisis Salarial Gerencial - Sueldos Ejecutivos por Nivel Jerárquico
            </h3>
            <p class="chart-description">
                <strong>Compensación ejecutiva real:</strong> {metrics['total_gerencial']} puestos gerenciales clasificados por nivel jerárquico. 
                Sueldo promedio: S/ {metrics['promedio_gerencial']:,.0f}. 
                <br><strong>Jerarquía salarial:</strong> C-Level → Directores → Gerentes → Jefaturas → Supervisión.
            </p>
            <div id="gerencial-bubble">{bubble_gerencial}</div>
        </section>
        
        <!-- Análisis Menores Sueldos -->
        <section class="chart-container">
            <h3 class="chart-title">
                <i class="fas fa-chart-area"></i> 
                Análisis Salarial de Oportunidad - Puestos y Sectores con Menores Sueldos
            </h3>
            <p class="chart-description">
                <strong>Identificación de brechas salariales:</strong> Top 30 puestos con menores salarios y sectores industriales con menor compensación promedio. 
                Útil para identificar oportunidades de mejora salarial por industria.
            </p>
            <div id="menor-pagados">{menor_pagados_chart}</div>
        </section>
    </main>

    <footer class="footer">
        <div class="container">
            <p>
                <i class="fas fa-database"></i> 
                Dashboard Análisis Salarial Ejecutivo - Estudio de Sueldos Perú 2024
                | 
                <a href="../index.html">
                    <i class="fas fa-home"></i> Volver al inicio
                </a>
            </p>
            <p style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.8;">
                Análisis salarial basado en {metrics['total_registros']:,} registros de sueldos reales sin datos simulados
            </p>
        </div>
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('📊 Dashboard Análisis Salarial Ejecutivo cargado');
            console.log('💻 Puestos TI:', {metrics['total_ti']});
            console.log('📈 Puestos Ventas/Marketing:', {metrics['total_ventas_marketing']});
            console.log('👥 Puestos No Gerenciales:', {metrics['total_no_gerencial']});
            console.log('👑 Puestos Gerenciales:', {metrics['total_gerencial']});
        }});
    </script>
</body>
</html>
        """
        
        # Guardar archivo
        output_file = os.path.join(self.output_dir, 'especializado.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Dashboard Ejecutivo Especializado creado: {output_file}")
        return output_file


def main():
    """Función principal"""
    print("🎯 DASHBOARD ANÁLISIS SALARIAL EJECUTIVO")
    print("🔍 Estudio de sueldos específicos: TI, Ventas/Marketing, Gerenciales, Menores Pagados")
    print("📊 Solo datos salariales reales - Sin simulaciones")
    print("=" * 60)
    
    try:
        dashboard = DashboardEjecutivoMejorado()
        dashboard_file = dashboard.generate_improved_dashboard()
        
        print(f"\n✅ Dashboard generado exitosamente!")
        print(f"📁 Ubicación: {dashboard_file}")
        print(f"🌐 URL: file://{os.path.abspath(dashboard_file)}")
        
        print(f"\n📊 ANÁLISIS SALARIALES INCLUIDOS:")
        print(f"💻 Análisis salarial TI con gráfico de quartiles por categoría")
        print(f"📈 Análisis salarial Ventas/Marketing con quartiles (sin gerenciales)")
        print(f"🏭 Análisis salarial Sectores Clave - Minería, Agroindustria y Banca")
        print(f"👥 Análisis salarial No Gerencial con top sueldos operativos")
        print(f"🔵 Análisis salarial por burbujas - compensación no gerencial")
        print(f"👑 Análisis salarial gerencial por nivel jerárquico ejecutivo")
        print(f"📉 Análisis de oportunidad - puestos y sectores con menores sueldos")
        
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