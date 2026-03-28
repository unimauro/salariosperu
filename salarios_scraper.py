#!/usr/bin/env python3
"""
Web Scraper para SalariosPerú.com (2026)
Descubre empresas desde el sitemap y extrae datos de salarios via JSON-LD.
Almacena en SQLite, CSV o MySQL.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import time
import re
import json
import logging
from datetime import datetime
from urllib.parse import urljoin, quote, unquote

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SalariosPeruScraper:
    def __init__(self, delay=2):
        self.base_url = "https://salariosperu.com"
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        self.companies = []
        self.salary_data = []

    def get_page(self, url):
        """Obtiene el contenido HTML de una página"""
        try:
            time.sleep(self.delay)
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Error al obtener {url}: {e}")
            return None

    def discover_companies(self):
        """Descubre empresas desde el sitemap.xml"""
        logger.info("Descubriendo empresas desde sitemap.xml...")

        try:
            response = self.session.get(f"{self.base_url}/sitemap.xml", timeout=15)
            response.raise_for_status()

            slugs = re.findall(
                r'<loc>https?://(?:www\.)?salariosperu\.com/empresa/([^<]+)</loc>',
                response.text
            )
            slugs = [s.strip() for s in slugs if s.strip() and s.strip() != 'None']

            self.companies = []
            for slug in slugs:
                name = unquote(slug).replace('-', ' ').title()
                self.companies.append((slug, name))

            logger.info(f"Encontradas {len(self.companies)} empresas en el sitemap")

        except Exception as e:
            logger.error(f"Error al obtener sitemap: {e}")
            # Fallback: cargar desde empresas_auto.py
            try:
                from empresas_auto import get_empresas_auto
                self.companies = get_empresas_auto()
                logger.info(f"Cargadas {len(self.companies)} empresas desde empresas_auto.py")
            except ImportError:
                logger.error("No se pudo obtener lista de empresas")

        # Guardar lista
        with open('empresas_encontradas.txt', 'w', encoding='utf-8') as f:
            for slug, name in self.companies:
                f.write(f"{slug}\t{name}\n")

        return self.companies

    def extract_company_data(self, company_info):
        """Extrae datos de salarios de una empresa usando JSON-LD"""
        if isinstance(company_info, tuple):
            slug, display_name = company_info
        else:
            slug = company_info
            display_name = unquote(slug).replace('-', ' ').title()

        encoded_slug = quote(slug, safe='-.')
        company_url = f"{self.base_url}/empresa/{encoded_slug}"

        logger.info(f"Extrayendo datos de: {display_name}")
        soup = self.get_page(company_url)
        if not soup:
            return []

        company_data = []
        real_name = display_name

        # Extraer de JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
            except (json.JSONDecodeError, TypeError):
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue

                if item.get('@type') == 'Organization':
                    real_name = item.get('name', display_name)

                if item.get('@type') == 'JobPosting':
                    title = item.get('title', '')
                    description = item.get('description', '')
                    salary_text = self._extract_salary_text(description)
                    salary_min, salary_max, salary_avg = self.parse_salary(salary_text)

                    if title:
                        company_data.append({
                            'empresa': real_name,
                            'puesto': title,
                            'salario_minimo': salary_min,
                            'salario_maximo': salary_max,
                            'salario_promedio': salary_avg,
                            'moneda': 'PEN',
                            'universidad_principal': None,
                            'url_empresa': company_url,
                            'fecha_inicio': item.get('datePosted', ''),
                            'fecha_fin': item.get('validThrough', ''),
                            'fecha_extraccion': datetime.now().isoformat()
                        })

        logger.info(f"Extraidos {len(company_data)} puestos de {real_name}")
        return company_data

    def _extract_salary_text(self, description):
        """Extrae texto de salario de la descripción"""
        if not description:
            return None
        match = re.search(r'Rango salarial:\s*(S/[^.]+)', description)
        if match:
            return match.group(1).strip()
        match = re.search(r'S/\s*[\d,]+\.?\d*(?:\s*-\s*S/\s*[\d,]+\.?\d*)?', description)
        if match:
            return match.group(0).strip()
        return None

    def parse_salary(self, salary_text):
        """Parsea texto de salario"""
        if not salary_text:
            return None, None, None

        clean = salary_text.replace('S/', '').replace('PEN', '').replace(',', '').strip()

        range_match = re.search(r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)', clean)
        if range_match:
            s_min = float(range_match.group(1))
            s_max = float(range_match.group(2))
            return s_min, s_max, (s_min + s_max) / 2

        single_match = re.search(r'(\d+\.?\d*)', clean)
        if single_match:
            val = float(single_match.group(1))
            return val, val, val

        return None, None, None

    def scrape_all_companies(self, max_companies=None):
        """Extrae datos de todas las empresas"""
        if not self.companies:
            self.discover_companies()

        companies = self.companies[:max_companies] if max_companies else self.companies
        logger.info(f"Iniciando scraping de {len(companies)} empresas...")

        for i, company in enumerate(companies, 1):
            data = self.extract_company_data(company)
            self.salary_data.extend(data)

            if i % 10 == 0:
                logger.info(f"Progreso: {i}/{len(companies)} | Registros: {len(self.salary_data)}")

        logger.info(f"Scraping completado. Total: {len(self.salary_data)} registros")
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
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_empresa ON salarios(empresa)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_puesto ON salarios(puesto)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_salario ON salarios(salario_promedio)")
        conn.commit()
        conn.close()
        logger.info(f"Datos guardados en SQLite: {db_name}")

    def save_to_mysql(self, host, user, password, database):
        """Guarda los datos en MySQL"""
        try:
            import mysql.connector
            if not self.salary_data:
                return
            conn = mysql.connector.connect(host=host, user=user, password=password, database=database)
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS salarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                empresa VARCHAR(255), puesto VARCHAR(500),
                salario_minimo DECIMAL(10,2), salario_maximo DECIMAL(10,2),
                salario_promedio DECIMAL(10,2), moneda VARCHAR(10),
                universidad_principal VARCHAR(255), url_empresa VARCHAR(500),
                fecha_inicio DATE, fecha_fin DATE,
                fecha_extraccion DATETIME,
                INDEX idx_empresa (empresa), INDEX idx_puesto (puesto),
                INDEX idx_salario (salario_promedio)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            cursor.execute("DELETE FROM salarios")
            insert_q = """
            INSERT INTO salarios (empresa, puesto, salario_minimo, salario_maximo,
                salario_promedio, moneda, universidad_principal, url_empresa,
                fecha_inicio, fecha_fin, fecha_extraccion)
            VALUES (%(empresa)s, %(puesto)s, %(salario_minimo)s, %(salario_maximo)s,
                %(salario_promedio)s, %(moneda)s, %(universidad_principal)s,
                %(url_empresa)s, %(fecha_inicio)s, %(fecha_fin)s, %(fecha_extraccion)s)
            """
            cursor.executemany(insert_q, self.salary_data)
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Datos guardados en MySQL: {database}")
        except ImportError:
            logger.error("mysql-connector-python no instalado")
        except Exception as e:
            logger.error(f"Error MySQL: {e}")

    def generate_analysis_report(self):
        """Genera un reporte de análisis"""
        if not self.salary_data:
            return
        df = pd.DataFrame(self.salary_data)
        df_valid = df[df['salario_promedio'].notna() & (df['salario_promedio'] > 0)]

        print("\n" + "=" * 60)
        print("REPORTE DE ANALISIS - SALARIOS PERU 2026")
        print("=" * 60)
        print(f"\nTotal registros: {len(df)}")
        print(f"Con salario: {len(df_valid)}")
        print(f"Empresas: {df['empresa'].nunique()}")
        print(f"Puestos unicos: {df['puesto'].nunique()}")

        if not df_valid.empty:
            print(f"\nPromedio: S/ {df_valid['salario_promedio'].mean():,.2f}")
            print(f"Mediana:  S/ {df_valid['salario_promedio'].median():,.2f}")

            print("\n--- TOP 10 SALARIOS ---")
            top = df_valid.nlargest(10, 'salario_promedio')[['empresa', 'puesto', 'salario_promedio']]
            for _, r in top.iterrows():
                print(f"  S/ {r['salario_promedio']:>10,.2f} | {r['empresa'][:25]:<25} | {r['puesto'][:40]}")

            print("\n--- TOP 10 EMPRESAS ---")
            avg = df_valid.groupby('empresa')['salario_promedio'].agg(['mean', 'count'])
            avg = avg[avg['count'] >= 3].sort_values('mean', ascending=False).head(10)
            for emp, r in avg.iterrows():
                print(f"  S/ {r['mean']:>10,.2f} ({int(r['count']):>3} puestos) | {emp[:40]}")


def main():
    import sys

    print("Salarios Peru - Web Scraper 2026")
    print("=" * 50)

    scraper = SalariosPeruScraper(delay=2)

    max_companies = None
    for arg in sys.argv:
        if arg.startswith('--limit='):
            try:
                max_companies = int(arg.split('=')[1])
            except ValueError:
                pass

    try:
        companies = scraper.discover_companies()
        print(f"Encontradas {len(companies)} empresas")

        data = scraper.scrape_all_companies(max_companies=max_companies)
        print(f"Extraidos {len(data)} registros")

        scraper.save_to_csv('salarios_peru.csv')
        scraper.save_to_sqlite('salarios_peru.db')
        scraper.generate_analysis_report()

        print("\nArchivos generados:")
        print("- salarios_peru.csv")
        print("- salarios_peru.db")
        print("- empresas_encontradas.txt")

    except KeyboardInterrupt:
        print("\nInterrumpido. Guardando datos parciales...")
        if scraper.salary_data:
            scraper.save_to_csv('salarios_peru_parcial.csv')
            scraper.save_to_sqlite('salarios_peru_parcial.db')
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
