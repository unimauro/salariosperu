#!/usr/bin/env python3
"""
Analizador Simplificado de Datos de Salarios Perú
Análisis básico sin errores de estructura
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import numpy as np
from datetime import datetime
import warnings
import os
import glob

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class SalariosAnalyzerSimple:
    def __init__(self, data_source):
        """Inicializa el analizador simplificado"""
        self.df = self.load_data(data_source)
        self.setup_data()
        print(f"✅ Datos cargados: {len(self.df)} registros")
    
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
        """Prepara y limpia los datos"""
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
        
        # Asignar sectores
        self.assign_sectors()
    
    def assign_sectors(self):
        """Asigna sectores basado en palabras clave"""
        sectores = {
            'Banca y Finanzas': ['bcp', 'bbva', 'interbank', 'banco', 'scotiabank', 'yape', 'culqi'],
            'Tecnología': ['tech', 'software', 'microsoft', 'google', 'data', 'developer'],
            'Consultoría': ['deloitte', 'pwc', 'kpmg', 'mckinsey', 'consulting'],
            'Telecomunicaciones': ['entel', 'movistar', 'claro', 'telefonica'],
            'Consumo Masivo': ['alicorp', 'gloria', 'nestle', 'unilever', 'falabella', 'ripley'],
            'Seguros': ['rimac', 'seguros', 'insurance'],
            'Bebidas': ['ab inbev', 'backus', 'coca cola'],
            'Cosmética': ['loreal', 'cosmetic'],
            'Minería': ['antamina', 'southern', 'volcan', 'mining'],
            'Energía': ['enel', 'energy', 'electric']
        }
        
        self.df['sector'] = 'Otros'
        
        for sector, keywords in sectores.items():
            for keyword in keywords:
                mask = (self.df['empresa'].str.lower().str.contains(keyword, na=False) | 
                       self.df['puesto'].str.lower().str.contains(keyword, na=False))
                self.df.loc[mask, 'sector'] = sector
    
    def resumen_general(self):
        """Genera resumen estadístico general"""
        print("\n" + "="*70)
        print("📈 RESUMEN ESTADÍSTICO GENERAL")
        print("="*70)
        
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
    
    def top_empresas_mejor_pagadas(self, top_n=15):
        """Analiza las empresas que mejor pagan"""
        print(f"\n🏆 TOP {top_n} EMPRESAS MEJOR PAGADAS")
        print("="*60)
        
        if 'salario_promedio' not in self.df.columns:
            print("❌ No hay datos de salarios disponibles")
            return
        
        empresa_stats = self.df.groupby('empresa').agg({
            'salario_promedio': ['mean', 'median', 'count', 'max'],
            'puesto': 'count'
        }).round(2)
        
        empresa_stats.columns = ['Salario_Promedio', 'Salario_Mediano', 
                               'Count_Salarios', 'Salario_Maximo', 'Total_Puestos']
        
        empresa_stats = empresa_stats[empresa_stats['Total_Puestos'] >= 2]
        empresa_stats = empresa_stats.sort_values('Salario_Promedio', ascending=False)
        
        print(empresa_stats.head(top_n))
        
        # Visualización simple
        plt.figure(figsize=(12, 8))
        top_empresas = empresa_stats.head(top_n)
        
        plt.barh(range(len(top_empresas)), top_empresas['Salario_Promedio'])
        plt.yticks(range(len(top_empresas)), top_empresas.index)
        plt.xlabel('Salario Promedio (S/)')
        plt.title(f'Top {top_n} Empresas Mejor Pagadas')
        plt.gca().invert_yaxis()
        
        for i, v in enumerate(top_empresas['Salario_Promedio']):
            plt.text(v + 200, i, f'S/ {v:,.0f}', va='center')
        
        plt.tight_layout()
        plt.savefig('top_empresas_salarios.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return empresa_stats.head(top_n)
    
    def analisis_sectores(self):
        """Analiza salarios por sector"""
        print("\n🏭 ANÁLISIS POR SECTORES")
        print("="*40)
        
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
    
    def top_puestos_mejor_pagados(self, top_n=20):
        """Analiza los puestos mejor pagados"""
        print(f"\n💼 TOP {top_n} PUESTOS MEJOR PAGADOS")
        print("="*60)
        
        if 'salario_promedio' not in self.df.columns:
            print("❌ No hay datos de salarios disponibles")
            return
        
        top_puestos = self.df.nlargest(top_n, 'salario_promedio')[
            ['puesto', 'empresa', 'salario_promedio']
        ].copy()
        
        print("\n🥇 PUESTOS INDIVIDUALES MEJOR PAGADOS:")
        for idx, row in top_puestos.iterrows():
            print(f"{idx+1:2d}. {row['puesto']}")
            print(f"    🏢 {row['empresa']}")
            print(f"    💰 S/ {row['salario_promedio']:,.2f}")
            print()
        
        return top_puestos
    
    def analisis_puestos_detallado(self):
        """Análisis detallado de la relación entre puestos y salarios"""
        print(f"\n💼 ANÁLISIS DETALLADO: PUESTOS vs SALARIOS")
        print("="*70)
        
        if 'salario_promedio' not in self.df.columns:
            print("❌ No hay datos de salarios disponibles")
            return
        
        # 1. Análisis por palabras clave en puestos
        print("\n🔍 ANÁLISIS POR PALABRAS CLAVE EN PUESTOS:")
        
        palabras_clave = {
            'Gerencial': ['gerente', 'manager', 'director', 'jefe', 'chief', 'head'],
            'Técnico': ['developer', 'programador', 'ingeniero', 'técnico', 'analista', 'specialist'],
            'Ventas': ['ventas', 'sales', 'comercial', 'vendedor'],
            'Marketing': ['marketing', 'brand', 'digital', 'social media', 'publicidad'],
            'Finanzas': ['financiero', 'contable', 'controller', 'tesorería', 'crédito'],
            'RRHH': ['recursos humanos', 'rrhh', 'hr', 'talent', 'people'],
            'Operaciones': ['operaciones', 'logistics', 'supply', 'procurement', 'compras'],
            'Consultoría': ['consultant', 'consultor', 'advisory', 'business']
        }
        
        categoria_salarios = {}
        
        for categoria, keywords in palabras_clave.items():
            mask = self.df['puesto'].str.lower().str.contains('|'.join(keywords), na=False, regex=True)
            puestos_categoria = self.df[mask]
            
            if len(puestos_categoria) > 0:
                categoria_salarios[categoria] = {
                    'count': len(puestos_categoria),
                    'salario_promedio': puestos_categoria['salario_promedio'].mean(),
                    'salario_mediano': puestos_categoria['salario_promedio'].median(),
                    'salario_max': puestos_categoria['salario_promedio'].max(),
                    'empresas': puestos_categoria['empresa'].nunique()
                }
        
        # Mostrar resultados
        categoria_df = pd.DataFrame(categoria_salarios).T
        categoria_df = categoria_df.sort_values('salario_promedio', ascending=False)
        print(categoria_df.round(2))
        
        # 2. Análisis por nivel de seniority
        print(f"\n📈 ANÁLISIS POR NIVEL DE SENIORITY:")
        
        def classify_seniority(puesto):
            puesto_lower = str(puesto).lower()
            
            # Senior level
            senior_keywords = ['senior', 'sr', 'lead', 'principal', 'manager', 'gerente', 
                             'director', 'chief', 'head', 'supervisor', 'coordinator']
            if any(keyword in puesto_lower for keyword in senior_keywords):
                return 'Senior'
            
            # Junior level  
            junior_keywords = ['junior', 'jr', 'trainee', 'intern', 'practicante', 
                             'asistente', 'assistant', 'apprentice']
            if any(keyword in puesto_lower for keyword in junior_keywords):
                return 'Junior'
            
            # Specialist/Analyst (Mid-level)
            mid_keywords = ['analyst', 'analista', 'specialist', 'especialista', 
                          'professional', 'officer', 'executive']
            if any(keyword in puesto_lower for keyword in mid_keywords):
                return 'Mid-Level'
            
            return 'Entry-Level'
        
        self.df['seniority_level'] = self.df['puesto'].apply(classify_seniority)
        
        seniority_stats = self.df.groupby('seniority_level').agg({
            'salario_promedio': ['mean', 'median', 'count', 'std'],
            'empresa': 'nunique'
        }).round(2)
        
        seniority_stats.columns = ['Salario_Promedio', 'Salario_Mediano', 'Cantidad', 'Desv_Std', 'Empresas']
        seniority_stats = seniority_stats.sort_values('Salario_Promedio', ascending=False)
        print(seniority_stats)
        
        # 3. Visualización
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Gráfico por categorías
        if len(categoria_df) > 0:
            categoria_df['salario_promedio'].plot(kind='bar', ax=axes[0])
            axes[0].set_title('Salario Promedio por Categoría de Puesto')
            axes[0].set_ylabel('Salario Promedio (S/)')
            axes[0].tick_params(axis='x', rotation=45)
        
        # Gráfico por seniority
        seniority_stats['Salario_Promedio'].plot(kind='bar', ax=axes[1])
        axes[1].set_title('Salario Promedio por Nivel de Seniority')
        axes[1].set_ylabel('Salario Promedio (S/)')
        axes[1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('analisis_puestos_detallado.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return categoria_df, seniority_stats
    
    def analisis_universidades_carreras(self):
        """Análisis de relación entre universidades/carreras y salarios"""
        print(f"\n🎓 ANÁLISIS: UNIVERSIDADES Y CARRERAS vs SALARIOS")
        print("="*70)
        
        # Verificar si tenemos datos de universidades
        if 'universidad_principal' in self.df.columns:
            uni_data = self.df[self.df['universidad_principal'].notna()]
            
            if len(uni_data) > 0:
                print(f"📚 Registros con datos de universidad: {len(uni_data)}")
                
                uni_stats = uni_data.groupby('universidad_principal').agg({
                    'salario_promedio': ['mean', 'median', 'count', 'max'],
                    'empresa': 'nunique',
                    'puesto': 'count'
                }).round(2)
                
                uni_stats.columns = ['Salario_Promedio', 'Salario_Mediano', 
                                   'Count_Salarios', 'Salario_Maximo', 'Empresas', 'Total_Puestos']
                uni_stats = uni_stats.sort_values('Salario_Promedio', ascending=False)
                
                print("\n🏆 RANKING DE UNIVERSIDADES POR SALARIO:")
                print(uni_stats)
                
                # Visualización si hay datos suficientes
                if len(uni_stats) > 1:
                    plt.figure(figsize=(14, 8))
                    uni_stats['Salario_Promedio'].head(10).plot(kind='bar')
                    plt.title('Top 10 Universidades por Salario Promedio')
                    plt.ylabel('Salario Promedio (S/)')
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.savefig('universidades_salarios.png', dpi=300, bbox_inches='tight')
                    plt.show()
            else:
                print("⚠️  No hay datos de universidades en el dataset actual")
        
        # Análisis inferido por carreras basado en títulos de puestos
        print(f"\n🎯 ANÁLISIS INFERIDO POR ÁREA DE CARRERA:")
        
        areas_carrera = {
            'Ingeniería de Sistemas/Software': ['developer', 'programador', 'software', 'systems', 'it', 'tech'],
            'Administración/MBA': ['manager', 'gerente', 'director', 'administration', 'business'],
            'Marketing/Comunicaciones': ['marketing', 'brand', 'communication', 'digital', 'social'],
            'Finanzas/Contabilidad': ['financial', 'financiero', 'contable', 'accounting', 'controller'],
            'Ingeniería Industrial': ['operations', 'logistics', 'supply', 'process', 'industrial'],
            'Economía': ['economist', 'economic', 'research', 'planning', 'strategy'],
            'Psicología/RRHH': ['hr', 'human resources', 'talent', 'people', 'recruitment'],
            'Derecho': ['legal', 'compliance', 'regulatory', 'counsel'],
            'Ingeniería Civil/Construcción': ['construction', 'civil', 'project manager', 'infrastructure'],
            'Medicina/Salud': ['medical', 'health', 'safety', 'occupational']
        }
        
        carrera_salarios = {}
        
        for carrera, keywords in areas_carrera.items():
            mask = self.df['puesto'].str.lower().str.contains('|'.join(keywords), na=False, regex=True)
            puestos_carrera = self.df[mask]
            
            if len(puestos_carrera) > 0:
                carrera_salarios[carrera] = {
                    'count': len(puestos_carrera),
                    'salario_promedio': puestos_carrera['salario_promedio'].mean(),
                    'salario_mediano': puestos_carrera['salario_promedio'].median(),
                    'salario_max': puestos_carrera['salario_promedio'].max(),
                    'empresas': puestos_carrera['empresa'].nunique()
                }
        
        if carrera_salarios:
            carrera_df = pd.DataFrame(carrera_salarios).T
            carrera_df = carrera_df.sort_values('salario_promedio', ascending=False)
            print("\n💰 SALARIOS PROMEDIO POR ÁREA DE CARRERA (inferido):")
            print(carrera_df.round(2))
            
            # Visualización
            plt.figure(figsize=(14, 8))
            carrera_df['salario_promedio'].plot(kind='bar')
            plt.title('Salario Promedio por Área de Carrera (Inferido)')
            plt.ylabel('Salario Promedio (S/)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('carreras_salarios.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            return carrera_df
        else:
            print("⚠️  No se pudieron inferir áreas de carrera suficientes")
            return None
    
    def correlacion_salarios_avanzada(self):
        """Análisis de correlaciones avanzadas entre variables"""
        print(f"\n🔗 ANÁLISIS DE CORRELACIONES AVANZADAS")
        print("="*60)
        
        # Crear variables numéricas para correlación
        analysis_df = self.df.copy()
        
        # Longitud del título del puesto (complejidad)
        analysis_df['titulo_length'] = analysis_df['puesto'].str.len()
        
        # Número de palabras en el título
        analysis_df['titulo_words'] = analysis_df['puesto'].str.split().str.len()
        
        # Empresas por tamaño (número de puestos)
        empresa_sizes = analysis_df.groupby('empresa').size()
        analysis_df['empresa_size'] = analysis_df['empresa'].map(empresa_sizes)
        
        # Variables categóricas convertidas a numéricas
        if 'seniority_level' in analysis_df.columns:
            seniority_map = {'Junior': 1, 'Entry-Level': 2, 'Mid-Level': 3, 'Senior': 4}
            analysis_df['seniority_numeric'] = analysis_df['seniority_level'].map(seniority_map)
        
        # Seleccionar variables numéricas
        numeric_vars = ['salario_promedio', 'titulo_length', 'titulo_words', 'empresa_size']
        if 'seniority_numeric' in analysis_df.columns:
            numeric_vars.append('seniority_numeric')
        
        # Matriz de correlación
        correlation_matrix = analysis_df[numeric_vars].corr()
        
        print("📊 MATRIZ DE CORRELACIONES:")
        print(correlation_matrix.round(3))
        
        # Insights específicos
        print(f"\n🎯 INSIGHTS CLAVE:")
        
        if 'titulo_length' in correlation_matrix.columns:
            titulo_corr = correlation_matrix.loc['salario_promedio', 'titulo_length']
            print(f"• Correlación salario vs longitud de título: {titulo_corr:.3f}")
            if abs(titulo_corr) > 0.3:
                trend = "títulos más largos tienden a tener mejores salarios" if titulo_corr > 0 else "títulos más cortos tienden a tener mejores salarios"
                print(f"  → {trend}")
        
        if 'empresa_size' in correlation_matrix.columns:
            size_corr = correlation_matrix.loc['salario_promedio', 'empresa_size']
            print(f"• Correlación salario vs tamaño de empresa: {size_corr:.3f}")
            if abs(size_corr) > 0.3:
                trend = "empresas más grandes tienden a pagar mejor" if size_corr > 0 else "empresas más pequeñas tienden a pagar mejor"
                print(f"  → {trend}")
        
        if 'seniority_numeric' in correlation_matrix.columns:
            seniority_corr = correlation_matrix.loc['salario_promedio', 'seniority_numeric']
            print(f"• Correlación salario vs nivel de seniority: {seniority_corr:.3f}")
            if abs(seniority_corr) > 0.3:
                print(f"  → Mayor seniority está correlacionado con mejores salarios")
        
        # Visualización de correlaciones
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
                   square=True, fmt='.3f')
        plt.title('Matriz de Correlaciones: Salarios y Variables Relacionadas')
        plt.tight_layout()
        plt.savefig('correlaciones_salarios.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return correlation_matrix, analysis_df
    
    def dashboard_interactivo(self):
        """Crea un dashboard visual básico"""
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
        
        # 3. Salarios por sector
        if 'sector' in self.df.columns:
            sector_avg = self.df.groupby('sector')['salario_promedio'].mean()
            sector_avg.plot(kind='bar', ax=axes[1,0])
            axes[1,0].set_title('Salario Promedio por Sector')
            axes[1,0].tick_params(axis='x', rotation=45)
        
        # 4. Top 10 puestos mejor pagados
        if 'salario_promedio' in self.df.columns:
            top_salarios = self.df.nlargest(10, 'salario_promedio')
            axes[1,1].barh(range(len(top_salarios)), top_salarios['salario_promedio'])
            axes[1,1].set_yticks(range(len(top_salarios)))
            axes[1,1].set_yticklabels([f"{p[:20]}..." if len(p) > 20 else p for p in top_salarios['puesto']])
            axes[1,1].set_title('Top 10 Puestos Mejor Pagados')
            axes[1,1].invert_yaxis()
        
        plt.tight_layout()
        plt.savefig('dashboard_salarios.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generar_reporte_completo(self, output_file='reporte_salarios.txt'):
        """Genera un reporte completo en archivo de texto"""
        with open(output_file, 'w', encoding='utf-8') as f:
            import sys
            original_stdout = sys.stdout
            sys.stdout = f
            
            try:
                f.write("REPORTE COMPLETO DE ANÁLISIS DE SALARIOS PERÚ\n")
                f.write("=" * 60 + "\n")
                f.write(f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                self.resumen_general()
                self.top_empresas_mejor_pagadas()
                self.analisis_sectores()
                self.top_puestos_mejor_pagados()
                self.analisis_puestos_detallado()
                self.analisis_universidades_carreras()
                self.correlacion_salarios_avanzada()
            finally:
                sys.stdout = original_stdout
        
        print(f"✅ Reporte completo guardado en: {output_file}")


def main():
    """Función principal"""
    print("📊 ANALIZADOR SIMPLIFICADO DE SALARIOS PERÚ")
    print("=" * 50)
    
    # Buscar archivos disponibles
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
        
        # Priorizar archivo completo
        completo_files = [f for f in csv_files if 'completo' in f]
        if completo_files:
            default_file = max(completo_files, key=os.path.getsize)
        elif csv_files:
            default_file = max(csv_files, key=os.path.getsize)
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
                print("❌ Número inválido, usando sugerido")
                data_source = default_file
    else:
        print("⚠️  No se encontraron archivos de datos")
        data_source = input("📁 Ingresa la ruta del archivo: ")
        if not data_source.strip():
            print("❌ No se especificó archivo")
            return
    
    try:
        # Crear analizador
        analyzer = SalariosAnalyzerSimple(data_source)
        
        # Menú de opciones
        while True:
            print(f"\n🎯 MENÚ DE ANÁLISIS COMPLETO")
            print("1. 📊 Resumen General")
            print("2. 🏆 Top Empresas Mejor Pagadas")
            print("3. 🏭 Análisis por Sectores")
            print("4. 💼 Top Puestos Mejor Pagados")
            print("5. 🔍 Análisis Detallado: Puestos vs Salarios")
            print("6. 🎓 Análisis: Universidades y Carreras")
            print("7. 🔗 Correlaciones Avanzadas")
            print("8. 📈 Dashboard Visual")
            print("9. 📄 Generar Reporte Completo")
            print("10. 🚀 Ejecutar TODO el análisis")
            print("11. ❌ Salir")
            
            choice = input("\n👉 Selecciona una opción (1-11): ").strip()
            
            if choice == '1':
                analyzer.resumen_general()
            elif choice == '2':
                analyzer.top_empresas_mejor_pagadas()
            elif choice == '3':
                analyzer.analisis_sectores()
            elif choice == '4':
                analyzer.top_puestos_mejor_pagados()
            elif choice == '5':
                analyzer.analisis_puestos_detallado()
            elif choice == '6':
                analyzer.analisis_universidades_carreras()
            elif choice == '7':
                analyzer.correlacion_salarios_avanzada()
            elif choice == '8':
                analyzer.dashboard_interactivo()
            elif choice == '9':
                analyzer.generar_reporte_completo()
            elif choice == '10':
                print("\n🚀 Ejecutando análisis completo...")
                analyzer.resumen_general()
                analyzer.top_empresas_mejor_pagadas()
                analyzer.analisis_sectores()
                analyzer.top_puestos_mejor_pagados()
                analyzer.analisis_puestos_detallado()
                analyzer.analisis_universidades_carreras()
                analyzer.correlacion_salarios_avanzada()
                analyzer.dashboard_interactivo()
                analyzer.generar_reporte_completo()
                print("\n✅ ¡Análisis completo terminado!")
            elif choice == '11':
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 