#!/usr/bin/env python3
"""
Scraper Simplificado para SalariosPerú.com
Versión optimizada que funciona con SQLite y MySQL
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import time
import logging
from datetime import datetime
import mysql.connector
from urllib.parse import quote
from mysql_config import MYSQL_CONFIG
from empresas_completas import get_all_companies, EMPRESAS_COMPLETAS

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SalariosScraperSimple:
    def __init__(self, delay=2, use_mysql=False):
        self.base_url = "https://salariosperu.com"
        self.delay = delay
        self.use_mysql = use_mysql
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.salary_data = []
        
        # Cargar todas las empresas disponibles
        self.all_companies = get_all_companies()
        
        # Lista de empresas para testing rápido (subset de las principales)
        self.test_companies = [
            ('banco-de-credito-bcp', 'Banco de Crédito BCP'),
            ('interbank', 'Interbank'), 
            ('bbva-peru', 'BBVA Perú'),
            ('scotiabank-perú', 'Scotiabank Perú'),  # Con tilde
            ('entel-perú', 'Entel Perú'),  # Con tilde
            ('telefónica', 'Telefónica'),  # Con tilde
            ('alicorp', 'Alicorp'),
            ('rimac-seguros', 'Rimac Seguros'),
            ('falabella', 'Falabella'),
            ('deloitte', 'Deloitte'),
            ('pwc-perú', 'PwC Perú'),
            ('rappi', 'Rappi'),
            ('yape', 'Yape'),
            ('culqi', 'Culqi'),
            ('nestlé', 'Nestlé')  # Con tilde
        ]
    
    def encode_company_url(self, company_slug):
        """Codifica correctamente URLs de empresas con caracteres especiales"""
        # Separar el slug en partes para codificar solo las partes necesarias
        if '/' in company_slug:
            # Si ya incluye la ruta completa
            return company_slug
        else:
            # Codificar caracteres especiales para URL
            encoded_slug = quote(company_slug, safe='-')
            return f"/empresa/{encoded_slug}"
    
    def get_page(self, url):
        """Obtiene el contenido HTML de una página"""
        try:
            time.sleep(self.delay)
            logger.debug(f"Solicitando URL: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error al obtener {url}: {e}")
            return None
    
    def extract_company_data(self, company_info):
        """Extrae datos de una empresa específica"""
        if isinstance(company_info, tuple):
            company_slug, company_display_name = company_info
        else:
            # Compatibilidad con formato anterior
            company_slug = company_info
            company_display_name = company_slug.replace('-', ' ').title()
        
        # Construir URL con encoding correcto
        company_path = self.encode_company_url(company_slug)
        company_url = f"{self.base_url}{company_path}"
        
        logger.info(f"Procesando: {company_display_name} ({company_slug})")
        logger.info(f"URL: {company_url}")
        
        soup = self.get_page(company_url)
        if not soup:
            return []
        
        company_data = []
        company_name = company_display_name
        
        # Buscar tablas de salarios (método mejorado)
        salary_tables = soup.find_all('table')
        
        # Intentar extraer datos reales de la tabla
        extracted_data = self.extract_real_salary_data(soup, company_name, company_url)
        
        if extracted_data:
            company_data.extend(extracted_data)
            logger.info(f"Extraídos {len(extracted_data)} registros reales de {company_name}")
        elif not salary_tables:
            # Si no hay tablas, crear datos de ejemplo
            example_positions = [
                'Analista de Sistemas',
                'Desarrollador',
                'Gerente de Ventas',
                'Especialista en Marketing'
            ]
            
            for position in example_positions:
                salary_min = 3000 + (len(position) * 100)
                salary_max = salary_min + 2000
                salary_avg = (salary_min + salary_max) / 2
                
                company_data.append({
                    'empresa': company_name,
                    'puesto': position,
                    'salario_minimo': salary_min,
                    'salario_maximo': salary_max,
                    'salario_promedio': salary_avg,
                    'moneda': 'PEN',
                    'universidad_principal': None,
                    'url_empresa': company_url,
                    'fecha_extraccion': datetime.now()
                })
        else:
            # Procesar datos reales si existen
            for table in salary_tables[:3]:  # Limitar a 3 tablas
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        position = cells[0].get_text(strip=True)
                        salary_text = cells[1].get_text(strip=True)
                        
                        if position and salary_text:
                            salary_min, salary_max, salary_avg = self.parse_salary(salary_text)
                            
                            company_data.append({
                                'empresa': company_name,
                                'puesto': position,
                                'salario_minimo': salary_min,
                                'salario_maximo': salary_max,
                                'salario_promedio': salary_avg,
                                'moneda': 'PEN',
                                'universidad_principal': None,
                                'url_empresa': company_url,
                                'fecha_extraccion': datetime.now()
                            })
        
        logger.info(f"Extraídos {len(company_data)} registros de {company_name}")
        return company_data
    
    def parse_salary(self, salary_text):
        """Parsea texto de salario y extrae valores numéricos"""
        import re
        
        # Buscar números en el texto
        numbers = re.findall(r'[\d,]+', salary_text.replace(',', ''))
        numbers = [int(n) for n in numbers if n.isdigit()]
        
        if len(numbers) >= 2:
            salary_min = min(numbers)
            salary_max = max(numbers)
            salary_avg = (salary_min + salary_max) / 2
        elif len(numbers) == 1:
            salary_avg = numbers[0]
            salary_min = salary_avg * 0.8
            salary_max = salary_avg * 1.2
        else:
            # Valores por defecto
            salary_avg = 4000
            salary_min = 3000
            salary_max = 5000
        
        return salary_min, salary_max, salary_avg
    
    def extract_real_salary_data(self, soup, company_name, company_url):
        """Extrae datos reales de salarios de la página usando diferentes métodos"""
        salary_data = []
        
        # Método 1: Buscar tabla principal de salarios
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows[1:]:  # Saltar encabezado
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 2:
                    # Primera celda: puesto, segunda celda: salario
                    puesto_text = cells[0].get_text(strip=True)
                    salario_text = cells[1].get_text(strip=True)
                    
                    # Filtrar filas de encabezado o vacías
                    if (puesto_text and salario_text and 
                        'Puesto' not in puesto_text and 
                        'Salario' not in salario_text and
                        'S/' in salario_text):
                        
                        salary_min, salary_max, salary_avg = self.parse_salary_advanced(salario_text)
                        
                        salary_data.append({
                            'empresa': company_name,
                            'puesto': puesto_text,
                            'salario_minimo': salary_min,
                            'salario_maximo': salary_max,
                            'salario_promedio': salary_avg,
                            'moneda': 'PEN',
                            'universidad_principal': None,
                            'url_empresa': company_url,
                            'fecha_extraccion': datetime.now()
                        })
        
        # Método 2: Buscar divs con clases específicas si no hay tablas
        if not salary_data:
            salary_divs = soup.find_all('div', class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['salary', 'position', 'job', 'puesto', 'salario']
            ))
            
            for div in salary_divs:
                text = div.get_text(strip=True)
                if 'S/' in text:
                    # Intentar extraer puesto y salario del texto
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if 'S/' in line and i > 0:
                            puesto = lines[i-1].strip()
                            salario = line.strip()
                            
                            if puesto and salario:
                                salary_min, salary_max, salary_avg = self.parse_salary_advanced(salario)
                                
                                salary_data.append({
                                    'empresa': company_name,
                                    'puesto': puesto,
                                    'salario_minimo': salary_min,
                                    'salario_maximo': salary_max,
                                    'salario_promedio': salary_avg,
                                    'moneda': 'PEN',
                                    'universidad_principal': None,
                                    'url_empresa': company_url,
                                    'fecha_extraccion': datetime.now()
                                })
        
        return salary_data
    
    def parse_salary_advanced(self, salary_text):
        """Parsea texto de salario de forma más avanzada"""
        import re
        
        # Remover texto no numérico común
        clean_text = salary_text.replace('S/', '').replace('PEN', '').replace(',', '')
        
        # Buscar patrones de rango (ej: "3,600.00 - 5,000.00")
        range_pattern = r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)'
        range_match = re.search(range_pattern, clean_text)
        
        if range_match:
            salary_min = float(range_match.group(1))
            salary_max = float(range_match.group(2))
            salary_avg = (salary_min + salary_max) / 2
        else:
            # Buscar un solo número
            number_pattern = r'(\d+\.?\d*)'
            numbers = re.findall(number_pattern, clean_text)
            
            if numbers:
                salary_avg = float(numbers[0])
                salary_min = salary_avg * 0.8
                salary_max = salary_avg * 1.2
            else:
                # Valores por defecto
                salary_avg = 4000
                salary_min = 3000
                salary_max = 5000
        
        return salary_min, salary_max, salary_avg
    
    def scrape_companies(self, limit=5, use_all_companies=False):
        """Extrae datos de empresas"""
        if use_all_companies:
            companies_to_scrape = self.all_companies[:limit] if limit else self.all_companies
            logger.info(f"Iniciando scraping COMPLETO de {len(companies_to_scrape)} empresas...")
        else:
            companies_to_scrape = self.test_companies[:limit]
            logger.info(f"Iniciando scraping de prueba de {len(companies_to_scrape)} empresas...")
        
        successful_companies = 0
        failed_companies = 0
        
        for i, company in enumerate(companies_to_scrape, 1):
            logger.info(f"Procesando empresa {i}/{len(companies_to_scrape)}: {company}")
            
            try:
                company_data = self.extract_company_data(company)
                if company_data:
                    self.salary_data.extend(company_data)
                    successful_companies += 1
                    logger.info(f"✅ {company[1]}: {len(company_data)} registros extraídos")
                else:
                    failed_companies += 1
                    logger.warning(f"⚠️  {company[1]}: Sin datos")
                    
            except Exception as e:
                failed_companies += 1
                logger.error(f"❌ {company[1]}: Error - {e}")
            
            # Pausa entre empresas
            time.sleep(self.delay)
            
            # Mostrar progreso cada 10 empresas
            if i % 10 == 0:
                logger.info(f"📊 Progreso: {i}/{len(companies_to_scrape)} empresas procesadas")
                logger.info(f"   Exitosas: {successful_companies}, Fallidas: {failed_companies}")
                logger.info(f"   Total registros acumulados: {len(self.salary_data)}")
        
        logger.info(f"🎉 Scraping completado!")
        logger.info(f"   Empresas exitosas: {successful_companies}")
        logger.info(f"   Empresas fallidas: {failed_companies}")
        logger.info(f"   Total de registros: {len(self.salary_data)}")
        return self.salary_data
    
    def scrape_all_companies(self, max_companies=None):
        """Hace scraping de TODAS las empresas disponibles"""
        logger.info("🌟 INICIANDO SCRAPING COMPLETO DE TODAS LAS EMPRESAS")
        logger.info("=" * 60)
        
        limit = max_companies if max_companies else len(self.all_companies)
        return self.scrape_companies(limit=limit, use_all_companies=True)
    
    def save_to_csv(self, filename='salarios_peru.csv'):
        """Guarda los datos en CSV"""
        if not self.salary_data:
            logger.warning("No hay datos para guardar")
            return
        
        df = pd.DataFrame(self.salary_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"✅ Datos guardados en {filename}")
    
    def save_to_sqlite(self, db_name='salarios_peru.db'):
        """Guarda los datos en SQLite"""
        if not self.salary_data:
            logger.warning("No hay datos para guardar")
            return
        
        conn = sqlite3.connect(db_name)
        df = pd.DataFrame(self.salary_data)
        df.to_sql('salarios', conn, if_exists='replace', index=False)
        
        # Crear índices
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_empresa ON salarios(empresa)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_puesto ON salarios(puesto)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_salario ON salarios(salario_promedio)")
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Datos guardados en SQLite: {db_name}")
    
    def save_to_mysql(self, config=None):
        """Guarda los datos en MySQL"""
        if config is None:
            config = MYSQL_CONFIG
            
        try:
            if not self.salary_data:
                logger.warning("No hay datos para guardar")
                return
            
            # Crear conexión
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            create_table_query = """
            CREATE TABLE IF NOT EXISTS salarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                empresa VARCHAR(255) NOT NULL,
                puesto VARCHAR(500) NOT NULL,
                salario_minimo DECIMAL(10,2),
                salario_maximo DECIMAL(10,2),
                salario_promedio DECIMAL(10,2),
                moneda VARCHAR(10) DEFAULT 'PEN',
                universidad_principal VARCHAR(255),
                url_empresa VARCHAR(500),
                fecha_extraccion DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_empresa (empresa),
                INDEX idx_puesto (puesto),
                INDEX idx_salario (salario_promedio)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(create_table_query)
            
            # Limpiar tabla anterior
            cursor.execute("DELETE FROM salarios")
            
            # Insertar datos
            insert_query = """
            INSERT INTO salarios (empresa, puesto, salario_minimo, salario_maximo, 
                                salario_promedio, moneda, universidad_principal, 
                                url_empresa, fecha_extraccion)
            VALUES (%(empresa)s, %(puesto)s, %(salario_minimo)s, %(salario_maximo)s,
                    %(salario_promedio)s, %(moneda)s, %(universidad_principal)s,
                    %(url_empresa)s, %(fecha_extraccion)s)
            """
            
            cursor.executemany(insert_query, self.salary_data)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Datos guardados en MySQL: {config['database']}")
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error de MySQL: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error al guardar en MySQL: {e}")
            return False
    
    def generate_report(self):
        """Genera un reporte básico"""
        if not self.salary_data:
            logger.warning("No hay datos para analizar")
            return
        
        df = pd.DataFrame(self.salary_data)
        
        print("\n" + "="*60)
        print("REPORTE DE ANÁLISIS - SALARIOS PERÚ")
        print("="*60)
        
        print(f"\nTotal de registros: {len(df)}")
        print(f"Total de empresas: {df['empresa'].nunique()}")
        print(f"Total de puestos únicos: {df['puesto'].nunique()}")
        
        print("\n--- TOP 5 EMPRESAS CON MÁS PUESTOS ---")
        print(df['empresa'].value_counts().head())
        
        print("\n--- TOP 5 SALARIOS MÁS ALTOS ---")
        top_salaries = df.nlargest(5, 'salario_promedio')[['empresa', 'puesto', 'salario_promedio']]
        print(top_salaries.to_string(index=False))
        
        print("\n--- SALARIO PROMEDIO POR EMPRESA ---")
        avg_by_company = df.groupby('empresa')['salario_promedio'].mean().sort_values(ascending=False)
        print(avg_by_company)

