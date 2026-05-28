#!/usr/bin/env python3
"""
Descifra los charts CAS encriptados en docs/index.html para inspeccionar
su estructura. Guarda cada chart como JSON en scripts_cas/decrypted/.

Uso: ./venv/bin/python scripts_cas/decrypt_cas_charts.py
"""
import base64
import json
import re
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY = bytes.fromhex("5a6c3d8e9f1b2a4c7e8d5f3a2b1c0e9d")
ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "docs" / "index.html"
OUT = ROOT / "scripts_cas" / "decrypted"


def find_plotly_enc_calls(text):
    """Encuentra plotlyEnc("id", "b64", {layout}, config) — solo CAS."""
    results = []
    needle = 'plotlyEnc('
    i = 0
    while True:
        idx = text.find(needle, i)
        if idx < 0:
            break
        # match paréntesis respetando strings
        j = idx + len(needle)
        depth = 1
        in_string = None
        escape = False
        comma_pos = []
        while j < len(text) and depth > 0:
            c = text[j]
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif in_string:
                if c == in_string:
                    in_string = None
            elif c in '"\'`':
                in_string = c
            elif c == '(' or c in '[{':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
            elif c in ']}':
                depth -= 1
            elif c == ',' and depth == 1:
                comma_pos.append(j)
            j += 1

        if len(comma_pos) < 2:
            i = idx + 1
            continue

        div_id_raw = text[idx + len(needle):comma_pos[0]].strip().strip('"\'')
        b64_raw = text[comma_pos[0] + 1:comma_pos[1]].strip().strip('"\'')
        layout_str = text[comma_pos[1] + 1:comma_pos[2] if len(comma_pos) >= 3 else end - 1].strip()
        config_str = text[comma_pos[2] + 1:end - 1].strip() if len(comma_pos) >= 3 else ''

        if div_id_raw.startswith('chart-cas'):
            results.append({
                "id": div_id_raw,
                "b64": b64_raw,
                "layout_str": layout_str,
                "config_str": config_str,
                "start": idx,
                "end": end,
            })
        i = end
    return results


def decrypt_b64(b64_data):
    raw = base64.b64decode(b64_data)
    nonce, ct = raw[:12], raw[12:]
    plain = AESGCM(KEY).decrypt(nonce, ct, None)
    return json.loads(plain.decode('utf-8'))


def main():
    text = HTML.read_text()
    calls = find_plotly_enc_calls(text)
    print(f"Encontrados {len(calls)} charts CAS encriptados\n")

    OUT.mkdir(parents=True, exist_ok=True)

    for call in calls:
        try:
            data = decrypt_b64(call["b64"])
        except Exception as e:
            print(f"  ❌ {call['id']}: {e}")
            continue

        # Guardar data + layout para referencia
        try:
            layout = json.loads(call["layout_str"])
        except json.JSONDecodeError:
            layout = call["layout_str"]  # raw

        out_path = OUT / f"{call['id']}.json"
        payload = {
            "id": call["id"],
            "data": data,
            "layout": layout,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

        # Resumen rápido
        traces = data if isinstance(data, list) else [data]
        types = [t.get("type", "scatter") for t in traces if isinstance(t, dict)]
        title = (layout.get("title", {}) or {}).get("text", "") if isinstance(layout, dict) else ""
        title_short = re.sub(r"<[^>]+>", " ", str(title))[:80]
        print(f"  ✓ {call['id']}: {len(traces)} trace(s) [{', '.join(set(types))}] — {title_short}")

    print(f"\n→ JSON guardado en {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    sys.exit(main() or 0)
