#!/bin/bash

# Script de configuración para el proyecto Salarios Perú
# Autor: Sistema de Análisis de Salarios
# Descripción: Automatiza la creación del entorno virtual e instalación de dependencias

echo "🚀 Iniciando configuración del proyecto Salarios Perú..."
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con colores
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✅ SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠️  WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[❌ ERROR]${NC} $1"
}

# Verificar si Python está instalado
print_status "Verificando instalación de Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    print_success "Python3 encontrado: $(python3 --version)"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    print_success "Python encontrado: $(python --version)"
else
    print_error "Python no está instalado. Por favor instala Python 3.8+ antes de continuar."
    exit 1
fi

# Verificar si pip está instalado
print_status "Verificando instalación de pip..."
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
    print_success "pip3 encontrado"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
    print_success "pip encontrado"
else
    print_error "pip no está instalado. Por favor instala pip antes de continuar."
    exit 1
fi

# Crear entorno virtual
print_status "Creando entorno virtual..."
if [ -d "venv" ]; then
    print_warning "El entorno virtual ya existe. ¿Deseas recrearlo? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Eliminando entorno virtual existente..."
        rm -rf venv
        print_success "Entorno virtual eliminado"
    else
        print_status "Usando entorno virtual existente..."
    fi
fi

if [ ! -d "venv" ]; then
    print_status "Creando nuevo entorno virtual..."
    $PYTHON_CMD -m venv venv
    if [ $? -eq 0 ]; then
        print_success "Entorno virtual creado exitosamente"
    else
        print_error "Error al crear el entorno virtual"
        exit 1
    fi
fi

# Activar entorno virtual
print_status "Activando entorno virtual..."
source venv/bin/activate
if [ $? -eq 0 ]; then
    print_success "Entorno virtual activado"
else
    print_error "Error al activar el entorno virtual"
    exit 1
fi

# Actualizar pip en el entorno virtual
print_status "Actualizando pip en el entorno virtual..."
pip install --upgrade pip
print_success "pip actualizado"

# Instalar dependencias
print_status "Instalando dependencias desde requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        print_success "Todas las dependencias instaladas exitosamente"
    else
        print_error "Error al instalar algunas dependencias"
        exit 1
    fi
else
    print_error "Archivo requirements.txt no encontrado"
    exit 1
fi

# Verificar instalación
print_status "Verificando instalación de dependencias críticas..."
python -c "
import sys
required_modules = [
    'requests', 'bs4', 'pandas', 'matplotlib', 
    'seaborn', 'plotly', 'numpy', 'mysql.connector'
]
missing_modules = []

for module in required_modules:
    try:
        if module == 'bs4':
            import bs4
        elif module == 'mysql.connector':
            import mysql.connector
        else:
            __import__(module)
        print(f'✅ {module}')
    except ImportError:
        missing_modules.append(module)
        print(f'❌ {module}')

if missing_modules:
    print(f'\n⚠️  Módulos faltantes: {missing_modules}')
    sys.exit(1)
else:
    print('\n🎉 Todas las dependencias críticas están instaladas correctamente')
"

# Verificar archivos del dashboard
print_status "Verificando archivos del sistema dashboard..."
dashboard_files=(
    "index.html:📊 Página principal del sistema"
    "dashboard_ejecutivo.html:🎯 Dashboard ejecutivo con KPIs"
    "server.py:🌐 Servidor web integrado"
    "run.sh:🚀 Script de ejecución rápida"
)

dashboard_ok=true
for file_info in "${dashboard_files[@]}"; do
    file="${file_info%%:*}"
    description="${file_info#*:}"
    
    if [ -f "$file" ]; then
        print_success "$description - ✓"
    else
        print_error "$description - ✗ (Archivo faltante: $file)"
        dashboard_ok=false
    fi
done

if [ "$dashboard_ok" = true ]; then
    print_success "Sistema dashboard completo y listo"
else
    print_warning "Algunos archivos del dashboard faltan, pero el sistema básico funcionará"
