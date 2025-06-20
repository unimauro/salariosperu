#!/usr/bin/env python3
"""
Extractor automático de empresas desde SalariosPerú.com
Obtiene la lista completa desde el dropdown "Escoge una empresa"
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import unquote
import time

class EmpresasExtractor:
    def __init__(self):
        self.base_url = "https://salariosperu.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.empresas = []
    
    def extract_companies_from_dropdown(self):
        """Extrae empresas del dropdown principal"""
        print("🔍 Extrayendo empresas desde salariosperu.com...")
        print("=" * 60)
        
        try:
            # Obtener página principal
            response = self.session.get(self.base_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar el dropdown de empresas
            # Puede estar en un select, datalist, o estructura similar
            empresas_encontradas = []
            
            # Método 1: Buscar select con opciones
            selects = soup.find_all('select')
            for select in selects:
                options = select.find_all('option')
                if len(options) > 50:  # El dropdown de empresas debería tener muchas opciones
                    print(f"📋 Encontrado select con {len(options)} opciones")
                    for option in options:
                        value = option.get('value', '').strip()
                        text = option.get_text(strip=True)
                        
                        if value and text and value != 'default' and text != 'Escoge una empresa':
                            # Extraer slug de la URL
                            if '/empresa/' in value:
                                slug = value.replace('/empresa/', '').strip('/')
                            else:
                                slug = value
                            
                            empresas_encontradas.append({
                                'slug': slug,
                                'nombre': text,
                                'url_completa': f"{self.base_url}/empresa/{slug}"
                            })
            
            # Método 2: Buscar datalist
            datalists = soup.find_all('datalist')
            for datalist in datalists:
                options = datalist.find_all('option')
                if len(options) > 50:
                    print(f"📋 Encontrado datalist con {len(options)} opciones")
                    for option in options:
                        value = option.get('value', '').strip()
                        text = option.get_text(strip=True) or value
                        
                        if value and value != 'Escoge una empresa':
                            empresas_encontradas.append({
                                'slug': value,
                                'nombre': text,
                                'url_completa': f"{self.base_url}/empresa/{value}"
                            })
            
            # Método 3: Buscar en JavaScript (pueden estar en una variable JS)
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Buscar arrays de empresas en JavaScript
                    js_content = script.string
                    
                    # Patrón para encontrar arrays de empresas
                    patterns = [
                        r'empresas\s*=\s*\[(.*?)\]',
                        r'companies\s*=\s*\[(.*?)\]',
                        r'"empresa"\s*:\s*"([^"]+)"',
                        r'/empresa/([^"\']+)'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, js_content, re.DOTALL | re.IGNORECASE)
                        if matches and len(str(matches)) > 1000:  # Si encuentra muchos datos
                            print(f"📋 Encontrados datos de empresas en JavaScript")
                            # Procesar matches...
            
            # Método 4: Buscar enlaces directos a empresas
            enlaces_empresa = soup.find_all('a', href=re.compile(r'/empresa/'))
            if len(enlaces_empresa) > 20:
                print(f"📋 Encontrados {len(enlaces_empresa)} enlaces a empresas")
                for enlace in enlaces_empresa:
                    href = enlace.get('href', '')
                    texto = enlace.get_text(strip=True)
                    
                    if '/empresa/' in href:
                        slug = href.replace('/empresa/', '').strip('/')
                        if slug and texto:
                            empresas_encontradas.append({
                                'slug': slug,
                                'nombre': texto,
                                'url_completa': f"{self.base_url}{href}"
                            })
            
            # Eliminar duplicados y limpiar
            empresas_unicas = {}
            for empresa in empresas_encontradas:
                slug = empresa['slug']
                if slug not in empresas_unicas and len(slug) > 2:
                    empresas_unicas[slug] = empresa
            
            self.empresas = list(empresas_unicas.values())
            
            print(f"✅ Extraídas {len(self.empresas)} empresas únicas")
            return self.empresas
            
        except Exception as e:
            print(f"❌ Error al extraer empresas: {e}")
            return []
    
    def extract_companies_from_search_api(self):
        """Intenta extraer empresas desde API de búsqueda si existe"""
        print("\n🔍 Buscando API de empresas...")
        
        # URLs comunes de APIs
        api_urls = [
            f"{self.base_url}/api/empresas",
            f"{self.base_url}/api/companies",
            f"{self.base_url}/search/companies",
            f"{self.base_url}/empresas.json"
        ]
        
        for api_url in api_urls:
            try:
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 50:
                            print(f"✅ API encontrada: {api_url}")
                            return data
                    except:
                        pass
            except:
                continue
        
        print("⚠️  No se encontró API específica")
        return []
    
    def verify_companies(self, sample_size=5):
        """Verifica que las empresas extraídas son válidas"""
        print(f"\n🧪 Verificando muestra de {sample_size} empresas...")
        
        if not self.empresas:
            print("❌ No hay empresas para verificar")
            return False
        
        sample = self.empresas[:sample_size]
        valid_count = 0
        
        for i, empresa in enumerate(sample, 1):
            print(f"  {i}. Verificando: {empresa['nombre']}")
            
            try:
                response = self.session.get(empresa['url_completa'], timeout=10)
                if response.status_code == 200:
                    # Verificar que la página contiene información de salarios
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Buscar indicadores de que es una página válida
                    has_salary_data = (
                        soup.find('table') or 
                        'salario' in response.text.lower() or
                        'S/' in response.text or
                        'puesto' in response.text.lower()
                    )
                    
                    if has_salary_data:
                        valid_count += 1
                        print(f"    ✅ Válida")
                    else:
                        print(f"    ⚠️  Sin datos de salarios")
                else:
                    print(f"    ❌ Error HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
            
            time.sleep(1)  # Pausa entre verificaciones
        
        success_rate = (valid_count / sample_size) * 100
        print(f"\n📊 Tasa de éxito: {success_rate:.1f}% ({valid_count}/{sample_size})")
        
        return success_rate >= 60  # Al menos 60% de éxito
    
    def save_companies(self, filename='empresas_extraidas.json'):
        """Guarda las empresas en formato JSON"""
        if not self.empresas:
            print("❌ No hay empresas para guardar")
            return False
        
        data = {
            'metadata': {
                'total_empresas': len(self.empresas),
                'fecha_extraccion': time.strftime('%Y-%m-%d %H:%M:%S'),
                'fuente': 'salariosperu.com'
            },
            'empresas': self.empresas
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Empresas guardadas en: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error al guardar: {e}")
            return False
    
    def generate_python_file(self, filename='empresas_auto.py'):
        """Genera archivo Python con la lista de empresas"""
        if not self.empresas:
            print("❌ No hay empresas para generar archivo Python")
            return False
        
        # Filtrar empresas con tildes
        empresas_con_tildes = [e for e in self.empresas if any(char in e['slug'] for char in 'áéíóúñ')]
        
        python_code = f'''#!/usr/bin/env python3
"""
Lista de empresas extraída automáticamente desde SalariosPerú.com
Generado automáticamente el {time.strftime('%Y-%m-%d %H:%M:%S')}
Total de empresas: {len(self.empresas)}
Empresas con tildes: {len(empresas_con_tildes)}
"""

# Lista completa de empresas (slug, nombre)
EMPRESAS_AUTO = [
'''
        
        for empresa in self.empresas:
            slug = empresa['slug'].replace("'", "\\'")
            nombre = empresa['nombre'].replace("'", "\\'")
            python_code += f"    ('{slug}', '{nombre}'),\n"
        
        python_code += ''']

def get_empresas_auto():
    """Retorna la lista completa de empresas"""
    return EMPRESAS_AUTO

def get_empresas_con_tildes():
    """Retorna solo empresas con tildes"""
    return [e for e in EMPRESAS_AUTO if any(char in e[0] for char in 'áéíóúñ')]

def print_summary():
    """Imprime resumen de empresas"""
    print(f"Total de empresas: {len(EMPRESAS_AUTO)}")
    empresas_tildes = get_empresas_con_tildes()
    print(f"Empresas con tildes: {len(empresas_tildes)}")
    
    print("\\nEmpresas con caracteres especiales:")
    for slug, nombre in empresas_tildes:
        print(f"  • {nombre} ({slug})")

if __name__ == "__main__":
    print_summary()
'''
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            print(f"✅ Archivo Python generado: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error al generar archivo Python: {e}")
            return False
    
    def print_summary(self):
        """Imprime resumen de la extracción"""
        if not self.empresas:
            print("❌ No se extrajeron empresas")
            return
        
        print(f"\n📊 RESUMEN DE EXTRACCIÓN")
        print("=" * 50)
        print(f"Total de empresas: {len(self.empresas)}")
        
        # Contar empresas con tildes
        empresas_tildes = [e for e in self.empresas if any(char in e['slug'] for char in 'áéíóúñ')]
        print(f"Empresas con tildes: {len(empresas_tildes)}")
        
        # Mostrar primeras 10
        print(f"\n📋 Primeras 10 empresas:")
        for i, empresa in enumerate(self.empresas[:10], 1):
            print(f"  {i:2d}. {empresa['nombre']} ({empresa['slug']})")
        
        if len(empresas_tildes) > 0:
            print(f"\n🔤 Empresas con tildes:")
            for empresa in empresas_tildes[:5]:
                print(f"  • {empresa['nombre']} ({empresa['slug']})")


def main():
    """Función principal"""
    print("🔍 EXTRACTOR AUTOMÁTICO DE EMPRESAS - SALARIOSPERU.COM")
    print("=" * 70)
    
    extractor = EmpresasExtractor()
    
    # Extraer empresas del dropdown
    empresas = extractor.extract_companies_from_dropdown()
    
    if not empresas:
        # Intentar con API si el dropdown no funciona
        empresas = extractor.extract_companies_from_search_api()
    
    if empresas:
        # Mostrar resumen
        extractor.print_summary()
        
        # Verificar muestra
        if extractor.verify_companies():
            print("\n✅ Verificación exitosa!")
            
            # Guardar archivos
            extractor.save_companies()
            extractor.generate_python_file()
            
            print("\n🎉 Extracción completada exitosamente!")
            print("\nArchivos generados:")
            print("  • empresas_extraidas.json - Datos completos en JSON")
            print("  • empresas_auto.py - Lista para usar en Python")
        else:
            print("\n⚠️  Algunas empresas pueden no ser válidas")
            print("Guardando datos de cualquier manera...")
            extractor.save_companies()
            extractor.generate_python_file()
    else:
        print("❌ No se pudieron extraer empresas")

if __name__ == "__main__":
    main() 