#!/usr/bin/env python3
"""
Web Scraper para SalariosPerú.com
Extrae datos de salarios por empresa y los almacena en SQLite, CSV o MySQL
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import time
import re
from urllib.parse import urljoin, urlparse
import json
import logging
from datetime import datetime
import csv

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SalariosPeruScraper:
    def __init__(self, delay=1):
        """
        Inicializa el scraper
        
        Args:
            delay (int): Tiempo de espera entre requests en segundos
        """
        self.base_url = "https://salariosperu.com"
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.companies = []
        self.salary_data = []
        
    def get_page(self, url):
        """Obtiene el contenido HTML de una página"""
        try:
            time.sleep(self.delay)
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Error al obtener {url}: {e}")
            return None
    
    def discover_companies(self):
        """
        Descubre TODAS las empresas disponibles en el sitio usando múltiples estrategias
        """
        logger.info("🔍 Descubriendo TODAS las empresas disponibles...")
        
        company_links = set()
        
        # Estrategia 1: Página principal
        soup = self.get_page(self.base_url)
        if soup:
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/empresa/' in href:
                    full_url = urljoin(self.base_url, href)
                    company_links.add(full_url)
        
        # Estrategia 2: Buscar sitemap.xml
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap/",
            f"{self.base_url}/robots.txt"
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                response = self.session.get(sitemap_url)
                if response.status_code == 200:
                    # Buscar URLs de empresas en sitemap
                    import re
                    empresa_urls = re.findall(r'https?://[^<\s]+/empresa/[^<\s]+', response.text)
                    company_links.update(empresa_urls)
                    logger.info(f"✅ Encontradas empresas adicionales en {sitemap_url}")
            except:
                continue
        
        # Estrategia 3: Búsqueda alfabética sistemática
        logger.info("🔤 Realizando búsqueda alfabética sistemática...")
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        search_patterns = []
        
        # Generar patrones de búsqueda
        for letter in alphabet:
            search_patterns.extend([
                letter,
                f"{letter}a", f"{letter}e", f"{letter}i", f"{letter}o", f"{letter}u"
            ])
        
        # Agregar términos comunes de empresas
        business_terms = [
            'banco', 'tech', 'group', 'corp', 'company', 'sac', 'sa', 'peru',
            'consulting', 'services', 'international', 'global', 'solutions'
        ]
        search_patterns.extend(business_terms)
        
        for pattern in search_patterns[:20]:  # Limitar para no sobrecargar
            search_url = f"{self.base_url}/search?q={pattern}"
            try:
                soup = self.get_page(search_url)
                if soup:
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if '/empresa/' in href:
                            full_url = urljoin(self.base_url, href)
                            company_links.add(full_url)
            except:
                continue
            
            time.sleep(0.5)  # Pausa más corta para búsquedas
        
        # Estrategia 4: Lista extendida de empresas conocidas del mercado peruano
        known_companies = [
            # Banca y Finanzas
            'banco-de-credito-bcp', 'bbva-peru', 'interbank', 'scotiabank-peru',
            'banco-de-la-nacion', 'credicorp', 'rimac-seguros', 'pacifico-seguros',
            'yape', 'plin', 'culqi', 'izipay',
            
            # Retail y Consumo
            'alicorp', 'gloria', 'nestle-peru', 'unilever-peru', 'procter-gamble',
            'saga-falabella', 'ripley', 'tottus', 'plaza-vea', 'wong',
            'sodimac', 'maestro', 'cassinelli',
            
            # Tecnología
            'ibm-peru', 'microsoft-peru', 'google-peru', 'oracle-peru',
            'sap-peru', 'accenture-peru', 'tcs-peru', 'globant-peru',
            
            # Telecomunicaciones
            'entel-peru', 'movistar-peru', 'claro-peru', 'bitel',
            
            # Minería y Energía
            'antamina', 'southern-copper', 'volcan-cia-minera', 'buenaventura',
            'cerro-verde', 'enel-peru', 'luz-del-sur', 'electroandes',
            
            # Bebidas y Alimentos
            'ab-inbev', 'backus', 'coca-cola-peru', 'pepsi-peru',
            'san-fernando', 'redondos', 'laive',
            
            # Consultoría
            'ey', 'deloitte-peru', 'pwc-peru', 'kpmg-peru',
            'mckinsey-peru', 'bcg-peru', 'bain-peru',
            
            # Cosmética y Farmacia
            'loreal', 'nivea-peru', 'inkafarma', 'mifarma', 'boticas-fasa',
            
            # Construcción
            'cosapi', 'graa-montero', 'jjc-contratistas', 'motores-diesel',
            
            # Logística y Transporte
            'dhl-peru', 'fedex-peru', 'olva-courier', 'serpost',
            'ransa', 'neptunia',
            
            # Educación
            'universidad-pacifico', 'esan', 'utec', 'tecsup',
            
            # Otros
            'ferreyros', 'maple-energy', 'intercorp', 'grupo-romero'
        ]
        
        for company in known_companies:
            company_url = f"{self.base_url}/empresa/{company}"
            company_links.add(company_url)
        
        # Estrategia 5: Variaciones de nombres (plurales, con guiones, etc.)
        variations = []
        for company in known_companies:
            # Agregar variaciones
            variations.extend([
                company.replace('-', ''),
                company.replace('-peru', ''),
                company.replace('-', '_'),
                f"{company}-sa",
                f"{company}-sac",
                f"{company}-group"
            ])
        
        for variation in variations:
            company_url = f"{self.base_url}/empresa/{variation}"
            company_links.add(company_url)
        
        # Filtrar URLs válidas
        valid_companies = []
        logger.info("🔍 Validando empresas encontradas...")
        
        for i, company_url in enumerate(list(company_links)[:100]):  # Limitar para testing
            if i % 10 == 0:
                logger.info(f"Validando empresa {i}/{min(100, len(company_links))}")
            
            # Verificar si la URL existe
            try:
                response = self.session.head(company_url)
                if response.status_code == 200:
                    valid_companies.append(company_url)
                time.sleep(0.2)  # Pausa corta
            except:
                continue
        
        self.companies = valid_companies
        logger.info(f"✅ Descubrimiento completado: {len(self.companies)} empresas válidas encontradas")
        
        # Guardar lista de empresas para referencia
        with open('empresas_encontradas.txt', 'w', encoding='utf-8') as f:
            for company in self.companies:
                f.write(f"{company}\n")
        
        return self.companies
    
    def extract_company_data(self, company_url):
        """
        Extrae datos de salarios de una empresa específica
        """
        logger.info(f"Extrayendo datos de: {company_url}")
        
        soup = self.get_page(company_url)
        if not soup:
            return []
        
        company_name = self.extract_company_name(company_url, soup)
        company_data = []
        
        # Buscar tabla de salarios
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows[1:]:  # Saltar header
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    position = cells[0].get_text(strip=True)
                    salary_text = cells[1].get_text(strip=True)
                    
                    # Limpiar y parsear salario
                    salary_info = self.parse_salary(salary_text)
                    
                    if position and salary_info:
                        record = {
                            'empresa': company_name,
                            'puesto': position,
                            'salario_minimo': salary_info['min'],
                            'salario_maximo': salary_info['max'],
                            'salario_promedio': salary_info['avg'],
                            'moneda': salary_info['currency'],
                            'url_empresa': company_url,
                            'fecha_extraccion': datetime.now().isoformat()
                        }
                        company_data.append(record)
        
        # También buscar información adicional como universidades
        university_info = self.extract_university_info(soup)
        for record in company_data:
            record.update(university_info)
        
        logger.info(f"Extraídos {len(company_data)} puestos de {company_name}")
        return company_data
    
    def extract_company_name(self, url, soup):
        """Extrae el nombre de la empresa"""
        # Intentar obtener del título de la página
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            # Buscar patrón "Salarios en EMPRESA"
            match = re.search(r'Salarios en (.+?) en', title_text)
            if match:
                return match.group(1).strip()
        
        # Como fallback, usar la URL
        return url.split('/')[-1].replace('-', ' ').title()
    
    def parse_salary(self, salary_text):
        """
        Parsea texto de salario y extrae valores numéricos
        Ejemplos: "S/ 7,857.00", "S/ 6,364.00 - S/ 7,520.00"
        """
        if not salary_text:
            return None
        
        # Detectar moneda
        currency = 'PEN' if 'S/' in salary_text else 'USD'
        
        # Extraer números
        numbers = re.findall(r'[\d,]+\.?\d*', salary_text.replace(',', ''))
        
        if not numbers:
            return None
        
        # Convertir a float
        try:
            values = [float(num) for num in numbers]
        except ValueError:
            return None
        
        if len(values) == 1:
            # Salario único
            return {
                'min': values[0],
                'max': values[0],
                'avg': values[0],
                'currency': currency
            }
        elif len(values) == 2:
            # Rango de salarios
            return {
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / 2,
                'currency': currency
            }
        else:
            return None
    
    def extract_university_info(self, soup):
        """Extrae información sobre universidades si está disponible"""
        university_info = {'universidad_principal': None}
        
        # Buscar texto que mencione universidades
        text = soup.get_text()
        
        # Patrones comunes de universidades peruanas
        universities = [
            'Universidad del Pacífico',
            'Universidad de Lima',
            'Pontificia Universidad Católica del Perú',
            'Universidad San Martín de Porres',
            'Universidad Nacional Mayor de San Marcos',
            'Universidad Peruana de Ciencias Aplicadas',
            'Universidad ESAN',
            'Universidad Nacional de Ingeniería'
        ]
        
        for university in universities:
            if university in text:
                university_info['universidad_principal'] = university
                break
        
        return university_info
    
    def scrape_all_companies(self):
        """Extrae datos de todas las empresas"""
        if not self.companies:
            self.discover_companies()
        
        logger.info(f"Iniciando scraping de {len(self.companies)} empresas...")
        
        for i, company_url in enumerate(self.companies, 1):
            logger.info(f"Procesando empresa {i}/{len(self.companies)}")
            
            company_data = self.extract_company_data(company_url)
            self.salary_data.extend(company_data)
            
            # Pausa entre empresas
            time.sleep(self.delay)
        
        logger.info(f"Scraping completado. Total de registros: {len(self.salary_data)}")
        return self.salary_data
    
    def save_to_csv(self, filename='salarios_peru.csv'):
        """Guarda los datos en CSV"""
        if not self.salary_data:
            logger.warning("No hay datos para guardar")
            return
        
        df = pd.DataFrame(self.salary_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Datos guardados en {filename}")
    
    def save_to_sqlite(self, db_name='salarios_peru.db'):
        """Guarda los datos en SQLite"""
        if not self.salary_data:
            logger.warning("No hay datos para guardar")
            return
        
        conn = sqlite3.connect(db_name)
        df = pd.DataFrame(self.salary_data)
        df.to_sql('salarios', conn, if_exists='replace', index=False)
        
        # Crear índices para mejorar consultas
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_empresa ON salarios(empresa)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_puesto ON salarios(puesto)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_salario ON salarios(salario_promedio)")
        
        conn.commit()
        conn.close()
        logger.info(f"Datos guardados en base SQLite: {db_name}")
    
    def save_to_mysql(self, host, user, password, database):
        """Guarda los datos en MySQL"""
        try:
            import mysql.connector
            
            if not self.salary_data:
                logger.warning("No hay datos para guardar")
                return
            
            # Crear conexión
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            create_table_query = """
            CREATE TABLE IF NOT EXISTS salarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                empresa VARCHAR(255),
                puesto VARCHAR(500),
                salario_minimo DECIMAL(10,2),
                salario_maximo DECIMAL(10,2),
                salario_promedio DECIMAL(10,2),
                moneda VARCHAR(10),
                universidad_principal VARCHAR(255),
                url_empresa VARCHAR(500),
                fecha_extraccion DATETIME,
                INDEX idx_empresa (empresa),
                INDEX idx_puesto (puesto),
                INDEX idx_salario (salario_promedio)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(create_table_query)
            
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
            
            logger.info(f"Datos guardados en MySQL: {database}")
            
        except ImportError:
            logger.error("mysql-connector-python no está instalado. Instala con: pip install mysql-connector-python")
        except Exception as e:
            logger.error(f"Error al guardar en MySQL: {e}")
    
    def generate_analysis_report(self):
        """Genera un reporte de análisis básico"""
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
        
        print("\n--- TOP 10 EMPRESAS CON MÁS PUESTOS ---")
        print(df['empresa'].value_counts().head(10))
        
        print("\n--- TOP 10 SALARIOS MÁS ALTOS ---")
        top_salaries = df.nlargest(10, 'salario_promedio')[['empresa', 'puesto', 'salario_promedio']]
        print(top_salaries.to_string(index=False))
        
        print("\n--- SALARIO PROMEDIO POR EMPRESA ---")
        avg_by_company = df.groupby('empresa')['salario_promedio'].mean().sort_values(ascending=False).head(10)
        print(avg_by_company)
        
        if 'universidad_principal' in df.columns:
            universidades = df[df['universidad_principal'].notna()]
            if not universidades.empty:
                print("\n--- SALARIOS POR UNIVERSIDAD ---")
                avg_by_uni = universidades.groupby('universidad_principal')['salario_promedio'].mean().sort_values(ascending=False)
                print(avg_by_uni)


def main():
    """Función principal"""
    print("🔍 Iniciando Web Scraping de SalariosPerú.com")
    print("=" * 50)
    
    # Crear scraper
    scraper = SalariosPeruScraper(delay=2)  # 2 segundos entre requests
    
    # Ejecutar scraping
    try:
        # Descubrir empresas
        companies = scraper.discover_companies()
        print(f"✅ Encontradas {len(companies)} empresas")
        
        # Extraer datos
        data = scraper.scrape_all_companies()
        print(f"✅ Extraídos {len(data)} registros de salarios")
        
        # Guardar en diferentes formatos
        scraper.save_to_csv('salarios_simple.csv')
        scraper.save_to_sqlite('salarios_simple.db')
        
        # Generar reporte
        scraper.generate_analysis_report()
        
        print("\n🎉 Scraping completado exitosamente!")
        print("\nArchivos generados:")
        print("- salarios_simple.csv (datos en CSV)")
        print("- salarios_simple.db (base de datos SQLite)")
        
        # Ejemplo de uso con MySQL (comentado)
        # scraper.save_to_mysql('localhost', 'usuario', 'password', 'salarios_db')
        
    except KeyboardInterrupt:
        print("\n❌ Scraping interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error durante el scraping: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()