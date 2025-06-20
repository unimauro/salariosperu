# 📊 Salarios Perú - Análisis Salarial Completo

Sistema avanzado de análisis de salarios del mercado peruano con web scraping, visualizaciones interactivas y dashboard ejecutivo.

## 🎯 Características Principales

### 🕷️ Web Scraper Inteligente
- **Descubrimiento automático** de empresas peruanas
- **Extracción de datos** estructurados de salarios por puesto
- **Información universitaria** de ejecutivos
- **Múltiples formatos** de guardado (CSV, SQLite, MySQL)
- **Scraping ético** con delays respetuosos

### 📊 Dashboard y Visualizaciones
- **Dashboard ejecutivo** con KPIs en tiempo real
- **Bubble charts** tipo Gapminder interactivos
- **Análisis por universidades** con gráficos radar
- **Rankings dinámicos** de empresas y puestos
- **Heatmaps salariales** por sector
- **Servidor web integrado** para visualización

### 🎓 Análisis Específicos
- **"Los mejores pagados"**: Rankings por empresa, puesto y sector
- **"De qué universidades son"**: Correlación alma máter vs salarios
- **Análisis por sectores**: Banca, tech, minería, consumo, etc.
- **Tendencias salariales** por experiencia y nivel

## 🚀 Instalación Rápida

### 1. Configuración Automática
```bash
# Clonar y configurar todo automáticamente
git clone [tu-repo]
cd salariosperu
./setup.sh
```

### 2. Instalación Manual
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En macOS/Linux
# venv\Scripts\activate   # En Windows

# Instalar dependencias
pip install -r requirements.txt
```

## 📱 Uso del Sistema

### Método 1: Script de Ejecución Rápida
```bash
./run.sh
```
**Menú interactivo con opciones:**
1. 🕷️ Ejecutar Web Scraping
2. 📊 Ejecutar Análisis y Visualizaciones  
3. 🌐 Abrir Dashboard Web
4. 🔍 Ver archivos de datos
5. 🧹 Limpiar datos anteriores
6. ❌ Salir

### Método 2: Ejecución Manual
```bash
# Activar entorno
source venv/bin/activate

# Ejecutar scraping
python salarios_scraper.py

# Generar análisis
python salarios_analyzer.py

# Iniciar servidor web
python server.py
```

## 🌐 Dashboard Web

El sistema incluye un **servidor web integrado** que permite visualizar todos los reportes en el navegador:

- **Página principal**: `http://localhost:20000/index.html`
- **Dashboard ejecutivo**: `http://localhost:20000/dashboard_ejecutivo.html`
- **Reportes interactivos**: Todos los archivos HTML generados

### Características del Dashboard:
- ✅ **KPIs en tiempo real**: Empresas, salarios, universidades
- 📈 **Gráficos interactivos**: Zoom, hover, filtros
- 🎯 **Insights automáticos**: Tendencias y correlaciones
- 📊 **Rankings dinámicos**: Top empresas y puestos
- 🔄 **Actualización automática**: Detecta nuevos datos

## 📁 Archivos Generados

### Datos
- `salarios_data.csv` - Dataset principal
- `salarios.db` - Base de datos SQLite
- `empresas_encontradas.txt` - Lista de empresas procesadas
- `stats.json` - Estadísticas para el dashboard

### Visualizaciones
- `index.html` - Página principal del sistema
- `dashboard_ejecutivo.html` - Dashboard con KPIs
- `bubble_chart_salarios.html` - Análisis tipo Gapminder
- `radar_universidades.html` - Comparativa universidades
- `heatmap_salarios.html` - Mapa de calor sectorial
- Y más visualizaciones automáticas...

## 🎨 Tipos de Análisis

### 1. **Análisis por Empresas** 🏢
- Rankings de mejor pago por sector
- Distribución salarial por tamaño
- Bubble charts interactivos

### 2. **Análisis por Universidades** 🎓
- ¿De qué universidades son los mejor pagados?
- Correlaciones alma máter vs salario
- Gráficos radar comparativos

### 3. **Análisis por Puestos** 💼
- Ranking de puestos mejor pagados
- Progresión salarial por seniority
- Tendencias por industria

### 4. **Análisis por Sectores** 🏭
- Comparativa: Banca vs Tech vs Minería
- Distribución salarial sectorial
- Oportunidades emergentes

## 🚀 ¡Listo para Empezar!

**Sistema completo creado exitosamente** ✅

Ya tienes todo configurado:

1. **`requirements.txt`** - Todas las dependencias necesarias
2. **`setup.sh`** - Script de configuración automática
3. **`run.sh`** - Menú de ejecución interactivo
4. **`index.html`** - Página principal con navegación
5. **`dashboard_ejecutivo.html`** - Dashboard con KPIs y visualizaciones
6. **`server.py`** - Servidor web integrado
7. **`activate_env.sh`** - Activación rápida del entorno

### 🎯 Próximos Pasos:

```bash
# 1. Configurar el entorno (solo la primera vez)
./setup.sh

# 2. Para uso diario - menú interactivo
./run.sh
```

**El menú te permitirá:**
- 🕷️ Hacer scraping de datos
- 📊 Generar análisis y visualizaciones  
- 🌐 Abrir el dashboard web
- 🔍 Ver archivos generados
- 🧹 Limpiar datos

### 🌟 Características Destacadas:

- **Dashboard profesional** con KPIs en tiempo real
- **Visualizaciones interactivas** tipo Gapminder
- **Análisis específicos** por universidad y empresa
- **Servidor web integrado** para fácil navegación
- **Sistema de navegación** entre reportes
- **Indicadores de estado** para cada reporte

¡Tu sistema de análisis salarial está listo para descubrir los secretos del mercado peruano! 🚀
