#!/usr/bin/env python3
"""
Scraper para SalariosPerú.com (2026)
Extrae datos de salarios desde JSON-LD (Schema.org JobPosting)
Compatible con el nuevo sitio Next.js
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import json
import time
import re
import logging
from datetime import datetime
from urllib.parse import quote, unquote

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from empresas_auto import get_empresas_auto
    EMPRESAS_SOURCE = "auto"
except ImportError:
    from empresas_completas import get_all_companies
    EMPRESAS_SOURCE = "manual"


class SalariosScraperSimple:
    def __init__(self, delay=2, use_mysql=False):
        self.base_url = "https://salariosperu.com"
        self.delay = delay
        self.use_mysql = use_mysql
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-PE,es;q=0.9,en;q=0.8',
        })
        self.salary_data = []

        # Cargar empresas
        if EMPRESAS_SOURCE == "auto":
            self.all_companies = get_empresas_auto()
            logger.info(f"Usando lista automática: {len(self.all_companies)} empresas")
        else:
            self.all_companies = get_all_companies()
            logger.info(f"Usando lista manual: {len(self.all_companies)} empresas")

        # Empresas para testing rápido
        self.test_companies = [
            ('banco-de-credito-bcp', 'Banco de Crédito BCP'),
            ('interbank', 'Interbank'),
            ('bbva-peru', 'BBVA en Perú'),
            ('alicorpoficial', 'Alicorp'),
            ('yapeoficial', 'Yape'),
            ('culqi', 'Culqi'),
            ('entel-perú', 'Entel Perú'),
            ('deloitte', 'Deloitte'),
            ('rappi', 'Rappi'),
            ('minsur-s-a-', 'Minsur S.A.'),
            ('scotiabank', 'Scotiabank'),
            ('rimac-seguros', 'Rimac Seguros'),
            ('izipay', 'izipay'),
            ('loréal', "L'Oréal"),
            ('belcorpcorporativo', 'Belcorp'),
        ]

    def get_page(self, url):
        """Obtiene el contenido HTML de una página"""
        try:
            time.sleep(self.delay)
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error al obtener {url}: {e}")
            return None

    def extract_jsonld_data(self, soup):
        """Extrae datos de salarios desde tags <script type='application/ld+json'>"""
        job_postings = []
        company_info = {}

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
            except (json.JSONDecodeError, TypeError):
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                item_type = item.get('@type', '')

                if item_type == 'Organization':
                    company_info = {
                        'name': item.get('name', ''),
                        'url': item.get('url', ''),
                        'description': item.get('description', ''),
                    }
                elif item_type == 'JobPosting':
                    job_postings.append(item)

        return company_info, job_postings

    def extract_from_nextjs_data(self, soup):
        """Extrae datos de los scripts __next_f.push (RSC payload)"""
        salary_entries = []

        for script in soup.find_all('script'):
            text = script.string or ''
            if 'self.__next_f.push' not in text:
                continue

            # Buscar patrones de salary_range en el payload
            salary_matches = re.findall(
                r'"title"\s*:\s*"([^"]+)"[^}]*?"salary_range"\s*:\s*"([^"]+)"',
                text
            )
            for title, salary_range in salary_matches:
                salary_entries.append({
                    'title': title,
                    'salary_range': salary_range,
                })

        return salary_entries

    def parse_salary_range(self, salary_text):
        """Parsea texto de salario y extrae min, max, promedio"""
        if not salary_text:
            return None, None, None

        # Limpiar
        clean = salary_text.replace('S/', '').replace('PEN', '').replace(',', '').strip()

        # Rango: "3600.00 - 5000.00"
        range_match = re.search(r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)', clean)
        if range_match:
            salary_min = float(range_match.group(1))
            salary_max = float(range_match.group(2))
            return salary_min, salary_max, (salary_min + salary_max) / 2

        # Valor único: "4600.00"
        single_match = re.search(r'(\d+\.?\d*)', clean)
        if single_match:
            val = float(single_match.group(1))
            return val, val, val

        return None, None, None

    def extract_salary_from_description(self, description):
        """Extrae rango salarial de la descripción del JobPosting"""
        if not description:
            return None
        match = re.search(r'Rango salarial:\s*(S/[^.]+)', description)
        if match:
            return match.group(1).strip()
        match = re.search(r'S/\s*[\d,]+\.?\d*(?:\s*-\s*S/\s*[\d,]+\.?\d*)?', description)
        if match:
            return match.group(0).strip()
        return None

    def extract_company_data(self, company_info_tuple):
        """Extrae datos de salarios de una empresa"""
        if isinstance(company_info_tuple, tuple):
            company_slug, company_display_name = company_info_tuple
        else:
            company_slug = company_info_tuple
            company_display_name = unquote(company_slug).replace('-', ' ').title()

        # Codificar slug para URL
        encoded_slug = quote(company_slug, safe='-.')
        company_url = f"{self.base_url}/empresa/{encoded_slug}"

        logger.info(f"Procesando: {company_display_name}")
        soup = self.get_page(company_url)
        if not soup:
            return []

        company_data = []

        # Método 1: Extraer de JSON-LD (Schema.org)
        org_info, job_postings = self.extract_jsonld_data(soup)

        # Usar nombre real de la empresa si lo encontramos
        if org_info.get('name'):
            company_display_name = org_info['name']

        for job in job_postings:
            title = job.get('title', '')
            description = job.get('description', '')

            # Extraer salario de la descripción
            salary_text = self.extract_salary_from_description(description)
            salary_min, salary_max, salary_avg = self.parse_salary_range(salary_text)

            # Extraer universidad si está disponible
            universidad = None
            if 'universidad' in str(job).lower():
                uni_match = re.search(r'"universidad"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]+)"', json.dumps(job))
                if uni_match:
                    universidad = uni_match.group(1)

            # Fechas
            date_posted = job.get('datePosted', '')
            valid_through = job.get('validThrough', '')

            if title:
                company_data.append({
                    'empresa': company_display_name,
                    'puesto': title,
                    'salario_minimo': salary_min,
                    'salario_maximo': salary_max,
                    'salario_promedio': salary_avg,
                    'moneda': 'PEN',
                    'universidad_principal': universidad,
                    'url_empresa': company_url,
                    'fecha_inicio': date_posted,
                    'fecha_fin': valid_through,
                    'fecha_extraccion': datetime.now().isoformat()
                })

        # Método 2: Si JSON-LD no dio resultados, intentar Next.js RSC payload
        if not company_data:
            nextjs_entries = self.extract_from_nextjs_data(soup)
            for entry in nextjs_entries:
                salary_min, salary_max, salary_avg = self.parse_salary_range(entry.get('salary_range'))
                company_data.append({
                    'empresa': company_display_name,
                    'puesto': entry.get('title', 'Desconocido'),
                    'salario_minimo': salary_min,
                    'salario_maximo': salary_max,
                    'salario_promedio': salary_avg,
                    'moneda': 'PEN',
                    'universidad_principal': None,
                    'url_empresa': company_url,
                    'fecha_inicio': None,
                    'fecha_fin': None,
                    'fecha_extraccion': datetime.now().isoformat()
                })

        # Método 3: Fallback a tablas HTML (compatibilidad)
        if not company_data:
            company_data = self.extract_from_html_tables(soup, company_display_name, company_url)

        logger.info(f"  -> {len(company_data)} registros de {company_display_name}")
        return company_data

    def extract_from_html_tables(self, soup, company_name, company_url):
        """Fallback: extrae datos de tablas HTML si existen"""
        data = []
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    puesto = cells[0].get_text(strip=True)
                    salario_text = cells[1].get_text(strip=True)
                    if puesto and salario_text and 'S/' in salario_text:
                        salary_min, salary_max, salary_avg = self.parse_salary_range(salario_text)
                        data.append({
                            'empresa': company_name,
                            'puesto': puesto,
                            'salario_minimo': salary_min,
                            'salario_maximo': salary_max,
                            'salario_promedio': salary_avg,
                            'moneda': 'PEN',
                            'universidad_principal': None,
                            'url_empresa': company_url,
                            'fecha_inicio': None,
                            'fecha_fin': None,
                            'fecha_extraccion': datetime.now().isoformat()
                        })
        return data

    def scrape_companies(self, limit=5, use_all_companies=False):
        """Extrae datos de empresas"""
        if use_all_companies:
            companies_to_scrape = self.all_companies[:limit] if limit else self.all_companies
            logger.info(f"Scraping COMPLETO de {len(companies_to_scrape)} empresas...")
        else:
            companies_to_scrape = self.test_companies[:limit]
            logger.info(f"Scraping de prueba de {len(companies_to_scrape)} empresas...")

        successful = 0
        failed = 0

        for i, company in enumerate(companies_to_scrape, 1):
            try:
                company_data = self.extract_company_data(company)
                if company_data:
                    self.salary_data.extend(company_data)
                    successful += 1
                else:
                    failed += 1
                    logger.warning(f"  Sin datos para {company[1] if isinstance(company, tuple) else company}")
            except Exception as e:
                failed += 1
                logger.error(f"  Error en {company}: {e}")

            if i % 10 == 0:
                logger.info(f"Progreso: {i}/{len(companies_to_scrape)} | OK: {successful} | Fail: {failed} | Registros: {len(self.salary_data)}")

        logger.info(f"Scraping completado! OK: {successful} | Fail: {failed} | Total registros: {len(self.salary_data)}")
        return self.salary_data

    def scrape_all_companies(self, max_companies=None):
        """Hace scraping de TODAS las empresas disponibles"""
        limit = max_companies if max_companies else len(self.all_companies)
        return self.scrape_companies(limit=limit, use_all_companies=True)

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

        cursor = conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_empresa ON salarios(empresa)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_puesto ON salarios(puesto)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_salario ON salarios(salario_promedio)")
        conn.commit()
        conn.close()
        logger.info(f"Datos guardados en SQLite: {db_name}")

    def save_to_mysql(self, config=None):
        """Guarda los datos en MySQL"""
        try:
            import mysql.connector
            from mysql_config import MYSQL_CONFIG
            if config is None:
                config = MYSQL_CONFIG

            if not self.salary_data:
                logger.warning("No hay datos para guardar")
                return False

            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()

            cursor.execute("""
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
                fecha_inicio DATE,
                fecha_fin DATE,
                fecha_extraccion DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_empresa (empresa),
                INDEX idx_puesto (puesto),
                INDEX idx_salario (salario_promedio)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            cursor.execute("DELETE FROM salarios")

            insert_query = """
            INSERT INTO salarios (empresa, puesto, salario_minimo, salario_maximo,
                                salario_promedio, moneda, universidad_principal,
                                url_empresa, fecha_inicio, fecha_fin, fecha_extraccion)
            VALUES (%(empresa)s, %(puesto)s, %(salario_minimo)s, %(salario_maximo)s,
                    %(salario_promedio)s, %(moneda)s, %(universidad_principal)s,
                    %(url_empresa)s, %(fecha_inicio)s, %(fecha_fin)s, %(fecha_extraccion)s)
            """

            cursor.executemany(insert_query, self.salary_data)
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Datos guardados en MySQL: {config['database']}")
            return True
        except ImportError:
            logger.error("mysql-connector-python no instalado")
            return False
        except Exception as e:
            logger.error(f"Error MySQL: {e}")
            return False

    def generate_report(self):
        """Genera un reporte básico"""
        if not self.salary_data:
            logger.warning("No hay datos para analizar")
            return

        df = pd.DataFrame(self.salary_data)

        # Filtrar registros con salario válido
        df_valid = df[df['salario_promedio'].notna() & (df['salario_promedio'] > 0)]

        print("\n" + "=" * 60)
        print("REPORTE DE ANALISIS - SALARIOS PERU 2026")
        print("=" * 60)

        print(f"\nTotal de registros: {len(df)}")
        print(f"Registros con salario: {len(df_valid)}")
        print(f"Total de empresas: {df['empresa'].nunique()}")
        print(f"Total de puestos unicos: {df['puesto'].nunique()}")

        if not df_valid.empty:
            print(f"\nSalario promedio general: S/ {df_valid['salario_promedio'].mean():,.2f}")
            print(f"Salario mediano: S/ {df_valid['salario_promedio'].median():,.2f}")
            print(f"Rango: S/ {df_valid['salario_promedio'].min():,.2f} - S/ {df_valid['salario_promedio'].max():,.2f}")

            print("\n--- TOP 10 SALARIOS MAS ALTOS ---")
            top = df_valid.nlargest(10, 'salario_promedio')[['empresa', 'puesto', 'salario_promedio']]
            for _, row in top.iterrows():
                print(f"  S/ {row['salario_promedio']:>10,.2f} | {row['empresa'][:25]:<25} | {row['puesto'][:40]}")

            print("\n--- TOP 10 EMPRESAS (por salario promedio) ---")
            avg_by_company = df_valid.groupby('empresa')['salario_promedio'].agg(['mean', 'count'])
            avg_by_company = avg_by_company[avg_by_company['count'] >= 3].sort_values('mean', ascending=False).head(10)
            for empresa, row in avg_by_company.iterrows():
                print(f"  S/ {row['mean']:>10,.2f} ({int(row['count']):>3} puestos) | {empresa[:40]}")

        # Universidades
        if 'universidad_principal' in df.columns:
            unis = df[df['universidad_principal'].notna()]
            if not unis.empty:
                print(f"\n--- UNIVERSIDADES ({len(unis)} registros) ---")
                print(unis['universidad_principal'].value_counts().head(10))


