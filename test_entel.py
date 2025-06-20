#!/usr/bin/env python3
"""
Script de prueba para verificar la extracción de datos de Entel Perú
Incluye manejo de URLs con tildes y caracteres especiales
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
from datetime import datetime

def test_entel_scraping():
    """Prueba específica para Entel Perú"""
    print("🧪 Probando scraping de Entel Perú...")
    print("=" * 50)
    
    # URLs a probar
    urls_to_test = [
        'https://salariosperu.com/empresa/entel-perú',  # Con tilde
        'https://salariosperu.com/empresa/entel-per%C3%BA',  # URL encoded
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    for i, url in enumerate(urls_to_test, 1):
        print(f"\n🔍 Prueba {i}: {url}")
        
        try:
            response = session.get(url, timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar tabla de salarios
                tables = soup.find_all('table')
                print(f"   Tablas encontradas: {len(tables)}")
                
                if tables:
                    # Analizar primera tabla
                    table = tables[0]
                    rows = table.find_all('tr')
                    print(f"   Filas en la tabla: {len(rows)}")
                    
                    salary_data = []
                    for row_idx, row in enumerate(rows):
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            puesto = cells[0].get_text(strip=True)
                            salario = cells[1].get_text(strip=True)
                            
                            if puesto and salario and 'S/' in salario:
                                salary_data.append((puesto, salario))
                    
                    print(f"   Registros de salarios extraídos: {len(salary_data)}")
                    
                    # Mostrar algunos ejemplos
                    if salary_data:
                        print("   📋 Ejemplos encontrados:")
                        for puesto, salario in salary_data[:5]:
                            print(f"      • {puesto}: {salario}")
                    
                    return salary_data
                else:
                    print("   ❌ No se encontraron tablas")
            else:
                print(f"   ❌ Error HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return []

def test_url_encoding():
    """Prueba diferentes métodos de encoding de URLs"""
    print("\n🔧 Probando encoding de URLs...")
    print("=" * 50)
    
    company_names = [
        'entel-perú',
        'telefónica',
        'banco-de-crédito-bcp',
        'interbank'
    ]
    
    for company in company_names:
        encoded = quote(company, safe='-')
        url = f"https://salariosperu.com/empresa/{encoded}"
        print(f"Original: {company}")
        print(f"Encoded:  {encoded}")
        print(f"URL:      {url}")
        print()

def parse_entel_salary(salary_text):
    """Parsea específicamente los salarios de Entel"""
    import re
    
    # Remover 'S/' y espacios
    clean_text = salary_text.replace('S/', '').replace(',', '').strip()
    
    # Buscar patrón de rango
    range_pattern = r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)'
    range_match = re.search(range_pattern, clean_text)
    
    if range_match:
        salary_min = float(range_match.group(1))
        salary_max = float(range_match.group(2))
        salary_avg = (salary_min + salary_max) / 2
        return salary_min, salary_max, salary_avg
    else:
        # Buscar un solo número
        number_pattern = r'(\d+\.?\d*)'
        numbers = re.findall(number_pattern, clean_text)
        
        if numbers:
            salary_avg = float(numbers[0])
            salary_min = salary_avg * 0.9
            salary_max = salary_avg * 1.1
            return salary_min, salary_max, salary_avg
    
    return 0, 0, 0

def main():
    """Función principal de prueba"""
    print("🧪 PRUEBA DE SCRAPING - ENTEL PERÚ")
    print("=" * 60)
    
    # Probar encoding de URLs
    test_url_encoding()
    
    # Probar scraping real
    salary_data = test_entel_scraping()
    
    if salary_data:
        print("\n📊 ANÁLISIS DE DATOS EXTRAÍDOS")
        print("=" * 50)
        
        total_records = len(salary_data)
        print(f"Total de registros: {total_records}")
        
        # Parsear algunos salarios
        parsed_salaries = []
        for puesto, salario_text in salary_data[:5]:
            min_sal, max_sal, avg_sal = parse_entel_salary(salario_text)
            parsed_salaries.append({
                'puesto': puesto,
                'salario_texto': salario_text,
                'salario_min': min_sal,
                'salario_max': max_sal,
                'salario_promedio': avg_sal
            })
        
        print("\n📋 Salarios parseados:")
        for item in parsed_salaries:
            print(f"• {item['puesto']}")
            print(f"  Texto original: {item['salario_texto']}")
            print(f"  Rango: S/{item['salario_min']:.0f} - S/{item['salario_max']:.0f}")
            print(f"  Promedio: S/{item['salario_promedio']:.0f}")
            print()
        
        print("✅ Prueba completada exitosamente!")
    else:
        print("❌ No se pudieron extraer datos")

if __name__ == "__main__":
    main() 