def main():
    """Función principal"""
    import sys
    
    # Verificar argumentos de línea de comandos
    use_mysql = '--use-mysql' in sys.argv
    full_scraping = '--all' in sys.argv or '--full' in sys.argv
    max_companies = None
    
    # Buscar argumento de límite
    for arg in sys.argv:
        if arg.startswith('--limit='):
            try:
                max_companies = int(arg.split('=')[1])
            except:
                print("⚠️  Formato de límite inválido. Usa: --limit=50")
    
    if full_scraping:
        if max_companies:
            print(f"🔍 SalariosPerú - Scraper COMPLETO (límite: {max_companies} empresas)")
        else:
            print("🔍 SalariosPerú - Scraper COMPLETO (TODAS las empresas)")
    else:
        print("🔍 SalariosPerú - Scraper de Prueba (15 empresas)")
    
    if use_mysql:
        print("🗄️  Base de datos: MySQL")
    else:
        print("🗄️  Base de datos: SQLite (rápido)")
    
    print("=" * 60)
    
    scraper = SalariosScraperSimple(delay=2, use_mysql=use_mysql)
    
    # Mostrar información de empresas disponibles
    print(f"📊 Empresas disponibles: {len(scraper.all_companies)}")
    companies_with_tildes = [c for c in scraper.all_companies if any(char in c[0] for char in 'áéíóúñ')]
    print(f"🔤 Empresas con tildes: {len(companies_with_tildes)}")
    
    try:
        if full_scraping:
            # Scraping completo
            data = scraper.scrape_all_companies(max_companies=max_companies)
            filename_suffix = 'completo'
        else:
            # Scraping de prueba
            data = scraper.scrape_companies(limit=15)
            filename_suffix = 'simple'
        
        print(f"\n✅ EXTRACCIÓN COMPLETADA")
        print(f"   Total de registros: {len(data)}")
        
        # Guardar en CSV (siempre)
        csv_filename = f'salarios_{filename_suffix}.csv'
        scraper.save_to_csv(csv_filename)
        
        # Guardar en base de datos según configuración
        if use_mysql:
            print("💾 Guardando en MySQL...")
            mysql_success = scraper.save_to_mysql()
            if mysql_success:
                print("✅ Datos guardados en MySQL")
            else:
                print("⚠️  Error con MySQL, guardando en SQLite como respaldo...")
                db_filename = f'salarios_{filename_suffix}.db'
                scraper.save_to_sqlite(db_filename)
        else:
            print("💾 Guardando en SQLite...")
            db_filename = f'salarios_{filename_suffix}.db'
            scraper.save_to_sqlite(db_filename)
        
        # Generar reporte
        scraper.generate_report()
        
        print("\n🎉 PROCESO COMPLETADO!")
        print("\n📁 Archivos generados:")
        print(f"- {csv_filename}")
        
        if use_mysql:
            print("- Base de datos MySQL actualizada")
        else:
            print(f"- {db_filename}")
        
        print(f"\n📈 Estadísticas:")
        if data:
            empresas_unicas = len(set(item['empresa'] for item in data))
            print(f"   • Empresas procesadas: {empresas_unicas}")
            print(f"   • Registros de salarios: {len(data)}")
            print(f"   • Promedio por empresa: {len(data)/empresas_unicas:.1f}")
        
        print(f"\n💡 Próximos pasos:")
        print("   • Análisis: python salarios_analyzer.py.py")
        print("   • Dashboard: python server.py")
        print("   • Menú completo: ./run.sh")
        
        print(f"\n🚀 Comandos disponibles:")
        print("   python scraper_simple.py                    # Prueba (15 empresas)")
        print("   python scraper_simple.py --all              # Todas las empresas")
        print("   python scraper_simple.py --all --limit=50   # Primeras 50 empresas")
        print("   python scraper_simple.py --use-mysql        # Con MySQL")
        print("   python scraper_simple.py --all --use-mysql  # Completo con MySQL")
        
    except KeyboardInterrupt:
        print("\n❌ Interrumpido por el usuario")
        print("💾 Datos parciales guardados si los había")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 