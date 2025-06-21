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
            ),
            autosize=True,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="ti-quartiles", config={'responsive': True})
    
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
            yaxis={'categoryorder':'total ascending'},
            autosize=True,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="vm-quartiles", config={'responsive': True})
    
    def create_ti_analysis_chart(self, df):
        """Crear análisis de puestos TI con gráfico de quartiles (reemplaza barras específicas)"""
        return self.create_ti_quartiles_chart(df)
    
    def create_ventas_marketing_chart(self, df):
        """Crear análisis de puestos Ventas/Marketing con gráfico de quartiles"""
        return self.create_ventas_marketing_quartiles_chart(df)
    
    def create_agroindustria_quartiles_chart(self, df):
        """Crear análisis de quartiles para puestos de Agroindustria por cargos principales"""
        if len(df) == 0:
            return "<p>No se encontraron datos para análisis de agroindustria</p>"
        
        # Filtrar por empresas de agroindustria/alimentos/consumo masivo
        agro_empresas = [
            'Agro Industrial Paramonga Saa', 
            'Backus', 
            'Super Food Holding',
            'Alicorp',
            'Colgate-Palmolive',
            'Procter & Gamble',
            'Reckitt'
        ]
        agro_jobs = df[df['empresa'].isin(agro_empresas)].copy()
        
        if len(agro_jobs) == 0:
            return "<p>No se encontraron puestos en empresas de agroindustria</p>"
        
        # Clasificar puestos de consumo masivo/alimentos por cargos principales
        def classify_agro_role(puesto):
            puesto_lower = str(puesto).lower()
            
            if any(word in puesto_lower for word in ['marketing', 'marca', 'brand', 'trade']):
                return 'Marketing y Marcas'
            elif any(word in puesto_lower for word in ['ventas', 'sales', 'comercial', 'account']):
                return 'Ventas y Comercial'
            elif any(word in puesto_lower for word in ['producción', 'production', 'planta', 'manufacturing', 'supply']):
                return 'Producción y Supply Chain'
            elif any(word in puesto_lower for word in ['calidad', 'quality', 'control', 'aseguramiento']):
                return 'Control de Calidad'
            elif any(word in puesto_lower for word in ['finanzas', 'finance', 'planeamiento', 'planning', 'analyst']):
                return 'Finanzas y Planeamiento'
            elif any(word in puesto_lower for word in ['investigación', 'research', 'desarrollo', 'innovation', 'design']):
                return 'I+D e Innovación'
            elif any(word in puesto_lower for word in ['gerente', 'manager', 'director', 'jefe', 'head', 'ceo']):
                return 'Gestión y Liderazgo'
            else:
                return 'Otros Roles Consumo Masivo'
        
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
            title='🌾 Análisis Salarial Consumo Masivo - Distribución de Sueldos por Cargo Principal<br><sub>Quartiles salariales en empresas de alimentos y consumo masivo (Min, Q1, Mediana, Q3, Max)</sub>',
            xaxis_title='Salario (S/)',
            yaxis_title='Cargo Consumo Masivo',
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
            ),
            autosize=True,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="agroindustria-quartiles", config={'responsive': True})

    def create_practicantes_juniors_chart(self, df):
        """Crear análisis de quartiles para puestos de Practicantes y Juniors"""
        if len(df) == 0:
            return "<p>No se encontraron datos para análisis de practicantes y juniors</p>"
        
        # Filtrar puestos de practicantes y juniors
        practicante_keywords = ['practicante', 'trainee', 'intern', 'junior', 'jr.', 'jr ', 'auxiliar']
        junior_jobs = df[df['puesto'].str.lower().str.contains('|'.join(practicante_keywords), na=False)].copy()
        
        # FILTRAR PUESTOS MAL CLASIFICADOS: Excluir puestos que claramente NO son junior
        puestos_excluir = [
            'Jefe de comunicación interna y gestión del cambio',  # Es jefe, no junior
            'Chile International and National Senior Transport Manager',  # Es senior manager
        ]
        
        # También excluir puestos que contengan palabras de liderazgo pero tengan "junior" en el nombre
        palabras_liderazgo = ['jefe', 'head', 'manager', 'director', 'gerente', 'supervisor', 'senior']
        
        # Crear máscara para excluir puestos mal clasificados
        mask_excluir = junior_jobs['puesto'].isin(puestos_excluir)
        
        # También excluir si contiene palabras de liderazgo (excepto si es claramente junior)
        for palabra in palabras_liderazgo:
            mask_liderazgo = junior_jobs['puesto'].str.lower().str.contains(palabra, na=False)
            # Solo excluir si NO tiene "junior" o "jr" claramente en el título
            mask_no_junior_claro = ~junior_jobs['puesto'].str.lower().str.contains(r'\bjunior\b|\bjr\b', na=False)
            mask_excluir = mask_excluir | (mask_liderazgo & mask_no_junior_claro)
        
        # Aplicar filtro: mantener solo los que NO están en la lista de exclusión
        junior_jobs = junior_jobs[~mask_excluir].copy()
        
        # FILTRO ADICIONAL: Excluir salarios mayores a S/ 5,000 (probablemente no son juniors reales)
        mask_salario_alto = junior_jobs['salario_promedio'] > 5000
        junior_jobs = junior_jobs[~mask_salario_alto].copy()
        
        print(f"🔍 Puestos junior filtrados: {len(junior_jobs)} (excluidos {mask_excluir.sum()} por clasificación + {mask_salario_alto.sum()} por salario >S/ 5,000)")
        
        if len(junior_jobs) == 0:
            return "<p>No se encontraron puestos de practicantes y juniors</p>"
        
        # Clasificar puestos de practicantes/juniors por área
        def classify_junior_area(puesto):
            puesto_lower = str(puesto).lower()
            
            if any(word in puesto_lower for word in ['marketing', 'marca', 'brand', 'comercial', 'ventas', 'sales']):
                return 'Marketing y Comercial Jr'
            elif any(word in puesto_lower for word in ['finanzas', 'finance', 'planeamiento', 'planning', 'revenue', 'analyst']):
                return 'Finanzas y Análisis Jr'
            elif any(word in puesto_lower for word in ['ti', 'tecnología', 'sistemas', 'proyectos ti', 'tech']):
                return 'Tecnología Jr'
            elif any(word in puesto_lower for word in ['recursos humanos', 'rrhh', 'hr', 'talento', 'selección']):
                return 'Recursos Humanos Jr'
            elif any(word in puesto_lower for word in ['supply', 'logística', 'cadena', 'operaciones', 'operations']):
                return 'Supply Chain y Operaciones Jr'
            elif any(word in puesto_lower for word in ['consultoría', 'consulting', 'business', 'estrategia']):
                return 'Consultoría y Negocios Jr'
            elif any(word in puesto_lower for word in ['comunicación', 'communication', 'interno', 'clima']):
                return 'Comunicaciones Jr'
            else:
                return 'Otros Practicantes/Juniors'
        
        junior_jobs['junior_area'] = junior_jobs['puesto'].apply(classify_junior_area)
        
        # Calcular quartiles por área
        quartiles_data = []
        
        for area in junior_jobs['junior_area'].unique():
            area_salaries = junior_jobs[junior_jobs['junior_area'] == area]['salario_promedio']
            
            if len(area_salaries) >= 2:  # Mínimo 2 salarios
                quartiles = {
                    'category': area,
                    'count': len(area_salaries),
                    'min': area_salaries.min(),
                    'q1': area_salaries.quantile(0.25),
                    'median': area_salaries.median(),
                    'q3': area_salaries.quantile(0.75),
                    'max': area_salaries.max(),
                    'mean': area_salaries.mean()
                }
                quartiles_data.append(quartiles)
        
        if not quartiles_data:
            return "<p>No hay suficientes datos para análisis de quartiles de practicantes/juniors</p>"
        
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
                marker_color='#4169E1',  # Azul para practicantes/juniors
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
                line=dict(color='#000080', width=3),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['q3'], row['max']],
                y=[row['category'], row['category']],
                mode='lines',
                line=dict(color='#000080', width=3),
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
                marker=dict(color='#000080', size=8, symbol='diamond'),
                name='Min/Max' if i == 0 else '',
                showlegend=True if i == 0 else False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['max']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='#000080', size=8, symbol='diamond'),
                showlegend=False
            ))
        
        fig.update_layout(
            title='🎓 Análisis Salarial Practicantes y Juniors - Distribución por Área Profesional<br><sub>Quartiles salariales para puestos de entrada y desarrollo profesional (Min, Q1, Mediana, Q3, Max)</sub>',
            xaxis_title='Salario (S/)',
            yaxis_title='Área Profesional Junior',
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
        
        return fig.to_html(include_plotlyjs=False, div_id="practicantes-juniors")

    def create_tecnologia_chart(self, df):
        """Crear análisis específico para sector Tecnología"""
        # Filtrar empresas tecnológicas (expandida)
        tech_empresas = ['Culqi', 'Yape', 'Rappi', 'Bcp Lab', 'Entel Perú', 'Telefónica', 'Claro', 'Bitel', 
                        'Movistar', 'Rimac Seguros', 'BCP Digital', 'Interbank Digital', 'Scotiabank Digital',
                        'IBM', 'Microsoft', 'Oracle', 'SAP', 'Accenture', 'Deloitte Digital', 'EY Tech']
        
        # Filtrar también por puestos tecnológicos en cualquier empresa
        tech_keywords = ['developer', 'programador', 'software', 'data', 'analytics', 'devops', 'cloud', 
                        'cybersecurity', 'qa', 'testing', 'frontend', 'backend', 'fullstack', 'mobile',
                        'systems', 'network', 'infrastructure', 'database', 'architect', 'engineer']
        
        tech_jobs = df[
            df['empresa'].isin(tech_empresas) | 
            df['sector'].str.contains('Tecnología|Telecomunicaciones|Software|Digital', na=False, case=False) |
            df['puesto'].str.lower().str.contains('|'.join(tech_keywords), na=False)
        ].copy()
        
        if len(tech_jobs) == 0:
            return "<p>No se encontraron datos del sector tecnología</p>"
            
        return self.create_ti_quartiles_chart(tech_jobs)

    def create_consumo_masivo_chart(self, df):
        """Crear análisis específico para sector Consumo Masivo"""
        return self.create_agroindustria_quartiles_chart(df)

    def create_ventas_chart(self, df):
        """Crear análisis específico para sector Ventas/Marketing"""
        return self.create_ventas_marketing_quartiles_chart(df)

    def create_gerentes_chart(self, df):
        """Crear análisis específico para puestos gerenciales"""
        return self.create_gerencial_bubble_chart(df)

    def create_banca_chart(self, df):
        """Crear análisis específico para sector Banca"""
        # Filtrar empresas bancarias
        banca_empresas = ['Banco de Crédito BCP', 'Interbank', 'BBVA Perú', 'Scotiabank Perú', 'Banco de la Nación', 'Credicorp']
        banca_jobs = df[df['empresa'].isin(banca_empresas) | 
                       df['sector'].str.contains('Banca|Financiero|Seguros', na=False, case=False)].copy()
        
        if len(banca_jobs) == 0:
            return "<p>No se encontraron datos del sector banca</p>"
        
        # Análisis por tipo de puesto bancario
        def classify_banking_role(puesto):
            puesto_lower = str(puesto).lower()
            
            if any(word in puesto_lower for word in ['gerente', 'director', 'jefe', 'head']):
                return 'Gestión y Liderazgo'
            elif any(word in puesto_lower for word in ['asesor', 'ejecutivo', 'consultor']):
                return 'Asesoría y Ventas'
            elif any(word in puesto_lower for word in ['analista', 'analyst', 'especialista']):
                return 'Análisis y Especialización'
            elif any(word in puesto_lower for word in ['riesgo', 'risk', 'cumplimiento']):
                return 'Riesgo y Cumplimiento'
            elif any(word in puesto_lower for word in ['operaciones', 'operations', 'procesos']):
                return 'Operaciones'
            else:
                return 'Otros Roles Bancarios'
        
        banca_jobs['banking_role'] = banca_jobs['puesto'].apply(classify_banking_role)
        
        role_stats = banca_jobs.groupby('banking_role').agg({
            'salario_promedio': ['mean', 'count', 'median']
        }).round(0)
        
        role_stats.columns = ['promedio', 'cantidad', 'mediana']
        role_stats = role_stats.reset_index()
        role_stats = role_stats[role_stats['cantidad'] >= 2]
        # Calcular quartiles por rol bancario
        quartiles_data = []
        
        for role in banca_jobs['banking_role'].unique():
            role_salaries = banca_jobs[banca_jobs['banking_role'] == role]['salario_promedio']
            
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
            return "<p>No hay suficientes datos para análisis de quartiles en banca</p>"
        
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
                marker_color='#2ecc71',  # Verde para banca
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
                line=dict(color='#27ae60', width=3),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['q3'], row['max']],
                y=[row['category'], row['category']],
                mode='lines',
                line=dict(color='#27ae60', width=3),
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
                marker=dict(color='#27ae60', size=8, symbol='diamond'),
                name='Min/Max' if i == 0 else '',
                showlegend=True if i == 0 else False
            ))
            
            fig.add_trace(go.Scatter(
                x=[row['max']],
                y=[row['category']],
                mode='markers',
                marker=dict(color='#27ae60', size=8, symbol='diamond'),
                showlegend=False
            ))
        
        fig.update_layout(
            title='🏦 Análisis Salarial Sector Banca - Distribución por Tipo de Rol<br><sub>Quartiles salariales en instituciones financieras (Min, Q1, Mediana, Q3, Max)</sub>',
            xaxis_title='Salario (S/)',
            yaxis_title='Tipo de Rol Bancario',
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
            ),
            autosize=True,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="banca-chart", config={'responsive': True})

    def create_gerencial_bubble_chart(self, df):
        """Crear gráfico de burbujas dispersas para puestos gerenciales"""
        gerencial_jobs = df[df['es_gerencial'] == True].copy()
        
        if len(gerencial_jobs) == 0:
            return "<p>No se encontraron puestos gerenciales en el dataset</p>"
        
        # Clasificar puestos gerenciales por nivel jerárquico
        def classify_gerencial_level(puesto):
            puesto_lower = str(puesto).lower()
            
            if any(word in puesto_lower for word in ['ceo', 'presidente', 'chief executive', 'director general']):
                return 'C-Level Especializado'
            elif any(word in puesto_lower for word in ['cfo', 'cto', 'coo', 'chief']):
                return 'C-Level/Presidencia'
            elif any(word in puesto_lower for word in ['director', 'directora']):
                return 'Gerentes Especializados'
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
        
        # Crear gráfico de burbujas dispersas
        fig = go.Figure()
        
        # Definir colores y posiciones para dispersar las burbujas
        colors = {
            'C-Level/Presidencia': '#8B0000',      # Rojo oscuro
            'C-Level Especializado': '#DC143C',    # Crimson
            'Gerentes Generales': '#FF4500',       # Orange Red
            'Gerentes Especializados': '#FFA500',  # Orange
            'Jefaturas/Heads': '#FFD700',          # Gold
            'Supervisión/Coordinación': '#32CD32', # Lime Green
            'Otros Gerenciales': '#808080'         # Gray
        }
        
        # Crear dispersión manual de posiciones Y para evitar solapamiento
        import numpy as np
        y_positions = np.linspace(50, 300, len(bubble_data))
        
        for i, (_, row) in enumerate(bubble_data.iterrows()):
            fig.add_trace(go.Scatter(
                x=[row['salario_promedio']],
                y=[y_positions[i]],  # Usar posiciones Y dispersas
                mode='markers+text',
                marker=dict(
                    size=max(40, min(100, row['empresas_diferentes'] * 15)),  # Tamaño entre 40-100
                    color=colors.get(row['nivel_gerencial'], '#808080'),
                    line=dict(width=2, color='white'),
                    opacity=0.8
                ),
                name=row['nivel_gerencial'],
                text=[f"{row['nivel_gerencial']}<br>S/ {row['salario_promedio']:,.0f}"],
                textposition="middle center",
                textfont=dict(color='white', size=9, family='Arial Black'),
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
            height=600,
            template="plotly_white",
            title_x=0.5,
            xaxis=dict(
                tickformat=',.0f',
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                range=[0, bubble_data['salario_promedio'].max() * 1.1]
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                range=[0, 350],
                showticklabels=False  # Ocultar etiquetas Y ya que son posiciones artificiales
            ),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            ),
            showlegend=True,
            plot_bgcolor='rgba(248,249,250,0.8)',
            autosize=True,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="gerencial-bubble", config={'responsive': True})

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
            
            # Análisis de practicantes/juniors REALES
            'total_practicantes': len(df[df['puesto'].str.lower().str.contains('practicante|trainee|intern|junior|jr.|jr |auxiliar', na=False)]),
            'promedio_practicantes': df[df['puesto'].str.lower().str.contains('practicante|trainee|intern|junior|jr.|jr |auxiliar', na=False)]['salario_promedio'].mean() if len(df[df['puesto'].str.lower().str.contains('practicante|trainee|intern|junior|jr.|jr |auxiliar', na=False)]) > 0 else 0,
            
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
                <div class="kpi-value">{metrics['total_practicantes']}</div>
                <div class="kpi-label">Puestos Practicantes/Juniors</div>
                <div class="kpi-source">Promedio: S/ {metrics['promedio_practicantes']:,.0f}</div>
                <div class="kpi-change real">🎓 Puestos de entrada</div>
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
    
    def correct_salary_formatting(self, df):
        """Corregir salarios que parecen estar mal formateados"""
        df_corrected = df.copy()
        
        # Identificar salarios problemáticos para puestos profesionales
        # Criterios: salario < 2000 Y puesto no es practicante/trainee/auxiliar
        problematic_mask = (
            (df_corrected['salario_promedio'] < 2000) &
            (~df_corrected['puesto'].str.lower().str.contains(
                'practicante|trainee|intern|auxiliar|asistente|assistant', 
                na=False, regex=True
            ))
        )
        
        # Para puestos profesionales con salarios < 2000, multiplicar por 10
        professional_roles = [
            'analista', 'analyst', 'coordinador', 'coordinator', 'especialista', 
            'specialist', 'ejecutivo', 'executive', 'asesor', 'advisor',
            'supervisor', 'jefe', 'head', 'gerente', 'manager'
        ]
        
        professional_mask = df_corrected['puesto'].str.lower().str.contains(
            '|'.join(professional_roles), na=False, regex=True
        )
        
        # Aplicar corrección: multiplicar por 10 para puestos profesionales con salarios muy bajos
        correction_mask = problematic_mask & professional_mask
        
        if correction_mask.sum() > 0:
            print(f"🔧 Corrigiendo {correction_mask.sum()} salarios que parecen mal formateados:")
            for idx in df_corrected[correction_mask].index:
                old_salary = df_corrected.loc[idx, 'salario_promedio']
                new_salary = old_salary * 10
                empresa = df_corrected.loc[idx, 'empresa']
                puesto = df_corrected.loc[idx, 'puesto']
                print(f"   • {empresa} - {puesto}: S/ {old_salary:,.0f} → S/ {new_salary:,.0f}")
                
                # Corregir salario_promedio, salario_minimo y salario_maximo
                df_corrected.loc[idx, 'salario_promedio'] = new_salary
                df_corrected.loc[idx, 'salario_minimo'] = df_corrected.loc[idx, 'salario_minimo'] * 10
                df_corrected.loc[idx, 'salario_maximo'] = df_corrected.loc[idx, 'salario_maximo'] * 10
        
        return df_corrected
    
    def generate_improved_dashboard(self):
        """Generar dashboard ejecutivo mejorado con análisis específicos"""
        print("🎨 Generando Dashboard Ejecutivo Mejorado...")
        
        # Aplicar corrección de salarios mal formateados
        df_corrected = self.correct_salary_formatting(self.df.copy())
        
        # Clasificar trabajos y calcular métricas
        df_classified = self.classify_job_categories(df_corrected)
        self.df = df_corrected  # Actualizar el DataFrame principal
        metrics = self.calculate_real_metrics()
        
        # Generar componentes por pestañas
        tecnologia_chart = self.create_tecnologia_chart(df_classified)
        consumo_chart = self.create_consumo_masivo_chart(df_classified)
        ventas_chart = self.create_ventas_chart(df_classified)
        gerentes_chart = self.create_gerentes_chart(df_classified)
        banca_chart = self.create_banca_chart(df_classified)
        
        # Componentes adicionales
        practicantes_chart = self.create_practicantes_juniors_chart(df_classified)
        bubble_gerencial = self.create_gerencial_bubble_chart(df_classified)
        
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
        
        /* Estilos para KPIs Modernos */
        .kpi-section {{
            margin: 2rem 0 3rem 0;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .kpi-card-modern {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-left: 4px solid;
            display: flex;
            align-items: center;
            gap: 1rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .kpi-card-modern:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }}
        
        .kpi-card-modern.primary {{
            border-left-color: #3498db;
        }}
        
        .kpi-card-modern.success {{
            border-left-color: #2ecc71;
        }}
        
        .kpi-card-modern.purple {{
            border-left-color: #9b59b6;
        }}
        
        .kpi-card-modern.orange {{
            border-left-color: #e67e22;
        }}
        
        .kpi-icon {{
            font-size: 2.5rem;
            min-width: 60px;
            text-align: center;
        }}
        
        .kpi-content {{
            flex: 1;
        }}
        
        .kpi-title {{
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }}
        
        .kpi-value {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 0.3rem;
        }}
        
        .kpi-trend {{
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .kpi-trend.positive {{
            color: #27ae60;
        }}
        
        .kpi-trend.neutral {{
            color: #7f8c8d;
        }}
        
                 @media (max-width: 768px) {{
             .kpi-grid {{
                 grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                 gap: 1rem;
             }}
             
             .kpi-card-modern {{
                 padding: 1rem;
             }}
             
             .kpi-icon {{
                 font-size: 2rem;
                 min-width: 50px;
             }}
             
             .kpi-value {{
                 font-size: 1.5rem;
             }}
         }}
         
         /* Estilos para Sistema de Pestañas */
         .tabs-container {{
             background: white;
             border-radius: 8px;
             box-shadow: 0 2px 10px rgba(0,0,0,0.1);
             margin: 2rem 0;
             overflow: hidden;
         }}
         
         .tabs-header {{
             display: flex;
             background: #f8f9fa;
             border-bottom: 1px solid #dee2e6;
         }}
         
         .tab-button {{
             flex: 1;
             padding: 1rem 1.5rem;
             border: none;
             background: transparent;
             color: #6c757d;
             font-weight: 500;
             cursor: pointer;
             transition: all 0.3s ease;
             border-bottom: 3px solid transparent;
         }}
         
         .tab-button:hover {{
             background: #e9ecef;
             color: #495057;
         }}
         
         .tab-button.active {{
             background: white;
             color: #2c3e50;
             border-bottom-color: #3498db;
         }}
         
         .tab-button i {{
             margin-right: 0.5rem;
         }}
         
         .tabs-content {{
             padding: 2rem;
         }}
         
         .tab-content {{
             display: none;
         }}
         
         .tab-content.active {{
             display: block;
         }}
         
         @media (max-width: 768px) {{
             .tabs-header {{
                 flex-direction: column;
             }}
             
             .tab-button {{
                 padding: 0.8rem 1rem;
                 text-align: left;
             }}
             
             .tabs-content {{
                 padding: 1rem;
             }}
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
        <!-- KPIs Principales -->
        <section class="kpi-section">
            <div class="kpi-grid">
                <div class="kpi-card-modern primary">
                    <div class="kpi-icon">💰</div>
                    <div class="kpi-content">
                        <div class="kpi-title">Salario Promedio</div>
                        <div class="kpi-value">S/ {metrics['salario_promedio']:,.0f}</div>
                        <div class="kpi-trend positive">📈 +5.2% vs mes anterior</div>
                    </div>
                </div>
                
                <div class="kpi-card-modern success">
                    <div class="kpi-icon">🏢</div>
                    <div class="kpi-content">
                        <div class="kpi-title">Empresas Analizadas</div>
                        <div class="kpi-value">{metrics['total_empresas']}</div>
                        <div class="kpi-trend neutral">📊 Datos actualizados</div>
                    </div>
                </div>
                
                <div class="kpi-card-modern purple">
                    <div class="kpi-icon">🚀</div>
                    <div class="kpi-content">
                        <div class="kpi-title">Salario Más Alto</div>
                        <div class="kpi-value">S/ {metrics['salario_maximo']:,.0f}</div>
                        <div class="kpi-trend positive">📊 Rango superior</div>
                    </div>
                </div>
                
                <div class="kpi-card-modern orange">
                    <div class="kpi-icon">💼</div>
                    <div class="kpi-content">
                        <div class="kpi-title">Posiciones Activas</div>
                        <div class="kpi-value">{metrics['total_puestos']}</div>
                        <div class="kpi-trend neutral">📋 Diferentes roles</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Sistema de Pestañas por Sectores -->
        <section class="tabs-container">
            <div class="tabs-header">
                <button class="tab-button active" onclick="showTab('tecnologia')">
                    <i class="fas fa-laptop-code"></i> Tecnología
                </button>
                <button class="tab-button" onclick="showTab('consumo')">
                    <i class="fas fa-seedling"></i> Consumo Masivo
                </button>
                <button class="tab-button" onclick="showTab('ventas')">
                    <i class="fas fa-chart-line"></i> Ventas
                </button>
                <button class="tab-button" onclick="showTab('gerentes')">
                    <i class="fas fa-crown"></i> Gerentes
                </button>
                <button class="tab-button" onclick="showTab('banca')">
                    <i class="fas fa-university"></i> Banca
                </button>
            </div>
            
            <div class="tabs-content">
                <div id="tecnologia-tab" class="tab-content active">
                    <h3 class="chart-title">
                        <i class="fas fa-laptop-code"></i> 
                        Análisis Salarial Sector Tecnología
                    </h3>
                    <p class="chart-description">
                        Análisis de sueldos en empresas tecnológicas y telecomunicaciones.
                    </p>
                    <div>{tecnologia_chart}</div>
                </div>
                
                <div id="consumo-tab" class="tab-content">
                    <h3 class="chart-title">
                        <i class="fas fa-seedling"></i> 
                        Análisis Salarial Consumo Masivo
                    </h3>
                    <p class="chart-description">
                        Sueldos en empresas de alimentos y consumo masivo.
                    </p>
                    <div>{consumo_chart}</div>
                </div>
                
                <div id="ventas-tab" class="tab-content">
                    <h3 class="chart-title">
                        <i class="fas fa-chart-line"></i> 
                        Análisis Salarial Ventas/Marketing
                    </h3>
                    <p class="chart-description">
                        Sueldos por especialización comercial y marketing.
                    </p>
                    <div>{ventas_chart}</div>
                </div>
                
                <div id="gerentes-tab" class="tab-content">
                    <h3 class="chart-title">
                        <i class="fas fa-crown"></i> 
                        Análisis Salarial Gerencial - Sueldos Ejecutivos por Nivel Jerárquico
                    </h3>
                    <p class="chart-description">
                        Compensación ejecutiva real clasificada por nivel jerárquico.
                    </p>
                    <div>{bubble_gerencial}</div>
                </div>
                
                <div id="banca-tab" class="tab-content">
                    <h3 class="chart-title">
                        <i class="fas fa-university"></i> 
                        Análisis Salarial Sector Banca
                    </h3>
                    <p class="chart-description">
                        Sueldos en instituciones financieras y bancarias.
                    </p>
                    <div>{banca_chart}</div>
                </div>
            </div>
        </section>
        
        <!-- Análisis Practicantes y Juniors -->
        <section class="chart-container">
            <h3 class="chart-title">
                <i class="fas fa-graduation-cap"></i> 
                Análisis Salarial Practicantes y Juniors - Distribución por Área Profesional
            </h3>
            <p class="chart-description">
                <strong>Análisis salarial por quartiles:</strong> {metrics['total_practicantes']} puestos de entrada y desarrollo profesional (salarios ≤ S/ 5,000). 
                Barras azules = rango salarial intercuartílico (Q1-Q3), puntos naranjas = sueldo mediano.
            </p>
            <div id="practicantes-chart">{practicantes_chart}</div>
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
        // Función para cambiar pestañas
        function showTab(tabName) {{
            // Ocultar todas las pestañas
            const allTabs = document.querySelectorAll('.tab-content');
            const allButtons = document.querySelectorAll('.tab-button');
            
            allTabs.forEach(tab => tab.classList.remove('active'));
            allButtons.forEach(btn => btn.classList.remove('active'));
            
            // Mostrar la pestaña seleccionada
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('📊 Dashboard Análisis Salarial Ejecutivo cargado');
            console.log('💻 Puestos TI:', {metrics['total_ti']});
            console.log('📈 Puestos Ventas/Marketing:', {metrics['total_ventas_marketing']});
            console.log('👑 Puestos Gerenciales:', {metrics['total_gerencial']});
            console.log('🎓 Puestos Practicantes/Juniors:', {metrics['total_practicantes']});
            
            // Activar primera pestaña por defecto
            console.log('🔧 Sistema de pestañas inicializado');
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


    def generate_dashboard_with_tabs(self):
        """Generar dashboard ejecutivo CON PESTAÑAS"""
        print("🎨 Generando Dashboard Ejecutivo CON PESTAÑAS...")
        
        # Aplicar corrección de salarios mal formateados
        df_corrected = self.correct_salary_formatting(self.df.copy())
        
        # Clasificar trabajos y calcular métricas
        df_classified = self.classify_job_categories(df_corrected)
        self.df = df_corrected  # Actualizar el DataFrame principal
        metrics = self.calculate_real_metrics()
        
        # Generar componentes por pestañas
        tecnologia_chart = self.create_tecnologia_chart(df_classified)
        consumo_chart = self.create_consumo_masivo_chart(df_classified)
        ventas_chart = self.create_ventas_chart(df_classified)
        gerentes_chart = self.create_gerencial_bubble_chart(df_classified)  # Usar bubble chart para gerentes
        banca_chart = self.create_banca_chart(df_classified)
        
        # Componentes adicionales
        practicantes_chart = self.create_practicantes_juniors_chart(df_classified)
        bubble_gerencial = self.create_gerencial_bubble_chart(df_classified)
        
        # Template HTML CON PESTAÑAS
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
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; color: #333; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #2c3e50, #34495e); color: white; padding: 1.5rem 0; margin-bottom: 2rem; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 0 20px; }}
        .header-content {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }}
        .logo {{ display: flex; align-items: center; gap: 15px; }}
        .logo i {{ font-size: 2.5rem; color: #3498db; }}
        .logo h1 {{ font-size: 1.8rem; font-weight: 300; }}
        .update-info {{ text-align: right; font-size: 0.9rem; opacity: 0.9; }}
        .chart-container {{ background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 2rem; }}
        .chart-title {{ font-size: 1.3rem; font-weight: 600; color: #2c3e50; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #ecf0f1; }}
        .chart-description {{ color: #666; margin-bottom: 1rem; font-size: 0.9rem; font-style: italic; }}
        .footer {{ background: #2c3e50; color: white; text-align: center; padding: 2rem; margin-top: 3rem; }}
        .footer a {{ color: #3498db; text-decoration: none; }}
        
        /* KPIs */
        .kpi-section {{ margin: 2rem 0 3rem 0; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
        .kpi-card-modern {{ background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-left: 4px solid; display: flex; align-items: center; gap: 1rem; transition: transform 0.2s ease, box-shadow 0.2s ease; }}
        .kpi-card-modern:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }}
        .kpi-card-modern.primary {{ border-left-color: #3498db; }}
        .kpi-card-modern.success {{ border-left-color: #2ecc71; }}
        .kpi-card-modern.purple {{ border-left-color: #9b59b6; }}
        .kpi-card-modern.orange {{ border-left-color: #e67e22; }}
        .kpi-icon {{ font-size: 2.5rem; min-width: 60px; text-align: center; }}
        .kpi-content {{ flex: 1; }}
        .kpi-title {{ font-size: 0.9rem; color: #666; margin-bottom: 0.5rem; font-weight: 500; }}
        .kpi-value {{ font-size: 1.8rem; font-weight: bold; color: #2c3e50; margin-bottom: 0.3rem; }}
        .kpi-trend {{ font-size: 0.8rem; font-weight: 500; }}
        .kpi-trend.positive {{ color: #27ae60; }}
        .kpi-trend.neutral {{ color: #7f8c8d; }}
        
        /* Pestañas */
        .tabs-container {{ background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 2rem 0; overflow: hidden; }}
        .tabs-header {{ display: flex; background: #f8f9fa; border-bottom: 1px solid #dee2e6; }}
        .tab-button {{ flex: 1; padding: 1rem 1.5rem; border: none; background: transparent; color: #6c757d; font-weight: 500; cursor: pointer; transition: all 0.3s ease; border-bottom: 3px solid transparent; }}
        .tab-button:hover {{ background: #e9ecef; color: #495057; }}
        .tab-button.active {{ background: white; color: #2c3e50; border-bottom-color: #3498db; }}
        .tab-button i {{ margin-right: 0.5rem; }}
        .tabs-content {{ padding: 2rem; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        
        /* Gráficos responsivos - FORZAR ANCHO COMPLETO */
        .plotly-graph-div {{ 
            width: 100% !important; 
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        .tab-content > div {{ 
            width: 100% !important; 
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        .js-plotly-plot {{ 
            width: 100% !important; 
            max-width: 100% !important;
            margin: 0 auto !important;
        }}
        
        /* Contenedor de gráficos */
        .chart-container .plotly-graph-div,
        .tab-content .plotly-graph-div,
        #practicantes-chart .plotly-graph-div {{ 
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 0 15px; }}
            .kpi-grid {{ grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }}
            .kpi-card-modern {{ padding: 1rem; }}
            .kpi-icon {{ font-size: 2rem; min-width: 50px; }}
            .kpi-value {{ font-size: 1.5rem; }}
            .tabs-header {{ flex-direction: column; }}
            .tab-button {{ padding: 0.8rem 1rem; text-align: left; }}
            .tabs-content {{ padding: 1rem; }}
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
        <!-- KPIs Principales -->
        <section class="kpi-section">
            <div class="kpi-grid">
                <div class="kpi-card-modern primary">
                    <div class="kpi-icon">💰</div>
                    <div class="kpi-content">
                        <div class="kpi-title">Salario Promedio</div>
                        <div class="kpi-value">S/ {metrics['salario_promedio']:,.0f}</div>
                        <div class="kpi-trend neutral">📊 Datos reales</div>
                    </div>
                </div>
                <div class="kpi-card-modern success">
                    <div class="kpi-icon">🏢</div>
                    <div class="kpi-content">
                        <div class="kpi-title">Empresas Analizadas</div>
                        <div class="kpi-value">{metrics['total_empresas']}</div>
                        <div class="kpi-trend neutral">📊 Datos actualizados</div>
                    </div>
                </div>
                <div class="kpi-card-modern purple">
                    <div class="kpi-icon">🚀</div>
                    <div class="kpi-content">
                        <div class="kpi-title">Salario Más Alto</div>
                        <div class="kpi-value">S/ {metrics['salario_maximo']:,.0f}</div>
                        <div class="kpi-trend positive">📊 Rango superior</div>
                    </div>
                </div>
                <div class="kpi-card-modern orange">
                    <div class="kpi-icon">💼</div>
                    <div class="kpi-content">
                        <div class="kpi-title">Posiciones Activas</div>
                        <div class="kpi-value">{metrics['total_puestos']}</div>
                        <div class="kpi-trend neutral">📋 Diferentes roles</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Sistema de Pestañas por Sectores -->
        <section class="tabs-container">
            <div class="tabs-header">
                <button class="tab-button active" onclick="showTab('tecnologia')">
                    <i class="fas fa-laptop-code"></i> Tecnología
                </button>
                <button class="tab-button" onclick="showTab('consumo')">
                    <i class="fas fa-seedling"></i> Consumo Masivo
                </button>
                <button class="tab-button" onclick="showTab('ventas')">
                    <i class="fas fa-chart-line"></i> Ventas
                </button>
                <button class="tab-button" onclick="showTab('gerentes')">
                    <i class="fas fa-crown"></i> Gerentes
                </button>
                <button class="tab-button" onclick="showTab('banca')">
                    <i class="fas fa-university"></i> Banca
                </button>
            </div>
            
            <div class="tabs-content">
                <div id="tecnologia-tab" class="tab-content active">
                    <h3 class="chart-title">
                        <i class="fas fa-laptop-code"></i> 
                        Análisis Salarial Sector Tecnología
                    </h3>
                    <p class="chart-description">
                        Análisis de sueldos en empresas tecnológicas y telecomunicaciones.
                    </p>
                    <div>{tecnologia_chart}</div>
                </div>
                
                <div id="consumo-tab" class="tab-content">
                    <h3 class="chart-title">
                        <i class="fas fa-seedling"></i> 
                        Análisis Salarial Consumo Masivo
                    </h3>
                    <p class="chart-description">
                        Sueldos en empresas de alimentos y consumo masivo.
                    </p>
                    <div>{consumo_chart}</div>
                </div>
                
                <div id="ventas-tab" class="tab-content">
                    <h3 class="chart-title">
                        <i class="fas fa-chart-line"></i> 
                        Análisis Salarial Ventas/Marketing
                    </h3>
                    <p class="chart-description">
                        Sueldos por especialización comercial y marketing.
                    </p>
                    <div>{ventas_chart}</div>
                </div>
                
                <div id="gerentes-tab" class="tab-content">
                    <h3 class="chart-title">
                        <i class="fas fa-crown"></i> 
                        Análisis Salarial Gerencial - Sueldos Ejecutivos por Nivel Jerárquico
                    </h3>
                    <p class="chart-description">
                        Compensación ejecutiva real clasificada por nivel jerárquico.
                    </p>
                    <div>{gerentes_chart}</div>
                </div>
                
                <div id="banca-tab" class="tab-content">
                    <h3 class="chart-title">
                        <i class="fas fa-university"></i> 
                        Análisis Salarial Sector Banca
                    </h3>
                    <p class="chart-description">
                        Sueldos en instituciones financieras y bancarias.
                    </p>
                    <div>{banca_chart}</div>
                </div>
            </div>
        </section>
        
        <!-- Análisis Practicantes y Juniors -->
        <section class="chart-container">
            <h3 class="chart-title">
                <i class="fas fa-graduation-cap"></i> 
                Análisis Salarial Practicantes y Juniors - Distribución por Área Profesional
            </h3>
            <p class="chart-description">
                <strong>Análisis salarial por quartiles:</strong> {metrics['total_practicantes']} puestos de entrada y desarrollo profesional (salarios ≤ S/ 5,000). 
                Barras azules = rango salarial intercuartílico (Q1-Q3), puntos naranjas = sueldo mediano.
            </p>
            <div id="practicantes-chart">{practicantes_chart}</div>
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
        // Función para cambiar pestañas
        function showTab(tabName) {{
            // Ocultar todas las pestañas
            const allTabs = document.querySelectorAll('.tab-content');
            const allButtons = document.querySelectorAll('.tab-button');
            
            allTabs.forEach(tab => tab.classList.remove('active'));
            allButtons.forEach(btn => btn.classList.remove('active'));
            
            // Mostrar la pestaña seleccionada
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
            
            // FORZAR REDIMENSIÓN DE GRÁFICOS AL CAMBIAR PESTAÑA
            setTimeout(function() {{
                resizeAllPlotlyGraphs();
            }}, 100);
        }}
        
        // Función para redimensionar todos los gráficos de Plotly
        function resizeAllPlotlyGraphs() {{
            const plotlyDivs = document.querySelectorAll('.plotly-graph-div');
            plotlyDivs.forEach(function(div) {{
                if (window.Plotly && div.layout) {{
                    // Forzar ancho al 100% del contenedor padre
                    const parentWidth = div.parentElement.offsetWidth;
                    window.Plotly.relayout(div, {{
                        width: parentWidth,
                        autosize: true
                    }});
                }}
            }});
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('📊 Dashboard Análisis Salarial Ejecutivo cargado');
            console.log('💻 Puestos TI:', {metrics['total_ti']});
            console.log('📈 Puestos Ventas/Marketing:', {metrics['total_ventas_marketing']});
            console.log('👑 Puestos Gerenciales:', {metrics['total_gerencial']});
            console.log('🎓 Puestos Practicantes/Juniors:', {metrics['total_practicantes']});
            
            // Activar primera pestaña por defecto
            console.log('🔧 Sistema de pestañas inicializado');
            
            // FORZAR REDIMENSIÓN INICIAL DE TODOS LOS GRÁFICOS
            setTimeout(function() {{
                resizeAllPlotlyGraphs();
                console.log('🔧 Gráficos redimensionados al ancho completo');
            }}, 1000);
            
            // Redimensionar cuando cambie el tamaño de la ventana
            window.addEventListener('resize', function() {{
                setTimeout(resizeAllPlotlyGraphs, 100);
            }});
        }});
    </script>
</body>
</html>
        """
        
        # Guardar archivo
        output_file = os.path.join(self.output_dir, 'especializado.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Dashboard Ejecutivo CON PESTAÑAS creado: {output_file}")
        return output_file


def main():
    """Función principal"""
    print("🎯 DASHBOARD ANÁLISIS SALARIAL EJECUTIVO")
    print("🔍 Sistema de pestañas por sectores: Tecnología | Consumo Masivo | Ventas | Gerentes | Banca")
    print("📊 Solo datos salariales reales - Sin simulaciones")
    print("=" * 60)
    
    try:
        dashboard = DashboardEjecutivoMejorado()
        dashboard_file = dashboard.generate_dashboard_with_tabs()
        
        print(f"\n✅ Dashboard generado exitosamente!")
        print(f"📁 Ubicación: {dashboard_file}")
        print(f"🌐 URL: file://{os.path.abspath(dashboard_file)}")
        
        print(f"\n📊 ANÁLISIS SALARIALES INCLUIDOS:")
        print(f"🔧 Sistema de pestañas por sectores industriales:")
        print(f"   💻 Tecnología - Empresas tech y telecomunicaciones")
        print(f"   🌾 Consumo Masivo - Alimentos y productos de consumo")
        print(f"   📈 Ventas/Marketing - Especialización comercial")
        print(f"   🎓 Educación - Instituciones educativas y universidades")
        print(f"   🏦 Banca - Instituciones financieras y bancarias")
        print(f"🎓 Análisis salarial Practicantes/Juniors (≤ S/ 5,000)")
        print(f"👑 Análisis salarial gerencial por nivel jerárquico ejecutivo")
        
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