#!/usr/bin/env python3
"""
Scraper de convocatorias CAS vigentes del sector publico peruano.
Fuente: https://www.convocatoriasdetrabajo.com/convocatorias-cas-vigentes.php

Output: cas_vigentes.csv con columnas:
  institucion, puesto, requisitos, departamento, plazas, salario, fecha_limite, url
"""
import csv
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.convocatoriasdetrabajo.com/convocatorias-cas-vigentes.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 "
                  "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
}
DELAY = 1.0  # ser amable con el sitio
OUTFILE = Path(__file__).parent / "cas_vigentes.csv"


def parse_convocatoria(article):
    """Extrae datos de un <article class='convocatoria'>."""
    out = {
        "institucion": "", "puesto": "", "requisitos": "",
        "departamento": "", "plazas": "", "salario": "",
        "fecha_limite": "", "url": ""
    }

    h4_a = article.select_one("h4 a")
    if h4_a:
        out["url"] = h4_a.get("href", "").strip()
        title = h4_a.get_text(" ", strip=True)
        if ":" in title:
            inst, rest = title.split(":", 1)
            out["institucion"] = inst.strip()
            out["puesto"] = rest.strip()
        else:
            out["puesto"] = title

    detalle = article.select_one(".conv-detalle")
    if not detalle:
        return out

    grado = detalle.find("i", class_="icon-grado")
    if grado and grado.find_next_sibling("span"):
        out["requisitos"] = grado.find_next_sibling("span").get_text(strip=True)

    mapa = detalle.find("i", class_="icon-mapa1")
    if mapa and mapa.find_next_sibling("span"):
        out["departamento"] = mapa.find_next_sibling("span").get_text(strip=True)

    moneda = detalle.find("i", class_="icon-moneda")
    if moneda and moneda.find_next_sibling("span"):
        sal_text = moneda.find_next_sibling("span").get_text(strip=True)
        out["salario"] = re.sub(r"[^\d.,]", "", sal_text).replace(",", "")

    calendario = detalle.find("i", class_="icon-calendario")
    if calendario and calendario.find_next_sibling("span"):
        fecha_text = calendario.find_next_sibling("span").get_text(strip=True)
        m = re.search(r"(\d{2}/\d{2}/\d{4})", fecha_text)
        if m:
            out["fecha_limite"] = m.group(1)

    for p in detalle.select(".convocatoria__group-item span"):
        txt = p.get_text(" ", strip=True)
        m = re.search(r"plazas?:\s*(\d+)", txt, re.IGNORECASE)
        if m:
            out["plazas"] = m.group(1)
            break

    return out


def scrape_page(page_num, session):
    url = BASE_URL if page_num == 1 else f"{BASE_URL}?page={page_num}&sort=1"
    r = session.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    articles = soup.select("article.convocatoria")
    rows = [parse_convocatoria(a) for a in articles]
    return rows, soup


def detect_total_pages(soup):
    nums = []
    for a in soup.select("a"):
        href = a.get("href", "")
        m = re.search(r"page=(\d+)", href)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) if nums else 1


def main(max_pages=None):
    session = requests.Session()
    print("[1] Fetching page 1 ...", flush=True)
    first_rows, _ = scrape_page(1, session)
    print(f"Page 1: {len(first_rows)} convocatorias")
    all_rows = list(first_rows)
    seen_urls = {r["url"] for r in all_rows if r["url"]}

    p = 2
    hard_cap = max_pages if max_pages else 60
    while p <= hard_cap:
        time.sleep(DELAY)
        try:
            rows, _ = scrape_page(p, session)
        except Exception as e:
            print(f"  ! Error page {p}: {e}", file=sys.stderr)
            break

        if not rows:
            print(f"Page {p}: 0 convocatorias — fin de la paginacion.")
            break

        new_rows = [r for r in rows if r["url"] not in seen_urls]
        if not new_rows:
            print(f"Page {p}: todas duplicadas — fin.")
            break

        seen_urls.update(r["url"] for r in new_rows)
        all_rows.extend(new_rows)
        print(f"Page {p}: {len(new_rows)} nuevas (total acumulado: {len(all_rows)})")
        p += 1

    if not all_rows:
        print("No se encontraron convocatorias.", file=sys.stderr)
        return 1

    fieldnames = list(all_rows[0].keys()) + ["fecha_extraccion"]
    ts = datetime.now().isoformat(timespec="seconds")
    with OUTFILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in all_rows:
            r["fecha_extraccion"] = ts
            w.writerow(r)
    print(f"\nGuardado en {OUTFILE} — {len(all_rows)} filas")
    return 0


if __name__ == "__main__":
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(main(max_pages))