def main():
    """Función principal"""
    import sys

    use_mysql = '--use-mysql' in sys.argv
    full_scraping = '--all' in sys.argv or '--full' in sys.argv
    max_companies = None

    for arg in sys.argv:
        if arg.startswith('--limit='):
            try:
                max_companies = int(arg.split('=')[1])
            except ValueError:
                print("Formato invalido. Usa: --limit=50")

    if full_scraping:
        label = f"COMPLETO (limite: {max_companies})" if max_companies else "COMPLETO (TODAS)"
    else:
        label = "PRUEBA (15 empresas)"

    print(f"Salarios Peru - Scraper {label}")
    print(f"DB: {'MySQL' if use_mysql else 'SQLite'}")
    print("=" * 60)

    scraper = SalariosScraperSimple(delay=2, use_mysql=use_mysql)
    print(f"Empresas disponibles: {len(scraper.all_companies)}")

    try:
        if full_scraping:
            data = scraper.scrape_all_companies(max_companies=max_companies)
            suffix = 'completo'
        else:
            data = scraper.scrape_companies(limit=15)
            suffix = 'simple'

        print(f"\nTotal registros extraidos: {len(data)}")

        csv_file = f'salarios_{suffix}.csv'
        scraper.save_to_csv(csv_file)

        if use_mysql:
            if not scraper.save_to_mysql():
                db_file = f'salarios_{suffix}.db'
                scraper.save_to_sqlite(db_file)
        else:
            db_file = f'salarios_{suffix}.db'
            scraper.save_to_sqlite(db_file)

        scraper.generate_report()

        if data:
            empresas = len(set(item['empresa'] for item in data))
            con_salario = len([d for d in data if d.get('salario_promedio')])
            print(f"\nResumen: {empresas} empresas, {len(data)} registros, {con_salario} con salario")

        print(f"\nComandos:")
        print("  python scraper_simple.py                    # Prueba (15 empresas)")
        print("  python scraper_simple.py --all              # Todas las empresas")
        print("  python scraper_simple.py --all --limit=50   # Primeras 50")
        print("  python scraper_simple.py --use-mysql        # Con MySQL")
        print("  python update_empresas.py                   # Actualizar lista de empresas")

    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