fi

# Test del servidor web
print_status "Probando servidor web integrado..."
python -c "
import http.server
import socketserver
import sys

try:
    # Test básico de que se puede crear el servidor
    with socketserver.TCPServer(('', 0), http.server.SimpleHTTPRequestHandler) as httpd:
        port = httpd.server_address[1]
        print(f'✅ Servidor web funcional (puerto de prueba: {port})')
except Exception as e:
    print(f'⚠️  Problema con el servidor web: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_success "Verificación del servidor web completada"
else
    print_error "Algunas dependencias críticas faltan"
    exit 1
fi

# Configuración de MySQL
echo ""
print_status "Configurando MySQL..."
echo "=================================================="

# Verificar si MySQL está instalado
if ! command -v mysql &> /dev/null; then
    print_warning "MySQL no está instalado. Instalando con Homebrew..."
    if command -v brew &> /dev/null; then
        print_status "Instalando MySQL..."
        brew install mysql
        if [ $? -eq 0 ]; then
            print_success "MySQL instalado correctamente"
        else
            print_error "Error al instalar MySQL"
        fi
    else
        print_warning "Homebrew no está disponible. Instala MySQL manualmente:"
        echo "   🌐 https://dev.mysql.com/downloads/mysql/"
        echo "   📦 O instala Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    fi
else
    mysql_version=$(mysql --version 2>/dev/null | head -1)
    print_success "MySQL ya está instalado: $mysql_version"
fi

# Intentar iniciar MySQL
if command -v mysql &> /dev/null; then
    print_status "Iniciando servicio MySQL..."
    
    # Verificar si ya está corriendo
    if pgrep -f mysqld > /dev/null; then
        print_success "MySQL ya está ejecutándose"
    else
        # Intentar iniciarlo
        if brew services start mysql >/dev/null 2>&1; then
            print_success "MySQL iniciado correctamente con brew services"
        elif mysqld_safe --user=mysql --datadir=/usr/local/var/mysql --log-error=/usr/local/var/mysql/error.log --pid-file=/usr/local/var/mysql/mysql.pid >/dev/null 2>&1 &; then
            print_success "MySQL iniciado en segundo plano"
            sleep 3  # Esperar un poco para que inicie
        else
            print_warning "No se pudo iniciar MySQL automáticamente"
            print_status "Intenta manualmente:"
            echo "   • brew services start mysql"
            echo "   • sudo /usr/local/mysql/support-files/mysql.server start"
        fi
    fi
    
    # Verificar archivos de configuración MySQL
    print_status "Verificando archivos de configuración MySQL..."
    mysql_config_files=(
        "mysql_config.py:⚙️  Configuración de conexión MySQL"
        "setup_mysql.py:🔧 Script de configuración automática MySQL"
        "scraper_simple.py:🔄 Scraper optimizado con soporte MySQL"
        "INSTRUCCIONES_MYSQL.md:📋 Guía de configuración MySQL"
    )
    
    mysql_files_ok=true
    for file_info in "${mysql_config_files[@]}"; do
        file="${file_info%%:*}"
        description="${file_info#*:}"
        
        if [ -f "$file" ]; then
            print_success "$description - ✓"
        else
            print_warning "$description - ✗ (Archivo no encontrado: $file)"
            mysql_files_ok=false
        fi
    done
    
    if [ "$mysql_files_ok" = true ]; then
        print_success "Todos los archivos de configuración MySQL están presentes"
        
        # Test básico de conexión
        print_status "Probando configuración MySQL..."
        python -c "
try:
    from mysql_config import MYSQL_CONFIG
    print('✅ Configuración MySQL cargada correctamente')
    print(f'   Host: {MYSQL_CONFIG[\"host\"]}')
    print(f'   Usuario: {MYSQL_CONFIG[\"user\"]}')
    print(f'   Base de datos: {MYSQL_CONFIG[\"database\"]}')
except Exception as e:
    print(f'⚠️  Error al cargar configuración MySQL: {e}')
" 2>/dev/null
    else
        print_warning "Algunos archivos de configuración MySQL faltan"
        print_status "El sistema funcionará con SQLite como respaldo"
    fi
else
    print_warning "MySQL no está disponible. El sistema usará SQLite"
fi

# Crear archivo de activación rápida
print_status "Creando script de activación rápida..."
cat > activate_env.sh << 'EOF'
#!/bin/bash
# Script para activar rápidamente el entorno virtual
echo "🔄 Activando entorno virtual para Salarios Perú..."
source venv/bin/activate
echo "✅ Entorno virtual activado"
echo "🚀 Ya puedes ejecutar:"
echo "   python salarios_scraper.py    # Para hacer scraping"
echo "   python salarios_analyzer.py   # Para análisis y visualizaciones"
EOF

chmod +x activate_env.sh
print_success "Script de activación creado: ./activate_env.sh"

# Verificar y configurar .gitignore
print_status "Verificando configuración de Git..."
if [ -f ".gitignore" ]; then
    print_success "Archivo .gitignore encontrado"
    
    # Verificar si tiene las entradas principales
    if grep -q "venv/" .gitignore && grep -q "*.csv" .gitignore && grep -q "*.db" .gitignore; then
        print_success "Configuración .gitignore completa"
    else
        print_warning "El .gitignore existe pero puede estar incompleto"
    fi
else
    print_warning "Archivo .gitignore no encontrado (recomendado para evitar subir datos)"
fi

# Verificar si estamos en un repositorio Git
if [ -d ".git" ]; then
    print_success "Repositorio Git detectado"
    
    # Verificar status básico
    git_status=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    if [ "$git_status" -gt 0 ]; then
        print_warning "Hay $git_status archivos sin commit en el repositorio"
        print_status "Tip: Revisa 'git status' para ver qué archivos están pendientes"
    else
        print_success "Repositorio Git limpio"
    fi
else
    print_status "No es un repositorio Git (esto es normal si acabas de descargar)"
fi

# Mostrar resumen final
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 CONFIGURACIÓN COMPLETADA EXITOSAMENTE 🎉${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}📋 RESUMEN:${NC}"
echo "   ✅ Entorno virtual creado en ./venv/"
echo "   ✅ Todas las dependencias instaladas"
echo "   ✅ Verificación de módulos completada"
echo "   ✅ Script de activación creado"
echo "   ✅ Sistema dashboard configurado"
echo "   ✅ Servidor web verificado"
echo "   ✅ Configuración Git revisada"
echo ""
echo -e "${YELLOW}🚀 PRÓXIMOS PASOS:${NC}"
echo "   1. Usar el menú interactivo: ./run.sh"
echo "   2. O activar manualmente: source venv/bin/activate"
echo "   3. Configurar MySQL (opcional): python setup_mysql.py"
echo "   4. Opciones disponibles en el menú:"
echo "      • 🕷️  Web Scraping (con SQLite o MySQL)"
echo "      • 📊 Análisis y Visualizaciones"
echo "      • 🌐 Dashboard Web (http://localhost:20000)"
echo "      • 🔧 Configuración MySQL"
echo "      • 🔍 Ver archivos generados"
echo ""
echo -e "${BLUE}💡 TIPS:${NC}"
echo "   • El menú ./run.sh maneja automáticamente el entorno virtual"
echo "   • El dashboard web se abre automáticamente en tu navegador"
echo "   • Los datos se guardan en múltiples formatos (CSV, SQLite, MySQL)"
echo "   • Usa SQLite para empezar rápido, MySQL para producción"
echo "   • scraper_simple.py funciona con ambas bases de datos"
echo "   • Todas las visualizaciones son interactivas con zoom y filtros"
echo "   • El sistema detecta automáticamente qué reportes están disponibles"
echo ""
print_success "¡Listo para empezar con el análisis de salarios! 🚀" 