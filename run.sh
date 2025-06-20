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
echo "1) 🕷️  Web Scraping RÁPIDO (15 empresas + SQLite)"
echo "2) 🌟 Web Scraping COMPLETO (todas las empresas + SQLite)"
echo "3) 🔄 Web Scraping RÁPIDO con MySQL"
echo "4) 🚀 Web Scraping COMPLETO con MySQL"
echo "5) 📊 Ejecutar Análisis y Visualizaciones"
echo "6) 🌐 Abrir Dashboard Web (servidor local)"
echo "7) 🔧 Configurar MySQL"
echo "8) 🔍 Ver archivos de datos generados"
echo "9) 🧹 Limpiar datos anteriores (rápido)"
echo "10) 🗑️ Limpieza completa del proyecto"
echo "11) ❌ Salir"
echo ""
read -p "Selecciona una opción (1-11): " choice

case $choice in
    1)
        echo -e "${GREEN}🕷️  Iniciando Web Scraping RÁPIDO...${NC}"
        echo "💡 15 empresas principales con SQLite"
        python scraper_simple.py
        ;;
    2)
        echo -e "${GREEN}🌟 Iniciando Web Scraping COMPLETO...${NC}"
        echo "💡 TODAS las empresas disponibles con SQLite"
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
        if [ -f "salarios_analyzer.py.py" ]; then
            python salarios_analyzer.py.py
        elif [ -f "salarios_analyzer.py" ]; then
            python salarios_analyzer.py
        else
            echo "❌ Archivo de análisis no encontrado"
            echo "💡 Verifica que existe salarios_analyzer.py"
        fi
        ;;
    6)
        echo -e "${GREEN}🌐 Iniciando servidor web...${NC}"
        python server.py
        ;;
    7)
        echo -e "${GREEN}🔧 Configurando MySQL...${NC}"
        echo "=================================================="
        echo "Opciones de configuración MySQL:"
        echo "a) Configuración automática"
        echo "b) Verificar configuración actual"
        echo "c) Reiniciar configuración"
        echo ""
        read -p "Selecciona una opción (a/b/c): " mysql_option
        
        case $mysql_option in
            a)
                echo "🔧 Ejecutando configuración automática..."
                python setup_mysql.py
                ;;
            b)
                echo "🔍 Verificando configuración actual..."
                python setup_mysql.py check
                ;;
            c)
                echo "🔄 Reiniciando configuración..."
                python setup_mysql.py reset
                ;;
            *)
                echo "Opción no válida"
                ;;
        esac
        ;;
    8)
        echo -e "${GREEN}🔍 Archivos de datos encontrados:${NC}"
        echo "📊 Archivos CSV:"
        ls -la *.csv 2>/dev/null || echo "   No hay archivos CSV"
        echo "🗄️  Bases de datos:"
        ls -la *.db *.sqlite 2>/dev/null || echo "   No hay archivos de base de datos SQLite"
        echo "📄 Reportes HTML:"
        ls -la *reporte*.html *analisis*.html 2>/dev/null || echo "   No hay reportes HTML"
        echo "📝 Otros archivos:"
        ls -la *.txt *.json 2>/dev/null || echo "   No hay otros archivos de datos"
        ;;
    9)
        echo -e "${YELLOW}🧹 Limpiando datos anteriores...${NC}"
        read -p "¿Estás seguro? Esto eliminará todos los datos (y/n): " confirm
        if [[ "$confirm" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            rm -f *.csv *.db *.sqlite *.html empresas_encontradas.txt stats.json
            echo -e "${GREEN}✅ Datos limpiados${NC}"
        else
            echo "Operación cancelada"
        fi
        ;;
    10)
        echo -e "${YELLOW}🗑️  Iniciando limpieza completa...${NC}"
        ./clean.sh
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