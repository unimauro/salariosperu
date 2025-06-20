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

PORT = 8000

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
    """Crear archivo de estadísticas básicas"""
    stats = {
        "total_empresas": 142,
        "total_puestos": 1247,
        "total_universidades": 45,
        "ultima_actualizacion": datetime.now().strftime('%d/%m/%Y %H:%M')
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