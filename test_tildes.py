#!/usr/bin/env python3
"""
Script de prueba para verificar empresas con tildes
Incluye Entel Perú, Scotiabank Perú, Telefónica, etc.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import time

def test_companies_with_tildes():
    """Prueba empresas que usan tildes en sus URLs"""
    print("🧪 PROBANDO EMPRESAS CON TILDES")
    print("=" * 60)
    
    companies_to_test = [
        ('entel-perú', 'Entel Perú'),
        ('scotiabank-perú', 'Scotiabank Perú'),
        ('telefónica', 'Telefónica'),
        ('banco-pichincha-perú', 'Banco Pichincha Perú'),
        ('bbva-en-perú', 'BBVA en Perú'),
        ('banco-de-crédito-bcp', 'Banco de Crédito BCP'),
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    results = []
    
    for company_slug, company_name in companies_to_test:
        print(f"\n🏢 Probando: {company_name}")
        print(f"   Slug: {company_slug}")
        
        # Generar URL codificada
        encoded_slug = quote(company_slug, safe='-')
        url = f"https://salariosperu.com/empresa/{encoded_slug}"
        
        print(f"   URL: {url}")
        
        try:
            response = session.get(url, timeout=10)
            status = response.status_code
            print(f"   Status: {status}")
            
            if status == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar tabla de salarios
                tables = soup.find_all('table')
                table_count = len(tables)
                print(f"   Tablas: {table_count}")
                
                salary_records = 0
                if tables:
                    table = tables[0]
                    rows = table.find_all('tr')
                    
                    for row in rows[1:]:  # Saltar encabezado
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            puesto = cells[0].get_text(strip=True)
                            salario = cells[1].get_text(strip=True)
                            
                            if puesto and salario and 'S/' in salario:
                                salary_records += 1
                
                print(f"   Registros de salarios: {salary_records}")
                
                # Buscar título de la página para confirmar empresa
                title = soup.find('title')
                if title:
                    title_text = title.get_text()
                    print(f"   Título: {title_text[:50]}...")
                
                results.append({
                    'empresa': company_name,
                    'slug': company_slug,
                    'url': url,
                    'status': status,
                    'tablas': table_count,
                    'registros': salary_records,
                    'funciona': salary_records > 0
                })
                
                if salary_records > 0:
                    print(f"   ✅ ÉXITO - {salary_records} registros extraídos")
                else:
                    print(f"   ⚠️  SIN DATOS - Página carga pero no hay salarios")
            else:
                print(f"   ❌ ERROR HTTP {status}")
                results.append({
                    'empresa': company_name,
                    'slug': company_slug,
                    'url': url,
                    'status': status,
                    'tablas': 0,
                    'registros': 0,
                    'funciona': False
                })
            
            # Pausa entre requests
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ EXCEPCIÓN: {e}")
            results.append({
                'empresa': company_name,
                'slug': company_slug,
                'url': url,
                'status': 'ERROR',
                'tablas': 0,
                'registros': 0,
                'funciona': False
            })
    
    return results

def print_summary(results):
    """Imprime resumen de resultados"""
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    total_companies = len(results)
    successful = len([r for r in results if r['funciona']])
    failed = total_companies - successful
    
    print(f"Total de empresas probadas: {total_companies}")
    print(f"Exitosas: {successful}")
    print(f"Fallidas: {failed}")
    print(f"Tasa de éxito: {(successful/total_companies)*100:.1f}%")
    
    print(f"\n✅ EMPRESAS EXITOSAS:")
    for result in results:
        if result['funciona']:
            print(f"   • {result['empresa']}: {result['registros']} registros")
    
    print(f"\n❌ EMPRESAS CON PROBLEMAS:")
    for result in results:
        if not result['funciona']:
            status_str = str(result['status'])
            print(f"   • {result['empresa']}: Status {status_str}")
    
    print(f"\n🔗 URLs GENERADAS:")
    for result in results:
        status_icon = "✅" if result['funciona'] else "❌"
        print(f"   {status_icon} {result['url']}")

def test_specific_scotiabank():
    """Prueba específica para Scotiabank Perú"""
    print("\n" + "=" * 60)
    print("🏦 PRUEBA ESPECÍFICA - SCOTIABANK PERÚ")
    print("=" * 60)
    
    # Probar diferentes variaciones
    variations = [
        'scotiabank-perú',
        'scotiabank-peru', 
        'scotiabank',
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    for variation in variations:
        print(f"\n🔍 Probando variación: {variation}")
        
        encoded = quote(variation, safe='-')
        url = f"https://salariosperu.com/empresa/{encoded}"
        print(f"   URL: {url}")
        
        try:
            response = session.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar tabla
                tables = soup.find_all('table')
                if tables:
                    table = tables[0]
                    rows = table.find_all('tr')
                    
                    print(f"   Filas en tabla: {len(rows)}")
                    
                    # Extraer algunos registros
                    for i, row in enumerate(rows[1:6]):  # Primeras 5 filas
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            puesto = cells[0].get_text(strip=True)
                            salario = cells[1].get_text(strip=True)
                            
                            if puesto and salario and 'S/' in salario:
                                print(f"     {i+1}. {puesto}: {salario}")
                
                # Buscar información adicional
                h1 = soup.find('h1')
                if h1:
                    print(f"   Título H1: {h1.get_text(strip=True)}")
                    
        except Exception as e:
            print(f"   Error: {e}")
        
        time.sleep(1)

def main():
    """Función principal"""
    print("🔍 ANÁLISIS DE EMPRESAS CON TILDES - SALARIOSPERU.COM")
    print("=" * 80)
    
    # Probar todas las empresas con tildes
    results = test_companies_with_tildes()
    
    # Imprimir resumen
    print_summary(results)
    
    # Prueba específica de Scotiabank
    test_specific_scotiabank()
    
    print("\n🎉 Análisis completado!")

if __name__ == "__main__":
    main() 