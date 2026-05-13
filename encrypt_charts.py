#!/usr/bin/env python3
"""
Encripta los datos (primer argumento) de cada Plotly.newPlot() en docs/index.html.
Usa AES-128 GCM con clave hardcoded compartida con el JS.

Reemplaza:   Plotly.newPlot("chart-X", [DATA], {layout}, config)
Por:         plotlyEnc("chart-X", "BASE64_ENC", {layout}, config)

Idempotente: si encuentra plotlyEnc(), no toca esa llamada.

USO: python encrypt_charts.py
"""
import base64
import json
import os
import re
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Clave AES-128 (16 bytes). MUST coincidir con la clave del JS.
# Esta clave es publica por diseno (el JS la incluye); el cifrado solo
# protege contra scraping automatico, no contra inspeccion manual.
KEY_HEX = "5a6c3d8e9f1b2a4c7e8d5f3a2b1c0e9d"  # 16 bytes (32 hex chars)
KEY = bytes.fromhex(KEY_HEX)
assert len(KEY) == 16

HTML_PATH = Path(__file__).parent / "docs" / "index.html"


def find_plotly_calls(text):
    """Devuelve [(start, end, divId, data_str, rest_str)] para cada Plotly.newPlot()."""
    results = []
    i = 0
    needle = 'Plotly.newPlot('
    while True:
        idx = text.find(needle, i)
        if idx < 0:
            break
        # Parsear los argumentos: divId, data, layout, config
        # Manejamos el matching de parens respetando strings
        j = idx + len(needle)
        depth = 1
        in_string = None
        escape = False
        comma_positions = []  # posiciones de comas en nivel 1
        while j < len(text) and depth > 0:
            c = text[j]
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif in_string:
                if c == in_string:
                    in_string = None
            elif c in ('"', "'", '`'):
                in_string = c
            elif c == '(':
                depth += 1
            elif c in '[{':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
            elif c in ']}':
                depth -= 1
            elif c == ',' and depth == 1:
                comma_positions.append(j)
            j += 1
        else:
            i = idx + 1
            continue

        # comma_positions: el primero separa divId/data, el segundo data/layout
        if len(comma_positions) < 1:
            i = idx + 1
            continue
        divId_str = text[idx + len(needle):comma_positions[0]].strip()
        if len(comma_positions) >= 2:
            data_str = text[comma_positions[0] + 1:comma_positions[1]].strip()
            rest_str = text[comma_positions[1]:end - 1]  # incluye la coma inicial
        else:
            data_str = text[comma_positions[0] + 1:end - 1].strip()
            rest_str = ''

        results.append((idx, end, divId_str, data_str, rest_str))
        i = end
    return results


def encrypt_data(data_str):
    """Cifra el string (que es un JSON array literal) usando AES-GCM. Retorna base64."""
    aesgcm = AESGCM(KEY)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, data_str.encode('utf-8'), None)
    return base64.b64encode(nonce + ct).decode('ascii')


def main():
    if not HTML_PATH.exists():
        print(f"ERROR: {HTML_PATH} no existe", file=sys.stderr)
        return 1

    with HTML_PATH.open() as f:
        html = f.read()

    calls = find_plotly_calls(html)
    print(f"Encontradas {len(calls)} llamadas a Plotly.newPlot()")

    if not calls:
        print("Nada que cifrar.")
        return 0

    # Reemplazar de atras hacia adelante para preservar offsets
    modified = html
    encrypted_count = 0
    skipped_count = 0
    for start, end, divId, data_str, rest_str in reversed(calls):
        # Saltar si el data_str es una variable (no un array literal)
        s = data_str.strip()
        if not s.startswith('[') and not s.startswith('{'):
            skipped_count += 1
            continue

        # Validar que sea JSON parseable (no JS con funciones)
        try:
            json.loads(s)
        except json.JSONDecodeError:
            skipped_count += 1
            continue

        enc_b64 = encrypt_data(s)
        new_call = f'plotlyEnc({divId}, "{enc_b64}"{rest_str})'
        modified = modified[:start] + new_call + modified[end:]
        encrypted_count += 1

    with HTML_PATH.open('w') as f:
        f.write(modified)

    print(f"Cifrados: {encrypted_count}")
    print(f"Saltados (no eran JSON literal): {skipped_count}")
    print(f"Bytes diff: {len(modified) - len(html):+d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
