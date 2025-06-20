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
echo "1) 🕷️  Ejecutar Web Scraping (salarios_scraper.py)"
echo "2) 📊 Ejecutar Análisis y Visualizaciones (salarios_analyzer.py)"
echo "3) 🌐 Abrir Dashboard Web (servidor local)"
echo "4) 🔍 Ver archivos de datos generados"
echo "5) 🧹 Limpiar datos anteriores (rápido)"
echo "6) 🗑️  Limpieza completa del proyecto"
echo "7) ❌ Salir"
echo ""
read -p "Selecciona una opción (1-7): " choice

case $choice in
    1)
        echo -e "${GREEN}🕷️  Iniciando Web Scraping...${NC}"
        python salarios_scraper.py
        ;;
    2)
        echo -e "${GREEN}📊 Iniciando Análisis...${NC}"
        python salarios_analyzer.py
        ;;
    3)
        echo -e "${GREEN}🌐 Iniciando servidor web...${NC}"
        python server.py
        ;;
    4)
        echo -e "${GREEN}🔍 Archivos de datos encontrados:${NC}"
        ls -la *.csv *.db *.html *.txt 2>/dev/null || echo "No hay archivos de datos aún"
        ;;
    5)
        echo -e "${YELLOW}🧹 Limpiando datos anteriores...${NC}"
        read -p "¿Estás seguro? Esto eliminará todos los datos (y/n): " confirm
        if [[ "$confirm" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            rm -f *.csv *.db *.html empresas_encontradas.txt stats.json
            echo -e "${GREEN}✅ Datos limpiados${NC}"
        else
            echo "Operación cancelada"
        fi
        ;;
    6)
        echo -e "${YELLOW}🗑️  Iniciando limpieza completa...${NC}"
        ./clean.sh
        ;;
    7)
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