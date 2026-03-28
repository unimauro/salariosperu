#!/usr/bin/env python3
"""
Actualiza la lista de empresas desde el sitemap de SalariosPerú.com
Genera/actualiza empresas_auto.py con todos los slugs disponibles.
"""

import requests
import re
import json
import time
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import unquote

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://salariosperu.com"


def fetch_sitemap():
    """Descarga y parsea el sitemap.xml para obtener slugs de empresas"""
    logger.info("Descargando sitemap.xml...")
    response = requests.get(f"{BASE_URL}/sitemap.xml", timeout=15)
    response.raise_for_status()

    # Extraer URLs de empresas
    empresa_urls = re.findall(r'<loc>https?://(?:www\.)?salariosperu\.com/empresa/([^<]+)</loc>', response.text)

    # Filtrar el slug "None" (bug conocido del sitemap)
    empresa_slugs = [slug.strip() for slug in empresa_urls if slug.strip() and slug.strip() != 'None']

    logger.info(f"Encontrados {len(empresa_slugs)} slugs de empresas en el sitemap")
    return empresa_slugs


def fetch_company_name(slug, session):
    """Obtiene el nombre real de la empresa desde su página usando JSON-LD"""
    url = f"{BASE_URL}/empresa/{slug}"
    try:
        response = session.get(url, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscar en JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get('@type') == 'Organization':
                        return data.get('name')
                    if 'hiringOrganization' in data:
                        return data['hiringOrganization'].get('name')
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Organization':
                            return item.get('name')
            except (json.JSONDecodeError, TypeError):
                continue

        # Fallback: título de la página
        title = soup.find('title')
        if title:
            match = re.search(r'Salarios en (.+?)(?:\s*[-|])', title.get_text())
            if match:
                return match.group(1).strip()

        return None
    except Exception as e:
        logger.debug(f"Error obteniendo nombre para {slug}: {e}")
        return None


def slug_to_name(slug):
    """Convierte un slug a un nombre legible como fallback"""
    name = unquote(slug)
    # Manejar sufijos comunes
    name = name.replace('-s-a-', ' S.A.')
    name = name.replace('-s.a.', ' S.A.')
    name = name.replace('-sac', ' SAC')
    name = name.replace('-saa', ' SAA')
    name = name.replace('-s-a-c-', ' S.A.C.')
    name = name.replace('-', ' ')
    # Capitalizar cada palabra
    return name.title()


def fetch_all_company_names(slugs, batch_size=10, delay=1.0):
    """Obtiene nombres reales de empresas en lotes"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    empresas = []
    total = len(slugs)

    for i, slug in enumerate(slugs, 1):
        name = fetch_company_name(slug, session)
        if not name:
            name = slug_to_name(slug)

        empresas.append((slug, name))

        if i % 20 == 0:
            logger.info(f"Progreso: {i}/{total} empresas procesadas")

        if i % batch_size == 0:
            time.sleep(delay)

    return empresas


def generate_empresas_auto(empresas):
    """Genera el archivo empresas_auto.py con la lista actualizada"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tildes_count = len([e for e in empresas if any(c in e[0] for c in 'áéíóúñ%')])

    lines = [
        '#!/usr/bin/env python3',
        '"""',
        f'Lista de empresas extraída automáticamente desde SalariosPerú.com',
        f'Generado automáticamente el {now}',
        f'Total de empresas: {len(empresas)}',
        f'Empresas con tildes/caracteres especiales: {tildes_count}',
        '"""',
        '',
        '# Lista completa de empresas (slug, nombre)',
        'EMPRESAS_AUTO = [',
    ]

    for slug, name in sorted(empresas, key=lambda x: x[1].lower()):
        # Escapar comillas simples en nombres
        escaped_name = name.replace("'", "\\'")
        escaped_slug = slug.replace("'", "\\'")
        lines.append(f"    ('{escaped_slug}', '{escaped_name}'),")

    lines.extend([
        ']',
        '',
        '',
        'def get_empresas_auto():',
        '    """Retorna la lista completa de empresas"""',
        '    return EMPRESAS_AUTO',
        '',
        '',
        'def get_empresas_con_tildes():',
        '    """Retorna solo empresas con tildes"""',
        '    return [e for e in EMPRESAS_AUTO if any(char in e[0] for char in \'áéíóúñ\')]',
        '',
        '',
        'def print_summary():',
        '    """Imprime resumen de empresas"""',
        '    print(f"Total de empresas: {len(EMPRESAS_AUTO)}")',
        '    empresas_tildes = get_empresas_con_tildes()',
        '    print(f"Empresas con tildes: {len(empresas_tildes)}")',
        '',
        '    print("\\nEmpresas con caracteres especiales:")',
        '    for slug, nombre in empresas_tildes:',
        '        print(f"  • {nombre} ({slug})")',
        '',
        '',
        'if __name__ == "__main__":',
        '    print_summary()',
        '',
    ])

    with open('empresas_auto.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    logger.info(f"Archivo empresas_auto.py generado con {len(empresas)} empresas")


def main():
    """Función principal"""
    import sys

    print("=" * 60)
    print("ACTUALIZADOR DE EMPRESAS - SalariosPerú.com")
    print("=" * 60)

    # Paso 1: Obtener slugs del sitemap
    slugs = fetch_sitemap()
    print(f"\n Encontradas {len(slugs)} empresas en el sitemap")

    # Verificar si el usuario quiere obtener nombres reales (lento)
    fetch_names = '--fetch-names' in sys.argv
    quick = '--quick' in sys.argv

    if fetch_names and not quick:
        print("\n Obteniendo nombres reales de empresas (esto puede tardar)...")
        empresas = fetch_all_company_names(slugs, batch_size=5, delay=1.5)
    else:
        print("\n Usando nombres derivados de slugs (usa --fetch-names para nombres reales)")
        empresas = [(slug, slug_to_name(slug)) for slug in slugs]

    # Paso 2: Generar archivo
    generate_empresas_auto(empresas)

    print(f"\n empresas_auto.py actualizado con {len(empresas)} empresas")
    print(f"\nUso:")
    print(f"  python update_empresas.py              # Rápido (nombres de slugs)")
    print(f"  python update_empresas.py --fetch-names # Lento (nombres reales del sitio)")


if __name__ == "__main__":
    main()
