#!/bin/bash

# Script de ejecución rápida para Salarios Perú
# Para usar después de haber ejecutado setup.sh

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Salarios Perú - Ejecutor Rápido${NC}"
echo "=================================="

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Entorno virtual no encontrado. Ejecuta primero:${NC}"
    echo "   ./setup.sh"
    exit 1
fi

# Activar entorno virtual
echo -e "${BLUE}🔄 Activando entorno virtual...${NC}"
source venv/bin/activate

# Menú de opciones
echo ""
echo -e "${GREEN}¿Qué deseas hacer?${NC}"
echo "1) 🕷️  Web Scraping RÁPIDO (15 empresas automáticas + SQLite)"
echo "2) 🌟 Web Scraping COMPLETO (255+ empresas automáticas + SQLite)"
echo "3) 🔄 Web Scraping RÁPIDO con MySQL"
echo "4) 🚀 Web Scraping COMPLETO con MySQL"
echo "5) 📊 Ejecutar Análisis y Visualizaciones"
echo "6) 🌐 Abrir Dashboard Web (servidor local)"
echo "6b) 🎨 Generar Dashboard Web Moderno"
echo "6c) 🎯 Dashboard Ejecutivo Mejorado (con análisis de fuentes)"
echo "7) 📋 Generar dashboard para GitHub Pages"
echo "8) 🔧 Configurar MySQL"
echo "9) 🔄 Actualizar lista de empresas (extracción automática)"
echo "10) 📄 Ver estadísticas rápidas"
echo "11) ❌ Salir"
echo ""
read -p "Selecciona una opción (1-11): " choice

case $choice in
    1)
        echo -e "${GREEN}🕷️  Iniciando Web Scraping RÁPIDO...${NC}"
        echo "💡 15 empresas desde lista automática con SQLite"
        python scraper_simple.py
        ;;
    2)
        echo -e "${GREEN}🌟 Iniciando Web Scraping COMPLETO...${NC}"
        echo "💡 255+ empresas extraídas automáticamente con SQLite"
        echo "⏱️  Esto puede tomar varios minutos..."
        read -p "¿Continuar? (y/n): " confirm
        if [[ "$confirm" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            python scraper_simple.py --all
        else
            echo "Operación cancelada"
        fi
        ;;
    3)
        echo -e "${GREEN}🔄 Iniciando Web Scraping RÁPIDO con MySQL...${NC}"
        echo "🔍 Verificando configuración MySQL..."
        
        # Verificar si MySQL está configurado
        if python -c "from mysql_config import MYSQL_CONFIG; import mysql.connector; mysql.connector.connect(**MYSQL_CONFIG)" 2>/dev/null; then
            echo "✅ MySQL configurado correctamente"
            python scraper_simple.py --use-mysql
        else
            echo "❌ MySQL no está configurado o no está disponible"
            echo "💡 Configurando MySQL automáticamente..."
            python setup_mysql.py
            if [ $? -eq 0 ]; then
                echo "✅ MySQL configurado. Ejecutando scraper..."
                python scraper_simple.py --use-mysql
            else
                echo "⚠️  Error en configuración MySQL. Usando SQLite como respaldo."
                python scraper_simple.py
            fi
        fi
        ;;
    4)
        echo -e "${GREEN}🚀 Iniciando Web Scraping COMPLETO con MySQL...${NC}"
        echo "💡 TODAS las empresas disponibles con MySQL"
        echo "⏱️  Esto puede tomar varios minutos..."
        read -p "¿Continuar? (y/n): " confirm
        if [[ "$confirm" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            # Verificar MySQL
            if python -c "from mysql_config import MYSQL_CONFIG; import mysql.connector; mysql.connector.connect(**MYSQL_CONFIG)" 2>/dev/null; then
                echo "✅ MySQL configurado correctamente"
                python scraper_simple.py --all --use-mysql
            else
                echo "❌ MySQL no está configurado. Configurando primero..."
                python setup_mysql.py
                if [ $? -eq 0 ]; then
                    echo "✅ MySQL configurado. Ejecutando scraper completo..."
                    python scraper_simple.py --all --use-mysql
                else
                    echo "⚠️  Error en configuración MySQL. Usando SQLite como respaldo."
                    python scraper_simple.py --all
                fi
            fi
        else
            echo "Operación cancelada"
        fi
        ;;
    5)
        echo -e "${GREEN}📊 Iniciando Análisis...${NC}"
        if [ -f "salarios_analyzer_simple.py" ]; then
            python salarios_analyzer_simple.py
        elif [ -f "salarios_analyzer.py.py" ]; then
            python salarios_analyzer.py.py
        elif [ -f "salarios_analyzer.py" ]; then
            python salarios_analyzer.py
        else
            echo "❌ Archivo de análisis no encontrado"
            echo "💡 Verifica que existe salarios_analyzer_simple.py"
        fi
        ;;
    6)
        echo -e "${GREEN}🌐 Iniciando servidor web...${NC}"
        python server.py
        ;;
    "6b")
        echo -e "${GREEN}🎨 Generando Dashboard Web Moderno...${NC}"
        python dashboard_web.py
        ;;
    "6c")
        echo -e "${GREEN}🎯 Generando Dashboard Ejecutivo Mejorado...${NC}"
        python dashboard_ejecutivo_mejorado.py
        ;;
    7)
        echo "📋 Generando dashboard para GitHub Pages..."
        echo "🎯 El dashboard se generará directamente en docs/index.html"
        if [ -f "salarios_completo.csv" ]; then
            python dashboard_ejecutivo_corregido.py
            echo ""
            echo "✅ Dashboard generado en docs/index.html"
            echo "🌐 Puedes subirlo a GitHub Pages o abrirlo localmente"
            echo "�� Ubicación: $(pwd)/docs/index.html"
        else
            echo "❌ No se encontró salarios_completo.csv"
            echo "💡 Ejecuta primero la opción 2 (Scraping COMPLETO)"
        fi
        ;;
    8)
        echo -e "${GREEN}🔧 Configurando MySQL...${NC}"
        if [ -f "setup_mysql.py" ]; then
            python setup_mysql.py
        else
            echo "❌ No se encontró setup_mysql.py"
        fi
        ;;
    9)
        echo "🔄 Actualizando lista de empresas..."
        if [ -f "empresas_extractor.py" ]; then
            python empresas_extractor.py
            echo "✅ Lista actualizada. Ahora puedes usar el scraping completo."
        else
            echo "❌ No se encontró empresas_extractor.py"
        fi
        ;;
    10)
        echo "📄 Estadísticas rápidas de archivos existentes:"
        if [ -f "salarios_completo.csv" ]; then
            echo "📊 salarios_completo.csv: $(wc -l < salarios_completo.csv) líneas"
        fi
        if [ -f "salarios_simple.csv" ]; then
            echo "📊 salarios_simple.csv: $(wc -l < salarios_simple.csv) líneas"
        fi
        if [ -f "empresas_extraidas.json" ]; then
            echo "🏢 Empresas disponibles: $(python -c "import json; print(len(json.load(open('empresas_extraidas.json'))))" 2>/dev/null || echo "Error al leer")"
        fi
        ;;
    11)
        echo -e "${GREEN}👋 ¡Hasta luego!${NC}"
        exit 0
        ;;
    *)
        echo -e "${YELLOW}Opción no válida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Operación completada${NC}" 