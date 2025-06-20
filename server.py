#!/usr/bin/env python3
"""
Servidor web simple para el proyecto Salarios Perú
Sirve los archivos HTML y permite visualizar los reportes en el navegador
"""

import http.server
import socketserver
import webbrowser
import os
import threading
import time
from datetime import datetime

# Puerto por defecto - puede ser sobrescrito con variable de entorno
PORT = int(os.environ.get('SALARIOS_PORT', 20000))

class SalariosHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler personalizado para el servidor web"""
    
    def end_headers(self):
        # Agregar headers para permitir CORS y cache
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()
    
    def log_message(self, format, *args):
        """Log personalizado con timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")

def create_stats_file():
    """Crear archivo de estadísticas básicas desde los datos reales"""
    try:
        import pandas as pd
        import glob
        
        # Buscar archivos CSV
        csv_files = glob.glob("*.csv")
        
        if csv_files:
            # Usar el archivo más completo
            completo_files = [f for f in csv_files if 'completo' in f]
            if completo_files:
                data_file = max(completo_files, key=os.path.getsize)
            else:
                data_file = max(csv_files, key=os.path.getsize)
            
            # Cargar datos
            df = pd.read_csv(data_file)
            
            stats = {
                "total_empresas": int(df['empresa'].nunique()),
                "total_puestos": int(df['puesto'].nunique()),
                "total_registros": len(df),
                "total_sectores": int(df['sector'].nunique()),
                "salario_promedio": round(df['salario_promedio'].mean(), 2),
                "salario_maximo": round(df['salario_promedio'].max(), 2),
                "ultima_actualizacion": datetime.now().strftime('%d/%m/%Y %H:%M'),
                "archivo_datos": data_file
            }
        else:
            # Estadísticas por defecto si no hay datos
            stats = {
                "total_empresas": 255,
                "total_puestos": 278,
                "total_registros": 1055,
                "total_sectores": 10,
                "salario_promedio": 4850.00,
                "salario_maximo": 25000.00,
                "ultima_actualizacion": datetime.now().strftime('%d/%m/%Y %H:%M'),
                "archivo_datos": "No disponible"
            }
            
    except Exception as e:
        print(f"⚠️  Error leyendo datos: {e}")
        stats = {
            "total_empresas": 255,
            "total_puestos": 278,
            "total_registros": 1055,
            "total_sectores": 10,
            "salario_promedio": 4850.00,
            "salario_maximo": 25000.00,
            "ultima_actualizacion": datetime.now().strftime('%d/%m/%Y %H:%M'),
            "archivo_datos": "Error al cargar"
        }
    
    try:
        import json
        with open('stats.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print("✅ Archivo stats.json creado")
    except Exception as e:
        print(f"⚠️  Error creando stats.json: {e}")

def open_browser():
    """Abrir el navegador después de un delay"""
    time.sleep(2)
    url = f"http://localhost:{PORT}"
    print(f"\n🌐 Abriendo navegador en: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️  No se pudo abrir el navegador automáticamente: {e}")
        print(f"   Abre manualmente: {url}")

def start_server():
    """Iniciar el servidor web"""
    
    print("🚀 Iniciando servidor web para Salarios Perú...")
    print("=" * 50)
    
    # Verificar archivos disponibles
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    
    if html_files:
        print("📄 Archivos HTML disponibles:")
        for file in sorted(html_files):
            print(f"   • {file}")
    else:
        print("⚠️  No se encontraron archivos HTML")
        print("   Ejecuta primero el análisis para generar los reportes")
    
    print(f"\n🌐 Servidor corriendo en: http://localhost:{PORT}")
    print("📊 Página principal: index.html")
    print("🎯 Dashboard ejecutivo: dashboard_ejecutivo.html")
    print(f"🔗 URL completa: http://localhost:{PORT}/index.html")
    print("\n💡 Para detener el servidor: Ctrl+C")
    print("=" * 50)
    
    # Crear archivo de estadísticas
    create_stats_file()
    
    # Abrir navegador en un hilo separado
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Iniciar servidor
    try:
        with socketserver.TCPServer(("", PORT), SalariosHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido por el usuario")
    except OSError as e:
        if e.errno == 48:  # Puerto en uso
            print(f"\n❌ Error: El puerto {PORT} ya está en uso")
            print("   Intenta con otro puerto o cierra la aplicación que lo está usando")
        else:
            print(f"\n❌ Error del servidor: {e}")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    start_server() 