#!/bin/bash

# Script de limpieza para el proyecto Salarios Perú
# Limpia archivos temporales y datos generados

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧹 Limpieza del Proyecto Salarios Perú${NC}"
echo "======================================"

# Función para mostrar tamaño de archivos antes de borrar
show_file_size() {
    if [ -f "$1" ] || [ -d "$1" ]; then
        size=$(du -sh "$1" 2>/dev/null | cut -f1)
        echo "   📁 $1 ($size)"
    fi
}

# Mostrar qué se va a limpiar
echo -e "${YELLOW}📋 Archivos que se limpiarán:${NC}"

echo ""
echo "🗃️  Datos generados:"
show_file_size "*.csv"
show_file_size "*.db"
show_file_size "*.sqlite"
show_file_size "empresas_encontradas.txt"
show_file_size "stats.json"

echo ""
echo "📊 Reportes HTML generados:"
show_file_size "bubble_chart_salarios.html"
show_file_size "radar_universidades.html"
show_file_size "heatmap_salarios.html"
show_file_size "ranking_puestos.html"
show_file_size "dashboard_profesional_salarios.html"

echo ""
echo "📝 Logs y temporales:"
show_file_size "*.log"
show_file_size "__pycache__"
show_file_size "*.pyc"
show_file_size ".pytest_cache"

echo ""
echo -e "${RED}⚠️  IMPORTANTE:${NC}"
echo "   • Se mantendrán: código fuente, templates, configuración"
echo "   • Se eliminarán: datos, reportes generados, archivos temporales"
echo "   • El entorno virtual (venv/) NO se eliminará"

echo ""
read -p "¿Continuar con la limpieza? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${GREEN}🧹 Iniciando limpieza...${NC}"
    
    # Contadores
    files_removed=0
    dirs_removed=0
    
    # Limpiar datos
    echo -e "${BLUE}🗃️  Limpiando datos...${NC}"
    for file in *.csv *.db *.sqlite *.sqlite3; do
        if [ -f "$file" ]; then
            rm -f "$file" && echo "   ✅ $file" && ((files_removed++))
        fi
    done
    
    rm -f empresas_encontradas.txt stats.json && echo "   ✅ Archivos de texto" && ((files_removed++))
    
    # Limpiar reportes HTML (mantener templates)
    echo -e "${BLUE}📊 Limpiando reportes generados...${NC}"
    html_reports=(
        "bubble_chart_salarios.html"
        "radar_universidades.html" 
        "heatmap_salarios.html"
        "ranking_puestos.html"
        "ranking_universidades.html"
        "tendencias_puestos.html"
        "sectores_analisis.html"
        "comparativa_sectores.html"
        "dashboard_profesional_salarios.html"
    )
    
    for report in "${html_reports[@]}"; do
        if [ -f "$report" ]; then
            rm -f "$report" && echo "   ✅ $report" && ((files_removed++))
        fi
    done
    
    # Limpiar archivos temporales Python
    echo -e "${BLUE}🐍 Limpiando archivos temporales Python...${NC}"
    if [ -d "__pycache__" ]; then
        rm -rf __pycache__ && echo "   ✅ __pycache__/" && ((dirs_removed++))
    fi
    
    find . -name "*.pyc" -delete 2>/dev/null && echo "   ✅ Archivos .pyc"
    find . -name "*.pyo" -delete 2>/dev/null && echo "   ✅ Archivos .pyo"
    
    if [ -d ".pytest_cache" ]; then
        rm -rf .pytest_cache && echo "   ✅ .pytest_cache/" && ((dirs_removed++))
    fi
    
    # Limpiar logs
    echo -e "${BLUE}📝 Limpiando logs...${NC}"
    for log in *.log; do
        if [ -f "$log" ]; then
            rm -f "$log" && echo "   ✅ $log" && ((files_removed++))
        fi
    done
    
    # Limpiar archivos temporales del sistema
    echo -e "${BLUE}🔧 Limpiando archivos temporales del sistema...${NC}"
    rm -f .DS_Store && echo "   ✅ .DS_Store (macOS)"
    rm -f Thumbs.db && echo "   ✅ Thumbs.db (Windows)"
    
    # Limpiar archivos de respaldo
    for backup in *.bak *.backup *.old; do
        if [ -f "$backup" ]; then
            rm -f "$backup" && echo "   ✅ $backup" && ((files_removed++))
        fi
    done
    
    echo ""
    echo -e "${GREEN}✅ LIMPIEZA COMPLETADA${NC}"
    echo "======================================"
    echo "   📄 Archivos eliminados: $files_removed"
    echo "   📁 Directorios eliminados: $dirs_removed"
    echo ""
    echo -e "${BLUE}📋 Archivos que se mantuvieron:${NC}"
    echo "   ✅ Código fuente (.py)"
    echo "   ✅ Templates HTML (index.html, dashboard_ejecutivo.html)"
    echo "   ✅ Scripts de configuración (.sh)"
    echo "   ✅ Documentación (README.md, LICENSE)"
    echo "   ✅ Configuración (requirements.txt, .gitignore)"
    echo "   ✅ Entorno virtual (venv/)"
    echo ""
    echo -e "${GREEN}🚀 El proyecto está listo para una nueva ejecución!${NC}"
    
else
    echo ""
    echo -e "${YELLOW}❌ Limpieza cancelada${NC}"
    echo "   No se eliminó ningún archivo"
fi

echo ""
echo -e "${BLUE}💡 Para empezar de nuevo:${NC}"
echo "   1. ./run.sh (para usar el menú interactivo)"
echo "   2. O ejecutar manualmente el scraping y análisis" 